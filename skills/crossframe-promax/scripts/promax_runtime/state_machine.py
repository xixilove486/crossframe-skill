from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import re
import stat
from types import MappingProxyType
from typing import BinaryIO, Iterable, Iterator, Mapping
import warnings

from .errors import (
    JSONDocumentError,
    PhaseCASMismatch,
    PhaseHistoryError,
    PhaseLockBusy,
    PhaseParentHashError,
    PhaseReplayError,
    PhaseTransitionError,
    RunBindingError,
    StaleArtifactError,
)
from .jsonio import canonical_json_bytes, load_jsonl, sha256_json
from .paths import validate_relative_artifact_path


V8_SOURCE_SNAPSHOT_SHA256 = (
    "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
)
PHASES = tuple(f"P{number}" for number in range(12))

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_NONCE_RE = re.compile(r"^[A-Za-z0-9._~-]{32,256}$")
_EVENT_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "event_index",
        "event_type",
        "run_id",
        "run_nonce",
        "request_sha256",
        "source_snapshot_sha256",
        "phase_id",
        "status",
        "parent_phase_sha256",
        "input_phase_hashes",
        "input_artifact_hashes",
        "output_artifact_hashes",
        "previous_event_sha256",
        "invalidated_phases",
        "reset_reason",
        "event_sha256",
    }
)


