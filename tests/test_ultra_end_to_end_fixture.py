from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path
import shutil
import sys

from tests.pytest_import_guard import pytest

from tests.ultra_closed_fixture_support import (
    CLOSED_ORGANIZATION_CASE,
    accept_closed_semantic_review,
    write_closed_u4_u10_authoring,
    write_closed_u11_authoring,
)
from tests.ultra_fake_host import run_open_world_ai_employment_fixture


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
TEMPLATE_DIR = REPO_ROOT / "skills/crossframe-ultra/templates"
OPEN_WORLD_FIXTURE_DIR = (
    REPO_ROOT
    / "tests/fixtures/ultra-runtime/open-world-ai-employment"
)
RUN_ID = "20260802T000000Z-0123456789ab"

TEMPLATE_MARKERS = {
    "ultra-run-status-output.md": ("run_id", "phase", "validation", "continuation"),
    "ultra-world-volume-output.md": ("boundary", "node", "channel", "clock"),
    "ultra-transformation-ledger-output.md": ("rule", "effect", "provenance"),
    "ultra-concept-disposition-output.md": ("concept", "disposition", "justification"),
    "ultra-claim-mechanism-output.md": ("claim", "mechanism", "edge", "unknown"),
    "ultra-recursive-state-output.md": ("node", "parent", "state", "channel"),
    "ultra-recursive-lineage-output.md": ("lineage", "parent", "order-2", "order-3"),
    "ultra-order-evaluation-output.md": ("order-2", "reversal", "order-3", "lock-in"),
    "ultra-retrieval-output.md": ("query", "source", "result", "cutoff"),
    "ultra-red-team-output.md": ("rival", "counter", "residual", "confidence"),
    "ultra-verdict-output.md": ("fact", "prediction", "value", "responsibility", "authorization"),
    "ultra-action-ranking-output.md": ("action", "rank", "constraint", "indicator"),
    "ultra-forecast-output.md": ("forecast", "indicator", "window", "resolution"),
    "ultra-framework-gap-output.md": ("gap", "framework", "boundary", "disposition"),
    "ultra-dossier-output.md": ("推演", "证据", "机制", "撤回条件"),
    "ultra-artifact-index-output.md": ("artifact", "sha256", "phase", "path"),
    "ultra-validator-report-output.md": ("validator", "manifest", "passed", "error"),
    "ultra-repair-plan-output.md": ("attempt", "repair", "reset", "bounded"),
}

def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module(f"ultra_runtime.{name}")


def _layout(paths, tmp_path: Path):
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)


def _bind_validation_repo(validation, authority_repo: Path, monkeypatch) -> None:
    authority_module = (
        authority_repo
        / "skills/crossframe-ultra/scripts/ultra_runtime/validation.py"
    )
    loaded_module = Path(validation.__file__).resolve()
    assert hashlib.sha256(authority_module.read_bytes()).hexdigest() == hashlib.sha256(
        loaded_module.read_bytes()
    ).hexdigest()
    monkeypatch.setattr(validation, "__file__", str(authority_module))


def _accept_source_read_batch(layout, action, *, batch_ordinal: int) -> None:
    host_handshake = _module("host_handshake")
    jsonio = _module("jsonio")
    source_integrity = _module("source_integrity")
    payload = action.document["payload"]
    execution_id = f"end-to-end-reader-{batch_ordinal:06d}"
    issued_at = datetime.fromisoformat(
        action.document["issued_at"].replace("Z", "+00:00")
    )
    read_at = (issued_at + timedelta(seconds=1)).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    items = [
        {
            "source_unit_id": unit["source_unit_id"],
            "source_unit_sha256": unit["source_unit_sha256"],
            "receipt_sha256": source_integrity._host_read_item_sha256(
                action_sha256=action.action_sha256,
                read_plan_sha256=payload["read_plan_sha256"],
                reader_mode=payload["reader_mode"],
                execution_id=execution_id,
                read_at=read_at,
                source_unit_id=unit["source_unit_id"],
                source_unit_sha256=unit["source_unit_sha256"],
            ),
        }
        for unit in payload["source_units"]
    ]
    result = {
        "schema_id": "crossframe.ultra.v82.source-read-result",
        "schema_version": 1,
        "action_sha256": action.action_sha256,
        "read_plan_sha256": payload["read_plan_sha256"],
        "reader_mode": payload["reader_mode"],
        "execution_id": execution_id,
        "read_at": read_at,
        "items": items,
    }
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": copy.deepcopy(action.document["version_binding"]),
        "phase_id": "U1",
        "action_kind": "source-read",
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": execution_id,
        "completed_at": read_at,
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        jsonio.canonical_json_bytes(receipt)
    ).hexdigest()
    host_handshake.accept_host_result(layout, action=action, receipt=receipt)


class RecordingPhaseStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = [
            (phase, (phase.lower() * 32)[:64]) for phase in ("U0", "U1", "U2", "U3")
        ]

    def complete(self, phase_id: str, *, artifact_hashes, **kwargs):
        digests = tuple(artifact_hashes)
        assert digests and all(len(digest) == 64 for digest in digests)
        self.calls.append((phase_id, digests))
        return {
            "phase_id": phase_id,
            "event_sha256": (phase_id.lower() * 32)[:64],
            "artifact_hashes": list(digests),
        }


