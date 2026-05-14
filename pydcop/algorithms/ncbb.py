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


"""

NCBB: No-Commitment Branch and Bound
------------------------------------

NCBB is a polynomial-space search for DCOP proposed by Chechetka and Sycara in 2006
:cite:`chechetka_no-commitment_2006`.
It is a branch and bound search algorithm with modifications for efficiency, it runs
concurrent search process in different partitions of the search phase.

NCBB defines one computation for each variable in the DCOP and,
like DPOP, runs on a pseudo-tree, which is automatically built when using the
:ref:`solve<pydcop_commands_solve>` command.

In the current implementation, which maps the original article
:cite:`chechetka_no-commitment_2006` , only binary constraints are supported.
According to the authors, it could be extended to n-ary constraints.

NCBB is a synchronous algorithm and is composed of two phases:
* a initialization phase, during which a global upper bound is computed
* a search phase

The paper defines NCBB for minimization. This implementation also supports
pyDcop maximization problems by minimizing the negated objective internally;
the selected assignment is therefore optimal for the original max objective,
but this is a pyDcop extension rather than a behavior described in the paper.
The objective direction is inferred from the DCOP instance objective
(`min` or `max`) through `AlgorithmDef.mode`; NCBB has no separate objective
algorithm parameter.
Unary variable costs, when present in pyDcop variables, are treated as local
costs for the owning variable.

Problem requirements:

* variables must have finite discrete domains;
* constraints used with NCBB must be binary;
* no NCBB-specific YAML item is required beyond the usual pyDcop problem
  definition, agents/distribution, and `objective: min` or `objective: max`;
* the pseudo-tree computation graph is built automatically by `pydcop solve`.


Initialization phase:

* `VALUE` messages are propagated from top to bottom and a value is selected greedily
  for each variable, starting from the root and based on ancestors values
* The leaves compute a shifted upper bound, which is also propagated upwards in the
tree as `COST` messages
At the end of this phase, each variable has an upper-bound for the sub-tree rooted here.


Search phase:

Main:
* update context
* search
* subtree search
* send stop (1->)

update context:
* agents
  * receive values msg from their ancestors (->2)
    * send lower_bound to their ancestors (3->)
  * receive search msg from their ancestors (->4)
    * update their upper bound
  * receive stop message (->1)

Search:
* start subtree search
* receives costs from children
* send cost to parent

Subtree search:
 * send value to descendants (2->)
 * receive costs from descendants (->3)
 * send search to child, with upper-bound (4->)



"""
from pydcop.algorithms import ComputationDef
from pydcop.computations_graph.pseudotree import get_dfs_relations
from pydcop.dcop.relations import assignment_cost, generate_assignment_as_dict
from pydcop.infrastructure.computations import (
    VariableComputation,
    register,
    message_type,
    ComputationException,
)

GRAPH_TYPE = "pseudotree"
algo_params = []

HEADER_SIZE = 0
UNIT_SIZE = 1


def memory_footprint_estimate(computation):
    return len(computation.variable.domain) * max(1, len(computation.neighbors)) * UNIT_SIZE


def communication_load(src, target):
    return HEADER_SIZE + UNIT_SIZE


def build_computation(comp_def: ComputationDef):
    return NcbbAlgo(comp_def)


ValueMessage = message_type("value", ["value"])
CostMessage = message_type("cost", ["cost"])
SearchMessage = message_type("search", ["upper_bound"])
SearchValueMessage = message_type("search_value", ["value"])
SearchCostMessage = message_type("search_cost", ["lower_bound"])
StopMessage = message_type("stop", ["stop"])

PHASES = {"INIT", "SEARCH"}


