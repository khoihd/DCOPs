# DPOP Paper Check

## Source

- Paper: `verification_archive/papers/dpop_petcu_05.pdf`
- Title: "A Scalable Method for Multiagent Constraint Optimization"
- Authors: Adrian Petcu and Boi Faltings
- Implementation: `pydcop/algorithms/dpop.py`

## Review Scope

- Graph construction is treated as out of scope. The paper explicitly says DFS
  pseudotree creation is not detailed there.
- Both minimization and maximization are accepted unless the DPOP logic requires
  one direction. The paper is written for utility maximization.
- N-ary constraints are accepted. The paper focuses on unary and binary
  relations, but says higher arity can be handled with small modifications.
- The check focuses on whether the implementation follows or contradicts the
  paper's DPOP logic.

## Paper Contract

- The problem is a distributed constraint optimization problem with variables,
  finite domains, and relations whose utilities are summed.
- DPOP runs on a pseudotree with parent, children, pseudo-parent, and
  pseudo-child relations known before UTIL and VALUE propagation.
- UTIL propagation starts at leaves and moves only through tree edges from
  child to parent.
- A UTIL message is a utility hypercube over the sender's context: the parent
  variable plus any ancestor/context variables needed because of back edges.
- Each non-root computation waits for UTIL messages from all children, combines
  child utilities with local relations, optimizes out its own variable, and
  sends the projected utility relation to its parent.
- The root waits for all child UTIL messages, chooses its optimal value, and
  starts VALUE propagation.
- VALUE messages propagate parent/context assignments down the tree so each
  computation can choose the optimal value consistent with the separator values
  used in its UTIL message.
- The core algorithm sends one UTIL over each tree edge and VALUE messages down
  the tree; the largest UTIL message is exponential in induced width.

## Implementation Mapping

- `GRAPH_TYPE = "pseudotree"` matches the paper's pseudotree requirement.
- `DpopAlgo.__init__()` reads parent, pseudo-parents, children, and
  pseudo-children with `get_dfs_relations()`.
- Local constraints are filtered so each relation is handled by the lowest node
  involved in that relation, matching the paper's need to account for each
  relation once in the subtree computation.
- Leaf nodes send UTIL in `on_start()` by calling `_compute_utils_msg()`.
- Internal nodes accumulate child UTIL messages in `_on_util_message()` and wait
  until all children have sent one.
- `join()` sums local relations and child UTILs, matching the paper's utility
  combination.
- `projection(..., self._variable, self._mode)` optimizes out the local
  variable, matching the paper's dynamic-programming elimination step.
- The root chooses an optimal value from the joined child utilities and local
  constraints, then sends VALUE messages to children.
- Instead of storing an explicit table of optimal local values per context, the
  implementation keeps the joined relation. During VALUE propagation it slices
  that relation with received separator assignments and recomputes
  `find_arg_optimal()`. This is equivalent for correctness, with deterministic
  tie behavior delegated to relation/domain order.
- VALUE propagation sends the selected local value plus inherited ancestor
  assignments needed by each child's recorded UTIL separator.

## Verdict

The core DPOP solving logic matches the paper. I found no contradiction between
the paper's UTIL/VALUE algorithm and `pydcop/algorithms/dpop.py`.

The implementation intentionally generalizes the paper in these ways:

- It supports both `min` and `max` modes.
- It supports N-ary relations through generic relation `join()` and
  `projection()`.
- It handles isolated variables and variable-level cost functions, which are
  repo-specific behavior outside the paper.
- It recomputes the selected value from the retained joined relation during
  VALUE propagation instead of storing an explicit arg-optimal table.

## Caveats

- The paper does not define tie-breaking. The implementation selects the first
  value returned by `find_arg_optimal()`.
- The paper does not define process serialization, message priority, stopping
  hooks, or runtime orchestration.
- `communication_load()` is explicitly not implemented.
- `computation_memory()` estimates memory from the computation variable plus
  parent and direct pseudo-parents. The paper's induced-width discussion also
  accounts for ancestor context dimensions introduced by descendant back edges.
  This helper should not be treated as fully verified against the paper's
  complexity model without a separate memory-focused check.

## Existing Coverage

- `tests/unit/test_algorithms_dpop.py` covers message sizes, construction,
  local constraint filtering, leaf UTIL, internal UTIL, root VALUE start,
  ancestor context propagation through an intermediate node,
  separator-preserving VALUE messages, isolated/root leaf behavior, min mode,
  and N-ary projection behavior.
- `tests/api/test_api_solve_dpop.py` checks solve-level DPOP assignments/costs
  against a PuLP oracle on known instances.

## Follow-Up

- Optional: decide whether `computation_memory()` should be upgraded to model
  full induced-width separator/context dimensions or documented as a local
  approximation.
