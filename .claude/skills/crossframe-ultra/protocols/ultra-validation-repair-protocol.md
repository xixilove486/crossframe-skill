# Ultra validation and repair protocol

## Inputs

- The completed on-disk authoring tree, immutable upstream artifact DAG, current release/source/compatibility authority, phase/checkpoint chain, staging manifest, partial article, semantic coverage, article review, and transaction state.
- No in-memory object from the generating context as proof. Validation starts after authoring and reloads exact bytes under a new attempt ID.

## Outputs

- `validation/attempts/<attempt-id>/ultra-validator-report.json`, verified before atomic promotion to `validation/current`.
- For each failure: error code, artifact, earliest affected phase, downstream reset set, retryability, and concrete repair action.
- A schema-valid repair plan preserving unaffected upstream hashes; after a pass, official delivery, final manifest, indexes, `complete`, and final-chat projection.

## Dependencies

- Use Task 12's independent validation/artifact/repair modules and canonical `check_crossframe_ultra_artifacts.py` plus `build_crossframe_ultra_repair_plan.py` after integration.
- Revalidate source and release freshness, version binding, tree coverage, every structured artifact, hash ancestry, identity/provenance, world structure, recursion inheritance, judgment, forecasts, semantic coverage, blind recovery, fixed-root writes, privacy, logs, checkpoints, and delivery transaction.
- Task 13 alone performs materialization and official promotion after the fresh report passes.

## Stop/Failure

<!-- ULTRA-FRESH-CONTEXT-VALIDATION -->
Reject stale/copied/edited reports, another run's manifest, marker stuffing, fake reads, source/article hash mismatch, simulated-as-fact material, flattened state, lost lineage, root escape, secret leakage, early official delivery, or an overbroad repair plan. <!-- ULTRA-BOUNDED-LOCAL-REPAIR --> Repair only the earliest affected phase and downstream, revalidate fresh after each attempt, and refuse a fourth repair attempt; repeated failure becomes `needs_attention`. Never edit a report or reset a valid earlier phase to obtain a pass.

## Corresponding validator

Run the canonical `check_crossframe_ultra_artifacts.py` from a fresh process, validate its output with `ultra-validator-report.schema.json`, build the plan with `build_crossframe_ultra_repair_plan.py`, and validate it with `ultra-repair-plan.schema.json`. Only a freshly verified pass can authorize U12, official delivery, release/run manifests, index updates, and final chat.
