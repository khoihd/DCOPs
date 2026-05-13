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
- Ruff is now configured in `pyproject.toml` with `target-version = "py311"`
  and `extend-select = ["UP"]` for pyupgrade/modernization checks.

## Current Focus

- `todo.md` currently emphasizes paper verification first:
  - DPOP is done
  - MGM / MGM2 is done
  - DBA is done
  - GDBA is done
  - DSA is done
  - ADSA is done
  - MixedDSA is done / no separate paper source found
  - MaxSum is done
  - no next paper-verification target has been selected yet
- Generator cleanup remains open:
  - seed support is done for the active generators recently touched
  - random graph support is done
  - generated instance naming
  - multiple-instance generation
- Generator cleanup should stay incremental. Prefer moving generator-specific
  CLI arguments into the matching `pydcop/commands/generators/*.py` module.
- `generator_summary.txt` is the short generator overview; the older
  `generator_arguments.txt` is being retired.
- Generator docs were updated and Sphinx verified after docs config cleanup.
- Recent runtime/algorithm cleanup focused on logging/debugging notes, Ruff
  modernization warnings in VS Code, MGM/MGM2 termination behavior, GDBA
  fixed-cycle support, DSA/ADSA verification, MixedDSA review, and removing
  the obsolete DSA tutorial algorithm.
- Recent MaxSum/runtime work fixed synchronous cycle metrics so MaxSum now
  supports `--run_metrics` with `--collect_on cycle_change`; the runtime row
  uses the completed orchestrator cycle, and the final `FINISHED` row is still
  appended by `solve` shutdown behavior.

## Recent Maintenance Notes

- A repo-wide Ruff modernization pass was committed. It converted typing
  aliases, f-strings, `super()`, explicit `object` inheritance, and similar
  pyupgrade findings. Verification used `ruff check .` and full `pytest`.
- Remaining active `# type:` / `# Type:` comments in tracked Python files were
  replaced with modern annotations so VS Code/Pylance no longer warns on old
  `Dict`, `List`, `Tuple`, `Set`, `Optional`, or `Union` comments. A final
  scan with `rg -n "# type:|# Type:" -g "*.py"` found no matches.
- `pydcop/infrastructure/agents.py` had legacy type comments converted to
  annotations. Focused check: `pytest tests/unit/test_infra_agents.py`.
- Top-level CLI verbosity controls logging: use
  `python -m pydcop.dcop_cli -v 3 ...` for `logging.DEBUG`. Put `-v 3`
  before the subcommand.
- `--run_metrics <file>` writes CSV metrics when paired with
  `--collect_on value_change|cycle_change|period`; for per-iteration quality
  use `--collect_on cycle_change`.
- Generated scratch files currently untracked and intentionally not committed:
  `dsa_max_metrics.csv`, `dsa_min_metrics.csv`, `mgm_max_metrics.csv`,
  `mgm_min_metrics.csv`, `mgm2_max_metrics.csv`, `mgm2_min_metrics.csv`,
  `maxsum_max_metrics.csv`, and `random.yaml`. `verification_archive/.DS_Store`
  is also untracked scratch.

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
- The old algorithm-implementation tutorial and downloadable `dsa-tuto.py`
  sample were removed when `pydcop/algorithms/dsatuto.py` was retired.

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
- DPOP has been checked against `verification_archive/papers/dpop.pdf`,
  documented in `verification_archive/dpop_paper_check.md`, and marked
  verified.
- MGM and MGM2 use `verification_archive/papers/mgm.pdf`; both are marked
  verified in `verification_archive/algorithm_paper_check_tracker.md`.
- DBA has been checked against `verification_archive/papers/dba.pdf`,
  documented in `verification_archive/dba_paper_check.md`, and marked
  done / verified.
- GDBA has been checked against `verification_archive/papers/gdba.pdf`,
  documented in `verification_archive/gdba_paper_check.md`, and marked
  done / verified.
- DSA has been checked against `verification_archive/papers/dsa.pdf`,
  documented in `verification_archive/dsa_paper_check.md`, and marked
  done / verified.
