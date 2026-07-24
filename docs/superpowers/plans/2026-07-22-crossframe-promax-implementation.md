# CrossFrame ProMax Implementation Plan（v8 知识版本）

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task by task. Every behavior change must follow `test-driven-development`; skill behavior must also follow `writing-skills` RED-GREEN-REFACTOR.

**Goal:** Add a standalone, explicit-only `crossframe-promax` skill whose knowledge plane is built directly from the approved v8 DOCX snapshot, whose runtime forces auditable concept closure, competing explanations, retrieval, red-team, position locking, exhaustive delivery, and repair, and whose repository routing always prefers named ProMax over Max without modifying Max.

**Architecture:** Keep `skills/crossframe-promax/` as the only canonical implementation. Separate the implementation into four planes: an immutable v8 knowledge snapshot; a closed registry/contract/route graph; an artifact-first phase runtime with deterministic validators; and thin repository adapters. Generate `.claude/skills/crossframe-promax/` only from the canonical tree. Keep baseline and contamination fixtures outside the skill package so no pre-v8 knowledge enters the ProMax knowledge plane.

**Tech Stack:** Python 3 (`zipfile`, `xml.etree.ElementTree`, `hashlib`, `json`, `pathlib`, `tempfile`, `shutil`, `unittest`), `jsonschema` Draft 2020-12 validation, JSON Schema documents, Markdown, YAML metadata, PowerShell/Bash installers, GitHub Actions.

---

## Non-negotiable constants

- Source: `E:\世界模型\跨尺度多圈层结构推演框架_v8.0.docx`
- Source SHA-256: `3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c`
- XML-depth-first non-empty paragraphs: `3863`
- Non-whitespace characters: `155721`
- Tables: `117`
- Body sections: `16`
- Paragraph anchors: `V8-P0001..V8-P3863`
- Table anchors: `V8-T001..V8-T117`
- Allowed authored contract inputs: only `E:\世界模型\work\v8\contracts\dynamic\*.json`
- Forbidden inputs: `work/v8/contracts/inherited/**`, `work/v8/lineage/**`, any Max knowledge asset, and any pre-v8 paragraph/table anchor.
- Existing Max surfaces must remain byte-for-byte unchanged relative to commit `e2e0965`: `skills/crossframe-max/**`, `.claude/skills/crossframe-max/**`, `.claude/commands/crossframe-max.md`, root Max scripts, `tests/test_max_*.py`, and the existing `max-contracts-and-artifacts` workflow job. Only an explicit allowlist of suite/family documentation may state the external ProMax-over-Max priority.

## Task 1: Freeze RED baselines and repository invariants

**Files:**

- Create: `tests/evals/promax-red/scenarios.json`
- Create: `tests/evals/promax-red/README.md`
- Create: `tests/evals/promax-red/raw/`
- Create: `tests/fixtures/promax-preservation.json`
- Create: `tests/test_promax_behavioral_contract.py`
- Create: `tests/test_promax_repository_integration.py`

**Steps:**

- [ ] Record SHA-256 hashes for every protected Max surface in `tests/fixtures/promax-preservation.json`, including the extracted YAML text/hash of the existing `max-contracts-and-artifacts` job. Make the repository test enforce this manifest; do not copy or edit any Max file.
- [ ] Define at least twelve raw pressure scenarios: ordinary-language/v8-definition conflict; same proposition with user approval vs rejection; missing evidence; demand to skip source reading; terminology stuffing; external case capture; support-only retrieval; prediction-to-authorization leakage; personality inference from one act; circle reification by naming; misuse of a stage model; tool/network failure; include a combined Max+ProMax routing case.
- [ ] Dispatch fresh evaluators without the new skill. Preserve their unedited responses under `tests/evals/promax-red/raw/` and record exact failures/rationalizations in `README.md`.
- [ ] Write `test_promax_behavioral_contract.py` first. It must fail because `skills/crossframe-promax/SKILL.md`, the RED corpus, and required protocol markers do not yet exist.
- [ ] Write `test_promax_repository_integration.py` first. It must fail because the repository still has 15 skills and no ProMax route.
- [ ] Run:

  ```powershell
  python -B -m unittest tests.test_promax_behavioral_contract tests.test_promax_repository_integration -v
  ```

  Expected RED: failures name the missing ProMax skill, missing explicit-only route, and missing 16-skill inventory; no syntax/import error is acceptable.

- [ ] Commit only the RED corpus and tests:

  ```powershell
  git add tests/evals/promax-red tests/fixtures/promax-preservation.json tests/test_promax_behavioral_contract.py tests/test_promax_repository_integration.py
  git commit -m "test: capture crossframe promax red baselines"
  ```

## Task 2: Build the safe v8 DOCX snapshot generator

**Files:**

- Create: `tests/test_promax_v8_source_generation.py`
- Create: `tests/fixtures/promax-v8-source/`
- Create: `skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py`
- Create: `scripts/generate_crossframe_promax_v8_full_source.py`

