from __future__ import annotations

from collections.abc import Callable, Mapping
import copy
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
from typing import Any

from .jsonio import (
    atomic_write_bytes,
    atomic_write_json,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from .paths import RunLayout, assert_safe_descendant


ARTICLE_FILENAME = "CrossFrame-Ultra-完整文章.md"
DOSSIER_FILENAME = "完整推演档案.md"
ARTIFACT_INDEX_FILENAME = "工件索引.md"
MANIFEST_FILENAME = "ultra-artifact-manifest.json"
JOURNAL_FILENAME = "publish-transaction.json"

_TRANSACTION_ID_RE = re.compile(r"\A\d{8}T\d{6}Z-[0-9a-f]{12}\Z")


@dataclass(frozen=True, slots=True)
class PublicationPaths:
    staging_dir: Path
    journal_path: Path
    backup_dir: Path
    manifest_path: Path
    article_path: Path
    dossier_path: Path
    artifact_index_path: Path

    @property
    def official_paths(self) -> tuple[Path, ...]:
        return (
            self.manifest_path,
            self.article_path,
            self.dossier_path,
            self.artifact_index_path,
        )


@dataclass(frozen=True, slots=True)
class PublicationResult:
    paths: PublicationPaths
    precheck_report_bytes: bytes
    postcheck_report_bytes: bytes
    postcheck_passed: bool


def _validate_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    assert_safe_descendant(layout.root, layout.run_dir)
    expected = {
        "root_staging_dir": layout.root / ".staging",
        "artifacts_dir": layout.run_dir / "artifacts",
        "delivery_dir": layout.run_dir / "delivery",
        "recovery_dir": layout.run_dir / "recovery",
    }
    for field, value in expected.items():
        actual = getattr(layout, field)
        if actual != value:
            raise ValueError(f"layout field {field} differs from the fixed run layout")
        assert_safe_descendant(layout.root, actual)


def publication_paths(layout: RunLayout, transaction_id: str) -> PublicationPaths:
    _validate_layout(layout)
    if not isinstance(transaction_id, str) or _TRANSACTION_ID_RE.fullmatch(transaction_id) is None:
        raise ValueError("transaction_id must be a safe UTC id with twelve lowercase hex digits")
    paths = PublicationPaths(
        staging_dir=(
            layout.root_staging_dir
            / layout.run_dir.name
            / f"publish-{transaction_id}"
        ),
        journal_path=layout.recovery_dir / JOURNAL_FILENAME,
        backup_dir=(
            layout.recovery_dir / "publish-backups" / transaction_id
        ),
        manifest_path=layout.artifacts_dir / MANIFEST_FILENAME,
        article_path=layout.delivery_dir / ARTICLE_FILENAME,
        dossier_path=layout.delivery_dir / DOSSIER_FILENAME,
        artifact_index_path=layout.delivery_dir / ARTIFACT_INDEX_FILENAME,
    )
    for path in (
        paths.staging_dir,
        paths.journal_path,
        paths.backup_dir,
        *paths.official_paths,
    ):
        assert_safe_descendant(layout.root, path)
    return paths


def _payload_by_target(
    paths: PublicationPaths,
    *,
    article_bytes: bytes,
    dossier_bytes: bytes,
    artifact_index_bytes: bytes,
    manifest_bytes: bytes,
) -> dict[Path, bytes]:
    values = {
        paths.manifest_path: manifest_bytes,
        paths.article_path: article_bytes,
        paths.dossier_path: dossier_bytes,
        paths.artifact_index_path: artifact_index_bytes,
    }
    for target, value in values.items():
        if not isinstance(value, bytes):
            raise TypeError(f"publication payload for {target.name} must be bytes")
        if not value:
            raise ValueError(f"publication payload for {target.name} cannot be empty")
    return values


def _staged_path(paths: PublicationPaths, official: Path) -> Path:
    if official == paths.manifest_path:
        return paths.staging_dir / "artifacts" / official.name
    return paths.staging_dir / "delivery" / official.name


def _backup_path(paths: PublicationPaths, official: Path) -> Path:
    return paths.backup_dir / official.name


def _journal_object(
    layout: RunLayout,
    paths: PublicationPaths,
    *,
    transaction_id: str,
    state: str,
    payloads: Mapping[Path, bytes],
    previous: Mapping[Path, bytes | None],
    precheck_passed: bool | None,
    postcheck_passed: bool | None,
    failure: str | None,
) -> dict[str, object]:
    files = []
    for official, payload in payloads.items():
        prior = previous[official]
        files.append(
            {
                "official_path": official.relative_to(layout.run_dir).as_posix(),
                "staged_path": _staged_path(paths, official).relative_to(
                    layout.root
                ).as_posix(),
                "new_sha256": sha256_bytes(payload),
                "previous_existed": prior is not None,
                "previous_sha256": None if prior is None else sha256_bytes(prior),
            }
        )
    return {
        "failure": failure,
        "files": files,
        "postcheck_passed": postcheck_passed,
        "precheck_passed": precheck_passed,
        "run_id": layout.run_dir.name,
        "state": state,
        "transaction_id": transaction_id,
    }


def _write_journal(
    layout: RunLayout,
    paths: PublicationPaths,
    **values: object,
) -> None:
    atomic_write_json(paths.journal_path, _journal_object(layout, paths, **values))


def _remove_staging(layout: RunLayout, paths: PublicationPaths) -> None:
    if not paths.staging_dir.exists():
        return
    assert_safe_descendant(layout.root, paths.staging_dir)
    expected_parent = layout.root_staging_dir / layout.run_dir.name
    if paths.staging_dir.parent != expected_parent or not paths.staging_dir.name.startswith(
        "publish-"
    ):
        raise ValueError("refusing to remove a non-transaction staging directory")
    shutil.rmtree(paths.staging_dir)
    try:
        expected_parent.rmdir()
    except OSError:
        pass


def _validate_report_bytes(report_bytes: bytes, stage: str) -> bytes:
    if not isinstance(report_bytes, bytes):
        raise TypeError(f"{stage} fresh checker must return bytes")
    report = load_json_object_bytes(report_bytes, source=f"{stage} fresh checker stdout")
    if report.get("overall_status") != "pass":
        raise RuntimeError(
            f"{stage} fresh checker did not report overall_status=pass"
        )
    return report_bytes


def _attach_note(error: BaseException, note: str) -> None:
    add_note = getattr(error, "add_note", None)
    if callable(add_note):
        add_note(note)


def _restore_previous(
    layout: RunLayout,
    paths: PublicationPaths,
    previous: Mapping[Path, bytes | None],
) -> None:
    for official, prior in previous.items():
        assert_safe_descendant(layout.root, official)
        if prior is None:
            official.unlink(missing_ok=True)
        else:
            backup = _backup_path(paths, official)
            if backup.is_file():
                restored = backup.read_bytes()
                if sha256_bytes(restored) != sha256_bytes(prior):
                    raise RuntimeError(f"publish backup hash mismatch for {official.name}")
                atomic_write_bytes(official, restored)
            else:
                atomic_write_bytes(official, prior)


def publish_delivery(
    layout: RunLayout,
    *,
    transaction_id: str,
    article_bytes: bytes,
    dossier_bytes: bytes,
    artifact_index_bytes: bytes,
    manifest_bytes: bytes,
    fresh_check: Callable[[str], bytes],
    commit_report: Callable[[str, bytes], object],
    mark_needs_attention: Callable[[str], object],
) -> PublicationResult:
    """Publish the fixed final set with durable rollback evidence.

    The caller owns the run lease. ``fresh_check`` is the read-only child boundary;
    ``commit_report`` is the lease-owning parent write boundary.
    """

    _validate_layout(layout)
    if not callable(fresh_check) or not callable(commit_report):
        raise TypeError("fresh_check and commit_report must be callable")
    if not callable(mark_needs_attention):
        raise TypeError("mark_needs_attention must be callable")
    paths = publication_paths(layout, transaction_id)
    payloads = _payload_by_target(
        paths,
        article_bytes=article_bytes,
        dossier_bytes=dossier_bytes,
        artifact_index_bytes=artifact_index_bytes,
        manifest_bytes=manifest_bytes,
    )
    previous = {
        official: official.read_bytes() if official.is_file() else None
        for official in payloads
    }
    precheck_passed: bool | None = None
    postcheck_passed: bool | None = None
    precheck_report = b""
    postcheck_report = b""

    _remove_staging(layout, paths)
    _write_journal(
        layout,
        paths,
        transaction_id=transaction_id,
        state="journaled",
        payloads=payloads,
        previous=previous,
        precheck_passed=precheck_passed,
        postcheck_passed=postcheck_passed,
        failure=None,
    )
    try:
        for official, payload in payloads.items():
            staged = _staged_path(paths, official)
            assert_safe_descendant(layout.root, staged)
            atomic_write_bytes(staged, payload)
        _write_journal(
            layout,
            paths,
            transaction_id=transaction_id,
            state="staged",
            payloads=payloads,
            previous=previous,
            precheck_passed=precheck_passed,
            postcheck_passed=postcheck_passed,
            failure=None,
        )

        precheck_report = _validate_report_bytes(
            fresh_check("pre-publish"), "pre-publish"
        )
        precheck_passed = True
        commit_report("pre-publish", precheck_report)
        _write_journal(
            layout,
            paths,
            transaction_id=transaction_id,
            state="prechecked",
            payloads=payloads,
            previous=previous,
            precheck_passed=precheck_passed,
            postcheck_passed=postcheck_passed,
            failure=None,
        )

        paths.backup_dir.mkdir(parents=True, exist_ok=True)
        for official, prior in previous.items():
            if prior is not None:
                atomic_write_bytes(_backup_path(paths, official), prior)
        _write_journal(
            layout,
            paths,
            transaction_id=transaction_id,
            state="backed-up",
            payloads=payloads,
            previous=previous,
            precheck_passed=precheck_passed,
            postcheck_passed=postcheck_passed,
            failure=None,
        )

        for official in payloads:
            staged = _staged_path(paths, official)
            if sha256_bytes(staged.read_bytes()) != sha256_bytes(payloads[official]):
                raise RuntimeError(f"staged publication hash mismatch for {official.name}")
            atomic_write_bytes(official, staged.read_bytes())
        _write_journal(
            layout,
            paths,
            transaction_id=transaction_id,
            state="published",
            payloads=payloads,
            previous=previous,
            precheck_passed=precheck_passed,
            postcheck_passed=postcheck_passed,
            failure=None,
        )

        postcheck_report = _validate_report_bytes(
            fresh_check("post-publish"), "post-publish"
        )
        postcheck_passed = True
        commit_report("post-publish", postcheck_report)
        _write_journal(
            layout,
            paths,
            transaction_id=transaction_id,
            state="complete",
            payloads=payloads,
            previous=previous,
            precheck_passed=precheck_passed,
            postcheck_passed=postcheck_passed,
            failure=None,
        )
        _remove_staging(layout, paths)
        return PublicationResult(
            paths=paths,
            precheck_report_bytes=precheck_report,
            postcheck_report_bytes=postcheck_report,
            postcheck_passed=True,
        )
    except BaseException as error:
        rollback_error: BaseException | None = None
        try:
            _restore_previous(layout, paths, previous)
        except BaseException as caught:
            rollback_error = caught
        failure = f"{type(error).__name__}: {error}"
        if rollback_error is not None:
            failure += f"; rollback failed: {type(rollback_error).__name__}: {rollback_error}"
        postcheck_passed = False
        try:
            _write_journal(
                layout,
                paths,
                transaction_id=transaction_id,
                state="rolled-back" if rollback_error is None else "rollback-failed",
                payloads=payloads,
                previous=previous,
                precheck_passed=precheck_passed,
                postcheck_passed=postcheck_passed,
                failure=failure,
            )
        except BaseException as journal_error:
            _attach_note(error, f"failed to update publish journal: {journal_error}")
        try:
            mark_needs_attention(failure)
        except BaseException as attention_error:
            _attach_note(
                error,
                f"failed to mark run needs_attention: {attention_error}",
            )
        try:
            _remove_staging(layout, paths)
        except BaseException as staging_error:
            _attach_note(
                error,
                f"failed to remove transient staging: {staging_error}",
            )
        if rollback_error is not None:
            _attach_note(error, f"publish rollback failed: {rollback_error}")
        raise


def recover_publish_transaction(
    layout: RunLayout,
    *,
    mark_needs_attention: Callable[[str], object],
) -> dict[str, object] | None:
    """Recover an incomplete fixed journal without accepting caller-selected paths."""

    _validate_layout(layout)
    journal_path = layout.recovery_dir / JOURNAL_FILENAME
    if not journal_path.is_file():
        return None
    journal = load_json_object(journal_path)
    transaction_id = journal.get("transaction_id")
    if not isinstance(transaction_id, str):
        raise ValueError("publish journal has no valid transaction_id")
    paths = publication_paths(layout, transaction_id)
    state = journal.get("state")
    if state in {"complete", "rolled-back"}:
        _remove_staging(layout, paths)
        return journal
    files = journal.get("files")
    if not isinstance(files, list):
        raise ValueError("publish journal files must be an array")
    before_backup = state in {"journaled", "staged", "prechecked"}
    for entry in files:
        if not isinstance(entry, Mapping):
            raise ValueError("publish journal file entry must be an object")
        relative = entry.get("official_path")
        if not isinstance(relative, str):
            raise ValueError("publish journal official_path must be a string")
        official = layout.run_dir / relative
        assert_safe_descendant(layout.root, official)
        previous_existed = entry.get("previous_existed") is True
        backup = _backup_path(paths, official)
        previous_sha256 = entry.get("previous_sha256")
        if before_backup:
            if previous_existed:
                if (
                    not official.is_file()
                    or not isinstance(previous_sha256, str)
                    or sha256_bytes(official.read_bytes()) != previous_sha256
                ):
                    raise RuntimeError(
                        f"pre-backup official bytes changed for {official.name}"
                    )
            elif official.exists():
                raise RuntimeError(
                    f"pre-backup publication unexpectedly created {official.name}"
                )
            continue
        if previous_existed:
            if not backup.is_file():
                raise RuntimeError(f"missing durable publish backup for {official.name}")
            data = backup.read_bytes()
            if not isinstance(previous_sha256, str) or sha256_bytes(data) != previous_sha256:
                raise RuntimeError(f"publish backup hash mismatch for {official.name}")
            atomic_write_bytes(official, data)
        else:
            official.unlink(missing_ok=True)
    recovered = dict(journal)
    recovered["state"] = "rolled-back"
    recovered["postcheck_passed"] = False
    recovered["failure"] = "recovered incomplete publication journal"
    atomic_write_json(paths.journal_path, recovered)
    _remove_staging(layout, paths)
    mark_needs_attention("recovered incomplete publication journal")
    return recovered


def _status_value(status_record: object, field: str) -> object:
    if isinstance(status_record, Mapping):
        return status_record.get(field)
    return getattr(status_record, field, None)


def build_final_chat_projection(
    layout: RunLayout,
    verdict: Mapping[str, Any],
    status_record: object,
    *,
    continuation_entry: str | None = None,
) -> dict[str, object]:
    _validate_layout(layout)
    if _status_value(status_record, "status") != "complete" or _status_value(
        status_record, "current_phase"
    ) != "U12":
        raise ValueError("final-chat projection requires a complete U12 run")
    if not isinstance(verdict, Mapping) or verdict.get("judgment_kind") != "best-current":
        raise ValueError("final-chat projection requires the locked best-current verdict")
    main = verdict.get("main_verdict")
    if not isinstance(main, Mapping):
        raise ValueError("locked verdict has no main_verdict")
    proposition = main.get("proposition")
    reversal = main.get("reversal_conditions")
    if not isinstance(proposition, str) or not proposition.strip():
        raise ValueError("locked verdict proposition must be nonempty")
    if not isinstance(reversal, list) or not reversal or not all(
        isinstance(item, str) and item.strip() for item in reversal
    ):
        raise ValueError("locked verdict reversal_conditions must be nonempty strings")
    if continuation_entry is not None and (
        not isinstance(continuation_entry, str) or not continuation_entry.strip()
    ):
        raise ValueError("continuation_entry must be null or a nonempty string")
    article_path = layout.delivery_dir / ARTICLE_FILENAME
    if not article_path.is_file():
        raise ValueError("complete final-chat projection requires the official article")
    return {
        "run_status": "complete",
        "center_judgment_summary": proposition,
        "key_reversal_conditions": copy.deepcopy(reversal),
        "article_path": str(article_path.resolve()),
        "run_path": str(layout.run_dir.resolve()),
        "continuation_entry": continuation_entry,
    }


def write_final_chat_projection(
    layout: RunLayout,
    verdict: Mapping[str, Any],
    status_record: object,
    *,
    continuation_entry: str | None = None,
) -> Path:
    projection = build_final_chat_projection(
        layout,
        verdict,
        status_record,
        continuation_entry=continuation_entry,
    )
    path = layout.run_dir / "final-chat.json"
    assert_safe_descendant(layout.root, path)
    atomic_write_json(path, projection)
    return path


__all__ = (
    "ARTICLE_FILENAME",
    "ARTIFACT_INDEX_FILENAME",
    "DOSSIER_FILENAME",
    "JOURNAL_FILENAME",
    "MANIFEST_FILENAME",
    "PublicationPaths",
    "PublicationResult",
    "build_final_chat_projection",
    "publication_paths",
    "publish_delivery",
    "recover_publish_transaction",
    "write_final_chat_projection",
)