def test_all_eighteen_task13_templates_exist_and_freeze_semantic_fields() -> None:
    assert len(TEMPLATE_MARKERS) == 18
    for filename, markers in TEMPLATE_MARKERS.items():
        path = TEMPLATE_DIR / filename
        assert path.is_file(), path
        raw = path.read_bytes()
        assert raw.endswith(b"\n")
        assert b"\r\n" not in raw
        text = raw.decode("utf-8").casefold()
        assert text.startswith("# ")
        for marker in markers:
            assert marker.casefold() in text, f"{filename}: missing {marker}"


def test_closed_fixture_contract_has_the_required_structural_stressors() -> None:
    case = CLOSED_ORGANIZATION_CASE
    assert case["material_closed"] is True
    assert len(case["parents"]) >= 2
    assert len(case["channels"]) == 2
    assert len({channel["clock"] for channel in case["channels"]}) == 2
    assert case["order_2"]["effect"] == "reversal"
    assert case["order_3"]["effect"] == "lock-in"
    assert case["rival"]["confidence"] == "low"
    assert case["verdict_kinds"] == [
        "fact",
        "prediction",
        "value",
        "responsibility",
        "authorization",
    ]


@pytest.fixture(scope="module")
def open_world_ai_employment_result(tmp_path_factory) -> dict[str, object]:
    return run_open_world_ai_employment_fixture(
        REPO_ROOT,
        OPEN_WORLD_FIXTURE_DIR,
        tmp_path_factory.mktemp("ultra-open-world-ai-employment"),
    )


def test_open_world_ai_employment_run_reaches_u12_with_evidence_and_full_answer(
    open_world_ai_employment_result,
) -> None:
    result = open_world_ai_employment_result
    assert result["status"] == "complete"
    assert result["u2"]["retrieval_status"] == "required-complete"
    assert result["u2"]["query_count"] > 0
    assert any(
        entry["identity"] == "reported"
        for entry in result["u3"]["entries"]
    )
    assert result["quality"] == {
        "policy_comparison": "pass",
        "conditional_system_branches": "pass",
        "theory_comparison": "pass",
    }
    assert result["validation"]["overall_status"] == "pass"


