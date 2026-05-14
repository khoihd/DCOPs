# Main Continuity

## Project

- DCOP is a private continuation derived from Orange-OpenSource pyDcop.
- Public API compatibility is not a goal unless explicitly requested; prefer
  clear internal behavior for this private repo.
- Work conservatively: small targeted changes, behavior preserved by default,
  no new dependencies or broad refactors without approval.
- Keep original BSD 3-Clause attribution intact.

## Environment

- Use the active shell environment directly.
- Run focused tests with `pytest path/to/test_file.py`.
- Run focused lint with `ruff check path/to/file.py`; use `ruff check .` only
  for broader checks.
- Run CLI commands through the active interpreter when useful, e.g.
  `python -m pydcop.dcop_cli ...`.
- Plain `pytest` excludes tests marked `perf`; run performance tests explicitly
  with `pytest -m perf` or `make perf`.
- For local docs builds, use
  `SPHINXOPTS="-D autosummary_generate=0" make html` to avoid rewriting
  committed autosummary files.
- Ruff is configured in `pyproject.toml` with `target-version = "py311"` and
  pyupgrade checks.

## Current State

- Paper verification is tracked in
  `verification_archive/algorithm_paper_check_tracker.md`; detailed notes live
  in `verification_archive/*_paper_check.md`.
- Verified/done paper checks include DPOP, MGM, MGM2, DBA, GDBA, DSA, ADSA,
  MixedDSA, MaxSum, AMaxSum, Dynamic MaxSum, NCBB, and SyncBB.
- Dynamic MaxSum is marked `Done / No Separate Paper Source`, documented in
  `verification_archive/maxsum_dynamic_paper_check.md`, and treated as a
  pyDcop-specific dynamic factor-graph extension around AMaxSum/MaxSum.
- NCBB is marked `Done / Verified`, documented in
  `verification_archive/ncbb_paper_check.md`, with
  `verification_archive/papers/ncbb.pdf` committed as the source paper.
  Commit `3dfa63d` implemented NCBB search and max support.
- SyncBB verification and follow-up implementation are committed. The
  implementation supports both `objective: min` and `objective: max` by
  inferring objective direction from the DCOP instance, not from algorithm
  parameters.
- `todo.md` verification status edits have been committed.
- Recent TODO cleanups:
  - `pydcop/computations_graph/factor_graph.py` slices external variables out
    of factor constraints before graph construction, so external variable
    references do not create dangling factor links.
  - `pydcop/algorithms/mgm.py` has updated parameter documentation and a CLI
    example for running MGM with `stop_cycle` and `break_mode`.
  - MaxSum `factor_costs_for_var` now supports optional `valid_assignments`
    filtering for caller-provided valid tuples (`e2005f0`).
  - Exact `-float("inf")` occurrences were changed to explicit
    `float("-inf")` literals (`cbcea82`).
  - `ilp_fgdp` and `adhoc` repair hooks now clearly raise
    `ImpossibleDistributionException` instead of carrying TODO stubs because
    dynamic repair is unsupported for those methods (`be5c615`, `f3c009b`).
  - `gh_cgdp` tracks remaining capacity explicitly during greedy/backtracking
    distribution, including fixed placements and backtracking resets
    (`ef8db77`).
  - `oilp_cgdp` handles unique zero-hosting-cost fixed computations outside
    ILP variables, supports fixed-only distributions without GLPK, and rejects
    fixed capacity overrun (`3d5e38b`).
  - `pydcop commands run` no longer exposes command-level `--infinity`;
    local thread/process runners own the default `float("inf")`
    (`9aa370d`).
  - Recent CLI/generator/runtime TODO/FIXME cleanup commits on `main`:
    - `43a867b` adds intentional PEAV meeting constraints.
    - `32939f1` validates command module loading.
    - `d424b91` exposes hosted replicas in UI agent data.
    - `500c105` handles add-agent scenario events explicitly.
    - `76ae24e` adds meeting scheduling model variants.
    - `a93f3e0` documents AMaxSum example results.
    - `6bb63bd` clarifies dynamic MaxSum factor removal state.
    - `24a2662` documents MaxSum example results.
    - `0efb3a9` fixes comhost backtracking candidates.
    - `73ca0be` uses replica distribution algo params and default infinity.
    - `a34653c` uses orchestrator default infinity and stops the metrics
      collector.
    - `59881a5` stops the solve metrics collector cleanly.
    - `c6c208f` serializes meeting generator stdout as YAML documents.
    - `d88de73` stops the shared command metrics collector cleanly.
    - `4e1d05d` makes infrastructure run use symbolic infinity by default.
    - `8db15ef` tracks repair computations explicitly instead of filtering
      them by generated `B...` names.
    - `33eb7e7` gates scenario events on explicit completion instead of a
      fixed 20-second retry delay.
    - `2fa1ee5` removes the stale commented in-process address hack from
      communication.
    - `7968194` updates `todo.md`, marking TODO/FIX cleanup done and adding
      the multi-threading support follow-up.
  - Targeted checks used across this batch included the relevant unit/API
    tests, focused `ruff check` commands, and representative CLI help/solve
    invocations.
