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
from pathlib import Path
from pulp import GLPK_CMD, LpBinary, LpMaximize, LpMinimize, LpProblem, LpStatus
from pulp import LpStatusOptimal, LpVariable, lpSum, value

from pydcop.dcop.dcop import DCOP
from pydcop.dcop.relations import generate_assignment_as_dict
from pydcop.dcop.yamldcop import load_dcop_from_file
from tests.api.instances_and_utils import dcop_graphcoloring_3
from tests.integration.dmaxsum_graphcoloring import build_graph_coloring_problem
from tests.unit.test_algorithms_syncbb import build_pb


INSTANCE_DIR = Path(__file__).resolve().parents[1] / "instances"


def solve_dcop_with_pulp(dcop):
    sense = LpMinimize if dcop.objective == "min" else LpMaximize
    problem_name = f"{dcop.name}_oracle".replace(" ", "_")
    problem = LpProblem(problem_name, sense=sense)

    variable_choices = {}
    for variable in dcop.variables.values():
        choices = []
        for value_index, variable_value in enumerate(variable.domain):
            choice = LpVariable(
                f"assign_{variable.name}_{value_index}",
                cat=LpBinary,
            )
            variable_choices[(variable.name, variable_value)] = choice
            choices.append(choice)
        problem += lpSum(choices) == 1

    relation_choices = {}
    objective_terms = []
    for relation in dcop.constraints.values():
        tuples = list(generate_assignment_as_dict(relation.dimensions))
        tuple_choices = []

        for tuple_index, assignment in enumerate(tuples):
            choice = LpVariable(
                f"tuple_{relation.name}_{tuple_index}",
                cat=LpBinary,
            )
            relation_choices[(relation.name, tuple_index)] = (choice, assignment)
            tuple_choices.append(choice)
            objective_terms.append(relation(**assignment) * choice)

        problem += lpSum(tuple_choices) == 1

        for variable in relation.dimensions:
            for variable_value in variable.domain:
                matching_tuples = [
                    relation_choices[(relation.name, tuple_index)][0]
                    for tuple_index, assignment in enumerate(tuples)
                    if assignment[variable.name] == variable_value
                ]
                problem += (
                    lpSum(matching_tuples)
                    == variable_choices[(variable.name, variable_value)]
                )

    for variable in dcop.variables.values():
        for variable_value in variable.domain:
            objective_terms.append(
                variable.cost_for_val(variable_value)
                * variable_choices[(variable.name, variable_value)]
            )

    problem += lpSum(objective_terms)

    status = problem.solve(GLPK_CMD(msg=False))
    assert status == LpStatusOptimal, LpStatus[status]

    assignment = {}
    for variable in dcop.variables.values():
        selected_values = [
            variable_value
            for variable_value in variable.domain
            if value(variable_choices[(variable.name, variable_value)]) == 1
        ]
        assert len(selected_values) == 1
        assignment[variable.name] = selected_values[0]

    return assignment, value(problem.objective)


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


class TestPulpDcopOracle:
    def test_graphcoloring_3_matches_known_solution(self):
        dcop = dcop_graphcoloring_3()

        assignment, cost = solve_dcop_with_pulp(dcop)

        assert assignment == {"v1": "R", "v2": "G", "v3": "R"}
        assert cost == pytest.approx(-0.1)

    @pytest.mark.parametrize(
        ("filename", "expected_assignment", "expected_cost"),
        [
            (
                "graph_coloring1.yaml",
                {"v1": "R", "v2": "G", "v3": "R"},
                -0.1,
            ),
            (
                "secp_simple1.yaml",
                {"l1": 0, "l2": 3, "l3": 4, "m1": 3},
                2.3,
            ),
        ],
    )
    def test_yaml_instance_matches_known_solution(
        self, filename, expected_assignment, expected_cost
    ):
        dcop = load_test_dcop(filename)

        assignment, cost = solve_dcop_with_pulp(dcop)

        assert assignment == expected_assignment
        assert cost == pytest.approx(expected_cost)

    @pytest.mark.parametrize(
        "filename",
        [
            "graph_coloring_10_4_15_0.1.yml",
            "graph_coloring_csp.yaml",
        ],
    )
    def test_yaml_instance_matches_known_cost(self, filename):
        dcop = load_test_dcop(filename)

        _, cost = solve_dcop_with_pulp(dcop)

        assert cost == pytest.approx(0)

    @pytest.mark.parametrize(
        ("objective", "expected_assignment", "expected_cost"),
        [
            ("min", {"vA": "G", "vB": "G", "vC": "G", "vD": "G"}, 12),
            ("max", {"vA": "G", "vB": "R", "vC": "R", "vD": "G"}, 53),
        ],
    )
    def test_syncbb_toy_problem_matches_known_solution(
        self, objective, expected_assignment, expected_cost
    ):
        dcop = build_syncbb_dcop(objective)

        assignment, cost = solve_dcop_with_pulp(dcop)

        assert assignment == expected_assignment
        assert cost == pytest.approx(expected_cost)

    @pytest.mark.parametrize(
        ("relation_name", "expected_assignment", "expected_cost"),
        [
            (
                "r1",
                {"v1": "R", "v2": "G", "v3": "B", "v4": "R"},
                0,
            ),
            (
                "r1_2",
                {"v1": "B", "v2": "G", "v3": "B", "v4": "R"},
                5,
            ),
        ],
    )
    def test_dynamic_graphcoloring_state_matches_known_solution(
        self, relation_name, expected_assignment, expected_cost
    ):
        dcop = build_dynamic_graphcoloring_dcop(relation_name)

        assignment, cost = solve_dcop_with_pulp(dcop)

        assert assignment == expected_assignment
        assert cost == pytest.approx(expected_cost)
