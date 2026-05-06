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
- Relation optimization work in `pydcop/dcop/relations.py` was completed and
  is tracked in `relation_optimization_steps.txt` plus
  `optimization_tracker.md`:
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
  - `84a96ef Optimize assignment dict generation` switched
    `generate_assignment_as_dict()` to `itertools.product`, intentionally using
    last-variable-fastest order, and added order/mutability coverage.
  - `80b9f79 Optimize list assignment generation` did the same for
    `generate_assignment()` and updated both generator docstrings.
  - `b493457 Defer assignment cost optimization` and
    `ea53f29 Defer find optimal optimization` recorded the decision to leave
    `assignment_cost()` and `find_optimal()` unchanged without profiling.
  - `ecfdfd1 Optimize assignment filtering` made
    `filter_assignment_dict()` use set membership while preserving returned
    assignment order.
  - `bdd6882 Optimize relation optimum scan` made `find_optimum()` snapshot
    dimensions with `list(...)` and evaluate generated full assignments
    directly without redundant filtering.
  - `8b3c009 Cache conditional relation dimensions` cached
    `ConditionalRelation.dimensions` while still returning a copy.
  - `1f50acf Optimize function relation slice checks` changed
    `NAryFunctionRelation.slice()` unknown-variable checks to use a set.
  - `3b7e16c Ensure matrix repr cleanup on errors` wrapped
    `NAryMatrixRelation._simple_repr()` temporary `_matrix` state in
    `try/finally`.
  - `7fcd5d1 Add optimization planning docs` added
    `optimization_tracker.md` and `dpop_optimization_steps.txt`.
- DPOP adhoc distribution support was improved:
  - `a5f3da3 Add DPOP computation memory estimate` implemented
    `pydcop/algorithms/dpop.py::computation_memory()` for pseudo-tree nodes.
    The estimate is the UTIL relation size before projection: own variable
    domain size times parent and pseudo-parent domain sizes.
  - DPOP adhoc solve/distribute CLI tests that were previously skipped for
    missing computation size are now enabled. The stale skip comments that said
    "dcop does not have it" were removed; they meant DPOP, not DCOP.
- Current `relation_optimization_steps.txt` status:
  - Steps 1-6 are complete or explicitly deferred.
  - Deferred relation items: `assignment_cost()`, `find_optimal()`, and
    `NAryMatrixRelation.__hash__()`.
- DPOP optimization work has started in `pydcop/algorithms/dpop.py`, tracked
  in `dpop_optimization_steps.txt`:
  - `f51c372 Record DPOP optimization baseline` marked baseline unit/API/Ruff
    checks complete and identified local timing candidates.
  - `3d9a93d Simplify DPOP constraint filtering` replaced copy-then-remove
    constructor filtering with append-to-kept-list logic and added focused
    kept/filtered constraint coverage.
  - `3a1110a Clarify DPOP relation variable names` renamed a local helper
    variable in constructor filtering.
  - `7ddbe65 Use set membership for DPOP descendants` changed descendant and
    relation variable-name checks to set disjointness.
  - `a07454c Defer DPOP scope names cleanup` recorded the decision not to use
    `RelationProtocol.scope_names` here because it would still build a list and
    a broader cache would belong in relation-layer work.
  - `6b899e9 Mark DPOP constructor filtering complete` marked Step 2 complete.
  - `9063e86 Avoid exceptions in DPOP value forwarding` replaced
    `try`/`except KeyError` with explicit membership checks in VALUE forwarding.
  - `464f704 Cover DPOP value separator ordering` added focused coverage for
    child separator ordering and marked Step 3 complete.
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
  the working tree was clean after `464f704`; relation optimization is
  complete, DPOP optimization Steps 1-3 are complete, and DPOP Step 4 is next.

## Next Steps
- If continuing DPOP optimization, start at `dpop_optimization_steps.txt`
  Priority 4: relation join/projection phase review.
- Be conservative with DPOP Step 4: join order, pre-conversion to
  `NAryMatrixRelation`, and helper extraction can affect intermediate UTIL
  dimensions, memory, and tie behavior. Prefer measurement and oracle checks
  before changing this path.
- Baseline DPOP checks to rerun for meaningful DPOP changes:
  - `conda run -n khoihd python -m pytest tests/unit/test_algorithms_dpop.py`
  - `conda run -n khoihd python -m pytest tests/api/test_api_solve_dpop.py`
  - `conda run -n khoihd ruff check pydcop/algorithms/dpop.py tests/unit/test_algorithms_dpop.py`
- Consider `tests/dcop_cli/test_solve.py` only for DPOP changes that affect CLI
  solve/distribution behavior or message serialization.
- Leave relation helper changes alone unless profiling gives a specific reason;
  see `relation_optimization_steps.txt` for completed/deferred decisions.
- Continue targeted CLI/API stabilization and one-file Ruff cleanup only when
  requested.
- Review dependency/version policy later; the original project targeted older
  Python versions and CI/docs remain outdated.

## Important Paths
- `pydcop/dcop/relations.py` — relation primitives, `join`, `projection`,
  assignment helpers.
- `pydcop/algorithms/dpop.py` — DPOP implementation.
- `dpop_optimization_steps.txt` — current DPOP optimization plan and status.
- `optimization_tracker.md` — high-level optimization tracker by source area.
- `relation_optimization_steps.txt` — completed relation optimization plan.
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
