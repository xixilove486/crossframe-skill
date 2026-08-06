from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import math
from pathlib import Path

from .constants import current_version_binding
from .errors import UltraRuntimeError
from .jsonio import (
    _exclusive_path_lock,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    sha256_bytes,
)
from .paths import RunLayout, _require_utc, assert_safe_descendant
from .schemas import validate_instance


HOST_ACTION_KINDS = frozenset(
    {
        "capability-attestation",
        "source-read",
        "retrieval",
        "evidence-authoring",
        "subagent",
        "semantic-review",
    }
)

_ACTION_SCHEMA = "ultra-host-action.schema.json"
_RESULT_SCHEMA = "ultra-host-result-receipt.schema.json"
_ACTION_SCHEMA_ID = "crossframe.ultra.v82.host-action"
_PENDING_NAME = "pending-action.json"
_LOCK_NAME = ".host-handshake.lock"
_RESULT_AUTHORITY_FIELDS = (
    "run_id",
    "version_binding",
    "phase_id",
    "action_kind",
    "parent_event_sha256",
    "request_sha256",
    "action_sha256",
    "result_relative_path",
)


class HostHandshakeError(UltraRuntimeError, RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class HostActionSeal:
    document: dict[str, object]
    action_sha256: str
    result_path: Path


@dataclass(frozen=True, slots=True)
class HostResultSeal:
    document: dict[str, object]
    receipt_sha256: str
    action_sha256: str


def _canonical_utc(value: datetime) -> str:
    _require_utc(value, "now")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _require_native_json(value: object, *, label: str) -> None:
    stack = [value]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        if current is None or isinstance(current, (str, bool, int)):
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                raise ValueError(f"{label} must contain finite native JSON values")
            continue
        if isinstance(current, list):
            identity = id(current)
            if identity in seen:
                raise ValueError(f"{label} must not contain recursive JSON containers")
            seen.add(identity)
            stack.extend(current)
            continue
        if isinstance(current, dict):
            identity = id(current)
            if identity in seen:
                raise ValueError(f"{label} must not contain recursive JSON containers")
            seen.add(identity)
            if any(type(key) is not str for key in current):
                raise TypeError(f"{label} object keys must be native JSON strings")
            stack.extend(current.values())
            continue
        raise TypeError(
            f"{label} must contain only native JSON values, not "
            f"{type(current).__name__}"
        )


def _pending_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(layout.root, layout.recovery_dir / _PENDING_NAME)


def _lock_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(layout.root, layout.recovery_dir / _LOCK_NAME)


def _action_directory(layout: RunLayout, action_sha256: str) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "host-results" / action_sha256,
    )


def _checked_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    assert_safe_descendant(layout.root, layout.run_dir)
    assert_safe_descendant(layout.root, layout.recovery_dir)
    _pending_path(layout)
    _lock_path(layout)


def _checked_result_path(layout: RunLayout, relative_path: object) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise TypeError("result_relative_path must be a non-empty string")
    relative = Path(relative_path)
    if (
        relative.is_absolute()
        or "\\" in relative_path
        or ".." in relative.parts
        or relative.as_posix() != relative_path
    ):
        raise ValueError("result_relative_path must be a safe canonical relative path")
    if len(relative.parts) < 3 or relative.parts[:2] != ("work", "host"):
        raise ValueError(
            "result_relative_path must select a fixed work/host result slot"
        )
    return assert_safe_descendant(layout.root, layout.run_dir / relative)


def _seal_action(layout: RunLayout, document: Mapping[str, object]) -> HostActionSeal:
    snapshot = copy.deepcopy(dict(document))
    _require_native_json(snapshot, label="host action")
    try:
        validate_instance(_ACTION_SCHEMA, snapshot)
    except Exception as error:
        raise HostHandshakeError(
            f"host action authority is invalid: {error}"
        ) from error
    if snapshot["run_id"] != layout.run_dir.name:
        raise HostHandshakeError("host action run authority differs")
    if snapshot["version_binding"] != current_version_binding():
        raise HostHandshakeError("host action version authority differs")
    supplied = snapshot.pop("action_sha256")
    measured = sha256_bytes(canonical_json_bytes(snapshot))
    snapshot["action_sha256"] = supplied
    if supplied != measured:
        raise HostHandshakeError("host action hash authority differs")
    result_path = _checked_result_path(layout, snapshot["result_relative_path"])
    return HostActionSeal(snapshot, str(supplied), result_path)


