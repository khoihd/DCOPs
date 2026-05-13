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

import json
from unittest.mock import MagicMock, call

import pytest

from pydcop.algorithms import ComputationDef, AlgorithmDef
from pydcop.algorithms.maxsum import (
    FACTOR_UNIT_SIZE,
    HEADER_SIZE,
    SAME_COUNT,
    UNIT_SIZE,
    VARIABLE_UNIT_SIZE,
    MaxSumVariableComputation,
    MaxSumFactorComputation,
    MaxSumMessage,
    approx_match,
    build_computation,
    communication_load,
    memory_footprint_estimate,
    costs_for_factor,
    factor_costs_for_var,
    select_value,
)
from pydcop.computations_graph.factor_graph import (
    FactorComputationNode,
    VariableComputationNode,
    build_computation_graph,
)
from pydcop.dcop.objects import (
    Variable,
    Domain,
    VariableDomain,
    VariableWithCostFunc,
)
from pydcop.dcop.relations import AsNAryFunctionRelation, constraint_from_str
from pydcop.dcop.relations import relation_from_str
from pydcop.utils.simple_repr import from_repr, simple_repr


def _algo_def(params=None, mode="min"):
    params = {} if params is None else dict(params)
    params.setdefault("noise", 0)
    return AlgorithmDef.build_with_default_param("maxsum", params=params, mode=mode)


def _factor_comp_def(factor, params=None, mode="min"):
    return ComputationDef(FactorComputationNode(factor), _algo_def(params, mode))


def _variable_comp_def(variable, factors, params=None, mode="min"):
    return ComputationDef(
        VariableComputationNode(variable, factors), _algo_def(params, mode)
    )


def _factor_computation(factor, params=None, mode="min"):
    return MaxSumFactorComputation(_factor_comp_def(factor, params, mode))


def _variable_computation(variable, factors, params=None, mode="min"):
    return MaxSumVariableComputation(
        _variable_comp_def(variable, factors, params, mode)
    )


def test_comp_creation():
    d = Domain("d", "", ["R", "G"])
    v1 = Variable("v1", d)
    v2 = Variable("v2", d)
    c1 = constraint_from_str("c1", "10 if v1 == v2 else 0", [v1, v2])
    graph = build_computation_graph(None, constraints=[c1], variables=[v1, v2])

    comp_node = graph.computation("c1")
    algo_def = AlgorithmDef.build_with_default_param("maxsum")
    comp_def = ComputationDef(comp_node, algo_def)

    comp = MaxSumFactorComputation(comp_def)
    assert comp is not None
    assert comp.name == "c1"
    assert comp.factor == c1

    comp_node = graph.computation("v1")
    algo_def = AlgorithmDef.build_with_default_param("maxsum")
    comp_def = ComputationDef(comp_node, algo_def)

    comp = MaxSumVariableComputation(comp_def)
    assert comp is not None
    assert comp.name == "v1"
    assert comp.variable.name == "v1"
    assert comp.factors == ["c1"]


def test_factor_computation_init_from_real_computation_def():
    x1 = Variable("x1", [0, 1])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def phi(x1_, x2_):
        return x1_ + x2_

    computation = _factor_computation(phi)

    assert computation.name == "phi"
    assert computation.mode == "min"
    assert computation.factor == phi
    assert computation.variables == [x1, x2]
    assert computation._costs == {}
    assert computation.damping == 0.5
    assert computation.damping_nodes == "both"
    assert computation.start_messages == "all"
    assert computation.stop_cycle == 0
    assert not computation.auto_stop
    assert computation.stable_cycles == 1


def test_variable_computation_init_from_real_computation_def():
    variable = Variable("v1", [0, 1])

    computation = _variable_computation(
        variable,
        ["f1", "f2"],
        params={
            "damping": 0.25,
            "damping_nodes": "vars",
            "stability": 0.2,
            "start_messages": "all",
            "stop_cycle": 3,
            "auto_stop": 1,
            "stable_cycles": 2,
        },
    )

    assert computation.name == "v1"
    assert computation.variable == variable
    assert computation.factors == ["f1", "f2"]
    assert computation.mode == "min"
    assert computation.damping == 0.25
    assert computation.damping_nodes == "vars"
    assert computation.stability_coef == 0.2
    assert computation.start_messages == "all"
    assert computation.stop_cycle == 3
    assert computation.auto_stop
    assert computation.stable_cycles == 2
    assert computation.costs == {}