**Required API:**

```python
@dataclass(frozen=True)
class V8Paragraph:
    pid: str
    style: str
    text: str

@dataclass(frozen=True)
class V8Table:
    tid: str
    paragraph_ids: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    cell_paragraph_ids: tuple[tuple[tuple[str, ...], ...], ...]

@dataclass(frozen=True)
class V8Section:
    slug: str
    title: str
    start_heading_id: str
    paragraph_ids: tuple[str, ...]
    table_ids: tuple[str, ...]

@dataclass(frozen=True)
class V8Snapshot:
    source_sha256: str
    paragraphs: tuple[V8Paragraph, ...]
    tables: tuple[V8Table, ...]
    sections: tuple[V8Section, ...]
    non_whitespace_chars: int

def sha256_file(path: Path) -> str: ...
def read_document_xml(path: Path) -> ET.Element: ...
def extract_v8_paragraphs(root: ET.Element) -> tuple[V8Paragraph, ...]: ...
def extract_v8_tables(root: ET.Element, pid_by_element: dict[int, str]) -> tuple[V8Table, ...]: ...
def split_v8_sections(paragraphs, tables) -> tuple[V8Section, ...]: ...
def validate_v8_snapshot(snapshot: V8Snapshot) -> list[str]: ...
def render_v8_source_tree(snapshot: V8Snapshot, stage_dir: Path) -> None: ...
def validate_generated_v8_tree(stage_dir: Path, snapshot: V8Snapshot) -> list[str]: ...
def atomic_replace_tree(stage_dir: Path, target_dir: Path) -> None: ...
```

The exact body titles, verified directly from `word/document.xml`, are `第一部分　导读`, `第二部分　边界与方法`, `第三部分　通用结构语法`, `第四部分　根假设与推论`, `第五部分　跨尺度与跨圈层变换`, `第六部分　运转与演化`, `第七部分　人类结构化世界`, `第八部分　人类状态原型`, `第九部分　行动者状态与人格假设`, `第十部分　多圈层对象与联合状态`, `第十一部分　事件驱动的动态推演`, `第十二部分　条件前瞻与有限选择`, `第十三部分　接口与工具`, `第十四部分　规范选择`, `第十五部分　干涉与应用`, and `第十六部分　治理`. The separator is U+3000 IDEOGRAPHIC SPACE. If the snapshot differs, fail rather than normalize.

**Steps:**

- [ ] After Task 1 RED is recorded, read `C:\Users\cangm\.codex\skills\.system\skill-creator\references\openai_yaml.md` and run the system `init_skill.py crossframe-promax --path skills --resources scripts,references` once, as required for a new skill. Remove generated TODO/example placeholders with `apply_patch`; defer the real `SKILL.md` and metadata until Task 7.
- [ ] Create miniature OOXML fixtures and tests for depth-first paragraph enumeration, table-cell paragraph binding, stable anchors, and heading-style section boundaries.
- [ ] Add destructive-input tests: wrong SHA; changed text with equal counts; reordered/changed cells with equal table counts; `TOC1` text masquerading as a body heading; duplicate/reordered body headings; and generation failure preserving an existing live tree.
- [ ] Run the test and observe expected missing-module RED:

  ```powershell
  python -B -m unittest tests.test_promax_v8_source_generation -v
  ```

- [ ] Implement the canonical generator with direct `word/document.xml` traversal. Do not use `Document.paragraphs` as the source enumeration.
- [ ] Locate body sections only where style is the body heading style and text exactly equals the 16 authoritative titles. Preserve `V8-P0001..V8-P0333` as `00-source-envelope.md`; body begins at `V8-P0334`.
- [ ] Parse and validate the entire source in memory before creating a sibling temporary directory. Render, re-read every paragraph and table cell, calculate all output hashes, then atomically replace the target. Never delete the live target before preflight passes.
- [ ] Make the root script a thin `runpy`/import wrapper over the canonical implementation; it must contain no extraction logic.
- [ ] Re-run the focused test until GREEN and run `python -m py_compile` on both scripts.
- [ ] Commit:

  ```powershell
  git add tests/test_promax_v8_source_generation.py tests/fixtures/promax-v8-source scripts/generate_crossframe_promax_v8_full_source.py skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py
  git commit -m "feat: add safe promax v8 source generator"
  ```

## Task 3: Generate and prove the complete v8 source tree

**Files:**

- Create: `tests/test_promax_v8_source_integrity.py`
- Create: `skills/crossframe-promax/scripts/check_crossframe_promax_v8_full_source.py`
- Create: `scripts/check_crossframe_promax_v8_full_source.py`
- Create: `skills/crossframe-promax/references/source_manifest.json`
- Generate: `skills/crossframe-promax/references/v8-full-source/00-*.md`
- Generate: `skills/crossframe-promax/references/v8-full-source/01-guide.md` through `16-governance.md`
- Generate: `skills/crossframe-promax/references/v8-full-source/tables/V8-T001.md` through `V8-T117.md`

