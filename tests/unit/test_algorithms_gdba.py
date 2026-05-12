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


import unittest
from unittest.mock import MagicMock, call

import numpy
import pytest

from pydcop.algorithms import AlgorithmDef, ComputationDef, gdba
from pydcop.algorithms.gdba import (
    GdbaComputation,
    GdbaImproveMessage,
    GdbaOkMessage,
)
from pydcop.computations_graph.constraints_hypergraph import \
    VariableComputationNode
from pydcop.dcop.objects import Variable, VariableWithCostFunc
from pydcop.dcop.relations import AsNAryFunctionRelation, NAryMatrixRelation, \
    UnaryFunctionRelation, NAryFunctionRelation, constraint_from_str


def _computation_def(variable, constraints=None, params=None, mode="min"):
    constraints = [] if constraints is None else constraints
    return ComputationDef(
        VariableComputationNode(variable, constraints),
        AlgorithmDef.build_with_default_param(
            "gdba", params=params, mode=mode
        ),
    )


def _gdba_computation(variable, constraints=None, params=None, mode="min"):
    return gdba.build_computation(
        _computation_def(variable, constraints, params=params, mode=mode)
    )


class TestGdbaInfrastructure(unittest.TestCase):
    def test_memory_footprint_estimate_one_constraint(self):
        v1 = Variable('v1', [0, 1])
        v2 = Variable('v2', [0, 1])
        v3 = Variable('v3', [0, 1])
        c1 = constraint_from_str('c1', ' v1 + v2 == v3', [v1, v2, v3])
        v1_node = VariableComputationNode(v1, [c1])

        self.assertEqual(gdba.memory_footprint_estimate(v1_node), gdba.UNIT_SIZE * 2)

    def test_memory_footprint_estimate_uses_exact_variable_names(self):
        v1 = Variable('v1', [0, 1])
        v10 = Variable('v10', [0, 1])
        c1 = constraint_from_str('c1', ' v1 == v10', [v1, v10])
        v10_node = VariableComputationNode(v10, [c1])

        self.assertEqual(set(v10_node.neighbors), {'v1'})
        self.assertEqual(gdba.memory_footprint_estimate(v10_node), gdba.UNIT_SIZE)


class GdbaAlgoTest(unittest.TestCase):
    def test_init_from_constraints_as_functions(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            return x1_ + x2_

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())

        m = NAryMatrixRelation.from_func_relation(phi)
        (c_mat, mini, maxi) = g.__constraints__[0]
        self.assertEqual(c_mat, m)
        self.assertEqual(mini, 0)
        self.assertEqual(maxi, 4)

    def test_init_from_constraints_as_matrices(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)

        m = numpy.array([[1, 0], [0, 1]])
        mat = NAryMatrixRelation([x1, x2], m)

        g = GdbaComputation(x1, [mat], comp_def=MagicMock())
        c_mat, mini, maxi = g.__constraints__[0]

        self.assertTrue(numpy.array_equal(mat._m, m))
        self.assertEqual(mini, 0)
        self.assertEqual(maxi, 1)


