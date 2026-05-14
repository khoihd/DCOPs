# NCBB Paper Check

## Source

- Paper: `verification_archive/papers/ncbb.pdf`
- Title: "No-Commitment Branch and Bound Search for Distributed Constraint
  Optimization"
- Authors: Anton Chechetka and Katia Sycara
- Implementation: `pydcop/algorithms/ncbb.py`
- Status: Done / Verified

## Review Scope

- The paper presents NCBB as an optimal branch-and-bound DCOP algorithm for
  minimization with binary constraints, one variable per agent, and a DFS
  pseudo-tree ordering.
- Maximization support is reviewed as a pyDcop extension that minimizes the
  negated objective internally; it is not part of the paper contract.
- The paper assumes constraints only between ancestor/descendant pairs in the
  pseudo-tree.
- The check focuses on the paper's initialization phase, helper definitions
  `AgentCost` and `LB`, message flow, and the main branch-and-bound search in
  Figures 1 and 2.

## Paper Contract

- Before search, agents are arranged in a DFS tree. Each agent knows its parent,
  children, and constrained ancestors/descendants.
- Initialization computes a greedy assignment and an initial global upper bound.
  Values propagate top-down; costs propagate bottom-up.
- `AgentCost(x, B)` is the sum of binary constraints between `x` and its
  ancestors under assignment `B`.
- `LB(x, B, k)` minimizes `AgentCost` over `x` and over ancestor values not
  fixed among the first `k` ancestors.
- During search, each non-root waits for `SEARCH` from its parent, maintains a
  context of ancestor assignments, and reports lower-bound deltas when ancestor
  values are announced.
- Each agent tracks per-value costs, unexplored child/value combinations, and
  announced child values so different children can explore different values
  concurrently.
- `subtreeSearch` announces a value to constrained descendants, receives lower
  bound deltas from descendants, prunes if the bound is exceeded, otherwise
  sends `SEARCH` to the selected child.
- The root records the best value and sends `STOP` when all relevant search
  partitions are complete.

## Implementation Mapping

- `GRAPH_TYPE = "pseudotree"` matches the paper's DFS-tree requirement.
- `NcbbAlgo.__init__()` extracts parent, pseudo-parents, children, and
  pseudo-children from the pseudo-tree computation node.
- The implementation rejects non-binary constraints, matching the paper's
  restricted binary-constraint presentation.
- Initialization matches the paper's top-down value / bottom-up shifted-bound
  structure:
  - the root chooses a value and sends `ValueMessage` to descendants;
  - non-root computations wait for all ancestor values;
  - each non-root greedily chooses a value minimizing local `AgentCost`;
  - leaf shifted costs are sent upward with `CostMessage`;
  - internal nodes aggregate child costs and the root transitions to search
    after all children report.
- The initial upper bound now uses the paper's shifted bound:
  `sum(AgentCost(x, Bgreedy)) - sum(LB(x, empty, 0))`.
- `PseudoTreeNode.branch_descendants` records child-specific constrained
  descendants so `subtreeSearch` can implement the paper's
  `descendants[child]` structure.
- `agent_cost()` now implements the paper's `AgentCost` helper for constrained
  ancestors, with pyDcop unary variable costs added as a local extension when
  present.
- `lower_bound()` now implements the paper's `LB(x, B, k)` minimization helper.
- For `objective: max`, local costs are negated before entering the NCBB
  minimization machinery, so lower bounds, shifted costs, pruning, and result
  selection operate unchanged on the transformed objective.
- Search-phase handling now implements `SEARCH`, value announcements,
  lower-bound delta reporting, per-value costs, unexplored child/value
  combinations, announced child values, pruning, root result selection, and
  final `STOP` propagation.
- `memory_footprint_estimate()` and `communication_load()` now provide
  polynomial-space / constant-message-size estimates matching the paper's
  asymptotic properties.

## Resolved Gaps

- The previous real-solve initialization crash is fixed: root initializes
  `_upper_bound` before receiving child `CostMessage`s.
- The main NCBB search loop no longer raises `NotImplementedError`.
- Search-phase message handling for `search`, `search_value`, `search_cost`,
  and `stop` is implemented.
- `subtreeSearch`, pruning, per-value `costs`, `unexplored`, `anncdVals`, root
  result selection, and final `STOP` propagation are implemented.
- `memory_footprint_estimate()` and `communication_load()` no longer raise
  `NotImplementedError`.
- Solve-level coverage now proves an optimal NCBB result on a small
  pseudo-tree instance.

## Remaining Caveats

- The paper is minimization-only. Max-mode NCBB is supported as a pyDcop
  extension through objective negation, not as paper-verified behavior.
- NCBB requires finite-domain variables and binary constraints. No
  NCBB-specific YAML item is required beyond the usual pyDcop problem
  definition, agents/distribution, and `objective: min` or `objective: max`.

## Verdict

NCBB is now paper-correct for the minimization, binary-constraint setting
covered by Chechetka and Sycara. Initialization computes the shifted greedy
upper bound, `AgentCost` and `LB` match the paper definitions, and the main
branch-and-bound search from Figures 1 and 2 is implemented with lower-bound
delta propagation, child/value exploration state, pruning, and stop
propagation. Maximization instances are supported by minimizing the negated
objective internally.

## Existing Coverage

- `tests/unit/test_algorithms_ncbb.py` covers computation construction,
  binary-constraint validation, initialization value propagation, greedy value
  selection, cost propagation, phase validation, root transition into search,
  `agent_cost()`, `lower_bound()`, search value lower-bound deltas, leaf
  search result reporting, branch-specific value announcements, footprint /
  communication estimates, max-mode transformed lower bounds, and min/max
  solve-level optimality.
- `tests/unit/test_graph_pseudotree.py` covers the pseudo-tree graph behavior
  after adding child-branch descendant metadata.

## Follow-Up

- If documenting paper fidelity elsewhere, describe `objective: max` support as
  a pyDcop extension via objective negation.
