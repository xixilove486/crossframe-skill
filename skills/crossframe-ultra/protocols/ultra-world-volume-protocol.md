# Ultra world-volume protocol

## Inputs

- The frozen U3 evidence ledger, identities, source provenance, unknowns, cutoff, request boundary, and current version binding.
- The complete promoted concept registry, selected routes, contract requirements, and source read receipts.
- The U4/U5 authoring slots for world volume, transformations, and concept dispositions.

## Outputs

- U4 `ultra-world-volume`: complete actor/object, circle, circle-relation, actor-circle-role, local material/information, channel, event, asynchronous-clock, scale-profile, evidence, identity-criterion, unknown, residual, and local-spillover structures.
- U5 `ultra-transformation-ledger`: scale, circle-relation, and representation/translation transforms with input/output identity, effective variables, closure, loss, unknown, residual, and return conditions.
- U5 full-registry dispositions using only `applied`, `tested-rejected`, `not-applicable`, or `unknown-pending`, with independent request-bound rationale and all required route/contract/evidence/unknown/transformation links.

## Dependencies

- Use `scripts/ultra_runtime/world_volume.py`, `transformations.py`, and `concept_closure.py` with their public schemas.
- Preserve local multi-parent membership by declared basis, directed multi-relations, local M/Ψ, five asynchronous clocks, nine-axis local scale profiles, and real channel continuity.
- Keep observed/reported/inferred/competitor/user/model/simulated/unknown identities separate. Do not aggregate local states into one average or treat recursive depth as evidence strength.

## Stop/Failure

Stop when the world volume is flattened into a single tree/global label, IDs or endpoints are open, a channel-free location updates, a cross-circle hop lacks renewed channel/boundary/representation checks, local state or scale coverage is incomplete, transformations collapse their three kinds, or a registry item lacks a terminal disposition. `unknown-pending` must carry a condition branch and evidence plan; `not-applicable` cannot claim output material.

## Corresponding validator

Run `validate_world_volume`, `validate_local_state_coverage`, `validate_membership_bases`, `validate_transformations`, `validate_cascade`, and `validate_concept_closure`, then validate against `ultra-world-volume.schema.json`, `ultra-transformation-ledger.schema.json`, and `ultra-concept-disposition.schema.json`.
