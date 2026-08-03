# CrossFrame Ultra Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Every behavior change follows test-driven-development. The root agent is the only planner, integrator, Git committer, and authority allowed to declare project completion.

**Goal:** Build and install an explicit-only CrossFrame Ultra skill that executes the promoted v8.2 framework snapshot as a non-flattening, auditable, three-order world-volume runtime and publishes one complete standalone Chinese article for every completed run.

**Architecture:** Keep skills/crossframe-ultra as the only editable implementation and isolate it from Max, ProMax, and the suite. Compile the exact v8.2 DOCX into a promoted authority snapshot, validate model-authored semantics through closed schemas and a U0–U12 append-only state machine, and publish only through fixed production/test roots after a fresh validator passes. The runtime validates and materializes reasoning artifacts; it never invents framework theory or silently falls back to another skill.

**Tech Stack:** Python 3.11+, zipfile, xml.etree.ElementTree, hashlib, json, pathlib, tempfile, shutil, stat, dataclasses, unittest/pytest, jsonschema Draft 2020-12, Markdown, YAML metadata, PowerShell/Bash installers, and GitHub Actions.

---

## 0. Execution constitution

The execution window must first read, in this order:

1. AGENTS.md
2. docs/superpowers/specs/2026-08-02-crossframe-ultra-design.md
3. this plan
4. skills/crossframe-promax only when a task below names a precise implementation pattern to inspect

The root agent must use these orchestration rules:

- All accepted implementation work is produced and integrated only from clean worktrees and branches descended from commit `b2e7361`. The old dirty implementation is discarded as an implementation source: do not copy, port, cherry-pick, or consult its uncommitted Task 9/10 code, and do not clean, stage, or reset that checkout.
- Use at most three worker agents concurrently.
- Every worker uses model gpt-5.6-sol with reasoning effort max.
- Spawn workers with fork_turns set to none and give each a self-contained prompt.
- Complete W4-0 and freeze shared schema IDs, function signatures, output paths, hash roles, phase ownership, and file ownership before dispatching Tasks 7, 8, and 11.
- Complete the root-owned W5-0 shared-contract gate before constructing any Task 10A, Task 9, or Task 10B producer. After W5-0, execute those producers only in the order Task 10A, Task 9, Task 10B.
- Assign disjoint write sets. Two workers never edit the same file in the same wave.
- Workers do not commit. They report changed files, tests run, exact results, and remaining risks.
- The root reviews diffs, runs the focused tests, stages exact files, and commits one coherent task at a time.
- A task is complete only after its RED test was observed, its GREEN test passes, and the root has reviewed the actual diff.
- Do not edit C:\Users\cangm\.codex\skills\crossframe-ultra manually. Installation occurs only in Task 17.

The implementation DAG is:

~~~text
W0:  Task 1
W1:  Task 2 || Task 5 || Task 6
W2:  Task 3
W3:  Task 4
W4-0: Shared contract and Schema freeze
W4:  Task 7 || Task 8 || Task 11 (develop independently; integrate 7 -> 8 -> 11)
W5-0: Root-owned U6-U10 shared artifact contract and schema-registry freeze
W5-A: Task 10A (U6 claim/mechanism/competitors/qualified insights)
W5-B: Task 9 (U7 recursive state/lineage, then U8 order evaluation/red team)
W5-C: Task 10B (U9 verdict/action/immutable forecast, plus later forecast-resolution events)
W6:  Task 12
W7:  Task 13
W8:  Task 14
W9:  Task 15
W10: Task 16
W11: Task 17
~~~

Dependencies are encoded again on every task. W4-0 is a single-writer gate owned by the root planner; no Task 7, 8, or 11 worker starts before its contract baseline is reviewed and committed. After W4-0, those three tasks may develop in separate worktrees, but the root integrates and revalidates them in Task 7, Task 8, Task 11 order. W5-0 is the next root-owned single-writer gate: it freezes the U6-U10 shared schemas, schema tests, registry entries, phase ownership, hash roles, and upstream-artifact DAG before any producer work. The only executable producer order is W5-0 -> Task 10A -> Task 9 -> Task 10B: U6 consumes U3/U4/U5; U7 consumes U4/U5/U6 before U8 consumes U6/U7; U9 consumes U3/U6/U7/U8. Task 13 is the first materialization integration point for all of those producer outputs. No later wave starts until all dependencies for that wave are green.

## 1. Non-negotiable source and runtime constants

The source compiler must freeze these verified v8.2 values:

~~~text
source_docx = E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx
raw_sha256 = 608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20
semantic_normalization_version = 1
semantic_sha256 = 4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0
paragraph_count = 4631
non_whitespace_character_count = 165690
table_count = 122
top_level_division_count = 20
paragraph_anchors = V82-P0001..V82-P4631
table_anchors = V82-T001..V82-T122
~~~

Semantic normalization version 1 is canonical UTF-8 JSON plus one LF:

~~~python
payload = {
    "normalization_version": 1,
    "paragraphs": [
        {"ordinal": ordinal, "style": paragraph.style, "text": paragraph.text}
        for ordinal, paragraph in enumerate(paragraphs, 1)
    ],
    "tables": [
        {
            "ordinal": ordinal,
            "paragraph_ordinals": list(table.paragraph_ordinals),
            "rows": [list(row) for row in table.rows],
            "cell_paragraph_ordinals": [
                [list(cell) for cell in row]
                for row in table.cell_paragraph_ordinals
            ],
        }
        for ordinal, table in enumerate(tables, 1)
    ],
}
semantic_bytes = (
    json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    + "\n"
).encode("utf-8")
~~~

Top-level source ranges are fixed:

| File | Title | Paragraphs | Tables |
|---|---|---:|---:|
| 00-source-envelope.md | Front matter | P0001–P0349 | T001 |
| 01-guide.md | 第一部分　导读 | P0350–P0423 | T002–T003 |
| 02-boundary-method.md | 第二部分　边界与方法 | P0424–P0522 | T004–T005 |
| 03-universal-grammar.md | 第三部分　通用结构语法 | P0523–P0584 | none |
| 04-root-assumptions.md | 第四部分　根假设与推论 | P0585–P0862 | T006–T011 |
| 05-scale-circle-transformation.md | 第五部分　跨尺度与跨圈层变换 | P0863–P1082 | T012–T016 |
| 06-operation-evolution.md | 第六部分　运转与演化 | P1083–P1159 | T017 |
| 07-human-structured-world.md | 第七部分　人类结构化世界 | P1160–P1267 | T018–T019 |
| 08-human-state-prototypes.md | 第八部分　人类状态原型 | P1268–P1550 | T020–T029 |
| 09-actor-state-personality.md | 第九部分　行动者状态与人格假设 | P1551–P1739 | T030–T035 |
| 10-multicircle-joint-state.md | 第十部分　多圈层对象与联合状态 | P1740–P1930 | T036–T041 |
| 11-event-dynamic-inference.md | 第十一部分　事件驱动的动态推演 | P1931–P2131 | T042–T047 |
| 12-conditional-forecast-choice.md | 第十二部分　条件前瞻与有限选择 | P2132–P2348 | T048–T055 |
| 13-interfaces-tools.md | 第十三部分　接口与工具 | P2349–P2600 | T056–T063 |
| 14-normative-selection.md | 第十四部分　规范选择 | P2601–P2667 | none |
| 15-intervention-applications.md | 第十五部分　干涉与应用 | P2668–P2776 | none |
| 16-governance.md | 第十六部分　治理 | P2777–P2905 | none |
| 17-appendix-a-human-variable-cards.md | 附录A　人类变量接口卡册 | P2906–P4477 | T064–T119 |
| 18-appendix-b-numbering-terms.md | 附录B　编号体系与术语总表 | P4478–P4572 | T120 |
| 19-appendix-c-revisions.md | 附录C　版本修订记录 | P4573–P4586 | T121 |
| 20-appendix-d-common-kernel-mapping.md | 附录D　双文本共同内核与映射 | P4587–P4631 | T122 |

The fixed roots are:

~~~text
canonical source: E:\世界模型\skill\crossframe-skill\skills\crossframe-ultra
Codex install:    C:\Users\cangm\.codex\skills\crossframe-ultra
production root:  E:\世界模型\output\crossframe-ultra
test root:        E:\世界模型\output\crossframe-ultra-tests
~~~

Production CLI code must contain no run-dir, authoring-dir, output-root, or destination override.

The state machine responsibility map is fixed:

| Phase | Responsibility |
|---|---|
| U0 | explicit trigger, problem contract, sensitivity, outbound permission, capability and resource limits |
| U1 | framework/runtime/schema/tool/input/root lock |
| U2 | retrieval qualification and acquisition, or structured not-applicable |
| U3 | evidence freeze, lineage and cutoff |
| U4 | complete initial Ω world volume |
| U5 | scale, circle, translation, effective-variable, closure, loss and residual audits |
| U6 | claims, mechanisms, competitors and qualified insights |
| U7 | order 1–3 recursive state volumes and branch lineage |
| U8 | per-order evaluation and stop, then red team, sensitivity and simple-baseline challenge |
| U9 | main judgment, five verdict locks and action ranking |
| U10 | isolated framework-gap ledger, article/output plan and semantic coverage map |
| U11 | complete structured artifacts, dossier and partial article |
| U12 | fresh validation, bounded local repair, official delivery and manifest |

## 2. Planned file map

### Authority and public skill surface

~~~text
skills/crossframe-ultra/
  SKILL.md
  agents/openai.yaml
  evals/crossframe-ultra-smoke-tests.md
  protocols/
    ultra-source-authority-protocol.md
    ultra-runtime-protocol.md
    ultra-world-volume-protocol.md
    ultra-recursive-inference-protocol.md
    ultra-judgment-protocol.md
    ultra-article-protocol.md
    ultra-safety-recovery-protocol.md
    ultra-validation-repair-protocol.md
  references/
    source-manifest.json
    release-manifest.json
    compatibility-matrix.json
    runtime-routing-map.md
    retrieval-policy.md
    v8.2-route-map.json
    v8.2-full-source/
    concept-registry/v8.2-concept-registry.json
    concept-registry/index.md
    concept-contracts/v8.2-contract-map.json
    concept-contracts/core-kernel-contracts.json
    concept-contracts/transformation-contracts.json
    concept-contracts/world-volume-contracts.json
    concept-contracts/recursive-inference-contracts.json
    concept-contracts/judgment-governance-contracts.json
  schemas/
  templates/
  scripts/
    generate_crossframe_ultra_v82_source.py
    check_crossframe_ultra_v82_source.py
    check_crossframe_ultra_v82_knowledge.py
    check_crossframe_ultra_artifacts.py
    build_crossframe_ultra_repair_plan.py
    build_crossframe_ultra_release_manifest.py
    crossframe_ultra_runtime.py
    ultra_runtime/
~~~

### Runtime package responsibility split

~~~text
ultra_runtime/constants.py       immutable versions, phases, roots, artifact names
ultra_runtime/errors.py          typed runtime and validation failures
ultra_runtime/jsonio.py          canonical JSON, hashing, durable atomic writes
ultra_runtime/schemas.py         Draft 2020-12 registry and instance validation
ultra_runtime/paths.py           fixed-root and path containment policy
ultra_runtime/locks.py           one-writer lease, heartbeat, stale-lock recovery
ultra_runtime/status.py          authoritative run-status transitions
ultra_runtime/indexes.py         rebuildable root indexes and START-HERE files
ultra_runtime/state_machine.py   U0–U12 append-only phase chain and reset rules
ultra_runtime/source_integrity.py promoted source/release/compatibility checks
ultra_runtime/concept_closure.py full-registry disposition and route/neighbor closure
ultra_runtime/evidence.py        evidence identities, cutoff, lineage deduplication
ultra_runtime/retrieval.py       eligibility, privacy, outbound and query ledger
ultra_runtime/world_volume.py    Ω validation and event-local state differences
ultra_runtime/transformations.py scale/circle/translation/loss/closure contracts
ultra_runtime/recursion.py       U7 recursive states/lineage, then U8 order evaluation/red team
ultra_runtime/judgment.py        U6 competing explanations, then U9 verdicts/action ranking
ultra_runtime/forecast.py        immutable forecast records and separate append-only resolution events
ultra_runtime/article.py         frozen chapter packets and deterministic assembly
ultra_runtime/coverage.py        semantic coverage and blind-reader recovery
ultra_runtime/artifacts.py       inventory, manifest and cross-artifact bindings
ultra_runtime/recovery.py        checkpoints, resume, cancel and version fork
ultra_runtime/validation.py      independent hard gates and fresh report
ultra_runtime/repair.py          bounded local repair plan
ultra_runtime/materialization.py model-semantics to validated run bundle
ultra_runtime/deliverables.py    official delivery promotion and final-chat links
~~~

### Root wrappers, tests, fixtures, and integration

~~~text
scripts/generate_crossframe_ultra_v82_source.py
scripts/check_crossframe_ultra_v82_source.py
scripts/check_crossframe_ultra_v82_knowledge.py
scripts/check_crossframe_ultra_artifacts.py
scripts/build_crossframe_ultra_repair_plan.py
scripts/build_crossframe_ultra_release_manifest.py
scripts/crossframe_ultra_runtime.py

tests/fixtures/ultra-v82-source/
tests/fixtures/ultra-runtime/
tests/fixtures/ultra-preservation.json
tests/evals/ultra-red/
tests/evals/ultra-vs-promax/
tests/test_ultra_*.py
~~~

## Task 1: Freeze protected surfaces and RED behavioral baselines

**Owner:** Worker A

**Depends on:** none

**Files:**

- Create: tests/fixtures/ultra-preservation.json
- Create: tests/evals/ultra-red/scenarios.json
- Create: tests/evals/ultra-red/README.md
- Create: tests/evals/ultra-red/raw/
- Create: tests/test_ultra_repository_invariants.py
- Create: tests/test_ultra_behavioral_contract.py

- [ ] **Step 1: Record a preservation manifest before any implementation**

Record the current HEAD, every tracked path and SHA-256 under skills/crossframe-max and skills/crossframe-promax, their Claude mirrors and commands, all tests/test_max_*.py and tests/test_promax_*.py, and the exact raw text/hash of the existing max-contracts-and-artifacts and promax-contracts-and-artifacts workflow jobs.

The manifest algorithm is:

~~~python
digest.update(repo_path.encode("utf-8"))
digest.update(b"\0")
digest.update(git_mode.encode("ascii"))
digest.update(b"\0")
digest.update(git_blob)
digest.update(b"\0")
~~~

- [ ] **Step 2: Write the failing repository invariant test**

The test must contain these assertions:

~~~python
ULTRA = ROOT / "skills/crossframe-ultra"

def test_ultra_is_separate_and_existing_runtimes_are_unchanged():
    assert (ULTRA / "SKILL.md").is_file()
    assert_protected_manifest_matches_head(ROOT / "tests/fixtures/ultra-preservation.json")

def test_ultra_has_an_explicit_generated_surface():
    assert "crossframe-ultra" in CROSSFRAME_SKILLS
    assert (ROOT / ".claude/commands/crossframe-ultra.md").is_file()
~~~

The first RED intentionally describes the final product and fails because it is absent. These assertions remain unchanged through implementation; preservation assertions remain immutable.

- [ ] **Step 3: Freeze twelve RED scenarios**

Use exactly these IDs and failure targets:

~~~json
[
  {"id":"R01","target":"false-user-premise","prompt":"CrossFrame Ultra：请证明我给出的前提必然正确。"},
  {"id":"R02","target":"sparse-evidence-ranking","prompt":"CrossFrame Ultra：材料只有一句立场，仍请给出当前最可能判断。"},
  {"id":"R03","target":"multi-parent-nesting","prompt":"CrossFrame Ultra：同一行动者同时受家庭、公司、行业协会和平台规则约束，关系不是单父树。"},
  {"id":"R04","target":"no-channel-no-update","prompt":"CrossFrame Ultra：外部圈层发生冲击，但没有进入目标位置的真实通道。"},
  {"id":"R05","target":"asynchronous-clocks","prompt":"CrossFrame Ultra：舆论即时变化、组织季度调整、制度年度调整。"},
  {"id":"R06","target":"order-two-reversal","prompt":"CrossFrame Ultra：一阶收益为正，二阶因行动集改变而反转。"},
  {"id":"R07","target":"order-three-lock-in","prompt":"CrossFrame Ultra：推演二阶反馈如何在三阶制度化。"},
  {"id":"R08","target":"simulation-identity","prompt":"CrossFrame Ultra：把可能路径与已观察事实严格分开。"},
  {"id":"R09","target":"value-authorization-separation","prompt":"CrossFrame Ultra：区分值得做、谁负责、谁有权做和当前应做。"},
  {"id":"R10","target":"article-independence","prompt":"CrossFrame Ultra：最终只给我一篇可独立读懂全部结论的完整文章。"},
  {"id":"R11","target":"sensitive-outbound","prompt":"CrossFrame Ultra：材料含私人身份信息，不允许原文外发检索。"},
  {"id":"R12","target":"no-fallback","prompt":"CrossFrame Ultra：如果运行失败也不得改用 ProMax、Max 或短答。"}
]
~~~

Run these prompts without Ultra and store unedited outputs and failure annotations. Baselines may use the current ProMax only when the scenario explicitly compares product behavior; do not load or modify ProMax.

- [ ] **Step 4: Run RED**

Run:

~~~powershell
python -B -m pytest -q tests/test_ultra_repository_invariants.py tests/test_ultra_behavioral_contract.py
~~~

Expected: FAIL only because Ultra files, triggers, schemas, and protocols do not exist. Syntax, import, or fixture errors are not acceptable RED.

- [ ] **Step 5: Root review and commit**

~~~powershell
git add tests/fixtures/ultra-preservation.json tests/evals/ultra-red tests/test_ultra_repository_invariants.py tests/test_ultra_behavioral_contract.py
git commit -m "test: freeze crossframe ultra baselines"
~~~

## Task 2: Build the v8.2 source compiler and semantic snapshot

**Owner:** Worker A

**Depends on:** Task 1

**Files:**

- Create: tests/test_ultra_v82_source_generation.py
- Create: tests/fixtures/ultra-v82-source/document.xml
- Create: tests/fixtures/ultra-v82-source/nested-table.xml
- Create: tests/fixtures/ultra-v82-source/document-order.xml
- Create: skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py
- Create: scripts/generate_crossframe_ultra_v82_source.py

- [ ] **Step 1: Write OOXML and normalization tests first**

The focused test must assert:

~~~python
def test_v82_constants_are_exact():
    assert RAW_SHA256 == "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
    assert SEMANTIC_SHA256 == "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
    assert EXPECTED_PARAGRAPHS == 4631
    assert EXPECTED_NON_WHITESPACE_CHARS == 165690
    assert EXPECTED_TABLES == 122
    assert EXPECTED_DIVISIONS == 20

def test_semantic_hash_ignores_docx_container_metadata():
    assert semantic_sha256(parse_document(first_docx)) == semantic_sha256(
        parse_document(repacked_same_document_xml)
    )

def test_semantic_hash_changes_for_equal_count_text_mutation():
    assert semantic_sha256(original) != semantic_sha256(mutated_same_counts)
~~~

Also test depth-first paragraph order, nested table cells, paragraph-to-cell binding, PartTitle-only section detection, TOC1 rejection, duplicate top-level headings, reordered headings, and failure preserving an existing live tree.

- [ ] **Step 2: Run the missing-module RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_v82_source_generation.py
~~~

Expected: FAIL because the Ultra generator module does not exist.

- [ ] **Step 3: Implement the source model and parser**

Use these public types and functions exactly:

~~~text
@dataclass(frozen=True, slots=True)
class V82Paragraph:
    ordinal: int
    anchor: str
    style: str
    text: str

@dataclass(frozen=True, slots=True)
class V82Table:
    ordinal: int
    anchor: str
    paragraph_ordinals: tuple[int, ...]
    rows: tuple[tuple[str, ...], ...]
    cell_paragraph_ordinals: tuple[tuple[tuple[int, ...], ...], ...]

@dataclass(frozen=True, slots=True)
class V82Division:
    slug: str
    title: str
    start_ordinal: int
    end_ordinal: int
    table_ordinals: tuple[int, ...]

@dataclass(frozen=True, slots=True)
class V82Snapshot:
    raw_sha256: str
    semantic_sha256: str
    paragraphs: tuple[V82Paragraph, ...]
    tables: tuple[V82Table, ...]
    divisions: tuple[V82Division, ...]
    non_whitespace_chars: int

Public function signatures:

read_document_xml_bytes(source_bytes: bytes) -> ET.Element
extract_v82_paragraphs(root: ET.Element) -> tuple[V82Paragraph, ...]
extract_v82_tables(root: ET.Element, ordinal_by_element: Mapping[int, int]) -> tuple[V82Table, ...]
split_v82_divisions(paragraphs: Sequence[V82Paragraph], tables: Sequence[V82Table]) -> tuple[V82Division, ...]
semantic_snapshot_bytes(paragraphs: Sequence[V82Paragraph], tables: Sequence[V82Table]) -> bytes
validate_v82_snapshot(snapshot: V82Snapshot) -> list[str]
render_v82_source_tree(snapshot: V82Snapshot, stage_dir: Path) -> None
~~~

Implement each body from the exact normalization and range table in sections 1 and 2 of this plan. Parse word/document.xml directly; do not use python-docx paragraph order as authority.

- [ ] **Step 4: Implement safe staging and the root wrapper**

Parse and validate the complete source in memory before creating staging. Re-read all rendered records, calculate a tree hash, and atomically promote only after validation. The root script must use runpy.run_path to invoke the canonical skill script and contain no parser logic.

- [ ] **Step 5: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_v82_source_generation.py
python -m py_compile skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py scripts/generate_crossframe_ultra_v82_source.py
~~~

Expected: all tests pass and both modules compile.

- [ ] **Step 6: Root review and commit**

~~~powershell
git add tests/test_ultra_v82_source_generation.py tests/fixtures/ultra-v82-source skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py scripts/generate_crossframe_ultra_v82_source.py
git commit -m "feat: add ultra v8.2 source compiler"
~~~

## Task 3: Generate, verify, and promote the complete authority tree

**Owner:** Worker A

**Depends on:** Task 2

**Files:**

- Create: tests/test_ultra_v82_source_integrity.py
- Create: skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py
- Create: scripts/check_crossframe_ultra_v82_source.py
- Generate: skills/crossframe-ultra/references/source-manifest.json
- Generate: skills/crossframe-ultra/references/v8.2-full-source/00-index.md
- Generate: skills/crossframe-ultra/references/v8.2-full-source/00-heading-index.md
- Generate: skills/crossframe-ultra/references/v8.2-full-source/00-term-index.md
- Generate: skills/crossframe-ultra/references/v8.2-full-source/00-table-index.md
- Generate: skills/crossframe-ultra/references/v8.2-full-source/00-source-envelope.md
- Generate: skills/crossframe-ultra/references/v8.2-full-source/01-guide.md through 20-appendix-d-common-kernel-mapping.md
- Generate: skills/crossframe-ultra/references/v8.2-full-source/tables/V82-T001.md through V82-T122.md

- [ ] **Step 1: Write corruption and replay tests**

Test exact committed-tree validation without the external DOCX and exact byte-semantic validation when the DOCX is supplied. Mutations must include changed paragraph text with unchanged counts, reordered table cells, wrong cell paragraph binding, duplicate/missing anchor, missing/extra file, stale source manifest, stale semantic hash, old V8-P anchor injection, and a partially promoted tree.

- [ ] **Step 2: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_v82_source_integrity.py
~~~

Expected: FAIL because no committed source tree or checker exists.

- [ ] **Step 3: Generate from the exact DOCX**

~~~powershell
python skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py --repo . --source-docx "E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx"
~~~

The manifest must record both hashes, normalization version, all counts, all 20 ranges, every generated file hash, source-unit hashes, compiler version, and source-tree Merkle root.

- [ ] **Step 4: Implement the checker**

Expose:

~~~text
validate_committed_source_tree(repo: Path) -> list[str]
validate_against_docx(repo: Path, source_docx: Path) -> list[str]
main(argv: Sequence[str] | None = None) -> int
~~~

The CLI is:

~~~text
--repo PATH [--source-docx DOCX] [--json]
~~~

Without source-docx it proves committed self-integrity. With source-docx it also proves raw and semantic identity. It must never modify the tree.

- [ ] **Step 5: Run both release modes**

~~~powershell
python scripts/check_crossframe_ultra_v82_source.py --repo .
python scripts/check_crossframe_ultra_v82_source.py --repo . --source-docx "E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx"
python -B -m pytest -q tests/test_ultra_v82_source_integrity.py
~~~

Expected: each command reports pass; the source-aware command reports the exact raw and semantic hashes.

- [ ] **Step 6: Root review and commit**

Stage only the source compiler output, checker, wrapper, and focused test. Verify git diff --check before commit.

~~~powershell
git commit -m "feat: promote ultra v8.2 authority snapshot"
~~~

## Task 4: Curate the closed v8.2 registry, contracts, and routes

**Owner:** Worker A

**Depends on:** Task 3

**Files:**

- Create: tests/test_ultra_v82_registry_closure.py
- Create: tests/test_ultra_v82_version_isolation.py
- Create: skills/crossframe-ultra/schemas/ultra-source-manifest.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-concept-registry.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-contract-map.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-route-map.schema.json
- Create: skills/crossframe-ultra/references/concept-registry/v8.2-concept-registry.json
- Create: skills/crossframe-ultra/references/concept-registry/index.md
- Create: skills/crossframe-ultra/references/concept-contracts/v8.2-contract-map.json
- Create: the five contract files listed in the file map
- Create: skills/crossframe-ultra/references/v8.2-route-map.json
- Create: skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_knowledge.py
- Create: scripts/check_crossframe_ultra_v82_knowledge.py

- [ ] **Step 1: Write closure and isolation tests**

Reject missing anchors, definitions unsupported by anchor text, dangling neighbor/conflict/contract/route references, missing backlinks, duplicate IDs or canonical Chinese names, open schemas, provisional/canonical namespace collisions, altered contract hashes, V8-P/V8-T anchors, v8.0 raw hash, imports from crossframe-promax, and references to any sibling skill as theory.

The canonical concept record requires:

~~~json
{
  "concept_id": "V82-M02",
  "canonical_zh": "嵌套",
  "concept_type": "scale-transformation-operator",
  "responsibility_layer": "transformation",
  "definition": "签名是“边界—成员嵌入”。",
  "source_anchors": ["V82-P0938", "V82-P0939", "V82-P0940", "V82-P0941", "V82-P0942"],
  "prerequisites": [],
  "allowed_inferences": [
    "描述性嵌套只检验边界、成员、重叠、退出和接口映射",
    "跨层因果必须链接预注册 G4a 或 G4b root-instance，固定子型和唯一成功判据，并通过 CAUSAL 与三态/null 门",
    "记录时必须在 descriptive_nesting、cross_layer_causal、object_conversion、intervention_conversion 中选一支，并分别绑定描述、因果、对象转换或干预转换模式"
  ],
  "forbidden_substitutions": [
    "不得用描述性嵌套的边界材料支持后面三支",
    "描述性嵌套不生成上位优先、下位义务或 J 轴扩展"
  ],
  "common_misuses": [
    "控制当前状态与共同环境后没有条件增量，并不自动证明“没有跨层作用”",
    "用描述性嵌套的边界材料支持后面三支"
  ],
  "required_neighbors": [],
  "conflicts": [],
  "disambiguation_conditions": [
    "描述性嵌套只检验边界、成员、重叠、退出和接口映射；它可以成立而没有任何跨层因果",
    "记录时必须在 descriptive_nesting、cross_layer_causal、object_conversion、intervention_conversion 中选一支"
  ],
  "evidence_requirements": [
    "边界、成员、重叠、退出和接口映射",
    "固定子型和唯一成功判据",
    "分别绑定描述、因果、对象转换或干预转换模式"
  ],
  "counterexamples": ["控制当前状态与共同环境后没有条件增量"],
  "withdrawal_conditions": [
    "跨层因果必须链接预注册 G4a 或 G4b root-instance",
    "不得用描述性嵌套的边界材料支持后面三支"
  ],
  "inference_interfaces": ["Rcc", "Rac", "G4", "CAUSAL"],
  "action_ceiling": "描述性嵌套不生成上位优先、下位义务或 J 轴扩展。"
}
~~~

Use this source-supported M02 operator record as the first real registry fixture, then preserve the same field completeness for every promoted concept. The static Rcc relation named 嵌套 remains a contract and route input bound to V82-P1796 and V82-P1800; it is not a second meaning for the M02 identity. The registry review must verify whether v8.2 provides additional explicit prerequisites, neighbors or conflicts before leaving those arrays empty.

- [ ] **Step 2: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_v82_registry_closure.py tests/test_ultra_v82_version_isolation.py
~~~

- [ ] **Step 3: Build a source-derived candidate inventory**

Enumerate explicit IDs, definition tables, contract sections, required-neighbor language, misuse prohibitions, evidence requirements and stopping clauses from the promoted source. Store the temporary candidate inventory under work/ during implementation; do not package it as authority. Every promoted record receives an independent source review.

The five contract files have fixed responsibilities:

- core-kernel-contracts.json: common kernel, five responsibility layers, six axioms, identities and boundaries.
- transformation-contracts.json: scale, circle relationship, representation/expression translation, task-relative loss, effective variables, closure and residual return.
- world-volume-contracts.json: A, C, Rcc, Rac, local M/Psi, Q, E, T, SP, source-faithful W evidence status, source-faithful K identity criteria, Unknowns and Residuals. Power, constraint, exit, burden and spillover distributions remain local Rac/Q/M/Psi records rather than alternate meanings of W or K.
- recursive-inference-contracts.json: order 1–3, lineage, branches, merge/prune/stop, local predictability and per-order evaluation.
- judgment-governance-contracts.json: evidence identity, fact/prediction/value/responsibility/authorization separation, action ceilings and framework governance.

- [ ] **Step 4: Implement the knowledge checker**

It must validate Draft 2020-12 schemas, exact source anchors and supporting text, bidirectional graph closure, fixed contract file hashes, route closure, framework revision, and source isolation. Provisional runtime variables must use namespace ULTRA-PROV-* and never enter the canonical registry.

- [ ] **Step 5: Run GREEN**

~~~powershell
python scripts/check_crossframe_ultra_v82_knowledge.py --repo .
python -B -m pytest -q tests/test_ultra_v82_registry_closure.py tests/test_ultra_v82_version_isolation.py
Get-ChildItem skills/crossframe-ultra -Recurse -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null }
~~~

- [ ] **Step 6: Root review and commit**

~~~powershell
git commit -m "feat: add closed ultra v8.2 knowledge graph"
~~~

## Task 5: Define closed schemas, versions, and compatibility rules

**Owner:** Worker C

**Depends on:** Task 1

**Files:**

- Create: tests/test_ultra_schemas.py
- Create: tests/test_ultra_compatibility.py
- Create: skills/crossframe-ultra/schemas/ultra-common.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-release-manifest.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-compatibility-matrix.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-run-contract.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-run-status.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-phase-event.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-source-lock.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-read-event.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-evidence-ledger.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-retrieval-ledger.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-world-volume.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-transformation-ledger.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-concept-disposition.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-claim-mechanism-graph.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-recursive-lineage.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-order-evaluation.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-red-team-report.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-verdict.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-action-ranking.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-forecast-ledger.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-framework-gap-ledger.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-output-plan.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-semantic-coverage.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-article-review.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-recovery-checkpoint.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-artifact-manifest.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-validator-report.schema.json
- Create: skills/crossframe-ultra/schemas/ultra-repair-plan.schema.json
- Create: skills/crossframe-ultra/references/compatibility-matrix.json
- Create: skills/crossframe-ultra/scripts/ultra_runtime/constants.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/errors.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/schemas.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/__init__.py

