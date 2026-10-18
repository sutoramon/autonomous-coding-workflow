# Procedure 02 — Task implementation

1. **Reconcile:** Read task, instructions, working tree, history, associated remote PR if configured, and known active jobs. If another writer may exist, stop and verify before writing.
2. **Scope:** Risk classification, acceptance criteria, expected side effects, relevant modules/tests, bounded plan.
3. **Test:** For regression fix reproduce the previous bug and show a targeted assertion can detect it when practical. Cover invalid, denied and recovery paths commensurate with risk.
4. **Implement:** Small cohesive change. Prefer existing abstractions; validate inputs; preserve data integrity, cancellation and error visibility.
5. **Check:** Focused tests, format, types, lint or other checks required at this stage. Diagnose failures and rerun after repair. Do not skip unavailable required checks.
6. **Checkpoint:** Inspect diff, preserve unrelated changes, record current SHA plus dirty state and next step in one task record. Commit only intentional source after scanning for credentials and private data; do not push without authorization.
7. **Refactor:** Remove obsolete implementations; check module responsibilities and dependency boundaries rather than mechanically splitting files.
8. **Review:** Route to [same-agent review](03-self-review.md). Keep any unfinished task open and recoverable.
