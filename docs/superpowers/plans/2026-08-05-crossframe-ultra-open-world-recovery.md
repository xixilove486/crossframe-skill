# CrossFrame Ultra Open-World Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user requested continuous implementation followed by one unified review, so do not stop for per-task human approval.

**Goal:** Restore CrossFrame Ultra as an exact-name-only runtime that accepts natural-language questions, performs authorized host retrieval and evidence admission, preserves v8.2 concept fidelity and full inferential expansion, and completes U0–U12 without manual control-file surgery.

**Architecture:** Keep the Python runtime authoritative for identities, hashes, phase state and publication, while adding a persistent host-runtime handshake for capability, source-read, retrieval and semantic-authoring work. Extract fresh U0–U3 orchestration from the oversized materializer into focused `host_handshake.py` and `foundation.py` modules, then reuse the existing state-machine, retrieval, evidence, recovery and validation primitives. Expected host waits return typed progress results; only invalid or unsafe inputs become failures.

**Tech Stack:** Python 3.11+, JSON Schema Draft 2020-12, `jsonschema`, `pytest`, canonical UTF-8 JSON/JSONL, fixed-root Windows and Linux filesystem tests, Markdown skill/protocol assets.

## Global Constraints

- External activation remains exact-name-only: `crossframe-ultra`, `CrossFrame Ultra`, `$crossframe-ultra`, or `/crossframe-ultra`.
- Natural-language request payloads default to `analysis_kind=open-world`; `closed-input` and `pure-logic` require independently verifiable eligibility.
- Framework binding remains `8.2 / v8.2-r1`; raw SHA-256 remains `608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20`; semantic SHA-256 remains `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`.
- Final version binding is runtime `1.1.0`, artifact schema `2`, validator `1.1.0`, article contract `1.1.0`, compiler `1.0.0`.
- Existing completed v1 runs and `/mnt/e/世界模型/output/crossframe-ultra/runs/2026/08/20260805T183749Z-1b63228f680c` remain byte-unchanged and read-only.
- Runtime control fields, status, phase events, checkpoints, leases, manifests and official delivery remain runtime-owned.
- No arbitrary `--run-dir`, `--authoring-dir`, `--output-root`, `--destination` or `--fallback` flags.
- Required retrieval that cannot execute safely fails closed; it never becomes `not-applicable`.
- Expected host or authoring waits are successful progress outcomes, not exceptions, validation failures or `needs_attention`.
- Every production change follows RED → verify RED → GREEN → verify GREEN → commit.
- Implementation proceeds continuously; perform code review, full test gates, mirror synchronization and release audit once all focused changes are complete.

## File and Responsibility Map

- `skills/crossframe-ultra/scripts/ultra_runtime/host_handshake.py`: issue, persist, validate and consume host actions/results.
- `skills/crossframe-ultra/scripts/ultra_runtime/foundation.py`: classify request profiles and advance fresh U0–U3.
- `skills/crossframe-ultra/scripts/ultra_runtime/source_integrity.py`: U1 read-plan and host-read receipt verification.
- `skills/crossframe-ultra/scripts/ultra_runtime/retrieval.py`: persistable U2 authorization/action/result admission.
- `skills/crossframe-ultra/scripts/ultra_runtime/evidence.py`: U3 attribution, source admission and evidence-lineage checks.
- `skills/crossframe-ultra/scripts/ultra_runtime/materialization.py`: U4–U12 orchestration and typed waiting outcomes; no fresh-foundation policy ownership.
- `skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py`: stable CLI projection and `evidence-fork` entry.
- `skills/crossframe-ultra/scripts/ultra_runtime/locks.py`, `recovery.py`, `repair.py`: writer ownership, durable cancel, append-only repair and fork lineage.
- `skills/crossframe-ultra/scripts/ultra_runtime/judgment.py`, `validation.py`, `article.py`, `coverage.py`: evidence support and reader-quality gates.
- `skills/crossframe-ultra/schemas/`: public artifact contracts.
- `skills/crossframe-ultra/SKILL.md`, protocols and routing map: thin host execution instructions.
- `.claude/skills/crossframe-ultra/` and adapter files: generated/thin mirrors only.
- `tests/test_ultra_*.py`: unit, integration, adversarial, compatibility and end-to-end gates.

---

### Task 1: Persistent Host Action and Receipt Authority

**Files:**
- Create: `skills/crossframe-ultra/scripts/ultra_runtime/host_handshake.py`
- Create: `skills/crossframe-ultra/schemas/ultra-host-action.schema.json`
- Create: `skills/crossframe-ultra/schemas/ultra-host-result-receipt.schema.json`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py:25-61`
- Test: `tests/test_ultra_host_handshake.py`
- Test: `tests/test_ultra_schemas.py`

**Interfaces:**
- Produces: `HostActionSeal`, `HostResultSeal`, `issue_host_action(...)`, `load_pending_action(...)`, `accept_host_result(...)`, `complete_host_action(...)`.
- Consumes: `RunLayout`, `current_version_binding()`, canonical JSON helpers and fixed-root descendant checks.

- [ ] **Step 1: Write failing action/receipt tests**

```python
def test_pending_action_round_trip_is_parent_bound_and_replay_safe(run_layout, now):
    action = issue_host_action(
        run_layout,
        action_kind="capability-attestation",
        phase_id="U0",
        parent_event_sha256=None,
        request_sha256="1" * 64,
        payload={"required_capabilities": ["filesystem", "validators"]},
        result_relative_path="work/host/U00-capability-result.json",
        now=now,
    )
    receipt = write_result_for(action, execution_id="host-exec-1")
    accepted = accept_host_result(run_layout, action=action, receipt=receipt)
    assert accepted.action_sha256 == action.action_sha256
    with pytest.raises(HostHandshakeError, match="replay|completed"):
        accept_host_result(run_layout, action=action, receipt=receipt)


@pytest.mark.parametrize("mutation", ["run", "request", "parent", "slot", "hash"])
def test_host_result_cannot_select_or_reseal_its_authority(run_layout, mutation):
    action, receipt = issued_pair(run_layout)
    mutate_and_reseal(receipt, mutation)
    with pytest.raises(HostHandshakeError, match="authority|action|result"):
        accept_host_result(run_layout, action=action, receipt=receipt)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -B -m pytest -q tests/test_ultra_host_handshake.py tests/test_ultra_schemas.py -k 'host_action or host_result'`

Expected: FAIL because the module and schemas do not exist.

- [ ] **Step 3: Implement the closed handshake types and persistence**

```python
HOST_ACTION_KINDS = frozenset(
    {"capability-attestation", "source-read", "retrieval", "evidence-authoring", "subagent"}
)

@dataclass(frozen=True, slots=True)
class HostActionSeal:
    document: dict[str, object]
    action_sha256: str
    result_path: Path

@dataclass(frozen=True, slots=True)
class HostResultSeal:
    document: dict[str, object]
    receipt_sha256: str
    action_sha256: str

def issue_host_action(
    layout: RunLayout,
    *,
    action_kind: str,
    phase_id: str,
    parent_event_sha256: str | None,
    request_sha256: str,
    payload: Mapping[str, object],
    result_relative_path: str,
    now: datetime,
) -> HostActionSeal:
    result_path = layout.run_dir / result_relative_path
    assert_safe_descendant(layout.root, result_path)
    document = {
        "schema_id": "crossframe.ultra.v82.host-action",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "phase_id": phase_id,
        "action_kind": action_kind,
        "parent_event_sha256": parent_event_sha256,
        "request_sha256": request_sha256,
        "result_relative_path": result_relative_path,
        "payload": copy.deepcopy(dict(payload)),
        "issued_at": canonical_utc(now),
    }
    document["action_sha256"] = sha256_bytes(canonical_json_bytes(document))
    validate_instance("ultra-host-action.schema.json", document)
    atomic_write_json(layout.recovery_dir / "pending-action.json", document)
    return HostActionSeal(document, str(document["action_sha256"]), result_path)