def test_comp_creation_with_factory_method():
    d = Domain("d", "", ["R", "G"])
    v1 = Variable("v1", d)
    v2 = Variable("v2", d)
    c1 = constraint_from_str("c1", "10 if v1 == v2 else 0", [v1, v2])
    graph = build_computation_graph(None, constraints=[c1], variables=[v1, v2])

    comp_node = graph.computation("c1")
    algo_def = AlgorithmDef.build_with_default_param("maxsum")
    comp_def = ComputationDef(comp_node, algo_def)

    comp = build_computation(comp_def)
    assert comp is not None
    assert comp.name == "c1"
    assert comp.factor == c1

    comp_node = graph.computation("v1")
    algo_def = AlgorithmDef.build_with_default_param("maxsum")
    comp_def = ComputationDef(comp_node, algo_def)

    comp = build_computation(comp_def)
    assert comp is not None
    assert comp.name == "v1"
    assert comp.variable.name == "v1"
    assert comp.factors == ["c1"]


def test_compute_factor_cost_at_start():
    d = Domain("d", "", ["R", "G"])
    v1 = Variable("v1", d)
    v2 = Variable("v2", d)
    c1 = constraint_from_str("c1", "10 if v1 == v2 else 0", [v1, v2])

    obtained = factor_costs_for_var(c1, v1, {}, "min")
    assert obtained["R"] == 0
    assert obtained["G"] == 0
    assert len(obtained) == 2


def test_cost_for_unary_factor_in_min_mode():
    x1 = Variable("x1", [0, 1, 5])

    @AsNAryFunctionRelation(x1)
    def cost(x1_):
        return x1_ * 2

    computation = _factor_computation(cost, mode="min")

    costs = factor_costs_for_var(cost, x1, computation._costs, computation.mode)

    assert costs[0] == 0
    assert costs[5] == 10
    assert set(costs) == {0, 1, 5}


def test_cost_for_binary_factor_in_max_mode():
    x1 = Variable("x1", [0, 1, 2])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def cost(x1_, x2_):
        return abs(x1_ - x2_)

    computation = _factor_computation(cost, mode="max")

    costs = factor_costs_for_var(cost, x1, computation._costs, computation.mode)

    assert costs == {0: 1, 1: 1, 2: 2}


def test_cost_for_binary_factor_includes_received_costs_in_max_mode():
    x1 = Variable("x1", [0, 1, 2])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def cost(x1_, x2_):
        return x1_ - x2_

    computation = _factor_computation(cost, mode="max")
    computation._costs["x2"] = {0: -5, 1: 10}

    costs = factor_costs_for_var(cost, x1, computation._costs, computation.mode)

    assert costs == {0: 9, 1: 10, 2: 11}


def test_approx_match_accepts_small_relative_variations():
    assert approx_match({0: 10.0, 1: 20.0}, {0: 10.4, 1: 19.5}, 0.1)


def test_approx_match_rejects_missing_previous_costs():
    assert not approx_match({0: 0}, None, 0.1)


def test_approx_match_rejects_large_variations():
    assert not approx_match({0: 0, 1: 0, 2: 0}, {0: 0, 1: 1, 2: 0}, 0.1)


def test_approx_match_rejects_large_negative_to_zero_variations():
    c1 = {
        0: -46.0,
        1: -46.5,
        2: -55.5,
        3: -56.0,
        4: -56.5,
        5: -65.5,
        6: -66.0,
        7: -66.5,
        8: -67.0,
        9: -67.5,
    }
    c2 = dict.fromkeys(c1, 0.0)

    assert not approx_match(c1, c2, 0.1)


def test_factor_costs_for_ternary_factor_includes_received_costs_once():
    d = Domain("d", "", [0, 1])
    v1 = Variable("v1", d)
    v2 = Variable("v2", d)
    v3 = Variable("v3", d)
    c1 = constraint_from_str("c1", "v1 + v2 + v3", [v1, v2, v3])

    obtained = factor_costs_for_var(
        c1,
        v1,
        {"v2": {0: 3, 1: 0}, "v3": {0: 1, 1: 4}},
        "min",
    )

    assert obtained == {0: 2, 1: 3}


