---
name: release-closeout
description: Verify an authorized release or task closeout with actual source/build identity, safe recovery, evidence and cleanup.
---
# Release Closeout

Read [core policy](../../WORKFLOW.md), [release procedure](../../procedures/04-release.md), and [verification](../../docs/VERIFICATION.md). Use [recovery](../../procedures/05-recovery.md) when state is uncertain.

## Use when
A reviewed task is ready for local completion, a PR is ready under explicit authority, or an authorized deployment or cleanup is pending.

## Verify
For solo mode, verify applicable clean-commit evidence, updated docs and completion conditions. For GitHub mode, distinguish PR head, tested commit, merged SHA and installed SHA; require the configured exact-identity checks. Do not merge or deploy without current authorization. Before cleanup, prove all desirable work and evidence are preserved; never delete resources of another task.

## Exit
Report what is actually committed, checked, merged, deployed and cleaned. Mark the task done only after all applicable conditions pass. Pending human-only actions remain pending.