def accept_host_result(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    receipt: Mapping[str, object],
) -> HostResultSeal:
    document = copy.deepcopy(dict(receipt))
    validate_instance("ultra-host-result-receipt.schema.json", document)
    if document["action_sha256"] != action.action_sha256:
        raise HostHandshakeError("host result action authority differs")
    if document["run_id"] != action.document["run_id"]:
        raise HostHandshakeError("host result run authority differs")
    supplied = document.pop("receipt_sha256")
    measured = sha256_bytes(canonical_json_bytes(document))
    if supplied != measured:
        raise HostHandshakeError("host result receipt hash differs")
    document["receipt_sha256"] = supplied
    return HostResultSeal(document, str(supplied), action.action_sha256)
```

Persist one canonical `recovery/pending-action.json`; keep submitted and rejected receipts under append-only `recovery/host-results/<action-id>/attempts/`; write an immutable accepted receipt before clearing the pending action. Validate safe fixed paths, exact fields, native JSON scalar types, action hash, parent binding and result-slot identity.

- [ ] **Step 4: Run focused GREEN tests**

Run: `python -B -m pytest -q tests/test_ultra_host_handshake.py tests/test_ultra_schemas.py -k 'host_action or host_result'`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/host_handshake.py skills/crossframe-ultra/schemas/ultra-host-action.schema.json skills/crossframe-ultra/schemas/ultra-host-result-receipt.schema.json skills/crossframe-ultra/scripts/ultra_runtime/schemas.py tests/test_ultra_host_handshake.py tests/test_ultra_schemas.py
git commit -m "feat: add Ultra host handshake authority"
```

### Task 2: Natural-Language Request Profiles and Dynamic U0

**Files:**
- Create: `skills/crossframe-ultra/scripts/ultra_runtime/foundation.py`
- Create: `skills/crossframe-ultra/schemas/ultra-host-capability-attestation.schema.json`
- Create: `skills/crossframe-ultra/schemas/ultra-input-inventory.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-run-contract.schema.json`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/state_machine.py:447-505`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/recovery.py:990-1110`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py:25-61`
- Modify: `skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py:81-88, 221-265`
- Test: `tests/test_ultra_foundation.py`
- Test: `tests/test_ultra_cli.py`
- Test: `tests/test_ultra_state_machine.py`

**Interfaces:**
- Consumes: Task 1 host action/result seals.
- Produces: `RequestProfile`, `FoundationProgress`, `parse_request_profile(...)`, `advance_u0(...)`.

- [ ] **Step 1: Write RED tests for natural language and profile safety**

```python
def test_plain_natural_language_defaults_to_open_world():
    profile = parse_request_profile("AI 会怎样改变就业？\n".encode("utf-8"))
    assert profile.analysis_kind == "open-world"
    assert profile.claim == "AI 会怎样改变就业？"
    assert profile.material_inventory == ()


def test_question_cannot_copy_itself_into_closed_material():
    request = canonical({
        "analysis_kind": "closed-input",
        "claim": "AI 会怎样改变就业？",
        "material": "AI 会怎样改变就业？",
    })
    with pytest.raises(FoundationInputError, match="material universe|same as claim"):
        parse_request_profile(request)


def test_u0_waits_for_host_attestation_instead_of_blocking_plain_text(fresh_run):
    progress = advance_u0(fresh_run.layout, repo=fresh_run.repo, now=fresh_run.now)
    assert progress.outcome == "awaiting-host-action"
    assert progress.pending_action.action_kind == "capability-attestation"


def test_material_files_are_copied_into_a_separate_material_inventory(cli_run, tmp_path):
    source = tmp_path / "private-name.md"
    source.write_text("封闭材料", encoding="utf-8")
    started = cli_run.start("问题", material_files=[source])
    inventory = load_input_inventory(started.layout)
    assert [item["path"] for item in inventory["materials"]] == ["materials/MAT-0001.md"]
    assert all(item["path"] not in {"request.bin", "request-metadata.json"} for item in inventory["materials"])
    assert "private-name" not in canonical_json_bytes(inventory).decode("utf-8")
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_foundation.py tests/test_ultra_cli.py -k 'natural_language or profile or attestation'`

Expected: FAIL because plain text is still rejected and no U0 host action exists.

- [ ] **Step 3: Implement profile parsing and capability attestation**

```python
@dataclass(frozen=True, slots=True)
class RequestProfile:
    analysis_kind: str
    claim: str
    material_inventory: tuple[dict[str, str], ...]
    material_universe_sha256: str | None

@dataclass(frozen=True, slots=True)
class FoundationProgress:
    outcome: str
    phase_store: object | None
    pending_action: HostActionSeal | None
    completed_phase: str | None

def parse_request_profile(request_bytes: bytes) -> RequestProfile:
    text = request_bytes.decode("utf-8")
    stripped = text.strip()
    try:
        candidate = json.loads(stripped)
    except json.JSONDecodeError:
        candidate = None
    if not isinstance(candidate, dict) or candidate.get("analysis_kind") != "closed-input":
        if not stripped:
            raise FoundationInputError("natural-language request is empty")
        return RequestProfile("open-world", stripped, (), None)
    return validate_closed_input_profile(candidate, request_bytes=request_bytes)

def advance_u0(
    layout: RunLayout,
    *,
    repo: Path,
    now: datetime,
) -> FoundationProgress:
    profile = load_request_profile(layout)
    action = load_pending_action(layout)
    if action is None:
        action = issue_capability_action(layout, profile=profile, now=now)
        return FoundationProgress("awaiting-host-action", None, action, None)
    receipt = load_submitted_host_result(layout, action=action)
    if receipt is None:
        return FoundationProgress("awaiting-host-action", None, action, None)
    attestation = validate_host_capability_attestation(receipt, layout=layout, profile=profile)
    phase_store = create_fresh_phase_store(repo, layout, profile=profile, attestation=attestation, now=now)
    complete_and_checkpoint_u0(layout, phase_store, attestation=attestation, now=now)
    return FoundationProgress("advanced", phase_store, None, "U0")
```

Add repeatable read-only `--material-file PATH` input to `start`; runtime copies bytes to generated `input/materials/MAT-NNNN.<safe-ext>` names and seals a separate material inventory. Request and metadata files remain in the all-input snapshot but never count as closed material. Extend the U0 run contract with `analysis_kind` and `capability_attestation_sha256`. The attestation contains separate `requirements` and `measured_availability` matrices, provider/tool identities, sensitivity, retention, outbound permission, evidence cutoff, resource limits, measurement time, proof grade and run/request/version binding. Runtime constructs the run contract; the receipt cannot submit runtime-owned envelope fields. Replace `PhaseStore.__init__(capability_availability=...)` with a validated `capability_attestation: HostCapabilitySeal`; recovery revalidates this disk artifact instead of inferring availability from requirements.

- [ ] **Step 4: Add recovery tests and implement persisted availability restoration**

```python
def test_resume_uses_persisted_measured_availability_not_required_state(u0_checkpoint):
    restored = resume_run(u0_checkpoint.layout, now=u0_checkpoint.later)
    assert restored.phase_store.capability_availability["network"] == "unavailable"
    assert restored.phase_store.run_contract["capabilities"]["network"] == "required"
```

Run: `python -B -m pytest -q tests/test_ultra_foundation.py tests/test_ultra_state_machine.py tests/test_ultra_recovery.py -k 'capability or u0 or profile'`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/foundation.py skills/crossframe-ultra/schemas/ultra-host-capability-attestation.schema.json skills/crossframe-ultra/schemas/ultra-input-inventory.schema.json skills/crossframe-ultra/schemas/ultra-run-contract.schema.json skills/crossframe-ultra/scripts/ultra_runtime/state_machine.py skills/crossframe-ultra/scripts/ultra_runtime/recovery.py skills/crossframe-ultra/scripts/ultra_runtime/schemas.py skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py tests/test_ultra_foundation.py tests/test_ultra_cli.py tests/test_ultra_state_machine.py tests/test_ultra_recovery.py
git commit -m "feat: restore Ultra natural-language U0"
```

