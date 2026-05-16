import argparse
from itertools import product
from random import Random
from types import SimpleNamespace

import yaml

from pydcop.commands.generators.meetingscheduling import (
    DEFAULT_AGENT_CAPACITY,
    Event,
    Resource,
    eav_model,
    generate,
    generate_resources,
    generate_events,
    generate_problem_definition,
    init_cli_parser,
    peav_model,
    peav_variables_for_resource,
    tsav_model,
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
    assert args.model == "peav"


def test_cli_parser_accepts_model():
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
            "--model",
            "tsav",
        ]
    )

    assert args.model == "tsav"


def test_cli_parser_defaults_capacity():
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
        ]
    )

    assert args.capacity == DEFAULT_AGENT_CAPACITY


def test_generate_stdout_serializes_dcop_and_distribution_as_yaml_documents(capsys):
    args = SimpleNamespace(
        slots_count=2,
        events_count=1,
        resources_count=2,
        max_resources_event=2,
        max_length_event=1,
        max_resource_value=5,
        seed=3,
        no_agents=False,
        routes_default=None,
        hosting_default=None,
        capacity=DEFAULT_AGENT_CAPACITY,
        model="peav",
        intentional=False,
        output=None,
    )

    generate(args)

    documents = list(yaml.safe_load_all(capsys.readouterr().out))
    assert len(documents) == 2
    assert documents[0]["name"] == "MeetingSceduling"
    assert documents[0]["agents"]["a_0"]["capacity"] == DEFAULT_AGENT_CAPACITY
    assert documents[1]["inputs"]["dist_algo"] == "peav"
    assert documents[1]["inputs"]["dcop"] == "NA"
    assert "distribution" in documents[1]


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

    _assert_intentional_constraints_match_extensive(
        intentional_constraints, extensive_constraints
    )


def test_eav_intentional_constraints_match_extensive_constraints():
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

    _, extensive_constraints, _ = eav_model(slots, events, resources, penalty)
    _, intentional_constraints, _ = eav_model(
        slots, events, resources, penalty, intentional=True
    )

    _assert_intentional_constraints_match_extensive(
        intentional_constraints, extensive_constraints
    )


def test_eav_and_tsav_models_have_same_best_value_as_peav():
    slots = [1, 2]
    resources = {
        0: Resource(0, {1: 0, 2: 0}),
        1: Resource(1, {1: 0, 2: 0}),
    }
    events = {
        0: Event(0, {0: 5, 1: 4}, 1),
        1: Event(1, {0: 3}, 1),
    }
    penalty = 20

    peav_variables, peav_constraints, _ = peav_model(
        slots, events, resources, penalty
    )
    eav_variables, eav_constraints, _ = eav_model(slots, events, resources, penalty)
    tsav_variables, tsav_constraints, _ = tsav_model(
        slots, events, resources, penalty
    )

    assert _best_value(eav_variables, eav_constraints) == _best_value(
        peav_variables, peav_constraints
    )
    assert _best_value(tsav_variables, tsav_constraints) == _best_value(
        peav_variables, peav_constraints
    )


def test_tsav_event_constraint_requires_contiguous_matching_resource_slots():
    slots = [1, 2, 3]
    resources = {
        0: Resource(0, {1: 0, 2: 0, 3: 0}),
        1: Resource(1, {1: 0, 2: 0, 3: 0}),
    }
    events = {0: Event(0, {0: 5, 1: 4}, 2)}
    penalty = 20

    _, constraints, _ = tsav_model(slots, events, resources, penalty)
    constraint = constraints["ct_00"]
    assignment = {variable.name: 0 for variable in constraint.dimensions}

    scheduled = assignment | {
        "t_00_01": 1,
        "t_00_02": 1,
        "t_01_01": 1,
        "t_01_02": 1,
    }
    partial = assignment | {"t_00_01": 1, "t_00_02": 1}
    non_contiguous = assignment | {
        "t_00_01": 1,
        "t_00_03": 1,
        "t_01_01": 1,
        "t_01_03": 1,
    }

    assert constraint(**assignment) == 0
    assert constraint(**scheduled) == 18
    assert constraint(**partial) == -penalty
    assert constraint(**non_contiguous) == -penalty


def _assert_intentional_constraints_match_extensive(
    intentional_constraints, extensive_constraints
):
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


def _best_value(variables, constraints):
    variable_list = list(variables.values())
    best = None
    for values in product(*[variable.domain for variable in variable_list]):
        assignment = {
            variable.name: value for variable, value in zip(variable_list, values)
        }
        value = 0
        for constraint in constraints.values():
            constraint_assignment = {
                variable.name: assignment[variable.name]
                for variable in constraint.dimensions
            }
            value += constraint(**constraint_assignment)
        if best is None or value > best:
            best = value
    return best