@pytest.fixture(scope="module")
def real_seam_result(
    tmp_path_factory,
) -> dict[str, object]:
    from tests import test_ultra_state_machine as state_fixtures

    evidence = _module("evidence")
    jsonio = _module("jsonio")
    materialization = _module("materialization")
    recovery = _module("recovery")
    state_machine = _module("state_machine")
    status = _module("status")
    context = state_fixtures.u1_prerequisite_context.__wrapped__(tmp_path_factory)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(state_machine, "_SOURCE_REPOSITORY", context["repo"])
    layout = context["run_layout"]
    foundation = _module("foundation")
    foundation_now = datetime(2026, 8, 2, tzinfo=timezone.utc)
    now = datetime(2026, 8, 4, tzinfo=timezone.utc)
    statuses = status.RunStatusStore(layout)
    created = statuses.create(foundation_now)
    materialization.seal_request_intake_authority(
        layout,
        request_sha256=state_fixtures.REQUEST_SHA256,
        request_size=len(state_fixtures.REQUEST_BYTES),
        created_at=created.created_at,
    )
    foundation.seal_input_inventory(
        layout,
        request_sha256=state_fixtures.REQUEST_SHA256,
        material_files=(),
        now=foundation_now,
        request_bytes=state_fixtures.REQUEST_BYTES,
    )
    original_store = foundation._complete_u0(
        layout,
        repo=context["repo"],
        attestation=state_fixtures._capability_attestation(),
        now=foundation_now,
    )
    progress = foundation._advance_u1(
        layout,
        repo=context["repo"],
        phase_store=original_store,
        now=foundation_now + timedelta(seconds=1),
    )
    batch_ordinal = 0
    while progress.outcome == "awaiting-host-action":
        batch_ordinal += 1
        assert progress.pending_action is not None
        _accept_source_read_batch(
            layout,
            progress.pending_action,
            batch_ordinal=batch_ordinal,
        )
        progress = foundation._advance_u1(
            layout,
            repo=context["repo"],
            phase_store=original_store,
            now=foundation_now + timedelta(seconds=batch_ordinal * 2 + 1),
        )
        assert batch_ordinal <= 16
    assert progress.outcome == "advanced"
    assert progress.completed_phase == "U1"
    assert original_store.current_phase == "U1"
    _, retrieval_ledger = state_fixtures._complete_u2(
        original_store,
        include_artifact=True,
    )
    retrieval_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    jsonio.atomic_write_json(retrieval_path, retrieval_ledger)
    recovery.create_checkpoint(
        layout,
        original_store,
        boundary_kind="phase",
        boundary_id="U2",
        boundary_ordinal=0,
        artifact_paths=(retrieval_path,),
        now=now + timedelta(seconds=2),
    )
    evidence_fixture = json.loads(
        (
            REPO_ROOT / "tests/fixtures/ultra-runtime/evidence-ledger-valid.json"
        ).read_text("utf-8")
    )
    for entry in evidence_fixture["entries"]:
        admitted_entry = copy.deepcopy(entry)
        if admitted_entry["identity"] == "user-claim":
            admitted_entry["attribution"] = {
                "origin_kind": "request",
                "origin_ref": "request.bin",
                "content_sha256": state_fixtures.REQUEST_SHA256,
                "span": [0, len(state_fixtures.REQUEST_BYTES)],
                "proof_grade": "fixture-bound",
            }
        else:
            admitted_entry["attribution"] = {
                "origin_kind": "source",
                "origin_ref": admitted_entry["source_refs"][0],
                "content_sha256": hashlib.sha256(
                    admitted_entry["statement"].encode("utf-8")
                ).hexdigest(),
                "span": None,
                "proof_grade": "fixture-bound",
            }
        original_store.append_evidence(admitted_entry)
    evidence_seal = evidence.validate_evidence_artifact(
        original_store.evidence_artifact,
        expected_run_id=original_store.run_id,
        expected_version_binding=_module("constants").current_version_binding(),
        expected_phase_id="U3",
        expected_evidence_cutoff=original_store.evidence_cutoff,
    )
    original_store.complete(
        "U3",
        artifact_hashes=(evidence_seal.artifact_sha256,),
        evidence_authority=evidence_seal,
    )
    evidence_path = (
        layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
    )
    jsonio.atomic_write_json(evidence_path, original_store.evidence_artifact)
    checkpoint = recovery.create_checkpoint(
        layout,
        original_store,
        boundary_kind="phase",
        boundary_id="U3",
        boundary_ordinal=0,
        artifact_paths=(evidence_path,),
        now=now + timedelta(seconds=3),
    )
    expected_events = original_store.events
    del original_store

    running = statuses.transition(created, "running", now + timedelta(seconds=5))
    statuses.transition(running, "interrupted", now + timedelta(seconds=6))

    resumed = recovery.resume_run(
        layout,
        now=now + timedelta(seconds=7),
        source_repository=context["repo"],
    )

    assert resumed.checkpoint == checkpoint
    assert resumed.phase_store.events == expected_events
    assert resumed.phase_store.events[-1]["phase_id"] == "U3"
    assert resumed.phase_store.events[-1]["status"] == "complete"
    assert resumed.phase_store.evidence_frozen is True
    assert resumed.phase_store.evidence_sha256 == evidence_seal.artifact_sha256
    u3_snapshot_root = layout.root.parent / "u3-seam-snapshot"
    shutil.copytree(layout.root, u3_snapshot_root)

    world_source = layout.authoring_dir / "U04-world-volume.json"
    jsonio.atomic_write_json(
        world_source,
        json.loads(
            (
                REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json"
            ).read_text("utf-8")
        ),
    )
    world = materialization.seal_authoring_artifact(
        layout,
        world_source,
        generated_at=now + timedelta(seconds=8),
        authority_documents={"evidence": jsonio.load_json_object(evidence_path)},
    )
    world_path = materialization.artifact_destination(layout, world_source)
    jsonio.atomic_write_json(world_path, world)
    u4_event = materialization.record_materialized_phase(
        layout,
        resumed.phase_store,
        "U4",
        (world_path,),
        input_artifact_hashes=(
            hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        ),
    )

    assert u4_event["phase_id"] == "U4"
    recovery.create_checkpoint(
        layout,
        resumed.phase_store,
        boundary_kind="phase",
        boundary_id="U4",
        boundary_ordinal=0,
        artifact_paths=(world_path,),
        now=now + timedelta(seconds=9),
    )
    statuses.transition(
        statuses.read(),
        "interrupted",
        now + timedelta(seconds=9, microseconds=500_000),
    )
    restarted = recovery.resume_run(
        layout,
        now=now + timedelta(seconds=10),
        source_repository=context["repo"],
    )
    assert restarted.phase_store.evidence_frozen is True
    assert restarted.phase_store.evidence_sha256 == evidence_seal.artifact_sha256
    assert [
        event["phase_id"] for event in restarted.phase_store.events
    ].count("U4") == 1
    u4_snapshot_root = layout.root.parent / "u4-seam-snapshot"
    shutil.copytree(layout.root, u4_snapshot_root)

    output_authority = write_closed_u4_u10_authoring(REPO_ROOT, layout)

    with pytest.raises(ValueError, match="packet count"):
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            restarted.phase_store,
            now=now + timedelta(seconds=11),
            create_checkpoint=recovery.create_checkpoint,
        )

    sealed_plan = jsonio.load_json_object(
        layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
    )
    write_closed_u11_authoring(
        REPO_ROOT,
        layout,
        sealed_plan,
        output_authority,
        generated_at="2026-08-04T00:00:12Z",
    )
    pending_semantic = materialization.materialize_u4_u11(
        REPO_ROOT,
        layout,
        restarted.phase_store,
        now=now + timedelta(seconds=12),
        create_checkpoint=recovery.create_checkpoint,
    )
    assert pending_semantic.document["action_kind"] == "semantic-review"
    assert restarted.phase_store.current_phase == "U10"
    accept_closed_semantic_review(
        REPO_ROOT,
        layout,
        pending_semantic,
        reviewed_at="2026-08-04T00:00:12Z",
    )
    bundle = materialization.materialize_u4_u11(
        REPO_ROOT,
        layout,
        restarted.phase_store,
        now=now + timedelta(seconds=12, microseconds=100_000),
        create_checkpoint=recovery.create_checkpoint,
    )
    assert bundle.phase_events[-1]["phase_id"] == "U11"
    assert [
        event["phase_id"] for event in restarted.phase_store.events
    ] == [f"U{ordinal}" for ordinal in range(12)]
    statuses.transition(
        statuses.read(),
        "interrupted",
        now + timedelta(seconds=12, microseconds=250_000),
    )
    u11_resumed = recovery.resume_run(
        layout,
        now=now + timedelta(seconds=12, microseconds=500_000),
        source_repository=context["repo"],
    )
    assert u11_resumed.phase_store.current_phase == "U11"
    snapshot_root = layout.root.parent / "u11-seam-snapshot"
    shutil.copytree(layout.root, snapshot_root)

    paths = _module("paths")
    validation = _module("validation")
    policy = paths.RootPolicy(
        layout.root.parent / "production-control",
        layout.root,
    )
    monkeypatch.setattr(validation, "default_root_policy", lambda: policy)
    _bind_validation_repo(validation, context["repo"], monkeypatch)

    def fresh_check(stage: str) -> bytes:
        assert stage in {"pre-publish", "post-publish"}
        official_article = (
            layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
        )
        if stage == "pre-publish":
            assert not official_article.exists()
        else:
            assert official_article.is_file()
        return validation.validate_run_from_disk(
            context["repo"],
            paths.RunMode.TEST,
            layout.run_dir.name,
        )

    def commit_report(
        stage: str,
        report_bytes: bytes,
        lease: object,
    ) -> object:
        assert stage in {"pre-publish", "post-publish"}
        report = json.loads(report_bytes.decode("utf-8"))
        return validation.commit_validation_attempt(
            layout,
            attempt_id=report["attempt_id"],
            report_bytes=report_bytes,
            expected_manifest_sha256=report["manifest_sha256"],
            expected_validator_set_sha256=report["validator_set_sha256"],
            lease=lease,
        )

    complete = materialization.materialize_complete_run(
        context["repo"],
        paths.RunMode.TEST,
        layout.run_dir.name,
        policy=policy,
        now=now + timedelta(seconds=13),
        entropy=b"task12-task13-real-seam",
        fresh_check=fresh_check,
        commit_report=commit_report,
    )
    assert complete.status == "complete"
    final_status = status.RunStatusStore(layout).read()
    assert final_status.status == "complete"
    assert final_status.current_phase == "U12"
    assert final_status.last_complete_phase == "U12"
    assert final_status.validation_passed is True
    assert final_status.tools_allowed is False
    u12_checkpoint = recovery.select_resume_checkpoint(layout)
    assert u12_checkpoint["phase_id"] == "U12"
    manifest = jsonio.load_json_object(complete.manifest_path)
    journal = jsonio.load_json_object(
        layout.recovery_dir / "publish-transaction.json"
    )
    latest_complete = _module("indexes").IndexStore(layout.root).read_pointer(
        "latest-complete"
    )
    phase_events = tuple(
        json.loads(line)
        for line in (
            layout.recovery_dir / "phase-events.jsonl"
        ).read_text("utf-8").splitlines()
    )
    u12_events = tuple(
        event
        for event in phase_events
        if event["phase_id"] == "U12" and event["status"] == "complete"
    )
    u12_checkpoints = tuple(
        item
        for item in recovery.load_checkpoints(layout)
        if item["boundary_kind"] == "phase" and item["phase_id"] == "U12"
    )
    ordered_paths = (
        complete.manifest_path,
        layout.validation_current_dir / "ultra-validator-report.json",
        complete.article_path,
        complete.dossier_path,
        complete.artifact_index_path,
    )
    ordered_hashes = tuple(
        hashlib.sha256(path.read_bytes()).hexdigest() for path in ordered_paths
    )
    assert len(u12_events) == 1
    assert len(u12_checkpoints) == 1
    assert tuple(u12_events[0]["output_artifact_hashes"]) == ordered_hashes
    assert tuple(
        (item["path"], item["sha256"])
        for item in u12_checkpoints[0]["artifact_hashes"]
    ) == tuple(
        (path.relative_to(layout.run_dir).as_posix(), digest)
        for path, digest in zip(ordered_paths, ordered_hashes)
    )
    assert u12_checkpoints[0]["phase_event_sha256"] == u12_events[0][
        "event_sha256"
    ]
    monkeypatch.undo()
    return {
        "layout": layout,
        "authority_repo": context["repo"],
        "u3_snapshot_root": u3_snapshot_root,
        "u4_snapshot_root": u4_snapshot_root,
        "u11_snapshot_root": snapshot_root,
        "u3_evidence_frozen": resumed.phase_store.evidence_frozen,
        "u3_evidence_sha256": resumed.phase_store.evidence_sha256,
        "expected_evidence_sha256": evidence_seal.artifact_sha256,
        "u4_event_count": sum(
            event["phase_id"] == "U4" for event in phase_events
        ),
        "complete": complete,
        "final_status": final_status,
        "u12_checkpoint": u12_checkpoint,
        "u12_event": u12_events[0],
        "ordered_u12_hashes": ordered_hashes,
        "manifest": manifest,
        "journal": journal,
        "latest_complete": latest_complete,
    }


