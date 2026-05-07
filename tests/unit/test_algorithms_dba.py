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


from unittest.mock import MagicMock, call

import pytest

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms import dba
from pydcop.algorithms.dba import (
    DbaComputation,
    DbaEndMessage,
    DbaImproveMessage,
    DbaOkMessage,
)
from pydcop.computations_graph.constraints_hypergraph import (
    VariableComputationNode,
)
from pydcop.dcop.objects import Variable
from pydcop.dcop.relations import UnaryFunctionRelation, constraint_from_str


def _computation_def(variable, constraints=None, params=None, mode="min"):
    constraints = [] if constraints is None else constraints
    return ComputationDef(
        VariableComputationNode(variable, constraints),
        AlgorithmDef.build_with_default_param(
            "dba", params=params, mode=mode
        ),
    )


def _dba_computation(variable, constraints=None, params=None, mode="min"):
    return dba.build_computation(
        _computation_def(variable, constraints, params=params, mode=mode)
    )


def test_communication_load():
    v = Variable('v1', [0, 1])
    var_node = VariableComputationNode(v, [])
    expected = dba.UNIT_SIZE * 2 + dba.HEADER_SIZE

    assert dba.communication_load(var_node, 'f1') == expected
    assert dba.communication_load(var_node, 'another_neighbor') == expected


def test_memory_footprint_estimate_one_constraint():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    v3 = Variable('v3', [0, 1])
    c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
    v1_node = VariableComputationNode(v1, [c1])

    # here, we have an hyper-edges with 3 vertices
    assert set(v1_node.neighbors) == {'v2', 'v3'}
    assert dba.memory_footprint_estimate(v1_node) == dba.UNIT_SIZE * 2


def test_memory_footprint_estimate_two_constraints():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    v3 = Variable('v3', [0, 1])
    v4 = Variable('v4', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    c2 = constraint_from_str('c2', ' v1 == v3', [v1, v3])
    c3 = constraint_from_str('c3', ' v1 == v4', [v1, v4])
    v1_node = VariableComputationNode(v1, [c1, c2, c3])

    # here, we have 3 edges , one for each constraint
    assert set(v1_node.neighbors) == {'v2', 'v3', 'v4'}
    assert dba.memory_footprint_estimate(v1_node) == dba.UNIT_SIZE * 3


def test_memory_footprint_estimate_counts_duplicate_neighbor_once():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    c2 = constraint_from_str('c2', ' v1 != v2', [v1, v2])
    v1_node = VariableComputationNode(v1, [c1, c2])

    assert set(v1_node.neighbors) == {'v2'}
    assert dba.memory_footprint_estimate(v1_node) == dba.UNIT_SIZE


def test_memory_footprint_estimate_uses_exact_variable_names():
    v1 = Variable('v1', [0, 1])
    v10 = Variable('v10', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v10', [v1, v10])
    v10_node = VariableComputationNode(v10, [c1])

    assert set(v10_node.neighbors) == {'v1'}
    assert dba.memory_footprint_estimate(v10_node) == dba.UNIT_SIZE


def test_footprint_on_computation_object(monkeypatch):
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    computation = _dba_computation(v1, [c1])

    monkeypatch.setattr(dba, 'UNIT_SIZE', 1)

    assert computation.footprint() == 1


def test_build_computation_default_params():
    v1 = Variable('v1', [0, 1])
    comp_def = _computation_def(v1)

    computation = dba.build_computation(comp_def)

    assert isinstance(computation, DbaComputation)
    assert computation.variable == v1
    assert computation.constraints == []
    assert computation.neighbors == set()
    assert computation._max_distance == 50
    assert computation._mode == 'starting'


def test_build_computation_with_params(monkeypatch):
    monkeypatch.setattr(dba, 'INFINITY', dba.INFINITY)
    v1 = Variable('v1', [0, 1])

    computation = _dba_computation(
        v1, params={'infinity': 42, 'max_distance': 3}
    )

    assert dba.INFINITY == 42
    assert computation._max_distance == 3
    computation._termination_counter = 2
    assert not computation.stop_condition()
    computation._termination_counter = 3
    assert computation.stop_condition()


def test_build_computation_rejects_max_mode():
    v1 = Variable('v1', [0, 1])
    comp_def = _computation_def(v1, mode='max')

    with pytest.raises(ValueError, match='only support minimization'):
        dba.build_computation(comp_def)


def test_unary_constraints_have_no_neighbors():
    v1 = Variable('v1', [0, 1, 2])
    c1 = UnaryFunctionRelation('c1', v1, lambda x: abs(x - 1))
    c2 = UnaryFunctionRelation('c2', v1, lambda x: abs(x - 2))

    computation = _dba_computation(v1, [c1, c2])

    assert computation.neighbors == set()
    assert computation.constraints == [c1, c2]


def test_one_binary_constraint_has_one_neighbor():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])

    computation = _dba_computation(v1, [c1])

    assert computation.neighbors == {'v2'}
    assert computation.constraints == [c1]


