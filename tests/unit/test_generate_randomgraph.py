from random import Random

import networkx as nx
import pytest

from pydcop.commands.generators.randomgraph import (
    generate_connected_random_graph,
    generate_random_graph_dcop,
    recommended_p_edge,
    recommended_variables_count,
)
from pydcop.dcop.yamldcop import dcop_yaml


def test_generate_connected_random_graph():
    graph = generate_connected_random_graph(10, 0.5, Random(12))

    assert len(graph.nodes) == 10
    assert nx.is_connected(graph)


def test_random_graph_constraints_use_costs_in_range():
    dcop = generate_random_graph_dcop(
        5, 3, 0.8, "min", random_generator=Random(12)
    )

    assert dcop.objective == "min"
    assert len(dcop.variables) == 5
    assert len(dcop.agents) == 5
    for constraint in dcop.constraints.values():
        variable1, variable2 = constraint.dimensions
        for value1 in variable1.domain:
            for value2 in variable2.domain:
                cost = constraint(**{variable1.name: value1, variable2.name: value2})
                assert 0 <= cost <= 9


def test_random_graph_can_skip_agents():
    dcop = generate_random_graph_dcop(
        5, 3, 0.8, "max", no_agents=True, random_generator=Random(12)
    )

    assert dcop.objective == "max"
    assert dcop.agents == {}


def test_seed_makes_random_graph_generation_reproducible():
    dcop1 = generate_random_graph_dcop(
        5, 3, 0.8, "min", random_generator=Random(12)
    )
    dcop2 = generate_random_graph_dcop(
        5, 3, 0.8, "min", random_generator=Random(12)
    )

    assert dcop_yaml(dcop1) == dcop_yaml(dcop2)


def test_random_graph_rejects_impossible_connected_graph():
    with pytest.raises(ValueError):
        generate_random_graph_dcop(2, 3, 0, "min", random_generator=Random(12))


def test_random_graph_failure_recommends_better_parameters():
    with pytest.raises(ValueError) as excinfo:
        generate_connected_random_graph(10, 0.01, Random(12), max_attempts=1)

    message = str(excinfo.value)
    assert "Try p_edge >= 0.43" in message
    assert "or variables_count >= 878" in message


def test_random_graph_parameter_recommendations():
    assert recommended_p_edge(100) == pytest.approx(0.066, abs=0.001)
    assert recommended_variables_count(0.02) == 400
