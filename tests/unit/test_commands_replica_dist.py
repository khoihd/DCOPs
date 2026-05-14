from types import SimpleNamespace

from pydcop.commands.replica_dist import (
    aggregate_replication_metrics,
    build_result,
    format_replica_distribution,
)


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
