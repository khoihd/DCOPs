# PD-DCOP Java Reference: Key Points

Sources:

- Java reference: `pddcop/pddcop_java/`
- Paper notes: `pddcop/pddcop_jair_key_points.md`
- Source paper: `pddcop/pddcop_jair.pdf`

This file summarizes the Java reference implementation with an eye toward
porting the PD-DCOP models and algorithms into this Python repository.

## Repository Shape

Top-level `pddcop/` currently contains:

- `README.md`: short description of the reference-material folder.
- `pddcop_jair.pdf`: JAIR paper source.
- `pddcop_jair_key_points.md`: paper-oriented implementation notes.
- `pddcop_java/`: Java reference project.
- `pddcop_java_key_points.md`: this Java-source-oriented handoff.

The useful implementation is concentrated in `pddcop/pddcop_java/src/`:

- `agent/AgentPDDCOP.java`: central state holder, argument parsing, input
  parsing, probability propagation, table transformations, algorithm schedule,
  switching costs, online simulation, and result aggregation.
- `behavior/`: JADE behaviours implementing pseudotree construction, DPOP,
  MGM, local search, final utility collection, and experimental R-learning.
- `table/`: small utility table model.
- `transition/TransitionFunction.java`: finite Markov transition matrix.
- `utilities/Utilities.java`: tab-separated experiment output writers.
- `main/Main.java`: starts one JADE agent per decision variable.

The rest of `pddcop/pddcop_java/` is mostly generated `.dzn` instances and
experiment output files. At review time, `input_files/` contains 2,900 `.dzn`
fixtures across random and meeting topologies, while `output_files/` contains
69 checked-in experiment result files under `FINITE_HORIZON`,
`INFINITE_HORIZON`, and `ONLINE`.

The Java project is JADE-based Java 8 with Guava. It uses JADE agents for
message passing and `Sets.cartesianProduct` for exhaustive tuple generation.

The Java source count is small enough to read directly: 30 `.java` files, with
most behavior in `AgentPDDCOP.java`, `DPOP_UTIL.java`, and `DPOP_VALUE.java`.

## Run Interface

`Main` expects arguments in this order:

1. `pddcop_algorithm`
2. `dcop_algorithm`
3. `input_file`
4. `horizon`
5. `switching_cost`
6. `discount_factor`
7. `dynamic_type`
8. `heuristic_weight`
9. `rLearningIteration`

The README shows only eight arguments, but `AgentPDDCOP.readArguments()` reads
the ninth argument unconditionally.

`input_file` is relative to `input_files/`, for example:

`random_x5_y1_dx3_dy3/instance_0_x5_y1_dx3_dy3.dzn`

`Main` derives the number of agents from the filename and starts agents named
`1..agentCount`. The implementation assumes one decision variable per agent and
uses the same integer string as the agent id, decision variable id, and usually
the colocated random variable id.

## Input Format

The Java reader accepts a MiniZinc-style `.dzn` subset:

- `decision_xN=[lo,hi];`
- `random_yN=[lo,hi];`
- `constraint_xA_xB=[xA,xB,utility|...];`
- `constraint_xA_yA=[xA,yA,utility|...];`
- `initial_distribution_yN=[p0,p1,...];`
- `transition_yN=[row0|row1|...];`

The parser strips spaces and concatenates lines until `;`. Domains are expanded
from inclusive integer ranges, then represented as strings.

Decision-only constraints form the DCOP primal graph. Random variables are not
added as neighbors, but mixed constraints over decision variables and random
variables are stored as random tables.

Important parser behavior:

- Each agent stores only random variables whose id equals its own agent id.
- Each agent keeps only constraints whose label contains its own decision
  variable `x<agentID>`.
- Mixed tables may technically contain multiple random labels, but most online
  realization code assumes one random variable by reading `row.getRandomList().get(0)`.
- The random-table expectation code multiplies independent probabilities across
  all random labels, matching the paper assumption.

## Internal Table Model

`Table` stores:

- `decVarLabel`: decision variable labels without the `x` prefix.
- `randVarLabel`: random variable labels without the `y` prefix.
- `rowList`: rows of decision values, random values, and utility.
- `isRandTable`: a marker, but `Table.isRandTable()` is true whenever
  `randVarLabel` is non-empty.

`Row` stores:

- `valueList`: decision assignment tuple.
- `randomList`: random-state tuple.
- `utility`: double utility.

Missing table lookups return `-Double.MAX_VALUE`, not Java negative infinity.
The implementation is strictly utility maximization; switching costs are added
as negative utility rows.

