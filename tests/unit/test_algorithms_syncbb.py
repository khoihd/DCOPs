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
Unit tests for the SyncBB algorithm.

"""
from unittest.mock import MagicMock

import pytest

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms import syncbb
from pydcop.algorithms.syncbb import (
    get_value_candidates,
    get_next_assignment,
    constraints_for_variable,
    SyncBBComputation,
    SyncBBForwardMessage,
    SyncBBBackwardMessage,
    SyncBBTerminateMessage,
)
from pydcop.computations_graph.ordered_graph import build_computation_graph
from pydcop.dcop.dcop import DCOP
from pydcop.dcop.objects import Domain, Variable, create_agents
from pydcop.dcop.relations import constraint_from_str
from pydcop.infrastructure.run import solve


def build_pb():
    # A toy problem with 5 variables and 5 constraints.
    # The objective here is to have a problem that is simple enough to be solved
    # manually and used in test, but that is representative enough to be meaningful.

    v_a = Variable("vA", ["R", "G"])
    v_b = Variable("vB", ["R", "G"])
    v_c = Variable("vC", ["R", "G"])
    v_d = Variable("vD", ["R", "G"])
    c1 = constraint_from_str(
        "c1",
        "{('R', 'G'): 8, "
        " ('R', 'R'): 5, "
        " ('G', 'G'): 3, "
        " ('G', 'R'): 20 "
        "}[(vA, vB)]",
        [v_a, v_b],
    )
    c2 = constraint_from_str(
        "c2",
        "{('R', 'G'): 10, "
        " ('R', 'R'): 5, "
        " ('G', 'G'): 3, "
        " ('G', 'R'): 20 "
        "}[(vA, vC)]",
        [v_a, v_c],
    )
    c3 = constraint_from_str(
        "c3",
        "{('R', 'G'): 4, "
        " ('R', 'R'): 5, "
        " ('G', 'G'): 3, "
        " ('G', 'R'): 3 "
        "}[(vB, vC)]",
        [v_b, v_c],
    )
    c4 = constraint_from_str(
        "c4",
        "{('R', 'G'): 8, "
        " ('R', 'R'): 3, "
        " ('G', 'G'): 3, "
        " ('G', 'R'): 10 "
        "}[(vB, vD)]",
        [v_b, v_d],
    )
    return [v_a, v_b, v_c, v_d], [c1, c2, c3, c4]


@pytest.fixture
def toy_pb():
    return build_pb()


@pytest.fixture
def toy_pb_computation_graph():
    variables, constraints = build_pb()

    # build the pseudo-tree for this problem
    g = build_computation_graph(None, constraints=constraints, variables=variables)
    return g


def get_computation_instance(graph, name, mode="min"):
    # Get the computation node for x1
    comp_node = graph.computation(name)

    # Create the ComputationDef and computation instance
    algo_def = AlgorithmDef.build_with_default_param("syncbb", mode=mode)
    comp_def = ComputationDef(comp_node, algo_def)
    comp = SyncBBComputation(comp_def)
    comp._msg_sender = MagicMock()

    return comp


def test_build_computation_returns_syncbb_instance(toy_pb_computation_graph):
    comp_node = toy_pb_computation_graph.computation("vA")
    algo_def = AlgorithmDef.build_with_default_param("syncbb")
    comp_def = ComputationDef(comp_node, algo_def)

    comp = syncbb.build_computation(comp_def)

    assert isinstance(comp, SyncBBComputation)
    assert comp.name == "vA"


def test_terminate_message_has_no_payload():
    message = SyncBBTerminateMessage()

    assert message.type == "terminate"
    assert message.size == 0
    assert str(message) == "terminate()"
    assert repr(message) == "terminate()"
    assert message == SyncBBTerminateMessage()


def test_get_candidates_no_value_selected():
    d = Domain("d", "vals", [0, 1, 2, 3])
    v = Variable("v", d)

    obtained = get_value_candidates(v, None)
    assert obtained == [0, 1, 2, 3]


def test_get_candidate_value_selected():
    d = Domain("d", "vals", ["vB", "vD", "vA", "vE"])
    v = Variable("v", d)

    obtained = get_value_candidates(v, "vB")
    assert obtained == ["vD", "vA", "vE"]

    obtained = get_value_candidates(v, "vA")
    assert obtained == ["vE"]

    obtained = get_value_candidates(v, "vE")
    assert obtained == []


def test_get_next_assignement_empty_path_no_bound(toy_pb):
    variables, constraints = toy_pb
    variable = variables[0]
    var_constraints = [c for c in constraints if variable in c.dimensions]
    bound = float("inf")

    obtained = get_next_assignment(variable, None, var_constraints, [], bound, "min")
    assert obtained == ("R", 0)


def test_constraints_for_variable_uses_exact_variable_names():
    v1 = Variable("v1", [0, 1])
    v10 = Variable("v10", [0, 1])
    c1 = constraint_from_str("c1", "0 if v1 == v10 else 1", [v1, v10])

    assert constraints_for_variable([c1], "v1") == [c1]
    assert constraints_for_variable([c1], "v10") == [c1]
    assert constraints_for_variable([c1], "v") == []


def test_get_next_assignment_no_bound(toy_pb):
    variables, constraints = toy_pb
    v_a, v_b, v_c, v_d = variables
    bound = float("inf")

    constraints_b = [c for c in constraints if v_b in c.dimensions]
    obtained = get_next_assignment(
        v_b, None, constraints_b, [("vA", "R", 0)], bound, "min"
    )
    assert obtained == ("R", 5)

    constraints_c = [c for c in constraints if v_c in c.dimensions]
    obtained = get_next_assignment(
        v_c, None, constraints_c, [("vA", "R", 0), ("vB", "R", 5)], bound, "min"
    )
    assert obtained == ("R", 10)

    constraints_d = [c for c in constraints if v_d in c.dimensions]
    obtained = get_next_assignment(
        v_d,
        None,
        constraints_d,
        [("vA", "R", 0), ("vB", "R", 5), ("vC", "R", 10)],
        bound,
        "min",
    )
    assert obtained == ("R", 3)


def test_get_next_assignment_respects_min_bound(toy_pb):
    variables, constraints = toy_pb
    _, v_b, _, _ = variables
    constraints_b = [c for c in constraints if v_b in c.dimensions]

    obtained = get_next_assignment(
        v_b, None, constraints_b, [("vA", "R", 0)], 5, "min"
    )
    assert obtained is None


def test_get_next_assignment_skips_current_value(toy_pb):
    variables, constraints = toy_pb
    _, v_b, _, _ = variables
    constraints_b = [c for c in constraints if v_b in c.dimensions]

    obtained = get_next_assignment(
        v_b, "R", constraints_b, [("vA", "R", 0)], float("inf"), "min"
    )
    assert obtained == ("G", 8)


def test_get_next_assignment_rejects_candidate_pruned_after_partial_path():
    v0 = Variable("v0", [0, 1, 2])
    v1 = Variable("v1", [0, 1, 2])
    v2 = Variable("v2", [0, 1, 2])
    c0_2 = constraint_from_str(
        "c0_2",
        "{(0, 0): 5, (0, 1): 9, (0, 2): 3, "
        "(1, 0): 8, (1, 1): 2, (1, 2): 4, "
        "(2, 0): 2, (2, 1): 1, (2, 2): 9}[(v0, v2)]",
        [v0, v2],
    )
    c1_2 = constraint_from_str(
        "c1_2",
        "{(0, 0): 4, (0, 1): 8, (0, 2): 9, "
        "(1, 0): 2, (1, 1): 4, (1, 2): 1, "
        "(2, 0): 1, (2, 1): 5, (2, 2): 7}[(v1, v2)]",
        [v1, v2],
    )

    obtained = get_next_assignment(
        v2,
        0,
        [c0_2, c1_2],
        [("v0", 0, 0), ("v1", 2, 0)],
        10,
        "min",
    )

    assert obtained is None


def test_computations_message_at_start(toy_pb_computation_graph):
    # A is the first var in the ordering, it should start selecting a value:
    comp_a = get_computation_instance(toy_pb_computation_graph, "vA")
    assert comp_a.previous_var is None
    assert comp_a.next_var == "vB"
    comp_a.start()
    comp_a._msg_sender.assert_any_call(
        "vA", "vB", SyncBBForwardMessage([("vA", "R", 0)], float("inf")), None, None
    )

    # C is not a start, should not send any message:
    comp_c = get_computation_instance(toy_pb_computation_graph, "vC")
    assert comp_c.previous_var == "vB"
    assert comp_c.next_var == "vD"
    comp_c.start()
    comp_c.message_sender.assert_not_called()


def test_computation_start_uses_max_initial_bound(toy_pb_computation_graph):
    comp_a = get_computation_instance(toy_pb_computation_graph, "vA", mode="max")

    comp_a.start()

    comp_a._msg_sender.assert_any_call(
        "vA", "vB", SyncBBForwardMessage([("vA", "R", 0)], -float("inf")), None, None
    )


def test_forward_message_extends_path(toy_pb_computation_graph):
    comp_b = get_computation_instance(toy_pb_computation_graph, "vB")

    comp_b.on_forward_message(
        "vA", SyncBBForwardMessage([("vA", "R", 0)], float("inf")), 0
    )

    comp_b._msg_sender.assert_called_once_with(
        "vB",
        "vC",
        SyncBBForwardMessage([("vA", "R", 0), ("vB", "R", 5)], float("inf")),
        None,
        None,
    )
    assert comp_b.cycle_count == 1


def test_forward_message_backtracks_when_no_value_with_bound(
    toy_pb_computation_graph,
):
    comp_b = get_computation_instance(toy_pb_computation_graph, "vB")
    comp_b.upper_bound = 5

    comp_b.on_forward_message(
        "vA", SyncBBForwardMessage([("vA", "R", 0)], 5), 0
    )

    comp_b._msg_sender.assert_called_once_with(
        "vB",
        "vA",
        SyncBBBackwardMessage([("vA", "R", 0)], 5),
        None,
        None,
    )
    assert comp_b.cycle_count == 1


def test_last_variable_updates_bound_and_backtracks(toy_pb_computation_graph):
    comp_d = get_computation_instance(toy_pb_computation_graph, "vD")
    path = [("vA", "R", 0), ("vB", "R", 5), ("vC", "R", 10)]

    comp_d.on_forward_message("vC", SyncBBForwardMessage(path, float("inf")), 0)

    assert comp_d.upper_bound == 18
    assert comp_d.current_value == "R"
    assert comp_d.current_cost == 18
    comp_d._msg_sender.assert_called_once_with(
        "vD", "vC", SyncBBBackwardMessage(path, 18), None, None
    )
    assert comp_d.cycle_count == 1


def test_backward_message_updates_bound_and_tries_next_value(
    toy_pb_computation_graph,
):
    comp_b = get_computation_instance(toy_pb_computation_graph, "vB")

    comp_b.on_backward_msg(
        "vC", SyncBBBackwardMessage([("vA", "R", 0), ("vB", "R", 5)], 12), 0
    )

    assert comp_b.upper_bound == 12
    assert comp_b.current_value == "R"
    assert comp_b.current_cost == 12
    comp_b._msg_sender.assert_called_once_with(
        "vB",
        "vC",
        SyncBBForwardMessage([("vA", "R", 0), ("vB", "G", 8)], 12),
        None,
        None,
    )
    assert comp_b.cycle_count == 1


def test_backward_message_backtracks_when_domain_is_exhausted(
    toy_pb_computation_graph,
):
    comp_b = get_computation_instance(toy_pb_computation_graph, "vB")

    comp_b.on_backward_msg(
        "vC", SyncBBBackwardMessage([("vA", "R", 0), ("vB", "G", 8)], 12), 0
    )

    comp_b._msg_sender.assert_called_once_with(
        "vB", "vA", SyncBBBackwardMessage([("vA", "R", 0)], 12), None, None
    )
    assert comp_b.cycle_count == 1


def test_first_variable_terminates_when_backtracking_exhausts_domain(
    toy_pb_computation_graph,
):
    comp_a = get_computation_instance(toy_pb_computation_graph, "vA")
    comp_a.finished = MagicMock()

    comp_a.on_backward_msg("vB", SyncBBBackwardMessage([("vA", "G", 0)], 12), 0)

    comp_a.finished.assert_called_once_with()
    comp_a._msg_sender.assert_called_once_with(
        "vA", "vB", SyncBBTerminateMessage(), None, None
    )
    assert comp_a.cycle_count == 1


def test_terminate_message_is_forwarded_and_finishes(toy_pb_computation_graph):
    comp_b = get_computation_instance(toy_pb_computation_graph, "vB")
    comp_b.finished = MagicMock()

    comp_b.on_terminate_message("vA", SyncBBTerminateMessage(), 0)

    comp_b.finished.assert_called_once_with()
    comp_b._msg_sender.assert_called_once_with(
        "vB", "vC", SyncBBTerminateMessage(), None, None
    )
    assert comp_b.cycle_count == 1


def test_solve_min(toy_pb):
    variables, constraints = toy_pb

    dcop = DCOP(
        name="toy",
        variables={v.name: v for v in variables},
        constraints={c.name: c for c in constraints},
        objective="min"
    )
    dcop.add_agents(create_agents("a", [1, 2, 3, 4]))

    assignment = solve(dcop, "syncbb", "oneagent")

    # Note: this is exactly the same pb as in the file bellow
    # dcop = load_dcop_from_file(["/pyDcop/tests/instances/graph_coloring_tuto.yaml"])

    assert assignment == {"vA": "G", "vB": "G", "vC": "G", "vD": "G"}


def test_solve_max(toy_pb):
    variables, constraints = toy_pb

    dcop = DCOP(
        name="toy",
        variables={v.name: v for v in variables},
        constraints={c.name: c for c in constraints},
        objective="max"
    )
    dcop.add_agents(create_agents("a", [1, 2, 3, 4]))

    assignment = solve(dcop, "syncbb", "oneagent")

    # Note: this is supposed to be exactly the same pb as bellow
    assert assignment == {"vA": "G", "vB": "R", "vC": "R", "vD": "G"}


def test_solve_max_does_not_prune_low_partial_utility():
    v0 = Variable("v0", [0, 1])
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    c0_1 = constraint_from_str(
        "c0_1",
        "{(0, 0): 10, (0, 1): 0, "
        "(1, 0): 0, (1, 1): 0}[(v0, v1)]",
        [v0, v1],
    )
    c0_2 = constraint_from_str(
        "c0_2",
        "{(0, 0): 0, (0, 1): 0, "
        "(1, 0): 100, (1, 1): 0}[(v0, v2)]",
        [v0, v2],
    )
    variables = [v0, v1, v2]
    constraints = [c0_1, c0_2]
    dcop = DCOP(
        name="max_regression",
        variables={v.name: v for v in variables},
        constraints={c.name: c for c in constraints},
        objective="max"
    )
    dcop.add_agents(create_agents("a", [1, 2, 3]))

    assignment = solve(dcop, "syncbb", "oneagent")
    cost = sum(
        c(**{v.name: assignment[v.name] for v in c.dimensions})
        for c in constraints
    )

    assert assignment["v0"] == 1
    assert assignment["v2"] == 0
    assert cost == 100


def test_solve_min_with_candidate_pruned_after_partial_path():
    variables = [Variable(f"v{i}", [0, 1, 2]) for i in range(3)]
    v0, v1, v2 = variables
    c0_1 = constraint_from_str(
        "c0_1",
        "{(0, 0): 6, (0, 1): 6, (0, 2): 0, "
        "(1, 0): 4, (1, 1): 8, (1, 2): 7, "
        "(2, 0): 6, (2, 1): 4, (2, 2): 7}[(v0, v1)]",
        [v0, v1],
    )
    c0_2 = constraint_from_str(
        "c0_2",
        "{(0, 0): 5, (0, 1): 9, (0, 2): 3, "
        "(1, 0): 8, (1, 1): 2, (1, 2): 4, "
        "(2, 0): 2, (2, 1): 1, (2, 2): 9}[(v0, v2)]",
        [v0, v2],
    )
    c1_2 = constraint_from_str(
        "c1_2",
        "{(0, 0): 4, (0, 1): 8, (0, 2): 9, "
        "(1, 0): 2, (1, 1): 4, (1, 2): 1, "
        "(2, 0): 1, (2, 1): 5, (2, 2): 7}[(v1, v2)]",
        [v1, v2],
    )
    constraints = [c0_1, c0_2, c1_2]
    dcop = DCOP(
        name="regression",
        variables={v.name: v for v in variables},
        constraints={c.name: c for c in constraints},
        objective="min"
    )
    dcop.add_agents(create_agents("a", [1, 2, 3]))

    assignment = solve(dcop, "syncbb", "oneagent")

    assert assignment == {"v0": 0, "v1": 2, "v2": 0}
