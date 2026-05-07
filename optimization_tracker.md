# Optimization Tracker

This file tracks optimization work by source file. Keep detailed, file-specific
plans in separate notes when the work becomes large.

## Completed

### pydcop/dcop/relations.py

Status: optimized and reviewed.

Detailed plan:
- `relation_optimization_steps.txt`

Recent verification used:
- `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_base.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
- `conda run -n khoihd python -m pytest tests/unit/test_dcop_lp_oracle.py`
- `conda run -n khoihd ruff check pydcop/dcop/relations.py tests/unit/test_dcop_relations.py`

### pydcop/algorithms/dpop.py

Status: optimized through Step 4; Step 5 intentionally skipped.

Detailed plan:
- `dpop_optimization_steps.txt`

Recent verification used:
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
- `conda run -n khoihd python -m pytest tests/api/test_api_solve_dpop.py`
- `conda run -n khoihd python -m pytest tests/dcop_cli/test_solve.py`
- `conda run -n khoihd ruff check pydcop/algorithms/dpop.py`

## Future Candidates

### pydcop/algorithms/dsa.py

Status: first focused pass complete.

Detailed plan:
- `dsa_optimization_steps.txt`

Recent verification used:
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd ruff check pydcop/algorithms/dsa.py tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd ruff check profiling/profile_dsa_evaluate_cycle.py`

Notes:
- Fixed exact-neighbor memory accounting for similarly-prefixed variable names.
- Avoided repeated assignment copies in DSA-B violated-constraint checks.
- Added `profiling/profile_dsa_evaluate_cycle.py`; sampled profiles point at
  `find_optimal()` / relation evaluation as the main `evaluate_cycle()` cost.

### pydcop/algorithms/mgm.py

Status: first focused pass complete.

Detailed plan:
- `mgm_optimization_steps.txt`

Recent verification used:
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd ruff check pydcop/algorithms/mgm.py tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd python -m pytest tests/api/test_api_solve.py tests/dcop_cli/test_solve.py -k mgm`

Notes:
- Fixed exact-neighbor memory accounting for similarly-prefixed variable names.
- Fixed `break_mode: random` tie handling to use random tie-break numbers.
- Added message-property and state-transition guardrail tests before future
  MGM message-flow changes.

### pydcop/algorithms/

Status: DPOP complete; other algorithm modules remain future candidates.

Detailed plans:
- `dpop_optimization_steps.txt`
- `dsa_optimization_steps.txt`
- `mgm_optimization_steps.txt`

Suggested approach:
- Pick one algorithm at a time.
- Start with tests and profiling/benchmarks before changing behavior.
- Prefer message-flow, computation-memory, and local hot-loop cleanup over broad
  rewrites.
- Keep changes isolated by algorithm module and run that module's focused tests.

Possible first files:
- `pydcop/algorithms/dsa.py`
- `pydcop/algorithms/mgm.py`
- `pydcop/algorithms/mgm2.py`
- `pydcop/algorithms/gdba.py`

Useful focused tests:
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_gdba.py`
