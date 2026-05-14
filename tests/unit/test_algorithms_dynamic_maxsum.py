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


import types
import unittest
from unittest.mock import MagicMock, call

import pytest

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms.maxsum import MaxSumMessage, SAME_COUNT
from pydcop.algorithms.maxsum_dynamic import DynamicFunctionFactorComputation
from pydcop.algorithms.maxsum_dynamic import (
    DynamicFactorComputation,
    DynamicFactorVariableComputation,
    FactorWithReadOnlyVariableComputation,
)
from pydcop.computations_graph.factor_graph import FactorComputationNode
from pydcop.dcop.objects import ExternalVariable
from pydcop.dcop.objects import Variable, VariableDomain
from pydcop.dcop.relations import (
    AsNAryFunctionRelation,
    ConditionalRelation,
    NAryFunctionRelation,
)
from pydcop.infrastructure.computations import Message


def _factor_comp_def(factor):
    algo_def = AlgorithmDef.build_with_default_param(
        "amaxsum", params={"noise": 0}
    )
    return ComputationDef(FactorComputationNode(factor), algo_def)

#
class DynamicFunctionFactorComputationTest(unittest.TestCase):
    def test_init(self):
        domain = list(range(10))
        x1 = Variable("x1", domain)
        x2 = Variable("x2", domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            return x1_ + x2_

        f = DynamicFunctionFactorComputation(comp_def=_factor_comp_def(phi))

        self.assertEqual(f.name, "phi")

    def test_change_function_name(self):
        domain = list(range(10))
        x1 = Variable("x1", domain)
        x2 = Variable("x2", domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            return x1_ + x2_

        @AsNAryFunctionRelation(x1, x2)
        def phi2(x1_, x2_):
            return x1_ - x2_

        f = DynamicFunctionFactorComputation(comp_def=_factor_comp_def(phi))
        f.message_sender = MagicMock()
        f.change_factor_function(phi2)

        self.assertEqual(f.name, "phi")

    def test_change_function_different_order(self):
        domain = list(range(10))
        x1 = Variable("x1", domain)
        x2 = Variable("x2", domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            return x1_ + x2_

        @AsNAryFunctionRelation(x2, x1)
        def phi2(x2_, x1_):
            return x1_ - x2_

        f = DynamicFunctionFactorComputation(comp_def=_factor_comp_def(phi))
        f.message_sender = MagicMock()
        f.change_factor_function(phi2)

        self.assertEqual(f.name, "phi")

    def test_change_function_wrong_dimensions_len(self):
        domain = list(range(10))
        x1 = Variable("x1", domain)
        x2 = Variable("x2", domain)
        x3 = Variable("x3", domain)

        @AsNAryFunctionRelation(x1, x2)
        def phi(x1_, x2_):
            return x1_ + x2_

        @AsNAryFunctionRelation(x1, x2, x3)
        def phi2(x1_, x2_, x3_):
            return x1_ - x2_ + x3_

        f = DynamicFunctionFactorComputation(comp_def=_factor_comp_def(phi))
        # Monkey patch post_msg method with dummy mock to avoid error:
        f.post_msg = types.MethodType(lambda w, x, y, z: None, f)

        self.assertRaises(ValueError, f.change_factor_function, phi2)


def test_dynamic_function_change_sends_updated_costs():
    x1 = Variable("x1", [0, 1])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def phi(x1_, x2_):
        return x1_ + x2_

    @AsNAryFunctionRelation(x1, x2)
    def phi2(x1_, x2_):
        return x1_ + 2 * x2_

    computation = DynamicFunctionFactorComputation(comp_def=_factor_comp_def(phi))
    message_sender = MagicMock()
    computation.message_sender = message_sender

    msg_count, msg_size = computation.change_factor_function(phi2)

    assert computation.name == "phi"
    assert computation.factor == phi2
    assert msg_count == 2
    assert msg_size == 8
    message_sender.assert_has_calls(
        [
            call("phi", "x1", MaxSumMessage({0: 0, 1: 1}), None, None),
            call("phi", "x2", MaxSumMessage({0: 0, 1: 2}), None, None),
        ],
        any_order=True,
    )


def test_read_only_factor_waits_for_value_then_slices_relation():
    x = Variable("x", [0, 1])
    sensor = Variable("sensor", [False, True])

    @AsNAryFunctionRelation(x, sensor)
    def rule(x_, sensor_):
        return x_ if sensor_ else 10 - x_

    computation = FactorWithReadOnlyVariableComputation(rule, [sensor])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    assert computation.factor.dimensions == [x]
    assert computation.factor(x=0) == 0
    assert computation.factor(x=1) == 0

    result = computation._on_new_var_value_msg(
        "sensor", Message("VARIABLE_VALUE", True), None
    )

    assert computation.factor.dimensions == [x]
    assert computation.factor(x=0) == 0
    assert computation.factor(x=1) == 1
    assert result["num_msg_out"] == 1
    assert result["size_msg_out"] == 4
    message_sender.assert_called_once_with(
        "rule", "x", MaxSumMessage({0: 0, 1: 1}), None, None
    )


def test_read_only_factor_rejects_read_only_variable_outside_scope():
    x = Variable("x", [0, 1])
    sensor = Variable("sensor", [False, True])

    @AsNAryFunctionRelation(x)
    def rule(x_):
        return x_

    with pytest.raises(ValueError, match="Read only sensor variable"):
        FactorWithReadOnlyVariableComputation(rule, [sensor])


def test_dynamic_factor_sends_add_and_remove_when_external_scope_changes():
    x = Variable("x", [0, 1])
    bool_domain = VariableDomain("boolean", "boolean", [False, True])
    external = ExternalVariable("external", bool_domain, False)
    condition = NAryFunctionRelation(lambda external: external, [external], name="cond")

    @AsNAryFunctionRelation(x)
    def active_rule(x_):
        return x_

    relation = ConditionalRelation(condition, active_rule, name="dynamic_rule")
    computation = DynamicFactorComputation(relation)
    message_sender = MagicMock()
    computation.message_sender = message_sender

    assert computation.name == "dynamic_rule"
    assert computation.factor.dimensions == []

    computation._on_new_var_value_msg(
        "external", Message("VARIABLE_VALUE", True), None
    )

    assert computation.factor == active_rule
    message_sender.assert_called_once_with(
        "dynamic_rule", "x", Message("ADD", {0: 0, 1: 1}), None, None
    )

    message_sender.reset_mock()
    computation._on_new_var_value_msg(
        "external", Message("VARIABLE_VALUE", False), None
    )

    assert computation.factor.dimensions == []
    message_sender.assert_called_once_with(
        "dynamic_rule", "x", Message("REMOVE", None), None, None
    )


def test_dynamic_factor_scope_change_updates_retained_variables():
    x = Variable("x", [0, 1])
    y = Variable("y", [0, 1])
    z = Variable("z", [0, 1])

    @AsNAryFunctionRelation(x, y)
    def phi(x_, y_):
        return x_ + 10 * y_

    @AsNAryFunctionRelation(x, z)
    def phi2(x_, z_):
        return x_ + 2 * z_

    computation = DynamicFactorComputation(phi)
    message_sender = MagicMock()
    computation.message_sender = message_sender

    msg_count, msg_size = computation.change_factor_function(phi2)

    assert computation.factor == phi2
    assert computation.variables == [x, z]
    assert msg_count == 3
    assert msg_size == 8
    message_sender.assert_has_calls(
        [
            call("phi", "y", Message("REMOVE", None), None, None),
            call("phi", "z", Message("ADD", {0: 0, 1: 2}), None, None),
            call("phi", "x", MaxSumMessage({0: 0, 1: 1}), None, None),
        ]
    )
    assert computation._prev_messages["z"] == ({0: 0, 1: 2}, 1)
    assert computation._prev_messages["x"] == ({0: 0, 1: 1}, 1)


def test_dynamic_variable_processes_add_message_as_factor_costs():
    variable = Variable("x", [0, 1])
    computation = DynamicFactorVariableComputation(variable, ["old_factor"])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._on_add_msg("new_factor", Message("ADD", {0: 5, 1: 0}), None)

    assert computation.factors == ["old_factor", "new_factor"]
    assert computation._costs == {"new_factor": {0: 5, 1: 0}}
    assert computation.current_value == 1
    assert computation.current_cost == 0
    message_sender.assert_called_once_with(
        "x", "old_factor", MaxSumMessage({0: 2.5, 1: -2.5}), None, None
    )


def test_dynamic_variable_add_message_is_idempotent():
    variable = Variable("x", [0, 1])
    computation = DynamicFactorVariableComputation(variable, ["old_factor"])
    computation.message_sender = MagicMock()

    computation._on_add_msg("new_factor", Message("ADD", {0: 5, 1: 0}), None)
    computation._on_add_msg("new_factor", Message("ADD", {0: 2, 1: 0}), None)

    assert computation.factors == ["old_factor", "new_factor"]
    assert computation._costs == {"new_factor": {0: 2, 1: 0}}


def test_dynamic_variable_removes_factor_and_recomputes_remaining_messages():
    variable = Variable("x", [0, 1])
    computation = DynamicFactorVariableComputation(
        variable, ["old_factor", "removed_factor"]
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation._costs["old_factor"] = {0: 3, 1: 0}
    computation._costs["removed_factor"] = {0: 0, 1: 10}
    computation._prev_messages["old_factor"] = ({0: 1, 1: -1}, 1)

    msg_count, msg_size = computation._on_remove_msg(
        "removed_factor", Message("REMOVE", None), None
    )

    assert computation.factors == ["old_factor"]
    assert computation._costs == {"old_factor": {0: 3, 1: 0}}
    assert dict(computation._prev_messages) == {
        "old_factor": ({0: 0.0, 1: 0.0}, 1)
    }
    assert computation.current_value == 1
    assert computation.current_cost == 0
    assert msg_count == 1
    assert msg_size == 4
    message_sender.assert_called_once_with(
        "x", "old_factor", MaxSumMessage({0: 0.0, 1: 0.0}), None, None
    )


def test_dynamic_variable_remove_forgets_removed_factor_previous_message():
    variable = Variable("x", [0, 1])
    computation = DynamicFactorVariableComputation(
        variable, ["old_factor", "removed_factor"]
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation._costs["old_factor"] = {0: 3, 1: 0}
    computation._prev_messages["old_factor"] = ({0: 0.0, 1: 0.0}, SAME_COUNT)
    computation._prev_messages["removed_factor"] = ({0: 5, 1: -5}, 1)

    msg_count, msg_size = computation._on_remove_msg(
        "removed_factor", Message("REMOVE", None), None
    )

    assert computation.factors == ["old_factor"]
    assert computation._costs == {"old_factor": {0: 3, 1: 0}}
    assert dict(computation._prev_messages) == {
        "old_factor": ({0: 0.0, 1: 0.0}, SAME_COUNT)
    }
    assert msg_count == 0
    assert msg_size == 0
    message_sender.assert_not_called()


def test_change_function_wrong_dimensions_var():
    domain = list(range(10))
    x1 = Variable("x1", domain)
    x2 = Variable("x2", domain)
    x3 = Variable("x3", domain)

    @AsNAryFunctionRelation(x1, x2)
    def phi(x1_, x2_):
        return x1_ + x2_

    @AsNAryFunctionRelation(x1, x3)
    def phi2(x1_, x3_):
        return x1_ + x3_

    f = DynamicFunctionFactorComputation(comp_def=_factor_comp_def(phi))

    with pytest.raises(ValueError):
        f.change_factor_function(phi2)
