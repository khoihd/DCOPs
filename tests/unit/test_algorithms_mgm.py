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

from unittest.mock import MagicMock, call, patch

from pydcop.dcop.objects import Variable, VariableWithCostFunc
from pydcop.algorithms import AlgorithmDef, ComputationDef, mgm
from pydcop.algorithms.mgm import MgmComputation, MgmGainMessage, MgmValueMessage
from pydcop.computations_graph.constraints_hypergraph \
    import VariableComputationNode
from pydcop.dcop.relations import constraint_from_str


def _comp_def(variable, constraints, mode='min', params=None):
    return ComputationDef(
        VariableComputationNode(variable, constraints),
        AlgorithmDef.build_with_default_param('mgm', mode=mode, params=params),
    )


def _mgm_computation_with_two_neighbors():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    c2 = constraint_from_str('c2', ' v1 == v3', [v1, v3])
    return MgmComputation(_comp_def(v1, [c1, c2]))


def test_build_computation_factory_creates_mgm_computation():
    variable = Variable('v1', [0, 1])

    computation = mgm.build_computation(_comp_def(variable, []))

    assert isinstance(computation, MgmComputation)
    assert computation.name == 'v1'
    assert computation.variable == variable


def test_computation_init_from_real_computation_def():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])

    computation = MgmComputation(
        _comp_def(v1, [c1], params={'break_mode': 'random', 'stop_cycle': 5})
    )

    assert computation.name == 'v1'
    assert computation.utilities == [c1]
    assert computation.neighbors == {'v2'}
    assert computation.break_mode == 'random'
    assert computation.stop_cycle == 5
    assert computation._state == 'starting'
    assert computation._neighbors_values == {}
    assert computation._neighbors_gains == {}


def test_communication_load():
    v = Variable('v1', list(range(10)))
    var_node = VariableComputationNode(v, [])
    assert mgm.UNIT_SIZE + mgm.HEADER_SIZE \
           == mgm.communication_load(var_node, 'f1')


def test_memory_footprint_estimate_one_constraint():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
    v1_node = VariableComputationNode(v1, [c1])

    # here, we have an hyper-edges with 3 vertices
    assert mgm.memory_footprint_estimate(v1_node) == mgm.UNIT_SIZE * 2


def test_memory_footprint_estimate_two_constraints():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    v4 = Variable('v4', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    c2 = constraint_from_str('c2', ' v1 == v3', [v1, v3])
    c3 = constraint_from_str('c3', ' v1 == v4', [v1, v4])
    v1_node = VariableComputationNode(v1, [c1, c2, c3])

    # here, we have 3 edges , one for each constraint
    assert mgm.memory_footprint_estimate(v1_node) == mgm.UNIT_SIZE * 3


def test_memory_footprint_estimate_uses_exact_variable_names():
    v1 = Variable('v1', list(range(10)))
    v10 = Variable('v10', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v10', [v1, v10])
    v10_node = VariableComputationNode(v10, [c1])

    assert mgm.memory_footprint_estimate(v10_node) == mgm.UNIT_SIZE


def test_mgm_value_message_properties():
    message = MgmValueMessage(3)

    assert message.type == 'mgm_value'
    assert message.value == 3
    assert message.size == 1
    assert str(message) == 'MgmValueMessage(3)'
    assert repr(message) == 'MgmValueMessage(3)'
    assert message == MgmValueMessage(3)
    assert message != MgmValueMessage(4)
    assert message != object()


def test_mgm_gain_message_properties():
    message = MgmGainMessage(5, 0.4)

    assert message.type == 'mgm_gain'
    assert message.value == 5
    assert message.random_nb == 0.4
    assert message.size == 1
    assert str(message) == 'MgmGainMessage(5)'
    assert repr(message) == 'MgmGainMessage(5)'
    assert message == MgmGainMessage(5, 0.9)
    assert message != MgmGainMessage(4, 0.4)
    assert message != object()


def test_start_without_neighbors_selects_optimal_variable_cost_and_finishes():
    variable = VariableWithCostFunc('v1', [0, 1, 2], lambda value: abs(value - 1))
    computation = MgmComputation(_comp_def(variable, []))
    computation.finished = MagicMock()

    computation.start()

    assert computation.current_value == 1
    assert computation.current_cost == 0
    computation.finished.assert_called_once_with()


def test_start_with_neighbors_sends_initial_value():
    v1 = Variable('v1', [0, 1], initial_value=0)
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1]))
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value == 0
    assert computation.current_cost is None
    assert computation._state == 'values'
    assert computation.cycle_count == 1
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmValueMessage(0), None, None
    )


def test_value_message_is_postponed_outside_value_state():
    computation = _mgm_computation_with_two_neighbors()
    message = MgmValueMessage(2)
    computation._state = 'gain'

    computation._on_value_msg('v2', message, None)

    assert computation._neighbors_values == {}
    assert computation.__postponed_value_messages__ == [('v2', message)]


def test_gain_message_is_postponed_outside_gain_state():
    computation = _mgm_computation_with_two_neighbors()
    message = MgmGainMessage(2)
    computation._state = 'values'

    computation._on_gain_msg('v2', message, None)

    assert computation._neighbors_gains == {}
    assert computation.__postponed_gain_messages__ == [('v2', message)]


def test_wait_for_gains_processes_postponed_gain_messages():
    computation = _mgm_computation_with_two_neighbors()
    message = MgmGainMessage(2, 0.4)
    computation.__postponed_gain_messages__.append(('v2', message))

    computation._wait_for_gains()

    assert computation._state == 'gain'
    assert computation._neighbors_gains == {'v2': (2, 0.4)}
    assert computation.__postponed_gain_messages__ == []


