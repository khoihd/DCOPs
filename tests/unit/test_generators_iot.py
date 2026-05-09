from random import Random
from types import SimpleNamespace

from pydcop.commands.generators.iot import (
    agt_hosting_costs,
    generate_powerlaw_var_constraints,
)


def test_seed_makes_powerlaw_variables_and_constraints_reproducible():
    variables1, constraints1, domain1 = generate_powerlaw_var_constraints(
        8, 3, 10, Random(12)
    )
    variables2, constraints2, domain2 = generate_powerlaw_var_constraints(
        8, 3, 10, Random(12)
    )

    assert domain1 == domain2
    assert variables1 == variables2
    assert constraints1 == constraints2


def test_seed_makes_agent_hosting_costs_reproducible():
    var_comp = SimpleNamespace(name="v001")
    cg = SimpleNamespace(
        nodes=[
            SimpleNamespace(name="v001"),
            SimpleNamespace(name="v002"),
            SimpleNamespace(name="c001_002"),
        ]
    )

    costs1 = agt_hosting_costs(var_comp, cg, Random(12))
    costs2 = agt_hosting_costs(var_comp, cg, Random(12))

    assert costs1 == costs2
    assert costs1["v001"] == 0