### Task 3: U1 Read Plan and Honest Host Read Receipts

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/source_integrity.py:1398-1845`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/foundation.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/recovery.py:772-980`
- Create: `skills/crossframe-ultra/schemas/ultra-read-plan.schema.json`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- Test: `tests/test_ultra_source_read_coverage.py`
- Test: `tests/test_ultra_foundation.py`
- Test: `tests/test_ultra_recovery.py`

**Interfaces:**
- Consumes: sealed U0 and Task 1 `source-read` actions.
- Produces: `validate_host_read_receipt(...)`, persisted `read-plan.json`, runtime-created read events and U1 coverage.

- [ ] **Step 1: Write RED tests proving runtime cannot self-claim reads**

```python
def test_u1_persists_plan_before_requesting_host_reads(fresh_u0):
    progress = advance_foundation(fresh_u0.layout, repo=fresh_u0.repo, now=fresh_u0.now)
    assert progress.pending_action.action_kind == "source-read"
    plan = load_json_object(fresh_u0.layout.recovery_dir / "u1-authority/read-plan.json")
    assert plan["source_unit_count"] == 4_753
    assert not (fresh_u0.layout.artifacts_dir / READ_EVENTS_PATH).exists()


def test_runtime_generated_execution_identity_is_not_a_host_read_receipt(fresh_u0):
    forged = build_receipt_with_execution_id("runtime-bootstrap")
    with pytest.raises(SourceIntegrityError, match="host execution|receipt"):
        validate_host_read_receipt(forged, action=fresh_u0.pending_action, repo=fresh_u0.repo)
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_source_read_coverage.py tests/test_ultra_foundation.py -k 'host_read or persists_plan or self_claim'`

Expected: FAIL because fresh materialization currently reads and records all units itself.

- [ ] **Step 3: Implement batched read receipts**

```python
def validate_host_read_receipt(
    receipt: Mapping[str, object],
    *,
    action: HostActionSeal,
    repo: Path,
    manifest: SourceManifest,
) -> tuple[dict[str, object], ...]:
    accepted = []
    for item in require_receipt_items(receipt, action=action):
        source_unit = manifest.by_id[str(item["source_unit_id"])]
        measured = read_source_unit_bytes(repo, source_unit)
        if sha256_bytes(measured) != item["source_unit_sha256"]:
            raise SourceIntegrityError("host read receipt source hash differs")
        accepted.append(
            make_read_event_from_host_receipt(
                action=action,
                receipt_item=item,
                source_unit=source_unit,
            )
        )
    return tuple(accepted)
```

Issue bounded batches from the immutable plan so no single result exceeds the JSON authority size limit or creates long Windows paths. Each receipt binds action, host execution, read time, source-unit ID and current content hash. Runtime re-reads bytes, verifies hashes and then creates canonical `ultra-read-event` records. Merge accepted batches append-only; reissue an action for remaining IDs until all 4,753 are covered. U1 phase outputs and checkpoint contain three distinct hashes in order: source lock, read plan and source coverage.

- [ ] **Step 4: Verify U1 GREEN and recovery**

Run: `python -B -m pytest -q tests/test_ultra_source_read_coverage.py tests/test_ultra_foundation.py tests/test_ultra_recovery.py -k 'read_plan or read_receipt or u1'`

Expected: PASS, including missing/tampered plan failures and resumed partial batches.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/source_integrity.py skills/crossframe-ultra/scripts/ultra_runtime/foundation.py skills/crossframe-ultra/scripts/ultra_runtime/recovery.py skills/crossframe-ultra/schemas/ultra-read-plan.schema.json skills/crossframe-ultra/scripts/ultra_runtime/schemas.py tests/test_ultra_source_read_coverage.py tests/test_ultra_foundation.py tests/test_ultra_recovery.py
git commit -m "feat: require honest Ultra U1 read receipts"
```

### Task 4: U2 Persistent Retrieval and Subagent Bridge

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/retrieval.py:482-1470`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/foundation.py`
- Modify: `skills/crossframe-ultra/schemas/ultra-host-action.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-host-result-receipt.schema.json`
- Test: `tests/test_ultra_retrieval_privacy.py`
- Test: `tests/test_ultra_foundation.py`
- Create: `tests/test_ultra_host_retrieval.py`

**Interfaces:**
- Consumes: sealed U1 and generic host handshake.
- Produces: `issue_retrieval_action(...)`, `admit_host_retrieval_result(...)`, `admit_subagent_candidates(...)` and schema-valid U2 ledgers.

- [ ] **Step 1: Write RED CLI-level retrieval tests**

```python
def test_real_world_claim_issues_redacted_retrieval_action(fresh_u1):
    progress = advance_foundation(fresh_u1.layout, repo=fresh_u1.repo, now=fresh_u1.now)
    action = progress.pending_action.document
    assert action["action_kind"] == "retrieval"
    assert action["payload"]["decision"]["status"] == "required"
    assert "alice@example.com" not in canonical_json_bytes(action).decode("utf-8")


def test_host_result_becomes_required_complete_ledger(fresh_u1, primary_source_receipt):
    submit_host_result(fresh_u1.layout, primary_source_receipt)
    progress = advance_foundation(fresh_u1.layout, repo=fresh_u1.repo, now=fresh_u1.later)
    ledger = load_u2_ledger(fresh_u1.layout)
    assert ledger["retrieval_status"] == "required-complete"
    assert ledger["query_count"] >= 1
    assert ledger["sources"][0]["record"]["url"].startswith("https://")
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_host_retrieval.py tests/test_ultra_retrieval_privacy.py -k 'host_result or retrieval_action or subagent'`

Expected: FAIL because required retrieval is not reachable through CLI/materialization.

- [ ] **Step 3: Implement persistable retrieval action/result admission**

```python
def issue_retrieval_action(
    phase_store: PhaseStore,
    *,
    claim: str,
    trigger_kinds: Sequence[str],
    generated_at: str,
) -> dict[str, object]:
    decision = assess_retrieval_eligibility(
        claim,
        phase_store=phase_store,
        trigger_kinds=trigger_kinds,
    )
    authorization = gate_retrieval(decision, phase_store=phase_store)
    if authorization.status == "blocked":
        return build_retrieval_ledger(
            decision,
            generated_at=generated_at,
            phase_store=phase_store,
            authorization=authorization,
        )
    prepared = tuple(
        prepare_query(authorization, query, phase_store=phase_store)
        for query in build_bounded_queries(claim, trigger_kinds)
    )
    return build_retrieval_host_action(decision, authorization, prepared)

def admit_host_retrieval_result(
    receipt: HostResultSeal,
    *,
    phase_store: PhaseStore,
    decision: RetrievalDecision,
    authorization: RetrievalAuthorization,
) -> dict[str, object]:
    sources = tuple(
        make_source_record(**record)
        for record in require_source_records(receipt.document)
    )
    ledger = build_ledger_from_host_sources(
        phase_store=phase_store,
        decision=decision,
        authorization=authorization,
        receipt=receipt,
        sources=sources,
    )
    validate_retrieval_ledger(
        ledger,
        decision=decision,
        authorization=authorization,
        phase_store=phase_store,
    )
    return ledger
```

Persist decision, authorization and prepared redacted queries in the action. Validate actual provider/tool identity, action hash, URLs, source hashes, event/publication dates, interests, upstream lineage, supported claim and `cannot_prove`. Preserve source text as untrusted data. A blocked authorization emits no executable query and cannot complete U2.

- [ ] **Step 4: Add optional subagent candidate receipts**

```python
def admit_subagent_candidates(
    receipt: HostResultSeal,
    *,
    admitted_source_ids: Collection[str],
) -> tuple[dict[str, object], ...]:
    candidates = require_subagent_candidates(receipt.document)
    return tuple(
        copy.deepcopy(candidate)
        for candidate in candidates
        if set(candidate["source_refs"]).issubset(admitted_source_ids)
    )
