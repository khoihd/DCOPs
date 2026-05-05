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


import sys

import pytest

from pydcop.dcop.objects import VariableDomain, VariableNoisyCostFunc
from pydcop.dcop.relations import (
    NAryFunctionRelation,
    filter_assignment_dict,
    find_dependent_relations,
    generate_assignment_as_dict,
)

"""
Graph coloring sample with dynamic Maxsum
4 variable that can take one of 3 colors

One relation (r1) is periodically changed (with dimension change).

In this sample we do not use read-only variables but we directly change the
function on the factor node.

These tests validate the dynamic scenario model and expected optima without
starting the legacy dynamic Max-Sum runner.

"""

COLORS = VariableDomain("colors", "color", ["R", "G", "B"])
CONSTRAINT_VIOLATION_COST = 100
NON_PREFERRED_COLOR_COST = 5


def prefer_color(preferred_color):
    """Generate a cost function for a variable that prefers one color."""

    def color_cost(color):
        if color == preferred_color:
            return 0
        return NON_PREFERRED_COLOR_COST

    return color_cost


def build_graph_coloring_problem():
    v1 = VariableNoisyCostFunc("v1", COLORS, prefer_color("R"), noise_level=0)
    v2 = VariableNoisyCostFunc("v2", COLORS, prefer_color("G"), noise_level=0)
    v3 = VariableNoisyCostFunc("v3", COLORS, prefer_color("B"), noise_level=0)
    v4 = VariableNoisyCostFunc("v4", COLORS, prefer_color("R"), noise_level=0)

    def r1(v1_, v2_, v3_):
        if v1_ != v2_ and v2_ != v3_ and v1_ != v3_:
            return 0
        return CONSTRAINT_VIOLATION_COST

    r1 = NAryFunctionRelation(r1, [v1, v2, v3], name="r1")

    def r1_2(v1_, v2_, v4_):
        if v1_ != v2_ and v2_ != v4_ and v1_ != v4_:
            return 0
        return CONSTRAINT_VIOLATION_COST

    r1_2 = NAryFunctionRelation(r1_2, [v1, v2, v4], name="r1_2")

    def r2(v2_, v4_):
        if v2_ != v4_:
            return 0
        return CONSTRAINT_VIOLATION_COST

    r2 = NAryFunctionRelation(r2, [v2, v4], name="r2")

    def r3(v3_, v4_):
        if v3_ != v4_:
            return 0
        return CONSTRAINT_VIOLATION_COST

    r3 = NAryFunctionRelation(r3, [v3, v4], name="r3")

    variables = [v1, v2, v3, v4]
    relation_states = {
        "r1": [r1, r2, r3],
        "r1_2": [r1_2, r2, r3],
    }
    expected_results = {
        "r1": {"v1": "R", "v2": "G", "v3": "B", "v4": "R"},
        "r1_2": {"v1": "B", "v2": "G", "v3": "B", "v4": "R"},
    }
    return variables, relation_states, expected_results


def assignment_cost(variables, relations, assignment):
    variable_cost = sum(
        variable.cost_for_val(assignment[variable.name])
        for variable in variables
    )
    relation_cost = sum(
        relation(filter_assignment_dict(assignment, relation.dimensions))
        for relation in relations
    )
    return variable_cost + relation_cost


def optimal_assignments(variables, relations):
    assignments = list(generate_assignment_as_dict(variables))
    costs = [
        (assignment_cost(variables, relations, assignment), assignment)
        for assignment in assignments
    ]
    best_cost = min(cost for cost, _ in costs)
    return best_cost, [
        assignment for cost, assignment in costs if cost == best_cost
    ]


def dmaxsum_graphcoloring():
    variables, relation_states, expected_results = build_graph_coloring_problem()

    for relation_name, relations in relation_states.items():
        _, best_assignments = optimal_assignments(variables, relations)
        if best_assignments != [expected_results[relation_name]]:
            return 1
    return 0


def test_prefer_color_cost_function():
    red_cost = prefer_color("R")

    assert red_cost("R") == 0
    assert red_cost("G") == NON_PREFERRED_COLOR_COST
    assert red_cost("B") == NON_PREFERRED_COLOR_COST


def test_dynamic_relation_states_have_expected_scopes():
    _, relation_states, _ = build_graph_coloring_problem()

    scopes = {
        state: {
            relation.name: [variable.name for variable in relation.dimensions]
            for relation in relations
        }
        for state, relations in relation_states.items()
    }

    assert scopes == {
        "r1": {
            "r1": ["v1", "v2", "v3"],
            "r2": ["v2", "v4"],
            "r3": ["v3", "v4"],
        },
        "r1_2": {
            "r1_2": ["v1", "v2", "v4"],
            "r2": ["v2", "v4"],
            "r3": ["v3", "v4"],
        },
    }


@pytest.mark.parametrize(
    ("relation_name", "expected_cost"),
    [
        ("r1", 0),
        ("r1_2", NON_PREFERRED_COLOR_COST),
    ],
)
def test_expected_results_are_unique_optima(relation_name, expected_cost):
    variables, relation_states, expected_results = build_graph_coloring_problem()
    relations = relation_states[relation_name]
    expected = expected_results[relation_name]

    best_cost, best_assignments = optimal_assignments(variables, relations)

    assert best_cost == expected_cost
    assert best_assignments == [expected]


@pytest.mark.parametrize("relation_name", ["r1", "r1_2"])
def test_expected_results_satisfy_all_active_constraints(relation_name):
    _, relation_states, expected_results = build_graph_coloring_problem()
    expected = expected_results[relation_name]

    for relation in relation_states[relation_name]:
        relation_assignment = filter_assignment_dict(
            expected, relation.dimensions
        )
        assert relation(relation_assignment) == 0


def test_variable_dependencies_follow_dynamic_relation_scope():
    variables, relation_states, _ = build_graph_coloring_problem()

    dependencies = {
        relation_name: {
            variable.name: [
                relation.name
                for relation in find_dependent_relations(variable, relations)
            ]
            for variable in variables
        }
        for relation_name, relations in relation_states.items()
    }

    assert dependencies == {
        "r1": {
            "v1": ["r1"],
            "v2": ["r1", "r2"],
            "v3": ["r1", "r3"],
            "v4": ["r2", "r3"],
        },
        "r1_2": {
            "v1": ["r1_2"],
            "v2": ["r1_2", "r2"],
            "v3": ["r3"],
            "v4": ["r1_2", "r2", "r3"],
        },
    }


def test_dynamic_switch_sequence_matches_expected_results():
    variables, relation_states, expected_results = build_graph_coloring_problem()
    relation_sequence = ["r1", "r1_2", "r1", "r1_2", "r1"]

    observed = []
    for relation_name in relation_sequence:
        _, best_assignments = optimal_assignments(
            variables, relation_states[relation_name]
        )
        observed.append(best_assignments[0])

    assert observed == [
        expected_results[relation_name] for relation_name in relation_sequence
    ]


def run_test():
    return dmaxsum_graphcoloring()


if __name__ == "__main__":
    res = dmaxsum_graphcoloring()

    sys.exit(res)
