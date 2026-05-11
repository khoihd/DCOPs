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

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable, Mapping

from pydcop.dcop.dcop import DCOP
from pydcop.dcop.yamldcop import load_dcop_from_file
from tests.api.instances_and_utils import dcop_graphcoloring_3
from tests.integration.dmaxsum_graphcoloring import build_graph_coloring_problem
from tests.unit.test_algorithms_syncbb import build_pb


INSTANCE_DIR = Path(__file__).resolve().parents[1] / "instances"


@dataclass(frozen=True)
class KnownDcopCase:
    name: str
    dcop_factory: Callable[[], DCOP]
    optimal_cost: float
    optimal_assignment: Mapping[str, object] | None = None


def load_test_dcop(filename):
    return load_dcop_from_file([str(INSTANCE_DIR / filename)])


def build_syncbb_dcop(objective):
    variables, constraints = build_pb()
    return DCOP(
        name=f"syncbb_{objective}",
        variables={variable.name: variable for variable in variables},
        constraints={constraint.name: constraint for constraint in constraints},
        objective=objective,
    )


def build_dynamic_graphcoloring_dcop(relation_name):
    variables, relation_states, _ = build_graph_coloring_problem()
    relations = relation_states[relation_name]
    return DCOP(
        name=f"dmaxsum_{relation_name}",
        variables={variable.name: variable for variable in variables},
        constraints={relation.name: relation for relation in relations},
        objective="min",
    )


KNOWN_INSTANCE_SOLUTIONS = (
    KnownDcopCase(
        name="api_graphcoloring_3",
        dcop_factory=dcop_graphcoloring_3,
        optimal_assignment={"v1": "R", "v2": "G", "v3": "R"},
        optimal_cost=-0.1,
    ),
    KnownDcopCase(
        name="yaml_graph_coloring1",
        dcop_factory=lambda: load_test_dcop("graph_coloring1.yaml"),
        optimal_assignment={"v1": "R", "v2": "G", "v3": "R"},
        optimal_cost=-0.1,
    ),
    KnownDcopCase(
        name="yaml_secp_simple1",
        dcop_factory=lambda: load_test_dcop("secp_simple1.yaml"),
        optimal_assignment={"l1": 0, "l2": 3, "l3": 4, "m1": 3},
        optimal_cost=2.3,
    ),
    KnownDcopCase(
        name="syncbb_min",
        dcop_factory=lambda: build_syncbb_dcop("min"),
        optimal_assignment={"vA": "G", "vB": "G", "vC": "G", "vD": "G"},
        optimal_cost=12,
    ),
    KnownDcopCase(
        name="syncbb_max",
        dcop_factory=lambda: build_syncbb_dcop("max"),
        optimal_assignment={"vA": "G", "vB": "R", "vC": "R", "vD": "G"},
        optimal_cost=53,
    ),
    KnownDcopCase(
        name="dynamic_graphcoloring_r1",
        dcop_factory=lambda: build_dynamic_graphcoloring_dcop("r1"),
        optimal_assignment={"v1": "R", "v2": "G", "v3": "B", "v4": "R"},
        optimal_cost=0,
    ),
    KnownDcopCase(
        name="dynamic_graphcoloring_r1_2",
        dcop_factory=lambda: build_dynamic_graphcoloring_dcop("r1_2"),
        optimal_assignment={"v1": "B", "v2": "G", "v3": "B", "v4": "R"},
        optimal_cost=5,
    ),
)


KNOWN_INSTANCE_COSTS = (
    KnownDcopCase(
        name="yaml_graph_coloring_10_4_15",
        dcop_factory=lambda: load_test_dcop("graph_coloring_10_4_15_0.1.yml"),
        optimal_cost=0,
    ),
    KnownDcopCase(
        name="yaml_graph_coloring_csp",
        dcop_factory=lambda: load_test_dcop("graph_coloring_csp.yaml"),
        optimal_cost=0,
    ),
)


KNOWN_INSTANCES = KNOWN_INSTANCE_SOLUTIONS + KNOWN_INSTANCE_COSTS
