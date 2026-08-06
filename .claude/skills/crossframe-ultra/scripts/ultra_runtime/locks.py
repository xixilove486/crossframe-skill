from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import secrets

from .errors import UltraRuntimeError
from .jsonio import (
    RUN_LIFECYCLE_LOCK_FILENAME,
    _exclusive_path_lock,
    _fsync_directory,
    atomic_write_bytes,
    canonical_json_bytes,
    load_json_object,
    sha256_bytes,
)
from .paths import (
    RunLayout,
    _parse_canonical_utc,
    _require_utc,
    _validate_run_id,
    assert_safe_descendant,
)
from .status import RunStatusStore


LEASE_FILENAME = ".writer-lease.json"
LEASE_LOCK_FILENAME = ".writer-lease.lock"
CANCEL_INTENT_FILENAME = "cancel-intent.json"
CANCEL_INTENT_LOCK_FILENAME = ".cancel-intent.lock"
VALIDATION_CURRENT_COMMIT_LOCK_FILENAME = ".validation-current-commit.lock"


class LeaseError(UltraRuntimeError, RuntimeError):
    pass


class LeaseConflictError(LeaseError):
    pass


class LeaseNeedsAttentionError(LeaseError):
    pass


class LeaseOwnershipError(LeaseError):
    pass


class CancelledRunError(LeaseError):
    pass


@dataclass(frozen=True, slots=True)
class Lease:
    run_id: str
    owner_pid: int
    owner_nonce: str
    acquired_at: str
    heartbeat_at: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class CancellationIntent:
    run_id: str
    reason: str
    requested_at: str
    content_sha256: str


_LEASE_FIELDS = frozenset(
    {
        "run_id",
        "owner_pid",
        "owner_nonce",
        "acquired_at",
        "heartbeat_at",
        "expires_at",
    }
)
_CANCEL_INTENT_FIELDS = frozenset(
    {"run_id", "reason", "requested_at", "content_sha256"}
)


def _lease_path(layout: RunLayout) -> Path:
    _validate_layout(layout)
    return layout.run_dir / LEASE_FILENAME


def _lease_lock_path(layout: RunLayout) -> Path:
    _validate_layout(layout)
    return layout.run_dir / LEASE_LOCK_FILENAME


def _cancel_intent_path(layout: RunLayout) -> Path:
    _validate_layout(layout)
    return layout.recovery_dir / CANCEL_INTENT_FILENAME


def _cancel_intent_lock_path(layout: RunLayout) -> Path:
    _validate_layout(layout)
    return layout.recovery_dir / CANCEL_INTENT_LOCK_FILENAME


def _validation_current_commit_lock_path(layout: RunLayout) -> Path:
    _validate_layout(layout)
    return layout.validation_dir / VALIDATION_CURRENT_COMMIT_LOCK_FILENAME


def _validate_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    run_id = layout.run_dir.name
    _validate_run_id(run_id)
    expected_run_dir = (
        layout.root / "runs" / run_id[:4] / run_id[4:6] / run_id
    )
    if layout.run_dir != expected_run_dir:
        raise ValueError("run_dir does not match the selected root and run_id")
    for candidate in (
        layout.run_dir,
        layout.run_dir / LEASE_FILENAME,
        layout.run_dir / LEASE_LOCK_FILENAME,
        layout.run_dir / RUN_LIFECYCLE_LOCK_FILENAME,
        layout.run_dir / "run-status.json",
        layout.recovery_dir / CANCEL_INTENT_FILENAME,
        layout.recovery_dir / CANCEL_INTENT_LOCK_FILENAME,
        layout.validation_dir / VALIDATION_CURRENT_COMMIT_LOCK_FILENAME,
    ):
        assert_safe_descendant(layout.root, candidate)


