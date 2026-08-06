from __future__ import annotations

from collections.abc import Callable, Mapping
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import shutil
from typing import Any

from .jsonio import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from .locks import (
    CancelledRunError,
    Lease,
    LeaseOwnershipError,
    load_cancel_intent,
    require_run_lease_owner,
)
from .paths import RunLayout, assert_safe_descendant


ARTICLE_FILENAME = "CrossFrame-Ultra-完整文章.md"
DOSSIER_FILENAME = "完整推演档案.md"
ARTIFACT_INDEX_FILENAME = "工件索引.md"
MANIFEST_FILENAME = "ultra-artifact-manifest.json"
JOURNAL_FILENAME = "publish-transaction.json"

_TRANSACTION_ID_RE = re.compile(r"\A\d{8}T\d{6}Z-[0-9a-f]{12}\Z")
_SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_JOURNAL_STATES = frozenset(
    {
        "journaled",
        "staged",
        "prechecked",
        "backed-up",
        "published",
        "postchecked",
        "u12-durable",
        "complete",
        "rolled-back",
        "rollback-failed",
    }
)
_JOURNAL_FIELDS = frozenset(
    {
        "failure",
        "files",
        "postcheck_passed",
        "precheck_passed",
        "run_id",
        "state",
        "transaction_id",
        "u12_event_sha256",
        "u12_checkpoint_content_sha256",
    }
)
_LEGACY_JOURNAL_FIELDS = _JOURNAL_FIELDS - frozenset(
    {"u12_event_sha256", "u12_checkpoint_content_sha256"}
)
_JOURNAL_FILE_FIELDS = frozenset(
    {
        "backup_path",
        "new_sha256",
        "official_path",
        "previous_existed",
        "previous_sha256",
        "staged_path",
    }
)
_LEGACY_JOURNAL_FILE_FIELDS = _JOURNAL_FILE_FIELDS - frozenset({"backup_path"})
_PRE_BACKUP_STATES = frozenset({"journaled", "staged", "prechecked"})
_STAGED_REQUIRED_STATES = frozenset(
    {"staged", "prechecked", "backed-up", "published", "postchecked", "u12-durable"}
)
_BACKUP_REQUIRED_STATES = frozenset(
    {"backed-up", "published", "postchecked", "u12-durable", "complete"}
)
_PUBLISHED_STATES = frozenset(
    {"published", "postchecked", "u12-durable", "complete"}
)
_VALIDATION_LAYER_IDS = (
    "deterministic",
    "adversarial",
    "fresh-semantic",
)


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


