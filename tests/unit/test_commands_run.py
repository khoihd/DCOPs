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

import argparse
import inspect

from pydcop.commands import run
from pydcop.infrastructure.run import run_local_process_dcop, run_local_thread_dcop


def test_run_parser_has_no_command_level_infinity_argument():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    run.set_parser(subparsers)

    args = parser.parse_args(
        [
            "run",
            "-a",
            "maxsum",
            "-d",
            "oneagent",
            "-s",
            "scenario.yaml",
            "dcop.yaml",
        ]
    )

    assert not hasattr(args, "infinity")


def test_local_runners_provide_default_infinity():
    thread_default = inspect.signature(run_local_thread_dcop).parameters[
        "infinity"
    ].default
    process_default = inspect.signature(run_local_process_dcop).parameters[
        "infinity"
    ].default

    assert thread_default == float("inf")
    assert process_default == float("inf")
