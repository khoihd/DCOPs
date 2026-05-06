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
import pytest

import pydcop.dcop.relations
from pydcop.algorithms import AlgorithmDef, ComputationDef, dpop
from pydcop.algorithms.dpop import DpopMessage
from pydcop.computations_graph.pseudotree import PseudoTreeLink, PseudoTreeNode
from pydcop.dcop.objects import Variable
from pydcop.dcop.relations import NAryMatrixRelation, AsNAryFunctionRelation


def test_communication_load_not_implemented():
    with pytest.raises(NotImplementedError, match="communication_load"):
        dpop.communication_load()


def test_computation_memory_root():
    variable = Variable("x0", ["a", "b"])
    node = PseudoTreeNode(
        variable, constraints=[], links=[PseudoTreeLink("children", "x0", "x1")]
    )

    assert dpop.computation_memory(node) == 2


def test_computation_memory_parent_separator():
    x0 = Variable("x0", ["a", "b"])
    x1 = Variable("x1", ["a", "b", "c"])
    relation = NAryMatrixRelation([x0, x1])
    node = PseudoTreeNode(
        x1, constraints=[relation], links=[PseudoTreeLink("parent", "x1", "x0")]
    )

    assert dpop.computation_memory(node) == 6


def test_computation_memory_parent_and_pseudo_parent_separator():
    x0 = Variable("x0", ["a", "b"])
    x1 = Variable("x1", ["a", "b", "c"])
    x2 = Variable("x2", ["a", "b", "c", "d", "e"])
    relation = NAryMatrixRelation([x0, x1, x2])
    node = PseudoTreeNode(
        x2,
        constraints=[relation],
        links=[
            PseudoTreeLink("parent", "x2", "x1"),
            PseudoTreeLink("pseudo_parent", "x2", "x0"),
        ],
    )

    assert dpop.computation_memory(node) == 30


def test_dpop_message_util_size():
    variable = Variable("x0", ["a", "b"])
    util = NAryMatrixRelation([variable], np.array([2, 4]))
    message = DpopMessage("UTIL", util)

    assert message.type == "UTIL"
    assert message.content == util
    assert message.size == 2
    assert str(message) == f"DpopMessage(UTIL, {util})"


def test_dpop_message_value_size():
    variable = Variable("x0", ["a", "b"])
    message = DpopMessage("VALUE", ([variable], ["b"]))

    assert message.type == "VALUE"
    assert message.content == ([variable], ["b"])
    assert message.size == 2


class DummySender(object):
    def __init__(self):
        self.util_sender_var = None
        self.util_dest_var = None
        self.util_msg_data = None
        self.value_sender_var = None
        self.value_dest_var = None
        self.value_msg_data = None

    def __call__(self, sender_var, dest_var, msg, prio=None, on_error=None):
        if msg.type == "UTIL":
            self.util_sender_var = sender_var
            self.util_dest_var = dest_var
            self.util_msg_data = msg.content
        elif msg.type == "VALUE":
            self.value_sender_var = sender_var
            self.value_dest_var = dest_var
            self.value_msg_data = msg.content


def dpop_computation_def(variable, constraints, links, mode="max"):
    node = PseudoTreeNode(variable, constraints, links)
    algo_def = AlgorithmDef.build_with_default_param("dpop", mode=mode)
    return ComputationDef(node, algo_def)


def test_constructor_filters_descendant_constraints_without_removing_from_copy():
    x0 = Variable("x0", ["a", "b"])
    x1 = Variable("x1", ["a", "b"])
    x2 = Variable("x2", ["a", "b"])
    x3 = Variable("x3", ["a", "b"])

    parent_relation = NAryMatrixRelation([x0, x1], name="parent_relation")
    own_relation = NAryMatrixRelation([x1], name="own_relation")
    child_relation = NAryMatrixRelation([x1, x2], name="child_relation")
    pseudo_child_relation = NAryMatrixRelation(
        [x1, x3], name="pseudo_child_relation"
    )

    computation = dpop.DpopAlgo(
        dpop_computation_def(
            x1,
            constraints=[
                parent_relation,
                child_relation,
                own_relation,
                pseudo_child_relation,
            ],
            links=[
                PseudoTreeLink("parent", x1.name, x0.name),
                PseudoTreeLink("children", x1.name, x2.name),
                PseudoTreeLink("pseudo_children", x1.name, x3.name),
            ],
        )
    )

    assert computation._constraints == [parent_relation, own_relation]


