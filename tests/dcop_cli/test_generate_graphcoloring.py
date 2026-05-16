"""

Tests for the CLI commmand : generating graph coloring problems.

These tests only check that the command do not crash and the output
is a valid dcop, they do not check extensively the validity of the dcop
with regard to the requested model.


"""

from subprocess import CalledProcessError, check_output, STDOUT

import pytest

from pydcop.dcop.yamldcop import load_dcop
from tests.dcop_cli.utils import pydcop_cmd


def test_random_soft():
    dcop = run_generate("random", 10, 3, soft=True, p_edge=0.5)
    assert len(dcop.variables) == 10


def test_random_hard():
    dcop = run_generate("random", 10, 3, soft=False, p_edge=0.5)
    assert len(dcop.variables) == 10


def test_grid_hard():
    dcop = run_generate("grid", 9, 3, soft=False)
    assert len(dcop.variables) == 9
    assert len(dcop.constraints) == 12
    assert dcop.agents["a00"].capacity == 99


def test_capacity_can_be_overridden():
    dcop = run_generate("grid", 9, 3, soft=False, capacity=42)

    assert dcop.agents["a00"].capacity == 42


def test_grid_hard_max_objective():
    dcop = run_generate("grid", 4, 3, soft=False, objective="max")
    assert dcop.objective == "max"
    constraint = next(iter(dcop.constraints.values()))
    var1, var2 = constraint.dimensions
    color1, color2 = var1.domain.values[:2]
    assert constraint(**{var1.name: color1, var2.name: color1}) == -999999
    assert constraint(**{var1.name: color1, var2.name: color2}) == 0


def test_color_values_use_capital_english_letters():
    dcop = run_generate("grid", 4, 12, soft=False)
    domain = dcop.domains["colors"]

    assert list(domain.values) == list("ABCDEFGHIJKL")


def test_scalefree_hard():
    dcop = run_generate("scalefree", 20, 3, soft=False, m_edge=2)
    assert len(dcop.variables) == 20


def test_seed_makes_random_soft_generation_reproducible():
    output1 = run_generate_output("random", 10, 3, soft=True, p_edge=0.5, seed=12)
    output2 = run_generate_output("random", 10, 3, soft=True, p_edge=0.5, seed=12)

    assert output1 == output2


def test_objective_is_required():
    cmd = (
        f"{pydcop_cmd()} generate graph_coloring --graph grid "
        "--variables_count 4 --colors_count 3"
    )
    with pytest.raises(CalledProcessError):
        check_output(cmd, stderr=STDOUT, timeout=10, shell=True)


def run_generate(
    graph,
    variables_count,
    colors_count,
    intentional=False,
    soft=False,
    p_edge=None,
    m_edge=None,
    objective="min",
    seed=None,
    capacity=None,
):
    output = run_generate_output(
        graph,
        variables_count,
        colors_count,
        intentional,
        soft,
        p_edge,
        m_edge,
        objective,
        seed,
        capacity,
    )
    dcop = load_dcop(output)
    return dcop


def run_generate_output(
    graph,
    variables_count,
    colors_count,
    intentional=False,
    soft=False,
    p_edge=None,
    m_edge=None,
    objective="min",
    seed=None,
    capacity=None,
):
    cmd = f"{pydcop_cmd()} generate graph_coloring --graph {graph} " \
          f" --variables_count {variables_count} " \
          f" --colors_count {colors_count} "
    if p_edge:
        cmd += f" --p_edge {p_edge}"
    if m_edge:
        cmd += f" --m_edge {m_edge}"
    if intentional:
        cmd += " --intentional"
    if soft:
        cmd += " --soft"
    if objective:
        cmd += f" --objective {objective}"
    if seed is not None:
        cmd += f" --seed {seed}"
    if capacity is not None:
        cmd += f" --capacity {capacity}"
    output = check_output(cmd, stderr=STDOUT, timeout=10, shell=True)
    return output
