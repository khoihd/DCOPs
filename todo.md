- (DONE) Add print out when agent sends and receive messages for debugging
  - pydcop -v 3 # debugging mode

- (WIP) Verify the correctness of the implementation with the provided paper
  - (DONE) DPOP
  - (DONE) MGM / MGM2
  - (DONE) DBA / DSA / ADSA
  - (DONE) Maxsum / AMaxsum
  - (DONE) Maxsum Dynamic
  - (DONE) DSAAuto
  - GDBA
  - NCBB
  - SyncBB

- Require a parameter for termination mechanism to all iterative algorithms

- (WIP) Review instance generators:
  - (DONE) Add seed value
  - (DONE) Add random graph
  - Add support to generate multiple instances
    - Check how we should name instances

- Optimize commonly used files with overheads

- Optimize instance generator

- Check how the algorithm supports multi-threading

- Investigate optional multicore PuLP solving with a CBC backend and a
  `threads` parameter; current `GLPK_CMD` path is effectively single-core.