```

Allow only source discovery, counterexample, affected-position, lineage and calibration roles. A candidate without an admitted source remains untrusted and cannot enter U3. Required subagents unavailable block; optional unavailable records an explicit disposition.

- [ ] **Step 5: Verify GREEN**

Run: `python -B -m pytest -q tests/test_ultra_host_retrieval.py tests/test_ultra_retrieval_privacy.py tests/test_ultra_foundation.py`

Expected: PASS, including network/outbound/ACL zero-dispatch tests, idempotent redaction, replay rejection and bounded retry.

- [ ] **Step 6: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/retrieval.py skills/crossframe-ultra/scripts/ultra_runtime/foundation.py skills/crossframe-ultra/schemas/ultra-host-action.schema.json skills/crossframe-ultra/schemas/ultra-host-result-receipt.schema.json tests/test_ultra_retrieval_privacy.py tests/test_ultra_foundation.py tests/test_ultra_host_retrieval.py
git commit -m "feat: connect Ultra U2 to host retrieval"
```

### Task 5: U3 Evidence Admission, Attribution and Freeze

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/evidence.py:1-464`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/foundation.py`
- Modify: `skills/crossframe-ultra/schemas/ultra-evidence-ledger.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-host-action.schema.json`
- Test: `tests/test_ultra_evidence.py`
- Test: `tests/test_ultra_foundation.py`
- Create: `tests/test_ultra_evidence_admission.py`

**Interfaces:**
- Consumes: request profile, input inventory, U2 admitted sources and verified subagent candidates.
- Produces: `validate_evidence_attribution(...)`, `admit_evidence_candidate(...)`, a sealed U3 ledger and immutable cutoff.

- [ ] **Step 1: Write RED attribution and date tests**

```python
def test_user_claim_requires_exact_request_span(open_world_context):
    entry = user_claim_entry(statement="模型新写出的政策判断", span=(0, 8))
    with pytest.raises(EvidenceValidationError, match="user-claim.*request span"):
        admit_evidence_candidate(entry, authority=open_world_context.authority)


def test_unknown_source_dates_remain_null(retrieved_source_context):
    entry = reported_entry(event_date=None, publication_date=None)
    admitted = admit_evidence_candidate(entry, authority=retrieved_source_context.authority)
    assert admitted["event_date"] is None
    assert admitted["publication_date"] is None


def test_subagent_text_without_admitted_source_is_not_evidence(context):
    with pytest.raises(EvidenceValidationError, match="admitted source"):
        admit_evidence_candidate(subagent_only_entry(), authority=context.authority)
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_evidence_admission.py tests/test_ultra_evidence.py -k 'user_claim or source_dates or subagent'`

Expected: FAIL because attribution is absent and U3 dates require strings.

- [ ] **Step 3: Implement attribution-aware evidence admission**

```python
@dataclass(frozen=True, slots=True)
class EvidenceAdmissionAuthority:
    run_id: str
    request_bytes: bytes
    input_inventory: tuple[dict[str, str], ...]
    admitted_sources: Mapping[str, Mapping[str, object]]
    evidence_cutoff: str

def admit_evidence_candidate(
    entry: Mapping[str, object],
    *,
    authority: EvidenceAdmissionAuthority,
) -> dict[str, object]:
    snapshot = copy.deepcopy(dict(entry))
    attribution = validate_evidence_attribution(snapshot["attribution"], authority=authority)
    identity = str(snapshot["identity"])
    if identity == "user-claim":
        require_exact_user_span(snapshot["statement"], attribution, authority.request_bytes)
    elif identity in {"observed", "reported"}:
        require_admitted_source(attribution, authority.admitted_sources)
    elif identity in {"model-candidate", "simulated"}:
        require_model_origin(attribution)
    return validate_evidence_entry(snapshot, evidence_cutoff=authority.evidence_cutoff)
```

Add a closed `attribution` object with `origin_kind`, `origin_ref`, `content_sha256`, nullable span and `proof_grade`. Require request/material span for `user-claim`; source inventory membership for `reported/observed`; model origin for `model-candidate/simulated`; preserve nullable source dates. Build U3 only from admitted entries, then freeze and checkpoint.

- [ ] **Step 4: Verify GREEN and post-U3 immutability**

Run: `python -B -m pytest -q tests/test_ultra_evidence_admission.py tests/test_ultra_evidence.py tests/test_ultra_foundation.py`

Expected: PASS, including common-upstream clustering and late-evidence rejection.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/evidence.py skills/crossframe-ultra/scripts/ultra_runtime/foundation.py skills/crossframe-ultra/schemas/ultra-evidence-ledger.schema.json skills/crossframe-ultra/schemas/ultra-host-action.schema.json tests/test_ultra_evidence.py tests/test_ultra_foundation.py tests/test_ultra_evidence_admission.py
git commit -m "feat: enforce Ultra U3 evidence attribution"
```

### Task 6: Normal Agent Progress Loop and Materializer Integration

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/materialization.py:32-53, 3190-3512`
- Modify: `skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py:74-137, 286-307, 566-592`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/status.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/deliverables.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/validation.py`
- Modify: `tests/test_ultra_cli.py`
- Modify: `tests/test_ultra_materialization.py`
- Modify: `tests/test_ultra_end_to_end_fixture.py`

**Interfaces:**
- Consumes: `advance_foundation(...)` and existing `materialize_u4_u11(...)`.
- Produces: `MaterializationProgress`, `outcome=awaiting-host-action|awaiting-authoring|complete`, idempotent `prepare` and stable JSON CLI projection.

- [ ] **Step 1: Replace old blocking expectations with RED progress tests**

```python
def test_plain_text_fresh_run_returns_u0_next_action(cli_run):
    result = cli_run.start_prepare_materialize("请分析当前 AI 就业问题。\n")
    assert result.returncode == 0
    assert result.json["outcome"] == "awaiting-host-action"
    assert result.json["current_phase"] == "U0"
    assert result.json["next_action"]["action_kind"] == "capability-attestation"


def test_missing_u4_authoring_is_normal_wait_not_error(prepared_u3):
    result = materialize_complete_run(prepared_u3.repo, RunMode.TEST, prepared_u3.run_id)
    assert result["outcome"] == "awaiting-authoring"
    assert result["next_action"]["relative_path"] == "U04-world-volume.json"
    assert read_status(prepared_u3.layout)["status"] == "running"
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_cli.py tests/test_ultra_materialization.py -k 'plain_text or awaiting or next_action'`

Expected: FAIL because current runtime blocks plain text and missing slots raise errors.

- [ ] **Step 3: Implement typed progress without weakening failures**

```python
@dataclass(frozen=True, slots=True)
class MaterializationProgress:
    outcome: str
    run_id: str
    current_phase: str
    last_complete_phase: str | None
    next_action: dict[str, object] | None
    final_chat: dict[str, object] | None
```

`materialize_complete_run` first calls `advance_foundation`. If U0–U3 need host work, return progress and release lease. Once U3 is sealed, run U4–U12. A missing expected authoring slot returns `awaiting-authoring`; malformed, stale or unauthorized bytes remain errors. `prepare` returns the current pending action idempotently and never truncates accepted authoring.

- [ ] **Step 4: Verify resume and interruption behavior**

Run: `python -B -m pytest -q tests/test_ultra_cli.py tests/test_ultra_materialization.py tests/test_ultra_end_to_end_fixture.py`

Expected: PASS with no tests expecting ordinary missing work to become `blocked` or `needs_attention`.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/materialization.py skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py skills/crossframe-ultra/scripts/ultra_runtime/status.py tests/test_ultra_cli.py tests/test_ultra_materialization.py tests/test_ultra_end_to_end_fixture.py
git commit -m "feat: add Ultra host progress loop"
```

