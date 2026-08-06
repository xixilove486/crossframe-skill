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


__all__ = (
    "FoundationInputError",
    "FoundationProgress",
    "HostCapabilitySeal",
    "RequestProfile",
    "advance_u0",
    "load_input_inventory",
    "load_host_capability_attestation",
    "load_request_profile",
    "parse_request_profile",
    "seal_input_inventory",
    "validate_host_capability_attestation",
    "validate_closed_input_profile",
    "verify_host_capability_seal",
)
