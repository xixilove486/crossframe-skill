from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
from typing import Any, Mapping, Sequence

from check_crossframe_ultra_v82_source import (
    EXPECTED_TREE_MERKLE_ROOT,
    validate_committed_source_snapshot,
)

from .constants import (
    ARTICLE_CONTRACT_VERSION,
    ARTIFACT_SCHEMA_VERSION,
    COMPILER_VERSION,
    FRAMEWORK_RAW_SHA256,
    FRAMEWORK_REVISION,
    FRAMEWORK_SEMANTIC_SHA256,
    FRAMEWORK_VERSION,
    RUNTIME_VERSION,
    VALIDATOR_VERSION,
)


EXPECTED_PARAGRAPH_COUNT = 4_631
EXPECTED_TABLE_COUNT = 122
EXPECTED_SOURCE_UNIT_COUNT = 4_753
MAX_SOURCE_MANIFEST_BYTES = 2 * 1024 * 1024
READ_EVENT_SCHEMA_ID = "crossframe.ultra.v82.read-event"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_READER_MODES = frozenset({"full-source", "paragraph", "table", "assistive"})
_U1_PREREQUISITES = frozenset(
    {
        "source_manifest",
        "release_manifest",
        "compatibility_matrix",
        "knowledge_closure",
        "skill_tree_hash",
        "fixed_root",
        "free_space_reserve",
        "current_user_acl",
    }
)
_VERSION_BINDING_FIELDS = frozenset(
    {
        "framework_version",
        "framework_revision",
        "framework_raw_sha256",
        "framework_semantic_sha256",
        "runtime_version",
        "artifact_schema_version",
        "compiler_version",
        "validator_version",
        "article_contract_version",
        "source_tree_sha256",
    }
)
_CURRENT_VERSION_BINDING = {
    "framework_version": FRAMEWORK_VERSION,
    "framework_revision": FRAMEWORK_REVISION,
    "framework_raw_sha256": FRAMEWORK_RAW_SHA256,
    "framework_semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
    "runtime_version": RUNTIME_VERSION,
    "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
    "compiler_version": COMPILER_VERSION,
    "validator_version": VALIDATOR_VERSION,
    "article_contract_version": ARTICLE_CONTRACT_VERSION,
}
_READ_EVENT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "generated_at",
        "content_sha256",
        "phase_id",
        "source_unit_id",
        "source_kind",
        "source_ordinal",
        "source_manifest_sha256",
        "promoted_semantic_snapshot_sha256",
        "reader_mode",
        "execution_identity",
        "read_at",
        "read_event_sha256",
    }
)


class SourceManifestError(ValueError):
    """Raised when the promoted source manifest is malformed or unbound."""


class SourceCoverageError(ValueError):
    """Raised when human/host read events do not cover the frozen source."""


class SourceLockError(RuntimeError):
    """Raised when a U1 lock prerequisite cannot be proven."""


@dataclass(frozen=True, init=False)
class SourceManifestSnapshot:
    _document: dict[str, object]
    sha256: str
    semantic_sha256: str

    @property
    def document(self) -> dict[str, object]:
        return copy.deepcopy(self._document)


@dataclass(frozen=True, init=False)
class ReadReceipt:
    _source_unit: dict[str, object]
    _record_sha256: str

    @property
    def source_unit(self) -> dict[str, object]:
        return copy.deepcopy(self._source_unit)


@dataclass(frozen=True, init=False)
class ReadCaptureDiagnostic:
    """External diagnostic data only; it never authorizes a phase transition."""

    _events: tuple[dict[str, object], ...]
    _repo: Path
    _receipts: tuple[ReadReceipt, ...]
    _run_id: str
    _version_binding: dict[str, object]
    _parent_event_sha256: str

    @property
    def events(self) -> tuple[dict[str, object], ...]:
        return tuple(copy.deepcopy(event) for event in self._events)


@dataclass(frozen=True, init=False)
class U1Verification:
    ready: bool
    verified: tuple[str, ...]
    unknown: tuple[str, ...]
    _repo: Path
    _manifest_sha256: str


