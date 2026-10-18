# Risk-adaptive execution profiles

Select a task profile from the actual diff, intended behavior and trust boundaries, never solely by agent confidence. Record the trigger and chosen profile in the task.

| Profile | Typical scope | Minimum evidence |
| --- | --- | --- |
| `light` | Text, documentation, strictly visual tweaks with no behavior or privileged effects | Relevant local checks, correct artifact/content, brief diff self-review |
| `standard` | Normal features, APIs, persistence reads, stateful UI, routine fixes | Relevant unit/integration/contract tests, type/build/static checks as configured, full affected-path self-review |
| `critical` | Security/auth/permissions, secrets, destructive or backward-incompatible migrations, cross-user data, money, production-affecting operations, irreversible changes | All `standard` checks plus relevant negative security tests, migration/rollback or recovery checks, side-effect and concurrency review |

**Automatic escalation**: any critical trigger sets minimum `critical`, regardless of small diff size, file extension or estimated complexity. Unknown risk defaults to `standard`; unresolved safety-critical uncertainty defaults to `critical`. Agents may escalate, never auto-waive.

The CLI validates that a task's profile is not less than an explicitly declared `critical_triggers` signal and ensures every required check assigned to that profile exists and passed. It cannot infer all security risks from code, so both checklist inspection and executable checks are necessary.

Profiles determine **additional** checks, not exceptions. If an existing project mandates a scan on all changes, it stays mandatory in `light`. Optional checks may be scheduled for releases, but mandatory checks never become `not_applicable` without a scoped, recorded reason and owner authorization.

Avoid unnecessary expense: run focused tests during increments, full applicable checks at candidate/milestone closure, and long-running stress/mutation/restore checks when relevant and safe. No universal test-count or coverage threshold.
