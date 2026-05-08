# Main Continuity

## Project

- DCOP is a private continuation derived from Orange-OpenSource pyDcop.
- This repository is for private use only; do not worry about public API
  exposure or backward compatibility unless the human developer explicitly asks.
- Current goal: stabilize and understand the codebase before structural
  modernization.
- Work conservatively: small targeted changes, behavior preserved by default,
  no new dependencies or broad package refactors without approval.
- Keep original BSD 3-Clause attribution intact.

## Environment And Test Commands

- The project has been used from the `khoihd` Conda environment, but the
  Makefile now intentionally defaults to the active user's environment:
  - `PYTHON ?= python`
  - `PYTEST ?= $(PYTHON) -m pytest`
  - `RUFF ?= ruff`
- For explicit environment runs, use the desired environment directly, e.g.
  `conda run -n khoihd python -m pytest ...` or
  `conda run -n base python -m pytest ...`.
- Plain `pytest` is now configured as a correctness run and excludes tests
  marked `perf`.
- Run performance/benchmark tests explicitly with `pytest -m perf` or
  `make perf`.
- CLI tests invoke `python -m pydcop.dcop_cli` from the active interpreter to
  avoid stale installed wrapper warnings.

## Current State

- Python support metadata declares Python 3.11+ in setup/docs.
- Archived optimization tracking lives in
  `optimization_archive/optimization_tracker.md`.
- All algorithm candidates previously listed there now have focused
  optimization passes and file-specific notes.
- Algorithm behavior test expansion has covered ADSA, AMaxSum, DBA, DPOP,
  DSA, DSA tutorial, GDBA, Dynamic MaxSum, MaxSum, MGM, MGM2, MixedDSA, NCBB,
  and SyncBB.
- The memory-estimation hook was renamed repo-wide from
  `computation_memory()` to `memory_footprint_estimate()`.
- `todo.md` currently prioritizes verifying algorithm implementation
  correctness against source papers.
- Paper verification tracking lives in
  `verification_archive/algorithm_paper_check_tracker.md`.
- Source PDFs should live in `verification_archive/papers/`.
- DPOP has been checked against `verification_archive/papers/dpop.pdf`
  and documented in `verification_archive/dpop_paper_check.md`.
- MGM and MGM2 use `verification_archive/papers/mgm.pdf`.
  Initial paper-check notes live in `verification_archive/mgm_paper_check.md`
  and `verification_archive/mgm2_paper_check.md`.
- Current MGM verification focus: confirm min/max gain behavior with small
  deterministic experiment runs.

## DPOP Paper Check Notes

- Core DPOP UTIL/VALUE logic matches the Petcu/Faltings paper.
- DPOP test coverage now includes a cyclic pseudotree case where a child UTIL
  carries ancestor context through an intermediate node.
- `memory_footprint_estimate()` for DPOP is documented as a local
  distribution-time approximation, not exact runtime joined UTIL memory.
- Exact DPOP runtime context can include ancestor dimensions carried by child
  UTIL messages.

## MGM And MGM2 Paper Check Notes

- The Maheswaran/Pearce/Tambe 2004 graphical-game paper is stored as
  `verification_archive/papers/mgm.pdf`.
- MGM is currently `In progress` in the tracker. The paper contract and
  implementation mapping are drafted.
- MGM2 is now priority 3 in the tracker, directly after MGM, because it uses
  the same paper and should be checked while that context is fresh.
- MGM min/max sign convention has been checked with four focused
  `tests/unit/test_algorithms_mgm.py` tests; the targeted pytest run passed.
- MGM minimization uses `current_cost - candidate_cost > 0` as an improving
  gain; MGM maximization uses `current_cost - candidate_cost < 0` as an
  improving gain. Gain comparison follows this convention: largest gain wins
  in `min`, smallest gain wins in `max`.

## Generator/YAML Notes

- The project can generate YAML DCOP instances through
  `python -m pydcop.dcop_cli generate ...`, with optional global
  `--output <file>`.
- Live generator types include `graph_coloring`, `meetings`, `ising`,
  `agents`, `scenario`, `mixed_problem`, `ising_soft`, `small_world`, `iot`,
  and `secp`.
- `pydcop/commands/generators/graphcoloring.py` is the current graph-coloring
  generator implementation; generated DCOP YAML is serialized via
  `pydcop/dcop/yamldcop.py`.
