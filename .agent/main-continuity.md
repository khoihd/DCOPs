# Main Continuity

## Project
- Name: DCOP
- Origin: private continuation derived from Orange-OpenSource pyDcop.
- Current goal: stabilize and understand the codebase before structural
  modernization.

## Working Rules
- Work conservatively; keep changes small and targeted.
- Preserve behavior unless a task explicitly asks to change it.
- Do not introduce dependencies, rename public APIs, or make broad refactors
  without approval.
- Keep original BSD 3-Clause attribution intact.

## Environment
- Use the `khoihd` Conda environment explicitly:
  - `conda run -n khoihd python`
  - `conda run -n khoihd python -m pytest ...`
  - `conda run -n khoihd ruff check ...`
  - `conda run -n khoihd pydcop ...`
- The project is installed editable in `khoihd`; pytest, Ruff, coverage, PuLP,
  and websocket-server are installed there.
- Avoid bare `pytest`, `python`, or `pydcop` unless the shell is known to be in
  the intended Conda env.

## Current Focus
- Python 3.11 / modern dependency compatibility.
- CLI/API stabilization through the Conda env.
- Core DCOP algorithms, especially DPOP.
- Oracle-style algorithm correctness tests using known DCOP instances and the
  PuLP/GLPK oracle in `tests/utils/dcop_oracle.py`.

## Current Status
- Relation optimization in `pydcop/dcop/relations.py` is complete for now.
  Details live in `relation_optimization_steps.txt`.
- Deferred relation items: `assignment_cost()`, `find_optimal()`, and
  `NAryMatrixRelation.__hash__()`.
- High-level optimization tracking lives in `optimization_tracker.md`.
- DPOP optimization is in progress and tracked in `dpop_optimization_steps.txt`.
- DPOP Steps 1-3 are complete:
  - Baseline DPOP unit/API/Ruff checks were recorded.
  - Constructor constraint filtering now builds a kept list directly and uses
    set disjointness for descendant checks.
  - VALUE forwarding now uses membership checks instead of `KeyError` control
    flow, with coverage for child separator ordering.
- Current next item: DPOP Priority 4, relation join/projection phase review.

## Next Steps
- If continuing DPOP optimization, start at `dpop_optimization_steps.txt`
  Priority 4.
- Be careful with DPOP Step 4: join order, pre-conversion to
  `NAryMatrixRelation`, and helper extraction can affect intermediate UTIL
  dimensions, memory, and tie behavior.
- Prefer measurement and oracle checks before changing DPOP join/projection
  behavior.
- Baseline DPOP checks for meaningful DPOP changes:
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
  - `conda run -n khoihd python -m pytest tests/api/test_api_solve_dpop.py`
  - `conda run -n khoihd ruff check pydcop/algorithms/dpop.py tests/unit/test_algorithms_dpop.py`
- Consider `tests/dcop_cli/test_solve.py` only for DPOP changes that affect CLI
  solve/distribution behavior or message serialization.
- Leave relation helper changes alone unless profiling gives a specific reason.

## Important Paths
- `pydcop/algorithms/dpop.py` — DPOP implementation.
- `tests/unit/test_algorithms_dpop.py` — DPOP message-flow unit tests.
- `tests/api/test_api_solve_dpop.py` — DPOP API oracle checks.
- `dpop_optimization_steps.txt` — current DPOP optimization plan.
- `optimization_tracker.md` — high-level optimization tracker.
- `pydcop/dcop/relations.py` — optimized relation primitives.
- `relation_optimization_steps.txt` — completed relation optimization plan.
- `tests/utils/known_instances.py` — shared known DCOP cases.
- `tests/utils/dcop_oracle.py` — PuLP/GLPK DCOP oracle.

## Open Questions
- What is the primary long-term execution path: CLI, library API, or both?
- What minimum Python/dependency versions should be supported?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