class TestsCostComputation(unittest.TestCase):
    def test_compute_eval_binary(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            if x1_ == x2_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 0

        eval0, _ = g.compute_eval_value(0)
        eval1, _ = g.compute_eval_value(1)
        eval1_no_violations, violations = g.compute_eval_value(
            1, collect_violated=False)

        self.assertEqual(eval0, 1)
        self.assertEqual(eval1, 0)
        self.assertEqual(eval1_no_violations, 0)
        self.assertIsNone(violations)

    def test_compute_eval_3_ary(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_ or x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 0
        g._neighbors_values['x3'] = 1

        eval0, _ = g.compute_eval_value(0)
        eval1, _ = g.compute_eval_value(1)
        eval2, _ = g.compute_eval_value(2)

        self.assertEqual(eval0, 1)
        self.assertEqual(eval1, 1)
        self.assertEqual(eval2, 0)

    def test_min_compute_best_for_binary_constraint(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            if x1_ == x2_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 0
        bests, best = g._compute_best_improvement()

        self.assertEqual(best, 0)
        self.assertEqual(bests, [1])

    def test_max_compute_best_for_binary_constraint(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            if x1_ == x2_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], mode='max', comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        bests, best = g._compute_best_improvement()

        self.assertEqual(best, 1)
        self.assertEqual(bests, [1])

    def test_min_compute_best_for_3_ary_constraint(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_ or x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 0
        g._neighbors_values['x3'] = 0
        bests, best = g._compute_best_improvement()

        self.assertEqual(best, 0)
        self.assertEqual(bests, [1, 2])

    def test_eff_cost_A_unary(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)

        @AsNAryFunctionRelation(x1)
        def phi(x1_):
            return x1_

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        c, _, _ = g.__constraints__[0]
        g.__value__ = 0
        asgt = frozenset({'x1': 0}.items())
        g.__constraints_modifiers__[c][asgt] = 5

        self.assertEqual(g._eff_cost(c, 0), 5)
        self.assertEqual(g._eff_cost(c, 1), 1)
        self.assertEqual(g._eff_cost(c, 2), 2)

    def test_eff_cost_A_n_ary(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_:
                return 2
            if x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        c, _, _ = g.__constraints__[0]
        asgt = frozenset({'x1': 0, 'x2': 1, 'x3': 2}.items())
        g.__constraints_modifiers__[c][asgt] = 5

        self.assertEqual(g._eff_cost(c, 0), 5)
        self.assertEqual(g._eff_cost(c, 1), 2)
        self.assertEqual(g._eff_cost(c, 2), 1)

    def test_eff_cost_M_unary(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)

        @AsNAryFunctionRelation(x1)
        def phi(x1_):
            return x1_

        g = GdbaComputation(x1, [phi], modifier='M', comp_def=MagicMock())
        c, _, _ = g.__constraints__[0]
        asgt = frozenset({'x1': 0, }.items())
        g.__constraints_modifiers__[c][asgt] = 5

        self.assertEqual(g._eff_cost(c, 0), 0)
        self.assertEqual(g._eff_cost(c, 1), 1)
        self.assertEqual(g._eff_cost(c, 2), 2)

    def test_eff_cost_M_n_ary(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_:
                return 2
            if x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], modifier='M', comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        c, _, _ = g.__constraints__[0]
        asgt = frozenset({'x1': 0, 'x2': 1, 'x3': 2}.items())
        asgt2 = frozenset({'x1': 1, 'x2': 1, 'x3': 2}.items())
        g.__constraints_modifiers__[c][asgt] = 5
        g.__constraints_modifiers__[c][asgt2] = 5

        self.assertEqual(g._eff_cost(c, 0), 0)
        self.assertEqual(g._eff_cost(c, 1), 10)
        self.assertEqual(g._eff_cost(c, 2), 1)


class TestsConstraintViolation(unittest.TestCase):
    domain = list(range(2))
    x1 = Variable('x1', domain)
    x2 = Variable('x2', domain)
    x3 = Variable('x3', domain)

    phi = UnaryFunctionRelation('phi', Variable('x1', domain), lambda x: x)

    phi_n_ary = NAryFunctionRelation(
        lambda x1_, x2_, x3_: 2 if x1_ == x2_ else (1 if x1_ == x3_ else 0),
        [x1, x2, x3])

    def NZ_violation_unary(self):
        g = GdbaComputation(self.x1, [self.phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        c = g.__constraints__[0]
        self.assertEqual(g._is_violated(c, 0), False)
        self.assertEqual(g._is_violated(c, 1), True)
        self.assertEqual(g._is_violated(c, 2), True)

    def NZ_violation_n_ary(self):
        g = GdbaComputation(self.x1, [self.phi_n_ary], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        c = g.__constraints__[0]
        self.assertEqual(g._is_violated(c, 0), False)
        self.assertEqual(g._is_violated(c, 1), True)
        self.assertEqual(g._is_violated(c, 2), True)

    def NM_violation_unary(self):
        g = GdbaComputation(self.x1, [self.phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        g._violation_mode = 'NM'
        c = g.__constraints__[0]
        self.assertEqual(g._is_violated(c, 0), False)
        self.assertEqual(g._is_violated(c, 1), True)
        self.assertEqual(g._is_violated(c, 2), True)

    def NM_violation_n_ary(self):
        g = GdbaComputation(self.x1, [self.phi_n_ary], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        g._violation_mode = 'NM'
        c = g.__constraints__[0]
        self.assertEqual(g._is_violated(c, 0), False)
        self.assertEqual(g._is_violated(c, 1), True)
        self.assertEqual(g._is_violated(c, 2), True)

    def MX_violation_unary(self):
        g = GdbaComputation(self.x1, [self.phi], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        g._violation_mode = 'MX'
        c = g.__constraints__[0]
        self.assertEqual(g._is_violated(c, 0), False)
        self.assertEqual(g._is_violated(c, 1), False)
        self.assertEqual(g._is_violated(c, 2), True)

    def MX_violation_n_ary(self):
        g = GdbaComputation(self.x1, [self.phi_n_ary], comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        g._violation_mode = 'MX'
        c = g.__constraints__[0]
        self.assertEqual(g._is_violated(c, 0), False)
        self.assertEqual(g._is_violated(c, 1), True)
        self.assertEqual(g._is_violated(c, 2), False)


class TestIncreaseCost(unittest.TestCase):
    def test_increase_E(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_:
                return 2
            if x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], comp_def=MagicMock())
        g.__value__ = 0
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        c, _, _ = g.__constraints__[0]
        g._increase_cost(c)
        asgt = {'x1': 0, 'x2': 1, 'x3': 2}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)

    def test_increase_C_updates_local_column(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_:
                return 2
            if x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], increase_mode='C', comp_def=MagicMock())
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 1
        c, _, _ = g.__constraints__[0]
        g._increase_cost(c)
        asgt = g._neighbors_values.copy()
        for val in x1.domain:
            asgt['x1'] = val
            modifier = frozenset(asgt.items())
            self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)

    def test_increase_R_updates_local_row(self):
        domain = list(range(3))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_:
                return 2
            if x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], increase_mode='R', comp_def=MagicMock())
        c, _, _ = g.__constraints__[0]
        g.__value__ = 0
        g._neighbors_values['x2'] = 1
        g._neighbors_values['x3'] = 2
        g._increase_cost(c)
        asgt = {'x1': 0, 'x2': 0, 'x3': 0}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 0, 'x3': 1}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 0, 'x3': 2}
        modifier = frozenset(asgt.items())
        self.assertIn(modifier, g.__constraints_modifiers__[c])
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 1, 'x3': 0}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 1, 'x3': 1}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 1, 'x3': 2}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 2, 'x3': 0}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 2, 'x3': 1}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)
        asgt = {'x1': 0, 'x2': 2, 'x3': 2}
        modifier = frozenset(asgt.items())
        self.assertEqual(g.__constraints_modifiers__[c][modifier], 1)

    def test_increase_T(self):
        domain = list(range(2))
        x1 = Variable('x1', domain)
        x2 = Variable('x2', domain)
        x3 = Variable('x3', domain)

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi(x1_, x2_, x3_):
            if x1_ == x2_:
                return 2
            if x1_ == x3_:
                return 1
            return 0

        g = GdbaComputation(x1, [phi], increase_mode='T', comp_def=MagicMock())
        c, _, _ = g.__constraints__[0]
        g._increase_cost(c)
        modifiers = g.__constraints_modifiers__[c]
        for _, modifier in modifiers.items():
            self.assertEqual(modifier, 1)


