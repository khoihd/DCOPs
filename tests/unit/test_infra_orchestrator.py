import json
from collections import defaultdict
from unittest.mock import Mock

from pydcop.dcop.scenario import DcopEvent, EventAction
from pydcop.infrastructure.computations import Message
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


def _scenario_manager(repair_only=False):
    mgt = object.__new__(AgentsMgt)
    mgt.logger = Mock()
    mgt._orchestrator = Mock(repair_only=repair_only)
    mgt._request_pause = Mock()
    mgt._request_resume = Mock()
    mgt._agents_arrival = Mock()
    mgt._agents_removal = Mock()
    mgt._send_mgt_msg = Mock()
    return mgt


def test_add_agent_event_uses_arrival_path_without_removal_repair():
    mgt = _scenario_manager()
    event = DcopEvent("e1", actions=[EventAction("add_agent", agent="a_new")])

    mgt._orchestrator_scenario_event(Message("scenario_event", event), 0)

    mgt._request_pause.assert_called_once_with()
    mgt._agents_arrival.assert_called_once_with(["a_new"])
    mgt._agents_removal.assert_not_called()
    mgt._request_resume.assert_called_once_with()


def test_event_with_add_and_remove_runs_removal_repair_once():
    mgt = _scenario_manager()
    event = DcopEvent(
        "e1",
        actions=[
            EventAction("add_agent", agent="a_new"),
            EventAction("remove_agent", agent="a_old"),
        ],
    )

    mgt._orchestrator_scenario_event(Message("scenario_event", event), 0)

    mgt._agents_arrival.assert_called_once_with(["a_new"])
    mgt._agents_removal.assert_called_once_with(["a_old"])
    mgt._request_resume.assert_not_called()


def test_agents_arrival_records_registered_agent_state():
    mgt = object.__new__(AgentsMgt)
    mgt.logger = Mock()
    mgt.discovery = Mock()
    mgt.discovery.agents.return_value = ["a1"]
    mgt._agts_state = {}

    mgt._agents_arrival(["a1", "a2"])

    assert mgt._agts_state == {"a1": "running"}
    mgt.logger.info.assert_called_once()
    mgt.logger.warning.assert_called_once()