- No active interrupted TODO/FIXME request is pending. The last completed
  code cleanup request was the `pydcop/infrastructure/communication.py` FIXME
  removal in `2fa1ee5`; `todo.md` was committed afterward in `7968194`.
- Recent targeted checks:
  - `pytest tests/unit/test_infra_agents.py`
  - `ruff check pydcop/infrastructure/agents.py tests/unit/test_infra_agents.py`
  - `pytest tests/unit/test_infra_orchestrator.py`
  - `ruff check pydcop/infrastructure/orchestrator.py tests/unit/test_infra_orchestrator.py`
  - `pytest tests/unit/test_infra_communication.py`
  - `ruff check pydcop/infrastructure/communication.py`
- Generated scratch files are currently untracked and intentionally not
  committed:
  - `dsa_max_metrics.csv`, `dsa_min_metrics.csv`
  - `mgm_max_metrics.csv`, `mgm_min_metrics.csv`
  - `mgm2_max_metrics.csv`, `mgm2_min_metrics.csv`
  - `maxsum_max_metrics.csv`
  - `random.yaml`

## PuLP/CBC

- `pydcop solve -a pulp <dcop_file>` uses the centralized exact PuLP solver in
  `pydcop/solvers/pulp_solver.py`.
- The PuLP solve path skips distributed graph construction, distribution,
  agents, and message metrics.
- The solver creates one binary choice variable per DCOP variable value and
  one binary tuple variable per relation assignment, then optimizes relation
  values plus variable costs for `objective: min|max`.
- PuLP solve now defaults to CBC and accepts:
  - `-p solver:cbc|glpk`
  - `-p threads:N`
- PuLP metrics include `solver_backend`, `solver_threads`,
  `solver_status`, and `solver_solution_status`.
- CBC via PuLP can report coarse `solver_status: Optimal` even when the
  separate solution status is only `Solution Found` after a timeout or manual
  stop. The CLI maps this case to top-level `status: FEASIBLE`, meaning the
  assignment is valid but not proven optimal. Only `solver_solution_status:
  Optimal Solution Found` maps to top-level `status: FINISHED`.
- On the untracked `random.yaml` instance (`RandomGraph_30_10_0.4`, max),
  `-t 20` and `-t 60` with `-p threads:4` found objective/cost `1013` with
  `status: FEASIBLE`, so `1013` is a feasible incumbent, not a certified
  optimum.
- CBC selection prefers a `cbc` executable found on `PATH` via
  `COIN_CMD(path=...)`, falling back to PuLP's bundled `PULP_CBC_CMD` when no
  PATH CBC exists.
- On the current M1 laptop:
  - `/Users/khoihd/miniconda3/bin/cbc` is ARM64 but does not recognize
    `-threads`
  - `/opt/homebrew/bin/cbc` is ARM64 and recognizes `-threads`
  - Prefer Homebrew CBC first in `PATH` for threaded CBC runs.
- Relevant checks used recently:
  - `pytest tests/unit/test_solvers_pulp.py tests/dcop_cli/test_solve_pulp.py`
  - `ruff check pydcop/solvers/pulp_solver.py pydcop/commands/solve.py tests/unit/test_solvers_pulp.py tests/dcop_cli/test_solve_pulp.py`
  - `python -m pydcop.dcop_cli solve -a pulp -p threads:2 tests/instances/graph_coloring1.yaml`

## MaxSum

- MaxSum has been checked against `verification_archive/papers/maxsum.pdf`,
  documented in `verification_archive/maxsum_paper_check.md`, and marked
  done / verified in the tracker.
- Current MaxSum behavior:
  - supports both `min` and `max` objectives as repo-level generalizations of
    the paper's mostly maximization framing
  - supports fixed-cycle stop with `-p stop_cycle:N`
  - supports optional heuristic convergence stop with
    `-p auto_stop:1 -p stable_cycles:N`
  - defaults `start_messages` to `all`
  - keeps computations participating in synchronization after local
    auto-stop notification until the orchestrator stops all computations
  - supports `--run_metrics` with `--collect_on cycle_change`
- MaxSum verification/runtime fixes included:
  - corrected variable-to-factor normalization so integrated variable costs are
    included in the zero-sum Q-message normalization
  - added `stop_cycle`
  - added `auto_stop` / `stable_cycles`
  - fixed synchronous cycle metrics so the runtime row uses the completed
    orchestrator cycle
