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

from pydcop.dcop.objects import Variable
from pydcop.algorithms import AlgorithmDef, ComputationDef, mgm
from pydcop.algorithms.mgm import MgmComputation, MgmGainMessage, MgmValueMessage
from pydcop.computations_graph.constraints_hypergraph \
    import VariableComputationNode
from pydcop.dcop.relations import constraint_from_str


def _mgm_computation_with_two_neighbors():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    c2 = constraint_from_str('c2', ' v1 == v3', [v1, v3])
    comp_def = ComputationDef(
        VariableComputationNode(v1, [c1, c2]),
        AlgorithmDef.build_with_default_param('mgm')
    )
    return MgmComputation(comp_def)


def test_communication_load():
    v = Variable('v1', list(range(10)))
    var_node = VariableComputationNode(v, [])
    assert mgm.UNIT_SIZE + mgm.HEADER_SIZE \
           == mgm.communication_load(var_node, 'f1')


def test_computation_memory_one_constraint():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
    v1_node = VariableComputationNode(v1, [c1])

    # here, we have an hyper-edges with 3 vertices
    assert mgm.computation_memory(v1_node) == mgm.UNIT_SIZE * 2


def test_computation_memory_two_constraints():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    v4 = Variable('v4', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    c2 = constraint_from_str('c2', ' v1 == v3', [v1, v3])
    c3 = constraint_from_str('c3', ' v1 == v4', [v1, v4])
    v1_node = VariableComputationNode(v1, [c1, c2, c3])

    # here, we have 3 edges , one for each constraint
    assert mgm.computation_memory(v1_node) == mgm.UNIT_SIZE * 3


def test_computation_memory_uses_exact_variable_names():
    v1 = Variable('v1', list(range(10)))
    v10 = Variable('v10', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v10', [v1, v10])
    v10_node = VariableComputationNode(v10, [c1])

    assert mgm.computation_memory(v10_node) == mgm.UNIT_SIZE


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
