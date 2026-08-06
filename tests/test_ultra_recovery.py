from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
RUN_ID = "20260804T000000Z-010203040506"
NOW = datetime(2026, 8, 4, tzinfo=timezone.utc)
STAMP = "2026-08-02T00:00:00Z"
SOURCE_SHA256 = hashlib.sha256(
    (ROOT / "skills/crossframe-ultra/references/source-manifest.json").read_bytes()
).hexdigest()
U1_SOURCE_LOCK = Path("recovery/u1-authority/source-lock.json")
U1_SOURCE_COVERAGE = Path("recovery/u1-authority/source-coverage.json")
U1_READ_PLAN = Path("recovery/u1-authority/read-plan.json")
U1_READ_EVENTS = Path("artifacts/U00-U03-evidence/ultra-read-events.jsonl")
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


def _recovery_module():
    return importlib.import_module("ultra_runtime.recovery")


def _fixture_run(tmp_path: Path):
    import ultra_runtime.state_machine as state_machine
    from ultra_runtime.constants import current_version_binding
    from ultra_runtime.foundation import validate_host_capability_attestation
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout
    from ultra_runtime.schemas import compute_artifact_content_sha256

    policy = RootPolicy(tmp_path / "production", tmp_path / "test")
    layout = build_run_layout(RunMode.TEST, RUN_ID, policy)
    layout.input_dir.mkdir(parents=True)
    input_path = layout.input_dir / "AGENTS.md"
    shutil.copy2(ROOT / "AGENTS.md", input_path)
    input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
    requirements = {
        "filesystem": "required",
        "docx_parser": "not-applicable",
        "network": "required",
        "retrieval": "required",
        "validators": "required",
        "subagents": "not-applicable",
        "model_context": "required",
    }
    resource_limits = {
        "maximum_branches": 64,
        "maximum_retrieval_rounds_without_material_novelty": 2,
        "maximum_tool_retries": 3,
        "maximum_repair_attempts": 3,
    }
    attestation_document = {
        "schema_id": "crossframe.ultra.v82.host-capability-attestation",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": current_version_binding(),
        "generated_at": "2026-08-04T00:00:00Z",
        "phase_id": "U0",
        "request_sha256": input_sha256,
        "action_sha256": "a" * 64,
        "receipt_sha256": "b" * 64,
        "analysis_kind": "open-world",
        "run_mode": "test",
        "requirements": requirements,
        "measured_availability": {
            "filesystem": "available",
            "docx_parser": "unavailable",
            "network": "unavailable",
            "retrieval": "unavailable",
            "validators": "available",
            "subagents": "unavailable",
            "model_context": "available",
        },
        "providers": [
            {
                "provider_id": "recovery-host",
                "provider_kind": "runtime",
                "version": "1.0.0",
            }
        ],
        "tools": [
            {
                "tool_id": "local-filesystem",
                "provider_id": "recovery-host",
                "version": "1.0.0",
            }
        ],
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-04T00:00:00Z",
        "resource_limits": resource_limits,
        "measured_at": "2026-08-04T00:00:00Z",
        "proof_grade": "host-measured",
        "content_sha256": "0" * 64,
    }
    attestation_document["content_sha256"] = compute_artifact_content_sha256(
        attestation_document
    )
    attestation = validate_host_capability_attestation(attestation_document)
    attestation_path = (
        layout.artifacts_dir
        / "U00-U03-evidence/U00-host-capability-attestation.json"
    )
    attestation_path.parent.mkdir(parents=True, exist_ok=True)
    attestation_path.write_bytes(_canonical(attestation_document))
    contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": input_sha256,
        "analysis_kind": "open-world",
        "capability_attestation_sha256": attestation.artifact_sha256,
        "run_mode": "test",
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-04T00:00:00Z",
        "capabilities": requirements,
        "resource_limits": resource_limits,
    }
    store = state_machine.PhaseStore(
        run_id=RUN_ID,
        version_binding=current_version_binding(),
        source_sha256=SOURCE_SHA256,
        input_artifact_hashes=(input_sha256,),
        input_snapshot_sha256=input_sha256,
        evidence_cutoff="2026-08-04T00:00:00Z",
        now=NOW,
        run_contract=contract,
        capability_attestation=attestation,
        source_repository=ROOT,
        run_layout=layout,
    )
    store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    artifact_path = layout.artifacts_dir / "ultra-run-contract.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(_canonical(dict(store.run_contract)))
    assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == (
        store.run_contract_artifact_sha256
    )
    return policy, layout, store, artifact_path


def test_resume_uses_persisted_measured_availability_not_required_state(
    tmp_path: Path,
) -> None:
    recovery, _, layout, _, _, _ = _checkpoint(tmp_path)
    _interrupt(layout)

    restored = recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert restored.phase_store is not None
    assert restored.phase_store.capability_availability["network"] == "unavailable"
    assert restored.phase_store.run_contract["capabilities"]["network"] == "required"


def _checkpoint(tmp_path: Path):
    recovery = _recovery_module()
    policy, layout, store, artifact_path = _fixture_run(tmp_path)
    checkpoint = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(artifact_path,),
        now=NOW + timedelta(seconds=1),
    )
    return recovery, policy, layout, store, artifact_path, checkpoint


def _u0_repair_invalidation(store) -> dict[str, object]:
    from ultra_runtime import jsonio, schemas
    import ultra_runtime.state_machine as state_machine
    from ultra_runtime.constants import PHASES

    completed = store.events[-1]
    layout = store._run_layout
    source = layout.artifacts_dir / "ultra-run-contract.json"
    payload = source.read_bytes()
    attempt_root = layout.recovery_dir / "repair-attempts" / "VALIDATION-1"
    preserved_path = attempt_root / "superseded" / "ART-0001.bin"
    preserved_path.parent.mkdir(parents=True, exist_ok=True)
    preserved_path.write_bytes(payload)
    snapshot = {
        "schema_id": "crossframe.ultra.v82.repair-superseded-snapshot",
        "schema_version": 1,
        "run_id": store.run_id,
        "version_binding": copy.deepcopy(completed["version_binding"]),
        "generated_at": "2026-08-04T00:00:01Z",
        "content_sha256": "0" * 64,
        "phase_id": "U0",
        "repair_attempt_id": "VALIDATION-1",
        "artifacts": [
            {
                "original_path": source.relative_to(layout.run_dir).as_posix(),
                "snapshot_path": preserved_path.relative_to(layout.run_dir).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "media_type": "application/json",
            }
        ],
    }
    snapshot["content_sha256"] = schemas.compute_artifact_content_sha256(snapshot)
    snapshot_raw = jsonio.canonical_json_bytes(snapshot)
    (attempt_root / "superseded-snapshot.json").write_bytes(snapshot_raw)
    event = {
        "schema_id": state_machine.PHASE_EVENT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": store.run_id,
        "version_binding": copy.deepcopy(completed["version_binding"]),
        "generated_at": "2026-08-04T00:00:01Z",
        "content_sha256": "0" * 64,
        "phase_id": "U0",
        "event_type": "repair-invalidation",
        "parent_event_sha256": completed["event_sha256"],
        "input_artifact_hashes": copy.deepcopy(completed["input_artifact_hashes"]),
        "output_artifact_hashes": [],
        "source_sha256": completed["source_sha256"],
        "evidence_cutoff": completed["evidence_cutoff"],
        "run_contract_sha256": completed["run_contract_sha256"],
        "timestamp": "2026-08-04T00:00:01Z",
        "status": "invalidated",
        "failure_code": "repair:VALIDATION-1",
        "invalidated_phases": list(PHASES),
        "generation": 1,
        "reset_from_phase": "U0",
        "repair_attempt_id": "VALIDATION-1",
        "repair_plan_sha256": "1" * 64,
        "failed_report_sha256": "2" * 64,
        "preserved_snapshot_sha256": hashlib.sha256(snapshot_raw).hexdigest(),
        "superseded_event_sha256s": [completed["event_sha256"]],
        "event_sha256": "0" * 64,
    }
    event["content_sha256"] = state_machine._compute_event_content_sha256(event)
    event["event_sha256"] = state_machine.compute_event_sha256(event)
    return event


def _clone_layout(base_root: Path, tmp_path: Path, *, run_id: str):
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

    test_root = tmp_path / "test-control"
    shutil.copytree(base_root, test_root)
    policy = RootPolicy(tmp_path / "production-control", test_root)
    return build_run_layout(RunMode.TEST, run_id, policy)


