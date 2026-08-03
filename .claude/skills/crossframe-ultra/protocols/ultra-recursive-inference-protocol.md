# Ultra recursive inference protocol

## Inputs

- Sealed U4 world volume, U5 transformations/dispositions, and U6 claim-mechanism graph with ranked main, strongest competitor, mixed, and residual explanations.
- Frozen evidence/unknown identities, causal channels, asynchronous clocks, state diffs, residuals, baseline, branch budget, and maximum order three.
- Parent run/path/node IDs and the current framework/runtime/schema/tool binding.

## Outputs

- U7 order-1 direct consequences, order-2 changed action/resource/feedback/event-generation conditions, and order-3 institutionalization, lock-in, reversal, or cross-circle spillover.
- Immutable recursive state nodes and lineage covering main, strongest competitor, mixed, and residual paths, including inherited facts, unknowns, losses, residuals, identities, signals, and full state or bounded state subgraph.
- U8 per-order evaluation, simple-baseline comparison, branch merge/prune/stop records, red-team attacks, sensitivity results, and a justified continuation or legal early-stop decision.

## Dependencies

- Use `scripts/ultra_runtime/recursion.py`, the frozen upstream authority DAG, and the order/lineage/red-team schemas.
- Revalidate channel, boundary, representation qualification, and local clock at every hop. A child inherits structured state and identities, never only a parent conclusion.
- Compare explanatory increment, predictive increment, new assumptions, new losses, local predictability, and the value of another order.

## Stop/Failure

Reject an order that repeats the same claim, uses depth as evidence, omits a parent/state identity, loses inherited unknown/loss/residual records, invents a channel, folds simulated results into facts, prunes the strongest competitor without rule, or reports stopping without residual and likely-next-direction records. Stop no later than order three and earlier only under the schema's observable stop conditions.

## Corresponding validator

Validate every node with `ultra-recursive-state.schema.json`, then lineage with `validate_recursive_lineage` and `ultra-recursive-lineage.schema.json`. Validate U8 with `ultra-order-evaluation.schema.json` before `ultra-red-team-report.schema.json`; a schema-valid but authority-disconnected artifact still fails.