- Graph-coloring generation now supports `--objective min|max`. The default
  remains `min`.
- Graph-coloring pseudo-hard constraints use
  `HARD_CONSTRAINT_VALUE = 999999`: same-color neighbor assignments get
  `999999` in `min` mode and `-999999` in `max` mode; non-conflicts get `0`.
  This is still a finite pseudo-hard value, not symbolic infinity.
- Graph-coloring soft mode still generates random integer costs in `[0, 9]`
  for every joint assignment on each edge, with no additional hard conflict
  constraint.
- The graph-coloring generator docs were corrected to use the actual
  `graph_coloring` command name and current options.
- Targeted generator tests and the full `tests/unit` suite passed after these
  changes:
  `conda run -n khoihd python -m pytest tests/unit` reported
  `1095 passed, 6 deselected`.

## Solve/LP Notes

- `pydcop/commands/solve.py` currently solves with DCOP algorithms from
  `pydcop/algorithms/`; it does not yet offer a centralized linear/integer
  programming solver for the DCOP assignment problem.
- Existing LP/ILP code is for distribution only, not solving assignments.
  Distribution modules use PuLP with GLPK through `GLPK_CMD`, especially
  `pydcop/distribution/ilp_fgdp.py`,
  `pydcop/distribution/oilp_cgdp.py`, and related SECP distribution modules.
- Next implementation focus requested by the human developer: add a linear
  programming solver path in `pydcop/commands/solve.py`.
  Start by designing the smallest CLI integration that reuses existing
  dependencies/patterns if possible. Likely first pass: a centralized exact
  solver for finite-domain extensional/intensional DCOPs, with careful handling
  of `objective: min|max`, hard pseudo-costs, and output/metrics consistency.

## Durable Caveats

- Leave relation helpers `assignment_cost()`, `find_optimal()`, and
  `NAryMatrixRelation.__hash__()` alone unless profiling gives a specific
  reason.
- DPOP join order, pre-conversion to `NAryMatrixRelation`, and helper
  extraction can affect intermediate UTIL dimensions, memory, and tie behavior.
  Use `profiling/profile_dpop_utils.py --case generated --strategy all` before
  future DPOP join/projection changes.
- NCBB search-phase stubs remain incomplete. Current tests cover implemented
  initialization behavior, message dispatch, phase validation, and root
  transition into search, but not a real search implementation.
- SyncBB behavior tests cover direct message flow, pruning, termination, and
  solve-level min/max outcomes.
- If revisiting completed optimization modules, start a new focused plan rather
  than extending old optimization notes casually.

## Next Steps

- Prioritize the requested `solve.py` linear-programming solver implementation
  in the next session.
- Continue paper-based correctness verification one algorithm at a time,
  following `verification_archive/algorithm_paper_check_tracker.md`.
- Current tracker order starts with DPOP, MGM, MGM2, then DSA; DPOP is
  verified.
- Continue with MGM first: finish min/max experiment notes, check direct
  monotonicity/tie behavior coverage, then update `mgm_paper_check.md` and
  tracker status.
- For each algorithm paper check:
  - store the paper under `verification_archive/papers/`
  - create `verification_archive/<algorithm>_paper_check.md`
  - compare paper logic to implementation and tests
  - add focused tests for any coverage gaps
  - update the tracker status and notes
- For any new optimization, pick one file or subsystem, update/create a focused
  `*_optimization_steps.txt` plan, then run targeted tests and Ruff.

## Important Paths

- Core model/YAML: `pydcop/dcop/`.
- Algorithms: `pydcop/algorithms/`.
- Computation graphs: `pydcop/computations_graph/`.
- Runtime/agents/communication: `pydcop/infrastructure/`.
- CLI: `pydcop/commands/`, `pydcop/dcop_cli.py`, `pydcop/pydcop`.
- Tests: `tests/unit/`, `tests/api/`, `tests/dcop_cli/`,
  `tests/instances/`.
- Oracle/known cases: `tests/utils/known_instances.py`,
  `tests/utils/dcop_oracle.py`.
- Archived optimization notes: `optimization_archive/`.
- Paper verification notes: `verification_archive/`.

## Open Questions

- What is the primary long-term execution path: CLI, library API, or both?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
