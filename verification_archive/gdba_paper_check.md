# GDBA Paper Check

## Source

- Paper: `verification_archive/papers/gdba.pdf`
- Title: "Distributed Breakout: Beyond Satisfaction"
- Authors: Steven Okamoto, Roie Zivan, and Aviv Nahon
- Implementation: `pydcop/algorithms/gdba.py`
- Status: Done / Verified

## Review Scope

- The paper defines GDBA for general-valued DCOP minimization with binary
  constraints. The implementation supports `min` and `max` modes and generic
  relation objects; this check focuses on the paper's minimization logic.
- The paper's 24 variants are determined by three dimensions: modifier manner
  (`A` additive or `M` multiplicative), violation definition (`NZ`, `NM`, or
  `MX`), and increase scope (`E`, `C`, `R`, or `T`).
- The check focuses on Algorithm 1 and the helper functions `EFFCOST`,
  `ISVIOLATED`, and `INCREASEMOD`.

## Paper Contract

- Each agent initializes all modifiers to zero, chooses an initial value, and
  sends that value to neighbors.
- Each iteration has a value phase and an improve phase.
- After receiving all neighbor values, an agent computes its current effective
  local cost, its best unilateral value, and its possible improvement.
- An agent sends its improvement to all neighbors.
- If the agent can improve and has the best improvement in its neighborhood, it
  changes to its selected value.
- If the agent cannot improve and no neighbor can improve, it is in a
  quasi-local minimum and increases modifiers for currently violated
  constraints.
- `A` manner uses `Fij(xi, xj) + Mij(xi, xj)`.
- `M` manner uses `Fij(xi, xj) * (Mij(xi, xj) + 1)`.
- `NZ`, `NM`, and `MX` violation definitions are based on the base constraint
  cost: nonzero, non-minimum, and maximum respectively.
- Increase scopes are:
  - `E`: the current entry `(xi, xj)`.
  - `C`: all local values with the neighbor's current value fixed.
  - `R`: the current local value with all neighbor values.
  - `T`: the whole table.

## Implementation Mapping

- `algo_params` exposes the paper's three variant dimensions:
  `modifier`, `violation`, and `increase_mode`. It also exposes the
  repo-level `stop_cycle` parameter for fixed-cycle runs and metrics
  collection.
- Initialization converts constraints to `NAryMatrixRelation`, records per-table
  minimum and maximum base costs, and initializes modifier tables.
- `on_start()` selects an initial value and sends `GdbaOkMessage` to neighbors.
- `_handle_ok_message()` waits for all neighbor values, computes current
  evaluation and best local improvement, then sends `GdbaImproveMessage`.
- `_compute_best_improvement()` searches the variable domain for the locally
  best effective cost according to the configured optimization mode.
- `_eff_cost_for_assignment()` implements additive and multiplicative effective
  costs. For `M`, the implementation stores modifiers starting at `1` and
  multiplies by that stored value, which is equivalent to the paper's
  zero-based `Mij + 1` formulation.
- `_is_value_violated()` implements `NZ`, `NM`, and `MX` using base relation
  values and the recorded table minimum/maximum.
- `_handle_improve_message()` implements the improvement winner check and
  quasi-local-minimum breakout when all local and neighbor improvements are
  zero.
- `_increase_cost()` implements `E`, `C`, `R`, and `T`. During this check, `C`
  and `R` were corrected to match the paper's row/column convention.

## Verdict

The core GDBA minimization logic now matches Algorithm 1 and the paper's three
variant dimensions. The implementation supports the paper's additive and
multiplicative effective costs, all three violation definitions, and all four
increase scopes.

One paper mismatch was found and fixed during this check: the implementation's
`R` and `C` increase scopes were swapped. `C` now increases all local values
with the neighbor context fixed, and `R` now increases the current local value
across possible neighbor contexts.

## Caveats

- The implementation extends the paper's binary-constraint presentation to
  generic relations and constraints hypergraphs.
- The paper is written for minimization. The implementation also exposes
  `mode="max"` as a repo-level extension; that extension is not verified
  against the paper.
- The paper assumes a fixed iteration limit or an anytime framework. The
  implementation now provides a `stop_cycle` parameter for fixed-cycle runs,
  while still also supporting the surrounding runtime timeout/termination
  behavior.
- For no-neighbor computations, the implementation selects a local value and
  finishes immediately. This is outside the paper's neighbor-exchange focus.

## Existing Coverage

- `tests/unit/test_algorithms_gdba.py` covers construction, message classes,
  effective cost calculation for `A` and `M`, violation definitions, all
  increase scopes, startup behavior, postponed messages, improvement handling,
  quasi-local modifier increase, tie-breaking, and `stop_cycle` behavior.

## Follow-Up

- None currently required for core GDBA paper correctness.
