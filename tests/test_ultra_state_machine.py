from __future__ import annotations

import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
SOURCE_MANIFEST = ROOT / "skills/crossframe-ultra/references/source-manifest.json"
SOURCE_MANIFEST_SHA256 = (
    "1c22cda241473ecb3654e37ee9890b975457bb098334ab5c0f85d2775abf6725"
)
RUN_ID = "20260802T000000Z-5a7e9c31b022"
STAMP = "2026-08-02T00:00:00Z"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


LOCKED_INPUT_SHA256 = hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
_LOCKED_INPUTS = [
    {
        "path": "AGENTS.md",
        "sha256": LOCKED_INPUT_SHA256,
        "media_type": "text/markdown",
    }
]
INPUT_SNAPSHOT_SHA256 = hashlib.sha256(_canonical(_LOCKED_INPUTS)).hexdigest()
REQUEST_SHA256 = LOCKED_INPUT_SHA256


def _hash_without(value: dict[str, object], *fields: str) -> str:
    payload = copy.deepcopy(value)
    for field in fields:
        payload.pop(field, None)
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _binding() -> dict[str, object]:
    return {
        "framework_version": "8.2",
        "framework_revision": "v8.2-r1",
        "framework_raw_sha256": "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20",
        "framework_semantic_sha256": "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0",
        "runtime_version": "1.0.0",
        "artifact_schema_version": 1,
        "compiler_version": "1.0.0",
        "validator_version": "1.0.0",
        "article_contract_version": "1.0.0",
        "source_tree_sha256": "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187",
    }


def _run_contract(
    *,
    run_mode: str = "test",
    request_sha256: str = REQUEST_SHA256,
) -> dict[str, object]:
    return {
        "trigger": "crossframe-ultra",
        "request_sha256": request_sha256,
        "run_mode": run_mode,
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": STAMP,
        "capabilities": {
            "filesystem": "available",
            "docx_parser": "available",
            "network": "required",
            "retrieval": "required",
            "validators": "available",
            "subagents": "available",
            "model_context": "available",
        },
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }


_AUTHORITY_REPO = ROOT
_AUTHORITY_MEASUREMENT = None
_AUTHORITY_LAYOUT = None


def _store(
    module,
    *,
    run_id: str = RUN_ID,
    run_mode: str = "test",
    source_repository: Path | None = None,
    request_sha256: str = REQUEST_SHA256,
):
    from ultra_runtime.paths import RunMode, build_run_layout, default_root_policy

    selected_layout = (
        build_run_layout(RunMode.PRODUCTION, run_id, default_root_policy())
        if run_mode == "production"
        else _AUTHORITY_LAYOUT
    )
    return module.PhaseStore(
        run_id=run_id,
        version_binding=_binding(),
        source_sha256=SOURCE_MANIFEST_SHA256,
        input_artifact_hashes=(REQUEST_SHA256,),
        input_snapshot_sha256=INPUT_SNAPSHOT_SHA256,
        evidence_cutoff=STAMP,
        now=datetime(2026, 8, 2, tzinfo=timezone.utc),
        run_contract=_run_contract(
            run_mode=run_mode,
            request_sha256=request_sha256,
        ),
        capability_availability={"retrieval": "available", "network": "available"},
        source_repository=source_repository or _AUTHORITY_REPO,
        u1_prerequisite_measurement=(
            _AUTHORITY_MEASUREMENT if run_mode == "test" else None
        ),
        run_layout=selected_layout,
    )


def _locked_inputs() -> list[dict[str, str]]:
    return copy.deepcopy(_LOCKED_INPUTS)


def _release_artifacts(repo: Path) -> list[dict[str, str]]:
    skill_root = repo / "skills/crossframe-ultra"
    result: list[dict[str, str]] = []
    for path in sorted(skill_root.rglob("*")):
        relative = path.relative_to(skill_root)
        if (
            any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts)
            or relative.as_posix() == "references/release-manifest.json"
            or path.name == ".v8-full-source.lock"
        ):
            continue
        if path.is_file():
            result.append(
                {
                    "path": relative.as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "media_type": "application/octet-stream",
                }
            )
    return result


