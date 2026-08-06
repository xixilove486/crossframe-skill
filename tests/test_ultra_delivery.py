from __future__ import annotations

import copy
from datetime import datetime, timezone
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

    def commit_report(stage: str, report_bytes: bytes) -> None:
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
            commit_report=lambda stage, value: None,
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
            commit_report=lambda stage, report: None,
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
                commit_report=lambda stage, report: events.append(
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
            commit_report=lambda stage, report: None,
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
            commit_report=lambda stage, report: None,
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
