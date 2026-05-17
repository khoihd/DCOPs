# Proactive Dynamic DCOPs: Key Points

Source: `pddcop/pddcop_jair.pdf`

Paper: "Proactive Dynamic Distributed Constraint Optimization Problems", JAIR 74, 2022, by Khoi D. Hoang, Ferdinando Fioretto, Ping Hou, William Yeoh, Makoto Yokoo, and Roie Zivan.

## Purpose

The paper introduces Proactive Dynamic DCOPs (PD-DCOPs), a model for dynamic distributed constraint optimization when agents have probabilistic knowledge about how the problem may change over time.

Classic Dynamic DCOP work is mostly reactive: solve the current DCOP after changes are observed. PD-DCOPs are proactive: solve using known or predicted exogenous uncertainty before those changes fully realize.

The central practical question is when proactive planning is worth it compared with reactive replanning. The paper finds that proactive and hybrid methods are most useful when switching costs are high or the problem changes quickly; reactive methods work best when switching costs are low and agents have enough time to react.

## Core PD-DCOP Model

A PD-DCOP is a tuple:

`<A, X, Y, D, Omega, F, p0_Y, T, gamma, h, c, alpha>`

Where:

- `A`: agents.
- `X`: decision variables controlled by agents.
- `Y`: random variables representing exogenous uncertain state.
- `D`: finite domains for decision variables.
- `Omega`: finite domains for random variables.
- `F`: utility functions over decision variables and optionally random variables.
- `p0_Y`: initial probability distributions for random variables.
- `T`: transition matrices/functions for random variables.
- `gamma`: discount factor in `[0, 1]`.
- `h`: finite planning horizon.
- `c`: switching cost for changing a decision variable value between time steps.
- `alpha`: mapping from decision variables to agents.

Important assumptions used by the paper:

- Each agent controls exactly one decision variable.
- Each utility function has at most one random variable. If a function involves several random variables, they can be merged into one joint random variable.
- Random variables evolve independently through time-homogeneous Markov chains.
- Switching cost is identical across decision variables in the formal model.

## Objective

The solution is an open-loop sequence of assignments:

`x = <x^0, x^1, ..., x^h>`

The objective maximizes:

- discounted utility over time steps `0..h-1`;
- expected utility for constraints involving random variables, using the distribution of each random variable at each time step;
- minus discounted switching costs between consecutive decision assignments;
- plus a terminal/future utility term from time `h` onward.

The model separates utility functions into:

- `F_X`: constraints involving only decision variables.
- `F_Y`: constraints involving decision variables and one random variable.

For random-variable constraints, expected utility at time `t` is computed by summing over random states:

`sum_omega f(x | y = omega) * p_y^t(omega)`

Each random variable distribution evolves by:

`p_y^t(omega) = sum_omega' p_y^{t-1}(omega') * T_y(omega', omega)`

## Future Utility Handling

The paper uses two future-utility treatments depending on `gamma`.

### CDFU: Gamma Less Than 1

CDFU means Cumulative Discounted Future Utilities.

When `gamma < 1`, future utilities are discounted, so the infinite tail can be folded into the horizon utility.

For constraints without random variables, the terminal future term is scaled by:

`gamma^h / (1 - gamma)`

For constraints with random variables, the paper defines a recursive future expected utility over the Markov transition matrix. This behaves like a discounted infinite-horizon value calculation for a fixed decision assignment at horizon `h`.

Implementation idea:

- Use propagated random-variable distributions for `t = 0..h`.
- At horizon `h`, replace future random utility with a discounted expected tail value.
- Solve `0..h` together.

### MCC: Gamma Equals 1

MCC means Markov Chain Convergence.

When `gamma = 1`, future time steps are not discounted. The paper assumes each random variable Markov chain converges to a unique stationary distribution.

For each random variable `y`, compute stationary distribution `p*_y` satisfying:

`p*_y * T_y = p*_y`

and

`sum_omega p*_y(omega) = 1`

Then solve the horizon problem using stationary expected utilities:

`sum_omega f(x | y = omega) * p*_y(omega)`

Implementation idea:

- Solve the horizon assignment `s_h` using the stationary distribution.
- Then solve time steps `0..h-1`, including switching cost from time `h-1` to fixed assignment `s_h`.

## Exact Approach: Collapsed DCOP

The exact approach transforms the PD-DCOP into one equivalent static DCOP.

Key transformation:

- Each original decision variable `x_i` becomes a vector variable:
  `<x_i^0, x_i^1, ..., x_i^hbar>`.
- Its new domain is the Cartesian product of its original domain over all modeled time steps.
- Utility functions are collapsed by summing discounted utilities across time.
- Random-variable constraints are converted into expected utility constraints using the appropriate random-variable distributions.
- Each decision variable receives a unary switching-cost function over its vector assignment.

This collapsed DCOP can be solved by an exact DCOP algorithm such as DPOP.

Implementation implications:

- This is conceptually simple and good as a correctness baseline.
- Domain size grows exponentially with horizon: `|D_x|^(h+1)`.
- In practice it scales poorly beyond small horizons.

The paper calls the DPOP-based exact version `C-DPOP`.

## Heuristic Approach: Dynamic Sequence of DCOPs

The heuristic approach transforms the PD-DCOP into a sequence of ordinary DCOPs, one per time step, by removing random variables through expected utilities.

For every time step:

- Decision-only constraints are discounted.
- Random constraints become expected unary or lower-arity constraints over decision variables.
- Switching costs are handled either inside local search or through additional unary constraints in greedy sequential methods.

This supports two main heuristic families:

- Local Search.
- Sequential Greedy.

## Local Search Approach

The local search algorithm is inspired by MGM.

Each agent maintains:

- current assignment vector across all time steps;
- best local assignment vector;
- neighbor context for every neighbor and time step;
- current utilities;
- best utilities;
- gains per time step.

Process:

1. Initialize one value per time step.
2. Send `VALUE` messages containing the current vector assignment to neighbors.
3. Once neighbor contexts are current, enumerate all local value vectors across the horizon.
4. Compute the best cumulative local utility, including switching cost.
5. Send `GAIN` messages to neighbors.
6. At each time step, change value only if this agent has the largest positive gain among neighbors.
7. Repeat until the termination condition.

Important implementation details:

- Best response enumeration is over `D^(h+1)` local value sequences.
- Utility per time step includes local constraint utility minus switching cost to adjacent time steps.
- If a fixed next-horizon assignment exists, switching from `hbar` to `hbar + 1` is included.
- Like MGM, neighboring agents should not change conflicting values in the same time step if another has higher gain.
- The paper proves local-search solution quality is monotonically increasing by iteration.

Initial-assignment variants:

- `LS-SDPOP`: initialize each time step with S-DPOP.
- `LS-MGM`: initialize with MGM.
- `LS-RAND`: random initialization.

The paper proposes a pseudo-tree heuristic for `LS-SDPOP`:

- Put agents constrained with random variables higher in the pseudo-tree to maximize reuse across successive DCOPs.
- Combine that with max-degree using a weight `w`.
- Experiments found `w = 0.6` effective in their random-network setup.

## Sequential Greedy Approaches

Sequential greedy methods solve one time step at a time using an ordinary DCOP solver.

### FORWARD

FORWARD solves from `t = 0` to `hbar`.

At each step it:

- solves the current DCOP;
- adds unary switching-cost constraints from the previous solution;
- at the last step, if a fixed future assignment exists, also includes switching cost to that future assignment.

This is proactive and can be run offline.

### BACKWARD

BACKWARD solves from the fixed horizon solution backward.

It is applicable when the next assignment `x^(hbar+1)` is available, especially in the MCC case where the stationary-distribution horizon solution is computed first.

At each step it adds switching cost to the already chosen next time-step solution.

## Online Approaches

The paper compares three online styles:

- `FORWARD`: proactive; computes solutions ahead of time.
- `REACT`: reactive; waits for the random variables to realize, then solves the current problem.
- `HYBRID`: uses observed random-variable values at time `t` to update the distribution for time `t+1`, then solves the next problem before it arrives.

Effective utility accounts for:

- the time spent searching;
- the time a found solution is actually adopted;
- the previous solution used while searching;
- current solution quality;
- switching cost between adopted solutions.

Implementation takeaway:

- A later Python implementation should probably separate offline solution quality from online effective utility simulation.
- Online evaluation needs timing/adoption windows, not just objective values.

## Theoretical Results

Complexity:

- Optimally solving PD-DCOPs is PSPACE-complete when the horizon is polynomial in the number of variables.
- It is PSPACE-hard when the horizon is exponential.

MCC result:

- When `gamma = 1`, adopting the optimal solution for the stationary distribution from time `h` onward maximizes expected utility from that point onward, under the paper's convergence assumptions.