def _write_release_manifest(repo: Path, path: Path) -> None:
    source = json.loads(
        (repo / "skills/crossframe-ultra/references/source-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.release-manifest",
        "schema_version": 1,
        "run_id": "phase-authority-fixture",
        "version_binding": _binding(),
        "generated_at": STAMP,
        "release_id": "ultra-v8.2-r1",
        "release_state": "stable",
        "stable_pointer": "references/source-manifest.json",
        "framework_source": {
            "path": "references/source-manifest.json",
            "raw_sha256": source["raw_sha256"],
            "semantic_sha256": source["semantic_sha256"],
            "alternate_raw_packages": [],
        },
        "compiler": {
            "normalization_algorithm": "ultra-semantic-normalization",
            "normalization_version": "1.0.0",
        },
        "source_counts": {
            "paragraphs": source["paragraph_count"],
            "headings": source["heading_count"],
            "tables": source["table_count"],
            "concepts": source["concept_count"],
            "contracts": source["contract_count"],
            "source_units": source["source_unit_count"],
        },
        "release_artifacts": _release_artifacts(repo),
        "built_at": STAMP,
        "validated_at": STAMP,
    }
    document["content_sha256"] = _hash_without(document, "content_sha256")
    path.write_bytes(_canonical(document))


@pytest.fixture(scope="module", autouse=True)
def u1_prerequisite_context(tmp_path_factory):
    import ultra_runtime.source_integrity as source_integrity
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

    global _AUTHORITY_LAYOUT, _AUTHORITY_MEASUREMENT, _AUTHORITY_REPO
    fixture_root = tmp_path_factory.mktemp("phase-host-authority")
    authority_repo = fixture_root / "repo"
    skill_root = authority_repo / "skills/crossframe-ultra"
    skill_root.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/crossframe-ultra", skill_root)
    shutil.copy2(ROOT / "AGENTS.md", authority_repo / "AGENTS.md")
    jsonio = skill_root / "scripts/ultra_runtime/jsonio.py"
    jsonio.write_bytes(jsonio.read_bytes().replace(b"\r\n", b"\n"))
    release_path = fixture_root / "release-manifest.json"
    _write_release_manifest(authority_repo, release_path)
    manifest = source_integrity.load_source_manifest(
        skill_root / "references/source-manifest.json",
        expected_sha256=SOURCE_MANIFEST_SHA256,
    )
    measurement = source_integrity.measure_u1_prerequisites(
        authority_repo,
        manifest=manifest,
        release_manifest_path=release_path,
        run_mode="test",
    )
    assert measurement.ready
    policy = RootPolicy(
        fixture_root / "production-control",
        fixture_root / "test-control",
    )
    run_layout = build_run_layout(RunMode.TEST, RUN_ID, policy)
    run_layout.input_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "AGENTS.md", run_layout.input_dir / "AGENTS.md")
    _AUTHORITY_REPO = authority_repo
    _AUTHORITY_MEASUREMENT = measurement
    _AUTHORITY_LAYOUT = run_layout
    return {
        "repo": authority_repo,
        "manifest": manifest,
        "measurement": measurement,
        "run_layout": run_layout,
    }


def _issue_u1_authority(store, context, *, include_recovery_snapshot=False):
    import ultra_runtime.source_integrity as source_integrity

    u0 = store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    manifest = context["manifest"]
    measurement = context["measurement"]
    authority_repo = context["repo"]
    run_layout = context["run_layout"]
    lock = source_integrity.build_source_lock(
        run_id=RUN_ID,
        version_binding=_binding(),
        generated_at=STAMP,
        prerequisite_measurement=measurement,
        parent_event_sha256=u0["event_sha256"],
        evidence_cutoff=STAMP,
        run_layout=run_layout,
        inputs=_locked_inputs(),
    )
    lock_seal = source_integrity.validate_source_lock(
        lock,
        prerequisite_measurement=measurement,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_parent_event_sha256=u0["event_sha256"],
        expected_evidence_cutoff=STAMP,
        expected_inputs=_locked_inputs(),
        run_layout=run_layout,
    )
    session = source_integrity.open_source_read_session(
        authority_repo,
        run_id=RUN_ID,
        version_binding=_binding(),
        manifest=manifest,
        source_lock_sha256=lock_seal.artifact_sha256,
        parent_event_sha256=u0["event_sha256"],
        reader_mode="full-source",
        read_at=STAMP,
    )
    receipts = tuple(
        source_integrity.capture_source_unit_read(session, unit["unit_id"])[1]
        for unit in manifest.document["source_units"]
    )
    events = tuple(
        source_integrity.make_read_event(
            run_id=RUN_ID,
            version_binding=_binding(),
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            source_lock_sha256=lock_seal.artifact_sha256,
            parent_event_sha256=u0["event_sha256"],
            receipt=receipt,
        )
        for receipt in receipts
    )
    audit = source_integrity.audit_read_capture(
        events,
        manifest,
        receipts=receipts,
        promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_source_lock_sha256=lock_seal.artifact_sha256,
        expected_parent_event_sha256=u0["event_sha256"],
    )
    authority = source_integrity.validate_u1_authority(lock_seal, audit)
    if not include_recovery_snapshot:
        return authority
    source_coverage = {
        "artifact_type": "crossframe.ultra.v82.u1-source-coverage",
        "run_id": store.run_id,
        "version_binding": _binding(),
        "parent_event_sha256": u0["event_sha256"],
        "source_lock_sha256": lock_seal.artifact_sha256,
        "receipt_sha256s": [receipt.receipt_sha256 for receipt in receipts],
        "read_event_sha256s": [
            str(event["read_event_sha256"]) for event in events
        ],
    }
    read_plan = source_integrity.build_read_plan(
        manifest,
        promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
        source_manifest_sha256=manifest.sha256,
        source_lock_sha256=lock_seal.artifact_sha256,
        parent_event_sha256=u0["event_sha256"],
    )
    assert hashlib.sha256(_canonical(source_coverage)).hexdigest() == (
        audit.artifact_sha256
    )
    return {
        "authority": authority,
        "source_lock": copy.deepcopy(lock),
        "source_coverage": source_coverage,
        "read_plan": read_plan,
        "read_events": tuple(copy.deepcopy(event) for event in events),
    }


