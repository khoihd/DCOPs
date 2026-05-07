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


from unittest.mock import MagicMock

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms import adsa
from pydcop.algorithms.adsa import ADsaComputation, ADsaMessage
from pydcop.computations_graph.constraints_hypergraph import VariableComputationNode
from pydcop.dcop.objects import Variable, VariableWithCostFunc
from pydcop.dcop.relations import AsNAryFunctionRelation, constraint_from_str


def _computation(variable, constraints, params=None, mode="min"):
    node = VariableComputationNode(variable, constraints)
    comp_def = ComputationDef(
        node, AlgorithmDef.build_with_default_param("adsa", params, mode=mode)
    )
    return ADsaComputation(comp_def=comp_def)


def test_communication_load():
    v = Variable("v1", list(range(10)))
    var_node = VariableComputationNode(v, [])
    expected = adsa.UNIT_SIZE + adsa.HEADER_SIZE
    assert adsa.communication_load(var_node, "f1") == expected
    assert adsa.communication_load(var_node, "another_neighbor") == expected


def test_computation_memory_uses_exact_variable_names():
    v1 = Variable("v1", list(range(10)))
    v10 = Variable("v10", list(range(10)))
    c1 = constraint_from_str("c1", " v1 == v10", [v1, v10])
    v10_node = VariableComputationNode(v10, [c1])

    assert set(v10_node.neighbors) == {"v1"}
    assert adsa.computation_memory(v10_node) == adsa.UNIT_SIZE


def test_footprint_on_computation_object(monkeypatch):
    v1 = Variable("v1", [0, 1, 2, 3, 4])
    v2 = Variable("v2", [0, 1, 2, 3, 4])
    c1 = constraint_from_str("c1", "0 if v1 == v2 else 1", [v1, v2])
    computation = _computation(v1, [c1])

    monkeypatch.setattr(adsa, "UNIT_SIZE", 1)

    assert computation.footprint() == 1


def test_build_computation_default_params():
    v1 = Variable("v1", [0, 1, 2, 3, 4])
    computation = _computation(v1, [])

    assert computation.mode == "min"
    assert computation.variant == "B"
    assert computation.period == 0.5
    assert computation.probability == 0.7
    assert computation.constraints == []
    assert computation.current_assignment == {}
    assert computation.best_constraints_costs == {}


def test_adsa_message_properties():
    message = ADsaMessage(3)

    assert message.type == "adsa_value"
    assert message.value == 3
    assert message.size == 0
    assert str(message) == "adsa_value(value: 3)"
    assert repr(message) == "adsa_value(value: 3)"
    assert message == ADsaMessage(3)
    assert message != ADsaMessage(4)


def test_find_best_values_preserves_assignment():
    v1 = Variable("v1", [0, 1, 2, 3, 4])
    v2 = Variable("v2", [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2)
    def c1(v1_, v2_):
        return abs(v1_ - v2_)

    computation = _computation(v1, [c1])
    assignment = {"v2": 3}

    best_values, best_cost = computation.find_best_values(assignment)

    assert best_values == [3]
    assert best_cost == 0
    assert assignment == {"v2": 3}


def test_tick_waiting_for_neighbors_does_not_write_to_stdout(capsys):
    v1 = Variable("v1", [0, 1, 2, 3, 4])
    v2 = Variable("v2", [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2)
    def c1(v1_, v2_):
        return abs(v1_ - v2_)

    computation = _computation(v1, [c1])
    computation.message_sender = MagicMock()
    computation.value_selection(1)

    computation.tick()

    captured = capsys.readouterr()
    assert captured.out == ""


def test_delayed_start_selects_optimal_value_without_neighbors():
    v1 = VariableWithCostFunc("v1", [0, 1, 2], lambda value: abs(value - 2))
    computation = _computation(v1, [])
    computation._start_handle = object()
    computation.remove_periodic_action = MagicMock()
    computation.finished = MagicMock()
    computation.stop = MagicMock()

    computation.delayed_start()

    assert computation.current_value == 2
    assert computation.current_cost == 0


def test_tick_current_cost_includes_variable_cost():
    v1 = VariableWithCostFunc("v1", [0, 1, 2], lambda value: value * 10)
    v2 = Variable("v2", [0, 1, 2])

    @AsNAryFunctionRelation(v1, v2)
    def c1(v1_, v2_):
        return 0

    computation = _computation(v1, [c1], params={"variant": "A", "probability": 1.0})
    computation.message_sender = MagicMock()
    computation.current_assignment["v2"] = 0
    computation.value_selection(2)

    computation.tick()

    assert computation.current_value == 0
    assert computation.current_cost == 0


def test_exists_violated_constraint_can_reuse_full_assignment():
    v1 = Variable("v1", [0, 1, 2, 3, 4])
    v2 = Variable("v2", [0, 1, 2, 3, 4])

    @AsNAryFunctionRelation(v1, v2)
    def c1(v1_, v2_):
        return abs(v1_ - v2_)

    computation = _computation(v1, [c1], params={"variant": "B"})
    computation.current_assignment["v2"] = 1
    computation.value_selection(1)

    assert not computation.exists_violated_constraint()
    assert computation.exists_violated_constraint({"v1": 1, "v2": 0})
