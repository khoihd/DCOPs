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
- Targeted Ruff cleanup and unit-test modernization in legacy modules
- Focused cleanup in distribution, infrastructure, and replication modules
- One-file-at-a-time Ruff cleanup across DCOP core, computation graphs,
  algorithms, commands, and generators

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
- Prefer the `khoihd` Conda environment explicitly (`conda run -n khoihd
  python`, `conda run -n khoihd python -m pip`, `conda run -n khoihd
  pydcop`) over the project-local virtualenv or commands resolved from
  ambient `PATH`.

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
- Replaced deprecated `numpy.matrix` usage in the GDBA unit test with
  `numpy.array`, removing the NumPy pending deprecation warning.
- Stabilized the NCBB toy pseudotree fixture by ordering variables so the
  current highest-degree root heuristic selects the intended root in an A/D tie.
- Ignored generated PuLP `.out` artifacts with the existing PuLP ignore rules.
- Installed Ruff in the local venv (`./.venv/bin/ruff`).
- Added an architecture/search map to `AGENTS.md` to speed up future targeted
  inspection.
- Ran a series of small targeted Ruff cleanups in docs, `__init__.py` modules,
  core algorithms, and selected unit tests, committing each change separately.
- Modernized several legacy unit-test files by replacing skipped/placeholding
  tests with real assertions and current setup paths, especially around DSA,
  DPOP, DCOP relations, computation graph objects, infrastructure discovery,
  replication path utilities, and Ising/DUSC helpers.
- Removed stale or non-behavioral tests such as an unfinished replication-path
  test and a dict-vs-list benchmark, and tightened remaining assertions to
  check behavior rather than implementation accidents.
- Improved DBA and AMAX-SUM unit tests, plus the dynamic Max-Sum graph coloring
  integration test, with targeted Ruff/pytest checks and separate commits.
- Reviewed and fixed `pydcop/replication/objects.py`, especially
  `ReplicaDistribution` lookup/copy behavior, then committed the targeted
  replication object cleanup.
- Continued one-file-at-a-time Ruff cleanup and commits across utility,
  replication, infrastructure, and distribution modules:
  `simple_repr.py`, `expressionfunction.py`, `dist_ucs_hostingcosts.py`,
  `orchestrator.py`, `computations.py`, `agents.py`, `oilp_secp_cgdp.py`,
  `oilp_secp_fgdp.py`, `oilp_cgdp.py`, distribution `objects.py`,
  `ilp_compref_fg.py`, `ilp_compref.py`, `heur_comhost.py`, and `gh_cgdp.py`.
- Continued the isolated Ruff cleanup series with 17 additional commits, each
  limited to one requested file:
  `pydcop/distribution/adhoc.py`, `pydcop/dcop/relations.py`,
  `pydcop/dcop/objects.py`, `pydcop/computations_graph/ordered_graph.py`,
  `pydcop/computations_graph/objects.py`,
  `pydcop/computations_graph/factor_graph.py`,
  `pydcop/computations_graph/constraints_hypergraph.py`,
  `pydcop/commands/solve.py`, `pydcop/algorithms/mgm2.py`,
  `pydcop/commands/orchestrator.py`, `pydcop/algorithms/mixeddsa.py`,
  `pydcop/commands/generators/smallworld.py`,
  `pydcop/commands/consolidate.py`,
  `pydcop/commands/generators/agents.py`, `pydcop/commands/generate.py`,
  `pydcop/commands/generators/secp.py`, and
  `pydcop/commands/generators/iot.py`.
- These Ruff fixes were mostly mechanical `E721`, `E741`, `E402`, `F841`,
  and `E722` cleanups. Equality checks were kept as exact-class comparisons
  using `type(...) is not ...` where that preserved existing semantics.
- Targeted verification was run for each file when a focused suite existed,
  including relation/object tests, computation graph tests, solve CLI tests,
  MGM2 tests, generator tests, and smoke checks for files without dedicated
  tests.
- Recent local history before this continuity update included 17 commits ahead
  of `origin/main`, from `e6fdbfa Fix adhoc distribution Ruff issue` through
  `eea8507 Fix IoT generator Ruff issue`.
- Switched the local development default from `.venv` to the `khoihd` Conda
  environment. Installed the project editable in that environment along with
  pytest, Ruff, coverage, PuLP, and websocket-server. Updated `Makefile`,
  `AGENTS.md`, and dependency constraints to use or document
  `conda run -n khoihd ...`.

## Next Steps
- Continue targeted CLI/API test stabilization with
  `conda run -n khoihd python`.
- Continue improving remaining legacy unit tests one file at a time, with
  targeted Ruff and pytest checks before each commit.
- Continue one-file Ruff cleanup only when explicitly requested, keeping each
  cleanup isolated and committed separately.
- Review remaining CLI helpers for bare `pydcop` usage before running those
  suites broadly.
- Review dependency list and decide supported Python/dependency versions.
- Identify critical modules:
  - algorithm implementations
  - agent/distribution logic
  - communication/simulation layer
- Continue separating stale test assumptions from algorithm bugs, especially in
  older pseudotree/NCBB/DPOP-related tests.

## Known Issues
- Original codebase targeted older Python versions (README says >=3.6); current
  local stabilization is on Python 3.11 with modern dependencies.
- CI (Travis) is outdated
- Dependencies may be outdated or unpinned
- Documentation may reference deprecated tooling or workflows

## Important Files
- README.md — original project description (needs adaptation)
- setup.py / pyproject.toml — packaging and dependencies
- pydcop/ (main package) — core logic
- tests/ — validation and behavior reference
- docs/ — may contain useful architecture insights
- AGENTS.md — repo instructions plus compact project map and search hints

## Open Questions
- What is the primary execution path? (CLI vs library usage)
- Which modules are safe to modify first?
- What is the minimal supported Python version going forward?
- Should package/module names be renamed later?
- Which parts of the system are actively useful vs legacy?

## Notes for Agent
- Always read this file before starting work
- Use the `khoihd` Conda environment explicitly: `conda run -n khoihd python`,
  `conda run -n khoihd pydcop`, `conda run -n khoihd ruff`, and
  `conda run -n khoihd python -m pip`.
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
