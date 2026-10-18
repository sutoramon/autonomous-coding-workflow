# Autonomous Coding Workflow (ACW)

**A harness-independent, single-agent software development workflow with verifiable quality gates.**

ACW guides a coding agent through planning, implementation, testing, self-review, recovery, and release. Its core workflow is independent of agent runtimes and hosted services. A skill-aware agent can use the four `SKILL.md` files; any agent with file access can follow the same Markdown instructions directly.

## What you get

- Four phase skills: [onboarding](skills/project-onboarding/SKILL.md), [task execution](skills/task-execution/SKILL.md), [self-review](skills/self-review/SKILL.md), and [release closeout](skills/release-closeout/SKILL.md).
- Deterministic **light / standard / critical** risk profiles; critical signals cannot be downgraded by an AI score.
- Evidence-bound checks and truthful task state. A failed, missing, skipped, stale, or timed-out required check is never a pass.
- Recovery from Git plus one task record, without relying on chat history.
- Standard-library Python CLI for initialization, validation, and execution of project-defined checks.
- An optional GitHub Actions example; local and GitHub operation share the same rules.

## Requirements

Python 3.10+, Git 2.x, and the tools your project already needs. No pip dependencies. The core Markdown instructions work even without Python. A GitHub account, CI, or native skill registry is **not required**.

## Quick start

```sh
git clone <your-repository-url> autonomous-coding-workflow
cd autonomous-coding-workflow
python3 -B tools/acw.py package .
python3 -B -m unittest discover -s tests -v

# Run on a separate application repository (not on ACW itself):
python3 -B tools/acw.py init /path/to/your-app
# Edit /path/to/your-app/.acw/project.json and quality-gates.json
python3 -B tools/acw.py project /path/to/your-app
```

Start with [the full quick-start guide](docs/QUICKSTART.md). Your agent should read [WORKFLOW.md](WORKFLOW.md) once per new context, then the phase skill and its linked procedure. If native skills are unavailable, point the agent directly at the files. Native registration is optional.

## Modes

| | Solo (default) | GitHub (optional) |
| --- | --- | --- |
| Agent count | 1 | 1 |
| Git | Local commits/checkpoints | Branch + PR + commits |
| Review | Same-agent evidence-backed self-review | Same-agent review + required CI |
| Merge | Not required | Only under configured authority |
| Task Done | Applicable local checks, review, evidence, documentation | Also verified merge / exact merged SHA checks when configured |
| Recovery | Git + task record | Git + task + actual PR/CI state |

See [workflow rules](WORKFLOW.md), [risk profiles](docs/RISK-PROFILES.md), [engineering standards](docs/ENGINEERING-STANDARDS.md), [example task](docs/EXAMPLE-TASK.md), [CLI and evidence](docs/VERIFICATION.md), and [security](docs/SECURITY.md).

## Scope and explicit non-goals

ACW defines a **method** and executes configured project checks. It is not an orchestration daemon, auto-resume service, code-generation model, CI provider, compiler, security scanner, or guarantee of flawless output. It never silently grants merge, deploy, delete, or production authority. It uses real, project-specific tools for actual verification.

## License and contribution

[MIT license](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md). This public distribution is an adapted, streamlined derivative of a privately authored development-workflow checklist and package; it intentionally excludes private paths, project state, credentials and vendor-specific agent instructions.
