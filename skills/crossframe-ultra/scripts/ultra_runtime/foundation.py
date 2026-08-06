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
    _load_bound_result_document,
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
from .paths import (
    PRODUCTION_ROOT,
    RunLayout,
    _parse_canonical_utc,
    _require_utc,
    assert_safe_descendant,
)
from .schemas import compute_artifact_content_sha256, validate_instance
from .status import RunStatusStore


INPUT_INVENTORY_FILENAME = "material-inventory.json"
CAPABILITY_ACTION_FILENAME = "u0-capability-action.json"
CAPABILITY_ATTESTATION_RELATIVE_PATH = Path(
    "U00-U03-evidence/U00-host-capability-attestation.json"
)
EVIDENCE_LINEAGE_RELATIVE_PATH = Path(
    "U00-U03-evidence/U00-evidence-lineage.json"
)
EVIDENCE_LINEAGE_REQUEST_RELATIVE_PATH = Path("evidence-lineage-request.json")
U2_RETRIEVAL_LEDGER_RELATIVE_PATH = Path(
    "U00-U03-evidence/U02-retrieval-ledger.json"
)
U3_EVIDENCE_RELATIVE_PATH = Path(
    "U00-U03-evidence/U03-evidence-ledger.json"
)
U3_ACTION_RELATIVE_PATH = Path("u3-authority/evidence-action.json")
U3_RESULT_RELATIVE_PATH = "work/host/U03-evidence-authoring.json"
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
    lease: object | None = None,
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
        lease=lease,
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
        return _seal_result(layout, action=action, receipt=document)
    except Exception as error:
        raise FoundationInputError("accepted capability result receipt is invalid") from error


def _build_capability_attestation(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
    profile: RequestProfile | None,
    result_document: Mapping[str, object] | None = None,
) -> HostCapabilitySeal:
    if result_document is None:
        try:
            result_document, result_raw = _load_bound_result_document(
                layout,
                action=action,
                receipt=result.document,
            )
        except Exception as error:
            raise FoundationInputError("host capability result is invalid JSON") from error
    else:
        result_document = copy.deepcopy(dict(result_document))
        result_raw = canonical_json_bytes(result_document)
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
    if result_raw != canonical_json_bytes(result_document):
        raise FoundationInputError("host capability result is not canonical")
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
    analysis_kind = payload.get("analysis_kind")
    if (
        action.document.get("phase_id") != "U0"
        or action.document.get("action_kind") != "capability-attestation"
        or analysis_kind not in {"open-world", "closed-input"}
        or (profile is not None and analysis_kind != profile.analysis_kind)
        or payload.get("requested_result_fields") != sorted(expected_result_fields)
    ):
        raise FoundationInputError("U0 capability action differs from request profile")
    receipt_provider = result.document.get("provider")
    receipt_tool = result.document.get("tool")
    providers = result_document.get("providers")
    tools = result_document.get("tools")
    if (
        not isinstance(receipt_provider, Mapping)
        or not isinstance(receipt_tool, Mapping)
        or not isinstance(providers, list)
        or not isinstance(tools, list)
        or dict(receipt_provider) not in providers
        or dict(receipt_tool) not in tools
    ):
        raise FoundationInputError(
            "host capability receipt identity differs from measured providers or tools"
        )
    try:
        issued_at = _parse_canonical_utc(
            action.document.get("issued_at"),
            "U0 capability issued_at",
        )
        measured_at = _parse_canonical_utc(
            result_document.get("measured_at"),
            "U0 capability measured_at",
        )
        completed_at = _parse_canonical_utc(
            result.document.get("completed_at"),
            "U0 capability completed_at",
        )
    except (TypeError, ValueError) as error:
        raise FoundationInputError("host capability timestamps are invalid") from error
    if not issued_at <= measured_at <= completed_at:
        raise FoundationInputError(
            "host capability measurement is outside its action execution"
        )
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
        "analysis_kind": analysis_kind,
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


_EVIDENCE_LINEAGE_INHERITED_FIELDS = (
    "parent_run_id",
    "parent_u3_event_sha256",
    "parent_evidence_sha256",
    "parent_evidence_cutoff",
    "evidence_cutoff",
    "inherited_input_refs",
    "new_evidence_ref",
)


def _lineage_path(layout: RunLayout, relative: Path) -> Path:
    return assert_safe_descendant(layout.root, layout.run_dir / relative)


def _load_canonical_lineage(
    path: Path,
    *,
    label: str,
    expected_status: str,
) -> tuple[dict[str, object], bytes]:
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError(f"{label} is unavailable") from error
    try:
        validate_instance("ultra-evidence-lineage.schema.json", document)
    except Exception as error:
        raise FoundationInputError(f"{label} violates the public schema") from error
    if (
        raw != canonical_json_bytes(document)
        or document.get("content_sha256")
        != compute_artifact_content_sha256(document)
        or document.get("status") != expected_status
    ):
        raise FoundationInputError(f"{label} authority differs")
    return document, raw


def _parse_lineage_cutoff(value: object, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise FoundationInputError(f"{label} is not canonical UTC")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise FoundationInputError(f"{label} is not canonical UTC") from error
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timezone.utc.utcoffset(parsed)
        or _canonical_utc(parsed) != value
    ):
        raise FoundationInputError(f"{label} is not canonical UTC")
    return parsed