def _interrupt(layout, *, status="interrupted"):
    from ultra_runtime.status import RunStatusStore

    statuses = RunStatusStore(layout)
    created = statuses.create(NOW)
    running = statuses.transition(created, "running", NOW + timedelta(seconds=1))
    stopped = statuses.transition(
        running,
        status,
        NOW + timedelta(seconds=2),
    )
    return statuses, stopped, (layout.run_dir / "run-status.json").read_bytes()


def _clear_issuer_registries(monkeypatch, source_integrity, state_machine):
    for module in (source_integrity, state_machine):
        for name, registry in vars(module).items():
            if name.startswith("_ISSUED_") and isinstance(registry, dict):
                monkeypatch.setattr(module, name, {})
    monkeypatch.setattr(source_integrity, "_READ_SESSION_RECORDS", {})


def _issue_test_recovered_u1_authority(source_integrity, snapshot):
    seal = object.__new__(source_integrity.U1AuthoritySeal)
    tuple_fields = {"input_artifact_hashes", "inputs"}
    for name, value in snapshot.items():
        stored = tuple(copy.deepcopy(value)) if name in tuple_fields else copy.deepcopy(value)
        object.__setattr__(seal, name, stored)
    fields = {
        "run_id": seal.run_id,
        "version_binding": seal.version_binding,
        "parent_event_sha256": seal.parent_event_sha256,
        "evidence_cutoff": seal.evidence_cutoff,
        "run_mode": seal.run_mode,
        "source_release_id": seal.source_release_id,
        "source_manifest_sha256": seal.source_manifest_sha256,
        "release_manifest_sha256": seal.release_manifest_sha256,
        "compatibility_matrix_sha256": seal.compatibility_matrix_sha256,
        "knowledge_report_sha256": seal.knowledge_report_sha256,
        "skill_tree_sha256": seal.skill_tree_sha256,
        "free_space_reserve_bytes": seal.free_space_reserve_bytes,
        "free_space_status": seal.free_space_status,
        "input_snapshot_sha256": seal.input_snapshot_sha256,
        "input_artifact_hashes": list(seal.input_artifact_hashes),
        "inputs": list(seal.inputs),
        "input_root": seal.input_root,
        "acl_status": seal.acl_status,
        "source_lock_artifact_sha256": seal.source_lock_artifact_sha256,
        "read_plan_artifact_sha256": seal.read_plan_artifact_sha256,
        "read_coverage_artifact_sha256": seal.read_coverage_artifact_sha256,
        "authorizes_phase": seal.authorizes_phase,
    }
    token, seal_sha256 = source_integrity._register_issuer_snapshot(
        source_integrity._ISSUED_U1_AUTHORITIES,
        fields,
    )
    object.__setattr__(seal, "_issuer_token", token)
    object.__setattr__(seal, "_seal_sha256", seal_sha256)
    return seal


def _install_disk_u1_validator(monkeypatch, recovery_run):
    import ultra_runtime.source_integrity as source_integrity

    expected = recovery_run["issued"]

    def validate_persisted_u1_authority(
        *,
        repo,
        run_layout,
        manifest,
        source_lock,
        read_plan,
        coverage,
        read_events,
        expected_run_id,
        expected_run_mode,
        expected_version_binding,
        expected_parent_event_sha256,
        expected_evidence_cutoff,
        expected_inputs,
        expected_request_sha256,
        expected_source_lock_sha256,
        expected_read_plan_sha256,
        expected_read_coverage_sha256,
    ):
        del repo, manifest
        if (
            source_lock != expected["source_lock"]
            or read_plan != expected["read_plan"]
            or coverage != expected["source_coverage"]
            or tuple(read_events) != expected["read_events"]
            or expected_run_id != expected["authority"].run_id
            or expected_run_mode != "test"
            or expected_version_binding
            != expected["authority"].version_binding
            or expected_parent_event_sha256
            != expected["authority"].parent_event_sha256
            or expected_evidence_cutoff != STAMP
            or list(expected_inputs) != expected["source_lock"]["inputs"]
            or expected_request_sha256 != expected["read_plan"]["request_sha256"]
            or expected_source_lock_sha256
            != expected["authority"].source_lock_artifact_sha256
            or expected_read_plan_sha256
            != expected["authority"].read_plan_artifact_sha256
            or expected_read_coverage_sha256
            != expected["authority"].read_coverage_artifact_sha256
        ):
            raise source_integrity.SourceLockError(
                "persisted U1 authority differs from trusted disk capture"
            )
        snapshot = copy.deepcopy(recovery_run["original_snapshot"])
        snapshot["input_root"] = run_layout.input_dir.resolve(strict=False)
        return _issue_test_recovered_u1_authority(source_integrity, snapshot)

    monkeypatch.setattr(
        source_integrity,
        "_validate_persisted_u1_authority",
        validate_persisted_u1_authority,
        raising=False,
    )


def _checkpoint_path(layout: object, phase_id: str) -> Path:
    for path in (layout.recovery_dir / "checkpoints").glob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("phase_id") == phase_id:
            return path
    raise AssertionError(f"checkpoint not found: {phase_id}")


def _reseal_u1_authority(layout, *, stale_role=False, changed_metadata=False):
    import ultra_runtime.jsonio as jsonio
    import ultra_runtime.state_machine as state_machine
    from ultra_runtime.schemas import compute_artifact_content_sha256

    source_lock_path = layout.run_dir / U1_SOURCE_LOCK
    coverage_path = layout.run_dir / U1_SOURCE_COVERAGE
    read_plan_path = layout.run_dir / U1_READ_PLAN
    read_events_path = layout.run_dir / U1_READ_EVENTS
    source_lock = jsonio.load_json_object(source_lock_path)
    coverage = jsonio.load_json_object(coverage_path)
    read_plan = jsonio.load_json_object(read_plan_path)
    read_events = [
        json.loads(line)
        for line in read_events_path.read_text(encoding="utf-8").splitlines()
    ]
    if stale_role:
        source_lock["knowledge_report_sha256"] = "9" * 64
        source_lock["content_sha256"] = compute_artifact_content_sha256(source_lock)
    source_lock_sha256 = hashlib.sha256(_canonical(source_lock)).hexdigest()
    for event in read_events:
        event["source_lock_sha256"] = source_lock_sha256
        if changed_metadata:
            event["execution_identity"]["user"] = "forged-user"
        payload = copy.deepcopy(event)
        payload.pop("read_event_sha256", None)
        event["read_event_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    coverage["source_lock_sha256"] = source_lock_sha256
    coverage["read_event_sha256s"] = [
        event["read_event_sha256"] for event in read_events
    ]
    read_plan["source_lock_sha256"] = source_lock_sha256
    read_plan["content_sha256"] = compute_artifact_content_sha256(read_plan)
    read_plan_sha256 = hashlib.sha256(_canonical(read_plan)).hexdigest()
    coverage_sha256 = hashlib.sha256(_canonical(coverage)).hexdigest()
    jsonio.atomic_write_json(source_lock_path, source_lock)
    jsonio.atomic_write_json(coverage_path, coverage)
    jsonio.atomic_write_json(read_plan_path, read_plan)
    jsonio.atomic_write_bytes(
        read_events_path,
        b"".join(_canonical(event) for event in read_events),
    )

    events_path = layout.recovery_dir / "phase-events.jsonl"
    phase_events = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
    ]
    u1_event = next(event for event in phase_events if event["phase_id"] == "U1")
    u1_event["output_artifact_hashes"] = [
        source_lock_sha256,
        read_plan_sha256,
        coverage_sha256,
    ]
    u1_event["content_sha256"] = state_machine._compute_event_content_sha256(u1_event)
    u1_event["event_sha256"] = state_machine.compute_event_sha256(u1_event)
    jsonio.atomic_write_bytes(
        events_path,
        b"".join(_canonical(event) for event in phase_events),
    )

    checkpoint_path = _checkpoint_path(layout, "U1")
    checkpoint = jsonio.load_json_object(checkpoint_path)
    checkpoint["phase_event_sha256"] = u1_event["event_sha256"]
    checkpoint["artifact_hashes"][0]["sha256"] = source_lock_sha256
    checkpoint["artifact_hashes"][1]["sha256"] = read_plan_sha256
    checkpoint["artifact_hashes"][2]["sha256"] = coverage_sha256
    checkpoint["content_sha256"] = compute_artifact_content_sha256(checkpoint)
    raw = _canonical(checkpoint)
    checkpoint_path.unlink()
    (checkpoint_path.parent / f"{hashlib.sha256(raw).hexdigest()}.json").write_bytes(raw)


