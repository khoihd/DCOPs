# Optimization Tracker

Concise index of optimization work. Keep detailed plans and verification notes
in the file-specific `*_optimization_steps.txt` documents.

## Status

- `pydcop/dcop/relations.py`
  - Complete.
  - Optimized/reviewed.
  - Deferred `assignment_cost()`, `find_optimal()`, and
    `NAryMatrixRelation.__hash__()` are documented in code.
- `pydcop/algorithms/dpop.py`
  - Complete.
  - Optimized through Step 4; the earlier planned Step 5 was removed from
    scope.
  - Future DPOP work should start from a new focused plan.
- `pydcop/algorithms/dsa.py`
  - Complete.
  - Memory accounting fix, DSA-B assignment-copy cleanup, profiler added.
  - Relation helper optimization excluded.
  - No further DSA optimization planned; future work should start from a new
    focused plan.
- `pydcop/algorithms/mgm.py`
  - Complete.
  - Memory accounting fix, random tie fix, message/state guardrails, profiler
    added.
  - Relation helper optimization excluded.
  - No further MGM optimization planned; future work should start from a new
    focused plan.
- `pydcop/algorithms/mgm2.py`
  - In progress.
  - Step 1 memory accounting fix complete.
  - Next: profile `_compute_best_value()` / `_compute_offers_to_send()` before
    local relation changes.

## Detailed Notes

- `relation_optimization_steps.txt`
- `dpop_optimization_steps.txt`
- `dsa_optimization_steps.txt`
- `mgm_optimization_steps.txt`
- `mgm2_optimization_steps.txt`

## Current Next Step

Continue with `pydcop/algorithms/mgm2.py`.

Recommended next work:
- Profile `_compute_best_value()` and `_compute_offers_to_send()`.
- Keep `assignment_cost()` out of scope unless there is a separate
  relation-focused plan.
- Prefer small message-flow, computation-memory, and local hot-loop changes
  over broad rewrites.

## Focused Checks

- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
- `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`

Use targeted Ruff checks with the touched source and test files, for example:

- `conda run -n khoihd ruff check pydcop/algorithms/mgm2.py tests/unit/test_algorithms_mgm2.py`
