# CrossFrame Ultra Skill runtime routing map

This file is the compact execution map. It does not replace the promoted v8.2 source, concept registry, contracts, schemas, or responsibility protocols.

## Fixed roots

| Role | Absolute root |
| --- | --- |
| canonical source | `E:\世界模型\skill\crossframe-skill\skills\crossframe-ultra` |
| Codex install | `C:\Users\cangm\.codex\skills\crossframe-ultra` |
| Reasonix install | `C:\Users\cangm\.agents\skills\crossframe-ultra` |
| Claude install | `C:\Users\cangm\.claude\skills\crossframe-ultra` |
| production | `E:\世界模型\output\crossframe-ultra` |
| test | `E:\世界模型\output\crossframe-ultra-tests` |

Resolve every generated path beneath the selected production or test root. Reject an unavailable root, a root collision, traversal, symlink, reparse point, or path escape; never choose a replacement root.

## Runtime installation coherence

Execute `<repo>\skills\crossframe-ultra\scripts\crossframe_ultra_runtime.py` and pass that exact same `<repo>` to `--repo`. Codex uses `C:\Users\cangm\.codex`, Reasonix uses `C:\Users\cangm\.agents`, and Claude uses `C:\Users\cangm\.claude`. Never mix a script from one installation tree with authority files from another tree or from the canonical source checkout.

## Exact CLI

Prefix every signature below with `python -B <repo>\skills\crossframe-ultra\scripts\crossframe_ultra_runtime.py`, and pass that same resolved `<repo>` to `--repo`. Do not add a parameter that is not present in the Task 13 parser.

<!-- ULTRA-CLI-BEGIN -->
```text
start          --repo PATH --mode production|test (--request-file PATH | --request-stdin) [--material-file PATH ...]
prepare        --repo PATH --mode production|test --run-id RUN_ID
checkpoint     --repo PATH --mode production|test --run-id RUN_ID --phase U0..U11
materialize    --repo PATH --mode production|test --run-id RUN_ID
validate       --repo PATH --mode production|test --run-id RUN_ID [--json]
repair-plan    --repo PATH --mode production|test --run-id RUN_ID
resume         --repo PATH --mode production|test --run-id RUN_ID
fork           --repo PATH --mode production|test --run-id RUN_ID --reason TEXT
cancel         --repo PATH --mode production|test --run-id RUN_ID
rebuild-index  --repo PATH --mode production|test
```
<!-- ULTRA-CLI-END -->

The production CLI contains none of:

<!-- ULTRA-FORBIDDEN-CLI-OPTIONS-BEGIN -->
- `--run-dir`
- `--authoring-dir`
- `--output-root`
- `--destination`
- `--fallback`
<!-- ULTRA-FORBIDDEN-CLI-OPTIONS-END -->

Use `--request-stdin` when request text should not enter process arguments. `start` copies the exact request bytes into the run input directory, records their hash, and independently seals `recovery/request-intake-authority.json`; it never embeds request text in a run ID, path, or index. Replacing both request bytes and metadata after `start` does not replace that authority and is rejected.

### Request branches

Exact Ultra naming applies to activation only. `start` accepts ordinary UTF-8 natural-language request bytes and freezes them unchanged; such a fresh request defaults to `analysis_kind=open-world`. Attachments or long materials enter only through repeated `--material-file` inputs and a runtime-owned immutable inventory.

Use `closed-input` only when the user explicitly requests a materials-only boundary and independently supplied, non-empty materials close the full evidence universe. The runtime must bind the inventory and material-universe hash. The question cannot serve as both claim and invented material. `pure-logic` remains a separately proven eligibility basis. If neither special branch is independently established, keep open-world.

Do not include caller-authored IDs, hashes, version bindings, policy fields, capability assertions, read receipts, retrieval dispositions, evidence envelopes, phase events, checkpoints, or leases in request payloads or materials.

### Persistent host loop

The provider-neutral loop is:

1. `start` freezes request bytes and input inventory.
2. `prepare` idempotently returns the current `recovery/pending-action.json`, its fixed `work/host/...` result slot, or the next model-owned authoring slot.
3. The host executes the pending action with a real authorized tool and writes only the requested receipt or semantic file to that slot.
4. `materialize` validates and admits the result, seals any completed phase, releases the writer lease, and either returns the next action or advances.
5. Repeat through U12; use `validate`, `repair-plan`, and `resume` only at their declared boundaries.

The runtime can issue these host action kinds:

- `capability-attestation`: measure actual provider/tool availability, privacy permission, ACL, proof grade, and resource limits for U0.
- `source-read`: execute the fixed U1 read plan and return source-unit-bound read receipts; runtime verification cannot stand in for a real reader.
- `retrieval`: run the issued deidentified query with an actual web/search/browser provider and return source-bearing receipts for U2.
- `subagent`: run the bounded task for discovery, counterexample, affected-position, source-lineage, or calibration work; its output remains an untrusted candidate.
- `evidence-authoring`: write only the action-bound evidence or semantic result requested by the runtime; it cannot assign evidence identity or control fields.

The host adapter contract is `references/host-adapter-contract.md`. It translates real Codex, Reasonix, Claude, or other host tools into the same action/receipt boundary; the core runtime does not guess a provider API. A subagent or model `candidate` is not evidence until source verification and U3 admission accept it.

`outcome=awaiting-host-action` and `outcome=awaiting-authoring` are successful normal progress with `status=running`, a released writer lease, and one next action. They are not exceptions, validation failures, or `needs_attention`. Invalid, expired, unauthorized, replayed, or parent-mismatched receipts fail closed.

Never hand-edit or delete control state, pending action authority, phase events, checkpoints, validation history, manifests, or lease files. Resume only through runtime commands. New evidence after U3 uses `evidence-fork`, which creates a child that begins with its own U0 attestation; it does not reopen or rewrite the parent. Ultra failure never selects a fallback runtime.

## Phase routing

| Phase | Required responsibility | Primary protocol |
| --- | --- | --- |
| U0 | Explicit trigger, request profile, host capability attestation, sensitivity, outbound permission, ACL, and resource bounds | `protocols/ultra-runtime-protocol.md` |
| U1 | Framework, runtime, schema, tool, input, root, release tree, read plan, and accepted source-read receipts | `protocols/ultra-source-authority-protocol.md` |
| U2 | Retrieval qualification, issued real-host retrieval/subagent actions, admission, or sealed not-applicable disposition | `references/retrieval-policy.md` |
| U3 | Evidence freeze, provenance, identity, and cutoff | `protocols/ultra-runtime-protocol.md` |
| U4 | Complete initial Ω world volume | `protocols/ultra-world-volume-protocol.md` |
| U5 | Scale, circle, translation, closure, loss, residual, and registry-disposition audit | `protocols/ultra-world-volume-protocol.md` |
| U6 | Claims, mechanisms, competitors, and qualified insights | `protocols/ultra-judgment-protocol.md` |
| U7 | Order 1–3 recursive state volumes and lineage | `protocols/ultra-recursive-inference-protocol.md` |
| U8 | Per-order evaluation, simple baseline, red team, sensitivity, and stop decision | `protocols/ultra-recursive-inference-protocol.md` |
| U9 | Main judgment, five verdicts, action ranking, and immutable forecast originals | `protocols/ultra-judgment-protocol.md` |
| U10 | Isolated framework-gap ledger, output plan, and coverage responsibilities | `protocols/ultra-article-protocol.md` |
| U11 | Structured artifacts, dossier, packets, partial article, coverage, and article review | `protocols/ultra-article-protocol.md` |
| U12 | Fresh disk validation, bounded repair, official delivery, indexes, and manifest | `protocols/ultra-validation-repair-protocol.md` |

Do not advance a phase until its upstream artifacts and phase event validate. New evidence after U3 requires a fork with a new cutoff. A framework-gap candidate remains isolated from the current run.

## Model-owned authoring slots

`prepare` declares the complete compatibility slot-path superset; ownership is branch-specific. The complete set is:

<!-- ULTRA-AUTHORING-SLOTS-BEGIN -->
- `work/authoring/U01-read-events.jsonl`
- `work/authoring/U02-retrieval-ledger.json`
- `work/authoring/U03-evidence-ledger.json`
- `work/authoring/U04-world-volume.json`
- `work/authoring/U05-transformation-ledger.json`
- `work/authoring/U05-concept-disposition.json`
- `work/authoring/U06-claim-mechanism-graph.json`
- `work/authoring/U07-recursive-states/<node-id>.json`
- `work/authoring/U07-recursive-lineage.json`
- `work/authoring/U08-order-evaluation.json`
- `work/authoring/U08-red-team-report.json`
- `work/authoring/U09-verdict.json`
- `work/authoring/U09-action-ranking.json`
- `work/authoring/U09-forecast-ledger.json`
- `work/authoring/U10-framework-gap-ledger.json`
- `work/authoring/U10-output-plan.json`
- `work/authoring/U11-semantic-coverage.json`
- `work/authoring/article/packets/<packet-id>.md`
- `work/authoring/U11-article-review.json`
- `work/authoring/完整推演档案.md`
<!-- ULTRA-AUTHORING-SLOTS-END -->

The runtime owns IDs, version bindings, hashes, phase events, status, manifests, indexes, validation reports, and delivery paths. It overwrites runtime-owned fields from sealed control state and never trusts a model-authored control value.

Fresh U11 semantic review is not an authoring slot. The runtime issues a persistent `semantic-review` host action with a fixed result slot, accepts the bound receipt through the host handshake, and projects `artifacts/U09-U10-verdict/U11-semantic-review.json` itself.

For the fresh foundation path, the listed U01–U03 authoring names are reserved compatibility slots and are not model-owned. Caller-authored U01 read events, U02 retrieval ledgers, and U03 evidence envelopes cannot authorize those phases; runtime artifacts are derived from accepted host receipts and frozen input. A model writes only the slot returned by `prepare`; ordinary semantic authoring begins at U04.

## Template authority

Task 11 provides the article-contract templates:

- `templates/ultra-output-plan-output.md`
- `templates/ultra-article-output.md`
- `templates/ultra-semantic-coverage-output.md`
- `templates/ultra-article-review-output.md`

Task 13 provides the materialization and publication templates:

- `templates/ultra-run-status-output.md`
- `templates/ultra-world-volume-output.md`
- `templates/ultra-transformation-ledger-output.md`
- `templates/ultra-concept-disposition-output.md`
- `templates/ultra-claim-mechanism-output.md`
- `templates/ultra-recursive-state-output.md`
- `templates/ultra-recursive-lineage-output.md`
- `templates/ultra-order-evaluation-output.md`
- `templates/ultra-retrieval-output.md`
- `templates/ultra-red-team-output.md`
- `templates/ultra-verdict-output.md`
- `templates/ultra-action-ranking-output.md`
- `templates/ultra-forecast-output.md`
- `templates/ultra-framework-gap-output.md`
- `templates/ultra-dossier-output.md`
- `templates/ultra-artifact-index-output.md`
- `templates/ultra-validator-report-output.md`
- `templates/ultra-repair-plan-output.md`

These are references to Task 11/Task 13-owned files, not permission for Task 14 to create or alter templates. If an integrated Task 13 template, CLI, or materializer is absent, stop at the dependency boundary and do not synthesize it.

## Materialization and delivery order

On a fresh open-world, eligible closed-input, or independently proven pure-logic run, repeated `prepare` / host execution / `materialize` cycles establish U0–U3 as described above. Materialization then validates and freezes recursive states before lineage, order evaluation before red team, verdict before action/forecast, and output plan before packets/coverage/review. It validates every semantic artifact, assembles only a partial article, writes staging control state, and starts the fresh checker from disk.

Only a passing U12 transaction may atomically promote:

- `delivery/CrossFrame-Ultra-完整文章.md`
- `delivery/完整推演档案.md`
- `delivery/工件索引.md`

On failure, the official article filename must not exist. Final chat is a projection of the validated run and contains absolute `article_path` and `run_path` values derived from the selected fixed root.
