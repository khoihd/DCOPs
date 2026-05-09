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

- The active shell resolves `python` to
  `/Users/khoihd/miniconda3/bin/python` and `pytest` to
  `/Users/khoihd/miniconda3/bin/pytest`; `ruff` resolves to
  `/opt/homebrew/bin/ruff`.
- AGENTS.md now intentionally uses the active environment directly:
  `pytest path/to/test_file.py`, `ruff check path/to/file.py`, and
  `ruff check .`. This was committed as
  `bfa9873 Use default environment commands`.
- The Makefile intentionally defaults to the active user's environment:
  - `PYTHON ?= python`
  - `PYTEST ?= $(PYTHON) -m pytest`
  - `RUFF ?= ruff`
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
- `todo.md` currently includes generator review/cleanup items, with seed
  support marked WIP, plus later paper verification and optimization items.
- The latest generator todo wording was committed as
  `5fc003f Update generator todo list`.
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
- `DCOP` objects now require both `name` and `objective` constructor
  arguments explicitly; there is no longer a default objective at the model
  layer. Tests and production call sites were updated accordingly.

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
- Generator argument inventory is saved in `generator_arguments.txt`; it lists
  the registered `pydcop generate ...` arguments, including aliases, required
  flags, defaults, choices, and positional trailing-file arguments.
- Graph-coloring generation now requires an explicit `--objective min|max`;
  there is no default objective for `pydcop generate graph_coloring`.
- The focused graph-coloring objective change was committed as
  `8f3c243 Require graph coloring objective`. Targeted validation passed:
  `conda run -n khoihd python -m pytest tests/dcop_cli/test_generate_graphcoloring.py`
  and
  `conda run -n khoihd ruff check pydcop/commands/generators/graphcoloring.py tests/dcop_cli/test_generate_graphcoloring.py`.
- Graph-coloring generation now also accepts optional `--seed <int>`,
  committed as `4b0575e Add graph coloring generator seed`. One
  `random.Random(args.seed)` stream controls NetworkX graph generation,
  scale-free node shuffling, and soft constraint random costs. Targeted
  validation passed with
  `pytest tests/dcop_cli/test_generate_graphcoloring.py` and
  `ruff check pydcop/commands/generators/graphcoloring.py tests/dcop_cli/test_generate_graphcoloring.py`.
- IoT generation now requires an explicit `--objective min|max` CLI argument
  from `pydcop generate iot`; `pydcop/commands/generators/iot.py` no longer
  hardcodes `min` when constructing the intermediate or final `DCOP`.
- The IoT generator creates a power-law Barabási-Albert binary DCOP with random
  matrix costs in `range(--range)`, plus a computed factor-graph distribution
  when output is written.
- IoT generation now accepts optional `--seed <int>`, committed as
  `19b8724 Add IoT generator seed`. The seeded RNG is threaded through the
  Barabási graph, random constraint matrices, and random hosting costs.
- IoT now owns its CLI parser in
  `pydcop/commands/generators/iot.py:init_cli_parser`, matching the
  graph-coloring generator pattern. `pydcop/commands/generate.py` calls
  `iot.init_cli_parser(subparsers)`. This was committed as
  `791bb8d Move IoT parser into generator`.
- Focused IoT validation passed with
  `pytest tests/unit/test_generators_iot.py`,
  `ruff check pydcop/commands/generate.py pydcop/commands/generators/iot.py tests/unit/test_generators_iot.py`,
  and `python -m pydcop.dcop_cli generate iot --help`.
- Graph-coloring color domains now use capital English letters from `A` to
  `Z`; `--colors_count` is restricted to 1 through 26.
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
- Current generator review context includes `meetingscheduling.py`: it uses a
  PEAV meeting model with one agent per resource. Variables are named
  `v_<resource_id>_<event_id>` and assigned a start slot; value `0` means the
  resource-event pair is not scheduled. Constraint types are `ci_...`
  intra-resource conflict/utility constraints, `ce_...` inter-resource
  same-event synchronization constraints, and `cu_...` unary utility
  constraints for resources with a single event variable. The DCOP objective is
  `max`; assigning a resource is only beneficial when event value over the
  occupied slots exceeds the generated free-slot opportunity value.
