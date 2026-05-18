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

- No active interrupted request is pending.
- Recent work on `main`:
  - `b2bc4f7` updates these continuity notes.
  - `99c06c1` updates `todo.md` follow-ups: output parent-directory support is
    marked done, instance generator review is marked done with multi-instance
    generation delegated to scripts using `--output`, and PD-DCOP support is
    tracked as the next larger TODO area.
  - `0ca82ec` adds shared command output helpers in
    `pydcop/commands/_utils.py` using `pathlib.Path` with
    `mkdir(parents=True, exist_ok=True)`. Command and generator output writes
    now create missing parent directories for nested `--output`, run metrics,
    and end metrics paths.
  - `6a0e442` updates `todo.md` notes around PuLP HiGHS naming, algorithm
    termination options, and generator review wording.
- Recent checks for the output-directory work:
  - `ruff check` on touched command/generator files and
    `tests/unit/test_commands_utils.py`.
  - `pytest tests/unit/test_commands_utils.py
    tests/unit/test_commands_solve.py tests/unit/test_commands_orchestrator.py`
  - `pytest tests/dcop_cli/test_generate_randomgraph.py
    tests/dcop_cli/test_solve_pulp.py`
  - Smoke checks for nested `--output` paths with `generate random_graph` and
    `solve --algo pulp`; scratch `.tmp-output` was removed.

## Repository Notes

- Paper verification is tracked in
  `archived_tasks/verification_archive/algorithm_paper_check_tracker.md`.
  Detailed notes live in `archived_tasks/verification_archive/*_paper_check.md`.
- Verified/done paper checks include DPOP, MGM, MGM2, DBA, GDBA, DSA, ADSA,
  MixedDSA, MaxSum, AMaxSum, Dynamic MaxSum, NCBB, and SyncBB.
- Paper verification notes and source PDFs now live under
  `archived_tasks/verification_archive/`.
- Optimization archive notes live under `archived_tasks/optimization_archive/`.
- PD-DCOP reference material lives under `pddcop/`:
  - `pddcop/pddcop_jair_key_points.md`
  - `pddcop/pddcop_java_key_points.md`
  - `pddcop/pddcop_java/`
- Generated CSV/YAML experiment files are ignored via `.gitignore`.

## PuLP/HiGHS/CBC

- `pydcop solve -a pulp <dcop_file>` uses the centralized exact PuLP solver in
  `pydcop/solvers/pulp_solver.py`.
- The PuLP solve path skips distributed graph construction, distribution,
  agents, and message metrics.
- The solver creates one binary choice variable per DCOP variable value and
  one binary tuple variable per relation assignment, then optimizes relation
  values plus variable costs for `objective: min|max`.
- PuLP solve defaults to HiGHS and accepts:
  - `-p solver:highs|cbc|glpk`
  - `-p threads:N`
- Default HiGHS behavior:
  - plain `pydcop solve -a pulp ...` reports `solver_backend: highs`
  - default thread count is `os.cpu_count() or 1`
  - on the current M1 laptop this reports `solver_threads: 8`
  - passing a concrete thread count to PuLP's `HiGHS_CMD` enables HiGHS
    `parallel=on`
  - `msg` remains `False`, so solver logs do not corrupt JSON stdout
- PuLP metrics include `solver_backend`, `solver_threads`, `solver_status`,
  and `solver_solution_status`.
- CBC via PuLP can report coarse `solver_status: Optimal` while
  `solver_solution_status` is only `Solution Found`; the CLI maps that to
  top-level `status: FEASIBLE`. Only `Optimal Solution Found` maps to
  `status: FINISHED`.
- CBC selection prefers a `cbc` executable found on `PATH` via
  `COIN_CMD(path=...)`, falling back to PuLP's bundled `PULP_CBC_CMD`.
