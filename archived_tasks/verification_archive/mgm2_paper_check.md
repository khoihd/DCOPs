# MGM2 Paper Check

## Source

- Paper: `archived_tasks/verification_archive/papers/mgm.pdf`
- Title: "Distributed Algorithms for DCOP: A Graphical-Game-Based Approach"
- Authors: Rajiv T. Maheswaran, Jonathan P. Pearce, and Milind Tambe
- Implementation: `pydcop/algorithms/mgm2.py`

## Review Scope

- The paper is written for utility maximization. The implementation supports
  both `min` and `max`; this check accepts that as a repo-level generalization.
- Graph construction is treated as out of scope. The implementation runs on the
  constraints hypergraph and uses local neighbor messages.
- The paper presents binary coordination between neighboring agents. This check
  focuses on the 2-coordinated MGM-2 behavior in Algorithm 2.
- The check does not cover SCA-2, which is described in the same paper but is
  not implemented in `mgm2.py`.

## Paper Contract

- Each round starts with every agent broadcasting its current value to all
  neighbors.
- Each agent draws a random number and becomes an offerer if it is below the
  offerer threshold `q`.
- Offerers cannot accept offers. Each offerer chooses one random neighbor and
  sends that neighbor all coordinated value pairs that give the offerer local
  gain.
- Non-offerers act as receivers. A receiver evaluates incoming offers by adding
  the offerer's local gain to the receiver's local utility change and
  subtracting the partner-link gain to avoid double-counting.
- A receiver accepts the best positive coordinated gain when it is better than
  its unilateral gain; otherwise it rejects offers.
- After offers and replies, every agent sends a gain message. Uncommitted
  agents send unilateral gain; committed agents send coordinated global gain.
- Uncommitted agents use the MGM rule and move only if their gain is larger than
  all neighbor gains.
- Committed agents send their partner a go message when their coordinated gain
  beats competing neighbor gains; a committed agent changes only if it receives
  go from its partner.
- The paper states MGM-2 costs five communication cycles per round: value,
  offer, accept or reject, gain, then go or no-go.

## Implementation Mapping

- `GRAPH_TYPE = "constraints_hypergraph"` keeps MGM2 local to neighboring
  variable computations.
- `threshold` implements the paper's offerer probability `q`.
- `Mgm2ValueMessage`, `Mgm2OfferMessage`, `Mgm2ResponseMessage`,
  `Mgm2GainMessage`, and `Mgm2GoMessage` correspond to the five message phases
  in Algorithm 2.
- `_send_value()` broadcasts the current value and starts a new cycle.
- `_handle_value_messages()` waits for all neighbor values, chooses whether the
  computation is an offerer, chooses one random partner when offering, sends
  one real offer and fake non-offers to other neighbors, and computes the best
  unilateral move.
- `_compute_offers_to_send()` enumerates coordinated value pairs for the chosen
  partner and keeps pairs that improve the offerer's local cost or utility.
- `_find_best_offer()` evaluates received offers by combining the offerer's
  gain with the receiver-side change while filtering shared relations to avoid
  double-counting the partner link.
- `_handle_offer_messages()` rejects offers when already an offerer, otherwise
  accepts the best offer when it beats the unilateral gain according to the
  configured objective direction.
- `_handle_response_message()` commits an offerer when the selected partner
  accepts, then sends the resulting gain.
- `_handle_gain_messages()` applies the MGM rule for uncommitted moves and the
  go/no-go rule for committed coordinated moves.
- `_handle_go_message()` changes value only when the partner sent go and this
  computation also determined it can move.

## Verdict

The core MGM-2 message flow matches Algorithm 2: value, offer, accept or reject,
gain, then go or no-go. The implementation also captures the paper's key
double-counting rule when evaluating coordinated offers.

The implementation intentionally generalizes or extends the paper in these ways:

- It supports both minimization and maximization.
- It broadcasts fake non-offers to every non-partner neighbor so receivers can
  know when the offer phase is complete.
- It adds a `favor` parameter for coordinated versus unilateral tie behavior.
- It handles isolated variables by selecting their local optimum immediately.

## Caveats

- The implementation excludes the committed partner's gain when a committed
  agent compares coordinated gain against neighbor gains. This appears aligned
  with the paired move intent: partners send the same coordinated gain and must
  not block each other solely because of that shared gain. The paper pseudocode
  says `gain > max(neighborGains)` more tersely.
- As in MGM, minimization represents improvement as positive cost reduction and
  maximization as negative cost delta.
- The paper does not specify fake offer synchronization, message postponement,
  stop cycles, or tie handling.

## Implementation Fixes

- `_find_best_offer()` was corrected to subtract the current shared
  partner-relation cost before adding the offerer's local gain. Previously, the
  receiver excluded the new shared relation from its candidate-side cost but
  kept the old shared relation in `current_cost`, which over-counted
  coordinated gain by the old partner-link value.

## Existing Coverage

- `tests/unit/test_algorithms_mgm2.py` covers message properties, memory and
  communication estimates, startup behavior, local cost and best-value
  computation, offer creation, receiver-side best-offer selection in min and
  max modes, the paper's meeting-scheduling coordinated-move example,
  state transitions, response handling, go/no-go handling, gain comparisons,
  and clearing per-round state.
- API tests exercise MGM2 in solve-level graph-coloring scenarios.

## Follow-Up

- None currently required for MGM-2 paper correctness.
