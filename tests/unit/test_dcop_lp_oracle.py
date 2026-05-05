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

from tests.utils.dcop_oracle import solve_dcop_with_pulp
from tests.utils.known_instances import KNOWN_INSTANCE_COSTS, KNOWN_INSTANCE_SOLUTIONS


class TestPulpDcopOracle:
    @pytest.mark.parametrize(
        "known_case",
        KNOWN_INSTANCE_SOLUTIONS,
        ids=[known_case.name for known_case in KNOWN_INSTANCE_SOLUTIONS],
    )
    def test_instance_matches_known_solution(self, known_case):
        dcop = known_case.dcop_factory()

        assignment, cost = solve_dcop_with_pulp(dcop)

        assert assignment == known_case.optimal_assignment
        assert cost == pytest.approx(known_case.optimal_cost)

    @pytest.mark.parametrize(
        "known_case",
        KNOWN_INSTANCE_COSTS,
        ids=[known_case.name for known_case in KNOWN_INSTANCE_COSTS],
    )
    def test_instance_matches_known_cost(self, known_case):
        dcop = known_case.dcop_factory()

        _, cost = solve_dcop_with_pulp(dcop)

        assert cost == pytest.approx(known_case.optimal_cost)
