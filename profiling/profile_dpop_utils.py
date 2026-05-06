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

import argparse
import cProfile
import pstats
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from pydcop.algorithms import AlgorithmDef, ComputationDef, dpop
from pydcop.computations_graph.pseudotree import PseudoTreeLink, PseudoTreeNode
from pydcop.dcop.objects import Variable
from pydcop.dcop.relations import AsNAryFunctionRelation, NAryMatrixRelation


@dataclass
class OperationStats:
    operation: str
    elapsed: float
    left: str
    right: str
    result: str


def _relation_summary(relation):
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
    return "{} dims=[{}] shape={} cells={}".format(
        type(relation).__name__, names, shape, cells
    )


@contextmanager
def profile_dpop_relations(stats):
    original_join = dpop.join
    original_projection = dpop.projection

    def profiled_join(left, right):
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

    def profiled_projection(relation, variable, mode):
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


def _dpop_computation_def(variable, constraints, links, mode="min"):
    node = PseudoTreeNode(variable, constraints, links)
    algo_def = AlgorithmDef.build_with_default_param("dpop", mode=mode)
    return ComputationDef(node, algo_def)


def smart_light_case():
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


def child_util_case():
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


CASES = {
    "smart-light": smart_light_case,
    "child-util": child_util_case,
}


def run_case(case_name, repeat):
    stats = []
    start = perf_counter()
    with profile_dpop_relations(stats):
        for _ in range(repeat):
            computation = CASES[case_name]()
            computation._compute_utils_msg()
    elapsed = perf_counter() - start
    return elapsed, stats


def print_summary(case_name, repeat, elapsed, stats, details):
    print("case={} repeat={} total={:.6f}s".format(case_name, repeat, elapsed))
    by_operation = {}
    for stat in stats:
        by_operation.setdefault(stat.operation, [0, 0.0])
        by_operation[stat.operation][0] += 1
        by_operation[stat.operation][1] += stat.elapsed

    for operation, (count, op_elapsed) in sorted(by_operation.items()):
        average = op_elapsed / count if count else 0
        print(
            "  {} count={} total={:.6f}s avg={:.6f}s".format(
                operation, count, op_elapsed, average
            )
        )

    if details:
        for index, stat in enumerate(stats, start=1):
            print(
                "  #{:03d} {} {:.6f}s\n"
                "       left:   {}\n"
                "       right:  {}\n"
                "       result: {}".format(
                    index,
                    stat.operation,
                    stat.elapsed,
                    stat.left,
                    stat.right,
                    stat.result,
                )
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        choices=sorted(CASES),
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

    if args.cprofile:
        profiler = cProfile.Profile()
        profiler.enable()

    elapsed, stats = run_case(args.case, args.repeat)

    if args.cprofile:
        profiler.disable()

    print_summary(args.case, args.repeat, elapsed, stats, args.details)

    if args.cprofile:
        pstats.Stats(profiler).strip_dirs().sort_stats("cumtime").print_stats(25)


if __name__ == "__main__":
    main()
