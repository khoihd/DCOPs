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


import pytest

from pydcop.computations_graph.objects import ComputationGraph, ComputationNode, Link
from pydcop.utils.simple_repr import from_repr, simple_repr


def test_node_creation_minimal():
    # name is the only mandatory param:
    n = ComputationNode('n1')
    assert n.name == 'n1'
    assert not n.type
    assert not n.links
    assert not n.neighbors
    assert repr(n) == 'ComputationNode(n1)'


def test_node_creation_with_links():

    link = Link(['n1', 'n2'])
    n1 = ComputationNode('n1', node_type='test', links=[link])

    assert n1.type == 'test'
    assert n1.neighbors == ['n2']
    assert n1.links == [link]
    assert n1.links[0].has_node('n2')
    assert repr(n1) == 'ComputationNode(n1, test)'


def test_node_creation_with_hyperlinks():

    links = [Link(['n1', 'n2', 'n3']), Link(['n1', 'n4'])]
    n1 = ComputationNode('n1', links=links)

    assert set(n1.neighbors) == {'n2', 'n3', 'n4'}
    assert n1.links == links


def test_node_creation_with_one_neighbor():

    n1 = ComputationNode('n1', neighbors=['n2'])

    assert n1.neighbors == ['n2']
    assert len(n1.links) == 1
    assert n1.links[0] == Link(['n1', 'n2'])


def test_node_creation_with_several_neighbors():

    n1 = ComputationNode('n1', neighbors=['n2', 'n3', 'n4'])

    assert n1.neighbors == ['n2', 'n3', 'n4']
    assert len(n1.links) == 3
    assert set(n1.links) == {
        Link(['n1', 'n2']),
        Link(['n1', 'n3']),
        Link(['n1', 'n4']),
    }


def test_node_creation_raises_when_giving_links_neighbors():

    with pytest.raises(ValueError):
        ComputationNode('n1', links=[Link(['n2'])], neighbors=['n2'])


def test_node_simplerepr():
    n1 = ComputationNode('n1', 'test', neighbors=['n2', 'n3', 'n4'])

    r1 = simple_repr(n1)
    obtained = from_repr(r1)

    assert r1['__module__'] == 'pydcop.computations_graph.objects'
    assert r1['__qualname__'] == 'ComputationNode'
    assert r1['name'] == 'n1'
    assert r1['node_type'] == 'test'
    assert 'neighbors' not in r1
    assert set(from_repr(r1['links'])) == {
        Link(['n1', 'n2']),
        Link(['n1', 'n3']),
        Link(['n1', 'n4']),
    }
    assert n1 == obtained
    assert set(obtained.neighbors) == {'n2', 'n3', 'n4'}
    assert set(obtained.links) == set(n1.links)


def test_link_creation_and_simple_repr():
    link = Link(['n1', 'n2'], link_type='neighbor')

    r = simple_repr(link)
    obtained = from_repr(r)

    assert link.type == 'neighbor'
    assert link.nodes == frozenset({'n1', 'n2'})
    assert link.has_node('n1')
    assert not link.has_node('n3')
    assert repr(link).startswith('Link(neighbor, frozenset({')
    assert r['link_type'] == 'neighbor'
    assert set(r['nodes']) == {'n1', 'n2'}
    assert obtained == link


def test_computation_graph_accessors():
    n1 = ComputationNode('n1', neighbors=['n2'])
    n2 = ComputationNode('n2', neighbors=['n1'])
    graph = ComputationGraph('test', nodes=[n1, n2])

    assert graph.type == 'test'
    assert graph.nodes == [n1, n2]
    assert graph.node_names() == ['n1', 'n2']
    assert graph.computation('n1') is n1
    assert graph.links == {Link(['n1', 'n2'])}
    assert graph.links_for_node('n1') == n1.links
    assert graph.neighbors('n1') == ['n2']


def test_computation_graph_accessors_raise_for_unknown_node():
    graph = ComputationGraph(nodes=[ComputationNode('n1')])

    with pytest.raises(KeyError, match='no computation named missing found'):
        graph.computation('missing')
    with pytest.raises(KeyError, match='No node named missing'):
        graph.links_for_node('missing')
    with pytest.raises(KeyError, match='No node named missing'):
        graph.neighbors('missing')


def test_base_computation_graph_density_is_abstract():
    graph = ComputationGraph()

    with pytest.raises(NotImplementedError, match='Abstract class'):
        graph.density()
