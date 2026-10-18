"""Run project checks with immutable logs, process-group cleanup and interruption evidence."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from acw_core import canonical, digest, fail, filehash, repository_state, required_ids, timestamp, validate_project


def _write_private(path, payload):
    """Create a private evidence file without overwriting existing output."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)


def _private_log(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(fd, "wb")


def _terminate_group(proc):
    """A completed shell may have live grandchildren; kill the entire isolated group."""
    if proc is None:
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    finally:
        # Reap the direct child even on cancellation or unexpected failures.
        proc.wait()


def _execute_check(root, check, logfile, source, ordinal):
    """Execute one check, returning a row even when interrupted or unexpectedly failing."""
    started = time.monotonic()
    started_at = timestamp()
    result = "blocked"
    exit_code = None
    interrupted = None
    proc = None

    with _private_log(logfile) as log:
        try:
            try:
                proc = subprocess.Popen(
                    check["argv"], cwd=root, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    exit_code = proc.wait(timeout=check["timeout_seconds"])
                    result = "passed" if exit_code == 0 else "failed"
                except subprocess.TimeoutExpired:
                    result = "timed_out"
                    log.write(b"\nACW: timeout; terminating process group\n")
            except (FileNotFoundError, PermissionError, OSError) as exc:
                log.write(f"{type(exc).__name__}: {exc}\n".encode("utf-8", errors="replace"))
            except BaseException as exc:
                # A keyboard interrupt or unexpected exception must not discard this check.
                result = "interrupted"
                interrupted = exc
                log.write(f"\nACW: interrupted ({type(exc).__name__}); terminating group\n".encode())
        finally:
            # Always clean up grandchildren, even when the shell returned exit code 0.
            try:
                _terminate_group(proc)
            except BaseException as exc:
                result = "interrupted"
                if interrupted is None:
                    interrupted = exc
                log.write(f"\nACW: cleanup failed ({type(exc).__name__})\n".encode())
    row = {
        "check_id": check["id"], "argv": check["argv"],
        "timeout_seconds": check["timeout_seconds"], "tool": check["argv"][0],
        "source_sha": source["sha"], "tree_digest": source["tree_digest"],
        "result": result, "exit_code": exit_code,
        "started_at": started_at, "finished_at": timestamp(),
        "duration_ms": round((time.monotonic() - started) * 1000),
        "log": str(logfile.relative_to(root)), "log_sha256": filehash(logfile),
    }
    return row, interrupted


def run_checks(root, profile, output):
    root = Path(root).resolve()
    _, gates = validate_project(root)
    source = repository_state(root)
    output = Path(output).resolve()
    if root not in output.parents:
        fail("Evidence output must reside inside the target project")
    if output.exists():
        fail("Evidence output exists; don't overwrite historical evidence")

    selected = set(required_ids(gates, profile))
    if not selected:
        fail("No checks selected")

    lockpath = root / ".acw" / "check-run.lock"
    lockfd = os.open(lockpath, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fail("Another ACW check run is active")
        os.ftruncate(lockfd, 0)
        os.write(lockfd, str(os.getpid()).encode("ascii"))

        if output.exists():
            fail("Evidence output exists; don't overwrite historical evidence")
        output.parent.mkdir(parents=True, exist_ok=True)
        logdir = output.parent / "logs" / output.stem
        if logdir.exists():
            fail("Log directory already exists; choose a unique output file")
        logdir.mkdir(parents=True, mode=0o700)

        results = []
        error = None
        started_at = timestamp()
        after = None
        # Once the run directory exists, preserve evidence even on Ctrl+C/exception.
        try:
            for check in gates["checks"]:
                if check["id"] not in selected:
                    continue
                logfile = logdir / f"{check['id']}-{len(results):03d}.log"
                row, interrupted = _execute_check(root, check, logfile, source, len(results))
                results.append(row)
                if interrupted is not None:
                    raise interrupted
            after = repository_state(root)
        except BaseException as exc:
            error = exc
        finally:
            # A follow-up status check can fail too; retain the original exception.
            if after is None:
                try:
                    after = repository_state(root)
                except Exception:
                    after = None
            report = {
                "schema_version": 1, "profile": profile, "source": source,
                "source_after": after, "gate_digest": digest(canonical(gates)),
                "checks": results, "started_at": started_at, "finished_at": timestamp(),
                "complete": error is None and len(results) == len(selected),
            }
            _write_private(output, json.dumps(report, indent=2) + "\n")

        if error is not None:
            raise error
        if after["tree_digest"] != source["tree_digest"] or after["dirty"] != source["dirty"]:
            fail("Application source changed during checks; results cannot be final evidence")
        if any(row["result"] != "passed" for row in results):
            fail("One or more mandatory checks did not pass")
        return {
            "status": "PASS", "source_sha": source["sha"], "dirty": source["dirty"],
            "checks": len(results), "evidence": str(output),
        }
    finally:
        fcntl.flock(lockfd, fcntl.LOCK_UN)
        os.close(lockfd)
        # Leave the lock inode in place: flock releases on process death.
