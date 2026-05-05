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

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms.amaxsum import (
    MaxSumFactorComputation,
    MaxSumVariableComputation,
    build_computation,
    communication_load,
    computation_memory,
)
from pydcop.algorithms.maxsum import (
    FACTOR_UNIT_SIZE,
    HEADER_SIZE,
    MaxSumMessage,
    UNIT_SIZE,
    VARIABLE_UNIT_SIZE,
    approx_match,
    factor_costs_for_var,
)
from pydcop.computations_graph.factor_graph import (
    FactorComputationNode,
    VariableComputationNode,
    build_computation_graph,
)
from pydcop.dcop.objects import Variable, VariableDomain
from pydcop.dcop.relations import AsNAryFunctionRelation, relation_from_str
from pydcop.utils.simple_repr import from_repr, simple_repr


def _algo_def(params=None, mode="min"):
    params = {} if params is None else dict(params)
    # Disable default noise in unit tests that inspect variable behavior.
    params.setdefault("noise", 0)
    return AlgorithmDef.build_with_default_param(
        "amaxsum", params=params, mode=mode
    )


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


def test_factor_computation_init_from_real_computation_def():
    domain = [0, 1]
    x1 = Variable("x1", domain)
    x2 = Variable("x2", domain)

    @AsNAryFunctionRelation(x1, x2)
    def phi(x1_, x2_):
        return x1_ + x2_

    f = _factor_computation(phi)

    assert f.name == "phi"
    assert f.mode == "min"
    assert f.factor == phi
    assert f.variables == [x1, x2]
    assert f._costs == {}
    assert f.damping == 0.5
    assert f.damping_nodes == "both"
    assert f.start_messages == "leafs"


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
        },
    )

    assert computation.name == "v1"
    assert computation.variable == variable
    assert computation._factors == ["f1", "f2"]
    assert computation.mode == "min"
    assert computation.damping == 0.25
    assert computation.damping_nodes == "vars"
    assert computation.stability_coef == 0.2
    assert computation.start_messages == "all"
    assert computation._costs == {}


def test_build_computation_factory_creates_factor_and_variable_computations():
    domain = VariableDomain("color", "color", ["R", "G"])
    v1 = Variable("v1", domain)
    v2 = Variable("v2", domain)
    c1 = relation_from_str("c1", "10 if v1 == v2 else 0", [v1, v2])
    graph = build_computation_graph(None, constraints=[c1], variables=[v1, v2])

    factor = build_computation(
        ComputationDef(graph.computation("c1"), _algo_def())
    )
    variable = build_computation(
        ComputationDef(graph.computation("v1"), _algo_def())
    )

    assert isinstance(factor, MaxSumFactorComputation)
    assert factor.name == "c1"
    assert factor.factor == c1
    assert isinstance(variable, MaxSumVariableComputation)
    assert variable.name == "v1"
    assert variable.variable == v1
    assert variable._factors == ["c1"]


def test_cost_for_unary_factor_in_min_mode():
    domain = [0, 1, 5]
    x1 = Variable("x1", domain)

    @AsNAryFunctionRelation(x1)
    def cost(x1_):
        return x1_ * 2

    f = _factor_computation(cost, mode="min")

    costs = factor_costs_for_var(cost, x1, f._costs, f.mode)

    # in the max-sum algorithm, for an unary factor the costs is simply
    # the result of the factor function
    assert costs[0] == 0
    assert costs[5] == 10
    assert set(costs) == {0, 1, 5}


def test_cost_for_unary_factor_in_max_mode():
    domain = [0, 1, 5]
    x1 = Variable("x1", domain)

    @AsNAryFunctionRelation(x1)
    def cost(x1_):
        return x1_ * 2

    f = _factor_computation(cost, mode="max")

    costs = factor_costs_for_var(cost, x1, f._costs, f.mode)

    # in the max-sum algorithm, for an unary factor the costs is simply
    # the result of the factor function
    assert costs[0] == 0
    assert costs[5] == 10
    assert set(costs) == {0, 1, 5}


def test_cost_for_binary_factor_in_min_mode():
    x1 = Variable("x1", [0, 1, 2])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def cost(x1_, x2_):
        return abs(x1_ - x2_)

    f = _factor_computation(cost, mode="min")

    costs = factor_costs_for_var(cost, x1, f._costs, f.mode)

    # in this test, the factor did not receive any costs messages from
    # other variables, this means it  only uses the factor function when
    # calculating costs.

    # x1 = 2, best value for x2 is 1, with cost = 1
    assert costs == {0: 0, 1: 0, 2: 1}


def test_cost_for_binary_factor_in_max_mode():
    x1 = Variable("x1", [0, 1, 2])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def cost(x1_, x2_):
        return abs(x1_ - x2_)

    f = _factor_computation(cost, mode="max")

    costs = factor_costs_for_var(cost, x1, f._costs, f.mode)

    assert costs == {0: 1, 1: 1, 2: 2}


def test_cost_for_binary_factor_includes_received_costs():
    x1 = Variable("x1", [0, 1, 2])
    x2 = Variable("x2", [0, 1])

    @AsNAryFunctionRelation(x1, x2)
    def cost(x1_, x2_):
        return x1_ + x2_

    f = _factor_computation(cost, mode="min")
    f._costs["x2"] = {0: 5, 1: -1}

    costs = factor_costs_for_var(cost, x1, f._costs, f.mode)

    assert costs == {0: 0, 1: 1, 2: 2}


def test_approx_match_exact_costs():
    c1 = {0: 0, 1: 0, 2: 0}
    c2 = {0: 0, 1: 0, 2: 0}

    assert approx_match(c1, c2, 0.1)


