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
  MixedDSA, and MaxSum.
- No next paper-verification target has been selected yet. AMaxSum and Dynamic
  MaxSum remain separate tracker items.
- Generated scratch files are currently untracked and intentionally not
  committed:
  - `dsa_max_metrics.csv`, `dsa_min_metrics.csv`
  - `mgm_max_metrics.csv`, `mgm_min_metrics.csv`
  - `mgm2_max_metrics.csv`, `mgm2_min_metrics.csv`
  - `maxsum_max_metrics.csv`
  - `random.yaml`
  - `verification_archive/.DS_Store`

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
  - `pytest tests/unit/test_algorithms_maxsum.py tests/unit/test_algorithms_amaxsum.py`
  - `ruff check pydcop/algorithms/maxsum.py tests/unit/test_algorithms_maxsum.py`
  - `python -m pydcop.dcop_cli -t 10 solve -a maxsum -p auto_stop:1 -p stable_cycles:1 -d oneagent tests/instances/graph_coloring1.yaml`

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