def _issue_u1_recovery_snapshot(store, context):
    return _issue_u1_authority(
        store,
        context,
        include_recovery_snapshot=True,
    )


@pytest.fixture(scope="module")
def u1_authority(u1_prerequisite_context):
    import ultra_runtime.state_machine as state_machine

    return _issue_u1_authority(
        _store(state_machine),
        u1_prerequisite_context,
    )


def _complete_u0_u1(store, authority):
    store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    return store.complete(
        "U1",
        artifact_hashes=(
            authority.source_lock_artifact_sha256,
            authority.read_coverage_artifact_sha256,
        ),
        u1_authority=authority,
    )


def _complete_u2(store, *, include_artifact=False):
    import ultra_runtime.retrieval as retrieval

    decision = retrieval.assess_retrieval_eligibility(
        "If A then B.",
        phase_store=store,
        pure_logic=True,
    )
    ledger = retrieval.build_retrieval_ledger(
        decision,
        generated_at=STAMP,
        phase_store=store,
    )
    seal = retrieval.validate_retrieval_ledger(
        ledger,
        phase_store=store,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_phase_id="U2",
        expected_u1_parent_event_sha256=store.events[-1]["event_sha256"],
        expected_request_sha256=REQUEST_SHA256,
        expected_decision_sha256=decision.decision_sha256,
        expected_authorization_sha256=None,
    )
    event = store.complete(
        "U2",
        artifact_hashes=(seal.artifact_sha256,),
        retrieval_authority=seal,
    )
    return (event, ledger) if include_artifact else event


def _evidence_entry() -> dict[str, object]:
    return {
        "evidence_id": "EV-STATE-1",
        "identity": "reported",
        "statement": "A bounded statement.",
        "source_refs": ["report-1"],
        "observed_at": None,
        "confidence": "medium",
        "event_date": "2026-08-01",
        "publication_date": "2026-08-01",
        "interest": "none declared",
        "upstream_lineage": ["report-1"],
        "supported_claim": "claim-1",
        "cannot_prove": "universal validity",
    }


def _complete_u3(store):
    store.append_evidence(_evidence_entry())
    import ultra_runtime.evidence as evidence

    seal = evidence.validate_evidence_artifact(
        store.evidence_artifact,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_phase_id="U3",
        expected_evidence_cutoff=STAMP,
    )
    return store.complete(
        "U3",
        artifact_hashes=(seal.artifact_sha256,),
        evidence_authority=seal,
    )


def test_u0_phase_event_is_schema_valid_with_two_special_hash_roles():
    import ultra_runtime.state_machine as module
    from ultra_runtime.schemas import validate_instance

    store = _store(module)
    event = store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    validate_instance("ultra-phase-event.schema.json", event)
    assert event["content_sha256"] == _hash_without(
        event, "content_sha256", "event_sha256"
    )
    assert event["event_sha256"] == _hash_without(event, "event_sha256")
    assert event["run_contract_sha256"] == store.run_contract_artifact_sha256
    assert event["parent_event_sha256"] == "0" * 64


def test_phase_store_accepts_only_the_canonical_control_plane_run_layout(tmp_path):
    import ultra_runtime.state_machine as module
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

    policy = RootPolicy(tmp_path / "production-control", tmp_path / "test-control")
    layout = build_run_layout(RunMode.TEST, RUN_ID, policy)
    layout.input_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "AGENTS.md", layout.input_dir / "AGENTS.md")
    arguments = {
        "run_id": RUN_ID,
        "version_binding": _binding(),
        "source_sha256": SOURCE_MANIFEST_SHA256,
        "input_artifact_hashes": (REQUEST_SHA256,),
        "input_snapshot_sha256": INPUT_SNAPSHOT_SHA256,
        "evidence_cutoff": STAMP,
        "now": datetime(2026, 8, 2, tzinfo=timezone.utc),
        "run_contract": _run_contract(),
        "capability_availability": {
            "retrieval": "available",
            "network": "available",
        },
        "source_repository": ROOT,
    }
    store = module.PhaseStore(**arguments, run_layout=layout)
    assert store.run_input_root == layout.input_dir.resolve()

    repo_substitute = replace(layout, input_dir=ROOT)
    with pytest.raises(module.PhaseIntegrityError, match="layout|input"):
        module.PhaseStore(**arguments, run_layout=repo_substitute)

    other_layout = build_run_layout(
        RunMode.TEST,
        "20260802T000001Z-6b8fae42c033",
        policy,
    )
    with pytest.raises(module.PhaseIntegrityError, match="layout|run"):
        module.PhaseStore(**arguments, run_layout=other_layout)


