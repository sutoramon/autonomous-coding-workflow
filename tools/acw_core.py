"""Shared schemas, project rules, source identity and package verification."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit

VERSION = "1.0.1"
PROFILES = ("light", "standard", "critical")
STATUSES = {"backlog", "in_progress", "in_review", "done", "cancelled"}
EXCLUDED = {".git", ".acw", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox"}
TASK_PREFIX = b".acw/tasks/"
PLACEHOLDER = re.compile(r"\b(?:todo|tbd|change_me|replace this|placeholder)\b|\{\{[^}]*\}\}|<[^>]+>", re.I)


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


def applies(check, profile):
    """Required checks are cumulative: critical includes standard and light."""
    return any(PROFILES.index(level) <= PROFILES.index(profile) for level in check["required_for"])


def required_ids(gates, profile):
    if profile not in PROFILES:
        fail(f"Invalid risk profile: {profile}")
    return sorted(c["id"] for c in gates["checks"] if applies(c, profile))


def validate_gates(gates):
    if not isinstance(gates, dict) or gates.get("schema_version") != 1 or not isinstance(gates.get("checks"), list):
        fail("Invalid gate schema")
    ids = set()
    for check in gates["checks"]:
        if not isinstance(check, dict):
            fail("Invalid gate entry")
        cid = check.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{2,79}", cid) or cid in ids:
            fail(f"Duplicate or invalid check id: {cid}")
        ids.add(cid)
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a for a in argv):
            fail(f"Invalid command argv: {cid}")
        levels = check.get("required_for")
        if not isinstance(levels, list) or not levels or any(p not in PROFILES for p in levels) or len(levels) != len(set(levels)):
            fail(f"Invalid profile list: {cid}")
        timeout = check.get("timeout_seconds")
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            fail(f"Invalid timeout: {cid}")
    if not gates["checks"] or all(c.get("example_only") for c in gates["checks"]):
        fail("No configured real quality checks; replace demonstration gate")
    for level in PROFILES:
        if not any(not c.get("example_only") and applies(c, level) for c in gates["checks"]):
            fail(f"No real mandatory gate for profile {level}")


def git_bytes(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.decode(errors="replace").strip()[:250]
        fail(f"Git operation failed ({' '.join(args)}): {detail}")
    return result.stdout


def repository_state(root):
    """Identity of application code, excluding .acw/tasks metadata in commits and worktree.

    Git HEAD remains provenance; tree_digest identifies the actual tracked source snapshot
    plus any non-task changes. A task-only commit can advance HEAD without invalidating checks.
    """
    root = Path(root).resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
                          capture_output=True, check=False)
    if head.returncode:
        fail("Repository has no commits; make an initial commit before source-bound checks")
    sha = head.stdout.decode().strip()
    tree = git_bytes(root, "ls-tree", "-r", "-z", "HEAD")
    filtered = b"".join(entry + b"\0" for entry in tree.split(b"\0")
                        if entry and not entry.partition(b"\t")[2].startswith(TASK_PREFIX))
    excluded = ":(exclude).acw/tasks/**"
    diff = git_bytes(root, "diff", "--binary", "HEAD", "--", ".", excluded)
    status = git_bytes(root, "status", "--porcelain=v1", "--untracked-files=all", "--", ".", excluded)
    untracked = git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", excluded)
    raw = bytearray(filtered + b"\0DIFF\0" + diff)
    for rel in sorted(n for n in untracked.split(b"\0") if n):
        file = root / os.fsdecode(rel)
        if not file.is_file() or file.is_symlink():
            fail("Untracked source contains an unsupported non-file/symlink entry")
        raw.extend(b"\0UNTRACKED\0" + rel + b"\0" + bytes.fromhex(filehash(file)))
    return {"sha": sha, "dirty": bool(status.strip()), "tree_digest": digest(bytes(raw))}


def validate_project(root):
    root = Path(root).resolve()
    config = load(root / ".acw/project.json")
    gates = load(root / ".acw/quality-gates.json")
    if config.get("schema_version") != 1 or config.get("workflow_version") not in ("1.0.0", VERSION):
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
    if not isinstance(task, dict) or task.get("schema_version") != 1 or task.get("status") not in STATUSES or task.get("risk") not in PROFILES:
        fail("Invalid task schema / status / risk")
    if not isinstance(task.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,99}", task["id"]):
        fail("Invalid task identifier")
    acceptance = task.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance or any(not isinstance(a, str) or not a.strip() or PLACEHOLDER.search(a) for a in acceptance):
        fail("Real, non-placeholder acceptance criteria required")
    action = task.get("next_action")
    if not isinstance(action, str) or not action.strip() or PLACEHOLDER.search(action):
        fail("Task needs a concrete, non-placeholder next action")
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
            fail("Done requires live project and verified evidence (--evidence)")
        validate_evidence(evidence, Path(root), task["risk"])
        state = repository_state(root)
        recorded = evidence["source"]["sha"]
        if state["dirty"] or sr["source_sha"] != recorded or task.get("source_sha") != recorded:
            fail("Done review/task SHA must match the verified source commit; code must be clean")
    return True


def _ancestor(root, source_sha, current_sha):
    result = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", source_sha, current_sha],
                            capture_output=True, check=False)
    return result.returncode == 0


def validate_evidence(report, root, profile):
    if not isinstance(report, dict) or report.get("schema_version") != 1 or report.get("profile") != profile:
        fail("Wrong evidence schema or profile")
    root = Path(root).resolve()
    _, gates = validate_project(root)
    state = repository_state(root)
    source = report.get("source", {})
    if state["dirty"] or source.get("dirty"):
        fail("Final evidence requires clean application source; dirty evidence is development-only")
    if source.get("tree_digest") != state["tree_digest"]:
        fail("Stale source content identity")
    if not isinstance(source.get("sha"), str) or not _ancestor(root, source["sha"], state["sha"]):
        fail("Evidence source SHA must be an ancestor of current HEAD")
    after = report.get("source_after", {})
    if after.get("tree_digest") != source.get("tree_digest") or after.get("dirty") != source.get("dirty"):
        fail("Source changed while quality gates ran")
    if report.get("gate_digest") != digest(canonical(gates)):
        fail("Gate config changed since checks ran")
    rows = report.get("checks", [])
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        fail("Invalid evidence checks")
    byid = {r.get("check_id"): r for r in rows}
    if len(byid) != len(rows):
        fail("Duplicate evidence check results")
    for cid in required_ids(gates, profile):
        row = byid.get(cid)
        if not row or row.get("result") != "passed" or row.get("exit_code") != 0:
            fail(f"Required check absent or not passed: {cid}")
        if row.get("source_sha") != source["sha"] or row.get("tree_digest") != source["tree_digest"]:
            fail(f"Stale evidence for {cid}")
        rel = row.get("log")
        if not isinstance(rel, str):
            fail(f"Missing log for {cid}")
        logfile = (root / rel).resolve()
        if not logfile.is_relative_to(root) or not logfile.is_file() or logfile.is_symlink():
            fail(f"Missing/unsafe log path for {cid}")
        if row.get("log_sha256") != filehash(logfile):
            fail(f"Log checksum mismatch for {cid}")
    return True


def _inventory(root):
    root = Path(root).resolve()
    current = {}
    for path in root.rglob("*"):
        if any(part in EXCLUDED for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            fail(f"Unsafe package symlink: {path.relative_to(root)}")
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "package-manifest.json":
            continue
        current[rel] = filehash(path)
        if path.suffix == ".md":
            raw = re.sub(r"```[\s\S]*?```", "", path.read_text(encoding="utf-8"))
            for link in re.findall(r"\]\(([^)]+)\)", raw):
                if link.startswith("#"):
                    continue
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                ref = (path.parent / unquote(parsed.path)).resolve()
                if not ref.is_relative_to(root) or not ref.exists():
                    fail(f"Broken/unsafe Markdown link in {rel}: {link}")
    return current


def write_manifest(root):
    root = Path(root).resolve()
    inventory = _inventory(root)
    manifest = {"schema_version": 1, "version": VERSION,
                "files": [{"path": k, "sha256": v} for k, v in sorted(inventory.items())]}
    tmp = root / "package-manifest.json.tmp"
    if tmp.exists():
        fail("Manifest temporary path exists; inspect before retry")
    with tmp.open("x", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    tmp.replace(root / "package-manifest.json")
    return {"status": "WRITTEN", "files": len(inventory), "version": VERSION}


def package(root):
    root = Path(root).resolve()
    manifest = load(root / "package-manifest.json")
    if manifest.get("version") != VERSION:
        fail("Wrong package manifest version")
    entries = manifest.get("files", [])
    if not isinstance(entries, list):
        fail("Invalid package manifest entries")
    known = {e["path"]: e["sha256"] for e in entries}
    if len(known) != len(entries):
        fail("Duplicate package manifest paths")
    current = _inventory(root)
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
                  dest / "tasks/TASK-EXAMPLE.json": src / "task.json",
                  dest / ".gitignore": None}
    for target in candidates:
        if target.exists():
            fail(f"Initialization refused: {target} already exists")
    for target, source in candidates.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if source is None:
            target.write_text("evidence/\ncheck-run.lock\n", encoding="utf-8")
        else:
            shutil.copyfile(source, target)
    return {"status": "CREATED", "files": [str(p) for p in candidates]}
