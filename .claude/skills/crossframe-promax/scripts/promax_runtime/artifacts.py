from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
from typing import Iterable, Mapping, Sequence

from .errors import RunBindingError
from .jsonio import sha256_json
from .paths import validate_relative_artifact_path
from .pollution import platform_selected_promax_route
from .schemas import validate_instance
from .source_integrity import V8_SOURCE_SNAPSHOT_SHA256, build_source_snapshot
from .state_machine import PHASES, RunBinding


ROLE_IDS = (
    "v8_source_concept_auditor",
    "external_case_researcher",
    "counterexample_auditor",
    "position_adjudicator",
    "longform_writer",
)
CANONICAL_VALIDATOR_IDS = (
    "schema",
    "source-integrity",
    "version-isolation",
    "concept-closure",
    "claim-path",
    "retrieval",
    "position",
    "output",
    "manifest",
    "state-machine",
    "continuation",
)
_ROLE_INPUT_MAX_PHASE = ("P3", "P5", "P6", "P7", "P9")
_ROLE_OUTPUT_PHASE = ("P4", "P6", "P7", "P8", "P10")
ALLOWED_MODES = (
    "promax-artifact-run",
    "promax-complete",
    "promax-design-review",
    "promax-blocked/progress",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
def _bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be a boolean")
    return value


def build_capability_disclosure(
    *,
    subagents_available: bool,
    max_parallelism: int,
    validator_ids: Iterable[str] = CANONICAL_VALIDATOR_IDS,
    files_available: bool = True,
    files_readable: bool = True,
    files_writable: bool = True,
    network_available: bool = True,
    live_retrieval: bool = True,
    validators_available: bool = True,
    validators_executable: bool = True,
) -> dict[str, object]:
    files_available = _bool(files_available, field="files_available")
    files_readable = _bool(files_readable, field="files_readable")
    files_writable = _bool(files_writable, field="files_writable")
    network_available = _bool(network_available, field="network_available")
    live_retrieval = _bool(live_retrieval, field="live_retrieval")
    subagents_available = _bool(
        subagents_available, field="subagents_available"
    )
    validators_available = _bool(
        validators_available, field="validators_available"
    )
    validators_executable = _bool(
        validators_executable, field="validators_executable"
    )
    if type(max_parallelism) is not int or max_parallelism < 0:
        raise ValueError("max_parallelism must be a non-negative integer")
    if not files_available:
        files_readable = False
        files_writable = False
    if not network_available:
        live_retrieval = False
    if subagents_available:
        if max_parallelism < 1:
            raise ValueError(
                "available subagents require max_parallelism of at least one"
            )
    elif max_parallelism != 0:
        raise ValueError("unavailable subagents require max_parallelism zero")
    if isinstance(validator_ids, (str, bytes)):
        raise ValueError("validator_ids must be an iterable of identifiers, not text")
    validator_names = tuple(validator_ids)
    if any(not isinstance(item, str) or not item.strip() for item in validator_names):
        raise ValueError("validator_ids must contain non-empty strings")
    validator_names = tuple(item.strip() for item in validator_names)
    if len(set(validator_names)) != len(validator_names):
        raise ValueError("validator_ids must be unique after normalization")
    if validators_available:
        if not validators_executable or not validator_names:
            raise ValueError(
                "available validators must be executable and identify their set"
            )
    else:
        validators_executable = False
        validator_names = ()

    file_limitations: list[str] = []
    if not files_available:
        file_limitations.append("file access unavailable")
    else:
        if not files_readable:
            file_limitations.append("file reads unavailable")
        if not files_writable:
            file_limitations.append("file writes unavailable")

    return {
        "files": {
            "available": files_available,
            "readable": files_readable,
            "writable": files_writable,
            "limitations": file_limitations,
        },
        "network": {
            "available": network_available,
            "live_retrieval": live_retrieval,
            "limitations": [] if network_available else ["network unavailable"],
        },
        "subagents": {
            "available": subagents_available,
            "isolated_roles": subagents_available,
            "max_parallelism": max_parallelism,
            "limitations": (
                [] if subagents_available else ["subagent API unavailable"]
            ),
        },
        "validators": {
            "available": validators_available,
            "executable": validators_executable,
            "validator_ids": list(validator_names),
            "limitations": (
                [] if validators_available else ["validator execution unavailable"]
            ),
        },
    }


def build_role_plan(capabilities: Mapping[str, object]) -> list[dict[str, object]]:
    if not isinstance(capabilities, Mapping):
        raise ValueError("capabilities must be a structured object")
    subagents = capabilities.get("subagents")
    if not isinstance(subagents, Mapping):
        raise ValueError("capabilities.subagents must be a structured object")
    available = subagents.get("available")
    isolated = subagents.get("isolated_roles")
    parallelism = subagents.get("max_parallelism")
    if type(available) is not bool or type(isolated) is not bool:
        raise ValueError("subagent availability and role isolation must be booleans")
    if type(parallelism) is not int:
        raise ValueError("subagent max_parallelism must be an integer")
    if available:
        if isolated is not True or parallelism < 1:
            raise ValueError(
                "multi-agent mode requires isolated roles and positive parallelism"
            )
        execution_mode = "multi-agent-isolated"
    else:
        if isolated is not False or parallelism != 0:
            raise ValueError(
                "single-agent separation cannot claim isolated subagent execution"
            )
        execution_mode = "single-agent-separated"
    return [
        {
            "role_id": role_id,
            "sequence": sequence,
            "execution_mode": execution_mode,
            "exchange_protocol": "structured-artifacts-only",
        }
        for sequence, role_id in enumerate(ROLE_IDS, start=1)
    ]


def _capability_section(
    capabilities: Mapping[str, object], name: str
) -> Mapping[str, object]:
    section = capabilities.get(name)
    if not isinstance(section, Mapping):
        raise ValueError(f"capabilities.{name} must be a structured object")
    return section


def _validate_mode_capabilities(
    mode: str,
    blocker: Mapping[str, object] | None,
    capabilities: Mapping[str, object],
) -> None:
    files = _capability_section(capabilities, "files")
    _capability_section(capabilities, "network")
    validators = _capability_section(capabilities, "validators")
    if mode != "promax-blocked/progress":
        if not (
            files.get("available") is True
            and files.get("readable") is True
            and files.get("writable") is True
            and validators.get("available") is True
            and validators.get("executable") is True
        ):
            raise ValueError(
                "an artifact run with missing file or validator capabilities must use "
                "promax-blocked/progress"
            )
        return
    assert blocker is not None
    category = blocker.get("category")
    if category == "filesystem_unwritable" and files.get("writable") is not False:
        raise ValueError("filesystem_unwritable requires writable=false disclosure")
    if category == "required_tool_forbidden":
        has_required_limitation = (
            files.get("available") is False
            or files.get("readable") is False
            or files.get("writable") is False
            or validators.get("available") is False
            or validators.get("executable") is False
        )
        if not has_required_limitation:
            raise ValueError(
                "required_tool_forbidden requires a matching capability limitation"
            )


def initialize_run(
    repo: Path | str,
    request_text: str,
    *,
    mode: str,
    capabilities: Mapping[str, object],
    created_at: str,
    run_id: str | None = None,
    blocker: Mapping[str, object] | None = None,
    recommendation_required: bool = False,
) -> dict[str, dict[str, object]]:
    route = platform_selected_promax_route()
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported ProMax mode: {mode!r}")
    if type(recommendation_required) is not bool:
        raise ValueError("recommendation_required must be a real boolean")
    allowed_blockers = {
        "source_unavailable",
        "filesystem_unwritable",
        "required_tool_forbidden",
        "user_stopped",
        "safety_boundary",
    }
    if mode == "promax-blocked/progress":
        if not isinstance(blocker, Mapping) or set(blocker) != {
            "category",
            "detail",
        }:
            raise ValueError(
                "promax-blocked/progress requires one closed structured blocker"
            )
        if blocker.get("category") not in allowed_blockers:
            raise ValueError("blocked mode uses an unauthorized blocker category")
        if not isinstance(blocker.get("detail"), str) or not blocker["detail"].strip():
            raise ValueError("blocked mode requires a non-empty blocker detail")
        normalized_blocker: dict[str, object] | None = {
            "category": blocker["category"],
            "detail": blocker["detail"].strip(),
        }
    else:
        if blocker is not None:
            raise ValueError("a blocker is forbidden outside promax-blocked/progress")
        normalized_blocker = None
    _validate_mode_capabilities(mode, normalized_blocker, capabilities)
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("created_at must be a non-empty timestamp")
    role_plan = build_role_plan(capabilities)
    execution_mode = role_plan[0]["execution_mode"]
    nonce = secrets.token_hex(32)
    effective_run_id = run_id or f"promax-run-{secrets.token_hex(8)}"
    request_sha256 = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
    binding = RunBinding(
        run_id=effective_run_id,
        run_nonce=nonce,
        request_sha256=request_sha256,
        source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
    )
    contract: dict[str, object] = {
        "schema_id": "crossframe.promax.v8.run-contract",
        "schema_version": 1,
        "framework_version": "v8.0",
        "run_id": binding.run_id,
        "run_nonce": binding.run_nonce,
        "request_sha256": binding.request_sha256,
        "source_snapshot_sha256": binding.source_snapshot_sha256,
        "mode": mode,
        "recommendation_required": recommendation_required,
        "blocker": normalized_blocker,
        **route,
        "capabilities": copy.deepcopy(dict(capabilities)),
        "orchestration_mode": execution_mode,
        "role_plan": role_plan,
        "budgets": {
            "paragraphs": 3863,
            "tables": 117,
            "registry_concepts": 709,
            "minimum_red_team_rounds": 2,
            "minimum_no_novelty_rounds": 2,
        },
        "completion_criteria": [
            "source-closure",
            "concept-closure",
            "claim-path-closure",
            "retrieval-and-counterexample-closure",
            "position-lock",
            "output-and-validator-closure",
        ],
        "created_at": created_at.strip(),
    }
    validate_instance("promax-run-contract.schema.json", contract)
    source_blocked = (
        normalized_blocker is not None
        and normalized_blocker.get("category") == "source_unavailable"
    )
    files = _capability_section(capabilities, "files")
    snapshot: dict[str, object] | None = None
    if source_blocked and files.get("readable") is False:
        pass
    else:
        try:
            snapshot = build_source_snapshot(repo, verified_at=created_at)
        except (OSError, RuntimeError, ValueError):
            if not source_blocked:
                raise
        else:
            if source_blocked:
                raise ValueError(
                    "source_unavailable cannot be declared when the v8 source verifies"
                )
    initialized: dict[str, dict[str, object]] = {"run_contract": contract}
    if snapshot is not None:
        initialized["source_snapshot"] = snapshot
    return initialized


def _require_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be one lowercase SHA-256 digest")
    return value


def _safe_relative_path(value: object) -> str:
    try:
        return validate_relative_artifact_path(value)
    except ValueError as error:
        raise ValueError(f"invalid artifact path {value!r}: {error}") from error


def _media_type(path: str) -> str:
    suffix = PurePosixPath(path).suffix.casefold()
    return {
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".md": "text/markdown",
        ".txt": "text/plain",
    }.get(suffix, "application/octet-stream")


def _validate_artifact_ref(
    value: object,
    *,
    field: str,
    known_artifacts: Mapping[str, str],
) -> tuple[str, str, str]:
    if not isinstance(value, Mapping) or set(value) != {
        "path",
        "sha256",
        "media_type",
    }:
        raise ValueError(f"{field} must be a closed structured artifact reference")
    path = _safe_relative_path(value["path"])
    digest = _require_sha256(value["sha256"], field=f"{field}.sha256")
    media_type = value["media_type"]
    if not isinstance(media_type, str) or "/" not in media_type:
        raise ValueError(f"{field}.media_type must be an explicit media type")
    if media_type != _media_type(path):
        raise ValueError(
            f"{field}.media_type does not match the artifact path: {path}"
        )
    if known_artifacts.get(path) != digest:
        raise ValueError(f"{field} is not bound to current artifact bytes: {path}")
    return path, digest, media_type


def _validate_attestation_artifact_ref(
    value: object,
    *,
    field: str,
) -> tuple[str, str, str]:
    if not isinstance(value, Mapping) or set(value) != {
        "path",
        "sha256",
        "media_type",
    }:
        raise ValueError(f"{field} must be a closed structured artifact reference")
    path = _safe_relative_path(value["path"])
    digest = _require_sha256(value["sha256"], field=f"{field}.sha256")
    media_type = value["media_type"]
    if media_type != _media_type(path):
        raise ValueError(f"{field}.media_type does not match the artifact path: {path}")
    return path, digest, str(media_type)


def validate_role_records(
    run_contract: Mapping[str, object],
    role_records: Sequence[Mapping[str, object]],
    known_artifacts: Mapping[str, str],
    *,
    artifact_records: Sequence[Mapping[str, object]] | None = None,
) -> list[dict[str, object]]:
    known_casefold: dict[str, str] = {}
    for raw_path, digest in known_artifacts.items():
        path = _safe_relative_path(raw_path)
        _require_sha256(digest, field=f"known_artifacts[{path}]")
        folded = path.casefold()
        if folded in known_casefold and known_casefold[folded] != path:
            raise ValueError(
                f"known artifact map contains a casefold path alias: {path}"
            )
        known_casefold[folded] = path
    artifact_details: dict[str, Mapping[str, object]] | None = None
    if artifact_records is not None:
        if not isinstance(artifact_records, Sequence) or isinstance(
            artifact_records, (str, bytes)
        ):
            raise ValueError("artifact_records must be a structured sequence")
        artifact_details = {}
        for artifact_index, raw_artifact in enumerate(artifact_records):
            if not isinstance(raw_artifact, Mapping):
                raise ValueError(f"artifact record {artifact_index} must be an object")
            artifact_path = _safe_relative_path(raw_artifact.get("path"))
            if raw_artifact.get("status") != "current":
                continue
            if artifact_path in artifact_details:
                raise ValueError(f"duplicate current artifact metadata: {artifact_path}")
            artifact_details[artifact_path] = raw_artifact
    plan = run_contract.get("role_plan")
    if not isinstance(plan, list) or len(plan) != len(ROLE_IDS):
        raise ValueError("run contract does not contain the five-role plan")
    if not isinstance(role_records, Sequence) or isinstance(
        role_records, (str, bytes)
    ):
        raise ValueError("role_records must be an ordered structured sequence")
    if len(role_records) != len(plan):
        raise ValueError("all five planned role records are required")
    normalized: list[dict[str, object]] = []
    output_owners: dict[str, int] = {}
    base_expected_keys = {
        "role_id",
        "sequence",
        "execution_mode",
        "exchange_protocol",
        "input_artifacts",
        "observed_input_artifacts",
        "output_artifacts",
        "status",
    }
    for owner_index, raw_record in enumerate(role_records, start=1):
        if not isinstance(raw_record, Mapping):
            raise ValueError(f"role record {owner_index} must be a structured object")
        outputs = raw_record.get("output_artifacts")
        if not isinstance(outputs, list) or not outputs:
            raise ValueError(f"role record {owner_index}.output_artifacts cannot be empty")
        for value in outputs:
            output_path, _, _ = _validate_artifact_ref(
                value,
                field=f"role_records[{owner_index - 1}].output_artifacts",
                known_artifacts=known_artifacts,
            )
            folded_output = output_path.casefold()
            if folded_output in output_owners:
                raise ValueError(
                    f"role records {output_owners[folded_output]} and {owner_index} "
                    f"claim the same output artifact: {output_path}"
                )
            output_owners[folded_output] = owner_index

    multi_agent_ids: list[str] = []
    for index, (planned, raw_record) in enumerate(
        zip(plan, role_records), start=1
    ):
        if not isinstance(planned, Mapping) or not isinstance(raw_record, Mapping):
            raise ValueError(f"role record {index} must be a structured object")
        record = copy.deepcopy(dict(raw_record))
        expected_keys = set(base_expected_keys)
        if planned.get("execution_mode") == "multi-agent-isolated":
            expected_keys.update({"agent_id", "execution_attestation"})
        if set(record) != expected_keys:
            raise ValueError(f"role record {index} has an open or incomplete shape")
        for key in (
            "role_id",
            "sequence",
            "execution_mode",
            "exchange_protocol",
        ):
            if record.get(key) != planned.get(key):
                raise ValueError(f"role record {index} does not match its frozen plan")
        if record["exchange_protocol"] != "structured-artifacts-only":
            raise ValueError("roles may exchange structured artifacts only")
        if record["status"] not in {"completed", "blocked", "invalidated"}:
            raise ValueError(f"role record {index} has an invalid status")
        if run_contract.get("mode") == "promax-complete" and record["status"] != "completed":
            raise ValueError("promax-complete requires all five roles to complete")
        if planned.get("execution_mode") == "multi-agent-isolated":
            agent_id = record.get("agent_id")
            if not isinstance(agent_id, str) or len(agent_id.strip()) < 3:
                raise ValueError(f"role record {index} lacks a stable agent identity")
            normalized_agent_id = agent_id.strip()
            multi_agent_ids.append(normalized_agent_id)
            attestation = record.get("execution_attestation")
            expected_attestation_keys = {
                "run_id",
                "request_sha256",
                "source_snapshot_sha256",
                "completed_at",
                "observed_input_artifacts",
                "produced_output_artifacts",
                "claim_sha256",
            }
            if not isinstance(attestation, Mapping) or set(attestation) != expected_attestation_keys:
                raise ValueError(f"role record {index} execution attestation is incomplete")
            for field in ("run_id", "request_sha256", "source_snapshot_sha256"):
                if attestation.get(field) != run_contract.get(field):
                    raise ValueError(
                        f"role record {index} execution attestation changes {field}"
                    )
            completed_at = attestation.get("completed_at")
            if not isinstance(completed_at, str) or not completed_at.strip():
                raise ValueError(f"role record {index} lacks an attested completion time")
            attested_refs: dict[str, list[dict[str, object]]] = {}
            for field in ("observed_input_artifacts", "produced_output_artifacts"):
                values = attestation.get(field)
                if not isinstance(values, list) or len(values) != 1:
                    raise ValueError(f"role record {index}.{field} must contain one artifact")
                path, digest, media_type = _validate_attestation_artifact_ref(
                    values[0],
                    field=f"role_records[{index - 1}].execution_attestation.{field}[0]",
                )
                if path in known_artifacts and known_artifacts[path] != digest:
                    raise ValueError(
                        f"role record {index} execution attestation does not bind "
                        f"published artifact bytes: {path}"
                    )
                attested_refs[field] = [
                    {"path": path, "sha256": digest, "media_type": media_type}
                ]
            claim = {
                "run_id": run_contract["run_id"],
                "request_sha256": run_contract["request_sha256"],
                "source_snapshot_sha256": run_contract["source_snapshot_sha256"],
                "role_id": record["role_id"],
                "sequence": record["sequence"],
                "agent_id": normalized_agent_id,
                "completed_at": completed_at.strip(),
                "observed_input_artifacts": attested_refs["observed_input_artifacts"],
                "produced_output_artifacts": attested_refs["produced_output_artifacts"],
            }
            if attestation.get("claim_sha256") != sha256_json(claim):
                raise ValueError(f"role record {index} execution claim hash mismatch")

        parsed: dict[str, list[tuple[str, str, str]]] = {}
        for field in (
            "input_artifacts",
            "observed_input_artifacts",
            "output_artifacts",
        ):
            values = record[field]
            if not isinstance(values, list):
                raise ValueError(f"role record {index}.{field} must be an array")
            if field != "observed_input_artifacts" and not values:
                raise ValueError(f"role record {index}.{field} cannot be empty")
            refs = [
                _validate_artifact_ref(
                    value,
                    field=f"role_records[{index - 1}].{field}",
                    known_artifacts=known_artifacts,
                )
                for value in values
            ]
            if len(set(refs)) != len(refs) or len(
                {path.casefold() for path, _, _ in refs}
            ) != len(refs):
                raise ValueError(f"role record {index}.{field} contains duplicates")
            parsed[field] = refs
        declared = {(path, digest) for path, digest, _ in parsed["input_artifacts"]}
        observed = {
            (path, digest) for path, digest, _ in parsed["observed_input_artifacts"]
        }
        outputs = {
            (path, digest) for path, digest, _ in parsed["output_artifacts"]
        }
        if not observed.issubset(declared):
            raise ValueError(
                f"role record {index} observed an artifact not declared in its input set"
            )
        if declared & outputs:
            raise ValueError(
                f"role record {index} cannot read its own not-yet-produced output"
            )
        for input_path, _, _ in parsed["input_artifacts"]:
            owner = output_owners.get(input_path.casefold())
            if owner is not None and owner >= index:
                raise ValueError(
                    f"role record {index} cannot read role {owner}'s current or future output"
                )
        if artifact_details is not None:
            maximum_input_phase = _ROLE_INPUT_MAX_PHASE[index - 1]
            maximum_input_index = PHASES.index(maximum_input_phase)
            for input_path, _, _ in parsed["input_artifacts"]:
                details = artifact_details.get(input_path)
                phase = details.get("generating_phase") if details is not None else None
                if phase not in PHASES or PHASES.index(phase) > maximum_input_index:
                    raise ValueError(
                        f"role record {index} input lacks a prior producer before "
                        f"{maximum_input_phase}: {input_path}"
                    )
            observed_hashes = {
                digest for _, digest, _ in parsed["observed_input_artifacts"]
            }
            if record["status"] == "completed" and not observed_hashes:
                raise ValueError(f"completed role record {index} must observe an input")
            expected_output_phase = _ROLE_OUTPUT_PHASE[index - 1]
            for output_path, _, _ in parsed["output_artifacts"]:
                details = artifact_details.get(output_path)
                if details is None or details.get("generating_phase") != expected_output_phase:
                    raise ValueError(
                        f"role record {index} output must be generated in "
                        f"{expected_output_phase}: {output_path}"
                    )
                lineage = details.get("input_artifact_sha256s")
                if not isinstance(lineage, list) or set(lineage) != observed_hashes:
                    raise ValueError(
                        f"role record {index} output lineage must equal its observed inputs"
                    )
        normalized.append(record)
    if multi_agent_ids and len(set(multi_agent_ids)) != len(multi_agent_ids):
        raise ValueError("multi-agent role records require unique agent identities")
    return normalized


def _hash_inventory_file(root: Path, target: Path, path: str) -> str:
    try:
        resolved_before = target.resolve(strict=True)
        resolved_before.relative_to(root)
        before_path_stat = target.stat()
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError(f"artifact does not resolve inside the run directory: {path}") from error
    if target.is_symlink() or not stat.S_ISREG(before_path_stat.st_mode):
        raise ValueError(f"artifact must be a regular non-symlink file: {path}")
    if before_path_stat.st_nlink != 1:
        raise ValueError(f"artifact must not be a hard-linked file: {path}")

    digest = hashlib.sha256()
    try:
        with target.open("rb") as handle:
            opened_stat = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened_stat.st_mode) or opened_stat.st_nlink != 1:
                raise ValueError(f"artifact must remain one regular unlinked file: {path}")
            resolved_open = target.resolve(strict=True)
            resolved_open.relative_to(root)
            current_path_stat = target.stat()
            if target.is_symlink() or not os.path.samestat(opened_stat, current_path_stat):
                raise ValueError(f"artifact changed while it was opened: {path}")
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
            closed_over_stat = os.fstat(handle.fileno())
            if (
                not os.path.samestat(opened_stat, closed_over_stat)
                or closed_over_stat.st_nlink != 1
                or closed_over_stat.st_size != opened_stat.st_size
                or closed_over_stat.st_mtime_ns != opened_stat.st_mtime_ns
            ):
                raise ValueError(f"artifact changed while it was read: {path}")
            resolved_after = target.resolve(strict=True)
            resolved_after.relative_to(root)
            final_path_stat = target.stat()
            if target.is_symlink() or not os.path.samestat(closed_over_stat, final_path_stat):
                raise ValueError(f"artifact path changed while it was read: {path}")
    except ValueError:
        raise
    except (OSError, RuntimeError) as error:
        raise ValueError(f"cannot safely read artifact: {path}") from error
    return digest.hexdigest()


