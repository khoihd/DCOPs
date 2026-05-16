from subprocess import STDOUT, check_output

from pydcop.dcop.yamldcop import load_dcop
from tests.dcop_cli.utils import pydcop_cmd


def test_mixed_problem_defaults_to_intentional_constraints():
    output = run_generate_output()

    assert b"type: intention" in output
    assert b"type: extensional" not in output
    dcop = load_dcop(output)
    assert len(dcop.constraints) == 2


def test_mixed_problem_extensive_flag_generates_extensional_constraints():
    output = run_generate_output(extensive=True)

    assert b"type: extensional" in output
    assert b"type: intention" not in output
    dcop = load_dcop(output)
    assert len(dcop.constraints) == 2


def test_mixed_problem_capacity_is_written_on_agents():
    output = run_generate_output(capacity=25)

    dcop = load_dcop(output)
    assert dcop.agents["a1"].capacity == 25
    assert dcop.agents["a2"].capacity == 25


def test_mixed_problem_defaults_capacity_on_agents():
    output = run_generate_output()

    dcop = load_dcop(output)
    assert dcop.agents["a1"].capacity == 99
    assert dcop.agents["a2"].capacity == 99


def run_generate_output(extensive=False, capacity=None):
    cmd = (
        f"{pydcop_cmd()} generate mixed_problem "
        "-v 2 "
        "-c 2 "
        "-H 0.5 "
        "-A 1 "
        "-r 2 "
        "-d 1"
    )
    if extensive:
        cmd += " --extensive"
    if capacity is not None:
        cmd += f" --capacity {capacity}"

    return check_output(cmd, stderr=STDOUT, timeout=10, shell=True)