def _iso_utc(value: datetime) -> str:
    _require_utc(value, "time")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _parse_utc(value: object, field: str) -> datetime:
    try:
        return _parse_canonical_utc(value, f"lease field {field}")
    except ValueError as error:
        raise LeaseNeedsAttentionError(
            f"lease field {field} must be a canonical UTC timestamp"
        ) from error


def _lease_object(lease: Lease) -> dict[str, object]:
    return {
        "run_id": lease.run_id,
        "owner_pid": lease.owner_pid,
        "owner_nonce": lease.owner_nonce,
        "acquired_at": lease.acquired_at,
        "heartbeat_at": lease.heartbeat_at,
        "expires_at": lease.expires_at,
    }


def _cancel_intent_content_sha256(value: dict[str, object]) -> str:
    payload = {key: child for key, child in value.items() if key != "content_sha256"}
    return sha256_bytes(canonical_json_bytes(payload))


def _cancel_intent_from_object(
    value: dict[str, object],
    *,
    expected_run_id: str,
) -> CancellationIntent:
    if set(value) != _CANCEL_INTENT_FIELDS:
        raise LeaseNeedsAttentionError(
            "cancel intent is corrupt or has unexpected fields"
        )
    run_id = value["run_id"]
    reason = value["reason"]
    requested_at = value["requested_at"]
    content_sha256 = value["content_sha256"]
    if not isinstance(run_id, str) or run_id != expected_run_id:
        raise LeaseNeedsAttentionError("cancel intent run_id differs from its run")
    if not isinstance(reason, str) or not reason.strip() or reason != reason.strip():
        raise LeaseNeedsAttentionError("cancel intent reason is invalid")
    try:
        _parse_canonical_utc(requested_at, "cancel intent requested_at")
    except ValueError as error:
        raise LeaseNeedsAttentionError(
            "cancel intent requested_at must be canonical UTC"
        ) from error
    if (
        not isinstance(content_sha256, str)
        or content_sha256 != _cancel_intent_content_sha256(value)
    ):
        raise LeaseNeedsAttentionError("cancel intent content hash differs")
    return CancellationIntent(
        run_id=run_id,
        reason=reason,
        requested_at=str(requested_at),
        content_sha256=content_sha256,
    )


def load_cancel_intent(layout: RunLayout) -> CancellationIntent | None:
    _validate_layout(layout)
    path = _cancel_intent_path(layout)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    try:
        value = load_json_object(path)
        intent = _cancel_intent_from_object(
            value,
            expected_run_id=layout.run_dir.name,
        )
    except LeaseError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise LeaseNeedsAttentionError("cancel intent is corrupt") from error
    if raw != canonical_json_bytes(value):
        raise LeaseNeedsAttentionError("cancel intent bytes are not canonical JSON")
    return intent


def _reject_terminal_cancel_admission(layout: RunLayout) -> None:
    status_path = layout.run_dir / "run-status.json"
    if status_path.exists():
        status = RunStatusStore(layout).read()
        if status.status in {"failed", "complete", "cancelled"}:
            raise LeaseConflictError(
                f"{status.status} run is terminal and cannot accept cancellation"
            )

    events_path = layout.recovery_dir / "phase-events.jsonl"
    if not events_path.exists():
        return
    assert_safe_descendant(layout.root, events_path)
    from . import recovery

    authority, compatibility, _ = recovery._validate_authority_record(layout)
    events = recovery._read_events(
        layout,
        authority,
        compatibility=compatibility,
    )
    tail = events[-1] if events else None
    terminal_tail = tail is not None and (
        tail.get("status") in {"failed", "blocked", "cancelled"}
        or (tail.get("status") == "complete" and tail.get("phase_id") == "U12")
    )
    if terminal_tail:
        raise LeaseConflictError(
            "verified terminal phase event "
            f"{tail.get('phase_id')} ({tail.get('status')}) cannot accept cancellation"
        )