def test_value_message_preserves_child_separator_order():
    x0 = Variable("x0", [0, 1])
    x1 = Variable("x1", ["a", "b"])
    x2 = Variable("x2", ["child"])
    x3 = Variable("x3", [10, 20])
    x4 = Variable("x4", ["outside"])

    computation = dpop.DpopAlgo(
        dpop_computation_def(
            x1,
            constraints=[],
            links=[
                PseudoTreeLink("parent", x1.name, x0.name),
                PseudoTreeLink("children", x1.name, x2.name),
            ],
        )
    )
    sender = DummySender()
    computation.message_sender = sender
    computation._children_separator[x2.name] = [x3, x4, x0]
    matrix = np.zeros((2, 2, 2), dtype=np.float64)
    matrix[0, 0, 1] = 1
    matrix[0, 1, 1] = 5
    computation._joined_utils = NAryMatrixRelation([x0, x1, x3], matrix)

    msg = DpopMessage("VALUE", ([x0, x3], [0, 20]))
    computation._on_value_message(x0.name, msg, 0)

    assert sender.value_dest_var == x2.name
    assert sender.value_msg_data == ([x1, x3, x0], ["b", 20, 0])


class TestAlgoExampleTwoVars:
    """
    Test case with a very simplistic setup with only two vars and one relation
     a0 -> a1

    """

    def setup_method(self):
        self.x0 = Variable("x0", ["a", "b"])
        self.x1 = Variable("x1", ["a", "b"])

        self.r0_1 = NAryMatrixRelation([self.x0, self.x1], np.array([[1, 2], [4, 3]]))

        self.sender0 = DummySender()
        self.sender1 = DummySender()
        self.a0 = dpop.DpopAlgo(
            dpop_computation_def(
                self.x0,
                constraints=[],
                links=[PseudoTreeLink("children", self.x0.name, self.x1.name)],
            )
        )
        self.a1 = dpop.DpopAlgo(
            dpop_computation_def(
                self.x1,
                constraints=[self.r0_1],
                links=[PseudoTreeLink("parent", self.x1.name, self.x0.name)],
            )
        )

        self.a0.message_sender = self.sender0
        self.a1.message_sender = self.sender1

    def test_onstart_two_vars(self):
        # a0 is the root, must not send any message on start
        self.a0.on_start()
        assert self.a0.is_root
        assert not self.a0.is_leaf
        assert self.sender0.util_msg_data is None
        assert self.sender0.value_msg_data is None

        # a1 is the leaf, sends a util message
        self.a1.on_start()
        assert self.a1.is_leaf
        assert not self.a1.is_root

        assert self.sender1.util_sender_var == "x1"
        assert self.sender1.util_dest_var == "x0"
        assert self.sender1.util_msg_data.dimensions == [self.x0]
        assert self.sender1.util_msg_data("a") == 2
        assert self.sender1.util_msg_data("b") == 4

    def test_on_util_root_two_vars(self):
        # Testing that the root select the correct variable when receiving
        # the util message from its only child.

        self.a0.on_start()
        self.a1.on_start()

        u1_0 = NAryMatrixRelation([self.x0], np.array([2, 4]))
        msg = DpopMessage("UTIL", u1_0)
        self.a0._on_util_message(self.x1.name, msg, 0)

        # a0 id the root, when receiving UTIL message it must compute its own
        #  optimal value and send a value message
        msg = DpopMessage("VALUE", ([self.x0], ["b"]))
        assert self.sender0.value_sender_var == "x0"
        assert self.sender0.value_dest_var == "x1"
        assert self.sender0.value_msg_data == msg.content
        assert self.a0.current_value == "b"
        assert self.a0.current_cost == 4.0

    def test_value_leaf_two_vars(self):
        self.a0.on_start()
        self.a1.on_start()

        msg = DpopMessage("VALUE", ([self.x0], ["b"]))
        self.a1._on_value_message(self.x0.name, msg, 0)
        assert self.a1.current_value == "a"
        assert self.a1.current_cost == 4.0


