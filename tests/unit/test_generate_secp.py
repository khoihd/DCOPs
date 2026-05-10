from random import Random

from pydcop.commands.generators.secp import build_lights, build_models, build_rules
from pydcop.dcop.dcop import DCOP
from pydcop.dcop.objects import Domain
from pydcop.dcop.yamldcop import dcop_yaml


def test_seed_makes_secp_generation_reproducible():
    assert generate_seeded_secp() == generate_seeded_secp()


def generate_seeded_secp():
    random_generator = Random(12)
    light_domain = Domain("light", "light", range(0, 5))

    lights_var, lights_cost = build_lights(4, light_domain, random_generator)
    models_var, models_constraints = build_models(
        light_domain, lights_var, 2, 3, random_generator
    )
    rules_constraints = build_rules(
        1, lights_var, models_var, 2, random_generator
    )

    variables = lights_var.copy()
    variables.update(models_var)

    constraints = models_constraints.copy()
    constraints.update(lights_cost)
    constraints.update(rules_constraints)

    dcop = DCOP(
        "secp",
        "min",
        domains={"light_domain": light_domain},
        variables=variables,
        agents={},
        constraints=constraints,
    )

    return dcop_yaml(dcop)
