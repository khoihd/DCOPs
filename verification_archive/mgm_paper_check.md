# MGM Paper Check

## Source

- Paper: `verification_archive/papers/mgm.pdf`
- Title: "Distributed Algorithms for DCOP: A Graphical-Game-Based Approach"
- Authors: Rajiv T. Maheswaran, Jonathan P. Pearce, and Milind Tambe
- Implementation: `pydcop/algorithms/mgm.py`

## Review Scope

- The paper is written for utility maximization. The implementation supports
  both `min` and `max`; this check accepts that as a repo-level generalization.
- Graph construction is treated as out of scope. The implementation runs on the
  constraints hypergraph and uses local neighbor messages.
- The paper presents pairwise DCOP constraints. The implementation accepts
  generic relation objects and hypergraph constraints; this is accepted unless
  it contradicts the local MGM logic.
- The check focuses on Algorithm 1 and the monotonicity argument for MGM.

## Paper Contract

- Each round starts with every agent broadcasting its current value to all
  neighbors.
- After receiving neighbor values, an agent computes the best unilateral move
  in the current context.
- The agent broadcasts a gain message containing the maximum local utility
  change available from that unilateral move.
- After receiving neighbor gains, the agent changes value only if its gain is
  larger than all neighbor gains.
- Ties may be broken by variable ordering or another method.
- The paper states MGM costs two communication cycles per round: value, then
  gain.
- The monotonicity proof depends on adjacent variables not moving in the same
  round and on selected moves having positive local gain.

## Implementation Mapping

- `GRAPH_TYPE = "constraints_hypergraph"` keeps MGM local to neighboring
  variable computations.
- `MgmValueMessage` carries the current value; `MgmGainMessage` carries the
  local gain and, for random tie-breaking, a random number.
- `on_start()` selects an initial value, then enters the value phase.
- `_send_value()` broadcasts `MgmValueMessage` to all neighbors and starts a
  new cycle.
- `_handle_value_message()` waits for all neighbor values, computes the current
  local cost when needed, calls `_compute_best_value()`, stores the candidate
  value, and sends a gain message.
- `_compute_best_value()` optimizes the local constraints sliced by the current
  neighbor context, matching the paper's best unilateral gain step.
- `_send_gain()` broadcasts the local gain to all neighbors.
- `_handle_gain_message()` waits for all neighbor gains and changes value only
  when this computation has the best gain according to the configured objective
  direction.
- `_break_ties()` implements the paper's open tie-breaking choice using either
  lexicographic variable names or random numbers.

## Preliminary Verdict

The core MGM message flow matches Algorithm 1: value broadcast, local unilateral
gain computation, gain broadcast, and a move only when the local gain wins
against neighbors.

The implementation intentionally generalizes the paper in these ways:

- It supports both minimization and maximization.
- It supports relation and variable cost helpers outside the paper's pairwise
  utility notation.
- It implements explicit tie-breaking modes.
- It handles isolated variables by selecting their local optimum immediately.

## Caveats

- The implementation represents minimization gains as positive cost reductions
  and maximization gains as negative cost deltas. This is consistent internally,
  but differs from the paper's utility-increase wording.
- The paper's monotonicity proof assumes only positive gain moves. The code
  avoids changing to a worse local value, but tie-breaking can still select a
  no-op candidate if all gains tie at zero.
- The paper does not specify runtime message postponement, stopping hooks, or
  initial value selection.

## Existing Coverage

- `tests/unit/test_algorithms_mgm.py` covers message properties, memory and
  communication estimates, startup behavior, postponed messages, value to gain
  computation, min and max gain handling, stop cycles, and random tie-breaking.
- API and CLI tests exercise MGM in solve-level graph-coloring scenarios.

## Follow-Up

- Review whether existing unit tests explicitly cover the paper monotonicity
  condition that adjacent agents with equal gain do not both move.
- Add a small hand-checkable two-variable or three-variable monotonicity case if
  that behavior is not already covered directly.
