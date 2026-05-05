# Main Continuity

## Project
- Name: DCOP
- Origin: private continuation derived from Orange-OpenSource pyDcop
- Status: early-stage stabilization and exploration
- Current goal: understand and stabilize the existing codebase before
  structural changes or modernization.

## Working Rules
- Work conservatively; keep changes small and targeted.
- Preserve behavior unless the task explicitly asks to change it.
- Do not introduce dependencies, rename public APIs, or make broad refactors
  without approval.
- Keep full commit history; no squash/rewrite.
- Keep original BSD 3-Clause attribution intact. New README attribution notes
  that original pyDcop code is copyright 2017 Orange.

## Environment
- Use the `khoihd` Conda environment explicitly:
  - `conda run -n khoihd python`
  - `conda run -n khoihd python -m pytest ...`
  - `conda run -n khoihd ruff check ...`
  - `conda run -n khoihd python -m pip ...`
  - `conda run -n khoihd pydcop ...`
- The project is installed editable in `khoihd`; pytest, Ruff, coverage, PuLP,
  and websocket-server are installed there.
- Avoid bare `pytest`, `python`, or `pydcop` unless the shell is known to be in
  the intended Conda env.

## Current Focus
- Python 3.11 / modern dependency compatibility.
- CLI/API test stabilization through the Conda env.
- Core DCOP algorithms, especially DPOP and relation operations.
- Oracle-style algorithm correctness tests using known DCOP instances and a
  centralized PuLP/GLPK solver for independent optima.
- One-file-at-a-time Ruff cleanup and legacy unit-test modernization when
  explicitly requested.

## Recent Context
- Dependency workflow now uses flexible `requirements.txt` plus
  `constraints.txt`; `Makefile` and `AGENTS.md` use `conda run -n khoihd`.
- `README.md` now contains upstream attribution for Orange-OpenSource pyDcop.
- `pydcop/dcop/objects.py` had a small typing cleanup:
  `self._cb: list[Callable[[Any], Any]] = []`.
- Existing DPOP correctness coverage:
  - `tests/unit/test_algorithms_dpop.py` has hand-built message-flow tests.
  - `tests/api/test_api_solve.py` checks a known DPOP optimum on a small
    graph-coloring DCOP.
  - `tests/dcop_cli/test_solve.py` checks DPOP CLI solves on fixtures.
  - `tests/integration/dmaxsum_graphcoloring.py` has brute-force optimum
    helpers, but not paired with a DCOP algorithm solve.
- Oracle and known-instance testing groundwork was added:
  - `tests/utils/known_instances.py` stores small known-answer DCOP cases,
    including API graph coloring, YAML fixtures, SyncBB toy min/max cases, and
    dynamic graph-coloring states.
  - `tests/utils/dcop_oracle.py` provides `solve_dcop_with_pulp`, a centralized
    PuLP/GLPK ILP oracle for finite DCOP instances.
  - `tests/unit/test_dcop_lp_oracle.py` validates the PuLP oracle against the
    known assignments/costs.
  - Recent focused checks passed:
    `conda run -n khoihd python -m pytest tests/unit/test_dcop_lp_oracle.py`
    and `conda run -n khoihd ruff check tests/unit/test_dcop_lp_oracle.py tests/utils/dcop_oracle.py tests/utils/known_instances.py`.
- `pydcop/dcop/relations.py::join` is a likely performance hotspot. It
  currently fills an immutable `NAryMatrixRelation` by repeated
  `set_value_for_assignment` calls, causing repeated full matrix copies.
  NumPy broadcasting could optimize matrix-relation joins, but add correctness
  tests first.

## Next Steps
- Continue the current testing task: use `tests/utils/known_instances.py` and
  `tests/utils/dcop_oracle.py` to add oracle-style correctness tests for DCOP
  algorithms.
- Start with a small API-level test, likely `tests/api/test_api_solve_oracle.py`:
  solve a known instance with PuLP, solve the same instance with DPOP through
  `pydcop.infrastructure.run.solve`, and compare objective costs rather than
  exact assignments.
- Keep exact assignment assertions only for known unique/stable cases; compare
  costs for algorithm checks because multiple optima can exist.
- After oracle tests exist, consider optimizing `relations.join` carefully with
  targeted relation, DPOP, API, and CLI tests.
- Continue targeted CLI/API stabilization and one-file Ruff cleanup only when
  requested.
- Review dependency/version policy later; the original project targeted older
  Python versions and CI/docs remain outdated.

## Important Paths
- `pydcop/dcop/relations.py` — relation primitives, `join`, `projection`,
  assignment helpers.
- `pydcop/algorithms/dpop.py` — DPOP implementation.
- `tests/unit/test_algorithms_dpop.py` — DPOP message-flow unit tests.
- `tests/api/test_api_solve.py` — API solve checks, including DPOP.
- `tests/dcop_cli/test_solve.py` — CLI solve fixtures.
- `tests/utils/known_instances.py` — shared test-owned known DCOP cases and
  expected optima.
- `tests/utils/dcop_oracle.py` — PuLP/GLPK centralized DCOP oracle for tests.
- `tests/unit/test_dcop_lp_oracle.py` — validation that the oracle matches
  known instances.
- `AGENTS.md` — repo instructions, project map, command conventions.

## Open Questions
- What is the primary long-term execution path: CLI, library API, or both?
- What minimum Python/dependency versions should be supported?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
