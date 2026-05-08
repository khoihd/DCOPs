import pytest

from pydcop.commands.generators.graphcoloring import (
    HARD_CONSTRAINT_VALUE,
    generate_grid_graph,
    generate_hard_constraints,
    generate_scalefree_graph,
)
from pydcop.dcop.objects import Variable, VariableDomain


def test_grid_graph_raises_with_invalide_size():
    with pytest.raises(ValueError):
        generate_grid_graph(5)


def test_grid_graph():
    graph = generate_grid_graph(16)
    assert len(list(graph.nodes)) == 16
    assert len(list(graph.edges)) == 24


def test_generate_scale_free():
    graph = generate_scalefree_graph(10, 2, False)
    assert len(graph.nodes) == 10


@pytest.mark.parametrize(
    "objective, expected_value",
    [("min", HARD_CONSTRAINT_VALUE), ("max", -HARD_CONSTRAINT_VALUE)],
)
@pytest.mark.parametrize("intentional", [False, True])
def test_hard_constraints_use_objective_signed_value(objective, expected_value, intentional):
    graph = generate_grid_graph(4)
    domain = VariableDomain("colors", "color", ["R", "G"])
    variables = {
        node: Variable(f"v{i:02d}", domain)
        for i, node in enumerate(sorted(graph.nodes))
    }

    constraints = generate_hard_constraints(
        graph, variables, intentional, objective=objective
    )

    constraint = next(iter(constraints.values()))
    var1, var2 = constraint.dimensions
    assert constraint(**{var1.name: "R", var2.name: "R"}) == expected_value
    assert constraint(**{var1.name: "R", var2.name: "G"}) == 0
