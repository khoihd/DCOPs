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

import inspect
from types import SimpleNamespace

from pydcop.infrastructure import run
from pydcop.infrastructure.run import run_local_process_dcop, run_local_thread_dcop


class FakeOrchestrator:
    def deploy_computations(self):
        pass

    def run(self, timeout):
        pass

    def wait_ready(self):
        pass

    def end_metrics(self):
        return {"assignment": {"x": 1}}

    def stop_agents(self, timeout):
        pass

    def stop(self):
        pass


def test_default_infinity_is_symbolic():
    assert run.DEFAULT_INFINITY == float("inf")
    assert run.INFINITY == run.DEFAULT_INFINITY

    thread_default = inspect.signature(run_local_thread_dcop).parameters[
        "infinity"
    ].default
    process_default = inspect.signature(run_local_process_dcop).parameters[
        "infinity"
    ].default

    assert thread_default == run.DEFAULT_INFINITY
    assert process_default == run.DEFAULT_INFINITY


def test_solve_uses_local_runner_default_infinity(monkeypatch):
    captured = {}

    def fake_load_algorithm_module(algo):
        assert algo == "fake"
        return SimpleNamespace()

    def fake_run_local_thread_dcop(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeOrchestrator()

    monkeypatch.setattr(run, "load_algorithm_module", fake_load_algorithm_module)
    monkeypatch.setattr(run, "run_local_thread_dcop", fake_run_local_thread_dcop)

    algo_def = SimpleNamespace(algo="fake")
    graph = object()
    distribution = object()
    dcop = SimpleNamespace(objective="min")

    assignment = run.solve(dcop, algo_def, distribution, graph, timeout=0)

    assert assignment == {"x": 1}
    assert captured["args"] == (algo_def, graph, distribution, dcop)
    assert "infinity" not in captured["kwargs"]