def _write_immutable(path: Path, document: object, *, label: str) -> None:
    if path.exists():
        raise HostHandshakeError(
            f"{label} already exists; replay or completed action"
        )
    atomic_write_json(path, document)


def issue_host_action(
    layout: RunLayout,
    *,
    action_kind: str,
    phase_id: str,
    parent_event_sha256: str | None,
    request_sha256: str,
    payload: Mapping[str, object],
    result_relative_path: str,
    now: datetime,
) -> HostActionSeal:
    _checked_layout(layout)
    if action_kind not in HOST_ACTION_KINDS:
        raise ValueError(f"unknown host action kind: {action_kind!r}")
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    payload_snapshot = copy.deepcopy(dict(payload))
    _require_native_json(payload_snapshot, label="host action payload")
    _checked_result_path(layout, result_relative_path)
    document: dict[str, object] = {
        "schema_id": _ACTION_SCHEMA_ID,
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "phase_id": phase_id,
        "action_kind": action_kind,
        "parent_event_sha256": parent_event_sha256,
        "request_sha256": request_sha256,
        "result_relative_path": result_relative_path,
        "payload": payload_snapshot,
        "issued_at": _canonical_utc(now),
    }
    document["action_sha256"] = sha256_bytes(canonical_json_bytes(document))
    try:
        validate_instance(_ACTION_SCHEMA, document)
    except Exception as error:
        raise ValueError(f"host action is invalid: {error}") from error
    action = _seal_action(layout, document)
    pending_path = _pending_path(layout)
    with _exclusive_path_lock(_lock_path(layout)):
        if pending_path.exists():
            raise HostHandshakeError("a pending host action already holds authority")
        _write_immutable(pending_path, action.document, label="pending host action")
    return action


def _load_pending_unlocked(layout: RunLayout) -> HostActionSeal | None:
    path = _pending_path(layout)
    if not path.exists():
        return None
    try:
        document = load_json_object(path)
    except Exception as error:
        raise HostHandshakeError(
            f"pending host action is unreadable: {error}"
        ) from error
    return _seal_action(layout, document)


def load_pending_action(layout: RunLayout) -> HostActionSeal | None:
    _checked_layout(layout)
    with _exclusive_path_lock(_lock_path(layout)):
        return _load_pending_unlocked(layout)


def _reject_attempt(
    attempts_dir: Path,
    attempt_id: str,
    attempt_sha256: str,
    error: BaseException,
) -> None:
    rejection = {
        "status": "rejected",
        "submitted_sha256": attempt_sha256,
        "reason": str(error),
    }
    _write_immutable(
        attempts_dir / f"{attempt_id}-rejected.json",
        rejection,
        label="rejected host result attempt",
    )


def _next_attempt_id(attempts_dir: Path) -> str:
    highest = 0
    if attempts_dir.is_dir():
        for path in attempts_dir.iterdir():
            prefix, separator, _ = path.name.partition("-")
            if separator and prefix.isascii() and prefix.isdecimal():
                highest = max(highest, int(prefix))
    return f"{highest + 1:06d}"