def test_select_value_no_cost_var():
    d = Domain("d", "", ["R", "G", "B"])
    v1 = Variable("v1", d)

    selected, cost = select_value(v1, {}, "min")
    assert selected in {"R", "G", "B"}
    assert cost == 0

    v1 = VariableWithCostFunc("v1", [1, 2, 3], lambda v: (4 - v) / 10)

    selected, cost = select_value(v1, {}, "min")
    assert selected == 3
    assert cost == 0.1


def test_select_value_max_mode_uses_cost_messages_and_variable_cost():
    v1 = VariableWithCostFunc("v1", [0, 1, 2], lambda v: v / 10)

    selected, cost = select_value(
        v1, {"f1": {0: 4, 1: 2, 2: 1}, "f2": {0: 0, 1: 5, 2: 1}}, "max"
    )

    assert selected == 1
    assert cost == 7.1


def test_costs_for_factor_normalizes_complete_message():
    v1 = VariableWithCostFunc("v1", [0, 1], lambda v: v)
    costs = {"f1": {0: 10, 1: 30}, "f2": {0: 3, 1: 5}}

    obtained = costs_for_factor(v1, "f1", ["f1", "f2"], costs)

    assert obtained == {0: -1.5, 1: 1.5}
    assert sum(obtained.values()) == 0


def test_variable_memory_no_neighbor():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2, 3, 5]))
    vn1 = VariableComputationNode(v1, [])

    assert memory_footprint_estimate(vn1) == 0


def test_variable_memory_one_neighbor():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2, 3, 5]))
    cv1 = VariableComputationNode(v1, ["f1"])

    assert memory_footprint_estimate(cv1) == VARIABLE_UNIT_SIZE * 4


def test_factor_memory_two_neighbors():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2, 3, 4, 5]))
    v2 = Variable("v2", VariableDomain("d2", "", [1, 2, 3]))
    f1 = relation_from_str("f1", "v1 * 0.5 + v2", [v1, v2])
    cf1 = FactorComputationNode(f1)

    assert memory_footprint_estimate(cf1) == FACTOR_UNIT_SIZE * (5 + 3)


def test_communication_load_from_variable_uses_variable_domain_size():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2, 3, 5]))
    cv1 = VariableComputationNode(v1, ["f1"])

    assert communication_load(cv1, "f1") == HEADER_SIZE + UNIT_SIZE * len(v1.domain)


def test_communication_load_from_factor_uses_target_variable_domain_size():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2, 3, 5]))
    v2 = Variable("v2", VariableDomain("d2", "", [1, 2]))
    f1 = relation_from_str("f1", "v1 * 0.5 + v2", [v1, v2])
    cf1 = FactorComputationNode(f1)

    assert communication_load(cf1, "v1") == HEADER_SIZE + UNIT_SIZE * 4
    assert communication_load(cf1, "v2") == HEADER_SIZE + UNIT_SIZE * 2


def test_communication_load_from_factor_rejects_unknown_target():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2, 3, 5]))
    f1 = relation_from_str("f1", "v1 * 0.5", [v1])
    cf1 = FactorComputationNode(f1)

    with pytest.raises(ValueError, match="Could not find variable"):
        communication_load(cf1, "unknown")


def test_communication_load_rejects_invalid_computation_node():
    with pytest.raises(ValueError, match="maxsum communication_load only supports"):
        communication_load(object(), "f1")


def test_maxsum_message_properties():
    message = MaxSumMessage({1: 10, 2: 20})

    assert message.type == "max_sum"
    assert message.costs == {1: 10, 2: 20}
    assert message.size == 4
    assert str(message) == "MaxSumMessage({1: 10, 2: 20})"
    assert repr(message) == "MaxSumMessage({1: 10, 2: 20})"
    assert message == MaxSumMessage({1: 10, 2: 20})
    assert message != MaxSumMessage({1: 10, 2: 21})
    assert message != object()


def test_maxsum_message_serializes_integer_keys():
    msg = MaxSumMessage({1: 10, 2: 20})
    msg_json = json.dumps(simple_repr(msg))

    msg2 = from_repr(json.loads(msg_json))

    assert msg == msg2


