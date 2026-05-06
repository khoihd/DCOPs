# BSD-3-Clause License
#
# Copyright 2017 Orange

"""Profile DPOP UTIL join/projection behavior.

This script is intentionally kept outside the regular test suite. It measures
the current `_compute_utils_msg()` hot path without changing DPOP behavior or
adding brittle timing assertions.

Run from the repository root, for example:

    conda run -n khoihd python profiling/profile_dpop_utils.py --repeat 10
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np

from pydcop.algorithms import AlgorithmDef, ComputationDef, dpop
from pydcop.computations_graph.pseudotree import PseudoTreeLink, PseudoTreeNode
from pydcop.dcop.objects import Variable
from pydcop.dcop.relations import AsNAryFunctionRelation, NAryMatrixRelation


@dataclass(frozen=True, slots=True)
class OperationStats:
    operation: str
    elapsed: float
    left: str
    right: str
    result: str


CaseFactory = Callable[[], dpop.DpopAlgo]


def _relation_summary(relation: Any) -> str:
    dimensions = getattr(relation, "dimensions", [])
    names = ",".join(v.name for v in dimensions) or "-"
    shape = getattr(relation, "shape", None)
    if shape is None and hasattr(relation, "_m"):
        shape = relation._m.shape
    cells = 1
    if shape:
        for size in shape:
            cells *= size
    else:
        cells = 0
    return f"{type(relation).__name__} dims=[{names}] shape={shape} cells={cells}"


@contextmanager
def profile_dpop_relations(stats: list[OperationStats]) -> Iterator[None]:
    original_join = dpop.join
    original_projection = dpop.projection

    def profiled_join(left: Any, right: Any) -> Any:
        start = perf_counter()
        result = original_join(left, right)
        elapsed = perf_counter() - start
        stats.append(
            OperationStats(
                "join",
                elapsed,
                _relation_summary(left),
                _relation_summary(right),
                _relation_summary(result),
            )
        )
        return result

    def profiled_projection(relation: Any, variable: Variable, mode: str) -> Any:
        start = perf_counter()
        result = original_projection(relation, variable, mode)
        elapsed = perf_counter() - start
        stats.append(
            OperationStats(
                "projection",
                elapsed,
                _relation_summary(relation),
                variable.name,
                _relation_summary(result),
            )
        )
        return result

    dpop.join = profiled_join
    dpop.projection = profiled_projection
    try:
        yield
    finally:
        dpop.join = original_join
        dpop.projection = original_projection


def _dpop_computation_def(
    variable: Variable,
    constraints: Iterable[Any],
    links: Iterable[PseudoTreeLink],
    mode="min",
) -> ComputationDef:
    node = PseudoTreeNode(variable, constraints, links)
    algo_def = AlgorithmDef.build_with_default_param("dpop", mode=mode)
    return ComputationDef(node, algo_def)


def smart_light_case() -> dpop.DpopAlgo:
    l1 = Variable("l1", list(range(10)))
    l2 = Variable("l2", list(range(10)))
    l3 = Variable("l3", list(range(10)))
    y1 = Variable("y1", list(range(10)))

    @AsNAryFunctionRelation(l1, l2, l3, y1)
    def scene_rel(l1_, l2_, l3_, y1_):
        if y1_ == round((l1_ + l2_ + l3_) / 3):
            return 0
        return 10000

    @AsNAryFunctionRelation(l3)
    def cost_l3(l3_):
        return l3_

    return dpop.DpopAlgo(
        _dpop_computation_def(
            l3,
            constraints=[scene_rel, cost_l3],
            links=[
                PseudoTreeLink("parent", l3.name, l2.name),
                PseudoTreeLink("pseudo_parent", l3.name, l1.name),
                PseudoTreeLink("pseudo_parent", l3.name, y1.name),
            ],
        )
    )


def child_util_case() -> dpop.DpopAlgo:
    parent = Variable("x0", list(range(7)))
    variable = Variable("x1", list(range(8)))
    pseudo_parent = Variable("x2", list(range(6)))
    child_sep = Variable("x3", list(range(5)))

    @AsNAryFunctionRelation(parent, variable, pseudo_parent)
    def local_rel(x0, x1, x2):
        return (x0 - x1) ** 2 + x2

    child_util = NAryMatrixRelation(
        [variable, pseudo_parent, child_sep],
        np.fromfunction(lambda x1, x2, x3: x1 + x2 * 2 + x3 * 3, (8, 6, 5)),
        name="child_util",
    )
    computation = dpop.DpopAlgo(
        _dpop_computation_def(
            variable,
            constraints=[local_rel],
            links=[
                PseudoTreeLink("parent", variable.name, parent.name),
                PseudoTreeLink("pseudo_parent", variable.name, pseudo_parent.name),
                PseudoTreeLink("children", variable.name, child_sep.name),
            ],
        )
    )
    computation._joined_utils = child_util
    return computation


CASES: dict[str, CaseFactory] = {
    "smart-light": smart_light_case,
    "child-util": child_util_case,
}


def run_case(case_name: str, repeat: int) -> tuple[float, list[OperationStats]]:
    stats: list[OperationStats] = []
    start = perf_counter()
    with profile_dpop_relations(stats):
        for _ in range(repeat):
            computation = CASES[case_name]()
            computation._compute_utils_msg()
    elapsed = perf_counter() - start
    return elapsed, stats


def print_summary(
    case_name: str,
    repeat: int,
    elapsed: float,
    stats: Sequence[OperationStats],
    details: bool,
) -> None:
    print(f"case={case_name} repeat={repeat} total={elapsed:.6f}s")
    by_operation: dict[str, tuple[int, float]] = {}
    for stat in stats:
        count, op_elapsed = by_operation.get(stat.operation, (0, 0.0))
        by_operation[stat.operation] = (count + 1, op_elapsed + stat.elapsed)

    for operation, (count, op_elapsed) in sorted(by_operation.items()):
        average = op_elapsed / count if count else 0
        print(
            f"  {operation} count={count} "
            f"total={op_elapsed:.6f}s avg={average:.6f}s"
        )

    if details:
        for index, stat in enumerate(stats, start=1):
            print(
                f"  #{index:03d} {stat.operation} {stat.elapsed:.6f}s\n"
                f"       left:   {stat.left}\n"
                f"       right:  {stat.right}\n"
                f"       result: {stat.result}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        choices=["all"] + sorted(CASES),
        default="smart-light",
        help="profiling case to run",
    )
    parser.add_argument("--repeat", type=int, default=5, help="number of runs")
    parser.add_argument(
        "--details",
        action="store_true",
        help="print each join/projection operation",
    )
    parser.add_argument(
        "--cprofile",
        action="store_true",
        help="also print cProfile cumulative function timings",
    )
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be greater than zero")

    if args.cprofile:
        profiler = cProfile.Profile()
        profiler.enable()

    case_names = sorted(CASES) if args.case == "all" else [args.case]
    results = [(case_name, *run_case(case_name, args.repeat)) for case_name in case_names]

    if args.cprofile:
        profiler.disable()

    for index, (case_name, elapsed, stats) in enumerate(results):
        if index:
            print()
        print_summary(case_name, args.repeat, elapsed, stats, args.details)

    if args.cprofile:
        pstats.Stats(profiler).strip_dirs().sort_stats("cumtime").print_stats(25)


if __name__ == "__main__":
    main()
