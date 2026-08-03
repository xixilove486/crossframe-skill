from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
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
from .evidence import EvidenceArtifactSeal, EvidenceFrozenError, EvidenceLedger
from .paths import (
    PRODUCTION_ROOT,
    RunLayout,
    RunMode,
    RootPolicy,
    assert_safe_descendant,
    build_run_layout,
)
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


@dataclass(frozen=True, init=False)
class RetrievalBoundary:
    run_id: str
    version_binding: dict[str, object]
    u1_parent_event_sha256: str
    request_sha256: str
    run_contract_sha256: str
    network_available: bool
    outbound_permission: str
    sensitivity: str
    acl_status: str
    run_mode: str
    input_snapshot_sha256: str
    input_artifact_hashes: tuple[str, ...]
    inputs: tuple[dict[str, str], ...]
    input_root: Path
    maximum_tool_retries: int
    maximum_retrieval_rounds_without_material_novelty: int
    expected_eligibility_basis_sha256: str | None
    _issuer_token: str
    _seal_sha256: str


@dataclass(frozen=True, init=False)
class _U0AuthoritySeal:
    run_id: str
    run_contract_sha256: str
    capability_availability: dict[str, str]
    expected_eligibility_basis_sha256: str | None
    _issuer_token: str
    _seal_sha256: str


_ISSUED_U0_AUTHORITIES: dict[str, str] = {}
_ISSUED_RETRIEVAL_BOUNDARIES: dict[str, str] = {}


def _issue_snapshot(registry: dict[str, str], fields: Mapping[str, object]) -> tuple[str, str]:
    token = hashlib.sha256(os.urandom(32)).hexdigest()
    seal_sha256 = hashlib.sha256(_canonical_json(fields)).hexdigest()
    registry[token] = seal_sha256
    return token, seal_sha256


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
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PhaseIntegrityError(f"event is not canonical JSON: {error}") from error


def _u0_authority_fields(seal: _U0AuthoritySeal) -> dict[str, object]:
    return {
        "run_id": seal.run_id,
        "run_contract_sha256": seal.run_contract_sha256,
        "capability_availability": copy.deepcopy(seal.capability_availability),
        "expected_eligibility_basis_sha256": seal.expected_eligibility_basis_sha256,
    }


def _make_u0_authority(
    *,
    run_id: str,
    run_contract_sha256: str,
    availability: Mapping[str, str],
    expected_eligibility_basis_sha256: str | None,
) -> _U0AuthoritySeal:
    seal = object.__new__(_U0AuthoritySeal)
    object.__setattr__(seal, "run_id", run_id)
    object.__setattr__(seal, "run_contract_sha256", run_contract_sha256)
    object.__setattr__(seal, "capability_availability", copy.deepcopy(dict(availability)))
    object.__setattr__(
        seal,
        "expected_eligibility_basis_sha256",
        expected_eligibility_basis_sha256,
    )
    token, seal_sha256 = _issue_snapshot(_ISSUED_U0_AUTHORITIES, _u0_authority_fields(seal))
    object.__setattr__(seal, "_issuer_token", token)
    object.__setattr__(seal, "_seal_sha256", seal_sha256)
    return seal


def _verify_u0_authority(seal: object) -> _U0AuthoritySeal:
    if not isinstance(seal, _U0AuthoritySeal):
        raise PhaseIntegrityError("U0 capability authority is not issuer-produced")
    fields = _u0_authority_fields(seal)
    issued = _ISSUED_U0_AUTHORITIES.get(getattr(seal, "_issuer_token", ""))
    computed = hashlib.sha256(_canonical_json(fields)).hexdigest()
    if issued is None or seal._seal_sha256 != issued or issued != computed:
        raise PhaseIntegrityError("U0 capability authority integrity is invalid")
    return seal


