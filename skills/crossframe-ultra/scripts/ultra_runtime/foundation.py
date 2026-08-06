from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .constants import current_version_binding
from .host_handshake import (
    HostActionSeal,
    HostResultSeal,
    _seal_action,
    _seal_result,
    issue_host_action,
    load_pending_action,
)
from .jsonio import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object_bytes,
    sha256_bytes,
)
from .paths import PRODUCTION_ROOT, RunLayout, _require_utc, assert_safe_descendant
from .schemas import compute_artifact_content_sha256, validate_instance
from .status import RunStatusStore


INPUT_INVENTORY_FILENAME = "material-inventory.json"
CAPABILITY_ACTION_FILENAME = "u0-capability-action.json"
CAPABILITY_ATTESTATION_RELATIVE_PATH = Path(
    "U00-U03-evidence/U00-host-capability-attestation.json"
)
U2_RETRIEVAL_LEDGER_RELATIVE_PATH = Path(
    "U00-U03-evidence/U02-retrieval-ledger.json"
)
U3_EVIDENCE_RELATIVE_PATH = Path(
    "U00-U03-evidence/U03-evidence-ledger.json"
)
_SAFE_EXTENSION_RE = re.compile(r"[a-z0-9]{1,10}")


class FoundationInputError(ValueError):
    """The immutable request cannot authorize a fresh U0 foundation."""


@dataclass(frozen=True, slots=True)
class RequestProfile:
    analysis_kind: str
    claim: str
    material_inventory: tuple[dict[str, str], ...]
    material_universe_sha256: str | None


@dataclass(frozen=True, slots=True)
class FoundationProgress:
    outcome: str
    phase_store: object | None
    pending_action: HostActionSeal | None
    completed_phase: str | None


@dataclass(frozen=True, slots=True, init=False)
class HostCapabilitySeal:
    _artifact_bytes: bytes
    artifact_sha256: str

    @property
    def artifact_bytes(self) -> bytes:
        return bytes(self._artifact_bytes)

    @property
    def document(self) -> dict[str, object]:
        return load_json_object_bytes(
            self._artifact_bytes,
            source="validated host capability attestation",
        )

    @property
    def measured_availability(self) -> dict[str, str]:
        value = self.document["measured_availability"]
        assert isinstance(value, dict)
        return copy.deepcopy(value)


def _canonical_utc(value: datetime) -> str:
    _require_utc(value, "now")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _material_universe_sha256(
    materials: Sequence[Mapping[str, str]],
) -> str | None:
    snapshot = tuple(copy.deepcopy(dict(item)) for item in materials)
    return sha256_bytes(canonical_json_bytes(snapshot)) if snapshot else None


def validate_host_capability_attestation(
    value: Mapping[str, object],
    *,
    expected_run_id: str | None = None,
    expected_request_sha256: str | None = None,
    expected_version_binding: Mapping[str, object] | None = None,
) -> HostCapabilitySeal:
    if not isinstance(value, Mapping):
        raise FoundationInputError("host capability attestation must be an object")
    document = copy.deepcopy(dict(value))
    try:
        validate_instance(
            "ultra-host-capability-attestation.schema.json",
            document,
        )
    except Exception as error:
        raise FoundationInputError("host capability attestation is invalid") from error
    if document.get("content_sha256") != compute_artifact_content_sha256(document):
        raise FoundationInputError("host capability attestation content hash differs")
    expected = {
        "run_id": expected_run_id,
        "request_sha256": expected_request_sha256,
        "version_binding": (
            copy.deepcopy(dict(expected_version_binding))
            if expected_version_binding is not None
            else None
        ),
    }
    if any(
        wanted is not None and document.get(field) != wanted
        for field, wanted in expected.items()
    ):
        raise FoundationInputError("host capability attestation binding differs")
    providers = document.get("providers")
    tools = document.get("tools")
    assert isinstance(providers, list) and isinstance(tools, list)
    provider_ids = {
        str(provider["provider_id"])
        for provider in providers
        if isinstance(provider, Mapping)
    }
    if any(
        not isinstance(tool, Mapping)
        or str(tool.get("provider_id")) not in provider_ids
        for tool in tools
    ):
        raise FoundationInputError(
            "host capability attestation tool provider identity is unknown"
        )
    artifact_bytes = canonical_json_bytes(document)
    seal = object.__new__(HostCapabilitySeal)
    object.__setattr__(seal, "_artifact_bytes", artifact_bytes)
    object.__setattr__(seal, "artifact_sha256", sha256_bytes(artifact_bytes))
    return seal


def verify_host_capability_seal(value: object) -> HostCapabilitySeal:
    if not isinstance(value, HostCapabilitySeal):
        raise FoundationInputError("capability attestation is not a validated seal")
    verified = validate_host_capability_attestation(value.document)
    if verified.artifact_sha256 != value.artifact_sha256:
        raise FoundationInputError("capability attestation seal hash differs")
    return value


def validate_closed_input_profile(
    candidate: Mapping[str, object],
    *,
    request_bytes: bytes,
) -> RequestProfile:
    if set(candidate) != {"analysis_kind", "claim", "material"}:
        raise FoundationInputError(
            "closed-input request must contain exactly analysis_kind, claim, and material"
        )
    if request_bytes != canonical_json_bytes(dict(candidate)):
        raise FoundationInputError("closed-input request bytes must be canonical JSON")
    claim = candidate.get("claim")
    material = candidate.get("material")
    if not isinstance(claim, str) or not claim.strip():
        raise FoundationInputError("closed-input claim must be non-empty text")
    if not isinstance(material, str) or not material.strip():
        raise FoundationInputError("closed-input material universe must be non-empty text")
    normalized_claim = claim.strip()
    normalized_material = material.strip()
    if normalized_material == normalized_claim:
        raise FoundationInputError(
            "closed-input material universe cannot be the same as claim"
        )
    material_bytes = normalized_material.encode("utf-8")
    inventory = (
        {
            "path": "materials/MAT-0001.txt",
            "sha256": sha256_bytes(material_bytes),
            "media_type": "text/plain",
        },
    )
    return RequestProfile(
        "closed-input",
        normalized_claim,
        inventory,
        _material_universe_sha256(inventory),
    )


def parse_request_profile(request_bytes: bytes) -> RequestProfile:
    if not isinstance(request_bytes, bytes):
        raise TypeError("request_bytes must be bytes")
    try:
        stripped = request_bytes.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise FoundationInputError("natural-language request must be UTF-8") from error
    if not stripped:
        raise FoundationInputError("natural-language request is empty")
    try:
        candidate = json.loads(stripped)
    except json.JSONDecodeError:
        candidate = None
    if not isinstance(candidate, dict) or candidate.get("analysis_kind") != "closed-input":
        return RequestProfile("open-world", stripped, (), None)
    return validate_closed_input_profile(candidate, request_bytes=request_bytes)