### Task 7: Writer Ownership and Durable Cancellation

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/locks.py:295-406`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/recovery.py:1439-1537`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/materialization.py:3190-3512`
- Modify: `skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py:212-218, 546-563`
- Test: `tests/test_ultra_locks.py`
- Test: `tests/test_ultra_recovery.py`
- Test: `tests/test_ultra_cli.py`
- Test: `tests/test_ultra_tamper_resistance.py`

**Interfaces:**
- Produces: `request_cancel(...)`, `load_cancel_intent(...)`, `converge_cancel_if_requested(...)`, `require_run_lease_owner(...)`.
- Consumes: current lease CAS and terminal phase authority checks.

- [ ] **Step 1: Write RED lease-owner and active-writer cancel tests**

```python
def test_non_owner_foundation_failure_cannot_change_status(run_with_live_writer):
    before = read_status_bytes(run_with_live_writer.layout)
    with pytest.raises(LeaseConflictError):
        materialize_complete_run(run_with_live_writer.repo, RunMode.TEST, run_with_live_writer.run_id)
    assert read_status_bytes(run_with_live_writer.layout) == before


def test_cancel_records_intent_without_waiting_for_writer_lease(run_with_live_writer):
    intent = request_cancel(
        run_with_live_writer.layout,
        reason="operator requested cancellation",
        now=run_with_live_writer.now,
    )
    assert intent["run_id"] == run_with_live_writer.run_id
    with pytest.raises(CancelledRunError):
        heartbeat_run_lease(run_with_live_writer.layout, run_with_live_writer.lease, run_with_live_writer.later)
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_locks.py tests/test_ultra_recovery.py tests/test_ultra_cli.py -k 'non_owner or cancel_intent or live_writer'`

Expected: FAIL because cancel currently must acquire the writer lease and a pre-lease exception can mutate status.

- [ ] **Step 3: Implement cancel intent and strict mutation ownership**

```python
def request_cancel(
    layout: RunLayout,
    *,
    reason: str,
    now: datetime,
) -> CancellationIntent:
    intent = CancellationIntent(
        run_id=layout.run_dir.name,
        reason=reason,
        requested_at=canonical_utc(now),
    )
    write_cancel_intent_once(layout, intent)
    return intent

def require_run_lease_owner(layout: RunLayout, lease: Lease) -> None:
    current = read_run_lease(layout)
    if current.owner_pid != lease.owner_pid or current.owner_nonce != lease.owner_nonce:
        raise LeaseOwnershipError("lease owner PID or nonce does not match")
```

Use `recovery/cancel-intent.json` and a dedicated `.cancel-intent.lock`; write one immutable intent. Check intent during acquisition, heartbeat, before/after host tool dispatch, before phase commit and before publication. Thread `lease: Lease` through every authoritative status transition, checkpoint, validation commit, repair commit and publication callback; `RunStatusStore.create()` is the only bootstrap write without a lease. Move every exception-driven status transition in `materialize_complete_run` inside the lease-owner branch. If no writer is active, cancel uses a dedicated convergence acquisition before updating authority. Terminal cancellation authority blocks future lease/heartbeat even when status is stale; retries do not duplicate the terminal event. Keep lock order fixed: cancel-intent → authority snapshot → lifecycle → writer lease → status/checkpoint/publication.

- [ ] **Step 4: Verify GREEN and race coverage**

Run: `python -B -m pytest -q tests/test_ultra_locks.py tests/test_ultra_recovery.py tests/test_ultra_cli.py tests/test_ultra_tamper_resistance.py -k 'cancel or lease or owner'`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/locks.py skills/crossframe-ultra/scripts/ultra_runtime/status.py skills/crossframe-ultra/scripts/ultra_runtime/recovery.py skills/crossframe-ultra/scripts/ultra_runtime/materialization.py skills/crossframe-ultra/scripts/ultra_runtime/deliverables.py skills/crossframe-ultra/scripts/ultra_runtime/validation.py skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py tests/test_ultra_locks.py tests/test_ultra_recovery.py tests/test_ultra_cli.py tests/test_ultra_tamper_resistance.py
git commit -m "fix: enforce Ultra writer and cancel authority"
```

### Task 8: Append-Only Repair Execution and Evidence Fork

**Files:**
- Create: `skills/crossframe-ultra/schemas/ultra-evidence-lineage.schema.json`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/repair.py:495-631`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/recovery.py:1180-1625`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/materialization.py`
- Modify: `skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py:50-137, 472-543, 595-667`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/state_machine.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/validation.py`
- Modify: `skills/crossframe-ultra/schemas/ultra-phase-event.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-recovery-checkpoint.schema.json`
- Test: `tests/test_ultra_repair.py`
- Test: `tests/test_ultra_recovery.py`
- Test: `tests/test_ultra_cli.py`

**Interfaces:**
- Produces: `apply_repair_plan(...)`, `fork_for_new_evidence(...)`, CLI `evidence-fork`.
- Keeps: existing `fork_run(...)` limited to version migration.

- [ ] **Step 1: Write RED append-only repair tests**

```python
def test_apply_repair_plan_appends_invalidation_without_deleting_history(failed_u10):
    before_events = read_phase_events(failed_u10.layout)
    before_checkpoints = checkpoint_bytes(failed_u10.layout)
    result = apply_repair_plan(failed_u10.layout, plan=failed_u10.plan, now=failed_u10.later)
    assert result["reopened_phase"] == "U10"
    assert read_phase_events(failed_u10.layout)[: len(before_events)] == before_events
    assert checkpoint_bytes(failed_u10.layout).items() >= before_checkpoints.items()
    assert result["next_action"]["relative_path"] == "U10-output-plan.json"


def test_resume_selects_the_active_repair_generation(repaired_u10):
    resumed = resume_run(repaired_u10.layout, lease=repaired_u10.lease, now=repaired_u10.later)
    assert resumed.active_generation == repaired_u10.new_generation
    assert resumed.checkpoint["phase_event_sha256"] == repaired_u10.new_u10_event_sha256
```

- [ ] **Step 2: Write RED evidence-fork tests**

```python
def test_evidence_fork_preserves_parent_and_reopens_at_u0(completed_parent, new_evidence):
    child = fork_for_new_evidence(
        completed_parent.layout,
        mode=RunMode.TEST,
        policy=completed_parent.policy,
        evidence_bytes=new_evidence,
        now=completed_parent.later,
        entropy=b"evidence-child",
    )
    assert child["parent_evidence_sha256"] == completed_parent.u3_hash
    assert child["evidence_cutoff"] > completed_parent.cutoff
    assert not child.layout.artifacts_dir.joinpath("U04-U05-world-volume").exists()
    assert tree_hash(completed_parent.layout.run_dir) == completed_parent.original_tree_hash
```

- [ ] **Step 3: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_repair.py tests/test_ultra_recovery.py tests/test_ultra_cli.py -k 'apply_repair or evidence_fork or append_only'`

Expected: FAIL because repair only builds a plan and fork only supports version migration.

- [ ] **Step 4: Implement bounded repair and evidence lineage**

```python
def apply_repair_plan(
    layout: RunLayout,
    *,
    plan: Mapping[str, object],
    now: datetime,
) -> dict[str, object]:
    validated = validate_committed_repair_plan(layout, plan)
    preserved = preserve_superseded_generation(layout, plan=validated)
    invalidation = append_repair_invalidation(
        layout,
        plan=validated,
        preserved_snapshot_sha256=preserved,
        now=now,
    )
    reopen_authoring_from(layout, phase_id=str(validated["reset_from_phase"]))
    return build_repair_application(validated, invalidation=invalidation)

def fork_for_new_evidence(
    parent_layout: RunLayout,
    *,
    mode: RunMode,
    policy: RootPolicy,
    evidence_bytes: bytes,
    now: datetime,
    entropy: bytes,
) -> dict[str, object]:
    parent = load_frozen_parent_evidence(parent_layout)
    child = create_evidence_child_layout(mode, policy, now=now, entropy=entropy)
    copy_immutable_input_refs(parent_layout, child)
    write_evidence_lineage_request(
        child,
        parent=parent,
        evidence_bytes=evidence_bytes,
        evidence_cutoff=canonical_utc(now),
    )
    return {"child_run_id": child.run_dir.name, "parent_evidence_sha256": parent.artifact_sha256}
