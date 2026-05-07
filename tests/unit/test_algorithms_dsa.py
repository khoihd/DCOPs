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

from pydcop.algorithms import dsa, AlgorithmDef, ComputationDef
from pydcop.algorithms.dsa import DsaComputation, DsaMessage
from pydcop.computations_graph.constraints_hypergraph \
    import VariableComputationNode
from pydcop.dcop.objects import Variable, VariableWithCostFunc
from pydcop.dcop.relations import UnaryFunctionRelation, \
    AsNAryFunctionRelation, relation_from_str, constraint_from_str


def test_communication_load():
    v = Variable('v1', list(range(10)))
    var_node = VariableComputationNode(v, [])
    expected = dsa.UNIT_SIZE + dsa.HEADER_SIZE
    assert dsa.communication_load(var_node, 'f1') == expected
    assert dsa.communication_load(var_node, 'another_neighbor') == expected


def test_computation_memory_one_constraint():
    v1 = Variable('v1', list(range(10)))
    v2 = Variable('v2', list(range(10)))
    v3 = Variable('v3', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
    v1_node = VariableComputationNode(v1, [c1])

    # here, we have an hyper-edges with 3 vertices
    assert set(v1_node.neighbors) == {'v2', 'v3'}
    assert dsa.computation_memory(v1_node) == dsa.UNIT_SIZE * 2


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
    assert set(v1_node.neighbors) == {'v2', 'v3', 'v4'}
    assert dsa.computation_memory(v1_node) == dsa.UNIT_SIZE * 3


def test_computation_memory_uses_exact_variable_names():
    v1 = Variable('v1', list(range(10)))
    v10 = Variable('v10', list(range(10)))
    c1 = constraint_from_str('c1', ' v1 == v10', [v1, v10])
    v10_node = VariableComputationNode(v10, [c1])

    assert set(v10_node.neighbors) == {'v1'}
    assert dsa.computation_memory(v10_node) == dsa.UNIT_SIZE


def test_footprint_on_computation_object(monkeypatch):
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    v2 = Variable('v2', [0, 1, 2, 3, 4])
    c1 = relation_from_str('c1', '0 if v1 == v2 else  1', [v1, v2])
    n1 = VariableComputationNode(v1, [c1])
    comp_def = ComputationDef(
        n1, AlgorithmDef.build_with_default_param('dsa', mode='min'))
    c = DsaComputation(comp_def)

    # Must fix unit size otherwise the tests fails when we change the default
    # value
    monkeypatch.setattr(dsa, 'UNIT_SIZE', 1)

    footprint = c.footprint()
    assert footprint == 1


def test_build_computation_default_params():
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    n1 = VariableComputationNode(v1, [])
    comp_def = ComputationDef(
        n1, AlgorithmDef.build_with_default_param('dsa'))
    c = DsaComputation(comp_def)
    assert c.mode == 'min'
    assert c.variant == 'B'
    assert c.stop_cycle == 0
    assert c.probability == 0.7
    assert c.constraints == []
    assert c.current_cycle == {}
    assert c.next_cycle == {}
    assert c.best_constraints_costs == {}


def test_build_computation_max_mode():
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    n1 = VariableComputationNode(v1, [])
    comp_def = ComputationDef(
        n1, AlgorithmDef.build_with_default_param('dsa', mode='max'))
    c = DsaComputation(comp_def)
    assert c.mode == 'max'
    assert c.variant == 'B'
    assert c.stop_cycle == 0
    assert c.probability == 0.7


def test_build_computation_with_params():
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    n1 = VariableComputationNode(v1, [])
    comp_def = ComputationDef(
        n1, AlgorithmDef.build_with_default_param(
            'dsa', mode='max', params={'variant': 'C', 'stop_cycle': 10,
                                       'probability': 0.5}))
    c = DsaComputation(comp_def)
    assert c.mode == 'max'
    assert c.variant == 'C'
    assert c.stop_cycle == 10
    assert c.probability == 0.5
    assert c.constraints == []


def test_build_computation_factory():
    v1 = Variable('v1', [0, 1, 2])
    n1 = VariableComputationNode(v1, [])
    comp_def = ComputationDef(
        n1, AlgorithmDef.build_with_default_param('dsa'))

    computation = dsa.build_computation(comp_def)

    assert isinstance(computation, DsaComputation)
    assert computation.variable == v1


def test_build_computation_with_arity_probability():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    v3 = Variable('v3', [0, 1])
    c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
    n1 = VariableComputationNode(v1, [c1])
    comp_def = ComputationDef(
        n1, AlgorithmDef.build_with_default_param(
            'dsa', params={'p_mode': 'arity'}))

    computation = DsaComputation(comp_def)

    assert computation.probability == 0.6


def test_1_unary_constraint_means_no_neighbors():
    variable = Variable('a', [0, 1, 2, 3, 4])
    c1 = UnaryFunctionRelation('c1', variable, lambda x: abs(x - 2))

    node = VariableComputationNode(variable, [c1])
    comp_def = ComputationDef(node,
                              AlgorithmDef.build_with_default_param('dsa'))

    computation = DsaComputation(comp_def=comp_def)
    assert computation.neighbors == []
    assert computation.constraints == [c1]


def test_2_unary_constraint_means_no_neighbors():
    variable = Variable('a', [0, 1, 2, 3, 4])
    c1 = UnaryFunctionRelation('c1', variable, lambda x: abs(x - 3))
    c2 = UnaryFunctionRelation('c1', variable, lambda x: abs(x - 1) * 2)

    node = VariableComputationNode(variable, [c1, c2])
    comp_def = ComputationDef(node,
                              AlgorithmDef.build_with_default_param('dsa'))

    computation = DsaComputation(comp_def=comp_def)
    assert computation.neighbors == []
    assert computation.constraints == [c1, c2]


def test_one_binary_constraint_one_neighbors():
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    v2 = Variable('v2', [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2)
    def c1(v1_, v2_):
        return abs(v1_ - v2_)

    node = VariableComputationNode(v1, [c1])
    comp_def = ComputationDef(node,
                              AlgorithmDef.build_with_default_param('dsa'))

    computation = DsaComputation(comp_def=comp_def)
    assert set(computation.neighbors) == {'v2'}
    assert computation.constraints == [c1]


def test_2_binary_constraint_one_neighbors():
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    v2 = Variable('v2', [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2)
    def c1(v1_, v2_):
        return abs(v1_ - v2_)

    @AsNAryFunctionRelation(v1, v2)
    def c2(v1_, v2_):
        return abs(v1_ + v2_)

    node = VariableComputationNode(v1, [c1, c2])
    comp_def = ComputationDef(node,
                              AlgorithmDef.build_with_default_param('dsa'))

    computation = DsaComputation(comp_def=comp_def)
    assert set(computation.neighbors) == {'v2'}
    assert computation.constraints == [c1, c2]


def test_3ary_constraint_2_neighbors():
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    v2 = Variable('v2', [0, 1, 2, 3, 4])
    v3 = Variable('v3', [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2, v3)
    def c1(v1_, v2_, v3_):
        return abs(v1_ - v2_ + v3_)

    node = VariableComputationNode(v1, [c1])
    comp_def = ComputationDef(node,
                              AlgorithmDef.build_with_default_param('dsa'))

    computation = DsaComputation(comp_def=comp_def)
    assert set(computation.neighbors) == {'v2', 'v3'}
    assert computation.constraints == [c1]


def test_dsa_message_properties():
    message = DsaMessage(3)

    assert message.type == 'dsa_value'
    assert message.value == 3
    assert message.size == 1
    assert str(message) == 'DsaMessage(3)'
    assert repr(message) == 'DsaMessage(3)'
    assert message == DsaMessage(3)
    assert message != DsaMessage(4)
    assert message != object()

################################################################################


def test_select_and_send_random_value_when_starting():
    # When starting, a DSA computation select a random value and send it to
    # all neighbors
    v1 = Variable('v1', [0, 1, 2, 3, 4])
    v2 = Variable('v2', [0, 1, 2, 3, 4])
    v3 = Variable('v3', [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2, v3)
    def c1(v1_, v2_, v3_):
        return abs(v1_ - v2_ + v3_)

    node = VariableComputationNode(v1, [c1])
    comp_def = ComputationDef(node,
                              AlgorithmDef.build_with_default_param('dsa'))

    computation = DsaComputation(comp_def=comp_def)
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value in v1.domain
    expected_message = DsaMessage(computation.current_value)
    assert message_sender.call_count == 2
    message_sender.assert_has_calls(
        [call('v1', 'v2', expected_message, None, None),
         call('v1', 'v3', expected_message, None, None)],
        any_order=True
    )

################################################################################


def test_on_start_without_neighbors_selects_optimal_value_and_stops():
    variable = VariableWithCostFunc(
        'v1', [0, 1, 2], lambda value: abs(value - 2))
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(variable, []),
            AlgorithmDef.build_with_default_param('dsa')))
    computation.finished = MagicMock()
    computation.stop = MagicMock()

    computation.on_start()

    assert computation.current_value == 2
    assert computation.current_cost == 0
    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()


def test_value_message_is_ignored_before_start():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, [c1]),
            AlgorithmDef.build_with_default_param('dsa')))

    computation._on_value_msg('v2', DsaMessage(1), None)

    assert computation.current_cycle == {}
    assert computation.next_cycle == {}


