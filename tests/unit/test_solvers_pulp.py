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

from pydcop.solvers import pulp_solver
from pydcop.solvers.pulp_solver import PulpDcopSolverError, solve_dcop
from tests.utils.known_instances import KNOWN_INSTANCE_COSTS, KNOWN_INSTANCE_SOLUTIONS
from tests.utils.known_instances import load_test_dcop


@pytest.mark.parametrize(
    "known_case",
    KNOWN_INSTANCE_SOLUTIONS,
    ids=[known_case.name for known_case in KNOWN_INSTANCE_SOLUTIONS],
)
def test_pulp_solver_matches_known_solution(known_case):
    dcop = known_case.dcop_factory()

    result = solve_dcop(dcop)

    assert result.status == "FINISHED"
    assert result.assignment == known_case.optimal_assignment
    assert result.objective_value == pytest.approx(known_case.optimal_cost)


@pytest.mark.parametrize(
    "known_case",
    KNOWN_INSTANCE_COSTS,
    ids=[known_case.name for known_case in KNOWN_INSTANCE_COSTS],
)
def test_pulp_solver_matches_known_cost(known_case):
    dcop = known_case.dcop_factory()

    result = solve_dcop(dcop)

    assert result.status == "FINISHED"
    assert result.objective_value == pytest.approx(known_case.optimal_cost)


def test_pulp_solver_solves_random_graph_instance():
    dcop = load_test_dcop("random_graph_6_3_0.7.yaml")

    result = solve_dcop(dcop)

    assert result.status == "FINISHED"
    assert result.objective_value == pytest.approx(35)


def test_pulp_solver_uses_cbc_threads_by_default(monkeypatch):
    captured = {}

    class FakeCbcSolver:
        def __init__(self, msg, timeLimit, threads):
            captured["msg"] = msg
            captured["timeLimit"] = timeLimit
            captured["threads"] = threads

    monkeypatch.setattr(pulp_solver, "PULP_CBC_CMD", FakeCbcSolver)
    monkeypatch.setattr(pulp_solver.os, "cpu_count", lambda: 8)

    solver, solver_name, threads = pulp_solver._build_solver("cbc", timeout=12)

    assert isinstance(solver, FakeCbcSolver)
    assert solver_name == "cbc"
    assert threads == 8
    assert captured == {"msg": False, "timeLimit": 12, "threads": 8}


def test_pulp_solver_rejects_threads_for_glpk():
    with pytest.raises(PulpDcopSolverError, match="GLPK"):
        pulp_solver._build_solver("glpk", threads=2)
