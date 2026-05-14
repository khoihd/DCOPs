import argparse
from types import SimpleNamespace

from pydcop.commands.replica_dist import (
    aggregate_replication_metrics,
    build_result,
    format_replica_distribution,
)
from pydcop.commands import replica_dist


def test_parser_accepts_algo_params_and_has_no_infinity_argument():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    replica_dist.set_parser(subparsers)

    args = parser.parse_args(
        [
            "replica_dist",
            "-k",
            "2",
            "-r",
            "dist_ucs",
            "-a",
            "dsa",
            "-p",
            "variant:C",
            "-p",
            "probability:0.5",
            "-d",
            "dist.yaml",
            "problem.yaml",
        ]
    )

    assert args.algo_params == ["variant:C", "probability:0.5"]
    assert not hasattr(args, "infinity")


def test_aggregate_replication_metrics_sums_external_message_metrics():
    metrics = {
        "a1": {"count_ext_msg": 2, "size_ext_msg": 30},
        "a2": {"count_ext_msg": 3, "size_ext_msg": 40},
    }

    assert aggregate_replication_metrics(metrics) == (5, 70)


def test_format_replica_distribution_sorts_computations_and_hosts():
    replica_hosts = {
        "c2": {"a3", "a1"},
        "c1": {"a2"},
    }

    assert format_replica_distribution(replica_hosts) == {
        "c1": ["a2"],
        "c2": ["a1", "a3"],
    }


def test_build_result_includes_inputs_metrics_and_replica_distribution():
    args = SimpleNamespace(
        dcop_files=["problem.yaml"],
        algo="dsa",
        algo_params=["variant:C"],
        replication="dist_ucs",
        ktarget=3,
        distribution="dist.yaml",
    )

    result = build_result(
        args,
        duration=1.25,
        msg_count=5,
        msg_size=70,
        replica_dist={"c1": ["a2"]},
    )

    assert result == {
        "inputs": {
            "dcop": ["problem.yaml"],
            "algo": "dsa",
            "algo_params": ["variant:C"],
            "replication": "dist_ucs",
            "k": 3,
            "distribution": "dist.yaml",
        },
        "metrics": {
            "duration": 1.25,
            "msg_count": 5,
            "msg_size": 70,
        },
        "replica_dist": {"c1": ["a2"]},
    }


def test_run_cmd_uses_algo_params_and_runner_default_infinity(monkeypatch):
    dcop = SimpleNamespace(objective="min")
    algo_module = SimpleNamespace(GRAPH_TYPE="fake_graph")
    graph_module = SimpleNamespace(build_computation_graph=lambda dcop: "cg")
    orchestrator = _FakeOrchestrator()
    runner_calls = []
    build_algo_calls = []

    def build_algo_def(algo_module, algo_name, objective, cli_params):
        build_algo_calls.append((algo_module, algo_name, objective, cli_params))
        return "algo_def"

    def run_local_thread_dcop(*args, **kwargs):
        runner_calls.append((args, kwargs))
        return orchestrator

    monkeypatch.setattr(replica_dist, "load_dcop_from_file", lambda files: dcop)
    monkeypatch.setattr(
        replica_dist, "load_algorithm_module", lambda algo: algo_module
    )
    monkeypatch.setattr(replica_dist, "build_algo_def", build_algo_def)
    monkeypatch.setattr(replica_dist, "import_module", lambda name: graph_module)
    monkeypatch.setattr(
        replica_dist, "load_dist_from_file", lambda distribution: "distribution"
    )
    monkeypatch.setattr(replica_dist, "run_local_thread_dcop", run_local_thread_dcop)

    args = SimpleNamespace(
        dcop_files=["problem.yaml"],
        algo="dsa",
        algo_params=["variant:C"],
        replication="dist_ucs",
        ktarget=2,
        distribution="dist.yaml",
        mode="thread",
        output=None,
    )

    try:
        replica_dist.run_cmd(args)
    except SystemExit as exc:
        assert exc.code == 0

    assert build_algo_calls == [(algo_module, "dsa", "min", ["variant:C"])]
    assert runner_calls == [
        (
            ("algo_def", "cg", "distribution", dcop),
            {"replication": "dist_ucs"},
        )
    ]


class _FakeOrchestrator:
    def __init__(self):
        self.mgt = SimpleNamespace(replica_hosts={"c1": {"a2"}})

    def deploy_computations(self):
        pass

    def start_replication(self, ktarget):
        self.ktarget = ktarget

    def wait_ready(self):
        pass

    def replication_metrics(self):
        return {}

    def stop_agents(self, timeout):
        pass

    def stop(self):
        pass
