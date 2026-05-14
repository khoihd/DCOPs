from types import SimpleNamespace

from pydcop.infrastructure.ui import UiServer


class AgentDef:
    def extra_attr(self):
        return {"capacity": 10}


def _ui_server(agent):
    server = UiServer.__new__(UiServer)
    server._agent = agent
    return server


def _agent(replication_comp=None):
    return SimpleNamespace(
        name="a1",
        agent_def=AgentDef(),
        address="addr1",
        replication_comp=replication_comp,
        computations=lambda: [],
    )


def test_agent_data_has_no_replicas_without_replication_computation():
    agent = _agent()
    server = _ui_server(agent)

    assert server._agent_data(agent)["replicas"] == []


def test_agent_data_includes_hosted_replicas():
    replication_comp = SimpleNamespace(
        hosted_replicas={
            "c2": ("a3", 4),
            "c1": ("a2", 2),
        }
    )
    agent = _agent(replication_comp)
    server = _ui_server(agent)

    assert server._agent_data(agent)["replicas"] == [
        {"name": "c1", "origin": "a2", "footprint": 2},
        {"name": "c2", "origin": "a3", "footprint": 4},
    ]
