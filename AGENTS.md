# AGENTS.md

## Role
You are assisting development in VSCode on a Python project derived from pyDcop.

Work conservatively. The human developer remains in control of decisions, architecture, and final changes.

This is a private-use repository. Do not preserve public API compatibility for
its own sake; prefer clear internal names and behavior when the human developer
asks for a change.

## Session continuity
- When a session starts, read `.agent/main-continuity.md` if it exists; if it is large, read only the latest/current-session-relevant section first.

## Project map
- `pydcop/dcop/` — core DCOP model: `dcop.py`, variables/agents in `objects.py`, constraints/relations in `relations.py`, YAML load/dump in `yamldcop.py`.
- `pydcop/algorithms/` — algorithm implementations such as MaxSum, DSA, DPOP, MGM, DBA. Look here for message classes, computation behavior, `GRAPH_TYPE`, `algo_params`, and memory/communication hooks.
- `pydcop/computations_graph/` — graph builders and graph data structures: factor graph, constraints hypergraph, pseudotree, and ordered graph.
- `pydcop/distribution/` — distribution algorithms and distribution objects/yaml format. CLI distribution failures usually involve this package plus `pydcop/commands/distribute.py`.
- `pydcop/infrastructure/` — runtime, orchestration, agents, communication, discovery, computation base classes, and thread/process run helpers.
- `pydcop/commands/` and `pydcop/dcop_cli.py` — CLI command registration and command implementations. `pydcop/pydcop` is the shell wrapper script.
- `pydcop/commands/generators/` — CLI instance generators for graph coloring, meetings, IoT, agents, scenarios, etc.
- `pydcop/replication/` and `pydcop/reparation/` — replication and repair/resilience support.
- `pydcop/utils/` — shared helpers such as simple serialization, expressions, graph utilities, and miscellaneous functions.
- `tests/unit/`, `tests/api/`, `tests/dcop_cli/`, and `tests/instances/` — focused unit tests, public API tests, end-to-end CLI tests, and YAML fixtures.

## Search hints
- CLI output or argument issues: start in `tests/dcop_cli/`, then `pydcop/dcop_cli.py`, then the matching `pydcop/commands/<command>.py`.
- Solve/distribute runtime issues: inspect `pydcop/commands/solve.py`, `pydcop/commands/distribute.py`, `pydcop/infrastructure/run.py`, `pydcop/infrastructure/orchestrator.py`, `pydcop/infrastructure/agents.py`, and `pydcop/infrastructure/communication.py`.
- Algorithm behavior: inspect `pydcop/algorithms/<name>.py` and the corresponding `tests/unit/test_algorithms_<name>.py`.
- Serialization/YAML issues: inspect `pydcop/dcop/yamldcop.py`, `pydcop/utils/simple_repr.py`, and, for process-mode messages, `pydcop/infrastructure/communication.py`.
- Distribution failures: inspect `pydcop/distribution/objects.py`, the selected `pydcop/distribution/<method>.py`, and `tests/unit/test_distribution_<method>.py` when present.

## Core principles
- Make small, targeted changes.
- Do not rewrite entire files unless explicitly asked.
- Do not refactor unrelated code.
- Do not introduce new dependencies without approval.
- Preserve existing behavior unless the task says otherwise.
- Public API exposure is not a concern unless the human developer explicitly
  says otherwise.
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
conda run -n khoihd python -m pytest path/to/test_file.py
```

## Python linting
Use Ruff as the preferred Python linter.

Prefer targeted lint checks first:
```bash
conda run -n khoihd ruff check path/to/file.py
```

For broader checks, use:
```bash
conda run -n khoihd ruff check .
```
