- Review instance generators:
  - (DONE) Add seed value
  - (DONE) Add random graph
  - Add support to generate multiple instances
    - Check how we should name instances
  
- Add print out when agent sends and receive messages for debugging

- Check how the algorithm supports multi-threading

- Investigate optional multicore PuLP solving with a CBC backend and a
  `threads` parameter; current `GLPK_CMD` path is effectively single-core.
- Verify the correctness of the implementation with the provided paper
- Optimize commonly used files with overheads
- Optimize instance generator