def test_u0_run_contract_is_frozen_schema_valid_and_hash_bound():
    import ultra_runtime.state_machine as module
    from ultra_runtime.schemas import validate_instance

    contract = _run_contract()
    store = _store(module)
    contract["sensitivity"] = "restricted"
    validate_instance("ultra-run-contract.schema.json", store.run_contract)
    assert store.run_contract["sensitivity"] == "private"
    assert store.run_contract["content_sha256"] == _hash_without(
        dict(store.run_contract), "content_sha256"
    )
    assert store.run_contract_artifact_sha256 == hashlib.sha256(
        _canonical(dict(store.run_contract))
    ).hexdigest()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("maximum_branches", 65),
        ("maximum_retrieval_rounds_without_material_novelty", 3),
        ("maximum_tool_retries", 4),
        ("maximum_repair_attempts", 4),
        ("maximum_branches", 2**63),
        ("maximum_tool_retries", 2**63),
    ),
)
def test_u0_resource_limits_reject_oversized_caller_sealed_values(field, value):
    import ultra_runtime.state_machine as module

    contract = _run_contract()
    contract["resource_limits"][field] = value
    with pytest.raises(module.RunContractError, match="maximum|limit|between"):
        module.validate_run_contract(
            contract,
            capability_availability={"network": "available", "retrieval": "available"},
        )


@pytest.mark.parametrize("phase", ("U1", "U2", "U3"))
def test_skipped_phase_is_rejected(phase):
    import ultra_runtime.state_machine as module

    with pytest.raises(module.PhaseTransitionError):
        _store(module).complete(phase, artifact_hashes=("a" * 64,))


@pytest.mark.parametrize("completed_phase", (None, "U0", "U1"))
def test_u3_evidence_authority_cannot_form_before_successful_u2(
    completed_phase,
    u1_authority,
):
    import ultra_runtime.state_machine as module

    store = _store(module)
    if completed_phase in {"U0", "U1"}:
        store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    if completed_phase == "U1":
        store.complete(
            "U1",
            artifact_hashes=(
                u1_authority.source_lock_artifact_sha256,
                u1_authority.read_coverage_artifact_sha256,
            ),
            u1_authority=u1_authority,
        )
    events_before = store.events
    unknowns_before = store.evidence_unknowns
    entries_before = store._evidence_ledger.entries
    attempts = (
        lambda: store.append_evidence(_evidence_entry()),
        lambda: store.append_unknown(
            {
                "unknown_id": "UNKNOWN-PREMATURE",
                "location_ref": "POS-1",
                "description": "A premature unknown.",
                "resolution_condition": "Complete U2.",
            }
        ),
        store.freeze_evidence,
        lambda: store.freeze_evidence_cutoff(STAMP),
    )
    for attempt in attempts:
        with pytest.raises(module.PhaseTransitionError, match="U2"):
            attempt()
    assert store.events == events_before
    assert store.evidence_unknowns == unknowns_before
    assert store._evidence_ledger.entries == entries_before
    assert not store.evidence_frozen


def test_u1_requires_external_source_and_read_authority_and_never_auto_marks_reads(monkeypatch):
    import ultra_runtime.source_integrity as source_integrity
    import ultra_runtime.state_machine as module

    store = _store(module)
    store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))

    def forbidden_capture(*args, **kwargs):
        raise AssertionError("PhaseStore must not synthesize source reads")

    monkeypatch.setattr(
        source_integrity,
        "capture_authority_read_diagnostic",
        forbidden_capture,
    )
    with pytest.raises(module.PhaseIntegrityError, match="U1|authority|source"):
        store.complete("U1", artifact_hashes=("a" * 64,))


def test_u1_rejects_a_run_request_hash_outside_the_locked_input_authority(
    u1_prerequisite_context,
):
    import ultra_runtime.state_machine as module

    store = _store(module, request_sha256="9" * 64)
    u1_authority = _issue_u1_authority(store, u1_prerequisite_context)
    before = store.events
    with pytest.raises(module.PhaseIntegrityError, match="request|input"):
        store.complete(
            "U1",
            artifact_hashes=(
                u1_authority.source_lock_artifact_sha256,
                u1_authority.read_coverage_artifact_sha256,
            ),
            u1_authority=u1_authority,
        )
    assert store.events == before
    assert store.current_phase == "U0"


def test_adjacent_u0_u3_chain_uses_sealed_phase_authorities(u1_authority):
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    assert store.retrieval_boundary.run_id == RUN_ID
    assert store.retrieval_boundary.input_root == _AUTHORITY_LAYOUT.input_dir.resolve()
    _complete_u2(store)
    _complete_u3(store)
    assert [event["phase_id"] for event in store.events] == ["U0", "U1", "U2", "U3"]
    assert store.current_phase == "U3"
    assert store.evidence_frozen


def test_parent_input_source_version_and_cutoff_bindings_are_immutable():
    import ultra_runtime.state_machine as module

    store = _store(module)
    first = store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    attempts = (
        {"parent_event_sha256": "9" * 64},
        {"input_artifact_hashes": ("8" * 64,)},
        {"source_sha256": "7" * 64},
        {"version_binding": {**_binding(), "runtime_version": "9.9.9"}},
        {"evidence_cutoff": "2027-01-01T00:00:00Z"},
    )
    for kwargs in attempts:
        with pytest.raises(module.PhaseIntegrityError):
            store.complete("U1", artifact_hashes=("a" * 64,), **kwargs)
    assert store.events == (first,)


