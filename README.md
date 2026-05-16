# Dcop python

[![Documentation Status](https://readthedocs.org/projects/pydcop/badge/?version=latest)](http://pydcop.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/Orange-OpenSource/pyDcop.svg?branch=master)](https://travis-ci.org/Orange-OpenSource/pyDcop)

pyDCOP is a python library for Distributed Constraints Optimization.
It contains implementations of several standard DCOP algorithms (MaxSum, DSA,
DPOP, MGM, etc.), an exact centralized PuLP solver for finite-domain DCOPs,
and allows you to develop your own algorithms.

pyDCOP runs on python >= 3.11.

Documentation is hosted on 
[ReadTheDoc](https://pydcop.readthedocs.io)

## Solving DCOPs

Distributed algorithms are selected with `-a` / `--algo`:

```bash
python -m pydcop.dcop_cli solve -a dpop instance.yaml
python -m pydcop.dcop_cli solve --algo mgm instance.yaml
```

For an exact centralized solve, use the PuLP backend as an algorithm choice:

```bash
python -m pydcop.dcop_cli solve -a pulp instance.yaml
```

The `pulp` solver builds a centralized LP/ILP model and does not use the
distributed computation graph, distribution method, agents, or message runtime.
It uses HiGHS by default and also supports CBC and GLPK:

```bash
python -m pydcop.dcop_cli solve -a pulp instance.yaml
python -m pydcop.dcop_cli solve -a pulp -p solver:cbc -p threads:4 instance.yaml
```

When `threads` is omitted, CBC and HiGHS are given an explicit thread count of
`os.cpu_count() or 1`. With PuLP's HiGHS command wrapper, any explicit thread
count enables HiGHS `parallel=on`; HiGHS would only keep its own
`parallel=choose` default if no thread count were passed to the wrapper.
 
## Acknowledgment

This project is derived from the original pyDcop repository by Orange-OpenSource:
https://github.com/Orange-OpenSource/pyDcop.

The original pyDcop code is copyright 2017 Orange and is licensed under the
BSD 3-Clause License. This repository preserves that license and attribution
while continuing development independently.