def test_unary_factor_sends_initial_message_when_leaf_start_messages_enabled():
    v1 = Variable("v1", VariableDomain("d1", "", [1, 2]))
    f1 = relation_from_str("f1", "v1 * 0.5", [v1])
    computation = _factor_computation(f1, params={"start_messages": "leafs"})
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    message_sender.assert_called_once_with(
        "f1", "v1", MaxSumMessage({1: 0.5, 2: 1.0}), None, None
    )


def test_binary_factor_sends_initial_messages_to_all_variables_when_configured():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(f1, params={"start_messages": "all"})
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    expected_message = MaxSumMessage({0: 0, 1: 0})
    message_sender.assert_has_calls(
        [
            call("f1", "v1", expected_message, None, None),
            call("f1", "v2", expected_message, None, None),
        ],
        any_order=True,
    )
    assert message_sender.call_count == 2


def test_factor_cycle_sends_costs_to_all_variables():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(f1)
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    expected_message = MaxSumMessage({0: 0, 1: 0})
    message_sender.assert_has_calls(
        [
            call("f1", "v1", expected_message, None, None),
            call("f1", "v2", expected_message, None, None),
        ],
        any_order=True,
    )
    assert message_sender.call_count == 2
    assert computation._costs == {"v2": {0: 0, 1: 0}}
    assert computation._prev_messages["v1"] == ({0: 0, 1: 0}, 1)
    assert computation._prev_messages["v2"] == ({0: 0, 1: 0}, 1)