def test_resealed_phase_mutation_is_rejected_by_external_authority_not_stale_hash():
    import ultra_runtime.state_machine as module
    from ultra_runtime.schemas import validate_instance

    source = _store(module)
    event = source.complete("U0", artifact_hashes=(source.run_contract_artifact_sha256,))
    changed = copy.deepcopy(event)
    changed["source_sha256"], changed["run_contract_sha256"] = (
        changed["run_contract_sha256"],
        changed["source_sha256"],
    )
    changed["content_sha256"] = _hash_without(
        changed, "content_sha256", "event_sha256"
    )
    changed["event_sha256"] = _hash_without(changed, "event_sha256")
    validate_instance("ultra-phase-event.schema.json", changed)
    with pytest.raises(module.PhaseIntegrityError, match="source|contract|authority"):
        _store(module).replay_event(changed)


def test_replay_duplicate_and_overwrite_are_rejected():
    import ultra_runtime.state_machine as module

    store = _store(module)
    event = store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    with pytest.raises(module.PhaseIntegrityError):
        store.replay_event(event)
    with pytest.raises(module.PhaseTransitionError):
        store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))


@pytest.mark.parametrize("status", ("failed", "blocked", "cancelled"))
def test_terminal_events_have_no_outputs_and_end_the_run(status):
    import ultra_runtime.state_machine as module
    from ultra_runtime.schemas import validate_instance

    store = _store(module)
    terminal = store.fail if status == "failed" else getattr(store, status)
    event = terminal("U0", failure_code=f"U0_{status.upper()}")
    validate_instance("ultra-phase-event.schema.json", event)
    assert event["output_artifact_hashes"] == []
    assert event["status"] == status
    with pytest.raises(module.PhaseTransitionError, match="terminal"):
        store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    with pytest.raises(module.PhaseTransitionError, match="terminal"):
        store.replay_event(event)


@pytest.mark.parametrize("status", ("failed", "blocked", "cancelled"))
def test_terminal_guard_precedes_all_evidence_and_fork_authority_paths(status):
    import ultra_runtime.state_machine as module

    store = _store(module)
    terminal = store.fail if status == "failed" else getattr(store, status)
    terminal("U0", failure_code=f"U0_{status.upper()}")
    events_before = store.events
    unknowns_before = store.evidence_unknowns
    entries_before = store._evidence_ledger.entries
    attempts = (
        lambda: store.append_evidence(_evidence_entry()),
        lambda: store.append_unknown(
            {
                "unknown_id": "UNKNOWN-TERMINAL",
                "location_ref": "POS-1",
                "description": "A terminal attempt.",
                "resolution_condition": "Start a new run.",
            }
        ),
        store.freeze_evidence,
        lambda: store.freeze_evidence_cutoff(STAMP),
        lambda: store.fork_run(
            "run-terminal-child",
            evidence_cutoff="2026-08-03T00:00:00Z",
        ),
        lambda: store.retrieval_boundary,
    )
    for attempt in attempts:
        with pytest.raises(module.PhaseTransitionError, match="terminal"):
            attempt()
    assert store.events == events_before
    assert store.evidence_unknowns == unknowns_before
    assert store._evidence_ledger.entries == entries_before
    assert not store.evidence_frozen


def test_retrieval_boundary_is_factory_sealed_and_cannot_be_caller_selected(u1_authority):
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    with pytest.raises(TypeError):
        module.RetrievalBoundary(
            run_id=RUN_ID,
            version_binding=_binding(),
            u1_parent_event_sha256=store.events[-1]["event_sha256"],
            request_sha256=REQUEST_SHA256,
        )


def test_u0_sealed_capability_availability_propagates_required_network_to_u2(
    u1_authority,
):
    import ultra_runtime.state_machine as module

    availability = {"retrieval": "available", "network": "available"}
    store = module.PhaseStore(
        run_id=RUN_ID,
        version_binding=_binding(),
        source_sha256=SOURCE_MANIFEST_SHA256,
        input_artifact_hashes=(REQUEST_SHA256,),
        input_snapshot_sha256=INPUT_SNAPSHOT_SHA256,
        evidence_cutoff=STAMP,
        now=datetime(2026, 8, 2, tzinfo=timezone.utc),
        run_contract=_run_contract(),
        capability_availability=availability,
        source_repository=_AUTHORITY_REPO,
        u1_prerequisite_measurement=_AUTHORITY_MEASUREMENT,
        run_layout=_AUTHORITY_LAYOUT,
    )
    availability["network"] = "unavailable"
    _complete_u0_u1(store, u1_authority)
    boundary = store.retrieval_boundary
    assert boundary.network_available is True
    with pytest.raises(TypeError):
        module.PhaseStore(
            run_id=RUN_ID,
            version_binding=_binding(),
            source_sha256=SOURCE_MANIFEST_SHA256,
            input_artifact_hashes=(REQUEST_SHA256,),
            input_snapshot_sha256=INPUT_SNAPSHOT_SHA256,
            evidence_cutoff=STAMP,
            now=datetime(2026, 8, 2, tzinfo=timezone.utc),
            run_contract=_run_contract(),
            capability_availability={"retrieval": "available", "network": "available"},
            source_repository=_AUTHORITY_REPO,
            u1_prerequisite_measurement=_AUTHORITY_MEASUREMENT,
            run_layout=_AUTHORITY_LAYOUT,
            network_available=True,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "source-release",
        "source",
        "release",
        "compatibility",
        "knowledge",
        "tree",
        "input-snapshot",
        "input-hashes",
        "cutoff",
        "root",
        "run-mode",
        "acl",
    ),
)
def test_existing_phase_store_rejects_cross_authority_u1_seals(u1_authority, mutation):
    import ultra_runtime.state_machine as module

    changed = copy.copy(u1_authority)
    if mutation == "source-release":
        object.__setattr__(changed, "source_release_id", "ultra-v8.2-r2")
    elif mutation == "source":
        object.__setattr__(changed, "source_manifest_sha256", "8" * 64)
    elif mutation == "release":
        object.__setattr__(changed, "release_manifest_sha256", "1" * 64)
    elif mutation == "compatibility":
        object.__setattr__(changed, "compatibility_matrix_sha256", "2" * 64)
    elif mutation == "knowledge":
        object.__setattr__(changed, "knowledge_report_sha256", "3" * 64)
    elif mutation == "tree":
        object.__setattr__(changed, "skill_tree_sha256", "4" * 64)
    elif mutation == "input-snapshot":
        object.__setattr__(changed, "input_snapshot_sha256", "7" * 64)
    elif mutation == "input-hashes":
        object.__setattr__(changed, "input_artifact_hashes", ("6" * 64,))
    elif mutation == "cutoff":
        object.__setattr__(changed, "evidence_cutoff", "2026-08-01T00:00:00Z")
    elif mutation == "acl":
        object.__setattr__(changed, "acl_status", "unknown")
    elif mutation == "run-mode":
        object.__setattr__(changed, "run_mode", "production")
    else:
        object.__setattr__(changed, "input_root", _AUTHORITY_REPO / "skills")
    store = _store(module)
    store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    with pytest.raises(module.PhaseIntegrityError, match="U1|authority|source|input|cutoff|root"):
        store.complete(
            "U1",
            artifact_hashes=(
                changed.source_lock_artifact_sha256,
                changed.read_coverage_artifact_sha256,
            ),
            u1_authority=changed,
        )