```

Add generation-aware `repair-invalidation` authority bound to the failed validator report, committed plan, reset phase, superseded active event hashes and preserved artifact snapshot. Include phase generation and active phase-event hash in checkpoint identity; recovery and validation select the unique active generation instead of rejecting a second completion for the same phase. Before reusing fixed artifact paths, copy superseded bytes to `recovery/repair-attempts/<attempt-id>/superseded/`. Never delete old events/checkpoints/artifacts/attempts. Reopen the earliest affected authoring boundary and stop after the U0 maximum repair count.

`evidence-fork` is a two-stage child flow: the command creates the child and immutable lineage request first; child `prepare` then issues its own U0 attestation action; only U0 admission finalizes the evidence-lineage artifact. The child inherits immutable request/input references and a later cutoff but no U4–U12 conclusions. It never reuses the parent attestation.

- [ ] **Step 5: Verify GREEN**

Run: `python -B -m pytest -q tests/test_ultra_repair.py tests/test_ultra_recovery.py tests/test_ultra_cli.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/crossframe-ultra/schemas/ultra-evidence-lineage.schema.json skills/crossframe-ultra/schemas/ultra-phase-event.schema.json skills/crossframe-ultra/schemas/ultra-recovery-checkpoint.schema.json skills/crossframe-ultra/scripts/ultra_runtime/repair.py skills/crossframe-ultra/scripts/ultra_runtime/recovery.py skills/crossframe-ultra/scripts/ultra_runtime/state_machine.py skills/crossframe-ultra/scripts/ultra_runtime/validation.py skills/crossframe-ultra/scripts/ultra_runtime/materialization.py skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py skills/crossframe-ultra/scripts/ultra_runtime/schemas.py tests/test_ultra_repair.py tests/test_ultra_recovery.py tests/test_ultra_cli.py
git commit -m "feat: add append-only Ultra recovery paths"
```

### Task 9: Evidence Support and Identity Enforcement Through U9

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/judgment.py:400-470, 750-825`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/validation.py:390-480`
- Modify: `skills/crossframe-ultra/schemas/ultra-claim-mechanism-graph.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-verdict.schema.json`
- Test: `tests/test_ultra_claim_mechanism.py`
- Test: `tests/test_ultra_judgment.py`
- Test: `tests/test_ultra_validation.py`
- Test: `tests/test_ultra_adversarial.py`

**Interfaces:**
- Consumes: attribution-aware U3 ledger.
- Produces: `validate_support_edges(...)` used by U6, U9 and fresh disk validation.

- [ ] **Step 1: Write RED fixtures for the Reasonix failure class**

```python
def test_real_world_fact_cannot_pass_with_empty_or_nonmaterial_support(artifact_set):
    graph = artifact_set.graph
    graph["claims"][0]["identity"] = "reported"
    graph["claims"][0]["evidence_refs"] = []
    reseal(graph)
    with pytest.raises(ClaimMechanismError, match="material support|evidence_refs"):
        validate_claim_mechanism_graph(graph, **artifact_set.authority)


def test_simulated_number_cannot_enter_fact_verdict(artifact_set):
    artifact_set.evidence["entries"][0]["identity"] = "simulated"
    reseal(artifact_set.evidence)
    with pytest.raises(JudgmentError, match="simulated.*fact"):
        validate_verdict(artifact_set.verdict, **artifact_set.authority)
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_claim_mechanism.py tests/test_ultra_judgment.py tests/test_ultra_validation.py tests/test_ultra_adversarial.py -k 'empty_support or simulated_number or user_claim'`

Expected: at least one fixture passes unexpectedly, reproducing the structural-but-evidence-hollow gap.

- [ ] **Step 3: Implement one shared support validator**

```python
def validate_support_edges(
    *,
    claim: Mapping[str, object],
    evidence_records: Mapping[str, Mapping[str, object]],
    factual: bool,
) -> tuple[str, ...]:
    refs = tuple(str(ref) for ref in claim["evidence_refs"])
    if factual and not refs:
        raise ClaimMechanismError("factual claim requires material support")
    records = tuple(evidence_records[ref] for ref in refs)
    prohibited = {"user-claim", "model-candidate", "simulated", "unknown"}
    if factual and any(record["identity"] in prohibited for record in records):
        raise ClaimMechanismError("factual claim uses non-material evidence")
    require_supported_scope(str(claim["statement"]), records)
    return tuple(sorted(independent_lineage_cluster_ids(records)))
```

Require nonempty evidence for factual claims/verdicts; reject `user-claim`, `model-candidate`, `simulated`, `unknown` and unsupported subagent candidates as factual support. Require claim statement/scope to remain within each evidence entry's `supported_claim` and outside `cannot_prove`. Count shared upstream lineage once. Use this same function during authoring validation and fresh disk validation.

- [ ] **Step 4: Verify GREEN**

Run: `python -B -m pytest -q tests/test_ultra_claim_mechanism.py tests/test_ultra_judgment.py tests/test_ultra_validation.py tests/test_ultra_adversarial.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/judgment.py skills/crossframe-ultra/scripts/ultra_runtime/validation.py skills/crossframe-ultra/schemas/ultra-claim-mechanism-graph.schema.json skills/crossframe-ultra/schemas/ultra-verdict.schema.json tests/test_ultra_claim_mechanism.py tests/test_ultra_judgment.py tests/test_ultra_validation.py tests/test_ultra_adversarial.py
git commit -m "fix: reject evidence-hollow Ultra judgments"
```

### Task 10: Article Quality and Fresh Semantic Review

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/article.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/coverage.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/validation.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/materialization.py`
- Create: `skills/crossframe-ultra/scripts/ultra_runtime/semantic_review.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/concept_closure.py`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/deliverables.py`
- Create: `skills/crossframe-ultra/schemas/ultra-semantic-review.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-article-review.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-semantic-coverage.schema.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-validator-report.schema.json`
- Modify: `skills/crossframe-ultra/protocols/ultra-article-protocol.md`
- Test: `tests/test_ultra_article.py`
- Test: `tests/test_ultra_article_independence.py`
- Test: `tests/test_ultra_semantic_coverage.py`
- Create: `tests/test_ultra_answer_quality.py`
- Create: `tests/test_ultra_semantic_review.py`
- Modify: `tests/test_ultra_delivery.py`

**Interfaces:**
- Produces: ID-based coverage responsibilities and a separate fresh semantic-review action/artifact that cannot be satisfied by marker repetition.
- Consumes: sealed U3/U6/U9 authorities and the partial article bytes.

- [ ] **Step 1: Write RED hollow-marker and substantive-answer tests**

```python
def test_repeated_markers_cannot_satisfy_article_quality(valid_article_bundle):
    article = "\n".join(valid_article_bundle.required_labels * 8)
    review = build_article_review_artifact(article_text=article, **valid_article_bundle.authority)
    assert review["overall_status"] == "fail"


def test_ai_employment_quality_fixture_requires_real_comparison(quality_fixture):
    review = evaluate_answer_quality(quality_fixture.article, quality_fixture.contract)
    assert review["direct_answer"] == "pass"
    assert review["policy_comparison"] == "pass"
    assert review["conditional_system_branches"] == "pass"
    assert review["theory_comparison"] == "pass"
    assert review["simulated_as_fact"] == "fail"


def test_semantic_review_cannot_be_replayed_for_another_article(review_bundle):
    changed = review_bundle.article_text + "\n新增段落"
    with pytest.raises(SemanticReviewError, match="article.*hash"):
        validate_semantic_review(review_bundle.receipt, article_text=changed, **review_bundle.authority)
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_answer_quality.py tests/test_ultra_article_independence.py -k 'markers or quality_fixture'`

Expected: FAIL because current mechanical coverage can be optimized by field/marker rewriting and no end-to-end quality contract exists.

- [ ] **Step 3: Implement structured coverage and fresh review receipt**

```python
QUALITY_DIMENSIONS = (
    "direct-answer",
    "evidence-boundary",
    "mechanism-competition",
    "recursive-expansion",
    "reversal-conditions",
    "action-comparison",
    "reader-independence",
)

