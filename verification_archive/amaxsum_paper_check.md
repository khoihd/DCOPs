# AMaxSum Paper Check

## Source

- Paper: `verification_archive/papers/maxsum.pdf`
- Title: "Decentralised Coordination of Low-Power Embedded Devices Using the
  Max-Sum Algorithm"
- Authors: A. Farinelli, A. Rogers, A. Petcu, and N. R. Jennings
- Venue: AAMAS 2008
- Implementation: `pydcop/algorithms/amaxsum.py`
- Status: Done / Verified with documented runtime caveats

## Review Scope

- There is no separate paper source for `amaxsum.py`. The asynchronous behavior
  is described in the same Farinelli et al. Max-Sum paper used for
  `pydcop/algorithms/maxsum.py`.
- The paper is framed as social-welfare maximization on cyclic bipartite factor
  graphs. This implementation supports both `min` and `max`; `min` is accepted
  as the cost-minimization dual of the paper's utility-maximization equations.
- Graph construction is treated as out of scope except that Max-Sum requires
  `GRAPH_TYPE = "factor_graph"`.

## Paper Contract

- Build a factor graph with variable nodes and function nodes.
- Variable-to-function messages contain, for each value of the variable, the
  sum of incoming function-to-variable messages from all other neighboring
  functions.
- Variable-to-function messages are normalized on the fly with an additive
  scalar so the outgoing vector sums to zero.
- Function-to-variable messages contain, for each value of the target variable,
  the best local function value plus incoming variable-to-function messages
  from all other variables in that function scope.
- Variables select the value that optimizes the sum of all incoming
  function-to-variable messages.
- On cyclic factor graphs, the result is approximate. The paper says there is
  no need for a formal update schedule: outgoing messages may be initialized,
  then agents update whenever they receive an updated message from a neighbor.
- The paper discusses two practical termination styles for cyclic graphs:
  propagate until messages and states converge, or propagate for a fixed number
  of iterations per agent.

## Implementation Mapping

- `GRAPH_TYPE = "factor_graph"` matches the paper's bipartite representation.
- `MaxSumFactorComputation` and `MaxSumVariableComputation` do not use
  `SynchronousComputationMixin`; they react directly to incoming `max_sum`
  messages.
- `MaxSumMessage`, `factor_costs_for_var()`, `costs_for_factor()`, and
  `select_value()` are shared with `maxsum.py`, so the Q-message, R-message,
  normalization, and marginal value-selection equations match the same helper
  implementation verified for synchronous Max-Sum.
- Factor computations store incoming variable-to-factor messages and, once
  they have messages for all variables in the factor scope, send updated
  factor-to-variable messages to the other variables.
- Variable computations store incoming factor-to-variable messages, immediately
  update their selected value from the latest local marginal, and send updated
  variable-to-factor messages to the other factors.
- `start_messages` controls how outgoing messages are seeded. `all` most
  closely mirrors the paper's initialized-message description and is now the
  default; `leafs` and `leafs_vars` are repo-level startup controls.
- `stop_cycle` is interpreted as a local async update limit. Each computation
  increments its own local cycle count when it performs a real message-driven
  processing update. Once the count reaches `stop_cycle`, the computation
  reports finished if needed and then stops itself locally.
- `auto_stop` and `stable_cycles` are also interpreted locally. A computation
  reports finished after `stable_cycles` consecutive local async updates where
  every outgoing message is approximately unchanged according to the existing
  `stability` check, but keeps processing messages until the orchestrator
  observes all computations as stable and stops the run. If a later update
  changes an outgoing message, the computation reports itself as running again.
  A computation can also report stable after a local quiet period, which
  handles the asynchronous case where its last changed message does not trigger
  another incoming update.
  The existing `SAME_COUNT` threshold remains the resend / suppression throttle
  for stable messages.
- `stability` and `SAME_COUNT` implement local stable-message suppression:
  once a directed message remains approximately unchanged for several sends,
  the computation stops resending it until the value changes. This corresponds
  to the paper's "propagation ceases" behavior for converged messages, but is
  local and approximate rather than a global convergence proof.

## Verification Notes

- The paper explicitly supports asynchronous scheduling: nodes may update
  outgoing messages at any time and, for the cyclic DCOP setting, update when
  they receive a message from a neighboring agent.
- The implementation's event-driven receive handlers match that asynchronous
  shape. The synchronous `maxsum.py` implementation is the repo-specific cycle
  adaptation, not the paper's only update model.
- Waiting for all variables in a factor scope before sending factor messages is
  a startup guard. Once all incoming Q-message tables are known, subsequent
  updates use the latest received messages as described by the paper.
- The implementation does not implement the paper's graph-colouring
  `MS-Stable` utility-function modification internally. That is a modeling
  choice for graph-colouring instances, not part of the generic Max-Sum message
  equations.

## Existing Coverage

- `tests/unit/test_algorithms_amaxsum.py` covers computation construction,
  factor-to-variable messages in `min` and `max` modes, value-indexed message
  serialization, memory and communication estimates, startup messages, pause /
  resume state reset, damping, stable-message suppression, variable value
  selection after incoming messages, event-driven variable/factor sends,
  `stop_cycle`, and `auto_stop` / `stable_cycles`.
- Shared helper coverage in `tests/unit/test_algorithms_maxsum.py` covers
  variable-to-factor normalization, value selection, and the underlying
  factor-message equations used by AMaxSum.

## Caveats

- `auto_stop` is still local and message-based, but completion is coordinated
  globally: locally stable computations keep processing messages and can reset
  themselves to running before the orchestrator sees every computation stable.
- AMaxSum runs until `stop_cycle` stops computations locally, `auto_stop`
  reports every computation stable and the orchestrator stops the run, the
  runtime stops it externally, or
  stable-message suppression leaves no more messages to send.
- `start_messages: leafs` can under-seed cyclic graphs without a leaf-based
  seed and may start with little or no propagation.
- `damping`, `damping_nodes`, `stability`, `noise`, `start_messages`, generic
  N-ary constraints, integrated variable costs, and `min` mode are repo-level
  extensions or generalizations beyond the graph-colouring examples in the
  paper.

## Follow-Up

- No AMaxSum paper-check follow-up is currently pending.
