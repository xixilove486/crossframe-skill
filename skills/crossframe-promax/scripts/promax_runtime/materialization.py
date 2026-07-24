from __future__ import annotations

import copy
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Mapping, Sequence
import unicodedata

from .artifacts import build_artifact_manifest, inventory_artifacts
from .jsonio import canonical_json_bytes, load_json_bytes, sha256_json
from .position import selection_review_basis_sha256
from .safe_files import read_stable_regular_file
from .schemas import validate_instance
from .source_integrity import (
    V8_CONTROL_ASSET_SHA256,
    V8_SOURCE_SNAPSHOT_SHA256,
    build_read_events,
    build_source_snapshot,
    sha256_file,
    validate_read_event_coverage,
)
from .state_machine import (
    RunBinding,
    append_phase_event,
    exclusive_run_lock,
    phase_event_cas_guard,
    seal_phase_event,
    validate_phase_history,
)


AUTHORING_CONTRACT_ARTIFACT = "promax-authoring-contract.json"
CONCEPT_DECISIONS_ARTIFACT = "promax-concept-decisions.json"
ROLE_ATTESTATIONS_ARTIFACT = "promax-role-attestations.json"
MATERIALIZATION_RESULT_ARTIFACT = "promax-materialization-result.json"

SEMANTIC_JSON_ARTIFACTS = (
    "promax-local-world-model.locked.json",
    "promax-claim-path-graph.json",
    "promax-retrieval-ledger.json",
    "promax-red-team-report.json",
    "promax-position.locked.json",
    "promax-recommendation.locked.json",
    "promax-output-plan.locked.json",
)
SEMANTIC_TEXT_ARTIFACTS = (
    "promax-worldview-capsule.locked.md",
    "promax-dossier.md",
    "promax-concept-atlas.md",
    "promax-case-and-countercase.md",
    "promax-essay.md",
    "promax-continuation-index.md",
)
REQUIRED_SEMANTIC_ARTIFACTS = (
    CONCEPT_DECISIONS_ARTIFACT,
    *SEMANTIC_JSON_ARTIFACTS,
    *SEMANTIC_TEXT_ARTIFACTS,
)
_ROLE_BINDINGS = (
    ("promax-local-world-model.locked.json", "promax-concept-disposition-ledger.json"),
    ("promax-claim-path-graph.json", "promax-retrieval-ledger.json"),
    ("promax-retrieval-ledger.json", "promax-red-team-report.json"),
    ("promax-red-team-report.json", "promax-position.locked.json"),
    ("promax-output-plan.locked.json", "promax-essay.md"),
)
_ROLE_ATTESTATION_BINDINGS = (
    ("promax-worldview-capsule.locked.md", CONCEPT_DECISIONS_ARTIFACT),
    ("promax-claim-path-graph.json", "promax-retrieval-ledger.json"),
    ("promax-retrieval-ledger.json", "promax-red-team-report.json"),
    ("promax-red-team-report.json", "promax-position.locked.json"),
    ("promax-output-plan.locked.json", "promax-essay.md"),
)

_TEST_FIXTURE_RUN_ID_RE = re.compile(r"^promax-fixture(?:-|$)", re.IGNORECASE)
_FORBIDDEN_REQUEST_KEYWORDS = {
    "$crossframe-promax",
    "/crossframe-promax",
    "crossframe-promax",
    "crossframe promax",
    "crossframe",
    "promax",
    "使用",
    "请使用",
    "分析",
    "框架",
}
_SEMANTIC_BINDINGS = {
    "promax-local-world-model.locked.json": {
        "schema_id": "crossframe.promax.v8.local-world-model",
        "schema_version": 1,
        "phase_id": "P3",
        "timestamp_field": "locked_at",
        "schema": "promax-local-world-model.schema.json",
    },
    "promax-claim-path-graph.json": {
        "schema_id": "crossframe.promax.v8.claim-path-graph",
        "schema_version": 1,
        "timestamp_field": "updated_at",
        "schema": "promax-claim-path-graph.schema.json",
    },
    "promax-retrieval-ledger.json": {
        "schema_id": "crossframe.promax.v8.retrieval-ledger",
        "schema_version": 1,
        "timestamp_field": "completed_at",
        "schema": "promax-retrieval-ledger.schema.json",
    },
    "promax-red-team-report.json": {
        "schema_id": "crossframe.promax.v8.red-team-report",
        "schema_version": 1,
        "timestamp_field": "completed_at",
        "schema": "promax-red-team-report.schema.json",
    },
    "promax-position.locked.json": {
        "schema_id": "crossframe.promax.v8.position",
        "schema_version": 1,
        "timestamp_field": "locked_at",
        "schema": "promax-position.schema.json",
    },
    "promax-recommendation.locked.json": {
        "schema_id": "crossframe.promax.v8.recommendation",
        "schema_version": 1,
        "timestamp_field": "locked_at",
        "schema": "promax-recommendation.schema.json",
    },
    "promax-output-plan.locked.json": {
        "schema_id": "crossframe.promax.v8.output-plan",
        "schema_version": 1,
        "timestamp_field": "locked_at",
        "schema": "promax-output-plan.schema.json",
    },
}


class MaterializationError(ValueError):
    """Raised when production materialization cannot preserve its hard gates."""


def _trusted_directory(path: Path | str, *, label: str) -> Path:
    candidate = Path(path)
    if candidate.is_symlink():
        raise MaterializationError(f"{label} cannot be a symbolic link")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise MaterializationError(f"{label} does not exist: {candidate}") from error
    if not resolved.is_dir():
        raise MaterializationError(f"{label} is not a directory: {resolved}")
    return resolved


def _new_directory_target(path: Path | str, *, label: str) -> Path:
    candidate = Path(path)
    try:
        resolved = candidate.resolve(strict=False)
        parent = resolved.parent.resolve(strict=True)
    except OSError as error:
        raise MaterializationError(f"{label} parent is unavailable: {candidate}") from error
    if not parent.is_dir() or parent.is_symlink():
        raise MaterializationError(f"{label} parent must be a real directory")
    if resolved.exists() or resolved.is_symlink():
        raise MaterializationError(f"{label} already exists: {resolved}")
    return resolved


def _read_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    try:
        return read_stable_regular_file(path, within_root=root)
    except Exception as error:
        raise MaterializationError(
            f"semantic_bundle_missing_or_unsafe:{relative}:{error}"
        ) from error


def _read_object(root: Path, relative: str) -> dict[str, object]:
    raw = _read_bytes(root, relative)
    try:
        value = load_json_bytes(raw, source=str(root / relative))
    except ValueError as error:
        raise MaterializationError(f"semantic_bundle_invalid_json:{relative}:{error}") from error
    if not isinstance(value, dict):
        raise MaterializationError(f"semantic_bundle_invalid:{relative}:expected object")
    return value


def _read_jsonl(root: Path, relative: str) -> list[dict[str, object]]:
    raw = _read_bytes(root, relative)
    if not raw.endswith(b"\n"):
        raise MaterializationError(f"event_log_not_newline_terminated:{relative}")
    records: list[dict[str, object]] = []
    for index, line in enumerate(raw[:-1].split(b"\n"), start=1):
        try:
            value = load_json_bytes(line, source=f"{root / relative}:{index}")
        except ValueError as error:
            raise MaterializationError(f"event_log_invalid:{relative}:{index}:{error}") from error
        if not isinstance(value, dict):
            raise MaterializationError(f"event_log_invalid:{relative}:{index}:not object")
        if canonical_json_bytes(value) != line:
            raise MaterializationError(f"event_log_noncanonical:{relative}:{index}")
        records.append(value)
    return records


def _write_bytes(path: Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise MaterializationError(f"materializer refuses to overwrite staged path: {path}")
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: object) -> str:
    return _write_bytes(path, canonical_json_bytes(value) + b"\n")


def _jsonl_bytes(records: Sequence[Mapping[str, object]]) -> bytes:
    return b"".join(canonical_json_bytes(record) + b"\n" for record in records)


