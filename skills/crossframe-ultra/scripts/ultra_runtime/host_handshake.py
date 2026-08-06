from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path

from .constants import current_version_binding
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
    _parse_canonical_utc,
    _require_utc,
    assert_safe_descendant,
)
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
_ACCEPTED_NAME = "accepted.json"
_ACCEPTED_RESULT_NAME = "accepted-result.json"
_HOST_ACTION_TTL = timedelta(minutes=30)
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


def _accepted_path(layout: RunLayout, action_sha256: str) -> Path:
    return assert_safe_descendant(
        layout.root,
        _action_directory(layout, action_sha256) / _ACCEPTED_NAME,
    )


def _accepted_result_path(layout: RunLayout, action_sha256: str) -> Path:
    return assert_safe_descendant(
        layout.root,
        _action_directory(layout, action_sha256) / _ACCEPTED_RESULT_NAME,
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
    try:
        issued_at = _parse_canonical_utc(
            snapshot.get("issued_at"),
            "host action issued_at",
        )
        expires_at = _parse_canonical_utc(
            snapshot.get("expires_at"),
            "host action expires_at",
        )
    except (TypeError, ValueError) as error:
        raise HostHandshakeError(
            f"host action authority timestamp is invalid: {error}"
        ) from error
    if expires_at < issued_at:
        raise HostHandshakeError("host action expires before it is issued")
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


def _write_immutable_bytes(path: Path, raw: bytes, *, label: str) -> None:
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError as error:
            raise HostHandshakeError(f"{label} is unreadable") from error
        if existing != raw:
            raise HostHandshakeError(f"{label} differs from its immutable bytes")
        return
    atomic_write_bytes(path, raw)


def _terminal_phase_event(layout: RunLayout) -> Mapping[str, object] | None:
    events_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "phase-events.jsonl",
    )
    if not events_path.exists():
        return None
    try:
        from . import recovery

        authority, compatibility, _ = recovery._validate_authority_record(layout)
        events = recovery._read_events(
            layout,
            authority,
            compatibility=compatibility,
        )
    except Exception as error:
        raise HostHandshakeError(
            "terminal phase event authority is unreadable or invalid"
        ) from error
    if not events:
        raise HostHandshakeError("phase event authority is empty")
    tail = events[-1]
    if tail.get("status") in {"failed", "blocked", "cancelled"} or (
        tail.get("phase_id") == "U12" and tail.get("status") == "complete"
    ):
        return tail
    return None


def _require_open_host_action_boundary(layout: RunLayout) -> None:
    from .locks import load_cancel_intent

    if load_cancel_intent(layout) is not None:
        raise HostHandshakeError("cancel intent blocks host action authority")
    status_path = assert_safe_descendant(
        layout.root,
        layout.run_dir / "run-status.json",
    )
    if status_path.exists():
        try:
            from .status import RunStatusStore

            status = RunStatusStore(layout).read()
        except Exception as error:
            raise HostHandshakeError("run status authority is unreadable or invalid") from error
        if status.status in {"complete", "failed", "cancelled"}:
            raise HostHandshakeError(
                f"terminal run status {status.status} blocks host action authority"
            )
    terminal_event = _terminal_phase_event(layout)
    if terminal_event is not None:
        raise HostHandshakeError(
            "terminal phase event blocks host action authority"
        )


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
        "expires_at": _canonical_utc(now + _HOST_ACTION_TTL),
    }
    document["action_sha256"] = sha256_bytes(canonical_json_bytes(document))
    try:
        validate_instance(_ACTION_SCHEMA, document)
    except Exception as error:
        raise ValueError(f"host action is invalid: {error}") from error
    action = _seal_action(layout, document)
    pending_path = _pending_path(layout)
    from .locks import _cancel_intent_lock_path

    with _exclusive_path_lock(_cancel_intent_lock_path(layout)):
        _require_open_host_action_boundary(layout)
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


