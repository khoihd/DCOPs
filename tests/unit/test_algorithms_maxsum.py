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

from pydcop.algorithms import ComputationDef, AlgorithmDef
from pydcop.algorithms.maxsum import (
    MaxSumVariableComputation,
    MaxSumFactorComputation,
    build_computation,
    costs_for_factor,
    factor_costs_for_var,
    select_value,
)
from pydcop.computations_graph.factor_graph import build_computation_graph
from pydcop.dcop.objects import (
    Variable,
    Domain,
    VariableWithCostFunc,
)
from pydcop.dcop.relations import constraint_from_str


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


def test_costs_for_factor_normalizes_other_factor_costs():
    v1 = VariableWithCostFunc("v1", [0, 1], lambda v: v)
    costs = {"f1": {0: 10, 1: 30}, "f2": {0: 3, 1: 5}}

    obtained = costs_for_factor(v1, "f1", ["f1", "f2"], costs)

    assert obtained == {0: -1.0, 1: 2.0}
