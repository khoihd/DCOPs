# BSD-3-Clause License
#
# Copyright 2017 Orange

"""Profile DSA ``evaluate_cycle()`` behavior.

This script is intentionally kept outside the regular test suite. It measures
the current DSA cycle hot path without adding brittle timing assertions.

Run from the repository root, for example:

    conda run -n khoihd python profiling/profile_dsa_evaluate_cycle.py

    conda run -n khoihd python profiling/profile_dsa_evaluate_cycle.py \
        --case generated --repeat 200 --neighbors 8 --constraints 24 \
        --domain-size 8 --max-arity 4 --variant B --cprofile
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import random
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from pydcop.algorithms import AlgorithmDef, ComputationDef, dsa
from pydcop.computations_graph.constraints_hypergraph import VariableComputationNode
from pydcop.dcop.objects import Variable
from pydcop.dcop.relations import NAryFunctionRelation


@dataclass(frozen=True, slots=True)
class OperationStats:
    operation: str
    elapsed: float


@dataclass(frozen=True, slots=True)
class GeneratedCaseConfig:
    neighbors: int
    constraints: int
    domain_size: int
    max_arity: int
    seed: int


CaseFactory = Callable[[str, float, GeneratedCaseConfig], dsa.DsaComputation]


class CountingSender:
    def __init__(self) -> None:
        self.count = 0
        self.total_size = 0

    def __call__(self, source: str, target: str, msg: Any, prio, on_error) -> None:
        del source, target, prio, on_error
        self.count += 1
        self.total_size += msg.size


def _algorithm_def(variant: str, probability: float) -> AlgorithmDef:
    return AlgorithmDef.build_with_default_param(
        "dsa",
        params={
            "variant": variant,
            "probability": probability,
        },
    )


def _profile_computation(
    variable: Variable,
    constraints: Sequence[Any],
    variant: str,
    probability: float,
) -> dsa.DsaComputation:
    node = VariableComputationNode(variable, constraints)
    computation = dsa.DsaComputation(
        ComputationDef(node, _algorithm_def(variant, probability))
    )
    computation.message_sender = CountingSender()
    computation.value_selection(variable.domain[0], 0)
    return computation


def graph_coloring_case(
    variant: str, probability: float, generated_config: GeneratedCaseConfig
) -> dsa.DsaComputation:
    del generated_config
    colors = ["R", "G", "B"]
    variable = Variable("x0", colors)
    neighbors = [Variable(f"x{index}", colors) for index in range(1, 5)]

    constraints = []
    for neighbor in neighbors:
        scope = [variable, neighbor]

        def color_conflict(_neighbor=neighbor, **assignment):
            return 1 if assignment[variable.name] == assignment[_neighbor.name] else 0

        constraints.append(
            NAryFunctionRelation(
                color_conflict,
                scope,
                name=f"color_conflict_{neighbor.name}",
                f_kwargs=True,
            )
        )

    return _profile_computation(variable, constraints, variant, probability)


def _generated_scope(
    variable: Variable,
    neighbors: Sequence[Variable],
    relation_index: int,
    arity: int,
) -> list[Variable]:
    scope = [variable]
    for index in range(arity - 1):
        scope.append(neighbors[(relation_index + index) % len(neighbors)])
    return scope


def _generated_relation(
    scope: Sequence[Variable], relation_index: int, rng: random.Random
) -> NAryFunctionRelation:
    coefficients = [rng.randint(1, 13) for _ in scope]
    offset = rng.randint(0, 23)
    modulus = max(7, len(scope) * 5)

    def relation(**assignment):
        value = offset
        for coefficient, variable in zip(coefficients, scope):
            value += coefficient * assignment[variable.name]
        return value % modulus

    return NAryFunctionRelation(
        relation,
        scope,
        name=f"generated_{relation_index:03d}",
        f_kwargs=True,
    )


def generated_case(
    variant: str, probability: float, generated_config: GeneratedCaseConfig
) -> dsa.DsaComputation:
    domain = list(range(generated_config.domain_size))
    variable = Variable("x0", domain)
    neighbors = [
        Variable(f"x{index}", domain)
        for index in range(1, generated_config.neighbors + 1)
    ]
    rng = random.Random(generated_config.seed)

    constraints = []
    for relation_index in range(generated_config.constraints):
        arity = 2 + (relation_index % (generated_config.max_arity - 1))
        arity = min(arity, generated_config.neighbors + 1)
        scope = _generated_scope(variable, neighbors, relation_index, arity)
        constraints.append(_generated_relation(scope, relation_index, rng))

    return _profile_computation(variable, constraints, variant, probability)


CASES: dict[str, CaseFactory] = {
    "generated": generated_case,
    "graph-coloring": graph_coloring_case,
}


@contextmanager
def profile_dsa_operations(stats: list[OperationStats]) -> Iterator[None]:
    original_find_optimal = dsa.find_optimal
    original_assignment_cost = dsa.assignment_cost
    original_filter_assignment_dict = dsa.filter_assignment_dict
    original_exists_violated = dsa.DsaComputation.exists_violated_constraint

    def time_call(operation: str, func: Callable, *args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        stats.append(OperationStats(operation, perf_counter() - start))
        return result

    def profiled_find_optimal(*args, **kwargs):
        return time_call("find_optimal", original_find_optimal, *args, **kwargs)

    def profiled_assignment_cost(*args, **kwargs):
        return time_call(
            "assignment_cost", original_assignment_cost, *args, **kwargs
        )

    def profiled_filter_assignment_dict(*args, **kwargs):
        return time_call(
            "filter_assignment_dict", original_filter_assignment_dict, *args, **kwargs
        )

    def profiled_exists_violated(self):
        return time_call(
            "exists_violated_constraint", original_exists_violated, self
        )

    dsa.find_optimal = profiled_find_optimal
    dsa.assignment_cost = profiled_assignment_cost
    dsa.filter_assignment_dict = profiled_filter_assignment_dict
    dsa.DsaComputation.exists_violated_constraint = profiled_exists_violated
    try:
        yield
    finally:
        dsa.find_optimal = original_find_optimal
        dsa.assignment_cost = original_assignment_cost
        dsa.filter_assignment_dict = original_filter_assignment_dict
        dsa.DsaComputation.exists_violated_constraint = original_exists_violated


def _cycle_assignment(computation: dsa.DsaComputation, cycle_index: int) -> dict:
    assignment = {}
    for index, neighbor in enumerate(computation.neighbors, start=1):
        domain = computation.variable.domain
        assignment[neighbor] = domain[(cycle_index + index) % len(domain)]
    return assignment


def run_case(
    case_name: str,
    variant: str,
    probability: float,
    repeat: int,
    generated_config: GeneratedCaseConfig,
) -> tuple[float, list[OperationStats], dsa.DsaComputation]:
    stats: list[OperationStats] = []
    computation = CASES[case_name](variant, probability, generated_config)

    start = perf_counter()
    with profile_dsa_operations(stats):
        for cycle_index in range(repeat):
            computation.current_cycle = _cycle_assignment(computation, cycle_index)
            computation.next_cycle = {}
            computation.evaluate_cycle()
    elapsed = perf_counter() - start
    return elapsed, stats, computation


def print_summary(
    case_name: str,
    variant: str,
    repeat: int,
    elapsed: float,
    stats: Sequence[OperationStats],
    computation: dsa.DsaComputation,
) -> None:
    sender = computation.message_sender
    print(
        f"case={case_name} variant={variant} repeat={repeat} "
        f"total={elapsed:.6f}s avg_cycle={elapsed / repeat:.6f}s"
    )
    print(
        f"  neighbors={len(computation.neighbors)} "
        f"constraints={len(computation.constraints)} "
        f"messages={sender.count} message_units={sender.total_size}"
    )

    by_operation: dict[str, tuple[int, float]] = {}
    for stat in stats:
        count, operation_elapsed = by_operation.get(stat.operation, (0, 0.0))
        by_operation[stat.operation] = (
            count + 1,
            operation_elapsed + stat.elapsed,
        )

    for operation, (count, operation_elapsed) in sorted(by_operation.items()):
        print(
            f"  {operation} count={count} total={operation_elapsed:.6f}s "
            f"avg={operation_elapsed / count:.6f}s"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        choices=sorted(CASES),
        default="generated",
        help="profiling case to run",
    )
    parser.add_argument("--variant", choices=["A", "B", "C"], default="B")
    parser.add_argument("--probability", type=float, default=0.0)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--neighbors", type=int, default=6)
    parser.add_argument("--constraints", type=int, default=18)
    parser.add_argument("--domain-size", type=int, default=6)
    parser.add_argument("--max-arity", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--cprofile",
        action="store_true",
        help="also print cProfile cumulative function timings",
    )
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be greater than zero")
    if args.neighbors < 1:
        parser.error("--neighbors must be greater than zero")
    if args.constraints < 1:
        parser.error("--constraints must be greater than zero")
    if args.domain_size < 1:
        parser.error("--domain-size must be greater than zero")
    if args.max_arity < 2:
        parser.error("--max-arity must be at least two")
    if not 0 <= args.probability <= 1:
        parser.error("--probability must be between 0 and 1")

    random.seed(args.seed)
    generated_config = GeneratedCaseConfig(
        neighbors=args.neighbors,
        constraints=args.constraints,
        domain_size=args.domain_size,
        max_arity=args.max_arity,
        seed=args.seed,
    )

    if args.cprofile:
        profiler = cProfile.Profile()
        profiler.enable()

    elapsed, stats, computation = run_case(
        args.case,
        args.variant,
        args.probability,
        args.repeat,
        generated_config,
    )

    if args.cprofile:
        profiler.disable()

    print_summary(args.case, args.variant, args.repeat, elapsed, stats, computation)

    if args.cprofile:
        pstats.Stats(profiler).strip_dirs().sort_stats("cumtime").print_stats(25)


if __name__ == "__main__":
    main()
