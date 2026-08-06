# CrossFrame Ultra host adapter contract

This is the provider-neutral boundary between a real Agent host and the fixed Ultra runtime. It does not replace the runtime, schemas, promoted v8.2 source, registry, or contracts, and it does not bind the core runtime to a private SDK.

## Activation and request

Exact naming limits activation only. After the host has selected Ultra, pass the user's ordinary UTF-8 natural-language request bytes unchanged; they default to `open-world`. Use `closed-input` only for an explicit materials-only request with independently supplied, non-empty materials that the runtime inventories and hashes. Never manufacture a closed universe by copying the question into material.

## Persistent loop

1. Call `start`, then call `prepare` for the returned run ID.
2. Read the runtime-issued `recovery/pending-action.json` or the model-owned authoring slot returned by `prepare`.
3. Execute the one pending action with a real authorized host tool. Write only the requested action result to the fixed result slot.
4. Submit the separate bound receipt through the provider-neutral adapter callback `ultra_runtime.host_handshake.accept_host_result(...)`. Admission first freezes the exact canonical result bytes as the internal `recovery/host-results/<action-sha256>/accepted-result.json`, then writes the existing `accepted.json` receipt whose `result_sha256` binds that snapshot. This is the existing adapter seam, 不是新的 CLI 命令.
5. After runtime admission succeeds, call `materialize`. Let the runtime seal, release its writer lease, and issue the next action.
6. Repeat until U12 passes or the runtime returns a terminal boundary.

`outcome=awaiting-host-action` and `outcome=awaiting-authoring` are successful normal progress with `status=running`; execute the single next action and continue. Do not relabel either outcome as an exception, validation failure, or `needs_attention`.

## Action mapping

| Action kind | Host duty | Result boundary |
| --- | --- | --- |
| `capability-attestation` | Measure actual filesystem, parser, network, retrieval, validator, subagent, model-context, privacy, ACL, provider, tool, and resource availability. | Return measured facts and proof grade; do not author the U0 run contract. |
| `source-read` | Use the issued read plan to perform real source-unit reads, directly or through an authorized controlled reader. | Return execution-bound read receipts; runtime hash and coverage checks do not prove a reader acted. |
| `retrieval` | Call the issued real web/search/browser tool with the authorized deidentified query. | Return source-bearing receipts with lineage, limited extracts, hashes, interests, and `cannot_prove`. |
| `subagent` | Run only the issued bounded discovery, counterexample, affected-position, source-lineage, or calibration task. | Return an untrusted `candidate`; it is not evidence before source verification and U3 admission. |
| `evidence-authoring` | Produce only the requested evidence or semantic candidate in the fixed slot. | Do not assign evidence identity, phase authority, final judgment, or publication state. |
| `semantic-review` | At U11, execute the issued fresh review with the bound reviewer/provider/execution identity and all nine requested dimensions. | Return only the action-bound judgment; runtime owns the semantic-review artifact envelope and publication disposition, and the result cannot override deterministic or adversarial failure. |

Codex, Reasonix, Claude, and other adapters translate their real tool results into this same receipt shape. Preserve the runtime's action ID, action SHA-256, request/run/version/parent binding, provider/tool/execution identity, actual execution status, attempts, timestamps, content hashes, and fixed result-relative path. Every runtime-issued action carries a 30-minute `expires_at`; a successful receipt must complete from `issued_at` through `expires_at`, inclusive. A receipt is untrusted until runtime admission; the adapter cannot promote a candidate by labeling it evidence.

## Ownership and failure

The host may write only the action result slot or current model-owned authoring slot. Never hand-edit or delete status, control, pending-action authority, phase events, checkpoints, validation attempts, manifests, indexes, delivery state, or lease files. Never acquire authority by clearing a lease or rebuilding a hash. Use runtime `resume`, `cancel`, repair, and publication commands at their documented boundaries.

The fixed `work/host/...` result path is an adapter-owned mutable submission slot only. After admission, U0-U3, subagent, and semantic consumers revalidate `accepted.json` to `accepted-result.json` and their runtime projection; changing or reusing the submission slot cannot change accepted authority, while changing the accepted snapshot fails closed. Invalid, unauthorized, expired, replayed, parent-mismatched, unsafe, cancelled, terminal, or unavailable required work fails closed. Required retrieval cannot become `not-applicable`. Late evidence uses `evidence-fork` to create a child with a fresh U0 attestation and later cutoff; it never mutates the parent. Ultra failure does not fall back to Max, ProMax, suite, another runtime, or a chat-only answer.
