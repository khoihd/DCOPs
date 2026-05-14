# SyncBB Paper Check

## Source

- Paper: `verification_archive/papers/syncbb.pdf`
- Title: "Distributed Partial Constraint Satisfaction Problem"
- Authors: Katsutoshi Hirayama and Makoto Yokoo
- Implementation: `pydcop/algorithms/syncbb.py`
- Status: Done / Verified with documented pyDcop extensions

## Review Scope

- The paper defines Synchronous Branch and Bound (SBB) for Distributed
  Maximal Constraint Satisfaction Problems.
- The paper setting assumes a fixed variable/agent ordering, fixed value
  ordering, one variable per agent, binary constraints, sequential token
  passing, and minimization of the path evaluation value.
- The pyDcop implementation is reviewed as a DCOP adaptation of SBB: it keeps
  the fixed sequential branch-and-bound token flow, but optimizes additive
  weighted costs instead of the paper's max-per-agent violation distance.

## Paper Contract

- The first agent starts the search by sending a token containing its first
  value to the next agent.
- On a token from the previous agent, an agent stores the received upper bound,
  tries domain values in order, extends the path if the value passes the bound
  check, and backtracks when its domain is exhausted.
- On a token from the next agent, an agent resumes at the value after its
  current path value and either sends a new extended path forward or backtracks.
- The last agent tries the remaining values locally, updates the best complete
  path bound, and sends the bound backward.
- Path entries contain variable, value, and a local cost/violation count.
- In the paper, `check(path)` must reject the whole candidate as soon as any
  bound check fails; it must not return a candidate that only passed a prefix
  of the path.
- The first agent terminates when its domain is exhausted, and termination is
  propagated along the ordering.

## Implementation Mapping

- `GRAPH_TYPE = "ordered_graph"` matches the paper's fixed chain ordering.
- `SyncBBForwardMessage` carries the token path and current bound.
- `SyncBBBackwardMessage` carries the prefix path and improved bound while
  backtracking.
- `SyncBBTerminateMessage` is a pyDcop implementation message used to propagate
  the paper's final termination condition through the chain.
- `on_start()` implements the first-agent initialization with the first domain
  value.
- `on_forward_message()` implements token receipt from the previous variable,
  local bound adoption, value selection, forward extension, and backward
  backtracking.
- `on_backward_msg()` implements token receipt from the next variable, bound
  update, resumed value search, and further backtracking.
- The last-variable branch in `on_forward_message()` scans the remaining local
  values and sends the best bound backward, matching the paper's special
  last-agent treatment.
- `get_next_assignment()` implements the value-ordering and bound-check helper.
  It now rejects a candidate if any prefix/path consistency check fails, rather
  than keeping a partially valid candidate.
- `memory_footprint_estimate()` and `communication_load()` estimate SyncBB's
  local state and path-token payload instead of relying on pyDcop's generic
  default estimates. Communication is counted only along the fixed previous /
  next ordering links.

## Resolved Gaps

- Forward-token handling now adopts a better received bound before searching,
  matching the paper's `ni <- ub` step on token receipt.
- `get_next_assignment()` no longer returns a candidate after a later path
  element fails the bound check. The previous behavior could accept only the
  prefix cost of a weighted candidate and produce a non-optimal solve result.
- Maximization support is explicit: SyncBB does not prune max-mode candidates
  from their current partial utility alone, because later variables may add
  enough utility to beat the incumbent.
- Path-token memory and communication planning estimates are now implemented
  explicitly for SyncBB.
- Regression coverage now includes both the helper-level stale-prefix case and
  a solve-level weighted binary DCOP where the previous implementation returned
  cost `10` instead of the optimal cost `6`, plus a max-mode case where a low
  partial utility later becomes the optimal assignment.

## Documented Deviations

- The paper's SBB minimizes the maximum number of violated constraints over
  agents for DMCSPs. This implementation minimizes or maximizes pyDcop's
  additive weighted DCOP objective.
- The paper includes sufficient-solution thresholds `si`; pyDcop SyncBB
  searches to optimality and does not expose an early sufficient-threshold
  parameter.
- `objective: max` is a pyDcop extension. The paper's SBB presentation is a
  minimization branch-and-bound algorithm.
- The implementation passes the known bound inside token messages instead of
  broadcasting a separate bound update.
- The implementation has no SyncBB-specific algorithm parameters.
- The path-token estimates are conservative local planning estimates. The
  estimate hooks receive a computation node, not the full ordered chain, so the
  implementation counts the variables visible from that node's order and
  constraint links.

## Verdict

SyncBB is faithful to Hirayama and Yokoo's sequential branch-and-bound token
flow for the fixed-order, binary-constraint setting, with pyDcop's documented
extension from DMCSP violation distance to additive weighted DCOP objectives.
The bound adoption and candidate-pruning behavior now match the paper's token
and `check(path)` control flow closely enough for the implemented DCOP
adaptation.

## Existing Coverage

- `tests/unit/test_algorithms_syncbb.py` covers computation construction,
  termination messages, value-ordering helpers, exact variable-name constraint
  lookup, forward extension, backward search, pruning, termination propagation,
  min/max solve-level outcomes, max-mode non-pruning of partial utilities, and
  the weighted regression case fixed during this check. It also covers the
  explicit memory and communication estimates.

## Follow-Up

- None currently identified.
