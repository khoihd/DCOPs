- Review instance generators:
    - Let difference instances share common arguments from generate
      - Seed value
    
    - Utility [0, 9], hard constraint 999999, max and min objective
      - (DONE) Graph coloring: random-graph, scalefree, grid
      - (DONE) IoT
      - (DONE) Meeting scheduling
  
- Add option for the generator to name the instances:
  - Instance file name and in the instance file

- Add options for the generator to support multiple instances

- Add print out when agent sends and receive messages for debugging
- Check how the algorithm supports multi-threading
- Investigate optional multicore PuLP solving with a CBC backend and a
  `threads` parameter; current `GLPK_CMD` path is effectively single-core.
- Verify the correctness of the implementation with the provided paper
- Optimize commonly used files with overheads
- Optimize instance generator
