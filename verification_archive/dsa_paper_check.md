# DSA Paper Check

## Source

- Paper: `verification_archive/papers/dsa.pdf`
- Title: "Distributed stochastic search and distributed breakout: properties,
  comparison and applications to constraint optimization problems in sensor
  networks"
- Authors: Weixiong Zhang, Guandong Wang, Zhao Xing, and Lars Wittenburg
- Implementation: `pydcop/algorithms/dsa.py`
- Status: In progress

## Review Scope

- The paper presents DSA as a family of synchronous stochastic local-search
  algorithms for DisCSP / DisCOP-style graph-coloring and sensor-network
  scheduling problems.
- This implementation supports variants `A`, `B`, and `C` from Table 1. It
  does not expose the paper's more aggressive `D` or `E` variants.
- The implementation applies DSA to generic DCOP relations on a constraints
  hypergraph, with both `min` and `max` modes. The paper discussion is framed
  mostly around conflict reduction / weighted graph coloring.

## Paper Contract

- Each agent initially chooses a random value.
- DSA is synchronous in principle: agents proceed in repeated steps and base
  each local decision on their own value plus known neighbor values.
- In each step, an agent sends its current value to neighbors if it changed in
  the previous step, receives new neighbor values if any, then selects its next
  value.
- `p` controls the probability of applying an allowed value change.
- Let `delta` be the best possible local conflict reduction and `v` a value
  achieving that reduction.
- DSA-A: if `delta > 0`, move to `v` with probability `p`; otherwise stay.
- DSA-B: same as A, plus if there is a conflict and `delta == 0`, move to a
  non-degrading value with probability `p`.
- DSA-C: same as B, plus if there is no conflict and `delta == 0`, move to an
  equal-quality value with probability `p`.

## Implementation Mapping

- `algo_params` exposes `variant`, `probability`, `p_mode`, and `stop_cycle`.
- `on_start()` randomly selects an initial value for computations with
  neighbors and sends `DsaMessage(current_value)` to all neighbors.
- `_on_value_msg()` stores the first value from each neighbor in
  `current_cycle`; additional values from the same neighbor are held in
  `next_cycle`.
- `evaluate_cycle()` waits until all neighbor values are available, computes
  the current local cost, finds local best values with `find_optimal()`, runs
  the selected DSA variant, advances the cycle, and sends the current value to
  neighbors unless `stop_cycle` has been reached.
- `variant_a()`, `variant_b()`, and `variant_c()` implement the paper's
  A/B/C value-change conditions.
- `probabilistic_change()` applies the probability threshold and randomly
  chooses among best values when a move is attempted.
- `exists_violated_constraint()` treats a constraint as violated when its
  current value is not the best achievable value for that relation according to
  the optimization mode.

## Current Findings

- The core A/B/C local value-selection behavior appears to match Table 1.
- The implementation sends a value message every cycle, not only after the
  value changed. This differs from Algorithm 1 and the paper's communication
  cost discussion, but it fits the implementation's synchronous wait-for-all
  neighbor-values design. This affects communication metrics and should be
  documented as an implementation/runtime adaptation if kept.
- `p_mode="arity"` is a repo-level extension not described in the paper.
- `stop_cycle` is a repo-level termination parameter. The paper assumes an
  external termination condition.
- `mode="max"` and generic N-ary constraints are repo-level extensions beyond
  the paper's graph-coloring presentation.

## Existing Coverage

- `tests/unit/test_algorithms_dsa.py` covers construction, communication and
  memory estimates, message properties, startup behavior, no-neighbor behavior,
  value-message routing, cycle evaluation, `stop_cycle`, variants A/B/C,
  probability threshold behavior, and violated-constraint detection.

## Follow-Up

- Decide whether the every-cycle value broadcast should be kept as an
  intentional deviation or changed to the paper's send-on-change behavior.
- Review focused tests for communication semantics once that decision is made.
- Tighten DSA docstrings after the verification decision, especially around
  `p_mode`, metrics, and the paper-vs-runtime communication behavior.
