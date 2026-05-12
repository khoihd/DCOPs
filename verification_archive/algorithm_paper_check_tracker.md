# Algorithm Paper Check Tracker

Purpose: track paper-based correctness verification for every algorithm module in
`pydcop/algorithms`.

Use this as the ordering source for paper checks. Reorder the table whenever the
priority changes. Each algorithm gets a dedicated `*_paper_check.md` file once
verification starts.

## Status Legend

- `Not started`: no paper comparison has been done yet.
- `Paper needed`: implementation identified, but source paper is not attached or
  confirmed.
- `In progress`: paper contract is being mapped to implementation behavior.
- `Needs tests`: likely behavior is understood, but coverage gaps remain.
- `Needs fix`: a correctness mismatch was found and implementation changes are
  pending.
- `Verified`: paper comparison and focused tests are complete.
- `Intentional deviation`: implementation differs from the paper by design and
  the deviation is documented.

## Workflow

For each algorithm:

1. Create `verification_archive/<algorithm>_paper_check.md`.
2. Record the paper citation/link or attached filename.
3. Extract the algorithm contract: assumptions, graph type, initialization,
   message types, message contents, per-cycle behavior, termination, objective
   direction, stochastic behavior, and complexity claims when relevant.
4. Map the contract to `pydcop/algorithms/<algorithm>.py` and related graph,
   runtime, and test files.
5. Add focused tests for hand-checkable behavior or discovered gaps.
6. Record any implementation fixes or intentional deviations.

## Review Assumptions

- Ignore how the computation graph is constructed unless the algorithm's
  correctness depends on a specific construction method.
- Assume both minimization and maximization are acceptable unless the algorithm
  is inherently tied to one objective direction.
- Assume N-ary constraints are acceptable unless the algorithm is inherently
  tied to a specific constraint arity, such as unary or binary constraints.
- Focus on whether the implementation follows the paper's algorithmic logic and
  whether any implementation behavior contradicts the paper.

## Tracker

- DPOP
  - Priority: 1
  - Implementation: `pydcop/algorithms/dpop.py`
  - Paper / Source: `verification_archive/papers/dpop.pdf`
  - Check File: `verification_archive/dpop_paper_check.md`
  - Status: Verified
  - Notes: Core UTIL/VALUE logic matches the paper; `memory_footprint_estimate()` is
    documented as a local distribution-time approximation.

- MGM
  - Priority: 2
  - Implementation: `pydcop/algorithms/mgm.py`
  - Paper / Source: `verification_archive/papers/mgm.pdf`
  - Check File: `verification_archive/mgm_paper_check.md`
  - Status: Verified
  - Notes: Core value/gain flow matches Algorithm 1; min/max gain sign handling
    and equal-gain tie separation are covered by focused tests.

- MGM2
  - Priority: 3
  - Implementation: `pydcop/algorithms/mgm2.py`
  - Paper / Source: `verification_archive/papers/mgm.pdf`
  - Check File: `verification_archive/mgm2_paper_check.md`
  - Status: Verified
  - Notes: Core five-phase flow matches Algorithm 2; coordinated-gain
    double-counting was fixed and covered by focused tests.

- DBA
  - Priority: 4
  - Implementation: `pydcop/algorithms/dba.py`
  - Paper / Source: `verification_archive/papers/dba.pdf`
  - Check File: `verification_archive/dba_paper_check.md`
  - Status: Done / Verified
  - Notes: Core ok/improve flow matches the paper. Termination state handling
    was fixed, and breakout weights now use exact violated assignment tuples
    instead of one weight per constraint.

- GDBA
  - Priority: 5
  - Implementation: `pydcop/algorithms/gdba.py`
  - Paper / Source: `verification_archive/papers/gdba.pdf`
  - Check File: `verification_archive/gdba_paper_check.md`
  - Status: Done / Verified
  - Notes: Core minimization flow matches the paper. During verification,
    `R` and `C` increase scopes were corrected to follow the paper's
    row/column convention. Fixed-cycle `stop_cycle` support was added for
    reproducible runs and per-cycle metrics.

- DSA
  - Priority: 6
  - Implementation: `pydcop/algorithms/dsa.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/dsa_paper_check.md`
  - Status: Not started
  - Notes:

- ADSA
  - Priority: 7
  - Implementation: `pydcop/algorithms/adsa.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/adsa_paper_check.md`
  - Status: Not started
  - Notes:

- AMaxSum
  - Priority: 8
  - Implementation: `pydcop/algorithms/amaxsum.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/amaxsum_paper_check.md`
  - Status: Not started
  - Notes:

- DSA Tutorial
  - Priority: 9
  - Implementation: `pydcop/algorithms/dsatuto.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/dsatuto_paper_check.md`
  - Status: Not started
  - Notes: Tutorial implementation; verify if it should be checked against DSA
    paper or docs only.

- MaxSum
  - Priority: 10
  - Implementation: `pydcop/algorithms/maxsum.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/maxsum_paper_check.md`
  - Status: Not started
  - Notes:

- Dynamic MaxSum
  - Priority: 11
  - Implementation: `pydcop/algorithms/maxsum_dynamic.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/maxsum_dynamic_paper_check.md`
  - Status: Not started
  - Notes:

- MixedDSA
  - Priority: 12
  - Implementation: `pydcop/algorithms/mixeddsa.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/mixeddsa_paper_check.md`
  - Status: Not started
  - Notes:

- NCBB
  - Priority: 13
  - Implementation: `pydcop/algorithms/ncbb.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/ncbb_paper_check.md`
  - Status: Not started
  - Notes: Search phase is known incomplete from continuity notes.

- SyncBB
  - Priority: 14
  - Implementation: `pydcop/algorithms/syncbb.py`
  - Paper / Source: TBD
  - Check File: `verification_archive/syncbb_paper_check.md`
  - Status: Not started
  - Notes:

## Cross-Cutting Checks

- Confirm each algorithm's `GRAPH_TYPE` matches the paper assumptions.
- Confirm `algo_params` default values and validation match the paper or are
  documented deviations.
- Confirm objective direction (`min`, `max`, or both) is implemented consistently.
- Confirm message classes serialize cleanly for thread and process modes.
- Confirm `build_computation()` and `memory_footprint_estimate()` behavior is covered
  where the algorithm exposes them.
- Prefer tiny deterministic DCOP fixtures and oracle-backed solve tests where
  possible.
