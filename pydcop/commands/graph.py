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

"""
.. _pydcop_commands_graph:

pydcop graph
============

``pydcop graph`` outputs some metrics for a graph model for a DCOP.

Synopsis
--------
::

  pydcop graph --graph <graph_model> <dcop_files>


Description
-----------

Outputs some metrics for a graph model for a DCOP:

* constraints_count
* variables_count
* density
* edges_count
* nodes_count
* is_connected
* components_count
* diameter
* cycles_count
* max_degree
* average_degree


Options
-------

``--graph <graph_model>`` / ``-g <graph_model>``
  The computation graph model,
  one of ``factor_graph``, ``pseudotree``, ``constraints_hypergraph``
  (see. :ref:`concepts_graph`)
  The set of computation to distribute depends on the graph model used to
  represent the DCOP.

``--display``
  Display a graphical representation of the constraints graph using
  networkx and matplotlib.

``<dcop-files>``
  One or several paths to the files containing the dcop. If several paths are
  given, their content is concatenated as used a the yaml definition for the
  DCOP.


Example
-------

::

  pydcop graph --graph factor_graph graph_coloring1.yaml

Example output::

  constraints_count: 2
  density: 0.4
  edges_count: 4
  nodes_count: 5
  status: OK
  variables_count: 3



"""

from collections import Counter, deque
from itertools import combinations
import logging
from importlib import import_module
import sys
import yaml

from pydcop.dcop.yamldcop import load_dcop_from_file
from pydcop.utils.graphs import (
    display_graph,
    display_bipartite_graph,
)

logger = logging.getLogger("pydcop.cli.graph")


def set_parser(subparsers):
    parser = subparsers.add_parser(
        "graph",
        help="Graph metrics for dcop graphs. Can also be used to display a graphical "
        "representation of the graph.",
    )
    parser.set_defaults(func=run_cmd)

    parser.add_argument("dcop_file", type=str, nargs="+", help="dcop file(s)")

    parser.add_argument(
        "--display",
        default=False,
        action="store_true",
        help="Display the constraints graph using networkx and " "matplotlib",
    )
    parser.add_argument(
        "-g",
        "--graph",
        choices=["factor_graph", "pseudotree", "constraints_hypergraph"],
        help="graphical model for dcop computations",
    )


def run_cmd(args):
    logger.debug(f'dcop command "graph" with arguments {args} ')

    dcop_yaml_file = args.dcop_file
    logger.info(f"loading dcop from {dcop_yaml_file}")
    dcop = load_dcop_from_file(dcop_yaml_file)

    if args.display:
        if args.graph == "factor_graph":
            display_bipartite_graph(dcop.variables.values(), dcop.constraints.values())
        else:
            display_graph(dcop.variables.values(), dcop.constraints.values())

    try:
        graph_module = import_module(f"pydcop.computations_graph.{args.graph}")
        logger.info(f"Building computation graph for dcop {dcop.name}")
        graph_stats(dcop, graph_module)
    except ImportError:
        _error(f"Could not find computation graph type: {args.graph}")


def graph_stats(dcop, graph_module):
    logger.info(f"Building computation graph for dcop {dcop.name}")
    cg = graph_module.build_computation_graph(dcop)

    edges_count = len(list(cg.links))
    nodes_count = len(list(cg.nodes))
    density = cg.density()

    # Note : when using variables with integrated costs, the costs factors
    # are not accounted for in the metrics.

    result = {
        "status": "OK",
        "variables_count": len(dcop.variables),
        "constraints_count": len(dcop.constraints),
        "nodes_count": nodes_count,
        "edges_count": edges_count,
        "density": density,
    }
    result.update(projected_graph_metrics(cg))
    result.update(computation_graph_specific_metrics(cg))
    print(yaml.dump(result, default_flow_style=False))


def projected_graph_metrics(computation_graph):
    adjacency = projected_adjacency(computation_graph)
    components = connected_components(adjacency)
    component_count = len(components)
    projected_edges_count = sum(len(neighbors) for neighbors in adjacency.values()) // 2
    nodes_count = len(adjacency)

    component_diameters = [component_diameter(adjacency, c) for c in components]
    degrees = [len(neighbors) for neighbors in adjacency.values()]

    return {
        "is_connected": component_count == 1 if nodes_count else True,
        "components_count": component_count,
        "component_sizes": [len(c) for c in components],
        "projected_edges_count": projected_edges_count,
        "diameter": max(component_diameters, default=0),
        "cycles_count": projected_edges_count - nodes_count + component_count,
        "max_degree": max(degrees, default=0),
        "average_degree": (
            2 * projected_edges_count / nodes_count if nodes_count else 0
        ),
    }


def projected_adjacency(computation_graph):
    adjacency = {node.name: set() for node in computation_graph.nodes}
    for link in computation_graph.links:
        link_nodes = sorted(set(link.nodes))
        for node in link_nodes:
            adjacency.setdefault(node, set())
        for left, right in combinations(link_nodes, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
    return adjacency


def connected_components(adjacency):
    remaining = set(adjacency)
    components = []
    while remaining:
        start = min(remaining)
        component = set()
        queue = deque([start])
        remaining.remove(start)
        while queue:
            node = queue.popleft()
            component.add(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    return components


def component_diameter(adjacency, component):
    diameter = 0
    for node in component:
        distances = shortest_distances(adjacency, node)
        diameter = max(diameter, max(distances[n] for n in component))
    return diameter


def shortest_distances(adjacency, start):
    distances = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in adjacency[node]:
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    return distances


def computation_graph_specific_metrics(computation_graph):
    result = {}
    node_type_counts = Counter(
        node.type for node in computation_graph.nodes if node.type is not None
    )
    if node_type_counts:
        result["node_type_counts"] = dict(sorted(node_type_counts.items()))

    if hasattr(computation_graph, "roots"):
        roots = sorted(root.name for root in computation_graph.roots)
        result["roots"] = roots
        result["roots_count"] = len(roots)
        child_counts = Counter(
            link.source
            for link in computation_graph.links
            if link.type == "children" and hasattr(link, "source")
        )
        result["max_branching_factor"] = max(child_counts.values(), default=0)

    return result


def _error(msg):
    print(f"Error: {msg}")
    sys.exit(2)
