# Main Continuity

## Project

- DCOP is a private continuation derived from Orange-OpenSource pyDcop.
- This repository is for private use only; do not preserve public API
  compatibility unless the human developer explicitly asks.
- Work conservatively: small targeted changes, behavior preserved by default,
  no new dependencies or broad refactors without approval.
- Keep original BSD 3-Clause attribution intact.

## Environment

- Use the active shell environment directly.
- Test focused changes with `pytest path/to/test_file.py`.
- Lint focused Python changes with `ruff check path/to/file.py`.
- Use `ruff check .` only for broader checks.
- Run CLI commands through the active interpreter, e.g.
  `python -m pydcop.dcop_cli generate ...`.
- Plain `pytest` excludes tests marked `perf`; run performance tests
  explicitly with `pytest -m perf` or `make perf`.
- Documentation builds with Sphinx in the active environment. For local builds
  use `SPHINXOPTS="-D autosummary_generate=0" make html` to avoid rewriting
  committed autosummary files.

## Current Focus

- `todo.md` currently emphasizes generator cleanup:
  - seed support is done for the active generators recently touched
  - random graph support is done
  - generated instance naming
  - multiple-instance generation
- Generator cleanup should stay incremental. Prefer moving generator-specific
  CLI arguments into the matching `pydcop/commands/generators/*.py` module.
- `generator_summary.txt` is the short generator overview; the older
  `generator_arguments.txt` is being retired.
- Generator docs were updated and Sphinx verified after docs config cleanup.

## Generator Notes

- Generate YAML DCOP instances with
  `python -m pydcop.dcop_cli generate ...`; global `--output <file>` writes
  output to a file.
- Live generator types include `graph_coloring`, `random_graph`, `meetings`,
  `ising`, `agents`, `scenario`, `mixed_problem`, `small_world`, `iot`, and
  `secp`.
- `ising_soft` was removed from `pydcop/commands/generate.py`; the real Ising
  generator is `pydcop/commands/generators/ising.py`.
- `graph_coloring` now requires explicit `--objective min|max` and accepts
  optional `--seed <int>`.
- Graph-coloring color domains use capital letters `A` through `Z`;
  `--colors_count` is restricted to 1 through 26.
- Graph-coloring pseudo-hard constraints use `999999` for same-color neighbor
  assignments in `min` mode and `-999999` in `max` mode; non-conflicts use
  `0`. These are finite pseudo-hard values, not symbolic infinity.
- Graph-coloring soft mode still generates random integer costs in `[0, 9]`
  for every joint assignment on each edge, with no extra hard conflict
  constraint.
- `iot` now owns its parser in
  `pydcop/commands/generators/iot.py:init_cli_parser`, matching the
  graph-coloring pattern.
- `iot` requires explicit `--objective min|max` and accepts optional
  `--seed <int>`.
- The IoT generator creates a power-law Barabasi-Albert DCOP with binary
  random matrix constraints in `range(--range)`, plus a computed factor-graph
  distribution when output is written.
- `ising`, `meetings`, and `secp` accept optional `--seed <int>` and thread a
  local random generator through their random builders.
- `secp` now follows the generator parser pattern with
  `pydcop/commands/generators/secp.py:init_cli_parser`.
- `random_graph` lives in `pydcop/commands/generators/randomgraph.py` and
  requires `--variables_count`, `--domain_size`, `--p_edge`, and
  `--objective min|max`; it accepts optional `--seed` and `--no_agents`.
- `random_graph` always tries to generate a connected Erdos-Renyi graph, uses
  extensive binary random costs in `[0, 9]`, and fails with concise guidance
  such as `Try p_edge >= 0.43 or variables_count >= 878` if connected graph
  generation exhausts bounded attempts.
- A deterministic random-graph fixture lives at
  `tests/instances/random_graph_6_3_0.7.yaml`; it has 6 variables, 14
  constraints, 6 agents, and PuLP optimum cost `35`.
- `small_world` is incomplete/experimental.
- `scenario` is for Dynamic DCOPs.
- Recent focused generator checks used:
  - `pytest tests/dcop_cli/test_generate_graphcoloring.py`
  - `pytest tests/unit/test_generators_iot.py`
  - `pytest tests/unit/test_generate_ising.py`
  - `pytest tests/unit/test_generate_meetingscheduling.py`
  - `pytest tests/unit/test_generate_secp.py`
  - `pytest tests/unit/test_generate_randomgraph.py tests/dcop_cli/test_generate_randomgraph.py`
  - `pytest tests/dcop_cli/test_graph.py tests/unit/test_solvers_pulp.py tests/dcop_cli/test_solve_pulp.py`
  - `ruff check pydcop/commands/generate.py pydcop/commands/generators/iot.py tests/unit/test_generators_iot.py`
  - `python -m pydcop.dcop_cli generate iot --help`