def _input_inventory_path(layout: RunLayout) -> Path:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    return assert_safe_descendant(
        layout.root,
        layout.input_dir / INPUT_INVENTORY_FILENAME,
    )


def _safe_material_extension(path: Path) -> str:
    extension = path.suffix[1:].casefold()
    return extension if _SAFE_EXTENSION_RE.fullmatch(extension) else "bin"


def _media_type(extension: str) -> str:
    return {
        "json": "application/json",
        "md": "text/markdown",
        "markdown": "text/markdown",
        "txt": "text/plain",
    }.get(extension, "application/octet-stream")


def seal_input_inventory(
    layout: RunLayout,
    *,
    request_sha256: str,
    material_files: Sequence[Path],
    now: datetime,
    request_bytes: bytes | None = None,
) -> dict[str, object]:
    if isinstance(material_files, (str, bytes)):
        raise TypeError("material_files must be a sequence of paths")
    _require_utc(now, "now")
    inventory_path = _input_inventory_path(layout)
    if inventory_path.exists():
        raise FileExistsError("material input inventory already exists")
    material_payloads: list[tuple[bytes, str]] = []
    if request_bytes is not None:
        profile = parse_request_profile(request_bytes)
        if profile.analysis_kind == "closed-input":
            candidate = json.loads(request_bytes.decode("utf-8"))
            material_payloads.append(
                (str(candidate["material"]).strip().encode("utf-8"), "txt")
            )
    for source in tuple(material_files):
        if not isinstance(source, Path):
            raise TypeError("material file entries must be pathlib.Path values")
        source = source.resolve()
        if not source.is_file():
            raise ValueError(f"--material-file is not a file: {source}")
        material_payloads.append(
            (source.read_bytes(), _safe_material_extension(source))
        )
    materials: list[dict[str, str]] = []
    for ordinal, (material_bytes, extension) in enumerate(
        material_payloads,
        start=1,
    ):
        relative_path = f"materials/MAT-{ordinal:04d}.{extension}"
        target = assert_safe_descendant(layout.root, layout.input_dir / relative_path)
        atomic_write_bytes(target, material_bytes)
        materials.append(
            {
                "path": relative_path,
                "sha256": sha256_bytes(material_bytes),
                "media_type": _media_type(extension),
            }
        )
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.input-inventory",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": _canonical_utc(now),
        "request_sha256": request_sha256,
        "materials": materials,
        "material_universe_sha256": _material_universe_sha256(materials),
        "content_sha256": "0" * 64,
    }
    document["content_sha256"] = compute_artifact_content_sha256(document)
    validate_instance("ultra-input-inventory.schema.json", document)
    atomic_write_json(inventory_path, document)
    return copy.deepcopy(document)


def load_input_inventory(layout: RunLayout) -> dict[str, object]:
    path = _input_inventory_path(layout)
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("material input inventory is unavailable") from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError("material input inventory is not canonical")
    try:
        validate_instance("ultra-input-inventory.schema.json", document)
    except Exception as error:
        raise FoundationInputError("material input inventory is invalid") from error
    if (
        document.get("run_id") != layout.run_dir.name
        or document.get("version_binding") != current_version_binding()
        or document.get("content_sha256")
        != compute_artifact_content_sha256(document)
    ):
        raise FoundationInputError("material input inventory authority differs")
    materials = document.get("materials")
    if not isinstance(materials, list):
        raise FoundationInputError("material input inventory materials are invalid")
    if document.get("material_universe_sha256") != _material_universe_sha256(materials):
        raise FoundationInputError("material universe hash differs from its inventory")
    for item in materials:
        if not isinstance(item, Mapping):
            raise FoundationInputError("material inventory entry is invalid")
        relative = str(item["path"])
        if relative in {"request.bin", "request-metadata.json"}:
            raise FoundationInputError("request authority cannot count as closed material")
        candidate = assert_safe_descendant(layout.root, layout.input_dir / relative)
        try:
            measured = sha256_bytes(candidate.read_bytes())
        except OSError as error:
            raise FoundationInputError("material inventory file is unavailable") from error
        if measured != item.get("sha256"):
            raise FoundationInputError("material inventory file hash differs")
    return copy.deepcopy(document)


def load_host_capability_attestation(
    layout: RunLayout,
    *,
    expected_request_sha256: str | None = None,
    expected_version_binding: Mapping[str, object] | None = None,
) -> HostCapabilitySeal:
    path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / CAPABILITY_ATTESTATION_RELATIVE_PATH,
    )
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError(
            "persisted host capability attestation is unavailable"
        ) from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError(
            "persisted host capability attestation is not canonical"
        )
    return validate_host_capability_attestation(
        document,
        expected_run_id=layout.run_dir.name,
        expected_request_sha256=expected_request_sha256,
        expected_version_binding=expected_version_binding,
    )


def load_request_profile(layout: RunLayout) -> RequestProfile:
    request_path = assert_safe_descendant(layout.root, layout.input_dir / "request.bin")
    try:
        request_bytes = request_path.read_bytes()
    except OSError as error:
        raise FoundationInputError("immutable request is unavailable") from error
    profile = parse_request_profile(request_bytes)
    inventory = load_input_inventory(layout)
    disk_materials = tuple(copy.deepcopy(inventory["materials"]))
    if disk_materials:
        return RequestProfile(
            profile.analysis_kind,
            profile.claim,
            disk_materials,
            str(inventory["material_universe_sha256"]),
        )
    return profile


def build_evidence_admission_authority(
    layout: RunLayout,
    *,
    admitted_sources: Mapping[str, Mapping[str, object]],
    evidence_cutoff: str,
):
    from .evidence import EvidenceAdmissionAuthority

    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    request_path = assert_safe_descendant(
        layout.root,
        layout.input_dir / "request.bin",
    )
    try:
        request_bytes = request_path.read_bytes()
    except OSError as error:
        raise FoundationInputError("immutable request is unavailable for U3") from error
    if sha256_bytes(request_bytes) != _request_sha256(layout):
        raise FoundationInputError("U3 request bytes differ from request authority")
    inventory = load_input_inventory(layout)
    materials = inventory.get("materials")
    if not isinstance(materials, list):
        raise FoundationInputError("U3 material inventory is invalid")
    admitted_materials: list[dict[str, object]] = []
    for item in materials:
        if not isinstance(item, Mapping):
            raise FoundationInputError("U3 material inventory entry is invalid")
        snapshot = copy.deepcopy(dict(item))
        relative = snapshot.get("path")
        if not isinstance(relative, str):
            raise FoundationInputError("U3 material inventory path is invalid")
        material_path = assert_safe_descendant(
            layout.root,
            layout.input_dir / relative,
        )
        try:
            content_bytes = material_path.read_bytes()
        except OSError as error:
            raise FoundationInputError(
                "U3 material bytes are unavailable for attribution"
            ) from error
        if sha256_bytes(content_bytes) != snapshot.get("sha256"):
            raise FoundationInputError("U3 material bytes differ from input inventory")
        snapshot["content_bytes"] = content_bytes
        admitted_materials.append(snapshot)
    return EvidenceAdmissionAuthority(
        run_id=layout.run_dir.name,
        request_bytes=request_bytes,
        input_inventory=tuple(admitted_materials),
        admitted_sources=admitted_sources,
        evidence_cutoff=evidence_cutoff,
    )