def evaluate_answer_quality(
    article_text: str,
    contract: Mapping[str, object],
) -> dict[str, object]:
    spans = map_contract_responsibilities_to_article(article_text, contract)
    deterministic = validate_distinct_substantive_spans(spans)
    return {
        "schema_id": "crossframe.ultra.v82.answer-quality",
        "dimensions": deterministic,
        "overall_status": (
            "pass" if all(value == "pass" for value in deterministic.values()) else "fail"
        ),
    }
```

Keep the existing U11 mechanical review responsible only for packet structure, ID coverage, blind-reader recovery, duplicate prose and machine dumps. Coverage maps concept/claim/section IDs to article spans and source authorities; deterministic checks reject empty, duplicate and marker-stuffed spans. Before U12 publication, issue a fresh `semantic-review` host action bound to request/intake, article, output-plan, coverage, evidence, concept-disposition and the unchanged `validate_concept_closure(...)` required-unit set. Its receipt evaluates direct answer, evidence boundary, current judgment, competition, three-order expansion, residuals, reversal conditions, action comparison and concept fidelity; it records reviewer/provider/execution identity and cannot override deterministic failures. Add deterministic/adversarial/fresh-semantic layers to the validator report, and require all three plus `publication_allowed=true`. Include semantic-review code/schema and the compatibility matrix in `validator_set_sha256()`. Strengthen delivery report admission so a forged top-level pass with any failed layer or stale article/manifest generation cannot publish. Preserve full inferential expansion and a substantive `center_judgment_summary` in final chat.

- [ ] **Step 4: Verify GREEN**

Run: `python -B -m pytest -q tests/test_ultra_article.py tests/test_ultra_article_independence.py tests/test_ultra_semantic_coverage.py tests/test_ultra_answer_quality.py tests/test_ultra_semantic_review.py tests/test_ultra_validation.py tests/test_ultra_delivery.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/article.py skills/crossframe-ultra/scripts/ultra_runtime/coverage.py skills/crossframe-ultra/scripts/ultra_runtime/semantic_review.py skills/crossframe-ultra/scripts/ultra_runtime/concept_closure.py skills/crossframe-ultra/scripts/ultra_runtime/validation.py skills/crossframe-ultra/scripts/ultra_runtime/deliverables.py skills/crossframe-ultra/scripts/ultra_runtime/materialization.py skills/crossframe-ultra/schemas/ultra-semantic-review.schema.json skills/crossframe-ultra/schemas/ultra-article-review.schema.json skills/crossframe-ultra/schemas/ultra-semantic-coverage.schema.json skills/crossframe-ultra/schemas/ultra-validator-report.schema.json skills/crossframe-ultra/protocols/ultra-article-protocol.md tests/test_ultra_article.py tests/test_ultra_article_independence.py tests/test_ultra_semantic_coverage.py tests/test_ultra_answer_quality.py tests/test_ultra_semantic_review.py tests/test_ultra_validation.py tests/test_ultra_delivery.py
git commit -m "fix: validate Ultra answer quality semantically"
```

### Task 11: Runtime v1.1 / Artifact v2 Compatibility Boundary

**Files:**
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/constants.py:4-19`
- Modify: `skills/crossframe-ultra/schemas/ultra-common.schema.json:130-166`
- Modify: `skills/crossframe-ultra/references/compatibility-matrix.json`
- Modify: `skills/crossframe-ultra/schemas/ultra-compatibility-matrix.schema.json`
- Modify: `skills/crossframe-ultra/scripts/ultra_runtime/schemas.py:72-86`
- Create: `skills/crossframe-ultra/schemas/legacy-v1/` containing the v1 common schema and every schema modified by this plan
- Modify: version-binding fixtures in `tests/test_ultra_*.py`
- Test: `tests/test_ultra_compatibility.py`
- Test: `tests/test_ultra_v82_version_isolation.py`
- Test: `tests/test_ultra_v82_source_fidelity.py`

**Interfaces:**
- Produces: current v2 binding and explicit read-only/migration behavior for v1.
- Preserves: framework and compiler constants byte-for-byte.

- [ ] **Step 1: Write RED version-boundary tests**

```python
def test_current_runtime_binding_is_v2_without_framework_drift():
    binding = current_version_binding()
    assert binding["runtime_version"] == "1.1.0"
    assert binding["artifact_schema_version"] == 2
    assert binding["validator_version"] == "1.1.0"
    assert binding["article_contract_version"] == "1.1.0"
    assert binding["framework_semantic_sha256"] == EXPECTED_V82_SEMANTIC_SHA256
    assert binding["compiler_version"] == "1.0.0"


def test_completed_v1_is_read_only_and_in_progress_v1_requires_child(v1_runs):
    assert resolve_compatibility(v1_runs.complete) == "read-only"
    assert resolve_compatibility(v1_runs.running) == "fork-required"


def test_v1_read_only_validation_uses_legacy_registry_without_writing(v1_complete_run):
    before = tree_hash(v1_complete_run.layout.run_dir)
    report = validate_legacy_run_read_only(v1_complete_run.layout)
    assert report["overall_status"] == "pass"
    assert tree_hash(v1_complete_run.layout.run_dir) == before
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_compatibility.py tests/test_ultra_v82_version_isolation.py tests/test_ultra_v82_source_fidelity.py -k 'v2 or v1 or framework_drift'`

Expected: FAIL because current binding is v1.

- [ ] **Step 3: Bump runtime contracts and update fixtures mechanically**

```python
RUNTIME_VERSION = "1.1.0"
ARTIFACT_SCHEMA_VERSION = 2
COMPILER_VERSION = "1.0.0"
VALIDATOR_VERSION = "1.1.0"
ARTICLE_CONTRACT_VERSION = "1.1.0"
```

Update only runtime/artifact/validator/article binding fields. Add a versioned schema registry: current schemas validate v2; immutable `schemas/legacy-v1/` snapshots validate completed v1 in read-only mode. Add one exact migration rule for the full v1→v2 binding delta; do not rely on the current single-field mismatch logic. Reject creation of new v1 runs. Do not rewrite v8.2 full-source files, source manifest semantic content, concept registry IDs or contract semantics. Add explicit v1 compatibility fixtures rather than deleting legacy coverage.

- [ ] **Step 4: Verify GREEN and source fidelity**

Run: `python -B -m pytest -q tests/test_ultra_compatibility.py tests/test_ultra_v82_version_isolation.py tests/test_ultra_v82_source_fidelity.py tests/test_ultra_schemas.py`

