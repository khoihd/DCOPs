import argparse
from itertools import product
from random import Random

from pydcop.commands.generators.meetingscheduling import (
    Event,
    Resource,
    generate_resources,
    generate_events,
    generate_problem_definition,
    init_cli_parser,
    peav_model,
    peav_variables_for_resource,
)
from pydcop.dcop.relations import NAryFunctionRelation


def test_generate_resources():
    resources = generate_resources(count=3, max_value=5, slots=[1, 2, 3])

    assert len(resources) == 3
    for id, resource in resources.items():
        assert id == resource.id
        assert len(resource.value_free) == 3
        for value in resource.value_free:
            assert 0 <= value <= 5


def test_generate_events():
    resources = generate_resources(count=3, max_value=5, slots=[1, 2, 3])
    events = generate_events(
        count=20,
        max_value=5,
        max_length=2,
        resources=list(resources.values()),
        max_resources_count=3,
    )

    assert len(events) == 20
    for id, event in events.items():
        assert event.id == id
        assert 1 <= event.length <= 5
        assert 1 <= len(event.resources) <= 3
        assert len(set(event.resources)) == len(event.resources)
        for resource, value in event.resources.items():
            assert 0 <= value <= 5


def test_generate_variables():
    slots_count = 10
    slots, events, resources = generate_problem_definition(
        slots_count=slots_count,
        resources_count=5,
        max_resource_value=10,
        events_count=3,
        max_length_event=2,
        max_resources_event=3,
    )

    _, resource = resources.popitem()
    variables = peav_variables_for_resource(resource, events, slots_count)
    events_with_resource = [
        evt for evt in events.values() if resource.id in evt.resources
    ]
    assert len(variables) == len(events_with_resource)


def test_seed_makes_problem_definition_reproducible():
    problem1 = generate_problem_definition(
        slots_count=5,
        resources_count=4,
        max_resource_value=10,
        events_count=6,
        max_length_event=2,
        max_resources_event=3,
        random_generator=Random(12),
    )
    problem2 = generate_problem_definition(
        slots_count=5,
        resources_count=4,
        max_resource_value=10,
        events_count=6,
        max_length_event=2,
        max_resources_event=3,
        random_generator=Random(12),
    )

    assert problem1 == problem2


def test_cli_parser_accepts_intentional():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    init_cli_parser(subparsers)

    args = parser.parse_args(
        [
            "meetings",
            "--slots_count",
            "3",
            "--events_count",
            "2",
            "--resources_count",
            "2",
            "--max_resources_event",
            "2",
            "--intentional",
        ]
    )

    assert args.intentional


def test_peav_intentional_constraints_match_extensive_constraints():
    slots = [1, 2, 3]
    resources = {
        0: Resource(0, {1: 1, 2: 2, 3: 3}),
        1: Resource(1, {1: 3, 2: 2, 3: 1}),
    }
    events = {
        0: Event(0, {0: 5, 1: 4}, 1),
        1: Event(1, {0: 3}, 2),
    }
    penalty = 20

    _, extensive_constraints, _ = peav_model(slots, events, resources, penalty)
    _, intentional_constraints, _ = peav_model(
        slots, events, resources, penalty, intentional=True
    )

    assert intentional_constraints.keys() == extensive_constraints.keys()
    assert all(
        isinstance(constraint, NAryFunctionRelation)
        for constraint in intentional_constraints.values()
    )

    for name, intentional in intentional_constraints.items():
        extensive = extensive_constraints[name]
        variables = [variable.name for variable in intentional.dimensions]
        domains = [variable.domain for variable in intentional.dimensions]
        for values in product(*domains):
            assignment = dict(zip(variables, values))
            assert intentional(**assignment) == extensive(**assignment)
