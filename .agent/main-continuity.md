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
- Python 3.11+ / modern dependency compatibility.
- CLI/API stabilization through the Conda env.
- Focused optimization passes for core DCOP algorithms.
- Oracle-style algorithm correctness tests using known DCOP instances and the
  PuLP/GLPK oracle in `tests/utils/dcop_oracle.py`.

## Current Status
- Test-suite stabilization pass completed: the suite is reported passing
  without skipped tests after modernizing legacy tests and benchmark tests.
- Recent fixes covered:
  - `tests/unit/test_agentfw.py`: modernized in-process agent messaging tests.
  - `tests/unit/test_algorithms_mgm2.py`: updated stale MGM2 offer-handling
    tests to match current message storage and offer-count semantics.
  - `pydcop/infrastructure/communication.py` and
    `tests/unit/test_infra_communication.py`: retry messages are now resent
    automatically when missing agents register.
  - `tests/unit/test_dcop_relations.py`: assignment-cost benchmark test now
    works with or without the optional benchmark fixture.
  - `tests/unit/test_replication_path_utils.py`: replication path benchmark
    tests use the current list-of-tuples path table shape.
- Project-wide declaration newline style was normalized: blank lines immediately
  after `def`, `async def`, and `class` declarations were removed.
- Relation optimization in `pydcop/dcop/relations.py` is complete for now.
  Details live in `relation_optimization_steps.txt`.
- Deferred relation items: `assignment_cost()`, `find_optimal()`, and
  `NAryMatrixRelation.__hash__()`.
- High-level optimization tracking lives in `optimization_tracker.md`.
- Python support metadata now declares Python 3.11+ in `setup.py`, README, and
  installation docs.
- DPOP optimization is complete through Step 4 and tracked in
  `dpop_optimization_steps.txt`; Step 5 was intentionally removed/skipped.
- DPOP Steps 1-4 are complete:
  - Baseline DPOP unit/API/Ruff checks were recorded.
  - Constructor constraint filtering now builds a kept list directly and uses
    set disjointness for descendant checks.
  - VALUE forwarding now uses membership checks instead of `KeyError` control
    flow, with coverage for child separator ordering.
  - Priority 4 profiling added `profiling/profile_dpop_utils.py`, including
    fixed and generated cases plus strategy comparison for original,
    pre-convert, ordered, and pre-convert+ordered local joins.
  - Production DPOP now orders local constraints by estimated relation
    footprint/arity after descendant filtering.
  - `_join_local_constraints()` factors the repeated local-constraint join loop
    without changing the points where local constraints are joined.
- `optimization_tracker.md` lists `pydcop/algorithms/dpop.py` as completed.
- DSA optimization is complete and tracked in `dsa_optimization_steps.txt`;
  no further DSA optimization is planned.
- MGM optimization is complete and tracked in `mgm_optimization_steps.txt`;
  `assignment_cost()` and `find_optimal()` remain intentionally excluded from
  optimization based on their relation docstrings.
- MGM2 optimization is complete and tracked in `mgm2_optimization_steps.txt`;
  `_compute_offers_to_send()` now avoids the generic
  `generate_assignment_as_dict()` path by iterating the two domains directly.
- `optimization_tracker.md` now lists only completed items under Status and
  records remaining algorithm candidates under Current Next Step.

## Next Steps
- No active optimization pass is planned. Pick one remaining algorithm at a
  time and create a focused `*_optimization_steps.txt` plan before changing it.
- Remaining algorithm candidates:
  - `pydcop/algorithms/adsa.py`
  - `pydcop/algorithms/amaxsum.py`
  - `pydcop/algorithms/dba.py`
  - `pydcop/algorithms/dsatuto.py`
  - `pydcop/algorithms/gdba.py`
  - `pydcop/algorithms/maxsum.py`
  - `pydcop/algorithms/maxsum_dynamic.py`
  - `pydcop/algorithms/mixeddsa.py`
  - `pydcop/algorithms/ncbb.py`
  - `pydcop/algorithms/syncbb.py`
- If revisiting completed modules, prefer a new focused plan rather than
  reviving removed or intentionally deferred polish.
- Focused checks already recorded in `optimization_tracker.md` include:
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_amaxsum.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dba.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsatuto.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_gdba.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_maxsum.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_ncbb.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_syncbb.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
- Be careful with DPOP join order, pre-conversion to `NAryMatrixRelation`, and
  helper extraction: these can affect intermediate UTIL dimensions, memory, and
  tie behavior.
- Consider `profiling/profile_dpop_utils.py --case generated --strategy all`
  when evaluating future DPOP join/projection changes.
- Leave relation helper changes alone unless profiling gives a specific reason.

## Important Paths
- `pydcop/algorithms/dpop.py` — DPOP implementation.
- `pydcop/algorithms/dsa.py` — completed DSA optimization pass.
- `pydcop/algorithms/mgm.py` — completed MGM optimization pass.
- `pydcop/algorithms/mgm2.py` — completed MGM2 optimization pass.
- `tests/unit/test_algorithms_dpop.py` — DPOP message-flow unit tests.
- `tests/api/test_api_solve_dpop.py` — DPOP API oracle checks.
- `dpop_optimization_steps.txt` — current DPOP optimization plan.
- `dsa_optimization_steps.txt` — completed DSA optimization plan.
- `mgm_optimization_steps.txt` — completed MGM optimization plan.
- `mgm2_optimization_steps.txt` — completed MGM2 optimization plan.
- `optimization_tracker.md` — high-level optimization tracker.
- `pydcop/dcop/relations.py` — optimized relation primitives.
- `relation_optimization_steps.txt` — completed relation optimization plan.
- `tests/utils/known_instances.py` — shared known DCOP cases.
- `tests/utils/dcop_oracle.py` — PuLP/GLPK DCOP oracle.

## Open Questions
- What is the primary long-term execution path: CLI, library API, or both?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