def test_seam_recovery_restores_frozen_u3_evidence_with_same_sha(
    real_seam_result,
) -> None:
    assert real_seam_result["u3_evidence_frozen"] is True
    assert real_seam_result["u3_evidence_sha256"] == real_seam_result[
        "expected_evidence_sha256"
    ]


def test_seam_restart_reuses_u4_without_duplicate_phase_event(
    real_seam_result,
) -> None:
    assert real_seam_result["u4_event_count"] == 1


def test_task12_task13_real_disk_seam_commits_atomic_complete_run(
    real_seam_result,
) -> None:
    complete = real_seam_result["complete"]
    status_record = real_seam_result["final_status"]
    assert complete.status == "complete"
    assert status_record.status == "complete"
    assert status_record.current_phase == "U12"
    assert status_record.last_complete_phase == "U12"
    assert status_record.validation_passed is True
    assert status_record.tools_allowed is False
    assert real_seam_result["u12_checkpoint"]["phase_id"] == "U12"
    assert tuple(
        real_seam_result["u12_event"]["output_artifact_hashes"]
    ) == real_seam_result["ordered_u12_hashes"]
    assert real_seam_result["manifest"]["official_delivery_published"] is True
    assert real_seam_result["journal"]["state"] == "complete"
    assert real_seam_result["latest_complete"]["run_id"] == status_record.run_id


