from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from tests.pytest_import_guard import pytest

from tests.ultra_closed_fixture_support import (
    write_closed_u4_u10_authoring,
    write_closed_u11_authoring,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
MATERIALIZATION_PATH = RUNTIME_DIR / "materialization.py"

EXPECTED_AUTHORING_SLOTS = (
    "U04-world-volume.json",
    "U05-transformation-ledger.json",
    "U05-concept-disposition.json",
    "U06-claim-mechanism-graph.json",
    "U07-recursive-states/<node-id>.json",
    "U07-recursive-lineage.json",
    "U08-order-evaluation.json",
    "U08-red-team-report.json",
    "U09-verdict.json",
    "U09-action-ranking.json",
    "U09-forecast-ledger.json",
    "U10-framework-gap-ledger.json",
    "U10-output-plan.json",
    "U11-semantic-coverage.json",
    "article/packets/<packet-id>.md",
    "U11-article-review.json",
    "完整推演档案.md",
)


def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


@pytest.fixture
def runtime():
    if not MATERIALIZATION_PATH.is_file():
        pytest.skip(f"Task 13 runtime is not implemented: {MATERIALIZATION_PATH}")
    return _module("materialization"), _module("paths"), _module("jsonio")


def _layout(paths, tmp_path: Path):
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths.build_run_layout(
        paths.RunMode.TEST,
        "20260802T030405Z-000000000013",
        policy,
    )


class _RecordingPhaseStore:
    def __init__(self) -> None:
        self.events: tuple[dict[str, object], ...] = ()
        self.current_phase = "U3"
        self.active_generation = 0
        self.run_contract: dict[str, object] = {}

    def complete(self, phase_id: str, *, artifact_hashes, **kwargs):
        digests = tuple(artifact_hashes)
        event = {
            "phase_id": phase_id,
            "status": "complete",
            "event_sha256": hashlib.sha256(
                f"{phase_id}:{len(self.events)}".encode("utf-8")
            ).hexdigest(),
            "output_artifact_hashes": list(digests),
        }
        self.events = (*self.events, event)
        self.current_phase = phase_id
        return event


def _write_evidence_authority(runtime, layout):
    materialization, paths, jsonio = runtime
    evidence = json.loads(
        (REPO_ROOT / "tests/fixtures/ultra-runtime/evidence-ledger-valid.json").read_text(
            "utf-8"
        )
    )
    evidence.update(
        {
            "run_id": layout.run_dir.name,
            "version_binding": _module("constants").current_version_binding(),
            "generated_at": "2026-08-02T03:04:05Z",
            "phase_id": "U3",
            "content_sha256": "0" * 64,
        }
    )
    for entry in evidence["entries"]:
        statement_bytes = entry["statement"].encode("utf-8")
        if entry["identity"] == "user-claim":
            origin_kind = "request"
            origin_ref = "request.bin"
            span = [0, len(statement_bytes)]
        else:
            origin_kind = "source"
            origin_ref = entry["source_refs"][0]
            span = None
        entry["attribution"] = {
            "origin_kind": origin_kind,
            "origin_ref": origin_ref,
            "content_sha256": hashlib.sha256(statement_bytes).hexdigest(),
            "span": span,
            "proof_grade": "fixture-bound",
        }
    evidence["content_sha256"] = _module(
        "schemas"
    ).compute_artifact_content_sha256(evidence)
    evidence_path = materialization.artifact_destination(
        layout,
        layout.authoring_dir / "U03-evidence-ledger.json",
    )
    jsonio.atomic_write_json(evidence_path, evidence)
    return evidence_path, evidence


def _prepare_u10_authority_case(runtime, tmp_path: Path):
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    prepared = materialization.prepare_authoring(layout)
    _write_evidence_authority(runtime, layout)
    authority = write_closed_u4_u10_authoring(REPO_ROOT, layout)
    return materialization, jsonio, layout, prepared, authority, _RecordingPhaseStore()


def _freeze_public_foundation_progress(
    runtime,
    layout,
    store: _RecordingPhaseStore,
    monkeypatch: pytest.MonkeyPatch,
    *,
    created_at: datetime,
):
    materialization, paths, jsonio = runtime
    foundation = _module("foundation")
    recovery = _module("recovery")
    status = _module("status")
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"若 A 则 B。",'
        '"material":"本请求是完整且封闭的材料全集。"}\n'
    ).encode("utf-8")
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    jsonio.atomic_write_bytes(layout.input_dir / "request.bin", request_bytes)
    jsonio.atomic_write_json(
        layout.input_dir / "request-metadata.json",
        {
            "request_sha256": request_sha256,
            "request_size": len(request_bytes),
        },
    )
    status_store = status.RunStatusStore(layout)
    created = status_store.create(created_at)
    materialization.seal_request_intake_authority(
        layout,
        request_sha256=request_sha256,
        request_size=len(request_bytes),
        created_at=created.created_at,
    )
    foundation.seal_input_inventory(
        layout,
        request_sha256=request_sha256,
        material_files=(),
        now=created_at,
        request_bytes=request_bytes,
    )
    store.run_contract = {"request_sha256": request_sha256}
    progress = SimpleNamespace(
        outcome="advanced",
        pending_action=None,
        phase_store=store,
        completed_phase="U3",
    )
    monkeypatch.setattr(foundation, "advance_foundation", lambda *args, **kwargs: progress)
    checkpoints: list[dict[str, object]] = []

    def record_checkpoint(*args, **kwargs):
        checkpoint = {
            "boundary_kind": kwargs["boundary_kind"],
            "phase_id": kwargs["boundary_id"],
            "boundary_ordinal": kwargs["boundary_ordinal"],
            "artifact_paths": tuple(kwargs["artifact_paths"]),
        }
        checkpoints.append(checkpoint)
        return checkpoint

    monkeypatch.setattr(recovery, "create_checkpoint", record_checkpoint)
    policy = paths.RootPolicy(layout.root.parent / "production", layout.root)
    return policy, status_store, checkpoints


