
.. _implementation_reference_algorithms_dba:

pydcop.algorithms.dba
=====================

Verified Behavior Notes
-----------------------

DBA implements the two-phase Distributed Breakout Algorithm from
:cite:`yokoo_distributed_1996`: computations alternate between ``ok?`` value
messages and ``improve`` messages, postpone messages received in the wrong
phase, and use the paper's improvement comparison with a fixed name-order
tie-break.

This implementation is a satisfaction algorithm. It accepts ``min`` mode and
uses the ``infinity`` parameter as the violation threshold; ordinary finite
costs are not optimized. Breakout weights are stored per exact violated
assignment tuple, extending the paper's binary variable-value-pair weights to
the repository's generic relation support.

Termination follows the paper's distance-counter scheme through
``max_distance`` when a solution is found. As in the paper, unsatisfied or
unlucky runs may require an external timeout.

.. automodule:: pydcop.algorithms.dba