def test_wait_for_values_sends_value_and_processes_postponed_value_messages():
    computation = _mgm_computation_with_two_neighbors()
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.value_selection(3, 0)
    message = MgmValueMessage(2)
    computation.__postponed_value_messages__.append(('v2', message))

    computation._wait_for_values()

    assert computation._state == 'values'
    assert computation._neighbors_values == {'v2': 2}
    assert computation.__postponed_value_messages__ == []
    expected_message = MgmValueMessage(3)
    assert message_sender.call_count == 2
    message_sender.assert_has_calls(
        [
            call('v1', 'v2', expected_message, None, None),
            call('v1', 'v3', expected_message, None, None),
        ],
        any_order=True,
    )


def test_value_messages_compute_gain_and_send_gain():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1]))
    computation.value_selection(0, None)
    computation._state = 'values'
    message_sender = MagicMock()
    computation.message_sender = message_sender

    with patch('pydcop.algorithms.mgm.random.choice', return_value=1), patch(
        'pydcop.algorithms.mgm.random.random', return_value=0.4
    ):
        computation._handle_value_message('v2', MgmValueMessage(1))

    assert computation.current_cost == 1
    assert computation._gain == 1
    assert computation._new_value == 1
    assert computation.random_nb == 0.4
    assert computation._state == 'gain'
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmGainMessage(1, 0.4), None, None
    )


def test_compute_best_value_uses_candidate_variable_cost():
    v1 = VariableWithCostFunc('v1', [0, 1], lambda value: 10 if value == 0 else 0)
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 * v1 + 0 * v2', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1]))
    computation.value_selection(0, 10)
    computation._neighbors_values = {'v2': 0}

    values, cost = computation._compute_best_value()

    assert values == [1]
    assert cost == 0


def test_value_messages_compute_negative_gain_in_max_mode():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0])
    c1 = constraint_from_str('c1', 'v1 + v2', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1], mode='max'))
    computation.value_selection(0, None)
    computation._state = 'values'
    message_sender = MagicMock()
    computation.message_sender = message_sender

    with patch('pydcop.algorithms.mgm.random.choice', return_value=1), patch(
        'pydcop.algorithms.mgm.random.random', return_value=0.3
    ):
        computation._handle_value_message('v2', MgmValueMessage(0))

    assert computation.current_cost == 0
    assert computation._gain == -1
    assert computation._new_value == 1
    assert computation._state == 'gain'
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmGainMessage(-1, 0.3), None, None
    )


def test_gain_message_applies_better_min_gain_and_sends_next_value():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1]))
    computation.value_selection(0, 5)
    computation._gain = 3
    computation._new_value = 1
    computation._state = 'gain'
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._handle_gain_message('v2', MgmGainMessage(2))

    assert computation.current_value == 1
    assert computation.current_cost == 2
    assert computation._state == 'values'
    assert computation._neighbors_values == {}
    assert computation._neighbors_gains == {}
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmValueMessage(1), None, None
    )


def test_gain_message_keeps_value_when_neighbor_has_better_min_gain():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1]))
    computation.value_selection(0, 5)
    computation._gain = 2
    computation._new_value = 1
    computation._state = 'gain'
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._handle_gain_message('v2', MgmGainMessage(3))

    assert computation.current_value == 0
    assert computation.current_cost == 5
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmValueMessage(0), None, None
    )


def test_gain_message_applies_better_max_gain_and_sends_next_value():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'v1 + v2', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1], mode='max'))
    computation.value_selection(0, 1)
    computation._gain = -4
    computation._new_value = 1
    computation._state = 'gain'
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._handle_gain_message('v2', MgmGainMessage(-2))

    assert computation.current_value == 1
    assert computation.current_cost == 5
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmValueMessage(1), None, None
    )


def test_send_value_sends_initial_value_before_stop_cycle():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1], params={'stop_cycle': 1}))
    computation.value_selection(0, 0)
    computation.finished = MagicMock()
    message_sender = MagicMock()
    computation.message_sender = message_sender

    sent = computation._send_value()

    assert sent is True
    assert computation.cycle_count == 1
    computation.finished.assert_not_called()
    message_sender.assert_called_once_with(
        'v1', 'v2', MgmValueMessage(0), None, None
    )


def test_send_value_stops_at_stop_cycle_without_posting():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1], params={'stop_cycle': 1}))
    computation.value_selection(0, 0)
    computation.new_cycle()
    computation.finished = MagicMock()
    computation.stop = MagicMock()
    message_sender = MagicMock()
    computation.message_sender = message_sender

    sent = computation._send_value()

    assert sent is False
    assert computation.cycle_count == 1
    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()
    message_sender.assert_not_called()


def test_wait_for_values_does_not_process_postponed_messages_after_stop_cycle():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = MgmComputation(_comp_def(v1, [c1], params={'stop_cycle': 1}))
    computation.value_selection(0, 0)
    computation.new_cycle()
    computation.__postponed_value_messages__.append(('v2', MgmValueMessage(1)))
    computation.finished = MagicMock()
    computation.stop = MagicMock()
    computation._handle_value_message = MagicMock()
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._wait_for_values()

    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()
    computation._handle_value_message.assert_not_called()
    message_sender.assert_not_called()


def test_random_break_mode_uses_random_numbers():
    variable = Variable('b', [0, 1])
    comp_def = ComputationDef(
        VariableComputationNode(variable, []),
        AlgorithmDef.build_with_default_param(
            'mgm', params={'break_mode': 'random'})
    )
    computation = MgmComputation(comp_def)
    computation.value_selection(0, 10)
    computation._new_value = 1
    computation._gain = 5
    computation._neighbors_gains = {'a': (5, 0.9)}
    computation._random_nb = 0.1

    computation._break_ties(5)

    assert computation.current_value == 1
