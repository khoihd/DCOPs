- (DONE) Add print out when agent sends and receive messages for debugging
  - pydcop -v 3 # debugging mode

- (DONE) Verify the correctness of the implementation with the provided paper
  - DPOP
  - MGM / MGM2
  - DBA / DSA / ADSA
  - Maxsum / AMaxsum
  - Maxsum Dynamic
  - GDBA
  - NCBB
  - SyncBB

- (DONE) Fix TODO and FIXME

- (DONE) Add multi-threading support for exact algorithms
  - Pulp: highs
  - No need to further optimize join / util functions from DPOP

- (DONE) Two ways to terminate the algorithms:
  - '--timeout' from solve
  - '-p stop_cycle:30' from the algorithm

- (WIP) Review instance generators:
  - (DONE) Add seed value
  - (DONE) Add random graph
  - Add support to generate multiple instances
    - How should we name instances?
      - Provide prefix ?

- CLI:
    python -m pydcop.dcop_cli -v 3 solve -a dpop random20.yaml
    python -m pydcop.dcop_cli -v 3 solve -a pulp random20.yaml
    python -m pydcop.dcop_cli -v 3 solve -a dsa random20.yaml -p stop_cycle:30 -c cycle_change --run_metrics dsa_max_random20.csv
    python -m pydcop.dcop_cli generate random_graph --variables_count 20 --domain_size 10 --p_edge 0.4 --objective max > random20.yaml

    pip install -e .
    pytest
    ruff check .