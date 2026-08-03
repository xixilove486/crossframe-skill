from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
RUN_ID = "20260804T000000Z-010203040506"
NOW = datetime(2026, 8, 4, tzinfo=timezone.utc)
SOURCE_SHA256 = hashlib.sha256(b"source-manifest").hexdigest()
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