def _retrieval_boundary_fields(boundary: RetrievalBoundary) -> dict[str, object]:
    return {
        "run_id": boundary.run_id,
        "version_binding": copy.deepcopy(boundary.version_binding),
        "u1_parent_event_sha256": boundary.u1_parent_event_sha256,
        "request_sha256": boundary.request_sha256,
        "run_contract_sha256": boundary.run_contract_sha256,
        "network_available": boundary.network_available,
        "outbound_permission": boundary.outbound_permission,
        "sensitivity": boundary.sensitivity,
        "acl_status": boundary.acl_status,
        "run_mode": boundary.run_mode,
        "input_snapshot_sha256": boundary.input_snapshot_sha256,
        "input_artifact_hashes": list(boundary.input_artifact_hashes),
        "inputs": list(boundary.inputs),
        "input_root": str(boundary.input_root.resolve()),
        "maximum_tool_retries": boundary.maximum_tool_retries,
        "maximum_retrieval_rounds_without_material_novelty": (
            boundary.maximum_retrieval_rounds_without_material_novelty
        ),
        "expected_eligibility_basis_sha256": (
            boundary.expected_eligibility_basis_sha256
        ),
    }


def verify_retrieval_boundary(boundary: object) -> RetrievalBoundary:
    if not isinstance(boundary, RetrievalBoundary):
        raise PhaseIntegrityError("retrieval boundary is not issuer-produced")
    fields = _retrieval_boundary_fields(boundary)
    issued = _ISSUED_RETRIEVAL_BOUNDARIES.get(
        getattr(boundary, "_issuer_token", "")
    )
    computed = hashlib.sha256(_canonical_json(fields)).hexdigest()
    if issued is None or boundary._seal_sha256 != issued or issued != computed:
        raise PhaseIntegrityError("retrieval boundary issuer integrity is invalid")
    return boundary


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


def _validated_capability_availability(
    value: Mapping[str, str] | None,
) -> dict[str, str]:
    if value is not None and not isinstance(value, Mapping):
        raise RunContractError("capability availability must be an object")
    availability = copy.deepcopy(dict(value or {}))
    if any(name not in _CAPABILITY_NAMES for name in availability):
        raise RunContractError("capability availability contains an unknown capability")
    for name, state in availability.items():
        if state not in _CAPABILITY_STATES:
            raise RunContractError(f"invalid availability for {name}: {state!r}")
    return availability


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
    if not 1 <= limits["maximum_branches"] <= 64:
        raise RunContractError("maximum_branches must be between one and 64")
    if not 0 <= limits["maximum_retrieval_rounds_without_material_novelty"] <= 2:
        raise RunContractError("retrieval novelty limit must be between zero and two")
    if not 1 <= limits["maximum_tool_retries"] <= 3:
        raise RunContractError("maximum_tool_retries must be between one and three")
    if not 0 <= limits["maximum_repair_attempts"] <= 3:
        raise RunContractError("maximum_repair_attempts must be between zero and three")
    contract["resource_limits"] = limits

    availability = _validated_capability_availability(capability_availability)
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


