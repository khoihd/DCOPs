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

## Tracker

| Priority | Algorithm | Implementation | Paper / Source | Check File | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ADSA | `pydcop/algorithms/adsa.py` | TBD | `verification_archive/adsa_paper_check.md` | Not started |  |
| 2 | AMaxSum | `pydcop/algorithms/amaxsum.py` | TBD | `verification_archive/amaxsum_paper_check.md` | Not started |  |
| 3 | DBA | `pydcop/algorithms/dba.py` | TBD | `verification_archive/dba_paper_check.md` | Not started |  |
| 4 | DPOP | `pydcop/algorithms/dpop.py` | TBD | `verification_archive/dpop_paper_check.md` | Not started |  |
| 5 | DSA | `pydcop/algorithms/dsa.py` | TBD | `verification_archive/dsa_paper_check.md` | Not started |  |
| 6 | DSA Tutorial | `pydcop/algorithms/dsatuto.py` | TBD | `verification_archive/dsatuto_paper_check.md` | Not started | Tutorial implementation; verify if it should be checked against DSA paper or docs only. |
| 7 | GDBA | `pydcop/algorithms/gdba.py` | TBD | `verification_archive/gdba_paper_check.md` | Not started |  |
| 8 | MaxSum | `pydcop/algorithms/maxsum.py` | TBD | `verification_archive/maxsum_paper_check.md` | Not started |  |
| 9 | Dynamic MaxSum | `pydcop/algorithms/maxsum_dynamic.py` | TBD | `verification_archive/maxsum_dynamic_paper_check.md` | Not started |  |
| 10 | MGM | `pydcop/algorithms/mgm.py` | TBD | `verification_archive/mgm_paper_check.md` | Not started |  |
| 11 | MGM2 | `pydcop/algorithms/mgm2.py` | TBD | `verification_archive/mgm2_paper_check.md` | Not started |  |
| 12 | MixedDSA | `pydcop/algorithms/mixeddsa.py` | TBD | `verification_archive/mixeddsa_paper_check.md` | Not started |  |
| 13 | NCBB | `pydcop/algorithms/ncbb.py` | TBD | `verification_archive/ncbb_paper_check.md` | Not started | Search phase is known incomplete from continuity notes. |
| 14 | SyncBB | `pydcop/algorithms/syncbb.py` | TBD | `verification_archive/syncbb_paper_check.md` | Not started |  |

## Cross-Cutting Checks

- Confirm each algorithm's `GRAPH_TYPE` matches the paper assumptions.
- Confirm `algo_params` default values and validation match the paper or are
  documented deviations.
- Confirm objective direction (`min`, `max`, or both) is implemented consistently.
- Confirm message classes serialize cleanly for thread and process modes.
- Confirm `build_computation()` and `computation_memory()` behavior is covered
  where the algorithm exposes them.
- Prefer tiny deterministic DCOP fixtures and oracle-backed solve tests where
  possible.
