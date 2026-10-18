# Autonomous Coding Workflow — Normative Rules

Version: **1.0.0**. Applies to any coding agent with access to project files and tools. This document owns shared policy; the phase skills route work; procedures describe execution. **MUST** indicates a mandatory rule within the currently authorized scope.

## 1. Authority and boundaries

Follow platform and user instructions, repository instructions, and project authorization. This workflow cannot grant permissions. The executing agent owns implementation, verification, self-review, and authorized release actions.

Default mode is `solo`. Optional `github` mode adds PR and actual CI/merge evidence. Only the project owner grants merge/deploy authority. No automatic remote publishing.

The current project file `.acw/project.json` defines mode, repository instructions and authority. Its gate file `.acw/quality-gates.json` defines actual project commands. The current task record owns task state; Git proves source identity; process/CI logs prove checks; runtime inspection proves deployment. Do not create parallel authoritative status ledgers.

## 2. First read and risk classification

At session start or after interruption read: applicable repository instructions; project configuration; the current task record; latest Git status/log; relevant architecture, code and tests. Select the first incomplete phase from actual evidence, not the last chat message.

Determine risk profile using [risk rules](docs/RISK-PROFILES.md). Deterministic critical triggers (e.g. credentials, permissions, destructive migrations, production state, money or irreversible effects) set a **minimum** of `critical`. Unknown risk is `standard` until assessed; if a critical trigger cannot be ruled out, treat it as critical. An agent may escalate but may not downgrade a trigger.

A tool suggestion, confidence score or narrative judgement cannot waive a required gate.

## 3. Plan and implement

Write observable acceptance conditions before changing behavior. Choose the smallest coherent work item; inspect existing code and tests before designing a replacement. For existing code prefer repair over speculative rewrites. Document consequential design decisions, data migrations and contracts.

Use bounded implementation increments: code + meaningful tests + focused check + coherent Git checkpoint. For bugs reproduce behavior where feasible before fixing. Include normal, failure, denial, retry, concurrency and recovery paths as relevant. Keep modules cohesive; avoid unrelated abstractions, hidden state, uncontrolled retries and silent errors. Never overwrite unrelated working-tree changes or reuse a concurrent writer's workspace.

Detailed expectations: [engineering standards](docs/ENGINEERING-STANDARDS.md). Targets (not universal pass/fail gates): handwritten production files ~300 physical lines; functions ~40 lines; cyclomatic complexity ~10. Investigate larger units by responsibility; don't split simply to satisfy numbers. Enforce numerical limits only with an actual configured analyzer and explicit project acceptance. Avoid shipping placeholders represented as finished features.

## 4. Verification

Only **actual** executed checks count. Select capabilities (types, formatting, static analysis, secrets, dependencies, unit, integration, E2E, accessibility, performance, migration, recovery) by project risk and changed behavior. Bind commands and required profiles in `.acw/quality-gates.json`. The CLI runs explicitly configured commands; no scanner is magically installed by a template.

A check result records exact source SHA, dirty status and diff identity when relevant, command, exit code, timestamps, duration, timeout, tool identity, and log reference. Working-tree results are **development evidence**, not clean-commit or CI proof. After source changes, refresh impacted checks on the current candidate; don't relabel stale results. Missing/unavailable mandatory tools mean `blocked`, not `passed`.

Do not treat low test counts, zero discovered tests or green aggregate coverage as proof of acceptance. An appropriate test must fail when relevant behavior is broken. Full review scope is risk-adaptive, but configured mandatory checks cannot be skipped by selecting a light task label.

Tests must use isolated data, fake/safe external targets, and no production side effects by default. Failures and flaky outcomes remain visible.

## 5. Self-review

Before completion the agent reads acceptance criteria, the full candidate diff, surrounding affected code, contracts, tests, logs, and documentation. Review correctness, security, data integrity, concurrency, cancellation, cleanup, performance, maintainability, forbidden effects and outward publication data. Record findings, repairs and final SHA. For medium/high risk, prefer a fresh-context read of evidence without previous implementation justifications, when supported. Fresh-context review helps reduce confirmation bias but does not replace required executable checks.

No self-review may override a failed or absent mandatory executable gate. If a defect is repaired, rerun affected checks and update candidate identity. Audit the **whole project** at each milestone boundary, not just the latest diff.

## 6. Completion states

Tasks use `backlog`, `in_progress`, `in_review`, `done`, `cancelled`. Blockers are separate and may occur in an open state. `done` requires acceptance evidence, applicable required checks passed for the correct source identity, current self-review, documentation updates, preserved source and authorized release steps where applicable.

In `solo` mode a verified local commit/checkpoint can close a task; a PR, merge and external CI are not required unless explicitly configured. In `github` mode require actual PR and exact head/merged-SHA evidence at the configured gate; a local commit is not a remote merge. Human-reserved merge/deploy must remain pending and never be simulated.

## 7. Recovery and safety

When execution stops or context is compacted, inspect live jobs/processes and source state before retrying. **Do not start parallel writers**: if another run may be active, stop and obtain a reliable state check. Match the existing task, branch, worktree, PR, artifacts and checkpoint. Avoid replaying any non-idempotent operation until its outcome is known.

The task record includes the concrete next action, current revision and outstanding validation. It must not duplicate Git or a CI server's authoritative data. Checkpoint Git only after reviewing content for secrets and correctness; retain uncommitted work safely. A new session follows [recovery](procedures/05-recovery.md) and the current phase.

A workflow file does not implement orchestration, liveness checks or automatic process restarts. These are responsibilities of the chosen runtime; don't claim reliability you cannot prove.

## 8. Release and milestone closure

Never equate build success, merge, deployment and healthy runtime. Confirm actual target identity and permissions; verify migrations/backups where applicable; test installed behavior. Clean up only resources owned by the task after work is preserved. Reject ambiguous cleanup rather than deleting unknown data.

At **every milestone**, run [whole-project audit](procedures/06-milestone-audit.md): feature vs behavior, full relevant tests, security/data/recovery, architecture, documentation, source inventory and records. Log findings and unresolved blockers.

## 9. Skills and operating profiles

Choose one [phase skill](skills/task-execution/SKILL.md) based on actual state; load only its procedure. See [onboarding](skills/project-onboarding/SKILL.md), [self-review](skills/self-review/SKILL.md), [release](skills/release-closeout/SKILL.md). Never dump the entire workflow/checklist into every prompt. Use [evidence rules](docs/VERIFICATION.md) and the current task record. Native skill registration is optional; direct Markdown reading is sufficient.
