from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
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

from jsonschema import ValidationError

from check_crossframe_ultra_v82_source import (
    EXPECTED_TREE_MERKLE_ROOT,
    validate_committed_source_snapshot,
)
from check_crossframe_ultra_v82_knowledge import validate_knowledge

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
from .jsonio import canonical_json_bytes
from .paths import (
    PRODUCTION_ROOT,
    RunLayout,
    RunMode,
    RootPolicy,
    assert_safe_descendant,
    build_run_layout,
)
from .schemas import validate_instance


EXPECTED_PARAGRAPH_COUNT = 4_631
EXPECTED_TABLE_COUNT = 122
EXPECTED_SOURCE_UNIT_COUNT = 4_753
MAX_SOURCE_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_U1_AUTHORITY_BYTES = 8 * 1024 * 1024
MIN_FREE_SPACE_RESERVE_BYTES = 1 << 30
READ_EVENT_SCHEMA_ID = "crossframe.ultra.v82.read-event"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_READER_MODES = frozenset({"full-source", "paragraph", "table", "assistive"})
_PERSISTED_U1_SOURCE_LOCK_PATH = Path("recovery/u1-authority/source-lock.json")
_PERSISTED_U1_READ_PLAN_PATH = Path("recovery/u1-authority/read-plan.json")
_PERSISTED_U1_COVERAGE_PATH = Path("recovery/u1-authority/source-coverage.json")
_PERSISTED_U1_READ_EVENTS_PATH = Path(
    "artifacts/U00-U03-evidence/ultra-read-events.jsonl"
)
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
        "source_lock_sha256",
        "parent_event_sha256",
        "receipt_sha256",
        "reader_mode",
        "execution_identity",
        "read_at",
        "read_event_sha256",
    }
)
_PERSISTED_READ_COVERAGE_FIELDS = frozenset(
    {
        "artifact_type",
        "run_id",
        "version_binding",
        "parent_event_sha256",
        "source_lock_sha256",
        "receipt_sha256s",
        "read_event_sha256s",
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
    source_manifest_sha256: str
    content_sha256: str
    receipt_sha256: str
    reader_mode: str
    execution_identity: dict[str, object]
    read_at: str
    run_id: str
    version_binding: dict[str, object]
    source_lock_sha256: str
    parent_event_sha256: str
    _session_token: str
    _issuer_token: str
    _seal_sha256: str

    @property
    def source_unit(self) -> dict[str, object]:
        return copy.deepcopy(self._source_unit)


@dataclass(frozen=True, init=False)
class SourceReadSession:
    _repo: Path
    _manifest_sha256: str
    _manifest_semantic_sha256: str
    _run_id: str
    _version_binding: dict[str, object]
    _source_lock_sha256: str
    _parent_event_sha256: str
    _reader_mode: str
    _read_at: str
    _execution_identity: dict[str, object]
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class ReadCaptureDiagnostic:
    """External diagnostic data only; it never authorizes a phase transition."""

    _events: tuple[dict[str, object], ...]
    _repo: Path
    _receipts: tuple[ReadReceipt, ...]
    _run_id: str
    _version_binding: dict[str, object]
    _parent_event_sha256: str
    _source_lock_sha256: str

    @property
    def events(self) -> tuple[dict[str, object], ...]:
        return tuple(copy.deepcopy(event) for event in self._events)

    @property
    def receipts(self) -> tuple[ReadReceipt, ...]:
        return self._receipts


@dataclass(frozen=True, init=False)
class U1PrerequisiteMeasurement:
    ready: bool
    verified: tuple[str, ...]
    unknown: tuple[str, ...]
    missing: tuple[str, ...]
    run_mode: str
    source_release_id: str | None
    source_manifest_sha256: str
    release_manifest_sha256: str | None
    compatibility_matrix_sha256: str | None
    knowledge_report_sha256: str
    skill_tree_sha256: str | None
    free_space_reserve_bytes: int
    free_space_status: str
    _repo: Path
    _manifest_sha256: str
    _release_manifest_path: Path
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class ReadCoverageAudit:
    total: int
    paragraphs: int
    tables: int
    complete: bool
    authorizes_phase: bool = False
    run_id: str
    version_binding: dict[str, object]
    source_lock_artifact_sha256: str
    parent_event_sha256: str
    artifact_sha256: str
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class SourceLockValidation:
    run_id: str
    version_binding: dict[str, object]
    parent_event_sha256: str
    evidence_cutoff: str
    content_sha256: str
    artifact_sha256: str
    run_mode: str
    acl_status: str
    source_release_id: str
    source_manifest_sha256: str
    release_manifest_sha256: str
    compatibility_matrix_sha256: str
    knowledge_report_sha256: str
    skill_tree_sha256: str
    free_space_reserve_bytes: int
    free_space_status: str
    input_snapshot_sha256: str
    input_artifact_hashes: tuple[str, ...]
    inputs: tuple[dict[str, str], ...]
    input_root: Path
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class U1AuthoritySeal:
    run_id: str
    version_binding: dict[str, object]
    parent_event_sha256: str
    evidence_cutoff: str
    run_mode: str
    source_release_id: str
    source_manifest_sha256: str
    release_manifest_sha256: str
    compatibility_matrix_sha256: str
    knowledge_report_sha256: str
    skill_tree_sha256: str
    free_space_reserve_bytes: int
    free_space_status: str
    input_snapshot_sha256: str
    input_artifact_hashes: tuple[str, ...]
    inputs: tuple[dict[str, str], ...]
    input_root: Path
    acl_status: str
    source_lock_artifact_sha256: str
    read_coverage_artifact_sha256: str
    authorizes_phase: bool
    _issuer_token: str
    _seal_sha256: str


_ISSUED_U1_MEASUREMENTS: dict[str, str] = {}
_ISSUED_SOURCE_LOCK_SEALS: dict[str, str] = {}
_ISSUED_READ_AUDITS: dict[str, str] = {}
_ISSUED_U1_AUTHORITIES: dict[str, str] = {}
_ISSUED_READ_SESSIONS: dict[str, str] = {}
_READ_SESSION_RECORDS: dict[
    str, dict[str, tuple[dict[str, object], dict[str, object], str]]
] = {}
_ISSUED_READ_RECEIPTS: dict[str, str] = {}


def _register_issuer_snapshot(
    registry: dict[str, str], fields: Mapping[str, object]
) -> tuple[str, str]:
    token = hashlib.sha256(os.urandom(32)).hexdigest()
    seal_sha256 = _opaque_seal_sha256(fields)
    registry[token] = seal_sha256
    return token, seal_sha256


def _opaque_seal_sha256(fields: Mapping[str, object]) -> str:
    normalized = {
        key: (str(value.resolve()) if isinstance(value, Path) else value)
        for key, value in fields.items()
    }
    return hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()


def _issue_snapshot(
    document: Mapping[str, object], *, sha256: str, semantic_sha256: str
) -> SourceManifestSnapshot:
    snapshot = object.__new__(SourceManifestSnapshot)
    object.__setattr__(snapshot, "_document", copy.deepcopy(dict(document)))
    object.__setattr__(snapshot, "sha256", sha256)
    object.__setattr__(snapshot, "semantic_sha256", semantic_sha256)
    return snapshot


def _issue_receipt(
    source_unit: Mapping[str, object],
    *,
    record_sha256: str,
    source_manifest_sha256: str,
    reader_mode: str,
    identity: Mapping[str, object],
    read_at: str,
    run_id: str,
    version_binding: Mapping[str, object],
    source_lock_sha256: str,
    parent_event_sha256: str,
    session_token: str = "",
    authorizing: bool = False,
) -> ReadReceipt:
    unit = _validate_source_unit(source_unit)
    payload = {
        "receipt_type": "crossframe.ultra.v82.anchored-source-read",
        "source_unit_id": unit["unit_id"],
        "content_sha256": unit["sha256"],
        "record_sha256": record_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "reader_mode": reader_mode,
        "execution_identity": copy.deepcopy(dict(identity)),
        "read_at": read_at,
        "run_id": run_id,
        "version_binding": copy.deepcopy(dict(version_binding)),
        "source_lock_sha256": source_lock_sha256,
        "parent_event_sha256": parent_event_sha256,
    }
    receipt = object.__new__(ReadReceipt)
    object.__setattr__(receipt, "_source_unit", unit)
    object.__setattr__(receipt, "_record_sha256", record_sha256)
    object.__setattr__(receipt, "source_manifest_sha256", source_manifest_sha256)
    object.__setattr__(receipt, "content_sha256", str(unit["sha256"]))
    object.__setattr__(
        receipt,
        "receipt_sha256",
        hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    )
    object.__setattr__(receipt, "reader_mode", reader_mode)
    object.__setattr__(receipt, "execution_identity", copy.deepcopy(dict(identity)))
    object.__setattr__(receipt, "read_at", read_at)
    object.__setattr__(receipt, "run_id", run_id)
    object.__setattr__(
        receipt, "version_binding", copy.deepcopy(dict(version_binding))
    )
    object.__setattr__(receipt, "source_lock_sha256", source_lock_sha256)
    object.__setattr__(receipt, "parent_event_sha256", parent_event_sha256)
    object.__setattr__(receipt, "_session_token", session_token)
    fields = _receipt_fields(receipt)
    if authorizing:
        token, seal_sha256 = _register_issuer_snapshot(
            _ISSUED_READ_RECEIPTS, fields
        )
    else:
        token, seal_sha256 = "", _opaque_seal_sha256(fields)
    object.__setattr__(receipt, "_issuer_token", token)
    object.__setattr__(receipt, "_seal_sha256", seal_sha256)
    return receipt


def _receipt_fields(receipt: ReadReceipt) -> dict[str, object]:
    return {
        "source_unit": receipt.source_unit,
        "record_sha256": receipt._record_sha256,
        "source_manifest_sha256": receipt.source_manifest_sha256,
        "content_sha256": receipt.content_sha256,
        "receipt_sha256": receipt.receipt_sha256,
        "reader_mode": receipt.reader_mode,
        "execution_identity": copy.deepcopy(receipt.execution_identity),
        "read_at": receipt.read_at,
        "run_id": receipt.run_id,
        "version_binding": copy.deepcopy(receipt.version_binding),
        "source_lock_sha256": receipt.source_lock_sha256,
        "parent_event_sha256": receipt.parent_event_sha256,
        "session_token": receipt._session_token,
    }


def _valid_authorizing_receipt(receipt: object) -> bool:
    if not isinstance(receipt, ReadReceipt):
        return False
    try:
        fields = _receipt_fields(receipt)
        issued = _ISSUED_READ_RECEIPTS.get(receipt._issuer_token)
        payload = {
            "receipt_type": "crossframe.ultra.v82.anchored-source-read",
            "source_unit_id": receipt.source_unit["unit_id"],
            "content_sha256": receipt.content_sha256,
            "record_sha256": receipt._record_sha256,
            "source_manifest_sha256": receipt.source_manifest_sha256,
            "reader_mode": receipt.reader_mode,
            "execution_identity": copy.deepcopy(receipt.execution_identity),
            "read_at": receipt.read_at,
            "run_id": receipt.run_id,
            "version_binding": copy.deepcopy(receipt.version_binding),
            "source_lock_sha256": receipt.source_lock_sha256,
            "parent_event_sha256": receipt.parent_event_sha256,
        }
        return bool(
            issued
            and receipt._seal_sha256 == issued == _opaque_seal_sha256(fields)
            and receipt._session_token in _ISSUED_READ_SESSIONS
            and receipt.receipt_sha256
            == hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def _read_session_fields(session: SourceReadSession) -> dict[str, object]:
    return {
        "repo": session._repo,
        "manifest_sha256": session._manifest_sha256,
        "manifest_semantic_sha256": session._manifest_semantic_sha256,
        "run_id": session._run_id,
        "version_binding": copy.deepcopy(session._version_binding),
        "source_lock_sha256": session._source_lock_sha256,
        "parent_event_sha256": session._parent_event_sha256,
        "reader_mode": session._reader_mode,
        "read_at": session._read_at,
        "execution_identity": copy.deepcopy(session._execution_identity),
    }


def _verify_read_session(session: object) -> SourceReadSession:
    if not isinstance(session, SourceReadSession):
        raise SourceCoverageError("source read session is not host-issued")
    try:
        fields = _read_session_fields(session)
        issued = _ISSUED_READ_SESSIONS.get(session._issuer_token)
        records = _READ_SESSION_RECORDS.get(session._issuer_token)
        if (
            issued is None
            or records is None
            or session._seal_sha256 != issued
            or issued != _opaque_seal_sha256(fields)
        ):
            raise SourceCoverageError("source read session issuer integrity is invalid")
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise SourceCoverageError("source read session issuer integrity is invalid") from error
    _validate_execution_identity(session._execution_identity, require_current=True)
    return session


def _issue_batch(
    events: Sequence[Mapping[str, object]],
    *,
    repo: Path,
    receipts: Sequence[ReadReceipt],
    run_id: str,
    version_binding: Mapping[str, object],
    parent_event_sha256: str,
    source_lock_sha256: str,
) -> ReadCaptureDiagnostic:
    captured = tuple(copy.deepcopy(dict(event)) for event in events)
    batch = object.__new__(ReadCaptureDiagnostic)
    object.__setattr__(batch, "_events", captured)
    object.__setattr__(batch, "_repo", repo.resolve())
    object.__setattr__(batch, "_receipts", tuple(receipts))
    object.__setattr__(batch, "_run_id", run_id)
    object.__setattr__(batch, "_version_binding", copy.deepcopy(dict(version_binding)))
    object.__setattr__(batch, "_parent_event_sha256", parent_event_sha256)
    object.__setattr__(batch, "_source_lock_sha256", source_lock_sha256)
    return batch


def _measurement_fields(measurement: U1PrerequisiteMeasurement) -> dict[str, object]:
    return {
        "ready": measurement.ready,
        "verified": list(measurement.verified),
        "unknown": list(measurement.unknown),
        "missing": list(measurement.missing),
        "run_mode": measurement.run_mode,
        "source_release_id": measurement.source_release_id,
        "source_manifest_sha256": measurement.source_manifest_sha256,
        "release_manifest_sha256": measurement.release_manifest_sha256,
        "compatibility_matrix_sha256": measurement.compatibility_matrix_sha256,
        "knowledge_report_sha256": measurement.knowledge_report_sha256,
        "skill_tree_sha256": measurement.skill_tree_sha256,
        "free_space_reserve_bytes": measurement.free_space_reserve_bytes,
        "free_space_status": measurement.free_space_status,
        "repo": measurement._repo,
        "manifest_sha256": measurement._manifest_sha256,
        "release_manifest_path": measurement._release_manifest_path,
    }


def _issue_u1_measurement(
    *,
    ready: bool,
    verified: Sequence[str],
    unknown: Sequence[str],
    missing: Sequence[str],
    run_mode: str,
    source_release_id: str | None,
    source_manifest_sha256: str,
    release_manifest_sha256: str | None,
    compatibility_matrix_sha256: str | None,
    knowledge_report_sha256: str,
    skill_tree_sha256: str | None,
    free_space_reserve_bytes: int,
    free_space_status: str,
    repo: Path,
    manifest_sha256: str,
    release_manifest_path: Path,
) -> U1PrerequisiteMeasurement:
    result = object.__new__(U1PrerequisiteMeasurement)
    object.__setattr__(result, "ready", ready)
    object.__setattr__(result, "verified", tuple(verified))
    object.__setattr__(result, "unknown", tuple(unknown))
    object.__setattr__(result, "missing", tuple(missing))
    object.__setattr__(result, "run_mode", run_mode)
    object.__setattr__(result, "source_release_id", source_release_id)
    object.__setattr__(result, "source_manifest_sha256", source_manifest_sha256)
    object.__setattr__(result, "release_manifest_sha256", release_manifest_sha256)
    object.__setattr__(
        result, "compatibility_matrix_sha256", compatibility_matrix_sha256
    )
    object.__setattr__(result, "knowledge_report_sha256", knowledge_report_sha256)
    object.__setattr__(result, "skill_tree_sha256", skill_tree_sha256)
    object.__setattr__(result, "free_space_reserve_bytes", free_space_reserve_bytes)
    object.__setattr__(result, "free_space_status", free_space_status)
    object.__setattr__(result, "_repo", repo.resolve())
    object.__setattr__(result, "_manifest_sha256", manifest_sha256)
    object.__setattr__(result, "_release_manifest_path", release_manifest_path.resolve())
    token, seal_sha256 = _register_issuer_snapshot(
        _ISSUED_U1_MEASUREMENTS, _measurement_fields(result)
    )
    object.__setattr__(result, "_issuer_token", token)
    object.__setattr__(result, "_seal_sha256", seal_sha256)
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


def _artifact_content_sha256(artifact: Mapping[str, object]) -> str:
    payload = copy.deepcopy(dict(artifact))
    payload.pop("content_sha256", None)
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _windows_current_user_owns(path: Path) -> bool | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        owner_sid = ctypes.c_void_p()
        security_descriptor = ctypes.c_void_p()
        advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        advapi32.GetNamedSecurityInfoW.argtypes = [
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
        advapi32.OpenProcessToken.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        ]
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.GetTokenInformation.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        advapi32.GetTokenInformation.restype = wintypes.BOOL
        advapi32.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        advapi32.EqualSid.restype = wintypes.BOOL
        result = advapi32.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000001,
            ctypes.byref(owner_sid),
            None,
            None,
            None,
            ctypes.byref(security_descriptor),
        )
        if result != 0 or not owner_sid.value:
            return None
        token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            return None
        try:
            required = wintypes.DWORD()
            advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
            if required.value == 0:
                return None
            buffer = ctypes.create_string_buffer(required.value)
            if not advapi32.GetTokenInformation(
                token, 1, buffer, required, ctypes.byref(required)
            ):
                return None

            class SidAndAttributes(ctypes.Structure):
                _fields_ = [("sid", ctypes.c_void_p), ("attributes", wintypes.DWORD)]

            token_user = ctypes.cast(buffer, ctypes.POINTER(SidAndAttributes)).contents
            return bool(advapi32.EqualSid(owner_sid, token_user.sid))
        finally:
            kernel32.CloseHandle(token)
            if security_descriptor.value:
                kernel32.LocalFree(security_descriptor)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _current_user_owns(path: Path, metadata: os.stat_result) -> bool | None:
    getuid = getattr(os, "getuid", None)
    if callable(getuid):
        try:
            return metadata.st_uid == getuid()
        except (AttributeError, OSError):
            return None
    return _windows_current_user_owns(path)


def measure_current_user_acl(path: Path) -> str:
    """Return a diagnostic ownership/readability result without authorizing a lock."""
    if not isinstance(path, Path):
        raise TypeError("ACL path must be a pathlib.Path")
    try:
        metadata = path.stat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            return "unknown"
    except OSError:
        return "unknown"
    if not os.access(path, os.R_OK):
        return "unknown"
    return (
        "verified-current-user"
        if _current_user_owns(path, metadata) is True
        else "unknown"
    )


def _measure_locked_inputs(
    input_root: Path,
    inputs: Sequence[Mapping[str, object]],
) -> tuple[Path, list[dict[str, str]], tuple[str, ...], str, str]:
    if not isinstance(input_root, Path):
        raise TypeError("input_root must be a pathlib.Path")
    root = input_root.resolve(strict=False)
    if isinstance(inputs, (str, bytes)) or not inputs:
        raise SourceLockError("source lock requires input artifacts")
    normalized: list[dict[str, str]] = []
    acl_verified = True
    for raw in inputs:
        if not isinstance(raw, Mapping) or set(raw) != {"path", "sha256", "media_type"}:
            raise SourceLockError("locked input fields are not closed")
        relative = raw.get("path")
        expected_sha256 = raw.get("sha256")
        media_type = raw.get("media_type")
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise SourceLockError("locked input path must be relative")
        if not _is_sha256(expected_sha256):
            raise SourceLockError("locked input hash is invalid")
        if not isinstance(media_type, str) or "/" not in media_type:
            raise SourceLockError("locked input media type is invalid")
        try:
            candidate = assert_safe_descendant(root, root / Path(relative))
        except (OSError, ValueError) as error:
            raise SourceLockError("locked input path escapes the input root") from error
        try:
            metadata = candidate.stat()
            if candidate.is_symlink() or not stat.S_ISREG(metadata.st_mode):
                raise SourceLockError("locked input is not a regular file")
            payload = candidate.read_bytes()
        except (OSError, PermissionError) as error:
            raise SourceLockError("locked input is missing or unreadable") from error
        if hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise SourceLockError("locked input content hash mismatch")
        if (
            not os.access(candidate, os.R_OK)
            or _current_user_owns(candidate, metadata) is not True
        ):
            acl_verified = False
        normalized.append(
            {
                "path": Path(relative).as_posix(),
                "sha256": str(expected_sha256),
                "media_type": media_type,
            }
        )
    if len({item["path"] for item in normalized}) != len(normalized):
        raise SourceLockError("locked inputs contain duplicate paths")
    input_snapshot_sha256 = hashlib.sha256(canonical_json_bytes(normalized)).hexdigest()
    return (
        root,
        normalized,
        tuple(item["sha256"] for item in normalized),
        input_snapshot_sha256,
        "verified-current-user" if acl_verified else "unknown",
    )


def _validated_run_input_root(
    run_layout: object,
    *,
    run_id: str,
    run_mode: str,
) -> Path:
    if not isinstance(run_layout, RunLayout):
        raise SourceLockError("source lock requires a validated RunLayout authority")
    try:
        mode = RunMode(run_mode)
        policy = (
            RootPolicy(run_layout.root, run_layout.root.parent / "test-control")
            if mode is RunMode.PRODUCTION
            else RootPolicy(PRODUCTION_ROOT, run_layout.root)
        )
        expected = build_run_layout(mode, run_id, policy)
    except (OSError, TypeError, ValueError) as error:
        raise SourceLockError("run layout authority is invalid") from error
    if mode is RunMode.PRODUCTION and run_layout.root != PRODUCTION_ROOT:
        raise SourceLockError("production run layout must use the fixed root")
    if run_layout != expected:
        raise SourceLockError("run layout differs from the canonical run authority")
    try:
        return assert_safe_descendant(
            run_layout.run_dir.resolve(strict=False),
            run_layout.input_dir.resolve(strict=False),
        ).resolve(strict=False)
    except (OSError, TypeError, ValueError) as error:
        raise SourceLockError("run input root escapes the validated layout") from error


def build_source_lock(
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    generated_at: str,
    prerequisite_measurement: U1PrerequisiteMeasurement,
    parent_event_sha256: str,
    evidence_cutoff: str,
    run_layout: RunLayout,
    inputs: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    binding = _validate_read_version_binding(version_binding)
    if not isinstance(run_id, str) or not run_id.strip():
        raise SourceLockError("source lock run_id must be non-empty")
    measurement = verify_u1_prerequisites(prerequisite_measurement)
    if not _is_sha256(parent_event_sha256):
        raise SourceLockError("parent_event_sha256 must be a lowercase SHA-256")
    _parse_read_timestamp(generated_at)
    _parse_read_timestamp(evidence_cutoff)
    input_root = _validated_run_input_root(
        run_layout,
        run_id=run_id,
        run_mode=measurement.run_mode,
    )
    root, normalized_inputs, _input_hashes, input_snapshot_sha256, acl_status = (
        _measure_locked_inputs(input_root, inputs)
    )
    required_roles = {
        "source_release_id": measurement.source_release_id,
        "source_manifest_sha256": measurement.source_manifest_sha256,
        "release_manifest_sha256": measurement.release_manifest_sha256,
        "compatibility_matrix_sha256": measurement.compatibility_matrix_sha256,
        "knowledge_report_sha256": measurement.knowledge_report_sha256,
        "skill_tree_sha256": measurement.skill_tree_sha256,
    }
    if not isinstance(required_roles["source_release_id"], str) or any(
        not _is_sha256(value)
        for name, value in required_roles.items()
        if name != "source_release_id"
    ):
        raise SourceLockError("U1 prerequisite measurement lacks complete authority roles")
    artifact: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.source-lock",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": binding,
        "generated_at": generated_at,
        "phase_id": "U1",
        **required_roles,
        "input_snapshot_sha256": input_snapshot_sha256,
        "parent_event_sha256": parent_event_sha256,
        "evidence_cutoff": evidence_cutoff,
        "acl_status": acl_status,
        "lock_status": "locked",
        "inputs": normalized_inputs,
    }
    artifact["content_sha256"] = _artifact_content_sha256(artifact)
    try:
        validate_instance("ultra-source-lock.schema.json", artifact)
    except ValidationError as error:
        raise SourceLockError(f"source lock violates public schema: {error.message}") from error
    return artifact


def validate_source_lock(
    artifact: Mapping[str, object],
    *,
    prerequisite_measurement: U1PrerequisiteMeasurement,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_parent_event_sha256: str,
    expected_evidence_cutoff: str,
    expected_inputs: Sequence[Mapping[str, object]],
    run_layout: RunLayout,
) -> SourceLockValidation:
    if not isinstance(artifact, Mapping):
        raise SourceLockError("source lock must be an object")
    snapshot = copy.deepcopy(dict(artifact))
    try:
        validate_instance("ultra-source-lock.schema.json", snapshot)
    except ValidationError as error:
        raise SourceLockError(f"source lock violates public schema: {error.message}") from error
    if snapshot.get("content_sha256") != _artifact_content_sha256(snapshot):
        raise SourceLockError("source lock content hash is invalid")
    measurement = verify_u1_prerequisites(prerequisite_measurement)
    binding = _validate_read_version_binding(expected_version_binding)
    input_root = _validated_run_input_root(
        run_layout,
        run_id=expected_run_id,
        run_mode=measurement.run_mode,
    )
    root, normalized_inputs, input_hashes, measured_input_snapshot, measured_acl = (
        _measure_locked_inputs(input_root, expected_inputs)
    )
    measured_roles = {
        "source_release_id": measurement.source_release_id,
        "source_manifest_sha256": measurement.source_manifest_sha256,
        "release_manifest_sha256": measurement.release_manifest_sha256,
        "compatibility_matrix_sha256": measurement.compatibility_matrix_sha256,
        "knowledge_report_sha256": measurement.knowledge_report_sha256,
        "skill_tree_sha256": measurement.skill_tree_sha256,
    }
    if (
        snapshot.get("run_id") != expected_run_id
        or snapshot.get("version_binding") != binding
        or snapshot.get("parent_event_sha256") != expected_parent_event_sha256
        or snapshot.get("evidence_cutoff") != expected_evidence_cutoff
        or snapshot.get("inputs") != normalized_inputs
        or snapshot.get("input_snapshot_sha256") != measured_input_snapshot
        or snapshot.get("acl_status") != measured_acl
    ):
        raise SourceLockError("source lock differs from expected run, parent, or input authority")
    if any(snapshot.get(field) != value for field, value in measured_roles.items()):
        raise SourceLockError("source lock upstream authority differs from expectation")
    seal = object.__new__(SourceLockValidation)
    object.__setattr__(seal, "run_id", expected_run_id)
    object.__setattr__(seal, "version_binding", binding)
    object.__setattr__(seal, "parent_event_sha256", expected_parent_event_sha256)
    object.__setattr__(seal, "evidence_cutoff", expected_evidence_cutoff)
    object.__setattr__(seal, "content_sha256", str(snapshot["content_sha256"]))
    object.__setattr__(seal, "artifact_sha256", hashlib.sha256(canonical_json_bytes(snapshot)).hexdigest())
    object.__setattr__(seal, "run_mode", measurement.run_mode)
    object.__setattr__(seal, "acl_status", str(snapshot["acl_status"]))
    object.__setattr__(seal, "source_release_id", str(snapshot["source_release_id"]))
    object.__setattr__(seal, "source_manifest_sha256", str(snapshot["source_manifest_sha256"]))
    object.__setattr__(seal, "release_manifest_sha256", str(snapshot["release_manifest_sha256"]))
    object.__setattr__(
        seal, "compatibility_matrix_sha256", str(snapshot["compatibility_matrix_sha256"])
    )
    object.__setattr__(seal, "knowledge_report_sha256", str(snapshot["knowledge_report_sha256"]))
    object.__setattr__(seal, "skill_tree_sha256", str(snapshot["skill_tree_sha256"]))
    object.__setattr__(
        seal, "free_space_reserve_bytes", measurement.free_space_reserve_bytes
    )
    object.__setattr__(seal, "free_space_status", measurement.free_space_status)
    object.__setattr__(seal, "input_snapshot_sha256", measured_input_snapshot)
    object.__setattr__(seal, "input_artifact_hashes", input_hashes)
    object.__setattr__(seal, "inputs", tuple(copy.deepcopy(normalized_inputs)))
    object.__setattr__(seal, "input_root", root)
    source_fields = {
        "run_id": seal.run_id,
        "version_binding": seal.version_binding,
        "parent_event_sha256": seal.parent_event_sha256,
        "evidence_cutoff": seal.evidence_cutoff,
        "content_sha256": seal.content_sha256,
        "artifact_sha256": seal.artifact_sha256,
        "run_mode": seal.run_mode,
        "acl_status": seal.acl_status,
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
    }
    token, seal_sha256 = _register_issuer_snapshot(_ISSUED_SOURCE_LOCK_SEALS, source_fields)
    object.__setattr__(seal, "_issuer_token", token)
    object.__setattr__(seal, "_seal_sha256", seal_sha256)
    return seal


def _validate_persisted_source_lock(
    artifact: Mapping[str, object],
    *,
    repo: Path,
    manifest: SourceManifestSnapshot,
    expected_run_id: str,
    expected_run_mode: str,
    expected_version_binding: Mapping[str, object],
    expected_parent_event_sha256: str,
    expected_evidence_cutoff: str,
    expected_inputs: Sequence[Mapping[str, object]],
    run_layout: RunLayout,
) -> str:
    if not isinstance(artifact, Mapping):
        raise SourceLockError("persisted source lock must be an object")
    snapshot = copy.deepcopy(dict(artifact))
    try:
        validate_instance("ultra-source-lock.schema.json", snapshot)
    except ValidationError as error:
        raise SourceLockError(
            f"persisted source lock violates public schema: {error.message}"
        ) from error
    if snapshot.get("content_sha256") != _artifact_content_sha256(snapshot):
        raise SourceLockError("persisted source lock content hash is invalid")
    if expected_run_mode not in {"production", "test"}:
        raise SourceLockError("persisted source lock run mode is invalid")
    binding = _validate_read_version_binding(expected_version_binding)
    input_root = _validated_run_input_root(
        run_layout,
        run_id=expected_run_id,
        run_mode=expected_run_mode,
    )
    _root, normalized_inputs, _input_hashes, measured_snapshot, measured_acl = (
        _measure_locked_inputs(input_root, expected_inputs)
    )
    skill_root = repo.resolve() / "skills" / "crossframe-ultra"
    release_path = skill_root / "references" / "release-manifest.json"
    release_raw = _read_u1_authority_bytes(
        release_path,
        root=release_path.parent.resolve(),
        label="release manifest",
    )
    release_document = _parse_u1_json(release_raw, label="release manifest")
    release_id, declared_tree_sha256 = _validate_release_document(
        release_document,
        manifest=manifest,
        skill_root=skill_root,
    )
    compatibility_sha256 = _measure_compatibility_matrix(skill_root)
    try:
        knowledge_errors = validate_knowledge(repo.resolve())
    except Exception as error:
        knowledge_errors = [f"knowledge validator failed: {error}"]
    knowledge_report_sha256 = hashlib.sha256(
        canonical_json_bytes(
            {
                "valid": not knowledge_errors,
                "framework_revision": FRAMEWORK_REVISION,
                "raw_sha256": FRAMEWORK_RAW_SHA256,
                "semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
                "errors": knowledge_errors,
            }
        )
    ).hexdigest()
    if knowledge_errors:
        raise SourceLockError("persisted source lock knowledge authority is invalid")
    expected_roles = {
        "source_release_id": release_id,
        "source_manifest_sha256": manifest.sha256,
        "release_manifest_sha256": hashlib.sha256(release_raw).hexdigest(),
        "compatibility_matrix_sha256": compatibility_sha256,
        "knowledge_report_sha256": knowledge_report_sha256,
        "skill_tree_sha256": declared_tree_sha256,
    }
    if (
        snapshot.get("run_id") != expected_run_id
        or snapshot.get("version_binding") != binding
        or snapshot.get("parent_event_sha256") != expected_parent_event_sha256
        or snapshot.get("evidence_cutoff") != expected_evidence_cutoff
        or snapshot.get("inputs") != normalized_inputs
        or snapshot.get("input_snapshot_sha256") != measured_snapshot
        or snapshot.get("acl_status") != measured_acl
        or snapshot.get("lock_status") != "locked"
        or any(snapshot.get(field) != value for field, value in expected_roles.items())
    ):
        raise SourceLockError("persisted source lock differs from disk authority")
    return hashlib.sha256(canonical_json_bytes(snapshot)).hexdigest()


def _valid_source_lock_seal(seal: object) -> bool:
    if not isinstance(seal, SourceLockValidation):
        return False
    fields = {
        "run_id": seal.run_id,
        "version_binding": seal.version_binding,
        "parent_event_sha256": seal.parent_event_sha256,
        "evidence_cutoff": seal.evidence_cutoff,
        "content_sha256": seal.content_sha256,
        "artifact_sha256": seal.artifact_sha256,
        "run_mode": seal.run_mode,
        "acl_status": seal.acl_status,
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
    }
    issued = _ISSUED_SOURCE_LOCK_SEALS.get(getattr(seal, "_issuer_token", ""))
    computed = _opaque_seal_sha256(fields)
    return issued is not None and seal._seal_sha256 == issued == computed


def _valid_read_audit_seal(seal: object) -> bool:
    if not isinstance(seal, ReadCoverageAudit):
        return False
    fields = {
        "total": seal.total,
        "paragraphs": seal.paragraphs,
        "tables": seal.tables,
        "complete": seal.complete,
        "authorizes_phase": seal.authorizes_phase,
        "run_id": seal.run_id,
        "version_binding": seal.version_binding,
        "source_lock_artifact_sha256": seal.source_lock_artifact_sha256,
        "parent_event_sha256": seal.parent_event_sha256,
        "artifact_sha256": seal.artifact_sha256,
    }
    issued = _ISSUED_READ_AUDITS.get(getattr(seal, "_issuer_token", ""))
    computed = _opaque_seal_sha256(fields)
    return issued is not None and seal._seal_sha256 == issued == computed


def validate_u1_authority(
    source_lock: SourceLockValidation,
    read_audit: ReadCoverageAudit,
) -> U1AuthoritySeal:
    if not _valid_source_lock_seal(source_lock) or not _valid_read_audit_seal(read_audit):
        raise SourceLockError("U1 authority requires sealed source lock and read audit")
    if (
        not read_audit.complete
        or not read_audit.authorizes_phase
        or source_lock.run_id != read_audit.run_id
        or source_lock.version_binding != read_audit.version_binding
        or source_lock.parent_event_sha256 != read_audit.parent_event_sha256
        or source_lock.artifact_sha256 != read_audit.source_lock_artifact_sha256
    ):
        raise SourceLockError("U1 source/read authority boundary mismatch")
    seal = object.__new__(U1AuthoritySeal)
    object.__setattr__(seal, "run_id", source_lock.run_id)
    object.__setattr__(seal, "version_binding", copy.deepcopy(source_lock.version_binding))
    object.__setattr__(seal, "parent_event_sha256", source_lock.parent_event_sha256)
    object.__setattr__(seal, "evidence_cutoff", source_lock.evidence_cutoff)
    object.__setattr__(seal, "run_mode", source_lock.run_mode)
    object.__setattr__(seal, "source_release_id", source_lock.source_release_id)
    object.__setattr__(seal, "source_manifest_sha256", source_lock.source_manifest_sha256)
    object.__setattr__(seal, "release_manifest_sha256", source_lock.release_manifest_sha256)
    object.__setattr__(
        seal, "compatibility_matrix_sha256", source_lock.compatibility_matrix_sha256
    )
    object.__setattr__(seal, "knowledge_report_sha256", source_lock.knowledge_report_sha256)
    object.__setattr__(seal, "skill_tree_sha256", source_lock.skill_tree_sha256)
    object.__setattr__(
        seal, "free_space_reserve_bytes", source_lock.free_space_reserve_bytes
    )
    object.__setattr__(seal, "free_space_status", source_lock.free_space_status)
    object.__setattr__(seal, "input_snapshot_sha256", source_lock.input_snapshot_sha256)
    object.__setattr__(seal, "input_artifact_hashes", source_lock.input_artifact_hashes)
    object.__setattr__(seal, "inputs", tuple(copy.deepcopy(source_lock.inputs)))
    object.__setattr__(seal, "input_root", source_lock.input_root)
    object.__setattr__(seal, "acl_status", source_lock.acl_status)
    object.__setattr__(seal, "source_lock_artifact_sha256", source_lock.artifact_sha256)
    object.__setattr__(seal, "read_coverage_artifact_sha256", read_audit.artifact_sha256)
    object.__setattr__(seal, "authorizes_phase", True)
    authority_fields = {
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
    token, seal_sha256 = _register_issuer_snapshot(_ISSUED_U1_AUTHORITIES, authority_fields)
    object.__setattr__(seal, "_issuer_token", token)
    object.__setattr__(seal, "_seal_sha256", seal_sha256)
    return seal


def verify_u1_authority_seal(seal: object) -> U1AuthoritySeal:
    if not isinstance(seal, U1AuthoritySeal):
        raise SourceLockError("U1 authority seal is not issuer-produced")
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
    issued = _ISSUED_U1_AUTHORITIES.get(getattr(seal, "_issuer_token", ""))
    if issued is None or seal._seal_sha256 != issued or issued != _opaque_seal_sha256(fields):
        raise SourceLockError("U1 authority seal integrity is invalid")
    return seal


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
    source_lock_sha256: str | None = None,
    parent_event_sha256: str | None = None,
) -> dict[str, object]:
    if not _is_sha256(promoted_semantic_snapshot_sha256):
        raise SourceManifestError("promoted semantic snapshot hash is invalid")
    document, units, manifest_hash, manifest_semantic = _manifest_parts(
        manifest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if manifest_semantic != promoted_semantic_snapshot_sha256:
        raise SourceManifestError("promoted semantic snapshot differs from the manifest")
    plan = {
        "source_manifest_sha256": manifest_hash,
        "promoted_semantic_snapshot_sha256": promoted_semantic_snapshot_sha256,
        "source_unit_count": document["source_unit_count"],
        "paragraph_count": document["paragraph_count"],
        "table_count": document["table_count"],
        "source_unit_ids": [str(unit["unit_id"]) for unit in units],
        "source_units": copy.deepcopy(list(units)),
    }
    if source_lock_sha256 is not None:
        if not _is_sha256(source_lock_sha256):
            raise SourceManifestError("source lock hash is invalid")
        plan["source_lock_sha256"] = source_lock_sha256
    if parent_event_sha256 is not None:
        if not _is_sha256(parent_event_sha256):
            raise SourceManifestError("read plan parent hash is invalid")
        plan["parent_event_sha256"] = parent_event_sha256
    return plan


def _load_committed_read_records(
    repo: Path,
    *,
    manifest: SourceManifestSnapshot,
) -> dict[str, tuple[dict[str, object], dict[str, object], str]]:
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
    records: dict[str, tuple[dict[str, object], dict[str, object], str]] = {}
    for record in tuple(committed.paragraphs) + tuple(committed.tables):
        unit = units.get(str(record.get("anchor")))
        if unit is None:
            raise SourceCoverageError("anchored source read produced an unknown source unit")
        record_payload = dict(record)
        content_payload = {"kind": unit["kind"], **record_payload}
        if hashlib.sha256(canonical_json_bytes(content_payload)).hexdigest() != unit["sha256"]:
            raise SourceCoverageError("anchored source body differs from the manifest content hash")
        record_sha256 = hashlib.sha256(canonical_json_bytes(record_payload)).hexdigest()
        unit_id = str(unit["unit_id"])
        if unit_id in records:
            raise SourceCoverageError("anchored source contains duplicate unit bodies")
        records[unit_id] = (copy.deepcopy(unit), record_payload, record_sha256)
    if len(records) != EXPECTED_SOURCE_UNIT_COUNT or set(records) != set(units):
        raise SourceCoverageError("anchored source read did not cover every source unit")
    return records


def open_source_read_session(
    repo: Path,
    *,
    manifest: SourceManifestSnapshot,
    run_id: str,
    version_binding: Mapping[str, object],
    source_lock_sha256: str,
    parent_event_sha256: str,
    reader_mode: str = "full-source",
    read_at: str | None = None,
) -> SourceReadSession:
    """Open a host-bound read session without minting receipts or read events."""
    _manifest_parts(manifest, source_manifest_sha256=None)
    if not isinstance(run_id, str) or not run_id.strip():
        raise SourceCoverageError("run_id must be non-empty")
    binding = _validate_read_version_binding(version_binding)
    if not _is_sha256(source_lock_sha256) or not _is_sha256(parent_event_sha256):
        raise SourceCoverageError("read session source lock or parent authority is invalid")
    if reader_mode not in _READER_MODES:
        raise SourceCoverageError("reader mode is invalid")
    timestamp = read_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    _parse_read_timestamp(timestamp)
    identity = _validate_execution_identity(execution_identity(), require_current=True)
    records = _load_committed_read_records(repo, manifest=manifest)
    session = object.__new__(SourceReadSession)
    object.__setattr__(session, "_repo", repo.resolve())
    object.__setattr__(session, "_manifest_sha256", manifest.sha256)
    object.__setattr__(
        session, "_manifest_semantic_sha256", manifest.semantic_sha256
    )
    object.__setattr__(session, "_run_id", run_id)
    object.__setattr__(session, "_version_binding", binding)
    object.__setattr__(session, "_source_lock_sha256", source_lock_sha256)
    object.__setattr__(session, "_parent_event_sha256", parent_event_sha256)
    object.__setattr__(session, "_reader_mode", reader_mode)
    object.__setattr__(session, "_read_at", timestamp)
    object.__setattr__(session, "_execution_identity", identity)
    token, seal_sha256 = _register_issuer_snapshot(
        _ISSUED_READ_SESSIONS, _read_session_fields(session)
    )
    object.__setattr__(session, "_issuer_token", token)
    object.__setattr__(session, "_seal_sha256", seal_sha256)
    _READ_SESSION_RECORDS[token] = records
    return session


def capture_source_unit_read(
    session: SourceReadSession,
    source_unit_id: str,
) -> tuple[dict[str, object], ReadReceipt]:
    verified = _verify_read_session(session)
    if not isinstance(source_unit_id, str) or not source_unit_id:
        raise SourceCoverageError("source_unit_id must be non-empty")
    record_entry = _READ_SESSION_RECORDS[verified._issuer_token].get(source_unit_id)
    if record_entry is None:
        raise SourceCoverageError("source read requested an unknown source unit")
    unit, record, record_sha256 = record_entry
    receipt = _issue_receipt(
        unit,
        record_sha256=record_sha256,
        source_manifest_sha256=verified._manifest_sha256,
        reader_mode=verified._reader_mode,
        identity=verified._execution_identity,
        read_at=verified._read_at,
        run_id=verified._run_id,
        version_binding=verified._version_binding,
        source_lock_sha256=verified._source_lock_sha256,
        parent_event_sha256=verified._parent_event_sha256,
        session_token=verified._issuer_token,
        authorizing=True,
    )
    return copy.deepcopy(record), receipt


def _capture_committed_read_receipts(
    repo: Path,
    *,
    manifest: SourceManifestSnapshot,
    run_id: str,
    version_binding: Mapping[str, object],
    source_lock_sha256: str,
    parent_event_sha256: str,
    reader_mode: str = "full-source",
    read_at: str | None = None,
) -> tuple[ReadReceipt, ...]:
    """Bulk diagnostic only; these receipts are intentionally non-authorizing."""
    binding = _validate_read_version_binding(version_binding)
    if reader_mode not in _READER_MODES:
        raise SourceCoverageError("reader mode is invalid")
    timestamp = read_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    _parse_read_timestamp(timestamp)
    identity = _validate_execution_identity(execution_identity(), require_current=True)
    records = _load_committed_read_records(repo, manifest=manifest)
    receipts = tuple(
        _issue_receipt(
            unit,
            record_sha256=record_sha256,
            source_manifest_sha256=manifest.sha256,
            reader_mode=reader_mode,
            identity=identity,
            read_at=timestamp,
            run_id=run_id,
            version_binding=binding,
            source_lock_sha256=source_lock_sha256,
            parent_event_sha256=parent_event_sha256,
        )
        for unit, _record, record_sha256 in records.values()
    )
    if len(receipts) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("diagnostic source read did not cover every source unit")
    return receipts


def capture_authority_read_diagnostic(
    repo: Path,
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    manifest: SourceManifestSnapshot,
    source_lock_sha256: str,
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
    if not _is_sha256(source_lock_sha256):
        raise SourceCoverageError("read capture source lock is invalid")
    receipts = _capture_committed_read_receipts(
        repo,
        manifest=manifest,
        run_id=run_id,
        version_binding=binding,
        source_lock_sha256=source_lock_sha256,
        parent_event_sha256=parent_event_sha256,
        reader_mode=reader_mode,
        read_at=read_at,
    )
    events = [
        make_read_event(
            run_id=run_id,
            version_binding=binding,
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            source_lock_sha256=source_lock_sha256,
            parent_event_sha256=parent_event_sha256,
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
        source_lock_sha256=source_lock_sha256,
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
        encoded = canonical_json_bytes(payload)
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
    source_lock_sha256: str,
    parent_event_sha256: str,
    receipt: ReadReceipt,
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
    if not _is_sha256(source_lock_sha256) or not _is_sha256(parent_event_sha256):
        raise SourceCoverageError("read event source lock or parent authority is invalid")
    if (
        not isinstance(receipt, ReadReceipt)
        or receipt.source_unit != unit
        or receipt.source_manifest_sha256 != source_manifest_sha256
        or receipt.content_sha256 != unit["sha256"]
    ):
        raise SourceCoverageError("trusted read receipt does not bind this source read")
    identity = _validate_execution_identity(receipt.execution_identity, require_current=True)
    _parse_read_timestamp(receipt.read_at)
    event: dict[str, object] = {
        "schema_id": READ_EVENT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": binding,
        "generated_at": receipt.read_at,
        "phase_id": "U1",
        "source_unit_id": unit["unit_id"],
        "source_kind": unit["kind"],
        "source_ordinal": unit["ordinal"],
        "content_sha256": unit["sha256"],
        "source_manifest_sha256": source_manifest_sha256,
        "promoted_semantic_snapshot_sha256": promoted_semantic_snapshot_sha256,
        "source_lock_sha256": source_lock_sha256,
        "parent_event_sha256": parent_event_sha256,
        "receipt_sha256": receipt.receipt_sha256,
        "reader_mode": receipt.reader_mode,
        "execution_identity": identity,
        "read_at": receipt.read_at,
    }
    event["read_event_sha256"] = _read_event_sha256(event)
    try:
        validate_instance("ultra-read-event.schema.json", event)
    except ValidationError as error:
        raise SourceCoverageError(f"read event violates public schema: {error.message}") from error
    return event


@lru_cache(maxsize=1)
def _authority_manifest_sha256() -> str | None:
    path = Path(__file__).resolve().parents[2] / "references" / "source-manifest.json"
    try:
        return hashlib.sha256(_read_regular_bounded(path)).hexdigest()
    except (OSError, SourceManifestError):
        return None


def audit_read_capture(
    events: Sequence[Mapping[str, object]],
    manifest: SourceManifestSnapshot,
    *,
    receipts: Sequence[ReadReceipt],
    promoted_semantic_snapshot_sha256: str,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_source_lock_sha256: str,
    expected_parent_event_sha256: str,
    source_manifest_sha256: str | None = None,
) -> ReadCoverageAudit:
    """Audit external read events against independently issued one-unit receipts."""
    if isinstance(events, ReadCaptureDiagnostic) or isinstance(events, (str, bytes)):
        raise SourceCoverageError("read audit requires external events, not a diagnostic")
    if isinstance(receipts, (str, bytes)):
        raise SourceCoverageError("read audit receipts must be a sequence")
    event_snapshots = tuple(events)
    receipt_snapshots = tuple(receipts)
    if len(receipt_snapshots) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("read batch must contain exactly 4,753 trusted receipts")
    expected_binding = _validate_read_version_binding(expected_version_binding)
    if not isinstance(expected_run_id, str) or not expected_run_id.strip():
        raise SourceCoverageError("expected read run_id is invalid")
    if not _is_sha256(expected_parent_event_sha256) or not _is_sha256(expected_source_lock_sha256):
        raise SourceCoverageError("expected read source lock or parent boundary is invalid")
    _document, units, manifest_hash, manifest_semantic = _manifest_parts(
        manifest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if not _is_sha256(promoted_semantic_snapshot_sha256):
        raise SourceCoverageError("semantic snapshot hash is invalid")
    if manifest_semantic != promoted_semantic_snapshot_sha256:
        raise SourceCoverageError("semantic snapshot differs from the manifest")
    known_unit_ids = {str(unit["unit_id"]) for unit in units}
    receipt_unit_ids: list[str] = []
    session_tokens: set[str] = set()
    for receipt in receipt_snapshots:
        if not _valid_authorizing_receipt(receipt):
            raise SourceCoverageError(
                "read batch requires independently issued one-unit receipts"
            )
        assert isinstance(receipt, ReadReceipt)
        try:
            unit_id = str(receipt.source_unit["unit_id"])
        except (AttributeError, KeyError, TypeError) as error:
            raise SourceCoverageError("read receipt does not resolve a known unit") from error
        if unit_id not in known_unit_ids:
            raise SourceCoverageError("read receipt resolves an unknown source unit")
        if (
            receipt.run_id != expected_run_id
            or receipt.version_binding != expected_binding
            or receipt.source_lock_sha256 != expected_source_lock_sha256
            or receipt.parent_event_sha256 != expected_parent_event_sha256
            or receipt.source_manifest_sha256 != manifest_hash
        ):
            raise SourceCoverageError("read receipt upstream authority differs")
        session_tokens.add(receipt._session_token)
        receipt_unit_ids.append(unit_id)
    if len(set(receipt_unit_ids)) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("read receipts contain a duplicate source unit")
    if len(session_tokens) != 1:
        raise SourceCoverageError("read receipts cross host read sessions")
    session_token = next(iter(session_tokens))
    session_records = _READ_SESSION_RECORDS.get(session_token)
    if session_records is None:
        raise SourceCoverageError("read receipt session authority is unavailable")
    captured_receipts = {
        str(receipt.source_unit["unit_id"]): receipt
        for receipt in receipt_snapshots
        if isinstance(receipt, ReadReceipt)
    }
    if len(captured_receipts) != EXPECTED_SOURCE_UNIT_COUNT or any(
        unit_id not in session_records
        or receipt._record_sha256 != session_records[unit_id][2]
        or receipt.content_sha256 != session_records[unit_id][0]["sha256"]
        for unit_id, receipt in captured_receipts.items()
    ) or set(captured_receipts) != set(session_records):
        raise SourceCoverageError("read batch does not match its host read session")
    if len(event_snapshots) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("read event count is not exactly 4,753")
    expected = {str(unit["unit_id"]): unit for unit in units}
    seen: set[str] = set()
    run_id: str | None = None
    batch_binding: dict[str, object] | None = None
    for raw_event in event_snapshots:
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
        if event.get("source_lock_sha256") != expected_source_lock_sha256:
            raise SourceCoverageError("read event source lock authority differs")
        if event.get("parent_event_sha256") != expected_parent_event_sha256:
            raise SourceCoverageError("read event parent authority differs")
        if (
            event.get("promoted_semantic_snapshot_sha256")
            != promoted_semantic_snapshot_sha256
        ):
            raise SourceCoverageError("read event semantic snapshot differs")
        if event.get("reader_mode") not in _READER_MODES:
            raise SourceCoverageError("read event reader mode is invalid")
        receipt = captured_receipts[unit_id]
        if event.get("receipt_sha256") != receipt.receipt_sha256:
            raise SourceCoverageError("read event receipt differs from trusted source capture")
        if event.get("reader_mode") != receipt.reader_mode:
            raise SourceCoverageError("read event reader mode differs from receipt")
        if event.get("execution_identity") != receipt.execution_identity:
            raise SourceCoverageError("read event identity differs from receipt")
        if event.get("read_at") != receipt.read_at:
            raise SourceCoverageError("read event timestamp differs from receipt")
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
    complete = (
        len(seen) == EXPECTED_SOURCE_UNIT_COUNT
        and paragraphs == EXPECTED_PARAGRAPH_COUNT
        and tables == EXPECTED_TABLE_COUNT
    )
    artifact_sha256 = _coverage_artifact_sha256(
        event_snapshots,
        receipt_snapshots,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_binding,
        expected_parent_event_sha256=expected_parent_event_sha256,
        expected_source_lock_sha256=expected_source_lock_sha256,
    )
    audit = object.__new__(ReadCoverageAudit)
    object.__setattr__(audit, "total", len(seen))
    object.__setattr__(audit, "paragraphs", paragraphs)
    object.__setattr__(audit, "tables", tables)
    object.__setattr__(audit, "complete", complete)
    object.__setattr__(audit, "authorizes_phase", True)
    object.__setattr__(audit, "run_id", expected_run_id)
    object.__setattr__(audit, "version_binding", expected_binding)
    object.__setattr__(audit, "source_lock_artifact_sha256", expected_source_lock_sha256)
    object.__setattr__(audit, "parent_event_sha256", expected_parent_event_sha256)
    object.__setattr__(audit, "artifact_sha256", artifact_sha256)
    fields = {
        "total": audit.total,
        "paragraphs": audit.paragraphs,
        "tables": audit.tables,
        "complete": audit.complete,
        "authorizes_phase": audit.authorizes_phase,
        "run_id": audit.run_id,
        "version_binding": audit.version_binding,
        "source_lock_artifact_sha256": audit.source_lock_artifact_sha256,
        "parent_event_sha256": audit.parent_event_sha256,
        "artifact_sha256": audit.artifact_sha256,
    }
    token, seal_sha256 = _register_issuer_snapshot(_ISSUED_READ_AUDITS, fields)
    object.__setattr__(audit, "_issuer_token", token)
    object.__setattr__(audit, "_seal_sha256", seal_sha256)
    return audit


def _validate_persisted_read_capture(
    events: Sequence[Mapping[str, object]],
    manifest: SourceManifestSnapshot,
    *,
    repo: Path,
    coverage: Mapping[str, object],
    promoted_semantic_snapshot_sha256: str,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_source_lock_sha256: str,
    expected_parent_event_sha256: str,
    source_manifest_sha256: str | None = None,
) -> None:
    if isinstance(events, (str, bytes)):
        raise SourceCoverageError("persisted read events must be a sequence")
    if not isinstance(coverage, Mapping):
        raise SourceCoverageError("persisted read coverage must be an object")
    coverage_snapshot = copy.deepcopy(dict(coverage))
    if frozenset(coverage_snapshot) != _PERSISTED_READ_COVERAGE_FIELDS:
        raise SourceCoverageError("persisted read coverage fields are incomplete")
    expected_binding = _validate_read_version_binding(expected_version_binding)
    if not isinstance(expected_run_id, str) or not expected_run_id.strip():
        raise SourceCoverageError("expected read run_id is invalid")
    if not _is_sha256(expected_parent_event_sha256) or not _is_sha256(
        expected_source_lock_sha256
    ):
        raise SourceCoverageError(
            "expected read source lock or parent boundary is invalid"
        )
    _document, units, manifest_hash, manifest_semantic = _manifest_parts(
        manifest,
        source_manifest_sha256=source_manifest_sha256,
    )
    if manifest_semantic != promoted_semantic_snapshot_sha256:
        raise SourceCoverageError("semantic snapshot differs from the manifest")
    event_snapshots = tuple(events)
    if len(event_snapshots) != EXPECTED_SOURCE_UNIT_COUNT:
        raise SourceCoverageError("read event count is not exactly 4,753")
    raw_receipt_hashes = coverage_snapshot.get("receipt_sha256s")
    raw_event_hashes = coverage_snapshot.get("read_event_sha256s")
    if (
        coverage_snapshot.get("artifact_type")
        != "crossframe.ultra.v82.u1-source-coverage"
        or coverage_snapshot.get("run_id") != expected_run_id
        or coverage_snapshot.get("version_binding") != expected_binding
        or coverage_snapshot.get("parent_event_sha256")
        != expected_parent_event_sha256
        or coverage_snapshot.get("source_lock_sha256")
        != expected_source_lock_sha256
        or not isinstance(raw_receipt_hashes, list)
        or not isinstance(raw_event_hashes, list)
        or len(raw_receipt_hashes) != EXPECTED_SOURCE_UNIT_COUNT
        or len(raw_event_hashes) != EXPECTED_SOURCE_UNIT_COUNT
        or any(not _is_sha256(value) for value in raw_receipt_hashes)
        or any(not _is_sha256(value) for value in raw_event_hashes)
        or len(set(raw_receipt_hashes)) != EXPECTED_SOURCE_UNIT_COUNT
        or len(set(raw_event_hashes)) != EXPECTED_SOURCE_UNIT_COUNT
    ):
        raise SourceCoverageError("persisted read coverage authority is invalid")

    expected_units = {str(unit["unit_id"]): unit for unit in units}
    committed = _load_committed_read_records(repo, manifest=manifest)
    seen: set[str] = set()
    for ordinal, raw_event in enumerate(event_snapshots):
        if not isinstance(raw_event, Mapping):
            raise SourceCoverageError("read event must be an object")
        event = copy.deepcopy(dict(raw_event))
        if frozenset(event) != _READ_EVENT_FIELDS:
            raise SourceCoverageError("read event fields do not match the closed contract")
        try:
            validate_instance("ultra-read-event.schema.json", event)
        except ValidationError as error:
            raise SourceCoverageError(
                f"read event violates public schema: {error.message}"
            ) from error
        if (
            event.get("schema_id") != READ_EVENT_SCHEMA_ID
            or event.get("schema_version") != 1
            or event.get("phase_id") != "U1"
            or event.get("generated_at") != event.get("read_at")
            or event.get("run_id") != expected_run_id
            or _validate_read_version_binding(event.get("version_binding"))
            != expected_binding
            or event.get("source_manifest_sha256") != manifest_hash
            or event.get("promoted_semantic_snapshot_sha256")
            != promoted_semantic_snapshot_sha256
            or event.get("source_lock_sha256") != expected_source_lock_sha256
            or event.get("parent_event_sha256") != expected_parent_event_sha256
        ):
            raise SourceCoverageError("read event upstream authority differs")
        event_hash = event.get("read_event_sha256")
        if not _is_sha256(event_hash) or event_hash != _read_event_sha256(event):
            raise SourceCoverageError("read event hash is invalid")
        unit_id = event.get("source_unit_id")
        if not isinstance(unit_id, str) or unit_id not in expected_units:
            raise SourceCoverageError("read event references an unknown source unit")
        if unit_id in seen:
            raise SourceCoverageError("duplicate source-unit read event")
        seen.add(unit_id)
        unit = expected_units[unit_id]
        if (
            event.get("source_kind") != unit["kind"]
            or event.get("source_ordinal") != unit["ordinal"]
        ):
            raise SourceCoverageError("read event source kind or ordinal differs")
        if event.get("content_sha256") != unit["sha256"]:
            raise SourceCoverageError(
                "read event content hash differs from the manifest"
            )
        if raw_event_hashes[ordinal] != event_hash:
            raise SourceCoverageError("read event differs from persisted coverage")
        if event.get("reader_mode") not in _READER_MODES:
            raise SourceCoverageError("read event reader mode is invalid")
        identity = _validate_execution_identity(
            event.get("execution_identity"), require_current=False
        )
        _parse_read_timestamp(event.get("read_at"))
        record_sha256 = committed[unit_id][2]
        receipt_payload = {
            "receipt_type": "crossframe.ultra.v82.anchored-source-read",
            "source_unit_id": unit_id,
            "content_sha256": unit["sha256"],
            "record_sha256": record_sha256,
            "source_manifest_sha256": manifest_hash,
            "reader_mode": event["reader_mode"],
            "execution_identity": identity,
            "read_at": event["read_at"],
            "run_id": expected_run_id,
            "version_binding": expected_binding,
            "source_lock_sha256": expected_source_lock_sha256,
            "parent_event_sha256": expected_parent_event_sha256,
        }
        expected_receipt = hashlib.sha256(
            canonical_json_bytes(receipt_payload)
        ).hexdigest()
        if (
            event.get("receipt_sha256") != expected_receipt
            or raw_receipt_hashes[ordinal] != expected_receipt
        ):
            raise SourceCoverageError(
                "read event receipt differs from committed source capture"
            )
    if seen != set(expected_units):
        raise SourceCoverageError("read events do not cover every source unit")


def _read_persisted_u1_object(
    run_layout: RunLayout,
    relative: Path,
    provided: Mapping[str, object],
    *,
    label: str,
) -> tuple[dict[str, object], bytes]:
    if not isinstance(provided, Mapping):
        raise SourceLockError(f"{label} must be an object")
    path = run_layout.run_dir / relative
    raw = _read_u1_authority_bytes(
        path,
        root=run_layout.run_dir.resolve(strict=False),
        label=label,
    )
    snapshot = _parse_u1_json(raw, label=label)
    try:
        provided_raw = canonical_json_bytes(provided)
    except (TypeError, ValueError) as error:
        raise SourceLockError(f"{label} witness is not canonical JSON") from error
    if raw != canonical_json_bytes(snapshot) or provided_raw != raw:
        raise SourceLockError(f"{label} differs from canonical fresh disk bytes")
    return snapshot, raw


def _read_persisted_u1_events(
    run_layout: RunLayout,
    provided: Sequence[Mapping[str, object]],
) -> tuple[tuple[dict[str, object], ...], bytes]:
    if isinstance(provided, (str, bytes)) or not isinstance(provided, Sequence):
        raise SourceCoverageError("persisted read events must be a sequence")
    raw = _read_u1_authority_bytes(
        run_layout.run_dir / _PERSISTED_U1_READ_EVENTS_PATH,
        root=run_layout.run_dir.resolve(strict=False),
        label="persisted read events",
    )
    if not raw or not raw.endswith(b"\n"):
        raise SourceCoverageError("persisted read event journal is incomplete")
    disk_events: list[dict[str, object]] = []
    for ordinal, row in enumerate(raw.splitlines(keepends=True), start=1):
        try:
            event = _parse_u1_json(row, label=f"persisted read event {ordinal}")
        except SourceLockError as error:
            raise SourceCoverageError(str(error)) from error
        if row != canonical_json_bytes(event):
            raise SourceCoverageError("persisted read event bytes are not canonical")
        disk_events.append(event)
    try:
        provided_raw = b"".join(canonical_json_bytes(event) for event in provided)
    except (TypeError, ValueError) as error:
        raise SourceCoverageError(
            "persisted read event witness is not canonical JSON"
        ) from error
    if provided_raw != raw:
        raise SourceCoverageError("persisted read events differ from fresh disk bytes")
    return tuple(disk_events), raw


def _validate_persisted_u1_authority(
    *,
    repo: Path,
    run_layout: RunLayout,
    manifest: SourceManifestSnapshot,
    source_lock: Mapping[str, object],
    read_plan: Mapping[str, object],
    coverage: Mapping[str, object],
    read_events: Sequence[Mapping[str, object]],
    expected_run_id: str,
    expected_run_mode: str,
    expected_version_binding: Mapping[str, object],
    expected_parent_event_sha256: str,
    expected_evidence_cutoff: str,
    expected_inputs: Sequence[Mapping[str, object]],
    expected_source_lock_sha256: str,
    expected_read_coverage_sha256: str,
) -> U1AuthoritySeal:
    if not isinstance(repo, Path):
        raise TypeError("repo must be a pathlib.Path")
    if not isinstance(run_layout, RunLayout):
        raise TypeError("run_layout must be a RunLayout")
    if not isinstance(manifest, SourceManifestSnapshot):
        raise TypeError("manifest must be a sealed SourceManifestSnapshot")
    if not _is_sha256(expected_source_lock_sha256) or not _is_sha256(
        expected_read_coverage_sha256
    ):
        raise SourceLockError("persisted U1 checkpoint hashes are invalid")

    source_lock_snapshot, source_lock_raw = _read_persisted_u1_object(
        run_layout,
        _PERSISTED_U1_SOURCE_LOCK_PATH,
        source_lock,
        label="persisted source lock",
    )
    read_plan_snapshot, read_plan_raw = _read_persisted_u1_object(
        run_layout,
        _PERSISTED_U1_READ_PLAN_PATH,
        read_plan,
        label="persisted read plan",
    )
    coverage_snapshot, coverage_raw = _read_persisted_u1_object(
        run_layout,
        _PERSISTED_U1_COVERAGE_PATH,
        coverage,
        label="persisted read coverage",
    )
    event_snapshots, _read_events_raw = _read_persisted_u1_events(
        run_layout,
        read_events,
    )

    binding = _validate_read_version_binding(expected_version_binding)
    source_lock_sha256 = _validate_persisted_source_lock(
        source_lock_snapshot,
        repo=repo,
        manifest=manifest,
        expected_run_id=expected_run_id,
        expected_run_mode=expected_run_mode,
        expected_version_binding=binding,
        expected_parent_event_sha256=expected_parent_event_sha256,
        expected_evidence_cutoff=expected_evidence_cutoff,
        expected_inputs=expected_inputs,
        run_layout=run_layout,
    )
    if (
        source_lock_sha256 != hashlib.sha256(source_lock_raw).hexdigest()
        or source_lock_sha256 != expected_source_lock_sha256
    ):
        raise SourceLockError("persisted source lock differs from checkpoint authority")

    rebuilt_read_plan = build_read_plan(
        manifest,
        promoted_semantic_snapshot_sha256=str(
            binding["framework_semantic_sha256"]
        ),
        source_manifest_sha256=manifest.sha256,
        source_lock_sha256=source_lock_sha256,
        parent_event_sha256=expected_parent_event_sha256,
    )
    if read_plan_raw != canonical_json_bytes(rebuilt_read_plan):
        raise SourceCoverageError("persisted read plan differs from fresh source authority")
    if read_plan_snapshot != rebuilt_read_plan:
        raise SourceCoverageError("persisted read plan reconstruction mismatch")

    coverage_sha256 = hashlib.sha256(coverage_raw).hexdigest()
    if coverage_sha256 != expected_read_coverage_sha256:
        raise SourceCoverageError(
            "persisted read coverage differs from checkpoint authority"
        )
    _validate_persisted_read_capture(
        event_snapshots,
        manifest,
        repo=repo,
        coverage=coverage_snapshot,
        promoted_semantic_snapshot_sha256=str(
            binding["framework_semantic_sha256"]
        ),
        expected_run_id=expected_run_id,
        expected_version_binding=binding,
        expected_source_lock_sha256=source_lock_sha256,
        expected_parent_event_sha256=expected_parent_event_sha256,
        source_manifest_sha256=manifest.sha256,
    )

    input_root = _validated_run_input_root(
        run_layout,
        run_id=expected_run_id,
        run_mode=expected_run_mode,
    )
    locked_inputs = copy.deepcopy(source_lock_snapshot["inputs"])
    if not isinstance(locked_inputs, list):
        raise SourceLockError("persisted source lock inputs are invalid")
    try:
        free_space_status = (
            "available"
            if shutil.disk_usage(repo.resolve()).free >= MIN_FREE_SPACE_RESERVE_BYTES
            else "insufficient"
        )
    except OSError as error:
        raise SourceLockError("persisted U1 free-space authority is unavailable") from error
    if free_space_status != "available":
        raise SourceLockError("persisted U1 free-space authority is insufficient")

    source_seal = object.__new__(SourceLockValidation)
    source_values = {
        "run_id": expected_run_id,
        "version_binding": copy.deepcopy(binding),
        "parent_event_sha256": expected_parent_event_sha256,
        "evidence_cutoff": expected_evidence_cutoff,
        "content_sha256": str(source_lock_snapshot["content_sha256"]),
        "artifact_sha256": source_lock_sha256,
        "run_mode": expected_run_mode,
        "acl_status": str(source_lock_snapshot["acl_status"]),
        "source_release_id": str(source_lock_snapshot["source_release_id"]),
        "source_manifest_sha256": str(source_lock_snapshot["source_manifest_sha256"]),
        "release_manifest_sha256": str(source_lock_snapshot["release_manifest_sha256"]),
        "compatibility_matrix_sha256": str(
            source_lock_snapshot["compatibility_matrix_sha256"]
        ),
        "knowledge_report_sha256": str(
            source_lock_snapshot["knowledge_report_sha256"]
        ),
        "skill_tree_sha256": str(source_lock_snapshot["skill_tree_sha256"]),
        "free_space_reserve_bytes": MIN_FREE_SPACE_RESERVE_BYTES,
        "free_space_status": free_space_status,
        "input_snapshot_sha256": str(source_lock_snapshot["input_snapshot_sha256"]),
        "input_artifact_hashes": tuple(str(item["sha256"]) for item in locked_inputs),
        "inputs": tuple(locked_inputs),
        "input_root": input_root,
    }
    for field, value in source_values.items():
        object.__setattr__(source_seal, field, value)
    source_fields = {
        **source_values,
        "input_artifact_hashes": list(source_seal.input_artifact_hashes),
        "inputs": list(source_seal.inputs),
    }
    source_token, source_seal_sha256 = _register_issuer_snapshot(
        _ISSUED_SOURCE_LOCK_SEALS,
        source_fields,
    )
    object.__setattr__(source_seal, "_issuer_token", source_token)
    object.__setattr__(source_seal, "_seal_sha256", source_seal_sha256)

    _document, units, _manifest_hash, _manifest_semantic = _manifest_parts(
        manifest,
        source_manifest_sha256=manifest.sha256,
    )
    paragraphs = sum(1 for unit in units if unit["kind"] == "paragraph")
    tables = sum(1 for unit in units if unit["kind"] == "table")
    read_audit = object.__new__(ReadCoverageAudit)
    audit_values = {
        "total": len(units),
        "paragraphs": paragraphs,
        "tables": tables,
        "complete": (
            len(units) == EXPECTED_SOURCE_UNIT_COUNT
            and paragraphs == EXPECTED_PARAGRAPH_COUNT
            and tables == EXPECTED_TABLE_COUNT
        ),
        "authorizes_phase": True,
        "run_id": expected_run_id,
        "version_binding": copy.deepcopy(binding),
        "source_lock_artifact_sha256": source_lock_sha256,
        "parent_event_sha256": expected_parent_event_sha256,
        "artifact_sha256": coverage_sha256,
    }
    for field, value in audit_values.items():
        object.__setattr__(read_audit, field, value)
    audit_token, audit_seal_sha256 = _register_issuer_snapshot(
        _ISSUED_READ_AUDITS,
        audit_values,
    )
    object.__setattr__(read_audit, "_issuer_token", audit_token)
    object.__setattr__(read_audit, "_seal_sha256", audit_seal_sha256)
    return validate_u1_authority(source_seal, read_audit)


def _coverage_artifact_sha256(
    events: Sequence[Mapping[str, object]],
    receipts: Sequence[ReadReceipt],
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_parent_event_sha256: str,
    expected_source_lock_sha256: str,
) -> str:
    binding = _validate_read_version_binding(expected_version_binding)
    payload = {
        "artifact_type": "crossframe.ultra.v82.u1-source-coverage",
        "run_id": expected_run_id,
        "version_binding": binding,
        "parent_event_sha256": expected_parent_event_sha256,
        "source_lock_sha256": expected_source_lock_sha256,
        "receipt_sha256s": [
            receipt.receipt_sha256 for receipt in receipts
        ],
        "read_event_sha256s": [
            str(event["read_event_sha256"]) for event in events
        ],
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _read_u1_authority_bytes(path: Path, *, root: Path, label: str) -> bytes:
    try:
        checked = assert_safe_descendant(root.resolve(), path)
        before = checked.stat()
        if checked.is_symlink() or not stat.S_ISREG(before.st_mode):
            raise SourceLockError(f"{label} is not a regular authority file")
        if before.st_size > MAX_U1_AUTHORITY_BYTES:
            raise SourceLockError(f"{label} exceeds the authority size limit")
        with checked.open("rb") as handle:
            opened = os.fstat(handle.fileno())
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
                raise SourceLockError(f"{label} changed before it was opened")
            payload = handle.read(MAX_U1_AUTHORITY_BYTES + 1)
            after = os.fstat(handle.fileno())
    except SourceLockError:
        raise
    except (OSError, ValueError) as error:
        raise SourceLockError(f"cannot read {label} authority") from error
    if len(payload) > MAX_U1_AUTHORITY_BYTES or len(payload) != opened.st_size:
        raise SourceLockError(f"{label} changed while it was read")
    if (opened.st_dev, opened.st_ino, opened.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ):
        raise SourceLockError(f"{label} changed while it was read")
    return payload


def _parse_u1_json(raw: bytes, *, label: str) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
        if text.startswith("\ufeff"):
            raise ValueError("BOM is forbidden")
        value = json.loads(
            text,
            object_pairs_hook=_pairs_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON value: {token}")
            ),
        )
    except (UnicodeDecodeError, ValueError, SourceManifestError) as error:
        raise SourceLockError(f"{label} is not strict UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise SourceLockError(f"{label} must be a JSON object")
    return value


def canonical_skill_tree_hashes(skill_root: Path) -> dict[str, str]:
    """Return the release tree using the repository mirror conventions."""
    if not isinstance(skill_root, Path):
        raise TypeError("skill_root must be a pathlib.Path")
    root = skill_root.resolve()
    if not root.is_dir() or root.is_symlink():
        raise SourceLockError("CrossFrame Ultra skill root is not a regular directory")
    hashes: dict[str, str] = {}
    try:
        candidates = sorted(root.rglob("*"), key=lambda item: item.as_posix())
    except OSError as error:
        raise SourceLockError("cannot enumerate the CrossFrame Ultra skill tree") from error
    for path in candidates:
        relative = path.relative_to(root)
        if (
            any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts)
            or relative.as_posix() == "references/release-manifest.json"
            or path.name == ".v8-full-source.lock"
        ):
            continue
        try:
            checked = assert_safe_descendant(root, path)
            metadata = checked.lstat()
        except (OSError, ValueError) as error:
            raise SourceLockError("skill tree path is unsafe") from error
        attributes = getattr(metadata, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if stat.S_ISLNK(metadata.st_mode) or bool(attributes & reparse_flag):
            raise SourceLockError("skill tree contains a symlink or reparse point")
        if stat.S_ISREG(metadata.st_mode):
            payload = _read_u1_authority_bytes(checked, root=root, label="skill tree file")
            hashes[relative.as_posix()] = hashlib.sha256(payload).hexdigest()
    return dict(sorted(hashes.items()))


def _release_tree_sha256(
    release_document: Mapping[str, object],
    *,
    skill_root: Path,
    verify_disk_tree: bool = True,
) -> str:
    release_artifacts = release_document.get("release_artifacts")
    if not isinstance(release_artifacts, list):
        raise SourceLockError("release manifest artifacts are malformed")
    declared: dict[str, str] = {}
    for item in release_artifacts:
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256", "media_type"}:
            raise SourceLockError("release manifest artifact fields are not closed")
        relative = item.get("path")
        digest = item.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or Path(relative).is_absolute()
            or not _is_sha256(digest)
            or relative in declared
        ):
            raise SourceLockError("release manifest artifact authority is invalid")
        declared[relative] = str(digest)
    declared = dict(sorted(declared.items()))
    if verify_disk_tree:
        actual = canonical_skill_tree_hashes(skill_root)
        if declared != actual:
            raise SourceLockError(
                "release manifest does not exactly cover the canonical skill tree"
            )
    return hashlib.sha256(canonical_json_bytes(declared)).hexdigest()


def _validate_release_document(
    document: Mapping[str, object],
    *,
    manifest: SourceManifestSnapshot,
    skill_root: Path,
    verify_disk_tree: bool = True,
) -> tuple[str, str]:
    try:
        validate_instance("ultra-release-manifest.schema.json", document)
    except ValidationError as error:
        raise SourceLockError(f"release manifest violates public schema: {error.message}") from error
    if document.get("content_sha256") != _artifact_content_sha256(document):
        raise SourceLockError("release manifest content hash is invalid")
    if document.get("version_binding") != {
        **_CURRENT_VERSION_BINDING,
        "source_tree_sha256": EXPECTED_TREE_MERKLE_ROOT,
    }:
        raise SourceLockError("release manifest version binding is not current")
    if document.get("release_state") != "stable":
        raise SourceLockError("release manifest is not the stable authority")
    framework_source = document.get("framework_source")
    source_counts = document.get("source_counts")
    source = manifest.document
    if not isinstance(framework_source, Mapping) or (
        framework_source.get("raw_sha256") != FRAMEWORK_RAW_SHA256
        or framework_source.get("semantic_sha256") != FRAMEWORK_SEMANTIC_SHA256
    ):
        raise SourceLockError("release manifest framework source is not current")
    expected_counts = {
        "paragraphs": source.get("paragraph_count"),
        "headings": source.get("heading_count"),
        "tables": source.get("table_count"),
        "concepts": source.get("concept_count"),
        "contracts": source.get("contract_count"),
        "source_units": source.get("source_unit_count"),
    }
    if source_counts != expected_counts:
        raise SourceLockError("release manifest source counts differ from the source authority")
    release_id = document.get("release_id")
    if not isinstance(release_id, str) or not release_id:
        raise SourceLockError("release manifest release ID is invalid")
    return release_id, _release_tree_sha256(
        document,
        skill_root=skill_root,
        verify_disk_tree=verify_disk_tree,
    )


def _measure_compatibility_matrix(skill_root: Path) -> str:
    path = skill_root / "references" / "compatibility-matrix.json"
    raw = _read_u1_authority_bytes(path, root=skill_root, label="compatibility matrix")
    document = _parse_u1_json(raw, label="compatibility matrix")
    try:
        validate_instance("ultra-compatibility-matrix.schema.json", document)
    except ValidationError as error:
        raise SourceLockError(
            f"compatibility matrix violates public schema: {error.message}"
        ) from error
    if document.get("content_sha256") != _artifact_content_sha256(document):
        raise SourceLockError("compatibility matrix content hash is invalid")
    if document.get("version_binding") != {
        **_CURRENT_VERSION_BINDING,
        "source_tree_sha256": EXPECTED_TREE_MERKLE_ROOT,
    }:
        raise SourceLockError("compatibility matrix version binding is not current")
    return hashlib.sha256(raw).hexdigest()


def measure_u1_prerequisites(
    repo: Path,
    *,
    manifest: SourceManifestSnapshot,
    release_manifest_path: Path | None = None,
    run_mode: str = "production",
) -> U1PrerequisiteMeasurement:
    """Measure U1 authority exclusively from sealed snapshots and host files."""
    if not isinstance(repo, Path):
        raise TypeError("U1 measurement requires a repository path")
    if run_mode not in {"production", "test"}:
        raise SourceLockError("U1 measurement run mode is invalid")
    repo = repo.resolve()
    skill_root = repo / "skills" / "crossframe-ultra"
    if run_mode == "production":
        if release_manifest_path is not None:
            raise SourceLockError("production U1 rejects a release manifest override")
        selected_release = skill_root / "references" / "release-manifest.json"
    else:
        if not isinstance(release_manifest_path, Path):
            raise SourceLockError("test U1 requires an explicit release manifest path")
        selected_release = release_manifest_path.resolve()

    try:
        _manifest_parts(manifest, source_manifest_sha256=None)
        repository_manifest = load_source_manifest(
            skill_root / "references" / "source-manifest.json",
            expected_sha256=manifest.sha256,
        )
        source_ready = (
            repository_manifest.document == manifest.document
            and not validate_committed_source_snapshot(repo).errors
        )
    except (OSError, SourceManifestError):
        source_ready = False
    source_manifest_sha256 = manifest.sha256

    release_ready = False
    source_release_id: str | None = None
    release_manifest_sha256: str | None = None
    skill_tree_sha256: str | None = None
    try:
        release_raw = _read_u1_authority_bytes(
            selected_release,
            root=selected_release.parent.resolve(),
            label="release manifest",
        )
        release_document = _parse_u1_json(release_raw, label="release manifest")
        source_release_id, skill_tree_sha256 = _validate_release_document(
            release_document, manifest=manifest, skill_root=skill_root
        )
        release_manifest_sha256 = hashlib.sha256(release_raw).hexdigest()
        release_ready = True
    except SourceLockError:
        pass

    try:
        compatibility_matrix_sha256 = _measure_compatibility_matrix(skill_root)
        compatibility_ready = True
    except SourceLockError:
        compatibility_matrix_sha256 = None
        compatibility_ready = False

    try:
        knowledge_errors = validate_knowledge(repo)
    except Exception as error:
        knowledge_errors = [f"knowledge validator failed: {error}"]
    knowledge_report = {
        "valid": not knowledge_errors,
        "framework_revision": FRAMEWORK_REVISION,
        "raw_sha256": FRAMEWORK_RAW_SHA256,
        "semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
        "errors": knowledge_errors,
    }
    knowledge_report_sha256 = hashlib.sha256(
        canonical_json_bytes(knowledge_report)
    ).hexdigest()
    knowledge_ready = not knowledge_errors

    canonical_root = Path(__file__).resolve().parents[4]
    fixed_root_ready = (
        skill_root.resolve() == repo / "skills" / "crossframe-ultra"
        and (run_mode == "test" or repo == canonical_root)
    )
    try:
        free_space_ready = shutil.disk_usage(repo).free >= MIN_FREE_SPACE_RESERVE_BYTES
        free_space_status = "available" if free_space_ready else "insufficient"
    except OSError:
        free_space_ready = False
        free_space_status = "unknown"
    checks: dict[str, bool | str] = {
        "source_manifest": source_ready,
        "release_manifest": release_ready,
        "compatibility_matrix": compatibility_ready,
        "knowledge_closure": knowledge_ready,
        "skill_tree_hash": release_ready and skill_tree_sha256 is not None,
        "fixed_root": fixed_root_ready,
        "free_space_reserve": free_space_ready,
        "current_user_acl": "unknown",
    }
    verified = tuple(sorted(name for name, result in checks.items() if result is True))
    unknown = tuple(sorted(name for name, result in checks.items() if result == "unknown"))
    missing = tuple(sorted(name for name, result in checks.items() if result is False))
    return _issue_u1_measurement(
        ready=all(
            checks[name] is True
            for name in _U1_PREREQUISITES - {"current_user_acl"}
        ),
        verified=verified,
        unknown=unknown,
        missing=missing,
        run_mode=run_mode,
        source_release_id=source_release_id,
        source_manifest_sha256=source_manifest_sha256,
        release_manifest_sha256=release_manifest_sha256,
        compatibility_matrix_sha256=compatibility_matrix_sha256,
        knowledge_report_sha256=knowledge_report_sha256,
        skill_tree_sha256=skill_tree_sha256,
        free_space_reserve_bytes=MIN_FREE_SPACE_RESERVE_BYTES,
        free_space_status=free_space_status,
        repo=repo,
        manifest_sha256=manifest.sha256,
        release_manifest_path=selected_release,
    )


def verify_u1_prerequisites(
    measurement: object,
) -> U1PrerequisiteMeasurement:
    if not isinstance(measurement, U1PrerequisiteMeasurement):
        raise SourceLockError("U1 requires an issuer-produced prerequisite measurement")
    try:
        fields = _measurement_fields(measurement)
        issued = _ISSUED_U1_MEASUREMENTS.get(measurement._issuer_token)
        computed = _opaque_seal_sha256(fields)
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise SourceLockError("U1 prerequisite measurement is malformed") from error
    if issued is None or measurement._seal_sha256 != issued or issued != computed:
        raise SourceLockError("U1 prerequisite measurement issuer integrity is invalid")
    if not measurement.ready:
        raise SourceLockError("U1 prerequisite measurement is not ready")
    try:
        manifest = load_source_manifest(
            measurement._repo
            / "skills"
            / "crossframe-ultra"
            / "references"
            / "source-manifest.json",
            expected_sha256=measurement._manifest_sha256,
        )
        fresh = measure_u1_prerequisites(
            measurement._repo,
            manifest=manifest,
            release_manifest_path=(
                measurement._release_manifest_path
                if measurement.run_mode == "test"
                else None
            ),
            run_mode=measurement.run_mode,
        )
    except (OSError, SourceManifestError, SourceLockError) as error:
        raise SourceLockError("U1 prerequisite host authority is stale") from error
    if not fresh.ready or _measurement_fields(fresh) != fields:
        raise SourceLockError("U1 prerequisite host authority is stale or not ready")
    return fresh


__all__ = (
    "EXPECTED_PARAGRAPH_COUNT",
    "EXPECTED_SOURCE_UNIT_COUNT",
    "EXPECTED_TABLE_COUNT",
    "MIN_FREE_SPACE_RESERVE_BYTES",
    "READ_EVENT_SCHEMA_ID",
    "ReadCaptureDiagnostic",
    "ReadCoverageAudit",
    "ReadReceipt",
    "SourceReadSession",
    "SourceCoverageError",
    "SourceLockError",
    "SourceLockValidation",
    "SourceManifestError",
    "SourceManifestSnapshot",
    "U1PrerequisiteMeasurement",
    "U1AuthoritySeal",
    "build_source_lock",
    "build_read_plan",
    "audit_read_capture",
    "capture_authority_read_diagnostic",
    "capture_source_unit_read",
    "canonical_skill_tree_hashes",
    "execution_identity",
    "load_source_manifest",
    "make_read_event",
    "measure_current_user_acl",
    "measure_u1_prerequisites",
    "open_source_read_session",
    "verify_u1_prerequisites",
    "validate_source_lock",
    "validate_u1_authority",
    "verify_u1_authority_seal",
)