## Algorithms And Modes

`AgentPDDCOP.PDDcopAlgorithm` includes:

- `C_DCOP`: exact collapsed PD-DCOP solved by DPOP. This corresponds to
  C-DPOP in the paper.
- `LS_SDPOP`: local search initialized by sequential DPOP.
- `LS_RAND`: local search initialized randomly.
- `FORWARD`: greedy sequential solve from early to late time steps.
- `BACKWARD`: greedy sequential solve from late to early time steps.
- `SDPOP`: enum value exists, but no main schedule branch was found.
- `REACT`: online reactive solve using realized random states.
- `HYBRID`: online solve using observation-updated next-step distributions.
- `R_LEARNING`: experimental MD-DCOP-style R-learning path.
- `BOUND_DPOP`: incomplete exploratory code for random realization bounds.

`AgentPDDCOP.DcopAlgorithm` includes only:

- `DPOP`
- `MGM`

`AgentPDDCOP.DynamicType` includes:

- `FINITE_HORIZON`: Java implementation of the paper's CDFU case
  (`discount_factor < 1` in experiments).
- `INFINITE_HORIZON`: Java implementation of the paper's MCC case
  (`discount_factor == 1` in experiments).
- `ONLINE`: online simulation for FORWARD, HYBRID, and REACT.
- `STATIONARY`: stationary online/simulation variant used mostly with
  R-learning and FORWARD.

Main schedule in `AgentPDDCOP.setup()`:

1. Parse arguments and the `.dzn` file.
2. Register with JADE DF and build the pseudotree.
3. Simulate or propagate random-variable distributions.
4. For `INFINITE_HORIZON`, solve the horizon/stationary DCOP first.
5. Run the selected PD-DCOP algorithm:
   - collapsed solve once for `C_DCOP`;
   - forward time-step loop for `LS_SDPOP`, `FORWARD`, `HYBRID`, and `REACT`;
   - backward time-step loop for `BACKWARD`;
   - random vector initialization for `LS_RAND`;
   - learning/apply loops for `R_LEARNING`.
6. For local-search algorithms, exchange initial vectors and run 40
   improvement iterations.
7. Exchange final values, aggregate final utilities, write results, and
   terminate the JADE process.

## Probability And Markov Handling

Each random variable has:

- initial distribution `probabilityAtEachTimeStepMap[random][0]`;
- transition matrix `TransitionFunction`;
- propagated distributions for time steps up to the horizon.

Probability propagation is row-vector multiplication:

`p_t[col] = sum_k p_{t-1}[k] * T[k][col]`

For `ONLINE`:

- Random realizations are sampled for every time step.
- `FORWARD` propagates expected distributions from the initial distribution.
- `HYBRID` replaces the distribution at time `t+1` with the transition row from
  the observed random value at time `t`.
- `REACT` solves against realized random tables, not expected tables.

For `STATIONARY`:

- The initial distribution is replaced by 40 transition multiplications.
- Actual random values are then sampled from that distribution and transitions.
- `FORWARD` reuses the stationary distribution for every time step.

For `INFINITE_HORIZON`:

- `lastTimeStep = horizon - 1`.
- The implementation solves a separate horizon DCOP first.
- Stationary/converged distribution is approximated by propagating from
  `horizon - 1` to `MARKOV_CONVERGENCE_TIME_STEP = 40`, then storing that in
  slot `horizon`.

This is not an exact stationary-distribution solver. A Python port should
prefer an explicit stationary distribution routine when implementing MCC.

## Discounted Expected Tables

Decision-only tables:

- At ordinary time `t`, utility is multiplied by `discount_factor^t`.
- In `FINITE_HORIZON` at `t == horizon`, decision-only utility is multiplied by
  `discount_factor^h / (1 - discount_factor)`.

Random tables:

- `computeDiscountedExpectedTable()` removes random variables by expectation.
- It computes joint random probability as a product of per-random-variable
  marginal probabilities.
- The expected utility is multiplied by `discount_factor^t`.
- In `FINITE_HORIZON` at `t == horizon`, it first calls
  `computeLongtermExpectedTable()`.

`computeLongtermExpectedTable()` implements the CDFU infinite discounted tail
for random tables at the horizon. For each decision tuple, it solves a linear
system over random states:

`V(row_state) = gamma^h * utility(row_state) + gamma * sum_next P(row,next) V(next)`

The code builds coefficients equivalent to:

`(I - gamma P) V = gamma^h u`

It solves with a local Gaussian elimination helper.

## Switching Costs

Switching cost is represented as utility loss.

