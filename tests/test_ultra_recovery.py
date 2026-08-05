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
    from ultra_runtime.paths import RootPolicy, RunMode, build_run_layout

    policy = RootPolicy(tmp_path / "production", tmp_path / "test")
    layout = build_run_layout(RunMode.TEST, RUN_ID, policy)
    layout.input_dir.mkdir(parents=True)
    input_path = layout.input_dir / "AGENTS.md"
    shutil.copy2(ROOT / "AGENTS.md", input_path)
    input_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
    contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": input_sha256,
        "run_mode": "test",
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-04T00:00:00Z",
        "capabilities": {
            "filesystem": "available",
            "docx_parser": "available",
            "network": "available",
            "retrieval": "available",
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
    store = state_machine.PhaseStore(
        run_id=RUN_ID,
        version_binding=current_version_binding(),
        source_sha256=SOURCE_SHA256,
        input_artifact_hashes=(input_sha256,),
        input_snapshot_sha256=input_sha256,
        evidence_cutoff="2026-08-04T00:00:00Z",
        now=NOW,
        run_contract=contract,
        capability_availability={"network": "available", "retrieval": "available"},
        source_repository=ROOT,
        run_layout=layout,
    )
    store.complete("U0", artifact_hashes=(store.run_contract_artifact_sha256,))
    artifact_path = layout.artifacts_dir / "ultra-run-contract.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(_canonical(dict(store.run_contract)))
    assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == (
        store.run_contract_artifact_sha256
    )
    return policy, layout, store, artifact_path


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
        expected_source_lock_sha256,
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
            or expected_source_lock_sha256
            != expected["authority"].source_lock_artifact_sha256
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
    u1_event["output_artifact_hashes"] = [source_lock_sha256, coverage_sha256]
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
    checkpoint["artifact_hashes"][1]["sha256"] = coverage_sha256
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
    jsonio.atomic_write_json(layout.run_dir / U1_SOURCE_LOCK, issued["source_lock"])
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
        artifact_paths=(layout.run_dir / U1_SOURCE_LOCK, layout.run_dir / U1_SOURCE_COVERAGE),
        now=NOW + timedelta(seconds=1),
    )
    read_plan_path = layout.run_dir / U1_READ_PLAN
    read_plan_persisted = read_plan_path.is_file()
    persisted_read_plan = (
        jsonio.load_json_object(read_plan_path) if read_plan_persisted else None
    )
    if not read_plan_persisted:
        jsonio.atomic_write_json(read_plan_path, issued["read_plan"])

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


def test_resume_uses_last_full_boundary_and_cancel_is_terminal(tmp_path):
    recovery, _, layout, store, _, checkpoint = _checkpoint(tmp_path)
    import ultra_runtime.state_machine as state_machine
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
    with pytest.raises(state_machine.PhaseTransitionError, match="terminal|cancelled"):
        store.complete("U1", artifact_hashes=(hashlib.sha256(b"late").hexdigest(),))
    with pytest.raises(recovery.RecoveryStateError, match="cancelled|terminal"):
        recovery.resume_run(layout, now=NOW + timedelta(seconds=5))


def test_partial_cancellation_blocks_new_lease_and_retry_converges(
    tmp_path,
    monkeypatch,
):
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
    with pytest.raises(locks.LeaseNeedsAttentionError) as caught:
        locks.acquire_run_lease(
            layout,
            NOW + timedelta(seconds=3),
            timedelta(seconds=30),
        )
    assert isinstance(caught.value.__cause__, recovery.RecoveryIntegrityError)
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

    with pytest.raises(recovery.RecoveryIntegrityError, match="read plan|U1"):
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