def complete_u3_evidence(
    layout: RunLayout,
    *,
    phase_store: object,
    authority: object,
    candidate_entries: Sequence[Mapping[str, object]],
    verified_subagent_candidates: Sequence[Mapping[str, object]],
    now: datetime,
):
    from . import evidence, recovery
    from .state_machine import PhaseStore

    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    if not isinstance(phase_store, PhaseStore):
        raise TypeError("phase_store must be a PhaseStore")
    if not isinstance(authority, evidence.EvidenceAdmissionAuthority):
        raise TypeError("authority must be an EvidenceAdmissionAuthority")
    if isinstance(candidate_entries, (str, bytes)) or isinstance(
        verified_subagent_candidates, (str, bytes)
    ):
        raise TypeError("U3 candidates must be sequences of evidence objects")
    _require_utc(now, "now")
    if (
        layout.run_dir.name != phase_store.run_id
        or authority.run_id != phase_store.run_id
        or authority.evidence_cutoff != phase_store.evidence_cutoff
        or phase_store.current_phase != "U2"
        or phase_store.evidence_frozen
        or sha256_bytes(authority.request_bytes)
        != phase_store.run_contract["request_sha256"]
    ):
        raise FoundationInputError("U3 authority differs from the completed U2 boundary")
    existing_entries = phase_store.evidence_artifact.get("entries")
    if not isinstance(existing_entries, list) or existing_entries:
        raise FoundationInputError(
            "U3 seam rejects pre-existing evidence outside the admission batch"
        )
    candidates = tuple(candidate_entries)
    subagent_candidates = tuple(verified_subagent_candidates)
    if not candidates and not subagent_candidates:
        raise FoundationInputError("U3 requires at least one evidence candidate")
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise TypeError("U3 evidence candidates must be objects")
        attribution = candidate.get("attribution")
        if isinstance(attribution, Mapping) and attribution.get("origin_kind") == "subagent":
            raise FoundationInputError(
                "subagent candidates must enter through the verified U2 candidate seam"
            )
    for candidate in subagent_candidates:
        if not isinstance(candidate, Mapping):
            raise TypeError("verified subagent candidates must be objects")
        attribution = candidate.get("attribution")
        if not isinstance(attribution, Mapping) or attribution.get("origin_kind") != "subagent":
            raise FoundationInputError(
                "verified subagent candidate lacks subagent attribution"
            )
    admitted = tuple(
        evidence.admit_evidence_candidate(candidate, authority=authority)
        for candidate in (*candidates, *subagent_candidates)
    )
    evidence_ids = tuple(str(entry["evidence_id"]) for entry in admitted)
    if len(evidence_ids) != len(set(evidence_ids)):
        raise evidence.EvidenceValidationError(
            "duplicate evidence_id in U3 admission candidates"
        )
    phase_store.freeze_evidence_cutoff(authority.evidence_cutoff)
    for entry in admitted:
        phase_store.append_evidence(entry)
    seal = phase_store.freeze_evidence()
    artifact = phase_store.evidence_artifact
    evidence_path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / U3_EVIDENCE_RELATIVE_PATH,
    )
    artifact_bytes = canonical_json_bytes(artifact)
    if evidence_path.exists():
        try:
            existing = evidence_path.read_bytes()
        except OSError as error:
            raise FoundationInputError("persisted U3 evidence artifact is unreadable") from error
        if existing != artifact_bytes:
            raise FoundationInputError("persisted U3 evidence artifact changed")
    else:
        atomic_write_bytes(evidence_path, artifact_bytes)
    phase_store.complete(
        "U3",
        artifact_hashes=(seal.artifact_sha256,),
        evidence_authority=seal,
    )
    recovery.create_checkpoint(
        layout,
        phase_store,
        boundary_kind="phase",
        boundary_id="U3",
        boundary_ordinal=0,
        artifact_paths=(evidence_path,),
        now=now,
    )
    return seal