def request_cancel(
    layout: RunLayout,
    *,
    reason: str,
    now: datetime,
) -> CancellationIntent:
    _validate_layout(layout)
    _require_utc(now, "now")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("cancellation reason must be non-empty")
    checked_reason = reason.strip()
    layout.recovery_dir.mkdir(parents=True, exist_ok=True)
    _validate_layout(layout)
    with _exclusive_path_lock(_cancel_intent_lock_path(layout)):
        existing = load_cancel_intent(layout)
        if existing is not None:
            return existing
        from . import recovery

        _reject_terminal_cancel_admission(layout)
        if recovery._has_durable_u12_checkpoint(layout):
            raise LeaseConflictError(
                "durable U12 checkpoint rejects cancellation before intent creation"
            )
        value: dict[str, object] = {
            "run_id": layout.run_dir.name,
            "reason": checked_reason,
            "requested_at": _iso_utc(now),
            "content_sha256": "0" * 64,
        }
        value["content_sha256"] = _cancel_intent_content_sha256(value)
        intent = _cancel_intent_from_object(
            value,
            expected_run_id=layout.run_dir.name,
        )
        atomic_write_bytes(_cancel_intent_path(layout), canonical_json_bytes(value))
        return intent


def _lease_from_object(value: dict[str, object], expected_run_id: str) -> Lease:
    if set(value) != _LEASE_FIELDS:
        raise LeaseNeedsAttentionError("lease JSON is corrupt or has unexpected fields")
    run_id = value["run_id"]
    owner_pid = value["owner_pid"]
    owner_nonce = value["owner_nonce"]
    if not isinstance(run_id, str):
        raise LeaseNeedsAttentionError("lease run_id must be a string")
    try:
        _validate_run_id(run_id)
    except (TypeError, ValueError) as error:
        raise LeaseNeedsAttentionError("lease run_id is invalid") from error
    if run_id != expected_run_id:
        raise LeaseNeedsAttentionError("lease run_id does not match its run bundle")
    if isinstance(owner_pid, bool) or not isinstance(owner_pid, int) or owner_pid <= 0:
        raise LeaseNeedsAttentionError("lease owner_pid must be a positive integer")
    if not isinstance(owner_nonce, str) or len(owner_nonce) < 16:
        raise LeaseNeedsAttentionError("lease owner_nonce is invalid")
    acquired = _parse_utc(value["acquired_at"], "acquired_at")
    heartbeat = _parse_utc(value["heartbeat_at"], "heartbeat_at")
    expires = _parse_utc(value["expires_at"], "expires_at")
    if acquired > heartbeat or heartbeat >= expires:
        raise LeaseNeedsAttentionError("lease timestamps are not monotonic")
    return Lease(
        run_id=run_id,
        owner_pid=owner_pid,
        owner_nonce=owner_nonce,
        acquired_at=str(value["acquired_at"]),
        heartbeat_at=str(value["heartbeat_at"]),
        expires_at=str(value["expires_at"]),
    )


def _read_lease_bytes(layout: RunLayout) -> tuple[bytes, Lease]:
    path = _lease_path(layout)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise LeaseOwnershipError("run has no active lease") from error
    try:
        value = load_json_object(path)
        lease = _lease_from_object(value, layout.run_dir.name)
    except LeaseError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise LeaseNeedsAttentionError(
            f"lease record is corrupt and needs attention: {path}"
        ) from error
    return raw, lease


def _read_lease(layout: RunLayout) -> Lease:
    return _read_lease_bytes(layout)[1]


def _write_lease_exclusive(path: Path, lease: Lease) -> None:
    encoded = canonical_json_bytes(_lease_object(lease))
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    created = True
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            if hasattr(os, "fsync"):
                os.fsync(handle.fileno())
        _fsync_directory(path.parent)
    except BaseException:
        if created:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def _replace_lease_cas(path: Path, expected_raw: bytes, replacement: Lease) -> None:
    try:
        current_raw = path.read_bytes()
    except FileNotFoundError as error:
        raise LeaseConflictError("lease changed during CAS") from error
    if current_raw != expected_raw:
        raise LeaseConflictError("lease changed during CAS")
    atomic_write_bytes(path, canonical_json_bytes(_lease_object(replacement)))