@dataclass(frozen=True)
class ReadCoverageAudit:
    total: int
    paragraphs: int
    tables: int
    complete: bool
    authorizes_phase: bool = False


def _issue_snapshot(
    document: Mapping[str, object], *, sha256: str, semantic_sha256: str
) -> SourceManifestSnapshot:
    snapshot = object.__new__(SourceManifestSnapshot)
    object.__setattr__(snapshot, "_document", copy.deepcopy(dict(document)))
    object.__setattr__(snapshot, "sha256", sha256)
    object.__setattr__(snapshot, "semantic_sha256", semantic_sha256)
    return snapshot


def _issue_receipt(source_unit: Mapping[str, object], *, record_sha256: str) -> ReadReceipt:
    receipt = object.__new__(ReadReceipt)
    object.__setattr__(receipt, "_source_unit", _validate_source_unit(source_unit))
    object.__setattr__(receipt, "_record_sha256", record_sha256)
    return receipt


def _issue_batch(
    events: Sequence[Mapping[str, object]],
    *,
    repo: Path,
    receipts: Sequence[ReadReceipt],
    run_id: str,
    version_binding: Mapping[str, object],
    parent_event_sha256: str,
) -> ReadCaptureDiagnostic:
    captured = tuple(copy.deepcopy(dict(event)) for event in events)
    batch = object.__new__(ReadCaptureDiagnostic)
    object.__setattr__(batch, "_events", captured)
    object.__setattr__(batch, "_repo", repo.resolve())
    object.__setattr__(batch, "_receipts", tuple(receipts))
    object.__setattr__(batch, "_run_id", run_id)
    object.__setattr__(batch, "_version_binding", copy.deepcopy(dict(version_binding)))
    object.__setattr__(batch, "_parent_event_sha256", parent_event_sha256)
    return batch


def _issue_u1_verification(
    *,
    ready: bool,
    verified: Sequence[str],
    unknown: Sequence[str],
    repo: Path,
    manifest_sha256: str,
) -> U1Verification:
    result = object.__new__(U1Verification)
    object.__setattr__(result, "ready", ready)
    object.__setattr__(result, "verified", tuple(verified))
    object.__setattr__(result, "unknown", tuple(unknown))
    object.__setattr__(result, "_repo", repo.resolve())
    object.__setattr__(result, "_manifest_sha256", manifest_sha256)
    return result


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _validate_read_version_binding(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise SourceCoverageError("read event version binding must be an object")
    binding = copy.deepcopy(dict(value))
    if frozenset(binding) != _VERSION_BINDING_FIELDS:
        raise SourceCoverageError("read event version binding fields are incomplete")
    if any(binding[field] != expected for field, expected in _CURRENT_VERSION_BINDING.items()):
        raise SourceCoverageError("read event version binding is not current")
    if binding["source_tree_sha256"] != EXPECTED_TREE_MERKLE_ROOT:
        raise SourceCoverageError("read event source tree is not the authority tree")
    return binding


def _pairs_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SourceManifestError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _parse_json_object(raw: bytes) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceManifestError("source manifest is not UTF-8") from error
    if text.startswith("\ufeff"):
        raise SourceManifestError("source manifest must not contain a BOM")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                SourceManifestError(f"non-finite JSON value: {token}")
            ),
        )
    except json.JSONDecodeError as error:
        raise SourceManifestError(f"invalid source manifest JSON: {error}") from error
    if not isinstance(value, dict):
        raise SourceManifestError("source manifest root must be an object")
    return value


