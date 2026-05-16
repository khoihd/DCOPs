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

.. _pydcop_commands_generate_meetings:

pydcop generate meetings
========================

Meetings scheduling benchmark problem generator
-----------------------------------------------

Synopsis
--------

::

  pydcop generate meetings
          --slots_count <slots_count>
          --events_count <events_count>
          --resources_count <resources_count>
          --max_resources_event <max_resources_event>
          [--max_length_event <max_length_event>]
          [--max_resource_value <max_resource_value>]
          [--model <model>]
          [--seed <seed>]
          [--no_agents]
          [--routes_default <routes_default>]
          [--hosting_default <hosting_default>]
          [--capacity <capacity>]


Description
-----------

This command generates a meeting scheduling problem, based on
:cite:`maheswaran_taking_2004` with the *Private Event As Variable* (PEAV) model
by default.

Note that this command generates both a DCOP and a distribution, as the selected
model also specifies the list of agents (one for each resource) and where each
variable is hosted.


**Note:** the generated DCOP and distribution are both written to the standard output
as separate YAML documents. To write in files, you can use the ``--output <file>``
:ref:`global option<usage_cli_ref_options>`.

Options
-------

``--slots_count <slots_count>``
  Total number of time slots

``--events_count``
  Number of events (aka meetings) to schedule

``--resources_count <resources_count>``
  Number of resources

``--max_resources_event <max_resources_event>``
  Maximum number of resources for each event: each event has a random
  number of requested resources in [1, max_resources_event]

``--max_length_event <max_length_event>``
  Maximum number of time slot for an event: each event has a random
  length in [1, max_length_event]. Optional, defaults to 1.

``--max_resource_value <max_resource_value>``
  Each resources has a random value in [1, max_resource_value] for
  each time slot and a value for being kept free (in [1, max_resource_value])
  at a given time slot. Optional, defaults to 10.

``--seed <seed>``
  Seed for random problem generation. Optional.

``--model <model>``
  Model used for the meeting scheduling problem: ``peav`` (default),
  ``eav`` (Events As Variables), or ``tsav`` (Time Slots As Variables).

``--no_agents``
  Do not generate agents or the model distribution.

``--intentional``
  Generate constraints as intentional functions instead of extensional matrices.

``--routes_default <routes_default>``
  Default route cost for generated agents. Optional.

``--hosting_default <hosting_default>``
  Default hosting cost for generated agents. Optional.

``--capacity <capacity>``
  Capacity for generated agents. Optional, defaults to 999.


Examples
--------

Generating a meetings scheduling problem written directly to stdout::

    pydcop generate meetings --slots_count 5 \
        --events_count 4 --resources_count 3 --max_resources_event 2

Generating a meetings scheduling problem written in in ``meetings.yaml``. The
distribution is written in ``meetings_dist.yaml``::

    pydcop --output meetings.yaml generate meetings \\
        --slots_count 5 --events_count 6 --resources_count 3 \\
        --max_resources_event 2 --max_length_event 2