def _public_materialize(
    runtime,
    layout,
    policy,
    *,
    now: datetime,
    forbidden_calls: list[tuple[object, ...]],
):
    materialization, paths, _ = runtime

    def forbidden(*args):
        forbidden_calls.append(args)
        pytest.fail("validation or publication ran before authoring completed")

    return materialization.materialize_complete_run(
        REPO_ROOT,
        paths.RunMode.TEST,
        layout.run_dir.name,
        policy=policy,
        now=now,
        entropy=f"task-13-b1-{now.second}".encode("ascii"),
        fresh_check=forbidden,
        commit_report=forbidden,
    )


def _write_mutated_plan(jsonio, layout, plan: dict[str, object]) -> None:
    plan["semantic_universe_sha256"] = jsonio.sha256_bytes(
        jsonio.canonical_json_bytes(plan["semantic_universe"])
    )
    jsonio.atomic_write_json(layout.authoring_dir / "U10-output-plan.json", plan)


def _refresh_plan_dependencies(plan: dict[str, object]) -> None:
    units = plan.get("semantic_universe")
    if not isinstance(units, list):
        raise TypeError("test output plan lacks a semantic universe")
    units_by_id = {
        unit["unit_id"]: unit
        for unit in units
        if isinstance(unit, dict) and isinstance(unit.get("unit_id"), str)
    }
    for entry in (*plan["sections"], *plan["appendices"]):
        entry["dependency_hashes"] = list(
            dict.fromkeys(
                units_by_id[unit_id]["authority_artifact_sha256"]
                for unit_id in entry["semantic_unit_ids"]
            )
        )


def _rebind_semantic_unit(
    plan: dict[str, object],
    unit_id: str,
    *,
    artifact_suffix: str,
    authority_locator: str,
) -> None:
    artifact = next(
        record
        for record in plan["required_artifacts"]
        if record["path"].endswith(artifact_suffix)
    )
    unit = next(
        item for item in plan["semantic_universe"] if item["unit_id"] == unit_id
    )
    unit["authority_artifact_sha256"] = artifact["sha256"]
    unit["authority_locator"] = authority_locator
    _refresh_plan_dependencies(plan)


def _assert_u10_rejected_before_outputs(
    materialization,
    layout,
    store: _RecordingPhaseStore,
    *,
    expected_fragment: str,
) -> None:
    with pytest.raises(ValueError) as captured:
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            store,
            now=datetime(2026, 8, 2, 3, 4, 10, tzinfo=timezone.utc),
            create_checkpoint=lambda *args, **kwargs: kwargs,
            commit_guard=lambda: None,
        )
    assert expected_fragment in str(captured.value)
    assert all(event["phase_id"] not in {"U10", "U11"} for event in store.events)
    assert not (layout.authoring_dir / "article.partial.md").exists()
    assert list(layout.delivery_dir.glob("*")) == []


def test_task13_materialization_module_exists_for_red_gate() -> None:
    assert MATERIALIZATION_PATH.is_file(), MATERIALIZATION_PATH


def test_prepare_returns_only_the_frozen_model_owned_slots(runtime, tmp_path: Path) -> None:
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)

    prepared = materialization.prepare_authoring(layout)

    assert tuple(prepared.relative_slots) == EXPECTED_AUTHORING_SLOTS
    assert prepared.authoring_dir == layout.authoring_dir
    assert prepared.control_path == layout.artifacts_dir / "ultra-materialization-control.json"
    assert prepared.control_path.is_file()
    control = jsonio.load_json_object(prepared.control_path)
    assert control == materialization.build_materialization_control(layout)
    assert control["run_id"] == layout.run_dir.name
    assert control["authoring_slots"] == list(EXPECTED_AUTHORING_SLOTS)
    assert all(
        path == layout.authoring_dir or layout.authoring_dir in path.parents
        for path in prepared.slot_paths
    )
    assert not any(path.is_file() for path in prepared.slot_paths)
    assert not (layout.authoring_dir / "article.partial.md").exists()
    assert not (layout.authoring_dir / "U09-forecast-resolution.json").exists()
    assert list(layout.delivery_dir.glob("*")) == []