def _request_sha256(layout: RunLayout) -> str:
    request_path = assert_safe_descendant(layout.root, layout.input_dir / "request.bin")
    metadata_path = assert_safe_descendant(
        layout.root, layout.input_dir / "request-metadata.json"
    )
    try:
        request_bytes = request_path.read_bytes()
        metadata_raw = metadata_path.read_bytes()
        metadata = load_json_object_bytes(metadata_raw, source=str(metadata_path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("request metadata is unavailable") from error
    measured = sha256_bytes(request_bytes)
    if (
        metadata_raw != canonical_json_bytes(metadata)
        or metadata
        != {"request_sha256": measured, "request_size": len(request_bytes)}
    ):
        raise FoundationInputError("request metadata differs from immutable request")
    return measured


def _capability_requirements(analysis_kind: str) -> dict[str, str]:
    open_world = analysis_kind == "open-world"
    return {
        "filesystem": "required",
        "docx_parser": "not-applicable",
        "network": "required" if open_world else "not-applicable",
        "retrieval": "required" if open_world else "not-applicable",
        "validators": "required",
        "subagents": "not-applicable",
        "model_context": "required",
    }


def _capability_action_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir / CAPABILITY_ACTION_FILENAME,
    )


def _validate_capability_action(
    layout: RunLayout,
    document: Mapping[str, object],
) -> HostActionSeal:
    action = copy.deepcopy(dict(document))
    try:
        validate_instance("ultra-host-action.schema.json", action)
    except Exception as error:
        raise FoundationInputError("persisted U0 capability action is invalid") from error
    supplied = action.get("action_sha256")
    payload = copy.deepcopy(action)
    payload.pop("action_sha256", None)
    if (
        supplied != sha256_bytes(canonical_json_bytes(payload))
        or action.get("run_id") != layout.run_dir.name
        or action.get("version_binding") != current_version_binding()
        or action.get("phase_id") != "U0"
        or action.get("action_kind") != "capability-attestation"
    ):
        raise FoundationInputError("persisted U0 capability action authority differs")
    result_relative = action.get("result_relative_path")
    if not isinstance(result_relative, str):
        raise FoundationInputError("persisted U0 capability result path is invalid")
    result_path = assert_safe_descendant(
        layout.root,
        layout.run_dir / result_relative,
    )
    return HostActionSeal(action, str(supplied), result_path)


def _persist_capability_action(layout: RunLayout, action: HostActionSeal) -> None:
    path = _capability_action_path(layout)
    if path.exists():
        try:
            existing = load_json_object_bytes(path.read_bytes(), source=str(path))
        except (OSError, TypeError, ValueError) as error:
            raise FoundationInputError(
                "persisted U0 capability action is unreadable"
            ) from error
        if existing != action.document:
            raise FoundationInputError("persisted U0 capability action changed")
        return
    atomic_write_json(path, action.document)


def _load_capability_action(layout: RunLayout) -> HostActionSeal | None:
    path = _capability_action_path(layout)
    if not path.exists():
        return None
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("persisted U0 capability action is unreadable") from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError("persisted U0 capability action is not canonical")
    return _validate_capability_action(layout, document)


def _load_accepted_capability_result(
    layout: RunLayout,
    action: HostActionSeal,
) -> HostResultSeal | None:
    accepted_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json",
    )
    if not accepted_path.exists():
        return None
    try:
        raw = accepted_path.read_bytes()
        document = load_json_object_bytes(raw, source=str(accepted_path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("accepted capability result is unreadable") from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError("accepted capability result is not canonical")
    try:
        validate_instance("ultra-host-result-receipt.schema.json", document)
    except Exception as error:
        raise FoundationInputError("accepted capability result receipt is invalid") from error
    supplied = document.get("receipt_sha256")
    payload = copy.deepcopy(document)
    payload.pop("receipt_sha256", None)
    if supplied != sha256_bytes(canonical_json_bytes(payload)):
        raise FoundationInputError("accepted capability result receipt hash differs")
    action_fields = (
        "run_id",
        "version_binding",
        "phase_id",
        "action_kind",
        "parent_event_sha256",
        "request_sha256",
        "result_relative_path",
    )
    if (
        document.get("action_sha256") != action.action_sha256
        or any(document.get(field) != action.document.get(field) for field in action_fields)
    ):
        raise FoundationInputError("accepted capability result authority differs")
    try:
        result_bytes = action.result_path.read_bytes()
    except OSError as error:
        raise FoundationInputError("accepted host capability result is unavailable") from error
    if document.get("result_sha256") != sha256_bytes(result_bytes):
        raise FoundationInputError("accepted host capability result hash differs")
    return HostResultSeal(document, str(supplied), action.action_sha256)


def _build_capability_attestation(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
    profile: RequestProfile,
) -> HostCapabilitySeal:
    try:
        result_document = load_json_object_bytes(
            action.result_path.read_bytes(),
            source=str(action.result_path),
        )
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("host capability result is invalid JSON") from error
    expected_result_fields = {
        "measured_availability",
        "providers",
        "tools",
        "measured_at",
        "proof_grade",
    }
    if set(result_document) != expected_result_fields:
        raise FoundationInputError(
            "host capability result contains runtime-owned or unknown fields"
        )
    payload = action.document.get("payload")
    if not isinstance(payload, Mapping):
        raise FoundationInputError("U0 capability action payload is invalid")
    expected_payload_fields = {
        "analysis_kind",
        "requirements",
        "run_mode",
        "sensitivity",
        "retention",
        "outbound_permission",
        "evidence_cutoff",
        "resource_limits",
        "requested_result_fields",
    }
    if set(payload) != expected_payload_fields:
        raise FoundationInputError("U0 capability action payload is not closed")
    if (
        payload.get("analysis_kind") != profile.analysis_kind
        or payload.get("requested_result_fields") != sorted(expected_result_fields)
    ):
        raise FoundationInputError("U0 capability action differs from request profile")
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.host-capability-attestation",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": result.document["completed_at"],
        "phase_id": "U0",
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "receipt_sha256": result.receipt_sha256,
        "analysis_kind": profile.analysis_kind,
        "run_mode": payload["run_mode"],
        "requirements": copy.deepcopy(payload["requirements"]),
        "measured_availability": copy.deepcopy(
            result_document["measured_availability"]
        ),
        "providers": copy.deepcopy(result_document["providers"]),
        "tools": copy.deepcopy(result_document["tools"]),
        "sensitivity": payload["sensitivity"],
        "retention": payload["retention"],
        "outbound_permission": payload["outbound_permission"],
        "evidence_cutoff": payload["evidence_cutoff"],
        "resource_limits": copy.deepcopy(payload["resource_limits"]),
        "measured_at": result_document["measured_at"],
        "proof_grade": result_document["proof_grade"],
        "content_sha256": "0" * 64,
    }
    document["content_sha256"] = compute_artifact_content_sha256(document)
    return validate_host_capability_attestation(
        document,
        expected_run_id=layout.run_dir.name,
        expected_request_sha256=str(action.document["request_sha256"]),
        expected_version_binding=current_version_binding(),
    )


def _input_media_type(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return "application/json"
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    if suffix == ".txt":
        return "text/plain"
    return "application/octet-stream"


def _snapshot_all_inputs(
    layout: RunLayout,
) -> tuple[tuple[dict[str, str], ...], str]:
    try:
        files = tuple(
            sorted(
                (path for path in layout.input_dir.rglob("*") if path.is_file()),
                key=lambda path: path.relative_to(layout.input_dir).as_posix(),
            )
        )
    except OSError as error:
        raise FoundationInputError("immutable input snapshot is unavailable") from error
    if not files:
        raise FoundationInputError("immutable input snapshot is empty")
    inputs = tuple(
        {
            "path": path.relative_to(layout.input_dir).as_posix(),
            "sha256": sha256_bytes(path.read_bytes()),
            "media_type": _input_media_type(path),
        }
        for path in files
    )
    return inputs, sha256_bytes(canonical_json_bytes(inputs))


def _complete_u0(
    layout: RunLayout,
    *,
    repo: Path,
    attestation: HostCapabilitySeal,
    now: datetime,
) -> object:
    from . import recovery, source_integrity
    from .state_machine import PhaseStore

    document = attestation.document
    request_sha256 = str(document["request_sha256"])
    inputs, input_snapshot_sha256 = _snapshot_all_inputs(layout)
    manifest = source_integrity.load_source_manifest(
        repo / "skills/crossframe-ultra/references/source-manifest.json"
    )
    run_contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": request_sha256,
        "analysis_kind": document["analysis_kind"],
        "capability_attestation_sha256": attestation.artifact_sha256,
        "run_mode": document["run_mode"],
        "sensitivity": document["sensitivity"],
        "retention": document["retention"],
        "outbound_permission": document["outbound_permission"],
        "evidence_cutoff": document["evidence_cutoff"],
        "capabilities": copy.deepcopy(document["requirements"]),
        "resource_limits": copy.deepcopy(document["resource_limits"]),
    }
    phase_store = PhaseStore(
        run_id=layout.run_dir.name,
        version_binding=current_version_binding(),
        source_sha256=manifest.sha256,
        input_artifact_hashes=tuple(item["sha256"] for item in inputs),
        input_snapshot_sha256=input_snapshot_sha256,
        evidence_cutoff=str(document["evidence_cutoff"]),
        now=now,
        run_contract=run_contract,
        capability_attestation=attestation,
        source_repository=repo,
        run_layout=layout,
    )
    attestation_path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / CAPABILITY_ATTESTATION_RELATIVE_PATH,
    )
    if attestation_path.exists():
        if attestation_path.read_bytes() != attestation.artifact_bytes:
            raise FoundationInputError("persisted host capability attestation changed")
    else:
        atomic_write_bytes(attestation_path, attestation.artifact_bytes)
    run_contract_path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / "ultra-run-contract.json",
    )
    atomic_write_json(run_contract_path, dict(phase_store.run_contract))
    phase_store.complete(
        "U0",
        artifact_hashes=(phase_store.run_contract_artifact_sha256,),
    )
    recovery.create_checkpoint(
        layout,
        phase_store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(run_contract_path,),
        now=now,
    )
    return phase_store