def test_communication_load():
    v1 = Variable('v1', [0, 1])
    node = VariableComputationNode(v1, [])
    expected = gdba.HEADER_SIZE + 2 * gdba.UNIT_SIZE

    assert gdba.communication_load(node, 'v2') == expected
    assert gdba.communication_load(node, 'another_neighbor') == expected


def test_build_computation_default_params():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'v1 + v2', [v1, v2])

    computation = _gdba_computation(v1, [c1])

    assert isinstance(computation, GdbaComputation)
    assert computation.variable == v1
    assert computation._mode == 'min'
    assert computation._modifier_mode == 'A'
    assert computation._violation_mode == 'NZ'
    assert computation._increase_mode == 'E'
    assert computation.stop_cycle == 0
    assert {v.name for v in computation.neighbors} == {'v2'}


def test_build_computation_with_params():
    v1 = Variable('v1', [0, 1])
    computation = _gdba_computation(
        v1,
        params={
            'modifier': 'M',
            'violation': 'MX',
            'increase_mode': 'T',
            'stop_cycle': 5,
        },
        mode='max',
    )

    assert computation._mode == 'max'
    assert computation._modifier_mode == 'M'
    assert computation._violation_mode == 'MX'
    assert computation._increase_mode == 'T'
    assert computation.stop_cycle == 5


def test_gdba_ok_message_properties():
    message = GdbaOkMessage('red')

    assert message.type == 'gdba_ok'
    assert message.value == 'red'
    assert message.size == 1
    assert str(message) == 'GdbaOkMessage(red)'
    assert repr(message) == 'GdbaOkMessage(red)'
    assert message == GdbaOkMessage('red')
    assert message != GdbaOkMessage('blue')
    assert message != object()


