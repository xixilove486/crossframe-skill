from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

from .constants import PHASES, RUN_STATUSES, current_version_binding
from .errors import UltraRuntimeError
from .jsonio import (
    AUTHORITY_SNAPSHOT_LOCK_FILENAME,
    RUN_LIFECYCLE_LOCK_FILENAME,
    _exclusive_path_lock,
    atomic_write_json,
    load_json_object,
)
from .paths import (
    RunLayout,
    _parse_canonical_utc,
    _require_utc,
    _validate_run_id,
    assert_safe_descendant,
)
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


RUN_STATUS_TRANSITIONS = {
    "created": frozenset(
        {"running", "blocked", "needs_attention", "failed", "cancelled"}
    ),
    "running": frozenset(
        {
            "interrupted",
            "blocked",
            "needs_attention",
            "failed",
            "cancelled",
            "complete",
        }
    ),
    "interrupted": frozenset(
        {"running", "blocked", "needs_attention", "failed", "cancelled"}
    ),
    "blocked": frozenset(
        {"running", "interrupted", "needs_attention", "failed", "cancelled"}
    ),
    "needs_attention": frozenset(
        {"running", "interrupted", "blocked", "failed", "cancelled"}
    ),
    "failed": frozenset(),
    "cancelled": frozenset(),
    "complete": frozenset(),
}

_RUN_STATUS_SCHEMA = "ultra-run-status.schema.json"
_RUN_STATUS_SCHEMA_ID = "crossframe.ultra.v82.run-status"
_UNSET = object()
_U12_COMPLETE_AUTHORITY = object()
_REPAIR_REOPEN_AUTHORITY = object()


class RunStatusError(UltraRuntimeError, RuntimeError):
    pass


class RunStatusConflictError(RunStatusError):
    pass


class RunStatusTransitionError(RunStatusError):
    pass


@dataclass(frozen=True, slots=True)
class RunStatusRecord:
    schema_id: str
    schema_version: int
    run_id: str
    version_binding: Mapping[str, object]
    generated_at: str
    content_sha256: str
    phase_id: str
    status: str
    previous_status: str | None
    current_phase: str
    last_complete_phase: str | None
    reason: str | None
    tools_allowed: bool
    validation_passed: bool
    updated_at: str
    created_at: str
    revision: int


_STATUS_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "generated_at",
        "content_sha256",
        "phase_id",
        "status",
        "previous_status",
        "current_phase",
        "last_complete_phase",
        "reason",
        "tools_allowed",
        "validation_passed",
        "updated_at",
        "created_at",
        "revision",
    }
)


def _iso_utc(value: datetime) -> str:
    _require_utc(value, "time")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _parse_utc(value: object, field: str) -> datetime:
    try:
        return _parse_canonical_utc(value, f"status field {field}")
    except ValueError as error:
        raise ValueError(
            f"status field {field} must be a canonical UTC timestamp"
        ) from error


def _record_to_object(record: RunStatusRecord) -> dict[str, object]:
    return {
        "schema_id": record.schema_id,
        "schema_version": record.schema_version,
        "run_id": record.run_id,
        "version_binding": dict(record.version_binding),
        "generated_at": record.generated_at,
        "content_sha256": record.content_sha256,
        "phase_id": record.phase_id,
        "status": record.status,
        "previous_status": record.previous_status,
        "current_phase": record.current_phase,
        "last_complete_phase": record.last_complete_phase,
        "reason": record.reason,
        "tools_allowed": record.tools_allowed,
        "validation_passed": record.validation_passed,
        "updated_at": record.updated_at,
        "created_at": record.created_at,
        "revision": record.revision,
    }


