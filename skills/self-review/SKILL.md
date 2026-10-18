---
name: self-review
description: Review candidate changes and complete whole-project milestone audits using requirements, source diffs, tests, and verification evidence.
---
# Self Review

Read [core policy](../../WORKFLOW.md), [review procedure](../../procedures/03-self-review.md), [verification](../../docs/VERIFICATION.md), and for milestone boundaries [full audit](../../procedures/06-milestone-audit.md).

## Modes
- **Candidate:** Inspect the full change, surrounding paths and acceptance evidence.
- **Milestone:** Inspect the *whole project*, not just a diff, and validate feature interactions, documentation and quality gates.

## Review contract
Read requirements, the candidate diff, and verification evidence before revisiting implementation rationale. A fresh context can help reduce confirmation bias. Findings must name severity, location, observed risk, desired repair, and verification. Check security and denied operations, data lifecycle, concurrency/restart, failure handling, test strength, accessibility where applicable, code cohesion, docs and outward publication hygiene.

Tests and static analyzers provide evidence to inspect; they do not replace a review of the relevant code and behavior. Do not override failing, missing or stale required checks; do not self-approve a requested exception. Following fixes, rerun affected checks and revalidate SHA and evidence.

## Exit
Current source-bound findings and an explicit `passed`, `changes_requested` or `blocked` verdict. Pass only when acceptance and applicable mandatory gates hold.
