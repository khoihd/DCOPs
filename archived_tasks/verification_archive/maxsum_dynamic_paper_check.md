# Dynamic MaxSum Paper Check

## Source

- Implementation: `pydcop/algorithms/maxsum_dynamic.py`
- Status: Done / No Separate Paper Source
- Result: Treat as a pyDcop-specific dynamic factor-graph extension around
  AMaxSum/MaxSum, not as a standalone paper algorithm.

## Source Search

No separate Dynamic MaxSum paper source was found for this module.
Internet and local documentation searches point instead to pyDcop's dynamic
DCOP and resilient-distribution work:

- `rust_deployment_2017`: discusses operating Max-Sum in dynamic ambient
  environments, but focuses on factor-graph element deployment and repair.
- `rust_self-organized_2018`: discusses resilient distribution and repair for
  dynamic physical multi-agent systems.
- `farinelli_decentralised_2008`: remains the source for the underlying
  Max-Sum message equations used through `maxsum.py` and `amaxsum.py`.

The module itself has no standalone algorithm metadata such as `GRAPH_TYPE`,
`algo_params`, or `build_computation()`. It exposes specialized computation
classes for changing factor functions, read-only/external-variable slicing,
and dynamic ADD/REMOVE factor-scope messages.

## Implementation Behavior

- `DynamicFunctionFactorComputation` supports changing a factor relation while
  keeping the same variable scope, then sends refreshed factor-to-variable
  messages.
- `FactorWithReadOnlyVariableComputation` starts from a neutral relation,
  subscribes to read-only variables, slices the full relation once their values
  are known, and sends updated costs when the sliced relation changes.
- `DynamicFactorComputation` supports relation changes whose optimized
  variable scope may change. Removed variables receive `REMOVE`, newly added
  variables receive `ADD` with initial factor costs, and retained variables now
  receive refreshed factor-to-variable costs.
- `DynamicFactorVariableComputation` handles `ADD` and `REMOVE` messages by
  updating its factor list, cost table, selected value, and outgoing
  variable-to-factor messages.
- Dynamic computations reuse AMaxSum parameters internally through a default
  AMaxSum definition with `noise:0`; they are not exposed as a normal CLI
  algorithm module.

## Review Fixes

- Forced dynamic factor sends now update `_prev_messages`, keeping stable
  message suppression state aligned with messages sent outside the normal
  AMaxSum receive loop.
- Dynamic factor scope changes now propagate refreshed costs to retained
  variables, not only `ADD`/`REMOVE` messages for added/removed variables.
- Dynamic variable `ADD` handling is idempotent: repeated `ADD` messages from
  the same factor update costs without duplicating the factor in the neighbor
  list.
- Tests that instantiated dynamic computations now use real `ComputationDef`
  objects with AMaxSum defaults instead of incomplete mocks.

## Existing Coverage

- `tests/unit/test_algorithms_dynamic_maxsum.py` covers fixed-scope function
  changes, read-only slicing, external-variable activation/deactivation,
  scope ADD/REMOVE behavior, retained-variable updates, idempotent ADD
  handling, variable-side REMOVE recomputation, and invalid scope changes.
- `tests/integration/dmaxsum_graphcoloring.py` covers dynamic scenario model
  expectations without starting the legacy dynamic Max-Sum runner.
- `tests/integration/dmaxsum_external_variable.py` remains a demonstration
  sample for dynamic MaxSum with external variables.

## Follow-Up

- No paper-correctness follow-up is required because no separate paper source
  was identified.
- The module remains a low-level helper implementation rather than a regular
  algorithm entry point.