def advance_u0(
    layout: RunLayout,
    *,
    repo: Path,
    now: datetime,
) -> FoundationProgress:
    if not isinstance(repo, Path) or not repo.resolve().is_dir():
        raise ValueError("repo must be an existing pathlib.Path directory")
    _require_utc(now, "now")
    profile = load_request_profile(layout)
    request_sha256 = _request_sha256(layout)
    pending = load_pending_action(layout)
    persisted_action = _load_capability_action(layout)
    if pending is not None:
        if (
            pending.document.get("phase_id") != "U0"
            or pending.document.get("action_kind") != "capability-attestation"
            or pending.document.get("request_sha256") != request_sha256
        ):
            raise FoundationInputError("pending host action differs from U0 authority")
        if persisted_action is not None and persisted_action != pending:
            raise FoundationInputError("pending and persisted U0 actions differ")
        _persist_capability_action(layout, pending)
        return FoundationProgress("awaiting-host-action", None, pending, None)
    if persisted_action is not None:
        result = _load_accepted_capability_result(layout, persisted_action)
        if result is None:
            raise FoundationInputError(
                "persisted U0 capability action has no accepted host result"
            )
        attestation = _build_capability_attestation(
            layout,
            action=persisted_action,
            result=result,
            profile=profile,
        )
        phase_store = _complete_u0(
            layout,
            repo=repo.resolve(),
            attestation=attestation,
            now=now,
        )
        return FoundationProgress("advanced", phase_store, None, "U0")
    status = RunStatusStore(layout).read()
    run_mode = "production" if layout.root == PRODUCTION_ROOT else "test"
    requirements = _capability_requirements(profile.analysis_kind)
    action = issue_host_action(
        layout,
        action_kind="capability-attestation",
        phase_id="U0",
        parent_event_sha256=None,
        request_sha256=request_sha256,
        payload={
            "analysis_kind": profile.analysis_kind,
            "requirements": requirements,
            "run_mode": run_mode,
            "sensitivity": "private",
            "retention": "retain",
            "outbound_permission": "deidentified-only",
            "evidence_cutoff": status.created_at,
            "resource_limits": {
                "maximum_branches": 64,
                "maximum_retrieval_rounds_without_material_novelty": 2,
                "maximum_tool_retries": 3,
                "maximum_repair_attempts": 3,
            },
            "requested_result_fields": [
                "measured_at",
                "measured_availability",
                "proof_grade",
                "providers",
                "tools",
            ],
        },
        result_relative_path="work/host/U00-capability-result.json",
        now=now,
    )
    _persist_capability_action(layout, action)
    return FoundationProgress("awaiting-host-action", None, action, None)


def _u1_authority_path(layout: RunLayout, name: str) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "u1-authority" / name,
    )


def _load_canonical_u1_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError(f"{label} is unavailable") from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError(f"{label} is not canonical JSON")
    return document


def _persist_immutable_u1_object(
    path: Path,
    document: Mapping[str, object],
    *,
    label: str,
) -> None:
    snapshot = copy.deepcopy(dict(document))
    if path.exists():
        existing = _load_canonical_u1_object(path, label=label)
        if existing != snapshot:
            raise FoundationInputError(f"{label} changed after it was sealed")
        return
    atomic_write_json(path, snapshot)


def _prepare_u1_authority(
    layout: RunLayout,
    *,
    repo: Path,
    phase_store: object,
    now: datetime,
):
    from . import source_integrity

    if getattr(phase_store, "current_phase", None) != "U0":
        raise FoundationInputError("U1 requires a completed U0 boundary")
    events = phase_store.events
    if not events or events[-1].get("phase_id") != "U0":
        raise FoundationInputError("U1 parent event authority is unavailable")
    parent_event_sha256 = str(events[-1]["event_sha256"])
    manifest = source_integrity.load_source_manifest(
        repo / "skills/crossframe-ultra/references/source-manifest.json",
        expected_sha256=str(phase_store._source_sha256),
    )
    measurement = getattr(phase_store, "_u1_prerequisite_measurement", None)
    inputs, input_snapshot_sha256 = _snapshot_all_inputs(layout)
    if input_snapshot_sha256 != phase_store._input_snapshot_sha256:
        raise FoundationInputError("U1 input snapshot differs from sealed U0 authority")
    source_lock_path = _u1_authority_path(layout, "source-lock.json")
    read_plan_path = _u1_authority_path(layout, "read-plan.json")
    existing_u1_authority = source_lock_path.exists() and read_plan_path.exists()
    if source_lock_path.exists() != read_plan_path.exists():
        raise FoundationInputError("U1 source lock and read plan must exist together")
    if not source_lock_path.exists():
        if measurement is None:
            raise FoundationInputError("U1 prerequisite measurement is unavailable")
        source_lock = source_integrity.build_source_lock(
            run_id=layout.run_dir.name,
            version_binding=current_version_binding(),
            generated_at=_canonical_utc(now),
            prerequisite_measurement=measurement,
            parent_event_sha256=parent_event_sha256,
            evidence_cutoff=phase_store.evidence_cutoff,
            run_layout=layout,
            inputs=inputs,
            remeasure_prerequisites=False,
        )
        _persist_immutable_u1_object(
            source_lock_path,
            source_lock,
            label="U1 source lock",
        )
        source_lock_sha256 = sha256_bytes(source_lock_path.read_bytes())
        read_plan = source_integrity.build_read_plan(
            manifest,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            source_lock_sha256=source_lock_sha256,
            parent_event_sha256=parent_event_sha256,
            run_id=layout.run_dir.name,
            version_binding=current_version_binding(),
            generated_at=_canonical_utc(now),
            request_sha256=str(phase_store.run_contract["request_sha256"]),
            input_snapshot_sha256=input_snapshot_sha256,
            reader_mode="full-source",
            batch_size=source_integrity.SOURCE_READ_BATCH_SIZE,
        )
        _persist_immutable_u1_object(
            read_plan_path,
            read_plan,
            label="U1 read plan",
        )
    source_lock = _load_canonical_u1_object(
        source_lock_path,
        label="U1 source lock",
    )
    read_plan = _load_canonical_u1_object(
        read_plan_path,
        label="U1 read plan",
    )
    try:
        source_lock_sha256 = source_integrity.validate_source_lock_envelope(
            source_lock,
            expected_run_id=layout.run_dir.name,
            expected_run_mode=str(phase_store.run_contract["run_mode"]),
            expected_version_binding=current_version_binding(),
            expected_parent_event_sha256=parent_event_sha256,
            expected_evidence_cutoff=phase_store.evidence_cutoff,
            expected_inputs=inputs,
            run_layout=layout,
        )
        if source_lock_sha256 != sha256_bytes(source_lock_path.read_bytes()):
            raise FoundationInputError("U1 source lock disk hash differs")
        read_plan_sha256 = source_integrity.validate_read_plan(
            read_plan,
            manifest=manifest,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_request_sha256=str(phase_store.run_contract["request_sha256"]),
            expected_input_snapshot_sha256=input_snapshot_sha256,
            expected_source_lock_sha256=source_lock_sha256,
            expected_parent_event_sha256=parent_event_sha256,
            expected_reader_mode="full-source",
            expected_batch_size=source_integrity.SOURCE_READ_BATCH_SIZE,
            validate_schema=not existing_u1_authority,
        )
    except FoundationInputError:
        raise
    except Exception as error:
        raise FoundationInputError("U1 read plan or source lock is invalid") from error
    if read_plan_sha256 != sha256_bytes(read_plan_path.read_bytes()):
        raise FoundationInputError("U1 read plan disk hash differs")
    return (
        manifest,
        source_lock,
        source_lock_sha256,
        source_lock_path,
        read_plan,
        read_plan_sha256,
        read_plan_path,
        parent_event_sha256,
    )


