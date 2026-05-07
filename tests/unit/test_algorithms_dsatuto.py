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
from pydcop.algorithms.dsatuto import DsaMessage, DsaTutoComputation
from pydcop.computations_graph.constraints_hypergraph import VariableComputationNode
from pydcop.dcop.objects import Variable
from pydcop.dcop.relations import constraint_from_str


def _computation(variable, constraints=None, mode="min"):
    constraints = [] if constraints is None else constraints
    comp_def = ComputationDef(
        VariableComputationNode(variable, constraints),
        AlgorithmDef.build_with_default_param("dsatuto", mode=mode),
    )
    return DsaTutoComputation(comp_def)


def _cycle_message(value, cycle_id=0):
    message = DsaMessage(value)
    message.cycle_id = cycle_id
    return message


def test_build_computation_default_params():
    v1 = Variable("v1", [0, 1])
    computation = _computation(v1)

    assert computation.variable == v1
    assert computation.mode == "min"
    assert computation.constraints == []


def test_dsa_tuto_message_properties():
    message = DsaMessage("red")

    assert message.type == "dsa_value"
    assert message.value == "red"
    assert message.size == 0
    assert str(message) == "dsa_value(value: red)"
    assert repr(message) == "dsa_value(value: red)"
    assert message == DsaMessage("red")
    assert message != DsaMessage("blue")


def test_select_and_send_random_value_when_starting():
    v1 = Variable("v1", [0, 1, 2])
    v2 = Variable("v2", [0, 1, 2])
    c1 = constraint_from_str("c1", "abs(v1 - v2)", [v1, v2])
    computation = _computation(v1, [c1])
    message_sender = MagicMock()
    computation.message_sender = message_sender

    computation.start()

    assert computation.current_value in v1.domain
    expected_message = _cycle_message(computation.current_value)
    message_sender.assert_called_once_with(
        "v1", "v2", expected_message, None, None
    )


def test_on_new_cycle_selects_better_value_in_min_mode(monkeypatch):
    v1 = Variable("v1", [0, 1, 2])
    v2 = Variable("v2", [0, 1, 2])
    c1 = constraint_from_str("c1", "abs(v1 - v2)", [v1, v2])
    computation = _computation(v1, [c1])
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.value_selection(2)
    monkeypatch.setattr("pydcop.algorithms.dsatuto.random.random", lambda: 0.0)

    computation.on_new_cycle({"v2": (DsaMessage(0), None)}, 0)

    assert computation.current_value == 0
    assert computation.current_cost == 0
    message_sender.assert_called_once_with(
        "v1", "v2", _cycle_message(0), None, None
    )


def test_on_new_cycle_selects_better_value_in_max_mode(monkeypatch):
    v1 = Variable("v1", [0, 1, 2])
    v2 = Variable("v2", [0, 1, 2])
    c1 = constraint_from_str("c1", "v1 + v2", [v1, v2])
    computation = _computation(v1, [c1], mode="max")
    message_sender = MagicMock()
    computation.message_sender = message_sender
    computation.value_selection(0)
    monkeypatch.setattr("pydcop.algorithms.dsatuto.random.random", lambda: 0.0)

    computation.on_new_cycle({"v2": (DsaMessage(0), None)}, 0)

    assert computation.current_value == 2
    assert computation.current_cost == 2
    message_sender.assert_called_once_with(
        "v1", "v2", _cycle_message(2), None, None
    )