class TestAlgoExampleThreeVars:
    """
    Test case with a very simplistic setup with only two vars and one relation
     a0 -> a1
        -> a2

    """

    def setup_method(self, method):
        self.x0 = Variable("x0", ["a", "b"])
        self.x1 = Variable("x1", ["a", "b"])
        self.x2 = Variable("x2", ["a", "b"])

        self.r0_1 = NAryMatrixRelation([self.x0, self.x1], np.array([[1, 2], [2, 3]]))
        self.r0_2 = NAryMatrixRelation([self.x0, self.x2], np.array([[5, 2], [3, 1]]))

        self.sender0 = DummySender()
        self.sender1 = DummySender()
        self.sender2 = DummySender()

        self.a0 = dpop.DpopAlgo(
            dpop_computation_def(
                self.x0,
                constraints=[],
                links=[
                    PseudoTreeLink("children", self.x0.name, self.x1.name),
                    PseudoTreeLink("children", self.x0.name, self.x2.name),
                ],
            )
        )
        self.a1 = dpop.DpopAlgo(
            dpop_computation_def(
                self.x1,
                constraints=[self.r0_1],
                links=[PseudoTreeLink("parent", self.x1.name, self.x0.name)],
            )
        )
        self.a2 = dpop.DpopAlgo(
            dpop_computation_def(
                self.x2,
                constraints=[self.r0_2],
                links=[PseudoTreeLink("parent", self.x2.name, self.x0.name)],
            )
        )

        self.a0.message_sender = self.sender0
        self.a1.message_sender = self.sender1
        self.a2.message_sender = self.sender2

    def test_on_start(self):
        # a0 is the root, must not send any message on start
        self.a0.on_start()
        assert self.a0.is_root
        assert not self.a0.is_leaf
        assert self.a0._waited_children == ["x1", "x2"]
        assert self.sender0.util_msg_data is None
        assert self.sender0.value_msg_data is None

        # a1 is a leaf, sends a util message
        self.a1.on_start()

        assert self.sender1.util_sender_var == "x1"
        assert self.sender1.util_dest_var == "x0"
        assert self.sender1.util_msg_data.dimensions == [self.x0]
        assert self.sender1.util_msg_data("a") == 2
        assert self.sender1.util_msg_data("b") == 3

        self.a2.on_start()

        assert self.sender2.util_sender_var == "x2"
        assert self.sender2.util_dest_var == "x0"
        assert self.sender2.util_msg_data.dimensions == [self.x0]
        assert self.sender2.util_msg_data("a") == 5
        assert self.sender2.util_msg_data("b") == 3

    def test_on_util_root_two_vars(self):
        # Testing that the root select the correct variable when receiving
        # the util message from its only child.

        self.a0.on_start()
        self.a1.on_start()

        u1_0 = NAryMatrixRelation([self.x0], np.array([2, 3]))
        msg = DpopMessage("UTIL", u1_0)
        self.a0._on_util_message(self.x1.name, msg, 0)

        # root only received one message, it should not send any message yet
        assert self.sender0.value_msg_data is None
        assert self.sender0.util_msg_data is None
        assert self.a0._waited_children == ["x2"]

        u2_0 = NAryMatrixRelation([self.x0], np.array([5, 3]))
        msg = DpopMessage("UTIL", u2_0)
        self.a0._on_util_message(self.x2.name, msg, 0)

        # a0 is the root, it has received UTIL message from all its children:
        #  it must compute its own optimal value
        assert self.sender0.value_msg_data == ([self.x0], ["a"])
        assert self.sender0.value_dest_var in {"x1", "x2"}
        assert self.a0.current_value == "a"
        assert self.a0.current_cost == 7.0

    def test_value_leaf_two_vars(self):
        self.a0.on_start()
        self.a1.on_start()
        self.a2.on_start()

        msg = DpopMessage("VALUE", ([self.x0], ["a"]))
        self.a1._on_value_message(self.x0.name, msg, 0)
        assert self.a1.current_value == "b"
        assert self.a1.current_cost == 2.0

        msg = DpopMessage("VALUE", ([self.x0], ["a"]))
        self.a2._on_value_message(self.x0.name, msg, 0)
        assert self.a2.current_value == "a"
        assert self.a2.current_cost == 5.0


class TestSmartLightSample:
    def test_4variables(self):
        l1 = Variable("l1", list(range(10)))
        l2 = Variable("l2", list(range(10)))
        l3 = Variable("l3", list(range(10)))
        y1 = Variable("y1", list(range(10)))

        @AsNAryFunctionRelation(l1, l2, l3, y1)
        def scene_rel(l1_, l2_, l3_, y1_):
            if y1_ == round((l1_ + l2_ + l3_) / 3):
                return 0
            return 10000

        @AsNAryFunctionRelation(l3)
        def cost_l3(l3_):
            return l3_

        assert scene_rel(9, 6, 0, 5) == 0

        assert scene_rel(3, 6, 0, 5) == 10000

        joined = pydcop.dcop.relations.join(scene_rel, cost_l3)

        assert joined(9, 6, 0, 5) == 0

        assert joined(3, 6, 0, 5) == 10000

        util = pydcop.dcop.relations.projection(joined, l3, "min")

        assert util.dimensions == [l1, l2, y1]
        assert util(l1=9, l2=6, y1=5) == 0
        assert util(l1=3, l2=6, y1=5) == 5