def _read_regular_bounded(path: Path) -> bytes:
    if not isinstance(path, Path):
        raise TypeError("source manifest path must be a pathlib.Path")
    if path.is_symlink():
        raise SourceManifestError("source manifest cannot be a symbolic link")
    try:
        before = path.stat()
    except OSError as error:
        raise SourceManifestError(f"cannot stat source manifest: {error}") from error
    if not stat.S_ISREG(before.st_mode):
        raise SourceManifestError("source manifest is not a regular file")
    if before.st_size > MAX_SOURCE_MANIFEST_BYTES:
        raise SourceManifestError("source manifest exceeds the size budget")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise SourceManifestError("opened source manifest is not regular")
            if (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            ) != (
                opened.st_dev,
                opened.st_ino,
                opened.st_size,
                opened.st_mtime_ns,
            ):
                raise SourceManifestError(
                    "source manifest changed or was replaced before it was opened"
                )
            if opened.st_size > MAX_SOURCE_MANIFEST_BYTES:
                raise SourceManifestError("source manifest exceeds the size budget")
            raw = handle.read(MAX_SOURCE_MANIFEST_BYTES + 1)
            after = os.fstat(handle.fileno())
    except OSError as error:
        raise SourceManifestError(f"cannot read source manifest: {error}") from error
    if len(raw) > MAX_SOURCE_MANIFEST_BYTES:
        raise SourceManifestError("source manifest grew beyond the size budget")
    if (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ):
        raise SourceManifestError("source manifest changed while it was read")
    if len(raw) != opened.st_size:
        raise SourceManifestError("source manifest length changed while it was read")
    return raw


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _validate_source_unit(unit: object) -> dict[str, object]:
    if not isinstance(unit, Mapping):
        raise SourceManifestError("source unit must be an object")
    snapshot = copy.deepcopy(dict(unit))
    required = {"unit_id", "kind", "ordinal", "sha256"}
    if set(snapshot) != required:
        raise SourceManifestError("source unit fields do not match the closed contract")
    kind = snapshot["kind"]
    ordinal = snapshot["ordinal"]
    if kind not in {"paragraph", "table"} or not _positive_int(ordinal):
        raise SourceManifestError("source unit kind or ordinal is invalid")
    prefix = "P" if kind == "paragraph" else "T"
    width = 4 if kind == "paragraph" else 3
    if snapshot["unit_id"] != f"V82-{prefix}{ordinal:0{width}d}":
        raise SourceManifestError("source unit ID does not match kind and ordinal")
    if not _is_sha256(snapshot["sha256"]):
        raise SourceManifestError("source unit content hash is invalid")
    return snapshot


