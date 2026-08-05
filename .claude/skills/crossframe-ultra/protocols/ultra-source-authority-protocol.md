# Ultra source authority protocol

## Inputs

- The promoted `references/source-manifest.json`, `references/release-manifest.json`, and `references/compatibility-matrix.json`.
- The promoted `references/v8.2-full-source/` tree, route map, complete concept registry, contract map, and contract files.
- The current repository root, run mode, fixed-root authority, U0 request/input hashes, capability matrix, and resource measurements.

## Outputs

- A sealed U1 prerequisite measurement and source lock bound to the current version, release manifest, compatibility matrix, knowledge closure, canonical skill-tree hashes, fixed root, ACL, and free-space reserve.
- A complete read plan and issuer-produced read events for every source unit before U2.
- A verified full-registry authority surface for later per-concept dispositions; indexes locate source units but never replace their content.

## Dependencies

- Use `scripts/ultra_runtime/source_integrity.py`, `scripts/ultra_runtime/schemas.py`, and `scripts/ultra_runtime/concept_closure.py`.
- Treat v8.2-r1 as authoritative only after build, validation, and promotion. Never select a document by a “latest” filename and never import v8.0 authority.
- Keep source definitions, runtime constraints, and writing guidance separate. Record a possible framework defect later in U10 instead of altering source authority.

## Stop/Failure

Stop U1 and close downstream execution when any source/release/knowledge hash is stale, the release artifact inventory differs from the exact canonical tree, a source unit is unread or duplicated, a registry/contract/route reference is open, or a symlink/reparse point enters authority. Also stop when the fixed root, ACL, capability, compatibility, or reserve check is not valid. Do not fall back to another framework, runtime, directory, or unpromoted source.

## Corresponding validator

Run `scripts/check_crossframe_ultra_v82_source.py` and `scripts/check_crossframe_ultra_v82_knowledge.py`, then validate the U1 artifacts through `validate_u1_authority`, `validate_source_lock`, and the public schemas. U12 must remeasure release-manifest freshness rather than trusting the U1 report alone.