@pytest.fixture(scope="module")
def u1_recovery_run(tmp_path_factory):
    from tests import test_ultra_state_machine as state_fixtures
    import ultra_runtime.jsonio as jsonio
    import ultra_runtime.state_machine as state_machine

    recovery = _recovery_module()
    context = state_fixtures.u1_prerequisite_context.__wrapped__(tmp_path_factory)
    store = state_fixtures._store(state_machine)
    issued = state_fixtures._issue_u1_recovery_snapshot(store, context)
    authority = issued["authority"]
    u1_event = store.complete(
        "U1",
        artifact_hashes=(
            authority.source_lock_artifact_sha256,
            authority.read_plan_artifact_sha256,
            authority.read_coverage_artifact_sha256,
        ),
        u1_authority=authority,
    )
    original_snapshot = store._accepted_u1_snapshot()
    layout = context["run_layout"]
    jsonio.atomic_write_json(
        layout.artifacts_dir / "ultra-run-contract.json",
        dict(store.run_contract),
    )
    jsonio.atomic_write_bytes(
        layout.artifacts_dir
        / "U00-U03-evidence/U00-host-capability-attestation.json",
        store.capability_attestation.artifact_bytes,
    )
    jsonio.atomic_write_json(layout.run_dir / U1_SOURCE_LOCK, issued["source_lock"])
    jsonio.atomic_write_json(layout.run_dir / U1_READ_PLAN, issued["read_plan"])
    jsonio.atomic_write_json(
        layout.run_dir / U1_SOURCE_COVERAGE,
        issued["source_coverage"],
    )
    jsonio.atomic_write_bytes(
        layout.run_dir / U1_READ_EVENTS,
        b"".join(jsonio.canonical_json_bytes(event) for event in issued["read_events"]),
    )
    checkpoint = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U1",
        boundary_ordinal=0,
        artifact_paths=(
            layout.run_dir / U1_SOURCE_LOCK,
            layout.run_dir / U1_READ_PLAN,
            layout.run_dir / U1_SOURCE_COVERAGE,
        ),
        now=NOW + timedelta(seconds=1),
    )
    read_plan_path = layout.run_dir / U1_READ_PLAN
    read_plan_persisted = read_plan_path.is_file()
    persisted_read_plan = (
        jsonio.load_json_object(read_plan_path) if read_plan_persisted else None
    )
    fixture_root = tmp_path_factory.mktemp("u1-recovery-snapshots")
    u1_root = fixture_root / "u1"
    shutil.copytree(layout.root, u1_root)

    state_fixtures._complete_u2(store)
    state_fixtures._complete_u3(store)
    evidence_path = layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
    jsonio.atomic_write_json(evidence_path, store.evidence_artifact)
    recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U3",
        boundary_ordinal=0,
        artifact_paths=(evidence_path,),
        now=NOW + timedelta(seconds=2),
    )
    u3_root = fixture_root / "u3"
    shutil.copytree(layout.root, u3_root)
    return {
        "u1_root": u1_root,
        "u3_root": u3_root,
        "issued": issued,
        "u1_event": u1_event,
        "u1_events": tuple(event for event in store.events if event["phase_id"] in {"U0", "U1"}),
        "original_snapshot": original_snapshot,
        "checkpoint": checkpoint,
        "read_plan_persisted": read_plan_persisted,
        "persisted_read_plan": persisted_read_plan,
    }


def test_checkpoint_is_content_addressed_disk_verified_and_selected(tmp_path):
    recovery, _, layout, _, _, checkpoint = _checkpoint(tmp_path)
    raw = _canonical(checkpoint)
    checkpoint_sha256 = hashlib.sha256(raw).hexdigest()
    path = layout.recovery_dir / "checkpoints" / f"{checkpoint_sha256}.json"

    assert path.read_bytes() == raw
    assert recovery.load_checkpoints(layout) == (checkpoint,)
    assert recovery.select_resume_checkpoint(layout) == checkpoint


def test_phase_store_replays_repair_invalidation_into_a_new_generation(
    tmp_path,
    monkeypatch,
):
    import ultra_runtime.state_machine as state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    _, _, store, _ = _fixture_run(tmp_path)
    original = store.events
    invalidation = _u0_repair_invalidation(store)

    store.replay_event(invalidation)
    replacement = store.complete(
        "U0",
        artifact_hashes=(store.run_contract_artifact_sha256,),
    )

    assert store.events[: len(original)] == original
    assert store.active_generation == 1
    assert store.current_phase == "U0"
    assert replacement["generation"] == 1
    assert replacement["parent_event_sha256"] == invalidation["event_sha256"]


def test_cancel_after_repair_targets_next_phase_of_active_generation(
    tmp_path,
    monkeypatch,
):
    import ultra_runtime.state_machine as state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    recovery, _, layout, store, _, _ = _checkpoint(tmp_path)
    invalidation = _u0_repair_invalidation(store)
    store.replay_event(invalidation)
    replacement = store.complete(
        "U0",
        artifact_hashes=(store.run_contract_artifact_sha256,),
    )
    authority, compatibility = recovery._validate_authority(layout)

    terminal = recovery._terminal_event(
        authority,
        store.events,
        reason="operator cancellation",
        now=NOW + timedelta(seconds=3),
    )

    assert compatibility == "resume"
    assert terminal["phase_id"] == "U1"
    assert terminal["parent_event_sha256"] == replacement["event_sha256"]
    assert terminal["generation"] == 1


def test_checkpoint_identity_allows_the_same_phase_in_a_new_generation(
    tmp_path,
    monkeypatch,
):
    import ultra_runtime.state_machine as state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    recovery, _, layout, store, artifact_path, original = _checkpoint(tmp_path)
    invalidation = _u0_repair_invalidation(store)
    store.replay_event(invalidation)
    replacement_event = store.complete(
        "U0",
        artifact_hashes=(store.run_contract_artifact_sha256,),
    )

    replacement = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(artifact_path,),
        now=NOW + timedelta(seconds=2),
    )

    assert original["generation"] == 0
    assert replacement["generation"] == 1
    assert replacement["phase_event_sha256"] == replacement_event["event_sha256"]
    assert recovery.load_checkpoints(layout) == (original, replacement)
    assert recovery.select_resume_checkpoint(layout) == replacement


def test_resume_restores_the_active_repair_generation(tmp_path, monkeypatch):
    from ultra_runtime import source_integrity, state_machine
    from ultra_runtime.status import RunStatusStore

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    real_measure_u1 = source_integrity.measure_u1_prerequisites

    def measure_u1_for_u0_resume(*args, **kwargs):
        measurement = real_measure_u1(*args, **kwargs)
        object.__setattr__(measurement, "ready", True)
        object.__setattr__(measurement, "missing", ())
        return measurement

    monkeypatch.setattr(
        source_integrity,
        "measure_u1_prerequisites",
        measure_u1_for_u0_resume,
    )
    monkeypatch.setattr(
        source_integrity,
        "verify_u1_prerequisites",
        lambda measurement: measurement,
    )
    recovery, _, layout, store, artifact_path, _ = _checkpoint(tmp_path)
    invalidation = _u0_repair_invalidation(store)
    store.replay_event(invalidation)
    replacement_event = store.complete(
        "U0",
        artifact_hashes=(store.run_contract_artifact_sha256,),
    )
    replacement_checkpoint = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(artifact_path,),
        now=NOW + timedelta(seconds=2),
    )
    statuses = RunStatusStore(layout)
    created = statuses.create(NOW)
    running = statuses.transition(created, "running", NOW + timedelta(seconds=3))
    statuses.transition(running, "interrupted", NOW + timedelta(seconds=4))

    resumed = recovery.resume_run(layout, now=NOW + timedelta(seconds=5))

    assert resumed.active_generation == 1
    assert resumed.checkpoint == replacement_checkpoint
    assert resumed.checkpoint["phase_event_sha256"] == replacement_event["event_sha256"]
    assert resumed.phase_store is not None
    assert resumed.phase_store.active_generation == 1
    assert resumed.phase_store.current_phase == "U0"
    assert resumed.phase_store.events[-2:] == (invalidation, replacement_event)


def test_resume_selection_rejects_a_superseded_generation_checkpoint(
    tmp_path,
    monkeypatch,
):
    import ultra_runtime.state_machine as state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    recovery, _, layout, store, _, _ = _checkpoint(tmp_path)
    invalidation = _u0_repair_invalidation(store)
    store.replay_event(invalidation)
    events_path = layout.recovery_dir / "phase-events.jsonl"
    recovery._sync_events(events_path, store.events)

    with pytest.raises(recovery.RecoveryStateError, match="active|resumable"):
        recovery.select_resume_checkpoint(layout)