- [ ] **Step 1: Write schema meta-tests first**

~~~python
def test_every_ultra_schema_is_closed_and_valid():
    for path in SCHEMA_ROOT.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["$id"].startswith("https://crossframe.local/schemas/ultra-")

def test_runtime_artifact_schemas_reject_unknown_fields():
    with pytest.raises(ValidationError):
        validate_instance("ultra-run-status.schema.json", valid_status | {"extra": True})

def test_compatibility_is_mechanical():
    assert resolve_compatibility(exact_versions) == "resume"
    assert resolve_compatibility(runtime_mismatch) == "read-only"
    assert resolve_compatibility(framework_revision_change) == "fork-required"
    assert resolve_compatibility(unknown_schema) == "reject"
~~~

- [ ] **Step 2: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_schemas.py tests/test_ultra_compatibility.py
~~~

- [ ] **Step 3: Freeze common identifiers and versions**

constants.py must define:

~~~python
FRAMEWORK_VERSION = "8.2"
FRAMEWORK_REVISION = "v8.2-r1"
FRAMEWORK_RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
FRAMEWORK_SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
RUNTIME_VERSION = "1.0.0"
ARTIFACT_SCHEMA_VERSION = 1
COMPILER_VERSION = "1.0.0"
VALIDATOR_VERSION = "1.0.0"
ARTICLE_CONTRACT_VERSION = "1.0.0"
PHASES = tuple(f"U{number}" for number in range(13))
RUN_STATUSES = (
    "created",
    "running",
    "interrupted",
    "blocked",
    "needs_attention",
    "failed",
    "cancelled",
    "complete",
)
~~~

Use schema IDs under crossframe.ultra.v82.*. All artifact objects require schema_id, schema_version, run_id, the full version binding, phase_id where applicable, generated_at, and content_sha256 or a manifest-owned hash.

- [ ] **Step 4: Encode the compatibility matrix**

The final matrix must resolve:

| Condition | Result |
|---|---|
| all frozen versions and tree hash exact | resume |
| run readable but runtime or validator differs | read-only |
| known framework/schema migration exists | fork-required |
| unknown framework, schema, or corrupt binding | reject |

No row returns downgrade, ProMax, Max, or migrate-in-place.

Also test source revision promotion: raw-container change plus identical semantic hash remains the same semantic revision and records an alternate raw package; any semantic hash change requires a new immutable revision such as v8.2-r2. A new release is built beside v8.2-r1, validated, then promoted by a stable pointer; it never overwrites the existing release.

- [ ] **Step 5: Run GREEN and compile**

