from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import sys

from tests.pytest_import_guard import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
DELIVERABLES_PATH = RUNTIME_DIR / "deliverables.py"
RUN_ID = "20260802T030405Z-000000000013"
TRANSACTION_ID = "20260802T030410Z-aaaaaaaaaaaa"
SEMANTIC_REVIEW = {
    "schema_id": "crossframe.ultra.v82.semantic-review",
    "phase_id": "U11",
    "run_id": RUN_ID,
    "overall_status": "pass",
    "publication_allowed": True,
    "active_generation": 0,
}
SEMANTIC_REVIEW_BYTES = (
    json.dumps(
        SEMANTIC_REVIEW,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    + "\n"
).encode("utf-8")


def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module(f"ultra_runtime.{name}")


@pytest.fixture
def runtime():
    if not DELIVERABLES_PATH.is_file():
        pytest.skip(f"Task 13 delivery runtime is not implemented: {DELIVERABLES_PATH}")
    return _module("deliverables"), _module("paths"), _module("jsonio")


def _layout(paths, tmp_path: Path):
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    layout = paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)
    semantic_path = (
        layout.artifacts_dir
        / "U09-U10-verdict/U11-semantic-review.json"
    )
    semantic_path.parent.mkdir(parents=True, exist_ok=True)
    semantic_path.write_bytes(SEMANTIC_REVIEW_BYTES)
    return layout


def _payload() -> dict[str, bytes]:
    return {
        "article_bytes": "# CrossFrame Ultra 完整文章\n\n正文。\n".encode("utf-8"),
        "dossier_bytes": "# 完整推演档案\n\n推演。\n".encode("utf-8"),
        "artifact_index_bytes": "# 工件索引\n\n索引。\n".encode("utf-8"),
        "manifest_bytes": b'{"manifest":"new"}\n',
    }


def _layered_report(
    payload: dict[str, bytes],
    *,
    failed_layer: str | None = None,
    article_sha256: str | None = None,
    manifest_sha256: str | None = None,
    semantic_review_artifact_sha256: str | None = None,
    active_generation: int = 0,
    include_checks: bool = True,
) -> bytes:
    layers = [
        {
            "layer_id": layer_id,
            "status": "fail" if layer_id == failed_layer else "pass",
            "artifact_refs": [],
        }
        for layer_id in ("deterministic", "adversarial", "fresh-semantic")
    ]
    report = {
        "overall_status": "pass",
        "publication_allowed": True,
        "article_sha256": article_sha256
        or hashlib.sha256(payload["article_bytes"]).hexdigest(),
        "manifest_sha256": manifest_sha256
        or hashlib.sha256(payload["manifest_bytes"]).hexdigest(),
        "semantic_review_artifact_sha256": (
            semantic_review_artifact_sha256
            or hashlib.sha256(SEMANTIC_REVIEW_BYTES).hexdigest()
        ),
        "active_generation": active_generation,
        "checks": (
            [
                {
                    "validator_id": "schema-closure",
                    "status": "pass",
                    "error_codes": [],
                    "artifact_refs": [],
                }
            ]
            if include_checks
            else []
        ),
        "layers": layers,
    }
    return (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def test_task13_delivery_module_exists_for_red_gate() -> None:
    assert DELIVERABLES_PATH.is_file(), DELIVERABLES_PATH


def test_publication_paths_are_fixed_and_cannot_be_redirected(runtime, tmp_path: Path) -> None:
    deliverables, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)

    assert publication.staging_dir == (
        layout.root_staging_dir / RUN_ID / f"publish-{TRANSACTION_ID}"
    )
    assert publication.journal_path == layout.recovery_dir / "publish-transaction.json"
    assert publication.backup_dir == (
        layout.recovery_dir / "publish-backups" / TRANSACTION_ID
    )
    assert publication.manifest_path == (
        layout.artifacts_dir / "ultra-artifact-manifest.json"
    )
    assert publication.article_path == (
        layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
    )
    assert publication.dossier_path == layout.delivery_dir / "完整推演档案.md"
    assert publication.artifact_index_path == layout.delivery_dir / "工件索引.md"

    with pytest.raises((TypeError, ValueError), match="transaction|safe|component"):
        deliverables.publication_paths(layout, "../escape")