def test_u1_authority_preserves_every_measured_role_and_test_mode_cannot_enter_production(
    u1_authority,
):
    import ultra_runtime.state_machine as module

    assert u1_authority.run_mode == "test"
    assert u1_authority.source_release_id == "ultra-v8.2-r1"
    assert u1_authority.free_space_reserve_bytes == 1 << 30
    assert u1_authority.free_space_status == "available"
    for name in (
        "source_manifest_sha256",
        "release_manifest_sha256",
        "compatibility_matrix_sha256",
        "knowledge_report_sha256",
        "skill_tree_sha256",
        "input_snapshot_sha256",
    ):
        assert len(getattr(u1_authority, name)) == 64

    production = _store(module, run_mode="production", source_repository=ROOT)
    production.complete("U0", artifact_hashes=(production.run_contract_artifact_sha256,))
    with pytest.raises(module.PhaseIntegrityError, match="mode|authority|U1"):
        production.complete(
            "U1",
            artifact_hashes=(
                u1_authority.source_lock_artifact_sha256,
                u1_authority.read_coverage_artifact_sha256,
            ),
            u1_authority=u1_authority,
        )


def test_post_acceptance_caller_mutation_cannot_alias_stored_u1_authority(u1_authority):
    import ultra_runtime.state_machine as module

    caller_authority = copy.deepcopy(u1_authority)
    store = _store(module)
    _complete_u0_u1(store, caller_authority)
    events_before = store.events
    boundary_before = store.retrieval_boundary

    object.__setattr__(caller_authority, "acl_status", "unknown")
    caller_authority.version_binding["runtime_version"] = "9.9.9"
    caller_authority.inputs[0]["sha256"] = "9" * 64

    boundary_after = store.retrieval_boundary
    assert boundary_after.acl_status == boundary_before.acl_status
    assert boundary_after.version_binding == boundary_before.version_binding
    assert boundary_after.inputs == boundary_before.inputs
    assert store.events == events_before


def test_u3_rejects_same_boundary_cross_ledger_seal_without_mutating_phase(u1_authority):
    import ultra_runtime.evidence as evidence
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    _complete_u2(store)
    other = evidence.EvidenceLedger(
        RUN_ID,
        STAMP,
        version_binding=_binding(),
        generated_at=STAMP,
    )
    changed = _evidence_entry()
    changed["evidence_id"] = "EV-OTHER"
    changed["statement"] = "A different same-boundary ledger."
    other.append(changed)
    other_seal = other.seal()
    before = store.events
    with pytest.raises(module.PhaseIntegrityError, match="evidence|ledger|authority"):
        store.complete(
            "U3",
            artifact_hashes=(other_seal.artifact_sha256,),
            evidence_authority=other_seal,
        )
    assert store.events == before
    assert store.current_phase == "U2"
    assert not store.evidence_frozen


def test_u3_empty_internal_ledger_failure_is_atomic(u1_authority):
    import ultra_runtime.evidence as evidence
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    _complete_u2(store)
    other = evidence.EvidenceLedger(
        RUN_ID,
        STAMP,
        version_binding=_binding(),
        generated_at=STAMP,
    )
    other.append(_evidence_entry())
    seal = other.seal()
    before = store.events
    with pytest.raises((module.PhaseIntegrityError, module.EvidenceFrozenError, ValueError)):
        store.complete(
            "U3",
            artifact_hashes=(seal.artifact_sha256,),
            evidence_authority=seal,
        )
    assert store.events == before
    assert store.current_phase == "U2"
    assert not store.evidence_frozen


