import json
from collections import defaultdict
from unittest.mock import Mock

from pydcop.infrastructure.orchestrator import AgentsMgt, RepairReadyMessage
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