def _u1_action_directory(layout: RunLayout) -> Path:
    return _u1_authority_path(layout, "read-actions")


def _persist_u1_action(layout: RunLayout, action: HostActionSeal) -> None:
    path = assert_safe_descendant(
        layout.root,
        _u1_action_directory(layout) / f"{action.action_sha256}.json",
    )
    _persist_immutable_u1_object(path, action.document, label="U1 source-read action")


def _load_u1_actions(
    layout: RunLayout,
    *,
    read_plan: Mapping[str, object],
    read_plan_sha256: str,
    source_lock_sha256: str,
    parent_event_sha256: str,
    request_sha256: str,
) -> tuple[HostActionSeal, ...]:
    directory = _u1_action_directory(layout)
    if not directory.exists():
        return ()
    try:
        paths = tuple(sorted(directory.glob("*.json")))
    except OSError as error:
        raise FoundationInputError("U1 source-read actions cannot be enumerated") from error
    units = read_plan.get("source_units")
    batch_size = read_plan.get("batch_size")
    if not isinstance(units, list) or not isinstance(batch_size, int):
        raise FoundationInputError("U1 read plan batch authority is invalid")
    actions: list[HostActionSeal] = []
    for path in paths:
        document = _load_canonical_u1_object(path, label="U1 source-read action")
        try:
            action = _seal_action(layout, document)
        except Exception as error:
            raise FoundationInputError("U1 source-read action seal is invalid") from error
        payload = action.document.get("payload")
        if not isinstance(payload, Mapping) or set(payload) != {
            "read_plan_sha256",
            "source_lock_sha256",
            "reader_mode",
            "batch_ordinal",
            "source_unit_count",
            "source_units",
        }:
            raise FoundationInputError("U1 source-read action payload is invalid")
        ordinal = payload.get("batch_ordinal")
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
            raise FoundationInputError("U1 source-read batch ordinal is invalid")
        start = (ordinal - 1) * batch_size
        expected_units = [
            {
                "source_unit_id": unit["unit_id"],
                "source_unit_sha256": unit["sha256"],
            }
            for unit in units[start : start + batch_size]
        ]
        if (
            action.document.get("phase_id") != "U1"
            or action.document.get("action_kind") != "source-read"
            or action.document.get("parent_event_sha256") != parent_event_sha256
            or action.document.get("request_sha256") != request_sha256
            or payload.get("read_plan_sha256") != read_plan_sha256
            or payload.get("source_lock_sha256") != source_lock_sha256
            or payload.get("reader_mode") != read_plan.get("reader_mode")
            or payload.get("source_units") != expected_units
            or payload.get("source_unit_count") != len(expected_units)
            or action.document.get("result_relative_path")
            != f"work/host/U01-read-{ordinal:06d}.json"
        ):
            raise FoundationInputError("U1 source-read action differs from read plan")
        actions.append(action)
    actions.sort(key=lambda item: int(item.document["payload"]["batch_ordinal"]))
    if [action.document["payload"]["batch_ordinal"] for action in actions] != list(
        range(1, len(actions) + 1)
    ):
        raise FoundationInputError("U1 source-read action batches are not contiguous")
    return tuple(actions)


def _load_accepted_u1_result(
    layout: RunLayout,
    action: HostActionSeal,
) -> HostResultSeal | None:
    path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json",
    )
    if not path.exists():
        return None
    document = _load_canonical_u1_object(path, label="accepted U1 host receipt")
    try:
        return _seal_result(layout, action=action, receipt=document)
    except Exception as error:
        raise FoundationInputError("accepted U1 host receipt is invalid") from error


def _load_u1_read_events(path: Path) -> tuple[dict[str, object], ...]:
    if not path.exists():
        return ()
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise FoundationInputError("U1 read event journal is unavailable") from error
    if not raw or not raw.endswith(b"\n"):
        raise FoundationInputError("U1 read event journal is incomplete")
    events: list[dict[str, object]] = []
    for ordinal, line in enumerate(raw.splitlines(keepends=True), start=1):
        try:
            event = load_json_object_bytes(line, source=f"{path}:{ordinal}")
        except (TypeError, ValueError) as error:
            raise FoundationInputError("U1 read event journal is invalid") from error
        if line != canonical_json_bytes(event):
            raise FoundationInputError("U1 read event journal is not canonical")
        events.append(event)
    return tuple(events)