- Relevant checks used recently:
  - `pytest tests/unit/test_algorithms_maxsum.py tests/unit/test_algorithms_amaxsum.py tests/unit/test_algorithms_objects.py`
  - `ruff check pydcop/algorithms/maxsum.py pydcop/algorithms/amaxsum.py tests/unit/test_algorithms_maxsum.py tests/unit/test_algorithms_amaxsum.py`
  - `python -m pydcop.dcop_cli -t 10 solve -a maxsum -p auto_stop:1 -p stable_cycles:1 -d oneagent tests/instances/graph_coloring1.yaml`
  - `python -m pydcop.dcop_cli -t 10 solve -a maxsum -p noise:0 -p stop_cycle:2 -d oneagent tests/instances/graph_coloring1.yaml`

## AMaxSum

- AMaxSum has been checked against `verification_archive/papers/maxsum.pdf`,
  documented in `verification_archive/amaxsum_paper_check.md`, and marked
  done / verified in the tracker.
- The Farinelli et al. Max-Sum paper explicitly describes asynchronous local
  updates, so `pydcop/algorithms/amaxsum.py` uses the same paper source as
  synchronous MaxSum.
- AMaxSum reuses MaxSum parameters but overrides `auto_stop` to default to `1`
  and requires either `stop_cycle > 0` or `auto_stop:1`.
- AMaxSum defaults `start_messages` to `all`.
- `stop_cycle` is interpreted as a local async update limit, not a globally
  synchronized round count. Variable computations increment the local count for
  each processed factor message; factor computations increment it only when
  they have enough variable messages to run a real factor update.
- `auto_stop` and `stable_cycles` are interpreted as coordinated async
  stability: computations report `finished()` after enough stable local updates
  but keep processing messages until the orchestrator sees every computation
  stable and stops the run. If a later message changes an outgoing message,
  AMaxSum reports `finished("running")` so the orchestrator clears its
  finished state.
- A quiet-period check lets an AMaxSum computation report stable when its last
  changed outgoing message does not trigger another incoming update.
- The generic computation finished management message now carries a `status`
  field; existing algorithms still call `finished()` with the default
  `"finished"` status.
- `SAME_COUNT` remains the resend/suppression throttle.
- Relevant checks used recently:
  - `pytest tests/unit/test_algorithms_amaxsum.py tests/unit/test_infra_orchestrator.py`
  - `pytest tests/unit/test_algorithms_amaxsum.py tests/unit/test_infra_orchestrator.py tests/unit/test_infra_agents.py tests/unit/test_infra_orchestratedagents.py`
  - `ruff check pydcop/algorithms/__init__.py pydcop/commands/_utils.py pydcop/algorithms/amaxsum.py tests/unit/test_algorithms_amaxsum.py`
  - `ruff check pydcop/algorithms/amaxsum.py pydcop/infrastructure/computations.py pydcop/infrastructure/orchestratedagents.py pydcop/infrastructure/orchestrator.py tests/unit/test_algorithms_amaxsum.py tests/unit/test_infra_orchestrator.py`
  - `python -m pydcop.dcop_cli -t 10 solve -a amaxsum -p noise:0 -d oneagent tests/instances/graph_coloring1.yaml`
  - `python -m pydcop.dcop_cli -t 10 solve -a amaxsum -p noise:0 -p auto_stop:0 -d oneagent tests/instances/graph_coloring1.yaml` exits early with the expected parameter error unless `stop_cycle` is set.

## Dynamic MaxSum

- Dynamic MaxSum has no separate paper source found. Contextual sources are
  Rust/Picard/Ramparany dynamic deployment/resilience papers plus the base
  Farinelli et al. Max-Sum paper for Q/R equations.
- `pydcop/algorithms/maxsum_dynamic.py` is a low-level helper module, not a
  normal CLI algorithm entry point: it has no `GRAPH_TYPE`, `algo_params`, or
  `build_computation()`.
- Current behavior is documented in
  `verification_archive/maxsum_dynamic_paper_check.md` and marked
  `Done / No Separate Paper Source` in the tracker.
- Recent review fixes:
  - retained variables receive refreshed factor-to-variable costs after a
    dynamic factor scope change
  - forced dynamic factor sends update `_prev_messages`, keeping stable-message
    suppression state aligned with messages sent outside the normal AMaxSum
    receive loop
  - variable-side `ADD` handling is idempotent for repeated `ADD` messages from
    the same factor
- Relevant checks used recently:
  - `pytest tests/unit/test_algorithms_dynamic_maxsum.py`
  - `pytest tests/unit/test_algorithms_dynamic_maxsum.py tests/unit/test_algorithms_amaxsum.py tests/unit/test_algorithms_maxsum.py`
  - `ruff check pydcop/algorithms/maxsum_dynamic.py tests/unit/test_algorithms_dynamic_maxsum.py`

