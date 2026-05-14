# BSD-3-Clause License
#
# Copyright 2017 Orange
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
OILP-CGDP : Optimal ILB-based distribution for Computation Graph

This is a generic distribution method, which works for any computation graph (constraint
graph, factor graph, etc.).

This method optimizes the distribution for:
* hosting costs
* communication cost, made of communication load (betwwen two computation)
  and route costs (between two agents)
A weighted sum is used to aggregate these two objectives.

Agents's capacities are used as hard constraints for the distribution.

References:
    AAMAS 2018

"""
import logging
import time
from itertools import combinations
from collections.abc import Iterable, Callable

import pulp
from pulp import (
    LpMinimize,
    LpProblem,
    LpVariable,
    LpBinary,
    LpStatusOptimal,
    GLPK_CMD,
    lpSum,
    LpAffineExpression,
    LpStatusUndefined, PulpSolverError)

from pydcop.computations_graph.objects import ComputationGraph, ComputationNode
from pydcop.dcop.objects import AgentDef
from pydcop.distribution.objects import (
    DistributionHints,
    Distribution,
    ImpossibleDistributionException,
)

logger = logging.getLogger("distribution.oilp_cgdp")


# Weight factors when aggregating communication costs and hosting costs in the
# objective function.
# the global objective is built as Comm_cost * RATIO + Hosting_cost * (1-RATIO)
RATIO_HOST_COMM = 0.8


def distribute(
    computation_graph: ComputationGraph,
    agentsdef: Iterable[AgentDef],
    hints: DistributionHints = None,
    memory_footprint_estimate=None,
    communication_load=None,
    timeout=600,  # Max 10 min
) -> Distribution:
    """

    Parameters
    ----------
    computation_graph
    agentsdef
    hints
    memory_footprint_estimate
    communication_load

    Returns
    -------

    """
    footprint_f = footprint_fonc(computation_graph, memory_footprint_estimate)
    capacity_f = capacity_fonc(agentsdef)
    route_f = route_fonc(agentsdef)
    msg_load_f = msg_load_func(computation_graph, communication_load)
    hosting_cost_f = hosting_cost_func(agentsdef)

    return Distribution(
        ilp_cgdp(
            computation_graph,
            agentsdef,
            footprint_f,
            capacity_f,
            route_f,
            msg_load_f,
            hosting_cost_f,
            timeout=timeout
        )
    )


def distribution_cost(
    distribution: Distribution,
    computation_graph: ComputationGraph,
    agentsdef: Iterable[AgentDef],
    memory_footprint_estimate: Callable[[ComputationNode], float],
    communication_load: Callable[[ComputationNode, str], float],
) -> float:
    route = route_fonc(agentsdef)
    msg_load = msg_load_func(computation_graph, communication_load)
    hosting_cost = hosting_cost_func(agentsdef)

    comm = 0
    for link in computation_graph.links:
        # As we support hypergraph, we may have more than 2 ends to a link
        for c1, c2 in combinations(link.nodes, 2):
            a1 = distribution.agent_for(c1)
            a2 = distribution.agent_for(c2)
            comm += route(a1, a2) * msg_load(c1, c2)

    hosting = 0
    for computation in computation_graph.nodes:
        agent = distribution.agent_for(computation.name)
        hosting += hosting_cost(agent, computation.name)

    cost = RATIO_HOST_COMM * comm + (1 - RATIO_HOST_COMM) * hosting
    return cost, comm, hosting


def ilp_cgdp(
    cg: ComputationGraph,
    agentsdef: Iterable[AgentDef],
    footprint: Callable[[str], float],
    capacity: Callable[[str], float],
    route: Callable[[str, str], float],
    msg_load: Callable[[str, str], float],
    hosting_cost: Callable[[str, str], float],
    timeout=600, # Max 10 min
):
    start_t = time.time()

    agents = list(agentsdef)
    agt_names = [a.name for a in agents]
    comp_names = cg.node_names()
    fixed_assignments = _fixed_assignments(comp_names, agents, hosting_cost)
    comps_to_host = [c for c in comp_names if c not in fixed_assignments]
    fixed_footprints = {
        a: sum(
            footprint(c)
            for c, fixed_agent in fixed_assignments.items()
            if fixed_agent == a
        )
        for a in agt_names
    }
    for agent, fixed_footprint in fixed_footprints.items():
        if fixed_footprint > capacity(agent):
            raise ImpossibleDistributionException(
                f"Not enough capacity on {agent} for fixed computations"
            )
    pb = LpProblem("oilp_cgdp", LpMinimize)

    # One binary variable xij for each non-fixed (variable, agent) couple.
    xs = _build_xs_binvars(comps_to_host, agt_names)

    if fixed_assignments:
        logger.debug("Fixed computations from zero hosting costs: %s", fixed_assignments)

    # One binary variable for computations c1 and c2, and agent a1 and a2
    comm_terms = []
    processed_pairs = set()
    for a1, a2 in combinations(agt_names, 2):
        # Only create variables for couple c1, c2 if there is an edge in the
        # graph between these two computations.
        for link in cg.links:
            # As we support hypergraph, we may have more than 2 ends to a link
            for c1, c2 in combinations(link.nodes, 2):
                pair = frozenset((c1, c2))
                if (pair, a1, a2) in processed_pairs:
                    continue
                processed_pairs.add((pair, a1, a2))

                c1_on_a1 = _assignment_expr(c1, a1, xs, fixed_assignments)
                c2_on_a2 = _assignment_expr(c2, a2, xs, fixed_assignments)
                _add_comm_term(
                    pb,
                    comm_terms,
                    c1_on_a1,
                    c2_on_a2,
                    route(a1, a2) * msg_load(c1, c2),
                    f"b_{c1}_{a1}_{c2}_{a2}",
                )

                c1_on_a2 = _assignment_expr(c1, a2, xs, fixed_assignments)
                c2_on_a1 = _assignment_expr(c2, a1, xs, fixed_assignments)
                _add_comm_term(
                    pb,
                    comm_terms,
                    c1_on_a2,
                    c2_on_a1,
                    route(a2, a1) * msg_load(c1, c2),
                    f"b_{c1}_{a2}_{c2}_{a1}",
                )

    # Set objective: communication + hosting_cost
    pb += (
        _objective(xs, comm_terms, hosting_cost),
        "Communication costs and prefs",
    )

    # Adding constraints:
    # Constraints: Memory capacity for all agents.
    for a in agt_names:
        pb += (
            lpSum([footprint(i) * xs[i, a] for i in comps_to_host])
            + fixed_footprints[a]
            <= capacity(a),
            f"Agent {a} capacity",
        )

    # Constraints: all computations must be hosted.
    for c in comps_to_host:
        pb += (
            lpSum([xs[c, a] for a in agt_names]) == 1,
            f"Computation {c} hosted",
        )

    if not comps_to_host:
        mapping = {a: [] for a in agt_names}
        for comp, agent in fixed_assignments.items():
            mapping[agent].append(comp)
        return mapping

    # the timeout for the solver must be minored by the time spent to build the pb:
    remaining_time = round(timeout - (time.time() - start_t)) -2
    # solve using GLPK
    try:
        status = pb.solve(solver=GLPK_CMD(keepFiles=0, msg=False, options=["--pcost", "--tmlim", str(remaining_time)]))
    except PulpSolverError as pse:
        raise ImpossibleDistributionException(f"Pulp error {pse}", pse)
    if status == LpStatusUndefined:
        # Generally means we have reach the timeout.
        raise TimeoutError(f"Could not find solution in {timeout}")

    if status != LpStatusOptimal:
        raise ImpossibleDistributionException(f"No possible optimal distribution {status}")
    logger.debug("GLPK cost : %s", pulp.value(pb.objective))

    mapping = {}
    for k in agt_names:
        agt_computations = [
            c for c, agent in fixed_assignments.items() if agent == k
        ]
        agt_computations += [
            i for i, ka in xs if ka == k and pulp.value(xs[(i, ka)]) == 1
        ]
        # print(k, ' -> ', agt_computations)
        mapping[k] = agt_computations
    return mapping


def _build_xs_binvars(comps_to_host, agt_names):
    if not comps_to_host:
        return {}
    return LpVariable.dict("x", (comps_to_host, agt_names), cat=LpBinary)


def _fixed_assignments(comp_names, agents, hosting_cost):
    fixed = {}
    for comp in comp_names:
        explicit_zero_cost_agents = [
            agent.name for agent in agents if agent.hosting_costs.get(comp) == 0
        ]
        if len(explicit_zero_cost_agents) == 1:
            fixed[comp] = explicit_zero_cost_agents[0]
            continue
        if len(explicit_zero_cost_agents) > 1:
            continue

        zero_cost_agents = [
            agent.name for agent in agents if hosting_cost(agent.name, comp) == 0
        ]
        if len(zero_cost_agents) == 1:
            fixed[comp] = zero_cost_agents[0]
    return fixed


def _assignment_expr(comp, agent, xs, fixed_assignments):
    if comp in fixed_assignments:
        return 1 if fixed_assignments[comp] == agent else 0
    return xs[(comp, agent)]


def _add_comm_term(pb, comm_terms, first_hosted, second_hosted, cost, name):
    if _is_zero(first_hosted) or _is_zero(second_hosted):
        return
    if _is_constant(first_hosted) and _is_constant(second_hosted):
        comm_terms.append(cost)
    elif _is_constant(first_hosted):
        comm_terms.append(cost * second_hosted)
    elif _is_constant(second_hosted):
        comm_terms.append(cost * first_hosted)
    else:
        beta = LpVariable(name, cat=LpBinary)
        pb += beta <= first_hosted
        pb += beta <= second_hosted
        pb += beta >= first_hosted + second_hosted - 1
        comm_terms.append(cost * beta)


def _is_constant(value):
    return isinstance(value, int)


def _is_zero(value):
    return _is_constant(value) and value == 0


def _objective(xs, comm_terms, hosting_cost):
    # We want to minimize communication and hosting costs
    # Objective is the communication + hosting costs
    comm = lpSum(comm_terms) if comm_terms else LpAffineExpression()
    costs = lpSum([hosting_cost(a, c) * xs[(c, a)] for c, a in xs])

    return lpSum([RATIO_HOST_COMM * comm, (1 - RATIO_HOST_COMM) * costs])


def footprint_fonc(
    cg: ComputationGraph, memory_footprint_estimate: Callable[[ComputationNode], float]
) -> Callable[[str], float]:
    """

    Parameters
    ----------
    cg: ComputationGraph
        the computation graph
    memory_footprint_estimate: Callable
        a function giving a memory footprint from a computation node and a set of links
         in the computation graph

    Returns
    -------
    Callable:
        a function that returns the memory footprint of a computation
        given it's name
    """

    def footprint(computation_name: str):
        c = cg.computation(computation_name)
        return memory_footprint_estimate(c)

    return footprint


def msg_load_func(
    cg: ComputationGraph, communication_load: Callable[[ComputationNode, str], float]
) -> Callable[[str, str], float]:
    def msg_load(c1: str, c2: str) -> float:
        load = 0
        links = cg.links_for_node(c1)
        for link in links:
            if c2 in link.nodes:
                load += communication_load(cg.computation(c1), c2)
        return load

    return msg_load


def capacity_fonc(agents_def: Iterable[AgentDef]) -> Callable[[str], float]:
    """
    :param agents_def:
    :return: a function that gives the agent's capacity given it's name
    """

    def capacity(agent_name):
        for a in agents_def:
            if a.name == agent_name:
                return a.capacity

    return capacity


def route_fonc(agents_def: Iterable[AgentDef]) -> Callable[[str, str], float]:
    def route(a1_name: str, a2_name: str):
        for a in agents_def:
            if a.name == a1_name:
                return a.route(a2_name)

    return route


def hosting_cost_func(agts_def: Iterable[AgentDef]) -> Callable[[str, str], float]:
    """

    :param agts_def: the AgentsDef
    :return: a function that returns the hosting cost for agt, comp
    """

    def cost(agt_name: str, comp_name: str):
        for a in agts_def:
            if a.name == agt_name:
                return a.hosting_cost(comp_name)

    return cost