def inventory_artifacts(
    run_dir: Path | str,
    metadata: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    root = Path(run_dir).resolve()
    if not isinstance(metadata, Mapping) or not metadata:
        raise ValueError("artifact metadata must be a non-empty mapping")
    inventory: list[dict[str, object]] = []
    casefold_paths: dict[str, str] = {}
    for raw_path in sorted(metadata):
        path = _safe_relative_path(raw_path)
        folded = path.casefold()
        if folded in casefold_paths:
            raise ValueError(
                f"artifact metadata contains a casefold path alias: "
                f"{casefold_paths[folded]!r} and {path!r}"
            )
        casefold_paths[folded] = path
        details = metadata[raw_path]
        if not isinstance(details, Mapping) or set(details) != {
            "generating_phase",
            "input_artifact_sha256s",
            "status",
        }:
            raise ValueError(f"artifact metadata has a non-closed shape: {path}")
        phase = details["generating_phase"]
        if phase not in PHASES:
            raise ValueError(f"artifact {path} has an unknown generating phase")
        inputs = details["input_artifact_sha256s"]
        if not isinstance(inputs, list):
            raise ValueError(f"artifact {path} input hashes must be an array")
        normalized_inputs = [
            _require_sha256(value, field=f"{path}.input_artifact_sha256s")
            for value in inputs
        ]
        if len(set(normalized_inputs)) != len(normalized_inputs):
            raise ValueError(f"artifact {path} input hashes contain duplicates")
        status = details["status"]
        if status not in {"current", "invalidated", "superseded"}:
            raise ValueError(f"artifact {path} has an invalid status")
        target = root.joinpath(*PurePosixPath(path).parts)
        digest = _hash_inventory_file(root, target, path)
        inventory.append(
            {
                "path": path,
                "sha256": digest,
                "media_type": _media_type(path),
                "generating_phase": phase,
                "input_artifact_sha256s": normalized_inputs,
                "status": status,
            }
        )
    return inventory


def build_artifact_manifest(
    run_contract: Mapping[str, object],
    *,
    phase_chain_head_sha256: str,
    artifacts: Sequence[Mapping[str, object]],
    role_records: Sequence[Mapping[str, object]],
    generated_at: str,
) -> dict[str, object]:
    validate_instance("promax-run-contract.schema.json", dict(run_contract))
    chain_head = _require_sha256(
        phase_chain_head_sha256, field="phase_chain_head_sha256"
    )
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes)):
        raise ValueError("artifacts must be a structured sequence")
    artifact_records = [copy.deepcopy(dict(item)) for item in artifacts]
    known: dict[str, str] = {}
    known_casefold: dict[str, str] = {}
    for index, item in enumerate(artifact_records):
        if not isinstance(item, dict):
            raise ValueError(f"artifact {index} must be an object")
        path = _safe_relative_path(item.get("path"))
        digest = _require_sha256(item.get("sha256"), field=f"artifacts[{index}].sha256")
        if path in known:
            raise ValueError(f"artifact manifest contains duplicate path: {path}")
        folded = path.casefold()
        if folded in known_casefold:
            raise ValueError(
                f"artifact manifest contains a casefold path alias: "
                f"{known_casefold[folded]!r} and {path!r}"
            )
        status = item.get("status")
        if status not in {"current", "invalidated", "superseded"}:
            raise ValueError(f"artifact {index} has an invalid status")
        if status == "current":
            known[path] = digest
        known_casefold[folded] = path
    normalized_roles = validate_role_records(
        run_contract,
        role_records,
        known,
        artifact_records=artifact_records,
    )
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise ValueError("generated_at must be a non-empty timestamp")
    try:
        binding = RunBinding(
            run_id=run_contract["run_id"],
            run_nonce=run_contract["run_nonce"],
            request_sha256=run_contract["request_sha256"],
            source_snapshot_sha256=run_contract["source_snapshot_sha256"],
        )
    except (KeyError, TypeError) as error:
        raise RunBindingError("run contract is missing immutable binding fields") from error
    body: dict[str, object] = {
        "schema_id": "crossframe.promax.v8.artifact-manifest",
        "schema_version": 1,
        "run_id": binding.run_id,
        "run_nonce": binding.run_nonce,
        "request_sha256": binding.request_sha256,
        "source_snapshot_sha256": binding.source_snapshot_sha256,
        "run_contract_sha256": sha256_json(dict(run_contract)),
        "mode": run_contract["mode"],
        "orchestration_mode": run_contract["orchestration_mode"],
        "role_records": normalized_roles,
        "phase_chain_head_sha256": chain_head,
        "artifacts": artifact_records,
        "generated_at": generated_at.strip(),
    }
    manifest = {**body, "manifest_sha256": sha256_json(body)}
    validate_instance("promax-artifact-manifest.schema.json", manifest)
    return manifest