def _record_from_object(
    value: dict[str, object], expected_run_id: str
) -> RunStatusRecord:
    if set(value) != _STATUS_FIELDS:
        unexpected = sorted(set(value) - _STATUS_FIELDS)
        missing = sorted(_STATUS_FIELDS - set(value))
        raise ValueError(
            f"run status must be a closed object; unexpected={unexpected}, missing={missing}"
        )
    current_phase = value["current_phase"]
    if not isinstance(current_phase, str) or current_phase not in PHASES:
        raise ValueError(f"run status current_phase must be one of {PHASES}")
    created_at = _parse_utc(value["created_at"], "created_at")
    updated_at = _parse_utc(value["updated_at"], "updated_at")
    _parse_utc(value["generated_at"], "generated_at")
    try:
        snapshot = validate_phase_artifact(
            _RUN_STATUS_SCHEMA,
            value,
            expected_schema_id=_RUN_STATUS_SCHEMA_ID,
            expected_run_id=expected_run_id,
            expected_version_binding=current_version_binding(),
            expected_phase_id=current_phase,
        )
    except Exception as error:
        raise ValueError(f"run status authority is invalid: {error}") from error

    if snapshot["phase_id"] != snapshot["current_phase"]:
        raise ValueError("run status phase_id must equal current_phase")
    if snapshot["generated_at"] != snapshot["updated_at"]:
        raise ValueError("run status generated_at must equal updated_at")
    if updated_at < created_at:
        raise ValueError("run status updated_at cannot precede created_at")
    last_complete_phase = snapshot["last_complete_phase"]
    if last_complete_phase is not None and PHASES.index(last_complete_phase) > PHASES.index(
        current_phase
    ):
        raise ValueError("run status last_complete_phase cannot exceed current_phase")

    return RunStatusRecord(
        schema_id=str(snapshot["schema_id"]),
        schema_version=int(snapshot["schema_version"]),
        run_id=str(snapshot["run_id"]),
        version_binding=MappingProxyType(dict(snapshot["version_binding"])),
        generated_at=str(snapshot["generated_at"]),
        content_sha256=str(snapshot["content_sha256"]),
        phase_id=str(snapshot["phase_id"]),
        status=str(snapshot["status"]),
        previous_status=(
            None
            if snapshot["previous_status"] is None
            else str(snapshot["previous_status"])
        ),
        current_phase=current_phase,
        last_complete_phase=(
            None if last_complete_phase is None else str(last_complete_phase)
        ),
        reason=None if snapshot["reason"] is None else str(snapshot["reason"]),
        tools_allowed=bool(snapshot["tools_allowed"]),
        validation_passed=bool(snapshot["validation_passed"]),
        updated_at=str(snapshot["updated_at"]),
        created_at=str(snapshot["created_at"]),
        revision=int(snapshot["revision"]),
    )


def _validate_record(record: RunStatusRecord, expected_run_id: str) -> None:
    if not isinstance(record, RunStatusRecord):
        raise TypeError("status record must be a RunStatusRecord")
    _record_from_object(_record_to_object(record), expected_run_id)


def _make_record(
    *,
    run_id: str,
    status: str,
    previous_status: str | None,
    current_phase: str,
    last_complete_phase: str | None,
    reason: str | None,
    validation_passed: bool,
    created_at: str,
    updated_at: str,
    revision: int,
) -> RunStatusRecord:
    value: dict[str, object] = {
        "schema_id": _RUN_STATUS_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": current_version_binding(),
        "generated_at": updated_at,
        "content_sha256": "0" * 64,
        "phase_id": current_phase,
        "status": status,
        "previous_status": previous_status,
        "current_phase": current_phase,
        "last_complete_phase": last_complete_phase,
        "reason": reason,
        "tools_allowed": status == "running",
        "validation_passed": validation_passed,
        "updated_at": updated_at,
        "created_at": created_at,
        "revision": revision,
    }
    value["content_sha256"] = compute_artifact_content_sha256(value)
    return _record_from_object(value, run_id)


