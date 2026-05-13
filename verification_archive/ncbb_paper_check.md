# NCBB Paper Check

## Source

- Paper: `verification_archive/papers/ncbb.pdf`
- Title: "No-Commitment Branch and Bound Search for Distributed Constraint
  Optimization"
- Authors: Anton Chechetka and Katia Sycara
- Implementation: `pydcop/algorithms/ncbb.py`
- Status: Needs fix

## Review Scope

- The paper presents NCBB as an optimal branch-and-bound DCOP algorithm for
  minimization with binary constraints, one variable per agent, and a DFS
  pseudo-tree ordering.
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
- Initialization is partially implemented:
  - the root chooses a value and sends `ValueMessage` to descendants;
  - non-root computations wait for all ancestor values;
  - each non-root greedily chooses a value with `find_optimal()`;
  - leaf costs are sent upward with `CostMessage`;
  - internal nodes aggregate child costs and the root transitions to search
    after all children report.
- `agent_cost()` now implements the paper's `AgentCost` helper for constrained
  ancestors.
- `lower_bound()` now implements the paper's `LB(x, B, k)` minimization helper.

## Gaps

- The main NCBB search loop is not implemented. `search()` raises
  `NotImplementedError`.
- Search-phase message handling for `search`, `search_value`, `search_cost`,
  and `stop` is not implemented.
- The implementation has no `subtreeSearch`, pruning logic, per-value `costs`,
  `unexplored`, `anncdVals`, root result selection, or final `STOP` propagation.
- `memory_footprint_estimate()` and `communication_load()` still raise
  `NotImplementedError`.
- The paper is minimization-only. The implementation accepts `mode="max"` for
  the greedy initialization helper, but max-mode NCBB is not verified against
  the paper.
- There are no solve-level tests proving optimal NCBB results.

## Verdict

NCBB is not paper-correct yet. The implemented initialization behavior matches
the broad top-down value / bottom-up cost shape from the paper, and the
`AgentCost` / `LB` helpers now match the paper definitions for minimization.
However, the defining branch-and-bound search phase from Figures 1 and 2 is
absent, so the algorithm remains incomplete and should not be marked verified.

## Existing Coverage

- `tests/unit/test_algorithms_ncbb.py` covers computation construction,
  binary-constraint validation, initialization value propagation, greedy value
  selection, cost propagation, phase validation, root transition into search,
  `agent_cost()`, `lower_bound()`, and explicit search-phase incompleteness.

## Follow-Up

- Implement the full search phase from Figures 1 and 2 before marking NCBB
  verified.