def _seal_result(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    receipt: Mapping[str, object],
) -> HostResultSeal:
    try:
        document = copy.deepcopy(dict(receipt))
        _require_native_json(document, label="host result receipt")
        validate_instance(_RESULT_SCHEMA, document)
    except Exception as error:
        raise HostHandshakeError(f"host result is invalid: {error}") from error
    supplied = document.pop("receipt_sha256")
    measured = sha256_bytes(canonical_json_bytes(document))
    document["receipt_sha256"] = supplied
    if supplied != measured:
        raise HostHandshakeError("host result receipt hash differs")
    for field in _RESULT_AUTHORITY_FIELDS:
        expected = (
            action.action_sha256
            if field == "action_sha256"
            else action.document[field]
        )
        if document[field] != expected:
            raise HostHandshakeError(
                f"host result {field} authority differs from action"
            )
    result_path = _checked_result_path(layout, document["result_relative_path"])
    if result_path != action.result_path:
        raise HostHandshakeError("host result slot authority differs from action")
    if not result_path.is_file():
        raise HostHandshakeError("host result is missing from its fixed result slot")
    measured_result = sha256_bytes(result_path.read_bytes())
    if document["result_sha256"] != measured_result:
        raise HostHandshakeError("host result hash differs from result slot bytes")
    result = HostResultSeal(document, str(supplied), action.action_sha256)
    if action.document.get("action_kind") == "semantic-review":
        from .semantic_review import validate_host_semantic_result_for_acceptance

        validate_host_semantic_result_for_acceptance(
            layout,
            action=action,
            result=result,
        )
    return result


def _complete_unlocked(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
) -> None:
    validated_result = _seal_result(
        layout,
        action=action,
        receipt=result.document,
    )
    if validated_result != result:
        raise HostHandshakeError("host result seal authority differs")
    pending = _load_pending_unlocked(layout)
    if pending is None or pending != action:
        raise HostHandshakeError(
            "pending host action authority differs or is completed"
        )
    if result.action_sha256 != action.action_sha256:
        raise HostHandshakeError("host result action authority differs")
    action_dir = _action_directory(layout, action.action_sha256)
    accepted_path = assert_safe_descendant(layout.root, action_dir / "accepted.json")
    _write_immutable(accepted_path, result.document, label="accepted host result")
    _pending_path(layout).unlink()


def complete_host_action(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
) -> None:
    _checked_layout(layout)
    if not isinstance(action, HostActionSeal):
        raise TypeError("action must be a HostActionSeal")
    if not isinstance(result, HostResultSeal):
        raise TypeError("result must be a HostResultSeal")
    with _exclusive_path_lock(_lock_path(layout)):
        _complete_unlocked(layout, action=action, result=result)


def accept_host_result(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    receipt: Mapping[str, object],
) -> HostResultSeal:
    _checked_layout(layout)
    if not isinstance(action, HostActionSeal):
        raise TypeError("action must be a HostActionSeal")
    if not isinstance(receipt, Mapping):
        raise TypeError("receipt must be a mapping")
    document = copy.deepcopy(dict(receipt))
    _require_native_json(document, label="host result receipt")
    attempt_sha256 = sha256_bytes(canonical_json_bytes(document))
    action_dir = _action_directory(layout, action.action_sha256)
    attempts_dir = assert_safe_descendant(layout.root, action_dir / "attempts")

    with _exclusive_path_lock(_lock_path(layout)):
        attempt_id = _next_attempt_id(attempts_dir)
        submitted_path = assert_safe_descendant(
            layout.root,
            attempts_dir / f"{attempt_id}-submitted.json",
        )
        _write_immutable(
            submitted_path,
            document,
            label="submitted host result attempt",
        )
        try:
            accepted_path = assert_safe_descendant(
                layout.root, action_dir / "accepted.json"
            )
            if accepted_path.exists():
                raise HostHandshakeError(
                    "host action is completed; result replay rejected"
                )
            pending = _load_pending_unlocked(layout)
            if pending is None:
                raise HostHandshakeError(
                    "host action is completed or has no pending authority"
                )
            if pending != action:
                raise HostHandshakeError(
                    "supplied host action authority differs from pending action"
                )
            result = _seal_result(
                layout,
                action=action,
                receipt=document,
            )
            _complete_unlocked(layout, action=action, result=result)
        except Exception as error:
            if not isinstance(error, HostHandshakeError):
                error = HostHandshakeError(f"host result is invalid: {error}")
            _reject_attempt(attempts_dir, attempt_id, attempt_sha256, error)
            raise error
    return result
