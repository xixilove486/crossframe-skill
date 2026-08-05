# Ultra runtime protocol

## Inputs

- A host-confirmed exact Ultra activation, immutable request bytes, and selected `production` or `test` mode. A resumed or externally established run also carries its already sealed sensitivity, outbound permission, capability matrix, and resource bounds.
- An eligible fresh canonical closed-input run uses the frozen runtime-owned bootstrap profile: sensitivity `private`; retention `retain`; outbound permission `deidentified-only`; filesystem, validators, and model context `available`; DOCX parser, network, retrieval, and subagents `not-applicable`; and the promoted resource limits 64 branches, 2 no-novelty retrieval rounds, 3 tool retries, and 3 repair attempts. The caller cannot override this profile, and selecting it grants no outbound or real-world retrieval authority.
- The U1 authority seal, U2 retrieval seal, U3 evidence cutoff, and each preceding immutable phase event.
- The exact commands, authoring slots, fixed roots, and template cross-links in `references/runtime-routing-map.md`.

## Outputs

- One run package beneath the selected fixed root with status, input snapshot, independent request-intake authority, U0–U12 phase events, authoring area, artifacts, validation attempts, recovery data, logs, indexes, and delivery transaction state.
- Runtime-owned identity, version bindings, hashes, phase ancestry, status, indexes, manifests, and final-chat projection derived from sealed control state.
- A final `complete` state only after U12; otherwise preserve one of the other closed run states and a recovery or attention boundary.

## Dependencies

- Use `scripts/ultra_runtime/paths.py`, `status.py`, `state_machine.py`, `locks.py`, `jsonio.py`, and Task 13's `crossframe_ultra_runtime.py` CLI/materializer once integrated.
- Move through U0–U12 in order. On the eligible fresh foundation branch, U01–U03 remain absent and runtime-owned; model authoring begins at U04. Resume an existing U0, U1, or U2 checkpoint from its next phase, and reject uncheckpointed downstream residue instead of overwriting it. The runtime owns control fields and validates every transition.
- Keep production and test roots distinct. Use locks, leases, heartbeats, compare-and-swap phase heads, same-volume staging, flush, atomic replace, and durable transaction recovery.

## Stop/Failure

Reject an implicit/near-miss route, mixed runtime intent without confirmation, non-current version, non-canonical or ineligible fresh input, caller-authored U0–U3 authority, phase skip, changed U3 evidence, stale parent hash, forged control field, second writer, cancelled run, root escape, or arbitrary directory flag. Missing Task 13 CLI/materialization is an unmet dependency, not permission to synthesize a substitute or issue a final answer.

## Corresponding validator

Validate each phase artifact with `validate_phase_artifact` and the state-machine transition checks. At U12 run Task 12's `check_crossframe_ultra_artifacts.py` against the on-disk run, invoked only through Task 13's `crossframe_ultra_runtime.py` fixed-root commands.
