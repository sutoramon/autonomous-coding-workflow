# Repository agent instructions

Follow the project-authorized development workflow. Read the project's `.acw/project.json`, the current task and the externally provided ACW package instructions when configured; do not hardcode host-specific paths.

One coding agent owns implementation, tests and evidence-backed self-review. Do not create a second reviewer agent. Reconcile active jobs and actual Git state before writes. Use deterministic risk escalation and project-specific executable quality gates. Record true check outcomes and exact source identities; missing or failed mandatory checks block completion. Never assume permission to push, merge, deploy or clean another task's resources.

Project-specific rules and commands belong here; do not overwrite existing repository instructions.
