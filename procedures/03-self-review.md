# Procedure 03 — Same-agent self-review

1. Read acceptance and the complete candidate diff **before** re-reading implementation rationale. Fresh-context reread is recommended when supported, but never requires another model or agent.
2. Compare behavior to specification: successful, empty, invalid, denied, timed-out, interrupted and concurrent flows as appropriate.
3. Examine security boundaries, secrets, data correctness, migrations, irreversible side effects, contract compatibility and cleanup.
4. Inspect impacted modules for architecture drift, redundant code, maintainability, complexity and tests that can actually detect regressions. Review UI keyboard, responsiveness and state coverage when relevant.
5. Execute required profile checks on the candidate (or inspect trusted, exact-source CI results). Run `acw verify`; check logs for real assertion discovery and any remaining failures.
6. Write findings into the existing task record, with severity and location. If changes are required, return to implementation and repeat affected verification after changing source.
7. Record `passed`, `changes_requested` or `blocked` tied to current source. This review is by the **same agent**; don't label it independent.
8. On a milestone, also complete [whole-project audit](06-milestone-audit.md). Never close a milestone from a diff review alone.
