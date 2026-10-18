---
name: task-execution
description: Implement or resume an accepted coding task with bounded changes, regression tests, source-bound evidence, checkpoints and no parallel writers.
---
# Task Execution

Read [core policy](../../WORKFLOW.md), [implementation procedure](../../procedures/02-implementation.md), and on interruption [recovery](../../procedures/05-recovery.md).

## Use when
The task is accepted and the next action is development or repair. This skill operates on the user's code; it does not launch a second worker, authorize deployment, or override project gates.

## Execute
1. Read the current task and live Git/job state; preserve uncommitted and unrelated files. If another writer could be active, do not start.
2. Select risk using deterministic trigger rules. Record acceptance and the narrowest useful plan.
3. Write a regression test first for reproducible defects where feasible; otherwise develop focused tests alongside each coherent behavior.
4. Implement in bounded increments with clear contracts and resource cleanup. Run focused verification; record actual failures and repair them.
5. Check diff, external effects and secrets before coherent Git checkpoints. Keep one task record updated with the exact next step.
6. Hand off *within the same agent* to [self-review](../self-review/SKILL.md) when the candidate is ready.

## Exit
Candidate changes and tests are inspectable, source state is recoverable, and no failed check was relabeled as passed.
