# Procedure 04 — Release and closeout

1. Confirm applicable authority: local completion, optional PR/merge, deployment target, and cleanup rights are distinct.
2. Check current full SHA and clean/dirty status; validate source-bound mandatory checks and current same-agent self-review.
3. In solo mode no remote PR is implied. In GitHub mode inspect live PR status, head/base and CI; after an authorized merge inspect the **actual merge SHA** and its required checks. Do not assume PR status or infer deployment.
4. For deploys, identify actual artifact and destination, back up/validate data where needed, verify migration and rollback options, and run installed smoke/health checks. Never confuse code rollback with database rollback.
5. Preserve desired changes and evidence; inspect ignored/untracked files and task-owned temporary processes before cleanup. Do not force-delete unknown data.
6. Update task state to `done` only if all applicable gates and explicitly required release actions passed; record unresolved work and source identity otherwise.
