# Task 2 Report: Natural-Language Request Profiles and Dynamic U0

## Scope

- Base: `ddd9988b1b5b79fa549ce39083d8e98b92564161`
- Commit message: `feat: restore Ultra natural-language U0`
- Release manifest regeneration, mirrors, local installs, pushes, merges, and the existing forensic run were left untouched.

## RED evidence

- The new foundation tests were written before the production foundation module and demonstrated that plain natural-language intake, independently sealed material inventories, host capability attestation, and `--material-file` did not exist.
- Existing fixtures exposed the old caller-sealed `capability_availability` path. They failed once `PhaseStore` required a validated capability attestation, proving the old path still encoded the drifted authority model.
- The first broader state-machine run also exposed stale release-manifest authority after source changes; regeneration remains intentionally deferred until the final release task.

## GREEN evidence

- Natural-language, U0 attestation, anonymous material inventory, CLI parser, and persisted recovery gate: `8 passed`.
- Full state-machine suite: `51 passed in 82.66s`.
- Capability/retrieval compatibility selection: `12 passed, 489 deselected in 51.49s`.
- CLI parser selection: `1 passed, 21 deselected`.
- Capability, input-inventory, and run-contract schema selection: `4 passed, 396 deselected`.
- `py_compile` for the changed runtime modules and `git diff --check` passed.

## Implementation

- Plain UTF-8 natural-language requests now resolve to `analysis_kind=open-world`.
- Closed input requires a separately copied and sealed material inventory; request and metadata files never count as material evidence.
- `start` accepts repeatable read-only `--material-file` arguments and stores generated anonymous material names under the fixed run root.
- U0 issues a persistent capability-attestation host action, validates measured availability and runtime-owned bindings, and advances only from an accepted receipt.
- `PhaseStore` consumes the validated capability seal rather than caller-supplied availability.
- Recovery revalidates the persisted attestation and does not infer measured availability from required capability state.
- Existing smoke, retrieval, CLI, recovery, schema, and state-machine fixtures now use the same attestation authority path.

## Changed files

- Runtime and schemas under `skills/crossframe-ultra/`
- `tests/test_ultra_foundation.py`
- `tests/ultra_capability_support.py`
- Updated Ultra CLI, recovery, retrieval, schema, state-machine, and fixed-root smoke tests

## Review boundary

Formal code review is deferred to the single final whole-branch audit requested by the user.
