# Contributing

Contributions should remain harness-independent, dependency-light and friendly to a single coding agent. Propose changes with acceptance criteria, minimal implementation, runnable tests and a self-review describing risks and evidence.

Before a pull request:

```sh
python3 -B tools/acw.py package .
python3 -B -m unittest discover -s tests -v
```

Keep documentation links relative; avoid private filesystem paths, vendor-specific invocation assumptions, credentials, fake verification reports and redundant policy copies. If modifying a schema, update templates, validator tests and version documentation together.

No second reviewer agent is required by this project. The contributor reviews its own changes; maintainers control merge permissions. Repo branch protection and workflows remain subject to owner configuration.