def _atomic_publish_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.publish-",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise MaterializationError(f"cannot publish through symbolic link: {path}")
        os.replace(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _binding_from_contract(contract: Mapping[str, object]) -> RunBinding:
    try:
        return RunBinding(
            run_id=contract["run_id"],
            run_nonce=contract["run_nonce"],
            request_sha256=contract["request_sha256"],
            source_snapshot_sha256=contract["source_snapshot_sha256"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise MaterializationError(f"run_contract_binding_invalid:{error}") from error


def _reject_fixture_provenance(contract: Mapping[str, object]) -> None:
    run_id = contract.get("run_id")
    if isinstance(run_id, str) and _TEST_FIXTURE_RUN_ID_RE.match(run_id):
        raise MaterializationError("test_fixture_provenance_forbidden")


def _load_run_state(
    repo: Path,
    run_dir: Path,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]], object]:
    contract = _read_object(run_dir, "promax-run-contract.json")
    snapshot = _read_object(run_dir, "promax-source-snapshot.json")
    events = _read_jsonl(run_dir, "promax-phase-events.jsonl")
    try:
        validate_instance("promax-run-contract.schema.json", contract)
        validate_instance("promax-source-snapshot.schema.json", snapshot)
        canonical_snapshot = build_source_snapshot(
            repo,
            verified_at=str(snapshot.get("verified_at", "")),
        )
        if snapshot != canonical_snapshot:
            raise MaterializationError("source_snapshot_content_mismatch")
        binding = _binding_from_contract(contract)
        state = validate_phase_history(events, expected_binding=binding)
    except MaterializationError:
        raise
    except Exception as error:
        raise MaterializationError(f"prepared_run_invalid:{error}") from error
    _reject_fixture_provenance(contract)
    active = state.active_artifact_hashes
    for relative in ("promax-run-contract.json", "promax-source-snapshot.json"):
        digest = hashlib.sha256(_read_bytes(run_dir, relative)).hexdigest()
        if active.get(relative) != digest:
            raise MaterializationError(f"prepared_run_hash_mismatch:{relative}")
    return contract, snapshot, events, state


def _registry_and_routes(repo: Path) -> tuple[dict[str, object], dict[str, object]]:
    references = repo / "skills" / "crossframe-promax" / "references"
    registry = _read_object(
        references,
        "concept-registry/v8-concept-registry.json",
    )
    routes = _read_object(references, "v8-route-map.json")
    if sha256_file(references / "concept-registry/v8-concept-registry.json") != (
        V8_CONTROL_ASSET_SHA256["concept_registry"]
    ):
        raise MaterializationError("canonical_registry_hash_mismatch")
    if sha256_file(references / "v8-route-map.json") != V8_CONTROL_ASSET_SHA256["route_map"]:
        raise MaterializationError("canonical_route_hash_mismatch")
    return registry, routes


def _unique_strings(*values: object) -> list[str]:
    result: list[str] = []
    for value in values:
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise MaterializationError("canonical concept string arrays are malformed")
        for item in value:
            if item not in result:
                result.append(item)
    return result


def _authoring_contract(
    contract: Mapping[str, object],
    *,
    prepared_at: str,
) -> dict[str, object]:
    template_map = {
        "promax-worldview-capsule.locked.md": "templates/promax-worldview-capsule-output.md",
        "promax-local-world-model.locked.json": "templates/promax-local-world-model-output.md",
        "promax-claim-path-graph.json": "templates/promax-claim-path-graph-output.md",
        "promax-retrieval-ledger.json": "templates/promax-retrieval-ledger-output.md",
        "promax-red-team-report.json": "templates/promax-red-team-report-output.md",
        "promax-position.locked.json": "templates/promax-position-output.md",
        "promax-recommendation.locked.json": "templates/promax-recommendation-output.md",
        "promax-output-plan.locked.json": "templates/promax-output-plan-output.md",
        "promax-dossier.md": "templates/promax-dossier-output.md",
        "promax-concept-atlas.md": "templates/promax-concept-atlas-output.md",
        "promax-case-and-countercase.md": "templates/promax-case-and-countercase-output.md",
        "promax-essay.md": "templates/promax-essay-output.md",
        "promax-continuation-index.md": "templates/promax-continuation-index-output.md",
    }
    return {
        "schema_id": "crossframe.promax.v8.authoring-contract",
        "schema_version": 1,
        "run_id": contract["run_id"],
        "request_sha256": contract["request_sha256"],
        "source_snapshot_sha256": contract["source_snapshot_sha256"],
        "concept_decisions_artifact": CONCEPT_DECISIONS_ARTIFACT,
        "required_semantic_artifacts": list(_required_semantic_artifacts(contract)),
        "template_map": template_map,
        "semantic_owner": "model",
        "control_plane_owner": "promax-runtime",
        "prepared_at": prepared_at,
    }


def _required_semantic_artifacts(contract: Mapping[str, object]) -> tuple[str, ...]:
    if contract.get("orchestration_mode") == "multi-agent-isolated":
        return (*REQUIRED_SEMANTIC_ARTIFACTS, ROLE_ATTESTATIONS_ARTIFACT)
    return REQUIRED_SEMANTIC_ARTIFACTS


def _role_attestation_scaffold(contract: Mapping[str, object]) -> dict[str, object]:
    plan = contract.get("role_plan")
    if not isinstance(plan, list) or len(plan) != len(_ROLE_BINDINGS):
        raise MaterializationError("run contract lacks the frozen five-role plan")
    roles: list[dict[str, object]] = []
    for planned, (input_path, output_path) in zip(plan, _ROLE_ATTESTATION_BINDINGS):
        if not isinstance(planned, Mapping):
            raise MaterializationError("frozen role plan entry is not structured")
        roles.append(
            {
                "role_id": planned["role_id"],
                "sequence": planned["sequence"],
                "execution_mode": planned["execution_mode"],
                "exchange_protocol": planned["exchange_protocol"],
                "agent_id": None,
                "input_artifact_paths": [input_path],
                "output_artifact_paths": [output_path],
                "observed_input_artifacts": [],
                "produced_output_artifacts": [],
                "completed_at": None,
                "status": None,
            }
        )
    return {
        "schema_id": "crossframe.promax.v8.role-attestations",
        "schema_version": 2,
        "run_id": contract["run_id"],
        "request_sha256": contract["request_sha256"],
        "source_snapshot_sha256": contract["source_snapshot_sha256"],
        "roles": roles,
    }


def _concept_scaffold(
    contract: Mapping[str, object],
    registry: Mapping[str, object],
) -> dict[str, object]:
    raw_concepts = registry.get("concepts")
    if not isinstance(raw_concepts, list) or len(raw_concepts) != 709:
        raise MaterializationError("canonical registry must contain 709 concepts")
    decisions: list[dict[str, object]] = []
    for concept in raw_concepts:
        if not isinstance(concept, Mapping):
            raise MaterializationError("canonical concept must be an object")
        concept_id = concept.get("concept_id")
        name = concept.get("authoritative_name_zh")
        definition = concept.get("definition")
        if not all(isinstance(item, str) and item for item in (concept_id, name, definition)):
            raise MaterializationError("canonical concept identity is malformed")
        decisions.append(
            {
                "concept_id": concept_id,
                "authoritative_name_zh": name,
                "definition_sha256": sha256_json(definition),
                "status": None,
                "rationale": "",
                "evidence_refs": [],
                "output_section_ids": [],
                "pending_evidence": [],
            }
        )
    return {
        "schema_id": "crossframe.promax.v8.concept-decisions",
        "schema_version": 1,
        "run_id": contract["run_id"],
        "request_sha256": contract["request_sha256"],
        "source_snapshot_sha256": contract["source_snapshot_sha256"],
        "request_keywords": [],
        "request_binding_statement": "",
        "route_ids": [],
        "decisions": decisions,
        "completed_at": None,
    }


def prepare_run(
    repo: Path | str,
    *,
    run_dir: Path | str,
    authoring_dir: Path | str,
    read_at: str,
) -> dict[str, object]:
    """Seal deterministic P1 and create an external 709-item authoring pack."""

    repo_root = _trusted_directory(repo, label="repo")
    run_root = _trusted_directory(run_dir, label="run_dir")
    authoring_target = _new_directory_target(authoring_dir, label="authoring_dir")
    if not isinstance(read_at, str) or not read_at.strip():
        raise MaterializationError("read_at must be a non-empty timestamp")
    with exclusive_run_lock(run_root):
        _recover_interrupted_publish(run_root)
        return _prepare_run_locked(
            repo_root,
            run_root=run_root,
            authoring_target=authoring_target,
            read_at=read_at.strip(),
        )


def _prepare_run_locked(
    repo_root: Path,
    *,
    run_root: Path,
    authoring_target: Path,
    read_at: str,
) -> dict[str, object]:
    contract, _, events, state = _load_run_state(repo_root, run_root)
    if state.next_phase_id != "P1" or len(events) != 1:
        raise MaterializationError("prepare_requires_exact_p0_state")

    registry, _ = _registry_and_routes(repo_root)
    read_events = build_read_events(
        repo_root,
        run_id=str(contract["run_id"]),
        read_at=read_at,
    )
    validate_read_event_coverage(
        read_events,
        repo=repo_root,
        expected_run_id=str(contract["run_id"]),
        expected_source_snapshot_sha256=str(contract["source_snapshot_sha256"]),
    )
    read_raw = _jsonl_bytes(read_events)
    read_digest = hashlib.sha256(read_raw).hexdigest()
    source_digest = hashlib.sha256(
        _read_bytes(run_root, "promax-source-snapshot.json")
    ).hexdigest()
    event = seal_phase_event(
        state,
        "P1",
        input_artifact_hashes={"promax-source-snapshot.json": source_digest},
        output_artifact_hashes={"promax-read-events.jsonl": read_digest},
    )

    authoring_target.parent.mkdir(parents=True, exist_ok=True)
    authoring_stage = Path(
        tempfile.mkdtemp(
            prefix=f".{authoring_target.name}.stage-",
            dir=str(authoring_target.parent),
        )
    )
    published_authoring = False
    read_path = run_root / "promax-read-events.jsonl"
    try:
        _write_json(
            authoring_stage / AUTHORING_CONTRACT_ARTIFACT,
            _authoring_contract(contract, prepared_at=read_at),
        )
        _write_json(
            authoring_stage / CONCEPT_DECISIONS_ARTIFACT,
            _concept_scaffold(contract, registry),
        )
        if contract.get("orchestration_mode") == "multi-agent-isolated":
            _write_json(
                authoring_stage / ROLE_ATTESTATIONS_ARTIFACT,
                _role_attestation_scaffold(contract),
            )
        os.replace(authoring_stage, authoring_target)
        published_authoring = True
        _atomic_publish_bytes(read_path, read_raw)
        try:
            append_phase_event(
                run_root / "promax-phase-events.jsonl",
                event,
                expected_head_sha256=state.chain_head_sha256,
            )
        except BaseException:
            if read_path.exists() and not read_path.is_symlink():
                read_path.unlink()
            raise
    except BaseException:
        if authoring_stage.exists():
            shutil.rmtree(authoring_stage)
        if published_authoring and authoring_target.exists():
            shutil.rmtree(authoring_target)
        raise
    return {
        "status": "prepared",
        "phase": "P1",
        "run_id": contract["run_id"],
        "read_event_count": len(read_events),
        "authoring_dir": str(authoring_target),
        "required_semantic_artifacts": list(_required_semantic_artifacts(contract)),
    }


def _validate_authoring_contract(
    document: Mapping[str, object],
    contract: Mapping[str, object],
) -> None:
    expected_keys = {
        "schema_id",
        "schema_version",
        "run_id",
        "request_sha256",
        "source_snapshot_sha256",
        "concept_decisions_artifact",
        "required_semantic_artifacts",
        "template_map",
        "semantic_owner",
        "control_plane_owner",
        "prepared_at",
    }
    if set(document) != expected_keys:
        raise MaterializationError("authoring_contract_open_or_incomplete")
    if document.get("schema_id") != "crossframe.promax.v8.authoring-contract":
        raise MaterializationError("authoring_contract_schema_mismatch")
    if document.get("schema_version") != 1:
        raise MaterializationError("authoring_contract_version_mismatch")
    for field in ("run_id", "request_sha256", "source_snapshot_sha256"):
        if document.get(field) != contract.get(field):
            raise MaterializationError(f"authoring_contract_binding_mismatch:{field}")
    if document.get("concept_decisions_artifact") != CONCEPT_DECISIONS_ARTIFACT:
        raise MaterializationError("authoring_contract_concept_path_mismatch")
    if document.get("required_semantic_artifacts") != list(
        _required_semantic_artifacts(contract)
    ):
        raise MaterializationError("authoring_contract_artifact_inventory_mismatch")
    if document.get("semantic_owner") != "model":
        raise MaterializationError("authoring_contract_semantic_owner_mismatch")
    if document.get("control_plane_owner") != "promax-runtime":
        raise MaterializationError("authoring_contract_control_owner_mismatch")


def _normalized_keyword(value: object) -> str:
    if not isinstance(value, str):
        raise MaterializationError("request keywords must be strings")
    normalized = " ".join(value.strip().split())
    if len(normalized) < 2:
        raise MaterializationError("request keywords must be substantive")
    if normalized.casefold() in _FORBIDDEN_REQUEST_KEYWORDS:
        raise MaterializationError("request keyword cannot be only a ProMax trigger or generic verb")
    return normalized


def _contains_keyword(text: object, keywords: Sequence[str]) -> bool:
    if not isinstance(text, str):
        return False
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)