Expected: PASS and unchanged framework raw/semantic hashes.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra/scripts/ultra_runtime/constants.py skills/crossframe-ultra/schemas/ultra-common.schema.json skills/crossframe-ultra/schemas/legacy-v1 skills/crossframe-ultra/references/compatibility-matrix.json skills/crossframe-ultra/schemas/ultra-compatibility-matrix.schema.json skills/crossframe-ultra/scripts/ultra_runtime/schemas.py tests/test_ultra_*.py
git commit -m "feat: version Ultra open-world runtime contracts"
```

### Task 12: Skill Instructions, Adapters, Release Manifest and Mirrors

**Files:**
- Modify: `skills/crossframe-ultra/SKILL.md`
- Modify: `skills/crossframe-ultra/protocols/ultra-runtime-protocol.md`
- Modify: `skills/crossframe-ultra/protocols/ultra-source-authority-protocol.md`
- Modify: `skills/crossframe-ultra/protocols/ultra-validation-repair-protocol.md`
- Modify: `skills/crossframe-ultra/references/runtime-routing-map.md`
- Modify: `skills/crossframe-ultra/references/retrieval-policy.md`
- Create: `skills/crossframe-ultra/references/host-adapter-contract.md`
- Modify: `skills/crossframe-ultra/evals/crossframe-ultra-smoke-tests.md`
- Modify: `.claude/skills/crossframe-ultra/` via mirror synchronization
- Modify: `.claude/commands/crossframe-ultra.md`
- Modify: `scripts/install-codex.sh`
- Modify: `scripts/install-codex.ps1`
- Modify: `scripts/check_crossframe_skill_integrity.py`
- Modify: `skills/crossframe-ultra/references/release-manifest.json`
- Test: `tests/test_ultra_skill_contract.py`
- Test: `tests/test_ultra_protocol_assets.py`
- Test: `tests/test_ultra_repository_invariants.py`
- Test: `tests/test_ultra_installers.py`
- Test: `tests/test_ultra_release_manifest.py`

**Interfaces:**
- Documents the exact host loop from Tasks 1–6 without copying v8.2 theory.
- Keeps adapters thin and canonical/mirror trees byte-identical.

- [ ] **Step 1: Write RED contract tests**

```python
def test_skill_accepts_natural_language_and_keeps_closed_input_special(skill_text):
    assert "普通自然语言" in skill_text
    assert "open-world" in skill_text
    assert "closed-input" in skill_text
    assert "普通自由文本" not in forbidden_blocking_contract(skill_text)


def test_runtime_map_names_the_persistent_host_loop(runtime_map):
    for marker in (
        "capability-attestation",
        "source-read",
        "retrieval",
        "evidence-authoring",
        "awaiting-host-action",
        "evidence-fork",
    ):
        assert marker in runtime_map
```

- [ ] **Step 2: Verify RED**

Run: `python -B -m pytest -q tests/test_ultra_skill_contract.py tests/test_ultra_protocol_assets.py tests/test_ultra_repository_invariants.py`

Expected: FAIL because current public contract is closed-input-only.

- [ ] **Step 3: Update the thin execution contract and adapters**

State explicitly: exact naming applies to activation; plain question bytes are valid; open-world is default; runtime actions must be executed with real host tools; closed-input is explicit-only; subagent candidates are untrusted; waiting is normal; no manual control-file edits. Keep full theory in source/registry/contracts, not SKILL.md.

Use runtime-qualified release ID `ultra-v8.2-r1-runtime-1.1.0`; do not reuse an immutable v1 release ID for new artifact bytes. Installers must verify the promoted live skill tree, root checker wrapper, validator-set SHA and release manifest before deleting their backup. Run mirror generation, not manual duplicate editing:

```bash
python -B scripts/build_crossframe_ultra_release_manifest.py --repo . --write
python -B scripts/sync_skill_mirrors.py --repo .
python -B scripts/build_crossframe_ultra_release_manifest.py --repo . --check
python -B scripts/sync_skill_mirrors.py --repo . --check
```

- [ ] **Step 4: Verify installers, mirrors and manifest**

Run: `python -B -m pytest -q tests/test_ultra_skill_contract.py tests/test_ultra_protocol_assets.py tests/test_ultra_repository_invariants.py tests/test_ultra_installers.py tests/test_ultra_release_manifest.py`

Run: `python -B scripts/build_crossframe_ultra_release_manifest.py --repo . --check`

Run: `python -B scripts/sync_skill_mirrors.py --repo . --check`

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/crossframe-ultra .claude/skills/crossframe-ultra .claude/commands/crossframe-ultra.md scripts/install-codex.sh scripts/install-codex.ps1 scripts/check_crossframe_skill_integrity.py scripts/build_crossframe_ultra_release_manifest.py tests/test_ultra_skill_contract.py tests/test_ultra_protocol_assets.py tests/test_ultra_repository_invariants.py tests/test_ultra_installers.py tests/test_ultra_release_manifest.py
git commit -m "docs: restore Ultra open-world host contract"
```

### Task 13: End-to-End Quality, Unified Review, Full Gates and Local Installation Sync

**Files:**
- Modify: `tests/test_ultra_end_to_end_fixture.py`
- Modify: `tests/test_ultra_behavioral_contract.py`
- Modify: `tests/test_ultra_benchmark_contract.py`
- Create: `tests/fixtures/ultra-runtime/open-world-ai-employment/`
- Modify: `.github/workflows/verify.yml` only if the existing explicit Windows test enumeration needs new files or dependencies
- Modify: release/mirror artifacts only through their generators

**Interfaces:**
- Produces: deterministic CI host/provider fixture, one optional live smoke record, and final release evidence.
- Verifies all prior tasks together; no new runtime behavior originates here.

- [ ] **Step 1: Add the deterministic open-world full-run fixture**

```python
def test_open_world_ai_employment_run_reaches_u12_with_evidence_and_full_answer(open_world_fixture):
    result = run_fixture_to_completion(open_world_fixture)
    assert result.status == "complete"
    assert result.u2["retrieval_status"] == "required-complete"
    assert result.u2["query_count"] > 0
    assert any(entry["identity"] == "reported" for entry in result.u3["entries"])
    assert result.quality["policy_comparison"] == "pass"
    assert result.quality["conditional_system_branches"] == "pass"
    assert result.quality["theory_comparison"] == "pass"
    assert result.validation["overall_status"] == "pass"
```

- [ ] **Step 2: Run the focused end-to-end gate**

Run: `python -B -m pytest -q tests/test_ultra_end_to_end_fixture.py tests/test_ultra_behavioral_contract.py tests/test_ultra_answer_quality.py`

Expected: PASS with a final pytest summary.

- [ ] **Step 3: Perform the unified code review**

Review the complete diff against the approved design and check:

- no runtime policy remains in `materialization.py` that belongs in `foundation.py`;
- no host receipt can author control fields or select its parent authority;
- no non-owner path mutates status;
- no repair/fork deletes history;
- no evidence identity or support bypass remains;
- no new v8.2 concept, source unit or contract semantics were introduced;
- SKILL and adapters remain thin;
- no external forensic/test run was modified.

Fix every Critical/Important finding with a new RED test before changing production code.

- [ ] **Step 4: Run Linux integrity and Ultra tests**

Run: `python -B -m pytest -q tests/test_ultra_*.py --basetemp=/tmp/cfu-pt`

Run: `python -B scripts/check_crossframe_skill_integrity.py`

Run: `python -B scripts/build_crossframe_ultra_release_manifest.py --repo . --check`

Run: `python -B scripts/sync_skill_mirrors.py --repo . --check`

Run: `git diff --check`

Expected: every command exits 0 and pytest prints a final pass/skip summary.

- [ ] **Step 5: Run the authoritative Windows gate**

```powershell
$files = Get-ChildItem -LiteralPath tests -File -Filter 'test_ultra_*.py' |
  Sort-Object FullName |
  ForEach-Object FullName
python -B -m pytest -q $files --basetemp=E:\pt
```

Expected: exit 0 with the final pytest summary. A silent, terminated or summary-less run is inconclusive.

- [ ] **Step 6: Sync local installations and prove byte identity**

Use the repository installers to synchronize canonical Ultra into:

- `C:\Users\cangm\.codex\skills\crossframe-ultra`
- `C:\Users\cangm\.agents\skills\crossframe-ultra`
- `C:\Users\cangm\.claude\skills\crossframe-ultra`

Then enumerate every file in each tree, compare relative path sets and SHA-256 values against `skills/crossframe-ultra/`, and require zero missing, extra or differing files. Do not invoke the installed Ultra during synchronization.

- [ ] **Step 7: Commit final test/release evidence**

```bash
git add tests .github/workflows/verify.yml skills/crossframe-ultra/references/release-manifest.json .claude/skills/crossframe-ultra
git commit -m "test: verify Ultra open-world recovery"
```

- [ ] **Step 8: Push, merge and re-verify release identity**

Push `codex/crossframe-ultra-open-world-recovery`, create a ready PR, wait for CI, merge only after all required checks are green, pull/verify `origin/main`, then compare the merged commit and all three installed trees again. Report exact commit IDs and test summaries; do not infer success from partial output.