def _append_u1_read_events(
    path: Path,
    *,
    expected_events: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    disk_events = _load_u1_read_events(path)
    snapshots = tuple(copy.deepcopy(dict(event)) for event in expected_events)
    if len(disk_events) > len(snapshots) or disk_events != snapshots[: len(disk_events)]:
        raise FoundationInputError("U1 read event journal differs from accepted receipts")
    if len(disk_events) < len(snapshots):
        existing = b"".join(canonical_json_bytes(event) for event in disk_events)
        appended = b"".join(
            canonical_json_bytes(event) for event in snapshots[len(disk_events) :]
        )
        atomic_write_bytes(path, existing + appended)
    return _load_u1_read_events(path)


def _issue_u1_read_action(
    layout: RunLayout,
    *,
    read_plan: Mapping[str, object],
    read_plan_sha256: str,
    source_lock_sha256: str,
    parent_event_sha256: str,
    request_sha256: str,
    batch_ordinal: int,
    now: datetime,
) -> HostActionSeal:
    units = read_plan.get("source_units")
    batch_size = read_plan.get("batch_size")
    if not isinstance(units, list) or not isinstance(batch_size, int):
        raise FoundationInputError("U1 read plan cannot issue a bounded batch")
    start = (batch_ordinal - 1) * batch_size
    selected = units[start : start + batch_size]
    if not selected:
        raise FoundationInputError("U1 source-read action has no remaining units")
    action = issue_host_action(
        layout,
        action_kind="source-read",
        phase_id="U1",
        parent_event_sha256=parent_event_sha256,
        request_sha256=request_sha256,
        payload={
            "read_plan_sha256": read_plan_sha256,
            "source_lock_sha256": source_lock_sha256,
            "reader_mode": read_plan["reader_mode"],
            "batch_ordinal": batch_ordinal,
            "source_unit_count": len(selected),
            "source_units": [
                {
                    "source_unit_id": unit["unit_id"],
                    "source_unit_sha256": unit["sha256"],
                }
                for unit in selected
            ],
        },
        result_relative_path=f"work/host/U01-read-{batch_ordinal:06d}.json",
        now=now,
    )
    _persist_u1_action(layout, action)
    return action


def _advance_u1(
    layout: RunLayout,
    *,
    repo: Path,
    phase_store: object,
    now: datetime,
) -> FoundationProgress:
    from . import recovery, source_integrity

    (
        manifest,
        _source_lock,
        source_lock_sha256,
        source_lock_path,
        read_plan,
        read_plan_sha256,
        read_plan_path,
        parent_event_sha256,
    ) = _prepare_u1_authority(
        layout,
        repo=repo,
        phase_store=phase_store,
        now=now,
    )
    request_sha256 = str(phase_store.run_contract["request_sha256"])
    actions = _load_u1_actions(
        layout,
        read_plan=read_plan,
        read_plan_sha256=read_plan_sha256,
        source_lock_sha256=source_lock_sha256,
        parent_event_sha256=parent_event_sha256,
        request_sha256=request_sha256,
    )
    pending = load_pending_action(layout)
    if pending is not None and (
        pending.document.get("phase_id") != "U1"
        or pending.document.get("action_kind") != "source-read"
    ):
        raise FoundationInputError("pending host action differs from U1 authority")
    read_events_path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl",
    )
    disk_events = _load_u1_read_events(read_events_path)
    disk_offset = 0
    expected_events: list[dict[str, object]] = []
    outstanding: HostActionSeal | None = None
    for action in actions:
        accepted = _load_accepted_u1_result(layout, action)
        if accepted is None:
            if outstanding is not None or pending != action:
                raise FoundationInputError(
                    "U1 source-read action lacks its pending or accepted authority"
                )
            outstanding = action
            continue
        if outstanding is not None:
            raise FoundationInputError("U1 accepted actions follow an incomplete batch")
        try:
            payload = action.document["payload"]
            batch_count = int(payload["source_unit_count"])
            admitted = disk_events[disk_offset : disk_offset + batch_count]
            if admitted and admitted[0].get("action_sha256") == action.action_sha256:
                if len(admitted) != batch_count:
                    raise FoundationInputError("U1 admitted read batch is incomplete")
                batch_events = source_integrity.validate_admitted_host_read_events(
                    admitted,
                    accepted.document,
                    action=action,
                    manifest=manifest,
                )
                disk_offset += batch_count
            else:
                batch_events = source_integrity.validate_host_read_receipt(
                    accepted.document,
                    action=action,
                    repo=repo,
                    manifest=manifest,
                )
        except Exception as error:
            raise FoundationInputError("accepted U1 host read receipt is invalid") from error
        expected_events.extend(batch_events)
    if pending is not None and pending not in actions:
        raise FoundationInputError("pending U1 action is not durably persisted")
    if disk_offset != len(disk_events):
        raise FoundationInputError("U1 read event journal has no accepted action authority")
    read_events = _append_u1_read_events(
        read_events_path,
        expected_events=expected_events,
    )
    if outstanding is not None:
        return FoundationProgress(
            "awaiting-host-action",
            phase_store,
            outstanding,
            None,
        )
    total = int(read_plan["source_unit_count"])
    if len(read_events) < total:
        if pending is not None:
            raise FoundationInputError("U1 pending action does not match durable batches")
        action = _issue_u1_read_action(
            layout,
            read_plan=read_plan,
            read_plan_sha256=read_plan_sha256,
            source_lock_sha256=source_lock_sha256,
            parent_event_sha256=parent_event_sha256,
            request_sha256=request_sha256,
            batch_ordinal=len(actions) + 1,
            now=now,
        )
        return FoundationProgress(
            "awaiting-host-action",
            phase_store,
            action,
            None,
        )
    if len(read_events) != total or pending is not None:
        raise FoundationInputError("U1 read coverage exceeds or conflicts with its plan")
    coverage = source_integrity.build_host_read_coverage(
        read_events,
        read_plan=read_plan,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_parent_event_sha256=parent_event_sha256,
        expected_source_lock_sha256=source_lock_sha256,
        expected_read_plan_sha256=read_plan_sha256,
    )
    coverage_path = _u1_authority_path(layout, "source-coverage.json")
    _persist_immutable_u1_object(
        coverage_path,
        coverage,
        label="U1 source coverage",
    )
    coverage_sha256 = sha256_bytes(coverage_path.read_bytes())
    inputs, _input_snapshot_sha256 = _snapshot_all_inputs(layout)
    try:
        authority = source_integrity._validate_persisted_u1_authority(
            repo=repo,
            run_layout=layout,
            manifest=manifest,
            source_lock=_source_lock,
            read_plan=read_plan,
            coverage=coverage,
            read_events=read_events,
            expected_run_id=layout.run_dir.name,
            expected_run_mode=str(phase_store.run_contract["run_mode"]),
            expected_version_binding=current_version_binding(),
            expected_parent_event_sha256=parent_event_sha256,
            expected_evidence_cutoff=phase_store.evidence_cutoff,
            expected_inputs=inputs,
            expected_request_sha256=request_sha256,
            expected_source_lock_sha256=source_lock_sha256,
            expected_read_plan_sha256=read_plan_sha256,
            expected_read_coverage_sha256=coverage_sha256,
        )
    except Exception as error:
        raise FoundationInputError("final U1 disk authority validation failed") from error
    phase_store.complete(
        "U1",
        artifact_hashes=(
            source_lock_sha256,
            read_plan_sha256,
            coverage_sha256,
        ),
        u1_authority=authority,
    )
    recovery.create_checkpoint(
        layout,
        phase_store,
        boundary_kind="phase",
        boundary_id="U1",
        boundary_ordinal=0,
        artifact_paths=(source_lock_path, read_plan_path, coverage_path),
        now=now,
    )
    return FoundationProgress("advanced", phase_store, None, "U1")


