# Procedure 01 — Project onboarding

1. **Read:** User request, applicable repo instructions, existing project and the [core workflow](../WORKFLOW.md).
2. **Define:** Users, desired behavior, exclusions, constraints, failure behavior and observable acceptance conditions. Investigate high-impact uncertainties before committing to an architecture.
3. **Design:** Simplest adequate stack and modular responsibilities, APIs, persistence, concurrency and trust boundaries. Record actual decisions, not speculative abstractions.
4. **Plan verification:** Name concrete test tools and configured commands for the stack; classify risky changes with [profiles](../docs/RISK-PROFILES.md). Separate mandatory and optional checks. Missing tools block only relevant verification; don't fabricate green CI.
5. **Bootstrap:** Create/reconcile an actual Git repository, README, developer commands, isolated test data and `.acw/project.json`, `.acw/quality-gates.json`, one task file. The CLI may create starter files, never overwrite existing ones.
6. **Prove baseline:** Install/build/typecheck/test only when user-authorized and safe; record genuine output. Test environments must not mutate production.
7. **Exit:** Record exact baseline SHA, open questions, first task, authority and next action. An existing project may adopt incrementally without rewriting unrelated state.
