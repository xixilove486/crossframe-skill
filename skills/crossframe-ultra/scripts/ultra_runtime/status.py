from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .constants import PHASES, RUN_STATUSES
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


class RunStatusError(UltraRuntimeError, RuntimeError):
    pass


class RunStatusConflictError(RunStatusError):
    pass


class RunStatusTransitionError(RunStatusError):
    pass


@dataclass(frozen=True, slots=True)
class RunStatusRecord:
    run_id: str
    status: str
    created_at: str
    updated_at: str
    revision: int
    phase_id: str | None
    reason: str | None


_STATUS_FIELDS = frozenset(
    {
        "run_id",
        "status",
        "created_at",
        "updated_at",
        "revision",
        "phase_id",
        "reason",
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
        "run_id": record.run_id,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "revision": record.revision,
        "phase_id": record.phase_id,
        "reason": record.reason,
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
    run_id = value["run_id"]
    status = value["status"]
    revision = value["revision"]
    phase_id = value["phase_id"]
    reason = value["reason"]
    if not isinstance(run_id, str):
        raise ValueError("run status run_id must be a string")
    _validate_run_id(run_id)
    if run_id != expected_run_id:
        raise ValueError("run status run_id does not match its run bundle")
    if not isinstance(status, str) or status not in RUN_STATUSES:
        raise ValueError(f"unknown run status: {status!r}")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ValueError("run status revision must be a non-negative integer")
    if phase_id is not None and (
        not isinstance(phase_id, str) or phase_id not in PHASES
    ):
        raise ValueError(f"run status phase_id must be one of {PHASES} or null")
    if reason is not None and (
        not isinstance(reason, str) or not reason.strip()
    ):
        raise ValueError("run status reason must be a non-empty string or null")
    created_at = _parse_utc(value["created_at"], "created_at")
    updated_at = _parse_utc(value["updated_at"], "updated_at")
    if updated_at < created_at:
        raise ValueError("run status updated_at cannot precede created_at")
    return RunStatusRecord(
        run_id=run_id,
        status=status,
        created_at=str(value["created_at"]),
        updated_at=str(value["updated_at"]),
        revision=revision,
        phase_id=phase_id,
        reason=reason,
    )


def _validate_record(record: RunStatusRecord, expected_run_id: str) -> None:
    if not isinstance(record, RunStatusRecord):
        raise TypeError("status record must be a RunStatusRecord")
    _record_from_object(_record_to_object(record), expected_run_id)


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
        record = RunStatusRecord(
            run_id=self.layout.run_dir.name,
            status="created",
            created_at=timestamp,
            updated_at=timestamp,
            revision=0,
            phase_id=None,
            reason=None,
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

    def replace(
        self,
        expected: RunStatusRecord,
        replacement: RunStatusRecord,
    ) -> RunStatusRecord:
        run_id = self.layout.run_dir.name
        _validate_record(expected, run_id)
        _validate_record(replacement, run_id)
        if replacement.created_at != expected.created_at:
            raise RunStatusTransitionError("created_at is immutable")
        if replacement.revision != expected.revision + 1:
            raise RunStatusTransitionError("replacement revision must advance by one")
        expected_updated = _parse_utc(expected.updated_at, "updated_at")
        replacement_updated = _parse_utc(replacement.updated_at, "updated_at")
        if replacement_updated <= expected_updated:
            raise RunStatusTransitionError(
                "replacement updated_at must advance monotonically after the old value"
            )
        allowed = RUN_STATUS_TRANSITIONS[expected.status]
        if replacement.status not in allowed:
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

    def transition(
        self,
        expected: RunStatusRecord,
        status: str,
        now: datetime,
        *,
        phase_id: str | None = None,
        reason: str | None = None,
    ) -> RunStatusRecord:
        _require_utc(now, "now")
        if not isinstance(status, str) or status not in RUN_STATUSES:
            raise ValueError(f"unknown run status: {status!r}")
        replacement = RunStatusRecord(
            run_id=expected.run_id,
            status=status,
            created_at=expected.created_at,
            updated_at=_iso_utc(now),
            revision=expected.revision + 1,
            phase_id=expected.phase_id if phase_id is None else phase_id,
            reason=reason,
        )
        return self.replace(expected, replacement)
