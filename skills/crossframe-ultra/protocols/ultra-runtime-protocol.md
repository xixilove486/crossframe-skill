# Ultra runtime protocol

## Inputs

- A host-confirmed exact Ultra activation, immutable UTF-8 request bytes, optional runtime-inventoried material files, and selected `production` or `test` mode. Exact naming governs activation only; ordinary natural-language requests（普通自然语言问题）are valid payloads and default to `analysis_kind=open-world`.
- A `closed-input` request only when the user explicitly limits the run to independently supplied, non-empty materials whose inventory and material-universe hash close the evidence universe. `pure-logic` needs an independent eligibility basis; neither branch may be inferred by copying the question into material.
- A runtime-issued U0 `capability-attestation` action measuring the actual host, provider, tools, sensitivity, retention, outbound permission, ACL, availability, proof grade, and resource bounds. The caller cannot self-author the U0 contract.
- The U1 authority seal, U2 retrieval seal, U3 evidence cutoff, and each preceding immutable phase event.
- The exact commands, authoring slots, fixed roots, and template cross-links in `references/runtime-routing-map.md`.

## Outputs

- One run package beneath the selected fixed root with status, input snapshot, independent request-intake authority, U0–U12 phase events, authoring area, artifacts, validation attempts, recovery data, logs, indexes, and delivery transaction state.
- Runtime-owned identity, version bindings, hashes, phase ancestry, status, indexes, manifests, and final-chat projection derived from sealed control state.
- A final `complete` state only after U12; otherwise preserve one of the other closed run states and a recovery or attention boundary.
- A successful progress result with `status=running` and `outcome=awaiting-host-action` or `outcome=awaiting-authoring` when the unique next host result or semantic authoring slot is not yet present.

## Dependencies

- Use `scripts/ultra_runtime/paths.py`, `status.py`, `state_machine.py`, `locks.py`, `jsonio.py`, and Task 13's `crossframe_ultra_runtime.py` CLI/materializer once integrated.
- Use `scripts/ultra_runtime/host_handshake.py` and the fixed `recovery/pending-action.json` loop. `prepare` returns the pending `capability-attestation`, `source-read`, `retrieval`, `subagent`, or `evidence-authoring` action and fixed result slot; the host executes a real permitted tool, writes only that receipt or authoring slot, and `materialize` validates it before advancing.
- Move through U0–U12 in order. U0–U3 authority remains runtime-owned; model authoring begins only at a slot returned by `prepare`. Resume from the next phase after a verified checkpoint, and reject uncheckpointed downstream residue instead of overwriting it. Late evidence uses `evidence-fork` rather than mutating U3.
- Keep production and test roots distinct. Use locks, leases, heartbeats, compare-and-swap phase heads, same-volume staging, flush, atomic replace, and durable transaction recovery.

## Stop/Failure

Reject an implicit/near-miss route, mixed runtime intent without confirmation, non-current version, invalid closed-input claim, unauthorized or unbound host receipt, caller-authored U0–U3 authority, phase skip, changed U3 evidence, stale parent hash, forged control field, second writer, cancelled run, root escape, or arbitrary directory flag. Waiting for an unexpired result or authoring slot is normal progress, not failure. Never hand-edit control, checkpoint, validation history, or lease files; missing integration remains an unmet dependency and Ultra never falls back.

## Corresponding validator

Validate each phase artifact with `validate_phase_artifact` and the state-machine transition checks. At U12 run Task 12's `check_crossframe_ultra_artifacts.py` against the on-disk run, invoked only through Task 13's `crossframe_ultra_runtime.py` fixed-root commands.