class RunStatusStore:
    def __init__(self, layout: RunLayout):
        if not isinstance(layout, RunLayout):
            raise TypeError("layout must be a RunLayout")
        _validate_run_id(layout.run_dir.name)
        self.layout = layout
        self.path = layout.run_dir / "run-status.json"
        self.authority_lock_path = (
            layout.root / AUTHORITY_SNAPSHOT_LOCK_FILENAME
        )
        self.lifecycle_lock_path = layout.run_dir / RUN_LIFECYCLE_LOCK_FILENAME
        self.lock_path = layout.run_dir / ".run-status.lock"
        self._assert_paths_safe()

    def _assert_paths_safe(self) -> None:
        assert_safe_descendant(self.layout.root, self.path)
        assert_safe_descendant(self.layout.root, self.authority_lock_path)
        assert_safe_descendant(self.layout.root, self.lifecycle_lock_path)
        assert_safe_descendant(self.layout.root, self.lock_path)

    def read(self) -> RunStatusRecord:
        self._assert_paths_safe()
        value = load_json_object(self.path)
        return _record_from_object(value, self.layout.run_dir.name)

    def create(self, now: datetime) -> RunStatusRecord:
        _require_utc(now, "now")
        self._assert_paths_safe()
        timestamp = _iso_utc(now)
        record = _make_record(
            run_id=self.layout.run_dir.name,
            status="created",
            previous_status=None,
            current_phase="U0",
            last_complete_phase=None,
            reason=None,
            validation_passed=False,
            created_at=timestamp,
            updated_at=timestamp,
            revision=0,
        )
        with _exclusive_path_lock(self.authority_lock_path):
            self._assert_paths_safe()
            self.layout.run_dir.mkdir(parents=True, exist_ok=True)
            self._assert_paths_safe()
            with _exclusive_path_lock(self.lifecycle_lock_path):
                self._assert_paths_safe()
                with _exclusive_path_lock(self.lock_path):
                    self._assert_paths_safe()
                    if self.path.exists():
                        raise RunStatusConflictError("run status already exists")
                    atomic_write_json(self.path, _record_to_object(record))
        return record

    def _replace(
        self,
        expected: RunStatusRecord,
        replacement: RunStatusRecord,
        *,
        completion_authority: object | None = None,
        repair_authority: object | None = None,
        lease: object | None = None,
    ) -> RunStatusRecord:
        run_id = self.layout.run_dir.name
        _validate_record(expected, run_id)
        _validate_record(replacement, run_id)
        completing = replacement.status == "complete"
        repairing = repair_authority is _REPAIR_REOPEN_AUTHORITY
        if completion_authority is not None and repair_authority is not None:
            raise RunStatusTransitionError(
                "completion and repair authorities are mutually exclusive"
            )
        if repair_authority is not None and not repairing:
            raise RunStatusTransitionError("repair reopen authority is invalid")
        if completing and completion_authority is not _U12_COMPLETE_AUTHORITY:
            raise RunStatusTransitionError(
                "ordinary status replacement cannot complete outside the durable U12 closure"
            )
        if not completing and completion_authority is not None:
            raise RunStatusTransitionError(
                "U12 completion authority cannot be used for an ordinary replacement"
            )
        if (
            replacement.schema_id != expected.schema_id
            or replacement.schema_version != expected.schema_version
            or replacement.run_id != expected.run_id
            or replacement.version_binding != expected.version_binding
            or replacement.created_at != expected.created_at
        ):
            raise RunStatusTransitionError(
                "schema, run, version, and created_at authority are immutable"
            )
        if replacement.revision != expected.revision + 1:
            raise RunStatusTransitionError("replacement revision must advance by one")
        if replacement.previous_status != expected.status:
            raise RunStatusTransitionError(
                "replacement previous_status must equal the previous status authority"
            )
        expected_updated = _parse_utc(expected.updated_at, "updated_at")
        replacement_updated = _parse_utc(replacement.updated_at, "updated_at")
        if replacement_updated <= expected_updated:
            raise RunStatusTransitionError(
                "replacement updated_at must advance monotonically after the old value"
            )
        if not repairing and PHASES.index(replacement.current_phase) < PHASES.index(
            expected.current_phase
        ):
            raise RunStatusTransitionError("current_phase cannot move backwards")
        if not repairing and expected.last_complete_phase is not None and (
            replacement.last_complete_phase is None
            or PHASES.index(replacement.last_complete_phase)
            < PHASES.index(expected.last_complete_phase)
        ):
            raise RunStatusTransitionError("last_complete_phase cannot move backwards")
        allowed = RUN_STATUS_TRANSITIONS[expected.status]
        allowed_completion = completing and expected.status == "running"
        allowed_repair = (
            repairing
            and expected.status not in {"complete", "failed", "cancelled"}
            and replacement.status == "running"
            and replacement.validation_passed is False
        )
        if not allowed_completion and not allowed_repair and replacement.status not in allowed:
            terminal = expected.status in {"complete", "failed", "cancelled"}
            qualifier = "terminal " if terminal else ""
            raise RunStatusTransitionError(
                f"illegal transition from {qualifier}{expected.status} to {replacement.status}"
            )

        self._assert_paths_safe()
        with _exclusive_path_lock(self.authority_lock_path):
            self._assert_paths_safe()
            with _exclusive_path_lock(self.lifecycle_lock_path):
                self._assert_paths_safe()
                from .locks import LeaseOwnershipError, _read_lease, _require_owner

                if lease is None:
                    raise LeaseOwnershipError(
                        "status mutation requires the current writer lease"
                    )
                _require_owner(_read_lease(self.layout), lease)
                with _exclusive_path_lock(self.lock_path):
                    self._assert_paths_safe()
                    current = self.read()
                    if (
                        current.revision != expected.revision
                        or current.updated_at != expected.updated_at
                        or current != expected
                    ):
                        raise RunStatusConflictError(
                            "status CAS rejected stale revision or updated_at"
                        )
                    atomic_write_json(self.path, _record_to_object(replacement))
        return replacement

    def replace(
        self,
        expected: RunStatusRecord,
        replacement: RunStatusRecord,
        *,
        lease: object | None = None,
    ) -> RunStatusRecord:
        run_id = self.layout.run_dir.name
        _validate_record(expected, run_id)
        _validate_record(replacement, run_id)
        if lease is not None:
            return self._replace(expected, replacement, lease=lease)
        from .locks import acquire_run_lease, release_run_lease

        owned = acquire_run_lease(
            self.layout,
            _parse_utc(replacement.updated_at, "updated_at"),
            timedelta(minutes=5),
        )
        try:
            return self._replace(expected, replacement, lease=owned)
        finally:
            release_run_lease(self.layout, owned)

    def transition(
        self,
        expected: RunStatusRecord,
        status: str,
        now: datetime,
        *,
        current_phase: str | None = None,
        last_complete_phase: str | None | object = _UNSET,
        reason: str | None = None,
        validation_passed: bool = False,
        lease: object | None = None,
    ) -> RunStatusRecord:
        _require_utc(now, "now")
        if not isinstance(status, str) or status not in RUN_STATUSES:
            raise ValueError(f"unknown run status: {status!r}")
        if not isinstance(validation_passed, bool):
            raise TypeError("validation_passed must be a boolean")
        if status == "complete":
            raise RunStatusTransitionError(
                "ordinary status transition cannot complete outside the durable U12 closure"
            )
        target_phase = expected.current_phase if current_phase is None else current_phase
        target_last_complete = (
            expected.last_complete_phase
            if last_complete_phase is _UNSET
            else last_complete_phase
        )
        replacement = _make_record(
            run_id=expected.run_id,
            status=status,
            previous_status=expected.status,
            current_phase=target_phase,
            last_complete_phase=target_last_complete,
            reason=reason,
            validation_passed=validation_passed,
            created_at=expected.created_at,
            updated_at=_iso_utc(now),
            revision=expected.revision + 1,
        )
        return self.replace(expected, replacement, lease=lease)

    def reopen_for_repair(
        self,
        expected: RunStatusRecord,
        now: datetime,
        *,
        reset_from_phase: str,
        invalidation_event_sha256: str,
        generation: int,
        lease: object,
    ) -> RunStatusRecord:
        _require_utc(now, "now")
        _validate_record(expected, self.layout.run_dir.name)
        if reset_from_phase not in PHASES:
            raise ValueError("repair reset phase is outside U0-U12")
        if not isinstance(invalidation_event_sha256, str):
            raise TypeError("repair invalidation event SHA-256 must be a string")
        if type(generation) is not int or generation < 1:
            raise ValueError("repair generation must be a positive integer")
        from . import recovery

        authority, compatibility, _ = recovery._validate_authority_record(self.layout)
        events = recovery._read_events(
            self.layout,
            authority,
            compatibility=compatibility,
        )
        matches = [
            event
            for event in events
            if event.get("event_sha256") == invalidation_event_sha256
        ]
        if len(matches) != 1:
            raise RunStatusTransitionError(
                "repair reopen requires one validated invalidation event"
            )
        invalidation = matches[0]
        if (
            invalidation.get("status") != "invalidated"
            or invalidation.get("reset_from_phase") != reset_from_phase
            or invalidation.get("generation") != generation
        ):
            raise RunStatusTransitionError(
                "repair reopen authority differs from the requested boundary"
            )
        reset_index = PHASES.index(reset_from_phase)
        last_complete = PHASES[reset_index - 1] if reset_index else None
        replacement = _make_record(
            run_id=expected.run_id,
            status="running",
            previous_status=expected.status,
            current_phase=reset_from_phase,
            last_complete_phase=last_complete,
            reason=(
                "repair generation "
                f"{generation} reopened by {invalidation_event_sha256}"
            ),
            validation_passed=False,
            created_at=expected.created_at,
            updated_at=_iso_utc(now),
            revision=expected.revision + 1,
        )
        return self._replace(
            expected,
            replacement,
            repair_authority=_REPAIR_REOPEN_AUTHORITY,
            lease=lease,
        )

    def commit_u12_complete(
        self,
        expected: RunStatusRecord,
        now: datetime,
        *,
        reason: str,
        lease: object | None = None,
    ) -> RunStatusRecord:
        _require_utc(now, "now")
        _validate_record(expected, self.layout.run_dir.name)
        if expected.status != "running":
            raise RunStatusTransitionError(
                "durable U12 completion requires the current running status authority"
            )
        from .deliverables import verify_u12_status_commit_authority

        verify_u12_status_commit_authority(self.layout)
        replacement = _make_record(
            run_id=expected.run_id,
            status="complete",
            previous_status=expected.status,
            current_phase="U12",
            last_complete_phase="U12",
            reason=reason,
            validation_passed=True,
            created_at=expected.created_at,
            updated_at=_iso_utc(now),
            revision=expected.revision + 1,
        )
        if lease is not None:
            return self._replace(
                expected,
                replacement,
                completion_authority=_U12_COMPLETE_AUTHORITY,
                lease=lease,
            )
        from .locks import acquire_run_lease, release_run_lease

        owned = acquire_run_lease(self.layout, now, timedelta(minutes=5))
        try:
            return self._replace(
                expected,
                replacement,
                completion_authority=_U12_COMPLETE_AUTHORITY,
                lease=owned,
            )
        finally:
            release_run_lease(self.layout, owned)
