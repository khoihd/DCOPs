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

## Future Candidates

### pydcop/algorithms/

Status: DPOP plan drafted.

Detailed plans:
- `dpop_optimization_steps.txt`

Suggested approach:
- Pick one algorithm at a time.
- Start with tests and profiling/benchmarks before changing behavior.
- Prefer message-flow, computation-memory, and local hot-loop cleanup over broad
  rewrites.
- Keep changes isolated by algorithm module and run that module's focused tests.

Possible first files:
- `pydcop/algorithms/dpop.py`
- `pydcop/algorithms/dsa.py`
- `pydcop/algorithms/mgm.py`
- `pydcop/algorithms/mgm2.py`
- `pydcop/algorithms/gdba.py`

Useful focused tests:
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_gdba.py`