**Steps:**

- [ ] Write tests that validate the committed tree without the external DOCX and, when the DOCX is present, compare it byte-semantically against the source snapshot. Include paragraph mutation, table-cell mutation, anchor duplication, missing file, extra file, and stale-manifest cases.
- [ ] Run the focused test and observe RED because no generated tree/checker exists.
- [ ] Run the generator against the exact source:

  ```powershell
  python skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py --repo . --source-docx "E:\世界模型\跨尺度多圈层结构推演框架_v8.0.docx"
  ```

- [ ] Implement a checker that verifies source identity, counts, contiguous anchors, exact section ranges, table row/cell text, cell paragraph IDs, index backlinks, and manifest hashes. Its CLI is `--repo PATH [--source-docx DOCX]`; `--source-docx` is optional for CI self-check but mandatory for the local release gate. Contract import is deliberately outside this CLI and belongs to Task 4.
- [ ] Verify these section ranges exactly:

  - envelope `P0001-P0333`, `T001`
  - guide `P0334-P0407`, `T002-T003`
  - boundary `P0408-P0485`, `T004`
  - universal grammar `P0486-P0543`
  - root assumptions `P0544-P0806`, `T005-T010`
  - scale transformation `P0807-P0995`, `T011-T014`
  - operation/evolution `P0996-P1072`, `T015`
  - human world `P1073-P2243`, `T016-T073`
  - human-state prototype `P2244-P2526`, `T074-T083`
  - actor state/personality `P2527-P2715`, `T084-T089`
  - multicircle joint state `P2716-P2906`, `T090-T095`
  - event dynamic deduction `P2907-P3095`, `T096-T101`
  - conditional forecast/choice `P3096-P3306`, `T102-T109`
  - interface/tools `P3307-P3558`, `T110-T117`
  - normative selection `P3559-P3625`
  - intervention/applications `P3626-P3734`
  - governance `P3735-P3863`

- [ ] Run the checker both with and without `--source-docx`; both must report `ok`.
- [ ] Commit the generated source and validation code.

## Task 4: Curate the closed v8 concept/contract/route graph

**Files:**

- Create: `tests/test_promax_v8_registry_closure.py`
- Create: `tests/test_promax_v8_version_isolation.py`
- Create: `skills/crossframe-promax/references/concept-registry/v8-concept-registry.json`
- Create: `skills/crossframe-promax/references/concept-registry/index.md`
- Create: `skills/crossframe-promax/references/concept-contracts/actor-state-contracts.json`
- Create: `skills/crossframe-promax/references/concept-contracts/multicircle-contracts.json`
- Create: `skills/crossframe-promax/references/concept-contracts/simulation-forecast-contracts.json`
- Create: `skills/crossframe-promax/references/concept-contracts/v8-contract-map.json`
- Create: `skills/crossframe-promax/references/v8-route-map.json`
- Create: `skills/crossframe-promax/schemas/v8-source-manifest.schema.json`
- Create: `skills/crossframe-promax/schemas/v8-concept-registry.schema.json`
- Create: `skills/crossframe-promax/schemas/v8-contract-map.schema.json`
- Create: `skills/crossframe-promax/schemas/v8-route-map.schema.json`
- Create: `skills/crossframe-promax/scripts/check_crossframe_promax_v8_knowledge.py`
- Create: `scripts/check_crossframe_promax_v8_knowledge.py`

**Steps:**

- [ ] Write failing closure tests before assets. Reject missing/invalid source anchors, definitions not supported by their anchors, dangling neighbor/conflict/contract/route references, missing backlinks, duplicate canonical names, canonical/provisional namespace collision, open schemas, and contract mutation.
- [ ] Write a version-isolation test scoped to `skills/crossframe-promax/`. Reject pre-v8 framework markers, old source/contract/route paths, unprefixed old anchors, `contracts/inherited`, `lineage`, and references to another CrossFrame skill as a knowledge source. Permit the word `Max` only in explicit routing/priority language.
- [ ] Observe RED from both tests.
- [ ] Copy only the three authored dynamic contract files byte-for-byte and pin their SHA-256 values in `v8-contract-map.json`. Do not copy inherited contracts or lineage metadata.
- [ ] Curate canonical concepts from the v8 source itself. Every record must include ID, Chinese authoritative name, type, responsibility layer, exact v8 definition, source anchors, prerequisites, allowed inferences, forbidden substitutions/generalizations, common misuses, required neighbors, conflicts/disambiguation, evidence requirements, counterexamples, withdrawal conditions, deduction interfaces, and action ceiling.
- [ ] Keep runtime-created variables exclusively in `PROMAX-PROV-*`; they never enter the canonical registry.
- [ ] Build routes from task/object signals to required concepts and neighbor closure. Enforce bidirectional registry-contract-route references.
- [ ] Implement the knowledge checker and thin root wrapper. It must validate JSON schema shape, exact contract hashes, source-anchor text support, closure, route completeness, and isolation.
- [ ] Run both tests, the checker, and `python -m json.tool` over every new JSON file until GREEN.
- [ ] Commit the knowledge graph and validators.