def test_public_materialize_after_only_u4_returns_u5_wait(
    runtime,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    _write_evidence_authority(runtime, layout)
    store = _RecordingPhaseStore()
    policy, status_store, checkpoints = _freeze_public_foundation_progress(
        runtime,
        layout,
        store,
        monkeypatch,
        created_at=datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    forbidden_calls: list[tuple[object, ...]] = []

    first = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    assert first.status == "running"
    assert first.outcome == "awaiting-authoring"
    assert first.current_phase == "U4"
    assert first.last_complete_phase == "U3"
    assert first.next_action is not None
    assert first.next_action["relative_path"] == "U04-world-volume.json"

    world = json.loads(
        (
            REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json"
        ).read_text("utf-8")
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / str(first.next_action["relative_path"]),
        world,
    )
    second = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 7, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )

    assert second.status == "running"
    assert second.outcome == "awaiting-authoring"
    assert second.current_phase == "U5"
    assert second.last_complete_phase == "U4"
    assert second.next_action is not None
    assert second.next_action["relative_path"] == "U05-transformation-ledger.json"
    assert second.next_action["relative_paths"] == [
        "U05-transformation-ledger.json",
        "U05-concept-disposition.json",
    ]
    assert [event["phase_id"] for event in store.events] == ["U4"]
    assert [checkpoint["phase_id"] for checkpoint in checkpoints] == ["U4"]
    assert not (
        layout.artifacts_dir
        / "U04-U05-world-volume/U05-transformation-ledger.json"
    ).exists()
    assert not (
        layout.artifacts_dir / "U04-U05-world-volume/U05-concept-disposition.json"
    ).exists()
    assert status_store.read().status == "running"
    assert forbidden_calls == []
    assert not (layout.recovery_dir / "publish-transaction.json").exists()
    assert not (layout.artifacts_dir / "ultra-artifact-manifest.json").exists()
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_stale_u4_writer_is_fenced_before_formal_artifact_overwrite(
    runtime,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, paths, jsonio = runtime
    locks = _module("locks")
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    _write_evidence_authority(runtime, layout)
    store = _RecordingPhaseStore()
    policy, status_store, checkpoints = _freeze_public_foundation_progress(
        runtime,
        layout,
        store,
        monkeypatch,
        created_at=datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    world_source = layout.authoring_dir / "U04-world-volume.json"
    jsonio.atomic_write_json(
        world_source,
        json.loads(
            (
                REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json"
            ).read_text("utf-8")
        ),
    )
    destination = materialization.artifact_destination(layout, world_source)
    sentinel = b"foreign owner U4 formal artifact\n"
    real_seal = materialization.seal_authoring_artifact
    transferred = False

    def seal_then_transfer_owner(*args, **kwargs):
        nonlocal transferred
        sealed = real_seal(*args, **kwargs)
        source = args[1]
        if source == world_source and not transferred:
            transferred = True
            lease_path = layout.run_dir / ".writer-lease.json"
            owner = jsonio.load_json_object(lease_path)
            owner["owner_nonce"] = "foreign-u4-owner-0000000000000"
            jsonio.atomic_write_json(lease_path, owner)
            jsonio.atomic_write_bytes(destination, sentinel)
        return sealed

    monkeypatch.setattr(
        materialization,
        "seal_authoring_artifact",
        seal_then_transfer_owner,
    )
    forbidden_calls: list[tuple[object, ...]] = []
    with pytest.raises(locks.LeaseOwnershipError):
        _public_materialize(
            runtime,
            layout,
            policy,
            now=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
            forbidden_calls=forbidden_calls,
        )

    assert transferred is True
    assert destination.read_bytes() == sentinel
    assert all(event["phase_id"] != "U4" for event in store.events)
    assert checkpoints == []
    assert status_store.read().status == "running"
    assert forbidden_calls == []


def test_public_authoring_wait_does_not_hide_malformed_present_sibling(
    runtime,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    _write_evidence_authority(runtime, layout)
    store = _RecordingPhaseStore()
    policy, status_store, checkpoints = _freeze_public_foundation_progress(
        runtime,
        layout,
        store,
        monkeypatch,
        created_at=datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    forbidden_calls: list[tuple[object, ...]] = []
    first = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    world = json.loads(
        (
            REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json"
        ).read_text("utf-8")
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / str(first.next_action["relative_path"]),
        world,
    )
    malformed_path = layout.authoring_dir / "U05-transformation-ledger.json"
    malformed_bytes = b'{"malformed":\n'
    malformed_path.write_bytes(malformed_bytes)

    with pytest.raises(ValueError, match="U05-transformation-ledger|unreadable|JSON"):
        _public_materialize(
            runtime,
            layout,
            policy,
            now=datetime(2026, 8, 2, 3, 4, 7, tzinfo=timezone.utc),
            forbidden_calls=forbidden_calls,
        )

    assert malformed_path.read_bytes() == malformed_bytes
    assert [event["phase_id"] for event in store.events] == ["U4"]
    assert [checkpoint["phase_id"] for checkpoint in checkpoints] == ["U4"]
    assert status_store.read().status == "running"
    assert forbidden_calls == []
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_public_u11_waits_for_each_declared_semantic_input_before_review(
    runtime,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, jsonio, layout, _, output_authority, store = (
        _prepare_u10_authority_case(runtime, tmp_path)
    )
    with pytest.raises(ValueError, match="packet count"):
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            store,
            now=datetime(2026, 8, 2, 3, 4, 10, tzinfo=timezone.utc),
            create_checkpoint=lambda *args, **kwargs: kwargs,
            commit_guard=lambda: None,
        )
    assert store.current_phase == "U10"
    policy, status_store, checkpoints = _freeze_public_foundation_progress(
        runtime,
        layout,
        store,
        monkeypatch,
        created_at=datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
    )
    sealed_plan = jsonio.load_json_object(
        layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
    )
    write_closed_u11_authoring(
        REPO_ROOT,
        layout,
        sealed_plan,
        output_authority,
        generated_at="2026-08-02T03:04:15Z",
    )
    authored_paths = (
        *sorted(
            (layout.authoring_dir / "article/packets").glob("*.md"),
            key=lambda path: path.name,
        ),
        layout.authoring_dir / "U11-semantic-coverage.json",
        layout.authoring_dir / "U11-article-review.json",
        layout.authoring_dir / "完整推演档案.md",
    )
    authored = {
        path.relative_to(layout.authoring_dir).as_posix(): path.read_bytes()
        for path in authored_paths
    }
    for path in authored_paths:
        path.unlink()
    (layout.authoring_dir / "article.partial.md").unlink()
    semantic_review = _module("semantic_review")
    semantic_action_path = semantic_review.semantic_review_action_path(layout, 0)
    forbidden_calls: list[tuple[object, ...]] = []

    packet_wait = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 11, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    assert packet_wait.status == "running"
    assert packet_wait.outcome == "awaiting-authoring"
    assert packet_wait.current_phase == "U11"
    assert packet_wait.last_complete_phase == "U10"
    assert packet_wait.next_action is not None
    assert packet_wait.next_action["relative_path"] == (
        "article/packets/<packet-id>.md"
    )
    assert "relative_paths" not in packet_wait.next_action
    assert not semantic_action_path.exists()

    packet_relatives = sorted(
        relative
        for relative in authored
        if relative.startswith("article/packets/")
    )
    assert packet_relatives
    for relative in packet_relatives:
        target = layout.authoring_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(authored[relative])

    coverage_wait = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 12, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    assert coverage_wait.outcome == "awaiting-authoring"
    assert coverage_wait.next_action is not None
    assert coverage_wait.next_action["relative_path"] == (
        "U11-semantic-coverage.json"
    )
    assert coverage_wait.next_action["relative_paths"] == [
        "U11-semantic-coverage.json",
        "U11-article-review.json",
        "完整推演档案.md",
    ]
    assert not semantic_action_path.exists()

    (layout.authoring_dir / "U11-semantic-coverage.json").write_bytes(
        authored["U11-semantic-coverage.json"]
    )
    review_wait = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 13, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    assert review_wait.outcome == "awaiting-authoring"
    assert review_wait.next_action is not None
    assert review_wait.next_action["relative_path"] == "U11-article-review.json"
    assert review_wait.next_action["relative_paths"] == [
        "U11-article-review.json",
        "完整推演档案.md",
    ]
    assert not semantic_action_path.exists()

    (layout.authoring_dir / "U11-article-review.json").write_bytes(
        authored["U11-article-review.json"]
    )
    dossier_wait = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 14, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    assert dossier_wait.outcome == "awaiting-authoring"
    assert dossier_wait.next_action is not None
    assert dossier_wait.next_action["relative_path"] == "完整推演档案.md"
    assert "relative_paths" not in dossier_wait.next_action
    assert not semantic_action_path.exists()

    (layout.authoring_dir / "完整推演档案.md").write_bytes(
        authored["完整推演档案.md"]
    )
    semantic_wait = _public_materialize(
        runtime,
        layout,
        policy,
        now=datetime(2026, 8, 2, 3, 4, 15, tzinfo=timezone.utc),
        forbidden_calls=forbidden_calls,
    )
    assert semantic_wait.status == "running"
    assert semantic_wait.outcome == "awaiting-host-action"
    assert semantic_wait.current_phase == "U11"
    assert semantic_wait.last_complete_phase == "U10"
    assert semantic_wait.next_action is not None
    assert semantic_wait.next_action["action_kind"] == "semantic-review"
    assert semantic_action_path.is_file()
    assert all(event["phase_id"] != "U11" for event in store.events)
    assert all(
        checkpoint["phase_id"] != "U11"
        for checkpoint in checkpoints
        if checkpoint["boundary_kind"] == "phase"
    )
    assert status_store.read().status == "running"
    assert forbidden_calls == []
    assert not (layout.recovery_dir / "publish-transaction.json").exists()
    assert not (layout.artifacts_dir / "ultra-artifact-manifest.json").exists()
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_discovery_freezes_recursive_and_cross_phase_dependency_order(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    authored = (
        "U09-forecast-ledger.json",
        "U08-red-team-report.json",
        "U09-action-ranking.json",
        "U07-recursive-states/node-z.json",
        "U09-verdict.json",
        "U08-order-evaluation.json",
        "U07-recursive-lineage.json",
        "U07-recursive-states/node-a.json",
    )
    for relative in authored:
        target = layout.authoring_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"{}\n")

    discovered = materialization.discover_authoring_inputs(layout)
    names = tuple(path.relative_to(layout.authoring_dir).as_posix() for path in discovered)

    assert names.index("U07-recursive-states/node-a.json") < names.index(
        "U07-recursive-lineage.json"
    )
    assert names.index("U07-recursive-states/node-z.json") < names.index(
        "U07-recursive-lineage.json"
    )
    assert names.index("U07-recursive-states/node-a.json") < names.index(
        "U07-recursive-states/node-z.json"
    )
    assert names.index("U08-order-evaluation.json") < names.index(
        "U08-red-team-report.json"
    )
    assert names.index("U09-verdict.json") < names.index(
        "U09-action-ranking.json"
    )
    assert names.index("U09-verdict.json") < names.index(
        "U09-forecast-ledger.json"
    )


def test_runtime_overwrites_model_owned_envelope_and_validates_closed_schema(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    source = layout.authoring_dir / "U04-world-volume.json"
    document = json.loads(
        (REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json").read_text(
            "utf-8"
        )
    )
    document.update(
        {
            "schema_id": "model.forged.schema",
            "run_id": "model-controlled-run",
            "version_binding": {"runtime_version": "999.0.0"},
            "generated_at": "1999-01-01T00:00:00Z",
            "phase_id": "U12",
            "content_sha256": "f" * 64,
        }
    )
    source.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    sealed = materialization.seal_authoring_artifact(
        layout,
        source,
        generated_at=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
    )

    assert sealed["schema_id"] == "crossframe.ultra.v82.world-volume"
    assert sealed["run_id"] == layout.run_dir.name
    assert sealed["phase_id"] == "U4"
    assert sealed["generated_at"] == "2026-08-02T03:04:06Z"
    assert sealed["version_binding"] == _module("constants").current_version_binding()
    assert sealed["content_sha256"] == _module(
        "schemas"
    ).compute_artifact_content_sha256(sealed)
    assert jsonio.load_json_object(source) == sealed

    document = dict(sealed)
    document["model_runtime_field"] = "must not cross the boundary"
    source.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(Exception, match="field|schema|unevaluated|Additional"):
        materialization.seal_authoring_artifact(
            layout,
            source,
            generated_at=datetime(2026, 8, 2, 3, 4, 7, tzinfo=timezone.utc),
        )


def test_runtime_rebinds_parent_run_identity_and_nested_output_plan_hashes(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    generated_at = datetime(2026, 8, 2, 3, 4, 8, tzinfo=timezone.utc)

    recursive_source = (
        layout.authoring_dir / "U07-recursive-states/NODE-MAIN-ORDER-1.json"
    )
    recursive_source.write_bytes(
        (
            REPO_ROOT / "tests/fixtures/ultra-runtime/recursive-state-valid.json"
        ).read_bytes()
    )
    recursive = materialization.seal_authoring_artifact(
        layout,
        recursive_source,
        generated_at=generated_at,
    )
    assert recursive["parent_run_id"] == layout.run_dir.name

    authority = json.loads(
        (
            REPO_ROOT
            / "tests/fixtures/ultra-runtime/article-packets/frozen-upstream-authority.json"
        ).read_text("utf-8")
    )
    required_paths = (
        "artifacts/U09-U10-verdict/U09-verdict.json",
        "artifacts/U09-U10-verdict/U09-action-ranking.json",
    )
    old_hashes = tuple(record["sha256"] for record in authority["required_artifacts"])
    new_hashes = []
    for ordinal, relative in enumerate(required_paths, start=1):
        target = layout.run_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"frozen artifact {ordinal}\n".encode("utf-8"))
        new_hashes.append(hashlib.sha256(target.read_bytes()).hexdigest())
    required_artifacts = [
        {
            "path": relative,
            "sha256": old_hash,
            "media_type": "application/json",
        }
        for relative, old_hash in zip(required_paths, old_hashes, strict=True)
    ]
    article = _module("article")
    plan = article.build_output_plan_artifact(
        run_id=layout.run_dir.name,
        version_binding=_module("constants").current_version_binding(),
        generated_at="2026-08-02T03:04:08Z",
        u9_parent_event_sha256="9" * 64,
        article_path="work/authoring/article.partial.md",
        sections=authority["sections"],
        appendices=authority["appendices"],
        required_artifacts=required_artifacts,
        semantic_universe=authority["semantic_universe"],
        blind_recovery_expectations=authority["blind_recovery_expectations"],
    )
    plan_source = layout.authoring_dir / "U10-output-plan.json"
    plan_source.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    sealed = materialization.seal_authoring_artifact(
        layout,
        plan_source,
        generated_at=generated_at,
        authority_values={
            "u9_parent_event_sha256": "9" * 64,
            "output_plan_required_artifacts": [
                {
                    "path": relative,
                    "sha256": digest,
                    "media_type": "application/json",
                }
                for relative, digest in zip(
                    required_paths,
                    new_hashes,
                    strict=True,
                )
            ],
        },
    )

    assert [record["sha256"] for record in sealed["required_artifacts"]] == new_hashes
    assert {
        digest
        for entry in (*sealed["sections"], *sealed["appendices"])
        for digest in entry["dependency_hashes"]
    } == set(new_hashes)
    assert {
        unit["authority_artifact_sha256"]
        for unit in sealed["semantic_universe"]
    } == set(new_hashes)
    assert sealed["semantic_universe_sha256"] == _module("jsonio").sha256_bytes(
        _module("jsonio").canonical_json_bytes(sealed["semantic_universe"])
    )


def test_output_plan_dependencies_must_resolve_inside_the_artifacts_namespace(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    materialization.prepare_authoring(layout)
    outside = layout.input_dir / "request.bin"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_bytes(b"request\n")
    authority = json.loads(
        (
            REPO_ROOT
            / "tests/fixtures/ultra-runtime/article-packets/frozen-upstream-authority.json"
        ).read_text("utf-8")
    )
    authority["required_artifacts"][0]["path"] = "input/request.bin"
    plan_source = layout.authoring_dir / "U10-output-plan.json"
    plan_source.write_text(json.dumps(authority, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="artifacts"):
        materialization.seal_authoring_artifact(
            layout,
            plan_source,
            generated_at=datetime(2026, 8, 2, 3, 4, 9, tzinfo=timezone.utc),
        )


@pytest.mark.parametrize(
    "mutation",
    ("control-only", "omit-verdict", "omit-action", "omit-forecast"),
)
def test_materialization_rejects_self_selected_or_core_omitting_u10_authority(
    runtime,
    tmp_path: Path,
    mutation: str,
) -> None:
    materialization, jsonio, layout, prepared, _, store = (
        _prepare_u10_authority_case(runtime, tmp_path)
    )
    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    entries = (*plan["sections"], *plan["appendices"])
    units = plan["semantic_universe"]
    if mutation == "control-only":
        control_hash = hashlib.sha256(prepared.control_path.read_bytes()).hexdigest()
        plan["required_artifacts"] = [
            {
                "path": prepared.control_path.relative_to(layout.run_dir).as_posix(),
                "sha256": control_hash,
                "media_type": "application/json",
            }
        ]
        for entry in entries:
            entry["dependency_hashes"] = [control_hash]
        for unit in units:
            unit["authority_artifact_sha256"] = control_hash
            unit["authority_locator"] = "materialization-control"
    else:
        suffix = {
            "omit-verdict": "/U09-verdict.json",
            "omit-action": "/U09-action-ranking.json",
            "omit-forecast": "/U09-forecast-ledger.json",
        }[mutation]
        removed = next(
            record
            for record in plan["required_artifacts"]
            if record["path"].endswith(suffix)
        )
        fallback = next(
            record
            for record in plan["required_artifacts"]
            if record["path"].endswith("/U03-evidence-ledger.json")
        )
        plan["required_artifacts"] = [
            record for record in plan["required_artifacts"] if record is not removed
        ]
        for entry in entries:
            entry["dependency_hashes"] = list(
                dict.fromkeys(
                    fallback["sha256"] if digest == removed["sha256"] else digest
                    for digest in entry["dependency_hashes"]
                )
            )
        for unit in units:
            if unit["authority_artifact_sha256"] == removed["sha256"]:
                unit["authority_artifact_sha256"] = fallback["sha256"]
                unit["authority_locator"] = "EVIDENCE-ROSTER-ATLAS"
    _write_mutated_plan(jsonio, layout, plan)

    _assert_u10_rejected_before_outputs(
        materialization,
        layout,
        store,
        expected_fragment="runtime-derived U3-U9 required_artifacts",
    )


@pytest.mark.parametrize(
    "locator",
    ("VERDICT-NOT-PRESENT", "OPTION-PROBE"),
    ids=("fabricated", "mismatched-artifact"),
)
def test_materialization_rejects_locator_outside_its_bound_upstream_artifact(
    runtime,
    tmp_path: Path,
    locator: str,
) -> None:
    materialization, jsonio, layout, _, _, store = _prepare_u10_authority_case(
        runtime,
        tmp_path,
    )
    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    unit = next(
        item
        for item in plan["semantic_universe"]
        if item["unit_id"] == "UNIT-FIVE-VERDICTS"
    )
    verdict_authority = next(
        record
        for record in plan["required_artifacts"]
        if record["path"].endswith("/U09-verdict.json")
    )
    assert unit["authority_artifact_sha256"] == verdict_authority["sha256"]
    unit["authority_locator"] = locator
    _write_mutated_plan(jsonio, layout, plan)

    _assert_u10_rejected_before_outputs(
        materialization,
        layout,
        store,
        expected_fragment="authority_locator",
    )


def test_materialization_rejects_omitted_required_concept_semantic_unit(
    runtime,
    tmp_path: Path,
) -> None:
    materialization, jsonio, layout, _, _, store = _prepare_u10_authority_case(
        runtime,
        tmp_path,
    )
    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    omitted_id = "SEMANTIC-UNIT-V82-M01"
    plan["semantic_universe"] = [
        unit for unit in plan["semantic_universe"] if unit["unit_id"] != omitted_id
    ]
    for entry in (*plan["sections"], *plan["appendices"]):
        entry["semantic_unit_ids"] = [
            unit_id for unit_id in entry["semantic_unit_ids"] if unit_id != omitted_id
        ]
    _refresh_plan_dependencies(plan)
    _write_mutated_plan(jsonio, layout, plan)

    _assert_u10_rejected_before_outputs(
        materialization,
        layout,
        store,
        expected_fragment="required concept semantic units",
    )


@pytest.mark.parametrize(
    ("unit_id", "expected_suffix"),
    (
        (
            "UNIT-ORDER-2",
            "/U07-recursive-states/NODE-MAIN-ORDER-2.json",
        ),
        ("UNIT-APPENDIX-BRANCHES", "/U07-recursive-lineage.json"),
        ("UNIT-CONFIDENCE", "/U08-order-evaluation.json"),
    ),
    ids=("recursive-state", "recursive-lineage", "order-evaluation"),
)
def test_materialization_requires_every_runtime_artifact_to_authorize_a_semantic_unit(
    runtime,
    tmp_path: Path,
    unit_id: str,
    expected_suffix: str,
) -> None:
    materialization, jsonio, layout, _, _, store = _prepare_u10_authority_case(
        runtime,
        tmp_path,
    )
    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    unit = next(
        item for item in plan["semantic_universe"] if item["unit_id"] == unit_id
    )
    original = next(
        record
        for record in plan["required_artifacts"]
        if record["sha256"] == unit["authority_artifact_sha256"]
    )
    assert original["path"].endswith(expected_suffix)
    _rebind_semantic_unit(
        plan,
        unit_id,
        artifact_suffix="/U03-evidence-ledger.json",
        authority_locator="EVIDENCE-ROSTER-ATLAS",
    )
    _write_mutated_plan(jsonio, layout, plan)

    _assert_u10_rejected_before_outputs(
        materialization,
        layout,
        store,
        expected_fragment="without semantic-unit authority",
    )


def test_closed_fixture_assigns_semantic_authority_to_all_seventeen_upstream_artifacts(
    runtime,
    tmp_path: Path,
) -> None:
    _, jsonio, layout, _, _, _ = _prepare_u10_authority_case(runtime, tmp_path)
    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")

    required_hashes = {
        record["sha256"] for record in plan["required_artifacts"]
    }
    represented_hashes = {
        unit["authority_artifact_sha256"] for unit in plan["semantic_universe"]
    }

    assert len(required_hashes) == 17
    assert represented_hashes == required_hashes


@pytest.mark.parametrize(
    ("unit_id", "artifact_suffix", "reference_locator"),
    (
        (
            "UNIT-CIRCLE-RELATION",
            "/U05-transformation-ledger.json",
            "UNKNOWN-ADAPTATION",
        ),
        (
            "UNIT-FIVE-VERDICTS",
            "/U09-verdict.json",
            "EXPLANATION-RIVAL",
        ),
    ),
    ids=("u5-unknown-reference", "u9-explanation-reference"),
)
def test_materialization_rejects_reference_only_authority_locator(
    runtime,
    tmp_path: Path,
    unit_id: str,
    artifact_suffix: str,
    reference_locator: str,
) -> None:
    materialization, jsonio, layout, _, _, store = _prepare_u10_authority_case(
        runtime,
        tmp_path,
    )
    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    _rebind_semantic_unit(
        plan,
        unit_id,
        artifact_suffix=artifact_suffix,
        authority_locator=reference_locator,
    )
    _write_mutated_plan(jsonio, layout, plan)

    _assert_u10_rejected_before_outputs(
        materialization,
        layout,
        store,
        expected_fragment="authority_locator",
    )


def test_materialization_rejects_ambiguous_cross_owner_evidence_locator(
    runtime,
    tmp_path: Path,
) -> None:
    materialization, jsonio, layout, _, _, store = _prepare_u10_authority_case(
        runtime,
        tmp_path,
    )
    evidence_path = materialization.artifact_destination(
        layout,
        layout.authoring_dir / "U03-evidence-ledger.json",
    )
    evidence_document = jsonio.load_json_object(evidence_path)
    duplicate_locator = evidence_document["entries"][0]["evidence_id"]
    evidence_document["unknowns"].append(
        {
            "unknown_id": duplicate_locator,
            "location_ref": "POS-TEAM-MANAGER",
            "description": "This string identifies a distinct unknown owner record.",
            "resolution_condition": "Observe the next review cycle.",
        }
    )
    evidence_document["content_sha256"] = _module(
        "schemas"
    ).compute_artifact_content_sha256(evidence_document)
    _module("evidence").validate_evidence_artifact(
        evidence_document,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=_module("constants").current_version_binding(),
        expected_phase_id="U3",
        expected_evidence_cutoff=evidence_document["evidence_cutoff"],
    )
    jsonio.atomic_write_json(evidence_path, evidence_document)

    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    _rebind_semantic_unit(
        plan,
        "UNIT-DECISIVE-EVIDENCE",
        artifact_suffix="/U03-evidence-ledger.json",
        authority_locator=duplicate_locator,
    )
    _write_mutated_plan(jsonio, layout, plan)

    _assert_u10_rejected_before_outputs(
        materialization,
        layout,
        store,
        expected_fragment="duplicate owner locator",
    )


def test_materialization_accepts_owned_transformation_effective_variable_locator(
    runtime,
    tmp_path: Path,
) -> None:
    materialization, jsonio, layout, _, _, store = _prepare_u10_authority_case(
        runtime,
        tmp_path,
    )
    transformation_document = jsonio.load_json_object(
        layout.authoring_dir / "U05-transformation-ledger.json"
    )
    variable_locator = transformation_document["transformations"][0][
        "effective_variables"
    ][0]["variable_ref"]
    assert variable_locator == "VAR-SCALE-MANAGER-BUDGET"

    plan = jsonio.load_json_object(layout.authoring_dir / "U10-output-plan.json")
    _rebind_semantic_unit(
        plan,
        "UNIT-CIRCLE-RELATION",
        artifact_suffix="/U05-transformation-ledger.json",
        authority_locator=variable_locator,
    )
    _write_mutated_plan(jsonio, layout, plan)

    with pytest.raises(
        ValueError,
        match="article packet count differs from the frozen output plan",
    ):
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            store,
            now=datetime(2026, 8, 2, 3, 4, 10, tzinfo=timezone.utc),
            create_checkpoint=lambda *args, **kwargs: kwargs,
            commit_guard=lambda: None,
        )
    assert any(event["phase_id"] == "U10" for event in store.events)
    assert all(event["phase_id"] != "U11" for event in store.events)
    assert not (layout.authoring_dir / "article.partial.md").exists()
    assert list(layout.delivery_dir.glob("*")) == []


def test_u11_materialization_rejects_external_dependent_mechanical_review(
    runtime,
    tmp_path: Path,
) -> None:
    materialization, jsonio, layout, _, output_authority, store = (
        _prepare_u10_authority_case(runtime, tmp_path)
    )
    with pytest.raises(ValueError, match="packet count"):
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            store,
            now=datetime(2026, 8, 2, 3, 4, 10, tzinfo=timezone.utc),
            create_checkpoint=lambda *args, **kwargs: kwargs,
            commit_guard=lambda: None,
        )
    sealed_plan = jsonio.load_json_object(
        layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
    )
    generated_at = "2026-08-02T03:04:11Z"
    write_closed_u11_authoring(
        REPO_ROOT,
        layout,
        sealed_plan,
        output_authority,
        generated_at=generated_at,
    )

    packet_path = layout.authoring_dir / "article/packets/packet-01.md"
    packet_path.write_text(
        packet_path.read_text("utf-8").rstrip()
        + "\n\n完整判断依据详见附件。\n",
        encoding="utf-8",
        newline="\n",
    )
    article = _module("article")
    coverage = _module("coverage")
    packet_paths = tuple(
        sorted(
            (layout.authoring_dir / "article/packets").glob("*.md"),
            key=lambda path: path.name,
        )
    )
    assembled = article.assemble_article(
        sealed_plan,
        materialization._packet_mappings(sealed_plan, packet_paths),
        layout.authoring_dir / "article.partial.md",
    )
    plan_sha256 = hashlib.sha256(jsonio.canonical_json_bytes(sealed_plan)).hexdigest()
    coverage_document = coverage.build_semantic_coverage_artifact(
        assembled.article_text,
        sealed_plan,
        output_authority["mappings"],
        run_id=layout.run_dir.name,
        version_binding=_module("constants").current_version_binding(),
        generated_at=generated_at,
        expected_output_plan_artifact_sha256=plan_sha256,
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / "U11-semantic-coverage.json",
        coverage_document,
    )
    review_document = coverage.build_article_review_artifact(
        assembled.article_text,
        sealed_plan,
        coverage_document,
        run_id=layout.run_dir.name,
        version_binding=_module("constants").current_version_binding(),
        generated_at=generated_at,
        expected_output_plan_artifact_sha256=plan_sha256,
        expected_coverage_artifact_sha256=hashlib.sha256(
            jsonio.canonical_json_bytes(coverage_document)
        ).hexdigest(),
    )
    assert review_document["overall_status"] == "mechanical-fail"
    assert review_document["external_dependencies"]
    jsonio.atomic_write_json(
        layout.authoring_dir / "U11-article-review.json",
        review_document,
    )

    with pytest.raises(ValueError, match="mechanical-complete"):
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            store,
            now=datetime(2026, 8, 2, 3, 4, 11, tzinfo=timezone.utc),
            create_checkpoint=lambda *args, **kwargs: kwargs,
            commit_guard=lambda: None,
        )
    assert all(event["phase_id"] != "U11" for event in store.events)


def test_materialization_rejects_a_forged_layout_outside_the_selected_root(
    runtime, tmp_path: Path
) -> None:
    materialization, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    forged = paths.RunLayout(
        root=layout.root,
        root_staging_dir=layout.root_staging_dir,
        run_dir=tmp_path / "escape",
        input_dir=layout.input_dir,
        authoring_dir=layout.authoring_dir,
        artifacts_dir=layout.artifacts_dir,
        delivery_dir=layout.delivery_dir,
        validation_dir=layout.validation_dir,
        validation_current_dir=layout.validation_current_dir,
        validation_attempts_dir=layout.validation_attempts_dir,
        recovery_dir=layout.recovery_dir,
        logs_dir=layout.logs_dir,
    )

    with pytest.raises((TypeError, ValueError), match="outside|layout|root|run"):
        materialization.prepare_authoring(forged)
