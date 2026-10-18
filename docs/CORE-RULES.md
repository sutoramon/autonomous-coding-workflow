# Core Rules — Session Startup

Read this short summary at session start. [WORKFLOW.md](../WORKFLOW.md) contains the full normative policy; this page does not replace it.

1. Follow user authorization and repository/project instructions. Skills never grant push, merge, deployment or cleanup permission.
2. Read the current task, project configuration, relevant code/tests and actual Git/job state before changing files.
3. Preserve existing changes. Never duplicate an active writer or retry an uncertain non-idempotent operation blindly.
4. Define observable acceptance criteria and classify risk as `light`, `standard` or `critical`. Security and irreversible operations cannot be downgraded.
5. Implement coherent increments with meaningful regression tests, explicit contracts and bounded side effects.
6. Execute the real project-defined checks. A failed, timed-out, absent or unavailable required check blocks completion.
7. `critical` inherits `standard` and `light` gates. Do not bypass mandatory checks on a smaller diff.
8. Bind evidence to committed source content, gate configuration and immutable hashed logs; terminate gate-owned process groups on exit and preserve interrupted evidence; keep test artifacts private.
9. Review the full change, edge cases, security, data, architecture, test strength and documentation before completion.
10. Mark `done` only with passed current evidence and source-bound self-review; task-record-only commits may follow verified code.
11. On interruption, reconcile actual processes, Git/worktrees, source and evidence before resuming.
12. At each milestone audit the **whole project**, not only the latest diff.
13. Separate local completion from optional remote PR/CI/merge verification and actual runtime deployment.

See [skills](../README.md), [quality gates](VERIFICATION.md), [risk profiles](RISK-PROFILES.md), and [recovery](../procedures/05-recovery.md).