CDFU error bound:

- When `gamma < 1`, finite-horizon error is bounded by a geometric tail:
  `gamma^h / (1 - gamma) * F_delta`.

MCC error bound:

- With positive minimum joint transition probability, the finite-horizon MCC error decreases according to the Markov-chain convergence rate, plus a switching-cost term.

Local-search complexity:

- Per-agent space: `O(L + (h + 1)|A|)`, where `L` is the initial-assignment solver space.
- Per-iteration local best-response time: `O(D^h)` in the paper's notation, with `D` the maximum decision-domain size.

## Experimental Findings

Offline experiments compare:

- `C-DPOP`.
- `LS-SDPOP`, `LS-MGM`, `LS-RAND`.
- `F-DPOP`, `F-MGM`.
- `B-DPOP`, `B-MGM`.

Problem domains:

- random networks;
- dynamic distributed meeting scheduling;
- distributed radar coordination and scheduling.

Main findings:

- `C-DPOP` is exact but scales poorly because the collapsed variable domains grow exponentially with horizon.
- DPOP-based methods give better solution quality than MGM-based methods but time out sooner.
- MGM-based methods and `LS-RAND` scale to larger instances.
- Sequential greedy methods often perform well when switching costs are significant because they account for switching costs while choosing each step.
- Local search can improve initially infeasible or low-quality solutions, but may get stuck in local maxima and can be sensitive to switching cost.
- `LS-SDPOP` tends to require fewer local-search iterations because it starts with stronger per-time-step solutions.

Online findings:

- Reactive algorithms are best when switching cost is small and there is enough time between changes.
- Proactive algorithms are best when switching cost is large or changes happen quickly.
- Hybrid algorithms gain from both sides: they can adopt immediately like proactive approaches while using observations to improve next-step predictions.

## Relation To MD-DCOPs

PD-DCOPs differ from Markovian Dynamic DCOPs (MD-DCOPs):

- MD-DCOPs assume state observability.
- PD-DCOPs can operate without observing random-variable realizations.
- PD-DCOPs include explicit switching costs.
- PD-DCOP solutions are open-loop assignment sequences, unlike closed-loop policies in Dec-MDP/Dec-POMDP-style models.

For fair comparison, the paper augments MD-DCOP state with previous decision assignments so switching cost can be represented.

Trade-off:

- R-learning-style MD-DCOP methods can exploit observed states and avoid overly reactive switching.
- They require training and may be less attractive when computation time is limited.

## Implementation Notes For This Repository

Likely useful Python implementation layers:

1. `PD-DCOP` data model:
   - decision variables;
   - random variables;
   - initial distributions;
   - transition matrices;
   - mixed constraints;
   - discount factor;
   - horizon;
   - switching cost.

2. Probability utilities:
   - propagate `p_y^t = p_y^(t-1) T_y`;
   - compute stationary distributions for MCC;
   - validate Markov matrices.

3. Constraint transformation:
   - turn mixed decision/random constraints into expected decision-only constraints for each time step;
   - compute CDFU terminal terms for `gamma < 1`;
   - compute MCC horizon constraints for `gamma = 1`.

4. Exact collapsed solver path:
   - build vector-valued variables over the horizon;
   - generate collapsed constraints;
   - add switching-cost unary constraints;
   - solve with an existing exact solver when feasible.

5. Sequential greedy path:
   - implement FORWARD first;
   - optionally implement BACKWARD for MCC/fixed-horizon assignments;
   - use existing DCOP solvers for each time-step subproblem.

6. Local search path:
   - implement after the transformations are tested;
   - reuse MGM concepts where possible;
   - message classes likely need value vectors and gain vectors;
   - local best-response search is over per-agent time-step value sequences.

7. Online simulation path:
   - separate from offline algorithms;
   - model actual realized random-variable trajectories;
   - compute effective utility with search/adoption time windows.

## Open Questions For Java-Source Reading

- How does the Java project represent random variables and mixed constraints?
- Does it implement all algorithms from the paper or a subset?
- How are CDFU recursive terminal utilities computed numerically?
- How does it solve stationary distributions?
- Does it use JADE message passing directly for all distributed algorithms?
- How does it encode switching costs in generated unary constraints?
- What termination conditions are used for local search and MGM?
- How are infeasible utilities represented?
- How is online effective utility simulated?
- Which pieces should be ported literally and which should map to pyDcop's existing abstractions?
