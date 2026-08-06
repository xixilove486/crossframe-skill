from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
from typing import Literal

from .constants import PHASES, current_version_binding
from .errors import UltraRuntimeError
from .jsonio import (
    _exclusive_path_lock,
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from .paths import (
    RunLayout,
    RunMode,
    RootPolicy,
    _parse_canonical_utc,
    _require_utc,
    _validate_run_id,
    assert_safe_descendant,
    build_run_layout,
    create_run_id,
)
from .schemas import (
    compute_artifact_content_sha256,
    resolve_compatibility,
    validate_instance,
    validate_phase_artifact,
)
from .state_machine import (
    PHASE_EVENT_SCHEMA_ID,
    PhaseStore,
    _compute_event_content_sha256,
    _validate_phase_output_contract,
    compute_event_sha256,
)
from .status import RunStatusRecord, RunStatusStore


_CHECKPOINT_SCHEMA = "ultra-recovery-checkpoint.schema.json"
_CHECKPOINT_SCHEMA_ID = "crossframe.ultra.v82.recovery-checkpoint"
_MIGRATION_SCHEMA = "ultra-run-migration.schema.json"
_MIGRATION_SCHEMA_ID = "crossframe.ultra.v82.run-migration"
_AUTHORITY_FILENAME = "run-authority.json"
_EVENTS_FILENAME = "phase-events.jsonl"
_CHECKPOINT_LOCK_FILENAME = ".checkpoint.lock"
_U1_SOURCE_LOCK_PATH = Path("recovery/u1-authority/source-lock.json")
_U1_SOURCE_COVERAGE_PATH = Path("recovery/u1-authority/source-coverage.json")
_U1_READ_PLAN_PATH = Path("recovery/u1-authority/read-plan.json")
_U1_READ_EVENTS_PATH = Path("artifacts/U00-U03-evidence/ultra-read-events.jsonl")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}")
_AUTHORITY_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "source_sha256",
        "input_artifact_hashes",
        "input_snapshot_sha256",
        "evidence_cutoff",
        "run_contract_sha256",
        "input_refs",
        "content_sha256",
    }
)
_CHECKPOINT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "generated_at",
        "content_sha256",
        "phase_id",
        "boundary_kind",
        "boundary_id",
        "boundary_ordinal",
        "phase_event_sha256",
        "artifact_hashes",
        "evidence_cutoff",
        "completed_boundary",
        "resumable",
    }
)
_EVENT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "generated_at",
        "content_sha256",
        "phase_id",
        "event_type",
        "parent_event_sha256",
        "input_artifact_hashes",
        "output_artifact_hashes",
        "source_sha256",
        "evidence_cutoff",
        "run_contract_sha256",
        "timestamp",
        "status",
        "failure_code",
        "invalidated_phases",
        "event_sha256",
    }
)


class RecoveryError(UltraRuntimeError, RuntimeError):
    pass


class RecoveryIntegrityError(RecoveryError):
    pass


class _RecoveryInputDriftError(RecoveryIntegrityError):
    pass


class RecoveryCompatibilityError(RecoveryError):
    pass


class RecoveryStateError(RecoveryError):
    pass


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    outcome: str
    compatibility_result: str
    checkpoint: Mapping[str, object] | None
    status: RunStatusRecord | None
    phase_store: PhaseStore | None


@dataclass(frozen=True, slots=True)
class ForkResult:
    run_id: str
    layout: RunLayout
    parent_checkpoint: Mapping[str, object]
    migration: Mapping[str, object]


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _iso_utc(value: datetime) -> str:
    _require_utc(value, "now")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _media_type(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return "application/json"
    if suffix == ".jsonl":
        return "application/x-ndjson"
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    if suffix in {".txt", ".log"}:
        return "text/plain"
    return "application/octet-stream"


def _paths(layout: RunLayout) -> tuple[Path, Path, Path, Path, Path]:
    checkpoints = layout.recovery_dir / "checkpoints"
    quarantine = layout.recovery_dir / "quarantine"
    authority = layout.recovery_dir / _AUTHORITY_FILENAME
    events = layout.recovery_dir / _EVENTS_FILENAME
    lock = layout.recovery_dir / _CHECKPOINT_LOCK_FILENAME
    for path in (checkpoints, quarantine, authority, events, lock):
        try:
            assert_safe_descendant(layout.root, path)
        except (OSError, TypeError, ValueError) as error:
            raise RecoveryIntegrityError("recovery path authority is invalid") from error
    return checkpoints, quarantine, authority, events, lock


def _validate_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    try:
        _validate_run_id(layout.run_dir.name)
        expected = {
            "input_dir": layout.run_dir / "input",
            "authoring_dir": layout.run_dir / "work" / "authoring",
            "artifacts_dir": layout.run_dir / "artifacts",
            "delivery_dir": layout.run_dir / "delivery",
            "validation_dir": layout.run_dir / "validation",
            "validation_current_dir": layout.run_dir / "validation" / "current",
            "validation_attempts_dir": layout.run_dir / "validation" / "attempts",
            "recovery_dir": layout.run_dir / "recovery",
            "logs_dir": layout.run_dir / "logs",
        }
        if any(getattr(layout, name) != path for name, path in expected.items()):
            raise ValueError("layout members differ from the canonical run tree")
        for path in (layout.run_dir, layout.root_staging_dir, *expected.values()):
            assert_safe_descendant(layout.root, path)
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError("run layout authority is invalid") from error
    _paths(layout)


def _artifact_ref(layout: RunLayout, path: Path) -> dict[str, str]:
    if not isinstance(path, Path):
        raise TypeError("artifact_paths must contain pathlib.Path values")
    candidate = path if path.is_absolute() else layout.run_dir / path
    try:
        assert_safe_descendant(layout.root, candidate)
        relative = candidate.relative_to(layout.run_dir)
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError("checkpoint artifact escapes the run") from error
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise RecoveryIntegrityError("checkpoint artifact path is invalid")
    try:
        if not candidate.is_file():
            raise RecoveryIntegrityError(
                f"checkpoint artifact is missing: {relative.as_posix()}"
            )
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    except RecoveryIntegrityError:
        raise
    except OSError as error:
        raise RecoveryIntegrityError(
            f"checkpoint artifact cannot be read: {relative.as_posix()}"
        ) from error
    return {
        "path": relative.as_posix(),
        "sha256": digest,
        "media_type": _media_type(candidate),
    }


def _artifact_refs(layout: RunLayout, paths: Sequence[Path]) -> list[dict[str, str]]:
    if isinstance(paths, (str, bytes)):
        raise TypeError("artifact_paths must be a sequence of paths")
    refs = [_artifact_ref(layout, path) for path in tuple(paths)]
    if not refs:
        raise RecoveryIntegrityError("checkpoint requires at least one artifact hash")
    if len({item["path"] for item in refs}) != len(refs):
        raise RecoveryIntegrityError("checkpoint artifact paths contain duplicates")
    if len({item["sha256"] for item in refs}) != len(refs):
        raise RecoveryIntegrityError("checkpoint artifact hashes contain duplicates")
    return refs


def _input_refs(layout: RunLayout) -> list[dict[str, str]]:
    try:
        if not layout.input_dir.is_dir():
            raise RecoveryIntegrityError("frozen input directory is unavailable")
        files = sorted(
            (path for path in layout.input_dir.rglob("*") if path.is_file()),
            key=lambda item: item.relative_to(layout.run_dir).as_posix(),
        )
    except OSError as error:
        raise RecoveryIntegrityError("frozen input directory cannot be read") from error
    refs = [_artifact_ref(layout, path) for path in files]
    if not refs:
        raise RecoveryIntegrityError("recovery requires at least one frozen input file")
    return refs


def _authority_from_store(
    layout: RunLayout, phase_store: PhaseStore
) -> dict[str, object]:
    if not isinstance(phase_store, PhaseStore):
        raise TypeError("phase_store must be the existing PhaseStore")
    if phase_store.run_id != layout.run_dir.name or phase_store._run_layout != layout:
        raise RecoveryIntegrityError("phase store and run layout authority differ")
    authority: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.recovery-authority",
        "schema_version": 1,
        "run_id": phase_store.run_id,
        "version_binding": copy.deepcopy(phase_store._version_binding),
        "source_sha256": phase_store._source_sha256,
        "input_artifact_hashes": list(phase_store._input_artifact_hashes),
        "input_snapshot_sha256": phase_store._input_snapshot_sha256,
        "evidence_cutoff": phase_store._evidence_cutoff,
        "run_contract_sha256": phase_store.run_contract_artifact_sha256,
        "input_refs": _input_refs(layout),
        "content_sha256": "0" * 64,
    }
    authority["content_sha256"] = compute_artifact_content_sha256(authority)
    return authority


