# DBA Paper Check

## Source

- Paper: `verification_archive/papers/dba.pdf`
- Title: "Distributed Breakout Algorithm for Solving Distributed Constraint
  Satisfaction Problems"
- Authors: Makoto Yokoo and Katsutoshi Hirayama
- Implementation: `pydcop/algorithms/dba.py`

## Review Scope

- The paper is for distributed CSPs, not optimization DCOPs. The implementation
  accepts only `min` mode and treats costs greater than or equal to `infinity`
  as violated constraints.
- The paper assumes one variable per agent and binary constraints. The
  implementation runs on the constraints hypergraph and can slice generic
  relation objects; this is treated as a repo-level generalization unless it
  contradicts DBA's local message logic.
- The check focuses on the two-mode DBA algorithm in Figure 2: `ok?`,
  `improve`, breakout weight updates, move permission, and termination
  detection.

## Paper Contract

- Each agent randomly selects an initial value, sends `ok?` messages to all
  neighbors, and alternates between wait-ok and wait-improve modes.
- An `ok?` message carries the sender's current value.
- After receiving `ok?` messages from all neighbors, an agent computes its
  current evaluation value, best unilateral improvement, and best new value.
- An `improve` message carries the sender's possible improvement, current
  evaluation value, and termination counter.
- Adjacent agents compare improvement values. An agent may change value only if
  no neighbor has a larger improvement; equal improvements are separated by a
  fixed ordering.
- A quasi-local minimum is detected when the agent has no positive improvement
  and no neighbor can improve. In that case, the agent increases the weights of
  the currently violated variable-value pairs.
- Termination is detected by propagating a counter through improve messages:
  when an agent and all agents within `max_distance` are consistent, a solution
  is known and the algorithm terminates.
- Messages received in the wrong phase are postponed until the matching phase.

## Implementation Mapping

- `DbaOkMessage`, `DbaImproveMessage`, and `DbaEndMessage` cover the paper's
  message contents plus a repo-specific explicit end notification.
- `on_start()` chooses a random initial value, sends it to neighbors, and enters
  wait-ok mode.
- `_handle_ok_message()` records neighbor values, waits for all neighbors,
  slices local constraints by the received context, computes the current
  evaluation, and sends an improve message.
- `improve()` computes the best unilateral assignment, sets `can_move`,
  `quasi_local_minimum`, `consistent`, `my_improve`, and `new_value`, then
  broadcasts `DbaImproveMessage`.
- `_handle_improve_message()` applies the improvement comparison and
  lexicographic tie-break, folds neighbor termination counters with `min()`,
  marks the local neighborhood inconsistent when a neighbor reports nonzero
  evaluation, and waits for all neighbor improve messages.
- `_send_ok()` implements the paper's end-of-round action: increment
  termination counter when consistent, stop when `max_distance` is reached,
  otherwise increase breakout weights in quasi-local minima, move if permitted,
  and broadcast the current value.
- Wrong-phase `ok?` and `improve` messages are stored in postponed-message
  queues and replayed when the corresponding phase starts.

## Verdict

The core two-phase DBA message loop matches the paper, and the normal
termination path preserves the `finished` state and stops the computation.

Breakout weights are stored per exact violated assignment tuple, matching the
paper's "pair of variable values" weighting for binary CSPs while extending the
same idea to this implementation's generic relation support. For example,
increasing the weight for graph-coloring violation `(x1=R, x2=R)` does not
increase the weight for `(x1=G, x2=G)` on the same constraint.

## Caveats

- The implementation extends the paper's binary-CSP presentation to generic
  relations by slicing local constraints with the current neighbor context.
- DBA remains a satisfaction algorithm. It uses finite relation values only to
  decide whether a constraint is violated by comparing them to `infinity`; it
  does not optimize ordinary finite DCOP costs.
- Like the paper algorithm, DBA is incomplete. It can fail to terminate on
  unsatisfiable problems or on satisfiable problems where the local search does
  not find a solution before the runtime timeout.
- Satisfied agents can temporarily have `quasi_local_minimum = True` when their
  own improvement is zero, but the violated-constraint list is empty in that
  case, so no weights are changed.
- Each computation stores its configured `infinity` threshold independently.
- Isolated or purely unary computations are outside the paper's connected
  graph-coloring focus and do not naturally receive messages to drive the
  wait-ok/wait-improve loop.
- Initial value selection is random and DBA has no dedicated seed parameter.
- Tie-breaking uses natural computation name order as the fixed ordering, so
  names with numeric suffixes compare as expected (`v2` before `v10`).

## Existing Coverage

- `tests/unit/test_algorithms_dba.py` covers message properties, memory and
  communication estimates, construction, min-mode validation, evaluation and
  per-violation-tuple weight counting, startup, postponed messages,
  tie-breaking, quasi-local weight increase, end-message propagation, and
  termination state handling.
- `tests/dcop_cli/test_solve.py` exercises DBA on graph-coloring CSP instances
  in thread and process modes.

## Follow-Up

- None currently required for core DBA paper correctness.
- Consider explicit handling for isolated or unary-only computations so they
  evaluate and terminate without waiting for neighbor messages.