def _load_evidence_lineage_request(
    layout: RunLayout,
) -> tuple[dict[str, object], bytes] | None:
    request_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir / EVIDENCE_LINEAGE_REQUEST_RELATIVE_PATH,
    )
    if not request_path.exists():
        return None
    request, raw = _load_canonical_lineage(
        request_path,
        label="evidence lineage request",
        expected_status="pending-u0-attestation",
    )
    if (
        request.get("run_id") != layout.run_dir.name
        or request.get("version_binding") != current_version_binding()
        or request.get("phase_id") != "U0"
        or request.get("parent_run_id") == layout.run_dir.name
    ):
        raise FoundationInputError("evidence lineage request binding differs")
    parent_cutoff = _parse_lineage_cutoff(
        request.get("parent_evidence_cutoff"),
        label="parent evidence cutoff",
    )
    child_cutoff = _parse_lineage_cutoff(
        request.get("evidence_cutoff"),
        label="child evidence cutoff",
    )
    if child_cutoff <= parent_cutoff:
        raise FoundationInputError(
            "evidence lineage child cutoff must be strictly later"
        )
    inherited = request.get("inherited_input_refs")
    new_ref = request.get("new_evidence_ref")
    if not isinstance(inherited, list) or not inherited or not isinstance(new_ref, Mapping):
        raise FoundationInputError("evidence lineage input refs are invalid")
    refs = [*inherited, new_ref]
    paths: set[str] = set()
    for ref in refs:
        if not isinstance(ref, Mapping):
            raise FoundationInputError("evidence lineage input ref is invalid")
        relative = ref.get("path")
        if not isinstance(relative, str):
            raise FoundationInputError("evidence lineage input path is invalid")
        candidate = _lineage_path(layout, Path(relative))
        try:
            candidate.relative_to(layout.input_dir)
            measured = sha256_bytes(candidate.read_bytes())
        except (OSError, ValueError) as error:
            raise FoundationInputError(
                "evidence lineage input ref is unavailable"
            ) from error
        if relative in paths or measured != ref.get("sha256"):
            raise FoundationInputError("evidence lineage input ref binding differs")
        paths.add(relative)
    from . import recovery

    try:
        recovery._validate_evidence_fork_authority(
            layout,
            lineage_request=request,
            lineage_request_bytes=raw,
        )
    except recovery.RecoveryError as error:
        raise FoundationInputError(
            "evidence lineage fork authority differs"
        ) from error
    return request, raw


def _validate_lineage_u0_bindings(
    request: Mapping[str, object],
    *,
    request_sha256: str,
    capability_attestation_sha256: str,
    run_contract_sha256: str,
    u0_event: Mapping[str, object],
) -> None:
    input_hashes = u0_event.get("input_artifact_hashes")
    if not isinstance(input_hashes, list):
        raise FoundationInputError("U0 event input authority is invalid")
    inherited = request.get("inherited_input_refs")
    new_ref = request.get("new_evidence_ref")
    if not isinstance(inherited, list) or not isinstance(new_ref, Mapping):
        raise FoundationInputError("evidence lineage input authority is invalid")
    lineage_hashes = {
        str(ref["sha256"])
        for ref in (*inherited, new_ref)
        if isinstance(ref, Mapping)
    }
    if (
        u0_event.get("run_id") != request.get("run_id")
        or u0_event.get("phase_id") != "U0"
        or u0_event.get("status") != "complete"
        or u0_event.get("evidence_cutoff") != request.get("evidence_cutoff")
        or u0_event.get("output_artifact_hashes") != [run_contract_sha256]
        or not lineage_hashes.issubset(set(input_hashes))
        or not request_sha256
        or not capability_attestation_sha256
    ):
        raise FoundationInputError("evidence lineage U0 admission binding differs")


def validate_evidence_lineage_admission(
    layout: RunLayout,
    *,
    request_sha256: str,
    capability_attestation_sha256: str,
    run_contract_sha256: str,
    u0_event: Mapping[str, object],
) -> dict[str, object] | None:
    request_record = _load_evidence_lineage_request(layout)
    finalized_path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / EVIDENCE_LINEAGE_RELATIVE_PATH,
    )
    if request_record is None:
        if finalized_path.exists():
            raise FoundationInputError(
                "finalized evidence lineage has no immutable request"
            )
        return None
    request, request_bytes = request_record
    _validate_lineage_u0_bindings(
        request,
        request_sha256=request_sha256,
        capability_attestation_sha256=capability_attestation_sha256,
        run_contract_sha256=run_contract_sha256,
        u0_event=u0_event,
    )
    finalized, _ = _load_canonical_lineage(
        finalized_path,
        label="finalized evidence lineage",
        expected_status="finalized-u0-admission",
    )
    expected = {
        field: copy.deepcopy(request[field])
        for field in _EVIDENCE_LINEAGE_INHERITED_FIELDS
    }
    expected.update(
        {
            "schema_id": "crossframe.ultra.v82.evidence-lineage",
            "schema_version": 1,
            "run_id": layout.run_dir.name,
            "version_binding": current_version_binding(),
            "phase_id": "U0",
            "lineage_request_sha256": sha256_bytes(request_bytes),
            "request_sha256": request_sha256,
            "capability_attestation_sha256": capability_attestation_sha256,
            "run_contract_sha256": run_contract_sha256,
            "u0_phase_event_sha256": u0_event.get("event_sha256"),
            "status": "finalized-u0-admission",
        }
    )
    if any(finalized.get(field) != value for field, value in expected.items()):
        raise FoundationInputError("finalized evidence lineage binding differs")
    return copy.deepcopy(finalized)


