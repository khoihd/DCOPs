from types import SimpleNamespace
from queue import Queue
from threading import Thread

import pytest

import pydcop.commands.orchestrator as orchestrator_cmd


def test_collect_thread_stops_on_sentinel():
    metrics_queue = Queue()
    collected = []
    thread = Thread(
        target=orchestrator_cmd.collect_tread,
        args=[metrics_queue, collected.append],
    )

    thread.start()
    metrics_queue.put((0, {"cost": 0}))
    metrics_queue.put(orchestrator_cmd.METRICS_COLLECTOR_STOP)
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert collected == [{"cost": 0}]


def test_run_cmd_uses_orchestrator_default_infinity(monkeypatch, capsys):
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
    created_orchestrators = []

    class FakeOrchestrator:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.status = "FINISHED"
            created_orchestrators.append(self)

        def start(self):
            pass

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

    monkeypatch.setattr(
        orchestrator_cmd,
        "_load_modules",
        lambda distribution, algo: (dist_module, algo_module, graph_module),
    )
    monkeypatch.setattr(orchestrator_cmd, "load_dcop_from_file", lambda files: dcop)
    monkeypatch.setattr(
        orchestrator_cmd,
        "build_algo_def",
        lambda algo_module, algo_name, objective, cli_params: "algo_def",
    )
    monkeypatch.setattr(
        orchestrator_cmd,
        "HttpCommunicationLayer",
        lambda address: ("comm", address),
    )
    monkeypatch.setattr(orchestrator_cmd, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(orchestrator_cmd, "timeout_stopped", False)
    monkeypatch.setattr(orchestrator_cmd, "run_metrics", None)
    monkeypatch.setattr(orchestrator_cmd, "end_metrics", None)
    monkeypatch.setattr(orchestrator_cmd, "output_file", None)

    args = SimpleNamespace(
        output=None,
        collect_on="value_change",
        dcop_files=["problem.yaml"],
        period=None,
        run_metrics=None,
        end_metrics=None,
        distribution="oneagent",
        algo="dsa",
        scenario=None,
        algo_params=["variant:C"],
        ktarget=None,
        port=None,
        address=None,
        uiport=None,
    )

    with pytest.raises(SystemExit) as exc:
        orchestrator_cmd.run_cmd(args)

    assert exc.value.code == 0
    created = created_orchestrators[0]
    assert created.args == (
        "algo_def",
        "cg",
        "distribution",
        ("comm", (None, 9000)),
        dcop,
    )
    assert "collector" in created.kwargs
    assert created.kwargs["collect_moment"] == "value_change"
    assert created.kwargs["collect_period"] is None
    assert created.kwargs["ui_port"] is None
    assert "FINISHED" in capsys.readouterr().out


def test_load_modules_validates_distribution_module(monkeypatch, capsys):
    monkeypatch.setattr(
        orchestrator_cmd,
        "import_module",
        lambda module_name: SimpleNamespace(),
    )

    with pytest.raises(SystemExit):
        orchestrator_cmd._load_modules("broken_dist", "dsa")

    captured = capsys.readouterr()
    assert (
        "distribution method broken_dist does not expose required callable distribute"
        in captured.out
    )


def test_load_modules_validates_algorithm_graph_type(monkeypatch, capsys):
    monkeypatch.setattr(
        orchestrator_cmd,
        "load_algorithm_module",
        lambda algo_name: SimpleNamespace(),
    )

    with pytest.raises(SystemExit):
        orchestrator_cmd._load_modules(None, "broken_algo")

    captured = capsys.readouterr()
    assert (
        "algorithm broken_algo does not expose required attribute GRAPH_TYPE"
        in captured.out
    )


def test_load_modules_validates_graph_module(monkeypatch, capsys):
    monkeypatch.setattr(
        orchestrator_cmd,
        "load_algorithm_module",
        lambda algo_name: SimpleNamespace(GRAPH_TYPE="broken_graph"),
    )
    monkeypatch.setattr(
        orchestrator_cmd,
        "import_module",
        lambda module_name: SimpleNamespace(),
    )

    with pytest.raises(SystemExit):
        orchestrator_cmd._load_modules(None, "algo")

    captured = capsys.readouterr()
    assert (
        "computation graph type broken_graph does not expose required callable "
        "build_computation_graph"
    ) in captured.out


def test_load_modules_returns_validated_modules(monkeypatch):
    dist_module = SimpleNamespace(distribute=lambda *args, **kwargs: None)
    algo_module = SimpleNamespace(GRAPH_TYPE="test_graph")
    graph_module = SimpleNamespace(build_computation_graph=lambda dcop: None)

    def import_module(module_name):
        if module_name == "pydcop.distribution.test_dist":
            return dist_module
        if module_name == "pydcop.computations_graph.test_graph":
            return graph_module
        raise AssertionError(f"Unexpected module import: {module_name}")

    monkeypatch.setattr(orchestrator_cmd, "import_module", import_module)
    monkeypatch.setattr(
        orchestrator_cmd,
        "load_algorithm_module",
        lambda algo_name: algo_module,
    )

    loaded_dist, loaded_algo, loaded_graph = orchestrator_cmd._load_modules(
        "test_dist", "test_algo"
    )

    assert loaded_dist is dist_module
    assert loaded_algo is algo_module
    assert loaded_graph is graph_module
