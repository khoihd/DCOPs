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


def run_generate_output(extensive=False):
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

    return check_output(cmd, stderr=STDOUT, timeout=10, shell=True)