@dataclass(frozen=True, slots=True)
class _JournalFileAuthority:
    official_path: Path
    staged_path: Path
    backup_path: Path
    new_sha256: str
    previous_existed: bool
    previous_sha256: str | None


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
                "backup_path": _backup_path(paths, official).relative_to(
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
        "u12_event_sha256": None,
        "u12_checkpoint_content_sha256": None,
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


def _validate_report_bytes(
    report_bytes: bytes,
    stage: str,
    *,
    expected_article_sha256: str,
    expected_manifest_sha256: str,
    expected_semantic_review_artifact_sha256: str,
    expected_active_generation: int,
) -> bytes:
    if not isinstance(report_bytes, bytes):
        raise TypeError(f"{stage} fresh checker must return bytes")
    report = load_json_object_bytes(report_bytes, source=f"{stage} fresh checker stdout")
    if report.get("overall_status") != "pass":
        failures = [
            {
                "validator_id": check.get("validator_id"),
                "error_codes": check.get("error_codes"),
                "artifact_refs": check.get("artifact_refs"),
            }
            for check in report.get("checks", [])
            if isinstance(check, Mapping) and check.get("status") != "pass"
        ]
        raise RuntimeError(
            f"{stage} fresh checker did not report overall_status=pass: {failures}"
        )
    layers = report.get("layers")
    if not isinstance(layers, list) or tuple(
        layer.get("layer_id") if isinstance(layer, Mapping) else None
        for layer in layers
    ) != _VALIDATION_LAYER_IDS:
        raise RuntimeError(f"{stage} fresh checker validation layer contract is invalid")
    failed_layers = [
        str(layer.get("layer_id"))
        for layer in layers
        if not isinstance(layer, Mapping) or layer.get("status") != "pass"
    ]
    if failed_layers:
        raise RuntimeError(
            f"{stage} fresh checker has failed validation layer: {failed_layers}"
        )
    checks = report.get("checks", [])
    if not isinstance(checks, list) or not checks or any(
        not isinstance(check, Mapping) or check.get("status") != "pass"
        for check in checks
    ):
        raise RuntimeError(f"{stage} fresh checker contains a failed check")
    if report.get("publication_allowed") is not True:
        raise RuntimeError(f"{stage} fresh checker did not allow publication")
    if report.get("article_sha256") != expected_article_sha256:
        raise RuntimeError(f"{stage} fresh checker article generation is stale")
    if report.get("manifest_sha256") != expected_manifest_sha256:
        raise RuntimeError(f"{stage} fresh checker manifest generation is stale")
    if (
        report.get("semantic_review_artifact_sha256")
        != expected_semantic_review_artifact_sha256
    ):
        raise RuntimeError(
            f"{stage} fresh checker semantic review generation is stale"
        )
    if report.get("active_generation") != expected_active_generation:
        raise RuntimeError(
            f"{stage} fresh checker active recovery generation is stale"
        )
    return report_bytes


def _semantic_publication_authority(layout: RunLayout) -> tuple[str, int]:
    path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir
        / "U09-U10-verdict"
        / "U11-semantic-review.json",
    )
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise RuntimeError(
            "publication requires the runtime-owned semantic review artifact"
        ) from error
    if (
        raw != canonical_json_bytes(document)
        or document.get("schema_id")
        != "crossframe.ultra.v82.semantic-review"
        or document.get("phase_id") != "U11"
        or document.get("run_id") != layout.run_dir.name
        or document.get("overall_status") != "pass"
        or document.get("publication_allowed") is not True
        or type(document.get("active_generation")) is not int
        or int(document["active_generation"]) < 0
    ):
        raise RuntimeError(
            "publication semantic review authority is invalid or non-passing"
        )
    return sha256_bytes(raw), int(document["active_generation"])


def _attach_note(error: BaseException, note: str) -> None:
    add_note = getattr(error, "add_note", None)
    if callable(add_note):
        add_note(note)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _validate_journal_state(journal: Mapping[str, object], state: str) -> None:
    precheck = journal.get("precheck_passed")
    postcheck = journal.get("postcheck_passed")
    failure = journal.get("failure")
    event_sha256 = journal.get("u12_event_sha256")
    checkpoint_sha256 = journal.get("u12_checkpoint_content_sha256")
    if precheck is not None and type(precheck) is not bool:
        raise ValueError("publish journal precheck_passed must be boolean or null")
    if postcheck is not None and type(postcheck) is not bool:
        raise ValueError("publish journal postcheck_passed must be boolean or null")
    if failure is not None and (
        not isinstance(failure, str) or not failure.strip()
    ):
        raise ValueError("publish journal failure must be a non-empty string or null")

    if state in {"journaled", "staged"}:
        valid = precheck is None and postcheck is None and failure is None
    elif state in {"prechecked", "backed-up", "published"}:
        valid = precheck is True and postcheck is None and failure is None
    elif state == "postchecked":
        valid = precheck is True and postcheck is True and failure is None
    elif state in {"u12-durable", "complete"}:
        valid = (
            precheck is True
            and postcheck is True
            and failure is None
            and _is_sha256(event_sha256)
            and _is_sha256(checkpoint_sha256)
        )
    else:
        valid = (
            state in {"rolled-back", "rollback-failed"}
            and (precheck is None or precheck is True)
            and postcheck is False
            and isinstance(failure, str)
            and bool(failure.strip())
        )
    if not valid:
        raise ValueError(f"publish journal state flags are invalid for {state}")
    if state not in {"u12-durable", "complete"} and (
        event_sha256 is not None or checkpoint_sha256 is not None
    ):
        raise ValueError("publish journal U12 hashes are present before durable U12")