def _check_cancelled(layout: RunLayout) -> None:
    if load_cancel_intent(layout) is not None:
        raise CancelledRunError("cancel intent blocks lease acquisition and heartbeat")
    status_path = layout.run_dir / "run-status.json"
    if not status_path.exists():
        return
    try:
        status = RunStatusStore(layout).read()
    except (OSError, TypeError, ValueError, UltraRuntimeError) as error:
        raise LeaseNeedsAttentionError(
            "run status is corrupt; lease acquisition needs attention"
        ) from error
    if status.status == "cancelled":
        raise CancelledRunError("cancelled run cannot acquire or heartbeat a lease")
    events_path = layout.recovery_dir / "phase-events.jsonl"
    if not events_path.exists():
        return
    try:
        from . import recovery

        authority, compatibility, _ = recovery._validate_authority_record(layout)
        events = recovery._read_events(
            layout,
            authority,
            compatibility=compatibility,
        )
    except Exception as error:
        raise LeaseNeedsAttentionError(
            "phase event authority is corrupt; lease acquisition needs attention"
        ) from error
    if events and events[-1].get("status") == "cancelled":
        raise CancelledRunError("cancelled run cannot acquire or heartbeat a lease")
    try:
        recovery._validate_authority(layout)
    except Exception as error:
        raise LeaseNeedsAttentionError(
            "phase event authority is corrupt; lease acquisition needs attention"
        ) from error


def _new_lease(layout: RunLayout, now: datetime, ttl: timedelta) -> Lease:
    return Lease(
        run_id=layout.run_dir.name,
        owner_pid=os.getpid(),
        owner_nonce=secrets.token_urlsafe(24),
        acquired_at=_iso_utc(now),
        heartbeat_at=_iso_utc(now),
        expires_at=_iso_utc(now + ttl),
    )


def _pid_exists(pid: int) -> bool:
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        error_code = ctypes.get_last_error()
        if error_code == 87:
            return False
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _acquire_run_lease(
    layout: RunLayout,
    now: datetime,
    ttl: timedelta,
    *,
    cancel_convergence: bool,
) -> Lease:
    _validate_layout(layout)
    _require_utc(now, "now")
    if not isinstance(ttl, timedelta):
        raise TypeError("ttl must be a timedelta")
    if ttl <= timedelta(0):
        raise ValueError("ttl must be positive")
    layout.run_dir.mkdir(parents=True, exist_ok=True)
    _validate_layout(layout)
    lifecycle_lock_path = layout.run_dir / RUN_LIFECYCLE_LOCK_FILENAME
    with _exclusive_path_lock(lifecycle_lock_path):
        _validate_layout(layout)
        with _exclusive_path_lock(_lease_lock_path(layout)):
            _validate_layout(layout)
            if cancel_convergence:
                if load_cancel_intent(layout) is None:
                    raise CancelledRunError(
                        "cancel convergence requires an immutable cancel intent"
                    )
            else:
                _check_cancelled(layout)
            path = _lease_path(layout)
            replacement = _new_lease(layout, now, ttl)
            try:
                expected_raw, existing = _read_lease_bytes(layout)
            except LeaseOwnershipError:
                try:
                    _validate_layout(layout)
                    _write_lease_exclusive(path, replacement)
                except FileExistsError as error:
                    raise LeaseConflictError(
                        "another writer acquired the run lease"
                    ) from error
                return replacement

            expires_at = _parse_utc(existing.expires_at, "expires_at")
            if now <= expires_at:
                raise LeaseConflictError("run already has a live writer lease")
            if _pid_exists(existing.owner_pid):
                raise LeaseConflictError(
                    "expired lease belongs to a live local PID and cannot be reclaimed"
                )
            _validate_layout(layout)
            _replace_lease_cas(path, expected_raw, replacement)
            return replacement