def test_post_u3_evidence_requires_new_run_and_strictly_later_cutoff(u1_authority):
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    _complete_u2(store)
    store.append_unknown(
        {
            "unknown_id": "UNKNOWN-STATE-1",
            "location_ref": "POS-1",
            "description": "A located unknown.",
            "resolution_condition": "Observe the next cycle.",
        }
    )
    _complete_u3(store)
    with pytest.raises(module.EvidenceFrozenError):
        store.append_evidence(_evidence_entry())
    with pytest.raises(module.PhaseIntegrityError, match="new run_id"):
        store.fork_run(RUN_ID, evidence_cutoff="2026-08-03T00:00:00Z")
    with pytest.raises(module.PhaseIntegrityError, match="cutoff"):
        store.fork_run("20260803T000000Z-7c90bf53d144", evidence_cutoff=STAMP)
    with pytest.raises(module.PhaseIntegrityError, match="start"):
        store.fork_run(
            "20260803T000000Z-7c90bf53d144",
            evidence_cutoff="2026-08-03T00:00:00Z",
        )


def test_fork_is_rejected_before_successfully_frozen_u3(u1_authority):
    import ultra_runtime.state_machine as module

    fresh = _store(module)
    with pytest.raises(module.PhaseIntegrityError, match="U3|frozen"):
        fresh.fork_run(
            "20260803T000001Z-8da1c064e255",
            evidence_cutoff="2026-08-03T00:00:00Z",
        )
    _complete_u0_u1(fresh, u1_authority)
    _complete_u2(fresh)
    with pytest.raises(module.PhaseIntegrityError, match="U3|frozen"):
        fresh.fork_run(
            "20260803T000002Z-9eb2d175f366",
            evidence_cutoff="2026-08-03T00:00:00Z",
        )


def test_naive_event_clock_and_noncurrent_version_binding_are_rejected():
    import ultra_runtime.state_machine as module

    with pytest.raises(module.PhaseIntegrityError):
        module.PhaseStore(
            run_id=RUN_ID,
            version_binding=_binding(),
            source_sha256=SOURCE_MANIFEST_SHA256,
            input_artifact_hashes=(REQUEST_SHA256,),
            input_snapshot_sha256=INPUT_SNAPSHOT_SHA256,
            evidence_cutoff=STAMP,
            now=datetime(2026, 8, 2),
            run_contract=_run_contract(),
            capability_availability={"retrieval": "available"},
            run_layout=_AUTHORITY_LAYOUT,
        )
    with pytest.raises(module.PhaseIntegrityError, match="current|authority"):
        module.PhaseStore(
            run_id=RUN_ID,
            version_binding={**_binding(), "runtime_version": "9.9.9"},
            source_sha256=SOURCE_MANIFEST_SHA256,
            input_artifact_hashes=(REQUEST_SHA256,),
            input_snapshot_sha256=INPUT_SNAPSHOT_SHA256,
            evidence_cutoff=STAMP,
            now=datetime(2026, 8, 2, tzinfo=timezone.utc),
            run_contract=_run_contract(),
            capability_availability={"retrieval": "available"},
            run_layout=_AUTHORITY_LAYOUT,
        )