def _read_canonical_object(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError(f"cannot read recovery authority: {path.name}") from error
    if raw != canonical_json_bytes(value):
        raise RecoveryIntegrityError(f"recovery authority is not canonical: {path.name}")
    return value


def _validate_ref_record(value: object, *, role: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"path", "sha256", "media_type"}:
        raise RecoveryIntegrityError(f"{role} artifact hash record is invalid")
    relative_text = value.get("path")
    digest = value.get("sha256")
    media_type = value.get("media_type")
    if (
        not isinstance(relative_text, str)
        or not relative_text
        or not _is_sha256(digest)
        or not isinstance(media_type, str)
        or "/" not in media_type
    ):
        raise RecoveryIntegrityError(f"{role} artifact hash record is invalid")
    relative = Path(relative_text)
    if (
        relative.is_absolute()
        or relative.drive
        or relative.as_posix() != relative_text
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise RecoveryIntegrityError(f"{role} artifact path is not canonical")
    return {
        "path": relative_text,
        "sha256": str(digest),
        "media_type": media_type,
    }


def _validate_disk_ref(layout: RunLayout, value: object, *, role: str) -> dict[str, str]:
    ref = _validate_ref_record(value, role=role)
    relative_text = ref["path"]
    relative = Path(relative_text)
    candidate = layout.run_dir / relative
    try:
        assert_safe_descendant(layout.root, candidate)
        candidate.relative_to(layout.run_dir)
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError(f"{role} artifact path is invalid") from error
    drift_error = _RecoveryInputDriftError if role == "input" else RecoveryIntegrityError
    try:
        if not candidate.is_file():
            raise drift_error(
                f"{role} artifact is missing: {relative_text}"
            )
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    except RecoveryIntegrityError:
        raise
    except OSError as error:
        raise drift_error(
            f"{role} artifact cannot be read: {relative_text}"
        ) from error
    if actual != ref["sha256"]:
        raise drift_error(
            f"{role} artifact hash differs from disk: {relative_text}"
        )
    return ref


def _validate_authority_record(
    layout: RunLayout,
) -> tuple[dict[str, object], str, list[dict[str, str]]]:
    _, _, authority_path, _, _ = _paths(layout)
    authority = _read_canonical_object(authority_path)
    if set(authority) != _AUTHORITY_FIELDS:
        raise RecoveryIntegrityError("recovery run authority is not a closed object")
    if (
        authority.get("schema_id") != "crossframe.ultra.v82.recovery-authority"
        or authority.get("schema_version") != 1
        or authority.get("run_id") != layout.run_dir.name
        or not _is_sha256(authority.get("source_sha256"))
        or not _is_sha256(authority.get("run_contract_sha256"))
        or authority.get("content_sha256")
        != compute_artifact_content_sha256(authority)
    ):
        raise RecoveryIntegrityError("recovery run authority integrity is invalid")
    input_snapshot = authority.get("input_snapshot_sha256")
    if input_snapshot is not None and not _is_sha256(input_snapshot):
        raise RecoveryIntegrityError("recovery input snapshot authority is invalid")
    input_hashes = authority.get("input_artifact_hashes")
    if (
        not isinstance(input_hashes, list)
        or not input_hashes
        or any(not _is_sha256(value) for value in input_hashes)
        or len(input_hashes) != len(set(input_hashes))
    ):
        raise RecoveryIntegrityError("recovery input hash authority is invalid")
    try:
        _parse_canonical_utc(authority.get("evidence_cutoff"), "evidence cutoff")
    except ValueError as error:
        raise RecoveryIntegrityError("recovery evidence cutoff authority is invalid") from error
    binding = authority.get("version_binding")
    if not isinstance(binding, Mapping):
        raise RecoveryIntegrityError("recovery version binding authority is invalid")
    compatibility = resolve_compatibility(binding, current_version_binding())
    if compatibility == "reject":
        raise RecoveryCompatibilityError("recovery version binding is unsupported")
    raw_refs = authority.get("input_refs")
    if not isinstance(raw_refs, list) or not raw_refs:
        raise RecoveryIntegrityError("recovery frozen input refs are missing")
    refs = [_validate_ref_record(item, role="input") for item in raw_refs]
    if len({item["path"] for item in refs}) != len(refs):
        raise RecoveryIntegrityError("recovery frozen input refs contain duplicates")
    return authority, compatibility, refs


def _validate_authority(layout: RunLayout) -> tuple[dict[str, object], str]:
    authority, compatibility, raw_refs = _validate_authority_record(layout)
    for item in raw_refs:
        _validate_disk_ref(layout, item, role="input")
    return authority, compatibility


def _validate_event_chain(
    events: Sequence[Mapping[str, object]],
    authority: Mapping[str, object],
    *,
    compatibility: str,
) -> tuple[dict[str, object], ...]:
    if not events:
        raise RecoveryIntegrityError("phase event chain is empty")
    expected_parent = "0" * 64
    completed = 0
    terminal_seen = False
    snapshots: list[dict[str, object]] = []
    for index, event in enumerate(events):
        snapshot = copy.deepcopy(dict(event))
        if set(snapshot) != _EVENT_FIELDS:
            raise RecoveryIntegrityError("phase event chain contains a non-closed event")
        if (
            snapshot.get("schema_id") != PHASE_EVENT_SCHEMA_ID
            or snapshot.get("schema_version") != 1
            or snapshot.get("run_id") != authority["run_id"]
            or snapshot.get("version_binding") != authority["version_binding"]
            or snapshot.get("source_sha256") != authority["source_sha256"]
            or snapshot.get("input_artifact_hashes")
            != authority["input_artifact_hashes"]
            or snapshot.get("evidence_cutoff") != authority["evidence_cutoff"]
            or snapshot.get("run_contract_sha256")
            != authority["run_contract_sha256"]
            or snapshot.get("generated_at") != snapshot.get("timestamp")
            or snapshot.get("parent_event_sha256") != expected_parent
            or snapshot.get("content_sha256")
            != _compute_event_content_sha256(snapshot)
            or snapshot.get("event_sha256") != compute_event_sha256(snapshot)
        ):
            raise RecoveryIntegrityError("phase event chain authority or hash is invalid")
        try:
            _parse_canonical_utc(snapshot.get("timestamp"), "phase event timestamp")
        except ValueError as error:
            raise RecoveryIntegrityError("phase event timestamp is invalid") from error
        phase_id = snapshot.get("phase_id")
        status = snapshot.get("status")
        if terminal_seen:
            raise RecoveryIntegrityError("phase event appears after a terminal event")
        if status == "complete":
            if completed >= len(PHASES) or phase_id != PHASES[completed]:
                raise RecoveryIntegrityError("completed phase event order is invalid")
            outputs = snapshot.get("output_artifact_hashes")
            if not isinstance(outputs, list) or any(not _is_sha256(item) for item in outputs):
                raise RecoveryIntegrityError("completed phase outputs are invalid")
            if phase_id == "U0" and outputs != [authority["run_contract_sha256"]]:
                raise RecoveryIntegrityError("U0 event does not bind the run contract")
            try:
                _validate_phase_output_contract(str(phase_id), tuple(outputs))
            except Exception as error:
                raise RecoveryIntegrityError("completed phase output contract is invalid") from error
            if (
                snapshot.get("event_type") != "phase-completed"
                or snapshot.get("failure_code") is not None
                or snapshot.get("invalidated_phases") != []
            ):
                raise RecoveryIntegrityError("completed phase event disposition is invalid")
            completed += 1
        elif status in {"failed", "blocked", "cancelled"}:
            expected_phase = PHASES[completed] if completed < len(PHASES) else None
            if (
                phase_id != expected_phase
                or snapshot.get("event_type") != f"phase-{status}"
                or not isinstance(snapshot.get("failure_code"), str)
                or not str(snapshot["failure_code"]).strip()
                or snapshot.get("output_artifact_hashes") != []
            ):
                raise RecoveryIntegrityError("terminal phase event disposition is invalid")
            terminal_seen = True
        else:
            raise RecoveryIntegrityError("phase event status is invalid")
        if compatibility == "resume":
            try:
                validate_instance("ultra-phase-event.schema.json", snapshot)
            except Exception as error:
                raise RecoveryIntegrityError("phase event violates the public schema") from error
        expected_parent = str(snapshot["event_sha256"])
        snapshots.append(snapshot)
        if terminal_seen and index != len(events) - 1:
            raise RecoveryIntegrityError("terminal phase event is not the chain tail")
    return tuple(snapshots)


def _read_events(
    layout: RunLayout,
    authority: Mapping[str, object],
    *,
    compatibility: str,
) -> tuple[dict[str, object], ...]:
    _, _, _, events_path, _ = _paths(layout)
    try:
        raw = events_path.read_bytes()
    except OSError as error:
        raise RecoveryIntegrityError("phase event journal is unavailable") from error
    if not raw or not raw.endswith(b"\n"):
        raise RecoveryIntegrityError("phase event journal is incomplete")
    events: list[dict[str, object]] = []
    for number, line in enumerate(raw.splitlines(keepends=True), start=1):
        try:
            event = load_json_object_bytes(
                line,
                source=f"{events_path}:{number}",
            )
        except (TypeError, ValueError) as error:
            raise RecoveryIntegrityError("phase event journal contains invalid JSON") from error
        if line != canonical_json_bytes(event):
            raise RecoveryIntegrityError("phase event journal is not canonical JSONL")
        events.append(event)
    return _validate_event_chain(events, authority, compatibility=compatibility)


def _quarantine(layout: RunLayout, path: Path) -> None:
    _, quarantine_dir, _, _, _ = _paths(layout)
    try:
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        raw = path.read_bytes()
        source_hash = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:8]
        content_hash = hashlib.sha256(raw).hexdigest()[:12]
        target = quarantine_dir / f"half-{source_hash}-{content_hash}.json"
        assert_safe_descendant(layout.root, target)
        if target.exists():
            if target.read_bytes() != raw:
                raise RecoveryIntegrityError("checkpoint quarantine name collision")
            path.unlink()
        else:
            os.replace(path, target)
    except RecoveryIntegrityError:
        raise
    except OSError as error:
        raise RecoveryIntegrityError("half-written checkpoint cannot be quarantined") from error


def _checkpoint_slot(value: Mapping[str, object]) -> tuple[str, str, int]:
    return (
        str(value["phase_id"]),
        str(value["boundary_kind"]),
        int(value["boundary_ordinal"]),
    )


def _checkpoint_sort_key(value: Mapping[str, object]) -> tuple[int, int, int]:
    phase = str(value["phase_id"])
    kind_rank = 0 if value["boundary_kind"] == "article-packet" else 1
    return PHASES.index(phase), kind_rank, int(value["boundary_ordinal"])


def _validate_checkpoint(
    layout: RunLayout,
    checkpoint: Mapping[str, object],
    *,
    authority: Mapping[str, object],
    compatibility: str,
    events_by_hash: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    snapshot = copy.deepcopy(dict(checkpoint))
    if set(snapshot) != _CHECKPOINT_FIELDS:
        raise RecoveryIntegrityError("checkpoint is not a closed object")
    if (
        snapshot.get("schema_id") != _CHECKPOINT_SCHEMA_ID
        or snapshot.get("schema_version") != 1
        or snapshot.get("run_id") != authority["run_id"]
        or snapshot.get("version_binding") != authority["version_binding"]
        or snapshot.get("evidence_cutoff") != authority["evidence_cutoff"]
        or snapshot.get("content_sha256")
        != compute_artifact_content_sha256(snapshot)
    ):
        raise RecoveryIntegrityError("checkpoint immutable authority is invalid")
    phase_id = snapshot.get("phase_id")
    boundary_kind = snapshot.get("boundary_kind")
    boundary_id = snapshot.get("boundary_id")
    ordinal = snapshot.get("boundary_ordinal")
    if phase_id not in PHASES or boundary_kind not in {"phase", "article-packet"}:
        raise RecoveryIntegrityError("checkpoint boundary authority is invalid")
    if not isinstance(boundary_id, str) or _IDENTIFIER_RE.fullmatch(boundary_id) is None:
        raise RecoveryIntegrityError("checkpoint boundary identifier is invalid")
    if type(ordinal) is not int or ordinal < 0:
        raise RecoveryIntegrityError("checkpoint boundary ordinal is invalid")
    if type(snapshot.get("completed_boundary")) is not bool or type(
        snapshot.get("resumable")
    ) is not bool:
        raise RecoveryIntegrityError("checkpoint boundary flags are invalid")
    event_hash = snapshot.get("phase_event_sha256")
    event = events_by_hash.get(str(event_hash))
    if event is None:
        raise RecoveryIntegrityError("checkpoint phase event is not in the run ancestry")
    if boundary_kind == "phase":
        if boundary_id != phase_id or ordinal != 0:
            raise RecoveryIntegrityError("phase checkpoint boundary is invalid")
        if event.get("phase_id") != phase_id or event.get("status") != "complete":
            raise RecoveryIntegrityError("phase checkpoint does not bind its completed event")
    else:
        if phase_id != "U11" or ordinal < 1:
            raise RecoveryIntegrityError("article packet checkpoint boundary is invalid")
        if event.get("phase_id") != "U10" or event.get("status") != "complete":
            raise RecoveryIntegrityError("article packet checkpoint does not bind the U10 head")
    try:
        generated_at = _parse_canonical_utc(
            snapshot.get("generated_at"), "checkpoint generated_at"
        )
        event_time = _parse_canonical_utc(event.get("timestamp"), "phase event timestamp")
    except ValueError as error:
        raise RecoveryIntegrityError("checkpoint timestamp authority is invalid") from error
    if generated_at < event_time:
        raise RecoveryIntegrityError("checkpoint predates its phase event")
    raw_refs = snapshot.get("artifact_hashes")
    if not isinstance(raw_refs, list) or not raw_refs:
        raise RecoveryIntegrityError("checkpoint artifact hash boundary is empty")
    refs = [_validate_disk_ref(layout, item, role="checkpoint") for item in raw_refs]
    if len({item["path"] for item in refs}) != len(refs) or len(
        {item["sha256"] for item in refs}
    ) != len(refs):
        raise RecoveryIntegrityError("checkpoint artifact hash boundary has duplicates")
    if boundary_kind == "phase" and [item["sha256"] for item in refs] != event.get(
        "output_artifact_hashes"
    ):
        raise RecoveryIntegrityError("checkpoint artifact order differs from the phase event")
    if boundary_kind == "article-packet" and "work/authoring/article.partial.md" not in {
        item["path"] for item in refs
    }:
        raise RecoveryIntegrityError("article packet checkpoint omits the fixed partial article")
    if compatibility == "resume":
        try:
            validate_phase_artifact(
                _CHECKPOINT_SCHEMA,
                snapshot,
                expected_schema_id=_CHECKPOINT_SCHEMA_ID,
                expected_run_id=str(authority["run_id"]),
                expected_version_binding=current_version_binding(),
                expected_phase_id=str(phase_id),
            )
        except Exception as error:
            raise RecoveryIntegrityError("checkpoint violates the public schema") from error
    return snapshot


def _load_checkpoints_unlocked(
    layout: RunLayout,
) -> tuple[tuple[dict[str, object], ...], dict[str, object], str, tuple[dict[str, object], ...]]:
    checkpoints_dir, _, authority_path, events_path, _ = _paths(layout)
    if not checkpoints_dir.exists():
        if authority_path.exists() or events_path.exists():
            raise RecoveryIntegrityError("recovery authority exists without checkpoints")
        return (), {}, "resume", ()
    authority, compatibility = _validate_authority(layout)
    events = _read_events(layout, authority, compatibility=compatibility)
    events_by_hash = {str(event["event_sha256"]): event for event in events}
    checkpoints: list[dict[str, object]] = []
    slots: dict[tuple[str, str, int], str] = {}
    try:
        candidates = sorted(
            (path for path in checkpoints_dir.iterdir() if path.is_file()),
            key=lambda path: path.name,
        )
    except OSError as error:
        raise RecoveryIntegrityError("checkpoint directory cannot be read") from error
    for path in candidates:
        if re.fullmatch(r"[0-9a-f]{64}\.json", path.name) is None:
            _quarantine(layout, path)
            continue
        try:
            raw = path.read_bytes()
            checkpoint = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError):
            _quarantine(layout, path)
            continue
        if sha256_bytes(raw) != path.stem:
            raise RecoveryIntegrityError("checkpoint filename hash differs from file bytes")
        if raw != canonical_json_bytes(checkpoint):
            raise RecoveryIntegrityError("checkpoint bytes are not canonical JSON")
        validated = _validate_checkpoint(
            layout,
            checkpoint,
            authority=authority,
            compatibility=compatibility,
            events_by_hash=events_by_hash,
        )
        slot = _checkpoint_slot(validated)
        prior_hash = slots.get(slot)
        if prior_hash is not None and prior_hash != path.stem:
            raise RecoveryIntegrityError(
                "duplicate logical checkpoint slot has different checkpoint hashes"
            )
        slots[slot] = path.stem
        checkpoints.append(validated)
    checkpoints.sort(key=_checkpoint_sort_key)
    return tuple(checkpoints), authority, compatibility, events


def _write_immutable(path: Path, value: object) -> bytes:
    raw = canonical_json_bytes(value)
    if path.exists():
        try:
            if path.read_bytes() != raw:
                raise RecoveryIntegrityError(f"immutable recovery file differs: {path.name}")
        except OSError as error:
            raise RecoveryIntegrityError(f"immutable recovery file is unreadable: {path.name}") from error
        return raw
    atomic_write_bytes(path, raw)
    return raw


def _sync_events(path: Path, events: Sequence[Mapping[str, object]]) -> None:
    chunks = tuple(canonical_json_bytes(dict(event)) for event in events)
    raw = b"".join(chunks)
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError as error:
            raise RecoveryIntegrityError("phase event journal is unreadable") from error
        if not existing or not existing.endswith(b"\n"):
            raise RecoveryIntegrityError("phase event journal is incomplete")
        boundary = 0
        whole_event_prefix = False
        for chunk in chunks:
            boundary += len(chunk)
            if len(existing) == boundary:
                whole_event_prefix = True
                break
            if len(existing) < boundary:
                break
        if not whole_event_prefix or existing != raw[: len(existing)]:
            raise RecoveryIntegrityError("phase event journal diverges from PhaseStore")
        if existing == raw:
            return
    atomic_write_bytes(path, raw)


def _status_if_present(layout: RunLayout) -> RunStatusRecord | None:
    path = layout.run_dir / "run-status.json"
    if not path.exists():
        return None
    try:
        return RunStatusStore(layout).read()
    except Exception as error:
        raise RecoveryIntegrityError("run status authority is invalid") from error


def _u1_recovery_read_plan(
    phase_store: PhaseStore,
    *,
    parent_event_sha256: str,
    source_lock_sha256: str,
) -> dict[str, object]:
    from .source_integrity import (
        EXPECTED_SOURCE_UNIT_COUNT,
        build_read_plan,
        load_source_manifest,
    )

    try:
        accepted = phase_store._accepted_u1_snapshot()
        if (
            accepted.get("parent_event_sha256") != parent_event_sha256
            or accepted.get("source_lock_artifact_sha256") != source_lock_sha256
        ):
            raise RecoveryIntegrityError(
                "U1 checkpoint differs from accepted source authority"
            )
        manifest = load_source_manifest(
            phase_store._source_repository
            / "skills"
            / "crossframe-ultra"
            / "references"
            / "source-manifest.json",
            expected_sha256=str(accepted["source_manifest_sha256"]),
        )
        plan = build_read_plan(
            manifest,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            source_lock_sha256=source_lock_sha256,
            parent_event_sha256=parent_event_sha256,
        )
    except RecoveryIntegrityError:
        raise
    except Exception as error:
        raise RecoveryIntegrityError(
            "U1 recovery read plan cannot be reconstructed"
        ) from error
    if (
        plan.get("source_unit_count") != EXPECTED_SOURCE_UNIT_COUNT
        or not isinstance(plan.get("source_unit_ids"), list)
        or len(plan["source_unit_ids"]) != EXPECTED_SOURCE_UNIT_COUNT
        or not isinstance(plan.get("source_units"), list)
        or len(plan["source_units"]) != EXPECTED_SOURCE_UNIT_COUNT
    ):
        raise RecoveryIntegrityError(
            "U1 recovery read plan does not cover exactly 4,753 source units"
        )
    return plan


def _validated_u1_recovery_authority(
    layout: RunLayout,
    authority: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    checkpoints: Sequence[Mapping[str, object]],
    store: PhaseStore,
) -> object | None:
    u1_event = next(
        (
            event
            for event in events
            if event.get("phase_id") == "U1" and event.get("status") == "complete"
        ),
        None,
    )
    if u1_event is None:
        return None
    u1_checkpoint = next(
        (
            checkpoint
            for checkpoint in checkpoints
            if checkpoint.get("boundary_kind") == "phase"
            and checkpoint.get("phase_id") == "U1"
        ),
        None,
    )
    if u1_checkpoint is None:
        raise RecoveryIntegrityError("U1 recovery checkpoint is unavailable")
    refs = u1_checkpoint.get("artifact_hashes")
    outputs = u1_event.get("output_artifact_hashes")
    expected_paths = (
        _U1_SOURCE_LOCK_PATH.as_posix(),
        _U1_READ_PLAN_PATH.as_posix(),
        _U1_SOURCE_COVERAGE_PATH.as_posix(),
    )
    if (
        not isinstance(refs, list)
        or len(refs) != 3
        or tuple(
            item.get("path") if isinstance(item, Mapping) else None for item in refs
        )
        != expected_paths
        or not isinstance(outputs, list)
        or len(outputs) != 3
        or [
            item.get("sha256") if isinstance(item, Mapping) else None
            for item in refs
        ]
        != outputs
        or u1_checkpoint.get("phase_event_sha256")
        != u1_event.get("event_sha256")
    ):
        raise RecoveryIntegrityError("U1 checkpoint authority paths are invalid")

    source_lock_path = layout.run_dir / _U1_SOURCE_LOCK_PATH
    source_coverage_path = layout.run_dir / _U1_SOURCE_COVERAGE_PATH
    read_plan_path = layout.run_dir / _U1_READ_PLAN_PATH
    read_events_path = layout.run_dir / _U1_READ_EVENTS_PATH
    try:
        for path in (
            source_lock_path,
            source_coverage_path,
            read_plan_path,
            read_events_path,
        ):
            assert_safe_descendant(layout.root, path)
            path.relative_to(layout.run_dir)
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError("U1 recovery authority path is invalid") from error

    try:
        source_lock = _read_canonical_object(source_lock_path)
    except RecoveryIntegrityError as error:
        raise RecoveryIntegrityError("U1 source lock is unavailable or invalid") from error
    try:
        read_plan = _read_canonical_object(read_plan_path)
    except RecoveryIntegrityError as error:
        raise RecoveryIntegrityError("U1 read plan is unavailable or invalid") from error
    try:
        source_coverage = _read_canonical_object(source_coverage_path)
    except RecoveryIntegrityError as error:
        raise RecoveryIntegrityError(
            "U1 source coverage is unavailable or invalid"
        ) from error
    raw_input_refs = authority.get("input_refs")
    if not isinstance(raw_input_refs, list):
        raise RecoveryIntegrityError("U1 input authority is invalid")
    recovery_inputs: list[dict[str, str]] = []
    for item in raw_input_refs:
        if not isinstance(item, Mapping):
            raise RecoveryIntegrityError("U1 recovery input authority is invalid")
        relative = Path(str(item.get("path")))
        try:
            input_relative = relative.relative_to("input")
        except ValueError as error:
            raise RecoveryIntegrityError(
                "U1 recovery input is outside the fixed input root"
            ) from error
        recovery_inputs.append(
            {
                "path": input_relative.as_posix(),
                "sha256": str(item.get("sha256")),
                "media_type": str(item.get("media_type")),
            }
        )
    if [item["sha256"] for item in recovery_inputs] != authority[
        "input_artifact_hashes"
    ]:
        raise RecoveryIntegrityError("U1 locked inputs differ from recovery authority")

    try:
        raw_read_events = read_events_path.read_bytes()
    except OSError as error:
        raise RecoveryIntegrityError("U1 read events are unavailable") from error
    if not raw_read_events or not raw_read_events.endswith(b"\n"):
        raise RecoveryIntegrityError("U1 read event journal is incomplete")
    read_events: list[dict[str, object]] = []
    for index, line in enumerate(raw_read_events.splitlines(keepends=True)):
        try:
            event = load_json_object_bytes(
                line,
                source=f"{read_events_path}:{index + 1}",
            )
        except (TypeError, ValueError) as error:
            raise RecoveryIntegrityError("U1 read event journal is invalid") from error
        if line != canonical_json_bytes(event):
            raise RecoveryIntegrityError("U1 read event journal is not canonical")
        read_events.append(event)

    from . import source_integrity

    validator = getattr(source_integrity, "_validate_persisted_u1_authority", None)
    if not callable(validator):
        raise RecoveryIntegrityError("U1 persisted authority validator is unavailable")
    try:
        manifest = source_integrity.load_source_manifest(
            store._source_repository
            / "skills"
            / "crossframe-ultra"
            / "references"
            / "source-manifest.json",
            expected_sha256=str(authority["source_sha256"]),
        )
        return validator(
            repo=store._source_repository,
            run_layout=layout,
            manifest=manifest,
            source_lock=source_lock,
            read_plan=read_plan,
            coverage=source_coverage,
            read_events=tuple(read_events),
            expected_run_id=store.run_id,
            expected_run_mode=str(store.run_contract["run_mode"]),
            expected_version_binding=authority["version_binding"],
            expected_parent_event_sha256=str(u1_event["parent_event_sha256"]),
            expected_evidence_cutoff=str(authority["evidence_cutoff"]),
            expected_inputs=tuple(recovery_inputs),
            expected_request_sha256=str(store.run_contract["request_sha256"]),
            expected_source_lock_sha256=str(outputs[0]),
            expected_read_plan_sha256=str(outputs[1]),
            expected_read_coverage_sha256=str(outputs[2]),
        )
    except Exception as error:
        raise RecoveryIntegrityError("U1 persisted authority validation failed") from error


def _restore_phase_store(
    layout: RunLayout,
    authority: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    checkpoints: Sequence[Mapping[str, object]],
    *,
    source_repository: Path | None = None,
) -> PhaseStore:
    contract_path = layout.artifacts_dir / "ultra-run-contract.json"
    try:
        raw = contract_path.read_bytes()
        artifact = load_json_object_bytes(raw, source=str(contract_path))
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError("run contract artifact is unavailable") from error
    if (
        raw != canonical_json_bytes(artifact)
        or sha256_bytes(raw) != authority.get("run_contract_sha256")
        or artifact.get("schema_id") != "crossframe.ultra.v82.run-contract"
        or artifact.get("schema_version") != 1
        or artifact.get("run_id") != authority.get("run_id")
        or artifact.get("version_binding") != authority.get("version_binding")
        or artifact.get("phase_id") != "U0"
    ):
        raise RecoveryIntegrityError("run contract artifact authority differs from recovery")
    try:
        validate_instance("ultra-run-contract.schema.json", artifact)
        generated_at = _parse_canonical_utc(
            artifact.get("generated_at"),
            "run contract generated_at",
        )
    except Exception as error:
        raise RecoveryIntegrityError("run contract artifact is invalid") from error
    contract_fields = (
        "trigger",
        "request_sha256",
        "analysis_kind",
        "capability_attestation_sha256",
        "run_mode",
        "sensitivity",
        "retention",
        "outbound_permission",
        "evidence_cutoff",
        "capabilities",
        "resource_limits",
    )
    contract = {field: copy.deepcopy(artifact[field]) for field in contract_fields}
    from .foundation import (
        FoundationInputError,
        load_host_capability_attestation,
    )

    try:
        capability_attestation = load_host_capability_attestation(
            layout,
            expected_request_sha256=str(contract["request_sha256"]),
            expected_version_binding=authority["version_binding"],
        )
    except FoundationInputError as error:
        raise RecoveryIntegrityError(
            "persisted host capability attestation is invalid"
        ) from error
    if (
        capability_attestation.artifact_sha256
        != contract["capability_attestation_sha256"]
    ):
        raise RecoveryIntegrityError(
            "persisted host capability attestation hash differs from contract"
        )
    selected_repository = (
        source_repository.resolve()
        if isinstance(source_repository, Path)
        else Path(__file__).resolve().parents[4]
    )
    u1_prerequisite_measurement = None
    u1_prerequisite_roles = None
    if source_repository is not None:
        from . import source_integrity

        try:
            run_mode = str(contract["run_mode"])
            source_lock_path = layout.run_dir / _U1_SOURCE_LOCK_PATH
            if source_lock_path.is_file():
                source_lock = _read_canonical_object(source_lock_path)
                validate_instance("ultra-source-lock.schema.json", source_lock)
                if (
                    source_lock.get("content_sha256")
                    != compute_artifact_content_sha256(source_lock)
                    or source_lock.get("run_id") != authority["run_id"]
                    or source_lock.get("version_binding")
                    != authority["version_binding"]
                    or source_lock.get("source_manifest_sha256")
                    != authority["source_sha256"]
                    or source_lock.get("input_snapshot_sha256")
                    != authority.get("input_snapshot_sha256")
                    or source_lock.get("lock_status") != "locked"
                ):
                    raise RecoveryIntegrityError(
                        "persisted U1 source lock cannot restore prerequisite roles"
                    )
                free_space_status = (
                    "available"
                    if shutil.disk_usage(selected_repository).free
                    >= source_integrity.MIN_FREE_SPACE_RESERVE_BYTES
                    else "insufficient"
                )
                u1_prerequisite_roles = {
                    "run_mode": run_mode,
                    "source_release_id": source_lock["source_release_id"],
                    "source_manifest_sha256": source_lock[
                        "source_manifest_sha256"
                    ],
                    "release_manifest_sha256": source_lock[
                        "release_manifest_sha256"
                    ],
                    "compatibility_matrix_sha256": source_lock[
                        "compatibility_matrix_sha256"
                    ],
                    "knowledge_report_sha256": source_lock[
                        "knowledge_report_sha256"
                    ],
                    "skill_tree_sha256": source_lock["skill_tree_sha256"],
                    "free_space_reserve_bytes": source_integrity.MIN_FREE_SPACE_RESERVE_BYTES,
                    "free_space_status": free_space_status,
                }
            else:
                manifest = source_integrity.load_source_manifest(
                    selected_repository
                    / "skills"
                    / "crossframe-ultra"
                    / "references"
                    / "source-manifest.json",
                    expected_sha256=str(authority["source_sha256"]),
                )
                u1_prerequisite_measurement = source_integrity.measure_u1_prerequisites(
                    selected_repository,
                    manifest=manifest,
                    release_manifest_path=(
                        selected_repository
                        / "skills"
                        / "crossframe-ultra"
                        / "references"
                        / "release-manifest.json"
                        if run_mode == "test"
                        else None
                    ),
                    run_mode=run_mode,
                )
        except Exception as error:
            raise RecoveryIntegrityError(
                "U1 prerequisite authority cannot be restored"
            ) from error
    try:
        store = PhaseStore(
            run_id=str(authority["run_id"]),
            version_binding=authority["version_binding"],
            source_sha256=str(authority["source_sha256"]),
            input_artifact_hashes=authority["input_artifact_hashes"],
            input_snapshot_sha256=authority.get("input_snapshot_sha256"),
            evidence_cutoff=str(authority["evidence_cutoff"]),
            now=generated_at,
            run_contract=contract,
            capability_attestation=capability_attestation,
            source_repository=selected_repository,
            u1_prerequisite_measurement=u1_prerequisite_measurement,
            u1_prerequisite_roles=u1_prerequisite_roles,
            run_layout=layout,
        )
        if store.run_contract_artifact_sha256 != authority["run_contract_sha256"]:
            raise RecoveryIntegrityError("restored run contract hash differs")
        u3_event = next(
            (
                event
                for event in events
                if event.get("phase_id") == "U3" and event.get("status") == "complete"
            ),
            None,
        )
        if u3_event is not None:
            u3_checkpoint = next(
                (
                    item
                    for item in checkpoints
                    if item.get("boundary_kind") == "phase"
                    and item.get("phase_id") == "U3"
                ),
                None,
            )
            if u3_checkpoint is None:
                raise RecoveryIntegrityError("U3 recovery checkpoint is unavailable")
            outputs = u3_event.get("output_artifact_hashes")
            refs = u3_checkpoint.get("artifact_hashes")
            if not isinstance(outputs, list) or not isinstance(refs, list):
                raise RecoveryIntegrityError("U3 recovery authority is invalid")
            evidence_refs = [
                item
                for item in refs
                if isinstance(item, Mapping) and item.get("sha256") in outputs
            ]
            if len(evidence_refs) != 1:
                raise RecoveryIntegrityError("U3 evidence artifact authority is ambiguous")
            evidence_path = layout.run_dir / Path(str(evidence_refs[0]["path"]))
            evidence_document = load_json_object(evidence_path)
            validate_phase_artifact(
                "ultra-evidence-ledger.schema.json",
                evidence_document,
                expected_schema_id="crossframe.ultra.v82.evidence-ledger",
                expected_run_id=store.run_id,
                expected_version_binding=current_version_binding(),
                expected_phase_id="U3",
            )
            entries = evidence_document.get("entries")
            unknowns = evidence_document.get("unknowns")
            if not isinstance(entries, list) or not isinstance(unknowns, list):
                raise RecoveryIntegrityError("U3 evidence artifact payload is invalid")
            for entry in entries:
                store._evidence_ledger.append(entry)
            for unknown in unknowns:
                store._evidence_ledger.append_unknown(unknown)
            store._evidence_ledger.freeze()
            if (
                store.evidence_artifact != evidence_document
                or store.evidence_sha256 not in outputs
            ):
                raise RecoveryIntegrityError("restored U3 evidence hash differs")
        u1_authority = _validated_u1_recovery_authority(
            layout,
            authority,
            events,
            checkpoints,
            store,
        )
        store._restore_validated_recovery_events(
            events,
            u1_authority=u1_authority,
        )
    except RecoveryIntegrityError:
        raise
    except Exception as error:
        raise RecoveryIntegrityError("PhaseStore recovery hydration failed") from error
    return store


def create_checkpoint(
    layout: RunLayout,
    phase_store: PhaseStore,
    *,
    boundary_kind: Literal["phase", "article-packet"],
    boundary_id: str,
    boundary_ordinal: int,
    artifact_paths: Sequence[Path],
    now: datetime,
) -> dict[str, object]:
    _validate_layout(layout)
    timestamp = _iso_utc(now)
    authority = _authority_from_store(layout, phase_store)
    events = phase_store.events
    if not events or events[-1].get("status") != "complete":
        raise RecoveryStateError("checkpoint requires a completed phase event chain head")
    compatibility = resolve_compatibility(
        authority["version_binding"], current_version_binding()
    )
    if compatibility != "resume":
        raise RecoveryCompatibilityError("new checkpoints require exact current versions")
    _validate_event_chain(events, authority, compatibility=compatibility)
    refs = _artifact_refs(layout, artifact_paths)
    if boundary_kind == "phase":
        phase_id = phase_store.current_phase
        if (
            phase_id is None
            or boundary_id != phase_id
            or boundary_ordinal != 0
            or events[-1].get("phase_id") != phase_id
            or [item["sha256"] for item in refs]
            != events[-1].get("output_artifact_hashes")
        ):
            raise RecoveryIntegrityError("phase checkpoint boundary differs from PhaseStore")
        if phase_id == "U1":
            if tuple(item["path"] for item in refs) != (
                _U1_SOURCE_LOCK_PATH.as_posix(),
                _U1_READ_PLAN_PATH.as_posix(),
                _U1_SOURCE_COVERAGE_PATH.as_posix(),
            ):
                raise RecoveryIntegrityError(
                    "U1 checkpoint must use the fixed recovery authority paths"
                )
            accepted = phase_store._accepted_u1_snapshot()
            if [item["sha256"] for item in refs] != [
                accepted["source_lock_artifact_sha256"],
                accepted["read_plan_artifact_sha256"],
                accepted["read_coverage_artifact_sha256"],
            ]:
                raise RecoveryIntegrityError(
                    "U1 checkpoint hashes differ from accepted source authority"
                )
    elif boundary_kind == "article-packet":
        phase_id = "U11"
        if (
            phase_store.current_phase != "U10"
            or not isinstance(boundary_id, str)
            or _IDENTIFIER_RE.fullmatch(boundary_id) is None
            or type(boundary_ordinal) is not int
            or boundary_ordinal < 1
            or "work/authoring/article.partial.md" not in {item["path"] for item in refs}
        ):
            raise RecoveryIntegrityError("article packet checkpoint boundary is invalid")
    else:
        raise ValueError("boundary_kind must be 'phase' or 'article-packet'")
    status = _status_if_present(layout)
    if status is not None and status.status in {"cancelled", "failed"}:
        raise RecoveryStateError("terminal run cannot create a checkpoint")
    if status is not None and status.status == "complete" and phase_id != "U12":
        raise RecoveryStateError("completed run cannot create a non-U12 checkpoint")
    checkpoint: dict[str, object] = {
        "schema_id": _CHECKPOINT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": phase_store.run_id,
        "version_binding": copy.deepcopy(phase_store._version_binding),
        "generated_at": timestamp,
        "content_sha256": "0" * 64,
        "phase_id": phase_id,
        "boundary_kind": boundary_kind,
        "boundary_id": boundary_id,
        "boundary_ordinal": boundary_ordinal,
        "phase_event_sha256": events[-1]["event_sha256"],
        "artifact_hashes": refs,
        "evidence_cutoff": phase_store.evidence_cutoff,
        "completed_boundary": True,
        "resumable": True,
    }
    checkpoint["content_sha256"] = compute_artifact_content_sha256(checkpoint)
    try:
        validate_phase_artifact(
            _CHECKPOINT_SCHEMA,
            checkpoint,
            expected_schema_id=_CHECKPOINT_SCHEMA_ID,
            expected_run_id=phase_store.run_id,
            expected_version_binding=current_version_binding(),
            expected_phase_id=str(phase_id),
        )
    except Exception as error:
        raise RecoveryIntegrityError("checkpoint violates the public schema") from error
    checkpoints_dir, _, authority_path, events_path, lock_path = _paths(layout)
    with _exclusive_path_lock(lock_path):
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        if authority_path.exists():
            existing = _read_canonical_object(authority_path)
            if existing != authority:
                raise RecoveryIntegrityError("immutable run recovery authority changed")
        else:
            _write_immutable(authority_path, authority)
        _sync_events(events_path, events)
        existing, _, _, _ = _load_checkpoints_unlocked(layout)
        slot = _checkpoint_slot(checkpoint)
        if any(_checkpoint_slot(item) == slot and item != checkpoint for item in existing):
            raise RecoveryIntegrityError("duplicate logical checkpoint slot")
        raw = canonical_json_bytes(checkpoint)
        checkpoint_hash = sha256_bytes(raw)
        target = checkpoints_dir / f"{checkpoint_hash}.json"
        _write_immutable(target, checkpoint)
    return copy.deepcopy(checkpoint)


def load_checkpoints(layout: RunLayout) -> tuple[dict[str, object], ...]:
    _validate_layout(layout)
    checkpoints, _, _, _ = _load_checkpoints_unlocked(layout)
    return tuple(copy.deepcopy(item) for item in checkpoints)


def _select_latest(
    checkpoints: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    candidates = [
        copy.deepcopy(dict(item))
        for item in checkpoints
        if item.get("completed_boundary") is True and item.get("resumable") is True
    ]
    if not candidates:
        raise RecoveryStateError("no completed resumable checkpoint is available")
    return max(candidates, key=_checkpoint_sort_key)


def select_resume_checkpoint(layout: RunLayout) -> dict[str, object]:
    _validate_layout(layout)
    checkpoints, _, compatibility, _ = _load_checkpoints_unlocked(layout)
    if compatibility != "resume":
        raise RecoveryCompatibilityError(
            f"checkpoint compatibility is {compatibility}, not resume"
        )
    return _select_latest(checkpoints)


def resume_run(
    layout: RunLayout,
    *,
    now: datetime,
    source_repository: Path | None = None,
) -> RecoveryResult:
    _validate_layout(layout)
    _require_utc(now, "now")
    checkpoints, authority, compatibility, events = _load_checkpoints_unlocked(layout)
    status = _status_if_present(layout)
    if compatibility in {"read-only", "fork-required"}:
        return RecoveryResult(
            outcome=compatibility,
            compatibility_result=compatibility,
            checkpoint=None,
            status=status,
            phase_store=None,
        )
    if compatibility != "resume":
        raise RecoveryCompatibilityError("checkpoint compatibility rejects recovery")
    if status is None:
        raise RecoveryStateError("run status authority is unavailable")
    if status.status in {"cancelled", "failed", "complete"}:
        raise RecoveryStateError(f"{status.status} run is terminal and cannot resume")
    checkpoint = _select_latest(checkpoints)
    checkpoint_event_sha256 = checkpoint.get("phase_event_sha256")
    try:
        checkpoint_event_ordinal = next(
            index
            for index, event in enumerate(events)
            if event.get("event_sha256") == checkpoint_event_sha256
        )
    except StopIteration as error:
        raise RecoveryIntegrityError(
            "resume checkpoint phase event is unavailable"
        ) from error
    durable_events = events[: checkpoint_event_ordinal + 1]
    phase_store = _restore_phase_store(
        layout,
        authority,
        durable_events,
        checkpoints,
        source_repository=source_repository,
    )
    if status.status == "running":
        resumed = status
    else:
        phase_id = str(checkpoint["phase_id"])
        last_complete = "U10" if checkpoint["boundary_kind"] == "article-packet" else phase_id
        try:
            resumed = RunStatusStore(layout).transition(
                status,
                "running",
                now,
                current_phase=phase_id,
                last_complete_phase=last_complete,
                reason="resumed from immutable checkpoint",
            )
        except Exception as error:
            raise RecoveryStateError("run status cannot resume from the checkpoint") from error
    return RecoveryResult(
        outcome="resume",
        compatibility_result="resume",
        checkpoint=checkpoint,
        status=resumed,
        phase_store=phase_store,
    )


def _terminal_event(
    authority: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    *,
    reason: str,
    now: datetime,
) -> dict[str, object]:
    completed = sum(event.get("status") == "complete" for event in events)
    if completed >= len(PHASES):
        raise RecoveryStateError("completed U12 run cannot be cancelled")
    timestamp = _iso_utc(now)
    try:
        prior_time = _parse_canonical_utc(events[-1].get("timestamp"), "phase event timestamp")
    except ValueError as error:
        raise RecoveryIntegrityError("phase event timestamp is invalid") from error
    if now <= prior_time:
        raise RecoveryStateError("cancellation time must advance after the phase event")
    event: dict[str, object] = {
        "schema_id": PHASE_EVENT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": authority["run_id"],
        "version_binding": copy.deepcopy(authority["version_binding"]),
        "generated_at": timestamp,
        "content_sha256": "0" * 64,
        "phase_id": PHASES[completed],
        "event_type": "phase-cancelled",
        "parent_event_sha256": events[-1]["event_sha256"],
        "input_artifact_hashes": copy.deepcopy(authority["input_artifact_hashes"]),
        "output_artifact_hashes": [],
        "source_sha256": authority["source_sha256"],
        "evidence_cutoff": authority["evidence_cutoff"],
        "run_contract_sha256": authority["run_contract_sha256"],
        "timestamp": timestamp,
        "status": "cancelled",
        "failure_code": reason,
        "invalidated_phases": [],
        "event_sha256": "0" * 64,
    }
    event["content_sha256"] = _compute_event_content_sha256(event)
    event["event_sha256"] = compute_event_sha256(event)
    try:
        validate_instance("ultra-phase-event.schema.json", event)
    except Exception as error:
        raise RecoveryIntegrityError("cancellation event violates the public schema") from error
    return event


def cancel_run(
    layout: RunLayout,
    *,
    reason: str,
    now: datetime,
) -> RunStatusRecord:
    _validate_layout(layout)
    _require_utc(now, "now")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("cancellation reason must be non-empty")
    checkpoints, authority, compatibility, events = _load_checkpoints_unlocked(layout)
    if compatibility == "reject":
        raise RecoveryCompatibilityError("unsupported run cannot be cancelled")
    status = _status_if_present(layout)
    if status is None:
        raise RecoveryStateError("run status authority is unavailable")
    if status.status in {"failed", "complete"}:
        raise RecoveryStateError(f"{status.status} run is terminal and cannot be cancelled")
    if not checkpoints and not authority and not events:
        if status.current_phase != "U0" or status.last_complete_phase is not None:
            raise RecoveryIntegrityError("status-only cancellation requires pre-U0 authority")
        if status.status == "cancelled":
            return status
        try:
            return RunStatusStore(layout).transition(
                status,
                "cancelled",
                now,
                reason=reason.strip(),
            )
        except Exception as error:
            raise RecoveryStateError("run status cancellation transition failed") from error
    if status.status == "cancelled":
        if events[-1].get("status") != "cancelled":
            raise RecoveryIntegrityError("cancelled status lacks terminal phase authority")
        return status
    completed_events = [item for item in events if item.get("status") == "complete"]
    last_complete_phase = (
        None if not completed_events else str(completed_events[-1]["phase_id"])
    )
    if events[-1].get("status") == "cancelled":
        event = events[-1]
        try:
            return RunStatusStore(layout).transition(
                status,
                "cancelled",
                now,
                current_phase=str(event["phase_id"]),
                last_complete_phase=last_complete_phase,
                reason=str(event["failure_code"]),
            )
        except Exception as error:
            raise RecoveryStateError("run status cancellation transition failed") from error
    if events[-1].get("status") != "complete":
        raise RecoveryStateError("run already has a terminal phase event")
    event = _terminal_event(authority, events, reason=reason.strip(), now=now)
    _, _, _, events_path, lock_path = _paths(layout)
    with _exclusive_path_lock(lock_path):
        _sync_events(events_path, (*events, event))
    try:
        return RunStatusStore(layout).transition(
            status,
            "cancelled",
            now,
            current_phase=str(event["phase_id"]),
            last_complete_phase=last_complete_phase,
            reason=reason.strip(),
        )
    except Exception as error:
        raise RecoveryStateError("run status cancellation transition failed") from error


def _copy_verified_ref(
    parent_layout: RunLayout,
    child_layout: RunLayout,
    ref: Mapping[str, object],
) -> dict[str, str]:
    validated = _validate_disk_ref(parent_layout, ref, role="inherited")
    relative = Path(validated["path"])
    source = parent_layout.run_dir / relative
    target = child_layout.run_dir / relative
    try:
        assert_safe_descendant(child_layout.root, target)
        raw = source.read_bytes()
    except (OSError, TypeError, ValueError) as error:
        raise RecoveryIntegrityError("inherited artifact cannot be copied safely") from error
    if hashlib.sha256(raw).hexdigest() != validated["sha256"]:
        raise RecoveryIntegrityError("inherited artifact changed during fork")
    if target.exists():
        try:
            if target.read_bytes() != raw:
                raise RecoveryIntegrityError("child inherited artifact path collision")
        except OSError as error:
            raise RecoveryIntegrityError("child inherited artifact is unreadable") from error
    else:
        atomic_write_bytes(target, raw)
    return validated


def fork_run(
    parent_layout: RunLayout,
    *,
    mode: RunMode,
    policy: RootPolicy,
    reason: str,
    now: datetime,
    entropy: bytes,
) -> ForkResult:
    _validate_layout(parent_layout)
    _require_utc(now, "now")
    if not isinstance(mode, RunMode):
        raise TypeError("mode must be a RunMode")
    if not isinstance(policy, RootPolicy):
        raise TypeError("policy must be a RootPolicy")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("fork reason must be non-empty")
    if not isinstance(entropy, bytes):
        raise TypeError("entropy must be bytes")
    checkpoints, authority, compatibility, _ = _load_checkpoints_unlocked(parent_layout)
    if compatibility != "fork-required":
        raise RecoveryCompatibilityError(
            "recovery fork is allowed only for a fork-required version migration"
        )
    parent_checkpoint = _select_latest(checkpoints)
    child_run_id = create_run_id(now, entropy)
    child_layout = build_run_layout(mode, child_run_id, policy)
    if child_layout.run_dir.exists():
        raise RecoveryStateError("fork child run already exists")
    raw_input_refs = authority.get("input_refs")
    raw_inherited = parent_checkpoint.get("artifact_hashes")
    if not isinstance(raw_input_refs, list) or not raw_input_refs:
        raise RecoveryIntegrityError("fork parent has no frozen input refs")
    if not isinstance(raw_inherited, list) or not raw_inherited:
        raise RecoveryIntegrityError("fork parent has no inherited artifacts")
    frozen_input_refs = [
        _copy_verified_ref(parent_layout, child_layout, ref) for ref in raw_input_refs
    ]
    inherited_refs = [
        _copy_verified_ref(parent_layout, child_layout, ref) for ref in raw_inherited
    ]
    RunStatusStore(child_layout).create(now)
    checkpoint_sha256 = sha256_bytes(canonical_json_bytes(parent_checkpoint))
    migration: dict[str, object] = {
        "schema_id": _MIGRATION_SCHEMA_ID,
        "schema_version": 1,
        "run_id": child_run_id,
        "version_binding": current_version_binding(),
        "generated_at": _iso_utc(now),
        "content_sha256": "0" * 64,
        "parent_run_id": parent_layout.run_dir.name,
        "parent_checkpoint_sha256": checkpoint_sha256,
        "parent_version_binding": copy.deepcopy(authority["version_binding"]),
        "compatibility_result": "fork-required",
        "fork_reason": reason.strip(),
        "frozen_input_refs": frozen_input_refs,
        "inherited_artifact_hashes": inherited_refs,
    }
    migration["content_sha256"] = compute_artifact_content_sha256(migration)
    try:
        validate_instance(_MIGRATION_SCHEMA, migration)
    except Exception as error:
        raise RecoveryIntegrityError("fork migration artifact violates the public schema") from error
    migration_path = child_layout.recovery_dir / "ultra-run-migration.json"
    assert_safe_descendant(child_layout.root, migration_path)
    atomic_write_json(migration_path, migration)
    return ForkResult(
        run_id=child_run_id,
        layout=child_layout,
        parent_checkpoint=copy.deepcopy(parent_checkpoint),
        migration=copy.deepcopy(migration),
    )


__all__ = (
    "ForkResult",
    "RecoveryCompatibilityError",
    "RecoveryError",
    "RecoveryIntegrityError",
    "RecoveryResult",
    "RecoveryStateError",
    "cancel_run",
    "create_checkpoint",
    "fork_run",
    "load_checkpoints",
    "resume_run",
    "select_resume_checkpoint",
)
