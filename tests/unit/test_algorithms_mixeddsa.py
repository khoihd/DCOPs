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

import numpy as np

from pydcop.algorithms import AlgorithmDef, ComputationDef
from pydcop.algorithms import mixeddsa
from pydcop.algorithms.mixeddsa import MixedDsaComputation
from pydcop.computations_graph.constraints_hypergraph import VariableComputationNode
from pydcop.dcop.objects import Variable, VariableWithCostDict
from pydcop.dcop.relations import AsNAryFunctionRelation, NAryMatrixRelation


def _comp_def(variable, constraints, mode="min", params=None):
    node = VariableComputationNode(variable, constraints)
    algo = AlgorithmDef.build_with_default_param(
        "mixeddsa", mode=mode, params=params
    )
    return ComputationDef(node, algo)


def test_build_computation_default_params():
    variable = Variable("v1", [0, 1, 2])
    comp_def = _comp_def(variable, [])

    computation = mixeddsa.build_computation(comp_def)

    assert isinstance(computation, MixedDsaComputation)
    assert computation.mode == "min"
    assert computation.variant == "B"
    assert computation.proba_hard == 0.7
    assert computation.proba_soft == 0.5
    assert computation.stop_cycle == 0


def test_computation_memory_uses_exact_variable_names():
    v1 = Variable("v1", [0, 1])
    v10 = Variable("v10", [0, 1])

    @AsNAryFunctionRelation(v1, v10)
    def c1(v1_, v10_):
        return 0 if v1_ == v10_ else 1

    v10_node = VariableComputationNode(v10, [c1])

    assert set(v10_node.neighbors) == {"v1"}
    assert mixeddsa.computation_memory(v10_node) == mixeddsa.UNIT_SIZE


def test_compute_dcop_cost_keeps_hard_violations_out_of_cost():
    v1 = VariableWithCostDict("v1", [0, 1], {0: 2, 1: 3})
    v2 = Variable("v2", [0, 1])

    @AsNAryFunctionRelation(v1, v2)
    def soft(v1_, v2_):
        return abs(v1_ - v2_)

    @AsNAryFunctionRelation(v1, v2)
    def hard(v1_, v2_):
        return mixeddsa.INFINITY if v1_ == v2_ else 0

    computation = MixedDsaComputation(
        v1, [soft, hard], comp_def=_comp_def(v1, [soft, hard])
    )

    cost, violated = computation._compute_dcop_cost({"v1": 0, "v2": 0})
    assert cost == 2
    assert violated == [hard]

    cost, violated = computation._compute_dcop_cost({"v1": 1, "v2": 0})
    assert cost == 4
    assert violated == []


def test_exists_violated_soft_constraint_supports_matrix_relation():
    v1 = Variable("v1", [0, 1])
    v2 = Variable("v2", [0, 1])
    soft = NAryMatrixRelation(
        [v1, v2], np.array([[0, 3], [2, 0]]), name="soft_matrix"
    )
    computation = MixedDsaComputation(v1, [soft], comp_def=_comp_def(v1, [soft]))

    assert computation.exists_violated_soft_constraint({"v1": 1, "v2": 0})
    assert not computation.exists_violated_soft_constraint({"v1": 1, "v2": 1})