`switchingCostFunction(oldValue, newValue)` returns a positive cost:

- `CONSTANT`: `0` if equal, configured switching cost otherwise.
- `LINEAR`, `QUADRATIC`, `EXP_2`, and `EXP_3` exist but the static setting is
  `CONSTANT`.

If either value is `null` or empty, it returns `-Double.MAX_VALUE`. This is an
odd sentinel for a function documented as returning positive costs; callers
usually avoid nulls, but a Python port should make this behavior explicit or
replace it with validation.

Sequential algorithms add unary tables with utility:

`-switchingCostFunction(candidate_value, fixed_neighbor_time_value)`

Collapsed algorithms create one unary table per agent over the whole sequence.
The collapsed sequence value is stored as a comma-separated string such as
`"0,1,1,2"`.

## Collapsed Exact Solve: `C_DCOP`

`C_DCOP` transforms the horizon into one static DCOP:

- Each variable's value becomes a comma-separated sequence.
- Each decision table is copied for every modeled time step, discounted, then
  collapsed into one table by Cartesian product and summed utility.
- Each random table is converted to discounted expected tables per time step,
  then collapsed similarly.
- Each agent receives a collapsed unary switching-cost table.

For `FINITE_HORIZON`, the collapse covers `0..horizon`.

For `INFINITE_HORIZON`, the code first solves a horizon DCOP using the
converged/stationary distribution at `horizon`, stores `chosenValue[horizon]`,
then collapses `0..horizon-1` and includes switching cost from `horizon-1` to
that fixed horizon assignment.

The collapsed solve is exact relative to the transformed tables but quickly
explodes because each original domain becomes `D^(h+1)` or `D^h`.

## DPOP Implementation

The Java DPOP path is embedded in `DPOP_UTIL` and `DPOP_VALUE`.

Pseudotree:

- Agents register with JADE DF under each neighbor id.
- Search discovers neighbor AIDs.
- Distributed DFS builds parent, children, pseudo-parent, and pseudo-child sets.
- The root is chosen by a heuristic score.
- After pseudotree generation, each agent keeps only tables whose other
  decision variables are parent/pseudo-parent side variables. This avoids
  double-counting constraints in the UTIL aggregation.

UTIL:

- Leaves join local tables, project out self by max, and send the table upward.
- Internal nodes wait for child UTIL tables, join them with local tables,
  project out self by max, and send upward.
- Root joins child/local tables and chooses the row with maximal utility.

VALUE:

- Root sends chosen assignments down.
- Non-root agents select the maximal row consistent with assignments received
  from ancestors, store their own value, and forward the accumulated context to
  children.

The DPOP table operations are simple exhaustive joins and projections. They are
good as behavioral reference material, not as an efficient Python port.

## Message Protocol And Timing

`MESSAGE_TYPE.java` defines integer ACL performatives:

- `DPOP_UTIL = 0`
- `DPOP_VALUE = 1`
- `PROPAGATE_DPOP_VALUE = 2`
- `SWICHING_COST = 3`
- `LS_IMPROVE = 4`
- `LS_VALUE = 5`
- `LS_UTIL = 6`
- `RAND_VALUE = 7`
- `PSEUDOTREE = 9`
- `INFO = 10`
- `INIT_LS_UTIL = 11`
- `FINAL_UTIL = 12`
- `FINAL_VALUE = 13`
- `MGM_VALUE = 14`
- `MGM_IMPROVE = 15`
- `MGM_UTIL = 16`

`SWICHING_COST`, `RAND_VALUE`, and `INFO` are not active in the main reviewed
algorithm paths. The typo `SWICHING_COST` is in the Java constant name.

Object messages are serialized Java objects. Timed object messages place the
sender's simulated time in `ACLMessage.language`; receivers take the maximum of
their local simulated time and the received timestamp, then add the static
message delay, which defaults to `0`.

The root calls `killall -9 java` from `AGENT_TERMINATE`, so the Java project is
experiment-runner code rather than a reusable library service.

## Sequential Greedy: `FORWARD` And `BACKWARD`

`FORWARD` solves one DCOP per time step from `0` upward:

- Use discounted decision tables and expected random tables for the current
  time step.
- If `timeStep > 0`, add unary switching-cost table to the previous chosen
  solution.
- In `INFINITE_HORIZON`, when solving `horizon - 1`, also add switching cost to
  the precomputed horizon assignment.

`BACKWARD` solves from `lastTimeStep` down to `0`:

- Use discounted decision tables and expected random tables for the current
  time step.
- If `timeStep < horizon`, add unary switching-cost table to the already chosen
  next-step solution.