"""
import random
from os.path import splitext
from typing import NamedTuple

import itertools

import yaml

from pydcop.dcop.dcop import DCOP
from pydcop.dcop.objects import Variable, Domain, AgentDef
from pydcop.dcop.relations import Constraint, NAryFunctionRelation, NAryMatrixRelation
from pydcop.dcop.yamldcop import dcop_yaml
from pydcop.distribution.objects import Distribution
from pydcop.utils.expressionfunction import ExpressionFunction


DEFAULT_AGENT_CAPACITY = 999


def init_cli_parser(parent_parser):
    parser = parent_parser.add_parser(
        "meetings", help="Generate a meeting scheduling benchmark problem"
    )
    parser.set_defaults(func=generate)

    parser.add_argument(
        "--slots_count", required=True, type=int, help="Total number of time slots"
    )
    parser.add_argument(
        "--events_count",
        required=True,
        type=int,
        help="Number of events (aka meetings) to schedule",
    )
    parser.add_argument(
        "--resources_count", required=True, type=int, help="Number of resources"
    )
    parser.add_argument(
        "--max_resources_event",
        required=True,
        type=int,
        help="Maximum number of resources for each event: each event has a random "
        "number of requested resources in [1, max_resources_event]",
    )
    parser.add_argument(
        "--max_length_event",
        required=False,
        default=1,
        type=int,
        help="Maximum number of time slot for an event: each event has a random "
        "length in [1, max_length_event]",
    )
    parser.add_argument(
        "--max_resource_value",
        required=False,
        default=10,
        type=int,
        help="Each resources has a random value in [1, max_resource_value] for "
        "each time slot and a value for being kept free "
        "(in [1, max_resource_value]) at a given time slot",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for random problem generation",
    )

    parser.add_argument(
        "--no_agents",
        default=False,
        required=False,
        action="store_true",
        help="generate the problem without any agents. You can use the 'pydcop generate " \
             "agents' to generate them with their hosting and route costs"
    )

    parser.add_argument(
        "--routes_default", type=int, required=False, help="Default routes cost"
    )

    parser.add_argument(
        "--hosting_default", type=int, required=False, help="Default hosting cost"
    )

    parser.add_argument(
        "--capacity",
        type=int,
        required=False,
        default=DEFAULT_AGENT_CAPACITY,
        help=f"Capacity of agents (default: {DEFAULT_AGENT_CAPACITY})",
    )

    parser.add_argument(
        "--model",
        choices=["peav", "eav", "tsav"],
        default="peav",
        help="Model used for the meeting scheduling problem: "
        "'peav' (Private Events As Variables), "
        "'eav' (Events As Variables), or "
        "'tsav' (Time Slots As Variables)",
    )

    parser.add_argument(
        "--intentional",
        default=False,
        required=False,
        action="store_true",
        help="generate the problem in intentional form (default is extensive form)",
    )


def generate(args):
    random_generator = random.Random(args.seed)
    slots, events, resources = generate_problem_definition(
        args.slots_count,
        args.resources_count,
        args.max_resource_value,
        args.events_count,
        args.max_length_event,
        args.max_resources_event,
        random_generator,
    )

    penalty = args.max_resource_value * args.slots_count * args.resources_count
    model = getattr(args, "model", "peav")
    variables, constraints, agents = meeting_scheduling_model(
        model, slots, events, resources, penalty, args.intentional
    )

    domains = {variable.domain.name: variable.domain for variable in variables.values()}
    variables = {variable.name: variable for variable in variables.values()}
    # agents_defs = {agent.name: agent for agent, _ in agents.values()}
    # Generate agents hosting and route costs
    agents_defs = {}
    if not args.no_agents:
        for agent, agt_variables in agents.items():
            kw = {}
            kw["hosting_costs"] = {v.name: 0 for v in agt_variables}
            if args.hosting_default:
                kw["default_hosting_cost"] = args.hosting_default
            if args.capacity is not None:
                kw["capacity"] = args.capacity
            if args.routes_default:
                kw["default_route"] = args.routes_default
            agents_defs[agent] = AgentDef(agent, **kw)

    dcop = DCOP(
        "MeetingSceduling",
        objective="max",
        domains=domains,
        variables=variables,
        constraints=constraints,
        agents=agents_defs,
    )

    if not args.no_agents:
        distribution = Distribution(
            {
                agent.name: [v.name for v in agents[agent.name]]
                for agent in agents_defs.values()
            }
        )

    if args.output:
        output_file = args.output
        with open(output_file, encoding="utf-8", mode="w") as fo:
            fo.write(dcop_yaml(dcop))

        if not args.no_agents:
            dist_result = meeting_distribution_result(
                model, output_file, distribution.mapping()
            )
            path, ext = splitext(output_file)
            dist_output_file = f"{path}_dist{ext}"
            with open(dist_output_file, encoding="utf-8", mode="w") as fo:
                fo.write(yaml.dump(dist_result, default_flow_style=False))

    else:
        dist_result = None
        if not args.no_agents:
            dist_result = meeting_distribution_result(
                model, "NA", distribution.mapping()
            )
        print(generated_meetings_yaml(dcop, dist_result), end="")


def meeting_distribution_result(model, dcop_file, distribution_mapping):
    return {
        "inputs": {
            "dist_algo": model,
            "dcop": dcop_file,
            "graph": "constraints_graph",
            "algo": "NA",
        },
        "distribution": distribution_mapping,
        "cost": None,
    }


def generated_meetings_yaml(dcop, dist_result=None):
    documents = [dcop_yaml(dcop).rstrip()]
    if dist_result is not None:
        documents.append(yaml.dump(dist_result, default_flow_style=False).rstrip())
    return "\n---\n".join(documents) + "\n"


# Semantic type definitions:
EVT = int
RESOURCE = int
AGT = int
LENGTH = int
SLOT = int
VALUE = int


class Event(NamedTuple):
    id: EVT
    """Resources required for this event, with corresponding value"""
    resources: dict[RESOURCE, VALUE]
    length: int


class Resource(NamedTuple):
    id: RESOURCE
    value_free: dict[SLOT, VALUE]


def meeting_scheduling_model(
    model: str,
    slots: list[SLOT],
    events: dict[EVT, Event],
    resources: dict[RESOURCE, Resource],
    penalty,
    intentional: bool = False,
) -> tuple[
    dict[object, Variable],
    dict[str, Constraint],
    dict[str, list[Variable]],
]:
    if model == "peav":
        return peav_model(slots, events, resources, penalty, intentional)
    if model == "eav":
        return eav_model(slots, events, resources, penalty, intentional)
    if model == "tsav":
        return tsav_model(slots, events, resources, penalty, intentional)
    raise ValueError(f"Unknown meeting scheduling model {model}")


def peav_model(
    slots: list[SLOT],
    events: dict[EVT, Event],
    resources: dict[RESOURCE, Resource],
    penalty,
    intentional: bool = False,
) -> tuple[
    dict[tuple[RESOURCE, EVT], Variable],
    dict[str, Constraint],
    dict[str, list[Variable]],
]:
    """
    In the PEAV model

    * agents represent resources


    Parameters
    ----------

    Returns
    -------

    """
    all_variables: dict[tuple[RESOURCE, EVT], Variable] = {}
    all_constraints: dict[str, Constraint] = {}
    all_agents: dict[str, list[Variable]] = {}

    # Each resource is represented by an agent, which controls one variable
    # for each event it could participate.
    for resource in resources.values():
        variables = peav_variables_for_resource(resource, events, len(slots))
        all_variables.update(variables)
        all_agents[f"a_{resource.id}"] = list(variables.values())

        if intentional:
            constraints = peav_intra_intentional_constraints(
                resource, events, variables, penalty
            )
        else:
            constraints = peav_intra_extensive_constraints(
                resource, events, variables, penalty
            )
        all_constraints.update(constraints)

    # Generate inter-agent constraints: we have such constraint between any two
    # variables representing the same event for two different resources.
    for event in events.values():
        for resource_id1, resource_id2 in itertools.combinations(event.resources, 2):
            var1 = all_variables[(resource_id1, event.id)]
            var2 = all_variables[(resource_id2, event.id)]
            if intentional:
                constraint = peav_inter_intentional_constraint(var1, var2, penalty)
            else:
                constraint = peav_inter_extensive_constraint(var1, var2, penalty)
            all_constraints[constraint.name] = constraint

    return all_variables, all_constraints, all_agents


def eav_model(
    slots: list[SLOT],
    events: dict[EVT, Event],
    resources: dict[RESOURCE, Resource],
    penalty,
    intentional: bool = False,
) -> tuple[dict[EVT, Variable], dict[str, Constraint], dict[str, list[Variable]]]:
    all_variables = eav_variables(events, len(slots))
    all_constraints: dict[str, Constraint] = {}
    all_agents: dict[str, list[Variable]] = {
        f"a_{resource.id}": [] for resource in resources.values()
    }

    for event in events.values():
        variable = all_variables[event.id]
        host_resource = sorted(event.resources)[0]
        all_agents[f"a_{host_resource}"].append(variable)
        if intentional:
            constraint = eav_event_utility_intentional_constraint(
                event, resources, variable
            )
        else:
            constraint = eav_event_utility_extensive_constraint(
                event, resources, variable
            )
        all_constraints[constraint.name] = constraint

    for event1, event2 in itertools.combinations(events.values(), 2):
        shared_resources = set(event1.resources).intersection(event2.resources)
        if not shared_resources:
            continue
        var1 = all_variables[event1.id]
        var2 = all_variables[event2.id]
        if intentional:
            constraint = eav_conflict_intentional_constraint(
                event1, var1, event2, var2, penalty, len(shared_resources)
            )
        else:
            constraint = eav_conflict_extensive_constraint(
                event1, var1, event2, var2, penalty, len(shared_resources)
            )
        all_constraints[constraint.name] = constraint

    return all_variables, all_constraints, all_agents


def tsav_model(
    slots: list[SLOT],
    events: dict[EVT, Event],
    resources: dict[RESOURCE, Resource],
    penalty,
    intentional: bool = False,
) -> tuple[
    dict[tuple[RESOURCE, SLOT], Variable],
    dict[str, Constraint],
    dict[str, list[Variable]],
]:
    all_variables: dict[tuple[RESOURCE, SLOT], Variable] = {}
    all_constraints: dict[str, Constraint] = {}
    all_agents: dict[str, list[Variable]] = {}

    for resource in resources.values():
        variables = tsav_variables_for_resource(resource, events, slots)
        all_variables.update(variables)
        all_agents[f"a_{resource.id}"] = list(variables.values())

    # TSAV event constraints can have a large arity, so they are represented
    # intentionally even when the rest of the generator defaults to matrices.
    for event in events.values():
        constraint = tsav_event_intentional_constraint(
            event, resources, all_variables, slots, penalty
        )
        all_constraints[constraint.name] = constraint

    return all_variables, all_constraints, all_agents


def eav_variables(
    events: dict[EVT, Event], slots_count: int
) -> dict[EVT, Variable]:
    variables: dict[EVT, Variable] = {}
    for event in events.values():
        name = f"v_{event.id:02d}"
        # The domain represents the start time (as slot) for this event.
        # Time slots start at 1, the value 0 represents an unscheduled event.
        domain = Domain(
            f"d_{name}",
            "time_slot",
            values=range(0, slots_count - event.length + 2),
        )
        variables[event.id] = Variable(name, domain)
    return variables


def eav_event_utility_extensive_constraint(
    event: Event, resources: dict[RESOURCE, Resource], variable: Variable
) -> Constraint:
    constraint = NAryMatrixRelation([variable], name=f"cu_{variable.name}")
    for t in variable.domain:
        value = eav_event_utility(event, resources, t)
        constraint = constraint.set_value_for_assignment({variable.name: t}, value)
    return constraint


def eav_event_utility_intentional_constraint(
    event: Event, resources: dict[RESOURCE, Resource], variable: Variable
) -> Constraint:
    values = {t: eav_event_utility(event, resources, t) for t in variable.domain}
    expression = f"{values!r}[{variable.name}]"
    return NAryFunctionRelation(
        ExpressionFunction(expression),
        [variable],
        name=f"cu_{variable.name}",
        f_kwargs=True,
    )


def eav_event_utility(
    event: Event, resources: dict[RESOURCE, Resource], t: SLOT
) -> float:
    return sum(
        resource_value_for_event(resources[resource_id], event, t)
        for resource_id in event.resources
    )


def eav_conflict_extensive_constraint(
    event1: Event,
    var1: Variable,
    event2: Event,
    var2: Variable,
    penalty: int,
    shared_resources_count: int,
) -> Constraint:
    constraint = NAryMatrixRelation([var1, var2], name=f"cc_{var1.name}_{var2.name}")
    for t1 in var1.domain:
        for t2 in var2.domain:
            value = eav_conflict_value(
                event1, event2, penalty, shared_resources_count, t1, t2
            )
            constraint = constraint.set_value_for_assignment(
                {var1.name: t1, var2.name: t2}, value
            )
    return constraint


def eav_conflict_intentional_constraint(
    event1: Event,
    var1: Variable,
    event2: Event,
    var2: Variable,
    penalty: int,
    shared_resources_count: int,
) -> Constraint:
    penalty_value = penalty * shared_resources_count
    expression = (
        f"if {var1.name} != 0 and {var2.name} != 0:\n"
        f"    if {var1.name} <= {var2.name} <= "
        f"{var1.name} + {event1.length - 1}:\n"
        f"        return -{penalty_value}\n"
        f"    if {var2.name} <= {var1.name} <= "
        f"{var2.name} + {event2.length - 1}:\n"
        f"        return -{penalty_value}\n"
        "return 0"
    )
    return NAryFunctionRelation(
        ExpressionFunction(expression),
        [var1, var2],
        name=f"cc_{var1.name}_{var2.name}",
        f_kwargs=True,
    )


def eav_conflict_value(
    event1: Event,
    event2: Event,
    penalty: int,
    shared_resources_count: int,
    t1: SLOT,
    t2: SLOT,
) -> float:
    if events_overlap(event1, t1, event2, t2):
        return -penalty * shared_resources_count
    return 0


def tsav_event_token(event: Event) -> int:
    return event.id + 1


def tsav_variables_for_resource(
    resource: Resource, events: dict[EVT, Event], slots: list[SLOT]
) -> dict[tuple[RESOURCE, SLOT], Variable]:
    variables: dict[tuple[RESOURCE, SLOT], Variable] = {}
    domain_values = [0] + [
        tsav_event_token(event)
        for event in events.values()
        if resource.id in event.resources
    ]
    for slot in slots:
        name = f"t_{resource.id:02d}_{slot:02d}"
        # Domain values are event tokens; 0 means the resource is free.
        domain = Domain(f"d_{name}", "event", values=domain_values)
        variables[resource.id, slot] = Variable(name, domain)
    return variables


def tsav_event_intentional_constraint(
    event: Event,
    resources: dict[RESOURCE, Resource],
    variables: dict[tuple[RESOURCE, SLOT], Variable],
    slots: list[SLOT],
    penalty,
) -> Constraint:
    dimensions = []
    assigned_expressions = []
    token = tsav_event_token(event)

    for resource_id in sorted(event.resources):
        resource_variables = [(slot, variables[resource_id, slot]) for slot in slots]
        dimensions.extend(variable for _, variable in resource_variables)
        slot_assignments = ", ".join(
            f"({slot}, {variable.name})" for slot, variable in resource_variables
        )
        assigned_expressions.append(
            f"[slot for slot, value in [{slot_assignments}] if value == {token}]"
        )

    start_values = {
        t: eav_event_utility(event, resources, t)
        for t in range(1, len(slots) - event.length + 2)
    }
    expression = (
        f"assigned = [{', '.join(assigned_expressions)}]\n"
        "starts = []\n"
        "for resource_slots in assigned:\n"
        "    if not resource_slots:\n"
        "        starts.append(0)\n"
        "        continue\n"
        f"    if len(resource_slots) != {event.length}:\n"
        f"        return -{penalty}\n"
        "    start = min(resource_slots)\n"
        f"    if resource_slots != list(range(start, start + {event.length})):\n"
        f"        return -{penalty}\n"
        f"    if start not in {start_values!r}:\n"
        f"        return -{penalty}\n"
        "    starts.append(start)\n"
        "if all(start == 0 for start in starts):\n"
        "    return 0\n"
        "if any(start == 0 for start in starts):\n"
        f"    return -{penalty}\n"
        "if len(set(starts)) != 1:\n"
        f"    return -{penalty}\n"
        f"return {start_values!r}[starts[0]]"
    )
    return NAryFunctionRelation(
        ExpressionFunction(expression),
        dimensions,
        name=f"ct_{event.id:02d}",
        f_kwargs=True,
    )


def events_overlap(event1: Event, t1: SLOT, event2: Event, t2: SLOT) -> bool:
    return (
        t1 != 0
        and t2 != 0
        and (
            t1 <= t2 <= t1 + event1.length - 1
            or t2 <= t1 <= t2 + event2.length - 1
        )
    )


def generate_problem_definition(
    slots_count: int,
    resources_count: int,
    max_resource_value: VALUE,
    events_count: int,
    max_length_event,
    max_resources_event,
    random_generator=None,
) -> tuple[list[SLOT], dict[EVT, Event], dict[RESOURCE, Resource]]:
    """
    Generate a  Multi-event scheduling problem definition.

    The definition is independent of the model used to map the problem to a DCOP.

    Parameters
    ----------
    slots_count
    resources_count
    max_resource_value
    events_count
    max_length_event
    max_resources_event

    Returns
    -------

    """
    if random_generator is None:
        random_generator = random

    slots = list(range(1, slots_count + 1))
    resources = generate_resources(
        resources_count, max_resource_value, slots, random_generator
    )
    events = generate_events(
        events_count,
        max_resource_value,
        max_length_event,
        list(resources.values()),
        max_resources_event,
        random_generator,
    )

    return slots, events, resources


def generate_resources(
    count: int, max_value: VALUE, slots: list[SLOT], random_generator=None
) -> dict[RESOURCE, Resource]:
    if random_generator is None:
        random_generator = random

    resources: dict[RESOURCE, Resource] = {}
    for i in range(count):
        # A resource has, for each time slot, a value if kept free:
        value_free = {j: random_generator.randint(0, max_value) for j in slots}
        resources[i] = Resource(i, value_free)
    return resources


def generate_events(
    count: int,
    max_value: VALUE,
    max_length: int,
    resources: list[Resource],
    max_resources_count: int,
    random_generator=None,
) -> dict[EVT, Event]:
    if random_generator is None:
        random_generator = random

    events: dict[EVT, Event] = {}
    for i in range(count):
        # Event's length:
        length = random_generator.randint(1, max_length)
        # Resources required for this event:
        resources_count = random_generator.randint(1, max_resources_count)
        event_resources = random_generator.sample(resources, resources_count)
        # Value for each required resource for this event:
        values = {
            resource.id: random_generator.randint(1, max_value)
            for resource in event_resources
        }
        events[i] = Event(i, values, length)
    return events


def peav_variables_for_resource(
    resource: Resource, events: dict[EVT, Event], slots_count: int
) -> dict[tuple[RESOURCE, EVT], Variable]:
    variables: dict[tuple[RESOURCE, EVT], Variable] = {}
    for event in events.values():
        if resource.id in event.resources:
            name = f"v_{resource.id:02d}_{event.id:02d}"
            # The domain represents the start time (as slot) this event could start at.
            # Time slots start at 1, the value 0 represents a combination
            # (event, resource) that is not scheduled.
            domain = Domain(
                f"d_{name}",
                "time_slot",
                values=range(0, slots_count - event.length + 2),
            )
            variables[resource.id, event.id] = Variable(name, domain)
    return variables


def peav_intra_extensive_constraints(
    resource: Resource,
    events: dict[EVT, Event],
    variables: dict[tuple[RESOURCE, EVT], Variable],
    penalty,
):
    resource_events_count = len(variables)
    constraints = {}
    for (resource_id1, event_id1), (resource_id2, event_id2) in itertools.combinations(
        variables, 2
    ):
        # As we are generating intra-agent constraint and agents map to resources in
        # the peav model, all resources must be the same
        assert resource.id == resource_id1 == resource_id2
        constraint = peav_intra_extensive_constraint(
            resource,
            events[event_id1],
            variables[(resource.id, event_id1)],
            events[event_id2],
            variables[resource.id, event_id2],
            penalty,
            resource_events_count,
        )
        constraints[constraint.name] = constraint

    if len(variables) == 1:
        # If there is a single variable (and thus a single event) for this resource,
        # we add a unary constraint which will account for the utility of scheduling
        # the resource on this single event. Otherwise, as these utilities are given by
        # internal binary variables, it would not be accounted for.
        # In Maheswaran_2012, this is done by introducing a dummy variable === 0,
        # to keep an artificial binary constraint. The result is the same but the
        #  unary-constraint approach makes more sense to me and fits pydcop better.
        (_, event_id), variable = variables.popitem()
        event = events[event_id]
        constraint = NAryMatrixRelation([variable], name=f"cu_{variable.name}")
        for t in variable.domain:
            value = resource_value_for_event(resource, event, t)
            constraint = constraint.set_value_for_assignment({variable.name: t}, value)
            constraints[constraint.name] = constraint

    return constraints


def peav_intra_intentional_constraints(
    resource: Resource,
    events: dict[EVT, Event],
    variables: dict[tuple[RESOURCE, EVT], Variable],
    penalty,
):
    resource_events_count = len(variables)
    constraints = {}
    for (resource_id1, event_id1), (resource_id2, event_id2) in itertools.combinations(
        variables, 2
    ):
        # As we are generating intra-agent constraint and agents map to resources in
        # the peav model, all resources must be the same
        assert resource.id == resource_id1 == resource_id2
        constraint = peav_intra_intentional_constraint(
            resource,
            events[event_id1],
            variables[(resource.id, event_id1)],
            events[event_id2],
            variables[resource.id, event_id2],
            penalty,
            resource_events_count,
        )
        constraints[constraint.name] = constraint

    if len(variables) == 1:
        (_, event_id), variable = next(iter(variables.items()))
        event = events[event_id]
        constraint = peav_unary_intentional_constraint(resource, event, variable)
        constraints[constraint.name] = constraint

    return constraints


def peav_intra_extensive_constraint(
    resource: Resource,
    event1: Event,
    var1: Variable,
    event2: Event,
    var2: Variable,
    penalty: int,
    resource_events_count: int,
) -> Constraint:
    constraint = NAryMatrixRelation([var1, var2], name=f"ci_{var1.name}_{var2.name}")

    # For each possible partial assignment (t1, t2) to (var1, var2)
    # we compute the utility (or penalty)
    for t1 in var1.domain:
        for t2 in var2.domain:
            value = peav_intra_extensive_constraint_value(
                resource, event1, event2, penalty, resource_events_count, t1, t2
            )
            constraint = constraint.set_value_for_assignment(
                {var1.name: t1, var2.name: t2}, value
            )
    return constraint


def peav_unary_intentional_constraint(
    resource: Resource, event: Event, variable: Variable
) -> Constraint:
    values = {t: resource_value_for_event(resource, event, t) for t in variable.domain}
    expression = f"{values!r}[{variable.name}]"
    return NAryFunctionRelation(
        ExpressionFunction(expression),
        [variable],
        name=f"cu_{variable.name}",
        f_kwargs=True,
    )


def peav_intra_intentional_constraint(
    resource: Resource,
    event1: Event,
    var1: Variable,
    event2: Event,
    var2: Variable,
    penalty: int,
    resource_events_count: int,
) -> Constraint:
    values1 = {t: resource_value_for_event(resource, event1, t) for t in var1.domain}
    values2 = {t: resource_value_for_event(resource, event2, t) for t in var2.domain}
    factor = 1 / (resource_events_count - 1)
    expression = (
        f"if {var1.name} != 0 and {var2.name} != 0:\n"
        f"    if {var1.name} <= {var2.name} <= "
        f"{var1.name} + {event1.length - 1}:\n"
        f"        return -{penalty}\n"
        f"    if {var2.name} <= {var1.name} <= "
        f"{var2.name} + {event2.length - 1}:\n"
        f"        return -{penalty}\n"
        f"return {factor!r} * "
        f"({values1!r}[{var1.name}] + {values2!r}[{var2.name}])"
    )
    return NAryFunctionRelation(
        ExpressionFunction(expression),
        [var1, var2],
        name=f"ci_{var1.name}_{var2.name}",
        f_kwargs=True,
    )


def peav_intra_extensive_constraint_value(
    resource: Resource,
    event1: Event,
    event2: Event,
    penalty: int,
    resource_events_count: int,
    t1: SLOT,
    t2: SLOT,
) -> float:
    """
    Compute the value of an intra-agent constraint for assignment of a resource to two
    events scheduled at  (t1, t2).

    Parameters
    ----------
    resource: Resource
        the resource scheduled
    event1: Event
        The first scheduled event
    event2: Event
        The second scheduled event
    penalty: int
        Penalty in case of conflict
    resource_events_count
        The number of events this resources is participating to.
    t1: int
        schedule for first event
    t2: int
        schedule for second event

    Returns
    -------
    The value of the constraint for assignment (t1, t2)
    """

    if event1 == event2 and t1 != t2:
        # Penalty if two events are scheduled at different time by two
        # different resources/agents:
        return -penalty
    elif event1 != event2:
        # Intra-agent constraint: penalty if there is a schedule conflict.
        if t1 != 0 and t2 != 0 and t1 <= t2 <= t1 + event1.length - 1:
            return -penalty
        elif t1 != 0 and t2 != 0 and t2 <= t1 <= t2 + event2.length - 1:
            return -penalty
        else:
            # If there is no conflict: utility
            value = (
                1
                / (resource_events_count - 1)
                * (
                    resource_value_for_event(resource, event1, t1)
                    + resource_value_for_event(resource, event2, t2)
                )
            )
            return value
    else:
        raise Exception("Bug!")


def peav_inter_extensive_constraint(var1, var2, penalty):
    constraint = NAryMatrixRelation([var1, var2], name=f"ce_{var1.name}_{var2.name}")

    # For each possible partial assignment (t1, t2) to (var1, var2)
    # we compute the utility (or penalty)
    for t1 in var1.domain:
        for t2 in var2.domain:
            if t1 != t2:
                constraint = constraint.set_value_for_assignment(
                    {var1.name: t1, var2.name: t2}, -penalty
                )
    return constraint


def peav_inter_intentional_constraint(var1, var2, penalty):
    expression = f"-{penalty} if {var1.name} != {var2.name} else 0"
    return NAryFunctionRelation(
        ExpressionFunction(expression),
        [var1, var2],
        name=f"ce_{var1.name}_{var2.name}",
        f_kwargs=True,
    )


def resource_value_for_event(resource: Resource, event: Event, t: SLOT) -> float:
    """
    The utility of affecting a resource to a given event.

    This utility is defined as the difference between the value of affecting the
    resource for all the time slots of the event and the aggregate
    value of the time slots if left free.

    Parameters
    ----------
    resource: Resource
        the resource
    event: Event
        the event
    t: int
        time slot

    Returns
    -------
    the utility of affecting the resource to this event at time slot t.
    """
    if t == 0:
        return 0
    evt_value = event.resources[resource.id] * event.length
    resource_value_if_free = sum(
        [resource.value_free[t + j] for j in range(0, event.length)]
    )
    return evt_value - resource_value_if_free
