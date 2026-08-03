from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
DELIVERABLES_PATH = RUNTIME_DIR / "deliverables.py"
RUN_ID = "20260802T030405Z-000000000013"
TRANSACTION_ID = "20260802T030410Z-aaaaaaaaaaaa"


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
    return paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)


def _payload() -> dict[str, bytes]:
    return {
        "article_bytes": "# CrossFrame Ultra 完整文章\n\n正文。\n".encode("utf-8"),
        "dossier_bytes": "# 完整推演档案\n\n推演。\n".encode("utf-8"),
        "artifact_index_bytes": "# 工件索引\n\n索引。\n".encode("utf-8"),
        "manifest_bytes": b'{"manifest":"new"}\n',
    }


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
        return (f'{{"overall_status":"pass","stage":"{stage}"}}\n').encode("utf-8")

    def commit_report(stage: str, report_bytes: bytes) -> None:
        observed.append(f"commit:{stage}")
        assert report_bytes == (
            f'{{"overall_status":"pass","stage":"{stage}"}}\n'
        ).encode("utf-8")

    result = deliverables.publish_delivery(
        layout,
        transaction_id=TRANSACTION_ID,
        fresh_check=fresh_check,
        commit_report=commit_report,
        mark_needs_attention=lambda reason: pytest.fail(reason),
        **_payload(),
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
    assert not publication.staging_dir.exists()
    journal = jsonio.load_json_object(publication.journal_path)
    assert journal["transaction_id"] == TRANSACTION_ID
    assert journal["state"] == "complete"
    assert journal["postcheck_passed"] is True


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
        return b'{"overall_status":"pass"}\n'

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
