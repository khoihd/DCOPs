# MaxSum Paper Check

## Source

- Paper: `verification_archive/papers/maxsum.pdf`
- Title: "Decentralised Coordination of Low-Power Embedded Devices Using the
  Max-Sum Algorithm"
- Authors: A. Farinelli, A. Rogers, A. Petcu, and N. R. Jennings
- Venue: AAMAS 2008
- Implementation: `pydcop/algorithms/maxsum.py`
- Status: Done / Verified

## Review Scope

- The paper is framed as social-welfare maximization on a cyclic bipartite
  factor graph whose variable nodes represent agent states and whose function
  nodes represent local utilities.
- This implementation supports both `min` and `max` modes. `min` is accepted as
  the cost-minimization dual of the paper's utility-maximization equations.
- The paper describes asynchronous local updates after initialization. This
  module is intentionally synchronous; `pydcop/algorithms/amaxsum.py` covers the
  asynchronous runtime variant.
- Graph construction is treated as out of scope except that Max-Sum requires
  `GRAPH_TYPE = "factor_graph"`.

## Paper Contract

- Build a factor graph with variable nodes and function nodes.
- Variable-to-function messages contain, for each value of the variable, the
  sum of the incoming function-to-variable messages from all other neighboring
  functions.
- Variable-to-function messages are normalized on the fly with an additive
  scalar so the outgoing vector sums to zero.
- Function-to-variable messages contain, for each value of the target variable,
  the best value of the local function plus incoming variable-to-function
  messages from all other variables in that function scope.
- Variables select the value that optimizes the sum of all incoming
  function-to-variable messages.
- On cyclic graphs, the result is approximate. The paper discusses either
  running for a fixed number of iterations or stopping when messages converge.
- Function-message computation is exponential in the number of variables in the
  local function scope, not in the total number of agents.

## Implementation Mapping

- `GRAPH_TYPE = "factor_graph"` matches the paper's bipartite representation.
- `MaxSumMessage` carries the value-indexed message vector.
- `factor_costs_for_var()` implements the function-to-variable update. It uses
  `min` or `max` depending on the algorithm mode and adds the most recent
  messages from the other variables in the factor scope.
- `costs_for_factor()` implements the variable-to-function update. It sums all
  incoming factor messages except the destination factor and includes integrated
  variable costs as a local unary-cost extension.
- `costs_for_factor()` now normalizes the complete outgoing message vector,
  including integrated variable costs, so the vector sums to zero as required
  by the paper's normalized Q-message equation.
- `select_value()` implements the marginal decision step by optimizing the
  variable cost plus all incoming factor-message values.
- `damping`, `damping_nodes`, `stability`, `noise`, `start_messages`,
  `auto_stop`, and `stable_cycles` are repo/runtime extensions. Damping,
  stability, and auto-stop are practical loopy-belief propagation controls;
  `noise` represents a small unary preference/tie-breaker; `start_messages`
  controls how synchronous startup is seeded.
- `stop_cycle` now supports the paper's fixed-iteration termination option for
  the synchronous implementation.

## Verification Fixes

- Added `stop_cycle` to `algo_params` and made factor and variable computations
  call `finished()` and `stop()` at the configured synchronous cycle boundary.
- Added optional `auto_stop` / `stable_cycles` support. Computations report
  `finished()` after their local outgoing messages have remained stable for the
  configured number of cycles, but they keep participating in synchronization
  until the orchestrator stops all computations together.
- Corrected variable-to-function normalization so integrated variable costs are
  included in the average that is subtracted from the outgoing message.
- Updated MaxSum and AMaxSum tests affected by the shared normalization helper.

## Existing Coverage

- `tests/unit/test_algorithms_maxsum.py` covers computation construction,
  factor-to-variable messages in `min` and `max` modes, variable-to-function
  normalization, value selection, memory and communication estimates, message
  serialization, startup behavior, damping, stability suppression, and
  `stop_cycle`.
- `tests/unit/test_algorithms_amaxsum.py` covers the asynchronous Max-Sum
  implementation that shares the MaxSum message and variable-message helpers.

## Caveats

- The synchronous runtime adds bookkeeping sync messages between Q/R Max-Sum
  payloads. They only advance cycles and carry no costs, utilities, selected
  values, marginals, or other Max-Sum equation terms.
- The implementation's convergence handling is local and message-level. Each
  directed Q or R message is compared with the previous message on that edge
  using the `stability` coefficient. If the vector remains approximately the
  same, the computation still sends it for `SAME_COUNT` cycles, then suppresses
  further copies until the vector changes again. This reduces redundant traffic
  in stable loopy runs. When `auto_stop` is enabled, local computations report
  completion after `stable_cycles` such stable local cycles. This is still not a
  global termination proof: different edges can stabilize at different times,
  variables can still update from other incoming messages, and cyclic factor
  graphs can settle to a fixed point or oscillate depending on the instance and
  damping. The paper also treats convergence on cyclic graphs as an
  empirical/fixed-iteration matter rather than proving global convergence.
- Generic relation objects, N-ary constraints, integrated variable costs, and
  `min` mode are repo-level generalizations beyond the graph-colouring examples
  in the paper.

## Follow-Up

- AMaxSum and Dynamic MaxSum remain separate tracker items.