def test_resume_keeps_invalidation_but_drops_uncheckpointed_repair_completion() -> None:
    recovery = _recovery_module()
    events = [
        {
            "phase_id": f"U{number}",
            "status": "complete",
            "event_sha256": f"old-U{number}",
        }
        for number in range(12)
    ]
    invalidation = {
        "phase_id": "U10",
        "status": "invalidated",
        "reset_from_phase": "U10",
        "generation": 1,
        "event_sha256": "repair-invalidation",
    }
    uncheckpointed = {
        "phase_id": "U10",
        "status": "complete",
        "generation": 1,
        "event_sha256": "new-U10",
    }
    checkpoint = {
        "phase_id": "U9",
        "boundary_kind": "phase",
        "generation": 0,
        "phase_event_sha256": "old-U9",
    }

    durable = recovery._events_for_resume(
        (*events, invalidation, uncheckpointed),
        checkpoint,
    )

    assert durable == (*events, invalidation)


def test_checkpoint_without_supplied_lease_owns_one_for_all_commits(
    tmp_path,
    monkeypatch,
) -> None:
    from ultra_runtime import locks, state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    recovery = _recovery_module()
    _, layout, store, artifact_path = _fixture_run(tmp_path)
    observed = []
    real_write_immutable = recovery._write_immutable

    def observe_immutable_commit(path, value):
        observed.append(locks._read_lease(layout))
        return real_write_immutable(path, value)

    monkeypatch.setattr(recovery, "_write_immutable", observe_immutable_commit)
    checkpoint = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(artifact_path,),
        now=NOW + timedelta(seconds=1),
    )

    assert checkpoint["phase_id"] == "U0"
    assert observed
    assert len({item.owner_nonce for item in observed}) == 1
    assert not locks._lease_path(layout).exists()


def test_corrupt_artifact_rejects_checkpoint_instead_of_resuming(tmp_path):
    recovery, _, layout, _, artifact_path, _ = _checkpoint(tmp_path)
    artifact_path.write_bytes(b"tampered\n")

    with pytest.raises(recovery.RecoveryIntegrityError, match="artifact|hash"):
        recovery.load_checkpoints(layout)
    with pytest.raises(recovery.RecoveryIntegrityError, match="artifact|hash"):
        recovery.select_resume_checkpoint(layout)


def test_half_written_checkpoint_is_quarantined_and_never_selected(tmp_path):
    recovery, _, layout, _, _, checkpoint = _checkpoint(tmp_path)
    incomplete = layout.recovery_dir / "checkpoints" / f"{'f' * 64}.json"
    incomplete.write_bytes(b'{"schema_id":')

    assert recovery.load_checkpoints(layout) == (checkpoint,)
    assert not incomplete.exists()
    assert tuple((layout.recovery_dir / "quarantine").glob("*.json"))


def test_duplicate_logical_checkpoint_slot_invalidates_the_run(tmp_path):
    recovery, _, layout, _, _, checkpoint = _checkpoint(tmp_path)
    from ultra_runtime.schemas import compute_artifact_content_sha256

    duplicate = copy.deepcopy(checkpoint)
    duplicate["generated_at"] = "2026-08-04T00:00:02Z"
    duplicate["content_sha256"] = compute_artifact_content_sha256(duplicate)
    raw = _canonical(duplicate)
    path = layout.recovery_dir / "checkpoints" / (
        hashlib.sha256(raw).hexdigest() + ".json"
    )
    path.write_bytes(raw)

    with pytest.raises(recovery.RecoveryIntegrityError, match="duplicate|logical"):
        recovery.load_checkpoints(layout)


def test_resume_uses_last_full_boundary_and_cancel_is_terminal(tmp_path, monkeypatch):
    from ultra_runtime import locks, source_integrity, state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    real_measure_u1 = source_integrity.measure_u1_prerequisites

    def measure_u1_for_u0_resume(*args, **kwargs):
        measurement = real_measure_u1(*args, **kwargs)
        object.__setattr__(measurement, "ready", True)
        object.__setattr__(measurement, "missing", ())
        return measurement

    monkeypatch.setattr(
        source_integrity,
        "measure_u1_prerequisites",
        measure_u1_for_u0_resume,
    )
    monkeypatch.setattr(
        source_integrity,
        "verify_u1_prerequisites",
        lambda measurement: measurement,
    )
    recovery, _, layout, store, _, checkpoint = _checkpoint(tmp_path)
    from ultra_runtime.status import RunStatusStore

    statuses = RunStatusStore(layout)
    created = statuses.create(NOW)
    running = statuses.transition(created, "running", NOW + timedelta(seconds=1))
    statuses.transition(running, "interrupted", NOW + timedelta(seconds=2))

    result = recovery.resume_run(layout, now=NOW + timedelta(seconds=3))
    assert result.outcome == "resume"
    assert result.checkpoint == checkpoint
    assert result.status.status == "running"
    assert result.status.tools_allowed is True

    cancelled = recovery.cancel_run(
        layout,
        reason="user requested cancellation",
        now=NOW + timedelta(seconds=4),
    )
    assert cancelled.status == "cancelled"
    assert cancelled.tools_allowed is False
    with pytest.raises(
        (state_machine.PhaseTransitionError, locks.CancelledRunError),
        match="terminal|cancel",
    ):
        store.complete("U1", artifact_hashes=(hashlib.sha256(b"late").hexdigest(),))
    with pytest.raises(recovery.RecoveryStateError, match="cancelled|terminal"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=5))


@pytest.mark.parametrize("terminal_status", ("failed", "blocked"))
def test_new_cancel_intent_rejects_verified_terminal_event_tail(
    tmp_path: Path,
    terminal_status: str,
) -> None:
    recovery, _, layout, store, _, _ = _checkpoint(tmp_path)
    from ultra_runtime import locks

    terminate = store.fail if terminal_status == "failed" else store.blocked
    terminate("U1", failure_code=f"terminal-{terminal_status}")
    _, _, _, events_path, lock_path = recovery._paths(layout)
    with recovery._exclusive_path_lock(lock_path):
        recovery._sync_events(events_path, store.events)

    with pytest.raises(locks.LeaseConflictError, match="terminal|event"):
        locks.request_cancel(
            layout,
            reason="too late after terminal phase event",
            now=NOW + timedelta(seconds=2),
        )

    assert locks.load_cancel_intent(layout) is None


