# Quick start

## For a human operator

1. Obtain the repository on your machine; verify Python 3.10+ and Git.
2. Run `python3 -B tools/acw.py package .` and the bundled unit tests.
3. Initialize a **separate application** repository with `python3 -B tools/acw.py init /path/to/app`. Existing files are never overwritten.
4. Edit `.acw/project.json`: name, mode (`solo` or `github`), owner/authority and optional required project files.
5. Edit `.acw/quality-gates.json`: replace the demonstration commands with **real stack-specific** commands; identify which checks are required by each risk profile. Keep production mutation out of tests.
6. Run `python3 -B tools/acw.py project /path/to/app`. Start a task from `.acw/tasks/TASK-EXAMPLE.json`, rename it and fill acceptance conditions.
7. Tell the coding agent to follow [WORKFLOW](../WORKFLOW.md), read the project state and activate [task-execution](../skills/task-execution/SKILL.md).
8. Before closing the task, run the configured gates against a known candidate and validate the task.

Sample instructions to an agent (substitute actual repository paths):

```text
Follow the Autonomous Coding Workflow located at <workflow-directory>.
Read WORKFLOW.md, the relevant SKILL.md and procedure.
Work in <application-repository>. Read .acw/project.json, the current task
record, repository instructions and actual Git state before acting.
Use one agent, evidence-backed self-review and required project quality gates.
Never start another agent or assume deployment/merge authority.
```

## For an agent without native skills

Read the Markdown files directly. `SKILL.md` is a human/agent-readable phase guide, not executable code. A runtime without a skill registry loses no fundamental workflow capability.

## Task execution example

```sh
python3 -B /path/to/acw/tools/acw.py project /path/to/app
python3 -B /path/to/acw/tools/acw.py task /path/to/app/.acw/tasks/TASK-EXAMPLE.json --project /path/to/app
# After acceptance and appropriate isolated test setup:
python3 -B /path/to/acw/tools/acw.py run /path/to/app --profile standard --output /path/to/app/.acw/evidence/checks.json
```

The `run` command executes **only** commands explicitly defined by the user in the project's gate file. It does not select or install tools. A successful `run` alone does not complete a task: examine actual assertions, current SHA, candidate cleanliness and self-review.