def test_factor_cycle_applies_damping_before_sending_message():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "v1 + v2", [v1, v2])
    computation = _factor_computation(
        f1, params={"damping": 0.5, "damping_nodes": "factors"}
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation._prev_messages["v1"] = ({0: 2, 1: 2}, 1)
    computation._prev_messages["v2"] = ({0: 0, 1: 0}, SAME_COUNT)

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    message_sender.assert_has_calls(
        [
            call("f1", "v1", MaxSumMessage({0: 1.0, 1: 1.5}), None, None),
            call("f1", "v2", MaxSumMessage({0: 0.0, 1: 0.5}), None, None),
        ],
        any_order=True,
    )
    assert message_sender.call_count == 2
    assert computation._prev_messages["v1"] == ({0: 1.0, 1: 1.5}, 1)


def test_factor_cycle_suppresses_stable_message_after_same_count():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(f1)
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation._prev_messages["v1"] = ({0: 0, 1: 0}, SAME_COUNT)
    computation._prev_messages["v2"] = ({0: 0, 1: 0}, SAME_COUNT)

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    message_sender.assert_not_called()


def test_factor_auto_stops_after_stable_cycle():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(f1, params={"auto_stop": 1})
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.finished = MagicMock()
    computation.start()
    message_sender.reset_mock()
    computation._prev_messages["v1"] = ({0: 0, 1: 0}, SAME_COUNT)
    computation._prev_messages["v2"] = ({0: 0, 1: 0}, SAME_COUNT)

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    assert computation.is_running
    assert computation._stable_cycle_count == 1
    computation.finished.assert_called_once_with()
    message_sender.assert_not_called()


def test_factor_auto_stop_waits_for_configured_stable_cycles():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(
        f1, params={"auto_stop": 1, "stable_cycles": 2}
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.finished = MagicMock()
    computation.start()
    message_sender.reset_mock()
    computation._prev_messages["v1"] = ({0: 0, 1: 0}, SAME_COUNT)
    computation._prev_messages["v2"] = ({0: 0, 1: 0}, SAME_COUNT)

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    assert computation.is_running
    assert computation._stable_cycle_count == 1
    computation.finished.assert_not_called()

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 2)

    assert computation.is_running
    assert computation._stable_cycle_count == 2
    computation.finished.assert_called_once_with()


def test_variable_sends_initial_leaf_message_on_start():
    variable = Variable("v1", [0, 1], initial_value=1)
    computation = _variable_computation(variable, ["f1"])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value == 1
    message_sender.assert_called_once_with(
        "v1", "f1", MaxSumMessage({0: 0.0, 1: 0.0}), None, None
    )


def test_variable_sends_integrated_costs_on_start():
    variable = VariableWithCostFunc("v1", [0, 1, 2], lambda value: value * 2)
    computation = _variable_computation(variable, ["f1"])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value == 0
    assert computation.current_cost == 0
    message_sender.assert_called_once_with(
        "v1", "f1", MaxSumMessage({0: -2.0, 1: 0.0, 2: 2.0}), None, None
    )


def test_variable_cycle_selects_value_and_sends_costs_to_all_factors():
    variable = VariableWithCostFunc("v1", [0, 1], lambda value: value * 2)
    computation = _variable_computation(variable, ["f1", "f2"])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.on_new_cycle({"f1": (MaxSumMessage({0: 5, 1: 0}), 0)}, 1)

    assert computation.costs == {"f1": {0: 5, 1: 0}}
    assert computation.current_value == 1
    assert computation.current_cost == 2
    message_sender.assert_has_calls(
        [
            call("v1", "f1", MaxSumMessage({0: -1.0, 1: 1.0}), None, None),
            call("v1", "f2", MaxSumMessage({0: 1.5, 1: -1.5}), None, None),
        ],
        any_order=True,
    )
    assert message_sender.call_count == 2


def test_variable_cycle_applies_damping_before_sending_message():
    variable = Variable("v1", [0, 1])
    computation = _variable_computation(
        variable, ["f1", "f2"], params={"damping": 0.5, "damping_nodes": "vars"}
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation._prev_messages["f1"] = ({0: 0, 1: 0}, SAME_COUNT)
    computation._prev_messages["f2"] = ({0: 2, 1: 2}, 1)

    computation.on_new_cycle({"f1": (MaxSumMessage({0: 4, 1: 0}), 0)}, 1)

    message_sender.assert_called_once_with(
        "v1", "f2", MaxSumMessage({0: 2.0, 1: 0.0}), None, None
    )
    assert computation._prev_messages["f2"] == ({0: 2.0, 1: 0.0}, 1)


def test_factor_stops_at_stop_cycle_before_sending_next_messages():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(f1, params={"stop_cycle": 1})
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.start()
    message_sender.reset_mock()

    computation.on_new_cycle({"v2": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    assert not computation.is_running
    message_sender.assert_not_called()


def test_variable_stops_at_stop_cycle_after_selecting_final_value():
    variable = Variable("v1", [0, 1])
    computation = _variable_computation(
        variable, ["f1", "f2"], params={"stop_cycle": 1}
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.start()
    message_sender.reset_mock()

    computation.on_new_cycle({"f1": (MaxSumMessage({0: 5, 1: 0}), 0)}, 1)

    assert computation.current_value == 1
    assert not computation.is_running
    message_sender.assert_not_called()


def test_variable_cycle_suppresses_stable_message_after_same_count():
    variable = Variable("v1", [0, 1])
    computation = _variable_computation(variable, ["f1", "f2"])
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation._prev_messages["f1"] = ({0: 0.0, 1: 0.0}, SAME_COUNT)
    computation._prev_messages["f2"] = ({0: 0.0, 1: 0.0}, SAME_COUNT)

    computation.on_new_cycle({"f1": (MaxSumMessage({0: 0, 1: 0}), 0)}, 1)

    message_sender.assert_not_called()


def test_variable_auto_stop_requires_stable_selected_value():
    variable = Variable("v1", [0, 1])
    computation = _variable_computation(variable, ["f1"], params={"auto_stop": 1})
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.finished = MagicMock()
    computation.start()
    message_sender.reset_mock()
    computation._prev_messages["f1"] = ({0: 0.0, 1: 0.0}, SAME_COUNT)

    computation.on_new_cycle({"f1": (MaxSumMessage({0: 5, 1: 0}), 0)}, 1)

    assert computation.is_running
    assert computation.current_value == 1
    assert computation._stable_cycle_count == 0
    computation.finished.assert_not_called()

    computation.on_new_cycle({"f1": (MaxSumMessage({0: 5, 1: 0}), 0)}, 2)

    assert computation.is_running
    assert computation.current_value == 1
    assert computation._stable_cycle_count == 1
    computation.finished.assert_called_once_with()
    message_sender.assert_not_called()
