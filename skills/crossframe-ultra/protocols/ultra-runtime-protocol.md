# Ultra runtime protocol

## Inputs

- A host-confirmed exact Ultra activation, immutable request bytes, selected `production` or `test` mode, sensitivity, outbound permission, capability matrix, and resource bounds.
- The U1 authority seal, U2 retrieval seal, U3 evidence cutoff, and each preceding immutable phase event.
- The exact commands, authoring slots, fixed roots, and template cross-links in `references/runtime-routing-map.md`.

## Outputs

- One run package beneath the selected fixed root with status, input snapshot, U0–U12 phase events, authoring area, artifacts, validation attempts, recovery data, logs, indexes, and delivery transaction state.
- Runtime-owned identity, version bindings, hashes, phase ancestry, status, indexes, manifests, and final-chat projection derived from sealed control state.
- A final `complete` state only after U12; otherwise preserve one of the other closed run states and a recovery or attention boundary.

## Dependencies

- Use `scripts/ultra_runtime/paths.py`, `status.py`, `state_machine.py`, `locks.py`, `jsonio.py`, and Task 13's `crossframe_ultra_runtime.py` CLI/materializer once integrated.
- Move through U0–U12 in order. The model writes only slots returned by `prepare`; the runtime owns control fields and validates every transition.
- Keep production and test roots distinct. Use locks, leases, heartbeats, compare-and-swap phase heads, same-volume staging, flush, atomic replace, and durable transaction recovery.

## Stop/Failure

Reject an implicit/near-miss route, mixed runtime intent without confirmation, non-current version, phase skip, changed U3 evidence, stale parent hash, forged control field, second writer, cancelled run, root escape, or arbitrary directory flag. Missing Task 13 CLI/materialization is an unmet dependency, not permission to synthesize a substitute or issue a final answer.

## Corresponding validator

Validate each phase artifact with `validate_phase_artifact` and the state-machine transition checks. At U12 run Task 12's `check_crossframe_ultra_artifacts.py` against the on-disk run, invoked only through Task 13's `crossframe_ultra_runtime.py` fixed-root commands.