## NCBB

- NCBB has been checked against `verification_archive/papers/ncbb.pdf`,
  documented in `verification_archive/ncbb_paper_check.md`, and marked
  `Done / Verified` in the tracker.
- The paper is "No-Commitment Branch and Bound Search for Distributed
  Constraint Optimization" by Anton Chechetka and Katia Sycara.
- `pydcop/algorithms/ncbb.py` now implements initialization and the main
  branch-and-bound search loop from Figures 1 and 2, including
  child-specific constrained descendants, lower-bound delta propagation,
  subtree search, pruning, result selection, and STOP propagation.
- `PseudoTreeNode.branch_descendants` in
  `pydcop/computations_graph/pseudotree.py` records the paper's
  `descendants[child]` structure for NCBB.
- `memory_footprint_estimate()` and `communication_load()` are implemented
  with polynomial-space / constant-message-size estimates.
- The paper is minimization-only, but this implementation supports
  `objective: max` as a pyDcop extension by minimizing the negated objective
  internally.
- NCBB has no objective-specific `algo_params`; objective direction is inferred
  from the DCOP instance objective via `AlgorithmDef.mode`.
- NCBB requires finite-domain variables and binary constraints. It does not
  require NCBB-specific YAML fields beyond the usual problem definition,
  agents/distribution, and `objective: min|max`.
- Relevant checks used recently:
  - `pytest tests/unit/test_algorithms_ncbb.py tests/unit/test_graph_pseudotree.py`
  - `ruff check pydcop/algorithms/ncbb.py tests/unit/test_algorithms_ncbb.py`
  - `python -m pydcop.dcop_cli -t 10 solve -a ncbb -d oneagent tests/instances/graph_coloring1.yaml`
  - `python -m pydcop.dcop_cli -t 10 solve -a ncbb -d oneagent tests/instances/graph_coloring_tuto_max.yaml`

## SyncBB

- SyncBB has been checked against `verification_archive/papers/syncbb.pdf`,
  documented in `verification_archive/syncbb_paper_check.md`, and marked
  `Done / Verified with documented pyDcop extensions` in the tracker.
- The paper is "Distributed Partial Constraint Satisfaction Problem" by
  Katsutoshi Hirayama and Makoto Yokoo.
- The paper's SBB solves DMCSPs by minimizing the max per-agent number of
  violated constraints; `pydcop/algorithms/syncbb.py` is a pyDcop adaptation
  for additive weighted DCOP objectives and supports both `min` and `max`.
- SyncBB has no objective-specific `algo_params`; objective direction is
  inferred from the DCOP instance objective via `AlgorithmDef.mode`.
- Verification fixes:
  - forward-token handling now adopts better received bounds before local search
  - `get_next_assignment()` no longer returns a candidate that passed only a
    prefix of the path before a later bound check failed
  - max-mode support explicitly avoids pruning a candidate from partial utility
    alone, because later variables may make that branch optimal
  - explicit `memory_footprint_estimate()` and `communication_load()` estimates
    now account for SyncBB path-token payloads and fixed-order communication
- Relevant checks used recently:
  - `pytest tests/unit/test_algorithms_syncbb.py`
  - `ruff check pydcop/algorithms/syncbb.py tests/unit/test_algorithms_syncbb.py`

## Generator And Docs Notes

- Generate YAML DCOP instances with
  `python -m pydcop.dcop_cli generate ...`; global `--output <file>` writes
  output to a file.
- Live generator types include `graph_coloring`, `random_graph`, `meetings`,
  `ising`, `agents`, `scenario`, `mixed_problem`, `small_world`, `iot`, and
  `secp`.
- `small_world` is incomplete/experimental; `scenario` is for Dynamic DCOPs.
- A deterministic random-graph fixture lives at
  `tests/instances/random_graph_6_3_0.7.yaml`; it has 6 variables, 14
  constraints, 6 agents, and PuLP optimum cost `35`.
- `docs/conf.py` uses `bibtex_bibfiles = ["biblio.bib"]`, `language = "en"`,
  and no longer points at a missing `_static` directory.
- `Makefile` supports `SPHINXOPTS` and `make html` as an alias for `make doc`.
- Algorithm reference docs were updated with verified-behavior notes for DBA,
  GDBA, DSA, ADSA, MaxSum, AMaxSum, and MixedDSA. The docs build used
  `SPHINXOPTS="-D autosummary_generate=0" make html` and succeeded with only
  existing multiple-toctree consistency notices.

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
- SyncBB behavior tests cover direct message flow, pruning, termination, and
  solve-level min/max outcomes.
- MGM and DSA do not currently implement a global convergence stop such as
  "all computations kept the same value this cycle"; they rely on
  `stop_cycle`, timeout, or external stop.

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