def _require_sha256(value: object, *, field: str, error_type=PhaseHistoryError) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise error_type(f"{field} must be one lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class RunBinding:
    run_id: str
    run_nonce: str
    request_sha256: str
    source_snapshot_sha256: str = V8_SOURCE_SNAPSHOT_SHA256

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or _RUN_ID_RE.fullmatch(self.run_id) is None:
            raise RunBindingError("run_id is empty or is not a stable runtime identifier")
        if (
            not isinstance(self.run_nonce, str)
            or _NONCE_RE.fullmatch(self.run_nonce) is None
        ):
            raise RunBindingError(
                "run_nonce must be a caller-generated unpredictable value "
                "of at least 32 characters"
            )
        _require_sha256(
            self.request_sha256,
            field="request_sha256",
            error_type=RunBindingError,
        )
        if self.source_snapshot_sha256 != V8_SOURCE_SNAPSHOT_SHA256:
            raise RunBindingError(
                "source_snapshot_sha256 must equal the frozen CrossFrame ProMax v8 source SHA"
            )


@dataclass(frozen=True, slots=True)
class PhaseState:
    binding: RunBinding | None
    event_count: int
    chain_head_sha256: str | None
    completed_phases: tuple[str, ...]
    active_phase_hashes: Mapping[str, str]
    active_artifact_hashes: Mapping[str, str]
    artifact_owner_phases: Mapping[str, str]
    invalidated_phases: tuple[str, ...]
    next_phase_id: str | None


@dataclass(slots=True)
class _EventLock:
    path: Path
    handle: BinaryIO
    released: bool = False


_NO_EXPECTED_HEAD = object()


def _warn_nonfatal(message: str) -> None:
    try:
        warnings.warn(message, RuntimeWarning, stacklevel=2)
    except Exception:
        pass


def downstream_phases(phase_id: str, *, include_self: bool = True) -> tuple[str, ...]:
    try:
        index = PHASES.index(phase_id)
    except ValueError as error:
        raise PhaseTransitionError(f"unknown phase_id: {phase_id!r}") from error
    if not include_self:
        index += 1
    return PHASES[index:]


def _next_phase(completed_phases: tuple[str, ...]) -> str | None:
    if len(completed_phases) == len(PHASES):
        return None
    return PHASES[len(completed_phases)]


def _immutable_mapping(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _phase_state(
    *,
    binding: RunBinding | None,
    event_count: int,
    chain_head_sha256: str | None,
    active_phase_hashes: Mapping[str, str],
    active_artifact_hashes: Mapping[str, str],
    artifact_owner_phases: Mapping[str, str],
    invalidated_phases: tuple[str, ...],
) -> PhaseState:
    completed = tuple(
        phase_id for phase_id in PHASES if phase_id in active_phase_hashes
    )
    if completed != PHASES[: len(completed)]:
        raise PhaseHistoryError("active phase set is not one contiguous P0-P11 prefix")
    return PhaseState(
        binding=binding,
        event_count=event_count,
        chain_head_sha256=chain_head_sha256,
        completed_phases=completed,
        active_phase_hashes=_immutable_mapping(active_phase_hashes),
        active_artifact_hashes=_immutable_mapping(active_artifact_hashes),
        artifact_owner_phases=_immutable_mapping(artifact_owner_phases),
        invalidated_phases=tuple(invalidated_phases),
        next_phase_id=_next_phase(completed),
    )


def _event_binding(event: Mapping[str, object]) -> RunBinding:
    try:
        return RunBinding(
            run_id=event["run_id"],
            run_nonce=event["run_nonce"],
            request_sha256=event["request_sha256"],
            source_snapshot_sha256=event["source_snapshot_sha256"],
        )
    except KeyError as error:
        raise PhaseHistoryError(
            f"phase event is missing binding field: {error.args[0]}"
        ) from error
    except TypeError as error:
        raise RunBindingError(f"phase event binding has an invalid type: {error}") from error


def _validate_artifact_path(path: object) -> str:
    try:
        return validate_relative_artifact_path(path)
    except ValueError as error:
        raise PhaseTransitionError(f"invalid artifact path {path!r}: {error}") from error


def _validate_hash_map(value: object, *, field: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise PhaseHistoryError(f"{field} must be an object mapping names to SHA-256")
    normalized: dict[str, str] = {}
    for key, digest in value.items():
        if field == "input_phase_hashes":
            if key not in PHASES:
                raise PhaseHistoryError(f"{field} contains unknown phase: {key!r}")
            name = key
        else:
            name = _validate_artifact_path(key)
        normalized[name] = _require_sha256(digest, field=f"{field}/{name}")
    return normalized


def _normalize_emission_hash_map(
    value: Mapping[str, str], *, field: str
) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise PhaseTransitionError(f"{field} must be a mapping")
    return _validate_hash_map(dict(value), field=field)


def _expected_input_phase_hashes(
    active_phase_hashes: Mapping[str, str], phase_id: str
) -> dict[str, str]:
    phase_index = PHASES.index(phase_id)
    return {
        prior: active_phase_hashes[prior]
        for prior in PHASES[:phase_index]
    }


def _expected_parent_hash(
    active_phase_hashes: Mapping[str, str], phase_id: str
) -> str | None:
    phase_index = PHASES.index(phase_id)
    if phase_index == 0:
        return None
    return active_phase_hashes[PHASES[phase_index - 1]]


def _assert_active_inputs(
    *,
    phase_id: str,
    inputs: Mapping[str, str],
    active_artifact_hashes: Mapping[str, str],
) -> None:
    if phase_id == "P0":
        if inputs:
            raise StaleArtifactError("P0 cannot read an artifact from an earlier phase")
        return
    if not inputs:
        raise StaleArtifactError(f"{phase_id} must bind at least one active input artifact")
    for path, digest in inputs.items():
        if path not in active_artifact_hashes:
            raise StaleArtifactError(
                f"{phase_id} input artifact is not active in the current generation: {path}"
            )
        current = active_artifact_hashes[path]
        if digest != current:
            raise StaleArtifactError(
                f"{phase_id} input artifact is stale: {path}; expected {current}, got {digest}"
            )


def _assert_new_outputs(
    *,
    phase_id: str,
    outputs: Mapping[str, str],
    active_artifact_hashes: Mapping[str, str],
) -> None:
    if not outputs:
        raise PhaseTransitionError(f"{phase_id} must seal at least one output artifact hash")
    active_spellings = {
        path.casefold(): path for path in active_artifact_hashes
    }
    output_spellings: dict[str, str] = {}
    collisions: set[str] = set()
    for path in outputs:
        folded = path.casefold()
        if folded in active_spellings:
            collisions.add(active_spellings[folded])
        if folded in output_spellings:
            collisions.add(output_spellings[folded])
            collisions.add(path)
        output_spellings[folded] = path
    if collisions:
        raise PhaseTransitionError(
            f"{phase_id} cannot overwrite or alias artifact paths: "
            f"{', '.join(sorted(collisions))}"
        )


def _validate_event_shape(event: Mapping[str, object], *, index: int) -> None:
    if set(event) != _EVENT_KEYS:
        missing = sorted(_EVENT_KEYS - set(event))
        extra = sorted(set(event) - _EVENT_KEYS)
        raise PhaseHistoryError(
            f"phase event {index} has a non-closed shape; missing={missing}, extra={extra}"
        )
    if event["schema_id"] != "crossframe.promax.v8.phase-event":
        raise PhaseHistoryError(f"phase event {index} has an invalid schema_id")
    if type(event["schema_version"]) is not int or event["schema_version"] != 1:
        raise PhaseHistoryError(f"phase event {index} has an invalid schema_version")
    if type(event["event_index"]) is not int or event["event_index"] != index:
        raise PhaseHistoryError(
            f"phase event index mismatch: expected {index}, got {event['event_index']!r}"
        )
    if event["phase_id"] not in PHASES:
        raise PhaseTransitionError(f"phase event {index} has unknown phase_id")
    if event["event_type"] not in {"phase_sealed", "phase_reset"}:
        raise PhaseTransitionError(f"phase event {index} has unknown event_type")


def validate_phase_history(
    events: Iterable[Mapping[str, object]],
    *,
    expected_binding: RunBinding | None = None,
) -> PhaseState:
    """Validate a complete append-only history and return its active structured state."""

    if expected_binding is not None and not isinstance(expected_binding, RunBinding):
        raise RunBindingError("expected_binding must be a RunBinding")
    records = list(events)
    binding = expected_binding
    chain_head: str | None = None
    seen_event_hashes: set[str] = set()
    active_phase_hashes: dict[str, str] = {}
    active_artifact_hashes: dict[str, str] = {}
    artifact_owner_phases: dict[str, str] = {}
    invalidated_phases: tuple[str, ...] = ()

    for index, raw_event in enumerate(records):
        if not isinstance(raw_event, Mapping):
            raise PhaseHistoryError(f"phase event {index} must be an object")
        event = dict(raw_event)
        event_sha256 = _require_sha256(
            event.get("event_sha256"), field=f"event[{index}].event_sha256"
        )
        if event_sha256 in seen_event_hashes:
            raise PhaseReplayError(f"phase event replayed at index {index}: {event_sha256}")
        _validate_event_shape(event, index=index)

        unsigned = dict(event)
        unsigned.pop("event_sha256")
        actual_event_sha256 = sha256_json(unsigned)
        if event_sha256 != actual_event_sha256:
            raise PhaseHistoryError(
                f"phase event hash mismatch at index {index}: "
                f"expected {actual_event_sha256}, got {event_sha256}"
            )

        event_binding = _event_binding(event)
        if binding is None:
            binding = event_binding
        elif event_binding != binding:
            raise RunBindingError(
                f"phase event {index} changes immutable run_id/run_nonce/request/source binding"
            )

        previous = event["previous_event_sha256"]
        if chain_head is None:
            if previous is not None:
                raise PhaseHistoryError("P0 history head must have null previous_event_sha256")
        else:
            _require_sha256(
                previous,
                field=f"event[{index}].previous_event_sha256",
            )
            if previous != chain_head:
                raise PhaseHistoryError(
                    f"append-only event link mismatch at index {index}: "
                    f"expected {chain_head}, got {previous}"
                )

        phase_id = event["phase_id"]
        parent = event["parent_phase_sha256"]
        input_phase_hashes = _validate_hash_map(
            event["input_phase_hashes"], field="input_phase_hashes"
        )
        inputs = _validate_hash_map(
            event["input_artifact_hashes"], field="input_artifact_hashes"
        )
        outputs = _validate_hash_map(
            event["output_artifact_hashes"], field="output_artifact_hashes"
        )

        if event["event_type"] == "phase_sealed":
            completed = tuple(
                phase for phase in PHASES if phase in active_phase_hashes
            )
            expected_phase = _next_phase(completed)
            if phase_id != expected_phase:
                raise PhaseTransitionError(
                    f"phase event {index} skipped or duplicated a phase: "
                    f"expected {expected_phase}, got {phase_id}"
                )
            if event["status"] != "completed":
                raise PhaseTransitionError("phase_sealed event status must be completed")
            if event["invalidated_phases"] != [] or event["reset_reason"] is not None:
                raise PhaseTransitionError(
                    "phase_sealed event cannot contain reset scope or reset_reason"
                )

            expected_parent = _expected_parent_hash(active_phase_hashes, phase_id)
            if parent != expected_parent:
                raise PhaseParentHashError(
                    f"{phase_id} parent_phase_sha256 mismatch: "
                    f"expected {expected_parent}, got {parent}"
                )
            expected_inputs = _expected_input_phase_hashes(
                active_phase_hashes, phase_id
            )
            if input_phase_hashes != expected_inputs:
                raise StaleArtifactError(
                    f"{phase_id} input phase lineage is stale; "
                    f"expected {expected_inputs}, got {input_phase_hashes}"
                )
            _assert_active_inputs(
                phase_id=phase_id,
                inputs=inputs,
                active_artifact_hashes=active_artifact_hashes,
            )
            _assert_new_outputs(
                phase_id=phase_id,
                outputs=outputs,
                active_artifact_hashes=active_artifact_hashes,
            )
            active_phase_hashes[phase_id] = event_sha256
            for path, digest in outputs.items():
                active_artifact_hashes[path] = digest
                artifact_owner_phases[path] = phase_id
            invalidated_phases = tuple(
                phase for phase in invalidated_phases if phase != phase_id
            )
        else:
            if phase_id not in active_phase_hashes:
                raise PhaseTransitionError(
                    f"reset boundary {phase_id} is not an active completed phase"
                )
            if event["status"] != "reset":
                raise PhaseTransitionError("phase_reset event status must be reset")
            if inputs or outputs:
                raise PhaseTransitionError(
                    "phase_reset event cannot read or emit artifact hashes"
                )
            reason = event["reset_reason"]
            if not isinstance(reason, str) or not reason.strip():
                raise PhaseTransitionError("phase_reset requires a non-empty reset_reason")
            expected_invalidated = list(downstream_phases(phase_id))
            if event["invalidated_phases"] != expected_invalidated:
                raise PhaseTransitionError(
                    f"reset of {phase_id} must invalidate exactly {expected_invalidated}"
                )
            expected_parent = _expected_parent_hash(active_phase_hashes, phase_id)
            if parent != expected_parent:
                raise PhaseParentHashError(
                    f"reset of {phase_id} has stale parent_phase_sha256"
                )
            expected_inputs = _expected_input_phase_hashes(
                active_phase_hashes, phase_id
            )
            if input_phase_hashes != expected_inputs:
                raise StaleArtifactError(
                    f"reset of {phase_id} has stale input phase lineage"
                )

            affected = set(downstream_phases(phase_id))
            for affected_phase in affected:
                active_phase_hashes.pop(affected_phase, None)
            for path, owner in list(artifact_owner_phases.items()):
                if owner in affected:
                    artifact_owner_phases.pop(path)
                    active_artifact_hashes.pop(path)
            invalidated_phases = downstream_phases(phase_id)

        seen_event_hashes.add(event_sha256)
        chain_head = event_sha256

    return _phase_state(
        binding=binding,
        event_count=len(records),
        chain_head_sha256=chain_head,
        active_phase_hashes=active_phase_hashes,
        active_artifact_hashes=active_artifact_hashes,
        artifact_owner_phases=artifact_owner_phases,
        invalidated_phases=invalidated_phases,
    )


def _event_base(state: PhaseState, phase_id: str) -> dict[str, object]:
    if state.binding is None:
        raise RunBindingError("cannot emit a phase event from an unbound empty history")
    return {
        "schema_id": "crossframe.promax.v8.phase-event",
        "schema_version": 1,
        "event_index": state.event_count,
        "run_id": state.binding.run_id,
        "run_nonce": state.binding.run_nonce,
        "request_sha256": state.binding.request_sha256,
        "source_snapshot_sha256": state.binding.source_snapshot_sha256,
        "phase_id": phase_id,
        "parent_phase_sha256": _expected_parent_hash(
            state.active_phase_hashes, phase_id
        ),
        "input_phase_hashes": _expected_input_phase_hashes(
            state.active_phase_hashes, phase_id
        ),
        "previous_event_sha256": state.chain_head_sha256,
    }


def _seal_event_hash(event: dict[str, object]) -> dict[str, object]:
    sealed = dict(event)
    sealed["event_sha256"] = sha256_json(sealed)
    return sealed


def seal_phase_event(
    state: PhaseState,
    phase_id: str,
    *,
    input_artifact_hashes: Mapping[str, str],
    output_artifact_hashes: Mapping[str, str],
) -> dict[str, object]:
    """Create, but do not append, the next canonical completed-phase event."""

    if not isinstance(state, PhaseState):
        raise PhaseTransitionError("state must be a validated PhaseState")
    if phase_id not in PHASES:
        raise PhaseTransitionError(f"unknown phase_id: {phase_id!r}")
    if phase_id != state.next_phase_id:
        raise PhaseTransitionError(
            f"phase ordering violation: expected {state.next_phase_id}, got {phase_id}"
        )
    inputs = _normalize_emission_hash_map(
        input_artifact_hashes, field="input_artifact_hashes"
    )
    outputs = _normalize_emission_hash_map(
        output_artifact_hashes, field="output_artifact_hashes"
    )
    _assert_active_inputs(
        phase_id=phase_id,
        inputs=inputs,
        active_artifact_hashes=state.active_artifact_hashes,
    )
    _assert_new_outputs(
        phase_id=phase_id,
        outputs=outputs,
        active_artifact_hashes=state.active_artifact_hashes,
    )
    event = {
        **_event_base(state, phase_id),
        "event_type": "phase_sealed",
        "status": "completed",
        "input_artifact_hashes": dict(sorted(inputs.items())),
        "output_artifact_hashes": dict(sorted(outputs.items())),
        "invalidated_phases": [],
        "reset_reason": None,
    }
    return _seal_event_hash(event)


def build_reset_event(
    state: PhaseState,
    reset_from_phase: str,
    *,
    reason: str,
) -> dict[str, object]:
    """Create an append-only reset that invalidates one phase and all descendants."""

    if not isinstance(state, PhaseState):
        raise PhaseTransitionError("state must be a validated PhaseState")
    if reset_from_phase not in PHASES:
        raise PhaseTransitionError(f"unknown reset boundary: {reset_from_phase!r}")
    if reset_from_phase not in state.active_phase_hashes:
        raise PhaseTransitionError(
            f"reset boundary {reset_from_phase} is not an active completed phase"
        )
    if not isinstance(reason, str) or not reason.strip():
        raise PhaseTransitionError("reset reason must be non-empty")
    event = {
        **_event_base(state, reset_from_phase),
        "event_type": "phase_reset",
        "status": "reset",
        "input_artifact_hashes": {},
        "output_artifact_hashes": {},
        "invalidated_phases": list(downstream_phases(reset_from_phase)),
        "reset_reason": reason.strip(),
    }
    return _seal_event_hash(event)


def _lock_event_file(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_event_file(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _acquire_event_lock(lock_path: Path) -> _EventLock:
    lock_path = Path(lock_path)
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+b", buffering=0)
    except OSError as error:
        raise PhaseHistoryError(f"cannot open phase-event lock: {lock_path}") from error
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\x00")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        try:
            handle.close()
        except OSError:
            pass
        raise PhaseHistoryError(
            f"cannot initialize phase-event lock: {lock_path}"
        ) from error
    try:
        _lock_event_file(handle)
    except OSError as error:
        try:
            handle.close()
        except OSError:
            pass
        raise PhaseLockBusy(f"phase-event lock is already held: {lock_path}") from error
    return _EventLock(path=lock_path, handle=handle)


def _release_event_lock(event_lock: _EventLock) -> None:
    if event_lock.released:
        return
    descriptor = event_lock.handle.fileno()
    try:
        try:
            _unlock_event_file(event_lock.handle)
        except OSError as error:
            _warn_nonfatal(
                "phase-event explicit unlock failed; file close will release it: "
                f"{error}"
            )
    finally:
        try:
            event_lock.handle.close()
        except OSError as error:
            _warn_nonfatal(f"phase-event lock close failed: {error}")
            try:
                os.close(descriptor)
            except OSError as fallback_error:
                _warn_nonfatal(
                    "phase-event lock descriptor close failed: "
                    f"{fallback_error}"
                )
        event_lock.released = True


@contextmanager
def exclusive_run_lock(run_dir: Path | str) -> Iterator[None]:
    """Hold the cross-process transaction lock for one artifact run."""

    candidate = Path(run_dir)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise PhaseHistoryError(f"cannot resolve artifact run for locking: {candidate}") from error
    if not resolved.is_dir() or resolved.is_symlink():
        raise PhaseHistoryError(f"artifact run lock target must be a real directory: {resolved}")
    lock_path = resolved.parent / f".{resolved.name}.promax-runtime.lock"
    event_lock = _acquire_event_lock(lock_path)
    try:
        yield
    finally:
        _release_event_lock(event_lock)


@contextmanager
def phase_event_cas_guard(
    path: Path | str,
    *,
    expected_head_sha256: str | None | object = _NO_EXPECTED_HEAD,
    expected_binding: RunBinding | None = None,
) -> Iterator[tuple[list[dict[str, object]], PhaseState, bytes]]:
    """Lock and canonically reload one phase log for a multi-file transaction."""

    event_path = _canonical_event_log_path(path)
    _assert_single_link_event_log(event_path)
    lock_path = event_path.with_name(f".{event_path.name}.lock")
    event_lock = _acquire_event_lock(lock_path)
    try:
        _assert_single_link_event_log(event_path)
        records = _load_canonical_phase_events(event_path) if event_path.exists() else []
        state = validate_phase_history(records, expected_binding=expected_binding)
        if (
            expected_head_sha256 is not _NO_EXPECTED_HEAD
            and state.chain_head_sha256 != expected_head_sha256
        ):
            raise PhaseCASMismatch(
                "phase event CAS mismatch: expected head "
                f"{expected_head_sha256}, current head {state.chain_head_sha256}"
            )
        raw = event_path.read_bytes() if event_path.exists() else b""
        yield records, state, raw
    finally:
        _release_event_lock(event_lock)


def _load_canonical_phase_events(event_path: Path) -> list[dict[str, object]]:
    records = load_jsonl(event_path)
    try:
        raw = event_path.read_bytes()
    except OSError as error:
        raise JSONDocumentError(f"cannot re-read phase event log: {event_path}") from error
    physical_lines = [line + b"\n" for line in raw[:-1].split(b"\n")]
    if len(physical_lines) != len(records):
        raise JSONDocumentError(
            f"phase event log record count changed while locked: {event_path}"
        )
    for index, (physical_line, record) in enumerate(
        zip(physical_lines, records), start=1
    ):
        if physical_line != canonical_json_bytes(record) + b"\n":
            raise JSONDocumentError(
                f"phase event log record is not canonical JSON at "
                f"{event_path}:{index}"
            )
    return records


def _canonical_event_log_path(path: Path | str) -> Path:
    candidate = Path(path)
    try:
        if candidate.is_symlink():
            raise PhaseHistoryError(
                f"phase event log must not be a symbolic-link alias: {candidate}"
            )
        return candidate.resolve(strict=False)
    except OSError as error:
        raise PhaseHistoryError(
            f"cannot resolve phase event log path: {candidate}"
        ) from error


def _assert_single_link_event_log(event_path: Path) -> None:
    try:
        metadata = event_path.stat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise PhaseHistoryError(
            f"cannot inspect phase event log identity: {event_path}"
        ) from error
    if not stat.S_ISREG(metadata.st_mode):
        raise PhaseHistoryError(f"phase event log must be a regular file: {event_path}")
    if metadata.st_nlink != 1:
        raise PhaseHistoryError(
            f"phase event log hardlink aliases are forbidden: {event_path} "
            f"has link count {metadata.st_nlink}"
        )


def _assert_open_log_identity(handle: BinaryIO, event_path: Path) -> None:
    try:
        metadata = os.fstat(handle.fileno())
    except OSError as error:
        raise OSError(f"cannot inspect open phase event log: {event_path}") from error
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise OSError(
            f"phase event log became a hardlink or non-regular alias: {event_path}"
        )


def _fsync_directory(directory: Path) -> bool:
    """Durably sync a directory entry on platforms that expose this operation."""

    if os.name == "nt":
        return False
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(str(directory), flags)
        os.fsync(descriptor)
    except OSError as error:
        unsupported = {
            errno.EINVAL,
            getattr(errno, "ENOTSUP", errno.EINVAL),
            getattr(errno, "EOPNOTSUPP", errno.EINVAL),
        }
        if error.errno in unsupported:
            return False
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return True


def append_phase_event(
    path: Path | str,
    event: Mapping[str, object],
    *,
    expected_head_sha256: str | None,
) -> PhaseState:
    """CAS-append one canonical event while holding a cross-process sidecar lock."""

    event_path = _canonical_event_log_path(path)
    _assert_single_link_event_log(event_path)
    lock_path = event_path.with_name(f".{event_path.name}.lock")
    event_lock = _acquire_event_lock(lock_path)
    try:
        _assert_single_link_event_log(event_path)
        if event_path.exists():
            records = _load_canonical_phase_events(event_path)
        else:
            records = []
        current_state = validate_phase_history(records)
        if current_state.chain_head_sha256 != expected_head_sha256:
            raise PhaseCASMismatch(
                "phase event CAS mismatch: expected head "
                f"{expected_head_sha256}, current head {current_state.chain_head_sha256}"
            )
        candidate = dict(event)
        next_state = validate_phase_history(
            [*records, candidate],
            expected_binding=current_state.binding,
        )
        record = canonical_json_bytes(candidate) + b"\n"
        existed_before = event_path.exists()
        original_size = event_path.stat().st_size if existed_before else 0
        created_by_us = False
        try:
            event_path.parent.mkdir(parents=True, exist_ok=True)
            mode = "ab" if existed_before else "xb"
            with event_path.open(mode, buffering=0) as handle:
                created_by_us = not existed_before
                try:
                    _assert_open_log_identity(handle, event_path)
                    written = handle.write(record)
                    if written != len(record):
                        raise OSError(
                            f"short append: wrote {written} of {len(record)} bytes"
                        )
                    handle.flush()
                    os.fsync(handle.fileno())
                    _assert_open_log_identity(handle, event_path)
                    if created_by_us:
                        _fsync_directory(event_path.parent)
                except OSError as append_error:
                    try:
                        handle.truncate(original_size)
                        handle.flush()
                        os.fsync(handle.fileno())
                    except OSError as rollback_error:
                        raise OSError(
                            "phase event append failed and rollback could not be "
                            f"durably synced: {rollback_error}"
                        ) from append_error
                    raise
        except OSError as error:
            if created_by_us and event_path.exists():
                try:
                    event_path.unlink()
                    _fsync_directory(event_path.parent)
                except OSError as cleanup_error:
                    raise PhaseHistoryError(
                        "phase event append failed and the new empty log could not be removed: "
                        f"{event_path}"
                    ) from cleanup_error
            raise PhaseHistoryError(f"cannot append phase event: {event_path}") from error
        return next_state
    except JSONDocumentError:
        raise
    finally:
        _release_event_lock(event_lock)