def _validate_publish_journal(
    layout: RunLayout,
    paths: PublicationPaths,
    journal: Mapping[str, object],
) -> tuple[str, tuple[_JournalFileAuthority, ...]]:
    journal_fields = frozenset(journal) if isinstance(journal, Mapping) else frozenset()
    if not isinstance(journal, Mapping) or journal_fields not in {
        _JOURNAL_FIELDS,
        _LEGACY_JOURNAL_FIELDS,
    }:
        raise ValueError("publish journal must be a closed object")
    legacy_journal = journal_fields == _LEGACY_JOURNAL_FIELDS
    if journal.get("run_id") != layout.run_dir.name:
        raise ValueError("publish journal run_id differs from the current run")
    transaction_id = journal.get("transaction_id")
    if (
        not isinstance(transaction_id, str)
        or _TRANSACTION_ID_RE.fullmatch(transaction_id) is None
        or publication_paths(layout, transaction_id) != paths
    ):
        raise ValueError("publish journal transaction_id or fixed paths are invalid")
    state = journal.get("state")
    if not isinstance(state, str) or state not in _JOURNAL_STATES:
        raise ValueError("publish journal state is unknown")
    _validate_journal_state(journal, state)

    expected: dict[str, tuple[Path, Path, Path]] = {}
    for official in paths.official_paths:
        staged = _staged_path(paths, official)
        backup = _backup_path(paths, official)
        for candidate in (official, staged, backup):
            assert_safe_descendant(layout.root, candidate)
        expected[official.relative_to(layout.run_dir).as_posix()] = (
            official,
            staged,
            backup,
        )

    files = journal.get("files")
    if not isinstance(files, list) or len(files) != len(expected):
        raise ValueError("publish journal files must bijectively bind the fixed official set")
    observed: dict[str, _JournalFileAuthority] = {}
    legacy_file_entries: bool | None = None
    for record in files:
        record_fields = (
            frozenset(record) if isinstance(record, Mapping) else frozenset()
        )
        if not isinstance(record, Mapping) or record_fields not in {
            _JOURNAL_FILE_FIELDS,
            _LEGACY_JOURNAL_FILE_FIELDS,
        }:
            raise ValueError("publish journal file entry must be a closed object")
        record_is_legacy = record_fields == _LEGACY_JOURNAL_FILE_FIELDS
        if legacy_file_entries is None:
            legacy_file_entries = record_is_legacy
        elif legacy_file_entries is not record_is_legacy:
            raise ValueError("publish journal cannot mix legacy and current file entries")
        official_text = record.get("official_path")
        if not isinstance(official_text, str) or official_text not in expected:
            raise ValueError("publish journal official_path is not canonical")
        if official_text in observed:
            raise ValueError("publish journal repeats an official path")
        official, staged, backup = expected[official_text]
        staged_text = staged.relative_to(layout.root).as_posix()
        backup_text = backup.relative_to(layout.root).as_posix()
        if record.get("staged_path") != staged_text:
            raise ValueError("publish journal staged_path is not canonical")
        if not record_is_legacy and record.get("backup_path") != backup_text:
            raise ValueError("publish journal backup_path is not canonical")
        new_sha256 = record.get("new_sha256")
        if not _is_sha256(new_sha256):
            raise ValueError("publish journal new_sha256 is invalid")
        previous_existed = record.get("previous_existed")
        if type(previous_existed) is not bool:
            raise ValueError("publish journal previous_existed must be boolean")
        previous_sha256 = record.get("previous_sha256")
        if previous_existed:
            if not _is_sha256(previous_sha256):
                raise ValueError("publish journal previous_sha256 is invalid")
        elif previous_sha256 is not None:
            raise ValueError(
                "publish journal previous_sha256 must be null when no previous file existed"
            )
        observed[official_text] = _JournalFileAuthority(
            official_path=official,
            staged_path=staged,
            backup_path=backup,
            new_sha256=str(new_sha256),
            previous_existed=previous_existed,
            previous_sha256=(
                None if previous_sha256 is None else str(previous_sha256)
            ),
        )
    if set(observed) != set(expected):
        raise ValueError("publish journal does not bind the exact fixed official set")
    if legacy_journal and legacy_file_entries is not True:
        raise ValueError("legacy publish journal fields require legacy file entries")
    return state, tuple(
        observed[official.relative_to(layout.run_dir).as_posix()]
        for official in paths.official_paths
    )


def _disk_sha256(layout: RunLayout, path: Path, label: str) -> str | None:
    assert_safe_descendant(layout.root, path)
    if not path.exists():
        return None
    if not path.is_file():
        raise RuntimeError(f"publish journal {label} is not a regular file")
    return sha256_bytes(path.read_bytes())


def _journal_file_exists(layout: RunLayout, journal_path: Path) -> bool:
    assert_safe_descendant(layout.root, journal_path)
    if not journal_path.exists():
        return False
    if not journal_path.is_file():
        raise RuntimeError("fixed publish journal path is not a regular file")
    return True


