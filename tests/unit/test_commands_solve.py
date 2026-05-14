from queue import Queue
from threading import Thread
from types import SimpleNamespace

import pytest

import pydcop.commands.solve as solve_cmd


def test_collect_thread_stops_on_sentinel():
    metrics_queue = Queue()
    collected = []
    thread = Thread(
        target=solve_cmd.collect_tread,
        args=[metrics_queue, collected.append],
    )

    thread.start()
    metrics_queue.put((0, {"cost": 0}))
    metrics_queue.put(solve_cmd.METRICS_COLLECTOR_STOP)
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert collected == [{"cost": 0}]


def test_run_cmd_stops_metrics_collector(monkeypatch, capsys):
    dcop = SimpleNamespace(
        objective="min",
        agents={"a1": SimpleNamespace()},
        dist_hints=None,
    )
    dist_module = SimpleNamespace(distribute=lambda *args, **kwargs: "distribution")
    algo_module = SimpleNamespace(
        memory_footprint_estimate=lambda *args, **kwargs: 0,
        communication_load=lambda *args, **kwargs: 0,
    )
    graph_module = SimpleNamespace(build_computation_graph=lambda dcop: "cg")
    fake_queue = _FakeQueue()
    fake_threads = []

    class FakeThread:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon
            self.started = False
            self.joined = False
            fake_threads.append(self)

        def start(self):
            self.started = True

        def join(self, timeout=None):
            self.joined = True
            self.timeout = timeout

    monkeypatch.setattr(solve_cmd, "Queue", lambda: fake_queue)
    monkeypatch.setattr(solve_cmd, "Thread", FakeThread)
    monkeypatch.setattr(solve_cmd, "load_dcop_from_file", lambda files: dcop)
    monkeypatch.setattr(
        solve_cmd,
        "_load_modules",
        lambda distribution, algo: (dist_module, algo_module, graph_module),
    )
    monkeypatch.setattr(
        solve_cmd,
        "build_algo_def",
        lambda algo_module, algo_name, objective, cli_params: "algo_def",
    )
    monkeypatch.setattr(
        solve_cmd,
        "run_local_thread_dcop",
        lambda *args, **kwargs: _FakeOrchestrator(),
    )
    monkeypatch.setattr(solve_cmd, "timeout_stopped", False)
    monkeypatch.setattr(solve_cmd, "run_metrics", None)
    monkeypatch.setattr(solve_cmd, "end_metrics", None)
    monkeypatch.setattr(solve_cmd, "output_file", None)

    args = SimpleNamespace(
        infinity=float("inf"),
        output=None,
        collect_on="value_change",
        dcop_files=["problem.yaml"],
        algo="dsa",
        run_metrics=None,
        end_metrics=None,
        distribution="oneagent",
        algo_params=["variant:C"],
        mode="thread",
        period=None,
        delay=None,
        uiport=None,
    )

    with pytest.raises(SystemExit) as exc:
        solve_cmd.run_cmd(args)

    assert exc.value.code == 0
    assert fake_queue.items == [solve_cmd.METRICS_COLLECTOR_STOP]
    assert fake_threads[0].started
    assert fake_threads[0].joined
    assert fake_threads[0].timeout == 1
    assert "FINISHED" in capsys.readouterr().out


class _FakeQueue:
    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)


class _FakeOrchestrator:
    status = "FINISHED"

    def deploy_computations(self):
        pass

    def run(self, timeout=None):
        self.timeout = timeout

    def end_metrics(self):
        return {
            "cycle": 0,
            "time": 0,
            "cost": 0,
            "violation": 0,
            "msg_count": 0,
            "msg_size": 0,
        }
