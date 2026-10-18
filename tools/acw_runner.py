"""Bounded, process-group-aware, hash-verified command execution."""
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
    """Create a new private file, never overwrite, and never leave world-readable windows."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(payload)
    finally:
        if fd >= 0:
            os.close(fd)


def _private_log(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(fd, "wb")


def run_checks(root, profile, output):
    root = Path(root).resolve()
    _, gates = validate_project(root)
    source = repository_state(root)
    output = Path(output).resolve()
    if root not in output.parents:
        fail("Evidence output must reside inside the target project")
    if output.exists():
        fail("Evidence output exists; don't overwrite historical evidence")
    if not required_ids(gates, profile):
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
        # Validate all destinations while holding the lock.
        if output.exists():
            fail("Evidence output exists; don't overwrite historical evidence")
        output.parent.mkdir(parents=True, exist_ok=True)
        logdir = output.parent / "logs" / output.stem
        if logdir.exists():
            fail("Log directory already exists; choose a unique output file")
        logdir.mkdir(parents=True, mode=0o700)
        results = []
        for check in gates["checks"]:
            if check["id"] not in required_ids(gates, profile):
                continue
            logfile = logdir / f"{check['id']}-{len(results):03d}.log"
            # Exclusive open with secure permissions before writing any output.
            started = time.monotonic()
            started_at = timestamp()
            code = None
            result = "blocked"
            with _private_log(logfile) as log:
                try:
                    proc = subprocess.Popen(check["argv"], cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                            start_new_session=True)
                    try:
                        code = proc.wait(timeout=check["timeout_seconds"])
                        result = "passed" if code == 0 else "failed"
                    except subprocess.TimeoutExpired:
                        result = "timed_out"
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        proc.wait()
                        log.write(b"\nACW: timeout; process group killed\n")
                except (FileNotFoundError, PermissionError, OSError) as exc:
                    log.write(f"{type(exc).__name__}: {exc}\n".encode("utf-8", errors="replace"))
            results.append({
                "check_id": check["id"], "argv": check["argv"], "timeout_seconds": check["timeout_seconds"],
                "tool": check["argv"][0], "source_sha": source["sha"], "tree_digest": source["tree_digest"],
                "result": result, "exit_code": code, "started_at": started_at,
                "finished_at": timestamp(), "duration_ms": round((time.monotonic()-started)*1000),
                "log": str(logfile.relative_to(root)), "log_sha256": filehash(logfile),
            })
        after = repository_state(root)
        report = {"schema_version": 1, "profile": profile, "source": source,
                  "source_after": after, "gate_digest": digest(canonical(gates)), "checks": results,
                  "started_at": results[0]["started_at"], "finished_at": timestamp()}
        _write_private(output, json.dumps(report, indent=2)+"\n")
        if after["tree_digest"] != source["tree_digest"] or after["dirty"] != source["dirty"]:
            fail("Application source changed during checks; results cannot be final evidence")
        if any(x["result"] != "passed" for x in results):
            fail("One or more mandatory checks did not pass")
        return {"status": "PASS", "source_sha": source["sha"], "dirty": source["dirty"],
                "checks": len(results), "evidence": str(output)}
    finally:
        try:
            fcntl.flock(lockfd, fcntl.LOCK_UN)
        finally:
            os.close(lockfd)
        # Keep lock inode to prevent unlink/recreation race; flock releases on exit.
