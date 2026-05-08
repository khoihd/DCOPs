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
import math
from typing import Any, Dict, Mapping

from pulp import GLPK_CMD, LpBinary, LpMaximize, LpMinimize, LpProblem, LpStatus
from pulp import LpStatusOptimal, LpVariable, lpSum, value
from pulp import PulpSolverError as PulpBackendError

from pydcop.dcop.dcop import DCOP
from pydcop.dcop.relations import generate_assignment_as_dict


@dataclass(frozen=True)
class PulpDcopResult:
    status: str
    assignment: Dict[str, Any]
    objective_value: float | None
    solver_status: str


class PulpDcopSolverError(Exception):
    pass


def solve_dcop(dcop: DCOP, infinity=float("inf"), timeout=None) -> PulpDcopResult:
    sense = LpMinimize if dcop.objective == "min" else LpMaximize
    problem_name = "{}_pulp".format(dcop.name or "dcop").replace(" ", "_")
    problem = LpProblem(problem_name, sense=sense)

    variable_choices = {}
    domain_values = {}
    for variable_index, variable in enumerate(dcop.variables.values()):
        choices = []
        values = tuple(variable.domain)
        domain_values[variable.name] = values
        for value_index, variable_value in enumerate(values):
            choice = LpVariable(
                f"assign_{variable_index}_{value_index}",
                cat=LpBinary,
            )
            variable_choices[(variable.name, value_index)] = choice
            choices.append(choice)
        problem += lpSum(choices) == 1

    objective_terms = []
    external_values = {
        name: variable.value for name, variable in dcop.external_variables.items()
    }

    for relation_index, relation in enumerate(dcop.constraints.values()):
        tuples = [
            assignment
            for assignment in generate_assignment_as_dict(relation.dimensions)
            if _compatible_external_assignment(assignment, external_values)
        ]

        tuple_choices = []
        relation_choices = {}
        for tuple_index, assignment in enumerate(tuples):
            relation_value = relation(**assignment)
            if _is_forbidden_cost(relation_value, infinity):
                continue

            choice = LpVariable(
                f"tuple_{relation_index}_{tuple_index}",
                cat=LpBinary,
            )
            relation_choices[tuple_index] = (choice, assignment)
            tuple_choices.append(choice)
            objective_terms.append(relation_value * choice)

        if not tuple_choices:
            return PulpDcopResult("INFEASIBLE", {}, None, "Infeasible")

        problem += lpSum(tuple_choices) == 1

        for variable in relation.dimensions:
            if variable.name not in dcop.variables:
                continue
            for value_index, variable_value in enumerate(domain_values[variable.name]):
                matching_tuples = [
                    choice
                    for choice, assignment in relation_choices.values()
                    if assignment[variable.name] == variable_value
                ]
                problem += (
                    lpSum(matching_tuples)
                    == variable_choices[(variable.name, value_index)]
                )

    for variable in dcop.variables.values():
        for value_index, variable_value in enumerate(domain_values[variable.name]):
            variable_cost = variable.cost_for_val(variable_value)
            if _is_forbidden_cost(variable_cost, infinity):
                problem += variable_choices[(variable.name, value_index)] == 0
            else:
                objective_terms.append(
                    variable_cost * variable_choices[(variable.name, value_index)]
                )

    problem += lpSum(objective_terms)

    solver = GLPK_CMD(msg=False, timeLimit=timeout)
    try:
        status = problem.solve(solver)
    except PulpBackendError as e:
        raise PulpDcopSolverError(str(e)) from e
    solver_status = LpStatus[status]
    if status != LpStatusOptimal:
        return PulpDcopResult(
            _status_from_pulp_status(solver_status), {}, None, solver_status
        )

    assignment = _extract_assignment(dcop, domain_values, variable_choices)
    objective_value = value(problem.objective)
    if objective_value is None:
        objective_value = 0

    return PulpDcopResult("FINISHED", assignment, objective_value, solver_status)


def _compatible_external_assignment(
    assignment: Mapping[str, Any], external_values: Mapping[str, Any]
) -> bool:
    for variable_name, variable_value in external_values.items():
        if variable_name in assignment and assignment[variable_name] != variable_value:
            return False
    return True


def _is_forbidden_cost(cost, infinity) -> bool:
    try:
        numeric_cost = float(cost)
    except (TypeError, ValueError):
        return cost == infinity

    if not math.isfinite(numeric_cost):
        return True

    if numeric_cost == infinity:
        return True

    if math.isfinite(infinity) and numeric_cost == -infinity:
        return True

    return False


def _status_from_pulp_status(solver_status: str) -> str:
    if solver_status == "Infeasible":
        return "INFEASIBLE"
    if solver_status == "Unbounded":
        return "UNBOUNDED"
    if solver_status == "Not Solved":
        return "TIMEOUT"
    return "ERROR"


def _extract_assignment(dcop, domain_values, variable_choices):
    assignment = {}
    for variable in dcop.variables.values():
        selected_values = [
            variable_value
            for value_index, variable_value in enumerate(domain_values[variable.name])
            if value(variable_choices[(variable.name, value_index)]) > 0.5
        ]
        if len(selected_values) != 1:
            raise PulpDcopSolverError(
                f"Could not extract one selected value for variable {variable.name}"
            )
        assignment[variable.name] = selected_values[0]
    return assignment
