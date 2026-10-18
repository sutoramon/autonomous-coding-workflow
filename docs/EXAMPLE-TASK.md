# Example: fixing an API authorization bug

**This is illustrative, not evidence for a real application.** One coding agent can follow this without native skill registration.

1. Read [workflow](../WORKFLOW.md) and [task skill](../skills/task-execution/SKILL.md).
2. Inspect current Git and active jobs; do not start while another writer is active.
3. Record task ID, observable acceptance and risk. Because authorization changes are security-critical, set `risk=critical` and a nonempty `critical_triggers` list.
4. Add a regression test that demonstrates a denied user could formerly access another user's record, using synthetic identities and isolated test storage.
5. Repair the authoritative API authorization boundary. Test permitted and denied requests, leakage in error messages, audit behavior and existing normal use.
6. Run focused tests, then required `critical` profile checks from the **real** project gate file; retain results, source SHA and logs privately.
7. Commit the candidate after scanning the diff, then rerun clean-commit required gates if the dirty candidate differs from final source.
8. Perform [same-agent self-review](../procedures/03-self-review.md) from current requirements, diff and evidence, not implementation justifications.
9. Record review verdict on the final source identity. Close only if all mandatory checks, acceptance criteria and authorized release conditions hold.
10. If interrupted, use [recovery](../procedures/05-recovery.md) to inspect live Git and active jobs before any write.
