
.. _implementation_reference_algorithms_adsa:

pydcop.algorithms.adsa
======================

Verified Behavior Notes
-----------------------

ADSA follows the asynchronous wake-up model from
:cite:`fitzpatrick_distributed_2003`: computations start with randomized local
offsets, wake periodically, optimize from the latest known neighbor values,
and act as an anytime local-search algorithm.

This module combines that asynchronous schedule with the DSA A/B/C
value-change variants from :cite:`zhang_distributed_2005`. It computes the
local best values first, then applies the configured probability when the
variant permits a move.

The implementation broadcasts the current value every tick rather than only
after a value change. Generic N-ary relations, variable costs, ``mode="max"``,
and the DSA A/B/C variants are repository extensions around the paper's
fixed-probability asynchronous optimizer.

.. automodule:: pydcop.algorithms.adsa