def acquire_run_lease(
    layout: RunLayout, now: datetime, ttl: timedelta
) -> Lease:
    return _acquire_run_lease(
        layout,
        now,
        ttl,
        cancel_convergence=False,
    )


def acquire_cancel_convergence_lease(
    layout: RunLayout, now: datetime, ttl: timedelta
) -> Lease:
    return _acquire_run_lease(
        layout,
        now,
        ttl,
        cancel_convergence=True,
    )


def _require_owner(current: Lease, supplied: Lease) -> None:
    if not isinstance(supplied, Lease):
        raise TypeError("lease must be a Lease")
    if (
        current.run_id != supplied.run_id
        or current.owner_pid != supplied.owner_pid
        or current.owner_nonce != supplied.owner_nonce
    ):
        raise LeaseOwnershipError("lease owner PID or nonce does not match")


def require_run_lease_owner(layout: RunLayout, lease: Lease) -> None:
    _validate_layout(layout)
    lifecycle_lock_path = layout.run_dir / RUN_LIFECYCLE_LOCK_FILENAME
    with _exclusive_path_lock(lifecycle_lock_path):
        _validate_layout(layout)
        with _exclusive_path_lock(_lease_lock_path(layout)):
            _validate_layout(layout)
            current = _read_lease(layout)
            _require_owner(current, lease)


def heartbeat_run_lease(
    layout: RunLayout, lease: Lease, now: datetime
) -> Lease:
    _validate_layout(layout)
    _require_utc(now, "now")
    lifecycle_lock_path = layout.run_dir / RUN_LIFECYCLE_LOCK_FILENAME
    with _exclusive_path_lock(lifecycle_lock_path):
        _validate_layout(layout)
        with _exclusive_path_lock(_lease_lock_path(layout)):
            _validate_layout(layout)
            _check_cancelled(layout)
            expected_raw, current = _read_lease_bytes(layout)
            _require_owner(current, lease)
            if current != lease:
                raise LeaseConflictError(
                    "stale lease heartbeat cannot overwrite newer state"
                )
            previous_heartbeat = _parse_utc(current.heartbeat_at, "heartbeat_at")
            if now <= previous_heartbeat:
                raise ValueError(
                    "heartbeat time must advance monotonically after the prior heartbeat"
                )
            previous_expiry = _parse_utc(current.expires_at, "expires_at")
            ttl = previous_expiry - previous_heartbeat
            if ttl <= timedelta(0):
                raise LeaseNeedsAttentionError("lease TTL is invalid")
            replacement = Lease(
                run_id=current.run_id,
                owner_pid=current.owner_pid,
                owner_nonce=current.owner_nonce,
                acquired_at=current.acquired_at,
                heartbeat_at=_iso_utc(now),
                expires_at=_iso_utc(now + ttl),
            )
            _validate_layout(layout)
            _replace_lease_cas(_lease_path(layout), expected_raw, replacement)
            return replacement


def release_run_lease(layout: RunLayout, lease: Lease) -> None:
    _validate_layout(layout)
    lifecycle_lock_path = layout.run_dir / RUN_LIFECYCLE_LOCK_FILENAME
    with _exclusive_path_lock(lifecycle_lock_path):
        _validate_layout(layout)
        with _exclusive_path_lock(_lease_lock_path(layout)):
            _validate_layout(layout)
            path = _lease_path(layout)
            expected_raw, current = _read_lease_bytes(layout)
            _require_owner(current, lease)
            try:
                _validate_layout(layout)
                if path.read_bytes() != expected_raw:
                    raise LeaseConflictError("lease changed during release CAS")
                _validate_layout(layout)
                path.unlink()
                _fsync_directory(path.parent)
            except FileNotFoundError as error:
                raise LeaseConflictError("lease changed during release CAS") from error