def _finalize_evidence_lineage(
    layout: RunLayout,
    *,
    request_sha256: str,
    capability_attestation_sha256: str,
    phase_store: object,
    now: datetime,
) -> dict[str, object] | None:
    request_record = _load_evidence_lineage_request(layout)
    finalized_path = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / EVIDENCE_LINEAGE_RELATIVE_PATH,
    )
    if request_record is None:
        if finalized_path.exists():
            raise FoundationInputError(
                "finalized evidence lineage has no immutable request"
            )
        return None
    request, request_bytes = request_record
    events = getattr(phase_store, "events", ())
    if not events or not isinstance(events[-1], Mapping):
        raise FoundationInputError("evidence lineage U0 event is unavailable")
    u0_event = events[-1]
    run_contract_sha256 = str(
        getattr(phase_store, "run_contract_artifact_sha256", "")
    )
    _validate_lineage_u0_bindings(
        request,
        request_sha256=request_sha256,
        capability_attestation_sha256=capability_attestation_sha256,
        run_contract_sha256=run_contract_sha256,
        u0_event=u0_event,
    )
    if finalized_path.exists():
        return validate_evidence_lineage_admission(
            layout,
            request_sha256=request_sha256,
            capability_attestation_sha256=capability_attestation_sha256,
            run_contract_sha256=run_contract_sha256,
            u0_event=u0_event,
        )
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.evidence-lineage",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": _canonical_utc(now),
        "content_sha256": "0" * 64,
        "phase_id": "U0",
        **{
            field: copy.deepcopy(request[field])
            for field in _EVIDENCE_LINEAGE_INHERITED_FIELDS
        },
        "lineage_request_sha256": sha256_bytes(request_bytes),
        "request_sha256": request_sha256,
        "capability_attestation_sha256": capability_attestation_sha256,
        "run_contract_sha256": run_contract_sha256,
        "u0_phase_event_sha256": u0_event["event_sha256"],
        "status": "finalized-u0-admission",
    }
    document["content_sha256"] = compute_artifact_content_sha256(document)
    try:
        validate_instance("ultra-evidence-lineage.schema.json", document)
    except Exception as error:
        raise FoundationInputError(
            "finalized evidence lineage violates the public schema"
        ) from error
    atomic_write_bytes(finalized_path, canonical_json_bytes(document))
    return validate_evidence_lineage_admission(
        layout,
        request_sha256=request_sha256,
        capability_attestation_sha256=capability_attestation_sha256,
        run_contract_sha256=run_contract_sha256,
        u0_event=u0_event,
    )


def _complete_u0(
    layout: RunLayout,
    *,
    repo: Path,
    attestation: HostCapabilitySeal,
    now: datetime,
    lease: object | None = None,
) -> object:
    from . import recovery, source_integrity
    from .state_machine import PhaseStore

    document = attestation.document
    request_sha256 = str(document["request_sha256"])
    inputs, input_snapshot_sha256 = _snapshot_all_inputs(layout)
    manifest = source_integrity.load_source_manifest(
        repo / "skills/crossframe-ultra/references/source-manifest.json"
    )
    run_mode = str(document["run_mode"])
    prerequisite_measurement = source_integrity.measure_u1_prerequisites(
        repo,
        manifest=manifest,
        release_manifest_path=(
            repo / "skills/crossframe-ultra/references/release-manifest.json"
            if run_mode == "test"
            else None
        ),
        run_mode=run_mode,
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
        u1_prerequisite_measurement=prerequisite_measurement,
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
        lease=lease,
    )
    _finalize_evidence_lineage(
        layout,
        request_sha256=request_sha256,
        capability_attestation_sha256=attestation.artifact_sha256,
        phase_store=phase_store,
        now=now,
    )
    return phase_store


def advance_u0(
    layout: RunLayout,
    *,
    repo: Path,
    now: datetime,
    lease: object | None = None,
) -> FoundationProgress:
    if not isinstance(repo, Path) or not repo.resolve().is_dir():
        raise ValueError("repo must be an existing pathlib.Path directory")
    _require_utc(now, "now")
    _load_evidence_lineage_request(layout)
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
            lease=lease,
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
    lease: object | None = None,
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
                    layout=layout,
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
        lease=lease,
    )
    return FoundationProgress("advanced", phase_store, None, "U1")


