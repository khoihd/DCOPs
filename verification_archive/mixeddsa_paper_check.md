# MixedDSA Paper Check

## Source

- Base paper: `verification_archive/papers/dsa.pdf`
- Title: "Distributed stochastic search and distributed breakout: properties,
  comparison and applications to constraint optimization problems in sensor
  networks"
- Authors: Weixiong Zhang, Guandong Wang, Zhao Xing, and Lars Wittenburg
- Implementation: `pydcop/algorithms/mixeddsa.py`
- Status: Done / No Separate Paper Source

## Notes

MixedDSA appears to be a pyDcop-specific extension of DSA rather than an
algorithm implemented from a separate paper. The module cites Zhang et al. for
the underlying DSA A/B/C move variants, but the hard/soft split and separate
`proba_hard` / `proba_soft` parameters are repository-level adaptations.

The implementation treats a constraint as hard only when at least one local
assignment evaluates to symbolic infinity (`+inf` or `-inf`). Finite
pseudo-hard penalties remain soft costs.

## Current Behavior

- First minimize the number of violated hard constraints.
- If the hard-violation count cannot improve, optimize the soft cost.
- Apply `proba_hard` to hard-violation improvements and hard-conflict sideways
  moves for variants B/C.
- Apply `proba_soft` to soft-cost improvements and violated-soft sideways moves
  for variants B/C.
- Variant C may also make equal-cost sideways moves when there is no hard or
  soft violation.

## Recent Review

A focused engineering review fixed no-neighbor startup, stop-cycle stopping,
variant A sideways behavior under hard conflicts, and the previously
unreachable variant C equal-cost/no-violation move.