- On the current M1 laptop:
  - `/opt/homebrew/bin/highs` is installed and available on `PATH`
  - `/Users/khoihd/miniconda3/bin/cbc` is ARM64 but does not recognize
    `-threads`
  - `/opt/homebrew/bin/cbc` is ARM64 and recognizes `-threads`
  - Homebrew CBC is currently the `cbc` found first on `PATH`

## Algorithm Notes

- MaxSum and AMaxSum are verified against the Farinelli et al. Max-Sum paper.
  Both support `min` and `max` as pyDcop generalizations.
- MaxSum supports `stop_cycle`, optional `auto_stop` / `stable_cycles`, and
  `--run_metrics` with `--collect_on cycle_change`.
- AMaxSum reuses MaxSum parameters but defaults `auto_stop` to `1` and requires
  either `stop_cycle > 0` or `auto_stop:1`. Its `stop_cycle` is a local async
  update limit, not a globally synchronized round count.
- Dynamic MaxSum has no separate paper source found; it is documented as a
  pyDcop-specific dynamic factor-graph extension around AMaxSum/MaxSum.
  `pydcop/algorithms/maxsum_dynamic.py` is a low-level helper module, not a
  normal CLI algorithm entry point.
- NCBB is implemented in `pydcop/algorithms/ncbb.py`, including
  branch-specific descendants, lower-bound delta propagation, subtree search,
  pruning, result selection, STOP propagation, and max support via internal
  objective negation.
- SyncBB is implemented in `pydcop/algorithms/syncbb.py` as a pyDcop additive
  weighted-DCOP adaptation of SBB. Objective direction is inferred from the
  DCOP instance objective.
- MGM and DSA do not currently implement a global convergence stop such as
  "all computations kept the same value this cycle"; they rely on
  `stop_cycle`, timeout, or external stop.

## Generators And CLI

- Generate YAML DCOP instances with `python -m pydcop.dcop_cli generate ...`.
- `--output <file>` is a global option, so it must appear before the command:
  `python -m pydcop.dcop_cli --output out/file.yaml generate random_graph ...`.
- Command/generator output paths now create missing parent directories.
- Live generator types include `graph_coloring`, `random_graph`, `meetings`,
  `ising`, `agents`, `scenario`, `mixed_problem`, `small_world`, `iot`, and
  `secp`.
- `small_world` is incomplete/experimental; `scenario` is for Dynamic DCOPs.
- `meetings`, `secp`, `graph_coloring`, `random_graph`, `ising`, and
  `mixed_problem` default generated agents to capacity `999` when their
  generator creates agents and exposes `--capacity`; explicit `--capacity N`
  overrides it.
- `graph_coloring`, `random_graph`, `ising`, `meetings`, and `secp` have
  optional `--seed` arguments. `iot` already had optional seed behavior.
- A deterministic random-graph fixture lives at
  `tests/instances/random_graph_6_3_0.7.yaml`; it has 6 variables, 14
  constraints, 6 agents, and PuLP optimum cost `35`.

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

## Important Paths

- Core model/YAML: `pydcop/dcop/`.
- Algorithms: `pydcop/algorithms/`.
- Computation graphs: `pydcop/computations_graph/`.
- Runtime/agents/communication: `pydcop/infrastructure/`.
- Centralized solvers: `pydcop/solvers/`.
- CLI: `pydcop/commands/`, `pydcop/dcop_cli.py`, `pydcop/pydcop`.
- Generators: `pydcop/commands/generators/`.
- Tests: `tests/unit/`, `tests/api/`, `tests/dcop_cli/`, `tests/instances/`.
- Known cases: `tests/utils/known_instances.py`.
- Archived optimization notes: `archived_tasks/optimization_archive/`.
- Paper verification notes: `archived_tasks/verification_archive/`.
- PD-DCOP reference material: `pddcop/`.

## Open Questions

- What is the primary long-term execution path: CLI, library API, or both?
- Which modules are active and worth modernizing first versus legacy?
- Should package/module naming eventually move away from `pydcop`?