def _rationale_template_fingerprint(
    rationale: str,
    *,
    concept_id: str,
    authoritative_name: str,
) -> str:
    normalized = unicodedata.normalize("NFKC", rationale).casefold()
    for identity in sorted(
        {concept_id.casefold(), authoritative_name.casefold()},
        key=len,
        reverse=True,
    ):
        normalized = normalized.replace(identity, " <concept> ")
    normalized = re.sub(r"第\s*\d+\s*项", " <ordinal> ", normalized)
    normalized = re.sub(
        r"(?<![0-9a-z_])(?:序号|编号|条目|item|no\.?)"
        r"\s*(?:[:：#._-]\s*)?\d+(?![0-9a-z_])",
        " <ordinal> ",
        normalized,
    )
    normalized = re.sub(r"\b[0-9a-f]{8,64}\b", " <opaque> ", normalized)
    normalized = re.sub(r"[^0-9a-z_\u4e00-\u9fff<>]+", " ", normalized)
    return " ".join(normalized.split())


def _validate_request_keywords(
    decisions: Mapping[str, object],
    *,
    request_text: str,
    contract: Mapping[str, object],
) -> tuple[str, ...]:
    if not isinstance(request_text, str) or not request_text.strip():
        raise MaterializationError("request_text must be non-empty")
    request_sha = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
    if request_sha != contract.get("request_sha256"):
        raise MaterializationError("request_binding_hash_mismatch")
    raw_keywords = decisions.get("request_keywords")
    if not isinstance(raw_keywords, list) or not raw_keywords:
        raise MaterializationError("request_binding_requires_substantive_keywords")
    keywords = tuple(_normalized_keyword(item) for item in raw_keywords)
    if len(set(item.casefold() for item in keywords)) != len(keywords):
        raise MaterializationError("request keywords must be unique")
    folded_request = request_text.casefold()
    for keyword in keywords:
        if keyword.casefold() not in folded_request:
            raise MaterializationError(f"request keyword is absent from frozen request: {keyword}")
    statement = decisions.get("request_binding_statement")
    if not isinstance(statement, str) or len(statement.strip()) < 12:
        raise MaterializationError("request_binding_statement must explain the frozen object")
    if not _contains_keyword(statement, keywords):
        raise MaterializationError("request_binding_statement omits every request keyword")
    return keywords