def advance_foundation(
    layout: RunLayout,
    *,
    repo: Path,
    now: datetime,
    lease: object | None = None,
) -> FoundationProgress:
    """Advance the runtime-owned U0 through U3 foundation coordinator.

    The coordinator consumes only durable checkpoints and host receipts.  A
    missing host result is returned as typed progress; malformed or stale
    authority remains a hard failure.
    """

    if not isinstance(repo, Path) or not repo.resolve().is_dir():
        raise ValueError("repo must be an existing pathlib.Path directory")
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    _require_utc(now, "now")
    from . import recovery

    checkpoints_dir = layout.recovery_dir / "checkpoints"
    if not checkpoints_dir.is_dir():
        first = advance_u0(layout, repo=repo, now=now, lease=lease)
        if first.outcome != "advanced":
            return first
        try:
            resumed = recovery.resume_run(
                layout,
                now=now,
                source_repository=repo.resolve(),
                lease=lease,
            )
        except Exception as error:
            if isinstance(error, FoundationInputError):
                raise
            raise FoundationInputError(
                "newly completed U0 authority cannot be restored for U1"
            ) from error
        phase_store = resumed.phase_store
    else:
        try:
            resumed = recovery.resume_run(
                layout,
                now=now,
                source_repository=repo.resolve(),
                lease=lease,
            )
        except Exception as error:
            if isinstance(error, FoundationInputError):
                raise
            raise FoundationInputError("foundation recovery authority is invalid") from error
        phase_store = resumed.phase_store
    if phase_store is None:
        raise FoundationInputError("foundation recovery did not return a phase store")

    profile = load_request_profile(layout)
    trigger_kinds = ("real-world",) if profile.analysis_kind == "open-world" else ()

    if phase_store.current_phase == "U0":
        events = phase_store.events
        if not events or not isinstance(events[-1], Mapping):
            raise FoundationInputError("U0 phase event authority is unavailable")
        _finalize_evidence_lineage(
            layout,
            request_sha256=str(phase_store.run_contract["request_sha256"]),
            capability_attestation_sha256=str(
                phase_store.run_contract["capability_attestation_sha256"]
            ),
            phase_store=phase_store,
            now=now,
        )
        u1 = _advance_u1(
            layout,
            repo=repo.resolve(),
            phase_store=phase_store,
            now=now,
            lease=lease,
        )
        if u1.outcome != "advanced":
            return u1
        phase_store = u1.phase_store
    if phase_store is None:
        raise FoundationInputError("U1 foundation advancement returned no PhaseStore")

    if phase_store.current_phase == "U1":
        u2 = advance_u2(
            layout,
            phase_store=phase_store,
            analysis_kind=profile.analysis_kind,
            claim=profile.claim,
            trigger_kinds=trigger_kinds,
            material_inventory=profile.material_inventory or None,
            material_universe_sha256=profile.material_universe_sha256,
            now=now,
            lease=lease,
        )
        if u2.outcome != "advanced":
            return u2
        phase_store = u2.phase_store
    if phase_store is None:
        raise FoundationInputError("U2 foundation advancement returned no PhaseStore")

    if phase_store.current_phase == "U2":
        return _advance_u3(
            layout,
            phase_store=phase_store,
            profile=profile,
            now=now,
            lease=lease,
        )
    if phase_store.current_phase == "U3":
        return FoundationProgress("advanced", phase_store, None, "U3")
    if phase_store.current_phase in {"U4", "U5", "U6", "U7", "U8", "U9", "U10", "U11", "U12"}:
        return FoundationProgress(
            "advanced",
            phase_store,
            None,
            phase_store.current_phase,
        )
    raise FoundationInputError("foundation recovery is outside the U0-U3 boundary")
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


def _u2_ledger_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(
        layout.root,
        layout.artifacts_dir / U2_RETRIEVAL_LEDGER_RELATIVE_PATH,
    )