Both can use DPOP or MGM as the one-step DCOP solver.

## MGM Path

MGM is used as a bounded-iteration subsolver with `MAX_ITERATION = 40`.

For each PD-DCOP time step:

1. Pick an initial random value for the agent.
2. Build the current MGM table list, including expected/actual tables and
   switching-cost unary tables as needed.
3. Repeat 40 iterations:
   - send current value to neighbors;
   - receive neighbor values;
   - compute the best single-value local gain;
   - send the gain to neighbors;
   - change value only if this agent's gain is strictly greater than every
     neighbor gain;
   - aggregate current quality through the pseudotree.

Tie behavior is strict: equal gain is not enough to move.

Root stores the best nondecreasing quality seen across MGM iterations and uses
runtime maps to estimate wasted runtime after convergence.

## Local Search: `LS_SDPOP` And `LS_RAND`

Local search is horizon-vector MGM-like improvement.

Initialization:

- `LS_SDPOP` first solves each time-step DCOP with DPOP, with special reuse of
  decision-only UTIL tables across time steps.
- `LS_RAND` picks a random value for every time step.

After initialization, local search has a separate handshake:

- `INIT_PROPAGATE_DPOP_VALUE` sends each agent's full chosen vector to all
  neighbors.
- `INIT_RECEIVE_DPOP_VALUE` stores neighbors' full vectors in
  `agentViewEachTimeStepMap`.
- `INIT_RECEIVE_SEND_LS_UTIL` aggregates the initial local-search quality
  through the pseudotree and stores it at iteration `-1`.

Each local-search iteration:

1. Each agent enumerates all local value sequences across the modeled time
   steps: `domain^(lastTimeStep + 1)`.
2. It evaluates cumulative discounted local utility against neighbor views,
   subtracting switching cost between adjacent local time-step values.
3. It records the best sequence and a per-time-step improvement map.
4. It sends the improvement map to all neighbors.
5. If any neighbor has a better improvement for a time step, this agent clears
   its own proposed value for that time step.
6. It applies remaining proposed values.
7. It sends changed values to neighbors so neighbor views are updated.
8. It aggregates current solution quality through the pseudotree.

The implementation runs a fixed 40 iterations, then reports the first point
where quality stops changing.

The pseudotree heuristic for reuse:

- `agentRandHeuristic = (2 if agent has random variable else 1) * number of
  neighboring random variables`
- `score = heuristicWeight * agentRandHeuristic + (1 - heuristicWeight) * degree`
- The maximum score becomes the root.
- DFS expands neighbors by descending score.

The paper found `heuristicWeight = 0.6` useful for LS-SDPOP; scripts set `0.6`
only for `LS_SDPOP` with DPOP and `0.0` otherwise.

## Online Evaluation

`ONLINE` and `STATIONARY` modes maintain two notions of quality:

- expected/discounted tables used by proactive methods for solving;
- actual tables after random values are sampled, used for effective quality.

Final aggregation:

- `SEND_RECEIVE_FINAL_VALUE` exchanges complete chosen value maps with
  neighbors.
- `SEND_RECEIVE_FINAL_UTIL` aggregates expected PD-DCOP utility through the
  pseudotree.
- For online/stationary modes, it also aggregates actual quality and actual
  switching cost for each time step.
- Root computes per-step solving time by differencing cumulative simulated
  solve times.

The effective output is a table with:

- horizon/time step;
- effective quality;
- effective switching cost;
- effective solving time;
- algorithm metadata.

The Java code tracks "simulated time" using Java thread user time plus message
timestamps carried in ACL message language fields. A Python port should separate
algorithm quality from wall-clock or simulated online adoption models.

## R-Learning Path

`R_LEARNING` is an experimental MD-DCOP-style path, not one of the main
PD-DCOP algorithms from the paper.

Key details:

- Uses `STATIONARY`-style random simulation.
- Initializes an `RFunction` over `AugmentedState`.
- State is either `(random, current)` at the first step or
  `(random, previous_decision, current_decision)` later.
- During learning, DPOP solves realized-state DCOPs.
- `R_LEARNING_UPDATE` updates local R values and average reward with fixed
  `alpha_r = 0.05`, `beta_r = 0.5`.
- During application, random-table utilities are replaced by learned R values.

Limitations:

- The update code says "Assume unary constraint".
- `R_LEARNING_APPLY` exists but the main schedule applies R values through
  DPOP table construction instead.
- This should be treated as reference/experimental material after the core
  PD-DCOP model and algorithms are stable.