def _build_concept_ledger(
    repo: Path,
    contract: Mapping[str, object],
    decisions: Mapping[str, object],
    *,
    request_text: str,
) -> tuple[dict[str, object], tuple[str, ...]]:
    expected_top_keys = {
        "schema_id",
        "schema_version",
        "run_id",
        "request_sha256",
        "source_snapshot_sha256",
        "request_keywords",
        "request_binding_statement",
        "route_ids",
        "decisions",
        "completed_at",
    }
    if set(decisions) != expected_top_keys:
        raise MaterializationError("concept_decisions_open_or_incomplete")
    if decisions.get("schema_id") != "crossframe.promax.v8.concept-decisions":
        raise MaterializationError("concept_decisions_schema_mismatch")
    if decisions.get("schema_version") != 1:
        raise MaterializationError("concept_decisions_version_mismatch")
    for field in ("run_id", "request_sha256", "source_snapshot_sha256"):
        if decisions.get(field) != contract.get(field):
            raise MaterializationError(f"concept_decisions_binding_mismatch:{field}")
    keywords = _validate_request_keywords(
        decisions,
        request_text=request_text,
        contract=contract,
    )
    completed_at = decisions.get("completed_at")
    if not isinstance(completed_at, str) or not completed_at.strip():
        raise MaterializationError("concept_decisions_completed_at_missing")

    registry, route_map = _registry_and_routes(repo)
    raw_routes = route_map.get("routes")
    available_routes = {
        route.get("route_id")
        for route in raw_routes
        if isinstance(raw_routes, list) and isinstance(route, Mapping)
    }
    route_ids = decisions.get("route_ids")
    if (
        not isinstance(route_ids, list)
        or not route_ids
        or any(not isinstance(item, str) for item in route_ids)
        or len(set(route_ids)) != len(route_ids)
        or any(item not in available_routes for item in route_ids)
    ):
        raise MaterializationError("concept_decisions_route_ids_invalid")

    raw_concepts = registry.get("concepts")
    raw_decisions = decisions.get("decisions")
    if not isinstance(raw_concepts, list) or len(raw_concepts) != 709:
        raise MaterializationError("canonical registry count mismatch")
    if not isinstance(raw_decisions, list) or len(raw_decisions) != 709:
        raise MaterializationError("concept_decisions_require_exactly_709_entries")
    if any(not isinstance(item, Mapping) for item in raw_decisions):
        raise MaterializationError("concept decision entries must be objects")
    decision_by_id = {item.get("concept_id"): item for item in raw_decisions}
    if len(decision_by_id) != 709 or None in decision_by_id:
        raise MaterializationError("concept decision identities must be unique")

    entry_keys = {
        "concept_id",
        "authoritative_name_zh",
        "definition_sha256",
        "status",
        "rationale",
        "evidence_refs",
        "output_section_ids",
        "pending_evidence",
    }
    terminal = {"applied", "tested_rejected", "not_applicable", "unknown_pending"}
    dispositions: list[dict[str, object]] = []
    applied_count = 0
    seen_rationales: set[str] = set()
    template_clusters: dict[tuple[object, ...], list[str]] = {}
    for concept in raw_concepts:
        if not isinstance(concept, Mapping):
            raise MaterializationError("canonical concept is not structured")
        concept_id = concept.get("concept_id")
        name = concept.get("authoritative_name_zh")
        definition = concept.get("definition")
        if not all(isinstance(item, str) for item in (concept_id, name, definition)):
            raise MaterializationError("canonical concept identity is malformed")
        decision = decision_by_id.get(concept_id)
        if not isinstance(decision, Mapping) or set(decision) != entry_keys:
            raise MaterializationError(f"concept decision is open or missing: {concept_id}")
        if decision.get("authoritative_name_zh") != name:
            raise MaterializationError(f"concept authoritative name changed: {concept_id}")
        if decision.get("definition_sha256") != sha256_json(definition):
            raise MaterializationError(f"concept definition binding changed: {concept_id}")
        status = decision.get("status")
        if status not in terminal:
            raise MaterializationError(f"concept decision is not terminal: {concept_id}")
        rationale = decision.get("rationale")
        if not isinstance(rationale, str) or len(rationale.strip()) < 16:
            raise MaterializationError(f"concept rationale is not substantive: {concept_id}")
        rationale = rationale.strip()
        if name not in rationale:
            raise MaterializationError(f"concept rationale omits exact v8 name: {concept_id}")
        if not _contains_keyword(rationale, keywords):
            raise MaterializationError(f"concept rationale is not request-bound: {concept_id}")
        if rationale in seen_rationales:
            raise MaterializationError("concept rationales cannot use one repeated bulk default")
        seen_rationales.add(rationale)
        evidence_refs = decision.get("evidence_refs")
        output_sections = decision.get("output_section_ids")
        pending_evidence = decision.get("pending_evidence")
        for field, value in (
            ("evidence_refs", evidence_refs),
            ("output_section_ids", output_sections),
            ("pending_evidence", pending_evidence),
        ):
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ) or len(set(value)) != len(value):
                raise MaterializationError(f"concept {field} is invalid: {concept_id}")
        if status in {"applied", "tested_rejected"} and not evidence_refs:
            raise MaterializationError(f"evidence-bearing concept lacks evidence: {concept_id}")
        if status == "applied" and not output_sections:
            raise MaterializationError(f"applied concept lacks output section: {concept_id}")
        if status == "unknown_pending" and not pending_evidence:
            raise MaterializationError(f"unknown concept lacks pending evidence: {concept_id}")
        if status != "unknown_pending" and pending_evidence:
            raise MaterializationError(f"terminal concept retains pending evidence: {concept_id}")
        template_key = (
            status,
            bool(evidence_refs),
            bool(output_sections),
            bool(pending_evidence),
            _rationale_template_fingerprint(
                rationale,
                concept_id=concept_id,
                authoritative_name=name,
            ),
        )
        template_clusters.setdefault(template_key, []).append(concept_id)
        if status == "applied":
            applied_count += 1
        neighbors = concept.get("required_neighbor_ids")
        if not isinstance(neighbors, list) or any(not isinstance(item, str) for item in neighbors):
            raise MaterializationError(f"canonical neighbors malformed: {concept_id}")
        dispositions.append(
            {
                "concept_id": concept_id,
                "status": status,
                "rationale": rationale,
                "evidence_refs": list(evidence_refs),
                "required_neighbor_ids": list(neighbors),
                "misuses_excluded": _unique_strings(
                    concept.get("common_misuses"),
                    concept.get("forbidden_substitutions_or_generalizations"),
                ),
                "output_section_ids": list(output_sections),
                "pending_evidence": list(pending_evidence),
            }
        )
    if set(decision_by_id) != {item["concept_id"] for item in dispositions}:
        raise MaterializationError("concept decisions contain unknown identities")
    repeated_templates = [
        concept_ids
        for concept_ids in template_clusters.values()
        if len(concept_ids) >= 5
    ]
    if repeated_templates:
        largest = max(repeated_templates, key=len)
        sample = ",".join(largest[:3])
        raise MaterializationError(
            "bulk_rationale_template_detected:"
            f"size={len(largest)}:sample={sample}"
        )
    if applied_count == 0:
        raise MaterializationError("production analysis must apply at least one v8 concept")
    ledger = {
        "schema_id": "crossframe.promax.v8.concept-disposition",
        "schema_version": 1,
        "run_id": contract["run_id"],
        "source_snapshot_sha256": contract["source_snapshot_sha256"],
        "registry_sha256": V8_CONTROL_ASSET_SHA256["concept_registry"],
        "route_ids": list(route_ids),
        "dispositions": dispositions,
        "unchecked_concept_ids": [],
        "closure_complete": True,
        "completed_at": completed_at.strip(),
    }
    validate_instance("promax-concept-disposition.schema.json", ledger)
    return ledger, keywords


def _bind_fixed_fields(
    document: Mapping[str, object],
    *,
    fixed: Mapping[str, object],
    artifact: str,
) -> dict[str, object]:
    normalized = copy.deepcopy(dict(document))
    for field, expected in fixed.items():
        if field in normalized and normalized[field] != expected:
            raise MaterializationError(f"semantic_binding_mismatch:{artifact}:{field}")
        normalized[field] = expected
    return normalized


def _load_semantic_json(
    authoring: Path,
    contract: Mapping[str, object],
    *,
    generated_at: str,
) -> dict[str, dict[str, object]]:
    loaded = {name: _read_object(authoring, name) for name in SEMANTIC_JSON_ARTIFACTS}
    normalized: dict[str, dict[str, object]] = {}
    for artifact in SEMANTIC_JSON_ARTIFACTS:
        document = loaded[artifact]
        if artifact == "promax-recommendation.locked.json" and document == {
            "status": "not_requested"
        }:
            if contract.get("recommendation_required") is not False:
                raise MaterializationError("required recommendation cannot be not_requested")
            normalized[artifact] = document
            continue
        spec = _SEMANTIC_BINDINGS[artifact]
        fixed = {
            "schema_id": spec["schema_id"],
            "schema_version": spec["schema_version"],
            "run_id": contract["run_id"],
            "source_snapshot_sha256": contract["source_snapshot_sha256"],
        }
        if "phase_id" in spec:
            fixed["phase_id"] = spec["phase_id"]
        timestamp_field = str(spec["timestamp_field"])
        if timestamp_field not in document:
            fixed[timestamp_field] = generated_at
        normalized[artifact] = _bind_fixed_fields(
            document,
            fixed=fixed,
            artifact=artifact,
        )
    position = normalized["promax-position.locked.json"]
    recommendation = normalized["promax-recommendation.locked.json"]
    if recommendation != {"status": "not_requested"}:
        recommendation = _bind_fixed_fields(
            recommendation,
            fixed={"position_sha256": sha256_json(position)},
            artifact="promax-recommendation.locked.json",
        )
        normalized["promax-recommendation.locked.json"] = recommendation
    _bind_stability_control_fields(normalized, contract)
    for artifact, document in normalized.items():
        validate_instance(str(_SEMANTIC_BINDINGS[artifact]["schema"]), document)
    return normalized


def _set_control_field(
    record: dict[str, object],
    field: str,
    expected: object,
    *,
    artifact: str,
) -> None:
    actual = record.get(field)
    if field in record and actual != expected:
        raise MaterializationError(f"semantic_fixed_field_mismatch:{artifact}:{field}")
    record[field] = copy.deepcopy(expected)


