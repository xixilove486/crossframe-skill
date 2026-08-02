from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from jsonschema import ValidationError

from check_crossframe_ultra_v82_source import EXPECTED_TREE_MERKLE_ROOT

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
from .evidence import EvidenceFrozenError, EvidenceLedger
from .schemas import validate_instance

PHASE_ORDER = ("U0", "U1", "U2", "U3")
PHASE_EVENT_SCHEMA_ID = "crossframe.ultra.v82.phase-event"
RUN_CONTRACT_SCHEMA_ID = "crossframe.ultra.v82.run-contract"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_CAPABILITY_STATES = frozenset(
    {"available", "required", "unavailable", "not-applicable"}
)
_CAPABILITY_NAMES = frozenset(
    {
        "filesystem",
        "docx_parser",
        "network",
        "retrieval",
        "validators",
        "subagents",
        "model_context",
    }
)
_RUN_CONTRACT_FIELDS = frozenset(
    {
        "trigger",
        "request_sha256",
        "run_mode",
        "sensitivity",
        "retention",
        "outbound_permission",
        "evidence_cutoff",
        "capabilities",
        "resource_limits",
    }
)
_RESOURCE_LIMIT_FIELDS = frozenset(
    {
        "maximum_branches",
        "maximum_retrieval_rounds_without_material_novelty",
        "maximum_tool_retries",
        "maximum_repair_attempts",
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
    "source_tree_sha256": EXPECTED_TREE_MERKLE_ROOT,
}
_EVENT_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "generated_at",
        "content_sha256",
        "phase_id",
        "event_type",
        "parent_event_sha256",
        "input_artifact_hashes",
        "output_artifact_hashes",
        "version_binding",
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
_SOURCE_REPOSITORY = Path(__file__).resolve().parents[4]


class PhaseTransitionError(RuntimeError):
    """Raised when a phase would skip or overwrite an append-only boundary."""


class PhaseIntegrityError(RuntimeError):
    """Raised when immutable run or event bindings no longer match."""


class RunContractError(ValueError):
    """Raised when the closed U0 run contract is malformed."""


class RunBlockedError(RunContractError):
    """Raised when a required capability is unavailable."""


def _plain_mapping(value: object, *, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RunContractError(f"{name} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise RunContractError(f"{name} keys must be strings")
    return copy.deepcopy(dict(value))


def _require_exact_fields(
    value: Mapping[str, object], expected: frozenset[str], *, name: str
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RunContractError(
            f"{name} fields are not closed (missing={missing}, extra={extra})"
        )


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _parse_timestamp(value: object, *, error_type: type[Exception]) -> datetime:
    if not isinstance(value, str) or not value:
        raise error_type("timestamp must be a non-empty RFC3339 string")
    candidate = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise error_type(f"invalid RFC3339 timestamp: {value!r}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise error_type("timestamp must include an offset")
    return parsed


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PhaseIntegrityError("event clock must be timezone-aware")
    utc = value.astimezone(timezone.utc)
    return utc.isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PhaseIntegrityError(f"event is not canonical JSON: {error}") from error


def compute_event_sha256(event: Mapping[str, object]) -> str:
    payload = {key: copy.deepcopy(value) for key, value in event.items() if key != "event_sha256"}
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _compute_event_content_sha256(event: Mapping[str, object]) -> str:
    payload = {
        key: copy.deepcopy(value)
        for key, value in event.items()
        if key not in {"content_sha256", "event_sha256"}
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return copy.deepcopy(value)


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return copy.deepcopy(value)


def _validate_version_binding(value: Mapping[str, object]) -> dict[str, object]:
    binding = copy.deepcopy(dict(value))
    if frozenset(binding) != _VERSION_BINDING_FIELDS:
        raise PhaseIntegrityError("version binding fields do not match the closed contract")
    for field in (
        "framework_raw_sha256",
        "framework_semantic_sha256",
        "source_tree_sha256",
    ):
        if not _is_sha256(binding[field]):
            raise PhaseIntegrityError(f"invalid version binding hash: {field}")
    if (
        not isinstance(binding["artifact_schema_version"], int)
        or isinstance(binding["artifact_schema_version"], bool)
        or binding["artifact_schema_version"] < 1
    ):
        raise PhaseIntegrityError("artifact_schema_version must be a positive integer")
    for field in _VERSION_BINDING_FIELDS - {
        "framework_raw_sha256",
        "framework_semantic_sha256",
        "source_tree_sha256",
        "artifact_schema_version",
    }:
        if not isinstance(binding[field], str) or not binding[field]:
            raise PhaseIntegrityError(f"version binding field is empty: {field}")
    if binding != _CURRENT_VERSION_BINDING:
        raise PhaseIntegrityError("version binding differs from the current authority")
    return binding


def _make_run_contract_artifact(
    contract: Mapping[str, object],
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    generated_at: str,
) -> dict[str, object]:
    artifact = {
        "schema_id": RUN_CONTRACT_SCHEMA_ID,
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": copy.deepcopy(dict(version_binding)),
        "generated_at": generated_at,
        "phase_id": "U0",
        **copy.deepcopy(dict(contract)),
    }
    artifact["content_sha256"] = hashlib.sha256(_canonical_json(artifact)).hexdigest()
    try:
        validate_instance("ultra-run-contract.schema.json", artifact)
    except ValidationError as error:
        raise RunContractError(
            f"run contract violates the public schema: {error.message}"
        ) from error
    return artifact


def validate_run_contract(
    value: Mapping[str, object],
    *,
    capability_availability: Mapping[str, str] | None = None,
) -> dict[str, object]:
    contract = _plain_mapping(value, name="run contract")
    _require_exact_fields(contract, _RUN_CONTRACT_FIELDS, name="run contract")
    enums = {
        "trigger": {
            "crossframe-ultra",
            "CrossFrame Ultra",
            "$crossframe-ultra",
            "/crossframe-ultra",
        },
        "run_mode": {"production", "test"},
        "sensitivity": {"public", "internal", "private", "restricted"},
        "retention": {"retain", "delivery-only", "user-directed"},
        "outbound_permission": {"allowed", "deidentified-only", "denied"},
    }
    for field, allowed in enums.items():
        if contract[field] not in allowed:
            raise RunContractError(f"invalid {field}: {contract[field]!r}")
    if not _is_sha256(contract["request_sha256"]):
        raise RunContractError("request_sha256 must be a lowercase SHA-256")
    _parse_timestamp(contract["evidence_cutoff"], error_type=RunContractError)

    capabilities = _plain_mapping(contract["capabilities"], name="capabilities")
    _require_exact_fields(capabilities, _CAPABILITY_NAMES, name="capabilities")
    for name, state in capabilities.items():
        if state not in _CAPABILITY_STATES:
            raise RunContractError(f"invalid capability state for {name}: {state!r}")
    contract["capabilities"] = capabilities

    limits = _plain_mapping(contract["resource_limits"], name="resource limits")
    _require_exact_fields(limits, _RESOURCE_LIMIT_FIELDS, name="resource limits")
    for name, value_item in limits.items():
        if not isinstance(value_item, int) or isinstance(value_item, bool):
            raise RunContractError(f"resource limit {name} must be an integer")
    if limits["maximum_branches"] < 1:
        raise RunContractError("maximum_branches must be positive")
    if limits["maximum_retrieval_rounds_without_material_novelty"] < 0:
        raise RunContractError("retrieval novelty limit cannot be negative")
    if limits["maximum_tool_retries"] < 1:
        raise RunContractError("maximum_tool_retries must be positive")
    if not 0 <= limits["maximum_repair_attempts"] <= 3:
        raise RunContractError("maximum_repair_attempts must be between zero and three")
    contract["resource_limits"] = limits

    availability = dict(capability_availability or {})
    if any(name not in _CAPABILITY_NAMES for name in availability):
        raise RunContractError("capability availability contains an unknown capability")
    for name, state in availability.items():
        if state not in _CAPABILITY_STATES:
            raise RunContractError(f"invalid availability for {name}: {state!r}")
    for name, state in capabilities.items():
        if state == "required" and availability.get(name) != "available":
            raise RunBlockedError(f"required capability is unavailable: {name}")
    return contract


def _validate_hashes(values: Sequence[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise PhaseIntegrityError(f"{field} must be a sequence of hashes")
    snapshot = tuple(values)
    if any(not _is_sha256(value) for value in snapshot):
        raise PhaseIntegrityError(f"{field} contains an invalid SHA-256")
    if len(snapshot) != len(set(snapshot)):
        raise PhaseIntegrityError(f"{field} contains duplicate hashes")
    return snapshot


def _validate_invalidated_phases(
    phase_id: str, values: Sequence[str]
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise PhaseIntegrityError("invalidated_phases must be a sequence")
    snapshot = tuple(values)
    if any(not isinstance(phase, str) for phase in snapshot):
        raise PhaseIntegrityError("invalidated phases must be strings")
    if len(snapshot) != len(set(snapshot)):
        raise PhaseIntegrityError("invalidated phases contain duplicates")
    if phase_id not in PHASE_ORDER:
        raise PhaseIntegrityError("phase_id is outside U0-U3")
    current_index = PHASE_ORDER.index(phase_id)
    if any(
        phase not in PHASE_ORDER or PHASE_ORDER.index(phase) <= current_index
        for phase in snapshot
    ):
        raise PhaseIntegrityError("invalidated phases must be downstream")
    return snapshot


class PhaseStore:
    """In-memory U0-U3 append-only event chain with immutable run bindings."""

    def __init__(
        self,
        *,
        run_id: str,
        version_binding: Mapping[str, object],
        source_sha256: str,
        input_artifact_hashes: Sequence[str],
        evidence_cutoff: str,
        now: datetime,
        run_contract: Mapping[str, object],
        capability_availability: Mapping[str, str] | None = None,
        source_repository: Path | None = None,
    ) -> None:
        if not isinstance(run_id, str) or not run_id.strip():
            raise PhaseIntegrityError("run_id must be non-empty")
        if not _is_sha256(source_sha256):
            raise PhaseIntegrityError("source_sha256 must be a lowercase SHA-256")
        _parse_timestamp(evidence_cutoff, error_type=PhaseIntegrityError)
        timestamp = _format_timestamp(now)
        binding = _validate_version_binding(version_binding)
        contract = validate_run_contract(
            run_contract,
            capability_availability=capability_availability,
        )
        if contract["evidence_cutoff"] != evidence_cutoff:
            raise RunContractError("run contract evidence cutoff differs from the run")
        authority_repository = (source_repository or _SOURCE_REPOSITORY).resolve()
        if authority_repository != _SOURCE_REPOSITORY:
            raise PhaseIntegrityError("source authority repository must use the fixed runtime root")

        self.run_id = run_id
        self._version_binding = binding
        self._source_sha256 = source_sha256
        self._input_artifact_hashes = _validate_hashes(
            input_artifact_hashes, field="input_artifact_hashes"
        )
        self._evidence_cutoff = evidence_cutoff
        self._timestamp = timestamp
        contract_artifact = _make_run_contract_artifact(
            contract,
            run_id=run_id,
            version_binding=binding,
            generated_at=timestamp,
        )
        self._run_contract = _freeze(contract_artifact)
        self._run_contract_sha256 = str(contract_artifact["content_sha256"])
        self._capability_availability = copy.deepcopy(dict(capability_availability or {}))
        self._source_repository = authority_repository
        self._events: list[dict[str, object]] = []
        self._event_hashes: set[str] = set()
        self._completed: list[str] = []
        self._evidence_ledger = EvidenceLedger(run_id, evidence_cutoff)
        self._u1_coverage_sha256: str | None = None

    @property
    def run_contract(self) -> Mapping[str, object]:
        result = _thaw(self._run_contract)
        assert isinstance(result, dict)
        return result

    @property
    def events(self) -> tuple[dict[str, object], ...]:
        return tuple(copy.deepcopy(self._events))

    @property
    def current_phase(self) -> str | None:
        return self._completed[-1] if self._completed else None

    @property
    def evidence_frozen(self) -> bool:
        return self._evidence_ledger.frozen

    @property
    def evidence_sha256(self) -> str:
        return self._evidence_ledger.content_sha256

    @property
    def u1_coverage_sha256(self) -> str:
        if self._u1_coverage_sha256 is None:
            raise PhaseIntegrityError("U1 source coverage has not been captured")
        return self._u1_coverage_sha256

    @property
    def has_valid_u1_source_coverage(self) -> bool:
        return (
            self.current_phase == "U1"
            and self._u1_coverage_sha256 is not None
            and bool(self._events)
            and self._u1_coverage_sha256
            in self._events[-1]["output_artifact_hashes"]
        )

    def _capture_u1_source_coverage(self, parent_event_sha256: str) -> str:
        """Execute the authority read internally at the U0→U1 append boundary."""
        from . import source_integrity

        try:
            manifest_path = (
                self._source_repository
                / "skills"
                / "crossframe-ultra"
                / "references"
                / "source-manifest.json"
            )
            manifest = source_integrity.load_source_manifest(manifest_path)
            measurement = source_integrity.measure_u1_prerequisites(
                self._source_repository, manifest=manifest
            )
            source_integrity.verify_u1_prerequisites(measurement)
            return source_integrity._capture_validate_u1_authority(
                self._source_repository,
                run_id=self.run_id,
                version_binding=self._version_binding,
                manifest=manifest,
                read_at=self._timestamp,
                parent_event_sha256=parent_event_sha256,
            )
        except (
            source_integrity.SourceCoverageError,
            source_integrity.SourceLockError,
            source_integrity.SourceManifestError,
            OSError,
        ) as error:
            raise PhaseIntegrityError("U1 authority source coverage failed") from error

    def _expected_phase(self) -> str | None:
        index = len(self._completed)
        return PHASE_ORDER[index] if index < len(PHASE_ORDER) else None

    def _check_phase(self, phase_id: str) -> None:
        expected = self._expected_phase()
        if phase_id != expected:
            raise PhaseTransitionError(
                f"expected phase {expected!r}, received {phase_id!r}"
            )

    def _check_bindings(
        self,
        *,
        parent_event_sha256: str | None,
        input_artifact_hashes: Sequence[str] | None,
        version_binding: Mapping[str, object] | None,
        source_sha256: str | None,
        evidence_cutoff: str | None,
    ) -> str:
        expected_parent = (
            str(self._events[-1]["event_sha256"]) if self._events else "0" * 64
        )
        if parent_event_sha256 is not None and parent_event_sha256 != expected_parent:
            raise PhaseIntegrityError("parent event hash does not match the append boundary")
        if input_artifact_hashes is not None and _validate_hashes(
            input_artifact_hashes, field="input_artifact_hashes"
        ) != self._input_artifact_hashes:
            raise PhaseIntegrityError("input artifact hashes changed")
        if version_binding is not None and _validate_version_binding(
            version_binding
        ) != self._version_binding:
            raise PhaseIntegrityError("version binding changed")
        if source_sha256 is not None and source_sha256 != self._source_sha256:
            raise PhaseIntegrityError("source binding changed")
        if evidence_cutoff is not None and evidence_cutoff != self._evidence_cutoff:
            raise PhaseIntegrityError("evidence cutoff changed")
        return expected_parent

    def _make_event(
        self,
        *,
        phase_id: str,
        event_type: str,
        output_artifact_hashes: Sequence[str],
        status: str,
        failure_code: str | None,
        invalidated_phases: Sequence[str],
        parent_event_sha256: str,
    ) -> dict[str, object]:
        event: dict[str, object] = {
            "schema_id": PHASE_EVENT_SCHEMA_ID,
            "schema_version": 1,
            "run_id": self.run_id,
            "generated_at": self._timestamp,
            "phase_id": phase_id,
            "event_type": event_type,
            "parent_event_sha256": parent_event_sha256,
            "input_artifact_hashes": list(self._input_artifact_hashes),
            "output_artifact_hashes": list(output_artifact_hashes),
            "version_binding": copy.deepcopy(self._version_binding),
            "source_sha256": self._source_sha256,
            "evidence_cutoff": self._evidence_cutoff,
            "run_contract_sha256": self._run_contract_sha256,
            "timestamp": self._timestamp,
            "status": status,
            "failure_code": failure_code,
            "invalidated_phases": list(invalidated_phases),
        }
        event["content_sha256"] = _compute_event_content_sha256(event)
        event["event_sha256"] = compute_event_sha256(event)
        return event

    def _append_event(self, event: Mapping[str, object]) -> dict[str, object]:
        snapshot = copy.deepcopy(dict(event))
        if frozenset(snapshot) != _EVENT_FIELDS:
            raise PhaseIntegrityError("event fields do not match the closed contract")
        if snapshot.get("schema_id") != PHASE_EVENT_SCHEMA_ID:
            raise PhaseIntegrityError("event schema_id is invalid")
        if snapshot.get("schema_version") != 1:
            raise PhaseIntegrityError("event schema_version is invalid")
        if snapshot.get("generated_at") != snapshot.get("timestamp"):
            raise PhaseIntegrityError("event generated_at differs from its timestamp")
        if snapshot.get("content_sha256") != _compute_event_content_sha256(snapshot):
            raise PhaseIntegrityError("content_sha256 does not match the event payload")
        event_hash = snapshot.get("event_sha256")
        if not _is_sha256(event_hash):
            raise PhaseIntegrityError("event_sha256 is invalid")
        if event_hash != compute_event_sha256(snapshot):
            raise PhaseIntegrityError("event_sha256 does not match the event payload")
        if event_hash in self._event_hashes:
            raise PhaseIntegrityError("event hash replay detected")
        self._events.append(snapshot)
        self._event_hashes.add(str(event_hash))
        if snapshot["status"] == "complete":
            self._completed.append(str(snapshot["phase_id"]))
        return copy.deepcopy(snapshot)

    def complete(
        self,
        phase_id: str,
        *,
        artifact_hashes: Sequence[str],
        parent_event_sha256: str | None = None,
        input_artifact_hashes: Sequence[str] | None = None,
        version_binding: Mapping[str, object] | None = None,
        source_sha256: str | None = None,
        evidence_cutoff: str | None = None,
    ) -> dict[str, object]:
        self._check_phase(phase_id)
        parent = self._check_bindings(
            parent_event_sha256=parent_event_sha256,
            input_artifact_hashes=input_artifact_hashes,
            version_binding=version_binding,
            source_sha256=source_sha256,
            evidence_cutoff=evidence_cutoff,
        )
        outputs = _validate_hashes(artifact_hashes, field="artifact_hashes")
        if phase_id == "U1":
            coverage_sha256 = self._capture_u1_source_coverage(parent)
            outputs = tuple(dict.fromkeys((*outputs, coverage_sha256)))
        if phase_id == "U3" and self.evidence_sha256 not in outputs:
            raise PhaseIntegrityError(
                "U3 output hashes must bind the validated evidence ledger"
            )
        event = self._make_event(
            phase_id=phase_id,
            event_type="phase-completed",
            output_artifact_hashes=outputs,
            status="complete",
            failure_code=None,
            invalidated_phases=(),
            parent_event_sha256=parent,
        )
        appended = self._append_event(event)
        if phase_id == "U1":
            self._u1_coverage_sha256 = coverage_sha256
        if phase_id == "U3":
            self._evidence_ledger.freeze()
        return appended

    def fail(
        self,
        phase_id: str,
        *,
        failure_code: str,
        invalidated_phases: Sequence[str] = (),
    ) -> dict[str, object]:
        self._check_phase(phase_id)
        if not isinstance(failure_code, str) or not failure_code.strip():
            raise PhaseIntegrityError("failure_code must be non-empty")
        invalidated = _validate_invalidated_phases(phase_id, invalidated_phases)
        parent = self._check_bindings(
            parent_event_sha256=None,
            input_artifact_hashes=None,
            version_binding=None,
            source_sha256=None,
            evidence_cutoff=None,
        )
        event = self._make_event(
            phase_id=phase_id,
            event_type="phase-failed",
            output_artifact_hashes=(),
            status="failed",
            failure_code=failure_code,
            invalidated_phases=invalidated,
            parent_event_sha256=parent,
        )
        return self._append_event(event)

    def replay_event(
        self,
        event: Mapping[str, object],
    ) -> dict[str, object]:
        if not isinstance(event, Mapping):
            raise PhaseIntegrityError("replayed event must be an object")
        snapshot = copy.deepcopy(dict(event))
        if frozenset(snapshot) != _EVENT_FIELDS:
            raise PhaseIntegrityError("replayed event fields do not match the closed contract")
        if snapshot.get("event_sha256") in self._event_hashes:
            raise PhaseIntegrityError("event hash replay detected")
        if snapshot.get("event_sha256") != compute_event_sha256(snapshot):
            raise PhaseIntegrityError("replayed event hash is invalid")
        phase_id = snapshot.get("phase_id")
        if not isinstance(phase_id, str):
            raise PhaseIntegrityError("replayed event phase is invalid")
        self._check_phase(phase_id)
        expected_parent = self._check_bindings(
            parent_event_sha256=(
                snapshot.get("parent_event_sha256")
                if isinstance(snapshot.get("parent_event_sha256"), str)
                else ""
            ),
            input_artifact_hashes=(
                snapshot.get("input_artifact_hashes")
                if isinstance(snapshot.get("input_artifact_hashes"), list)
                else ()
            ),
            version_binding=(
                snapshot.get("version_binding")
                if isinstance(snapshot.get("version_binding"), Mapping)
                else {}
            ),
            source_sha256=(
                snapshot.get("source_sha256")
                if isinstance(snapshot.get("source_sha256"), str)
                else ""
            ),
            evidence_cutoff=(
                snapshot.get("evidence_cutoff")
                if isinstance(snapshot.get("evidence_cutoff"), str)
                else ""
            ),
        )
        if snapshot.get("parent_event_sha256") != expected_parent:
            raise PhaseIntegrityError("replayed event parent is invalid")
        if snapshot.get("run_id") != self.run_id:
            raise PhaseIntegrityError("replayed event run_id differs")
        if snapshot.get("run_contract_sha256") != self._run_contract_sha256:
            raise PhaseIntegrityError("replayed event run contract differs")
        _parse_timestamp(snapshot.get("timestamp"), error_type=PhaseIntegrityError)
        status = snapshot.get("status")
        raw_outputs = snapshot.get("output_artifact_hashes")
        if not isinstance(raw_outputs, list):
            raise PhaseIntegrityError("replayed output hashes must be an array")
        outputs = _validate_hashes(raw_outputs, field="output_artifact_hashes")
        raw_invalidated = snapshot.get("invalidated_phases")
        if not isinstance(raw_invalidated, list):
            raise PhaseIntegrityError("replayed invalidated phases must be an array")
        if status == "complete":
            if snapshot.get("event_type") != "phase-completed" or snapshot.get(
                "failure_code"
            ) is not None:
                raise PhaseIntegrityError("completed event failure fields are inconsistent")
            if raw_invalidated:
                raise PhaseIntegrityError("completed events cannot invalidate phases")
        elif status == "failed":
            failure_code = snapshot.get("failure_code")
            if (
                snapshot.get("event_type") != "phase-failed"
                or not isinstance(failure_code, str)
                or not failure_code.strip()
            ):
                raise PhaseIntegrityError("failed event fields are inconsistent")
            if outputs:
                raise PhaseIntegrityError("failed events cannot publish output hashes")
            _validate_invalidated_phases(phase_id, raw_invalidated)
        else:
            raise PhaseIntegrityError("replayed event status is invalid")
        if phase_id == "U3" and status == "complete":
            if self.evidence_sha256 not in outputs:
                raise PhaseIntegrityError(
                    "replayed U3 output hashes must bind the validated evidence ledger"
                )
        if phase_id == "U1" and status == "complete":
            coverage_sha256 = self._capture_u1_source_coverage(expected_parent)
            if coverage_sha256 not in outputs:
                raise PhaseIntegrityError(
                    "replayed U1 does not bind the verified source coverage artifact"
                )
        appended = self._append_event(snapshot)
        if phase_id == "U1" and status == "complete":
            self._u1_coverage_sha256 = coverage_sha256
        if phase_id == "U3" and status == "complete":
            self._evidence_ledger.freeze()
        return appended

    def append_evidence(self, entry: Mapping[str, object]) -> dict[str, object]:
        return self._evidence_ledger.append(entry)

    def freeze_evidence_cutoff(self, evidence_cutoff: str) -> str:
        _parse_timestamp(evidence_cutoff, error_type=PhaseIntegrityError)
        if evidence_cutoff == self._evidence_cutoff:
            return self._evidence_cutoff
        if self.evidence_frozen:
            raise EvidenceFrozenError("evidence cutoff is frozen at U3")
        raise PhaseIntegrityError("evidence cutoff is immutable for a run")

    def fork_run(
        self, run_id: str, *, evidence_cutoff: str | None = None
    ) -> "PhaseStore":
        if not isinstance(run_id, str) or not run_id.strip():
            raise PhaseIntegrityError("fork run_id must be non-empty")
        if run_id == self.run_id:
            raise PhaseIntegrityError("fork requires a new run_id")
        next_cutoff = evidence_cutoff or self._evidence_cutoff
        contract_artifact = _thaw(self._run_contract)
        assert isinstance(contract_artifact, dict)
        contract = {
            field: copy.deepcopy(contract_artifact[field])
            for field in _RUN_CONTRACT_FIELDS
        }
        contract["evidence_cutoff"] = next_cutoff
        forked = PhaseStore(
            run_id=run_id,
            version_binding=self._version_binding,
            source_sha256=self._source_sha256,
            input_artifact_hashes=self._input_artifact_hashes,
            evidence_cutoff=next_cutoff,
            now=datetime.fromisoformat(self._timestamp.replace("Z", "+00:00")),
            run_contract=contract,
            capability_availability=self._capability_availability,
        )
        for entry in self._evidence_ledger.entries:
            forked.append_evidence(entry)
        return forked


__all__ = (
    "EvidenceFrozenError",
    "PHASE_ORDER",
    "PHASE_EVENT_SCHEMA_ID",
    "PhaseIntegrityError",
    "PhaseStore",
    "PhaseTransitionError",
    "RunBlockedError",
    "RunContractError",
    "compute_event_sha256",
    "validate_run_contract",
)