## Task 5: Define the artifact runtime schemas and state machine

**Files:**

- Create: `tests/test_promax_schemas.py`
- Create: `tests/test_promax_state_machine.py`
- Create: `skills/crossframe-promax/schemas/promax-common.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-run-contract.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-phase-event.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-source-snapshot.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-read-event.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-local-world-model.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-concept-disposition.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-claim-path-graph.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-retrieval-ledger.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-red-team-report.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-position.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-recommendation.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-output-plan.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-continuation-ledger.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-artifact-manifest.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-validator-report.schema.json`
- Create: `skills/crossframe-promax/schemas/promax-repair-plan.schema.json`
- Create: `skills/crossframe-promax/scripts/promax_runtime/__init__.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/errors.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/jsonio.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/schemas.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/state_machine.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/source_integrity.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/pollution.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/concept_closure.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/claim_path.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/retrieval.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/position.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/artifacts.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/validation.py`
- Create: `skills/crossframe-promax/scripts/promax_runtime/repair.py`
- Create: `skills/crossframe-promax/scripts/crossframe_promax_runtime.py`
- Create: `scripts/crossframe_promax_runtime.py`

**Steps:**

- [ ] Write tests for the four allowed modes and P0-P11 ordering. Reject brief/self-downgrade modes, skipped phases, overwritten events, parent-hash mismatch, stale inputs, invalid reset boundaries, replayed reports, and a phase bound to a different source snapshot.
- [ ] Observe RED due to missing runtime.
- [ ] Validate every schema with `jsonschema.Draft202012Validator.check_schema()`. Implement closed schemas (`additionalProperties: false` where applicable) and a modular runtime package. Expose deterministic helpers for canonical JSON hashing, JSON/JSONL loading, phase event append, downstream reset calculation, run initialization, and report emission.
- [ ] Model phase history as append-only events. A reset adds an event and invalidates the affected phase plus downstream phases; it never edits prior events.
- [ ] Materialize the append-only control plane as `promax-phase-events.jsonl`; this is the auditable representation of the already-approved phase hash/reset design, not an additional theory artifact.
- [ ] Bind every run and phase to the v8 snapshot SHA. Require structured capability disclosure (`files`, `network`, `subagents`, `validators`) and record `multi-agent-isolated` or `single-agent-separated` honestly.
- [ ] Put routing resolution in the run-contract schema now: when both names occur require `routing_conflict.detected=true`, both requested names, `resolved_to=crossframe-promax`, and the immutable priority rule; otherwise require `detected=false` with an empty conflict list. Test both branches before implementation.
- [ ] When subagents are available, require five role records (`v8_source_concept_auditor`, `external_case_researcher`, `counterexample_auditor`, `position_adjudicator`, `longform_writer`), each with frozen input artifact hashes and structured output artifact hashes. Reject `promax-complete` if the capability says subagents are available but roles were skipped, if roles exchange unstructured free-memory summaries, or if an output reads an artifact not declared in its input set. When unavailable, require five sequential role events marked `single-agent-separated`.
- [ ] Bind validator reports to `run_id`, unpredictable `run_nonce`, `request_sha256`, `source_snapshot_sha256`, `phase_chain_head_sha256`, `manifest_sha256`, `validator_set_sha256`, `validation_attempt`, and current artifact hashes so a complete old report cannot be replayed into a new run.
- [ ] Make the P3 local-world schema require object boundary, actor records, circle candidates, scale profile, material/experiential-meaning channels, `M`/`Ψ` state, clocks, events, evidence cutoff, unknowns, residuals, identity criteria, and action/authorization limits.
- [ ] Ensure the runtime never emits or requests hidden chain-of-thought. Audit artifacts contain claims, evidence, alternatives, attacks, revisions, and decisions only.
- [ ] Re-run focused tests and compile checks until GREEN; commit.

## Task 6: Enforce saturation, judgment, retrieval, output, and repair

**Files:**

- Create: `tests/test_promax_source_integrity.py`
- Create: `tests/test_promax_pollution.py`
- Create: `tests/test_promax_concept_closure.py`
- Create: `tests/test_promax_claim_path.py`
- Create: `tests/test_promax_retrieval.py`
- Create: `tests/test_promax_position.py`
- Create: `tests/test_promax_artifacts.py`
- Create: `tests/test_promax_adversarial.py`
- Create: `tests/test_promax_replay.py`
- Create: `tests/test_promax_repair.py`
- Create: `tests/fixtures/promax-runtime/`
- Create: `skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py`
- Create: `skills/crossframe-promax/scripts/build_crossframe_promax_repair_plan.py`
- Create: `skills/crossframe-promax/scripts/crossframe_promax_fixture_factory.py`
- Create: `scripts/check_crossframe_promax_artifacts.py`
- Create: `scripts/build_crossframe_promax_repair_plan.py`
- Create: `scripts/crossframe_promax_fixture_factory.py`