`AugmentedState` is a tiny value object with `random`, optional `previous`, and
`current` fields. It is used as the key in the R-function map.

## Incomplete Or Stale Parts

- `BOUND_DPOP` contains TODOs and appears incomplete.
- `SDPOP` exists in the enum but does not have a clear main scheduling branch.
- `BROADCAST_RECEIVE_HEURISTIC_INFO.java` is entirely commented out.
- `MGM_READ_IMPROVE_MESSAGE.java` is a cyclic receiver for `MGM_VALUE`, but no
  active setup path adds it as a behaviour.
- `R_LEARNING_APPLY.java` exists, but the setup path does not schedule it.
- README and shell scripts are stale in places:
  - README omits `rLearningIteration`.
  - scripts refer to jar names like `ND-DCOP-1.0-jar-with-dependencies.jar`
    while `pom.xml` builds `pd-dcop`.
  - scripts mention algorithm names such as `C_DPOP`, while the enum uses
    `C_DCOP`.
- Some helper comments still describe minimization, but the active code
  maximizes utility.
- Stationary distributions are approximated by repeated transition
  multiplication rather than solved exactly.
- Missing utility lookup uses `-Double.MAX_VALUE`; Python code should prefer
  explicit invalid-assignment handling.

## Source Review Answers

These answer the open questions listed in `pddcop_jair_key_points.md`:

- Random variables and mixed constraints are represented as `Table` objects
  with decision labels, random labels, and rows split into decision values and
  random values.
- The Java project implements the main experimental algorithms from the paper
  plus extra/incomplete paths; it does not provide a clean implementation for
  every enum value.
- CDFU recursive terminal random utilities are computed by solving
  `(I - gamma P) V = gamma^h u` per decision tuple.
- Stationary distributions are not solved exactly; they are approximated by 40
  transition multiplications.
- JADE message passing is used directly for the distributed algorithms.
- Switching costs are encoded as unary negative-utility tables, or as collapsed
  unary sequence tables for `C_DCOP`.
- Local search and MGM both use fixed `MAX_ITERATION = 40`, with result output
  often selecting the first iteration where tracked quality stops improving.
- Infeasible or missing utilities are represented by `-Double.MAX_VALUE`.
- Online effective utility is computed from sampled realized random values and
  actual tables, then aggregated separately from expected PD-DCOP utility.

## Suggested Python Porting Order

1. Add a PD-DCOP model layer:
   - decision variables;
   - random variables;
   - initial distributions;
   - transition matrices;
   - decision-only and mixed utility relations;
   - horizon, discount factor, switching cost.

2. Add probability utilities:
   - transition validation;
   - distribution propagation;
   - exact stationary distribution computation;
   - optional sampled random trajectories for online simulation.

3. Add transformation utilities:
   - expected table construction for mixed random constraints;
   - CDFU horizon-tail construction for `gamma < 1`;
   - MCC/stationary expected table construction for `gamma == 1`;
   - switching-cost unary relations.

4. Add a centralized correctness baseline:
   - collapsed exact model;
   - solve with existing centralized solver when feasible;
   - test against small Java `.dzn` instances or converted YAML fixtures.

5. Add sequential greedy algorithms:
   - `FORWARD` first, because it is simplest and useful online/offline;
   - `BACKWARD` after fixed horizon/stationary handling is clear;
   - allow DPOP or centralized solver as the one-step backend before MGM.

6. Add distributed/local algorithms:
   - MGM one-step PD-DCOP subsolver if needed;
   - `LS_RAND`;
   - `LS_SDPOP` and reuse heuristics after DPOP/time-step reuse is well tested.

7. Add online simulation separately:
   - realized random trajectories;
   - actual utility tables;
   - solving/adoption time accounting;
   - effective utility metrics.

8. Treat R-learning and BOUND_DPOP as later optional work.

## Good Initial Tests

Small deterministic tests should cover:

- parsing or conversion of one `.dzn` fixture;
- propagation of a simple Markov distribution;
- stationary distribution for a known transition matrix;
- expected utility table from one mixed decision/random table;
- CDFU long-term table for a tiny two-state Markov chain;
- collapsed switching-cost unary table;
- `C_DCOP` on a one-agent one-random-variable fixture;
- `FORWARD` with and without switching cost;
- `REACT` actual-table construction from a fixed random realization;
- local-search best-response enumeration on a two-agent tiny horizon.

The Java fixture
`pddcop/pddcop_java/input_files/random_x5_y1_dx3_dy3/instance_0_x5_y1_dx3_dy3.dzn`
is a compact example of the file format.
