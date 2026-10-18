#!/usr/bin/env python3
"""Portable single-agent workflow checks and project gate runner (Python stdlib only)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import unquote, urlsplit

VERSION = "1.0.0"
PROFILES = ("light", "standard", "critical")
STATUSES = {"backlog", "in_progress", "in_review", "done", "cancelled"}
BLOCKING = {"failed", "blocked", "timed_out", "not_run"}
EXCLUDED = {".git", ".acw", "__pycache__", ".pytest_cache"}
PRIVATE = re.compile(r"(?:/home/[^/\s]+/|/mnt/data/|(?:api[_-]?key|token|password)\s*[:=]\s*[^\s]+)", re.I)

def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def fail(message):
    raise ValueError(message)

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def filehash(path):
    return digest(Path(path).read_bytes())

def required_ids(gates, profile):
    return sorted(x["id"] for x in gates["checks"] if profile in x["required_for"])

def validate_gates(gates):
    if gates.get("schema_version") != 1 or not isinstance(gates.get("checks"), list):
        fail("Invalid gate schema")
    ids = set()
    for check in gates["checks"]:
        cid = check.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{2,79}", cid) or cid in ids:
            fail(f"Duplicate or invalid check id: {cid}")
        ids.add(cid)
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a for a in argv):
            fail(f"Invalid command argv: {cid}")
        required = check.get("required_for")
        if not isinstance(required, list) or any(p not in PROFILES for p in required) or len(required) != len(set(required)):
            fail(f"Invalid profile list: {cid}")
        timeout = check.get("timeout_seconds")
        if not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            fail(f"Invalid timeout: {cid}")
    if not gates["checks"] or all(c.get("example_only") for c in gates["checks"]):
        fail("No configured real quality checks; replace demonstration gate")
    for p in PROFILES:
        if not required_ids(gates, p):
            fail(f"No mandatory gate for profile {p}")

def repository_state(root):
    def git(*args):
        res = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
        if res.returncode:
            fail(f"Git not available in {root}: {res.stderr.decode(errors='replace').strip()[:200]}")
        return res.stdout
    sha = git("rev-parse", "HEAD").decode().strip()
    diff = git("diff", "--binary", "HEAD", "--")  # tracked modifications, index and unstaged
    status = git("status", "--porcelain=v1", "--untracked-files=all", "--")
    # Include untracked content without revealing it in the returned report.
    untracked = git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    raw = bytearray(diff)
    for rel in sorted(n for n in untracked if n):
        path = root / os.fsdecode(rel)
        if not path.is_file() or path.is_symlink():
            continue
        raw.extend(b"\0UNTRACKED\0" + rel + b"\0")
        raw.extend(bytes.fromhex(filehash(path)))
    return {"sha": sha, "dirty": bool(status.strip()), "tree_digest": digest(bytes(raw))}

def validate_project(root):
    root = Path(root).resolve()
    config = load(root / ".acw/project.json")
    gates = load(root / ".acw/quality-gates.json")
    if config.get("schema_version") != 1 or config.get("workflow_version") != VERSION:
        fail("Unsupported project schema or workflow version")
    if config.get("mode") not in ("solo", "github"):
        fail("Mode must be solo or github")
    if not isinstance(config.get("project"), str) or not config["project"].strip() or config["project"] == "CHANGE_ME":
        fail("Project name must be configured")
    authority = config.get("authority", {})
    if not isinstance(authority, dict) or not all(isinstance(authority.get(k), str) and authority[k].strip() for k in ("merge", "deploy")):
        fail("Explicit merge and deploy authority required")
    required = config.get("required_files", [])
    if not isinstance(required, list) or any(not isinstance(x, str) or x.startswith("/") or ".." in Path(x).parts for x in required):
        fail("Invalid required project files")
    for rel in required:
        if not (root / rel).is_file():
            fail(f"Missing required project file: {rel}")
    validate_gates(gates)
    return config, gates

def validate_task(task, *, root=None, evidence=None):
    if task.get("schema_version") != 1 or task.get("status") not in STATUSES or task.get("risk") not in PROFILES:
        fail("Invalid task schema / status / risk")
    if not isinstance(task.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,99}", task["id"]):
        fail("Invalid task identifier")
    if not isinstance(task.get("acceptance"), list) or not task["acceptance"] or any(not isinstance(a, str) or not a.strip() for a in task["acceptance"]):
        fail("At least one real acceptance criterion required")
    if any("Replace this" in str(x) for x in task["acceptance"]):
        fail("Replace task acceptance placeholders")
    if not isinstance(task.get("next_action"), str):
        fail("Task needs a concrete next action")
    triggers = task.get("critical_triggers", [])
    if not isinstance(triggers, list) or any(not isinstance(x, str) for x in triggers):
        fail("Invalid critical triggers")
    if triggers and task["risk"] != "critical":
        fail("Critical triggers require the critical profile")
    sr = task.get("self_review")
    if not isinstance(sr, dict) or sr.get("verdict") not in ("not_run", "passed", "changes_requested", "blocked"):
        fail("Missing self-review verdict")
    if task["status"] == "done":
        if sr["verdict"] != "passed" or not sr.get("source_sha"):
            fail("Done requires passed source-bound self-review")
        if task.get("blockers"):
            fail("Done cannot retain blockers")
        if root is None or evidence is None:
            fail("Done requires live project and verified evidence")
        validate_evidence(evidence, Path(root), task["risk"])
        state = repository_state(Path(root))
        if state["dirty"] or sr["source_sha"] != state["sha"] or task.get("source_sha") != state["sha"]:
            fail("Done review/task SHA must match the current clean HEAD")
    return True

def validate_evidence(report, root, profile):
    if report.get("schema_version") != 1 or report.get("profile") != profile:
        fail("Wrong evidence schema or profile")
    _, gates = validate_project(root)
    state = repository_state(root)
    if state["dirty"]:
        fail("Final evidence requires a clean repository; dirty evidence is development-only")
    for key in ("sha", "tree_digest", "dirty"):
        if report.get("source", {}).get(key) != state[key]:
            fail(f"Stale source identity: {key}")
    if report.get("gate_digest") != digest(canonical(gates)):
        fail("Gate config changed since checks ran")
    byid = {r.get("check_id"): r for r in report.get("checks", [])}
    if len(byid) != len(report.get("checks", [])):
        fail("Duplicate evidence check results")
    for cid in required_ids(gates, profile):
        row = byid.get(cid)
        if not row or row.get("result") != "passed" or row.get("exit_code") != 0:
            fail(f"Required check absent or not passed: {cid}")
        if row.get("source_sha") != state["sha"] or row.get("tree_digest") != state["tree_digest"]:
            fail(f"Stale evidence for {cid}")
    return True

def package(root):
    root = Path(root).resolve()
    manifest = load(root / "package-manifest.json")
    if manifest.get("version") != VERSION:
        fail("Wrong package manifest version")
    known = {x["path"]: x["sha256"] for x in manifest["files"]}
    current = {}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in (".git", "__pycache__") for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "package-manifest.json":
            continue
        current[rel] = filehash(path)
        if path.suffix != ".md":
            continue
        raw = path.read_text(encoding="utf-8")
        raw = re.sub(r"```[\s\S]*?```", "", raw)
        for link in re.findall(r"\]\(([^)]+)\)", raw):
            if link.startswith("#"):
                continue
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            ref = (path.parent / unquote(parsed.path)).resolve()
            if not ref.is_relative_to(root) or not ref.exists():
                fail(f"Broken / unsafe Markdown link in {rel}: {link}")
    if current != known:
        mismatches = sorted(set(current) ^ set(known))
        changed = sorted(k for k in set(current) & set(known) if current[k] != known[k])
        fail(f"Package inventory/checksum mismatch: missing/extra={mismatches[:12]} changed={changed[:12]}")
    return {"status": "PASS", "files": len(current), "version": VERSION}

def init_project(root):
    root = Path(root).resolve()
    if not (root / ".git").exists():
        fail("Target must be a Git repository (no implicit init)")
    src = Path(__file__).resolve().parents[1] / "templates"
    dest = root / ".acw"
    candidates = {dest / "project.json": src / "project.json",
                  dest / "quality-gates.json": src / "quality-gates.json",
                  dest / "tasks/TASK-EXAMPLE.json": src / "task.json"}
    for target in candidates:
        if target.exists():
            fail(f"Initialization refused: {target} already exists")
    for target, source in candidates.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (dest / ".gitignore").write_text("evidence/\ncheck-run.lock\n", encoding="utf-8")
    return {"status": "CREATED", "files": [str(p) for p in candidates] + [str(dest / ".gitignore")]}

def run_checks(root, profile, output):
    root = Path(root).resolve()
    _, gates = validate_project(root)
    source = repository_state(root)
    output = Path(output).resolve()
    if root not in output.parents:
        fail("Evidence output must reside inside the target project")
    if output.exists():
        fail("Evidence output exists; don't overwrite historical evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    logdir = output.parent / "logs"
    logdir.mkdir(exist_ok=True)
    lockpath = root / ".acw" / "check-run.lock"
    fd = None
    try:
        fd = os.open(lockpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, str(os.getpid()).encode())
    except FileExistsError:
        fail("Another ACW check run may be active (lock exists); inspect before retry")
    finally:
        if fd is not None:
            os.close(fd)
    results = []
    try:
        for check in gates["checks"]:
            if profile not in check["required_for"]:
                continue
            start = time.monotonic()
            started = timestamp()
            status, code, output_text = "blocked", None, ""
            try:
                proc = subprocess.run(check["argv"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=check["timeout_seconds"], check=False)
                code = proc.returncode
                output_text = proc.stdout.decode("utf-8", errors="replace")
                status = "passed" if code == 0 else "failed"
            except subprocess.TimeoutExpired as exc:
                status = "timed_out"
                output_text = (exc.stdout or b"").decode("utf-8", errors="replace") + "\nTimed out"
            except (FileNotFoundError, PermissionError, OSError) as exc:
                status = "blocked"
                output_text = f"{type(exc).__name__}: {exc}"
            logfile = logdir / f"{check['id']}-{len(results):03d}.log"
            logfile.write_text(output_text, encoding="utf-8")
            logfile.chmod(0o600)
            results.append({
                "check_id": check["id"], "argv": check["argv"], "timeout_seconds": check["timeout_seconds"],
                "tool": check["argv"][0], "source_sha": source["sha"], "tree_digest": source["tree_digest"],
                "result": status, "exit_code": code, "started_at": started,
                "finished_at": timestamp(), "duration_ms": round((time.monotonic()-start)*1000),
                "log": str(logfile.relative_to(root)),
            })
        after = repository_state(root)
        report = {"schema_version": 1, "profile": profile, "source": source,
                  "source_after": after, "gate_digest": digest(canonical(gates)), "checks": results,
                  "started_at": results[0]["started_at"] if results else timestamp(), "finished_at": timestamp()}
        output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        output.chmod(0o600)
        if after != source:
            fail("Source changed during quality gates; results cannot be final evidence")
        if any(x["result"] != "passed" for x in results):
            fail("One or more mandatory checks did not pass")
        return {"status": "PASS", "source_sha": source["sha"], "dirty": source["dirty"], "checks": len(results), "evidence": str(output)}
    finally:
        lockpath.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("package", "init", "project", "task", "run", "verify"):
        p = sub.add_parser(action)
        p.add_argument("path")
        if action in ("task", "verify"):
            p.add_argument("--project", required=True)
        if action in ("run", "verify"):
            p.add_argument("--profile", choices=PROFILES, required=True)
        if action == "run":
            p.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.action == "package":
            result = package(args.path)
        elif args.action == "init":
            result = init_project(args.path)
        elif args.action == "project":
            config, gates = validate_project(args.path)
            result = {"status": "PASS", "project": config["project"], "mode": config["mode"], "checks": len(gates["checks"])}
        elif args.action == "task":
            root = Path(args.project).resolve()
            validate_project(root)
            task = load(args.path)
            validate_task(task, root=root)
            result = {"status": "PASS", "task": task["id"]}
        elif args.action == "run":
            result = run_checks(args.path, args.profile, args.output)
        else:
            root = Path(args.project).resolve()
            validate_evidence(load(args.path), root, args.profile)
            result = {"status": "PASS", "profile": args.profile}
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