- Current planned paper-check focus for the next session is MixedDSA.
- DBA verification fixes in `pydcop/algorithms/dba.py`:
  - normal termination now preserves `finished` mode and calls `stop()`
  - breakout weights now apply per exact violated assignment tuple instead
    of one weight per constraint
  - `infinity` is stored per computation as `self._infinity` instead of
    mutating the module global
  - equal-improvement tie-breaking uses natural name order, so `v2` precedes
    `v10`
  - no-neighbor / unary-only computations select a local best value, finish,
    and stop at startup
- Recent focused DBA checks used:
  - `pytest tests/unit/test_algorithms_dba.py`
  - `pytest tests/dcop_cli/test_solve.py::GraphColoringCsp`
  - `ruff check pydcop/algorithms/dba.py tests/unit/test_algorithms_dba.py`
- GDBA verification fixed `R` and `C` increase scopes in
  `pydcop/algorithms/gdba.py` to follow the paper's row/column convention:
  `C` increases all local values with neighbor context fixed, and `R`
  increases the current local value across possible neighbor contexts.
- GDBA now supports `stop_cycle` for fixed-cycle runs and per-cycle metrics.
  `_send_current_value()` follows the MGM-style stop boundary: send the
  initial value before `stop_cycle=1`, then call both `finished()` and
  `stop()` before posting the next value. The module docstring documents CLI
  metrics usage.
- Recent focused GDBA checks used:
  - `pytest tests/unit/test_algorithms_gdba.py`
  - `ruff check pydcop/algorithms/gdba.py tests/unit/test_algorithms_gdba.py`
- DSA verification notes:
  - implementation supports paper variants A, B, and C; variants D/E from the
    paper are intentionally not exposed
  - default repo behavior is `variant="B"` and `probability=0.7`; the paper
    sweeps probability experimentally rather than mandating a default
  - every-cycle value broadcast is an intentional runtime adaptation from the
    paper's lower-communication send-on-change behavior, preserving liveness
    under the current wait-for-all-neighbors protocol
  - `p_mode="arity"`, `stop_cycle`, `mode="max"`, and generic N-ary relations
    are repo-level extensions beyond the paper's graph-coloring presentation
  - DSA variants by paper experiment: B is the best practical default, C is
    strong but more active/sensitive to probability, A is conservative and more
    prone to local minima; D/E are not recommended by the paper and are not
    implemented here
- Recent focused DSA checks used:
  - `pytest tests/unit/test_algorithms_dsa.py`
  - `pytest tests/unit/test_algorithms_dsa.py tests/unit/test_algorithms_adsa.py`
  - `ruff check pydcop/algorithms/dsa.py tests/unit/test_algorithms_dsa.py`
- ADSA has been checked against `verification_archive/papers/adsa.pdf`,
  documented in `verification_archive/adsa_paper_check.md`, and marked done /
  verified.
- ADSA verification notes:
  - Fitzpatrick and Meertens define an ongoing peer-to-peer stochastic local
    optimizer with random initial values, periodic asynchronous wake-ups,
    probability-gated local optimization, and value messages on changes
  - `pydcop/algorithms/adsa.py` maps this to randomized startup offset,
    periodic `tick()`, latest-neighbor-value storage, local exhaustive best
    value search, and probability-gated DSA A/B/C value-change variants
  - every-tick value broadcast is an intentional runtime adaptation for
    startup timing and message-loss resilience, not the paper's lower-message
    send-on-change rule
  - `variant="A"|"B"|"C"`, default `probability=0.7`, `mode="max"`, variable
    costs, and generic N-ary relations are repo-level extensions/adaptations
  - no code behavior change was required; doc comments were tightened
  - the ADSA BibTeX key was corrected from `weiss_distributed_2003` to
    `fitzpatrick_distributed_2003`
- Recent focused ADSA checks used:
  - `pytest tests/unit/test_algorithms_adsa.py`
  - `ruff check pydcop/algorithms/adsa.py`
- MixedDSA has been documented in
  `verification_archive/mixeddsa_paper_check.md` and marked done / no separate
  paper source found in `verification_archive/algorithm_paper_check_tracker.md`.