def test_value_message_routes_current_and_next_cycle():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', ' v1 == v2', [v1, v2])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, [c1]),
            AlgorithmDef.build_with_default_param('dsa')))
    computation._running = True
    computation.evaluate_cycle = MagicMock()

    computation._on_value_msg('v2', DsaMessage(1), None)
    computation._on_value_msg('v2', DsaMessage(0), None)

    assert computation.current_cycle == {'v2': 1}
    assert computation.next_cycle == {'v2': 0}
    computation.evaluate_cycle.assert_called_once_with()


def test_evaluate_cycle_changes_value_rotates_cycles_and_posts():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 1', [v1, v2])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, [c1]),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'A', 'probability': 1.0})))
    computation.message_sender = MagicMock()
    computation.value_selection(0)
    computation.current_cycle = {'v2': 1}
    computation.next_cycle = {'v2': 0}

    computation.evaluate_cycle()

    assert computation.current_value == 1
    assert computation.current_cost == 0
    assert computation.cycle_count == 1
    assert computation.current_cycle == {'v2': 0}
    assert computation.next_cycle == {}
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', DsaMessage(1), None, None)


def test_evaluate_cycle_stops_at_stop_cycle_without_posting():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 1', [v1, v2])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, [c1]),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'A', 'probability': 1.0,
                               'stop_cycle': 1})))
    computation.message_sender = MagicMock()
    computation.finished = MagicMock()
    computation.stop = MagicMock()
    computation.value_selection(0)
    computation.current_cycle = {'v2': 1}

    computation.evaluate_cycle()

    assert computation.cycle_count == 1
    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()
    computation.message_sender.assert_not_called()


