from queue import Queue
from threading import Thread
from types import SimpleNamespace

import pytest

import pydcop.commands._utils as utils


def test_write_output_file_creates_parent_directories(tmp_path):
    output = tmp_path / "nested" / "deeper" / "result.txt"

    utils.write_output_file(output, "content")

    assert output.read_text(encoding="utf-8") == "content"


def test_collect_thread_stops_on_sentinel():
    metrics_queue = Queue()
    collected = []
    thread = Thread(
        target=utils.collect_tread,
        args=[metrics_queue, collected.append],
    )

    thread.start()
    metrics_queue.put((0, {"cost": 0}))
    metrics_queue.put(utils.METRICS_COLLECTOR_STOP)
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert collected == [{"cost": 0}]


def test_stop_collect_thread_sends_sentinel_and_joins():
    class FakeQueue:
        def __init__(self):
            self.items = []

        def put(self, item):
            self.items.append(item)

    class FakeThread:
        def join(self, timeout=None):
            self.joined_timeout = timeout

    queue = FakeQueue()
    thread = FakeThread()

    utils.stop_collect_thread(queue, thread)

    assert queue.items == [utils.METRICS_COLLECTOR_STOP]
    assert thread.joined_timeout == 1


def test_load_modules_validates_distribution_module(monkeypatch, capsys):
    monkeypatch.setattr(
        utils,
        "import_module",
        lambda module_name: SimpleNamespace(),
    )

    with pytest.raises(SystemExit):
        utils._load_modules("broken_dist", "dsa")

    captured = capsys.readouterr()
    assert (
        "distribution method broken_dist does not expose required callable distribute"
        in captured.out
    )


def test_load_modules_validates_algorithm_graph_type(monkeypatch, capsys):
    monkeypatch.setattr(
        utils,
        "load_algorithm_module",
        lambda algo_name: SimpleNamespace(),
    )

    with pytest.raises(SystemExit):
        utils._load_modules(None, "broken_algo")

    captured = capsys.readouterr()
    assert (
        "algorithm broken_algo does not expose required attribute GRAPH_TYPE"
        in captured.out
    )


def test_load_modules_validates_graph_module(monkeypatch, capsys):
    monkeypatch.setattr(
        utils,
        "load_algorithm_module",
        lambda algo_name: SimpleNamespace(GRAPH_TYPE="broken_graph"),
    )
    monkeypatch.setattr(
        utils,
        "import_module",
        lambda module_name: SimpleNamespace(),
    )

    with pytest.raises(SystemExit):
        utils._load_modules(None, "algo")

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

    monkeypatch.setattr(utils, "import_module", import_module)
    monkeypatch.setattr(
        utils,
        "load_algorithm_module",
        lambda algo_name: algo_module,
    )

    loaded_dist, loaded_algo, loaded_graph = utils._load_modules(
        "test_dist", "test_algo"
    )

    assert loaded_dist is dist_module
    assert loaded_algo is algo_module
    assert loaded_graph is graph_module
