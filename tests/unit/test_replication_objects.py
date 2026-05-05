# BSD-3-Clause License
#
# Copyright 2017 Orange
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import pytest

from pydcop.replication.objects import ReplicaDistribution


def test_replica_distribution_builds_computation_and_agent_lookups():
    distribution = ReplicaDistribution(
        {"c1": ["a1", "a2"], "c2": ["a2"]}
    )

    assert distribution.agents_for_computation("c1") == ["a1", "a2"]
    assert distribution.agents_for_computation("c2") == ["a2"]
    assert distribution.replicas_on("a1") == ["c1"]
    assert distribution.replicas_on("a2") == ["c1", "c2"]


def test_replicas_on_unknown_agent_returns_empty_list_by_default():
    distribution = ReplicaDistribution({"c1": ["a1"]})

    assert distribution.replicas_on("unknown") == []


def test_replicas_on_unknown_agent_can_raise_keyerror():
    distribution = ReplicaDistribution({"c1": ["a1"]})

    with pytest.raises(KeyError):
        distribution.replicas_on("unknown", raise_on_unknown=True)


def test_agents_for_unknown_computation_raises_keyerror():
    distribution = ReplicaDistribution({"c1": ["a1"]})

    with pytest.raises(KeyError):
        distribution.agents_for_computation("unknown")


def test_duplicate_replica_for_same_computation_and_agent_is_rejected():
    with pytest.raises(ValueError, match="hosting several replica"):
        ReplicaDistribution({"c1": ["a1", "a1"]})


def test_replica_distribution_copies_input_mapping():
    mapping = {"c1": ["a1"]}
    distribution = ReplicaDistribution(mapping)

    mapping["c1"].append("a2")

    assert distribution.agents_for_computation("c1") == ["a1"]
    assert distribution.replicas_on("a2") == []