def _late_phase_hash(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


_LATE_PHASE_OUTPUTS = {
    "U4": ("world-volume",),
    "U5": ("transformation-ledger", "concept-disposition"),
    "U6": ("claim-mechanism-graph",),
    "U7": ("recursive-state-node-1", "recursive-state-node-2", "recursive-lineage"),
    "U8": ("order-evaluation", "red-team-report"),
    "U9": ("verdict", "action-ranking", "forecast-ledger"),
    "U10": ("framework-gap-ledger", "output-plan"),
    "U11": (
        "semantic-coverage",
        "article-review",
        "article-partial",
        "dossier",
        "artifact-index",
    ),
}


def _complete_through_u11(store, authority) -> None:
    _complete_u0_u1(store, authority)
    _complete_u2(store)
    _complete_u3(store)
    for phase_id, labels in _LATE_PHASE_OUTPUTS.items():
        parent = store.events[-1]["event_sha256"]
        outputs = tuple(_late_phase_hash(label) for label in labels)
        event = store.complete(
            phase_id,
            artifact_hashes=outputs,
            parent_event_sha256=parent,
            input_artifact_hashes=(REQUEST_SHA256,),
            version_binding=_binding(),
            source_sha256=SOURCE_MANIFEST_SHA256,
            evidence_cutoff=STAMP,
        )
        assert tuple(event["output_artifact_hashes"]) == outputs
        assert event["parent_event_sha256"] == parent


def test_phase_store_extends_the_single_ordered_chain_through_u11(u1_authority):
    import ultra_runtime.state_machine as module
    from ultra_runtime.constants import PHASES

    assert module.PHASE_ORDER is PHASES
    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    _complete_u2(store)
    _complete_u3(store)
    before = store.events
    with pytest.raises(module.PhaseIntegrityError, match="parent"):
        store.complete(
            "U4",
            artifact_hashes=(_late_phase_hash("world-volume"),),
            parent_event_sha256="f" * 64,
        )
    assert store.events == before

    for phase_id, labels in _LATE_PHASE_OUTPUTS.items():
        outputs = tuple(_late_phase_hash(label) for label in labels)
        event = store.complete(
            phase_id,
            artifact_hashes=outputs,
            parent_event_sha256=store.events[-1]["event_sha256"],
            input_artifact_hashes=(REQUEST_SHA256,),
            version_binding=_binding(),
            source_sha256=SOURCE_MANIFEST_SHA256,
            evidence_cutoff=STAMP,
        )
        assert tuple(event["output_artifact_hashes"]) == outputs

    assert store.current_phase == "U11"
    assert tuple(event["phase_id"] for event in store.events) == PHASES[:12]


def test_late_phase_output_cardinality_is_rejected_atomically(u1_authority):
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete_u0_u1(store, u1_authority)
    _complete_u2(store)
    _complete_u3(store)
    before = store.events
    with pytest.raises(module.PhaseIntegrityError, match="U4|output"):
        store.complete("U4", artifact_hashes=())
    assert store.events == before
    store.complete("U4", artifact_hashes=(_late_phase_hash("world-volume"),))
    before = store.events
    with pytest.raises(module.PhaseIntegrityError, match="U5|output"):
        store.complete(
            "U5",
            artifact_hashes=(_late_phase_hash("transformation-ledger"),),
        )
    assert store.events == before


def test_u12_requires_hash_verified_post_publish_authority_before_status_commit(
    u1_authority,
):
    import ultra_runtime.state_machine as module
    from ultra_runtime.status import RunStatusStore

    store = _store(module)
    _complete_through_u11(store, u1_authority)
    layout = _AUTHORITY_LAYOUT
    assert layout is not None
    layout.artifacts_dir.mkdir(parents=True, exist_ok=True)
    layout.delivery_dir.mkdir(parents=True, exist_ok=True)
    layout.validation_current_dir.mkdir(parents=True, exist_ok=True)

    delivery_specs = (
        ("CrossFrame-Ultra-完整文章.md", "final article\n", "article"),
        ("完整推演档案.md", "final dossier\n", "dossier"),
        ("工件索引.md", "final index\n", "artifact-index"),
    )
    delivery_refs = []
    for filename, text, schema_suffix in delivery_specs:
        path = layout.delivery_dir / filename
        path.write_text(text, encoding="utf-8")
        delivery_refs.append(
            {
                "path": path.relative_to(layout.run_dir).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "media_type": "text/markdown",
                "schema_id": f"crossframe.ultra.v82.{schema_suffix}",
                "phase_id": "U12",
            }
        )

    validator_set_sha256 = _late_phase_hash("validator-set")
    manifest = {
        "schema_id": "crossframe.ultra.v82.artifact-manifest",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": _binding(),
        "generated_at": "2026-08-02T00:00:01Z",
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "phase_chain_head_sha256": store.events[-1]["event_sha256"],
        "validator_set_sha256": validator_set_sha256,
        "artifacts": delivery_refs,
        "delivery_artifacts": [
            {
                "path": item["path"],
                "sha256": item["sha256"],
                "media_type": item["media_type"],
            }
            for item in delivery_refs
        ],
        "official_delivery_published": True,
    }
    manifest["content_sha256"] = _hash_without(manifest, "content_sha256")
    manifest_path = layout.artifacts_dir / "ultra-artifact-manifest.json"
    manifest_path.write_bytes(_canonical(manifest))
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    report = {
        "schema_id": "crossframe.ultra.v82.validator-report",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": _binding(),
        "generated_at": "2026-08-02T00:00:02Z",
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "attempt_id": "post-publish-1",
        "manifest_sha256": manifest_sha256,
        "validator_set_sha256": validator_set_sha256,
        "checks": [
            {
                "validator_id": "post-publish",
                "status": "pass",
                "error_codes": [],
                "artifact_refs": [item["path"] for item in delivery_refs],
            }
        ],
        "overall_status": "pass",
        "validated_at": "2026-08-02T00:00:02Z",
        "fresh_context": True,
    }
    report["content_sha256"] = _hash_without(report, "content_sha256")
    report_path = layout.validation_current_dir / "ultra-validator-report.json"
    report_path.write_bytes(_canonical(report))

    status_store = RunStatusStore(layout)
    created = status_store.create(datetime(2026, 8, 2, tzinfo=timezone.utc))
    running = status_store.transition(
        created,
        "running",
        datetime(2026, 8, 2, tzinfo=timezone.utc) + timedelta(seconds=1),
        current_phase="U12",
        last_complete_phase="U11",
    )
    output_hashes = (
        manifest_sha256,
        hashlib.sha256(report_path.read_bytes()).hexdigest(),
        *(item["sha256"] for item in delivery_refs),
    )
    event = store.complete(
        "U12",
        artifact_hashes=output_hashes,
        parent_event_sha256=store.events[-1]["event_sha256"],
    )
    assert tuple(event["output_artifact_hashes"]) == output_hashes
    assert store.current_phase == "U12"
    assert status_store.read() == running
    assert running.status == "running"
    assert running.last_complete_phase == "U11"
    assert running.validation_passed is False
