"""

Tests for the CLI commmand : generating graph coloring problems.

These tests only check that the command do not crash and the output
is a valid dcop, they do not check extensively the validity of the dcop
with regard to the requested model.


"""

from subprocess import check_output, STDOUT

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


def test_grid_hard_max_objective():
    dcop = run_generate("grid", 4, 3, soft=False, objective="max")
    assert dcop.objective == "max"
    constraint = next(iter(dcop.constraints.values()))
    var1, var2 = constraint.dimensions
    assert constraint(**{var1.name: "R", var2.name: "R"}) == -999999
    assert constraint(**{var1.name: "R", var2.name: "G"}) == 0


def test_scalefree_hard():
    dcop = run_generate("scalefree", 20, 3, soft=False, m_edge=2)
    assert len(dcop.variables) == 20


def run_generate(graph, variables_count, colors_count, intentional=False,
                 soft=False,
                 p_edge=None, m_edge=None, objective=None):
    # filename = instance_path(filename)
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
    output = check_output(cmd, stderr=STDOUT, timeout=10, shell=True)
    dcop = load_dcop(output)
    return dcop
