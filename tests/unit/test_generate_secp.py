from random import Random

import argparse

from pydcop.commands.generators.secp import (
    DEFAULT_AGENT_CAPACITY,
    build_agents,
    build_lights,
    build_models,
    build_rules,
    init_cli_parser,
)
from pydcop.dcop.dcop import DCOP
from pydcop.dcop.objects import Domain
from pydcop.dcop.yamldcop import dcop_yaml


def test_seed_makes_secp_generation_reproducible():
    assert generate_seeded_secp() == generate_seeded_secp()


def test_cli_parser_defaults_capacity():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    init_cli_parser(subparsers)

    args = parser.parse_args(
        ["secp", "--lights", "2", "--models", "1", "--rules", "1"]
    )

    assert args.capacity == DEFAULT_AGENT_CAPACITY


def test_build_agents_defaults_capacity():
    agents = build_agents({"l1": object()}, {"lc1": object()})

    assert agents["al1"].capacity == DEFAULT_AGENT_CAPACITY


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