class NcbbAlgo(VariableComputation):
    """
    Computation implementation for the NCBB algorithm.

    Parameters
    ----------
    computation_definition: ComputationDef
        the definition of the computation, given as a ComputationDef instance.

    """

    def __init__(self, computation_definition: ComputationDef):
        super().__init__(computation_definition.node.variable, computation_definition)

        assert computation_definition.algo.algo == "ncbb"
        self._mode = computation_definition.algo.mode
        if self._mode not in {"min", "max"}:
            raise ComputationException(
                "NCBB requires mode 'min' or 'max'; "
                f"got mode {self._mode!r}."
            )
        self._cost_factor = 1 if self._mode == "min" else -1

        # Set parent, children and constraints
        self._parent, self._pseudo_parents, self._children, self._pseudo_children = get_dfs_relations(
            self.computation_def.node
        )
        self.phase = "INIT"
        self._upper_bound = None

        # parent and pseudo-parents:
        self._ancestors = list(self._pseudo_parents)
        if self._parent is not None:
            self._ancestors.append(self._parent)
        self._ancestor_names = set(self._ancestors)
        self._children_names = set(self._children)

        # Children and pseudo-children:
        self._descendants = self._pseudo_children + self._children
        self._descendants_by_child = {
            child: list(descendants)
            for child, descendants in getattr(
                self.computation_def.node, "branch_descendants", {}
            ).items()
        }
        for child in self._children:
            self._descendants_by_child.setdefault(child, [child])

        # Raise an exception if we pass a non-binary constraint
        self._constraints = []
        self._ancestor_constraints = []
        self._variables_by_name = {self.variable.name: self.variable}
        for r in computation_definition.node.constraints:
            if r.arity != 2:
                raise ComputationException(
                    f"Invalid constraint {r} with arity {r.arity} "
                    f"for variable {self.name}, "
                    f"NCBB implementation only supports binary constraints."
                )
            self._constraints.append(r)
            for v in r.dimensions:
                self._variables_by_name[v.name] = v
            if any(v.name in self._ancestor_names for v in r.dimensions):
                self._ancestor_constraints.append(r)

        self._parents_values = {}
        self._children_costs = {}
        self._search_context = {}
        self._pending_search_values = {}
        self._pending_search_bound = None
        self._search_bound = None
        self._search_commit = False
        self._search_fixed_values = None
        self._search_min_cost = None
        self._search_costs = {}
        self._search_unexplored = {}
        self._search_idle = []
        self._search_announced_values = {}
        self._search_pending_lb = {}
        self._search_pending_child = set()
        self._search_result_value = None

    @register("value")
    def _value_msg_registration(self, variable_name, recv_msg, t):
        if self.phase != "INIT":
            raise ComputationException(
                f"value messages received at {self.name} while not in INIT phase"
            )
        self.value_phase(variable_name, recv_msg.value)
        self.new_cycle()

    @register("cost")
    def _cost_msg_registration(self, variable_name, recv_msg, t):
        if self.phase != "INIT":
            raise ComputationException(
                f"cost messages received at {self.name} while not in INIT phase"
            )
        self.cost_phase(variable_name, recv_msg.cost)
        self.new_cycle()

    @register("search")
    def _search_msg_registration(self, variable_name, recv_msg, t):
        if self.phase != "SEARCH":
            raise ComputationException(
                f"search messages received at {self.name} while not in SEARCH phase"
            )
        self.search_phase(variable_name, recv_msg.upper_bound)
        self.new_cycle()

    @register("search_value")
    def _search_value_msg_registration(self, variable_name, recv_msg, t):
        if self.phase != "SEARCH":
            raise ComputationException(
                f"search_value messages received at {self.name} "
                f"while not in SEARCH phase"
            )
        self.search_value_phase(variable_name, recv_msg.value)
        self.new_cycle()

    @register("search_cost")
    def _search_cost_msg_registration(self, variable_name, recv_msg, t):
        if self.phase != "SEARCH":
            raise ComputationException(
                f"search_cost messages received at {self.name} "
                f"while not in SEARCH phase"
            )
        self.search_cost_phase(variable_name, recv_msg.lower_bound)
        self.new_cycle()

    @register("stop")
    def _stop_msg_registration(self, variable_name, recv_msg, t):
        if self.phase != "SEARCH":
            raise ComputationException(
                f"stop messages received at {self.name} while not in SEARCH phase"
            )
        self.stop_phase()
        self.new_cycle()

    @property
    def is_root(self):
        return self._parent is None

    @property
    def is_leaf(self):
        return len(self._children) == 0

    def on_start(self):
        # Start with the Initialization phase of NCBB
        # Starting from the root, variable send cost messages down the tree
        if not self.is_root:
            return

        # The root has no ancestors; pick a locally optimal value and start
        # the shifted greedy upper bound from its local shifted cost.
        values, local_cost = self._find_best_local_values({})
        self.value_selection(values[0])
        self._upper_bound = local_cost - self.lower_bound({}, 0)
        for child in self._descendants:
            self.post_msg(child, ValueMessage(self.current_value))
        if self.is_leaf:
            self.phase = "SEARCH"
            self.search()

    def on_new_cycle(self, messages, cycle_id) -> list | None:
        if not messages:
            return

        for sender, (message, t) in messages.items():
            if message.type == "value":
                if self.phase != "INIT":
                    raise ComputationException(
                        f"value messages received at {self.name} "
                        f"while not in INIT phase"
                    )
                self.value_phase(sender, message.value)
            elif message.type == "cost":
                if self.phase != "INIT":
                    raise ComputationException(
                        f"cost messages received at {self.name} "
                        f"while not in INIT phase"
                    )
                self.cost_phase(sender, message.cost)
            elif message.type == "search_value":
                if self.phase != "SEARCH":
                    raise ComputationException(
                        f"search_value messages received at {self.name} "
                        f"while not in SEARCH phase"
                    )
                self.search_value_phase(sender, message.value)
            elif message.type == "search_cost":
                if self.phase != "SEARCH":
                    raise ComputationException(
                        f"search_cost messages received at {self.name} "
                        f"while not in SEARCH phase"
                    )
                self.search_cost_phase(sender, message.lower_bound)
            elif message.type == "search":
                if self.phase != "SEARCH":
                    raise ComputationException(
                        f"search messages received at {self.name} "
                        f"while not in SEARCH phase"
                    )
                self.search_phase(sender, message.upper_bound)
            elif message.type == "stop":
                if self.phase != "SEARCH":
                    raise ComputationException(
                        f"stop messages received at {self.name} "
                        f"while not in SEARCH phase"
                    )
                self.stop_phase()

        return

    def value_phase(self, sender, value):
        if sender not in self._ancestor_names:
            raise ComputationException(
                f"Received at {self.name} value from {sender}, "
                f"which is not an ancestor: {self._ancestors}"
            )

        # Init phase: select a value and send down the tree
        # as value messages are sent by parent and pseudo-parents,
        # they might arrive in several cycles and must be accumulated before we
        # can select our value.
        self._parents_values[sender] = value

        if len(self._parents_values) == len(self._ancestors):
            # Select our own value greedily.
            # For this, we only take into account local cost and constraints
            # with our ancestors.
            values, cost = self._find_best_local_values(self._parents_values)
            self.value_selection(values[0])
            self._upper_bound = cost - self.lower_bound({}, 0)

            # Send our value to our children.
            if not self.is_leaf:
                for child in self._descendants:
                    self.post_msg(child, ValueMessage(self.current_value))
            else:
                # At leafs, we initiate cost message (sent up) as we don't
                # have to wait for costs from our children.
                self.post_msg(self._parent, CostMessage(self._upper_bound))
                self.phase = "SEARCH"

    def cost_phase(self, sender, cost):
        # compute the upper-bound for the subtree rooted at this variable.

        if sender not in self._children_names:
            raise ComputationException(
                f"Received cost at {self.name} from {sender}, "
                f"which is not a children: {self._children}"
            )

        self._children_costs[sender] = cost
        self._upper_bound += cost

        if len(self._children_costs) == len(self._children):
            # We have computed the upper-bound for our subtree.
            if not self.is_root:
                # Propagate costs up to parent.
                self.post_msg(self._parent, CostMessage(self._upper_bound))
            else:
                # If we are the root of the tree, we can now initiate the search phase.
                self.phase = "SEARCH"
                self.search()
            if not self.is_root:
                self.phase = "SEARCH"

    def search(self):
        self._start_search(self._upper_bound)

    def search_phase(self, sender, upper_bound):
        if sender != self._parent:
            raise ComputationException(
                f"Received search at {self.name} from {sender}, "
                f"which is not its parent: {self._parent}"
            )
        if not self._has_complete_search_context():
            self._pending_search_bound = upper_bound
            return
        self._start_search(upper_bound)

    def search_value_phase(self, sender, value):
        if sender not in self._ancestor_names:
            raise ComputationException(
                f"Received at {self.name} search value from {sender}, "
                f"which is not an ancestor: {self._ancestors}"
            )

        ancestor_index = self._ancestors.index(sender)
        if not self._has_prefix_context(ancestor_index):
            self._pending_search_values[sender] = value
            return

        self._apply_search_value(sender, value)
        self._process_pending_search_values()
        self._maybe_start_pending_search()

    def search_cost_phase(self, sender, cost):
        for child, pending_descendants in list(self._search_pending_lb.items()):
            if sender not in pending_descendants:
                continue
            value = self._search_announced_values[child]
            self._search_costs[value] += cost
            pending_descendants.remove(sender)
            if not pending_descendants:
                del self._search_pending_lb[child]
                self._finish_subtree_lower_bound_phase(child)
            return

        if sender in self._search_pending_child:
            self._search_pending_child.remove(sender)
            value = self._search_announced_values.pop(sender)
            self._search_costs[value] += cost
            if self._search_costs[value] > self._search_bound:
                self._prune_value(value)
            elif not self._search_unexplored.get(value):
                self._record_complete_value(value)
            self._mark_child_idle_if_needed(sender)
            self._schedule_search_work()
            return

        raise ComputationException(
            f"Unexpected search_cost at {self.name} from {sender}"
        )

    def stop_phase(self):
        for child in self._children:
            self.post_msg(child, StopMessage(True))
        self.finished()

    def _start_search(self, upper_bound, commit=False, fixed_values=None):
        self._search_bound = upper_bound
        self._search_commit = commit
        self._search_fixed_values = fixed_values
        self._search_min_cost = self.lower_bound(
            self._search_context, len(self._ancestors)
        )
        self._search_costs = {}
        self._search_unexplored = {}
        self._search_idle = list(self._children)
        self._search_announced_values = {}
        self._search_pending_lb = {}
        self._search_pending_child = set()
        self._search_result_value = None

        values = fixed_values if fixed_values is not None else self.variable.domain
        for value in values:
            assignment = dict(self._search_context)
            assignment[self.name] = value
            local_cost = self.agent_cost(assignment)
            shifted_cost = local_cost - self._search_min_cost
            if shifted_cost <= self._search_bound:
                self._search_costs[value] = shifted_cost
                self._search_unexplored[value] = set(self._children)

        if not self._children:
            self._finish_leaf_search()
            return

        if not self._search_costs:
            self._finish_search()
            return

        self._schedule_search_work()

    def _finish_leaf_search(self):
        if self._search_costs:
            value = min(self._search_costs, key=lambda d: self._search_costs[d])
            self._record_complete_value(value)
        self._finish_search()

    def _schedule_search_work(self):
        while True:
            selected = self._select_next_child_value()
            if selected is None:
                break
            child, value = selected
            self._search_idle.remove(child)
            self._search_unexplored[value].remove(child)
            self._start_subtree_search(value, child)

        if (
            not self._search_pending_lb
            and not self._search_pending_child
            and not any(self._search_unexplored.values())
        ):
            self._finish_search()

    def _select_next_child_value(self):
        active_values = set(self._search_announced_values.values())
        for child in list(self._search_idle):
            for value in self.variable.domain:
                if value in active_values:
                    continue
                if child in self._search_unexplored.get(value, set()):
                    return child, value
            if not any(child in children for children in self._search_unexplored.values()):
                self._search_idle.remove(child)
        return None

    def _start_subtree_search(self, value, child):
        descendants = self._descendants_by_child.get(child, [child])
        self._search_announced_values[child] = value
        self._search_pending_lb[child] = set(descendants)
        for descendant in descendants:
            self.post_msg(descendant, SearchValueMessage(value))

    def _finish_subtree_lower_bound_phase(self, child):
        value = self._search_announced_values[child]
        if self._search_costs[value] > self._search_bound:
            self._search_announced_values.pop(child)
            self._prune_value(value)
            self._mark_child_idle_if_needed(child)
            self._schedule_search_work()
            return

        self._search_pending_child.add(child)
        self.post_msg(
            child, SearchMessage(self._search_bound - self._search_costs[value])
        )

    def _record_complete_value(self, value):
        if (
            self._search_result_value is None
            or self._search_costs[value] <= self._search_bound
        ):
            self._search_bound = self._search_costs[value]
            self._search_result_value = value
            self._prune_values_over_bound()

    def _prune_values_over_bound(self):
        for value, cost in list(self._search_costs.items()):
            if cost > self._search_bound:
                self._prune_value(value)

    def _prune_value(self, value):
        self._search_unexplored[value] = set()

    def _mark_child_idle_if_needed(self, child):
        if any(child in children for children in self._search_unexplored.values()):
            if child not in self._search_idle:
                self._search_idle.append(child)

    def _finish_search(self):
        if self._search_result_value is not None:
            self.value_selection(self._search_result_value, self._search_bound)

        if not self.is_root:
            cost = self._search_bound
            if self._search_result_value is None:
                cost = float("inf")
            self.post_msg(self._parent, SearchCostMessage(cost))
            return

        if self._search_commit or not self._children:
            for child in self._children:
                self.post_msg(child, StopMessage(True))
            self.finished()
            return

        self._start_search(
            self._search_bound,
            commit=True,
            fixed_values=[self._search_result_value],
        )

    def _has_complete_search_context(self):
        return all(ancestor in self._search_context for ancestor in self._ancestors)

    def _has_prefix_context(self, ancestor_index):
        return all(
            ancestor in self._search_context
            for ancestor in self._ancestors[:ancestor_index]
        )

    def _apply_search_value(self, sender, value):
        ancestor_index = self._ancestors.index(sender)
        before = {
            ancestor: self._search_context[ancestor]
            for ancestor in self._ancestors[:ancestor_index]
        }
        after = dict(before)
        after[sender] = value

        for ancestor in self._ancestors[ancestor_index:]:
            self._search_context.pop(ancestor, None)
        self._search_context[sender] = value

        delta = self.lower_bound(after, ancestor_index + 1) - self.lower_bound(
            before, ancestor_index
        )
        self.post_msg(sender, SearchCostMessage(delta))

    def _process_pending_search_values(self):
        while True:
            processed = False
            for sender, value in list(self._pending_search_values.items()):
                ancestor_index = self._ancestors.index(sender)
                if not self._has_prefix_context(ancestor_index):
                    continue
                del self._pending_search_values[sender]
                self._apply_search_value(sender, value)
                processed = True
            if not processed:
                return

    def _maybe_start_pending_search(self):
        if self._pending_search_bound is None:
            return
        if not self._has_complete_search_context():
            return
        upper_bound = self._pending_search_bound
        self._pending_search_bound = None
        self._start_search(upper_bound)

    def _find_best_local_values(self, assignment):
        best_values = []
        best_cost = float("inf")
        candidate_assignment = dict(assignment)
        for value in self.variable.domain:
            candidate_assignment[self.name] = value
            cost = self.agent_cost(candidate_assignment)
            if cost == best_cost:
                best_values.append(value)
            elif cost < best_cost:
                best_cost = cost
                best_values = [value]
        return best_values, best_cost

    def agent_cost(self, assignment):
        """Return this variable's local cost in NCBB's minimization space."""
        cost = assignment_cost(assignment, self._ancestor_constraints)
        if self.name in assignment:
            cost += self.variable.cost_for_val(assignment[self.name])
        return self._cost_factor * cost

    def lower_bound(self, assignment, k):
        """Return LB(x, assignment, k) in NCBB's minimization space.

        ``k`` is the number of leading ancestors whose values are fixed by
        ``assignment``. Remaining ancestors and this computation's variable
        are minimized over. For maximization problems this is computed on the
        negated original objective.
        """
        if k < 0 or k > len(self._ancestors):
            raise ValueError(
                f"k must be between 0 and {len(self._ancestors)} for {self.name}"
            )

        fixed_names = set(self._ancestors[:k])
        missing = fixed_names - set(assignment)
        if missing:
            raise ValueError(
                f"Missing ancestor values for lower_bound at {self.name}: {missing}"
            )

        free_names = [self.variable.name] + [
            ancestor for ancestor in self._ancestors[k:] if ancestor in self._variables_by_name
        ]
        free_variables = [self._variables_by_name[name] for name in free_names]

        best_cost = float("inf")
        for free_assignment in generate_assignment_as_dict(free_variables):
            candidate = dict(assignment)
            candidate.update(free_assignment)
            best_cost = min(best_cost, self.agent_cost(candidate))

        return best_cost