def _bind_stability_control_fields(
    documents: dict[str, dict[str, object]],
    contract: Mapping[str, object],
) -> None:
    """Derive hashes and verdict prefixes owned by the deterministic control plane."""

    claim_graph = documents["promax-claim-path-graph.json"]
    problem = claim_graph.get("stance_neutral_problem")
    if not isinstance(problem, dict):
        raise MaterializationError("semantic_problem_missing:promax-claim-path-graph.json")
    semantic_payload: dict[str, object] = {}
    for field in ("analysis_object", "proposition_under_test", "time_window"):
        value = problem.get(field)
        if not isinstance(value, str) or not value.strip():
            raise MaterializationError(f"semantic_problem_field_invalid:{field}")
        semantic_payload[field] = value
    semantic_key = sha256_json(semantic_payload)
    _set_control_field(
        problem,
        "semantic_key_sha256",
        semantic_key,
        artifact="promax-claim-path-graph.json",
    )

    local_world = documents["promax-local-world-model.locked.json"]
    retrieval = documents["promax-retrieval-ledger.json"]
    evidence_basis = sha256_json(
        {
            "request_sha256": contract["request_sha256"],
            "source_snapshot_sha256": contract["source_snapshot_sha256"],
            "local_world_model_sha256": sha256_json(local_world),
            "retrieval_ledger_sha256": sha256_json(retrieval),
        }
    )
    red_team = documents["promax-red-team-report.json"]
    recommendation = documents.get(
        "promax-recommendation.locked.json",
        {"status": "not_requested"},
    )
    try:
        normative_selection_basis = (
            sha256_json({"status": "not_requested"})
            if recommendation == {"status": "not_requested"}
            else selection_review_basis_sha256(recommendation)
        )
    except ValueError as error:
        raise MaterializationError(
            f"selection_review_basis_invalid:{error}"
        ) from error
    checks = red_team.get("stability_checks")
    if not isinstance(checks, list) or not checks:
        raise MaterializationError("stability_checks_missing:promax-red-team-report.json")
    for index, raw_check in enumerate(checks):
        if not isinstance(raw_check, dict):
            raise MaterializationError(f"stability_check_invalid:{index}")
        for prompt_field, hash_field in (
            ("pro_prompt", "pro_prompt_sha256"),
            ("anti_prompt", "anti_prompt_sha256"),
        ):
            prompt = raw_check.get(prompt_field)
            if not isinstance(prompt, str) or not prompt.strip():
                raise MaterializationError(
                    f"stability_prompt_missing:{index}:{prompt_field}"
                )
            _set_control_field(
                raw_check,
                hash_field,
                sha256_json(prompt),
                artifact="promax-red-team-report.json",
            )
        for field in (
            "evidence_basis_sha256_before",
            "evidence_basis_sha256_after",
        ):
            _set_control_field(
                raw_check,
                field,
                evidence_basis,
                artifact="promax-red-team-report.json",
            )
        for field in (
            "semantic_problem_sha256_before",
            "semantic_problem_sha256_after",
        ):
            _set_control_field(
                raw_check,
                field,
                semantic_key,
                artifact="promax-red-team-report.json",
            )
        for field in (
            "normative_selection_basis_sha256_before",
            "normative_selection_basis_sha256_after",
        ):
            _set_control_field(
                raw_check,
                field,
                normative_selection_basis,
                artifact="promax-red-team-report.json",
            )

    proposition = semantic_payload["proposition_under_test"]
    position = documents["promax-position.locked.json"]
    relation = position.get("relation_to_proposition")
    if not isinstance(relation, str) or not relation:
        raise MaterializationError("position_relation_missing")
    _set_control_field(
        position,
        "proposition_verdict",
        f"VERDICT[{relation}] {proposition}",
        artifact="promax-position.locked.json",
    )


