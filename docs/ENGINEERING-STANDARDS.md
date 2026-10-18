# Engineering quality and test design

These are review standards, **not evidence by themselves**. The workflow favors testable, cohesive design over numerical game-playing. Adopt enforceable thresholds through actual project tools and quality-gate configuration.

## Qualitative criteria

| Dimension | Reviewer must examine |
| --- | --- |
| Correctness | Requirements, invalid states, invariants, failure propagation, observable effects |
| Cohesion | One meaningful reason for a module to change, predictable call sites |
| Simplicity | Reuse, minimal abstractions, no catch-all helpers or premature framework changes |
| Security | Inputs, authorization boundaries, secret leakage, harmful external effects |
| Data integrity | Constraints, atomicity, duplicate delivery, migrations, restart consistency |
| Robustness | Timeouts, cancellation, bounded retries, cleanup, partial failure |
| Performance | Bounded queries/loops/concurrency, performance budgets actually measured |
| Testing | Meaningful assertions, boundaries, real integration seams, tests that fail for intended defects |
| User experience | Loading/empty/error states, accessibility, responsive behavior, persistence |
| Operations | Reproducible build, correct installed identity, diagnostics, backup and rollback |
| Maintenance | Dead code removed, ownership evident, documented limitations and accepted debt |

## Suggested size/complexity review signals

| Metric | Investigate at | Suggested hard limit *only after project adoption* |
| --- | ---: | ---: |
| Handwritten production file (physical lines) | 300 | 500 |
| Function (physical lines) | 40 | 80 |
| Cyclomatic complexity | 10 | 15 |
| Cognitive complexity | 15 | 25 |
| Control nesting | 3 | 4 |
| Function parameters | 4 | 5 |
| Handwritten test file (lines) | 500 | 800 |

Avoid arbitrary splitting to satisfy limits. Exemptions must be scoped, owner-approved, documented and time-bounded. Generated artifacts and lockfiles are not subject to handwritten file size rules.

## Test matrix

For every task, examine applicability; write reasons for exclusions when material.

| Area | Evidence to seek |
| --- | --- |
| Unit/domain | Boundaries, invalid values, state transitions, invariants |
| Integration/DB | Real persistence, transactions, concurrency, migration upgrade |
| API | Input validation, auth denial, status/contract/error consistency |
| Security | Secret exclusion, access control negatives, adversarial but safe fixtures |
| Async/background | Duplicate runs, timeouts, cancellation, crash/recovery |
| Browser/E2E | Real user journey, failures, reload/persistence, keyboard accessibility |
| CLI/TUI | Exit codes, stdout/stderr, signals, prompt handling and terminal recovery |
| Data lifecycle | Create/update/delete/archive/restore semantics and referential integrity |
| Operations | Build identity, health/readiness, backup restore and rollback rehearsal |
| Performance | Representative load and measured budgets, not assumed speed |
| Dependencies | Vulnerabilities, licenses, unneeded packages, packaging provenance |
| Documentation | Consistent instructions, examples, references and source inventory |

**Minimum per behavior change**: prove the intended behavior with meaningful assertions. For important failure modes add negative cases; for integration boundaries use real integration evidence; for regressions prefer a red-before-green test. E2E checks must not mutate actual production state.

## Stage of checks

- **Increment**: focused fast checks and test(s) for changed behavior.
- **Candidate**: all configured mandatory checks for the risk profile plus affected regression and same-agent self-review.
- **Milestone**: [whole-project audit](../procedures/06-milestone-audit.md) and full applicable checks.
- **Release**: installed artifact identity, migration and recovery evidence plus critical user journeys.
- **Scheduled**: optional costly scans that never replace candidate-required checks.

A passed command is not automatically a passed acceptance criterion. Check whether tests were actually discovered and assertions cover the failure the task is meant to prevent.