def _snapshot_progress_runtime(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    snapshot_key: str,
):
    paths = _module("paths")
    state_machine = _module("state_machine")
    test_root = tmp_path / "test-control"
    shutil.copytree(real_seam_result[snapshot_key], test_root)
    policy = paths.RootPolicy(tmp_path / "production-control", test_root)
    layout = paths.build_run_layout(
        paths.RunMode.TEST,
        real_seam_result["final_status"].run_id,
        policy,
    )
    monkeypatch.setattr(
        state_machine,
        "_SOURCE_REPOSITORY",
        real_seam_result["authority_repo"],
    )
    return paths, layout, policy


def _foundation_authority_bytes(layout) -> dict[str, bytes]:
    selected = {
        layout.run_dir / "run-status.json",
        *(path for path in layout.input_dir.rglob("*") if path.is_file()),
        *(
            path
            for path in (layout.artifacts_dir / "U00-U03-evidence").rglob("*")
            if path.is_file()
        ),
        *(
            path
            for path in layout.recovery_dir.rglob("*")
            if path.is_file() and not path.name.endswith(".lock")
        ),
    }
    return {
        path.relative_to(layout.run_dir).as_posix(): path.read_bytes()
        for path in sorted(selected)
    }


def test_sealed_u3_missing_u4_is_idempotent_authoring_wait(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy = _snapshot_progress_runtime(
        real_seam_result,
        tmp_path,
        monkeypatch,
        "u3_snapshot_root",
    )
    materialization = _module("materialization")
    status = _module("status")
    forbidden_calls: list[tuple[object, ...]] = []

    def forbidden(*args):
        forbidden_calls.append(args)
        pytest.fail("validation or publication ran on an authoring wait")

    before = _foundation_authority_bytes(layout)
    first = materialization.materialize_complete_run(
        real_seam_result["authority_repo"],
        paths.RunMode.TEST,
        layout.run_dir.name,
        policy=policy,
        now=datetime(2026, 8, 4, 0, 0, 20, tzinfo=timezone.utc),
        entropy=b"task-6-u4-wait-first",
        fresh_check=forbidden,
        commit_report=forbidden,
    )
    second = materialization.materialize_complete_run(
        real_seam_result["authority_repo"],
        paths.RunMode.TEST,
        layout.run_dir.name,
        policy=policy,
        now=datetime(2026, 8, 4, 0, 0, 21, tzinfo=timezone.utc),
        entropy=b"task-6-u4-wait-second",
        fresh_check=forbidden,
        commit_report=forbidden,
    )

    assert first == second
    assert first.outcome == "awaiting-authoring"
    assert first.current_phase == "U4"
    assert first.last_complete_phase == "U3"
    assert first.next_action is not None
    assert first.next_action["relative_path"] == "U04-world-volume.json"
    assert status.RunStatusStore(layout).read().status == "running"
    assert _foundation_authority_bytes(layout) == before
    assert forbidden_calls == []
    assert not (layout.recovery_dir / "publish-transaction.json").exists()
    assert not (layout.artifacts_dir / "ultra-artifact-manifest.json").exists()
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_missing_u5_sibling_does_not_hide_malformed_existing_authoring(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy = _snapshot_progress_runtime(
        real_seam_result,
        tmp_path,
        monkeypatch,
        "u4_snapshot_root",
    )
    materialization = _module("materialization")
    status = _module("status")
    malformed_path = layout.authoring_dir / "U05-transformation-ledger.json"
    malformed_bytes = b'{"malformed":\n'
    malformed_path.write_bytes(malformed_bytes)
    assert not (layout.authoring_dir / "U05-concept-disposition.json").exists()
    forbidden_calls: list[tuple[object, ...]] = []

    def forbidden(*args):
        forbidden_calls.append(args)
        pytest.fail("validation or publication ran before authoring admission")

    with pytest.raises(ValueError, match="authoring|JSON|malformed|invalid"):
        materialization.materialize_complete_run(
            real_seam_result["authority_repo"],
            paths.RunMode.TEST,
            layout.run_dir.name,
            policy=policy,
            now=datetime(2026, 8, 4, 0, 0, 22, tzinfo=timezone.utc),
            entropy=b"task-6-malformed-u5",
            fresh_check=forbidden,
            commit_report=forbidden,
        )

    assert malformed_path.read_bytes() == malformed_bytes
    assert status.RunStatusStore(layout).read().status == "running"
    assert forbidden_calls == []
    assert not (layout.recovery_dir / "publish-transaction.json").exists()
    assert not (layout.artifacts_dir / "ultra-artifact-manifest.json").exists()
    assert not (layout.run_dir / ".writer-lease.json").exists()


def _snapshot_materialization_runtime(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    paths = _module("paths")
    validation = _module("validation")
    state_machine = _module("state_machine")
    test_root = tmp_path / "test-control"
    shutil.copytree(real_seam_result["u11_snapshot_root"], test_root)
    policy = paths.RootPolicy(tmp_path / "production-control", test_root)
    layout = paths.build_run_layout(
        paths.RunMode.TEST,
        real_seam_result["final_status"].run_id,
        policy,
    )
    monkeypatch.setattr(validation, "default_root_policy", lambda: policy)
    _bind_validation_repo(
        validation,
        real_seam_result["authority_repo"],
        monkeypatch,
    )
    monkeypatch.setattr(
        state_machine,
        "_SOURCE_REPOSITORY",
        real_seam_result["authority_repo"],
    )

    def fresh_check(stage: str) -> bytes:
        official_article = (
            layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
        )
        if stage == "pre-publish":
            assert not official_article.exists()
        else:
            assert official_article.is_file()
        return validation.validate_run_from_disk(
            real_seam_result["authority_repo"],
            paths.RunMode.TEST,
            layout.run_dir.name,
        )

    def commit_report(
        stage: str,
        report_bytes: bytes,
        lease: object,
    ) -> object:
        report = json.loads(report_bytes.decode("utf-8"))
        return validation.commit_validation_attempt(
            layout,
            attempt_id=report["attempt_id"],
            report_bytes=report_bytes,
            expected_manifest_sha256=report["manifest_sha256"],
            expected_validator_set_sha256=report["validator_set_sha256"],
            lease=lease,
        )

    return paths, layout, policy, fresh_check, commit_report


def test_seam_pre_u12_checkpoint_failure_rolls_back_official_names(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy, fresh_check, commit_report = (
        _snapshot_materialization_runtime(real_seam_result, tmp_path, monkeypatch)
    )
    materialization = _module("materialization")
    recovery = _module("recovery")
    status = _module("status")
    original_checkpoint = recovery.create_checkpoint

    def fail_u12_checkpoint(*args, **kwargs):
        if kwargs.get("boundary_id") == "U12":
            raise recovery.RecoveryStateError("injected U12 checkpoint failure")
        return original_checkpoint(*args, **kwargs)

    monkeypatch.setattr(recovery, "create_checkpoint", fail_u12_checkpoint)
    with pytest.raises(recovery.RecoveryStateError, match="injected U12"):
        materialization.materialize_complete_run(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
            policy=policy,
            now=datetime(2026, 8, 4, 0, 1, tzinfo=timezone.utc),
            entropy=b"pre-u12-rollback",
            fresh_check=fresh_check,
            commit_report=commit_report,
        )

    publication = _module("deliverables").publication_paths(
        layout,
        "20260804T000100Z-" + hashlib.sha256(b"pre-u12-rollback").hexdigest()[:12],
    )
    assert not any(path.exists() for path in publication.official_paths)
    assert status.RunStatusStore(layout).read().status == "needs_attention"
    assert _module("jsonio").load_json_object(publication.journal_path)[
        "state"
    ] == "rolled-back"
    assert recovery.select_resume_checkpoint(layout)["phase_id"] == "U11"


def test_seam_durable_u12_status_cas_failure_is_retained_then_rolled_forward(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy, fresh_check, commit_report = (
        _snapshot_materialization_runtime(real_seam_result, tmp_path, monkeypatch)
    )
    deliverables = _module("deliverables")
    materialization = _module("materialization")
    status = _module("status")
    original_commit = status.RunStatusStore.commit_u12_complete
    failed = False

    def fail_first_complete(self, expected, now, *, reason):
        nonlocal failed
        if not failed:
            failed = True
            raise status.RunStatusConflictError("injected complete CAS failure")
        return original_commit(self, expected, now, reason=reason)

    monkeypatch.setattr(
        status.RunStatusStore,
        "commit_u12_complete",
        fail_first_complete,
    )
    with pytest.raises(status.RunStatusConflictError, match="injected complete CAS"):
        materialization.materialize_complete_run(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
            policy=policy,
            now=datetime(2026, 8, 4, 0, 2, tzinfo=timezone.utc),
            entropy=b"u12-roll-forward",
            fresh_check=fresh_check,
            commit_report=commit_report,
        )

    retained = status.RunStatusStore(layout).read()
    assert retained.status == "needs_attention"
    assert retained.tools_allowed is False
    assert (layout.delivery_dir / "CrossFrame-Ultra-完整文章.md").is_file()
    assert _module("recovery").select_resume_checkpoint(layout)["phase_id"] == "U12"
    journal_path = layout.recovery_dir / "publish-transaction.json"
    assert _module("jsonio").load_json_object(journal_path)["state"] == "u12-durable"

    recovered = deliverables.recover_publish_transaction(
        layout,
        mark_needs_attention=lambda reason: pytest.fail(reason),
    )
    assert recovered["state"] == "complete"
    completed = status.RunStatusStore(layout).read()
    assert completed.status == "complete"
    assert completed.tools_allowed is False
    assert _module("jsonio").load_json_object(journal_path)["state"] == "complete"
    assert _module("indexes").IndexStore(layout.root).read_pointer(
        "latest-complete"
    )["run_id"] == layout.run_dir.name


def test_seam_u1_hydration_failure_preserves_status_bytes_and_delivery(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy, _, _ = _snapshot_materialization_runtime(
        real_seam_result,
        tmp_path,
        monkeypatch,
    )
    materialization = _module("materialization")
    recovery = _module("recovery")
    status = _module("status")
    statuses = status.RunStatusStore(layout)
    current = statuses.read()
    interrupted = statuses.transition(
        current,
        "interrupted",
        datetime(2026, 8, 4, 0, 3, tzinfo=timezone.utc),
        current_phase=current.current_phase,
        last_complete_phase=current.last_complete_phase,
        reason="inject U1 hydration failure",
    )
    status_bytes = statuses.path.read_bytes()
    (layout.recovery_dir / "u1-authority/read-plan.json").unlink()

    def publication_must_not_start(*args, **kwargs):
        pytest.fail("publication started before U1 hydration succeeded")

    with pytest.raises(recovery.RecoveryIntegrityError, match="U1 read plan"):
        materialization.materialize_complete_run(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
            policy=policy,
            now=datetime(2026, 8, 4, 0, 3, 1, tzinfo=timezone.utc),
            entropy=b"u1-hydration-failure",
            fresh_check=publication_must_not_start,
            commit_report=publication_must_not_start,
        )

    assert statuses.read() == interrupted
    assert statuses.path.read_bytes() == status_bytes
    assert not (layout.recovery_dir / "publish-transaction.json").exists()
    assert not (layout.artifacts_dir / "ultra-artifact-manifest.json").exists()
    assert not any(
        (layout.delivery_dir / filename).exists()
        for filename in (
            "CrossFrame-Ultra-完整文章.md",
            "完整推演档案.md",
            "工件索引.md",
        )
    )


def _u0_recovery_case(tmp_path: Path):
    from tests.test_ultra_recovery import _fixture_run

    recovery = _module("recovery")
    jsonio = _module("jsonio")
    status = _module("status")
    _, layout, store, artifact_path = _fixture_run(tmp_path)
    now = datetime(2026, 8, 4, tzinfo=timezone.utc)
    checkpoint = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(artifact_path,),
        now=now,
    )
    statuses = status.RunStatusStore(layout)
    created = statuses.create(now)
    running = statuses.transition(created, "running", now + timedelta(seconds=1))
    statuses.transition(running, "interrupted", now + timedelta(seconds=2))
    return recovery, jsonio, statuses, layout, artifact_path, checkpoint, now


@pytest.mark.parametrize(
    "corruption",
    ("checkpoint", "artifact"),
    ids=("corrupt-checkpoint", "corrupt-artifact"),
)
def test_seam_corrupt_checkpoint_or_artifact_fails_closed(
    tmp_path: Path,
    corruption: str,
) -> None:
    recovery, jsonio, statuses, layout, artifact_path, checkpoint, now = (
        _u0_recovery_case(tmp_path)
    )
    if corruption == "checkpoint":
        checkpoint_path = (
            layout.recovery_dir
            / "checkpoints"
            / f"{jsonio.sha256_bytes(jsonio.canonical_json_bytes(checkpoint))}.json"
        )
        changed = dict(checkpoint)
        changed["generated_at"] = "2026-08-04T00:00:01Z"
        jsonio.atomic_write_json(checkpoint_path, changed)
    else:
        artifact_path.write_bytes(b"tampered artifact\n")

    with pytest.raises(recovery.RecoveryError, match="checkpoint|artifact|hash"):
        recovery.resume_run(layout, now=now + timedelta(seconds=3))
    assert statuses.read().status == "interrupted"
    assert not (layout.delivery_dir / "CrossFrame-Ultra-完整文章.md").exists()


def test_seam_changed_frozen_input_fails_closed(tmp_path: Path) -> None:
    recovery, jsonio, statuses, layout, _, _, now = _u0_recovery_case(tmp_path)
    authority = jsonio.load_json_object(layout.recovery_dir / "run-authority.json")
    input_path = layout.run_dir / authority["input_refs"][0]["path"]
    input_path.write_bytes(input_path.read_bytes() + b"input drift\n")

    with pytest.raises(recovery.RecoveryIntegrityError, match="input|hash"):
        recovery.resume_run(layout, now=now + timedelta(seconds=3))
    assert statuses.read().status == "interrupted"
    assert not (layout.delivery_dir / "CrossFrame-Ultra-完整文章.md").exists()


@pytest.mark.parametrize("mutation", ("pruned", "mixed"))
def test_seam_mixed_or_pruned_lineage_fails_closed(mutation: str) -> None:
    from tests import test_ultra_recursion as recursion_fixtures

    lineage = recursion_fixtures.load_fixture("recursive-lineage-valid.json")
    registry = recursion_fixtures.state_registry()
    declared = lineage["nodes"][2]["recursive_state_artifact_sha256"]
    if mutation == "pruned":
        registry.pop(declared)
    else:
        replacement = next(
            value for key, value in registry.items() if key != declared
        )
        registry[declared] = copy.deepcopy(replacement)

    with pytest.raises(ValueError, match="recursive-state|registry|sealed|hash"):
        recursion_fixtures.validate_lineage(lineage, registry=registry)


def test_full_fixture_records_u0_u12_once_and_packet_checkpoints_are_not_phase_events(
    tmp_path: Path
) -> None:
    materialization_path = RUNTIME_DIR / "materialization.py"
    delivery_path = RUNTIME_DIR / "deliverables.py"
    if not materialization_path.is_file() or not delivery_path.is_file():
        pytest.skip("Task 13 materialization boundary is not implemented")
    materialization = _module("materialization")
    deliverables = _module("deliverables")
    paths = _module("paths")
    layout = _layout(paths, tmp_path)
    prepared = materialization.prepare_authoring(layout)
    store = RecordingPhaseStore()
    base_time = datetime(2026, 8, 2, tzinfo=timezone.utc)

    phase_files = {
        "U4": ["U04-world-volume.json"],
        "U5": ["U05-transformation-ledger.json", "U05-concept-disposition.json"],
        "U6": ["U06-claim-mechanism-graph.json"],
        "U7": ["U07-recursive-states/node-a.json", "U07-recursive-lineage.json"],
        "U8": ["U08-order-evaluation.json", "U08-red-team-report.json"],
        "U9": ["U09-verdict.json", "U09-action-ranking.json", "U09-forecast-ledger.json"],
        "U10": ["U10-framework-gap-ledger.json", "U10-output-plan.json"],
    }
    for phase, relatives in phase_files.items():
        artifact_paths: list[Path] = []
        for ordinal, relative in enumerate(relatives, start=1):
            target = prepared.authoring_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(
                    {
                        "case": CLOSED_ORGANIZATION_CASE,
                        "phase": phase,
                        "ordinal": ordinal,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            artifact_paths.append(target)
        materialization.record_materialized_phase(
            layout,
            store,
            phase,
            artifact_paths,
        )

    packet_paths = []
    for ordinal in range(1, 4):
        packet = layout.authoring_dir / "article/packets" / f"packet-{ordinal:02d}.md"
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(f"## packet {ordinal}\n\ncase material\n", encoding="utf-8")
        packet_paths.append(packet)
    partial_for_checkpoints = layout.authoring_dir / "article.partial.md"
    partial_for_checkpoints.write_text(
        "# partial article\n\npacket checkpoint authority\n",
        encoding="utf-8",
    )
    checkpoints: list[tuple[str, int, tuple[Path, ...]]] = []
    before_packet_events = tuple(store.calls)
    materialization.checkpoint_article_packets(
        layout,
        store,
        packet_paths,
        now=base_time,
        create_checkpoint=lambda layout, phase_store, **kwargs: checkpoints.append(
            (
                kwargs["boundary_id"],
                kwargs["boundary_ordinal"],
                tuple(kwargs["artifact_paths"]),
            )
        ),
    )
    assert store.calls == list(before_packet_events)
    assert [ordinal for _, ordinal, _ in checkpoints] == [1, 2, 3]

    u11_paths = (
        layout.authoring_dir / "U11-semantic-coverage.json",
        layout.authoring_dir / "U11-article-review.json",
        layout.authoring_dir / "article.partial.md",
        layout.authoring_dir / "完整推演档案.md",
        layout.artifacts_dir / "ultra-artifact-index.md",
    )
    for ordinal, target in enumerate(u11_paths, start=1):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"U11 fixture artifact {ordinal}\n", encoding="utf-8")
    materialization.record_materialized_phase(
        layout,
        store,
        "U11",
        u11_paths,
    )

    article = "# 完整文章\n\n组织激励与照护约束共同导致延期。\n".encode("utf-8")
    dossier = (layout.authoring_dir / "完整推演档案.md").read_bytes()
    index = "# 工件索引\n\nU0-U12\n".encode("utf-8")
    manifest = b'{"fixture":"manifest"}\n'
    publication = deliverables.publish_delivery(
        layout,
        transaction_id="20260802T000100Z-bbbbbbbbbbbb",
        article_bytes=article,
        dossier_bytes=dossier,
        artifact_index_bytes=index,
        manifest_bytes=manifest,
        fresh_check=lambda stage: (
            f'{{"overall_status":"pass","stage":"{stage}"}}\n'.encode("utf-8")
        ),
        commit_report=lambda stage, report, lease: None,
        mark_needs_attention=lambda reason: pytest.fail(reason),
    )
    postcheck_report_path = (
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    postcheck_report_path.parent.mkdir(parents=True, exist_ok=True)
    postcheck_report_path.write_bytes(publication.postcheck_report_bytes)
    materialization.complete_u12(
        layout,
        store,
        manifest_path=publication.paths.manifest_path,
        postcheck_report_path=postcheck_report_path,
        delivery_paths=(
            publication.paths.article_path,
            publication.paths.dossier_path,
            publication.paths.artifact_index_path,
        ),
        postcheck_passed=publication.postcheck_passed,
    )

    assert [phase for phase, _ in store.calls] == [f"U{number}" for number in range(13)]
    assert store.calls[-1][1] == tuple(
        __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        for path in (
            publication.paths.manifest_path,
            postcheck_report_path,
            publication.paths.article_path,
            publication.paths.dossier_path,
            publication.paths.artifact_index_path,
        )
    )
    assert not (layout.authoring_dir / "U09-forecast-resolution.json").exists()
    assert publication.paths.article_path.is_file()
    assert publication.paths.dossier_path.is_file()
    assert publication.paths.artifact_index_path.is_file()