def _load_semantic_text(authoring: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for artifact in SEMANTIC_TEXT_ARTIFACTS:
        raw = _read_bytes(authoring, artifact)
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise MaterializationError(f"semantic_text_not_utf8:{artifact}:{error}") from error
        if len(text.strip()) < 20:
            raise MaterializationError(f"semantic_text_not_substantive:{artifact}")
        texts[artifact] = text
    return texts


def _validate_cross_artifact_request_binding(
    documents: Mapping[str, Mapping[str, object]],
    texts: Mapping[str, str],
    *,
    keywords: Sequence[str],
) -> None:
    local_world = documents["promax-local-world-model.locked.json"]
    object_boundary = local_world.get("object_boundary")
    object_name = object_boundary.get("name") if isinstance(object_boundary, Mapping) else None
    claim_graph = documents["promax-claim-path-graph.json"]
    central_claim_id = claim_graph.get("central_claim_id")
    claims = claim_graph.get("claims")
    central_statement = None
    if isinstance(claims, list):
        for claim in claims:
            if isinstance(claim, Mapping) and claim.get("claim_id") == central_claim_id:
                central_statement = claim.get("statement")
                break
    position = documents["promax-position.locked.json"].get("position")
    required = {
        "local_world.object_boundary.name": object_name,
        "claim_graph.central_claim.statement": central_statement,
        "position.position": position,
        "promax-dossier.md": texts.get("promax-dossier.md"),
        "promax-essay.md": texts.get("promax-essay.md"),
    }
    missing = [field for field, value in required.items() if not _contains_keyword(value, keywords)]
    if missing:
        raise MaterializationError(
            "request_binding_missing_from_core_artifacts:" + ",".join(missing)
        )


def _artifact_ref(path: str, digest: str) -> dict[str, object]:
    suffix = Path(path).suffix.casefold()
    media_type = {
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".md": "text/markdown",
    }.get(suffix, "application/octet-stream")
    return {"path": path, "sha256": digest, "media_type": media_type}


def _validate_attested_artifact_ref(
    raw: object,
    *,
    expected_path: str,
    authoring: Path,
) -> dict[str, object]:
    if not isinstance(raw, Mapping) or set(raw) != {"path", "sha256"}:
        raise MaterializationError("role attestation artifact hash is open or incomplete")
    if raw.get("path") != expected_path:
        raise MaterializationError("role attestation artifact path mismatch")
    digest = raw.get("sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise MaterializationError("role attestation artifact hash is malformed")
    actual = hashlib.sha256(_read_bytes(authoring, expected_path)).hexdigest()
    if digest != actual:
        raise MaterializationError(
            f"role attestation artifact hash mismatch:{expected_path}"
        )
    return _artifact_ref(expected_path, actual)


def _role_records(
    contract: Mapping[str, object],
    digests: Mapping[str, str],
    *,
    authoring: Path,
) -> list[dict[str, object]]:
    plan = contract.get("role_plan")
    if not isinstance(plan, list) or len(plan) != len(_ROLE_BINDINGS):
        raise MaterializationError("run contract lacks the frozen five-role plan")
    attestations_by_role: dict[str, dict[str, object]] = {}
    if contract.get("orchestration_mode") == "multi-agent-isolated":
        attestation = _read_object(authoring, ROLE_ATTESTATIONS_ARTIFACT)
        expected_top = {
            "schema_id",
            "schema_version",
            "run_id",
            "request_sha256",
            "source_snapshot_sha256",
            "roles",
        }
        if set(attestation) != expected_top:
            raise MaterializationError("role_attestations_open_or_incomplete")
        if attestation.get("schema_id") != "crossframe.promax.v8.role-attestations":
            raise MaterializationError("role_attestations_schema_mismatch")
        if attestation.get("schema_version") != 2:
            raise MaterializationError("role_attestations_version_mismatch")
        for field in ("run_id", "request_sha256", "source_snapshot_sha256"):
            if attestation.get(field) != contract.get(field):
                raise MaterializationError(f"role_attestations_binding_mismatch:{field}")
        raw_roles = attestation.get("roles")
        if not isinstance(raw_roles, list) or len(raw_roles) != len(_ROLE_BINDINGS):
            raise MaterializationError("role_attestations_require_exactly_five_roles")
        expected_role_keys = {
            "role_id",
            "sequence",
            "execution_mode",
            "exchange_protocol",
            "agent_id",
            "input_artifact_paths",
            "output_artifact_paths",
            "observed_input_artifacts",
            "produced_output_artifacts",
            "completed_at",
            "status",
        }
        agent_ids: list[str] = []
        for planned, binding, raw_role in zip(
            plan,
            _ROLE_ATTESTATION_BINDINGS,
            raw_roles,
        ):
            if not isinstance(planned, Mapping) or not isinstance(raw_role, Mapping):
                raise MaterializationError("role attestation entry is not structured")
            if set(raw_role) != expected_role_keys:
                raise MaterializationError("role attestation entry is open or incomplete")
            for field in (
                "role_id",
                "sequence",
                "execution_mode",
                "exchange_protocol",
            ):
                if raw_role.get(field) != planned.get(field):
                    raise MaterializationError(f"role attestation changes frozen {field}")
            input_path, output_path = binding
            if raw_role.get("input_artifact_paths") != [input_path]:
                raise MaterializationError("role attestation input path mismatch")
            if raw_role.get("output_artifact_paths") != [output_path]:
                raise MaterializationError("role attestation output path mismatch")
            if raw_role.get("status") != "completed":
                raise MaterializationError("strict multi-agent role must be completed")
            agent_id = raw_role.get("agent_id")
            if not isinstance(agent_id, str) or len(agent_id.strip()) < 3:
                raise MaterializationError("multi-agent role lacks an execution identity")
            observed = raw_role.get("observed_input_artifacts")
            produced = raw_role.get("produced_output_artifacts")
            if not isinstance(observed, list) or len(observed) != 1:
                raise MaterializationError("role attestation requires one observed input hash")
            if not isinstance(produced, list) or len(produced) != 1:
                raise MaterializationError("role attestation requires one produced output hash")
            observed_ref = _validate_attested_artifact_ref(
                observed[0],
                expected_path=input_path,
                authoring=authoring,
            )
            produced_ref = _validate_attested_artifact_ref(
                produced[0],
                expected_path=output_path,
                authoring=authoring,
            )
            for label, artifact_ref in (
                ("input", observed_ref),
                ("output", produced_ref),
            ):
                path = str(artifact_ref["path"])
                if path in digests and artifact_ref["sha256"] != digests[path]:
                    raise MaterializationError(
                        "role attestation does not bind canonical staged bytes:"
                        f"{label}:{path}"
                    )
            completed_at = raw_role.get("completed_at")
            if not isinstance(completed_at, str) or not completed_at.strip():
                raise MaterializationError("role attestation lacks a completion timestamp")
            normalized_agent_id = agent_id.strip()
            agent_ids.append(normalized_agent_id)
            claim = {
                "run_id": contract["run_id"],
                "request_sha256": contract["request_sha256"],
                "source_snapshot_sha256": contract["source_snapshot_sha256"],
                "role_id": raw_role["role_id"],
                "sequence": raw_role["sequence"],
                "agent_id": normalized_agent_id,
                "completed_at": completed_at.strip(),
                "observed_input_artifacts": [observed_ref],
                "produced_output_artifacts": [produced_ref],
            }
            attestations_by_role[str(raw_role["role_id"])] = {
                "agent_id": normalized_agent_id,
                "execution_attestation": {
                    "run_id": claim["run_id"],
                    "request_sha256": claim["request_sha256"],
                    "source_snapshot_sha256": claim["source_snapshot_sha256"],
                    "completed_at": claim["completed_at"],
                    "observed_input_artifacts": claim["observed_input_artifacts"],
                    "produced_output_artifacts": claim["produced_output_artifacts"],
                    "claim_sha256": sha256_json(claim),
                },
            }
        if len(set(agent_ids)) != len(agent_ids):
            raise MaterializationError("multi-agent roles require five unique execution identities")
    elif contract.get("orchestration_mode") != "single-agent-separated":
        raise MaterializationError("unsupported frozen orchestration mode")
    records: list[dict[str, object]] = []
    for planned, (input_path, output_path) in zip(plan, _ROLE_BINDINGS):
        if not isinstance(planned, Mapping):
            raise MaterializationError("frozen role plan entry is not structured")
        attested = attestations_by_role.get(str(planned.get("role_id")))
        if attestations_by_role and attested is None:
            raise MaterializationError("frozen role lacks a matching attestation")
        input_ref = _artifact_ref(input_path, digests[input_path])
        record = {
            **copy.deepcopy(dict(planned)),
            "input_artifacts": [input_ref],
            "observed_input_artifacts": [copy.deepcopy(input_ref)],
            "output_artifacts": [_artifact_ref(output_path, digests[output_path])],
            "status": "completed",
        }
        if attested is not None:
            record.update(copy.deepcopy(attested))
        records.append(record)
    return records


def _metadata(digests: Mapping[str, str]) -> dict[str, dict[str, object]]:
    metadata: dict[str, dict[str, object]] = {
        "promax-source-snapshot.json": {
            "generating_phase": "P0",
            "input_artifact_sha256s": [],
            "status": "current",
        },
        "promax-read-events.jsonl": {
            "generating_phase": "P1",
            "input_artifact_sha256s": [digests["promax-source-snapshot.json"]],
            "status": "current",
        },
        "promax-worldview-capsule.locked.md": {
            "generating_phase": "P2",
            "input_artifact_sha256s": [digests["promax-read-events.jsonl"]],
            "status": "current",
        },
        "promax-local-world-model.locked.json": {
            "generating_phase": "P3",
            "input_artifact_sha256s": [digests["promax-worldview-capsule.locked.md"]],
            "status": "current",
        },
        "promax-concept-disposition-ledger.json": {
            "generating_phase": "P4",
            "input_artifact_sha256s": [digests["promax-local-world-model.locked.json"]],
            "status": "current",
        },
        "promax-claim-path-graph.json": {
            "generating_phase": "P5",
            "input_artifact_sha256s": [digests["promax-concept-disposition-ledger.json"]],
            "status": "current",
        },
        "promax-retrieval-ledger.json": {
            "generating_phase": "P6",
            "input_artifact_sha256s": [digests["promax-claim-path-graph.json"]],
            "status": "current",
        },
        "promax-red-team-report.json": {
            "generating_phase": "P7",
            "input_artifact_sha256s": [digests["promax-retrieval-ledger.json"]],
            "status": "current",
        },
        "promax-position.locked.json": {
            "generating_phase": "P8",
            "input_artifact_sha256s": [digests["promax-red-team-report.json"]],
            "status": "current",
        },
        "promax-recommendation.locked.json": {
            "generating_phase": "P8",
            "input_artifact_sha256s": [digests["promax-position.locked.json"]],
            "status": "current",
        },
        "promax-output-plan.locked.json": {
            "generating_phase": "P9",
            "input_artifact_sha256s": [
                digests["promax-position.locked.json"],
                digests["promax-recommendation.locked.json"],
            ],
            "status": "current",
        },
    }
    for path in (
        "promax-dossier.md",
        "promax-concept-atlas.md",
        "promax-case-and-countercase.md",
        "promax-essay.md",
        "promax-continuation-index.md",
    ):
        metadata[path] = {
            "generating_phase": "P10",
            "input_artifact_sha256s": [digests["promax-output-plan.locked.json"]],
            "status": "current",
        }
    return metadata


def _phase_specs(digests: Mapping[str, str]) -> tuple[tuple[str, dict[str, str], dict[str, str]], ...]:
    return (
        (
            "P2",
            {"promax-read-events.jsonl": digests["promax-read-events.jsonl"]},
            {
                "promax-worldview-capsule.locked.md": digests[
                    "promax-worldview-capsule.locked.md"
                ]
            },
        ),
        (
            "P3",
            {
                "promax-worldview-capsule.locked.md": digests[
                    "promax-worldview-capsule.locked.md"
                ]
            },
            {
                "promax-local-world-model.locked.json": digests[
                    "promax-local-world-model.locked.json"
                ]
            },
        ),
        (
            "P4",
            {
                "promax-local-world-model.locked.json": digests[
                    "promax-local-world-model.locked.json"
                ]
            },
            {
                "promax-concept-disposition-ledger.json": digests[
                    "promax-concept-disposition-ledger.json"
                ]
            },
        ),
        (
            "P5",
            {
                "promax-concept-disposition-ledger.json": digests[
                    "promax-concept-disposition-ledger.json"
                ]
            },
            {"promax-claim-path-graph.json": digests["promax-claim-path-graph.json"]},
        ),
        (
            "P6",
            {"promax-claim-path-graph.json": digests["promax-claim-path-graph.json"]},
            {"promax-retrieval-ledger.json": digests["promax-retrieval-ledger.json"]},
        ),
        (
            "P7",
            {"promax-retrieval-ledger.json": digests["promax-retrieval-ledger.json"]},
            {"promax-red-team-report.json": digests["promax-red-team-report.json"]},
        ),
        (
            "P8",
            {"promax-red-team-report.json": digests["promax-red-team-report.json"]},
            {
                "promax-position.locked.json": digests["promax-position.locked.json"],
                "promax-recommendation.locked.json": digests[
                    "promax-recommendation.locked.json"
                ],
            },
        ),
        (
            "P9",
            {
                "promax-position.locked.json": digests["promax-position.locked.json"],
                "promax-recommendation.locked.json": digests[
                    "promax-recommendation.locked.json"
                ],
            },
            {"promax-output-plan.locked.json": digests["promax-output-plan.locked.json"]},
        ),
        (
            "P10",
            {"promax-output-plan.locked.json": digests["promax-output-plan.locked.json"]},
            {
                path: digests[path]
                for path in (
                    "promax-dossier.md",
                    "promax-concept-atlas.md",
                    "promax-case-and-countercase.md",
                    "promax-essay.md",
                    "promax-continuation-index.md",
                )
            },
        ),
    )


_PUBLISH_JOURNAL = "publish-journal.json"
_PHASE_LOCK_ARTIFACT = ".promax-phase-events.jsonl.lock"


def _publish_transaction_path(run_dir: Path) -> Path:
    return run_dir.parent / f".{run_dir.name}.promax-publish-transaction"


def _transactional_run_files(run_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(run_dir.iterdir()):
        if path.name == _PHASE_LOCK_ARTIFACT:
            continue
        if path.is_symlink() or not path.is_file():
            raise MaterializationError(
                f"formal run contains an unsafe transactional entry:{path.name}"
            )
        files.append(path)
    return files


def _write_publish_journal(transaction: Path, journal: Mapping[str, object]) -> None:
    _atomic_publish_bytes(
        transaction / _PUBLISH_JOURNAL,
        canonical_json_bytes(journal) + b"\n",
    )


def _begin_publish_transaction(
    run_dir: Path,
    *,
    expected_head_sha256: str,
    target_head_sha256: str,
) -> tuple[Path, dict[str, object]]:
    target = _publish_transaction_path(run_dir)
    if target.exists() or target.is_symlink():
        raise MaterializationError("unrecovered_publish_transaction_exists")
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{run_dir.name}.promax-publish-stage-",
            dir=str(run_dir.parent),
        )
    )
    try:
        backup = stage / "backup"
        backup.mkdir()
        originals: dict[str, str] = {}
        for path in _transactional_run_files(run_dir):
            raw = _read_bytes(run_dir, path.name)
            _write_bytes(backup / path.name, raw)
            originals[path.name] = hashlib.sha256(raw).hexdigest()
        journal: dict[str, object] = {
            "schema_id": "crossframe.promax.v8.publish-transaction",
            "schema_version": 1,
            "status": "prepared",
            "expected_head_sha256": expected_head_sha256,
            "target_head_sha256": target_head_sha256,
            "original_files": originals,
        }
        _write_json(stage / _PUBLISH_JOURNAL, journal)
        os.replace(stage, target)
        return target, journal
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def _load_publish_journal(transaction: Path) -> dict[str, object]:
    journal = _read_object(transaction, _PUBLISH_JOURNAL)
    expected_keys = {
        "schema_id",
        "schema_version",
        "status",
        "expected_head_sha256",
        "target_head_sha256",
        "original_files",
    }
    if set(journal) != expected_keys:
        raise MaterializationError("publish transaction journal is open or incomplete")
    if journal.get("schema_id") != "crossframe.promax.v8.publish-transaction":
        raise MaterializationError("publish transaction journal schema mismatch")
    if journal.get("schema_version") != 1:
        raise MaterializationError("publish transaction journal version mismatch")
    if journal.get("status") not in {
        "prepared",
        "publishing",
        "rolling_back",
        "committed",
    }:
        raise MaterializationError("publish transaction journal status is invalid")
    originals = journal.get("original_files")
    if not isinstance(originals, Mapping) or any(
        not isinstance(name, str)
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        for name, digest in originals.items()
    ):
        raise MaterializationError("publish transaction originals are malformed")
    return journal


def _restore_publish_transaction(
    run_dir: Path,
    transaction: Path,
    journal: Mapping[str, object],
) -> None:
    originals_raw = journal.get("original_files")
    if not isinstance(originals_raw, Mapping):
        raise MaterializationError("publish transaction lacks original files")
    originals = {str(name): str(digest) for name, digest in originals_raw.items()}
    backup = transaction / "backup"
    if not backup.is_dir() or backup.is_symlink():
        raise MaterializationError("publish transaction backup is unavailable")
    for path in reversed(_transactional_run_files(run_dir)):
        if path.name not in originals:
            path.unlink()
    for name, expected_digest in originals.items():
        raw = _read_bytes(backup, name)
        if hashlib.sha256(raw).hexdigest() != expected_digest:
            raise MaterializationError(f"publish transaction backup hash mismatch:{name}")
        _atomic_publish_bytes(run_dir / name, raw)
    current = {
        path.name: hashlib.sha256(_read_bytes(run_dir, path.name)).hexdigest()
        for path in _transactional_run_files(run_dir)
    }
    if current != originals:
        raise MaterializationError("publish transaction rollback verification failed")


def _recover_interrupted_publish(run_dir: Path) -> None:
    transaction = _publish_transaction_path(run_dir)
    orphan_prefix = f".{run_dir.name}.promax-publish-stage-"
    for orphan in run_dir.parent.glob(f"{orphan_prefix}*"):
        if orphan.is_symlink() or not orphan.is_dir():
            raise MaterializationError("orphan publish stage path is unsafe")
        shutil.rmtree(orphan)
    if not transaction.exists():
        return
    if transaction.is_symlink() or not transaction.is_dir():
        raise MaterializationError("publish transaction path is unsafe")
    journal = _load_publish_journal(transaction)
    event_path = run_dir / "promax-phase-events.jsonl"
    with phase_event_cas_guard(event_path) as (_, state, _):
        allowed_heads = {
            journal["expected_head_sha256"],
            journal["target_head_sha256"],
        }
        if state.chain_head_sha256 not in allowed_heads:
            raise MaterializationError("publish transaction recovery head mismatch")
        if journal["status"] == "committed":
            if state.chain_head_sha256 != journal["target_head_sha256"]:
                raise MaterializationError("committed publish transaction lacks its target head")
        else:
            _restore_publish_transaction(run_dir, transaction, journal)
    shutil.rmtree(transaction)


def _apply_publish_stage(stage: Path, run_dir: Path) -> None:
    files = [path for path in sorted(stage.iterdir()) if path.is_file()]
    if any(path.is_symlink() for path in files):
        raise MaterializationError("staged workspace contains a symbolic link")
    immutable = {
        "promax-run-contract.json",
        "promax-source-snapshot.json",
        "promax-read-events.jsonl",
    }
    for name in immutable:
        if (stage / name).read_bytes() != _read_bytes(run_dir, name):
            raise MaterializationError(f"staged immutable artifact changed:{name}")
    phase_path = stage / "promax-phase-events.jsonl"
    for path in files:
        if (
            path.name in immutable
            or path.name == phase_path.name
            or path.name == _PHASE_LOCK_ARTIFACT
        ):
            continue
        _atomic_publish_bytes(run_dir / path.name, path.read_bytes())
    _atomic_publish_bytes(run_dir / phase_path.name, phase_path.read_bytes())


@contextmanager
def _publish_stage_transaction(
    stage: Path,
    run_dir: Path,
    *,
    expected_head_sha256: str,
    target_head_sha256: str,
    expected_binding: RunBinding,
    expected_phase_log: bytes,
):
    event_path = run_dir / "promax-phase-events.jsonl"
    with phase_event_cas_guard(
        event_path,
        expected_head_sha256=expected_head_sha256,
        expected_binding=expected_binding,
    ) as (records, state, current_raw):
        if len(records) != 2 or state.next_phase_id != "P2":
            raise MaterializationError("publish_requires_exact_p0_p1_state")
        if current_raw != expected_phase_log:
            raise MaterializationError("publish_phase_prefix_changed")
        transaction, journal = _begin_publish_transaction(
            run_dir,
            expected_head_sha256=expected_head_sha256,
            target_head_sha256=target_head_sha256,
        )
        try:
            journal["status"] = "publishing"
            _write_publish_journal(transaction, journal)
            _apply_publish_stage(stage, run_dir)
            yield
        except BaseException as publish_error:
            try:
                journal["status"] = "rolling_back"
                _write_publish_journal(transaction, journal)
                _restore_publish_transaction(run_dir, transaction, journal)
                shutil.rmtree(transaction)
            except BaseException as rollback_error:
                raise MaterializationError(
                    "publish failed and rollback could not restore the P1 workspace"
                ) from rollback_error
            raise publish_error
        else:
            journal["status"] = "committed"
            _write_publish_journal(transaction, journal)
            shutil.rmtree(transaction)


def materialize_run(
    repo: Path | str,
    *,
    run_dir: Path | str,
    authoring_dir: Path | str,
    request_text: str,
    generated_at: str,
) -> dict[str, object]:
    """Validate model-owned semantics and publish the deterministic P2-P10 plane."""

    repo_root = _trusted_directory(repo, label="repo")
    run_root = _trusted_directory(run_dir, label="run_dir")
    authoring_root = _trusted_directory(authoring_dir, label="authoring_dir")
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise MaterializationError("generated_at must be a non-empty timestamp")
    with exclusive_run_lock(run_root):
        _recover_interrupted_publish(run_root)
        return _materialize_run_locked(
            repo_root,
            run_root=run_root,
            authoring_root=authoring_root,
            request_text=request_text,
            generated_at=generated_at.strip(),
        )


def _materialize_run_locked(
    repo_root: Path,
    *,
    run_root: Path,
    authoring_root: Path,
    request_text: str,
    generated_at: str,
) -> dict[str, object]:
    contract, snapshot, events, state = _load_run_state(repo_root, run_root)
    if state.next_phase_id != "P2" or len(events) != 2:
        raise MaterializationError("materialize_requires_exact_p0_p1_state")
    read_events = _read_jsonl(run_root, "promax-read-events.jsonl")
    validate_read_event_coverage(
        read_events,
        repo=repo_root,
        expected_run_id=str(contract["run_id"]),
        expected_source_snapshot_sha256=str(contract["source_snapshot_sha256"]),
    )
    if state.active_artifact_hashes.get("promax-read-events.jsonl") != hashlib.sha256(
        _read_bytes(run_root, "promax-read-events.jsonl")
    ).hexdigest():
        raise MaterializationError("prepared_read_event_hash_mismatch")

    authoring_contract = _read_object(authoring_root, AUTHORING_CONTRACT_ARTIFACT)
    _validate_authoring_contract(authoring_contract, contract)
    for artifact in _required_semantic_artifacts(contract):
        if not (authoring_root / artifact).is_file():
            raise MaterializationError(f"semantic_bundle_missing:{artifact}")
    decisions = _read_object(authoring_root, CONCEPT_DECISIONS_ARTIFACT)
    concept_ledger, keywords = _build_concept_ledger(
        repo_root,
        contract,
        decisions,
        request_text=request_text,
    )
    documents = _load_semantic_json(
        authoring_root,
        contract,
        generated_at=generated_at,
    )
    texts = _load_semantic_text(authoring_root)
    _validate_cross_artifact_request_binding(documents, texts, keywords=keywords)

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{run_root.name}.materialize-",
            dir=str(run_root.parent),
        )
    )
    try:
        digests: dict[str, str] = {}
        for artifact, value in (
            ("promax-run-contract.json", contract),
            ("promax-source-snapshot.json", snapshot),
        ):
            digests[artifact] = _write_json(stage / artifact, value)
        digests["promax-read-events.jsonl"] = _write_bytes(
            stage / "promax-read-events.jsonl",
            _read_bytes(run_root, "promax-read-events.jsonl"),
        )
        digests["promax-worldview-capsule.locked.md"] = _write_bytes(
            stage / "promax-worldview-capsule.locked.md",
            texts["promax-worldview-capsule.locked.md"].encode("utf-8"),
        )
        digests["promax-local-world-model.locked.json"] = _write_json(
            stage / "promax-local-world-model.locked.json",
            documents["promax-local-world-model.locked.json"],
        )
        digests["promax-concept-disposition-ledger.json"] = _write_json(
            stage / "promax-concept-disposition-ledger.json",
            concept_ledger,
        )
        for artifact in SEMANTIC_JSON_ARTIFACTS:
            if artifact == "promax-local-world-model.locked.json":
                continue
            digests[artifact] = _write_json(stage / artifact, documents[artifact])
        for artifact in (
            "promax-dossier.md",
            "promax-concept-atlas.md",
            "promax-case-and-countercase.md",
            "promax-essay.md",
            "promax-continuation-index.md",
        ):
            digests[artifact] = _write_bytes(stage / artifact, texts[artifact].encode("utf-8"))

        _write_bytes(
            stage / "promax-phase-events.jsonl",
            _jsonl_bytes(events),
        )
        current_state = validate_phase_history(events, expected_binding=_binding_from_contract(contract))
        for phase_id, inputs, outputs in _phase_specs(digests):
            event = seal_phase_event(
                current_state,
                phase_id,
                input_artifact_hashes=inputs,
                output_artifact_hashes=outputs,
            )
            current_state = append_phase_event(
                stage / "promax-phase-events.jsonl",
                event,
                expected_head_sha256=current_state.chain_head_sha256,
            )
        if current_state.next_phase_id != "P11" or current_state.chain_head_sha256 is None:
            raise MaterializationError("phase_chain_did_not_close_through_p10")

        metadata = _metadata(digests)
        inventory = inventory_artifacts(stage, metadata)
        role_records = _role_records(contract, digests, authoring=authoring_root)
        manifest = build_artifact_manifest(
            contract,
            phase_chain_head_sha256=current_state.chain_head_sha256,
            artifacts=inventory,
            role_records=role_records,
            generated_at=generated_at,
        )
        _write_json(stage / "promax-artifact-manifest.json", manifest)
        continuation = {
            "schema_id": "crossframe.promax.v8.continuation-ledger",
            "schema_version": 1,
            "run_id": contract["run_id"],
            "source_snapshot_sha256": contract["source_snapshot_sha256"],
            "parent_manifest_sha256": manifest["manifest_sha256"],
            "continuations": [],
            "updated_at": generated_at,
        }
        _write_json(stage / "promax-continuation-ledger.json", continuation)
        position = documents["promax-position.locked.json"]
        output_plan = documents["promax-output-plan.locked.json"]
        import check_crossframe_promax_artifacts as checker

        preflight = checker.validate_workspace(
            stage,
            repo=repo_root,
            final_chat=False,
            write_report=False,
            validated_at=generated_at,
        )
        if preflight.get("failures"):
            result = checker.validate_workspace(
                stage,
                repo=repo_root,
                final_chat=False,
                write_report=True,
                validated_at=generated_at,
            )
        else:
            completion_status = preflight.get("completion_status")
            if not isinstance(completion_status, str) or not completion_status:
                raise MaterializationError("checker_preflight_omitted_completion_status")
            final_chat = {
                "run_status": completion_status,
                "center_judgment_summary": position["position"],
                "key_withdrawal_conditions": position["withdrawal_conditions"],
                "artifact_links": output_plan["required_artifacts"],
                "continuation_entry": None,
            }
            _write_json(stage / "promax-final-chat.json", final_chat)
            result = checker.validate_workspace(
                stage,
                repo=repo_root,
                final_chat=True,
                write_report=True,
                validated_at=generated_at,
            )
        publishable = not result.get("failures") and isinstance(
            result.get("final_chat_projection"),
            Mapping,
        )
        if not publishable:
            failure_record = {
                "schema_id": "crossframe.promax.v8.materialization-result",
                "schema_version": 1,
                "published": False,
                "run_id": contract["run_id"],
                "validator_result": result,
            }
            _atomic_publish_bytes(
                authoring_root / MATERIALIZATION_RESULT_ARTIFACT,
                canonical_json_bytes(failure_record) + b"\n",
            )
            return failure_record
        with _publish_stage_transaction(
            stage,
            run_root,
            expected_head_sha256=str(state.chain_head_sha256),
            target_head_sha256=str(current_state.chain_head_sha256),
            expected_binding=_binding_from_contract(contract),
            expected_phase_log=_jsonl_bytes(events),
        ):
            postcheck = checker.validate_workspace(
                run_root,
                repo=repo_root,
                final_chat=True,
                write_report=False,
                validated_at=generated_at,
            )
            if postcheck.get("failures") or postcheck.get(
                "final_chat_projection"
            ) != result.get("final_chat_projection"):
                raise MaterializationError("published_workspace_postcheck_failed")
        return {
            "schema_id": "crossframe.promax.v8.materialization-result",
            "schema_version": 1,
            "published": True,
            "run_id": contract["run_id"],
            "phase": "P10",
            "manifest_sha256": manifest["manifest_sha256"],
            "validator_result": result,
            "final_chat_projection": copy.deepcopy(result["final_chat_projection"]),
        }
    finally:
        if stage.exists():
            shutil.rmtree(stage)
