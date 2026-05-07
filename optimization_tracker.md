# Optimization Tracker

Concise index of optimization work. Keep detailed plans and verification notes
in the file-specific `*_optimization_steps.txt` documents.

## Status

- `pydcop/dcop/relations.py`
- `pydcop/algorithms/dpop.py`
- `pydcop/algorithms/dsa.py`
- `pydcop/algorithms/mgm.py`
- `pydcop/algorithms/mgm2.py`
- `pydcop/algorithms/adsa.py`
- `pydcop/algorithms/maxsum.py`
- `pydcop/algorithms/amaxsum.py`

## Detailed Notes

- `relation_optimization_steps.txt`
- `dpop_optimization_steps.txt`
- `dsa_optimization_steps.txt`
- `mgm_optimization_steps.txt`
- `mgm2_optimization_steps.txt`
- `adsa_optimization_steps.txt`
- `maxsum_optimization_steps.txt`

## Current Next Step

No active optimization pass is planned. Remaining algorithm candidates:

- `pydcop/algorithms/dba.py`
- `pydcop/algorithms/dsatuto.py`
- `pydcop/algorithms/gdba.py`
- `pydcop/algorithms/maxsum_dynamic.py`
- `pydcop/algorithms/mixeddsa.py`
- `pydcop/algorithms/ncbb.py`
- `pydcop/algorithms/syncbb.py`

Pick one file at a time and start a new focused plan before changing it.

## Focused Checks

- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm2.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_adsa.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_amaxsum.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dba.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dsatuto.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_gdba.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_maxsum.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_ncbb.py`
- `conda run -n khoihd python -m pytest tests/unit/test_algorithms_syncbb.py`
- `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`

Use targeted Ruff checks with the touched source and test files, for example:

- `conda run -n khoihd ruff check pydcop/algorithms/mgm2.py tests/unit/test_algorithms_mgm2.py`