def test_successful_publish_is_journal_stage_precheck_backup_publish_postcheck(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    observed: list[str] = []
    payload = _payload()
    expected_report = _layered_report(payload)

    def fresh_check(stage: str) -> bytes:
        observed.append(f"check:{stage}")
        assert publication.journal_path.is_file()
        if stage == "pre-publish":
            assert publication.staging_dir.is_dir()
            assert not publication.article_path.exists()
            assert not publication.backup_dir.exists()
        else:
            assert publication.backup_dir.is_dir()
            assert publication.article_path.read_bytes() == _payload()["article_bytes"]
            assert publication.manifest_path.read_bytes() == _payload()["manifest_bytes"]
        return expected_report

    def commit_report(stage: str, report_bytes: bytes, lease: object) -> None:
        observed.append(f"commit:{stage}")
        assert report_bytes == expected_report

    result = deliverables.publish_delivery(
        layout,
        transaction_id=TRANSACTION_ID,
        fresh_check=fresh_check,
        commit_report=commit_report,
        mark_needs_attention=lambda reason: pytest.fail(reason),
        **payload,
    )

    assert observed == [
        "check:pre-publish",
        "commit:pre-publish",
        "check:post-publish",
        "commit:post-publish",
    ]
    assert result.postcheck_passed is True
    assert result.paths == publication
    assert publication.article_path.read_bytes() == _payload()["article_bytes"]
    assert publication.dossier_path.read_bytes() == _payload()["dossier_bytes"]
    assert publication.artifact_index_path.read_bytes() == _payload()[
        "artifact_index_bytes"
    ]
    assert publication.manifest_path.read_bytes() == _payload()["manifest_bytes"]
    assert publication.journal_path.is_file()
    assert publication.backup_dir.is_dir()
    assert publication.staging_dir.is_dir()
    journal = jsonio.load_json_object(publication.journal_path)
    assert journal["transaction_id"] == TRANSACTION_ID
    assert journal["state"] == "postchecked"
    assert journal["postcheck_passed"] is True


def test_publish_rejects_existing_cancel_intent_before_any_publication_work(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, _ = runtime
    locks = _module("locks")
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    previous = {
        target: f"previous {target.name}\n".encode("utf-8")
        for target in publication.official_paths
    }
    for target, value in previous.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    lease = locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    try:
        locks.request_cancel(
            layout,
            reason="cancel before publication",
            now=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
        )
        with pytest.raises(locks.CancelledRunError):
            deliverables.publish_delivery(
                layout,
                transaction_id=TRANSACTION_ID,
                fresh_check=lambda stage: pytest.fail(
                    f"fresh checker ran after cancellation: {stage}"
                ),
                commit_report=lambda stage, report, lease: pytest.fail(
                    f"report commit ran after cancellation: {stage}"
                ),
                mark_needs_attention=lambda reason: pytest.fail(reason),
                lease=lease,
                **_payload(),
            )
    finally:
        locks.release_run_lease(layout, lease)

    assert not publication.journal_path.exists()
    assert not publication.staging_dir.exists()
    assert all(target.read_bytes() == value for target, value in previous.items())


@pytest.mark.parametrize("cancel_boundary", ("fresh", "commit"))
@pytest.mark.parametrize("cancel_stage", ("pre-publish", "post-publish"))
def test_publish_rechecks_cancel_after_each_checker_and_report_commit(
    runtime,
    tmp_path: Path,
    cancel_boundary: str,
    cancel_stage: str,
) -> None:
    deliverables, paths, _ = runtime
    locks = _module("locks")
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    payload = _payload()
    report = _layered_report(payload)
    previous = {
        target: f"previous {target.name}\n".encode("utf-8")
        for target in publication.official_paths
    }
    for target, value in previous.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    lease = locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    observed: list[str] = []
    callback_leases: list[object | None] = []
    attentions: list[str] = []

    def request_cancel() -> None:
        locks.request_cancel(
            layout,
            reason=f"cancel during {cancel_stage} {cancel_boundary}",
            now=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
        )

    def fresh_check(stage: str) -> bytes:
        observed.append(f"fresh:{stage}")
        if cancel_boundary == "fresh" and stage == cancel_stage:
            request_cancel()
        return report

    def commit_report(
        stage: str,
        report_bytes: bytes,
        callback_lease: object | None = None,
    ) -> None:
        observed.append(f"commit:{stage}")
        callback_leases.append(callback_lease)
        assert report_bytes == report
        if cancel_boundary == "commit" and stage == cancel_stage:
            request_cancel()

    try:
        with pytest.raises(locks.CancelledRunError):
            deliverables.publish_delivery(
                layout,
                transaction_id=TRANSACTION_ID,
                fresh_check=fresh_check,
                commit_report=commit_report,
                mark_needs_attention=attentions.append,
                lease=lease,
                **payload,
            )
    finally:
        locks.release_run_lease(layout, lease)

    all_callbacks = [
        "fresh:pre-publish",
        "commit:pre-publish",
        "fresh:post-publish",
        "commit:post-publish",
    ]
    expected_last = f"{cancel_boundary}:{cancel_stage}"
    assert observed == all_callbacks[: all_callbacks.index(expected_last) + 1]
    assert all(callback_lease is lease for callback_lease in callback_leases)
    assert all(target.read_bytes() == value for target, value in previous.items())
    assert attentions == []


def test_publish_rechecks_current_owner_after_fresh_check(
    runtime,
    tmp_path: Path,
) -> None:
    deliverables, paths, jsonio = runtime
    locks = _module("locks")
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    payload = _payload()
    report = _layered_report(payload)
    previous = {
        target: f"previous {target.name}\n".encode("utf-8")
        for target in publication.official_paths
    }
    for target, value in previous.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    lease = locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    lease_path = layout.run_dir / ".writer-lease.json"
    lease_bytes = lease_path.read_bytes()
    observed: list[str] = []
    attentions: list[str] = []

    def fresh_check(stage: str) -> bytes:
        observed.append(f"fresh:{stage}")
        jsonio.atomic_write_json(
            lease_path,
            {
                "run_id": lease.run_id,
                "owner_pid": lease.owner_pid,
                "owner_nonce": "foreign-owner-nonce-000000000000",
                "acquired_at": lease.acquired_at,
                "heartbeat_at": lease.heartbeat_at,
                "expires_at": lease.expires_at,
            },
        )
        return report

    try:
        with pytest.raises(locks.LeaseOwnershipError):
            deliverables.publish_delivery(
                layout,
                transaction_id=TRANSACTION_ID,
                fresh_check=fresh_check,
                commit_report=lambda stage, report_bytes, callback_lease: None,
                mark_needs_attention=attentions.append,
                lease=lease,
                **payload,
            )
    finally:
        jsonio.atomic_write_bytes(lease_path, lease_bytes)
        locks.release_run_lease(layout, lease)

    assert observed == ["fresh:pre-publish"]
    assert all(target.read_bytes() == value for target, value in previous.items())
    assert attentions == []


def test_stale_publisher_never_rolls_back_foreign_owner_bytes(
    runtime,
    tmp_path: Path,
) -> None:
    deliverables, paths, jsonio = runtime
    locks = _module("locks")
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    payload = _payload()
    report = _layered_report(payload)
    previous = {
        target: f"previous {target.name}\n".encode("utf-8")
        for target in publication.official_paths
    }
    for target, value in previous.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    owner = locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    lease_path = layout.run_dir / ".writer-lease.json"
    owner_bytes = lease_path.read_bytes()
    foreign_article = b"foreign owner official generation\n"
    foreign_journal = b"foreign owner journal generation\n"
    attentions: list[str] = []

    def transfer_owner_and_publish_sentinels(stage: str) -> bytes:
        assert stage == "pre-publish"
        jsonio.atomic_write_json(
            lease_path,
            {
                "run_id": owner.run_id,
                "owner_pid": owner.owner_pid,
                "owner_nonce": "foreign-publisher-owner-00000000",
                "acquired_at": owner.acquired_at,
                "heartbeat_at": owner.heartbeat_at,
                "expires_at": owner.expires_at,
            },
        )
        jsonio.atomic_write_bytes(publication.article_path, foreign_article)
        jsonio.atomic_write_bytes(publication.journal_path, foreign_journal)
        return report

    try:
        with pytest.raises(locks.LeaseOwnershipError):
            deliverables.publish_delivery(
                layout,
                transaction_id=TRANSACTION_ID,
                fresh_check=transfer_owner_and_publish_sentinels,
                commit_report=lambda stage, report_bytes, callback_lease: None,
                mark_needs_attention=attentions.append,
                lease=owner,
                **payload,
            )

        assert publication.article_path.read_bytes() == foreign_article
        assert publication.journal_path.read_bytes() == foreign_journal
        assert publication.staging_dir.is_dir()
        assert attentions == []
    finally:
        jsonio.atomic_write_bytes(lease_path, owner_bytes)
        locks.release_run_lease(layout, owner)


def _durable_u12_boundary(runtime, tmp_path: Path):
    from tests.test_ultra_repair import _write_recovery_chain

    deliverables, paths, jsonio = runtime
    locks = _module("locks")
    recovery = _module("recovery")
    schemas = _module("schemas")
    status = _module("status")
    layout = _layout(paths, tmp_path)
    statuses = status.RunStatusStore(layout)
    created = statuses.create(
        datetime(2026, 8, 4, 3, 55, tzinfo=timezone.utc)
    )
    statuses.transition(
        created,
        "running",
        datetime(2026, 8, 4, 3, 56, tzinfo=timezone.utc),
        current_phase="U12",
        last_complete_phase="U11",
    )
    owner = locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 4, 4, 5, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    payload = _payload()
    report = _layered_report(payload)

    def commit_report(
        stage: str,
        report_bytes: bytes,
        callback_lease: object,
    ) -> None:
        assert callback_lease is owner
        assert stage in {"pre-publish", "post-publish"}
        jsonio.atomic_write_bytes(
            layout.validation_current_dir / "ultra-validator-report.json",
            report_bytes,
        )

    publication_result = deliverables.publish_delivery(
        layout,
        transaction_id=TRANSACTION_ID,
        fresh_check=lambda stage: report,
        commit_report=commit_report,
        mark_needs_attention=lambda reason: pytest.fail(reason),
        lease=owner,
        **payload,
    )
    ordered_paths = (
        publication_result.paths.manifest_path,
        layout.validation_current_dir / "ultra-validator-report.json",
        publication_result.paths.article_path,
        publication_result.paths.dossier_path,
        publication_result.paths.artifact_index_path,
    )
    output_hashes = tuple(
        hashlib.sha256(path.read_bytes()).hexdigest() for path in ordered_paths
    )
    events = _write_recovery_chain(
        layout,
        through_phase="U12",
        output_overrides={"U12": output_hashes},
    )
    u12_event = events[-1]
    checkpoint = {
        "schema_id": "crossframe.ultra.v82.recovery-checkpoint",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": _module("constants").current_version_binding(),
        "generated_at": "2026-08-04T04:00:13Z",
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "boundary_kind": "phase",
        "boundary_id": "U12",
        "boundary_ordinal": 0,
        "generation": 0,
        "phase_event_sha256": u12_event["event_sha256"],
        "artifact_hashes": [
            {
                "path": path.relative_to(layout.run_dir).as_posix(),
                "sha256": digest,
                "media_type": (
                    "application/json"
                    if path.suffix.casefold() == ".json"
                    else "text/markdown"
                ),
            }
            for path, digest in zip(ordered_paths, output_hashes, strict=True)
        ],
        "evidence_cutoff": "2026-08-04T04:00:00Z",
        "completed_boundary": True,
        "resumable": True,
    }
    checkpoint["content_sha256"] = schemas.compute_artifact_content_sha256(
        checkpoint
    )
    checkpoint_raw = jsonio.canonical_json_bytes(checkpoint)
    checkpoint_path = layout.recovery_dir / "checkpoints" / (
        f"{hashlib.sha256(checkpoint_raw).hexdigest()}.json"
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_bytes(checkpoint_raw)
    assert recovery.load_checkpoints(layout)[-1] == checkpoint
    return (
        deliverables,
        jsonio,
        locks,
        layout,
        owner,
        publication_result.paths,
        u12_event,
        checkpoint,
    )


def _replace_lease_with_foreign_owner(jsonio, layout, owner) -> bytes:
    lease_path = layout.run_dir / ".writer-lease.json"
    owner_bytes = lease_path.read_bytes()
    jsonio.atomic_write_json(
        lease_path,
        {
            "run_id": owner.run_id,
            "owner_pid": owner.owner_pid,
            "owner_nonce": "foreign-u12-owner-000000000000",
            "acquired_at": owner.acquired_at,
            "heartbeat_at": owner.heartbeat_at,
            "expires_at": owner.expires_at,
        },
    )
    return owner_bytes


def test_cancel_after_durable_u12_checkpoint_is_rejected_before_intent(
    runtime,
    tmp_path: Path,
) -> None:
    (
        _,
        _,
        locks,
        layout,
        owner,
        _,
        _,
        _,
    ) = _durable_u12_boundary(runtime, tmp_path)
    try:
        with pytest.raises(locks.LeaseConflictError, match="U12|durable|checkpoint"):
            locks.request_cancel(
                layout,
                reason="too late after durable U12",
                now=datetime(2026, 8, 4, 4, 6, tzinfo=timezone.utc),
            )
        assert locks.load_cancel_intent(layout) is None
    finally:
        locks.release_run_lease(layout, owner)


def test_mark_u12_durable_requires_the_same_current_owner(
    runtime,
    tmp_path: Path,
) -> None:
    (
        deliverables,
        jsonio,
        locks,
        layout,
        owner,
        publication,
        event,
        checkpoint,
    ) = _durable_u12_boundary(runtime, tmp_path)
    journal_before = publication.journal_path.read_bytes()
    owner_bytes = _replace_lease_with_foreign_owner(jsonio, layout, owner)
    try:
        with pytest.raises(locks.LeaseOwnershipError):
            deliverables._mark_u12_durable(
                layout,
                publication,
                event=event,
                checkpoint=checkpoint,
                lease=owner,
            )
        assert publication.journal_path.read_bytes() == journal_before
    finally:
        jsonio.atomic_write_bytes(layout.run_dir / ".writer-lease.json", owner_bytes)
        locks.release_run_lease(layout, owner)


def test_u12_roll_forward_owner_loss_cannot_advance_journal_or_projections(
    runtime,
    tmp_path: Path,
) -> None:
    (
        deliverables,
        jsonio,
        locks,
        layout,
        owner,
        publication,
        _,
        _,
    ) = _durable_u12_boundary(runtime, tmp_path)
    tracked = (
        publication.journal_path,
        layout.run_dir / "run-status.json",
        layout.run_dir / "final-chat.json",
    )
    before = {
        path: path.read_bytes() if path.is_file() else None for path in tracked
    }
    index_dir = layout.root / "index"
    index_before = {
        path.relative_to(index_dir): path.read_bytes()
        for path in index_dir.rglob("*")
        if path.is_file()
    } if index_dir.is_dir() else {}
    journal = jsonio.load_json_object(publication.journal_path)
    owner_bytes = _replace_lease_with_foreign_owner(jsonio, layout, owner)
    try:
        with pytest.raises(locks.LeaseOwnershipError):
            deliverables._roll_forward_u12_transaction(
                layout,
                publication,
                journal,
                lease=owner,
            )
        assert {
            path: path.read_bytes() if path.is_file() else None for path in tracked
        } == before
        index_after = {
            path.relative_to(index_dir): path.read_bytes()
            for path in index_dir.rglob("*")
            if path.is_file()
        } if index_dir.is_dir() else {}
        assert index_after == index_before
    finally:
        jsonio.atomic_write_bytes(layout.run_dir / ".writer-lease.json", owner_bytes)
        locks.release_run_lease(layout, owner)


def test_publish_cancel_during_first_official_write_rolls_back_and_stops(
    runtime,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deliverables, paths, _ = runtime
    locks = _module("locks")
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    payload = _payload()
    report = _layered_report(payload)
    new_payloads = {
        publication.manifest_path: payload["manifest_bytes"],
        publication.article_path: payload["article_bytes"],
        publication.dossier_path: payload["dossier_bytes"],
        publication.artifact_index_path: payload["artifact_index_bytes"],
    }
    previous = {
        target: f"previous {target.name}\n".encode("utf-8")
        for target in publication.official_paths
    }
    for target, value in previous.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    lease = locks.acquire_run_lease(
        layout,
        datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        timedelta(minutes=5),
    )
    original_write = deliverables.atomic_write_bytes
    new_official_writes: list[Path] = []
    attentions: list[str] = []

    def cancelling_write(path: Path, value: bytes) -> None:
        original_write(path, value)
        if path in new_payloads and value == new_payloads[path]:
            new_official_writes.append(path)
            if len(new_official_writes) == 1:
                locks.request_cancel(
                    layout,
                    reason="cancel during first official write",
                    now=datetime(2026, 8, 2, 3, 4, 6, tzinfo=timezone.utc),
                )

    monkeypatch.setattr(deliverables, "atomic_write_bytes", cancelling_write)
    try:
        with pytest.raises(locks.CancelledRunError):
            deliverables.publish_delivery(
                layout,
                transaction_id=TRANSACTION_ID,
                fresh_check=lambda stage: report,
                commit_report=lambda stage, report_bytes, callback_lease=None: None,
                mark_needs_attention=attentions.append,
                lease=lease,
                **payload,
            )
    finally:
        locks.release_run_lease(layout, lease)

    assert new_official_writes == [publication.manifest_path]
    assert all(target.read_bytes() == value for target, value in previous.items())
    assert attentions == []


@pytest.mark.parametrize(
    "mutation",
    (
        "failed-layer",
        "missing-checks",
        "stale-article",
        "stale-manifest",
        "stale-semantic",
        "stale-generation",
    ),
)
def test_publish_rejects_forged_layer_or_stale_generation_report(
    runtime,
    tmp_path: Path,
    mutation: str,
) -> None:
    deliverables, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    payload = _payload()
    report = _layered_report(
        payload,
        failed_layer="fresh-semantic" if mutation == "failed-layer" else None,
        article_sha256="a" * 64 if mutation == "stale-article" else None,
        manifest_sha256="b" * 64 if mutation == "stale-manifest" else None,
        semantic_review_artifact_sha256=(
            "c" * 64 if mutation == "stale-semantic" else None
        ),
        active_generation=1 if mutation == "stale-generation" else 0,
        include_checks=mutation != "missing-checks",
    )
    attentions: list[str] = []

    with pytest.raises(
        RuntimeError,
        match="layer|check|article|manifest|semantic|generation|publication",
    ):
        deliverables.publish_delivery(
            layout,
            transaction_id=TRANSACTION_ID,
            fresh_check=lambda stage: report,
            commit_report=lambda stage, value, lease: None,
            mark_needs_attention=attentions.append,
            **payload,
        )

    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    assert attentions
    assert not any(path.exists() for path in publication.official_paths)


def test_publish_delivery_rejects_direct_completion_before_writes(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="completion|defer|U12"):
        deliverables.publish_delivery(
            layout,
            transaction_id=TRANSACTION_ID,
            fresh_check=lambda stage: b'{"overall_status":"pass"}\n',
            commit_report=lambda stage, report, lease: None,
            mark_needs_attention=lambda reason: pytest.fail(reason),
            defer_completion=False,
            **_payload(),
        )

    assert not publication.journal_path.exists()
    assert not publication.staging_dir.exists()
    assert not any(path.exists() for path in publication.official_paths)


@pytest.mark.parametrize("operation", ("recover", "publish"))
def test_directory_at_fixed_publish_journal_path_fails_closed_before_mutation(
    runtime,
    tmp_path: Path,
    operation: str,
) -> None:
    deliverables, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    sentinels = {
        publication.journal_path / "journal-sentinel.bin": b"journal sentinel\n",
        publication.staging_dir / "staging-sentinel.bin": b"staging sentinel\n",
        publication.backup_dir / "backup-sentinel.bin": b"backup sentinel\n",
        layout.root / "index/latest.json": b"index sentinel\n",
        (
            layout.root
            / "runs/2026/08/20260802T030406Z-000000000014/keep.bin"
        ): b"sibling sentinel\n",
        layout.recovery_dir / "recovery-sentinel.bin": b"recovery sentinel\n",
        **{
            official: f"official sentinel {official.name}\n".encode("utf-8")
            for official in publication.official_paths
        },
    }
    for path, value in sentinels.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    before = {
        path.relative_to(layout.root): path.read_bytes()
        for path in layout.root.rglob("*")
        if path.is_file()
    }
    events: list[str] = []

    with pytest.raises((OSError, TypeError, ValueError, RuntimeError)):
        if operation == "recover":
            deliverables.recover_publish_transaction(
                layout,
                mark_needs_attention=events.append,
            )
        else:
            deliverables.publish_delivery(
                layout,
                transaction_id=TRANSACTION_ID,
                fresh_check=lambda stage: events.append(f"check:{stage}"),
                commit_report=lambda stage, report, lease: events.append(
                    f"commit:{stage}"
                ),
                mark_needs_attention=events.append,
                **_payload(),
            )

    after = {
        path.relative_to(layout.root): path.read_bytes()
        for path in layout.root.rglob("*")
        if path.is_file()
    }
    assert events == []
    assert publication.journal_path.is_dir()
    assert after == before


def test_failed_replacement_restores_exact_prior_complete_bytes_and_keeps_audit(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    previous = {
        publication.article_path: b"old article\n",
        publication.dossier_path: b"old dossier\n",
        publication.artifact_index_path: b"old index\n",
        publication.manifest_path: b'{"manifest":"old"}\n',
    }
    for target, value in previous.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    attentions: list[str] = []

    def fresh_check(stage: str) -> bytes:
        if stage == "post-publish":
            raise RuntimeError("injected post-publish validator failure")
        return _layered_report(_payload())

    with pytest.raises(RuntimeError, match="post-publish"):
        deliverables.publish_delivery(
            layout,
            transaction_id=TRANSACTION_ID,
            fresh_check=fresh_check,
            commit_report=lambda stage, report, lease: None,
            mark_needs_attention=attentions.append,
            **_payload(),
        )

    assert attentions and "post-publish" in attentions[-1]
    assert all(target.read_bytes() == value for target, value in previous.items())
    assert publication.journal_path.is_file()
    assert publication.backup_dir.is_dir()
    assert not publication.staging_dir.exists()
    assert all(
        (publication.backup_dir / target.name).read_bytes() == value
        for target, value in previous.items()
    )
    journal = jsonio.load_json_object(publication.journal_path)
    assert journal["state"] == "rolled-back"
    assert journal["postcheck_passed"] is False


def test_failed_first_publication_leaves_all_official_names_absent(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)

    with pytest.raises(RuntimeError, match="pre-publish"):
        deliverables.publish_delivery(
            layout,
            transaction_id=TRANSACTION_ID,
            fresh_check=lambda stage: (_ for _ in ()).throw(
                RuntimeError("injected pre-publish failure")
            ),
            commit_report=lambda stage, report, lease: None,
            mark_needs_attention=lambda reason: None,
            **_payload(),
        )

    assert not publication.article_path.exists()
    assert not publication.dossier_path.exists()
    assert not publication.artifact_index_path.exists()
    assert not publication.manifest_path.exists()
    assert publication.journal_path.is_file()
    assert not publication.staging_dir.exists()


def test_recovery_before_backup_preserves_verified_previous_official_bytes(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    payloads = {
        publication.manifest_path: _payload()["manifest_bytes"],
        publication.article_path: _payload()["article_bytes"],
        publication.dossier_path: _payload()["dossier_bytes"],
        publication.artifact_index_path: _payload()["artifact_index_bytes"],
    }
    previous = {
        official: f"previous {official.name}\n".encode("utf-8")
        for official in payloads
    }
    for official, prior in previous.items():
        official.parent.mkdir(parents=True, exist_ok=True)
        official.write_bytes(prior)
        staged = deliverables._staged_path(publication, official)
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(payloads[official])
    jsonio.atomic_write_json(
        publication.journal_path,
        deliverables._journal_object(
            layout,
            publication,
            transaction_id=TRANSACTION_ID,
            state="staged",
            payloads=payloads,
            previous=previous,
            precheck_passed=None,
            postcheck_passed=None,
            failure=None,
        ),
    )
    attentions: list[str] = []

    recovered = deliverables.recover_publish_transaction(
        layout,
        mark_needs_attention=attentions.append,
    )

    assert recovered is not None and recovered["state"] == "rolled-back"
    assert attentions == ["recovered incomplete publication journal"]
    assert all(official.read_bytes() == prior for official, prior in previous.items())
    assert not publication.staging_dir.exists()
    assert not publication.backup_dir.exists()


def _recoverable_backed_up_journal(deliverables, jsonio, layout, publication):
    payloads = {
        publication.manifest_path: _payload()["manifest_bytes"],
        publication.article_path: _payload()["article_bytes"],
        publication.dossier_path: _payload()["dossier_bytes"],
        publication.artifact_index_path: _payload()["artifact_index_bytes"],
    }
    previous = {
        official: f"previous {official.name}\n".encode("utf-8")
        for official in payloads
    }
    for official, prior in previous.items():
        official.parent.mkdir(parents=True, exist_ok=True)
        official.write_bytes(prior)
        staged = deliverables._staged_path(publication, official)
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(payloads[official])
        backup = deliverables._backup_path(publication, official)
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(prior)
    journal = deliverables._journal_object(
        layout,
        publication,
        transaction_id=TRANSACTION_ID,
        state="backed-up",
        payloads=payloads,
        previous=previous,
        precheck_passed=True,
        postcheck_passed=None,
        failure=None,
    )
    journal.setdefault("u12_event_sha256", None)
    journal.setdefault("u12_checkpoint_content_sha256", None)
    for entry in journal["files"]:
        official = layout.run_dir / entry["official_path"]
        entry.setdefault(
            "backup_path",
            deliverables._backup_path(publication, official)
            .relative_to(layout.root)
            .as_posix(),
        )
    return journal


def test_recovery_adapts_closed_legacy_journal_after_full_preflight(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    journal = _recoverable_backed_up_journal(
        deliverables, jsonio, layout, publication
    )
    journal.pop("u12_event_sha256")
    journal.pop("u12_checkpoint_content_sha256")
    for entry in journal["files"]:
        entry.pop("backup_path")
    payloads = {
        publication.manifest_path: _payload()["manifest_bytes"],
        publication.article_path: _payload()["article_bytes"],
        publication.dossier_path: _payload()["dossier_bytes"],
        publication.artifact_index_path: _payload()["artifact_index_bytes"],
    }
    for official, payload in payloads.items():
        official.write_bytes(payload)
    index_sentinel = layout.root / "index/latest.json"
    sibling_sentinel = (
        layout.root
        / "runs/2026/08/20260802T030406Z-000000000014/keep.bin"
    )
    index_sentinel.parent.mkdir(parents=True, exist_ok=True)
    sibling_sentinel.parent.mkdir(parents=True, exist_ok=True)
    index_sentinel.write_bytes(b"index sentinel\n")
    sibling_sentinel.write_bytes(b"sibling sentinel\n")
    jsonio.atomic_write_json(publication.journal_path, journal)
    attentions: list[str] = []

    recovered = deliverables.recover_publish_transaction(
        layout,
        mark_needs_attention=attentions.append,
    )

    assert recovered is not None and recovered["state"] == "rolled-back"
    assert attentions == ["recovered incomplete publication journal"]
    for official in publication.official_paths:
        assert official.read_bytes() == f"previous {official.name}\n".encode("utf-8")
    assert index_sentinel.read_bytes() == b"index sentinel\n"
    assert sibling_sentinel.read_bytes() == b"sibling sentinel\n"


@pytest.mark.parametrize(
    "mutation",
    (
        "absolute-index",
        "absolute-sibling",
        "backslash",
        "dotdot",
        "duplicate",
        "missing",
        "extra",
        "wrong-run-id",
        "unknown-state",
        "wrong-staged",
        "wrong-backup",
        "missing-backup-field",
        "wrong-new-hash",
        "non-boolean-previous",
        "false-precheck",
        "open-journal",
        "open-entry",
    ),
)
def test_recovery_rejects_malformed_journal_before_mutating_any_sentinel(
    runtime,
    tmp_path: Path,
    mutation: str,
) -> None:
    deliverables, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    journal = _recoverable_backed_up_journal(
        deliverables, jsonio, layout, publication
    )

    index_sentinel = layout.root / "index/latest.json"
    sibling_sentinel = (
        layout.root
        / "runs/2026/08/20260802T030406Z-000000000014/keep.bin"
    )
    run_sentinel = layout.recovery_dir / "recovery-sentinel.bin"
    sentinels = {
        index_sentinel: b"index sentinel\n",
        sibling_sentinel: b"sibling sentinel\n",
        run_sentinel: b"run sentinel\n",
    }
    for path, value in sentinels.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)

    files = journal["files"]
    if mutation in {"absolute-index", "absolute-sibling"}:
        target = index_sentinel if mutation == "absolute-index" else sibling_sentinel
        files[0]["official_path"] = str(target)
        files[0]["previous_existed"] = False
        files[0]["previous_sha256"] = None
    elif mutation == "backslash":
        files[0]["official_path"] = files[0]["official_path"].replace("/", "\\")
    elif mutation == "dotdot":
        files[0]["official_path"] = "delivery/../recovery/recovery-sentinel.bin"
        files[0]["previous_existed"] = False
        files[0]["previous_sha256"] = None
    elif mutation == "duplicate":
        files[1] = copy.deepcopy(files[0])
    elif mutation == "missing":
        files.pop()
    elif mutation == "extra":
        extra = copy.deepcopy(files[0])
        extra["official_path"] = "recovery/recovery-sentinel.bin"
        extra["previous_existed"] = False
        extra["previous_sha256"] = None
        files.append(extra)
    elif mutation == "wrong-run-id":
        journal["run_id"] = "20260802T030406Z-000000000014"
    elif mutation == "unknown-state":
        journal["state"] = "almost-complete"
    elif mutation == "wrong-staged":
        files[0]["staged_path"] = str(index_sentinel)
    elif mutation == "wrong-backup":
        files[0]["backup_path"] = str(sibling_sentinel)
    elif mutation == "missing-backup-field":
        files[0].pop("backup_path")
    elif mutation == "wrong-new-hash":
        files[0]["new_sha256"] = "f" * 64
    elif mutation == "non-boolean-previous":
        files[0]["previous_existed"] = "yes"
    elif mutation == "false-precheck":
        journal["precheck_passed"] = False
        journal["postcheck_passed"] = False
        journal["failure"] = "rolled back after injected failure"
        journal["state"] = "rolled-back"
    elif mutation == "open-journal":
        journal["unexpected"] = "not closed"
    elif mutation == "open-entry":
        files[0]["unexpected"] = "not closed"
    else:  # pragma: no cover - the parameter list is the closed mutation set
        raise AssertionError(mutation)

    jsonio.atomic_write_json(publication.journal_path, journal)
    tracked_paths = (
        *sentinels,
        *publication.official_paths,
        *(deliverables._staged_path(publication, path) for path in publication.official_paths),
        *(deliverables._backup_path(publication, path) for path in publication.official_paths),
        publication.journal_path,
    )
    before = {path: path.read_bytes() for path in tracked_paths}
    attentions: list[str] = []

    with pytest.raises((TypeError, ValueError, RuntimeError), match="journal|path|state|hash|closed|canonical|boolean"):
        deliverables.recover_publish_transaction(
            layout,
            mark_needs_attention=attentions.append,
        )

    assert attentions == []
    assert {path: path.read_bytes() for path in tracked_paths} == before


def test_recovery_rejects_staged_reparse_ancestor_before_any_mutation(
    runtime,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deliverables, paths, jsonio = runtime
    layout = _layout(paths, tmp_path)
    publication = deliverables.publication_paths(layout, TRANSACTION_ID)
    journal = _recoverable_backed_up_journal(
        deliverables, jsonio, layout, publication
    )
    jsonio.atomic_write_json(publication.journal_path, journal)
    staged_delivery_dir = publication.staging_dir / "delivery"
    real_is_reparse_point = paths._is_reparse_point

    def simulated_reparse(path: Path) -> bool:
        return Path(path) == staged_delivery_dir or real_is_reparse_point(Path(path))

    tracked_paths = (
        *publication.official_paths,
        *(deliverables._staged_path(publication, path) for path in publication.official_paths),
        *(deliverables._backup_path(publication, path) for path in publication.official_paths),
        publication.journal_path,
    )
    before = {path: path.read_bytes() for path in tracked_paths}
    monkeypatch.setattr(paths, "_is_reparse_point", simulated_reparse)

    with pytest.raises((TypeError, ValueError, RuntimeError), match="reparse|symlink|junction"):
        deliverables.recover_publish_transaction(
            layout,
            mark_needs_attention=lambda reason: pytest.fail(reason),
        )

    assert {path: path.read_bytes() for path in tracked_paths} == before


def test_final_chat_projection_is_locked_complete_absolute_and_not_a_phase_artifact(
    runtime, tmp_path: Path
) -> None:
    deliverables, paths, _ = runtime
    layout = _layout(paths, tmp_path)
    layout.delivery_dir.mkdir(parents=True, exist_ok=True)
    article_path = layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
    article_path.write_text("complete\n", encoding="utf-8")
    verdict = {
        "judgment_kind": "best-current",
        "main_verdict": {
            "proposition": "当前最可能是组织激励与照护约束共同导致延期，而非单纯执行力不足。",
            "reversal_conditions": [
                "独立记录显示资源与约束均充足，且延期只随个人可控执行偏差变化。"
            ],
        },
    }
    status = SimpleNamespace(status="complete", current_phase="U12")

    projection = deliverables.build_final_chat_projection(layout, verdict, status)

    assert projection == {
        "run_status": "complete",
        "center_judgment_summary": verdict["main_verdict"]["proposition"],
        "key_reversal_conditions": verdict["main_verdict"]["reversal_conditions"],
        "article_path": str(article_path.resolve()),
        "run_path": str(layout.run_dir.resolve()),
        "continuation_entry": None,
    }
    assert set(projection).isdisjoint(
        {"schema_id", "schema_version", "phase_id", "content_sha256"}
    )
    assert not (layout.artifacts_dir / "final-chat.json").exists()

    verdict["main_verdict"]["proposition"] = "mutated after projection"
    assert projection["center_judgment_summary"] != "mutated after projection"

    with pytest.raises((TypeError, ValueError), match="complete|U12"):
        deliverables.build_final_chat_projection(
            layout,
            verdict,
            SimpleNamespace(status="running", current_phase="U11"),
        )
