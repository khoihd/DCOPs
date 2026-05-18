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
  - PulP with multi-threading HiGHS backend

- (DONE) Fix TODO and FIXME

- (DONE) Add multi-threading support for exact algorithms
  - Pulp: HiGHS
  - No need to further optimize join / util functions from DPOP

- (DONE) Two ways to terminate the algorithms
  - '--timeout' from solve
  - '-p stop_cycle:30' from the algorithm

- (DONE) Support checking and creating folders / subfolders for output
  python -m pydcop.dcop_cli --output folder/file.yaml generate random_graph
  python -m pydcop.dcop_cli --output folder/file.yaml solve -alg mgm instance.yaml

- (DONE) Review instance generators
  - Add optional seed value for reproducibility
  - Add random graph generator
  - Generate multiple instances via a script with --output

- (TODO) Support PD-DCOPs
  - Instance file format
  - Multi-step DCOPs:
    - DCOP at every step
    - Solution at every step
  - PD-DCOP model
  - PD-DCOP algorithms
  - Reactive D-DCOP model
  - Reactive D-DCOP algorithms
  - Hybrid D-DCOP (or General D-DCOPs)
    - Reusing algorthms

    - Experiment setting

- CLI:
    python -m pydcop.dcop_cli -v 3 solve -a dpop random20.yaml
    python -m pydcop.dcop_cli -v 3 solve -a pulp random20.yaml
    python -m pydcop.dcop_cli -v 3 solve -a dsa random20.yaml -p stop_cycle:30 -c cycle_change --run_metrics dsa_max_random20.csv
    python -m pydcop.dcop_cli generate random_graph --variables_count 20 --domain_size 10 --p_edge 0.4 --objective max > random20.yaml

    pip install -e .
    pytest
    ruff check .

    python -m pydcop.dcop_cli --output test.yaml generate random_graph --variables_count 40 --domain_size 10 --p_edge 0.4 --objective max