
.. _implementation_reference_algorithms_gdba:

pydcop.algorithms.gdba
======================

Verified Behavior Notes
-----------------------

GDBA implements the minimization algorithm from "Distributed Breakout: Beyond
Satisfaction" by Okamoto, Zivan, and Nahon: value and improve phases, additive
or multiplicative effective costs, the ``NZ`` / ``NM`` / ``MX`` violation
definitions, and the ``E`` / ``C`` / ``R`` / ``T`` modifier increase scopes.

The ``C`` and ``R`` increase modes follow the paper's row/column convention:
``C`` increases all local values with the neighbor context fixed, while ``R``
increases the current local value across possible neighbor contexts.

The implementation also supports generic relations, constraints hypergraphs,
``mode="max"``, and the fixed-cycle ``stop_cycle`` parameter as repository
extensions. The paper check verified the paper's minimization behavior.

.. automodule:: pydcop.algorithms.gdba
