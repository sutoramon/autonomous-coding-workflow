# Quality gates, source identity and evidence

## Gate configuration

A project owns its actual commands in `.acw/quality-gates.json`. Every check has an ID, an argument vector (no implicit shell), minimum required risk profile(s) and timeout. Gate commands are executed in the application repository root with the invoking user's privileges. ACW does not install scanners, configure CI, expose production credentials or invent passing evidence.

The generated example includes a harmless demonstration command marked `example_only`, and **must be replaced** before project readiness. The validator deliberately rejects a gate file whose only check is a demonstration.

## CLI

```sh
python3 -B tools/acw.py package .
python3 -B tools/acw.py manifest . --write  # after intentionally changing package files
python3 -B tools/acw.py init /path/to/app
python3 -B tools/acw.py project /path/to/app
python3 -B tools/acw.py task /path/to/app/.acw/tasks/TASK.json --project /path/to/app
# When the task status is done, provide verified evidence:
python3 -B tools/acw.py task /path/to/app/.acw/tasks/TASK.json --project /path/to/app --evidence /path/to/app/.acw/evidence/checks.json
python3 -B tools/acw.py run /path/to/app --profile standard --output /path/to/app/.acw/evidence/checks.json
python3 -B tools/acw.py verify /path/to/app/.acw/evidence/checks.json --project /path/to/app --profile standard
```

A `run` record includes: source full SHA, whether tree was dirty, SHA-256 of the source diff/untracked-content identity, tool/argv, UTC timestamps, elapsed time, exit code, result and log file. A missing executable is `blocked`, timeouts are `timed_out`, nonzero exits are `failed`; all cause an overall nonzero status if required.

The runner stores command logs under a separate `logs/<evidence-file-stem>/` folder for each run, with private permissions and SHA-256 checksums checked by `verify`; it **does not** sanitize arbitrary output. Keep evidence private, never commit logs with secrets, and inspect all outgoing content.

`verify` only accepts matching source identity, profile, exact required check IDs, passed status and current gate-config digest. Changing application source or gate configuration invalidates prior clean-candidate results. Tracked task-only record changes, including a task-only completion commit, preserve the application-source digest. Source SHA remains recorded for provenance. Dirty-tree results may support iterative work but **cannot** be used as clean release evidence.

Structured evidence complements, not replaces, code inspection: a zero-test suite that exits 0 remains insufficient if actual tests were required. In CI mode, exact PR head, actual merge SHA and CI association must be checked from the chosen forge; the CLI does not claim to do so.

## Status distinctions

`passed`, `failed`, `blocked`, `timed_out`, `not_run` and `not_applicable` are distinct. Any missing mandatory result blocks candidate acceptance. Exceptions require explicit owner authority, reason, scope, expiry and compensating verification; an agent must not invent self-exemptions.

## Safety and concurrency

This is an explicit command runner, not a sandbox. Review check configuration before use; commands execute with local permissions. Only run tests against disposable or project-designated test data. Avoid parallel writers. An `fcntl.flock` lock guards concurrent CLI runs on the same host and project, and releases after a killed process. On timeout the runner kills the child process group (POSIX); it cannot guarantee termination of detached children. It does not coordinate unrelated agents or processes. Check evidence before retrying.

## Profiles and GitHub boundaries

Profile requirements are cumulative: `critical` includes every `standard` and `light` gate, and `standard` includes `light`. A required check must be assigned to at least its minimum profile.

In `github` mode the CLI validates the local candidate and reports that **remote PR, CI, merge and deployment state require separate live verification**. It does not call `gh`, approve a PR, or certify a remote release.