- MixedDSA review notes:
  - `pydcop/algorithms/mixeddsa.py` is treated as a pyDcop-specific hard/soft
    extension of DSA, with base A/B/C move variants from
    `verification_archive/papers/dsa.pdf`
  - hard constraints are relations with at least one local assignment
    evaluating to symbolic `+inf` or `-inf`; finite pseudo-hard penalties are
    soft costs
  - the algorithm first reduces the number of violated hard constraints, then
    optimizes soft cost when hard violations cannot improve
  - separate `proba_hard` and `proba_soft` parameters control hard-violation
    and soft-cost moves
  - recent fixes added no-neighbor local-best startup and stop behavior,
    repaired `stop_cycle` to call both `finished()` and `stop()`, prevented
    variant A from making equal-cost hard-conflict sideway moves, and made
    variant C equal-cost/no-violation sideway moves reachable
- Recent focused MixedDSA checks used:
  - `pytest tests/unit/test_algorithms_mixeddsa.py`
  - `ruff check pydcop/algorithms/mixeddsa.py tests/unit/test_algorithms_mixeddsa.py`
- `pydcop/algorithms/dsatuto.py` was removed after DSA verification. Related
  unit/API tests, docs/reference pages, the algorithm-implementation tutorial,
  downloadable tutorial sample, optimization notes, and tracker entry were
  removed or updated. `dsatuto` no longer appears in
  `list_available_algorithms()`.
- Focused checks for the `dsatuto` removal used:
  - `pytest tests/unit/test_algorithms_objects.py tests/unit/test_infra_computations.py tests/api/test_api_solve.py`
  - `pytest tests/unit/test_algorithms_dsa.py tests/unit/test_algorithms_adsa.py`
  - `ruff check pydcop/algorithms/__init__.py pydcop/algorithms/dsa.py pydcop/algorithms/adsa.py pydcop/infrastructure/computations.py tests/api/test_api_solve.py tests/unit/test_algorithms_objects.py tests/unit/test_infra_computations.py`
  - `SPHINXOPTS="-D autosummary_generate=0" make html`
- MGM minimization treats `current_cost - candidate_cost > 0` as improvement;
  MGM maximization treats `current_cost - candidate_cost < 0` as improvement.
  Largest gain wins in `min`; smallest gain wins in `max`.
- MGM notes include a non-blocking terminology cleanup idea: consider switching
  MGM implementation wording from `cost` to `utility` where that would better
  match the paper's maximization framing and reduce gain-sign confusion.
- MGM2 coordinated-gain evaluation was fixed in
  `pydcop/algorithms/mgm2.py`: `_find_best_offer()` now subtracts the current
  shared partner-relation cost before adding the offerer's local gain, avoiding
  double-counting of the old partner-link value.
- Recent focused MGM/MGM2 verification checks used:
  - `pytest tests/unit/test_algorithms_mgm.py tests/unit/test_algorithms_mgm2.py`
  - `pytest tests/api/test_api_graph.py`
  - `ruff check pydcop/algorithms/mgm2.py tests/unit/test_algorithms_mgm.py tests/unit/test_algorithms_mgm2.py`
- MGM and DSA do not currently implement a global convergence stop such as
  "all computations kept the same value this cycle"; they rely on
  `stop_cycle`, timeout, or external stop.
- MGM stop-cycle handling was fixed in `pydcop/algorithms/mgm.py`: when the
  stop boundary is reached it now calls both `finished()` and `stop()`, and
  `_wait_for_values()` does not process postponed value messages after stop.
  `stop_cycle=1` now allows the initial value send before stopping on the
  next send attempt. Focused check: `pytest tests/unit/test_algorithms_mgm.py`.
- MGM2 stop-cycle handling was fixed in `pydcop/algorithms/mgm2.py` with the
  same pattern: `_send_value()` returns whether it continued, callers only
  enter `"value"` state after a real send, and no-neighbor computations call
  `stop()` after `finished()`. Focused check:
  `pytest tests/unit/test_algorithms_mgm2.py`.
- DSA already calls both `finished()` and `stop()` at `stop_cycle`; its
  indefinite-run cases are by design (`stop_cycle=0`) or due to missing
  neighbor messages in the synchronous protocol.
