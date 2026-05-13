.. _implementation_reference_algorithms_mixeddsa:

pydcop.algorithms.mixeddsa
==========================

Verified Behavior Notes
-----------------------

MixedDSA is a repository-specific hard/soft extension of
:ref:`DSA<implementation_reference_algorithms_dsa>`. No separate paper source
has been identified for the hard/soft behavior; the stochastic A/B/C move
variants are inherited from :cite:`zhang_distributed_2005`.

The algorithm treats a relation as hard only when at least one local assignment
evaluates to symbolic infinity. It first tries to reduce the number of
violated hard constraints; when that count cannot improve, it optimizes the
remaining soft cost.

``proba_hard`` controls hard-conflict improvements and permitted hard-conflict
sideways moves. ``proba_soft`` controls soft-cost improvements and permitted
soft sideways moves. Variant C may also perform equal-cost moves when neither
hard nor soft violations remain.

.. automodule:: pydcop.algorithms.mixeddsa