def test_dba_ok_message_properties():
    message = DbaOkMessage('red')

    assert message.type == 'dba_ok'
    assert message.value == 'red'
    assert message.size == 1
    assert str(message) == 'DbaOkMessage(red)'
    assert repr(message) == 'DbaOkMessage(red)'
    assert message == DbaOkMessage('red')
    assert message != DbaOkMessage('blue')
    assert message != object()


def test_dba_improve_message_properties():
    message = DbaImproveMessage(3, 5, 2)

    assert message.type == 'dba_improve'
    assert message.improve == 3
    assert message.current_eval == 5
    assert message.termination_counter == 2
    assert message.size == 1
    assert str(message) == 'DbaImproveMessage(improve:3, eval: 5)'
    assert repr(message) == 'DbaImproveMessage(3, 5)'
    assert message == DbaImproveMessage(3, 5, 2)
    assert message != DbaImproveMessage(4, 5, 2)
    assert message != DbaImproveMessage(3, 4, 2)
    assert message != object()


def test_dba_end_message_properties():
    message = DbaEndMessage()

    assert message.type == 'dba_end'
    assert message.size == 1
    assert str(message) == 'DbaEndMessage()'
    assert repr(message) == 'DbaEndMessage()'
    assert message == DbaEndMessage()
    assert message != object()


def test_compute_eval_value_counts_violated_constraints_and_weights():
    v1 = Variable('v1', [0, 1])
    c1 = UnaryFunctionRelation(
        'c1', v1, lambda x: 0 if x == 1 else dba.INFINITY
    )
    c2 = UnaryFunctionRelation(
        'c2', v1, lambda x: dba.INFINITY if x == 1 else 0
    )
    computation = _dba_computation(v1, [c1, c2])

    assert computation.compute_eval_value(1, [c1, c2]) == (1, [1])
    assert computation.compute_eval_value(0, [c1, c2]) == (1, [0])
    assert computation.compute_eval_value(
        1, [c1, c2], collect_violated=False) == (1, None)

    computation._increase_weights([1])

    assert computation.compute_eval_value(1, [c1, c2]) == (2, [1])


def test_compute_best_improvement_returns_all_best_values():
    v1 = Variable('v1', [0, 1, 2])
    c1 = UnaryFunctionRelation(
        'c1', v1, lambda x: 0 if x in [1, 2] else dba.INFINITY
    )
    computation = _dba_computation(v1, [c1])

    best_values, best_eval = computation._compute_best_improvement([c1])

    assert best_values == [1, 2]
    assert best_eval == 0


def test_improve_keeps_direct_call_violated_constraint_fallback():
    v1 = Variable('v1', [0, 1])
    c1 = UnaryFunctionRelation(
        'c1', v1, lambda x: 0 if x == 1 else dba.INFINITY
    )
    computation = _dba_computation(v1, [c1])
    computation.value_selection(0)
    computation.__cost__, _ = computation.compute_eval_value(0, [c1])

    computation.improve([c1])

    assert computation._violated_constraints == [0]


def test_select_and_send_random_value_when_starting():
    v1 = Variable('v1', [0, 1, 2])
    v2 = Variable('v2', [0, 1, 2])
    v3 = Variable('v3', [0, 1, 2])
    c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
    computation = _dba_computation(v1, [c1])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value in v1.domain
    assert computation._in_wait_ok_mode()
    expected_message = DbaOkMessage(computation.current_value)
    message_sender.assert_has_calls(
        [
            call('v1', 'v2', expected_message, None, None),
            call('v1', 'v3', expected_message, None, None),
        ],
        any_order=True,
    )
    assert message_sender.call_count == 2