- MaxSum has been checked against `verification_archive/papers/maxsum.pdf`,
  documented in `verification_archive/maxsum_paper_check.md`, and marked
  done / verified.
- MaxSum verification fixes in `pydcop/algorithms/maxsum.py`:
  - added `stop_cycle` support for fixed-cycle termination
  - corrected variable-to-factor normalization so integrated variable costs are
    included in the zero-sum Q-message normalization from the paper
  - updated shared-helper expectations in MaxSum and AMaxSum tests
- Recent focused MaxSum checks used:
  - `pytest tests/unit/test_algorithms_maxsum.py tests/unit/test_algorithms_amaxsum.py`
  - `ruff check pydcop/algorithms/maxsum.py tests/unit/test_algorithms_maxsum.py tests/unit/test_algorithms_amaxsum.py`
- MaxSum `--run_metrics` support depends on the standard cycle hook in
  `pydcop/infrastructure/computations.py:SynchronousComputationMixin`; this
  hook now fires when synchronous computations advance cycles.
- `pydcop/infrastructure/orchestrator.py` reports the completed orchestrator
  cycle for `cycle_change` metrics instead of the max cycle from per-agent
  snapshots, because many computations on one agent can be at slightly
  different cycle counts during aggregation.
- Recent focused MaxSum metrics checks used:
  - `pytest tests/unit/test_infra_synchronous_computation.py tests/unit/test_infra_orchestrator.py tests/unit/test_algorithms_maxsum.py`
  - `ruff check pydcop/infrastructure/computations.py pydcop/infrastructure/orchestrator.py tests/unit/test_infra_synchronous_computation.py tests/unit/test_infra_orchestrator.py`
  - `pydcop solve -a maxsum -d adhoc random.yaml -p stop_cycle:3 -c cycle_change --run_metrics /tmp/maxsum_cycle_metrics.csv`
- PuLP centralized solve now defaults to CBC instead of GLPK and accepts
  `-p solver:cbc|glpk` and `-p threads:N`. Metrics include
  `solver_backend` and `solver_threads`.
- CBC selection now prefers a `cbc` executable found on `PATH` via
  `COIN_CMD(path=...)`, falling back to PuLP's bundled `PULP_CBC_CMD` when no
  PATH CBC exists. On the current M1 laptop, `/Users/khoihd/miniconda3/bin/cbc`
  is ARM64 but does not recognize `-threads`; `/opt/homebrew/bin/cbc` is ARM64
  and does recognize `-threads`. Prefer Homebrew CBC first in `PATH` for
  threaded CBC runs.
- Recent focused PuLP checks used:
  - `pytest tests/unit/test_solvers_pulp.py tests/dcop_cli/test_solve_pulp.py`
  - `ruff check pydcop/solvers/pulp_solver.py pydcop/commands/solve.py tests/unit/test_solvers_pulp.py tests/dcop_cli/test_solve_pulp.py`
  - `python -m pydcop.dcop_cli solve -a pulp -p threads:2 tests/instances/graph_coloring1.yaml`
- MaxSum now has optional heuristic convergence stopping with
  `-p auto_stop:1 -p stable_cycles:N`. Each computation reports `finished()`
  after its local outgoing Q/R messages have remained stable for the configured
  number of cycles, but it keeps participating in synchronization until the
  orchestrator stops all computations together.
- `verification_archive/maxsum_paper_check.md` and
  `verification_archive/algorithm_paper_check_tracker.md` now mark MaxSum
  done / verified, document `auto_stop` as a heuristic local convergence stop,
  and clarify that both `min` and `max` objective support are repo-level
  generalizations of the paper's mostly maximization framing.
- Recent focused MaxSum auto-stop checks used:
  - `pytest tests/unit/test_algorithms_maxsum.py tests/unit/test_algorithms_amaxsum.py`
  - `ruff check pydcop/algorithms/maxsum.py tests/unit/test_algorithms_maxsum.py`
  - `python -m pydcop.dcop_cli -t 10 solve -a maxsum -p auto_stop:1 -p stable_cycles:1 -d oneagent tests/instances/graph_coloring1.yaml`

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
