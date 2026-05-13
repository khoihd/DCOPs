import json
from collections import defaultdict
from unittest.mock import Mock

from pydcop.infrastructure.orchestrator import (
    AgentsMgt,
    ComputationFinishedMessage,
    RepairReadyMessage,
)
from pydcop.utils.simple_repr import simple_repr


def test_serialize_RepairReadyMessage():
    msg = RepairReadyMessage('a1', ['c1', 'c2', 'c3'])

    msg_repr = simple_repr(msg)
    json.dumps(msg_repr)


class FakeDcop:
    variables = {}

    def solution_cost(self, assignment, infinity):
        return 0, 0


def _metrics_manager(collect_moment):
    mgt = object.__new__(AgentsMgt)
    mgt._current_cycle = 3
    mgt._collect_moment = collect_moment
    mgt._agent_cycle_values = defaultdict(dict)
    mgt._agt_cycle_metrics = defaultdict(dict)
    mgt._agt_cycle_metrics[3]['a1'] = {
        'count_ext_msg': {},
        'size_ext_msg': {},
        'cycles': {'c1': 5},
    }
    mgt._dcop = FakeDcop()
    mgt.infinity = float('inf')
    mgt.start_time = None
    mgt.logger = Mock()
    return mgt


def test_global_metrics_cycle_change_uses_completed_cycle():
    metrics = _metrics_manager('cycle_change').global_metrics('RUNNING', 12)

    assert metrics['cycle'] == 3


def test_global_metrics_period_uses_agent_cycle_count():
    metrics = _metrics_manager('period').global_metrics('RUNNING', 12)

    assert metrics['cycle'] == 5


def _end_message_manager():
    mgt = object.__new__(AgentsMgt)
    mgt.logger = Mock()
    mgt._computation_status = {"c1": "", "c2": ""}
    mgt._orchestrator_stop_agents = Mock()
    return mgt


def test_computation_finished_message_stops_when_all_finished():
    mgt = _end_message_manager()
    mgt._computation_status["c1"] = "finished"

    mgt._on_computation_end_msg(
        "a2", ComputationFinishedMessage("a2", "c2", "finished"), 0
    )

    assert mgt._computation_status == {"c1": "finished", "c2": "finished"}
    mgt._orchestrator_stop_agents.assert_called_once_with()


def test_computation_running_status_resets_finished_state():
    mgt = _end_message_manager()
    mgt._computation_status = {"c1": "finished", "c2": "finished"}

    mgt._on_computation_end_msg(
        "a2", ComputationFinishedMessage("a2", "c2", "running"), 0
    )

    assert mgt._computation_status == {"c1": "finished", "c2": "running"}
    mgt._orchestrator_stop_agents.assert_not_called()