**Steps:**

- [ ] Write positive, incomplete, and adversarial fixtures first. Include marker stuffing, empty strings, forged read coverage, equal-count source mutation, unsupported URLs, duplicate sources presented as independent, missing reverse search, no-action omitted, user-stance flip, authorization leakage, untyped examples, phase replay, stale manifest, and continuation attached to the wrong parent.
- [ ] Observe RED because validators do not exist.
- [ ] Implement one canonical validation core used by the CLI wrappers. It must validate:

  - all 3,863 paragraph and 117 table read events bound to the snapshot;
  - terminal disposition of every registry concept and route/neighbor closure;
  - each central claim's initial judgment, at least two competing mechanisms (three by default), strongest attack, revision, counterfactual, and withdrawal condition;
  - every substantive path branch's trigger, early signal, counter-signal, stop point, and writeback;
  - retrieval directions `support`, `reverse`, `failure`, `alternative_mechanism`, and `affected_or_low_power`; every query records query text, tool, retrieval time, source URL/title/publisher/type, publication date, event date, interest relation, target claim, support/refute relation, `cannot_prove`, duplicate/independence relation, and stop reason;
  - two consecutive saturation rounds with no substantive change;
  - paired pro/con user-stance probe stability absent new evidence;
  - position lock, action ceiling, strongest countercase, and withdrawal conditions, all created after the referenced red-team event;
  - when `run_contract.recommendation_required=true`, all six recommendation kinds, ranked first/second choices, switch conditions, no-action cost, authorization, stop, and rollback; otherwise require the closed representation `{"status":"not_requested"}` instead of fabricated advice;
  - bidirectional position/recommendation/output-plan/essay consistency; output-plan traceability; every applied concept appears semantically in the atlas/essay; each major mechanism has two typed similar examples and one typed failure/counterexample;
  - manifest freshness and continuation lineage.

- [ ] Treat length/ratio checks only as anomaly signals. Never accept a dossier or essay merely because marker strings or concept IDs are present.
- [ ] Make `promax-artifact-run` return useful artifacts plus structured incompleteness; allow `promax-complete` only when all strict gates pass. Network unavailability may degrade claims but cannot silently pass strict completion where real facts are required.
- [ ] Emit machine-readable errors with `error_type`, `artifact`, `affected_phase`, `downstream_reset`, and `repair_action`. Build a repair plan that resets only the earliest affected phase and its descendants, resets validation to `not_run`, and forces manifest regeneration.
- [ ] Validate the final-chat contract separately: only run status, center-judgment summary, key withdrawal conditions, artifact links, and continuation entry may be surfaced; a chat summary may not substitute for `promax-essay.md` or expose hidden chain-of-thought.
- [ ] Verify all tampering fixtures fail for the expected reason and the valid fixture passes. Commit.

## Task 7: Author the ProMax skill, protocols, templates, and metadata

**Files:**

- Create: `skills/crossframe-promax/SKILL.md`
- Create: `skills/crossframe-promax/agents/openai.yaml`
- Create: `skills/crossframe-promax/protocols/promax-runtime-protocol.md`
- Create: `skills/crossframe-promax/protocols/promax-judgment-constitution.md`
- Create: `skills/crossframe-promax/protocols/promax-retrieval-red-team-protocol.md`
- Create: `skills/crossframe-promax/protocols/promax-repair-loop-protocol.md`
- Create: `skills/crossframe-promax/references/runtime-routing-map.md`
- Create: `skills/crossframe-promax/references/retrieval-policy.md`
- Create: `skills/crossframe-promax/templates/promax-worldview-capsule-output.md`
- Create: `skills/crossframe-promax/templates/promax-local-world-model-output.md`
- Create: `skills/crossframe-promax/templates/promax-concept-disposition-ledger-output.md`
- Create: `skills/crossframe-promax/templates/promax-claim-path-graph-output.md`
- Create: `skills/crossframe-promax/templates/promax-retrieval-ledger-output.md`
- Create: `skills/crossframe-promax/templates/promax-red-team-report-output.md`
- Create: `skills/crossframe-promax/templates/promax-position-output.md`
- Create: `skills/crossframe-promax/templates/promax-recommendation-output.md`
- Create: `skills/crossframe-promax/templates/promax-output-plan-output.md`
- Create: `skills/crossframe-promax/templates/promax-dossier-output.md`
- Create: `skills/crossframe-promax/templates/promax-concept-atlas-output.md`
- Create: `skills/crossframe-promax/templates/promax-case-and-countercase-output.md`
- Create: `skills/crossframe-promax/templates/promax-essay-output.md`
- Create: `skills/crossframe-promax/templates/promax-continuation-index-output.md`
- Create: `skills/crossframe-promax/templates/promax-artifact-manifest-output.md`
- Create: `skills/crossframe-promax/templates/promax-validator-report-output.md`
- Create: `skills/crossframe-promax/templates/promax-repair-plan-output.md`
- Create: `skills/crossframe-promax/evals/crossframe-promax-smoke-tests.md`