def _load_bound_result_document(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    receipt: Mapping[str, object],
) -> tuple[dict[str, object], bytes]:
    accepted_path = _accepted_path(layout, action.action_sha256)
    if accepted_path.exists():
        try:
            accepted_raw = accepted_path.read_bytes()
            accepted = load_json_object_bytes(
                accepted_raw,
                source=str(accepted_path),
            )
        except (OSError, TypeError, ValueError) as error:
            raise HostHandshakeError("accepted host result receipt is unreadable") from error
        if (
            accepted_raw != canonical_json_bytes(accepted)
            or accepted != dict(receipt)
        ):
            raise HostHandshakeError("accepted host result receipt differs")
        result_path = _accepted_result_path(layout, action.action_sha256)
        unavailable = "accepted host result snapshot is unavailable"
    else:
        result_path = action.result_path
        unavailable = "host result is missing from its fixed result slot"
    try:
        result_raw = result_path.read_bytes()
        result_document = load_json_object_bytes(
            result_raw,
            source=str(result_path),
        )
    except (OSError, TypeError, ValueError) as error:
        raise HostHandshakeError(unavailable) from error
    if result_raw != canonical_json_bytes(result_document):
        raise HostHandshakeError("host result bytes are not canonical JSON")
    if receipt.get("result_sha256") != sha256_bytes(result_raw):
        raise HostHandshakeError("host result hash differs from accepted result bytes")
    if action.document.get("action_kind") == "subagent":
        projection = receipt.get("result")
        if not isinstance(projection, Mapping) or result_document != projection:
            raise HostHandshakeError(
                "subagent accepted result snapshot differs from its receipt projection"
            )
    return result_document, result_raw


def _seal_result_with_bytes(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    receipt: Mapping[str, object],
) -> tuple[HostResultSeal, bytes]:
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
    _validate_execution_receipt(action, document)
    result_document, result_raw = _load_bound_result_document(
        layout,
        action=action,
        receipt=document,
    )
    result = HostResultSeal(document, str(supplied), action.action_sha256)
    action_kind = action.document.get("action_kind")
    if action_kind == "capability-attestation":
        from .foundation import _build_capability_attestation

        _build_capability_attestation(
            layout,
            action=action,
            result=result,
            profile=None,
            result_document=result_document,
        )
    elif action_kind == "source-read":
        from . import source_integrity

        repo = Path(__file__).resolve().parents[4]
        manifest_path = (
            repo
            / "skills"
            / "crossframe-ultra"
            / "references"
            / "source-manifest.json"
        )
        manifest = source_integrity.load_source_manifest(
            manifest_path,
            expected_sha256=source_integrity._authority_manifest_sha256(),
        )
        source_integrity.validate_host_read_receipt(
            document,
            action=action,
            repo=repo,
            manifest=manifest,
            result_document=result_document,
        )
    elif action_kind == "retrieval":
        from .retrieval import _validate_host_retrieval_result_for_acceptance

        _validate_host_retrieval_result_for_acceptance(
            layout,
            action=action,
            receipt=result,
            result_document=result_document,
        )
    elif action_kind == "evidence-authoring":
        from .foundation import _validate_host_evidence_result_for_acceptance

        _validate_host_evidence_result_for_acceptance(
            layout,
            action=action,
            result=result,
            result_document=result_document,
        )
    elif action_kind == "subagent":
        from .retrieval import _validate_host_subagent_result_for_acceptance

        _validate_host_subagent_result_for_acceptance(
            layout,
            action=action,
            receipt=result,
            result_document=result_document,
        )
    elif action_kind == "semantic-review":
        from .semantic_review import validate_host_semantic_result_for_acceptance

        validate_host_semantic_result_for_acceptance(
            layout,
            action=action,
            result=result,
            result_document=result_document,
        )
    return result, result_raw


def _seal_result(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    receipt: Mapping[str, object],
) -> HostResultSeal:
    return _seal_result_with_bytes(
        layout,
        action=action,
        receipt=receipt,
    )[0]


