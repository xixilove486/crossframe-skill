from __future__ import annotations

from collections import deque
from collections.abc import Collection, Mapping, Sequence
import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from jsonschema import Draft202012Validator, ValidationError

from check_crossframe_ultra_v82_knowledge import (
    _unsupported_semantic_units as _checker_unsupported_semantic_units,
    _validate_concepts as _checker_validate_concepts,
    _validate_machine_requirement_closure as _checker_validate_requirements,
    _validate_routes as _checker_validate_routes,
)

from .errors import UltraSchemaError
from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import build_schema_registry, validate_instance, validate_phase_artifact
from .source_integrity import (
    SourceManifestError,
    load_source_manifest,
    validate_committed_source_snapshot,
)


_STATUSES = frozenset(
    {"applied", "tested-rejected", "not-applicable", "unknown-pending"}
)
_RETURNED_STATUSES = frozenset({"applied", "tested-rejected", "unknown-pending"})
_STANDALONE_ORDINAL_RE = re.compile(r"(?<!\w)\d+(?!\w)")
_STANDALONE_ROMAN_ORDINAL_RE = re.compile(
    r"(?<!\w)"
    r"(?:[\(\[\{（【]\s*)?"
    r"(?:viii|vii|vi|iv|ix|v|iii|ii|i)"
    r"(?:\s*[\)\]\}）】])?"
    r"(?!\w)",
    flags=re.IGNORECASE,
)
_STANDALONE_ENGLISH_ORDINAL_RE = re.compile(
    r"(?<!\w)"
    r"(?:one|two|three|four|five|six|seven|eight|nine|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth)"
    r"(?!\w)",
    flags=re.IGNORECASE,
)
_STANDALONE_CHINESE_ORDINAL_RE = re.compile(
    r"(?<!\w)(?:第一|第二|第三|第四|第五|第六|第七|第八|第九)(?!\w)"
)
_CONTRACT_DOCUMENT_REF = (
    "https://crossframe.local/schemas/ultra-contract-map.schema.json"
    "#/$defs/contractDocument"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class ConceptClosureError(ValueError):
    """Raised when a concept artifact claims closure without exact authority."""


def _require_native_json(value: object, *, label: str) -> None:
    value_type = type(value)
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ConceptClosureError(
                    f"{label} has a non-native JSON object key"
                )
            _require_native_json(item, label=label)
        return
    if value_type is list:
        for item in value:
            _require_native_json(item, label=label)
        return
    if value_type in {str, int, float, bool, type(None)}:
        return
    raise ConceptClosureError(f"{label} contains a non-native JSON value")


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ConceptClosureError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise ConceptClosureError(f"{label} cannot be snapshotted: {error}") from error
    _require_native_json(snapshot, label=label)
    return snapshot


def _canonical_sha256(value: object) -> str:
    try:
        return sha256_bytes(canonical_json_bytes(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise ConceptClosureError(f"artifact is not canonical JSON: {error}") from error


def _require_sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ConceptClosureError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _validated_public_authorities(
    *,
    expected_run_id: object,
    expected_version_binding: Mapping[str, object],
    expected_source_manifest_sha256: object,
    expected_evidence_artifact_sha256: object,
    expected_world_volume_artifact_sha256: object,
    expected_transformation_ledger_artifact_sha256: object,
    expected_registry_sha256: object,
    expected_route_map_sha256: object,
    expected_contract_map_sha256: object,
) -> tuple[str, dict[str, Any], str, str, str, str, str, str, str]:
    if type(expected_run_id) is not str or not expected_run_id:
        raise ConceptClosureError("expected_run_id must be a nonempty native string")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected version binding"
    )
    hashes = tuple(
        _require_sha256(value, label=label)
        for value, label in (
            (expected_source_manifest_sha256, "expected source manifest hash"),
            (expected_evidence_artifact_sha256, "expected evidence artifact hash"),
            (expected_world_volume_artifact_sha256, "expected world artifact hash"),
            (
                expected_transformation_ledger_artifact_sha256,
                "expected transformation-ledger artifact hash",
            ),
            (expected_registry_sha256, "expected registry hash"),
            (expected_route_map_sha256, "expected route-map hash"),
            (expected_contract_map_sha256, "expected contract-map hash"),
        )
    )
    return expected_run_id, binding, *hashes


def _load_json_bytes(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConceptClosureError(f"cannot load {label}: {error}") from error
    if not isinstance(value, dict):
        raise ConceptClosureError(f"{label} must be a JSON object")
    return raw, value


def _records_by_id(
    records: object, *, field: str, label: str
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise ConceptClosureError(f"{label} records must be an array")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise ConceptClosureError(f"{label} record must be an object")
        identifier = record.get(field)
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise ConceptClosureError(f"duplicate or invalid {label} ID")
        result[identifier] = record
    return result


def _checked_ids(value: Collection[str], *, label: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ConceptClosureError(f"{label} must be a collection")
    try:
        identifiers = tuple(value)
    except (TypeError, ValueError) as error:
        raise ConceptClosureError(f"{label} cannot be read: {error}") from error
    if any(type(item) is not str or not item for item in identifiers):
        raise ConceptClosureError(f"{label} contains an invalid identifier")
    if len(identifiers) != len(set(identifiers)):
        raise ConceptClosureError(f"{label} contains duplicate identifiers")
    return identifiers


def _source_ids(
    value: object,
    *,
    source_units: frozenset[str],
    label: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    identifiers = _checked_ids(value, label=label)
    if not allow_empty and not identifiers:
        raise ConceptClosureError(f"{label} must not be empty")
    if not set(identifiers).issubset(source_units):
        raise ConceptClosureError(f"{label} names an unknown source unit")
    return identifiers


def _validated_source_records(
    repo: Path,
    *,
    manifest_document: Mapping[str, object],
    expected_manifest_sha256: str,
) -> dict[str, str]:
    try:
        snapshot = validate_committed_source_snapshot(repo)
        manifest_bytes = snapshot.manifest_bytes
        paragraphs = tuple(snapshot.paragraphs)
        tables = tuple(snapshot.tables)
    except (AttributeError, MemoryError, OSError, TypeError, ValueError) as error:
        raise ConceptClosureError(f"cannot read committed source authority: {error}") from error
    if (
        not isinstance(manifest_bytes, bytes)
        or hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256
    ):
        raise ConceptClosureError("committed source snapshot uses another manifest")

    records: dict[str, str] = {}
    observed_units: list[dict[str, object]] = []
    for kind, source_records in (("paragraph", paragraphs), ("table", tables)):
        for source_record in source_records:
            if not isinstance(source_record, Mapping):
                raise ConceptClosureError("committed source record is not an object")
            record = dict(source_record)
            anchor = record.get("anchor")
            ordinal = record.get("ordinal")
            if not isinstance(anchor, str) or not anchor or anchor in records:
                raise ConceptClosureError("committed source record has a duplicate anchor")
            unit_payload = {"kind": kind, **record}
            observed_units.append(
                {
                    "unit_id": anchor,
                    "kind": kind,
                    "ordinal": ordinal,
                    "sha256": _canonical_sha256(unit_payload),
                }
            )
            if kind == "paragraph":
                text = record.get("text")
                if not isinstance(text, str):
                    raise ConceptClosureError("committed paragraph text is invalid")
                records[anchor] = text
            else:
                rows = record.get("rows")
                if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
                    raise ConceptClosureError("committed table rows are invalid")
                rendered_rows: list[str] = []
                for row in rows:
                    if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
                        raise ConceptClosureError("committed table row is invalid")
                    rendered_rows.append(" | ".join(str(cell) for cell in row))
                records[anchor] = "\n".join(rendered_rows)

    expected_units = manifest_document.get("source_units")
    if observed_units != expected_units:
        raise ConceptClosureError(
            "committed source records differ from the externally sealed manifest"
        )
    return records


def _nested_source_ref_lists(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if isinstance(value, Mapping):
        for field, nested in value.items():
            if (
                field == "source_refs"
                and isinstance(nested, Sequence)
                and not isinstance(nested, (str, bytes))
            ):
                found.append(nested)
            found.extend(_nested_source_ref_lists(nested))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for nested in value:
            found.extend(_nested_source_ref_lists(nested))
    return tuple(found)


def _contract_document_validator() -> Draft202012Validator:
    return Draft202012Validator(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": _CONTRACT_DOCUMENT_REF,
        },
        registry=build_schema_registry(),
    )


def _normalized_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _phase(
    schema_name: str,
    artifact: Mapping[str, object],
    *,
    schema_id: str,
    run_id: str,
    version_binding: Mapping[str, object],
    phase_id: str,
    label: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(artifact, label=label)
    try:
        return validate_phase_artifact(
            schema_name,
            snapshot,
            expected_schema_id=schema_id,
            expected_run_id=run_id,
            expected_version_binding=version_binding,
            expected_phase_id=phase_id,
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise ConceptClosureError(f"invalid {label}: {error}") from error


def _validate_upstream(
    document: Mapping[str, Any],
    *,
    evidence_ledger: Mapping[str, object],
    world_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    evidence = _phase(
        "ultra-evidence-ledger.schema.json",
        evidence_ledger,
        schema_id="crossframe.ultra.v82.evidence-ledger",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U3",
        label="U3 evidence ledger",
    )
    world = _phase(
        "ultra-world-volume.schema.json",
        world_volume,
        schema_id="crossframe.ultra.v82.world-volume",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U4",
        label="U4 world volume",
    )
    transformations = _phase(
        "ultra-transformation-ledger.schema.json",
        transformation_ledger,
        schema_id="crossframe.ultra.v82.transformation-ledger",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U5",
        label="U5 transformation ledger",
    )
    if _canonical_sha256(evidence) != expected_evidence_artifact_sha256:
        raise ConceptClosureError("U3 full artifact hash differs from external authority")
    if _canonical_sha256(world) != expected_world_volume_artifact_sha256:
        raise ConceptClosureError("U4 full artifact hash differs from external authority")
    if (
        _canonical_sha256(transformations)
        != expected_transformation_ledger_artifact_sha256
    ):
        raise ConceptClosureError("U5 full artifact hash differs from external authority")
    expected_chain = {
        "evidence_artifact_sha256": expected_evidence_artifact_sha256,
        "evidence_content_sha256": evidence["content_sha256"],
        "world_volume_artifact_sha256": expected_world_volume_artifact_sha256,
        "world_volume_content_sha256": world["content_sha256"],
        "transformation_ledger_artifact_sha256": (
            expected_transformation_ledger_artifact_sha256
        ),
        "transformation_ledger_content_sha256": transformations["content_sha256"],
    }
    if any(document[field] != value for field, value in expected_chain.items()):
        raise ConceptClosureError("concept artifact carries a stale upstream hash chain")
    return evidence, world, transformations


def _authority_paths(repo: Path) -> tuple[Path, Path, Path, Path]:
    if not isinstance(repo, Path):
        raise ConceptClosureError("repo must be a Path")
    references = repo.resolve() / "skills" / "crossframe-ultra" / "references"
    contracts = references / "concept-contracts"
    return (
        references / "concept-registry" / "v8.2-concept-registry.json",
        references / "v8.2-route-map.json",
        contracts / "v8.2-contract-map.json",
        contracts,
    )


def _validate_file_authorities(
    document: Mapping[str, Any],
    *,
    repo: Path,
    expected_version_binding: Mapping[str, object],
    expected_registry_sha256: str,
    expected_route_map_sha256: str,
    expected_contract_map_sha256: str,
    expected_source_manifest_sha256: str,
) -> tuple[
    dict[str, Mapping[str, Any]],
    dict[str, Mapping[str, Any]],
    dict[str, Mapping[str, Any]],
    dict[str, frozenset[str]],
    dict[str, str],
]:
    registry_path, route_path, contract_map_path, contracts_dir = _authority_paths(repo)
    source_manifest_path = (
        repo.resolve()
        / "skills"
        / "crossframe-ultra"
        / "references"
        / "source-manifest.json"
    )
    try:
        manifest = load_source_manifest(
            source_manifest_path,
            expected_sha256=expected_source_manifest_sha256,
        )
    except (OSError, SourceManifestError, TypeError, ValueError) as error:
        raise ConceptClosureError(f"invalid source manifest authority: {error}") from error
    source_units = frozenset(
        record["unit_id"] for record in manifest.document["source_units"]
    )
    source_records = _validated_source_records(
        repo,
        manifest_document=manifest.document,
        expected_manifest_sha256=expected_source_manifest_sha256,
    )
    registry_raw, registry = _load_json_bytes(registry_path, label="concept registry")
    route_raw, route_map = _load_json_bytes(route_path, label="route map")
    contract_raw, contract_map = _load_json_bytes(contract_map_path, label="contract map")
    computed = {
        "registry_sha256": hashlib.sha256(registry_raw).hexdigest(),
        "route_map_sha256": hashlib.sha256(route_raw).hexdigest(),
        "contract_map_sha256": hashlib.sha256(contract_raw).hexdigest(),
    }
    expected = {
        "registry_sha256": expected_registry_sha256,
        "route_map_sha256": expected_route_map_sha256,
        "contract_map_sha256": expected_contract_map_sha256,
    }
    if computed != expected:
        raise ConceptClosureError("knowledge authority raw-byte hash differs externally")
    if any(document[field] != value for field, value in computed.items()):
        raise ConceptClosureError("concept artifact binds another knowledge authority")
    try:
        validate_instance("ultra-concept-registry.schema.json", registry)
        validate_instance("ultra-route-map.schema.json", route_map)
        validate_instance("ultra-contract-map.schema.json", contract_map)
    except (ValidationError, UltraSchemaError) as error:
        raise ConceptClosureError(f"knowledge authority violates frozen schema: {error}") from error

    raw_sha = expected_version_binding["framework_raw_sha256"]
    semantic_sha = expected_version_binding["framework_semantic_sha256"]
    for authority in (registry, route_map, contract_map):
        if (
            authority["framework_version"] != "v8.2"
            or authority["framework_revision"] != "v8.2"
            or authority["raw_sha256"] != raw_sha
            or authority["semantic_sha256"] != semantic_sha
        ):
            raise ConceptClosureError("knowledge authority metadata drifts from version binding")

    concepts = _records_by_id(registry["concepts"], field="concept_id", label="concept")
    routes = _records_by_id(route_map["routes"], field="route_id", label="route")
    contracts = _records_by_id(
        contract_map["contracts"], field="contract_id", label="contract"
    )
    if registry["concept_count"] != len(concepts):
        raise ConceptClosureError("concept registry count is stale")
    if route_map["route_count"] != len(routes):
        raise ConceptClosureError("route map count is stale")
    if contract_map["contract_count"] != len(contracts):
        raise ConceptClosureError("contract map count is stale")

    canonical_names = [_normalized_name(record["canonical_zh"]) for record in concepts.values()]
    if any(not name for name in canonical_names) or len(canonical_names) != len(
        set(canonical_names)
    ):
        raise ConceptClosureError("concept registry has an empty or duplicate canonical name")
    for concept_id, concept in concepts.items():
        _source_ids(
            concept["source_anchors"],
            source_units=source_units,
            label=f"{concept_id} source_anchors",
        )
        for field in ("prerequisites", "required_neighbors", "conflicts"):
            related = _checked_ids(concept[field], label=f"{concept_id} {field}")
            if not set(related).issubset(concepts):
                raise ConceptClosureError(f"{concept_id} has a dangling {field} reference")
        for neighbor in concept["required_neighbors"]:
            if concept_id not in concepts[neighbor]["required_neighbors"]:
                raise ConceptClosureError("concept registry lacks a required-neighbor backlink")
        for conflict in concept["conflicts"]:
            if concept_id not in concepts[conflict]["conflicts"]:
                raise ConceptClosureError("concept registry lacks a conflict backlink")
    semantic_errors: list[str] = []
    checker_concepts = _checker_validate_concepts(
        registry,
        source_records,
        semantic_errors,
    )
    if semantic_errors or set(checker_concepts) != set(concepts):
        detail = semantic_errors[0] if semantic_errors else "concept set mismatch"
        raise ConceptClosureError(
            f"concept registry violates approved source semantics: {detail}"
        )

    contracts_root = contracts_dir.resolve()
    validator = _contract_document_validator()
    listed_files: list[str] = []
    contract_concepts: dict[str, frozenset[str]] = {}
    requirement_owners: dict[str, str] = {}
    checker_requirements: dict[
        str, tuple[str, Mapping[str, object], set[str]]
    ] = {}
    covered_contract_concepts: set[str] = set()
    metadata_fields = (
        "framework_version",
        "framework_revision",
        "raw_sha256",
        "semantic_sha256",
    )
    for contract_id, contract in contracts.items():
        filename = contract["file"]
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
            or filename in listed_files
        ):
            raise ConceptClosureError("contract map has an unsafe or duplicate file")
        listed_files.append(filename)
        contract_path = (contracts_root / filename).resolve()
        if contract_path.parent != contracts_root or contract_path.name != filename:
            raise ConceptClosureError("contract map file path escapes its authority directory")
        raw, contract_document = _load_json_bytes(
            contract_path, label=f"contract document {contract_id}"
        )
        if hashlib.sha256(raw).hexdigest() != contract["file_sha256"]:
            raise ConceptClosureError("contract map file_sha256 entry is stale")
        try:
            validator.validate(contract_document)
        except ValidationError as error:
            raise ConceptClosureError(
                f"contract document violates frozen contractDocument schema: {error}"
            ) from error
        entry_concepts = _checked_ids(
            contract["concept_ids"], label=f"{contract_id} map concept_ids"
        )
        document_concepts = _checked_ids(
            contract_document["concept_ids"],
            label=f"{contract_id} document concept_ids",
        )
        entry_anchors = _source_ids(
            contract["source_anchors"],
            source_units=source_units,
            label=f"{contract_id} map source_anchors",
        )
        document_anchors = _source_ids(
            contract_document["source_anchors"],
            source_units=source_units,
            label=f"{contract_id} document source_anchors",
        )
        if (
            contract_document["contract_id"] != contract_id
            or entry_concepts != document_concepts
            or entry_anchors != document_anchors
            or any(
                contract_document[field] != contract_map[field]
                for field in metadata_fields
            )
        ):
            raise ConceptClosureError("contract map and document metadata diverge")
        if not set(entry_concepts).issubset(concepts):
            raise ConceptClosureError("contract map names an unknown concept")
        contract_concepts[contract_id] = frozenset(entry_concepts)
        covered_contract_concepts.update(entry_concepts)

        owner_anchors = set(document_anchors)
        responsibility_sources = [source_records[anchor] for anchor in document_anchors]
        unsupported_responsibility = _checker_unsupported_semantic_units(
            contract_document["responsibility"],
            responsibility_sources,
        )
        if unsupported_responsibility:
            raise ConceptClosureError(
                f"{contract_id} responsibility is unsupported by source anchors"
            )
        for requirement in contract_document["machine_requirements"]:
            requirement_id = requirement["requirement_id"]
            if requirement_id in requirement_owners:
                raise ConceptClosureError("machine requirement ID is duplicated")
            requirement_owners[requirement_id] = contract_id
            checker_requirements[requirement_id] = (
                contract_id,
                requirement,
                owner_anchors,
            )
            for source_refs in _nested_source_ref_lists(requirement):
                checked_refs = _source_ids(
                    source_refs,
                    source_units=source_units,
                    label=f"{requirement_id} source_refs",
                    allow_empty=True,
                )
                if not set(checked_refs).issubset(owner_anchors):
                    raise ConceptClosureError(
                        "machine requirement source_refs escape owner anchors"
                    )

        clauses = _records_by_id(
            contract_document["clauses"],
            field="clause_id",
            label=f"{contract_id} clause",
        )
        for clause_id, clause in clauses.items():
            clause_anchors = _source_ids(
                clause["source_anchors"],
                source_units=source_units,
                label=f"{clause_id} source_anchors",
            )
            unsupported_clause = _checker_unsupported_semantic_units(
                clause["statement"],
                [source_records[anchor] for anchor in clause_anchors],
            )
            if unsupported_clause:
                raise ConceptClosureError(
                    f"{clause_id} statement is unsupported by source anchors"
                )

    try:
        discovered_files = {
            path.name
            for path in contracts_root.iterdir()
            if path.is_file()
            and path.suffix.casefold() == ".json"
            and path.name != contract_map_path.name
        }
    except OSError as error:
        raise ConceptClosureError(f"cannot enumerate contract authority files: {error}") from error
    if discovered_files != set(listed_files):
        raise ConceptClosureError("contract authority has a missing or orphan document")
    if covered_contract_concepts != set(concepts):
        raise ConceptClosureError("contract map does not cover every registry concept")
    requirement_errors: list[str] = []
    checker_owners = _checker_validate_requirements(
        checker_requirements,
        source_records,
        requirement_errors,
    )
    if requirement_errors or checker_owners != requirement_owners:
        detail = requirement_errors[0] if requirement_errors else "owner mismatch"
        raise ConceptClosureError(
            f"contract requirements violate approved source semantics: {detail}"
        )

    covered_route_concepts: set[str] = set()
    covered_route_contracts: set[str] = set()
    covered_route_requirements: set[str] = set()
    concept_route_counts = {concept_id: 0 for concept_id in concepts}
    for route_id, route in routes.items():
        _source_ids(
            route["source_anchors"],
            source_units=source_units,
            label=f"{route_id} source_anchors",
        )
        route_concepts = _checked_ids(
            route["concept_ids"], label=f"{route_id} concept_ids"
        )
        route_contracts = _checked_ids(
            route["contract_ids"], label=f"{route_id} contract_ids"
        )
        route_requirements = _checked_ids(
            route["requirement_ids"], label=f"{route_id} requirement_ids"
        )
        if not route_concepts or not route_contracts or not route_requirements:
            raise ConceptClosureError("route concept, contract, and requirement lists are required")
        if not set(route_concepts).issubset(concepts):
            raise ConceptClosureError("route map names an unknown concept")
        if not set(route_contracts).issubset(contracts):
            raise ConceptClosureError("route map names an unknown contract")
        if not set(route_requirements).issubset(requirement_owners):
            raise ConceptClosureError("route map names an unknown machine requirement")
        for concept_id in route_concepts:
            concept_route_counts[concept_id] += 1
        for requirement_id in route_requirements:
            if requirement_owners[requirement_id] not in route_contracts:
                raise ConceptClosureError("route omits a machine requirement owner contract")
        expected_contracts = {
            contract_id
            for contract_id, supported_concepts in contract_concepts.items()
            if set(route_concepts) & supported_concepts
        }
        if set(route_contracts) != expected_contracts:
            raise ConceptClosureError("route concept-contract compatibility diverges")
        covered_route_concepts.update(route_concepts)
        covered_route_contracts.update(route_contracts)
        covered_route_requirements.update(route_requirements)

    if (
        covered_route_concepts != set(concepts)
        or covered_route_contracts != set(contracts)
        or covered_route_requirements != set(requirement_owners)
        or any(count != 1 for count in concept_route_counts.values())
        or len(routes) != len(concepts)
    ):
        raise ConceptClosureError("complete route partition or authority closure is invalid")
    route_errors: list[str] = []
    _checker_validate_routes(
        route_map,
        checker_concepts,
        set(contracts),
        contract_concepts,
        requirement_owners,
        source_records,
        route_errors,
    )
    if route_errors:
        raise ConceptClosureError(
            f"route map violates approved source semantics: {route_errors[0]}"
        )
    return concepts, routes, contracts, contract_concepts, requirement_owners


def _route_closure(
    concepts: Mapping[str, Mapping[str, Any]],
    routes: Mapping[str, Mapping[str, Any]],
    required_route_ids: tuple[str, ...],
) -> tuple[frozenset[str], frozenset[str], frozenset[str], frozenset[str]]:
    if not required_route_ids or not set(required_route_ids).issubset(routes):
        raise ConceptClosureError("required routes are empty or unknown")
    concept_routes: dict[str, set[str]] = {concept_id: set() for concept_id in concepts}
    for route_id, route in routes.items():
        for concept_id in route["concept_ids"]:
            concept_routes.setdefault(concept_id, set()).add(route_id)
    required_routes: set[str] = set()
    required_concepts: set[str] = set()
    required_contracts: set[str] = set()
    required_requirements: set[str] = set()

    def add_route(route_id: str) -> tuple[str, ...]:
        if route_id in required_routes:
            return ()
        required_routes.add(route_id)
        route = routes[route_id]
        required_contracts.update(route["contract_ids"])
        required_requirements.update(route["requirement_ids"])
        added: list[str] = []
        for concept_id in route["concept_ids"]:
            if concept_id not in required_concepts:
                required_concepts.add(concept_id)
                added.append(concept_id)
        return tuple(added)

    queue: deque[str] = deque()
    for route_id in required_route_ids:
        queue.extend(add_route(route_id))
    while queue:
        concept_id = queue.popleft()
        concept = concepts.get(concept_id)
        if concept is None:
            raise ConceptClosureError("route or neighbor names an unknown concept")
        for neighbor in concept["required_neighbors"]:
            if neighbor not in concepts:
                raise ConceptClosureError("concept registry has an unknown neighbor")
            if neighbor not in required_concepts:
                required_concepts.add(neighbor)
                queue.append(neighbor)
            owner_routes = concept_routes.get(neighbor, set())
            if not owner_routes:
                raise ConceptClosureError("neighbor concept lacks an owner route")
            for route_id in sorted(owner_routes):
                queue.extend(add_route(route_id))
    return (
        frozenset(required_concepts),
        frozenset(required_routes),
        frozenset(required_contracts),
        frozenset(required_requirements),
    )


def _boilerplate_skeleton(
    value: str, *, concept_ids: Collection[str]
) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
    )
    for operator, token in (
        (">=", " operator_greater_equal "),
        ("<=", " operator_less_equal "),
        ("!=", " operator_not_equal "),
        ("==", " operator_equal "),
        ("≥", " operator_greater_equal "),
        ("≤", " operator_less_equal "),
        ("≠", " operator_not_equal "),
        (">", " operator_greater_than "),
        ("<", " operator_less_than "),
        ("=", " operator_equal "),
    ):
        normalized = normalized.replace(operator, token)
    for concept_id in sorted(concept_ids, key=len, reverse=True):
        normalized = re.sub(
            rf"(?<!\w){re.escape(concept_id.casefold())}(?!\w)",
            " concepttoken ",
            normalized,
        )
    for status in sorted(_STATUSES, key=len, reverse=True):
        normalized = re.sub(
            rf"(?<!\w){re.escape(status)}(?!\w)",
            " statustoken ",
            normalized,
        )
    normalized = _STANDALONE_ROMAN_ORDINAL_RE.sub(" ordinaltoken ", normalized)
    normalized = _STANDALONE_ENGLISH_ORDINAL_RE.sub(" ordinaltoken ", normalized)
    normalized = _STANDALONE_CHINESE_ORDINAL_RE.sub(" ordinaltoken ", normalized)
    normalized = _STANDALONE_ORDINAL_RE.sub(" ordinaltoken ", normalized)
    normalized = "".join(
        " "
        if character == "_" or unicodedata.category(character)[0] in {"P", "S"}
        else character
        for character in normalized
    )
    return " ".join(normalized.split())


def _require_independent_texts(
    values: Sequence[str], *, concept_ids: Collection[str], label: str
) -> None:
    skeletons = [
        _boilerplate_skeleton(value, concept_ids=concept_ids) for value in values
    ]
    if len(skeletons) != len(set(skeletons)):
        raise ConceptClosureError(f"copied boilerplate {label} is not independent")


def validate_required_concept_semantic_units(
    document: Mapping[str, object],
    expected_unit_ids: Collection[str],
) -> tuple[str, ...]:
    snapshot = _snapshot_mapping(document, label="concept disposition")
    expected = _checked_ids(
        expected_unit_ids,
        label="required concept semantic unit IDs",
    )
    obligations = snapshot.get("semantic_obligations")
    if not isinstance(obligations, list):
        raise ConceptClosureError(
            "concept disposition semantic obligations are unavailable"
        )
    retained: list[str] = []
    for index, obligation in enumerate(obligations):
        if not isinstance(obligation, Mapping):
            raise ConceptClosureError(
                f"semantic obligation {index} must be a mapping"
            )
        status = obligation.get("status")
        unit_id = obligation.get("semantic_unit_id")
        if status in _RETURNED_STATUSES:
            if not isinstance(unit_id, str) or not unit_id:
                raise ConceptClosureError(
                    "retained semantic obligation has no semantic unit ID"
                )
            retained.append(unit_id)
    if len(retained) != len(set(retained)):
        raise ConceptClosureError("concept disposition repeats a semantic unit ID")
    if set(retained) != set(expected) or len(retained) != len(expected):
        raise ConceptClosureError(
            "semantic review concept unit set differs from validate_concept_closure"
        )
    return tuple(sorted(retained))


def validate_concept_closure(
    document: Mapping[str, object],
    *,
    repo: Path,
    evidence_ledger: Mapping[str, object],
    world_volume: Mapping[str, object],
    transformation_ledger: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_source_manifest_sha256: str,
    expected_evidence_artifact_sha256: str,
    expected_world_volume_artifact_sha256: str,
    expected_transformation_ledger_artifact_sha256: str,
    expected_registry_sha256: str,
    expected_route_map_sha256: str,
    expected_contract_map_sha256: str,
    required_route_ids: Collection[str],
) -> frozenset[str]:
    (
        expected_run_id,
        expected_version_binding,
        expected_source_manifest_sha256,
        expected_evidence_artifact_sha256,
        expected_world_volume_artifact_sha256,
        expected_transformation_ledger_artifact_sha256,
        expected_registry_sha256,
        expected_route_map_sha256,
        expected_contract_map_sha256,
    ) = _validated_public_authorities(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_source_manifest_sha256=expected_source_manifest_sha256,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        expected_world_volume_artifact_sha256=expected_world_volume_artifact_sha256,
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
        expected_registry_sha256=expected_registry_sha256,
        expected_route_map_sha256=expected_route_map_sha256,
        expected_contract_map_sha256=expected_contract_map_sha256,
    )
    snapshot = _snapshot_mapping(document, label="concept disposition")
    snapshot = _phase(
        "ultra-concept-disposition.schema.json",
        snapshot,
        schema_id="crossframe.ultra.v82.concept-disposition",
        run_id=expected_run_id,
        version_binding=expected_version_binding,
        phase_id="U5",
        label="U5 concept disposition",
    )
    evidence, world, transformations = _validate_upstream(
        snapshot,
        evidence_ledger=evidence_ledger,
        world_volume=world_volume,
        transformation_ledger=transformation_ledger,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        expected_world_volume_artifact_sha256=expected_world_volume_artifact_sha256,
        expected_transformation_ledger_artifact_sha256=(
            expected_transformation_ledger_artifact_sha256
        ),
    )
    concepts, routes, contracts, _, _ = _validate_file_authorities(
        snapshot,
        repo=repo,
        expected_version_binding=expected_version_binding,
        expected_registry_sha256=expected_registry_sha256,
        expected_route_map_sha256=expected_route_map_sha256,
        expected_contract_map_sha256=expected_contract_map_sha256,
        expected_source_manifest_sha256=expected_source_manifest_sha256,
    )

    checked_routes = _checked_ids(required_route_ids, label="required_route_ids")
    if set(snapshot["required_route_ids"]) != set(checked_routes) or len(
        snapshot["required_route_ids"]
    ) != len(checked_routes):
        raise ConceptClosureError("document routes differ from caller-frozen routes")
    (
        required_concepts,
        closure_routes,
        required_contracts,
        required_requirements,
    ) = _route_closure(concepts, routes, checked_routes)
    if set(snapshot["required_contract_ids"]) != set(required_contracts):
        raise ConceptClosureError("top-level contract closure is stale")
    if set(snapshot["required_requirement_ids"]) != set(required_requirements):
        raise ConceptClosureError("top-level requirement closure is stale")
    if not required_contracts.issubset(contracts):
        raise ConceptClosureError("required contract closure is unresolved")

    dispositions = _records_by_id(
        snapshot["dispositions"], field="concept_id", label="disposition"
    )
    obligations = _records_by_id(
        snapshot["semantic_obligations"], field="obligation_id", label="obligation"
    )
    if set(dispositions) != set(concepts):
        raise ConceptClosureError("every registry concept requires exactly one disposition")
    if snapshot["closure_complete"] is not True or snapshot["unvisited_concept_ids"] != []:
        raise ConceptClosureError("concept registry closure is incomplete")

    evidence_ids = {record["evidence_id"] for record in evidence["entries"]}
    unknown_ids = {record["unknown_id"] for record in world["unknowns"]}
    transform_ids = {
        record["transform_id"] for record in transformations["transformations"]
    }
    disposition_obligation_ids: set[str] = set()
    semantic_unit_ids: list[str] = []
    branch_ids: list[str] = []
    plan_ids: list[str] = []
    pending_conditions: list[str] = []
    pending_evidence_items: list[str] = []
    retained: set[str] = set()

    _require_independent_texts(
        [record["rationale"] for record in dispositions.values()],
        concept_ids=concepts,
        label="rationale",
    )
    for concept_id, disposition in dispositions.items():
        concept = concepts[concept_id]
        status = disposition["status"]
        if status not in _STATUSES:
            raise ConceptClosureError("disposition status is not terminal")
        direct_routes = sorted(
            route_id
            for route_id in closure_routes
            if concept_id in routes[route_id]["concept_ids"]
        )
        direct_contracts = sorted(
            {
                contract_id
                for route_id in direct_routes
                for contract_id in routes[route_id]["contract_ids"]
            }
        )
        direct_requirements = sorted(
            {
                requirement_id
                for route_id in direct_routes
                for requirement_id in routes[route_id]["requirement_ids"]
            }
        )
        if (
            disposition["route_required"] is not (concept_id in required_concepts)
            or disposition["neighbor_concept_ids"] != concept["required_neighbors"]
            or disposition["route_ids"] != direct_routes
            or disposition["contract_ids"] != direct_contracts
            or disposition["requirement_ids"] != direct_requirements
        ):
            raise ConceptClosureError("disposition differs from route/neighbor closure")
        if (
            not set(disposition["evidence_ids"]).issubset(evidence_ids)
            or not set(disposition["unknown_ids"]).issubset(unknown_ids)
            or not set(disposition["transformation_ids"]).issubset(transform_ids)
        ):
            raise ConceptClosureError("disposition does not reach sealed U3/U4/U5 refs")
        if status in {"applied", "tested-rejected"} and (
            not disposition["evidence_ids"]
            or not disposition["transformation_ids"]
        ):
            raise ConceptClosureError(
                "substantive disposition lacks evidence or transformation authority"
            )

        obligation_ids = disposition["obligation_ids"]
        if len(obligation_ids) != len(set(obligation_ids)):
            raise ConceptClosureError("disposition repeats an obligation ID")
        disposition_obligation_ids.update(obligation_ids)
        branch = disposition["condition_branch"]
        if status == "not-applicable":
            if (
                obligation_ids
                or disposition["evidence_ids"]
                or disposition["unknown_ids"]
                or disposition["transformation_ids"]
                or branch is not None
            ):
                raise ConceptClosureError("not-applicable disposition claims output material")
        else:
            if len(obligation_ids) != 1:
                raise ConceptClosureError("applicable disposition needs one semantic obligation")
        if status == "unknown-pending":
            if branch is None:
                raise ConceptClosureError("unknown-pending disposition lacks its branch")
            branch_ids.append(branch["branch_id"])
            plan_ids.append(branch["evidence_plan"]["plan_id"])
            pending_conditions.append(branch["condition"])
            pending_evidence_items.extend(branch["evidence_plan"]["required_evidence"])
        elif branch is not None:
            raise ConceptClosureError("nonpending disposition cannot carry a branch")

        for obligation_id in obligation_ids:
            obligation = obligations.get(obligation_id)
            if obligation is None:
                raise ConceptClosureError("disposition obligation is unresolved")
            expected_branch_id = None if branch is None else branch["branch_id"]
            if (
                obligation["concept_id"] != concept_id
                or obligation["status"] != status
                or obligation["evidence_ids"] != disposition["evidence_ids"]
                or obligation["unknown_ids"] != disposition["unknown_ids"]
                or obligation["transformation_ids"] != disposition["transformation_ids"]
                or obligation["route_ids"] != disposition["route_ids"]
                or obligation["contract_ids"] != disposition["contract_ids"]
                or obligation["requirement_ids"] != disposition["requirement_ids"]
                or obligation["condition_branch_id"] != expected_branch_id
            ):
                raise ConceptClosureError("semantic obligation differs from its disposition")
            semantic_unit_ids.append(obligation["semantic_unit_id"])
            if status in _RETURNED_STATUSES:
                retained.add(obligation["semantic_unit_id"])

    if disposition_obligation_ids != set(obligations):
        raise ConceptClosureError("semantic obligation is orphaned or cross-concept")
    for values, label in (
        (semantic_unit_ids, "semantic unit"),
        (branch_ids, "condition branch"),
        (plan_ids, "evidence plan"),
    ):
        if len(values) != len(set(values)):
            raise ConceptClosureError(f"duplicate {label} ID")
    _require_independent_texts(
        pending_conditions, concept_ids=concepts, label="pending condition"
    )
    _require_independent_texts(
        pending_evidence_items, concept_ids=concepts, label="pending evidence item"
    )
    return frozenset(retained)


__all__ = (
    "ConceptClosureError",
    "validate_concept_closure",
    "validate_required_concept_semantic_units",
)
