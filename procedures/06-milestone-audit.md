# Procedure 06 — Whole-project milestone audit

Run at every milestone boundary. A candidate-diff review is not sufficient.

1. Identify the milestone, exact project scope, full SHA and open task state.
2. Compare every accepted feature to real implementation and relevant integration/user journeys.
3. Inspect **all in-scope modules**, module size/responsibility drift, dependency edges, unused code, redundant implementations, security and data flows, startup/restart/recovery.
4. Check project-wide documentation consistency, file inventory, actual command examples, operation/installation steps and decision records.
5. Run configured milestone-required and baseline regression checks. Tests use isolated resources and concrete source-bound evidence.
6. Check outstanding tasks, incidents, stale findings, known limitations, resource headroom and migration/release readiness.
7. Fix blocking defects and rerun impacted checks; record other findings as bounded follow-up tasks.
8. Record the milestone verdict and its scope in the existing task/roadmap. Missing mandatory evidence blocks closure. Do not call a partial audit complete.
