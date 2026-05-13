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

import json
import sys
from subprocess import STDOUT, check_output

import pytest

from tests.dcop_cli.utils import instance_path


def test_solve_accepts_pulp_as_algorithm():
    output = check_output(
        [
            sys.executable,
            "-m",
            "pydcop.dcop_cli",
            "-v",
            "0",
            "solve",
            "-a",
            "pulp",
            instance_path("graph_coloring1.yaml"),
        ],
        stderr=STDOUT,
        timeout=10,
    )

    result = json.loads(output.decode(encoding="utf-8"))
    assert result["status"] == "FINISHED"
    assert result["solver"] == "pulp"
    assert result["solver_solution_status"] == "Optimal Solution Found"
    assert result["assignment"] == {"v1": "R", "v2": "G", "v3": "R"}
    assert result["cost"] == pytest.approx(-0.1)


def test_solve_pulp_handles_random_graph_instance():
    output = check_output(
        [
            sys.executable,
            "-m",
            "pydcop.dcop_cli",
            "-v",
            "0",
            "solve",
            "-a",
            "pulp",
            instance_path("random_graph_6_3_0.7.yaml"),
        ],
        stderr=STDOUT,
        timeout=10,
    )

    result = json.loads(output.decode(encoding="utf-8"))
    assert result["status"] == "FINISHED"
    assert result["solver"] == "pulp"
    assert result["cost"] == pytest.approx(35)


def test_solve_pulp_accepts_threads_parameter():
    output = check_output(
        [
            sys.executable,
            "-m",
            "pydcop.dcop_cli",
            "-v",
            "0",
            "solve",
            "-a",
            "pulp",
            "-p",
            "threads:4",
            instance_path("graph_coloring1.yaml"),
        ],
        stderr=STDOUT,
        timeout=10,
    )

    result = json.loads(output.decode(encoding="utf-8"))
    assert result["status"] == "FINISHED"
    assert result["solver"] == "pulp"
    assert result["solver_backend"] == "cbc"
    assert result["solver_threads"] == 4
    assert result["solver_solution_status"] == "Optimal Solution Found"
