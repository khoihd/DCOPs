# Main Continuity

## Project
Name: DCOP  
Origin: Derived from pyDcop (Orange-OpenSource)  
Repo Type: Private continuation  
Status: Early-stage stabilization & exploration  

## Current Goal
Stabilize and understand the existing codebase before making structural changes.  
Prepare for incremental modernization (Python version, dependencies, tooling).

## Current Focus Area
- Python 3.11 / modern dependency compatibility
- CLI end-to-end tests and local virtualenv execution
- Core DCOP algorithms and process/thread execution flow

## Key Decisions
- Work conservatively: no large refactors without explicit approval
- Preserve original behavior unless explicitly changing it
- Keep full commit history (no squash/rewrite)
- Do NOT maintain upstream remote (detached from original repo)
- Rename project identity to "DCOP" (not pyDcop)

## Constraints
- Minimal diffs only
- No large-scale renaming or restructuring yet
- No new dependencies without approval
- Avoid touching multiple modules in one change
- Maintain compatibility with existing code until upgrade plan is defined
- Prefer the project-local virtualenv (`./.venv/bin/python`, `./.venv/bin/pip`,
  `./.venv/bin/pydcop`) over Conda or commands resolved from ambient `PATH`.

## Recent Changes
- Stabilized several Python 3.11 / dependency compatibility issues:
  - `collections.Mapping` -> `collections.abc.Mapping`
  - NumPy 2 `ndarray.itemset` removal
  - PuLP / GLPK command import compatibility
  - Iterable / YAML variable list checks
- Updated CLI test helpers to use the active local venv instead of Conda or
  ambient `PATH`.
- Fixed distribute CLI compatibility with distribution algorithms that do not
  accept a `timeout` keyword.
- Fixed process-mode solve tests by preserving synchronous message `cycle_id`
  across HTTP serialization.
- Made the 10-variable graph-coloring solve fixture deterministic with valid
  initial values for MGM.
- Installed Ruff in the local venv (`./.venv/bin/ruff`).

## Next Steps
- Continue targeted CLI/API test stabilization with `./.venv/bin/python`.
- Review remaining CLI helpers for bare `pydcop` usage before running those
  suites broadly.
- Review dependency list and decide supported Python/dependency versions.
- Identify critical modules:
  - algorithm implementations
  - agent/distribution logic
  - communication/simulation layer
- Decide whether generated solver artifacts such as `ilp_compref-pulp.out`
  should be ignored.

## Known Issues
- Original codebase targeted older Python versions (README says >=3.6); current
  local stabilization is on Python 3.11 with modern dependencies.
- CI (Travis) is outdated
- Dependencies may be outdated or unpinned
- Documentation may reference deprecated tooling or workflows
- `ilp_compref-pulp.out` is currently an untracked generated file and has been
  intentionally left untouched.

## Important Files
- README.md — original project description (needs adaptation)
- setup.py / pyproject.toml — packaging and dependencies
- pydcop/ (main package) — core logic
- tests/ — validation and behavior reference
- docs/ — may contain useful architecture insights

## Open Questions
- What is the primary execution path? (CLI vs library usage)
- Which modules are safe to modify first?
- What is the minimal supported Python version going forward?
- Should package/module names be renamed later?
- Which parts of the system are actively useful vs legacy?

## Notes for Agent
- Always read this file before starting work
- Use local venv commands explicitly: `./.venv/bin/python`, `./.venv/bin/pydcop`,
  `./.venv/bin/ruff`, and `./.venv/bin/python -m pip`.
- Only modify explicitly mentioned files
- Ask before touching core modules (e.g., algorithm logic, messaging)
- Prefer inspection and explanation before modification
- Suggest small, incremental improvements only
- Do not refactor for style alone
- Highlight uncertainty instead of guessing

## Working Style
- Human-in-the-loop (approval required for non-trivial changes)
- Prefer “analyze → propose → confirm → edit”
- Keep outputs concise and focused