def _validate_manifest_document(document: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    counts = {
        "paragraph_count": EXPECTED_PARAGRAPH_COUNT,
        "table_count": EXPECTED_TABLE_COUNT,
        "source_unit_count": EXPECTED_SOURCE_UNIT_COUNT,
    }
    for field, expected in counts.items():
        if document.get(field) != expected or isinstance(document.get(field), bool):
            raise SourceManifestError(f"source manifest {field} must equal {expected}")
    raw_units = document.get("source_units")
    if not isinstance(raw_units, list) or len(raw_units) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceManifestError("source manifest must contain exactly 4,753 units")
    units = tuple(_validate_source_unit(unit) for unit in raw_units)
    identifiers = [str(unit["unit_id"]) for unit in units]
    if len(identifiers) != len(set(identifiers)):
        raise SourceManifestError("source manifest contains duplicate unit IDs")
    paragraph_ordinals = [
        int(unit["ordinal"]) for unit in units if unit["kind"] == "paragraph"
    ]
    table_ordinals = [int(unit["ordinal"]) for unit in units if unit["kind"] == "table"]
    if paragraph_ordinals != list(range(1, EXPECTED_PARAGRAPH_COUNT + 1)):
        raise SourceManifestError("paragraph source units are incomplete or out of order")
    if table_ordinals != list(range(1, EXPECTED_TABLE_COUNT + 1)):
        raise SourceManifestError("table source units are incomplete or out of order")
    return units


def load_source_manifest(
    path: Path, *, expected_sha256: str | None = None
) -> SourceManifestSnapshot:
    if expected_sha256 is not None and not _is_sha256(expected_sha256):
        raise SourceManifestError("expected source manifest hash is invalid")
    raw = _read_regular_bounded(path)
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise SourceManifestError("source manifest hash does not match the authority binding")
    document = _parse_json_object(raw)
    _validate_manifest_document(document)
    semantic_sha256 = document.get("semantic_sha256")
    if not _is_sha256(semantic_sha256):
        raise SourceManifestError("source manifest semantic hash is invalid")
    return _issue_snapshot(
        document, sha256=actual_sha256, semantic_sha256=str(semantic_sha256)
    )


def _manifest_parts(
    manifest: SourceManifestSnapshot,
    *,
    source_manifest_sha256: str | None,
) -> tuple[dict[str, object], tuple[dict[str, object], ...], str, str]:
    if isinstance(manifest, SourceManifestSnapshot):
        try:
            document = copy.deepcopy(manifest.document)
            manifest_sha256 = manifest.sha256
            semantic_sha256 = manifest.semantic_sha256
        except AttributeError as error:
            raise SourceManifestError("source manifest snapshot was not issued by the loader") from error
        if source_manifest_sha256 is not None and source_manifest_sha256 != manifest_sha256:
            raise SourceManifestError("explicit manifest hash differs from the loaded snapshot")
    else:
        raise SourceManifestError("source reads require a sealed manifest snapshot")
    authority_path = Path(__file__).resolve().parents[2] / "references" / "source-manifest.json"
    authority = load_source_manifest(authority_path, expected_sha256=_authority_manifest_sha256())
    if (
        manifest_sha256 != authority.sha256
        or semantic_sha256 != authority.semantic_sha256
        or document != authority.document
    ):
        raise SourceManifestError("source reads require the current authority snapshot")
    units = _validate_manifest_document(document)
    return document, units, manifest_sha256, semantic_sha256


def build_read_plan(
    manifest: SourceManifestSnapshot,
    *,
    promoted_semantic_snapshot_sha256: str,
    source_manifest_sha256: str | None = None,
) -> dict[str, object]:
    if not _is_sha256(promoted_semantic_snapshot_sha256):
        raise SourceManifestError("promoted semantic snapshot hash is invalid")
    document, units, manifest_hash, manifest_semantic = _manifest_parts(
        manifest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if manifest_semantic != promoted_semantic_snapshot_sha256:
        raise SourceManifestError("promoted semantic snapshot differs from the manifest")
    return {
        "source_manifest_sha256": manifest_hash,
        "promoted_semantic_snapshot_sha256": promoted_semantic_snapshot_sha256,
        "source_unit_count": document["source_unit_count"],
        "paragraph_count": document["paragraph_count"],
        "table_count": document["table_count"],
        "source_unit_ids": [str(unit["unit_id"]) for unit in units],
        "source_units": copy.deepcopy(list(units)),
    }


def capture_committed_read_receipts(
    repo: Path, *, manifest: SourceManifestSnapshot
) -> tuple[ReadReceipt, ...]:
    """Read the authoritative paragraph and table bodies through its anchored checker."""
    if not isinstance(repo, Path):
        raise TypeError("repo must be a pathlib.Path")
    if not isinstance(manifest, SourceManifestSnapshot):
        raise SourceCoverageError("anchored source reads require a sealed manifest snapshot")
    committed = validate_committed_source_snapshot(repo)
    if committed.errors:
        raise SourceCoverageError(
            "anchored source read failed validation: " + "; ".join(committed.errors)
        )
    if committed.manifest_bytes is None:
        raise SourceCoverageError("anchored source read did not capture the manifest")
    if hashlib.sha256(committed.manifest_bytes).hexdigest() != manifest.sha256:
        raise SourceCoverageError("anchored source read manifest differs from the snapshot")
    units = {str(item["unit_id"]): item for item in manifest.document["source_units"]}
    receipts: list[ReadReceipt] = []
    for record in tuple(committed.paragraphs) + tuple(committed.tables):
        unit = units.get(str(record.get("anchor")))
        if unit is None:
            raise SourceCoverageError("anchored source read produced an unknown source unit")
        payload = json.dumps(
            dict(record),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        receipts.append(
            _issue_receipt(
                unit, record_sha256=hashlib.sha256(payload).hexdigest()
            )
        )
    if len(receipts) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("anchored source read did not cover every source unit")
    return tuple(receipts)


def capture_authority_read_diagnostic(
    repo: Path,
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    manifest: SourceManifestSnapshot,
    reader_mode: str,
    read_at: str,
    parent_event_sha256: str = "0" * 64,
) -> ReadCaptureDiagnostic:
    """Capture diagnostic data; callers cannot use it to authorize a phase."""
    _manifest_parts(manifest, source_manifest_sha256=None)
    binding = _validate_read_version_binding(version_binding)
    if not isinstance(run_id, str) or not run_id.strip():
        raise SourceCoverageError("run_id must be non-empty")
    if not _is_sha256(parent_event_sha256):
        raise SourceCoverageError("read capture parent boundary is invalid")
    receipts = capture_committed_read_receipts(repo, manifest=manifest)
    events = [
        make_read_event(
            run_id=run_id,
            version_binding=binding,
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            reader_mode=reader_mode,
            execution_identity=execution_identity(),
            read_at=read_at,
            receipt=receipt,
        )
        for receipt in receipts
    ]
    return _issue_batch(
        events,
        repo=repo,
        receipts=receipts,
        run_id=run_id,
        version_binding=binding,
        parent_event_sha256=parent_event_sha256,
    )


def execution_identity() -> dict[str, object]:
    return {
        "kind": "host-process",
        "process_id": os.getpid(),
        "executable": str(Path(sys.executable).resolve()),
        "user": getpass.getuser(),
    }


def _validate_execution_identity(value: object, *, require_current: bool) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise SourceCoverageError("execution identity must be an object")
    identity = copy.deepcopy(dict(value))
    if set(identity) != {"kind", "process_id", "executable", "user"}:
        raise SourceCoverageError("execution identity fields are incomplete")
    if identity["kind"] != "host-process":
        raise SourceCoverageError("read completion must come from a host process")
    if (
        not isinstance(identity["process_id"], int)
        or isinstance(identity["process_id"], bool)
        or identity["process_id"] < 1
    ):
        raise SourceCoverageError("execution process ID is invalid")
    if not isinstance(identity["executable"], str) or not identity["executable"]:
        raise SourceCoverageError("execution executable is invalid")
    if not isinstance(identity["user"], str) or not identity["user"]:
        raise SourceCoverageError("execution user is invalid")
    if require_current:
        current = execution_identity()
        if identity != current:
            raise SourceCoverageError("execution identity is not the current host process")
    return identity


def _parse_read_timestamp(value: object) -> None:
    if not isinstance(value, str) or not value:
        raise SourceCoverageError("read timestamp must be RFC3339")
    candidate = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise SourceCoverageError("read timestamp must be RFC3339") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceCoverageError("read timestamp must include an offset")


def _read_event_sha256(event: Mapping[str, object]) -> str:
    payload = {key: copy.deepcopy(value) for key, value in event.items() if key != "read_event_sha256"}
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SourceCoverageError("read event is not canonical JSON") from error
    return hashlib.sha256(encoded).hexdigest()


def make_read_event(
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    source_unit: Mapping[str, object],
    promoted_semantic_snapshot_sha256: str,
    source_manifest_sha256: str,
    reader_mode: str,
    execution_identity: Mapping[str, object],
    read_at: str,
    receipt: ReadReceipt | None = None,
) -> dict[str, object]:
    if not isinstance(run_id, str) or not run_id.strip():
        raise SourceCoverageError("run_id must be non-empty")
    binding = _validate_read_version_binding(version_binding)
    try:
        unit = _validate_source_unit(source_unit)
    except SourceManifestError as error:
        raise SourceCoverageError(str(error)) from error
    if not _is_sha256(promoted_semantic_snapshot_sha256):
        raise SourceCoverageError("semantic snapshot hash is invalid")
    if not _is_sha256(source_manifest_sha256):
        raise SourceCoverageError("source manifest hash is invalid")
    if reader_mode not in _READER_MODES:
        raise SourceCoverageError("reader mode is invalid")
    if receipt is not None:
        if not isinstance(receipt, ReadReceipt) or receipt.source_unit != unit:
            raise SourceCoverageError("read receipt does not bind this source read")
    elif source_manifest_sha256 == _authority_manifest_sha256():
        raise SourceCoverageError(
            "a real authority source read requires an anchored read receipt"
        )
    identity = _validate_execution_identity(execution_identity, require_current=True)
    _parse_read_timestamp(read_at)
    event: dict[str, object] = {
        "schema_id": READ_EVENT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": binding,
        "generated_at": read_at,
        "phase_id": "U1",
        "source_unit_id": unit["unit_id"],
        "source_kind": unit["kind"],
        "source_ordinal": unit["ordinal"],
        "content_sha256": unit["sha256"],
        "source_manifest_sha256": source_manifest_sha256,
        "promoted_semantic_snapshot_sha256": promoted_semantic_snapshot_sha256,
        "reader_mode": reader_mode,
        "execution_identity": identity,
        "read_at": read_at,
    }
    event["read_event_sha256"] = _read_event_sha256(event)
    return event


@lru_cache(maxsize=1)
def _authority_manifest_sha256() -> str | None:
    path = Path(__file__).resolve().parents[2] / "references" / "source-manifest.json"
    try:
        return hashlib.sha256(_read_regular_bounded(path)).hexdigest()
    except (OSError, SourceManifestError):
        return None


def audit_read_capture(
    events: ReadCaptureDiagnostic,
    manifest: SourceManifestSnapshot,
    *,
    promoted_semantic_snapshot_sha256: str,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_parent_event_sha256: str,
    source_manifest_sha256: str | None = None,
) -> ReadCoverageAudit:
    """Audit diagnostic capture data without conferring phase authorization."""
    if not isinstance(events, ReadCaptureDiagnostic):
        raise SourceCoverageError("read audit requires a captured diagnostic")
    if not isinstance(events._repo, Path) or not isinstance(events._receipts, tuple):
        raise SourceCoverageError("read batch is missing its authority capture record")
    expected_binding = _validate_read_version_binding(expected_version_binding)
    if not isinstance(expected_run_id, str) or not expected_run_id.strip():
        raise SourceCoverageError("expected read run_id is invalid")
    if not _is_sha256(expected_parent_event_sha256):
        raise SourceCoverageError("expected read parent boundary is invalid")
    if (
        events._run_id != expected_run_id
        or events._version_binding != expected_binding
        or events._parent_event_sha256 != expected_parent_event_sha256
    ):
        raise SourceCoverageError("read batch run, version, or boundary differs from expectation")
    _document, units, manifest_hash, manifest_semantic = _manifest_parts(
        manifest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if not _is_sha256(promoted_semantic_snapshot_sha256):
        raise SourceCoverageError("semantic snapshot hash is invalid")
    if manifest_semantic != promoted_semantic_snapshot_sha256:
        raise SourceCoverageError("semantic snapshot differs from the manifest")
    fresh_receipts = capture_committed_read_receipts(events._repo, manifest=manifest)
    expected_receipts = {
        str(receipt.source_unit["unit_id"]): receipt for receipt in fresh_receipts
    }
    captured_receipts = {
        str(receipt.source_unit["unit_id"]): receipt
        for receipt in events._receipts
        if isinstance(receipt, ReadReceipt)
    }
    if len(captured_receipts) != EXPECTED_SOURCE_UNIT_COUNT or any(
        receipt._record_sha256 != expected_receipts[unit_id]._record_sha256
        for unit_id, receipt in captured_receipts.items()
        if unit_id in expected_receipts
    ) or set(captured_receipts) != set(expected_receipts):
        raise SourceCoverageError("read batch does not match a fresh authority capture")
    if len(events._events) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("read event count is not exactly 4,753")
    expected = {str(unit["unit_id"]): unit for unit in units}
    seen: set[str] = set()
    run_id: str | None = None
    batch_binding: dict[str, object] | None = None
    for raw_event in events._events:
        if not isinstance(raw_event, Mapping):
            raise SourceCoverageError("read event must be an object")
        event = copy.deepcopy(dict(raw_event))
        if frozenset(event) != _READ_EVENT_FIELDS:
            raise SourceCoverageError("read event fields do not match the closed contract")
        if event.get("schema_id") != READ_EVENT_SCHEMA_ID:
            raise SourceCoverageError("read event schema_id is invalid")
        if event.get("schema_version") != 1 or event.get("phase_id") != "U1":
            raise SourceCoverageError("read event schema or phase version is invalid")
        if event.get("generated_at") != event.get("read_at"):
            raise SourceCoverageError("read event generated_at differs from read_at")
        binding = _validate_read_version_binding(event.get("version_binding"))
        if batch_binding is None:
            batch_binding = binding
        elif binding != batch_binding:
            raise SourceCoverageError("read events have mixed source tree/version bindings")
        event_hash = event.get("read_event_sha256")
        if not _is_sha256(event_hash) or event_hash != _read_event_sha256(event):
            raise SourceCoverageError("read event hash is invalid")
        event_run_id = event.get("run_id")
        if not isinstance(event_run_id, str) or not event_run_id.strip():
            raise SourceCoverageError("read event run_id is invalid")
        if run_id is None:
            run_id = event_run_id
        elif event_run_id != run_id:
            raise SourceCoverageError("read events cross run boundaries")
        unit_id = event.get("source_unit_id")
        if not isinstance(unit_id, str) or unit_id not in expected:
            raise SourceCoverageError("read event references an unknown source unit")
        if unit_id in seen:
            raise SourceCoverageError("duplicate source-unit read event")
        seen.add(unit_id)
        unit = expected[unit_id]
        if event.get("source_kind") != unit["kind"]:
            raise SourceCoverageError("read event source kind differs from the manifest")
        if event.get("source_ordinal") != unit["ordinal"]:
            raise SourceCoverageError("read event ordinal differs from the manifest")
        if event.get("content_sha256") != unit["sha256"]:
            raise SourceCoverageError("read event content hash differs from the manifest")
        if event.get("source_manifest_sha256") != manifest_hash:
            raise SourceCoverageError("read event manifest hash differs")
        if (
            event.get("promoted_semantic_snapshot_sha256")
            != promoted_semantic_snapshot_sha256
        ):
            raise SourceCoverageError("read event semantic snapshot differs")
        if event.get("reader_mode") not in _READER_MODES:
            raise SourceCoverageError("read event reader mode is invalid")
        _validate_execution_identity(event.get("execution_identity"), require_current=True)
        _parse_read_timestamp(event.get("read_at"))
    if seen != set(expected):
        raise SourceCoverageError("read events do not cover every source unit")
    if run_id != expected_run_id:
        raise SourceCoverageError("read events differ from the expected run")
    if batch_binding != expected_binding:
        raise SourceCoverageError("read events differ from the expected version binding")
    paragraphs = sum(1 for unit in units if unit["kind"] == "paragraph")
    tables = sum(1 for unit in units if unit["kind"] == "table")
    return ReadCoverageAudit(
        total=len(seen),
        paragraphs=paragraphs,
        tables=tables,
        complete=(
            len(seen) == EXPECTED_SOURCE_UNIT_COUNT
            and paragraphs == EXPECTED_PARAGRAPH_COUNT
            and tables == EXPECTED_TABLE_COUNT
        ),
    )


def _coverage_artifact_sha256(
    batch: ReadCaptureDiagnostic,
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_parent_event_sha256: str,
) -> str:
    """Hash a verified U1 source-read capture into a phase output artifact."""
    if not isinstance(batch, ReadCaptureDiagnostic):
        raise SourceCoverageError("coverage artifact requires a captured read batch")
    binding = _validate_read_version_binding(expected_version_binding)
    if (
        batch._run_id != expected_run_id
        or batch._version_binding != binding
        or batch._parent_event_sha256 != expected_parent_event_sha256
    ):
        raise SourceCoverageError("coverage artifact run, version, or boundary differs")
    payload = {
        "artifact_type": "crossframe.ultra.v82.u1-source-coverage",
        "run_id": expected_run_id,
        "version_binding": binding,
        "parent_event_sha256": expected_parent_event_sha256,
        "read_event_sha256s": [
            str(event["read_event_sha256"]) for event in batch._events
        ],
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _capture_validate_u1_authority(
    repo: Path,
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    manifest: SourceManifestSnapshot,
    read_at: str,
    parent_event_sha256: str,
) -> str:
    """The sole source module path that creates a U1 coverage artifact."""
    diagnostic = capture_authority_read_diagnostic(
        repo,
        run_id=run_id,
        version_binding=version_binding,
        manifest=manifest,
        reader_mode="full-source",
        read_at=read_at,
        parent_event_sha256=parent_event_sha256,
    )
    audit = audit_read_capture(
        diagnostic,
        manifest,
        promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
        expected_run_id=run_id,
        expected_version_binding=version_binding,
        expected_parent_event_sha256=parent_event_sha256,
    )
    if not audit.complete:
        raise SourceCoverageError("authority capture is incomplete")
    return _coverage_artifact_sha256(
        diagnostic,
        expected_run_id=run_id,
        expected_version_binding=version_binding,
        expected_parent_event_sha256=parent_event_sha256,
    )


def measure_u1_prerequisites(
    repo: Path, *, manifest: SourceManifestSnapshot
) -> U1Verification:
    """Measure U1 prerequisites from the host and promoted authority files."""
    if not isinstance(repo, Path):
        raise TypeError("U1 measurement requires a repository path")
    _manifest_parts(manifest, source_manifest_sha256=None)
    repo = repo.resolve()
    skill_root = repo / "skills" / "crossframe-ultra"
    checks = {
        "source_manifest": not validate_committed_source_snapshot(repo).errors,
        "release_manifest": (skill_root / "schemas" / "ultra-release-manifest.schema.json").is_file(),
        "compatibility_matrix": (skill_root / "references" / "compatibility-matrix.json").is_file(),
        "knowledge_closure": (skill_root / "references" / "v8.2-route-map.json").is_file(),
        "skill_tree_hash": manifest.document.get("source_tree_merkle_root") == EXPECTED_TREE_MERKLE_ROOT,
        "fixed_root": skill_root.resolve() == Path(__file__).resolve().parents[2],
        "free_space_reserve": shutil.disk_usage(repo).free > 0,
        "current_user_acl": "unknown",
    }
    verified = tuple(sorted(name for name, result in checks.items() if result is True))
    unknown = tuple(sorted(name for name, result in checks.items() if result == "unknown"))
    return _issue_u1_verification(
        ready=all(checks[name] is True for name in _U1_PREREQUISITES - {"current_user_acl"}),
        verified=verified,
        unknown=unknown,
        repo=repo,
        manifest_sha256=manifest.sha256,
    )


def verify_u1_prerequisites(measurement: object) -> U1Verification:
    if not isinstance(measurement, U1Verification):
        raise SourceLockError("U1 requires a trusted environment measurement attestation")
    try:
        if not isinstance(measurement._repo, Path) or not _is_sha256(measurement._manifest_sha256):
            raise SourceLockError("U1 measurement attestation is malformed")
        authority_path = Path(__file__).resolve().parents[2] / "references" / "source-manifest.json"
        manifest = load_source_manifest(
            authority_path, expected_sha256=measurement._manifest_sha256
        )
        fresh = measure_u1_prerequisites(measurement._repo, manifest=manifest)
    except (AttributeError, OSError, SourceManifestError) as error:
        raise SourceLockError("U1 measurement cannot be verified from the host") from error
    if not fresh.ready:
        raise SourceLockError("U1 environment measurement is not ready")
    return fresh


__all__ = (
    "EXPECTED_PARAGRAPH_COUNT",
    "EXPECTED_SOURCE_UNIT_COUNT",
    "EXPECTED_TABLE_COUNT",
    "READ_EVENT_SCHEMA_ID",
    "ReadCaptureDiagnostic",
    "ReadCoverageAudit",
    "ReadReceipt",
    "SourceCoverageError",
    "SourceLockError",
    "SourceManifestError",
    "SourceManifestSnapshot",
    "U1Verification",
    "build_read_plan",
    "audit_read_capture",
    "capture_authority_read_diagnostic",
    "capture_committed_read_receipts",
    "execution_identity",
    "load_source_manifest",
    "make_read_event",
    "measure_u1_prerequisites",
    "verify_u1_prerequisites",
)
