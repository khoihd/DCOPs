
.. _implementation_reference_algorithms_dsa:

pydcop.algorithms.dsa
=====================

Verified Behavior Notes
-----------------------

DSA implements the synchronous A, B, and C value-selection variants from
:cite:`zhang_distributed_2005`. Each cycle waits for neighbor values, computes
the locally best values, and applies the configured probability only when the
selected variant allows a move.

Unlike the paper's lower-communication presentation, this implementation sends
the current value every cycle, even when the value did not change. This is an
intentional runtime adaptation that keeps the wait-for-all-neighbors protocol
live when startup timing is uneven or neighbors keep the same value.

``p_mode="arity"``, ``stop_cycle``, generic N-ary relations, variable costs,
and both ``min`` and ``max`` modes are repository extensions beyond the paper's
graph-coloring-focused discussion.

.. automodule:: pydcop.algorithms.dsa