- `pydcop/commands/generators/secp.py` now has clearer `build_models`
  documentation with a smart-office lighting example. The generated DCOP name
  was corrected from `"graph coloring"` to `"secp"`. Committed as
  `da1e413 Document SECP model generation`; targeted Ruff passed.
- `pydcop/commands/generators/smallworld.py` now has a module docstring with a
  small CLI example and a prominent note that the generator is incomplete and
  experimental. The generated DCOP name was corrected from `"graph coloring"`
  to `"small world"`. Committed as
  `fcd7079 Document experimental small world generator`; targeted Ruff passed.
- `generator_summary.txt` was added as a short bullet summary of the generator
  modules, including notes that `scenario` is for Dynamic DCOPs,
  `small_world` is incomplete/experimental, and generator-specific CLI
  arguments should stay with each generator for now. Committed as
  `242f33e Add generator summary`.
- `generator_arguments.txt` is being retired in favor of the shorter
  `generator_summary.txt`.

## Solve/LP Notes

- `pydcop solve -a pulp <dcop_file>` now solves finite-domain DCOP instances
  with a centralized exact PuLP model instead of the distributed runtime.
- The production solver lives in `pydcop/solvers/pulp_solver.py`; `solve.py`
  exposes it as the `pulp` algorithm choice and skips graph construction,
  distribution, agents, and message metrics for that path.
- The solver creates one binary choice variable per DCOP variable value and
  one binary tuple variable per relation assignment, links relation tuples to
  variable choices, and optimizes relation values plus variable costs according
  to `objective: min|max`.
- The `pulp` path reports the usual JSON metrics shape, with zero message
  metrics plus `solver: "pulp"`, `solver_status`, and `objective`.
- The current PuLP backend uses `GLPK_CMD`, which does not expose a thread/core
  option through PuLP. Optional multicore support would likely require adding a
  CBC backend via `PULP_CBC_CMD(threads=...)` and CLI/algo parameters to select
  solver backend and thread count.
- Symbolic/non-finite hard costs are treated as forbidden assignments; finite
  pseudo-hard values such as graph-coloring `999999` remain objective terms.
- The old duplicate test-only oracle `tests/utils/dcop_oracle.py` was removed.
  Tests now use `pydcop.solvers.pulp_solver.solve_dcop` directly.
- Current focused validation passed:
  `conda run -n khoihd python -m pytest tests/unit/test_solvers_pulp.py tests/dcop_cli/test_solve_pulp.py`
  and, after retiring the oracle,
  `conda run -n khoihd python -m pytest tests/unit/test_solvers_pulp.py tests/api/test_api_solve_dpop.py`.

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
- Generator cleanup currently focuses on shared/explicit generator arguments
  such as instance name, objective, variable/domain/utility ranges, seed, and
  eventually multiple-instance generation.

## Important Paths

- Core model/YAML: `pydcop/dcop/`.
- Algorithms: `pydcop/algorithms/`.
- Computation graphs: `pydcop/computations_graph/`.
- Runtime/agents/communication: `pydcop/infrastructure/`.
- Centralized solvers: `pydcop/solvers/`.
- CLI: `pydcop/commands/`, `pydcop/dcop_cli.py`, `pydcop/pydcop`.
- Tests: `tests/unit/`, `tests/api/`, `tests/dcop_cli/`,
  `tests/instances/`.
- Known cases: `tests/utils/known_instances.py`.
- Archived optimization notes: `optimization_archive/`.
- Paper verification notes: `verification_archive/`.

## Open Questions

- What is the primary long-term execution path: CLI, library API, or both?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