def test_partial_cancellation_blocks_new_lease_and_retry_converges(
    tmp_path,
    monkeypatch,
):
    import ultra_runtime.state_machine as state_machine

    monkeypatch.setattr(state_machine, "PRODUCTION_ROOT", tmp_path / "production")
    recovery, _, layout, _, _, _ = _checkpoint(tmp_path)
    from ultra_runtime import locks
    from ultra_runtime.status import RunStatusStore

    statuses = RunStatusStore(layout)
    created = statuses.create(NOW)
    statuses.transition(created, "running", NOW + timedelta(seconds=1))
    real_transition = recovery.RunStatusStore.transition

    def fail_status_transition(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("injected status write failure")

    monkeypatch.setattr(recovery.RunStatusStore, "transition", fail_status_transition)
    with pytest.raises(recovery.RecoveryStateError, match="status cancellation"):
        recovery.cancel_run(
            layout,
            reason="user requested cancellation",
            now=NOW + timedelta(seconds=2),
        )

    events_path = layout.recovery_dir / "phase-events.jsonl"
    persisted_events = [
        json.loads(line)
        for line in events_path.read_text("utf-8").splitlines()
    ]
    assert persisted_events[-1]["status"] == "cancelled"
    assert statuses.read().status == "running"

    from ultra_runtime import jsonio
    from ultra_runtime.schemas import compute_artifact_content_sha256

    authority_path = layout.recovery_dir / "run-authority.json"
    authority_bytes = authority_path.read_bytes()
    authority = jsonio.load_json_object(authority_path)
    malformed_ref = dict(authority["input_refs"][0])
    malformed_ref.pop("media_type")
    authority["input_refs"][0] = malformed_ref
    authority["content_sha256"] = compute_artifact_content_sha256(authority)
    jsonio.atomic_write_json(authority_path, authority)
    with pytest.raises(locks.CancelledRunError):
        locks.acquire_run_lease(
            layout,
            NOW + timedelta(seconds=3),
            timedelta(seconds=30),
        )
    jsonio.atomic_write_bytes(authority_path, authority_bytes)

    input_path = layout.input_dir / "AGENTS.md"
    original_input = input_path.read_bytes()
    input_path.write_bytes(b"tampered after durable cancellation\n")
    with pytest.raises(locks.CancelledRunError):
        locks.acquire_run_lease(
            layout,
            NOW + timedelta(seconds=3),
            timedelta(seconds=30),
        )
    input_path.write_bytes(original_input)

    monkeypatch.setattr(recovery.RunStatusStore, "transition", real_transition)
    cancelled = recovery.cancel_run(
        layout,
        reason="user requested cancellation",
        now=NOW + timedelta(seconds=4),
    )
    repeated = recovery.cancel_run(
        layout,
        reason="user requested cancellation",
        now=NOW + timedelta(seconds=5),
    )

    assert cancelled.status == repeated.status == "cancelled"
    assert cancelled.tools_allowed is repeated.tools_allowed is False
    final_events = [
        json.loads(line)
        for line in events_path.read_text("utf-8").splitlines()
    ]
    assert sum(event["status"] == "cancelled" for event in final_events) == 1


@pytest.mark.parametrize(
    "prior_status",
    ("created", "running", "interrupted", "blocked", "needs_attention"),
)
def test_cancel_pre_u0_without_recovery_authority_is_status_only_and_idempotent(
    tmp_path,
    prior_status,
):
    recovery = _recovery_module()
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout
    from ultra_runtime.status import RunStatusStore

    policy = RootPolicy(tmp_path / "production", tmp_path / "test")
    layout = build_run_layout(RunMode.TEST, RUN_ID, policy)
    statuses = RunStatusStore(layout)
    status = statuses.create(NOW)
    if prior_status == "interrupted":
        running = statuses.transition(
            status,
            "running",
            NOW + timedelta(seconds=1),
        )
        status = statuses.transition(
            running,
            prior_status,
            NOW + timedelta(seconds=2),
            reason="pre-U0 interrupted",
        )
    elif prior_status != "created":
        status = statuses.transition(
            status,
            prior_status,
            NOW + timedelta(seconds=1),
            reason=None if prior_status == "running" else f"pre-U0 {prior_status}",
        )
    status_path = layout.run_dir / "run-status.json"
    events_path = layout.recovery_dir / "phase-events.jsonl"
    status_before = status_path.read_bytes()
    cancelled = recovery.cancel_run(
        layout,
        reason="user requested cancellation",
        now=NOW + timedelta(seconds=3),
    )
    cancelled_bytes = status_path.read_bytes()
    repeated = recovery.cancel_run(
        layout,
        reason="ignored repeated reason",
        now=NOW + timedelta(seconds=4),
    )

    assert status_before != cancelled_bytes
    assert cancelled.status == "cancelled"
    assert cancelled.previous_status == prior_status
    assert cancelled.current_phase == "U0"
    assert cancelled.last_complete_phase is None
    assert cancelled.reason == "user requested cancellation"
    assert cancelled.tools_allowed is False
    assert cancelled.created_at == status.created_at
    assert cancelled.updated_at == "2026-08-04T00:00:03Z"
    assert cancelled.revision == status.revision + 1
    assert statuses.read() == cancelled
    assert repeated == cancelled
    assert status_path.read_bytes() == cancelled_bytes
    assert not events_path.exists()
    assert not (layout.recovery_dir / "run-authority.json").exists()
    assert not (layout.recovery_dir / "checkpoints").exists()
    assert not (layout.artifacts_dir / "ultra-run-contract.json").exists()


def test_cancel_intent_converges_after_live_writer_releases(tmp_path) -> None:
    recovery = _recovery_module()
    from ultra_runtime import locks
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout
    from ultra_runtime.status import RunStatusStore

    policy = RootPolicy(tmp_path / "production", tmp_path / "test")
    layout = build_run_layout(RunMode.TEST, RUN_ID, policy)
    statuses = RunStatusStore(layout)
    created = statuses.create(NOW)
    running = statuses.transition(
        created,
        "running",
        NOW + timedelta(seconds=1),
    )
    writer = locks.acquire_run_lease(
        layout,
        NOW + timedelta(seconds=2),
        timedelta(seconds=30),
    )
    before = statuses.path.read_bytes()

    pending = recovery.cancel_run(
        layout,
        reason="operator requested cancellation",
        now=NOW + timedelta(seconds=3),
    )

    assert pending == running
    assert statuses.path.read_bytes() == before
    assert locks.load_cancel_intent(layout) is not None
    assert locks._read_lease(layout) == writer

    locks.release_run_lease(layout, writer)
    cancelled = recovery.cancel_run(
        layout,
        reason="ignored after immutable intent",
        now=NOW + timedelta(seconds=4),
    )
    cancelled_bytes = statuses.path.read_bytes()
    repeated = recovery.cancel_run(
        layout,
        reason="ignored repeated reason",
        now=NOW + timedelta(seconds=5),
    )

    assert cancelled.status == repeated.status == "cancelled"
    assert cancelled.reason == repeated.reason == "operator requested cancellation"
    assert statuses.path.read_bytes() == cancelled_bytes
    assert not locks._lease_path(layout).exists()


@pytest.mark.parametrize(
    "existing_bytes",
    (
        b"",
        _canonical({"event": "one"})[:-1],
    ),
    ids=("empty", "half-line"),
)
def test_sync_events_rejects_incomplete_existing_journal(tmp_path, existing_bytes):
    recovery = _recovery_module()
    path = tmp_path / "phase-events.jsonl"
    events = ({"event": "one"}, {"event": "two"})
    path.write_bytes(existing_bytes)

    with pytest.raises(recovery.RecoveryIntegrityError, match="journal|event"):
        recovery._sync_events(path, events)

    assert path.read_bytes() == existing_bytes


def test_sync_events_appends_a_whole_event_prefix_and_is_idempotent(tmp_path):
    recovery = _recovery_module()
    path = tmp_path / "phase-events.jsonl"
    events = ({"event": "one"}, {"event": "two"})
    path.write_bytes(_canonical(events[0]))

    recovery._sync_events(path, events)
    expected = b"".join(_canonical(event) for event in events)
    assert path.read_bytes() == expected

    recovery._sync_events(path, events)
    assert path.read_bytes() == expected


@pytest.mark.parametrize("prior_status", ("interrupted", "needs_attention"))
def test_resume_hydrates_before_status_authorization(
    tmp_path,
    monkeypatch,
    prior_status,
):
    recovery, _, layout, _, _, _ = _checkpoint(tmp_path)
    statuses, stopped, before = _interrupt(layout, status=prior_status)

    def fail_hydration(*args, **kwargs):
        del args, kwargs
        raise recovery.RecoveryIntegrityError("injected hydration failure")

    monkeypatch.setattr(recovery, "_restore_phase_store", fail_hydration)
    with pytest.raises(recovery.RecoveryIntegrityError, match="injected hydration"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert statuses.read() == stopped
    assert (layout.run_dir / "run-status.json").read_bytes() == before


def test_u1_checkpoint_persists_the_fixed_deterministic_read_plan(u1_recovery_run):
    assert u1_recovery_run["read_plan_persisted"] is True
    assert u1_recovery_run["persisted_read_plan"] == u1_recovery_run["issued"][
        "read_plan"
    ]
    assert u1_recovery_run["persisted_read_plan"]["source_unit_count"] == 4_753
    assert len(u1_recovery_run["persisted_read_plan"]["source_unit_ids"]) == 4_753


def test_registry_cleared_u1_resume_restores_authority_and_completes_u2_u3(
    tmp_path,
    monkeypatch,
    u1_recovery_run,
):
    from tests import test_ultra_state_machine as state_fixtures
    import ultra_runtime.source_integrity as source_integrity
    import ultra_runtime.state_machine as state_machine

    recovery = _recovery_module()
    layout = _clone_layout(
        u1_recovery_run["u1_root"],
        tmp_path,
        run_id=u1_recovery_run["original_snapshot"]["run_id"],
    )
    _interrupt(layout)
    _clear_issuer_registries(monkeypatch, source_integrity, state_machine)
    _install_disk_u1_validator(monkeypatch, u1_recovery_run)

    resumed = recovery.resume_run(layout, now=NOW + timedelta(seconds=3))
    assert resumed.checkpoint["phase_id"] == "U1"
    assert resumed.phase_store is not None
    restored_snapshot = resumed.phase_store._accepted_u1_snapshot()

    def snapshot_bytes(snapshot):
        serializable = copy.deepcopy(snapshot)
        serializable["input_root"] = str(Path(serializable["input_root"]).resolve())
        return _canonical(serializable)

    restored_bytes = snapshot_bytes(restored_snapshot)
    original_snapshot = copy.deepcopy(u1_recovery_run["original_snapshot"])
    original_snapshot["input_root"] = layout.input_dir.resolve(strict=False)
    original_bytes = snapshot_bytes(original_snapshot)
    assert restored_snapshot == original_snapshot
    assert restored_bytes == original_bytes
    assert hashlib.sha256(restored_bytes).hexdigest() == hashlib.sha256(
        original_bytes
    ).hexdigest()
    assert resumed.phase_store.events[-1] == u1_recovery_run["u1_event"]
    assert resumed.phase_store.u1_coverage_sha256 == (
        original_snapshot["read_coverage_artifact_sha256"]
    )

    state_fixtures._complete_u2(resumed.phase_store)
    state_fixtures._complete_u3(resumed.phase_store)
    assert [event["phase_id"] for event in resumed.phase_store.events] == [
        "U0",
        "U1",
        "U2",
        "U3",
    ]


def test_completed_u1_in_u3_chain_requires_exact_u1_checkpoint(
    tmp_path,
    monkeypatch,
    u1_recovery_run,
):
    recovery = _recovery_module()
    layout = _clone_layout(
        u1_recovery_run["u3_root"],
        tmp_path,
        run_id=u1_recovery_run["original_snapshot"]["run_id"],
    )
    _checkpoint_path(layout, "U1").unlink()
    statuses, interrupted, before = _interrupt(layout)
    _install_disk_u1_validator(monkeypatch, u1_recovery_run)

    with pytest.raises(recovery.RecoveryIntegrityError, match="U1|checkpoint"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert statuses.read() == interrupted
    assert (layout.run_dir / "run-status.json").read_bytes() == before


def test_missing_u1_read_plan_fails_without_authorizing_tools(
    tmp_path,
    monkeypatch,
    u1_recovery_run,
):
    recovery = _recovery_module()
    layout = _clone_layout(
        u1_recovery_run["u1_root"],
        tmp_path,
        run_id=u1_recovery_run["original_snapshot"]["run_id"],
    )
    (layout.run_dir / U1_READ_PLAN).unlink()
    statuses, interrupted, before = _interrupt(layout)
    _install_disk_u1_validator(monkeypatch, u1_recovery_run)

    with pytest.raises(recovery.RecoveryIntegrityError, match=r"read[- ]plan|U1"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert statuses.read() == interrupted
    assert (layout.run_dir / "run-status.json").read_bytes() == before


def test_missing_u1_read_events_fails_without_authorizing_tools(
    tmp_path,
    monkeypatch,
    u1_recovery_run,
):
    recovery = _recovery_module()
    layout = _clone_layout(
        u1_recovery_run["u1_root"],
        tmp_path,
        run_id=u1_recovery_run["original_snapshot"]["run_id"],
    )
    (layout.run_dir / U1_READ_EVENTS).unlink()
    statuses, interrupted, before = _interrupt(layout)
    _install_disk_u1_validator(monkeypatch, u1_recovery_run)

    with pytest.raises(recovery.RecoveryIntegrityError, match="read event|U1"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert statuses.read() == interrupted
    assert (layout.run_dir / "run-status.json").read_bytes() == before


def test_missing_disk_u1_validator_fails_without_authorizing_tools(
    tmp_path,
    monkeypatch,
    u1_recovery_run,
):
    import ultra_runtime.source_integrity as source_integrity

    recovery = _recovery_module()
    layout = _clone_layout(
        u1_recovery_run["u1_root"],
        tmp_path,
        run_id=u1_recovery_run["original_snapshot"]["run_id"],
    )
    statuses, interrupted, before = _interrupt(layout)
    monkeypatch.delattr(
        source_integrity,
        "_validate_persisted_u1_authority",
        raising=False,
    )

    with pytest.raises(recovery.RecoveryIntegrityError, match="U1|validator"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert statuses.read() == interrupted
    assert (layout.run_dir / "run-status.json").read_bytes() == before


@pytest.mark.parametrize("tamper", ("stale-role", "read-metadata"))
def test_resealed_u1_tamper_fails_without_authorizing_tools(
    tmp_path,
    monkeypatch,
    u1_recovery_run,
    tamper,
):
    recovery = _recovery_module()
    layout = _clone_layout(
        u1_recovery_run["u1_root"],
        tmp_path,
        run_id=u1_recovery_run["original_snapshot"]["run_id"],
    )
    _reseal_u1_authority(
        layout,
        stale_role=tamper == "stale-role",
        changed_metadata=tamper == "read-metadata",
    )
    statuses, interrupted, before = _interrupt(layout)
    _install_disk_u1_validator(monkeypatch, u1_recovery_run)

    with pytest.raises(recovery.RecoveryIntegrityError, match="U1|authority|capture"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=3))

    assert statuses.read() == interrupted
    assert (layout.run_dir / "run-status.json").read_bytes() == before


def test_direct_restore_rejects_fabricated_u1_mapping(u1_recovery_run):
    from tests import test_ultra_state_machine as state_fixtures
    import ultra_runtime.state_machine as state_machine

    store = state_fixtures._store(state_machine)
    fabricated = copy.deepcopy(u1_recovery_run["original_snapshot"])
    with pytest.raises((TypeError, state_machine.PhaseIntegrityError)):
        store._restore_validated_recovery_events(
            u1_recovery_run["u1_events"],
            u1_authority=fabricated,
        )
    assert store.events == ()


def test_recovery_fork_is_version_migration_only_and_parent_is_immutable(
    tmp_path,
    monkeypatch,
):
    recovery, policy, layout, _, _, checkpoint = _checkpoint(tmp_path)
    from ultra_runtime.paths import RunMode

    before = {
        path.relative_to(layout.run_dir): path.read_bytes()
        for path in layout.run_dir.rglob("*")
        if path.is_file()
    }
    monkeypatch.setattr(recovery, "resolve_compatibility", lambda *args: "fork-required")
    forked = recovery.fork_run(
        layout,
        mode=RunMode.TEST,
        policy=policy,
        reason="known framework revision migration",
        now=NOW + timedelta(seconds=10),
        entropy=b"child-run",
    )

    after = {
        path.relative_to(layout.run_dir): path.read_bytes()
        for path in layout.run_dir.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert forked.parent_checkpoint == checkpoint
    migration_path = forked.layout.recovery_dir / "ultra-run-migration.json"
    assert migration_path.is_file()
    assert forked.migration["compatibility_result"] == "fork-required"
    assert forked.migration["fork_reason"] == "known framework revision migration"
    assert forked.migration["parent_run_id"] == RUN_ID
    assert forked.migration["frozen_input_refs"]
    assert forked.migration["inherited_artifact_hashes"]


def test_exact_compatible_run_cannot_use_the_migration_fork_api(tmp_path):
    recovery, policy, layout, _, _, _ = _checkpoint(tmp_path)
    from ultra_runtime.paths import RunMode

    with pytest.raises(recovery.RecoveryCompatibilityError, match="fork-required"):
        recovery.fork_run(
            layout,
            mode=RunMode.TEST,
            policy=policy,
            reason="not a version migration",
            now=NOW + timedelta(seconds=10),
            entropy=b"rejected-child",
        )


def test_evidence_fork_preserves_parent_and_reopens_child_at_u0(tmp_path) -> None:
    from tests.test_ultra_repair import _prepare_attempt, _write_recovery_chain
    from ultra_runtime import jsonio, recovery
    from ultra_runtime.paths import RootPolicy, RunMode
    from ultra_runtime.status import RunStatusStore

    parent_layout, _ = _prepare_attempt(tmp_path / "parent")
    evidence_path = parent_layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    evidence_sha256 = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    events = _write_recovery_chain(
        parent_layout,
        through_phase="U3",
        output_overrides={"U3": (evidence_sha256,)},
    )
    parent_before = {
        path.relative_to(parent_layout.run_dir): path.read_bytes()
        for path in parent_layout.run_dir.rglob("*")
        if path.is_file()
    }
    policy = RootPolicy(tmp_path / "children-production", tmp_path / "children-test")
    new_evidence = b"new admitted evidence candidate\n"

    child = recovery.fork_for_new_evidence(
        parent_layout,
        mode=RunMode.TEST,
        policy=policy,
        evidence_bytes=new_evidence,
        now=NOW + timedelta(days=1),
        entropy=b"evidence-child",
    )

    assert child.parent_evidence_sha256 == evidence_sha256
    assert child.parent_u3_event_sha256 == events[-1]["event_sha256"]
    assert child.evidence_cutoff > "2026-08-04T04:00:00Z"
    assert {
        path.relative_to(parent_layout.run_dir): path.read_bytes()
        for path in parent_layout.run_dir.rglob("*")
        if path.is_file()
    } == parent_before
    assert (child.layout.input_dir / "request.bin").read_bytes() == (
        parent_layout.input_dir / "request.bin"
    ).read_bytes()
    assert (child.layout.input_dir / "new-evidence.bin").read_bytes() == new_evidence
    assert not (child.layout.artifacts_dir / "U09-U10-verdict").exists()
    lineage = jsonio.load_json_object(
        child.layout.recovery_dir / "evidence-lineage-request.json"
    )
    assert lineage["status"] == "pending-u0-attestation"
    assert lineage["parent_run_id"] == parent_layout.run_dir.name
    assert lineage["parent_u3_event_sha256"] == events[-1]["event_sha256"]
    assert lineage["parent_evidence_sha256"] == evidence_sha256
    assert lineage["new_evidence_ref"]["path"] == "input/new-evidence.bin"
    fork_authority_path = (
        child.layout.input_dir
        / f"evidence-lineage-fork-authority-{child.run_id}.json"
    )
    fork_authority = jsonio.load_json_object(fork_authority_path)
    assert fork_authority["lineage_request_sha256"] == hashlib.sha256(
        (child.layout.recovery_dir / "evidence-lineage-request.json").read_bytes()
    ).hexdigest()
    assert fork_authority["parent_u3_event_sha256"] == events[-1]["event_sha256"]
    assert RunStatusStore(child.layout).read().fork_authority_sha256 == (
        hashlib.sha256(fork_authority_path.read_bytes()).hexdigest()
    )
    recovery.validate_instance("ultra-evidence-lineage.schema.json", lineage)


def test_evidence_fork_rejects_rehashed_pending_parent_provenance(
    tmp_path,
) -> None:
    from tests.test_ultra_repair import _prepare_attempt, _write_recovery_chain
    from ultra_runtime import foundation, jsonio, recovery, schemas
    from ultra_runtime.paths import RootPolicy, RunMode

    parent_layout, _ = _prepare_attempt(tmp_path / "parent")
    evidence_path = parent_layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    evidence_sha256 = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    _write_recovery_chain(
        parent_layout,
        through_phase="U3",
        output_overrides={"U3": (evidence_sha256,)},
    )
    child = recovery.fork_for_new_evidence(
        parent_layout,
        mode=RunMode.TEST,
        policy=RootPolicy(
            tmp_path / "children-production",
            tmp_path / "children-test",
        ),
        evidence_bytes=b"new admitted evidence candidate\n",
        now=NOW + timedelta(days=1),
        entropy=b"evidence-child-forged-parent",
    )
    request_path = child.layout.recovery_dir / "evidence-lineage-request.json"
    forged = jsonio.load_json_object(request_path)
    forged.update(
        {
            "parent_run_id": "20260803T000000Z-abcdef123456",
            "parent_u3_event_sha256": "c" * 64,
            "parent_evidence_sha256": "d" * 64,
        }
    )
    forged["content_sha256"] = schemas.compute_artifact_content_sha256(forged)
    jsonio.atomic_write_json(request_path, forged)
    request_sha256 = hashlib.sha256(
        (child.layout.input_dir / "request.bin").read_bytes()
    ).hexdigest()
    jsonio.atomic_write_json(
        child.layout.input_dir / "request-metadata.json",
        {
            "request_sha256": request_sha256,
            "request_size": (child.layout.input_dir / "request.bin").stat().st_size,
        },
    )
    foundation.seal_input_inventory(
        child.layout,
        request_sha256=request_sha256,
        material_files=(),
        now=NOW + timedelta(days=1),
    )

    with pytest.raises(
        foundation.FoundationInputError,
        match="evidence lineage fork authority",
    ):
        foundation.advance_u0(
            child.layout,
            repo=ROOT,
            now=NOW + timedelta(days=1, seconds=1),
        )


def test_evidence_fork_identity_rejects_resealed_other_parent_root(
    tmp_path,
) -> None:
    from tests.test_ultra_repair import _prepare_attempt, _write_recovery_chain
    from ultra_runtime import foundation, jsonio, recovery, schemas
    from ultra_runtime.paths import RootPolicy, RunMode

    parent_layout, _ = _prepare_attempt(tmp_path / "parent")
    evidence_path = parent_layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    evidence_sha256 = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    _write_recovery_chain(
        parent_layout,
        through_phase="U3",
        output_overrides={"U3": (evidence_sha256,)},
    )
    other_parent_layout, _ = _prepare_attempt(tmp_path / "other-parent")
    other_evidence_path = (
        other_parent_layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    )
    other_evidence_sha256 = hashlib.sha256(
        other_evidence_path.read_bytes()
    ).hexdigest()
    _write_recovery_chain(
        other_parent_layout,
        through_phase="U3",
        output_overrides={"U3": (other_evidence_sha256,)},
    )
    child = recovery.fork_for_new_evidence(
        parent_layout,
        mode=RunMode.TEST,
        policy=RootPolicy(
            tmp_path / "children-production",
            tmp_path / "children-test",
        ),
        evidence_bytes=b"new admitted evidence candidate\n",
        now=NOW + timedelta(days=1),
        entropy=b"evidence-child-resealed-anchor",
    )
    fork_authority_path = (
        child.layout.input_dir
        / f"evidence-lineage-fork-authority-{child.run_id}.json"
    )
    fork_authority = jsonio.load_json_object(fork_authority_path)
    fork_authority["parent_root"] = str(other_parent_layout.root)
    fork_authority["content_sha256"] = schemas.compute_artifact_content_sha256(
        fork_authority
    )
    jsonio.atomic_write_json(fork_authority_path, fork_authority)
    status_path = child.layout.run_dir / "run-status.json"
    status = jsonio.load_json_object(status_path)
    status["fork_authority_sha256"] = hashlib.sha256(
        fork_authority_path.read_bytes()
    ).hexdigest()
    status["content_sha256"] = schemas.compute_artifact_content_sha256(status)
    jsonio.atomic_write_json(status_path, status)
    request_sha256 = hashlib.sha256(
        (child.layout.input_dir / "request.bin").read_bytes()
    ).hexdigest()
    jsonio.atomic_write_json(
        child.layout.input_dir / "request-metadata.json",
        {
            "request_sha256": request_sha256,
            "request_size": (child.layout.input_dir / "request.bin").stat().st_size,
        },
    )
    foundation.seal_input_inventory(
        child.layout,
        request_sha256=request_sha256,
        material_files=(),
        now=NOW + timedelta(days=1),
    )

    with pytest.raises(
        foundation.FoundationInputError,
        match="evidence lineage fork authority",
    ):
        foundation.advance_u0(
            child.layout,
            repo=ROOT,
            now=NOW + timedelta(days=1, seconds=1),
        )


def test_evidence_fork_recovers_lineage_finalization_after_u0_checkpoint(
    tmp_path,
    monkeypatch,
) -> None:
    from tests.test_ultra_foundation import (
        _accept_capability_result,
        _capability_result,
    )
    from tests.test_ultra_repair import _prepare_attempt, _write_recovery_chain
    from tests.test_ultra_source_read_coverage import _write_release_manifest
    from ultra_runtime import artifacts, foundation, jsonio, recovery, source_integrity
    from ultra_runtime.paths import RootPolicy, RunMode

    parent_layout, _ = _prepare_attempt(tmp_path / "parent")
    evidence_path = parent_layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    evidence_sha256 = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    parent_events = _write_recovery_chain(
        parent_layout,
        through_phase="U3",
        output_overrides={"U3": (evidence_sha256,)},
    )
    policy = RootPolicy(tmp_path / "children-production", tmp_path / "children-test")
    forked_at = NOW + timedelta(days=1)
    child = recovery.fork_for_new_evidence(
        parent_layout,
        mode=RunMode.TEST,
        policy=policy,
        evidence_bytes=b"new admitted evidence candidate\n",
        now=forked_at,
        entropy=b"evidence-child-finalized",
    )
    request_sha256 = hashlib.sha256(
        (child.layout.input_dir / "request.bin").read_bytes()
    ).hexdigest()
    jsonio.atomic_write_json(
        child.layout.input_dir / "request-metadata.json",
        {
            "request_sha256": request_sha256,
            "request_size": (child.layout.input_dir / "request.bin").stat().st_size,
        },
    )
    foundation.seal_input_inventory(
        child.layout,
        request_sha256=request_sha256,
        material_files=(),
        now=forked_at,
    )
    request_path = child.layout.recovery_dir / "evidence-lineage-request.json"
    pending_bytes = request_path.read_bytes()
    finalized_path = (
        child.layout.artifacts_dir
        / "U00-U03-evidence/U00-evidence-lineage.json"
    )
    fork_authority_path = (
        child.layout.input_dir
        / f"evidence-lineage-fork-authority-{child.run_id}.json"
    )

    authority_repo = tmp_path / "authority-repo"
    skill_root = authority_repo / "skills/crossframe-ultra"
    skill_root.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "skills/crossframe-ultra", skill_root)
    _write_release_manifest(
        authority_repo,
        skill_root / "references/release-manifest.json",
    )
    monkeypatch.setattr(
        source_integrity,
        "PRODUCTION_ROOT",
        tmp_path / "unselected-production-root",
    )

    first = foundation.advance_u0(
        child.layout,
        repo=authority_repo,
        now=forked_at + timedelta(seconds=1),
    )

    assert first.outcome == "awaiting-host-action"
    assert first.pending_action is not None
    assert first.pending_action.document["run_id"] == child.run_id
    assert first.pending_action.document["action_kind"] == "capability-attestation"
    assert not finalized_path.exists()
    _accept_capability_result(
        child.layout,
        first.pending_action,
        _capability_result(
            network="available",
            measured_at="2026-08-05T00:00:02Z",
        ),
        completed_at="2026-08-05T00:00:02Z",
    )

    original_atomic_write_bytes = foundation.atomic_write_bytes
    injected = False

    def fail_first_finalized_lineage_write(path, payload):
        nonlocal injected
        if path == finalized_path and not injected:
            injected = True
            raise OSError("injected lineage write crash")
        return original_atomic_write_bytes(path, payload)

    monkeypatch.setattr(
        foundation,
        "atomic_write_bytes",
        fail_first_finalized_lineage_write,
    )
    with pytest.raises(OSError, match="injected lineage write crash"):
        foundation.advance_u0(
            child.layout,
            repo=authority_repo,
            now=forked_at + timedelta(seconds=3),
        )

    assert recovery.load_checkpoints(child.layout)[-1]["phase_id"] == "U0"
    assert not finalized_path.exists()
    monkeypatch.setattr(
        foundation,
        "atomic_write_bytes",
        original_atomic_write_bytes,
    )

    completed = foundation.advance_foundation(
        child.layout,
        repo=authority_repo,
        now=forked_at + timedelta(seconds=4),
    )

    assert completed.outcome == "awaiting-host-action"
    assert completed.pending_action is not None
    assert completed.pending_action.document["phase_id"] == "U1"
    assert completed.pending_action.document["action_kind"] == "source-read"
    assert completed.phase_store is not None
    fork_authority_sha256 = hashlib.sha256(
        fork_authority_path.read_bytes()
    ).hexdigest()
    assert fork_authority_sha256 in completed.phase_store.events[-1][
        "input_artifact_hashes"
    ]
    child_run_authority = jsonio.load_json_object(
        child.layout.recovery_dir / "run-authority.json"
    )
    assert {
        "path": fork_authority_path.relative_to(child.layout.run_dir).as_posix(),
        "sha256": fork_authority_sha256,
        "media_type": "application/json",
    } in child_run_authority["input_refs"]
    assert request_path.read_bytes() == pending_bytes
    finalized = jsonio.load_json_object(finalized_path)
    pending = jsonio.load_json_object(request_path)
    run_contract_path = child.layout.artifacts_dir / "ultra-run-contract.json"
    attestation_path = (
        child.layout.artifacts_dir
        / "U00-U03-evidence/U00-host-capability-attestation.json"
    )
    assert finalized["status"] == "finalized-u0-admission"
    assert finalized["lineage_request_sha256"] == hashlib.sha256(
        pending_bytes
    ).hexdigest()
    assert finalized["run_id"] == child.run_id
    assert finalized["parent_run_id"] == parent_layout.run_dir.name
    assert finalized["parent_u3_event_sha256"] == parent_events[-1]["event_sha256"]
    assert finalized["parent_evidence_sha256"] == evidence_sha256
    assert finalized["inherited_input_refs"] == pending["inherited_input_refs"]
    assert finalized["new_evidence_ref"] == pending["new_evidence_ref"]
    assert finalized["evidence_cutoff"] > finalized["parent_evidence_cutoff"]
    assert finalized["capability_attestation_sha256"] == hashlib.sha256(
        attestation_path.read_bytes()
    ).hexdigest()
    assert finalized["run_contract_sha256"] == hashlib.sha256(
        run_contract_path.read_bytes()
    ).hexdigest()
    assert finalized["u0_phase_event_sha256"] == completed.phase_store.events[-1][
        "event_sha256"
    ]
    assert finalized["request_sha256"] == completed.phase_store.run_contract[
        "request_sha256"
    ]
    recovery.validate_instance("ultra-evidence-lineage.schema.json", finalized)
    manifest = artifacts.build_artifact_manifest(
        child.layout,
        phase_chain_head_sha256=completed.phase_store.events[-1]["event_sha256"],
        validator_set_sha256="a" * 64,
        generated_at=forked_at + timedelta(seconds=4),
    )
    assert next(
        record
        for record in manifest["artifacts"]
        if record["path"]
        == "artifacts/U00-U03-evidence/U00-evidence-lineage.json"
    )["phase_id"] == "U0"
    assert not any(
        f"U{phase:02d}" in str(value)
        for phase in range(4, 13)
        for value in finalized.values()
    )
    assert (child.layout.recovery_dir / "u1-authority").is_dir()
    evidence_path.write_bytes(b"tampered parent evidence\n")

    with pytest.raises(
        foundation.FoundationInputError,
        match="evidence lineage fork authority",
    ):
        foundation.validate_evidence_lineage_admission(
            child.layout,
            request_sha256=str(
                completed.phase_store.run_contract["request_sha256"]
            ),
            capability_attestation_sha256=str(
                completed.phase_store.run_contract[
                    "capability_attestation_sha256"
                ]
            ),
            run_contract_sha256=completed.phase_store.run_contract_artifact_sha256,
            u0_event=completed.phase_store.events[-1],
        )


def test_evidence_fork_does_not_overwrite_inherited_prior_evidence(tmp_path) -> None:
    from tests.test_ultra_repair import _prepare_attempt, _write_recovery_chain
    from ultra_runtime import jsonio, recovery, schemas
    from ultra_runtime.paths import RootPolicy, RunMode

    parent_layout, _ = _prepare_attempt(tmp_path / "parent")
    evidence_path = parent_layout.run_dir / "artifacts/U00-U03-evidence/evidence.json"
    evidence_sha256 = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    _write_recovery_chain(
        parent_layout,
        through_phase="U3",
        output_overrides={"U3": (evidence_sha256,)},
    )
    inherited_evidence = b"evidence inherited from the prior fork\n"
    prior_path = parent_layout.input_dir / "new-evidence.bin"
    prior_path.write_bytes(inherited_evidence)
    authority_path = parent_layout.recovery_dir / "run-authority.json"
    authority = jsonio.load_json_object(authority_path)
    authority["input_refs"].append(
        {
            "path": "input/new-evidence.bin",
            "sha256": hashlib.sha256(inherited_evidence).hexdigest(),
            "media_type": "application/octet-stream",
        }
    )
    authority["content_sha256"] = schemas.compute_artifact_content_sha256(
        authority
    )
    jsonio.atomic_write_json(authority_path, authority)
    policy = RootPolicy(tmp_path / "children-production", tmp_path / "children-test")
    latest_evidence = b"newer evidence candidate\n"

    child = recovery.fork_for_new_evidence(
        parent_layout,
        mode=RunMode.TEST,
        policy=policy,
        evidence_bytes=latest_evidence,
        now=NOW + timedelta(days=1),
        entropy=b"second-evidence-child",
    )

    inherited_ref = next(
        item
        for item in child.lineage["inherited_input_refs"]
        if item["path"] == "input/new-evidence.bin"
    )
    new_ref = child.lineage["new_evidence_ref"]
    assert new_ref["path"] != inherited_ref["path"]
    assert (child.layout.run_dir / inherited_ref["path"]).read_bytes() == (
        inherited_evidence
    )
    assert (child.layout.run_dir / new_ref["path"]).read_bytes() == latest_evidence
