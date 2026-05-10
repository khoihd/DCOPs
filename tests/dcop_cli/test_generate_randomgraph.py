from subprocess import check_output, STDOUT

from pydcop.dcop.yamldcop import load_dcop
from tests.dcop_cli.utils import pydcop_cmd


def test_generate_random_graph():
    output = run_generate_output(seed=12)
    dcop = load_dcop(output)

    assert dcop.name == "RandomGraph_6_3_0.7"
    assert dcop.objective == "min"
    assert len(dcop.variables) == 6
    assert len(dcop.agents) == 6


def test_seed_makes_random_graph_output_reproducible():
    output1 = run_generate_output(seed=12)
    output2 = run_generate_output(seed=12)

    assert output1 == output2


def test_no_agents_skips_agents():
    output = run_generate_output(seed=12, no_agents=True)
    dcop = load_dcop(output)

    assert dcop.agents == {}


def run_generate_output(seed=None, no_agents=False):
    cmd = (
        f"{pydcop_cmd()} generate random_graph "
        "--variables_count 6 "
        "--domain_size 3 "
        "--p_edge 0.7 "
        "--objective min"
    )
    if seed is not None:
        cmd += f" --seed {seed}"
    if no_agents:
        cmd += " --no_agents"

    return check_output(cmd, stderr=STDOUT, timeout=10, shell=True)