def test_gdba_improve_message_properties():
    message = GdbaImproveMessage(3)

    assert message.type == 'gdba_improve'
    assert message.improve == 3
    assert message.size == 1
    assert str(message) == 'GdbaImproveMessage(3)'
    assert repr(message) == 'GdbaImproveMessage(3)'
    assert message == GdbaImproveMessage(3)
    assert message != GdbaImproveMessage(4)
    assert message != object()


def test_on_start_without_neighbors_selects_optimal_value_and_finishes():
    v1 = VariableWithCostFunc('v1', [0, 1, 2], lambda value: abs(value - 2))
    computation = _gdba_computation(v1, [])
    computation.finished = MagicMock()

    computation.on_start()

    assert computation.current_value == 2
    assert computation.current_cost == 0
    computation.finished.assert_called_once_with()


def test_on_start_uses_initial_value_and_sends_to_neighbors():
    v1 = Variable('v1', [0, 1], initial_value=1)
    v2 = Variable('v2', [0, 1])
    v3 = Variable('v3', [0, 1])
    c1 = constraint_from_str('c1', 'v1 + v2 + v3', [v1, v2, v3])
    computation = _gdba_computation(v1, [c1])
    computation.message_sender = MagicMock()

    computation.start()

    assert computation.current_value == 1
    assert computation._waiting_mode == 'ok'
    assert computation.cycle_count == 1
    expected = GdbaOkMessage(1)
    computation.message_sender.assert_has_calls(
        [
            call('v1', 'v2', expected, None, None),
            call('v1', 'v3', expected, None, None),
        ],
        any_order=True,
    )
    assert computation.message_sender.call_count == 2


def test_send_current_value_sends_initial_value_before_stop_cycle():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = _gdba_computation(v1, [c1], params={'stop_cycle': 1})
    computation.value_selection(0, 0)
    computation.finished = MagicMock()
    computation.message_sender = MagicMock()

    sent = computation._send_current_value()

    assert sent is True
    assert computation.cycle_count == 1
    computation.finished.assert_not_called()
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', GdbaOkMessage(0), None, None
    )


def test_send_current_value_stops_at_stop_cycle_without_posting():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = _gdba_computation(v1, [c1], params={'stop_cycle': 1})
    computation.value_selection(0, 0)
    computation.new_cycle()
    computation.finished = MagicMock()
    computation.stop = MagicMock()
    computation.message_sender = MagicMock()

    sent = computation._send_current_value()

    assert sent is False
    assert computation.cycle_count == 1
    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()
    computation.message_sender.assert_not_called()


def test_improve_handling_does_not_process_postponed_ok_after_stop_cycle():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'abs(v1 - v2)', [v1, v2])
    computation = _gdba_computation(v1, [c1], params={'stop_cycle': 1})
    computation.value_selection(0, 1)
    computation.new_cycle()
    computation._waiting_mode = 'improve'
    computation._neighbors_values = {'v2': 1}
    computation._my_improve = 0
    computation.__postponed_ok_messages__.append(('v2', GdbaOkMessage(1)))
    computation.finished = MagicMock()
    computation.stop = MagicMock()
    computation._handle_ok_message = MagicMock()
    computation.message_sender = MagicMock()

    computation._handle_improve_message('v2', GdbaImproveMessage(0))

    computation.finished.assert_called_once_with()
    computation.stop.assert_called_once_with()
    computation._handle_ok_message.assert_not_called()
    computation.message_sender.assert_not_called()
    assert computation.__postponed_ok_messages__ == [('v2', GdbaOkMessage(1))]


def test_ok_message_received_outside_ok_mode_is_postponed():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'v1 + v2', [v1, v2])
    computation = _gdba_computation(v1, [c1])
    computation._waiting_mode = 'improve'

    computation._on_ok_msg('v2', GdbaOkMessage(1), None)

    assert computation._neighbors_values == {}
    assert computation.__postponed_ok_messages__ == [
        ('v2', GdbaOkMessage(1))
    ]


def test_postponed_ok_message_is_processed_when_returning_to_ok_mode():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 1', [v1, v2])
    computation = _gdba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0, 1)
    computation.__postponed_ok_messages__.append(('v2', GdbaOkMessage(1)))

    computation._go_to_wait_ok_mode()

    assert computation._waiting_mode == 'improve'
    assert computation.__postponed_ok_messages__ == []
    assert computation._neighbors_values == {'v2': 1}
    assert computation._my_improve == 1
    assert computation._new_value == 1
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', GdbaImproveMessage(1), None, None
    )


