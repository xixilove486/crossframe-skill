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
start          --repo PATH --mode production|test (--request-file PATH | --request-stdin)
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

### Fresh U0–U3 foundation

For a fresh CLI run, stdin or the request file must contain exactly one canonical closed-input envelope:

```json
{"analysis_kind":"closed-input","claim":"non-empty claim or question","material":"complete non-empty closed material"}
```

Encode it as UTF-8 without BOM, sort keys, use compact JSON separators, and terminate it with exactly one LF. The three keys above are the complete allowlist. Do not include caller-authored IDs, hashes, version bindings, policy fields, capability assertions, read receipts, retrieval dispositions, evidence envelopes, phase events, or checkpoints.

The supported order is `start` → `prepare` → write the U4–U11 semantic authoring slots → `materialize`. When no resumable checkpoint exists and the run is otherwise fresh, `materialize` establishes issuer-owned U0, performs the real U1 source read and seals all 4,753 read events, records closed-input U2 as `not-applicable`, freezes the request-bound U3 evidence, writes the four phase checkpoints, and then continues at U4. A retry resumes an existing U0, U1, U2, or U3 checkpoint and must not recreate sealed phases. Uncheckpointed downstream residue is never overwritten; it moves the run to `needs_attention`.

Selecting this eligible closed-input branch selects the frozen runtime-owned bootstrap profile: `sensitivity=private`, `retention=retain`, and `outbound_permission=deidentified-only`; filesystem, validators, and model context are `available`; the DOCX parser, network, retrieval, and subagents are `not-applicable`; resource limits are the promoted U0 values `64 / 2 / 3 / 3`. The caller cannot override this profile, and it grants no outbound or real-world retrieval authority.

If the request is ordinary free text, lacks a complete closed material universe, or requires real-world retrieval, do not relabel it as `closed-input`. Fresh materialization marks the run `blocked` and fails closed. Report that boundary once; do not loop through `resume`, `checkpoint`, `materialize`, or searches for an undocumented initializer.

## Phase routing

| Phase | Required responsibility | Primary protocol |
| --- | --- | --- |
| U0 | Explicit trigger, problem contract, sensitivity, outbound permission, capabilities, resource bounds | `protocols/ultra-runtime-protocol.md` |
| U1 | Framework, runtime, schema, tool, input, root, release tree, and source-read lock | `protocols/ultra-source-authority-protocol.md` |
| U2 | Retrieval qualification and execution, or sealed not-applicable disposition | `references/retrieval-policy.md` |
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

For the fresh foundation path, the listed U01–U03 authoring names are reserved compatibility slots and must remain absent. Caller-authored U01 read events, U02 retrieval ledgers, and U03 evidence envelopes cannot authorize those phases; `materialize` generates their canonical artifacts from frozen input and issuer measurements. Fresh authoring therefore begins at U04.

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

On an eligible fresh canonical closed-input run, `materialize` first establishes U0–U3 as described above. It then validates and freezes recursive states before lineage, order evaluation before red team, verdict before action/forecast, and output plan before packets/coverage/review. It validates every semantic artifact, assembles only a partial article, writes staging control state, and starts the fresh checker from disk.

Only a passing U12 transaction may atomically promote:

- `delivery/CrossFrame-Ultra-完整文章.md`
- `delivery/完整推演档案.md`
- `delivery/工件索引.md`

On failure, the official article filename must not exist. Final chat is a projection of the validated run and contains absolute `article_path` and `run_path` values derived from the selected fixed root.
