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
  - `tests/api/test_api_solve_dpop.py` now runs DPOP through the public
    `solve` API and compares costs against the PuLP oracle for both
    `KNOWN_INSTANCE_SOLUTIONS` and `KNOWN_INSTANCE_COSTS`.
- `pydcop/dcop/relations.py::join` was optimized in two small commits:
  - `cbe67ed Optimize join matrix filling` removed repeated full-matrix copies
    in the generic fallback by filling one raw NumPy matrix directly.
  - `f86a6a7 Add matrix fast path for join` added a broadcasting fast path for
    `NAryMatrixRelation` + `NAryMatrixRelation` joins, while preserving the
    generic callable fallback for non-matrix relations.
  - `tests/unit/test_dcop_relations.py::test_join_matrix_relations_different_order`
    covers matrix-axis alignment when shared variables appear in different
    relation orders.
- Recent focused checks passed after the join optimization:
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
  - `conda run -n khoihd python -m pytest tests/api/test_api_solve_dpop.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_lp_oracle.py tests/api/test_api_solve_dpop.py tests/api/test_api_solve.py`
  - `conda run -n khoihd ruff check pydcop/dcop/relations.py tests/unit/test_dcop_relations.py`
- `pydcop/dcop/relations.py::projection` was optimized in
  `c6a89a4 Optimize relation projection paths`:
  - `projection()` now dispatches to `projection_fast()` for
    `NAryMatrixRelation` and `projection_slow()` for generic relation types.
  - `projection_fast()` uses `np.max`/`np.min` over the projected axis.
  - `projection_slow()` preserves the generic `slice()` + `find_arg_optimal()`
    behavior but fills one raw NumPy result matrix directly instead of using
    repeated `set_value_for_assignment()` calls.
  - Tests in `tests/unit/test_dcop_relations.py` cover `projection_fast()`,
    `projection_slow()`, parity between both helpers, and a benchmark-style
    fast-vs-slow comparison.
- Recent projection checks passed:
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
  - `conda run -n khoihd python -m pytest tests/api/test_api_solve_dpop.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_lp_oracle.py tests/api/test_api_solve_dpop.py tests/api/test_api_solve.py`
  - `conda run -n khoihd ruff check pydcop/dcop/relations.py tests/unit/test_dcop_relations.py`
- `relation_optimization_steps.txt` is the active checklist:
  - Step 1 complete: projection matrix fast path and helper split.
  - Step 2 next: optimize `projection_slow()` direct generic evaluation.
  - Step 3 later: optimize `NAryMatrixRelation.from_func_relation()`.
  - Step 4 later: optimize scalar lookup in
    `NAryMatrixRelation.get_value_for_assignment()`.
  - Step 5 later: optimize `NAryMatrixRelation._slice_matrix()`.
- `pydcop/algorithms/mgm.py` had a small typing cleanup in
  `692b952 Modernize MGM neighbor type annotations`: old type comments on
  `_neighbors_values` and `_neighbors_gains` were converted to real
  annotations. Targeted checks passed:
  - `conda run -n khoihd ruff check pydcop/algorithms/mgm.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- Current local code note before this continuity update:
  `projection_slow()` has explanatory comments for its current slow-path
  mechanics. Ruff passed on `pydcop/dcop/relations.py`.

## Next Steps
- If continuing relation performance work, start with
  `pydcop/dcop/relations.py::projection_slow`:
  - current hot line is the loop body calling
    `find_arg_optimal(a_var, a_rel.slice(partial), mode)`.
  - `slice()` is necessary for the current `find_arg_optimal()`-based
    implementation, because `find_arg_optimal()` expects a one-variable
    relation.
  - It is not conceptually necessary for projection; the likely next
    optimization is to evaluate the original relation directly with a complete
    assignment dict and `a_rel.get_value_for_assignment(assignment)`.
  - Prefer the explicit method call over `a_rel(**assignment)` for readability.
  - Keep a fallback to the current `slice()` + `find_arg_optimal()` behavior if
    direct evaluation is unsafe for a relation type.
  - Add/keep tests for min/max, one-variable/scalar projection, function
    relations, and parity with `projection_fast()` on a matrix relation.
  - Verify with relation, DPOP unit, DPOP API oracle, and oracle/API smoke
    tests listed in `relation_optimization_steps.txt`.
- After `projection_slow()`, consider `NAryMatrixRelation.from_func_relation`,
  scalar lookup in `NAryMatrixRelation.get_value_for_assignment()`, then
  `_slice_matrix()` per `relation_optimization_steps.txt`.
- Leave `filter_assignment_dict` and `generate_assignment_as_dict` alone unless
  profiling shows they still matter after the targeted projection/slice work.
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
