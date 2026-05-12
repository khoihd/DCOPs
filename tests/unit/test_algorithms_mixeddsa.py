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

import numpy as np
from unittest.mock import MagicMock, call, patch

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms import mixeddsa
from pydcop.algorithms.mixeddsa import MixedDsaComputation, MixedDsaMessage
from pydcop.computations_graph.constraints_hypergraph import VariableComputationNode
from pydcop.dcop.objects import Variable, VariableWithCostDict
from pydcop.dcop.relations import AsNAryFunctionRelation, NAryMatrixRelation


def _comp_def(variable, constraints, mode="min", params=None):
    node = VariableComputationNode(variable, constraints)
    algo = AlgorithmDef.build_with_default_param(
        "mixeddsa", mode=mode, params=params
    )
    return ComputationDef(node, algo)


def test_build_computation_default_params():
    variable = Variable("v1", [0, 1, 2])
    comp_def = _comp_def(variable, [])

    computation = mixeddsa.build_computation(comp_def)

    assert isinstance(computation, MixedDsaComputation)
    assert computation.mode == "min"
    assert computation.variant == "B"
    assert computation.proba_hard == 0.7
    assert computation.proba_soft == 0.5
    assert computation.stop_cycle == 0


def test_computation_init_classifies_hard_and_soft_constraints():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return abs(v1_ - v2_)

    @AsNAryFunctionRelation(v1, v2)
    def hard(v1_, v2_):
        return mixeddsa.INFINITY if v1_ == v2_ else 0

    computation = MixedDsaComputation(
        v1,
        [soft, hard],
        variant="C",
        proba_hard=0.2,
        proba_soft=0.3,
        stop_cycle=4,
        comp_def=_comp_def(v1, [soft, hard]),
    )

    assert computation.name == "v1"
    assert computation.neighbors == ["v2"]
    assert computation.variant == "C"
    assert computation.proba_hard == 0.2
    assert computation.proba_soft == 0.3
    assert computation.stop_cycle == 4
    assert computation.soft_constraints == [soft]
    assert computation.hard_constraints == [hard]
    assert computation._neighbors_values == {}


def test_communication_load_uses_constant_message_size():
    variable = Variable("v1", [0, 1])
    node = VariableComputationNode(variable, [])

    assert mixeddsa.communication_load(node, "v2") == (
        mixeddsa.UNIT_SIZE + mixeddsa.HEADER_SIZE
    )


def test_mixed_dsa_message_properties():
    message = MixedDsaMessage(3)

    assert message.type == "mixed_dsa_value"
    assert message.value == 3
    assert message.size == 1
    assert str(message) == "MixedDsaMessage(3)"
    assert repr(message) == "MixedDsaMessage(3)"
    assert message == MixedDsaMessage(3)
    assert message != MixedDsaMessage(4)
    assert message != object()


def test_memory_footprint_estimate_uses_exact_variable_names():
    v1 = Variable("v1", [0, 1])
    v10 = Variable("v10", [0, 1])

    @AsNAryFunctionRelation(v1, v10)
    def c1(v1_, v10_):
        return 0 if v1_ == v10_ else 1

    v10_node = VariableComputationNode(v10, [c1])

    assert set(v10_node.neighbors) == {"v1"}
    assert mixeddsa.memory_footprint_estimate(v10_node) == mixeddsa.UNIT_SIZE


def test_compute_dcop_cost_keeps_hard_violations_out_of_cost():
    v1 = VariableWithCostDict("v1", [0, 1], {0: 2, 1: 3})
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return abs(v1_ - v2_)

    @AsNAryFunctionRelation(v1, v2)
    def hard(v1_, v2_):
        return mixeddsa.INFINITY if v1_ == v2_ else 0

    computation = MixedDsaComputation(
        v1, [soft, hard], comp_def=_comp_def(v1, [soft, hard])
    )

    cost, violated = computation._compute_dcop_cost({"v1": 0, "v2": 0})
    assert cost == 2
    assert violated == [hard]

    cost, violated = computation._compute_dcop_cost({"v1": 1, "v2": 0})
    assert cost == 4
    assert violated == []


def test_compute_dcop_cost_detects_negative_infinity_hard_violation_in_max_mode():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return v1_ + v2_

    @AsNAryFunctionRelation(v1, v2)
    def hard(v1_, v2_):
        return -mixeddsa.INFINITY if v1_ == v2_ else 0

    computation = MixedDsaComputation(
        v1,
        [soft, hard],
        mode="max",
        comp_def=_comp_def(v1, [soft, hard], mode="max"),
    )

    cost, violated = computation._compute_dcop_cost({"v1": 1, "v2": 1})
    assert cost == 2
    assert violated == [hard]
    assert computation._eff_cost(cost, len(violated)) == -mixeddsa.INFINITY

    cost, violated = computation._compute_dcop_cost({"v1": 1, "v2": 0})
    assert cost == 1
    assert violated == []


def test_exists_violated_soft_constraint_supports_matrix_relation():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    soft = NAryMatrixRelation(
        [v1, v2], np.array([[0, 3], [2, 0]]), name="soft_matrix"
    )
    computation = MixedDsaComputation(v1, [soft], comp_def=_comp_def(v1, [soft]))

    assert computation.exists_violated_soft_constraint({"v1": 1, "v2": 0})
    assert not computation.exists_violated_soft_constraint({"v1": 1, "v2": 1})