def _preflight_recovery_bytes(
    layout: RunLayout,
    state: str,
    authorities: tuple[_JournalFileAuthority, ...],
) -> None:
    for authority in authorities:
        staged_sha256 = _disk_sha256(
            layout, authority.staged_path, "staged path"
        )
        if staged_sha256 is not None and staged_sha256 != authority.new_sha256:
            raise RuntimeError(
                f"publish journal staged hash mismatch for {authority.official_path.name}"
            )
        if state in _STAGED_REQUIRED_STATES and staged_sha256 is None:
            raise RuntimeError(
                f"publish journal staged file is missing for {authority.official_path.name}"
            )

        backup_sha256 = _disk_sha256(
            layout, authority.backup_path, "backup path"
        )
        if authority.previous_existed:
            if backup_sha256 is not None and backup_sha256 != authority.previous_sha256:
                raise RuntimeError(
                    f"publish journal backup hash mismatch for {authority.official_path.name}"
                )
            if state in _BACKUP_REQUIRED_STATES and backup_sha256 is None:
                raise RuntimeError(
                    f"publish journal backup is missing for {authority.official_path.name}"
                )
        elif backup_sha256 is not None:
            raise RuntimeError(
                f"publish journal has an unexpected backup for {authority.official_path.name}"
            )
        if state in {"journaled", "staged"} and backup_sha256 is not None:
            raise RuntimeError("publish journal has a backup before the backup state")

        official_sha256 = _disk_sha256(
            layout, authority.official_path, "official path"
        )
        previous_sha256 = authority.previous_sha256
        if state in _PRE_BACKUP_STATES:
            expected = previous_sha256 if authority.previous_existed else None
            if official_sha256 != expected:
                raise RuntimeError(
                    f"pre-backup official bytes changed for {authority.official_path.name}"
                )
        elif state in _PUBLISHED_STATES:
            if official_sha256 != authority.new_sha256:
                raise RuntimeError(
                    f"published generation differs from journal for {authority.official_path.name}"
                )
        elif state == "rolled-back":
            expected = previous_sha256 if authority.previous_existed else None
            if official_sha256 != expected:
                raise RuntimeError(
                    f"rolled-back official bytes differ for {authority.official_path.name}"
                )
        elif state in {"backed-up", "rollback-failed"}:
            allowed = {None, authority.new_sha256}
            if authority.previous_existed:
                allowed.add(previous_sha256)
            if official_sha256 not in allowed:
                raise RuntimeError(
                    f"publish journal official hash is unknown for {authority.official_path.name}"
                )
            needs_restore = authority.previous_existed and official_sha256 != previous_sha256
            if needs_restore and backup_sha256 is None:
                raise RuntimeError(
                    f"publish journal cannot restore {authority.official_path.name} without its backup"
                )


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


def _require_publication_authority(layout: RunLayout, lease: Lease) -> None:
    if load_cancel_intent(layout) is not None:
        raise CancelledRunError("cancel intent blocks publication")
    require_run_lease_owner(layout, lease)


