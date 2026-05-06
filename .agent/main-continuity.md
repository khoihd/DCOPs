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
- Relation optimization work has progressed substantially in
  `pydcop/dcop/relations.py`:
  - `c0d57a4 Document relation slice behavior` refreshed slice docstrings.
  - `e29a00c Optimize generic relation projection` made
    `projection_slow()` evaluate the original relation directly when possible,
    with fallback to `slice()` + `find_arg_optimal()`.
  - `72f369c Iterate projection matrix coordinates directly` removed
    `generate_assignment_as_dict()` from the `projection_slow()` outer loop.
  - `bf60e09 Optimize matrix conversion from functions` made
    `NAryMatrixRelation.from_func_relation()` fill one raw matrix directly.
  - `5ad9a9b Optimize matrix relation value lookup` made
    `NAryMatrixRelation.get_value_for_assignment()` index matrices directly.
  - `a08605b Refresh relation optimization plan` rewrote
    `relation_optimization_steps.txt` with fresh priorities and complexity
    notes.
  - `e52fb7e Optimize matrix relation slicing` optimized
    `NAryMatrixRelation._slice_matrix()` bookkeeping with a per-call
    assignment dict and variable-name set.
  - `316b856 Split join into fast and slow paths` split public `join()` into
    a dispatcher plus `join_fast()` for matrix-backed joins and `join_slow()`
    for the generic fallback.
  - `d5f6019 Add join path benchmark coverage` added benchmark-style coverage
    comparing `join_fast()` and `join_slow()`.
  - `ce4db03 Clarify join dimension helper` made `_join_dimensions()` slightly
    clearer without changing behavior.
  - `e82c49d Optimize generic join loop` made `join_slow()` iterate matrix
    coordinates directly with `np.ndindex()`, avoiding
    `generate_assignment_as_dict()`, `filter_assignment_dict()`, and
    `domain.index()` coordinate recovery in the output-cell loop.
  - `b53c999 Optimize matrix relation value setting` made
    `NAryMatrixRelation.set_value_for_assignment()` compute matrix indexes
    directly for list and dict assignments, preserving copy-on-write behavior
    with a single `np.copy(self._m)` per call. It also documented
    `_slice_matrix()`, added regression coverage that setting values no longer
    calls `_slice_matrix()`, and marked Step 3 complete in
    `relation_optimization_steps.txt`.
- DPOP adhoc distribution support was improved:
  - `a5f3da3 Add DPOP computation memory estimate` implemented
    `pydcop/algorithms/dpop.py::computation_memory()` for pseudo-tree nodes.
    The estimate is the UTIL relation size before projection: own variable
    domain size times parent and pseudo-parent domain sizes.
  - DPOP adhoc solve/distribute CLI tests that were previously skipped for
    missing computation size are now enabled. The stale skip comments that said
    "dcop does not have it" were removed; they meant DPOP, not DCOP.
- Current `relation_optimization_steps.txt` status:
  - Completed: projection fast/slow split, `projection_slow()` direct eval,
    projection coordinate iteration, `from_func_relation()` direct fill,
    matrix scalar lookup, optimization-plan refresh, `_slice_matrix()`, join
    helper split, join fast/slow benchmark coverage, `join_slow()` loop
    optimization, and `NAryMatrixRelation.set_value_for_assignment()`.
  - Next priority: assignment generation helpers.
  - Later priorities: `assignment_cost()` / `find_optimal()` /
    `filter_assignment_dict()` if profiling justifies it.
- Recent focused relation checks passed during the optimization sequence:
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
  - `conda run -n khoihd python -m pytest tests/api/test_api_solve_dpop.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_gdba.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_lp_oracle.py tests/api/test_api_solve.py`
  - `conda run -n khoihd ruff check pydcop/dcop/relations.py tests/unit/test_dcop_relations.py`
- `pydcop/algorithms/mgm.py` had a small typing cleanup in
  `692b952 Modernize MGM neighbor type annotations`: old type comments on
  `_neighbors_values` and `_neighbors_gains` were converted to real
  annotations. Targeted checks passed:
  - `conda run -n khoihd ruff check pydcop/algorithms/mgm.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_mgm.py`
- Current local code note before this continuity update:
  the working tree was clean after `a5f3da3`; relation Step 3 and DPOP
  computation memory are committed.

## Next Steps
- If continuing relation performance work, start with assignment generation
  helpers (`generate_assignment()` / `generate_assignment_as_dict()`), but only
  after documenting current iteration order with focused tests.
- Verify assignment-helper changes with:
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_base.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_relations.py`
  - `conda run -n khoihd python -m pytest tests/unit/test_dcop_lp_oracle.py`
  - `conda run -n khoihd ruff check pydcop/dcop/relations.py`
- Consider DPOP or generator-focused tests only if the implementation touches
  behavior beyond assignment helper iteration.
- Leave broader relation helper changes (`filter_assignment_dict`,
  `assignment_cost`, `find_optimal`) until profiling or a focused algorithm
  task justifies the risk.
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
