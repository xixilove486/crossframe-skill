# Task 1 Report: Persistent Host Action and Receipt Authority

## Scope

- Base: `f0e808d3bef871895b166abbecae73ca3c9afa8f`
- Commit message: `feat: add Ultra host handshake authority`
- Release manifests, mirrors, installs, pushes, merges, and existing forensic runs were not touched.

## RED evidence

- Handoff RED from the prior implementer: `3 failed, 9 skipped, 398 deselected`; the host-handshake module and schemas were absent at that point.
- Candidate implementation check: `7 failed, 5 passed, 398 deselected`; append-only attempt paths exceeded the runtime's 240-character fixed-root limit.
- Direct completion authority test: `1 failed`; a hand-constructed, invalid `HostResultSeal` did not raise.
- Replay audit test: `1 failed`; the replay was rejected but did not persist a submitted/rejected attempt pair.

## GREEN evidence

- Final focused command:
  `TMPDIR=/home/xi-kari/.cache/crossframe-ultra-tmp /home/xi-kari/.cache/crossframe-ultra-venv/bin/python -B -m pytest -q -s --basetemp=/tmp/u tests/test_ultra_host_handshake.py tests/test_ultra_schemas.py -k 'host_action or host_result'`
- Final focused result: `13 passed, 398 deselected`.
- Regression command covered the host handshake, all schemas, path guards, canonical JSON I/O, dependency guards, and v8.2 import isolation.
- Regression result: `493 passed, 6 subtests passed`.
- `python -B -m py_compile skills/crossframe-ultra/scripts/ultra_runtime/host_handshake.py` exited successfully.
- `git diff --check` exited successfully.

## Changed files

- `skills/crossframe-ultra/scripts/ultra_runtime/host_handshake.py`
- `skills/crossframe-ultra/schemas/ultra-host-action.schema.json`
- `skills/crossframe-ultra/schemas/ultra-host-result-receipt.schema.json`
- `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- `tests/test_ultra_host_handshake.py`
- `tests/test_ultra_schemas.py`
- `.superpowers/sdd/2026-08-05-crossframe-ultra-open-world-recovery/task-1-report.md`

## Implementation and self-review

- Persists one sealed `recovery/pending-action.json` and validates it when loaded.
- Binds result receipts to the sealed run, version, phase, action kind, parent event, request, action hash, and fixed result slot.
- Verifies both the receipt hash and the bytes in the fixed result slot.
- Persists append-only submitted/rejected attempts with short monotonic identifiers; the fixed Windows test-root target is 198 characters and its atomic temporary path is approximately 234 characters, both within the 240-character guard.
- Writes the immutable accepted receipt before clearing pending authority.
- Revalidates result authority in `complete_host_action`, so a caller cannot bypass acceptance by constructing a seal directly.
- Records rejected replays while retaining the immutable accepted receipt.

## Commit

- Commit SHA: reported in the task handoff immediately after commit creation. A Git commit cannot embed its own final SHA in a tracked file because changing the file changes the commit SHA; no stale pre-amend SHA is recorded here.