def _load_validated_u2_source_projection(
    layout: RunLayout,
    *,
    expected_ledger_sha256: str,
    expected_request_sha256: object,
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    from . import retrieval

    ledger_path = _u2_ledger_path(layout)
    try:
        ledger_raw = ledger_path.read_bytes()
        ledger = load_json_object_bytes(ledger_raw, source=str(ledger_path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("persisted U2 retrieval ledger is unavailable") from error
    if ledger_raw != canonical_json_bytes(ledger):
        raise FoundationInputError("persisted U2 retrieval ledger is not canonical")
    try:
        validate_instance("ultra-retrieval-ledger.schema.json", ledger)
    except Exception as error:
        raise FoundationInputError("persisted U2 retrieval ledger is invalid") from error
    ledger_payload = copy.deepcopy(ledger)
    supplied_ledger_content_sha256 = ledger_payload.pop("content_sha256", None)
    if (
        sha256_bytes(ledger_raw) != expected_ledger_sha256
        or supplied_ledger_content_sha256
        != sha256_bytes(canonical_json_bytes(ledger_payload))
        or ledger.get("run_id") != layout.run_dir.name
        or ledger.get("version_binding") != current_version_binding()
        or ledger.get("phase_id") != "U2"
        or ledger.get("request_sha256") != expected_request_sha256
    ):
        raise FoundationInputError(
            "persisted U2 retrieval ledger differs from its checkpoint"
        )

    action_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "u2-authority/retrieval-action.json",
    )
    admitted_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "u2-authority/admitted-host-result.json",
    )
    status = ledger.get("retrieval_status")
    if status == "not-applicable":
        if action_path.exists() or admitted_path.exists():
            raise FoundationInputError(
                "not-applicable U2 has unexpected host retrieval projection"
            )
        return {}, ledger
    if status != "required-complete":
        raise FoundationInputError("U3 cannot proceed from a blocked U2 retrieval")

    try:
        action_raw = action_path.read_bytes()
        action_document = load_json_object_bytes(
            action_raw,
            source=str(action_path),
        )
        if action_raw != canonical_json_bytes(action_document):
            raise ValueError("retrieval action is not canonical")
        action = _seal_action(layout, action_document)
    except Exception as error:
        raise FoundationInputError("persisted U2 retrieval action is invalid") from error
    action_payload = action.document.get("payload")
    decision = ledger.get("decision")
    decision_basis = (
        decision.get("eligibility_basis")
        if isinstance(decision, Mapping)
        else None
    )
    trigger_kinds = (
        decision_basis.get("trigger_kinds")
        if isinstance(decision_basis, Mapping)
        else None
    )
    expected_decision_projection = (
        {
            "status": decision.get("status"),
            "reason": decision.get("reason"),
            "decision_sha256": decision.get("decision_sha256"),
            "claim_sha256": decision.get("claim_sha256"),
            "basis_sha256": decision.get("basis_sha256"),
            "trigger_kinds": copy.deepcopy(trigger_kinds),
        }
        if isinstance(decision, Mapping)
        else None
    )
    authorization = (
        action_payload.get("authorization")
        if isinstance(action_payload, Mapping)
        else None
    )
    if (
        action.document.get("phase_id") != "U2"
        or action.document.get("action_kind") != "retrieval"
        or action.document.get("parent_event_sha256")
        != ledger.get("u1_parent_event_sha256")
        or action.document.get("request_sha256") != expected_request_sha256
        or action.document.get("result_relative_path")
        != "work/host/U02-retrieval-result.json"
        or not isinstance(action_payload, Mapping)
        or action_payload.get("decision") != expected_decision_projection
        or action_payload.get("queries") != ledger.get("queries")
        or not isinstance(authorization, Mapping)
        or authorization.get("status") != "authorized"
        or authorization.get("decision_sha256") != ledger.get("decision_sha256")
        or authorization.get("authorization_sha256")
        != ledger.get("authorization_sha256")
        or authorization.get("network_available") is not ledger.get("network_available")
        or authorization.get("outbound_authorized")
        is not ledger.get("outbound_authorized")
        or authorization.get("block_result") != ledger.get("block_result")
    ):
        raise FoundationInputError(
            "persisted U2 retrieval action differs from ledger authority"
        )

    accepted_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json",
    )
    try:
        accepted_raw = accepted_path.read_bytes()
        accepted = load_json_object_bytes(accepted_raw, source=str(accepted_path))
        if accepted_raw != canonical_json_bytes(accepted):
            raise ValueError("accepted retrieval receipt is not canonical")
        receipt = _seal_result(layout, action=action, receipt=accepted)
        result, result_raw = _load_bound_result_document(
            layout,
            action=action,
            receipt=receipt.document,
        )
    except Exception as error:
        raise FoundationInputError(
            "accepted U2 retrieval authority is invalid"
        ) from error
    if receipt.document.get("result_sha256") != sha256_bytes(result_raw):
        raise FoundationInputError("accepted U2 retrieval result hash differs")

    result_sources = result.get("sources")
    source_inventory = ledger.get("sources")
    if not isinstance(result_sources, list) or not result_sources:
        raise FoundationInputError("accepted U2 retrieval has no source inventory")
    if not isinstance(source_inventory, list) or not source_inventory:
        raise FoundationInputError("required U2 retrieval has no source inventory")
    record_fields = (
        "source_id",
        "url",
        "event_date",
        "publication_date",
        "interest",
        "upstream_lineage",
        "supported_claim",
        "cannot_prove",
    )
    result_by_id: dict[str, dict[str, object]] = {}
    projected_sources: list[dict[str, object]] = []
    for source in result_sources:
        if not isinstance(source, Mapping):
            raise FoundationInputError("accepted U2 retrieval source is invalid")
        source_id = source.get("source_id")
        content = source.get("content")
        query_sha256 = source.get("query_sha256")
        if (
            not isinstance(source_id, str)
            or not source_id
            or source_id in result_by_id
            or not isinstance(content, str)
            or not isinstance(query_sha256, str)
        ):
            raise FoundationInputError("accepted U2 retrieval source authority is invalid")
        try:
            record = retrieval.validate_source_record(
                {field: copy.deepcopy(source.get(field)) for field in record_fields}
            )
            external = retrieval.store_external_content(content)
        except Exception as error:
            raise FoundationInputError(
                "accepted U2 retrieval source authority is invalid"
            ) from error
        if source.get("content_sha256") != external["content_sha256"]:
            raise FoundationInputError("accepted U2 retrieval source content hash differs")
        result_by_id[source_id] = {
            "record": record,
            "query_sha256": query_sha256,
            "content_sha256": external["content_sha256"],
        }
        projected_sources.append(
            {
                "source_id": source_id,
                "query_sha256": query_sha256,
                "external_content": external,
            }
        )

    sources: dict[str, dict[str, object]] = {}
    for item in source_inventory:
        if not isinstance(item, Mapping):
            raise FoundationInputError("U2 retrieval source inventory entry is invalid")
        record = item.get("record")
        source_id = record.get("source_id") if isinstance(record, Mapping) else None
        accepted_source = result_by_id.get(str(source_id))
        if (
            not isinstance(source_id, str)
            or source_id in sources
            or accepted_source is None
            or record != accepted_source["record"]
            or item.get("query_sha256") != accepted_source["query_sha256"]
            or item.get("authorization_sha256") != ledger.get("authorization_sha256")
            or item.get("decision_sha256") != ledger.get("decision_sha256")
            or item.get("run_id") != ledger.get("run_id")
            or item.get("u1_parent_event_sha256")
            != ledger.get("u1_parent_event_sha256")
            or item.get("request_sha256") != ledger.get("request_sha256")
            or item.get("version_binding") != ledger.get("version_binding")
            or item.get("source_record_sha256")
            != sha256_bytes(canonical_json_bytes(dict(record)))
        ):
            raise FoundationInputError(
                "U2 retrieval source differs from accepted result authority"
            )
        inventory_payload = copy.deepcopy(dict(item))
        supplied_inventory_sha256 = inventory_payload.pop(
            "inventory_item_sha256",
            None,
        )
        if supplied_inventory_sha256 != sha256_bytes(
            canonical_json_bytes(inventory_payload)
        ):
            raise FoundationInputError("U2 retrieval source inventory hash differs")
        sources[source_id] = {
            "source_id": source_id,
            "record": copy.deepcopy(dict(record)),
            "content_sha256": str(accepted_source["content_sha256"]),
        }
    if set(sources) != set(result_by_id):
        raise FoundationInputError(
            "U2 retrieval source set differs from accepted result authority"
        )

    expected_projection: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.admitted-host-retrieval-result",
        "schema_version": 1,
        "action_sha256": action.action_sha256,
        "receipt_sha256": receipt.receipt_sha256,
        "provider": copy.deepcopy(dict(receipt.document["provider"])),
        "tool": copy.deepcopy(dict(receipt.document["tool"])),
        "sources": projected_sources,
    }
    expected_projection["content_sha256"] = sha256_bytes(
        canonical_json_bytes(expected_projection)
    )
    try:
        admitted_raw = admitted_path.read_bytes()
        admitted = load_json_object_bytes(admitted_raw, source=str(admitted_path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError(
            "U2 admitted host retrieval projection is unavailable"
        ) from error
    if (
        admitted_raw != canonical_json_bytes(admitted)
        or admitted_raw != canonical_json_bytes(expected_projection)
    ):
        raise FoundationInputError(
            "U2 admitted host retrieval projection differs from accepted result authority"
        )
    return sources, ledger


def _load_u2_admitted_sources(
    layout: RunLayout,
    *,
    phase_store: object | None = None,
    action: HostActionSeal | None = None,
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    """Reload the sealed U2 ledger and its host-admitted source content.

    U3 receives only this disk-derived map.  In-memory retrieval objects and
    caller-supplied source dictionaries are deliberately not accepted as
    authority.
    """

    if (phase_store is None) == (action is None):
        raise FoundationInputError(
            "U2 source reload requires one phase or action authority"
        )
    if action is not None:
        action_payload = action.document.get("payload")
        if (
            action.document.get("phase_id") != "U3"
            or action.document.get("action_kind") != "evidence-authoring"
            or not isinstance(action_payload, Mapping)
        ):
            raise FoundationInputError("U3 evidence action authority is invalid")
        expected_request_sha256 = action.document.get("request_sha256")
        output_hashes = [action_payload.get("u2_ledger_sha256")]
    else:
        events = getattr(phase_store, "events", ())
        if (
            not isinstance(events, tuple)
            or not events
            or events[-1].get("phase_id") != "U2"
        ):
            raise FoundationInputError("U3 requires a completed U2 phase event")
        event = events[-1]
        output_hashes = event.get("output_artifact_hashes")
        run_contract = getattr(phase_store, "run_contract", None)
        if not isinstance(run_contract, Mapping):
            raise FoundationInputError("U3 phase run contract is invalid")
        expected_request_sha256 = run_contract.get("request_sha256")
    if (
        not isinstance(output_hashes, list)
        or len(output_hashes) != 1
        or not isinstance(output_hashes[0], str)
    ):
        raise FoundationInputError("persisted U2 retrieval ledger differs from its checkpoint")
    return _load_validated_u2_source_projection(
        layout,
        expected_ledger_sha256=output_hashes[0],
        expected_request_sha256=expected_request_sha256,
    )


def _validate_host_evidence_result_for_acceptance(
    layout: RunLayout,
    *,
    action: HostActionSeal,
    result: HostResultSeal,
    result_document: Mapping[str, object] | None = None,
) -> None:
    from . import evidence

    if result_document is None:
        try:
            document, raw = _load_bound_result_document(
                layout,
                action=action,
                receipt=result.document,
            )
        except Exception as error:
            raise FoundationInputError(
                "U3 evidence authoring result is unavailable"
            ) from error
    else:
        document = copy.deepcopy(dict(result_document))
        raw = canonical_json_bytes(document)
    if raw != canonical_json_bytes(document):
        raise FoundationInputError(
            "U3 evidence authoring result is not canonical"
        )
    if result.document.get("result_sha256") != sha256_bytes(raw):
        raise FoundationInputError("U3 evidence authoring result hash differs")
    if set(document) != {"candidate_entries", "verified_subagent_candidates"}:
        raise FoundationInputError(
            "U3 evidence authoring result fields are not closed"
        )
    candidates = document.get("candidate_entries")
    subagent_candidates = document.get("verified_subagent_candidates")
    if (
        not isinstance(candidates, list)
        or not isinstance(subagent_candidates, list)
        or any(not isinstance(item, Mapping) for item in candidates)
        or any(not isinstance(item, Mapping) for item in subagent_candidates)
        or not candidates + subagent_candidates
    ):
        raise FoundationInputError("U3 evidence authoring candidates are invalid")
    payload = action.document.get("payload")
    if not isinstance(payload, Mapping):
        raise FoundationInputError("U3 evidence action payload is invalid")
    sources, _ = _load_u2_admitted_sources(layout, action=action)
    expected_sources = [
        {
            "source_id": source_id,
            "content_sha256": str(source["content_sha256"]),
        }
        for source_id, source in sorted(sources.items())
    ]
    if (
        payload.get("u2_ledger_sha256")
        != sha256_bytes(_u2_ledger_path(layout).read_bytes())
        or payload.get("request_sha256") != action.document.get("request_sha256")
        or payload.get("admitted_sources") != expected_sources
    ):
        raise FoundationInputError(
            "U3 evidence action differs from persisted U2 source authority"
        )
    authority = build_evidence_admission_authority(
        layout,
        admitted_sources=sources,
        evidence_cutoff=str(payload["evidence_cutoff"]),
    )
    for candidate in candidates:
        attribution = candidate.get("attribution")
        if (
            isinstance(attribution, Mapping)
            and attribution.get("origin_kind") == "subagent"
        ):
            raise FoundationInputError(
                "subagent candidates must use the verified candidate seam"
            )
    for candidate in subagent_candidates:
        attribution = candidate.get("attribution")
        if (
            not isinstance(attribution, Mapping)
            or attribution.get("origin_kind") != "subagent"
        ):
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


def _u3_action_path(layout: RunLayout) -> Path:
    return assert_safe_descendant(layout.root, layout.recovery_dir / U3_ACTION_RELATIVE_PATH)


def _persist_u3_action(layout: RunLayout, action: HostActionSeal) -> None:
    path = _u3_action_path(layout)
    document = copy.deepcopy(action.document)
    if path.exists():
        try:
            raw = path.read_bytes()
            existing = load_json_object_bytes(raw, source=str(path))
        except (OSError, TypeError, ValueError) as error:
            raise FoundationInputError("persisted U3 evidence action is unreadable") from error
        if raw != canonical_json_bytes(existing) or existing != document:
            raise FoundationInputError("persisted U3 evidence action changed")
        return
    atomic_write_json(path, document)


def _load_u3_action(layout: RunLayout) -> HostActionSeal | None:
    path = _u3_action_path(layout)
    if not path.exists():
        return None
    try:
        raw = path.read_bytes()
        document = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError("persisted U3 evidence action is unreadable") from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError("persisted U3 evidence action is not canonical")
    try:
        action = _seal_action(layout, document)
    except Exception as error:
        raise FoundationInputError("persisted U3 evidence action is invalid") from error
    if (
        action.document.get("phase_id") != "U3"
        or action.document.get("action_kind") != "evidence-authoring"
        or action.document.get("result_relative_path") != U3_RESULT_RELATIVE_PATH
    ):
        raise FoundationInputError("persisted U3 evidence action authority differs")
    return action


def _load_accepted_host_result(
    layout: RunLayout,
    action: HostActionSeal,
) -> HostResultSeal | None:
    accepted_path = assert_safe_descendant(
        layout.root,
        layout.recovery_dir / "host-results" / action.action_sha256 / "accepted.json",
    )
    if not accepted_path.exists():
        return None
    try:
        raw = accepted_path.read_bytes()
        document = load_json_object_bytes(raw, source=str(accepted_path))
        if raw != canonical_json_bytes(document):
            raise ValueError("accepted host result is not canonical")
        return _seal_result(layout, action=action, receipt=document)
    except Exception as error:
        if isinstance(error, FoundationInputError):
            raise
        raise FoundationInputError("accepted U3 evidence result is invalid") from error


def _issue_u3_evidence_action(
    layout: RunLayout,
    *,
    phase_store: object,
    profile: RequestProfile,
    sources: Mapping[str, Mapping[str, object]],
    ledger: Mapping[str, object],
    now: datetime,
) -> HostActionSeal:
    events = getattr(phase_store, "events", ())
    if not isinstance(events, tuple) or not events or events[-1].get("phase_id") != "U2":
        raise FoundationInputError("U3 evidence action requires a completed U2 event")
    parent_event_sha256 = str(events[-1]["event_sha256"])
    ledger_path = _u2_ledger_path(layout)
    payload = _u3_evidence_payload(
        layout,
        phase_store=phase_store,
        profile=profile,
        sources=sources,
        ledger=ledger,
        parent_event_sha256=parent_event_sha256,
    )
    action = issue_host_action(
        layout,
        action_kind="evidence-authoring",
        phase_id="U3",
        parent_event_sha256=parent_event_sha256,
        request_sha256=str(phase_store.run_contract["request_sha256"]),
        payload=payload,
        result_relative_path=U3_RESULT_RELATIVE_PATH,
        now=now,
    )
    _persist_u3_action(layout, action)
    return action


def _u3_evidence_payload(
    layout: RunLayout,
    *,
    phase_store: object,
    profile: RequestProfile,
    sources: Mapping[str, Mapping[str, object]],
    ledger: Mapping[str, object],
    parent_event_sha256: str,
) -> dict[str, object]:
    ledger_path = _u2_ledger_path(layout)
    return {
        "u2_ledger_sha256": sha256_bytes(ledger_path.read_bytes()),
        "u2_event_sha256": parent_event_sha256,
        "request_sha256": str(phase_store.run_contract["request_sha256"]),
        "evidence_cutoff": phase_store.evidence_cutoff,
        "admitted_sources": [
            {
                "source_id": source_id,
                "content_sha256": str(source["content_sha256"]),
            }
            for source_id, source in sorted(sources.items())
        ],
        "material_inventory": [copy.deepcopy(dict(item)) for item in profile.material_inventory],
        "requested_result_fields": [
            "candidate_entries",
            "verified_subagent_candidates",
        ],
    }


def _complete_u3_from_host_result(
    layout: RunLayout,
    *,
    phase_store: object,
    profile: RequestProfile,
    action: HostActionSeal,
    result: HostResultSeal,
    sources: Mapping[str, Mapping[str, object]],
    now: datetime,
    lease: object | None = None,
):
    try:
        document, raw = _load_bound_result_document(
            layout,
            action=action,
            receipt=result.document,
        )
    except Exception as error:
        raise FoundationInputError("U3 evidence authoring result is unavailable") from error
    if raw != canonical_json_bytes(document):
        raise FoundationInputError("U3 evidence authoring result is not canonical")
    if set(document) != {"candidate_entries", "verified_subagent_candidates"}:
        raise FoundationInputError("U3 evidence authoring result fields are not closed")
    candidates = document["candidate_entries"]
    subagent_candidates = document["verified_subagent_candidates"]
    if (
        not isinstance(candidates, list)
        or not isinstance(subagent_candidates, list)
        or any(not isinstance(item, Mapping) for item in candidates)
        or any(not isinstance(item, Mapping) for item in subagent_candidates)
    ):
        raise FoundationInputError("U3 evidence authoring candidates are invalid")
    authority = build_evidence_admission_authority(
        layout,
        admitted_sources=sources,
        evidence_cutoff=phase_store.evidence_cutoff,
    )
    return complete_u3_evidence(
        layout,
        phase_store=phase_store,
        authority=authority,
        candidate_entries=tuple(candidates),
        verified_subagent_candidates=tuple(subagent_candidates),
        now=now,
        lease=lease,
    )


def _advance_u3(
    layout: RunLayout,
    *,
    phase_store: object,
    profile: RequestProfile,
    now: datetime,
    lease: object | None = None,
) -> FoundationProgress:
    if getattr(phase_store, "current_phase", None) != "U2":
        raise FoundationInputError("U3 requires a completed U2 boundary")
    sources, ledger = _load_u2_admitted_sources(layout, phase_store=phase_store)
    events = getattr(phase_store, "events", ())
    if not isinstance(events, tuple) or not events:
        raise FoundationInputError("U3 parent event authority is unavailable")
    parent_event_sha256 = str(events[-1].get("event_sha256"))
    expected_payload = _u3_evidence_payload(
        layout,
        phase_store=phase_store,
        profile=profile,
        sources=sources,
        ledger=ledger,
        parent_event_sha256=parent_event_sha256,
    )
    action = _load_u3_action(layout)
    pending = load_pending_action(layout)
    if action is None:
        if pending is not None:
            if (
                pending.document.get("phase_id") != "U3"
                or pending.document.get("action_kind") != "evidence-authoring"
            ):
                raise FoundationInputError("pending host action differs from U3 authority")
            action = pending
            _persist_u3_action(layout, action)
        else:
            action = _issue_u3_evidence_action(
                layout,
                phase_store=phase_store,
                profile=profile,
                sources=sources,
                ledger=ledger,
                now=now,
            )
            pending = action
    if (
        action.document.get("run_id") != layout.run_dir.name
        or action.document.get("version_binding") != current_version_binding()
        or action.document.get("phase_id") != "U3"
        or action.document.get("action_kind") != "evidence-authoring"
        or action.document.get("parent_event_sha256") != parent_event_sha256
        or action.document.get("request_sha256") != phase_store.run_contract.get("request_sha256")
        or action.document.get("result_relative_path") != U3_RESULT_RELATIVE_PATH
        or action.document.get("payload") != expected_payload
    ):
        raise FoundationInputError("U3 evidence action differs from the sealed U2 authority")
    if pending is not None and pending != action:
        raise FoundationInputError("pending host action differs from U3 authority")
    accepted = _load_accepted_host_result(layout, action)
    if accepted is None:
        if pending is None:
            raise FoundationInputError(
                "persisted U3 evidence action has no pending dispatch or accepted result"
            )
        return FoundationProgress("awaiting-host-action", phase_store, action, None)
    _complete_u3_from_host_result(
        layout,
        phase_store=phase_store,
        profile=profile,
        action=action,
        result=accepted,
        sources=sources,
        now=now,
        lease=lease,
    )
    return FoundationProgress("advanced", phase_store, None, "U3")


def advance_u2(
    layout: RunLayout,
    *,
    phase_store: object,
    analysis_kind: str | None = None,
    claim: str,
    trigger_kinds: Sequence[str],
    material_inventory: Sequence[Mapping[str, object]] | None = None,
    material_universe_sha256: str | None = None,
    now: datetime,
    lease: object | None = None,
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
        analysis_kind=analysis_kind,
        trigger_kinds=trigger_kinds,
        generated_at=_canonical_utc(now),
        material_inventory=material_inventory,
        material_universe_sha256=material_universe_sha256,
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
            analysis_kind=analysis_kind,
            trigger_kinds=trigger_kinds,
            material_inventory=material_inventory,
            material_universe_sha256=material_universe_sha256,
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
        from . import recovery

        recovery.create_checkpoint(
            layout,
            phase_store,
            boundary_kind="phase",
            boundary_id="U2",
            boundary_ordinal=0,
            artifact_paths=(_u2_ledger_path(layout),),
            now=now,
            lease=lease,
        )
        return FoundationProgress("advanced", phase_store, None, "U2")
    if not isinstance(disposition, Mapping):
        raise FoundationInputError("U2 retrieval disposition is invalid")
    decision = retrieval.assess_retrieval_eligibility(
        claim,
        phase_store=phase_store,
        analysis_kind=analysis_kind,
        trigger_kinds=trigger_kinds,
        material_inventory=material_inventory,
        material_universe_sha256=material_universe_sha256,
    )
    authorization = retrieval.gate_retrieval(
        decision,
        phase_store=phase_store,
    )
    if decision.status == "not-applicable":
        if authorization is not decision:
            raise FoundationInputError(
                "not-applicable U2 disposition changed its decision authority"
            )
        expected_authorization_sha256 = None
    elif isinstance(authorization, retrieval.RetrievalAuthorization):
        expected_authorization_sha256 = authorization.authorization_sha256
    else:
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
        expected_authorization_sha256=expected_authorization_sha256,
    )
    _persist_u2_ledger(layout, disposition)
    if seal.completion_authorized:
        phase_store.complete(
            "U2",
            artifact_hashes=(seal.artifact_sha256,),
            retrieval_authority=seal,
        )
        from . import recovery

        recovery.create_checkpoint(
            layout,
            phase_store,
            boundary_kind="phase",
            boundary_id="U2",
            boundary_ordinal=0,
            artifact_paths=(_u2_ledger_path(layout),),
            now=now,
            lease=lease,
        )
        return FoundationProgress("advanced", phase_store, None, "U2")
    if seal.retrieval_status != "required-blocked":
        raise FoundationInputError("blocked U2 disposition has an invalid completion state")
    return FoundationProgress("blocked", phase_store, None, None)


__all__ = (
    "EVIDENCE_LINEAGE_RELATIVE_PATH",
    "EVIDENCE_LINEAGE_REQUEST_RELATIVE_PATH",
    "FoundationInputError",
    "FoundationProgress",
    "HostCapabilitySeal",
    "RequestProfile",
    "U3_ACTION_RELATIVE_PATH",
    "U3_RESULT_RELATIVE_PATH",
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
    "validate_evidence_lineage_admission",
    "verify_host_capability_seal",
)
