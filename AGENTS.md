# AGENTS.md

## Role
You are assisting development in VSCode on a Python project derived from pyDcop.

Work conservatively. The human developer remains in control of decisions, architecture, and final changes.

## Session continuity
- When a session starts, read `.agent/main-continuity.md` if it exists; if it is large, read only the latest/current-session-relevant section first.

## Core principles
- Make small, targeted changes.
- Do not rewrite entire files unless explicitly asked.
- Do not refactor unrelated code.
- Do not introduce new dependencies without approval.
- Preserve existing behavior unless the task says otherwise.
- Prefer simple, readable solutions over clever ones.
- Keep explanations concise.

## Token efficiency
- Read only files directly relevant to the task.
- Prefer targeted `rg`, `sed -n`, and `git diff -- path` commands over broad file reads.
- Avoid scanning the whole repository unless requested.
- Summarize findings briefly; do not paste long command output unless asked.
- When proposing changes, reference file paths and line/function names.
- Use diffs or focused snippets, not full-file rewrites.
- Ask before analyzing large directories, generated files, logs, or vendored code.

## Workflow
Before editing:
1. Identify the likely target files.
2. Explain the intended change briefly.
3. Wait for confirmation if the change affects architecture, public APIs, dependencies, or many files.

When editing:
1. Change the smallest reasonable section.
2. Preserve formatting style already used in the file.
3. Keep compatibility with the project’s supported Python versions unless told otherwise.
4. Add or update tests only where directly relevant.

After editing:
1. Summarize what changed.
2. Mention tests run, or say if none were run.
3. Note any risks or follow-up items.

## Safety rules
Do not:
- delete branches, files, or large blocks of code without approval
- change licensing or attribution text unless explicitly asked
- modify secrets, credentials, or deployment settings without approval
- perform broad formatting changes
- rename packages, modules, or public APIs without approval

## Testing
Prefer targeted tests first.

Use:
```bash
pytest path/to/test_file.py
```

## Python linting
Use Ruff as the preferred Python linter.

Prefer targeted lint checks first:
```bash
ruff check path/to/file.py
```

For broader checks, use:
```bash
ruff check .
```
