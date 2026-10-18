#!/usr/bin/env python3
"""Autonomous Coding Workflow CLI, portable across agent runtimes (Python 3.10+)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from acw_core import (VERSION, PROFILES, STATUSES, EXCLUDED, timestamp, fail, load, digest,
                      canonical, filehash, required_ids, validate_gates, repository_state,
                      validate_project, validate_task, validate_evidence, package,
                      write_manifest, init_project)
from acw_runner import run_checks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("package", "manifest", "init", "project", "task", "run", "verify"):
        item = sub.add_parser(action)
        item.add_argument("path")
        if action in ("task", "verify"):
            item.add_argument("--project", required=True)
        if action in ("run", "verify"):
            item.add_argument("--profile", choices=PROFILES, required=True)
        if action == "run":
            item.add_argument("--output", required=True)
        if action == "task":
            item.add_argument("--evidence", help="Path to checks JSON, required for done tasks")
        if action == "manifest":
            item.add_argument("--write", action="store_true",
                              help="Explicitly regenerate the package inventory")
    args = parser.parse_args(argv)
    try:
        if args.action == "package":
            result = package(args.path)
        elif args.action == "manifest":
            if not args.write:
                fail("Use manifest --write to explicitly update the manifest")
            result = write_manifest(args.path)
        elif args.action == "init":
            result = init_project(args.path)
        elif args.action == "project":
            config, gates = validate_project(args.path)
            result = {"status": "PASS", "project": config["project"],
                      "mode": config["mode"], "checks": len(gates["checks"]),
                      "note": ("GitHub PR, merge and CI verification requires external "
                               "forge inspection; this CLI does not verify it."
                               if config["mode"] == "github" else None)}
        elif args.action == "task":
            root = Path(args.project).resolve()
            validate_project(root)
            task = load(args.path)
            validate_task(task, root=root, evidence=load(args.evidence) if args.evidence else None)
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