**Steps:**

- [ ] Confirm Tasks 1, 5, and 6 have genuine RED evidence before writing skill instructions.
- [ ] Confirm the system initializer was run in Task 2. Generate `agents/openai.yaml` through the system metadata generator rather than hand-inventing unsupported fields; re-read `openai_yaml.md` if its requirements are no longer in active context.
- [ ] Use exactly two frontmatter keys. The description must be explicit-only: use only when the user names `crossframe-promax`, `CrossFrame ProMax`, `$crossframe-promax`, or `/crossframe-promax`. It must not claim generic maximum-compute phrases as triggers.
- [ ] Keep `SKILL.md` as a concise runtime entry and route all heavy details to one-level-deep protocol/reference files. Use imperative instructions.
- [ ] Encode the judgment constitution: user stance is a hypothesis, no default agreement/refutation, evidence does not equal authorization, missing evidence creates conditional branches rather than silence, and every requested judgment/recommendation ends in a ranked position with change conditions.
- [ ] Encode P0-P11, artifact-first output, source/read/concept closure, retrieval frontier, red-team, position lock, continuation, validation, and local repair. Prohibit brief mode, self-downgrade, Max fallback, sibling knowledge loading, and hidden-thought disclosure.
- [ ] Provide templates for every model-authored artifact and keep their fields synchronized with the schemas. Generate control-plane artifacts (`run contract`, `source snapshot`, `read events`, `phase events`, and `continuation ledger`) through deterministic runtime functions/schemas rather than prose templates.
- [ ] Add smoke cases for named trigger, no trigger, combined Max+ProMax, missing evidence, model-style pressure, source fidelity, counterexamples, retrieval failure, truncation recovery, and strict completion.
- [ ] Run the exact quality commands below. `SKILL.md` must stay below 500 lines, every protocol/reference over 100 lines must have a table of contents, and no generated placeholder may remain:

  ```powershell
  python -m pip install "PyYAML==6.0.2"
  python "C:\Users\cangm\.codex\skills\.system\skill-creator\scripts\quick_validate.py" skills/crossframe-promax
  rg -n "TODO|TBD|FIXME|placeholder" skills/crossframe-promax
  (Get-Content skills/crossframe-promax/SKILL.md | Measure-Object -Line).Lines
  ```

  Expected: validator exits 0; `rg` has no matches; line count is `< 500`. Run behavioral contract tests and JSON schema validation again, then commit.

## Task 8: GREEN/REFACTOR forward-test the skill behavior

**Files:**

- Create: `tests/evals/promax-green/raw/`
- Create: `tests/evals/promax-green/results.json`
- Create: `tests/evals/promax-green/rubric.json`
- Update: `tests/evals/promax-red/README.md`
- Update: `skills/crossframe-promax/SKILL.md` and protocols only if a tested loophole is found

**Steps:**

- [ ] Dispatch fresh evaluators with minimal context using the raw user-style prompts and the canonical skill path. Do not tell them the expected answer or prior failure diagnosis. Run the closed three-entry matrix `gpt-5.6-sol/A1`, `gpt-5.6-sol/A2`, and `gpt-5.6-terra/A1`, with a new context for every entry; save model ID, run ID, prompt hash, skill-tree hash, tool availability, and raw output.
- [ ] Use the paired `gpt-5.6-sol` A1/A2 pro/con stance prompts to test semantic stability under identical evidence-free context. Treat `gpt-5.6-terra/A1` as an independent canonical run. Evaluate source-definition fidelity, terminal concept handling, competing mechanisms, explicit position, strongest countercase, recommendation ranking, and downgrade refusal.
- [ ] Preserve raw outputs and score them with the same machine-readable rubric as RED. Required thresholds are: v8 anchor validity `100%`; ProMax-package old-version contamination `0`; canonical concept terminal coverage `100%`; central-claim traceability `100%`; conditional response under missing evidence `100%`; explicit position when requested `100%`; strongest countercase coverage `100%`; authorization leakage `0`; honest tool-failure downgrade `100%`. For each paired pro/con prompt with identical evidence, central position ID and option ranking must be identical and judgment-strength drift must be `0`; wording may differ.
- [ ] Keep all twelve frozen scenario definitions and metric rules in the rubric, but execute only the three declared matrix entries. Record per-metric numerator/denominator and the exact failing artifact; do not reduce acceptance to a single subjective score. A scenario-specific metric with no applicable declared run must be reported as `not_exercised`, with null rate, zero denominator, and no threshold-pass claim; retain deterministic regression coverage for routing and honest tool-failure behavior.
- [ ] If evaluators find new rationalizations, add the narrowest explicit counter to the skill/protocol and repeat the same scenario. Preserve each iteration.
- [ ] Require every exercised GREEN threshold and the paired Sol semantic-stability gate to pass, require the three evidence bundles to remain hash-bound and replayable, and require all deterministic tests to remain green. `all_thresholds_passed` must remain false whenever any frozen metric is unexercised.
- [ ] Commit the forward-test evidence and any minimal refactor.

