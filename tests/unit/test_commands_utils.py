from types import SimpleNamespace

import pytest

import pydcop.commands._utils as utils


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