def _validate_run_layout_authority(
    run_layout: object,
    *,
    run_id: str,
    run_mode: str,
) -> RunLayout:
    if not isinstance(run_layout, RunLayout):
        raise PhaseIntegrityError("run requires a validated RunLayout authority")
    try:
        mode = RunMode(run_mode)
        policy = (
            RootPolicy(run_layout.root, run_layout.root.parent / "test-control")
            if mode is RunMode.PRODUCTION
            else RootPolicy(PRODUCTION_ROOT, run_layout.root)
        )
        expected = build_run_layout(mode, run_id, policy)
        assert_safe_descendant(
            expected.run_dir.resolve(strict=False),
            expected.input_dir.resolve(strict=False),
        )
    except (OSError, TypeError, ValueError) as error:
        raise PhaseIntegrityError("run layout authority is invalid") from error
    if mode is RunMode.PRODUCTION and run_layout.root != PRODUCTION_ROOT:
        raise PhaseIntegrityError("production run layout must use the fixed root")
    if run_layout != expected:
        raise PhaseIntegrityError("run layout differs from the canonical run authority")
    return copy.deepcopy(expected)


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
        input_snapshot_sha256: str | None = None,
        evidence_cutoff: str,
        now: datetime,
        run_contract: Mapping[str, object],
        capability_availability: Mapping[str, str] | None = None,
        source_repository: Path | None = None,
        u1_prerequisite_measurement: object | None = None,
        run_layout: RunLayout,
        expected_eligibility_basis_sha256: str | None = None,
    ) -> None:
        if not isinstance(run_id, str) or not run_id.strip():
            raise PhaseIntegrityError("run_id must be non-empty")
        if not _is_sha256(source_sha256):
            raise PhaseIntegrityError("source_sha256 must be a lowercase SHA-256")
        _parse_timestamp(evidence_cutoff, error_type=PhaseIntegrityError)
        timestamp = _format_timestamp(now)
        binding = _validate_version_binding(version_binding)
        availability = _validated_capability_availability(capability_availability)
        contract = validate_run_contract(
            run_contract,
            capability_availability=availability,
        )
        if contract["evidence_cutoff"] != evidence_cutoff:
            raise RunContractError("run contract evidence cutoff differs from the run")
        accepted_layout = _validate_run_layout_authority(
            run_layout,
            run_id=run_id,
            run_mode=str(contract["run_mode"]),
        )
        if (
            expected_eligibility_basis_sha256 is not None
            and not _is_sha256(expected_eligibility_basis_sha256)
        ):
            raise PhaseIntegrityError(
                "expected eligibility basis authority must be a lowercase SHA-256"
            )
        authority_repository = (source_repository or _SOURCE_REPOSITORY).resolve()
        if contract["run_mode"] == "production" and authority_repository != _SOURCE_REPOSITORY:
            raise PhaseIntegrityError("source authority repository must use the fixed runtime root")
        if not authority_repository.is_dir():
            raise PhaseIntegrityError("source authority repository is unavailable")

        verified_measurement = None
        prerequisite_roles: dict[str, object] | None = None
        if u1_prerequisite_measurement is not None:
            from .source_integrity import verify_u1_prerequisites

            try:
                verified_measurement = verify_u1_prerequisites(
                    u1_prerequisite_measurement
                )
            except Exception as error:
                raise PhaseIntegrityError("U1 prerequisite authority is invalid") from error
            if (
                verified_measurement.run_mode != contract["run_mode"]
                or verified_measurement._repo != authority_repository
                or verified_measurement.source_manifest_sha256 != source_sha256
            ):
                raise PhaseIntegrityError(
                    "U1 prerequisite mode, root, or source differs from the run"
                )
            prerequisite_roles = {
                "run_mode": verified_measurement.run_mode,
                "source_release_id": verified_measurement.source_release_id,
                "source_manifest_sha256": verified_measurement.source_manifest_sha256,
                "release_manifest_sha256": verified_measurement.release_manifest_sha256,
                "compatibility_matrix_sha256": verified_measurement.compatibility_matrix_sha256,
                "knowledge_report_sha256": verified_measurement.knowledge_report_sha256,
                "skill_tree_sha256": verified_measurement.skill_tree_sha256,
                "free_space_reserve_bytes": verified_measurement.free_space_reserve_bytes,
                "free_space_status": verified_measurement.free_space_status,
            }

        self.run_id = run_id
        self._version_binding = binding
        self._source_sha256 = source_sha256
        self._input_artifact_hashes = _validate_hashes(
            input_artifact_hashes, field="input_artifact_hashes"
        )
        self._input_snapshot_sha256 = input_snapshot_sha256
        if input_snapshot_sha256 is not None and not _is_sha256(input_snapshot_sha256):
            raise PhaseIntegrityError("input_snapshot_sha256 must be a lowercase SHA-256")
        self._evidence_cutoff = evidence_cutoff
        self._timestamp = timestamp
        contract_artifact = _make_run_contract_artifact(
            contract,
            run_id=run_id,
            version_binding=binding,
            generated_at=timestamp,
        )
        self._run_contract = _freeze(contract_artifact)
        self._run_contract_sha256 = hashlib.sha256(_canonical_json(contract_artifact)).hexdigest()
        self._u0_authority = _make_u0_authority(
            run_id=run_id,
            run_contract_sha256=self._run_contract_sha256,
            availability=availability,
            expected_eligibility_basis_sha256=(
                expected_eligibility_basis_sha256
            ),
        )
        self._capability_availability = _freeze(availability)
        self._source_repository = authority_repository
        self._run_layout = accepted_layout
        self._run_input_root = accepted_layout.input_dir.resolve(strict=False)
        self._u1_prerequisite_measurement = copy.deepcopy(verified_measurement)
        self._u1_prerequisite_roles = _freeze(prerequisite_roles) if prerequisite_roles else None
        self._events: list[dict[str, object]] = []
        self._event_hashes: set[str] = set()
        self._completed: list[str] = []
        self._evidence_ledger = EvidenceLedger(
            run_id,
            evidence_cutoff,
            version_binding=binding,
            generated_at=timestamp,
        )
        self._u1_coverage_sha256: str | None = None
        self._u1_authority: object | None = None
        self._u1_snapshot: object | None = None
        self._terminal = False
        self._retrieval_material_hashes: set[str] = set()
        self._retrieval_rounds = 0
        self._retrieval_no_novelty_rounds = 0
        self._retrieval_needs_attention = False

    @property
    def run_contract(self) -> Mapping[str, object]:
        result = _thaw(self._run_contract)
        assert isinstance(result, dict)
        return result

    @property
    def run_contract_artifact_sha256(self) -> str:
        return self._run_contract_sha256

    @property
    def run_input_root(self) -> Path:
        return self._run_input_root

    @property
    def evidence_cutoff(self) -> str:
        return self._evidence_cutoff

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
        return self._evidence_ledger.artifact_sha256

    @property
    def evidence_artifact(self) -> dict[str, object]:
        return self._evidence_ledger.artifact

    @property
    def evidence_unknowns(self) -> tuple[dict[str, str], ...]:
        return self._evidence_ledger.unknowns

    @property
    def terminal(self) -> bool:
        return self._terminal

    def _accepted_u1_snapshot(self) -> dict[str, object]:
        if self._u1_authority is None or self._u1_snapshot is None:
            raise PhaseIntegrityError("U1 authority has not been accepted")
        from .source_integrity import verify_u1_authority_seal

        try:
            verified = verify_u1_authority_seal(self._u1_authority)
        except Exception as error:
            raise PhaseIntegrityError("stored U1 authority integrity is invalid") from error
        current = {
            "run_id": verified.run_id,
            "version_binding": copy.deepcopy(verified.version_binding),
            "parent_event_sha256": verified.parent_event_sha256,
            "evidence_cutoff": verified.evidence_cutoff,
            "run_mode": verified.run_mode,
            "source_release_id": verified.source_release_id,
            "source_manifest_sha256": verified.source_manifest_sha256,
            "release_manifest_sha256": verified.release_manifest_sha256,
            "compatibility_matrix_sha256": verified.compatibility_matrix_sha256,
            "knowledge_report_sha256": verified.knowledge_report_sha256,
            "skill_tree_sha256": verified.skill_tree_sha256,
            "free_space_reserve_bytes": verified.free_space_reserve_bytes,
            "free_space_status": verified.free_space_status,
            "input_snapshot_sha256": verified.input_snapshot_sha256,
            "input_artifact_hashes": list(verified.input_artifact_hashes),
            "inputs": copy.deepcopy(list(verified.inputs)),
            "input_root": verified.input_root,
            "acl_status": verified.acl_status,
            "source_lock_artifact_sha256": verified.source_lock_artifact_sha256,
            "read_coverage_artifact_sha256": verified.read_coverage_artifact_sha256,
            "authorizes_phase": verified.authorizes_phase,
        }
        snapshot = _thaw(self._u1_snapshot)
        if not isinstance(snapshot, dict) or snapshot != current:
            raise PhaseIntegrityError("stored U1 authority snapshot differs from its seal")
        return snapshot

    @property
    def u1_acl_status(self) -> str:
        return str(self._accepted_u1_snapshot()["acl_status"])

    @property
    def retrieval_boundary(self) -> RetrievalBoundary:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        if self.current_phase != "U1" or self._u1_authority is None:
            raise PhaseIntegrityError("retrieval boundary requires completed sealed U1")
        u1 = self._accepted_u1_snapshot()
        u0 = _verify_u0_authority(self._u0_authority)
        if (
            u0.run_id != self.run_id
            or u0.run_contract_sha256 != self._run_contract_sha256
        ):
            raise PhaseIntegrityError("U0 capability authority differs from the run")
        contract = self.run_contract
        if (
            Path(u1["input_root"]).resolve(strict=False) != self._run_input_root
            or str(contract["request_sha256"])
            not in tuple(str(value) for value in u1["input_artifact_hashes"])
        ):
            raise PhaseIntegrityError(
                "retrieval request or input root differs from sealed U1 authority"
            )
        boundary = object.__new__(RetrievalBoundary)
        object.__setattr__(boundary, "run_id", self.run_id)
        object.__setattr__(boundary, "version_binding", copy.deepcopy(self._version_binding))
        object.__setattr__(boundary, "u1_parent_event_sha256", str(self._events[-1]["event_sha256"]))
        object.__setattr__(boundary, "request_sha256", str(contract["request_sha256"]))
        object.__setattr__(boundary, "run_contract_sha256", self._run_contract_sha256)
        object.__setattr__(
            boundary,
            "network_available",
            u0.capability_availability.get("network") == "available",
        )
        object.__setattr__(boundary, "outbound_permission", str(contract["outbound_permission"]))
        object.__setattr__(boundary, "sensitivity", str(contract["sensitivity"]))
        object.__setattr__(boundary, "acl_status", str(u1["acl_status"]))
        object.__setattr__(boundary, "run_mode", str(contract["run_mode"]))
        object.__setattr__(
            boundary, "input_snapshot_sha256", str(u1["input_snapshot_sha256"])
        )
        object.__setattr__(
            boundary,
            "input_artifact_hashes",
            tuple(str(value) for value in u1["input_artifact_hashes"]),
        )
        object.__setattr__(
            boundary,
            "inputs",
            tuple(copy.deepcopy(u1["inputs"])),
        )
        object.__setattr__(boundary, "input_root", Path(u1["input_root"]).resolve())
        object.__setattr__(
            boundary,
            "maximum_tool_retries",
            int(contract["resource_limits"]["maximum_tool_retries"]),
        )
        object.__setattr__(
            boundary,
            "maximum_retrieval_rounds_without_material_novelty",
            int(
                contract["resource_limits"][
                    "maximum_retrieval_rounds_without_material_novelty"
                ]
            ),
        )
        object.__setattr__(
            boundary,
            "expected_eligibility_basis_sha256",
            u0.expected_eligibility_basis_sha256,
        )
        token, seal_sha256 = _issue_snapshot(
            _ISSUED_RETRIEVAL_BOUNDARIES, _retrieval_boundary_fields(boundary)
        )
        object.__setattr__(boundary, "_issuer_token", token)
        object.__setattr__(boundary, "_seal_sha256", seal_sha256)
        return boundary

    def retrieval_round_available(self) -> bool:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        self.retrieval_boundary
        return not self._retrieval_needs_attention

    def record_retrieval_round(self, material_sha256: str) -> dict[str, object]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        boundary = self.retrieval_boundary
        if self._retrieval_needs_attention:
            raise PhaseIntegrityError("retrieval material novelty limit is exhausted")
        if not _is_sha256(material_sha256):
            raise PhaseIntegrityError("retrieval material hash is invalid")
        novel = material_sha256 not in self._retrieval_material_hashes
        self._retrieval_rounds += 1
        if novel:
            self._retrieval_material_hashes.add(material_sha256)
            self._retrieval_no_novelty_rounds = 0
        else:
            self._retrieval_no_novelty_rounds += 1
        limit = boundary.maximum_retrieval_rounds_without_material_novelty
        if not novel and self._retrieval_no_novelty_rounds >= limit:
            self._retrieval_needs_attention = True
        return {
            "rounds": self._retrieval_rounds,
            "material_novelty": novel,
            "needs_attention": self._retrieval_needs_attention,
        }

    @property
    def retrieval_saturation(self) -> dict[str, object]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        self.retrieval_boundary
        return {
            "rounds": self._retrieval_rounds,
            "stop_reason": (
                "material-novelty-exhausted"
                if self._retrieval_needs_attention
                else "bounded-result-recorded"
                if self._retrieval_rounds
                else "not-started"
            ),
        }

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
        try:
            validate_instance("ultra-phase-event.schema.json", snapshot)
        except ValidationError as error:
            raise PhaseIntegrityError(
                f"phase event violates public schema: {error.message}"
            ) from error
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
        u1_authority: object | None = None,
        retrieval_authority: object | None = None,
        evidence_authority: EvidenceArtifactSeal | None = None,
    ) -> dict[str, object]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        self._check_phase(phase_id)
        parent = self._check_bindings(
            parent_event_sha256=parent_event_sha256,
            input_artifact_hashes=input_artifact_hashes,
            version_binding=version_binding,
            source_sha256=source_sha256,
            evidence_cutoff=evidence_cutoff,
        )
        outputs = _validate_hashes(artifact_hashes, field="artifact_hashes")
        if phase_id == "U0":
            u0 = _verify_u0_authority(self._u0_authority)
            if (
                outputs != (self._run_contract_sha256,)
                or u0.run_id != self.run_id
                or u0.run_contract_sha256 != self._run_contract_sha256
            ):
                raise PhaseIntegrityError("U0 must bind the sealed run contract authority")
        if phase_id == "U1":
            from .source_integrity import (
                SourceLockError,
                U1AuthoritySeal,
                verify_u1_authority_seal,
            )

            if not isinstance(u1_authority, U1AuthoritySeal):
                raise PhaseIntegrityError("U1 requires issuer-produced source authority")
            try:
                verified_u1 = verify_u1_authority_seal(u1_authority)
            except SourceLockError as error:
                raise PhaseIntegrityError("U1 authority issuer integrity is invalid") from error
            if self._u1_prerequisite_roles is None:
                raise PhaseIntegrityError("U1 prerequisite authority was not sealed at U0")
            prerequisite_roles = _thaw(self._u1_prerequisite_roles)
            assert isinstance(prerequisite_roles, dict)
            expected = {
                "run_id": self.run_id,
                "version_binding": self._version_binding,
                "parent_event_sha256": parent,
                "evidence_cutoff": self._evidence_cutoff,
                "source_manifest_sha256": self._source_sha256,
                "input_artifact_hashes": self._input_artifact_hashes,
                "input_root": self._run_input_root,
            }
            if any(getattr(verified_u1, field, None) != value for field, value in expected.items()):
                raise PhaseIntegrityError("U1 authority source, input, cutoff, or root differs")
            if any(
                getattr(verified_u1, field, None) != value
                for field, value in prerequisite_roles.items()
            ):
                raise PhaseIntegrityError("U1 prerequisite roles differ from the sealed measurement")
            if (
                self._input_snapshot_sha256 is None
                or verified_u1.input_snapshot_sha256 != self._input_snapshot_sha256
                or not verified_u1.authorizes_phase
                or self.run_contract["request_sha256"]
                not in verified_u1.input_artifact_hashes
            ):
                raise PhaseIntegrityError("U1 request or input snapshot authority differs")
            expected_outputs = (
                verified_u1.source_lock_artifact_sha256,
                verified_u1.read_coverage_artifact_sha256,
            )
            if outputs != expected_outputs:
                raise PhaseIntegrityError("U1 output hashes differ from sealed authority")
            accepted_u1 = {
                "run_id": verified_u1.run_id,
                "version_binding": copy.deepcopy(verified_u1.version_binding),
                "parent_event_sha256": verified_u1.parent_event_sha256,
                "evidence_cutoff": verified_u1.evidence_cutoff,
                "run_mode": verified_u1.run_mode,
                "source_release_id": verified_u1.source_release_id,
                "source_manifest_sha256": verified_u1.source_manifest_sha256,
                "release_manifest_sha256": verified_u1.release_manifest_sha256,
                "compatibility_matrix_sha256": verified_u1.compatibility_matrix_sha256,
                "knowledge_report_sha256": verified_u1.knowledge_report_sha256,
                "skill_tree_sha256": verified_u1.skill_tree_sha256,
                "free_space_reserve_bytes": verified_u1.free_space_reserve_bytes,
                "free_space_status": verified_u1.free_space_status,
                "input_snapshot_sha256": verified_u1.input_snapshot_sha256,
                "input_artifact_hashes": list(verified_u1.input_artifact_hashes),
                "inputs": copy.deepcopy(list(verified_u1.inputs)),
                "input_root": verified_u1.input_root,
                "acl_status": verified_u1.acl_status,
                "source_lock_artifact_sha256": verified_u1.source_lock_artifact_sha256,
                "read_coverage_artifact_sha256": verified_u1.read_coverage_artifact_sha256,
                "authorizes_phase": verified_u1.authorizes_phase,
            }
        elif phase_id == "U2":
            from .retrieval import (
                RetrievalLedgerSeal,
                RetrievalPolicyError,
                verify_retrieval_ledger_seal,
            )

            if not isinstance(retrieval_authority, RetrievalLedgerSeal):
                raise PhaseIntegrityError("U2 requires issuer-produced retrieval authority")
            try:
                verified_retrieval = verify_retrieval_ledger_seal(
                    retrieval_authority
                )
            except RetrievalPolicyError as error:
                raise PhaseIntegrityError(
                    "U2 retrieval authority issuer integrity is invalid"
                ) from error
            if (
                verified_retrieval.run_id != self.run_id
                or verified_retrieval.version_binding != self._version_binding
                or verified_retrieval.u1_parent_event_sha256 != parent
                or verified_retrieval.request_sha256 != self.run_contract["request_sha256"]
                or outputs != (verified_retrieval.artifact_sha256,)
                or not verified_retrieval.completion_authorized
                or verified_retrieval.retrieval_status
                not in {"not-applicable", "required-complete"}
            ):
                raise PhaseIntegrityError(
                    "U2 retrieval authority or completion disposition differs"
                )
        elif phase_id == "U3":
            from .evidence import EvidenceValidationError, validate_evidence_artifact

            if not isinstance(evidence_authority, EvidenceArtifactSeal):
                raise PhaseIntegrityError("U3 requires issuer-produced evidence authority")
            internal_artifact = self._evidence_ledger.artifact
            try:
                internal_seal = validate_evidence_artifact(
                    internal_artifact,
                    expected_run_id=self.run_id,
                    expected_version_binding=self._version_binding,
                    expected_phase_id="U3",
                    expected_evidence_cutoff=self._evidence_cutoff,
                )
            except EvidenceValidationError as error:
                raise PhaseIntegrityError("U3 internal evidence ledger is invalid") from error
            if (
                evidence_authority.run_id != self.run_id
                or evidence_authority.version_binding != self._version_binding
                or evidence_authority.phase_id != "U3"
                or evidence_authority.evidence_cutoff != self._evidence_cutoff
                or evidence_authority.content_sha256 != internal_seal.content_sha256
                or evidence_authority.artifact_sha256 != internal_seal.artifact_sha256
                or outputs != (evidence_authority.artifact_sha256,)
            ):
                raise PhaseIntegrityError("U3 evidence authority differs from the run boundary")
            try:
                self._evidence_ledger.freeze()
            except EvidenceValidationError as error:
                raise PhaseIntegrityError("U3 evidence ledger cannot be frozen") from error
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
            self._u1_coverage_sha256 = verified_u1.read_coverage_artifact_sha256
            self._u1_authority = copy.deepcopy(verified_u1)
            self._u1_snapshot = _freeze(accepted_u1)
        return appended

    def fail(
        self,
        phase_id: str,
        *,
        failure_code: str,
        invalidated_phases: Sequence[str] = (),
    ) -> dict[str, object]:
        return self._terminate(
            phase_id,
            status="failed",
            failure_code=failure_code,
            invalidated_phases=invalidated_phases,
        )

    def blocked(self, phase_id: str, *, failure_code: str) -> dict[str, object]:
        return self._terminate(phase_id, status="blocked", failure_code=failure_code)

    def cancelled(self, phase_id: str, *, failure_code: str) -> dict[str, object]:
        return self._terminate(phase_id, status="cancelled", failure_code=failure_code)

    def _terminate(
        self,
        phase_id: str,
        *,
        status: str,
        failure_code: str,
        invalidated_phases: Sequence[str] = (),
    ) -> dict[str, object]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
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
            event_type=f"phase-{status}",
            output_artifact_hashes=(),
            status=status,
            failure_code=failure_code,
            invalidated_phases=invalidated,
            parent_event_sha256=parent,
        )
        appended = self._append_event(event)
        self._terminal = True
        return appended

    def replay_event(
        self,
        event: Mapping[str, object],
    ) -> dict[str, object]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
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
        elif status in {"failed", "blocked", "cancelled"}:
            failure_code = snapshot.get("failure_code")
            if (
                snapshot.get("event_type") != f"phase-{status}"
                or not isinstance(failure_code, str)
                or not failure_code.strip()
            ):
                raise PhaseIntegrityError("terminal event fields are inconsistent")
            if outputs:
                raise PhaseIntegrityError("terminal events cannot publish output hashes")
            _validate_invalidated_phases(phase_id, raw_invalidated)
        else:
            raise PhaseIntegrityError("replayed event status is invalid")
        if phase_id != "U0" and status == "complete":
            raise PhaseIntegrityError(
                "replayed U1-U3 completion requires external sealed authority"
            )
        if phase_id == "U0" and status == "complete" and outputs != (self._run_contract_sha256,):
            raise PhaseIntegrityError("replayed U0 does not bind the run contract")
        appended = self._append_event(snapshot)
        if status in {"failed", "blocked", "cancelled"}:
            self._terminal = True
        return appended

    def append_evidence(self, entry: Mapping[str, object]) -> dict[str, object]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        if self.evidence_frozen:
            raise EvidenceFrozenError("evidence is frozen at completed U3")
        if self.current_phase != "U2":
            raise PhaseTransitionError("U3 evidence can only be formed after completed U2")
        return self._evidence_ledger.append(entry)

    def append_unknown(self, unknown: Mapping[str, object]) -> dict[str, str]:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        if self.evidence_frozen:
            raise EvidenceFrozenError("evidence is frozen at completed U3")
        if self.current_phase != "U2":
            raise PhaseTransitionError("U3 unknowns can only be formed after completed U2")
        return self._evidence_ledger.append_unknown(unknown)

    def freeze_evidence(self) -> EvidenceArtifactSeal:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        if self.evidence_frozen:
            raise EvidenceFrozenError("evidence is frozen at completed U3")
        if self.current_phase != "U2":
            raise PhaseTransitionError("U3 evidence can only be frozen after completed U2")
        return self._evidence_ledger.seal()

    def freeze_evidence_cutoff(self, evidence_cutoff: str) -> str:
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        if self.evidence_frozen:
            raise EvidenceFrozenError("evidence cutoff is frozen at completed U3")
        if self.current_phase != "U2":
            raise PhaseTransitionError("evidence cutoff can only be frozen after completed U2")
        _parse_timestamp(evidence_cutoff, error_type=PhaseIntegrityError)
        if evidence_cutoff == self._evidence_cutoff:
            return self._evidence_cutoff
        raise PhaseIntegrityError("evidence cutoff is immutable for a run")

    def fork_run(
        self, run_id: str, *, evidence_cutoff: str | None = None
    ) -> "PhaseStore":
        if self._terminal:
            raise PhaseTransitionError("run is terminal")
        if self.current_phase != "U3" or not self.evidence_frozen:
            raise PhaseIntegrityError("fork requires a successfully frozen U3")
        if not isinstance(run_id, str) or not run_id.strip():
            raise PhaseIntegrityError("fork run_id must be non-empty")
        if run_id == self.run_id:
            raise PhaseIntegrityError("fork requires a new run_id")
        next_cutoff = evidence_cutoff or self._evidence_cutoff
        if _parse_timestamp(next_cutoff, error_type=PhaseIntegrityError) <= _parse_timestamp(
            self._evidence_cutoff, error_type=PhaseIntegrityError
        ):
            raise PhaseIntegrityError("fork requires a strictly later evidence cutoff")
        contract_artifact = _thaw(self._run_contract)
        assert isinstance(contract_artifact, dict)
        contract = {
            field: copy.deepcopy(contract_artifact[field])
            for field in _RUN_CONTRACT_FIELDS
        }
        contract["evidence_cutoff"] = next_cutoff
        mode = RunMode(str(contract["run_mode"]))
        policy = (
            RootPolicy(self._run_layout.root, self._run_layout.root.parent / "test-control")
            if mode is RunMode.PRODUCTION
            else RootPolicy(PRODUCTION_ROOT, self._run_layout.root)
        )
        forked_layout = build_run_layout(mode, run_id, policy)
        forked = PhaseStore(
            run_id=run_id,
            version_binding=self._version_binding,
            source_sha256=self._source_sha256,
            input_artifact_hashes=self._input_artifact_hashes,
            input_snapshot_sha256=self._input_snapshot_sha256,
            evidence_cutoff=next_cutoff,
            now=datetime.fromisoformat(self._timestamp.replace("Z", "+00:00")),
            run_contract=contract,
            capability_availability=_thaw(self._capability_availability),
            source_repository=self._source_repository,
            u1_prerequisite_measurement=self._u1_prerequisite_measurement,
            run_layout=forked_layout,
        )
        for entry in self._evidence_ledger.entries:
            forked._evidence_ledger.append(entry)
        for unknown in self._evidence_ledger.unknowns:
            forked._evidence_ledger.append_unknown(unknown)
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
    "RetrievalBoundary",
    "compute_event_sha256",
    "validate_run_contract",
    "verify_retrieval_boundary",
)