def _validate_execution_receipt(
    action: HostActionSeal,
    document: Mapping[str, object],
) -> None:
    provider = document.get("provider")
    tool = document.get("tool")
    if (
        not isinstance(provider, Mapping)
        or not isinstance(tool, Mapping)
        or tool.get("provider_id") != provider.get("provider_id")
    ):
        raise HostHandshakeError(
            "host result provider or tool identity is invalid"
        )
    if document.get("execution_status") != "complete":
        raise HostHandshakeError("host result execution status is not complete")
    attempts = document.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise HostHandshakeError("host result attempts are empty")
    for index, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, Mapping) or attempt.get("attempt") != index:
            raise HostHandshakeError("host result attempt sequence is invalid")
        status = attempt.get("status")
        if status == "success":
            if attempt.get("error") is not None:
                raise HostHandshakeError(
                    "successful host result attempt carries an error"
                )
            if index != len(attempts):
                raise HostHandshakeError(
                    "host result attempts continued after success"
                )
    if (
        not isinstance(attempts[-1], Mapping)
        or attempts[-1].get("status") != "success"
    ):
        raise HostHandshakeError("host result has no successful final attempt")
    try:
        issued_at = _parse_canonical_utc(
            action.document.get("issued_at"),
            "host action issued_at",
        )
        completed_at = _parse_canonical_utc(
            document.get("completed_at"),
            "host result completed_at",
        )
        expires_at = _parse_canonical_utc(
            action.document.get("expires_at"),
            "host action expires_at",
        )
    except (TypeError, ValueError) as error:
        raise HostHandshakeError(
            f"host result timestamp is invalid: {error}"
        ) from error
    if not issued_at <= completed_at <= expires_at:
        raise HostHandshakeError(
            "host result completed outside its issued action expiry window"
        )


def _complete_unlocked(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
    result_bytes: bytes,
) -> None:
    pending = _load_pending_unlocked(layout)
    if pending is None or pending != action:
        raise HostHandshakeError(
            "pending host action authority differs or is completed"
        )
    if result.action_sha256 != action.action_sha256:
        raise HostHandshakeError("host result action authority differs")
    if result.document.get("result_sha256") != sha256_bytes(result_bytes):
        raise HostHandshakeError("host result snapshot hash authority differs")
    accepted_path = _accepted_path(layout, action.action_sha256)
    accepted_result_path = _accepted_result_path(layout, action.action_sha256)
    _write_immutable_bytes(
        accepted_result_path,
        result_bytes,
        label="accepted host result snapshot",
    )
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
    document = copy.deepcopy(result.document)
    _require_native_json(document, label="host result receipt")
    attempt_sha256 = sha256_bytes(canonical_json_bytes(document))
    action_dir = _action_directory(layout, action.action_sha256)
    attempts_dir = assert_safe_descendant(layout.root, action_dir / "attempts")
    from .locks import _cancel_intent_lock_path

    with _exclusive_path_lock(_cancel_intent_lock_path(layout)):
        with _exclusive_path_lock(_lock_path(layout)):
            attempt_id = _next_attempt_id(attempts_dir)
            _write_immutable(
                assert_safe_descendant(
                    layout.root,
                    attempts_dir / f"{attempt_id}-submitted.json",
                ),
                document,
                label="submitted host result attempt",
            )
            try:
                _require_open_host_action_boundary(layout)
                if _accepted_path(layout, action.action_sha256).exists():
                    raise HostHandshakeError(
                        "host action is completed; result replay rejected"
                    )
                validated_result, result_bytes = _seal_result_with_bytes(
                    layout,
                    action=action,
                    receipt=document,
                )
                if validated_result != result:
                    raise HostHandshakeError("host result seal authority differs")
                _complete_unlocked(
                    layout,
                    action=action,
                    result=result,
                    result_bytes=result_bytes,
                )
            except Exception as error:
                if not isinstance(error, HostHandshakeError):
                    error = HostHandshakeError(f"host result is invalid: {error}")
                _reject_attempt(
                    attempts_dir,
                    attempt_id,
                    attempt_sha256,
                    error,
                )
                raise error


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
    from .locks import _cancel_intent_lock_path

    with _exclusive_path_lock(_cancel_intent_lock_path(layout)):
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
                _require_open_host_action_boundary(layout)
                if _accepted_path(layout, action.action_sha256).exists():
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
                result, result_bytes = _seal_result_with_bytes(
                    layout,
                    action=action,
                    receipt=document,
                )
                _complete_unlocked(
                    layout,
                    action=action,
                    result=result,
                    result_bytes=result_bytes,
                )
            except Exception as error:
                if not isinstance(error, HostHandshakeError):
                    error = HostHandshakeError(f"host result is invalid: {error}")
                _reject_attempt(attempts_dir, attempt_id, attempt_sha256, error)
                raise error
    return result