def test_improve_message_received_outside_improve_mode_is_postponed():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'v1 + v2', [v1, v2])
    computation = _gdba_computation(v1, [c1])
    computation._waiting_mode = 'ok'

    computation._on_improve_message('v2', GdbaImproveMessage(1), None)

    assert computation._neighbors_improvements == {}
    assert computation.__postponed_improve_messages__ == [
        ('v2', GdbaImproveMessage(1))
    ]


def test_self_winning_improvement_changes_value_and_cost():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 1', [v1, v2])
    computation = _gdba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0, 1)
    computation._waiting_mode = 'improve'
    computation._neighbors_values = {'v2': 1}
    computation.__cost__ = 1
    computation._my_improve = 1
    computation._new_value = 1

    computation._on_improve_message('v2', GdbaImproveMessage(0), None)

    assert computation.current_value == 1
    assert computation.current_cost == 0
    assert computation._waiting_mode == 'ok'
    assert computation._neighbors_improvements == {}
    assert computation._neighbors_values == {}
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', GdbaOkMessage(1), None, None
    )


def test_higher_neighbor_improvement_prevents_local_move():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', '0 if v1 == v2 else 1', [v1, v2])
    computation = _gdba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0, 1)
    computation._waiting_mode = 'improve'
    computation._neighbors_values = {'v2': 1}
    computation._my_improve = 1
    computation._new_value = 1

    computation._on_improve_message('v2', GdbaImproveMessage(2), None)

    assert computation.current_value == 0
    assert computation.current_cost == 1
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', GdbaOkMessage(0), None, None
    )


def test_zero_improvement_increases_violated_constraint_costs():
    v1 = Variable('v1', [0, 1])
    v2 = Variable('v2', [0, 1])
    c1 = constraint_from_str('c1', 'v1 * 0 + v2 * 0 + 1', [v1, v2])
    computation = _gdba_computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(0, 1)
    rel_mat, _, _ = computation.__constraints__[0]
    computation._waiting_mode = 'improve'
    computation._neighbors_values = {'v2': 1}
    computation.__cost__ = 1
    computation._violated_constraints = [rel_mat]
    computation._my_improve = 0
    assignment = frozenset({'v1': 0, 'v2': 1}.items())

    computation._on_improve_message('v2', GdbaImproveMessage(0), None)

    assert computation.__constraints_modifiers__[rel_mat][assignment] == 1
    computation.message_sender.assert_called_once_with(
        'v1', 'v2', GdbaOkMessage(0), None, None
    )


@pytest.mark.parametrize(
    'violation_mode,expected',
    [
        ('NZ', [False, True, True]),
        ('NM', [False, True, True]),
        ('MX', [False, False, True]),
    ],
)
def test_unary_violation_modes_are_discovered(violation_mode, expected):
    v1 = Variable('v1', [0, 1, 2])
    phi = NAryMatrixRelation([v1], numpy.array([0, 1, 2]), name='phi')
    computation = GdbaComputation(
        v1, [phi], violation=violation_mode, comp_def=MagicMock()
    )
    rel = computation.__constraints__[0]

    assert [computation._is_violated(rel, value) for value in v1.domain] == expected


@pytest.mark.parametrize(
    'violation_mode,expected',
    [
        ('NZ', [False, True, True]),
        ('NM', [False, True, True]),
        ('MX', [False, True, False]),
    ],
)
def test_nary_violation_modes_are_discovered(violation_mode, expected):
    v1 = Variable('v1', [0, 1, 2])
    v2 = Variable('v2', [0, 1, 2])
    v3 = Variable('v3', [0, 1, 2])

    @AsNAryFunctionRelation(v1, v2, v3)
    def phi(v1_, v2_, v3_):
        if v1_ == v2_:
            return 2
        if v1_ == v3_:
            return 1
        return 0

    computation = GdbaComputation(
        v1, [phi], violation=violation_mode, comp_def=MagicMock()
    )
    computation._neighbors_values['v2'] = 1
    computation._neighbors_values['v3'] = 2
    rel = computation.__constraints__[0]

    assert [computation._is_violated(rel, value) for value in v1.domain] == expected


def test_break_ties_selects_lexicographically_first_name():
    assert gdba.break_ties(['v10', 'v2', 'v1']) == 'v1'