def test_compute_best_value_uses_isolated_variable_cost():
    variable = VariableWithCostDict("v1", [0, 1, 2], {0: 5, 1: 0, 2: 4})
    computation = MixedDsaComputation(
        variable, [], comp_def=_comp_def(variable, [])
    )

    nb_violated, cost, values = computation._compute_best_value()

    assert nb_violated == 0
    assert cost == 0
    assert values == [1]


def test_on_start_without_neighbors_selects_best_value_and_stops():
    variable = VariableWithCostDict("v1", [0, 1, 2], {0: 5, 1: 0, 2: 4})
    computation = MixedDsaComputation(
        variable, [], comp_def=_comp_def(variable, [])
    )
    computation.finished = MagicMock()
    computation.stop = MagicMock()

    computation.on_start()

    assert computation.current_value == 1
    assert computation.current_cost == 0
    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()


def test_compute_best_value_prefers_fewer_hard_violations_before_soft_cost():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return 0 if v1_ == 0 else 10

    @AsNAryFunctionRelation(v1, v2)
    def hard(v1_, v2_):
        return mixeddsa.INFINITY if v1_ == v2_ else 0

    computation = MixedDsaComputation(
        v1, [soft, hard], comp_def=_comp_def(v1, [soft, hard])
    )
    computation._neighbors_values = {"v2": 0}

    nb_violated, cost, values = computation._compute_best_value()

    assert nb_violated == 0
    assert cost == 10
    assert values == [1]


def test_on_start_sends_initial_value_to_neighbors():
    v1 = Variable("v1", [0, 1], initial_value=1)
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return abs(v1_ - v2_)

    computation = MixedDsaComputation(
        v1, [soft], comp_def=_comp_def(v1, [soft])
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value == 1
    assert computation.cycle_count == 1
    message_sender.assert_called_once_with(
        "v1", "v2", MixedDsaMessage(1), None, None
    )


def test_send_value_stops_at_stop_cycle_without_posting():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return abs(v1_ - v2_)

    computation = MixedDsaComputation(
        v1,
        [soft],
        stop_cycle=1,
        comp_def=_comp_def(v1, [soft], params={"stop_cycle": 1}),
    )
    computation.value_selection(0, 0)
    computation.finished = MagicMock()
    computation.stop = MagicMock()
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._send_value()

    assert computation.cycle_count == 1
    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()
    message_sender.assert_not_called()


def test_variant_a_does_not_make_equal_cost_hard_sideway_move():
    v1 = Variable("v1", [0, 1], initial_value=0)
    v2 = Variable("v2", [0])

    @AsNAryFunctionRelation(v1, v2)
    def hard(v1_, v2_):
        return mixeddsa.INFINITY

    computation = MixedDsaComputation(
        v1,
        [hard],
        variant="A",
        proba_hard=1,
        comp_def=_comp_def(v1, [hard], params={"variant": "A", "proba_hard": 1}),
    )
    computation.value_selection(0, mixeddsa.INFINITY)
    computation._neighbors_values["v2"] = 0
    computation.message_sender = MagicMock()

    with patch("pydcop.algorithms.mixeddsa.random.random", return_value=0), patch(
        "pydcop.algorithms.mixeddsa.random.choice", lambda values: values[-1]
    ):
        computation._on_neighbors_values()

    assert computation.current_value == 0


def test_variant_c_can_make_equal_cost_sideway_move_without_violation():
    v1 = Variable("v1", [0, 1], initial_value=0)
    v2 = Variable("v2", [0])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return 0

    computation = MixedDsaComputation(
        v1,
        [soft],
        variant="C",
        proba_hard=1,
        proba_soft=1,
        comp_def=_comp_def(
            v1,
            [soft],
            params={"variant": "C", "proba_hard": 1, "proba_soft": 1},
        ),
    )
    computation.value_selection(0, 0)
    computation._neighbors_values["v2"] = 0
    computation.message_sender = MagicMock()

    with patch("pydcop.algorithms.mixeddsa.random.random", return_value=0), patch(
        "pydcop.algorithms.mixeddsa.random.choice", lambda values: values[-1]
    ):
        computation._on_neighbors_values()

    assert computation.current_value == 1


def test_value_message_full_cycle_processes_postponed_messages():
    v1 = Variable("v1", [0, 1], initial_value=0)
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return abs(v1_ - v2_)

    computation = MixedDsaComputation(
        v1,
        [soft],
        proba_soft=1,
        comp_def=_comp_def(v1, [soft], params={"proba_soft": 1}),
    )
    computation.value_selection(0, 1)
    computation._neighbors_values["v2"] = 1
    message_sender = MagicMock()
    computation.message_sender = message_sender

    with patch("pydcop.algorithms.mixeddsa.random.random", return_value=0), patch(
        "pydcop.algorithms.mixeddsa.random.choice", side_effect=[1, 0]
    ):
        computation._on_value_msg("v2", MixedDsaMessage(0), None)

    assert computation.current_value == 0
    assert computation.current_cost == 0
    assert computation._neighbors_values == {}
    message_sender.assert_has_calls(
        [
            call("v1", "v2", MixedDsaMessage(1), None, None),
            call("v1", "v2", MixedDsaMessage(0), None, None),
        ]
    )
