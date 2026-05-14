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

import pytest

from pydcop.computations_graph.objects import ComputationGraph, ComputationNode
from pydcop.dcop.objects import AgentDef
from pydcop.distribution import oilp_cgdp
from pydcop.distribution.objects import ImpossibleDistributionException


def _hosting_cost(agents):
    agents_by_name = {agent.name: agent for agent in agents}

    def hosting_cost(agent, computation):
        return agents_by_name[agent].hosting_cost(computation)

    return hosting_cost


def test_fixed_assignments_uses_unique_explicit_zero_hosting_cost():
    agents = [
        AgentDef("a1", hosting_costs={"c1": 0}),
        AgentDef("a2"),
    ]

    fixed = oilp_cgdp._fixed_assignments(
        ["c1"], agents, _hosting_cost(agents)
    )

    assert fixed == {"c1": "a1"}


def test_fixed_assignments_ignore_ambiguous_explicit_zero_hosting_costs():
    agents = [
        AgentDef("a1", hosting_costs={"c1": 0}),
        AgentDef("a2", hosting_costs={"c1": 0}),
    ]

    fixed = oilp_cgdp._fixed_assignments(
        ["c1"], agents, _hosting_cost(agents)
    )

    assert fixed == {}


def test_ilp_cgdp_returns_all_fixed_assignments_without_solver(monkeypatch):
    def fail_if_solver_is_used(*args, **kwargs):
        raise AssertionError("fixed-only distribution should not call GLPK")

    monkeypatch.setattr(oilp_cgdp, "GLPK_CMD", fail_if_solver_is_used)

    computation_graph = ComputationGraph(
        nodes=[ComputationNode("c1"), ComputationNode("c2")]
    )
    agents = [
        AgentDef("a1", capacity=1, default_hosting_cost=1, hosting_costs={"c1": 0}),
        AgentDef("a2", capacity=1, default_hosting_cost=1, hosting_costs={"c2": 0}),
    ]

    mapping = oilp_cgdp.ilp_cgdp(
        computation_graph,
        agents,
        footprint=lambda computation: 1,
        capacity=lambda agent: 1,
        route=lambda source, target: 0 if source == target else 1,
        msg_load=lambda source, target: 0,
        hosting_cost=_hosting_cost(agents),
    )

    assert mapping == {"a1": ["c1"], "a2": ["c2"]}


def test_ilp_cgdp_rejects_fixed_assignments_over_capacity():
    computation_graph = ComputationGraph(nodes=[ComputationNode("c1")])
    agents = [
        AgentDef("a1", capacity=1, default_hosting_cost=1, hosting_costs={"c1": 0}),
        AgentDef("a2", capacity=10, default_hosting_cost=1),
    ]

    with pytest.raises(ImpossibleDistributionException, match="Not enough capacity"):
        oilp_cgdp.ilp_cgdp(
            computation_graph,
            agents,
            footprint=lambda computation: 2,
            capacity=lambda agent: 1 if agent == "a1" else 10,
            route=lambda source, target: 0 if source == target else 1,
            msg_load=lambda source, target: 0,
            hosting_cost=_hosting_cost(agents),
        )


def test_distribute_handles_mixed_fixed_and_free_computations():
    computation_graph = ComputationGraph(
        nodes=[
            ComputationNode("c1", neighbors=["c2"]),
            ComputationNode("c2", neighbors=["c1"]),
        ]
    )
    agents = [
        AgentDef("a1", capacity=2, default_hosting_cost=1, hosting_costs={"c1": 0}),
        AgentDef("a2", capacity=2, default_hosting_cost=1),
    ]

    distribution = oilp_cgdp.distribute(
        computation_graph,
        agents,
        memory_footprint_estimate=lambda computation: 1,
        communication_load=lambda computation, other: 1,
    )

    assert distribution.agent_for("c1") == "a1"
    assert distribution.agent_for("c2") == "a1"