def test_ok_message_received_outside_ok_mode_is_postponed():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str(
        'c1', f'0 if v1 == v2 else {dba.INFINITY}', [v1, v2]
    )
    computation = _dba_computation(v1, [c1])
    computation._mode = 'improve'

    computation._on_ok_msg('v2', DbaOkMessage(1), None)

    assert computation._neighbors_values == {}
    assert computation.__postponed_ok_messages__ == [
        ('v2', DbaOkMessage(1))
    ]


def test_postponed_ok_message_is_processed_when_returning_to_ok_mode():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str(
        'c1', f'0 if v1 == v2 else {dba.INFINITY}', [v1, v2]
    )
    computation = _dba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0)
    computation.__postponed_ok_messages__.append(('v2', DbaOkMessage(1)))

    computation._go_to_wait_ok_mode()

    assert computation._in_wait_improve_mode()
    assert computation.__postponed_ok_messages__ == []
    assert computation._neighbors_values == {'v2': 1}
    assert computation._my_improve == 1
    assert computation._can_move
    assert computation._new_value == 1
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', DbaImproveMessage(1, 1, 0), None, None
    )


def test_improve_message_received_outside_improve_mode_is_postponed():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str(
        'c1', f'0 if v1 == v2 else {dba.INFINITY}', [v1, v2]
    )
    computation = _dba_computation(v1, [c1])
    computation._mode = 'ok'

    computation._on_improve_msg('v2', DbaImproveMessage(1, 1, 0), None)

    assert computation._neighbors_improvements == {}
    assert computation.__postponed_improve_messages__ == [
        ('v2', DbaImproveMessage(1, 1, 0))
    ]


def test_postponed_improve_message_is_processed_in_improve_mode():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str(
        'c1', f'0 if v1 == v2 else {dba.INFINITY}', [v1, v2]
    )
    computation = _dba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0)
    computation.__cost__ = 1
    computation._my_improve = 1
    computation._can_move = True
    computation._new_value = 1
    computation._consistent = False
    computation.__postponed_improve_messages__.append(
        ('v2', DbaImproveMessage(0, 1, 0))
    )

    computation._go_to_wait_improve_mode()

    assert computation._in_wait_ok_mode()
    assert computation.__postponed_improve_messages__ == []
    assert computation._neighbors_improvements == {}
    assert computation.current_value == 1
    assert computation.current_cost == 0
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', DbaOkMessage(1), None, None
    )


def test_equal_improvement_tie_break_prevents_larger_name_from_moving():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str(
        'c1', f'0 if v1 == v2 else {dba.INFINITY}', [v1, v2]
    )
    computation = _dba_computation(v2, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0)
    computation.__cost__ = 1
    computation._mode = 'improve'
    computation._my_improve = 1
    computation._can_move = True
    computation._new_value = 1
    computation._consistent = False

    computation._on_improve_msg('v1', DbaImproveMessage(1, 1, 0), None)

    assert computation._in_wait_ok_mode()
    assert not computation._can_move
    assert computation.current_value == 0
    computation.message_sender.assert_called_once_with(
        'v2', 'v1', DbaOkMessage(0), None, None
    )


def test_send_ok_increases_weights_in_quasi_local_minimum():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str(
        'c1', f'v1 * 0 + v2 * 0 + {dba.INFINITY}', [v1, v2]
    )
    computation = _dba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0)
    computation._consistent = False
    computation._quasi_local_minimum = True
    computation._violated_constraints = [0]

    computation._send_ok()

    assert computation.__constraints_weights__ == [2]
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', DbaOkMessage(0), None, None
    )


def test_send_ok_finishes_when_consistent_for_max_distance():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 10000', [v1, v2])
    computation = _dba_computation(v1, [c1], params={'max_distance': 1})
    computation.message_sender = MagicMock()
    computation.finished = MagicMock()
    computation.value_selection(0)
    computation._consistent = True

    computation._send_ok()

    assert computation._mode == 'finished'
    assert computation._termination_counter == 1
    computation.finished.assert_called_once_with()
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', DbaEndMessage(), None, None
    )


def test_end_message_is_propagated_once():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 10000', [v1, v2])
    computation = _dba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.finished = MagicMock()

    computation._on_end_msg('v2', DbaEndMessage(), None)

    assert computation._mode == 'finished'
    computation.finished.assert_called_once_with()
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', DbaEndMessage(), None, None
    )

    computation.message_sender.reset_mock()
    computation.finished.reset_mock()

    computation._on_end_msg('v2', DbaEndMessage(), None)

    computation.message_sender.assert_not_called()
    computation.finished.assert_not_called()
