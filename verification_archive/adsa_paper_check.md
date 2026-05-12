# ADSA Paper Check

## Source

- Paper: `verification_archive/papers/adsa.pdf`
- Title: "Distributed Coordination through Anarchic Optimization"
- Authors: Stephen Fitzpatrick and Lambert Meertens
- Implementation: `pydcop/algorithms/adsa.py`
- Status: Done / Verified
- Result: No behavior change required.

## Review Scope

- The paper presents a peer-to-peer stochastic local optimizer for distributed
  constraint optimization, first as a synchronized fixed-probability loop and
  then as an asynchronous wake-up process.
- The implementation applies this idea to generic DCOP relations on a
  constraints hypergraph, with both `min` and `max` modes.
- The check focuses on the paper's asynchronous execution model in section
  2.3 and the fixed-probability local optimization rule from section 2.

## Paper Contract

- Each variable chooses an initial value randomly and informs its neighbors.
- Each variable repeatedly wakes up after a local period; asynchronous
  execution is modeled by wake-up times distributed through that period.
- On wake-up, a variable activates with probability `p`.
- If activated, the variable chooses a value that optimizes the constraints in
  which it participates, using its latest known neighbor values.
- If the value changes, the variable sends the new value to its neighbors.
- The paper treats the algorithm as ongoing / anytime rather than defining a
  built-in termination condition.
- The experimental fixed-probability discussion highlights values around `0.3`
  as useful for many graph-coloring cases, but this is empirical guidance, not
  a required algorithm constant.

## Implementation Mapping

- `algo_params` exposes `period`, `probability`, and DSA-style `variant`.
- `on_start()` adds a randomized delay before `delayed_start()`, matching the
  paper's randomly distributed wake-up times within one period.
- `delayed_start()` selects an initial random value for variables with
  neighbors, schedules `tick()` periodically, and broadcasts the initial value.
- `_on_value_msg()` records the latest received value from each neighbor.
- `tick()` uses the latest known full neighbor assignment, computes locally
  best values with `find_best_values()`, applies the configured stochastic
  value-change variant, and then broadcasts the current value.
- `find_best_values()` enumerates the local domain and evaluates the local
  constraints plus any variable cost, supporting the paper's small discrete
  domain case while generalizing beyond graph coloring.
- `variant_a()`, `variant_b()`, and `variant_c()` reuse the DSA A/B/C
  conditions from `pydcop/algorithms/dsa.py`; this is a repo-level adaptation
  of the paper's fixed-probability activation rule.
- No-neighbor computations select a local value and stop immediately, because
  no neighbor exchange is needed to improve an isolated variable.

## Verdict

The implementation matches the paper's asynchronous peer-to-peer shape:
randomized start offset, periodic independent wake-ups, local optimization
from currently known neighbor values, probabilistic value changes, and ongoing
anytime execution.

No paper-correctness code change was required. During this check, only module
documentation was tightened to describe the Fitzpatrick/Meertens asynchronous
wake-up model and the implementation's DSA A/B/C variant extension.

## Caveats

- The paper's basic fixed-probability algorithm decides whether to activate
  before optimizing. This implementation computes local best values first and
  then applies the probability threshold only when the selected DSA variant
  permits a move. For the supported DSA variants, this preserves the intended
  stochastic local-search behavior while avoiding unnecessary no-op moves.
- The paper sends value messages only when a value changes. The implementation
  broadcasts the current value every tick to improve resilience to message loss
  and startup timing. This increases communication relative to the paper's
  cost discussion but is intentional for this runtime.
- The paper is framed around graph coloring and a later sensor-network
  scheduling case. The implementation supports generic N-ary relations,
  variable costs, and both optimization modes.
- The default `probability` remains `0.7`, matching the repository's DSA
  default. The paper's `0.3` value is an experimental recommendation for a
  range of graph-coloring instances, not a formal required default.
- The paper assumes changing variables/constraints can be noticed at wake-up
  time. This module does not add special dynamic-structure handling beyond the
  surrounding pyDcop runtime.

## Existing Coverage

- `tests/unit/test_algorithms_adsa.py` covers construction, communication and
  memory estimates, message properties, startup behavior, pause/resume behavior,
  periodic ticks, current-cost calculation, variants A/B/C, probability
  threshold behavior, and violated-constraint detection.

## Done

- None currently required for core ADSA paper correctness.