def test_variant_a_only_changes_on_positive_delta():
    v1 = Variable('v1', [0, 1])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, []),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'A'})))
    computation.probabilistic_change = MagicMock()

    computation.variant_a(0, 1, [1])
    computation.variant_a(2, 3, [0])

    computation.probabilistic_change.assert_called_once_with(3, [0])


def test_variant_b_equal_cost_changes_when_constraint_is_violated():
    v1 = Variable('v1', [0, 1])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, []),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'B'})))
    computation.value_selection(1)
    computation.exists_violated_constraint = MagicMock(return_value=True)
    computation.probabilistic_change = MagicMock()

    computation.variant_b(0, 5, [0, 1])

    computation.exists_violated_constraint.assert_called_once_with()
    computation.probabilistic_change.assert_called_once_with(5, [0])


def test_variant_b_equal_cost_stays_when_no_constraint_is_violated():
    v1 = Variable('v1', [0, 1])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, []),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'B'})))
    computation.exists_violated_constraint = MagicMock(return_value=False)
    computation.probabilistic_change = MagicMock()

    computation.variant_b(0, 5, [0, 1])

    computation.exists_violated_constraint.assert_called_once_with()
    computation.probabilistic_change.assert_not_called()


def test_variant_c_equal_cost_attempts_sideways_move():
    v1 = Variable('v1', [0, 1])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, []),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'C'})))
    computation.value_selection(1)
    computation.probabilistic_change = MagicMock()

    computation.variant_c(0, 5, [0, 1])

    computation.probabilistic_change.assert_called_once_with(5, [0])


def test_probabilistic_change_respects_threshold(monkeypatch):
    v1 = Variable('v1', [0, 1, 2])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, []),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'probability': 0.5})))
    monkeypatch.setattr(dsa.random, 'choice', lambda values: values[-1])
    monkeypatch.setattr(dsa.random, 'random', lambda: 0.4)

    computation.probabilistic_change(12, [1, 2])

    assert computation.current_value == 2
    assert computation.current_cost == 12

    computation.value_selection(0, 0)
    monkeypatch.setattr(dsa.random, 'random', lambda: 0.6)

    computation.probabilistic_change(12, [1, 2])

    assert computation.current_value == 0
    assert computation.current_cost == 0


def test_exists_violated_constraint_uses_current_value_when_missing():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 1', [v1, v2])
    computation = DsaComputation(
        ComputationDef(
            VariableComputationNode(v1, [c1]),
            AlgorithmDef.build_with_default_param(
                'dsa', params={'variant': 'B'})))
    computation.current_cycle = {'v2': 1}
    computation.value_selection(1)

    assert not computation.exists_violated_constraint()

    computation.value_selection(0)

    assert computation.exists_violated_constraint()


################################################################################


def test_str_dsa_class():
    variable = Variable('a', [0, 1, 2, 3, 4])
    c1 = UnaryFunctionRelation('c1', variable, lambda x: abs(x - 2))

    computation = DsaComputation(
        ComputationDef(VariableComputationNode(variable, [c1]),
                       AlgorithmDef.build_with_default_param('dsa')))

    assert str(computation) == "dsa.DsaComputation(a)"


def test_repr_dsa_class():
    variable = Variable('a', [0, 1, 2, 3, 4])
    c1 = UnaryFunctionRelation('c1', variable, lambda x: abs(x - 2))

    computation = DsaComputation(
        ComputationDef(VariableComputationNode(variable, [c1]),
                       AlgorithmDef.build_with_default_param('dsa')))

    assert repr(computation) == "dsa.DsaComputation(a)"
