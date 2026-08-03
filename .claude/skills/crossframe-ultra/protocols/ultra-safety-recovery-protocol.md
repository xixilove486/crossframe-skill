# Ultra safety and recovery protocol

## Inputs

- Selected fixed mode/root, normalized run layout, neutral system-generated run ID, sensitivity/outbound policy, capability/resource bounds, writer lease, heartbeat, and cancellation state.
- Immutable phase events, checkpoints, artifact hashes, evidence cutoff, current compatibility result, in-progress publication transaction, and last fully verified boundary.

## Outputs

- Single-writer run state, atomic same-volume writes, per-phase and per-article-packet checkpoints, bounded logs, and a recoverable transaction record.
- On interruption, the last complete hash-valid checkpoint, quarantined partial bytes, and explicit `interrupted`, `blocked`, `needs_attention`, `failed`, `cancelled`, or fork-required disposition.
- On fork, a new run ID and migration ledger that reference immutable parent inputs/artifacts by hash without modifying the parent.

## Dependencies

- Use `scripts/ultra_runtime/paths.py`, `locks.py`, `jsonio.py`, `status.py`, and Task 12 recovery/artifact modules after integration.
- Normalize every path under the fixed root; reject traversal, absolute injection, illegal Windows components, excess length, and symlink/reparse escape.
- Resume only when the checkpoint verifies and the framework/runtime/schema/validator/article binding, input bytes, and evidence cutoff are compatible. Cancellation stops new tools after its final status event.

## Stop/Failure

<!-- ULTRA-FIXED-ROOT-FAILS-CLOSED -->
An unavailable, unsafe, colliding, or unwritable fixed root closes the run. Never fall back to current, temporary, source, install, Max, or ProMax locations. Reject a corrupt checkpoint, changed input/evidence cutoff, incompatible runtime/validator, lost lease, second writer, half-written active file, or retry/resource limit; preserve recoverable bytes and choose read-only, fork-required, needs-attention, failed, or cancelled as the verified condition requires.

## Corresponding validator

Validate layout and path containment through the path runtime, lease/heartbeat ownership through the lock runtime, status ancestry through the status store, and each checkpoint against `ultra-recovery-checkpoint.schema.json`. Task 12's fresh `check_crossframe_ultra_artifacts.py` must verify recovery and publication state from disk before resume or delivery.