def advance_foundation(
    layout: RunLayout,
    *,
    repo: Path,
    now: datetime,
) -> FoundationProgress:
    if not isinstance(repo, Path) or not repo.resolve().is_dir():
        raise ValueError("repo must be an existing pathlib.Path directory")
    _require_utc(now, "now")
    from . import recovery

    checkpoints_dir = layout.recovery_dir / "checkpoints"
    if not checkpoints_dir.is_dir():
        return advance_u0(layout, repo=repo, now=now)
    try:
        resumed = recovery.resume_run(
            layout,
            now=now,
            source_repository=repo.resolve(),
        )
    except Exception as error:
        if isinstance(error, FoundationInputError):
            raise
        raise FoundationInputError("foundation recovery authority is invalid") from error
    phase_store = resumed.phase_store
    if phase_store is None:
        raise FoundationInputError("foundation recovery did not return a phase store")
    if phase_store.current_phase == "U0":
        return _advance_u1(
            layout,
            repo=repo.resolve(),
            phase_store=phase_store,
            now=now,
        )
    if phase_store.current_phase == "U1":
        return FoundationProgress("advanced", phase_store, None, "U1")
    raise FoundationInputError("foundation recovery is outside the U0-U1 Task 3 boundary")
def _persist_u2_ledger(
    layout: RunLayout,
    ledger: Mapping[str, object],
) -> None:
    path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / U2_RETRIEVAL_LEDGER_RELATIVE_PATH,
    )
    document = copy.deepcopy(dict(ledger))
    if path.exists():
        try:
            raw = path.read_bytes()
            existing = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError) as error:
            raise FoundationInputError("persisted U2 ledger is unreadable") from error
        if raw != canonical_json_bytes(existing) or existing != document:
            raise FoundationInputError("persisted U2 ledger changed")
        return
    atomic_write_json(path, document)


def advance_u2(
    layout: RunLayout,
    *,
    phase_store: object,
    claim: str,
    trigger_kinds: Sequence[str],
    now: datetime,
) -> FoundationProgress:
    """Advance only the U2 boundary from a caller-supplied sealed U1 store."""

    from . import retrieval

    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    _require_utc(now, "now")
    if getattr(phase_store, "_run_layout", None) != layout:
        raise FoundationInputError("sealed U1 run layout differs from U2 layout")
    disposition = retrieval.issue_retrieval_action(
        phase_store,
        claim=claim,
        trigger_kinds=trigger_kinds,
        generated_at=_canonical_utc(now),
    )
    if isinstance(disposition, HostActionSeal):
        pending = load_pending_action(layout)
        if pending is not None:
            if pending != disposition:
                raise FoundationInputError(
                    "pending host action differs from U2 retrieval authority"
                )
            return FoundationProgress(
                "awaiting-host-action",
                phase_store,
                disposition,
                None,
            )
        accepted_path = assert_safe_descendant(
            layout.root,
            layout.recovery_dir
            / "host-results"
            / disposition.action_sha256
            / "accepted.json",
        )
        try:
            accepted_raw = accepted_path.read_bytes()
            accepted = load_json_object_bytes(
                accepted_raw,
                source=str(accepted_path),
            )
        except (OSError, TypeError, ValueError) as error:
            raise FoundationInputError(
                "persisted U2 action has no accepted host result"
            ) from error
        if accepted_raw != canonical_json_bytes(accepted):
            raise FoundationInputError("accepted U2 host result is not canonical")
        receipt_sha256 = accepted.get("receipt_sha256")
        if not isinstance(receipt_sha256, str):
            raise FoundationInputError("accepted U2 host result has no receipt hash")
        receipt = HostResultSeal(
            accepted,
            receipt_sha256,
            disposition.action_sha256,
        )
        decision = retrieval.assess_retrieval_eligibility(
            claim,
            phase_store=phase_store,
            trigger_kinds=trigger_kinds,
        )
        authorization = retrieval.gate_retrieval(
            decision,
            phase_store=phase_store,
        )
        if not isinstance(authorization, retrieval.RetrievalAuthorization):
            raise FoundationInputError(
                "accepted U2 result has no required retrieval authorization"
            )
        ledger = retrieval.admit_host_retrieval_result(
            receipt,
            phase_store=phase_store,
            decision=decision,
            authorization=authorization,
        )
        _persist_u2_ledger(layout, ledger)
        boundary = phase_store.retrieval_boundary
        seal = retrieval.validate_retrieval_ledger(
            ledger,
            phase_store=phase_store,
            expected_run_id=phase_store.run_id,
            expected_version_binding=boundary.version_binding,
            expected_phase_id="U2",
            expected_u1_parent_event_sha256=boundary.u1_parent_event_sha256,
            expected_request_sha256=boundary.request_sha256,
            expected_decision_sha256=decision.decision_sha256,
            expected_authorization_sha256=authorization.authorization_sha256,
        )
        phase_store.complete(
            "U2",
            artifact_hashes=(seal.artifact_sha256,),
            retrieval_authority=seal,
        )
        return FoundationProgress("advanced", phase_store, None, "U2")
    if not isinstance(disposition, Mapping):
        raise FoundationInputError("U2 retrieval disposition is invalid")
    decision = retrieval.assess_retrieval_eligibility(
        claim,
        phase_store=phase_store,
        trigger_kinds=trigger_kinds,
    )
    authorization = retrieval.gate_retrieval(
        decision,
        phase_store=phase_store,
    )
    if not isinstance(authorization, retrieval.RetrievalAuthorization):
        raise FoundationInputError("blocked U2 disposition has no authorization")
    boundary = phase_store.retrieval_boundary
    seal = retrieval.validate_retrieval_ledger(
        disposition,
        phase_store=phase_store,
        expected_run_id=phase_store.run_id,
        expected_version_binding=boundary.version_binding,
        expected_phase_id="U2",
        expected_u1_parent_event_sha256=boundary.u1_parent_event_sha256,
        expected_request_sha256=boundary.request_sha256,
        expected_decision_sha256=decision.decision_sha256,
        expected_authorization_sha256=authorization.authorization_sha256,
    )
    if seal.completion_authorized or seal.retrieval_status != "required-blocked":
        raise FoundationInputError("blocked U2 disposition authorizes completion")
    _persist_u2_ledger(layout, disposition)
    return FoundationProgress("blocked", phase_store, None, None)


__all__ = (
    "FoundationInputError",
    "FoundationProgress",
    "HostCapabilitySeal",
    "RequestProfile",
    "advance_foundation",
    "advance_u0",
    "advance_u2",
    "build_evidence_admission_authority",
    "complete_u3_evidence",
    "load_input_inventory",
    "load_host_capability_attestation",
    "load_request_profile",
    "parse_request_profile",
    "seal_input_inventory",
    "validate_host_capability_attestation",
    "validate_closed_input_profile",
    "verify_host_capability_seal",
)
