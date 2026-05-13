
.. _implementation_reference_algorithms_amaxsum:

pydcop.algorithms.amaxsum
=========================

Verified Behavior Notes
-----------------------

AMaxSum is the event-driven asynchronous Max-Sum runtime variant. It uses the
same Q/R message helpers and normalization behavior as
:ref:`Max-Sum<implementation_reference_algorithms_maxsum>`, and follows the
asynchronous update style described by :cite:`farinelli_decentralised_2008`.

``start_messages`` defaults to ``all``. ``stop_cycle`` is a local asynchronous
update limit, not a globally synchronized cycle count. ``auto_stop`` defaults
to ``1`` for AMaxSum, and an AMaxSum run must configure either
``stop_cycle > 0`` or ``auto_stop:1``.

With ``auto_stop`` enabled, computations report local stability after
``stable_cycles`` stable updates, keep processing messages until the
orchestrator stops the whole run, and report themselves running again if a
later message changes their outgoing messages. This is a coordinated runtime
stop, not a global convergence proof.

.. automodule:: pydcop.algorithms.amaxsum
