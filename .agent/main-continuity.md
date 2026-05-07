# Main Continuity

## Project
- DCOP is a private continuation derived from Orange-OpenSource pyDcop.
- Current goal: stabilize and understand the codebase before structural
  modernization.
- Work conservatively: small targeted changes, behavior preserved by default,
  no new dependencies or broad API/package refactors without approval.
- Keep original BSD 3-Clause attribution intact.

## Environment
- Use the `khoihd` Conda environment explicitly:
  - `conda run -n khoihd python ...`
  - `conda run -n khoihd python -m pytest ...`
  - `conda run -n khoihd ruff check ...`
  - `conda run -n khoihd pydcop ...`
- The project is installed editable in `khoihd`; pytest, Ruff, coverage, PuLP,
  and websocket-server are installed there.
- Avoid bare `python`, `pytest`, or `pydcop` unless the shell is known to be in
  the intended Conda env.

## Current State
- Python support metadata declares Python 3.11+ in setup/docs.
- Test-suite stabilization was completed earlier, including modernized legacy
  tests, communication retry behavior, benchmark compatibility, and replication
  path benchmark shape updates.
- Project-wide declaration newline style was normalized.
- Archived optimization tracking lives in
  `optimization_archive/optimization_tracker.md`.
- All algorithm candidates previously listed there now have focused
  optimization passes and file-specific notes.

## Completed Optimization Passes
- Relations: `pydcop/dcop/relations.py`,
  `optimization_archive/relation_optimization_steps.txt`.
- Algorithms: DPOP, DSA, MGM, MGM2, ADSA, MaxSum/AMaxSum, DBA, DSA tutorial,
  GDBA, Dynamic MaxSum, MixedDSA, NCBB, and SyncBB.
- Details live in:
  - `optimization_archive/dpop_optimization_steps.txt`
  - `optimization_archive/dsa_optimization_steps.txt`
  - `optimization_archive/mgm_optimization_steps.txt`
  - `optimization_archive/mgm2_optimization_steps.txt`
  - `optimization_archive/adsa_optimization_steps.txt`
  - `optimization_archive/maxsum_optimization_steps.txt`
  - `optimization_archive/dba_optimization_steps.txt`
  - `optimization_archive/dsatuto_optimization_steps.txt`
  - `optimization_archive/gdba_optimization_steps.txt`
  - `optimization_archive/maxsum_dynamic_optimization_steps.txt`
  - `optimization_archive/mixeddsa_optimization_steps.txt`
  - `optimization_archive/ncbb_optimization_steps.txt`
  - `optimization_archive/syncbb_optimization_steps.txt`

## Durable Caveats
- Leave relation helpers `assignment_cost()`, `find_optimal()`, and
  `NAryMatrixRelation.__hash__()` alone unless profiling gives a specific
  reason.
- DPOP join order, pre-conversion to `NAryMatrixRelation`, and helper
  extraction can affect intermediate UTIL dimensions, memory, and tie behavior.
  Use `profiling/profile_dpop_utils.py --case generated --strategy all` before
  future DPOP join/projection changes.
- NCBB search-phase stubs remain incomplete; the completed NCBB pass only
  optimized initialization-phase behavior and nearby dispatch fixes.
- If revisiting completed modules, start a new focused plan rather than
  extending old optimization notes casually.

## Next Steps
- No active optimization pass is planned.
- `todo.md` includes a broader item to optimize commonly used files with
  overheads; treat that as a new focused planning pass.
- For any new optimization, pick one file or subsystem, update/create a focused
  `*_optimization_steps.txt` plan, then run targeted tests and Ruff.
- Focused checks are listed in
  `optimization_archive/optimization_tracker.md`; common examples:
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_syncbb.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
  - `conda run -n khoihd ruff check path/to/file.py path/to/test.py`

## Important Paths
- Core model/YAML: `pydcop/dcop/`.
- Algorithms: `pydcop/algorithms/`.
- Computation graphs: `pydcop/computations_graph/`.
- Runtime/agents/communication: `pydcop/infrastructure/`.
- CLI: `pydcop/commands/`, `pydcop/dcop_cli.py`, `pydcop/pydcop`.
- Tests: `tests/unit/`, `tests/api/`, `tests/dcop_cli/`,
  `tests/instances/`.
- Oracle/known cases: `tests/utils/known_instances.py`,
  `tests/utils/dcop_oracle.py`.
- Archived optimization notes: `optimization_archive/`.

## Open Questions
- What is the primary long-term execution path: CLI, library API, or both?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