def publish_delivery(
    layout: RunLayout,
    *,
    transaction_id: str,
    article_bytes: bytes,
    dossier_bytes: bytes,
    artifact_index_bytes: bytes,
    manifest_bytes: bytes,
    fresh_check: Callable[[str], bytes],
    commit_report: Callable[[str, bytes, Lease], object],
    mark_needs_attention: Callable[[str], object],
    defer_completion: bool = True,
    lease: Lease | None = None,
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
    if type(defer_completion) is not bool:
        raise TypeError("defer_completion must be boolean")
    if defer_completion is not True:
        raise ValueError(
            "publication cannot complete directly; durable U12 completion must remain deferred"
        )
    paths = publication_paths(layout, transaction_id)
    _journal_file_exists(layout, paths.journal_path)
    from .locks import (
        acquire_run_lease,
        release_run_lease,
    )

    if lease is None:
        owned = acquire_run_lease(
            layout,
            datetime.now(timezone.utc),
            timedelta(minutes=30),
        )
        try:
            return publish_delivery(
                layout,
                transaction_id=transaction_id,
                article_bytes=article_bytes,
                dossier_bytes=dossier_bytes,
                artifact_index_bytes=artifact_index_bytes,
                manifest_bytes=manifest_bytes,
                fresh_check=fresh_check,
                commit_report=commit_report,
                mark_needs_attention=mark_needs_attention,
                defer_completion=defer_completion,
                lease=owned,
            )
        finally:
            release_run_lease(layout, owned)
    _require_publication_authority(layout, lease)
    semantic_review_sha256, active_generation = _semantic_publication_authority(
        layout
    )
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

        _require_publication_authority(layout, lease)
        precheck_report_bytes = fresh_check("pre-publish")
        _require_publication_authority(layout, lease)
        precheck_report = _validate_report_bytes(
            precheck_report_bytes,
            "pre-publish",
            expected_article_sha256=sha256_bytes(article_bytes),
            expected_manifest_sha256=sha256_bytes(manifest_bytes),
            expected_semantic_review_artifact_sha256=semantic_review_sha256,
            expected_active_generation=active_generation,
        )
        precheck_passed = True
        _require_publication_authority(layout, lease)
        commit_report("pre-publish", precheck_report, lease)
        _require_publication_authority(layout, lease)
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
            _require_publication_authority(layout, lease)
            atomic_write_bytes(official, staged.read_bytes())
            _require_publication_authority(layout, lease)
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

        _require_publication_authority(layout, lease)
        postcheck_report_bytes = fresh_check("post-publish")
        _require_publication_authority(layout, lease)
        postcheck_report = _validate_report_bytes(
            postcheck_report_bytes,
            "post-publish",
            expected_article_sha256=sha256_bytes(article_bytes),
            expected_manifest_sha256=sha256_bytes(manifest_bytes),
            expected_semantic_review_artifact_sha256=semantic_review_sha256,
            expected_active_generation=active_generation,
        )
        postcheck_passed = True
        _require_publication_authority(layout, lease)
        commit_report("post-publish", postcheck_report, lease)
        _require_publication_authority(layout, lease)
        _write_journal(
            layout,
            paths,
            transaction_id=transaction_id,
            state="postchecked",
            payloads=payloads,
            previous=previous,
            precheck_passed=precheck_passed,
            postcheck_passed=postcheck_passed,
            failure=None,
        )
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
        if not isinstance(
            error,
            (CancelledRunError, LeaseOwnershipError),
        ):
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


def _journal_official_hashes(
    layout: RunLayout,
    paths: PublicationPaths,
    journal: Mapping[str, object],
) -> dict[Path, str]:
    _, authorities = _validate_publish_journal(layout, paths, journal)
    return {
        authority.official_path: authority.new_sha256
        for authority in authorities
    }


def _verify_published_generation(
    layout: RunLayout,
    paths: PublicationPaths,
    journal: Mapping[str, object],
) -> None:
    expected = set(paths.official_paths)
    observed = _journal_official_hashes(layout, paths, journal)
    if set(observed) != expected:
        raise RuntimeError("publish journal does not bind the fixed official set")
    for official, digest in observed.items():
        if not official.is_file() or sha256_bytes(official.read_bytes()) != digest:
            raise RuntimeError(
                f"published generation differs from journal for {official.name}"
            )


def _load_referenced_u12_checkpoint_read_only(
    layout: RunLayout,
    journal: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    from .recovery import (
        _paths,
        _read_events,
        _validate_authority,
        _validate_checkpoint,
    )

    event_sha256 = journal.get("u12_event_sha256")
    checkpoint_sha256 = journal.get("u12_checkpoint_content_sha256")
    if not _is_sha256(event_sha256) or not _is_sha256(checkpoint_sha256):
        raise RuntimeError("durable U12 journal hashes are unavailable")
    authority, compatibility = _validate_authority(layout)
    events = _read_events(layout, authority, compatibility=compatibility)
    events_by_hash = {str(event["event_sha256"]): event for event in events}
    event = events_by_hash.get(event_sha256)
    if (
        event is None
        or event.get("phase_id") != "U12"
        or event.get("status") != "complete"
    ):
        raise RuntimeError("durable U12 event is not in the recovery ancestry")

    checkpoints_dir, _, _, _, _ = _paths(layout)
    if not checkpoints_dir.is_dir():
        raise RuntimeError("durable U12 checkpoint directory is unavailable")
    try:
        candidates = sorted(checkpoints_dir.iterdir(), key=lambda path: path.name)
    except OSError as error:
        raise RuntimeError("durable U12 checkpoint directory cannot be read") from error
    matches: list[Mapping[str, object]] = []
    for path in candidates:
        assert_safe_descendant(layout.root, path)
        if not path.is_file():
            continue
        if path.suffix != ".json" or _SHA256_RE.fullmatch(path.stem) is None:
            continue
        try:
            raw = path.read_bytes()
            checkpoint = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError):
            continue
        if checkpoint.get("content_sha256") != checkpoint_sha256:
            continue
        if sha256_bytes(raw) != path.stem:
            raise RuntimeError(
                "referenced durable U12 checkpoint filename hash differs"
            )
        if raw != canonical_json_bytes(checkpoint):
            raise RuntimeError(
                "referenced durable U12 checkpoint is not canonical JSON"
            )
        validated = _validate_checkpoint(
            layout,
            checkpoint,
            authority=authority,
            compatibility=compatibility,
            events_by_hash=events_by_hash,
        )
        if (
            validated.get("boundary_kind") != "phase"
            or validated.get("phase_id") != "U12"
            or validated.get("completed_boundary") is not True
            or validated.get("phase_event_sha256") != event_sha256
        ):
            raise RuntimeError(
                "referenced durable U12 checkpoint authority is inconsistent"
            )
        matches.append(validated)
    if len(matches) != 1:
        raise RuntimeError(
            "durable U12 journal must reference exactly one valid checkpoint"
        )
    return tuple(matches)


def _durable_u12_checkpoint(
    layout: RunLayout,
    paths: PublicationPaths,
    journal: Mapping[str, object],
    *,
    read_only: bool = False,
) -> Mapping[str, object] | None:
    state, _ = _validate_publish_journal(layout, paths, journal)
    if read_only:
        checkpoints = _load_referenced_u12_checkpoint_read_only(layout, journal)
    else:
        from .recovery import load_checkpoints

        checkpoints = load_checkpoints(layout)
    matches = [
        item
        for item in checkpoints
        if item.get("boundary_kind") == "phase"
        and item.get("phase_id") == "U12"
        and item.get("completed_boundary") is True
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError("multiple durable U12 checkpoints are present")
    checkpoint = matches[0]
    event_sha256 = journal.get("u12_event_sha256")
    checkpoint_sha256 = journal.get("u12_checkpoint_content_sha256")
    if event_sha256 is not None and event_sha256 != checkpoint.get(
        "phase_event_sha256"
    ):
        raise RuntimeError("publish journal U12 event differs from recovery")
    if checkpoint_sha256 is not None and checkpoint_sha256 != checkpoint.get(
        "content_sha256"
    ):
        raise RuntimeError("publish journal U12 checkpoint differs from recovery")
    expected_paths = (
        paths.manifest_path,
        layout.validation_current_dir / "ultra-validator-report.json",
        paths.article_path,
        paths.dossier_path,
        paths.artifact_index_path,
    )
    expected_refs = [
        (
            path.relative_to(layout.run_dir).as_posix(),
            sha256_bytes(path.read_bytes()),
        )
        for path in expected_paths
    ]
    raw_refs = checkpoint.get("artifact_hashes")
    if not isinstance(raw_refs, list):
        raise RuntimeError("durable U12 checkpoint artifact authority is missing")
    observed_refs = [
        (item.get("path"), item.get("sha256"))
        if isinstance(item, Mapping)
        else (None, None)
        for item in raw_refs
    ]
    if observed_refs != expected_refs:
        raise RuntimeError(
            "durable U12 checkpoint does not bind the exact manifest, report, and delivery set"
        )
    if state in {"u12-durable", "complete"} and (
        event_sha256 != checkpoint.get("phase_event_sha256")
        or checkpoint_sha256 != checkpoint.get("content_sha256")
    ):
        raise RuntimeError("durable U12 journal hashes differ from the checkpoint")
    return checkpoint


def _mark_u12_durable(
    layout: RunLayout,
    paths: PublicationPaths,
    *,
    event: Mapping[str, object],
    checkpoint: Mapping[str, object],
) -> None:
    journal = load_json_object(paths.journal_path)
    state, authorities = _validate_publish_journal(layout, paths, journal)
    _preflight_recovery_bytes(layout, state, authorities)
    if state != "postchecked":
        raise RuntimeError("U12 durability requires a postchecked publish journal")
    if (
        event.get("phase_id") != "U12"
        or event.get("status") != "complete"
        or checkpoint.get("phase_id") != "U12"
        or checkpoint.get("phase_event_sha256") != event.get("event_sha256")
    ):
        raise RuntimeError("U12 event and checkpoint authority differ")
    durable = _durable_u12_checkpoint(layout, paths, journal)
    if (
        durable is None
        or durable.get("phase_event_sha256") != event.get("event_sha256")
        or durable.get("content_sha256") != checkpoint.get("content_sha256")
    ):
        raise RuntimeError("issuer-produced U12 checkpoint differs from durable recovery")
    _verify_published_generation(layout, paths, journal)
    updated = dict(journal)
    updated["state"] = "u12-durable"
    updated["u12_event_sha256"] = event["event_sha256"]
    updated["u12_checkpoint_content_sha256"] = checkpoint["content_sha256"]
    updated_state, updated_authorities = _validate_publish_journal(
        layout, paths, updated
    )
    _preflight_recovery_bytes(layout, updated_state, updated_authorities)
    atomic_write_json(paths.journal_path, updated)


def _verified_u12_authority(
    layout: RunLayout,
    *,
    allowed_states: frozenset[str],
) -> tuple[PublicationPaths, dict[str, object], Mapping[str, object]]:
    _validate_layout(layout)
    journal_path = layout.recovery_dir / JOURNAL_FILENAME
    journal = load_json_object(journal_path)
    transaction_id = journal.get("transaction_id")
    if not isinstance(transaction_id, str):
        raise ValueError("publish journal has no valid transaction_id")
    paths = publication_paths(layout, transaction_id)
    state, authorities = _validate_publish_journal(layout, paths, journal)
    _preflight_recovery_bytes(layout, state, authorities)
    if state not in allowed_states:
        raise RuntimeError(
            f"durable U12 authority requires journal state in {sorted(allowed_states)}"
        )
    checkpoint = _durable_u12_checkpoint(
        layout,
        paths,
        journal,
        read_only=True,
    )
    if checkpoint is None:
        raise RuntimeError("durable U12 authority has no verified checkpoint")
    _verify_published_generation(layout, paths, journal)
    return paths, dict(journal), checkpoint


def verify_u12_status_commit_authority(layout: RunLayout) -> None:
    _verified_u12_authority(
        layout,
        allowed_states=frozenset({"u12-durable", "complete"}),
    )


def verify_completed_u12_transaction(layout: RunLayout) -> None:
    _verified_u12_authority(
        layout,
        allowed_states=frozenset({"complete"}),
    )


def _roll_forward_u12_transaction(
    layout: RunLayout,
    paths: PublicationPaths,
    journal: Mapping[str, object],
    *,
    lease: object | None = None,
) -> dict[str, object]:
    reread = load_json_object(paths.journal_path)
    if dict(journal) != reread:
        raise RuntimeError("publish journal changed before U12 roll-forward")
    state, authorities = _validate_publish_journal(layout, paths, reread)
    _preflight_recovery_bytes(layout, state, authorities)
    checkpoint = _durable_u12_checkpoint(layout, paths, reread)
    if checkpoint is None:
        raise RuntimeError("U12 transaction has no durable checkpoint")
    if state not in {"postchecked", "u12-durable", "complete"}:
        raise RuntimeError("durable U12 checkpoint is paired with an illegal journal state")
    _verify_published_generation(layout, paths, reread)
    if state == "postchecked":
        bound = dict(reread)
        bound["state"] = "u12-durable"
        bound["u12_event_sha256"] = checkpoint["phase_event_sha256"]
        bound["u12_checkpoint_content_sha256"] = checkpoint["content_sha256"]
        bound_state, bound_authorities = _validate_publish_journal(
            layout, paths, bound
        )
        _preflight_recovery_bytes(layout, bound_state, bound_authorities)
        atomic_write_json(paths.journal_path, bound)
        reread = bound

    from .indexes import IndexStore
    from .status import RunStatusStore

    status_store = RunStatusStore(layout)
    current = status_store.read()
    if current.status != "complete":
        previous = datetime.fromisoformat(current.updated_at[:-1] + "+00:00")
        transition_at = max(
            datetime.now(timezone.utc),
            previous + timedelta(microseconds=1),
        )
        if current.status == "needs_attention":
            current = status_store.transition(
                current,
                "running",
                transition_at,
                current_phase=current.current_phase,
                last_complete_phase=current.last_complete_phase,
                reason="durable U12 transaction roll-forward admitted",
                validation_passed=False,
                lease=lease,
            )
            transition_at = transition_at + timedelta(microseconds=1)
        current = status_store.commit_u12_complete(
            current,
            transition_at,
            reason="durable U12 transaction roll-forward",
            lease=lease,
        )
    if (
        current.current_phase != "U12"
        or current.last_complete_phase != "U12"
        or current.validation_passed is not True
        or current.tools_allowed is not False
    ):
        raise RuntimeError("durable U12 status authority is inconsistent")

    verdict_path = layout.artifacts_dir / "U09-U10-verdict/U09-verdict.json"
    verdict = load_json_object(verdict_path)
    build_final_chat_projection(layout, verdict, current)
    write_final_chat_projection(layout, verdict, current)

    reread = load_json_object(paths.journal_path)
    reread_state, reread_authorities = _validate_publish_journal(
        layout, paths, reread
    )
    _preflight_recovery_bytes(layout, reread_state, reread_authorities)
    durable = _durable_u12_checkpoint(layout, paths, reread)
    if durable is None or durable.get("content_sha256") != checkpoint.get(
        "content_sha256"
    ):
        raise RuntimeError("U12 checkpoint changed before journal completion")
    _verify_published_generation(layout, paths, reread)
    final = dict(reread)
    final["state"] = "complete"
    final["postcheck_passed"] = True
    final_state, final_authorities = _validate_publish_journal(
        layout, paths, final
    )
    _preflight_recovery_bytes(layout, final_state, final_authorities)
    atomic_write_json(paths.journal_path, final)
    IndexStore(layout.root).rebuild()
    _remove_staging(layout, paths)
    return final


def recover_publish_transaction(
    layout: RunLayout,
    *,
    mark_needs_attention: Callable[[str], object],
    lease: object | None = None,
) -> dict[str, object] | None:
    """Recover an incomplete fixed journal without accepting caller-selected paths."""

    _validate_layout(layout)
    if not callable(mark_needs_attention):
        raise TypeError("mark_needs_attention must be callable")
    journal_path = layout.recovery_dir / JOURNAL_FILENAME
    if not _journal_file_exists(layout, journal_path):
        return None
    from .locks import (
        acquire_run_lease,
        release_run_lease,
        require_run_lease_owner,
    )

    if lease is None:
        owned = acquire_run_lease(
            layout,
            datetime.now(timezone.utc),
            timedelta(minutes=30),
        )
        try:
            return recover_publish_transaction(
                layout,
                mark_needs_attention=mark_needs_attention,
                lease=owned,
            )
        finally:
            release_run_lease(layout, owned)
    require_run_lease_owner(layout, lease)
    journal = load_json_object(journal_path)
    transaction_id = journal.get("transaction_id")
    if not isinstance(transaction_id, str):
        raise ValueError("publish journal has no valid transaction_id")
    paths = publication_paths(layout, transaction_id)
    state, authorities = _validate_publish_journal(layout, paths, journal)
    _preflight_recovery_bytes(layout, state, authorities)
    durable_u12 = _durable_u12_checkpoint(layout, paths, journal)
    if durable_u12 is not None:
        if state not in {"postchecked", "u12-durable", "complete"}:
            raise RuntimeError(
                "durable U12 checkpoint is paired with an illegal journal state"
            )
        return _roll_forward_u12_transaction(
            layout,
            paths,
            journal,
            lease=lease,
        )
    if state in {"u12-durable", "complete"}:
        raise RuntimeError(
            "publish journal declares durable U12 without a valid checkpoint"
        )
    if state == "rolled-back":
        _remove_staging(layout, paths)
        return journal
    if state not in _PRE_BACKUP_STATES:
        for authority in authorities:
            if authority.previous_existed:
                current_sha256 = _disk_sha256(
                    layout, authority.official_path, "official path"
                )
                if current_sha256 != authority.previous_sha256:
                    data = authority.backup_path.read_bytes()
                    if sha256_bytes(data) != authority.previous_sha256:
                        raise RuntimeError(
                            f"publish backup hash mismatch for {authority.official_path.name}"
                        )
                    atomic_write_bytes(authority.official_path, data)
            else:
                authority.official_path.unlink(missing_ok=True)
    recovered = dict(journal)
    recovered["state"] = "rolled-back"
    recovered["postcheck_passed"] = False
    recovered["failure"] = "recovered incomplete publication journal"
    recovered["u12_event_sha256"] = None
    recovered["u12_checkpoint_content_sha256"] = None
    recovered_state, recovered_authorities = _validate_publish_journal(
        layout, paths, recovered
    )
    _preflight_recovery_bytes(layout, recovered_state, recovered_authorities)
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