def test_approx_match_accepts_small_relative_variations():
    c1 = {0: 10.0, 1: 20.0}
    c2 = {0: 10.4, 1: 19.5}

    assert approx_match(c1, c2, 0.1)


def test_approx_match_rejects_missing_previous_costs():
    assert not approx_match({0: 0}, None, 0.1)


def test_approx_match_rejects_large_variations():
    c1 = {0: 0, 1: 0, 2: 0}
    c2 = {0: 0, 1: 1, 2: 0}

    assert not approx_match(c1, c2, 0.1)


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
    c2 = {
        0: 0.0,
        1: 0.0,
        2: 0.0,
        3: 0.0,
        4: 0.0,
        5: 0.0,
        6: 0.0,
        7: 0.0,
        8: 0.0,
        9: 0.0,
    }

    assert not approx_match(c1, c2, 0.1)


def test_variable_memory_no_neighbor():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)

    vn1 = VariableComputationNode(v1, [])

    # If a variable has no neighbors, it does not need to keep any cost
    # and thus requires no memory
    assert computation_memory(vn1) == 0


def test_variable_memory_one_neighbor():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)
    cv1 = VariableComputationNode(v1, ["f1"])

    assert computation_memory(cv1) == VARIABLE_UNIT_SIZE * 4


def test_factor_memory_one_neighbor():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)
    f1 = relation_from_str("f1", "v1 * 0.5", [v1])
    cf1 = FactorComputationNode(f1)

    assert computation_memory(cf1) == FACTOR_UNIT_SIZE * 4


def test_factor_memory_two_neighbors():
    d1 = VariableDomain("d1", "", [1, 2, 3, 4, 5])
    v1 = Variable("v1", d1)
    d2 = VariableDomain("d2", "", [1, 2, 3])
    v2 = Variable("v2", d2)
    f1 = relation_from_str("f1", "v1 * 0.5 + v2", [v1, v2])
    cf1 = FactorComputationNode(f1)

    assert computation_memory(cf1) == FACTOR_UNIT_SIZE * (5 + 3)


def test_variable_memory_two_neighbors():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)
    cv1 = VariableComputationNode(v1, ["f1", "f2"])

    assert computation_memory(cv1) == VARIABLE_UNIT_SIZE * 4 * 2


def test_communication_load_from_variable_uses_variable_domain_size():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)
    cv1 = VariableComputationNode(v1, ["f1"])

    assert communication_load(cv1, "f1") == HEADER_SIZE + UNIT_SIZE * len(v1.domain)


def test_communication_load_from_factor_uses_target_variable_domain_size():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)
    d2 = VariableDomain("d2", "", [1, 2])
    v2 = Variable("v2", d2)
    f1 = relation_from_str("f1", "v1 * 0.5 + v2", [v1, v2])
    cf1 = FactorComputationNode(f1)

    assert communication_load(cf1, "v1") == HEADER_SIZE + UNIT_SIZE * 4
    assert communication_load(cf1, "v2") == HEADER_SIZE + UNIT_SIZE * 2


def test_communication_load_from_factor_rejects_unknown_target():
    d1 = VariableDomain("d1", "", [1, 2, 3, 5])
    v1 = Variable("v1", d1)
    f1 = relation_from_str("f1", "v1 * 0.5", [v1])
    cf1 = FactorComputationNode(f1)

    with pytest.raises(ValueError, match="Could not find variable"):
        communication_load(cf1, "unknown")


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
    # Make sure that even after serialization / deserialization, from_repr and
    # simple_repr still produce equal messages. This has been causing problems
    # with maxsum costs dict where keys were integers.
    msg = MaxSumMessage({1: 10, 2: 20})
    r = simple_repr(msg)
    msg_json = json.dumps(r)

    r2 = json.loads(msg_json)
    msg2 = from_repr(r2)

    assert msg == msg2


def test_unary_factor_sends_initial_message_when_leaf_start_messages_enabled():
    d1 = VariableDomain("d1", "", [1, 2])
    v1 = Variable("v1", d1)
    f1 = relation_from_str("f1", "v1 * 0.5", [v1])
    computation = _factor_computation(f1)
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    message_sender.assert_called_once_with(
        "f1", "v1", MaxSumMessage({1: 0.5, 2: 1.0}), None, None
    )


def test_binary_factor_waits_for_all_variable_costs_before_sending():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    f1 = relation_from_str("f1", "abs(v1 - v2)", [v1, v2])
    computation = _factor_computation(f1)
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation._on_maxsum_msg("v1", MaxSumMessage({0: 0, 1: 0}), None)

    message_sender.assert_not_called()

    computation._on_maxsum_msg("v2", MaxSumMessage({0: 0, 1: 0}), None)

    message_sender.assert_called_once_with(
        "f1", "v1", MaxSumMessage({0: 0, 1: 0}), None, None
    )
    assert computation._prev_messages["v1"] == ({0: 0, 1: 0}, 1)


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


def test_variable_sends_initial_messages_to_all_factors_when_configured():
    variable = Variable("v1", [0, 1], initial_value=0)
    computation = _variable_computation(
        variable, ["f1", "f2"], params={"start_messages": "all"}
    )
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    expected_message = MaxSumMessage({0: 0.0, 1: 0.0})
    message_sender.assert_has_calls(
        [
            call("v1", "f1", expected_message, None, None),
            call("v1", "f2", expected_message, None, None),
        ],
        any_order=True,
    )
    assert message_sender.call_count == 2
