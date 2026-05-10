
PYTHON ?= python
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= ruff
MYPY ?= $(PYTHON) -m mypy
COVERAGE ?= $(PYTHON) -m coverage
SPHINXOPTS ?=

all: test integ

test:
	$(PYTEST) ./tests/unit
	$(PYTEST) --doctest-modules ./pydcop
	$(PYTEST) ./tests/dcop_cli
	$(PYTEST) ./tests/api

test_cli:
	$(PYTEST) ./tests/dcop_cli

test_unit:
	$(PYTEST) ./tests/unit
	$(PYTEST) --doctest-modules ./pydcop


test_api:
	$(PYTEST) ./tests/api

perf:
	$(PYTEST) -m perf

mypy:
	$(MYPY) --ignore-missing-imports pydcop

lint:
	$(RUFF) check .

coverage: 
	$(COVERAGE) run --source=. -m unittest discover ./tests/unit
	$(COVERAGE) report

doc:
	$(PYTHON) -m sphinx $(SPHINXOPTS) ./docs ./docs/_build/

html: doc