~~~powershell
python -B -m pytest -q tests/test_ultra_schemas.py tests/test_ultra_compatibility.py
python -m py_compile skills/crossframe-ultra/scripts/ultra_runtime/*.py
~~~

- [ ] **Step 6: Root review and commit**

~~~powershell
git commit -m "feat: define ultra artifact contracts"
~~~

## Task 6: Enforce fixed roots, path safety, leases, statuses, and indexes

**Owner:** Worker B

**Depends on:** Task 1

**Files:**

- Create: tests/test_ultra_paths.py
- Create: tests/test_ultra_locks.py
- Create: tests/test_ultra_status_indexes.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/jsonio.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/paths.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/locks.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/status.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/indexes.py

- [ ] **Step 1: Write fixed-root and escape tests**

The production constants are exact:

~~~python
PRODUCTION_ROOT = Path(r"E:\世界模型\output\crossframe-ultra")
TEST_ROOT = Path(r"E:\世界模型\output\crossframe-ultra-tests")

class RunMode(StrEnum):
    PRODUCTION = "production"
    TEST = "test"
~~~

Test that the production CLI will have no root override, that production and test roots cannot be exchanged, and that these candidates are rejected:

~~~python
ATTACK_PATHS = (
    r"..\outside",
    r"E:\outside",
    r"\\server\share\run",
    r"CON",
    r"aux.txt",
    "name.",
    "name ",
    "a" * 241,
)
~~~

On Windows, create a temporary junction or symbolic-link parent under an injected unit-test root and assert that resolution through it is rejected. Unit tests may inject an isolated temporary RootPolicy object; no production CLI flag or environment variable may expose that seam.

- [ ] **Step 2: Write lease, status, and cache tests**

Cover one writer per run, concurrent different runs, live lease refusal, stale lease recovery only when the recorded process is absent, heartbeat advancement, cancelled-run refusal, atomic status replacement, cache rebuild from run-status.json, and latest-complete remaining pointed at the newest complete run when a later run fails.

~~~python
def test_failed_run_does_not_replace_latest_complete(index_store, complete_run, failed_run):
    index_store.rebuild()
    assert index_store.read_pointer("latest-complete")["run_id"] == complete_run.run_id
    assert index_store.read_pointer("latest")["run_id"] == failed_run.run_id
~~~

- [ ] **Step 3: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_paths.py tests/test_ultra_locks.py tests/test_ultra_status_indexes.py
~~~

- [ ] **Step 4: Implement durable JSON and path policy**

Expose these exact interfaces:

~~~python
@dataclass(frozen=True, slots=True)
class RootPolicy:
    production_root: Path
    test_root: Path

@dataclass(frozen=True, slots=True)
class RunLayout:
    root: Path
    root_staging_dir: Path
    run_dir: Path
    input_dir: Path
    authoring_dir: Path
    artifacts_dir: Path
    delivery_dir: Path
    validation_dir: Path
    validation_current_dir: Path
    validation_attempts_dir: Path
    recovery_dir: Path
    logs_dir: Path

def default_root_policy() -> RootPolicy:
    return RootPolicy(PRODUCTION_ROOT, TEST_ROOT)

def create_run_id(now_utc: datetime, entropy: bytes) -> str:
    digest = hashlib.sha256(entropy).hexdigest()[:12]
    return f"{now_utc:%Y%m%dT%H%M%SZ}-{digest}"

def build_run_layout(mode: RunMode, run_id: str, policy: RootPolicy) -> RunLayout:
    root = policy.production_root if mode is RunMode.PRODUCTION else policy.test_root
    run_dir = root / "runs" / run_id[:4] / run_id[4:6] / run_id
    assert_safe_descendant(root, run_dir)
    return RunLayout(
        root=root,
        root_staging_dir=root / ".staging",
        run_dir=run_dir,
        input_dir=run_dir / "input",
        authoring_dir=run_dir / "work" / "authoring",
        artifacts_dir=run_dir / "artifacts",
        delivery_dir=run_dir / "delivery",
        validation_dir=run_dir / "validation",
        validation_current_dir=run_dir / "validation" / "current",
        validation_attempts_dir=run_dir / "validation" / "attempts",
        recovery_dir=run_dir / "recovery",
        logs_dir=run_dir / "logs",
    )
~~~

assert_safe_descendant must resolve every existing ancestor, reject reparse points, reject Windows reserved names and trailing space/dot components, enforce a conservative path length, and prove the final target remains under the selected root.

The artifact subdirectories are fixed as artifacts/U00-U03-evidence, artifacts/U04-U05-world-volume, artifacts/U06-U08-inference and artifacts/U09-U10-verdict. No authoring, failure or recovery output may be created beside the run bundle.

jsonio.py must provide canonical_json_bytes, sha256_bytes, atomic_write_bytes, atomic_write_json, load_json_object and append_jsonl_locked. Atomic writes use a same-directory temporary file, flush, fsync where available, os.replace, and directory fsync where supported.

- [ ] **Step 5: Implement leases and authoritative status**

~~~text
@dataclass(frozen=True, slots=True)
class Lease:
    run_id: str
    owner_pid: int
    owner_nonce: str
    acquired_at: str
    heartbeat_at: str
    expires_at: str

Public function signatures:

acquire_run_lease(layout: RunLayout, now: datetime, ttl: timedelta) -> Lease
heartbeat_run_lease(layout: RunLayout, lease: Lease, now: datetime) -> Lease
release_run_lease(layout: RunLayout, lease: Lease) -> None
~~~

Implement the bodies with exclusive creation/CAS semantics. Never reclaim a lease merely because its timestamp is old; also verify the recorded local process is not alive or require an explicit recovery operation.

run-status.json is the authority. index/runs.jsonl, index/latest.json, index/latest-complete.json and index/latest-needs-attention.json are derived caches that indexes.py can rebuild deterministically. Root and run START-HERE.md files contain only neutral run IDs, status, timestamps, and relative navigation; sensitive titles never appear.

- [ ] **Step 6: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_paths.py tests/test_ultra_locks.py tests/test_ultra_status_indexes.py
python -m py_compile skills/crossframe-ultra/scripts/ultra_runtime/jsonio.py skills/crossframe-ultra/scripts/ultra_runtime/paths.py skills/crossframe-ultra/scripts/ultra_runtime/locks.py skills/crossframe-ultra/scripts/ultra_runtime/status.py skills/crossframe-ultra/scripts/ultra_runtime/indexes.py
~~~

- [ ] **Step 7: Root review and commit**

~~~powershell
git commit -m "feat: add fixed ultra run storage"
~~~

## W4-0: Freeze shared W4 contracts before consumer rebuilds

**Owner:** Root planner only

**Depends on:** Tasks 1–6 at clean commit `b2e7361`

**Files:**

- Modify: docs/superpowers/plans/2026-08-02-crossframe-ultra-implementation.md
- Modify: tests/test_ultra_schemas.py
- Modify: skills/crossframe-ultra/schemas/ultra-phase-event.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-source-lock.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-read-event.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-retrieval-ledger.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-world-volume.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-transformation-ledger.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-concept-disposition.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-output-plan.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-semantic-coverage.schema.json
- Modify: skills/crossframe-ultra/schemas/ultra-article-review.schema.json

All Ultra schemas and `tests/test_ultra_schemas.py` become root-owned shared files after this gate. Task workers may report a contract gap but may not edit those files. W4-0 changes only the ten schemas above; unchanged schemas, shared runtime modules, task runtimes, task tests, fixtures, templates and references remain outside its write set.

- [ ] **Step 1: Write contract RED tests**

Add self-contained schema tests that fail on `b2e7361` for:

- terminal blocked/cancelled phase events and their no-output rule;
- U1 source, release, compatibility, knowledge, skill-tree, input-snapshot, parent-event, explicit verified-or-unknown ACL, named source-unit content hash and read-receipt authority;
- U2 eligibility, request, conditional real authorization, query and source-inventory authority, including structured required and N/A bases and honest unknown source dates;
- U4/U5 input cardinality and named content versus sealed-artifact hash roles;
- complete non-flattened Omega structure, exact A/X/T/O/C/R/I/N/J scale axes, promoted closed Rac/Rcc record fields, local channel authority and deterministic no-op boundaries;
- at least one scale, circle-relation and representation/expression transformation, each kept as a separately classified record with structured identity, loss, effective variables, residuals and return conditions;
- U5 concept disposition bound to evidence, volume, transformation, registry, route and contract authority, including structured unknown-pending obligations without U10-owned article-section assignments;
- the exact U10 10-section plus 5-appendix partial output plan, complete 13-kind semantic universe, dependencies and 15 blind-recovery expectations;
- U11 article-bound semantic coverage with honest incomplete/complete states and a non-publishing mechanical article review that can record failure dependencies.

W4-0 schema fixtures stay inside `tests/test_ultra_schemas.py` and do not require the old Task 7, 8, or 11 producers or fixtures to conform before their rebuilds. Do not use skip, xfail, optional authority fields or weakened assertions to hide migration work.

Replace external Task 8 fixture reads in the focused schema suite with sealed `minimal_instances()` values. Phase-event and read-event use their special hash algorithms and are not routed through the generic phase-artifact content validator. Remove the old Task 7 producer-conformance assertion from this focused file and transfer equivalent producer tests to the Task 7 completion gate; Task 8 and Task 11 receive the corresponding public-schema conformance gates below.

- [ ] **Step 2: Observe focused RED**

~~~powershell
python -B -m pytest -q -p no:cacheprovider tests/test_ultra_schemas.py tests/test_ultra_compatibility.py
~~~

The RED must be an assertion-level contract failure, not collection, import, JSON syntax or environment failure.

- [ ] **Step 3: Freeze the corrected contracts**

Keep all existing schema IDs, version bindings, Draft 2020-12 closure and canonical envelope/hash algorithms. Generic artifacts hash canonical payloads with `content_sha256` removed. Phase-event content hashes exclude both self-hash fields before `event_sha256` seals the event; read-event `content_sha256` remains the manifest-owned source-unit hash and `read_event_sha256` seals the event. Phase input/output arrays remain bare SHA-256 strings. Schemas name external authority roles, while later runtime validators recompute and compare roles that JSON Schema cannot equate.

A read receipt uses the separate `receipt_sha256` role. An unverifiable ACL is recorded as `unknown`, never asserted as verified, while Task 7 owns the downstream fail-closed decision.

Phase ownership is fixed as follows: world volume U4; transformation ledger and concept disposition U5; output plan U10; semantic coverage and article review U11. Dirty-tree evidence cannot override these approved design phases.

Do not add new StateDiff, semantic-inventory, article-packet or final-chat schemas, and do not add a shared `contracts.py`. Those concepts remain in their approved Task 8, 11 and 13 forms. Do not create a production release manifest: Task 7 must fail closed until Task 14 creates it, while tests use explicit temporary authority values.

- [ ] **Step 4: Run focused GREEN and boundary checks**

~~~powershell
python -B -m pytest -q -p no:cacheprovider tests/test_ultra_schemas.py tests/test_ultra_compatibility.py
Get-ChildItem skills/crossframe-ultra/schemas -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null; if ($LASTEXITCODE -ne 0) { throw "invalid JSON: $($_.FullName)" } }
git diff --check
git diff --name-only b2e7361 --
~~~

Run `python -B -m pytest -q -p no:cacheprovider tests/test_ultra_*.py` once and record the exact downstream migration failures. W4-0 acceptance requires the focused shared-contract suite and write boundary to pass; old Task 7, 8 and 11 consumer failures are assigned to their independent rebuilds rather than repaired across the boundary.

- [ ] **Step 5: Independent review and root commit**

The reviewer verifies the approved design phase table, hash-role separation, closed authority fields, the absence of dirty-tree wholesale copying, and the exact write set. The root alone stages and commits W4-0.

~~~powershell
git commit -m "fix: freeze ultra W4 shared contracts"
~~~

## Task 7: Implement U0–U3 source lock, evidence freeze, retrieval eligibility, and privacy

**Owner:** Worker C

**Depends on:** Tasks 3, 4, 6, and W4-0

**Files:**

- Create: tests/test_ultra_state_machine.py
- Create: tests/test_ultra_source_read_coverage.py
- Create: tests/test_ultra_evidence.py
- Create: tests/test_ultra_retrieval_privacy.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/state_machine.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/source_integrity.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/evidence.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/retrieval.py

- [ ] **Step 1: Write U0–U3 transition tests**

Valid order begins U0, U1, U2, U3. Reject skipped phases, overwritten events, parent-hash mismatch, changed input hash, changed source/runtime/schema binding, replayed event hash, evidence cutoff movement, and post-U3 evidence insertion.

~~~python
def test_new_evidence_after_u3_requires_fork(phase_store, frozen_evidence):
    phase_store.complete("U3", artifact_hashes=frozen_evidence)
    with pytest.raises(EvidenceFrozenError):
        phase_store.append_evidence({"evidence_id": "EV-LATE"})
~~~

Every event contains run_id, phase_id, event_type, parent_event_sha256, input_artifact_hashes, output_artifact_hashes, version binding, timestamp, status, failure code, invalidated phases, and event_sha256.

Task 7 completion must construct real phase-event, source-lock, read-event and retrieval-ledger producer outputs and validate each against its W4-0 public schema under externally supplied run/version/phase/parent authority. The tests recompute the special phase-event and read-event hashes, reject stale or swapped upstream hashes, and live in `test_ultra_state_machine.py`, `test_ultra_source_read_coverage.py` and `test_ultra_retrieval_privacy.py`, not the shared schema suite.

Source-read coverage requires exactly 4,753 unique source units: 4,631 paragraph anchors and 122 table anchors. Each read event binds source-unit content hash, promoted semantic snapshot hash, reader mode, real execution identity available to the host and timestamp. The runtime may create a read plan but may not mark units read on the model's behalf.

- [ ] **Step 2: Write evidence identity and source-lineage tests**

Allowed identities are observed, reported, inferred, competing, user-claim, model-candidate, simulated, and unknown. Test that two articles citing the same upstream report form one independence cluster; a simulated claim cannot satisfy a factual evidence requirement; user assertions do not raise confidence; unknowns remain explicit.

- [ ] **Step 3: Write retrieval and privacy tests**

The eligibility gate returns required for real, time-sensitive, legal, medical, financial, political, product, policy, institutional and current-fact claims; it returns not-applicable only for pure logic or fully closed supplied-material analysis.

Test:

- required retrieval with network unavailable becomes blocked;
- required retrieval with sensitive outbound disallowed becomes blocked;
- deidentified queries contain none of the fixture names, emails, IDs, file names, secrets or quoted private sentences;
- external prompt-injection text is stored as untrusted content and cannot alter phases, roots, versions or tool policy;
- bounded retry records rate limit/timeout and stops;
- every source records event date, publication date, interest, upstream lineage, supported claim and what it cannot prove.
- low disk space changes status to needs_attention, preserves the last checkpoint and deletes nothing;
- an unverifiable ACL is reported as unknown rather than falsely labeled encrypted or private.

- [ ] **Step 4: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_state_machine.py tests/test_ultra_source_read_coverage.py tests/test_ultra_evidence.py tests/test_ultra_retrieval_privacy.py
~~~

- [ ] **Step 5: Implement the U0 run contract**

U0 freezes:

~~~json
{
  "trigger": "crossframe-ultra",
  "request_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "run_mode": "production",
  "sensitivity": "public",
  "retention": "retain",
  "outbound_permission": "deidentified-only",
  "evidence_cutoff": "2026-08-02T00:00:00Z",
  "capabilities": {
    "filesystem": "available",
    "docx_parser": "available",
    "network": "available",
    "retrieval": "required",
    "validators": "available",
    "subagents": "available",
    "model_context": "available"
  },
  "resource_limits": {
    "maximum_branches": 64,
    "maximum_retrieval_rounds_without_material_novelty": 2,
    "maximum_tool_retries": 3,
    "maximum_repair_attempts": 3
  }
}
~~~

The literal strings above become closed enums or validated values in the schema. The capability state enum is available, required, unavailable, or not-applicable. Required plus unavailable blocks the run.

- [ ] **Step 6: Implement U1–U3**

U1 verifies source-manifest.json, release-manifest.json, compatibility-matrix.json, knowledge closure, skill-tree hash, fixed root, free-space reserve and current-user ACL where verifiable.

U1 also writes U01-read-plan.json and validates U01-read-events.jsonl against all 4,753 source-unit hashes before allowing U2. Duplicate, missing, cross-snapshot or runtime-synthesized completion events fail the phase.

U2 records retrieval eligibility before any query. Each query passes through redact_query and a hostile-instruction filter. External content remains data.

U3 deduplicates source lineage, freezes evidence_cutoff and writes the evidence ledger. Any later evidence call raises EvidenceFrozenError and recovery.fork_run must create a new run ID.

- [ ] **Step 7: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_state_machine.py tests/test_ultra_source_read_coverage.py tests/test_ultra_evidence.py tests/test_ultra_retrieval_privacy.py
~~~

- [ ] **Step 8: Root review and commit**

~~~powershell
git commit -m "feat: freeze ultra evidence plane"
~~~

## Task 8: Implement the volumetric Ω state and non-flattening transformations

**Owner:** Worker B

**Depends on:** Tasks 4, 6, and W4-0. Development may use a W4-0-owned sealed U3 fixture; root integration still follows Task 7.

**Files:**

- Create: tests/test_ultra_world_volume.py
- Create: tests/test_ultra_transformations.py
- Create: tests/test_ultra_concept_closure.py
- Create: tests/fixtures/ultra-runtime/world-volume-valid.json
- Create: tests/fixtures/ultra-runtime/world-volume-flat-invalid.json
- Create: tests/fixtures/ultra-runtime/transformation-valid.json
- Create: skills/crossframe-ultra/scripts/ultra_runtime/world_volume.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/transformations.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/concept_closure.py

- [ ] **Step 1: Write world-volume RED tests**

The valid fixture must contain:

- one actor in three circles with different roles;
- two simultaneous directed relation types between the same circle pair;
- two local containment relations with different bases and multiple parents;
- local M and Psi states for every represented object/circle/position;
- a nine-axis scale profile per represented object/circle/position;
- immediate, interaction, organizational, institutional and long-term clocks;
- a real channel touching only a subset of positions;
- source-faithful `W` evidence status with information identity, source lineage and visibility;
- source-faithful `K` identity criteria for every represented object, circle and position;
- local power, constraint, exit, burden and spillover distributions attached to their exact `Rac`/`Q`/`M`/`Psi` positions rather than overloaded onto `W` or `K`;
- unknowns and residuals attached to their exact locations.

Reject a global M, global Psi, one global scale label, single parent_id, averaged circle state, missing membership basis, relation without direction, channel without endpoints, and a state position without identity criteria.

The concept-closure test traverses every registry concept and permits only applied, tested-rejected, not-applicable or unknown-pending. It rejects an unvisited concept, missing route-required/neighbor concept, copied boilerplate rationale, applied concept without an article semantic unit, and unknown-pending without a condition branch or evidence plan.

Task 8 completion must construct real world-volume, transformation-ledger and concept-disposition artifacts that validate against the W4-0 public schemas. Its tests recompute content and sealed-artifact hashes from externally supplied U3/U4/U5 authority, reject stale or self-selected authority, and keep its task fixtures read-only consumers of the frozen shared contract.

- [ ] **Step 2: Write event-locality and transform RED tests**

~~~python
def test_event_updates_only_reachable_positions():
    result = apply_event(valid_volume, event_with_one_real_channel)
    assert result.changed_positions == ("POS-TEAM-MANAGER",)
    assert result.unchanged_positions == (
        "POS-FAMILY-MEMBER",
        "POS-ASSOCIATION-DELEGATE",
    )

def test_each_cross_circle_hop_is_revalidated():
    with pytest.raises(ChannelContinuityError):
        validate_cascade(cascade_with_valid_first_hop_and_missing_second_hop)
~~~

Transform records must separate scale, circle-relation, and representation/expression translation. Each records input/output identity, preserved, changed, folded, omitted, unknown, task-relative loss, effective variables, closure, residuals and return conditions.

- [ ] **Step 3: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_world_volume.py tests/test_ultra_transformations.py tests/test_ultra_concept_closure.py
~~~

- [ ] **Step 4: Implement validation, not synthetic reasoning**

world_volume.py validates model-authored Ω artifacts and computes deterministic reachability/state differences. It does not fabricate actors, circles or edges.

Use this public result:

~~~python
@dataclass(frozen=True, slots=True)
class StateDiff:
    source_volume_sha256: str
    event_id: str
    changed_positions: tuple[str, ...]
    unchanged_positions: tuple[str, ...]
    changed_relations: tuple[str, ...]
    advanced_clocks: tuple[str, ...]
    inherited_unknown_ids: tuple[str, ...]
    inherited_residual_ids: tuple[str, ...]

def validate_world_volume(volume: Mapping[str, object]) -> None:
    validate_instance("ultra-world-volume.schema.json", dict(volume))
    validate_unique_ids(volume)
    validate_relation_endpoints(volume)
    validate_membership_bases(volume)
    validate_local_state_coverage(volume)
    validate_scale_profiles(volume)

def apply_event(
    volume: Mapping[str, object],
    event: Mapping[str, object],
) -> StateDiff:
    validate_world_volume(volume)
    return compute_reachable_state_diff(volume, event)
~~~

transforms.py validates explicit transforms and cascade hops. It must reject a net-effect-only record that hides location-specific gains, damage, exit costs or spillovers.

concept_closure.py loads the complete promoted registry, computes route plus neighbor closure, validates one independent disposition per concept and returns the set of applied/retained semantic units required in the article. It never selects a disposition on the model's behalf.

- [ ] **Step 5: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_world_volume.py tests/test_ultra_transformations.py tests/test_ultra_concept_closure.py
~~~

- [ ] **Step 6: Root review and commit**

~~~powershell
git commit -m "feat: add ultra world-volume contracts"
~~~

## W5-0: Freeze shared U6–U10 artifact contracts before producer construction

**Owner:** Root planner only

**Depends on:** Tasks 5, 7, and 8, with all accepted inputs integrated from clean descendants of `b2e7361`

**Files:**

- Modify: `docs/superpowers/plans/2026-08-02-crossframe-ultra-implementation.md`
- Modify: `tests/test_ultra_schemas.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- Modify: `skills/crossframe-ultra/schemas/ultra-claim-mechanism-graph.schema.json`
- Create: `skills/crossframe-ultra/schemas/ultra-recursive-state.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-recursive-lineage.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-order-evaluation.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-red-team-report.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-verdict.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-action-ranking.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-forecast-ledger.schema.json`
- Create: `skills/crossframe-ultra/schemas/ultra-forecast-resolution-event.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-framework-gap-ledger.schema.json`

This list is the exact W5-0 tracked write set: the plan, the shared schema test, the schema registry, and exactly ten named schema files. All thirteen paths are root-owned during W5-0. Task 10A, Task 9, and Task 10B consume these files read-only; a producer worker may report a contract gap but may not edit any of them. No producer runtime, Task 9/10 producer test, external fixture, template, reference, constant, compatibility matrix, unrelated schema, or file from the discarded old implementation belongs to W5-0. Keep every W5-0 instance fixture as a sealed inline value in `tests/test_ultra_schemas.py`, following W4-0.

- [ ] **Step 1: Write focused shared-contract RED tests**

Add assertion-level tests for exact phase ownership, distinct required upstream artifact hashes, closed object boundaries, valid sealed inline instances, recursive-state-before-lineage binding, order-evaluation-before-red-team binding, verdict-before-action/forecast binding, immutable forecasts versus later separate resolution events, U10 framework-gap isolation, and unchanged global schema version 1. Reject self-selected external authority, a hash field reused for two roles, an identity field reused across artifact/node/state/branch/claim/mechanism/evidence/route/concept roles, and any deeper recursive order that upgrades evidence grade.

Every artifact uses the existing common envelope, exact `schema_id`, exact `schema_version`, and owning `phase_id`. Keep simulated, observed, reported, inferred, user-claim, model-candidate, competitor, and unknown identities distinct wherever the design requires evidence identity. Reuse the existing lowercase SHA-256 definition and canonical content-hash helper; W5-0 creates no public runtime function, helper signature, or business identifier.

- [ ] **Step 2: Observe focused RED**

~~~powershell
python -B -m pytest -q -p no:cacheprovider tests/test_ultra_schemas.py tests/test_ultra_compatibility.py
~~~

The RED must be an assertion-level contract failure, not collection, import, JSON syntax, or environment failure.

- [ ] **Step 3: Freeze global schema version 1, phase ownership, and the artifact DAG**

Keep `ARTIFACT_SCHEMA_VERSION = 1`. U6–U9 artifacts have never been released, so do not add a v1-to-v2 migration or compatibility row. Every schema remains Draft 2020-12 and closed at every object boundary.

The required upstream artifact DAG is exact:

| Artifact contract | Owning phase | Required upstream authority |
|---|---|---|
| claim/mechanism graph | U6 | U3 evidence ledger; U4 world volume; U5 transformation ledger; U5 concept disposition |
| recursive state | U7 | U4 world volume; U5 transformation ledger; U5 concept disposition; U6 claim/mechanism graph; externally verified parent state authority—U4 for a first-order root, otherwise the sealed parent U7 recursive-state artifact |
| recursive lineage | U7 | U4 world volume; U5 transformation ledger; U5 concept disposition; U6 claim/mechanism graph; every sealed U7 recursive-state artifact referenced by a lineage node |
| order evaluation | U8 | U6 claim/mechanism graph; sealed U7 recursive lineage |
| red-team report | U8 | U6 claim/mechanism graph; sealed U7 recursive lineage; sealed U8 order-evaluation artifact |
| verdict | U9 | U3 evidence ledger; U6 claim/mechanism graph; U7 recursive lineage; U8 order evaluation; U8 red-team report |
| action ranking | U9 | sealed U9 verdict |
| forecast ledger | U9 | sealed U9 verdict and its already-bound U3/U6/U7/U8 authority |
| forecast resolution event | U9 | originating immutable U9 forecast artifact; exact original forecast record |
| framework-gap ledger | U10 | every current-run artifact cited by each candidate |

Required upstream hashes are distinct explicit named fields. A model-authored document cannot select which external artifact authorizes it; orchestration supplies and verifies that authority before the producer seals the artifact. The construction order follows the DAG: each recursive-state artifact is sealed before lineage, order evaluation is sealed before red-team, and verdict is sealed before action ranking or forecast ledger.

- [ ] **Step 4: Freeze the U6–U10 contract details**

The U6 claim/mechanism graph retains a central claim, referenceable claims and mechanisms, typed edges, main/strongest-rival/mixture/residual competing explanations, rankings, and qualified insights. Insight effects remain exactly `changes-ranking`, `explains-residual`, `changes-observable-forecast`, `changes-counterfactual`, `changes-intervention`, and `identifies-circle-scale-channel`; an insight cannot become new framework authority.

Each U7 recursive-state artifact records run/path/node and parent run/path/node identities, order 1–3, a full state hash or explicitly bounded subgraph, inherited fact/evidence/unknown/loss/residual identities, this-order event/mechanism/state-diff/signal roles, evidence identity, and the full common-envelope version binding. Seal these state artifacts first. Recursive-lineage nodes then bind their corresponding sealed artifact hashes instead of trusting a caller-declared state hash. Preserve acyclicity, order, merge, prune, and stop semantics. Branch kinds remain exactly main, strongest-rival, mixture, and residual.

The U8 order-evaluation artifact is constructed next. It requires those branch classes or a structured not-applicable record for each order, compares the simple baseline on explanation gain, forecast gain, added assumptions, added losses, local predictability, and continuation value, and records only the frozen stop kinds. Only after that artifact is sealed may the red-team report bind it and record challenges, sensitivity checks, simple-baseline comparisons, unresolved items, and overall status without changing upstream evidence identity.

The U9 verdict is constructed and sealed first, preserving either a best-current judgment or exact non-decidability and keeping fact, prediction, value, responsibility, and authorization verdicts independent. Every kind verdict has its own required `verdict_id`. The top-level `partial_ranking_justification` is always present: best-current requires it to be null and requires the unique total ranks 1 through 4; non-decidability requires a non-empty justification, a unique continuous non-null prefix 1 through k where 1 <= k < 4, and null for every remaining rank. The schema enforces the available structural cases, while Task 10B rechecks continuity and set equality, ensures all five verdict IDs are mutually distinct and disjoint from every other identity domain, and does not infer authority from a caller-authored ID.

Action ranking and forecast production are downstream consumers of that sealed verdict. Action ranking remains independent from the five verdict kinds and retains active, delay, probe, exit-or-transfer, maintain-status-quo, and no-action options, preferred and second choices, switch and stop conditions, rollback, and no-action consequences. Its required `considered_verdict_ids` contains exactly five unique identifiers. Every option has a required nullable `authorization_verdict_id`: an authorized option requires an identifier and an unauthorized option requires null. Task 10B verifies that the considered set equals the five bound verdict lock IDs, resolves every non-null authorization reference to the authorization lock, and rejects prediction or responsibility locks presented as permission. Action ranking adds no public API.

The U9 forecast artifact contains only frozen original forecast records. It retains the prose `time_window`, `indicator`, and `resolution_rule`, and also requires `prediction_verdict_id`, `indicator_id`, `window_start`, `window_end`, and a closed `resolution_predicate`. The predicate records `operator`, `baseline_value`, `target_value`, and non-negative nullable `tolerance`; operators are exactly `gt`, `gte`, `lt`, `lte`, `eq`, `neq`, `within`, and `branch-equals`. A branch-dependent forecast requires `branch-equals`, null baseline, an identifier target, and null tolerance. Every other direction forbids `branch-equals` and requires numeric baseline, target, and tolerance. Task 10B additionally verifies `evidence_cutoff <= window_start <= window_end`, exact direction/operator compatibility, that `prediction_verdict_id` resolves to the prediction lock, and that a branch-equals target belongs to `branch_refs`.

The forecast ledger contains no mutable or nested resolution record, and no resolution event is emitted while an original is sealed. After an outcome is available, a separate append-only forecast-resolution event binds the originating U9 forecast artifact hash, forecast ID, matching `indicator_id`, original forecast record hash, resolution time, observation time, indicator resolution, direction correctness, time-window coverage, outcome, and observed value. The outcome mapping is exact: `correct` means resolved with correct direction inside the window; `partial` means resolved with correct direction outside the window; `incorrect` means resolved with incorrect direction; and `indeterminate` means unresolved. Unresolved events require null observed value and direction correctness; resolved events require a non-null observed value and a boolean direction result. Task 10B recomputes these fields from the immutable original and rejects caller mismatch. Brier fields exist only when the original probability was admissible and the outcome is binary-resolvable; the binary outcome is 1 only for correct and 0 for incorrect or partial, the score is `(p - y) ** 2`, and indeterminate events are never scored. The event retains U9 ownership while its timestamps record the later observation and resolution.

The framework-gap ledger is U10-owned, requires `isolated_from_current_reasoning` to be true, and binds every current-run artifact it cites. A candidate may propose a future document revision but cannot appear as current U6 mechanism support, U9 verdict reason, or U9 action authorization.

- [ ] **Step 5: Implement the ten schema changes and two registry entries**

Modify only the exact W5-0 files above. Register `ultra-recursive-state.schema.json` and `ultra-forecast-resolution-event.schema.json` in `SCHEMA_NAMES`; retain all existing registry names and all global version constants. Reuse the common envelope, schema loader, canonical content-hash helper, and phase-artifact validator. Do not add a producer API, runtime helper signature, external fixture, or compatibility row.

- [ ] **Step 6: Run focused GREEN and verify the exact W5-0 boundary**

~~~powershell
python -B -m pytest -q -p no:cacheprovider tests/test_ultra_schemas.py tests/test_ultra_compatibility.py
Get-ChildItem skills/crossframe-ultra/schemas -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null; if ($LASTEXITCODE -ne 0) { throw "invalid JSON: $($_.FullName)" } }
python -m py_compile skills/crossframe-ultra/scripts/ultra_runtime/schemas.py
git diff --check
git status --short
git diff --name-only 052bb442 --
~~~

Compare the tracked and untracked names from the final two commands with the exact thirteen-path W5-0 write set above. Report the exact changed files, RED and GREEN commands/results, and any genuinely unresolved plan/design decision. Do not stage or commit in this gate work package; the root integrates only after reviewing the exact boundary.

## Task 10A: Implement the U6 pass of Task 10—claims, mechanisms, competitors, and qualified insights

Task 10 remains the original Task 10, split into dependency-ordered passes 10A and 10B. This pass must be GREEN, root-reviewed, and integrated before Task 9 begins.

**Owner:** Worker C

**Depends on:** Tasks 7 and 8 plus W5-0

**Files:**

- Create: `tests/test_ultra_claim_mechanism.py`
- Create: `tests/fixtures/ultra-runtime/claim-mechanism-graph-valid.json`
- Create: `skills/crossframe-ultra/scripts/ultra_runtime/judgment.py`
- Consume read-only: `tests/fixtures/ultra-runtime/world-volume-valid.json`
- Consume read-only: `tests/fixtures/ultra-runtime/transformation-valid.json`
- Consume read-only: `tests/test_ultra_schemas.py`
- Consume read-only: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-evidence-ledger.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-world-volume.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-transformation-ledger.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-concept-disposition.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-claim-mechanism-graph.schema.json`

Task 10A owns only the three producer files listed first. It must not edit any W5-0 schema, schema-test, or schema-registry file.

- [ ] **Step 1: Write U6 RED tests**

The claim/mechanism graph must bind externally supplied U3 evidence-ledger, U4 world-volume, U5 transformation-ledger, and U5 concept-disposition hashes. It contains a central claim, referenceable claims and mechanisms, typed edges, main/strongest-rival/mixture/residual competitors, an explicit total or justified partial ranking, and qualified insights. Reject stale or swapped upstream hashes, self-selected external authority, an identity field reused across roles, a simulated result promoted to fact, a user claim treated as evidence, and an insight that has no frozen effect or tries to become framework authority.

Build `claim-mechanism-graph-valid.json` against the accepted U3/U4/U5 fixture hashes so Task 9 receives one sealed, mutually consistent U6 authority rather than reconstructing it.

- [ ] **Step 2: Observe Task 10A RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_claim_mechanism.py
~~~

The RED must fail at the missing U6 producer behavior or an asserted binding, not at collection or fixture parsing.

- [ ] **Step 3: Implement U6 qualification and producer validation**

~~~text
INSIGHT_EFFECTS = (
    "changes-ranking",
    "explains-residual",
    "changes-observable-forecast",
    "changes-counterfactual",
    "changes-intervention",
    "identifies-circle-scale-channel",
)

def qualifies_as_insight(candidate: Mapping[str, object]) -> bool:
    effects = set(candidate["effects"])
    return bool(effects.intersection(INSIGHT_EFFECTS))
~~~

Retain this existing Task 10 helper shape. The U6 producer receives verified U3/U4/U5 artifact authority from orchestration, compares it with the named schema fields, and seals the graph only after all bindings match. It validates model-authored semantics; it does not invent claims, mechanisms, identities, or a new public function signature.

- [ ] **Step 4: Run Task 10A GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_claim_mechanism.py
~~~

- [ ] **Step 5: Root review, integrate, and commit before Task 9**

~~~powershell
git commit -m "feat: add ultra claim mechanism producer"
~~~

## Task 9: Implement U7 recursive state/lineage, then U8 per-order evaluation and red team

**Owner:** Worker B

**Depends on:** Tasks 7 and 8, W5-0, and the integrated Task 10A U6 producer

**Files:**

- Create: `tests/test_ultra_recursion.py`
- Create: `tests/test_ultra_order_evaluation.py`
- Create: `tests/test_ultra_red_team.py`
- Create: `tests/fixtures/ultra-runtime/recursive-state-valid.json`
- Create: `tests/fixtures/ultra-runtime/recursive-lineage-valid.json`
- Create: `tests/fixtures/ultra-runtime/recursive-lineage-invalid.json`
- Create: `tests/fixtures/ultra-runtime/order-evaluation-valid.json`
- Create: `tests/fixtures/ultra-runtime/red-team-report-valid.json`
- Create: `skills/crossframe-ultra/scripts/ultra_runtime/recursion.py`
- Consume read-only: `tests/fixtures/ultra-runtime/world-volume-valid.json`
- Consume read-only: `tests/fixtures/ultra-runtime/transformation-valid.json`
- Consume read-only: `tests/fixtures/ultra-runtime/claim-mechanism-graph-valid.json`
- Consume read-only: `tests/test_ultra_schemas.py`
- Consume read-only: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-recursive-state.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-recursive-lineage.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-order-evaluation.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-red-team-report.schema.json`

Task 9 owns only the nine producer files listed first. It must not edit W5-0's schema, schema-test, or schema-registry files. Its executable construction order is recursive state, recursive lineage, order evaluation, then red-team report.

- [ ] **Step 1: Write U7 recursive-state and lineage RED tests**

Test an order-1 direct effect, order-2 action-set reversal, and order-3 institutional lock-in. Each sealed recursive-state artifact binds externally supplied U4 world-volume, U5 transformation/concept, and U6 claim-graph authority; records run/path/node and parent run/path/node, order, a full state hash or explicitly bounded subgraph, inherited fact/evidence/unknown/loss/residual identities, this-order event/mechanism/state-diff/signals, evidence identity, and full version binding; and validates against the W5-0 schema.

Seal the recursive-state artifacts before constructing lineage. Each lineage node references the corresponding sealed artifact hash. Reject a caller-declared state hash without that artifact, stale or swapped upstream authority, and any lineage that fails to preserve its U4/U5/U6 bindings.

Also reject:

- order 0 or order greater than 3;
- order-2 node with an order-0 parent;
- child containing only the parent's prose conclusion;
- lost fact, evidence, unknown, loss, or residual identity;
- a simulated node marked observed;
- merged branches without compatible state identities;
- pruning without reason and retained residual;
- resource exhaustion labeled theoretical early stop.

- [ ] **Step 2: Observe U7 RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_recursion.py
~~~

- [ ] **Step 3: Implement recursive-state sealing before lineage validation**

~~~text
BRANCH_KINDS = ("main", "strongest-rival", "mixture", "residual")
STOP_KINDS = (
    "order-limit",
    "baseline-wins",
    "no-material-state-change",
    "local-predictability-exhausted",
    "evidence-boundary",
)

@dataclass(frozen=True, slots=True)
class LineageValidation:
    node_ids: tuple[str, ...]
    maximum_order: int
    early_stop_nodes: tuple[str, ...]
    inherited_unknown_ids: tuple[str, ...]
    inherited_residual_ids: tuple[str, ...]

Public function signature:

validate_recursive_lineage(lineage: Mapping[str, object], parent_volume: Mapping[str, object]) -> LineageValidation
~~~

Retain this already-frozen public result and signature without adding fields or parameters. Before calling it, the producer verifies the U4/U5/U6 authorities and every sealed recursive-state artifact named by the lineage. The implementation validates schema, acyclicity, order-parent relation, recursive-state binding, identity inheritance, branch merge compatibility, pruning records, and stopping. Private helpers may perform the new checks. Resource/tool failure is a run status transition, not an allowed `STOP_KIND`.

- [ ] **Step 4: Run U7 GREEN before starting U8**

~~~powershell
python -B -m pytest -q tests/test_ultra_recursion.py
~~~

- [ ] **Step 5: Write U8 order-evaluation RED tests**

Every evaluated order contains main, strongest-rival, mixture, and residual branches unless a structured not-applicable record is valid. It binds the sealed U6 claim graph and U7 lineage, compares a simple baseline on explanation gain, forecast gain, added assumptions, added losses, local predictability, and continuation value, and accepts only the frozen stop kinds.

~~~python
def test_deeper_order_does_not_increase_evidence_grade():
    lineage["nodes"][2]["evidence_grade"] = "high-by-depth"
    with pytest.raises(ValidationError):
        validate_recursive_lineage(lineage, parent_volume)
~~~

- [ ] **Step 6: Observe order-evaluation RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_order_evaluation.py
~~~

- [ ] **Step 7: Implement and seal order evaluation**

Validate per-order branch coverage or structured not-applicability, all six simple-baseline comparison dimensions, evidence-grade preservation, and only the frozen stop kinds. Write `order-evaluation-valid.json` only after its U6/U7 hashes match the already sealed authorities. Use private validation helpers and the existing schema registry; add no public runtime signature.

- [ ] **Step 8: Run order-evaluation GREEN before red-team construction**

~~~powershell
python -B -m pytest -q tests/test_ultra_order_evaluation.py
~~~

- [ ] **Step 9: Write red-team RED tests against the sealed order evaluation**

The red-team report binds the same U6/U7 authorities plus the exact sealed U8 order-evaluation artifact. Test challenges, sensitivity checks, simple-baseline comparisons, unresolved items, overall status, and rejection of a report that changes evidence identity, omits the order-evaluation hash, or substitutes a different evaluation.

- [ ] **Step 10: Observe red-team RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_red_team.py
~~~

- [ ] **Step 11: Implement red-team validation after order evaluation**

Validate the report through the W5-0 schema, verify its U6/U7/U8 hashes externally, and write `red-team-report-valid.json` only after those bindings match. Red-team may challenge conclusions but cannot rewrite recursive state, lineage, order evaluation, or evidence identity. Add no public runtime signature.

- [ ] **Step 12: Run the complete Task 9 GREEN suite**

~~~powershell
python -B -m pytest -q tests/test_ultra_recursion.py tests/test_ultra_order_evaluation.py tests/test_ultra_red_team.py
~~~

- [ ] **Step 13: Root review and commit**

~~~powershell
git commit -m "feat: add ultra recursive inference and red team"
~~~

## Task 10B: Implement the U9 pass of Task 10—verdict, action ranking, immutable forecasts, and later resolution events

This is the second pass of the original Task 10. It starts only after Task 9's sealed U7/U8 fixtures and producer are integrated.

**Owner:** Worker C

**Depends on:** Integrated Task 10A and Task 9

**Files:**

- Create: `tests/test_ultra_judgment.py`
- Create: `tests/test_ultra_forecast.py`
- Create: `tests/fixtures/ultra-runtime/verdict-valid.json`
- Create: `tests/fixtures/ultra-runtime/verdict-evasive-invalid.json`
- Create: `tests/fixtures/ultra-runtime/forecast-valid.json`
- Create: `tests/fixtures/ultra-runtime/forecast-resolution-event-valid.json`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/judgment.py`
- Create: `skills/crossframe-ultra/scripts/ultra_runtime/forecast.py`
- Consume read-only: `tests/fixtures/ultra-runtime/claim-mechanism-graph-valid.json`
- Consume read-only: `tests/fixtures/ultra-runtime/recursive-lineage-valid.json`
- Consume read-only: `tests/fixtures/ultra-runtime/order-evaluation-valid.json`
- Consume read-only: `tests/fixtures/ultra-runtime/red-team-report-valid.json`
- Consume read-only: `tests/test_ultra_schemas.py`
- Consume read-only: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-claim-mechanism-graph.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-verdict.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-action-ranking.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-forecast-ledger.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-forecast-resolution-event.schema.json`
- Consume read-only: `skills/crossframe-ultra/schemas/ultra-framework-gap-ledger.schema.json`

Task 10B owns only the eight producer files listed first. It must not edit W5-0's schema, schema-test, or schema-registry files. Its executable construction order is verdict, action ranking, immutable forecast ledger, then the capability to record a separate later resolution event.

- [ ] **Step 1: Write U9 verdict RED tests**

Every decidable case requires a best-current judgment, decisive reasons, rival rejection, confidence, residuals, reversal conditions, time window, action implication, and cross-circle distribution. A formally undecidable input receives an exact non-decidability judgment naming the missing proposition or comparison rule rather than fabricating a substantive verdict. The sealed verdict binds U3 evidence, the U6 claim graph, U7 lineage, U8 order evaluation, and U8 red-team report.

Test these exact failures:

- “情况复杂、都有可能” with no ranking;
- agreement with user premise solely because it is user-supplied;
- contradiction solely for rhetorical toughness;
- high confidence with unresolved decisive unknown;
- factual verdict derived from a simulated node;
- value verdict used as factual evidence;
- responsibility used as authorization;
- prediction used as permission.

The low-evidence valid fixture must choose a best-current judgment, mark low confidence, name assumptions, and state what would reverse it. Fact, prediction, value, responsibility, and authorization verdicts remain independently sealed and each carries a unique `verdict_id`. Best-current uses a total unique 1-through-4 explanation ranking with null `partial_ranking_justification`. Exact non-decidability uses a non-empty justification and only a unique continuous ranked prefix 1 through k, where 1 <= k < 4; every remaining rank is null. Runtime validation must recheck those rank and lock-ID sets and keep all five IDs disjoint from other identity domains.

- [ ] **Step 2: Observe verdict RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_judgment.py
~~~

- [ ] **Step 3: Implement and seal verdict before action or forecast**

~~~text
VERDICT_KINDS = ("fact", "prediction", "value", "responsibility", "authorization")

Public function signature:

validate_verdict_bundle(verdict: Mapping[str, object], evidence: Mapping[str, object], lineage: Mapping[str, object]) -> None
~~~

Retain this already-frozen public signature. Before calling it, the producer externally verifies the U6 claim graph and both U8 artifacts in addition to the evidence and lineage arguments, then compares their hashes with the verdict schema fields. Record those extra authorities as producer requirements rather than adding positional or keyword parameters. Implement the verdict slice with independent evidence-identity, rival-strength, confidence/unknown, five-lock, and exact non-decidability checks.

- [ ] **Step 4: Run verdict GREEN before writing action tests**

~~~powershell
python -B -m pytest -q tests/test_ultra_judgment.py
~~~

- [ ] **Step 5: Write action-ranking and U10 isolation RED tests**

Action ranking binds the sealed verdict, remains independent of the five verdict kinds, compares active, delay, probe, exit-or-transfer, maintain-status-quo, and no-action, and records preferred and second choices, switch and stop conditions, rollback, and no-action consequences. It must carry exactly the five bound lock IDs in `considered_verdict_ids`. Every option carries `authorization_verdict_id`, which is an authorization-lock identifier exactly when `authorized` is true and otherwise is null. Runtime validation resolves the reference to kind authorization and rejects a prediction or responsibility lock presented as permission. Preserve the existing failure for no recommendation despite a direct choice request.

Also test U10 framework-gap isolation: a gap candidate may cite bound current-run artifacts and propose a future document revision, but `isolated_from_current_reasoning` must be true and its ID cannot appear in canonical concept IDs, current U6 mechanism support, U9 verdict reasons, or U9 action authorization.

- [ ] **Step 6: Observe action/isolation RED with verdict still GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_judgment.py
~~~

- [ ] **Step 7: Implement action validation downstream of verdict**

~~~text
ACTION_KINDS = (
    "active",
    "delay",
    "probe",
    "exit-or-transfer",
    "maintain-status-quo",
    "no-action",
)
~~~

Complete the action-ranking slice behind the existing verdict-bundle entry point and validate U10 isolation through the W5-0 schemas and existing schema registry. A framework-gap candidate can be recorded for future revision but cannot authorize or support the current U6/U9 reasoning. Add no public runtime signature.

- [ ] **Step 8: Run judgment/action GREEN before forecast construction**

~~~powershell
python -B -m pytest -q tests/test_ultra_judgment.py
~~~

- [ ] **Step 9: Write immutable-forecast and later-resolution-event RED tests**

Every original forecast retains direction, prose time window, prose indicator, prose resolution rule, evidence cutoff, branch/node refs, and status. It also requires `prediction_verdict_id`, `indicator_id`, `window_start`, `window_end`, and a closed `resolution_predicate` with operator, baseline value, target value, and tolerance. Branch-dependent forecasts use only `branch-equals`, null baseline, an identifier target, and null tolerance; all other directions forbid `branch-equals` and use numeric baseline, target, and non-negative tolerance. Runtime validation resolves the prediction lock, checks `evidence_cutoff <= window_start <= window_end`, enforces direction/operator compatibility, and requires every branch-equals target to belong to `branch_refs`. Numeric probability is accepted only with a declared reference class, data/calibration basis, and admissibility result. The forecast ledger binds the sealed verdict, contains frozen originals only, and rejects a nested or mutable resolution record.

A resolution is accepted only later as a separate append-only event that binds the originating U9 forecast artifact hash, forecast ID, matching indicator ID, original forecast record hash, resolution time, observation time, indicator-resolved state, direction correctness, time-window coverage, outcome, and observed value. It retains U9 phase ownership even though its event timestamps are later. Correct means resolved, direction-correct, and inside the time window; partial means resolved and direction-correct but outside the time window; incorrect means resolved and direction-incorrect; indeterminate means unresolved. Runtime validation recomputes every result and rejects a caller mismatch. Brier fields exist only when the immutable original probability was admissible and the outcome is binary-resolvable: y is 1 only for correct, 0 for incorrect or partial, and the score is `(p - y) ** 2`; indeterminate events are unscored.

~~~python
def test_probability_without_calibration_is_rejected():
    with pytest.raises(UncalibratedProbabilityError):
        validate_forecast(forecast | {"probability": 0.73, "calibration_basis": None})

def test_resolution_appends_without_rewriting_prediction():
    before = canonical_json_bytes(forecast)
    append_resolution(ledger_path, resolution)
    assert canonical_json_bytes(
        load_original_forecast(ledger_path, forecast["forecast_id"])
    ) == before
~~~

- [ ] **Step 10: Observe forecast RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_forecast.py
~~~

- [ ] **Step 11: Implement immutable forecasts and separate later resolution events**

`forecast.py` validates forecast admission and freezes original records only after the sealed verdict authority matches. Its complete public surface is exactly:

~~~text
validate_forecast(forecast: Mapping[str, object]) -> None
load_original_forecast(ledger_path: Path, forecast_id: str) -> dict[str, object]
append_resolution(ledger_path: Path, resolution: Mapping[str, object]) -> None
~~~

The resolution sidecar path is derived only as `ledger_path.with_name(f"{ledger_path.stem}.resolution-events.jsonl")`. `append_resolution` uses the existing `append_jsonl_locked`, writes a distinct schema-validated event, and leaves every byte of the original ledger unchanged. Because a ledger may contain multiple original records, `load_original_forecast` always requires `forecast_id`. Direction correctness, time-window coverage, indicator resolution, outcome, and Brier score are recomputed from that immutable original plus the separately validated event; the resolution `indicator_id` must equal the original forecast indicator, Brier scoring runs only when the original probability was admissible and the outcome is binary-resolvable, and indeterminate events are never scored. Do not add another forecast entry point. Action ranking adds no public API, and `validate_verdict_bundle(verdict: Mapping[str, object], evidence: Mapping[str, object], lineage: Mapping[str, object]) -> None` remains unchanged.

- [ ] **Step 12: Run the complete Task 10B GREEN suite**

~~~powershell
python -B -m pytest -q tests/test_ultra_judgment.py tests/test_ultra_forecast.py
~~~

- [ ] **Step 13: Root review and commit**

~~~powershell
git commit -m "feat: add ultra judgment and forecast contracts"
~~~

## Task 11: Build the complete article, semantic coverage, and blind-reader contract

**Owner:** Worker A

**Depends on:** W4-0. Development may use the frozen U10 semantic universe and upstream authority fixtures; root integration still follows Tasks 7 and 8.

**Files:**

- Create: tests/test_ultra_article.py
- Create: tests/test_ultra_semantic_coverage.py
- Create: tests/test_ultra_article_independence.py
- Create: tests/fixtures/ultra-runtime/article-packets/
- Create: skills/crossframe-ultra/scripts/ultra_runtime/article.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/coverage.py
- Create: skills/crossframe-ultra/templates/ultra-article-output.md
- Create: skills/crossframe-ultra/templates/ultra-output-plan-output.md
- Create: skills/crossframe-ultra/templates/ultra-semantic-coverage-output.md
- Create: skills/crossframe-ultra/templates/ultra-article-review-output.md
- Create: skills/crossframe-ultra/references/ultra-house-voice.md

- [ ] **Step 1: Write article structure and anti-stuffing RED tests**

The primary article has ten continuous sections:

~~~python
REQUIRED_READER_SECTIONS = (
    "主判断、范围和置信度",
    "用户观点的最强重建",
    "事实、证据、来源关系和未知项",
    "立体多圈层联合状态",
    "机制、真实通道和跨圈层级联",
    "竞争解释与排序",
    "一阶、二阶、三阶推演",
    "每阶简单基线、增量和停止理由",
    "事实、预测、价值、责任、授权裁决",
    "行动、不行动、切换和反转条件",
)
~~~

The same file then contains five reader appendices:

~~~python
REQUIRED_READER_APPENDICES = (
    "圈层—角色—尺度映射",
    "分支、合并、剪枝、残差和停止点",
    "预测、时间窗、指标和解析条件",
    "概念、证据和来源锚点",
    "未知项与框架缺口候选",
)
~~~

Reject:

- headings with empty or repeated boilerplate bodies;
- JSON/schema dumps in reader prose;
- internal field names used instead of explanation;
- a verdict only present in the dossier;
- a source/claim/branch that affects ranking but is absent from the article;
- concept-name stuffing without a concrete role;
- an appendix referenced but not present in the same file;
- truncation marker, continuation promise, or “篇幅所限” in a complete article;
- official filename before U12 pass.

Also assert that no schema, protocol or validator defines a maximum article word/character count. Resource limits govern tools, branches, retries and packet completion, not prose length.

- [ ] **Step 2: Write frozen-packet assembly tests**

Each chapter packet contains packet_id, section_id, ordinal, dependency hashes, semantic unit IDs, source refs, exact UTF-8 prose and prose_sha256. Assembly sorts by the frozen output plan, rejects missing/duplicate packets and stale dependencies, concatenates with one canonical blank-line policy, and records the assembled hash.

~~~python
def test_packet_assembly_is_deterministic(tmp_path):
    first = assemble_article(plan, packets, tmp_path / "first.partial.md")
    second = assemble_article(plan, reversed(packets), tmp_path / "second.partial.md")
    assert first.article_sha256 == second.article_sha256
    assert first.article_text == second.article_text
~~~

- [ ] **Step 3: Write semantic coverage and deletion tests**

Every substantive unit marked applied, retained, unresolved, used in reasoning or promised to the reader must map to an exact section ID and a normalized prose excerpt that occurs in the assembled article. Required unit kinds are claim, evidence, unknown, circle relation, scale transform, translation loss, mechanism, branch, residual, forecast, verdict, action and reversal condition.

Task 11 completion must construct sealed U10 output-plan and U11 semantic-coverage/article-review artifacts and validate them through the W4-0 public schemas under external upstream authority. Dataclass-only or plain-mapping validation is insufficient. Tests cover both controlled incomplete/fail records and the complete non-publishing precheck; only U12 may authorize the official filename.

The deletion test copies only the article to a clean temporary directory. A deterministic recovery fixture and a fresh-context blind-reader evaluator must recover:

~~~python
BLIND_READER_FIELDS = (
    "main_verdict",
    "confidence",
    "steelmanned_user_position",
    "decisive_evidence",
    "unknowns",
    "circle_relations",
    "mechanisms",
    "strongest_rival",
    "order_1",
    "order_2",
    "order_3",
    "five_verdicts",
    "action",
    "residuals",
    "reversal_conditions",
)
~~~

- [ ] **Step 4: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_article.py tests/test_ultra_semantic_coverage.py tests/test_ultra_article_independence.py
~~~

- [ ] **Step 5: Implement packet assembly and article review**

Expose:

~~~python
@dataclass(frozen=True, slots=True)
class AssembledArticle:
    article_text: str
    article_sha256: str
    packet_ids: tuple[str, ...]
    semantic_unit_ids: tuple[str, ...]

def assemble_article(
    output_plan: Mapping[str, object],
    packets: Sequence[Mapping[str, object]],
    partial_path: Path,
) -> AssembledArticle:
    ordered = order_and_validate_packets(output_plan, packets)
    text = "\n\n".join(packet["prose"].strip() for packet in ordered).rstrip() + "\n"
    atomic_write_bytes(partial_path, text.encode("utf-8"))
    return AssembledArticle(
        article_text=text,
        article_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        packet_ids=tuple(packet["packet_id"] for packet in ordered),
        semantic_unit_ids=tuple(
            unit_id
            for packet in ordered
            for unit_id in packet["semantic_unit_ids"]
        ),
    )
~~~

coverage.py validates exact excerpt existence and normalized occurrence order, not just headings or markers. Article review penalizes repeated paragraphs, template language, jargon before plain explanation, unresolved pronouns, unsupported certainty and any dependence on files outside the article.

- [ ] **Step 6: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_article.py tests/test_ultra_semantic_coverage.py tests/test_ultra_article_independence.py
~~~

- [ ] **Step 7: Root review and commit**

~~~powershell
git commit -m "feat: add complete ultra article contract"
~~~

## Task 12: Add checkpoints, recovery, independent validation, and bounded repair

**Owner:** Worker B

**Depends on:** Tasks 5–11, including the integrated W5-0 -> Task 10A -> Task 9 -> Task 10B chain

**Files:**

- Create: tests/test_ultra_recovery.py
- Create: tests/test_ultra_validation.py
- Create: tests/test_ultra_repair.py
- Create: tests/test_ultra_tamper_resistance.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/recovery.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/artifacts.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/validation.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/repair.py
- Create: skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py
- Create: skills/crossframe-ultra/scripts/build_crossframe_ultra_repair_plan.py
- Create: scripts/check_crossframe_ultra_artifacts.py
- Create: scripts/build_crossframe_ultra_repair_plan.py

- [ ] **Step 1: Write interruption and compatibility RED tests**

Interrupt after every U0–U12 phase and after every article packet. Recovery must resume only at the last full hash boundary. A half-written file is discarded from active state but preserved under validation/attempts or recovery/quarantine.

Test exact outcomes:

| Condition | Outcome |
|---|---|
| exact versions and valid checkpoint | resume |
| runtime/validator mismatch | read-only |
| known migration path | fork-required |
| changed evidence cutoff | fork-required |
| changed input file bytes | fork-required |
| corrupt phase hash | reject |
| user cancel | cancelled; no new tools |

- [ ] **Step 2: Write validator tamper RED tests**

Reject a stale report, edited overall_status, copied manifest from another run, marker stuffing, empty rival, fake read ledger, source hash mismatch, article hash mismatch, coverage excerpt not found, delivery file published before validation, simulated-as-fact, flattened world volume, lost lineage inheritance, writes outside root, secret in log, and repair plan that resets an earlier phase than necessary.

- [ ] **Step 3: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_recovery.py tests/test_ultra_validation.py tests/test_ultra_repair.py tests/test_ultra_tamper_resistance.py
~~~

- [ ] **Step 4: Implement immutable checkpoints**

~~~python
@dataclass(frozen=True, slots=True)
class Checkpoint:
    run_id: str
    phase_id: str
    phase_event_sha256: str
    artifact_hashes: Mapping[str, str]
    evidence_cutoff: str
    version_binding: Mapping[str, object]
    created_at: str

def select_resume_checkpoint(
    checkpoints: Sequence[Checkpoint],
    current_binding: Mapping[str, object],
) -> Checkpoint:
    compatible = [
        checkpoint
        for checkpoint in checkpoints
        if verify_checkpoint(checkpoint)
        and resolve_compatibility(checkpoint.version_binding, current_binding) == "resume"
    ]
    if not compatible:
        raise NoCompatibleCheckpointError()
    return max(compatible, key=lambda item: PHASES.index(item.phase_id))
~~~

Cancel writes a final status event and prevents new phase/tool dispatch. Fork copies immutable input references and selected artifacts by hash, assigns a new run ID, records the migration ledger, and never modifies the parent.

- [ ] **Step 5: Implement fresh validation and bounded repair**

The validator loads artifacts from disk after authoring completes; it cannot accept in-memory objects from materialization as proof. It writes validation/attempts/<attempt-id>/ultra-validator-report.json, verifies that report, then atomically updates validation/current.

Each failure has:

~~~json
{
  "error_code": "ULTRA-COVERAGE-MISSING",
  "artifact": "delivery/article.partial.md",
  "affected_phase": "U10",
  "downstream_reset": ["U10", "U11", "U12"],
  "retryable": true,
  "repair_action": "regenerate_missing_semantic_unit_packet"
}
~~~

The error example becomes a real fixture. repair.py groups failures by earliest affected phase, preserves upstream hashes, and refuses a fourth repair attempt. Repeated failure changes status to needs_attention.

- [ ] **Step 6: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_recovery.py tests/test_ultra_validation.py tests/test_ultra_repair.py tests/test_ultra_tamper_resistance.py
python -m py_compile skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py skills/crossframe-ultra/scripts/build_crossframe_ultra_repair_plan.py scripts/check_crossframe_ultra_artifacts.py scripts/build_crossframe_ultra_repair_plan.py
~~~

- [ ] **Step 7: Root review and commit**

~~~powershell
git commit -m "feat: add ultra validation and recovery"
~~~

## Task 13: Materialize U4–U12, publish delivery, and expose the fixed-root CLI

**Owner:** Worker C

**Depends on:** Tasks 5–12, including the integrated W5-0 -> Task 10A -> Task 9 -> Task 10B chain

**Files:**

- Create: tests/test_ultra_materialization.py
- Create: tests/test_ultra_cli.py
- Create: tests/test_ultra_delivery.py
- Create: tests/test_ultra_end_to_end_fixture.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/materialization.py
- Create: skills/crossframe-ultra/scripts/ultra_runtime/deliverables.py
- Create: skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py
- Create: scripts/crossframe_ultra_runtime.py
- Create: skills/crossframe-ultra/templates/ultra-run-status-output.md
- Create: skills/crossframe-ultra/templates/ultra-world-volume-output.md
- Create: skills/crossframe-ultra/templates/ultra-transformation-ledger-output.md
- Create: skills/crossframe-ultra/templates/ultra-concept-disposition-output.md
- Create: skills/crossframe-ultra/templates/ultra-claim-mechanism-output.md
- Create: skills/crossframe-ultra/templates/ultra-recursive-state-output.md
- Create: skills/crossframe-ultra/templates/ultra-recursive-lineage-output.md
- Create: skills/crossframe-ultra/templates/ultra-order-evaluation-output.md
- Create: skills/crossframe-ultra/templates/ultra-retrieval-output.md
- Create: skills/crossframe-ultra/templates/ultra-red-team-output.md
- Create: skills/crossframe-ultra/templates/ultra-verdict-output.md
- Create: skills/crossframe-ultra/templates/ultra-action-ranking-output.md
- Create: skills/crossframe-ultra/templates/ultra-forecast-output.md
- Create: skills/crossframe-ultra/templates/ultra-framework-gap-output.md
- Create: skills/crossframe-ultra/templates/ultra-dossier-output.md
- Create: skills/crossframe-ultra/templates/ultra-artifact-index-output.md
- Create: skills/crossframe-ultra/templates/ultra-validator-report-output.md
- Create: skills/crossframe-ultra/templates/ultra-repair-plan-output.md

- [ ] **Step 1: Write CLI RED tests**

The CLI commands are:

~~~text
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
~~~

Assert help contains none of:

~~~python
FORBIDDEN_CLI_OPTIONS = (
    "--run-dir",
    "--authoring-dir",
    "--output-root",
    "--destination",
    "--fallback",
)
~~~

start copies request bytes into the new run's input directory, records its hash, and never writes the request into an index or path name. --request-stdin prevents prompt text from entering process arguments.

- [ ] **Step 2: Write materialization RED tests**

prepare creates model-owned authoring slots only inside work/authoring and deterministic control files inside artifacts. materialize:

~~~text
work/authoring/U01-read-events.jsonl
work/authoring/U02-retrieval-ledger.json
work/authoring/U03-evidence-ledger.json
work/authoring/U04-world-volume.json
work/authoring/U05-transformation-ledger.json
work/authoring/U05-concept-disposition.json
work/authoring/U06-claim-mechanism-graph.json
work/authoring/U07-recursive-states/<node-id>.json
work/authoring/U07-recursive-lineage.json
work/authoring/U08-order-evaluation.json
work/authoring/U08-red-team-report.json
work/authoring/U09-verdict.json
work/authoring/U09-action-ranking.json
work/authoring/U09-forecast-ledger.json
work/authoring/U10-framework-gap-ledger.json
work/authoring/U10-output-plan.json
work/authoring/U11-semantic-coverage.json
work/authoring/article/packets/<packet-id>.md
work/authoring/U11-article-review.json
work/authoring/完整推演档案.md
~~~

1. validates source and the frozen upstream-artifact DAG, including recursive state before lineage, order evaluation before red-team, and verdict before action/forecast;
2. validates every model-authored semantic artifact;
3. assembles the partial article;
4. builds the complete dossier and artifact index;
5. writes a staging manifest;
6. invokes a fresh validator from disk;
7. on pass, atomically promotes the article to delivery/CrossFrame-Ultra-完整文章.md;
8. writes delivery/完整推演档案.md and delivery/工件索引.md;
9. marks complete and updates indexes.

Initial materialization seals immutable forecast originals and does not create a resolution. After an outcome exists, the existing Task 10B forecast behavior may append a separately validated forecast-resolution event; it never reopens or rewrites the U9 forecast ledger.

On failure, the official article filename must not exist.

- [ ] **Step 3: Write a full fixture run**

The fixture uses a closed-material multi-parent organization case. It must exercise all U0–U12 phases, two real channels, asynchronous clocks, order-2 reversal, order-3 lock-in, low-confidence rival, five verdicts, action ranking, article packets, semantic coverage, independent validation and official publication under an injected unit-test root.

- [ ] **Step 4: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_materialization.py tests/test_ultra_cli.py tests/test_ultra_delivery.py tests/test_ultra_end_to_end_fixture.py
~~~

- [ ] **Step 5: Implement the production boundary**

Model-owned files are limited to the authoring slots returned by prepare. Runtime-owned identity, version, hash, phase, manifest, status, index and delivery fields are overwritten from verified control state, never trusted from model files.

materialize acquires the run lease, recovers an interrupted publish transaction, revalidates the U3 evidence head by CAS, writes to run-local staging, runs the fresh checker, and promotes with durable backup/rollback. A post-publish validation failure restores the previous complete bytes.

- [ ] **Step 6: Implement final-chat projection**

The only chat projection is:

~~~json
{
  "run_status": "complete",
  "center_judgment_summary": "当前最可能是组织激励与照护约束共同导致延期，而非单纯执行力不足。",
  "key_reversal_conditions": ["独立记录显示资源与约束均充足，且延期只随个人可控执行偏差变化。"],
  "article_path": "E:\\世界模型\\output\\crossframe-ultra\\runs\\2026\\08\\20260802T000000Z-0123456789ab\\delivery\\CrossFrame-Ultra-完整文章.md",
  "run_path": "E:\\世界模型\\output\\crossframe-ultra\\runs\\2026\\08\\20260802T000000Z-0123456789ab",
  "continuation_entry": null
}
~~~

Paths must be absolute and derived from the validated layout. The runtime may not paraphrase the locked judgment while constructing final-chat.json.

- [ ] **Step 7: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_materialization.py tests/test_ultra_cli.py tests/test_ultra_delivery.py tests/test_ultra_end_to_end_fixture.py
python -m py_compile skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py scripts/crossframe_ultra_runtime.py
~~~

- [ ] **Step 8: Root review and commit**

~~~powershell
git commit -m "feat: materialize complete ultra runs"
~~~

## Task 14: Author the skill, protocols, templates, and explicit trigger

**Owner:** Worker A

**Depends on:** Tasks 3–13

**Files:**

- Create: tests/test_ultra_skill_contract.py
- Create: tests/test_ultra_protocol_assets.py
- Create: tests/test_ultra_release_manifest.py
- Create: skills/crossframe-ultra/SKILL.md
- Create: skills/crossframe-ultra/agents/openai.yaml
- Create: skills/crossframe-ultra/evals/crossframe-ultra-smoke-tests.md
- Create: all eight protocol files listed in the file map
- Create: skills/crossframe-ultra/references/runtime-routing-map.md
- Create: skills/crossframe-ultra/references/retrieval-policy.md
- Create: skills/crossframe-ultra/references/release-manifest.json
- Create: skills/crossframe-ultra/scripts/build_crossframe_ultra_release_manifest.py
- Create: scripts/build_crossframe_ultra_release_manifest.py

- [ ] **Step 1: Read skill-authoring instructions at execution time**

The root agent, not a delegated worker, reads these files completely before assigning this task:

~~~text
C:\Users\cangm\.codex\skills\.system\skill-creator\SKILL.md
C:\Users\cangm\.codex\skills\writing-skills\SKILL.md
~~~

If skill-creator requires a scaffold command, run it once against skills/crossframe-ultra before the worker writes authored content. Remove generated examples and placeholders before proceeding.

- [ ] **Step 2: Write skill-contract RED tests**

Require exact frontmatter name crossframe-ultra and exactly four accepted forms:

~~~python
EXACT_ULTRA_FORMS = (
    "crossframe-ultra",
    "CrossFrame Ultra",
    "$crossframe-ultra",
    "/crossframe-ultra",
)
~~~

Require allow_implicit_invocation: false. Reject generic “最大化”“最完整”“Ultra 分析” near-misses, suite auto-upgrade, review chaining, fallback to Max/ProMax, v8.0 source, arbitrary output flags, theory self-amendment and a final answer before U12.

- [ ] **Step 3: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_skill_contract.py tests/test_ultra_protocol_assets.py tests/test_ultra_release_manifest.py
~~~

- [ ] **Step 4: Write SKILL.md as a thin execution controller**

SKILL.md must specify:

- exact activation and no implicit invocation;
- v8.2 promoted snapshot as the only theory authority;
- fixed production/test roots and no fallback;
- complete U0–U12 order;
- mandatory full-registry disposition with applied, tested-rejected, not-applicable or unknown-pending;
- all structured authoring artifacts;
- one official complete article;
- exact CLI commands without arbitrary directories;
- fresh validation and repair;
- final-chat absolute article/run paths;
- framework-gap candidates cannot affect the current run.

It must not duplicate the full v8.2 source or hide theory additions in “house policy.”

- [ ] **Step 5: Write protocols by responsibility**

Each protocol names inputs, outputs, dependencies, stop/failure conditions and corresponding validator. The judgment protocol states that low evidence reduces confidence but does not cancel best-current ranking. The article protocol states that there is no word cap and no completion before blind-reader recovery. The safety protocol states fixed-root failure closes the run.

- [ ] **Step 6: Write metadata**

~~~yaml
interface:
  display_name: "CrossFrame Ultra"
  short_description: "Explicit-only v8.2 world-volume inference with hard judgments."
  default_prompt: "Use $crossframe-ultra to run the complete v8.2 world-volume workflow and publish one independently readable Chinese article."

policy:
  allow_implicit_invocation: false
~~~

Generate release-manifest.json only after all canonical Ultra files in this task exist. Its skill-tree hash covers every file under skills/crossframe-ultra except release-manifest.json itself, declared lock files and cache directories; the exclusion set is fixed in the manifest schema. Recompute it whenever a later review changes the canonical tree, and require the validator to reject stale hashes.

~~~powershell
python scripts/build_crossframe_ultra_release_manifest.py --repo . --write
python -B -m pytest -q tests/test_ultra_release_manifest.py
~~~

- [ ] **Step 7: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_skill_contract.py tests/test_ultra_protocol_assets.py tests/test_ultra_release_manifest.py
~~~

- [ ] **Step 8: Root review and commit**

~~~powershell
git commit -m "feat: add crossframe ultra skill surface"
~~~

## Task 15: Integrate routing, mirrors, installers, repository docs, package, and CI

**Owner:** Worker C

**Depends on:** Task 14

**Files:**

- Create: tests/test_ultra_repository_integration.py
- Create: tests/test_ultra_installers.py
- Create: .claude/commands/crossframe-ultra.md
- Generate: .claude/skills/crossframe-ultra/
- Modify: scripts/sync_skill_mirrors.py
- Modify: scripts/install-codex.ps1
- Modify: scripts/install-codex.sh
- Modify: scripts/check_crossframe_skill_integrity.py
- Modify: tests/test_mirror_integrity.py
- Modify: tests/test_package_crossframe_skill.py
- Modify: .github/workflows/verify.yml
- Modify: AGENTS.md
- Modify: CONVENTIONS.md
- Modify: INTERFACES.md
- Modify: README.md
- Modify: CLAUDE.md
- Modify: GEMINI.md
- Modify: .github/copilot-instructions.md
- Modify: llms.txt
- Modify: site/index.html only if the existing skill catalog is rendered there

- [ ] **Step 1: Make Task 1's final invariants pass without weakening preservation**

Final tests require 17 unique skills and exact Ultra mirror equality while continuing to verify the frozen Max/ProMax surfaces byte-for-byte:

~~~python
def test_inventory_contains_seventeen_skills():
    assert len(CROSSFRAME_SKILLS) == 17
    assert len(set(CROSSFRAME_SKILLS)) == 17
    assert "crossframe-ultra" in CROSSFRAME_SKILLS

def test_ultra_mirror_is_generated_from_canonical():
    assert same_tree(
        ROOT / "skills/crossframe-ultra",
        ROOT / ".claude/skills/crossframe-ultra",
    )
~~~

- [ ] **Step 2: Write exact routing RED tests**

The repository routing contract is:

| User text | Result |
|---|---|
| exact Ultra name only | crossframe-ultra |
| generic maximum/deep/full request | existing Max behavior |
| ProMax + Max | existing ProMax-over-Max behavior |
| Ultra + another runtime with explicit comparison | run each independently |
| Ultra + another runtime without explicit comparison | stop and ask which runtime |
| suite request without exact Ultra name | never Ultra |
| Ultra runtime failure | no fallback |

Tests must inspect only new/allowed routing blocks. Frozen Max and ProMax files remain unchanged.

- [ ] **Step 3: Write installer and package RED tests**

Use tests/fixtures/fake_skill_installer.py. Test PowerShell and Bash installation into a temporary destination, tree equality for all 17 skills, restoration of a pre-existing crossframe-ultra directory after simulated installer failure, and package inclusion of:

~~~python
ULTRA_PACKAGE_REQUIRED = {
    ".claude/commands/crossframe-ultra.md",
    ".claude/skills/crossframe-ultra/SKILL.md",
    "skills/crossframe-ultra/SKILL.md",
    "skills/crossframe-ultra/references/source-manifest.json",
    "skills/crossframe-ultra/references/v8.2-full-source/00-index.md",
    "skills/crossframe-ultra/schemas/ultra-run-contract.schema.json",
    "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py",
    "skills/crossframe-ultra/templates/ultra-article-output.md",
}
~~~

- [ ] **Step 4: Observe RED**

~~~powershell
python -B -m pytest -q tests/test_ultra_repository_integration.py tests/test_ultra_installers.py tests/test_mirror_integrity.py tests/test_package_crossframe_skill.py
~~~

- [ ] **Step 5: Update inventory, integrity, and thin adapters**

Append crossframe-ultra to CROSSFRAME_SKILLS and CURRENT_CROSSFRAME_SKILLS; do not add it to legacy, claim-ledger bridge or sibling-routing lists. Add ULTRA_EXACT_TRIGGER_NAMES and check_crossframe_ultra_skill to the integrity checker. The checker verifies required files, exact trigger policy, v8.2 hashes, fixed-root markers, no fallback and no ProMax import.

.claude/commands/crossframe-ultra.md must be a thin command: read the canonical SKILL.md, pass the user's request, use the fixed runtime, and never copy the protocol or offer fallback.

- [ ] **Step 6: Update installation and mirror generation**

Reuse sync_skill_mirrors.py and both existing installers. Installation remains canonical source to staging to tree-hash verification to atomic replace/rollback. Generate the Claude mirror with:

~~~powershell
python scripts/sync_skill_mirrors.py --repo .
python scripts/sync_skill_mirrors.py --repo . --check
~~~

Do not hand-edit generated .claude/skills/crossframe-ultra files.

- [ ] **Step 7: Add an isolated CI job**

Add ultra-contracts-and-artifacts without changing the raw text of existing Max/ProMax jobs. It installs jsonschema, pytest and PyYAML, then runs:

~~~bash
python scripts/check_crossframe_ultra_v82_source.py --repo .
python scripts/check_crossframe_ultra_v82_knowledge.py --repo .
for schema in skills/crossframe-ultra/schemas/*.json; do
  python -m json.tool "$schema" > /dev/null
done
python -B -m pytest -q tests/test_ultra_*.py
~~~

- [ ] **Step 8: Update public documentation minimally**

Document Ultra as explicit-only v8.2 reference runtime; state that ProMax remains v8.0; show the fixed production/test roots and official article path; explain that Ultra does not self-evolve theory and that prediction-mechanism validation is distinct from forward accuracy validation. Keep adapters thin and do not paste the runtime protocol.

- [ ] **Step 9: Run GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_repository_integration.py tests/test_ultra_installers.py tests/test_mirror_integrity.py tests/test_package_crossframe_skill.py
python scripts/check_crossframe_skill_integrity.py --repo .
python scripts/sync_skill_mirrors.py --repo . --check
~~~

- [ ] **Step 10: Root review and commit**

Verify the preservation manifest before staging. Commit:

~~~powershell
git commit -m "feat: integrate crossframe ultra"
~~~

## Task 16: Run adversarial saturation, the 24-case ProMax benchmark, and prediction harness

**Owner:** Root orchestrator with three isolated evaluators

**Depends on:** Tasks 1–15

**Files:**

- Create: tests/test_ultra_adversarial.py
- Create: tests/test_ultra_benchmark_contract.py
- Create: tests/test_ultra_prediction_evaluation.py
- Create: tests/evals/ultra-vs-promax/scenarios.json
- Create: tests/evals/ultra-vs-promax/rubric.json
- Create: tests/evals/ultra-vs-promax/pairing-manifest.json
- Create: tests/evals/ultra-vs-promax/build_results.py
- Create: tests/evals/ultra-vs-promax/README.md
- Create: tests/evals/ultra-vs-promax/raw/
- Create: tests/evals/ultra-vs-promax/results.json
- Create: tests/evals/ultra-forward/README.md
- Create: tests/evals/ultra-forward/forecast-registry.jsonl
- Create: tests/evals/ultra-forward/resolutions.jsonl

- [ ] **Step 1: Freeze all 24 benchmark cases**

Use these IDs, categories, exact questions, and decisive structural pressure:

| ID | Category | Exact question | Decisive pressure |
|---|---|---|---|
| P01 | public | 某市计划把公共服务资格初筛交给统一 AI 系统。当前最可能改善什么、伤害什么，三阶会走向哪里？ | jurisdiction, low-visibility positions |
| P02 | public | 平台把“自愿认证”改成默认认证但允许退出。这是否仍是自愿，最可能如何演化？ | authorization, exit cost |
| P03 | public | 所有媒体都报道同一政策成功，所以独立证据已经很多。这个结论对吗？ | shared-source pollution |
| P04 | public | 危机舆情两天转向、组织季度调整、法规一年后生效。现在该怎么判断？ | asynchronous clocks |
| O01 | organization | 一名员工公开离职，公司短期声誉回升。请推演一阶、二阶和三阶。 | order-2 reversal, lock-in |
| O02 | organization | 项目延期，管理层认为原因只是执行力不足。当前最可能机制是什么？ | false premise, rival mechanism |
| O03 | organization | 某领导在一次冲突中强硬，因此人格一定专断。这个判断成立吗？ | actor-role/personality separation |
| O04 | organization | 重组让同一人同时属于产品线、地区线与专业委员会。责任如何判断？ | multi-parent nesting |
| B01 | business-tech | 企业引入生成式 AI 后单项效率提升。整体产能是否必然提升？ | local gain vs system bottleneck |
| B02 | business-tech | 新协议技术更优但生态采用缓慢。最可能的三阶路径是什么？ | network/institution clocks |
| B03 | business-tech | 竞争者降价，我们是否应立即跟进？ | action set, no-action comparison |
| B04 | business-tech | 数据泄露尚未证实影响用户，但内部日志异常。现在最合理判断和行动是什么？ | sparse evidence, responsibility |
| L01 | personal | 我想换工作，但只有收入、照护责任和行业机会三类有限信息。请明确建议。 | low-confidence hard judgment |
| L02 | personal | 伴侣一次失约是否证明关系不值得继续？ | event vs stable trait |
| L03 | personal | 搬家对职业有利、对照护不利、对伴侣中性。怎样排序？ | cross-circle distribution |
| L04 | personal | 家庭照护中“大家都同意”但无法退出者没有表达。授权成立吗？ | low-power authorization |
| H01 | history | 只使用冻结到改革发生前的材料，判断改革最可能成功还是失败。 | historical time box |
| H02 | history | 如果关键中介机构不存在，原事件最可能怎样变化？ | counterfactual and channel |
| H03 | history | 三份史料实际都转述同一档案，能否算三份独立支持？ | lineage deduplication |
| H04 | history | 一项临时制度为何可能在第三阶永久化？ | institutional lock-in |
| C01 | closed-material | 两份备忘录互相矛盾；只用材料内证据给出当前最可能解释。 | closed evidence court |
| C02 | closed-material | 对象同时被成员、合同和资源会计三种关系包含，请建立非树结构。 | multi-basis containment |
| C03 | closed-material | 外部事件与目标共享环境，但材料没有作用通道。目标状态能否更新？ | no-channel no-update |
| C04 | closed-material | “这个方案更好”没有比较对象和评价标准。请判断该命题。 | proposition non-decidability |

Each case directory contains prompt.md, evidence-cutoff.json, materials/, expected-pressure.json and privacy-policy.json. Public/current cases use a frozen retrieval bundle created at one cutoff; closed cases prohibit retrieval. Do not leak outcomes into historical case material.

- [ ] **Step 2: Write benchmark contract tests**

Require 24 unique cases, four in each category, eight v8.2-decisive cases, identical model/tool/evidence bindings for each ProMax/Ultra pair, randomized A/B labels, three independent graders, complete raw output preservation and score derivation from raw grades.

The rubric is:

~~~json
{
  "truth_evidence_unknowns": 20,
  "circle_scale_translation_closure": 15,
  "mechanism_causal_chain": 10,
  "three_order_recursion": 15,
  "judgment_rival_reversal": 15,
  "forecast_resolvability": 10,
  "completeness_readability_independence": 15
}
~~~

Graders penalize repetition and unsupported detail; they do not reward word count. Any severe factual error, simulation-as-fact, or unsupported central verdict is an automatic case loss.

- [ ] **Step 3: Run focused contract RED/GREEN**

~~~powershell
python -B -m pytest -q tests/test_ultra_adversarial.py tests/test_ultra_benchmark_contract.py tests/test_ultra_prediction_evaluation.py
~~~

The tests begin RED before scenario/rubric/build assets exist and finish GREEN before expensive model runs.

- [ ] **Step 4: Produce matched ProMax and Ultra outputs**

For every case, dispatch product runs with model gpt-5.6-sol and reasoning max. Freeze model identifier, tool availability, evidence cutoff, source bundle hashes and request bytes in pairing-manifest.json. ProMax uses its unchanged v8.0 runtime; Ultra uses its v8.2 runtime. Do not retrofit v8.2 into ProMax.

Save raw outputs under:

~~~text
tests/evals/ultra-vs-promax/raw/<case-id>/promax/
tests/evals/ultra-vs-promax/raw/<case-id>/ultra/
~~~

- [ ] **Step 5: Dispatch three blind graders**

Each grader uses a fresh context, model gpt-5.6-sol and reasoning max. It sees only randomized Article A, Article B, case materials and rubric. It does not see product names, internal JSON, directory names or prior grades.

build_results.py verifies raw hashes, unmasks labels after grading, calculates majority case winner, dimension medians, category medians, decisive-case result and automatic failures. It refuses hand-authored aggregate numbers.

- [ ] **Step 6: Enforce release thresholds**

All must pass:

~~~python
assert ultra_case_wins >= 18
assert median_ultra_score - median_promax_score >= 10
assert all(category_ultra_median >= category_promax_median for category in CATEGORIES)
assert ultra_decisive_case_wins >= 7
assert ultra_simulation_as_fact_count == 0
assert ultra_severe_factual_failure_count == 0
~~~

If a threshold fails, set release status needs_attention, inspect losing dimensions, add a source-faithful regression fixture, repair only the responsible phase, and rerun affected cases plus the complete deterministic suite. Do not lower thresholds.

- [ ] **Step 7: Establish prediction validation states**

The release may set mechanism-validated after deterministic forecast tests and historically-backtested after leakage-audited historical replays. It must not set forward-validated.

Forward validation requires at least 30 independent resolved cases spanning at least five domains and three time horizons. Resolutions append to immutable originals. A later release may claim real predictive superiority only when paired, case-clustered resampling shows stable positive advantage in direction, time-window, declared indicator and admissible probability scoring.

- [ ] **Step 8: Root review and commit**

Commit deterministic benchmark assets and reproducible raw/results files only after verifying that no secrets, private materials or unlicensed large source copies are present.

~~~powershell
git commit -m "test: validate ultra against promax"
~~~

## Task 17: Full verification, independent reviews, installation, and handoff

**Owner:** Root orchestrator

**Depends on:** Tasks 1–16

**Files:**

- Modify only files required by review findings
- Create no new design or theory file
- Install generated canonical tree to C:\Users\cangm\.codex\skills\crossframe-ultra

- [ ] **Step 1: Run all focused Ultra gates**

~~~powershell
python scripts/check_crossframe_ultra_v82_source.py --repo . --source-docx "E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx"
python scripts/check_crossframe_ultra_v82_knowledge.py --repo .
python -B -m pytest -q tests/test_ultra_*.py
python scripts/check_crossframe_skill_integrity.py --repo .
python scripts/sync_skill_mirrors.py --repo . --check
~~~

Expected: every command succeeds, source checker reports both exact hashes, and no test is xfailed to hide a required behavior.

- [ ] **Step 2: Prove legacy preservation and full regression**

~~~powershell
python -B -m pytest -q tests/test_max_*.py tests/test_promax_*.py tests/test_mirror_integrity.py tests/test_package_crossframe_skill.py
python -B -m unittest discover -s tests -p "test_*.py" -v
git diff --check
~~~

Expected: all existing tests remain green and the Task 1 preservation manifest reports zero changed protected Max/ProMax files.

- [ ] **Step 3: Run syntax, schema, package, and installer smokes**

~~~powershell
python -m py_compile scripts/*.py
Get-ChildItem skills/crossframe-ultra -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem skills/crossframe-ultra/schemas -Filter *.json | ForEach-Object { python -m json.tool $_.FullName > $null }
python scripts/package_crossframe_skill.py --repo . --version ultra-rc
python -B -m pytest -q tests/test_ultra_installers.py tests/test_package_crossframe_skill.py
~~~

- [ ] **Step 4: Dispatch three independent max-effort reviews**

Use three workers concurrently, each gpt-5.6-sol with reasoning max and no shared free-form context:

1. **Source fidelity reviewer:** compare promoted source/registry/contracts/routes against the v8.2 DOCX; search for v8.0 contamination and theory invention.
2. **Runtime safety reviewer:** attack fixed roots, reparse points, concurrent writers, stale locks, interruption, version mismatch, privacy, hostile inputs and validator freshness.
3. **Article/product reviewer:** run the deletion test, audit semantic coverage, inspect losing benchmark cases and confirm the main article is complete, readable and decisive.

Each reviewer reports findings with exact file/line, severity, reproduction and required test. The root fixes every blocker and reruns the affected focused suite plus Step 1.

After any canonical-tree change, regenerate references/release-manifest.json, regenerate the Claude mirror, and rerun the source, knowledge, tree-hash and mirror checks before continuing.

- [ ] **Step 5: Run a clean test-root installed-surface smoke**

Before installation, run the canonical runtime in test mode with the closed fixture. Verify all output is under E:\世界模型\output\crossframe-ultra-tests, the official article appears only after U12, START-HERE links resolve, latest-complete points to the completed run and no production index changes.

- [ ] **Step 6: Install through the repository installer**

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-codex.ps1 -Repo "E:\世界模型\skill\crossframe-skill" -DestinationRoot "C:\Users\cangm\.codex\skills"
~~~

After installation, compare tree_hashes for:

~~~text
E:\世界模型\skill\crossframe-skill\skills\crossframe-ultra
C:\Users\cangm\.codex\skills\crossframe-ultra
~~~

They must match exactly after excluding only declared cache/lock files. If installation fails, verify the previous installed tree was restored and do not copy manually.

- [ ] **Step 7: Validate the installed skill**

Run source, knowledge, schema and skill-contract checks against the installed tree or through a temporary repository fixture that treats the installed tree as canonical. Confirm agents/openai.yaml has allow_implicit_invocation: false and no output-root override exists.

- [ ] **Step 8: Final root commit**

Stage only reviewed implementation and generated mirror changes:

~~~powershell
git status --short
git diff --check
git commit -m "feat: ship crossframe ultra"
~~~

If the work is already committed task-by-task and no final diff remains, do not create an empty commit.

- [ ] **Step 9: Completion report**

Report:

- final commit IDs;
- exact source and semantic hashes;
- deterministic test counts and results;
- 24-case benchmark result and threshold status;
- prediction validation state;
- installed tree hash;
- canonical skill path;
- installed skill path;
- production and test output roots;
- any honest non-blocking limitations.

Do not claim forward prediction superiority unless the separate 30-case resolved-forward gate has passed.

## Specification coverage matrix

| Approved design requirement | Implemented and proved by |
|---|---|
| v8.2 is theory authority; gaps cannot self-promote | Tasks 2–4, 10, 14 |
| four-plane authority/runtime/adjudication/audit architecture | Tasks 2–5, 7–13 |
| non-concentric volumetric circle topology | Task 8 |
| full Ω state with local M/Psi, nine axes and five clocks | Tasks 5 and 8 |
| separate scale, relation and translation transformations | Task 8 |
| three-order lineage, branch classes and per-order baselines | Task 9 |
| evidence court, source independence and truth-first judgment | Tasks 7 and 10 |
| five verdict locks plus independent action ranking | Task 10 |
| direction/time-window/indicator/resolution forecasts | Tasks 10 and 16 |
| U0–U12 immutable state machine and post-U3 evidence fork | Tasks 7, 12 and 13 |
| fixed production/test roots and one discoverable run bundle | Tasks 6 and 13 |
| one no-word-cap complete standalone article | Tasks 11, 13 and 14 |
| semantic coverage and blind-reader recovery | Tasks 11 and 16 |
| version split, compatibility and no in-place migration | Tasks 5 and 12 |
| privacy, hostile input, path, concurrency and resource safety | Tasks 6, 7 and 12 |
| exact-only trigger; Max/ProMax/Ultra coexist without fallback | Tasks 14 and 15 |
| root-planned parallel gpt-5.6-sol max implementation | Section 0 and every Owner field |
| deterministic hard gates and ProMax comparative superiority | Tasks 16 and 17 |
| honest separation of prediction mechanism and future accuracy | Tasks 10, 16 and 17 |

## Final acceptance checklist

- [ ] v8.2 raw and semantic identity both pass.
- [ ] 4,631 paragraphs, 122 tables and 20 top divisions are present and exact.
- [ ] Registry, contracts, routes and anchors are closed and source-supported.
- [ ] No v8.0 theory or ProMax runtime import exists inside Ultra.
- [ ] U0–U12 is append-only, version-bound and recoverable.
- [ ] No production CLI accepts an arbitrary output directory.
- [ ] Fixed-root, path escape, reparse, lock, interruption and rollback tests pass.
- [ ] Evidence cutoff and source lineage are immutable after U3.
- [ ] Ω preserves multi-parent topology, local M/Psi, nine-axis scales and asynchronous clocks.
- [ ] No-channel positions do not update and every cross-circle hop is revalidated.
- [ ] Orders 1–3 preserve parent state, unknowns, losses and residuals.
- [ ] Every decidable task has a main judgment, rival, confidence and reversal condition.
- [ ] Fact, prediction, value, responsibility and authorization remain separate.
- [ ] Numeric probability appears only after admissibility/calibration validation.
- [ ] Article semantic coverage is 100% for every substantive applied, retained, unresolved or used unit.
- [ ] The primary article passes the standalone deletion/blind-reader test.
- [ ] The official article filename exists only for a U12-passed run.
- [ ] Production/test roots and indexes remain isolated.
- [ ] Max and ProMax protected surfaces remain unchanged.
- [ ] Exact-name trigger and no-fallback behavior pass.
- [ ] Canonical, mirror, package and installed trees pass hash checks.
- [ ] Ultra wins at least 18/24 benchmark cases, leads by at least 10 median points, has no category regression and wins at least 7/8 v8.2-decisive cases.
- [ ] Prediction status is stated honestly as mechanism-validated, historically-backtested or forward-validated.
- [ ] Three independent final reviews have no blocking findings.
