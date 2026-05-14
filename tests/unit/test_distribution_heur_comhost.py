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

from pydcop.computations_graph.objects import ComputationGraph, ComputationNode
from pydcop.dcop.objects import AgentDef
from pydcop.distribution.heur_comhost import distribute


def _memory_footprint(computation):
    return {"c_big": 3, "c_mid": 2, "c_small": 2}[computation.name]


def _communication_load(computation, other):
    return 0


def test_distribute_rebuilds_candidates_after_backtracking():
    computation_graph = ComputationGraph(
        nodes=[
            ComputationNode("c_big"),
            ComputationNode("c_mid"),
            ComputationNode("c_small"),
        ]
    )
    agents = [
        AgentDef(
            "a1",
            capacity=4,
            default_hosting_cost=1,
            hosting_costs={"c_big": 0},
        ),
        AgentDef(
            "a2",
            capacity=3,
            default_hosting_cost=1,
            hosting_costs={"c_big": 10},
        ),
    ]

    distribution = distribute(
        computation_graph,
        agents,
        memory_footprint_estimate=_memory_footprint,
        communication_load=_communication_load,
    )

    assert distribution.agent_for("c_big") == "a2"
    assert distribution.agent_for("c_mid") == "a1"
    assert distribution.agent_for("c_small") == "a1"