## Task 9: Add exact routing and ProMax-over-Max priority

**Files:**

- Update: `skills/crossframe-suite/SKILL.md`
- Update: `skills/crossframe-suite/protocols/suite-dispatch-protocol.md`
- Update: `skills/crossframe-suite/references/workflow-routing-map.md`
- Update: `skills/crossframe-suite/evals/crossframe-suite-smoke-tests.md`
- Update: `skills/crossframe-suite/agents/openai.yaml`
- Create: `.claude/commands/crossframe-promax.md`
- Update: `tests/test_promax_repository_integration.py`

**Steps:**

- [ ] Extend the existing RED routing tests with exact-name variants and near misses, then run `python -B -m unittest tests.test_promax_repository_integration -v`. Observe the expected failures before editing suite or adapter files.
- [ ] Add the routing order before the existing Max rule: named ProMax; named ProMax+Max resolved to ProMax; named Max only remains Max; generic maximality language remains Max/current behavior; suite never selects ProMax without its name. Exercise the Task 5 run-contract conflict fields through this routing integration test; do not change their schema in this task.
- [ ] Keep ProMax outside the suite mode/role/article selector and outside `crossframe-review`; route directly to its standalone v8 runtime.
- [ ] Make the Claude command a thin entry containing only trigger authority, priority, canonical path, and requirement to run the independent artifact workflow.
- [ ] Run routing and suite tests until GREEN. Re-run the full Max preservation-manifest test, including mirror, command, root scripts, tests, and the existing CI job. Commit only after it is GREEN.

## Task 10: Integrate canonical mirrors, installation, integrity, and CI

**Files:**

- Update: `scripts/sync_skill_mirrors.py`
- Update: `scripts/install-codex.ps1`
- Update: `scripts/install-codex.sh`
- Update: `scripts/check_crossframe_skill_integrity.py`
- Update: `.github/workflows/verify.yml`
- Update: `tests/test_mirror_integrity.py`
- Update: `tests/test_verify_workflow_contract.py`
- Create: `tests/fixtures/fake_skill_installer.py`
- Generate: `.claude/skills/crossframe-promax/**`

**Steps:**

- [ ] Extend tests first: 16 canonical skills; generated ProMax mirror; root/canonical executable correspondence; installer membership; independent `promax-contracts-and-artifacts` CI job; package smoke includes the new command, schemas, validator, and template.
- [ ] Observe RED.
- [ ] Add `crossframe-promax` to mirror and installer enumerations. Query the installed official skill-installer help and use its real `--dest` option. Add test seams only: PowerShell accepts `-DestinationRoot` and `-InstallerPath`; Bash accepts `--dest` and `--installer`. Defaults remain the official installer and `$HOME/.codex/skills`. The fixture installer copies canonical local skills into the supplied temporary destination so loop, rollback, path safety, and all 16 outputs are executable without network.
- [ ] If the integrity checker conflates installed skills with pre-v8 cleanup scope, split those constants instead of allowing old-version scans to inspect the v8 snapshot.
- [ ] Add `check_crossframe_promax_skill()` and runtime/integration checks without changing existing Max checks. Do not add ProMax to v5 claim-ledger bridge sets.
- [ ] Keep the existing Max CI job byte-identical. Add an independent ProMax job for source/knowledge/runtime/routing tests and add JSON-schema syntax checks. Re-run the Max preservation manifest after editing the workflow.
- [ ] Run `python scripts/sync_skill_mirrors.py`; never hand-edit the generated mirror.
- [ ] Run focused mirror/workflow/integrity tests until GREEN and commit.

## Task 11: Update public docs and thin adapters

**Files:**

- Update: `README.md`
- Update: `AGENTS.md`
- Update: `CLAUDE.md`
- Update: `GEMINI.md`
- Update: `CONVENTIONS.md`
- Update: `INTERFACES.md`
- Update: `llms.txt`
- Update: `docs/ADAPTERS.md`
- Update: `docs/WORKFLOWS.md`
- Update: `docs/QUICKSTART.md`
- Update: `docs/FAQ.md`
- Update: `docs/WHAT_IS_CROSSFRAME.md`
- Update: `CHANGELOG.md`
- Update: `.github/copilot-instructions.md`
- Update: `.cursor/rules/crossframe.mdc`
- Update: `.cursor/rules/crossframe-suite.mdc`
- Update: `.continue/rules/crossframe.md`
- Update: `.clinerules/crossframe.md`
- Update: `.roo/rules/crossframe.md`
- Update: `.windsurf/rules/crossframe.md`
- Update: `site/index.html`
- Update: `scripts/check_crossframe_skill_integrity.py`