## Docs Notes

- `docs/conf.py` now configures `bibtex_bibfiles = ["biblio.bib"]`, sets
  `language = "en"`, and no longer points at a missing `_static` directory.
- `pydcop/commands/distribute.py` docstring formatting was fixed so the
  distribute command docs no longer trigger a block-quote warning.
- `Makefile` supports `SPHINXOPTS` and `make html` as an alias for `make doc`.
- Recent docs check: `SPHINXOPTS="-D autosummary_generate=0" make html`
  completed without warnings.

## Solve/LP Notes

- `pydcop solve -a pulp <dcop_file>` uses the centralized exact PuLP solver in
  `pydcop/solvers/pulp_solver.py`.
- The PuLP solve path skips distributed graph construction, distribution,
  agents, and message metrics.
- The solver creates one binary choice variable per DCOP variable value and
  one binary tuple variable per relation assignment, then optimizes relation
  values plus variable costs according to `objective: min|max`.
- The current PuLP backend uses `GLPK_CMD`, which does not expose a thread/core
  option through PuLP. Optional multicore support would likely require a CBC
  backend via `PULP_CBC_CMD(threads=...)`.
- Symbolic/non-finite hard costs are treated as forbidden assignments; finite
  pseudo-hard values such as graph-coloring `999999` remain objective terms.
- Tests now use `pydcop.solvers.pulp_solver.solve_dcop` directly instead of
  the old duplicate test-only oracle.

## Algorithm Verification

- Paper verification tracking lives in
  `verification_archive/algorithm_paper_check_tracker.md`.
- Source PDFs should live in `verification_archive/papers/`.
- DPOP has been checked against `verification_archive/papers/dpop.pdf` and
  documented in `verification_archive/dpop_paper_check.md`.
- MGM and MGM2 use `verification_archive/papers/mgm.pdf`.
- Current paper-check order starts with DPOP, MGM, MGM2, then DSA; DPOP is
  verified.
- MGM verification focus: finish min/max experiment notes, check direct
  monotonicity/tie behavior coverage, then update `mgm_paper_check.md` and
  the tracker.
- MGM minimization treats `current_cost - candidate_cost > 0` as improvement;
  MGM maximization treats `current_cost - candidate_cost < 0` as improvement.
  Largest gain wins in `min`; smallest gain wins in `max`.

## Durable Caveats

- `DCOP` objects require explicit `name` and `objective`; there is no default
  objective at the model layer.
- The memory-estimation hook is `memory_footprint_estimate()`.
- Leave relation helpers `assignment_cost()`, `find_optimal()`, and
  `NAryMatrixRelation.__hash__()` alone unless profiling gives a specific
  reason.
- DPOP join order, pre-conversion to `NAryMatrixRelation`, and helper
  extraction can affect intermediate UTIL dimensions, memory, and tie
  behavior. Use `profiling/profile_dpop_utils.py --case generated --strategy all`
  before future DPOP join/projection changes.
- NCBB search-phase stubs remain incomplete. Existing tests cover implemented
  initialization behavior, message dispatch, phase validation, and root
  transition into search, but not a real search implementation.
- SyncBB behavior tests cover direct message flow, pruning, termination, and
  solve-level min/max outcomes.

## Important Paths

- Core model/YAML: `pydcop/dcop/`.
- Algorithms: `pydcop/algorithms/`.
- Computation graphs: `pydcop/computations_graph/`.
- Runtime/agents/communication: `pydcop/infrastructure/`.
- Centralized solvers: `pydcop/solvers/`.
- CLI: `pydcop/commands/`, `pydcop/dcop_cli.py`, `pydcop/pydcop`.
- Generators: `pydcop/commands/generators/`.
- Tests: `tests/unit/`, `tests/api/`, `tests/dcop_cli/`,
  `tests/instances/`.
- Known cases: `tests/utils/known_instances.py`.
- Archived optimization notes: `optimization_archive/`.
- Paper verification notes: `verification_archive/`.

## Open Questions

- What is the primary long-term execution path: CLI, library API, or both?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
