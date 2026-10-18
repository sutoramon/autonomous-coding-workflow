# Procedure 05 — Crash-safe recovery / handoff

**Never replay a write because a previous message ended abruptly.**

1. Read repository/user instructions, `.acw/project.json`, current task JSON and last evidence references.
2. Inspect **live** processes/jobs for ongoing work. If a writer is active or status is unknown, do not spawn another. A Markdown instruction alone cannot enforce cross-harness exclusion.
3. Inspect Git branch, worktrees, full HEAD, status, staged and untracked files, actual PR/CI/deployment state if configured. Do not rely on transcript summaries.
4. Compare live outcomes with last recorded action: finished / running / failed / unknown. Query existing job IDs before retry. Avoid rerunning non-idempotent actions until effects are reconciled.
5. Do not reset, stash, overwrite or delete unrelated work by default. Preserve valid partial changes; verify any claimed completed tests against actual source identity.
6. Set one concrete next action and unresolved blockers in the **existing** task JSON; do not create parallel session ledgers.
7. Resume the earliest incomplete applicable stage under current authority. New context reads only necessary files; no need to replay the whole chat.
8. If recovery is unsafe, stop with explicit blocker; do not manufacture successful continuation.
