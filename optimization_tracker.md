# Optimization Tracker

Concise index of optimization work. Keep detailed plans and verification notes
in the file-specific `*_optimization_steps.txt` documents.

## Status

- `pydcop/dcop/relations.py`
- `pydcop/algorithms/dpop.py`
- `pydcop/algorithms/dsa.py`
- `pydcop/algorithms/mgm.py`
- `pydcop/algorithms/mgm2.py`

## Detailed Notes

- `relation_optimization_steps.txt`
- `dpop_optimization_steps.txt`
- `dsa_optimization_steps.txt`
- `mgm_optimization_steps.txt`
- `mgm2_optimization_steps.txt`

## Current Next Step

No active optimization pass is planned. Start a new focused plan before
revisiting any completed module.

## Focused Checks

- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
- `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`

Use targeted Ruff checks with the touched source and test files, for example:

- `conda run -n khoihd ruff check pydcop/algorithms/mgm2.py tests/unit/test_algorithms_mgm2.py`
