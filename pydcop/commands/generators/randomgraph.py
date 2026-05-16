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
.. _pydcop_commands_generate_random_graph:

pydcop generate random_graph
============================

Random graph DCOP generator
---------------------------

Synopsis
--------

::

  pydcop generate random_graph
                --variables_count <variables_count>
                --domain_size <domain_size>
                --p_edge <p_edge>
                --objective <objective>
                [--seed <seed>]
                [--no_agents]

Description
-----------

This command generates a DCOP whose constraint graph is a connected
Erdos-Renyi random graph. Each edge becomes an extensive binary constraint with
integer costs sampled uniformly in ``[0, 9]`` for every joint assignment.

Options
-------

``--variables_count <variables_count>``
  Number of variables. Must be at least 1.

``--domain_size <domain_size>``
  Number of values in each variable domain. Must be at least 1.

``--p_edge <p_edge>``
  Probability for edge creation in the Erdos-Renyi graph. The generated graph
  is always connected; low probabilities may fail after repeated attempts.
  When that happens, the error message recommends a larger ``p_edge`` or a
  larger ``variables_count`` using a connectivity-threshold heuristic.

``--objective <objective>``
  Optimization objective for the generated DCOP, either ``min`` or ``max``.

``--seed <seed>``
  Seed for random graph generation and constraint costs. Optional.

``--no_agents``
  Do not generate one agent per variable.

Examples
--------

Generate a random graph DCOP with 10 variables and domain size 3::

    pydcop generate random_graph --variables_count 10 --domain_size 3 \\
        --p_edge 0.4 --objective min --seed 12

"""
import logging
import math
import random

import networkx as nx

from pydcop.dcop.dcop import DCOP
from pydcop.dcop.objects import AgentDef, Variable, VariableDomain
from pydcop.dcop.relations import NAryMatrixRelation
from pydcop.dcop.yamldcop import dcop_yaml

logger = logging.getLogger("pydcop.cli.generate")

MAX_CONNECTED_GRAPH_ATTEMPTS = 1000
DEFAULT_AGENT_CAPACITY = 99


def init_cli_parser(parent_parser):
    parser = parent_parser.add_parser(
        "random_graph", help="Generate a random graph DCOP"
    )
    parser.set_defaults(func=generate)

    parser.add_argument(
        "-v", "--variables_count", type=int, required=True, help="Number of variables"
    )
    parser.add_argument(
        "-d",
        "--domain_size",
        type=int,
        required=True,
        help="Number of values in each variable domain",
    )
    parser.add_argument(
        "-p",
        "--p_edge",
        type=float,
        required=True,
        help="Probability for edge creation in the random graph",
    )
    parser.add_argument(
        "--objective",
        choices=["min", "max"],
        required=True,
        help="Optimization objective for the generated DCOP",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed value for random graph generation and constraint costs",
    )
    parser.add_argument(
        "--no_agents",
        default=False,
        required=False,
        action="store_true",
        help="Do not generate agents",
    )
    parser.add_argument(
        "--capacity",
        type=int,
        required=False,
        default=DEFAULT_AGENT_CAPACITY,
        help="Capacity of agents",
    )


def generate(args):
    random_generator = random.Random(args.seed)
    dcop = generate_random_graph_dcop(
        args.variables_count,
        args.domain_size,
        args.p_edge,
        args.objective,
        no_agents=args.no_agents,
        capacity=args.capacity,
        random_generator=random_generator,
    )

    if args.output:
        output_file = args.output
        with open(output_file, encoding="utf-8", mode="w") as fo:
            fo.write(dcop_yaml(dcop))
    else:
        print(dcop_yaml(dcop))


def generate_random_graph_dcop(
    variables_count,
    domain_size,
    p_edge,
    objective,
    no_agents=False,
    random_generator=None,
    capacity=DEFAULT_AGENT_CAPACITY,
):
    if random_generator is None:
        random_generator = random

    if variables_count < 1:
        raise ValueError("--variables_count must be at least 1")
    if domain_size < 1:
        raise ValueError("--domain_size must be at least 1")
    if p_edge < 0 or p_edge > 1:
        raise ValueError("--p_edge must be between 0 and 1")
    if variables_count > 1 and p_edge == 0:
        raise ValueError(
            "--p_edge must be greater than 0 to generate a connected graph "
            "with more than one variable"
        )

    graph = generate_connected_random_graph(
        variables_count, p_edge, random_generator
    )
    domain = VariableDomain("d", "value", range(domain_size))

    variables = {}
    for node in sorted(graph.nodes):
        variable = Variable(f"v{node:02d}", domain)
        variables[node] = variable

    agents = {}
    if not no_agents:
        for node in sorted(graph.nodes):
            agent = AgentDef(f"a{node:02d}", capacity=capacity)
            agents[agent.name] = agent

    constraints = generate_random_constraints(graph, variables, random_generator)

    return DCOP(
        f"RandomGraph_{variables_count}_{domain_size}_{p_edge}",
        objective=objective,
        domains={domain.name: domain},
        variables={variable.name: variable for variable in variables.values()},
        agents=agents,
        constraints=constraints,
    )


def generate_connected_random_graph(
    variables_count,
    p_edge,
    random_generator,
    max_attempts=MAX_CONNECTED_GRAPH_ATTEMPTS,
):
    for _ in range(max_attempts):
        graph = nx.gnp_random_graph(variables_count, p_edge, seed=random_generator)
        if nx.is_connected(graph):
            return graph

    raise ValueError(
        "Could not generate a connected random graph after "
        f"{max_attempts} attempts. "
        f"Try p_edge >= {recommended_p_edge(variables_count):.2f} "
        f"or variables_count >= {recommended_variables_count(p_edge)}."
    )


def recommended_p_edge(variables_count):
    if variables_count <= 1:
        return 0
    return min(1, (math.log(variables_count) + 2) / variables_count)


def recommended_variables_count(p_edge):
    if p_edge <= 0:
        return 1
    if p_edge >= 1:
        return 2

    low = 2
    high = 2
    while p_edge < recommended_p_edge(high):
        low = high + 1
        high *= 2

    while low < high:
        midpoint = (low + high) // 2
        if p_edge >= recommended_p_edge(midpoint):
            high = midpoint
        else:
            low = midpoint + 1

    return low


def generate_random_constraints(graph, variables, random_generator):
    constraints = {}
    for i, edge in enumerate(graph.edges):
        logger.debug("edge %s - %s", edge, i)
        name = f"c{i}"
        node1, node2 = edge
        variable1 = variables[node1]
        variable2 = variables[node2]
        constraint = NAryMatrixRelation([variable1, variable2], name=name)

        for value1 in variable1.domain:
            for value2 in variable2.domain:
                constraint = constraint.set_value_for_assignment(
                    {variable1.name: value1, variable2.name: value2},
                    random_generator.randint(0, 9),
                )
        constraints[name] = constraint

    return constraints
