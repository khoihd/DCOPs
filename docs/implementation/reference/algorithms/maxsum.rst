
.. _implementation_reference_algorithms_maxsum:

pydcop.algorithms.maxsum
========================

Verified Behavior Notes
-----------------------

Max-Sum uses the factor-graph message equations from
:cite:`farinelli_decentralised_2008`. Variable-to-factor messages sum incoming
factor messages from other neighboring factors and are normalized to a zero-sum
vector; factor-to-variable messages optimize the local function plus incoming
messages from the other variables in the factor scope.

This is the synchronous runtime variant. ``stop_cycle`` provides the paper's
fixed-iteration style of termination. ``auto_stop`` / ``stable_cycles`` are
optional local heuristic convergence controls, not a proof of global
convergence on cyclic graphs.

The implementation supports both ``min`` and ``max`` objectives, N-ary
relations, integrated variable costs, damping, stability-based message
suppression, noise, and configurable startup through ``start_messages``. The
default startup mode is ``all``. Variable costs are included in the normalized
variable-to-factor message.

.. automodule:: pydcop.algorithms.maxsum