**Steps:**

- [ ] Add failing public-doc markers to the integrity test before changing docs.
- [ ] Update the family count from 15 to 16 everywhere it is an inventory count.
- [ ] State consistently and minimally: ProMax is v8-only; exact-name only; ProMax wins if both names occur; generic maximality requests remain Max; suite never auto-upgrades; ProMax uses its own audit and does not chain review.
- [ ] Do not copy runtime protocol or v8 knowledge into adapters. Link to the canonical skill.
- [ ] Keep existing Max descriptions and commands intact except for the external priority clarification where both names occur.
- [ ] Run integrity and repository integration tests, regenerate the Claude mirror if canonical content changed, and commit.

## Task 12: Full verification, install/package smoke, and independent reviews

**Files:**

- Update only files required by a reproduced verification failure.

**Steps:**

- [ ] Run source gates:

  ```powershell
  python scripts/check_crossframe_promax_v8_full_source.py --repo . --source-docx "E:\世界模型\跨尺度多圈层结构推演框架_v8.0.docx"
  python scripts/check_crossframe_promax_v8_knowledge.py --repo .
  ```

- [ ] Run runtime and fixture gates:

  ```powershell
  python -B -m unittest tests.test_promax_schemas tests.test_promax_state_machine tests.test_promax_source_integrity tests.test_promax_pollution tests.test_promax_concept_closure tests.test_promax_claim_path tests.test_promax_retrieval tests.test_promax_position tests.test_promax_artifacts tests.test_promax_adversarial tests.test_promax_replay tests.test_promax_repair -v
  ```

- [ ] Run repository gates:

  ```powershell
  python -m pip install "jsonschema==4.26.0" "PyYAML==6.0.2"
  python scripts/sync_skill_mirrors.py --check
  python scripts/check_crossframe_skill_integrity.py --repo . --mirror .claude/skills
  python -B -m unittest discover -s tests -p "test_*.py" -v
  python -m compileall -q scripts skills/crossframe-promax/scripts
  bash -n scripts/install-codex.sh
  git diff --check
  ```

- [ ] Run package smoke into a new temporary directory:

  ```powershell
  $packageRoot = New-Item -ItemType Directory -Path ([System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "crossframe-promax-package-" + [guid]::NewGuid().ToString("N")))
  python scripts/package_crossframe_skill.py --repo . --version promax-ci --output-dir $packageRoot.FullName
  python -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); n=set(z.namelist()); required={'skills/crossframe-promax/SKILL.md','.claude/skills/crossframe-promax/SKILL.md','.claude/commands/crossframe-promax.md','skills/crossframe-promax/references/v8-full-source/00-index.md','skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py'}; assert required <= n; assert sum(x.startswith('skills/crossframe') and x.endswith('/SKILL.md') for x in n)==16" (Get-ChildItem $packageRoot -Filter *.zip | Select-Object -First 1).FullName
  ```

  Then inspect ProMax archive paths with the same pollution allowlist as the canonical validator and remove the temporary directory.
- [ ] Run the PowerShell Codex installer end-to-end against a new temporary destination with `tests/fixtures/fake_skill_installer.py`, passing the local repository and the real `--dest` seam. Assert 16 installed `SKILL.md` files and byte equality with canonical sources. CI performs the equivalent Bash smoke. Never mutate the user's installed skill directories.
- [ ] Re-run `tests/fixtures/promax-preservation.json` against all protected Max surfaces and require no mismatch. Verify `git status --short` contains no temporary/docx/cache artifacts.
- [ ] Dispatch a fresh specification reviewer against the approved design and actual diff. Fix and re-review every gap.
- [ ] Dispatch a fresh code/protocol quality reviewer only after spec compliance is approved. Fix and re-review every issue.
- [ ] Dispatch one final whole-implementation reviewer and run all gates again after the last fix.
- [ ] Commit any review fixes, then create a final verification commit only if required. Do not push unless the user separately authorizes a push.

## Final acceptance checklist

- [ ] The committed source tree proves `3863 / 155721 / 117 / 16` and exact source SHA.
- [ ] Every committed table cell is bound to its source paragraph anchors and verified by content.
- [ ] The skill package contains no pre-v8 knowledge or lineage asset.
- [ ] Registry, contracts, routes, source anchors, and backlinks form a closed graph.
- [ ] Runtime validators reject every documented bypass and accept the valid complete fixture.
- [ ] RED baseline failure and GREEN forward-test evidence both exist.
- [ ] Named ProMax is the only trigger; ProMax wins over Max; generic maximum requests do not upgrade.
- [ ] Max is unchanged.
- [ ] Canonical skill, mirror, installers, docs, site, package, and CI agree on 16 skills.
- [ ] Full tests, compile, shell syntax, integrity, mirror, source, knowledge, and runtime gates pass from a clean worktree.
