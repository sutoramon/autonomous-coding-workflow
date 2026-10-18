# Changelog

## 1.0.2 — 2026-10-18

- Terminate isolated gate process groups after every exit, including successful shells with background descendants.
- Preserve incomplete evidence and clean up gate processes on interruption or runtime errors.
- Narrow placeholder detection so code syntax, component names and regular TODO references remain valid acceptance criteria.
- Accept evidence from a stronger risk profile when validating lower-risk tasks.
- Document POSIX-only CLI requirements and tidy imports and check selection.

## 1.0.1 — 2026-10-18

- Fixed completed-task validation with explicit evidence and task-only commit handling.
- Added process-group timeout termination, streaming private run logs and log digest verification.
- Added per-run log isolation, robust flock locks, cumulative risk profiles, manifest regeneration, stronger task checks and CLI regressions.
- Clarified GitHub validation scope and added concise session core rules.

## 1.0.0 — 2026-10-18

- First public-ready, single-agent, harness-independent workflow.
- Four portable phase skills; six procedures; solo and optional GitHub modes.
- Risk-adaptive light/standard/critical profiles.
- Recovery guidance, SHA/dirty-tree-bound executable quality-gate evidence and whole-milestone audits.
- Standard-library Python command-line validator/runner, fixtures and CI example.
- No hosted-model integration, orchestration service, or automatic deployment.
