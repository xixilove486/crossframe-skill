from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping, Sequence

from jsonschema import ValidationError

from .jsonio import load_json_bytes
from .safe_files import read_stable_regular_file
from .source_integrity import (
    V8_CONCEPT_COUNT,
    V8_CONTROL_ASSET_SHA256,
    V8_SOURCE_SNAPSHOT_SHA256,
)
from .validation import validate_bound_document


TERMINAL_CONCEPT_STATUSES = {
    "applied",
    "tested_rejected",
    "not_applicable",
    "unknown_pending",
}


class ConceptClosureError(ValueError):
    """Raised when a disposition ledger only claims, but does not prove, closure."""


def _load_exact_object(
    path: Path,
    *,
    root: Path,
    expected_sha256: str,
) -> dict[str, object]:
    raw = read_stable_regular_file(path, within_root=root)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ConceptClosureError(f"canonical v8 graph hash mismatch: {path}")
    value = load_json_bytes(raw, source=str(path))
    if not isinstance(value, dict):
        raise ConceptClosureError(f"canonical v8 graph must be an object: {path}")
    return value


def _required_misuse_exclusions(concept: Mapping[str, object]) -> list[str]:
    result: list[str] = []
    for field in ("common_misuses", "forbidden_substitutions_or_generalizations"):
        values = concept.get(field)
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise ConceptClosureError(
                f"canonical concept has invalid {field}: {concept.get('concept_id')!r}"
            )
        for item in values:
            if item not in result:
                result.append(item)
    return result


def _checked_string_sequence(value: object, *, field: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ConceptClosureError(f"{field} must be a non-empty string sequence")
    result = tuple(value)
    if len(set(result)) != len(result):
        raise ConceptClosureError(f"{field} must not contain duplicates")
    return result


def validate_concept_disposition(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    """Validate the closed P4 artifact shape and immutable run binding.

    Registry-wide disposition and neighbor closure are deliberately enforced by
    the semantic artifact validator, not inferred by this schema-bound helper.
    """

    return validate_bound_document(
        "promax-concept-disposition.schema.json",
        document,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )


def validate_concept_closure(
    document: Mapping[str, object],
    *,
    repo: Path | str,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
    required_route_ids: Sequence[str],
) -> dict[str, object]:
    """Validate all 709 terminal dispositions against exact registry/routes."""

    try:
        normalized = validate_concept_disposition(
            document,
            expected_run_id=expected_run_id,
            expected_source_snapshot_sha256=expected_source_snapshot_sha256,
        )
    except ValidationError as error:
        raise ConceptClosureError(
            f"concept disposition violates its schema: {error.message}"
        ) from error
    if expected_source_snapshot_sha256 != V8_SOURCE_SNAPSHOT_SHA256:
        raise ConceptClosureError("concept closure must bind the exact v8 snapshot")

    repo_root = Path(repo).resolve()
    references = repo_root / "skills" / "crossframe-promax" / "references"
    registry_path = references / "concept-registry" / "v8-concept-registry.json"
    route_path = references / "v8-route-map.json"
    registry = _load_exact_object(
        registry_path,
        root=references,
        expected_sha256=V8_CONTROL_ASSET_SHA256["concept_registry"],
    )
    route_map = _load_exact_object(
        route_path,
        root=references,
        expected_sha256=V8_CONTROL_ASSET_SHA256["route_map"],
    )
    if (
        registry.get("schema_id") != "crossframe.promax.v8.concept-registry"
        or registry.get("framework_version") != "v8.0"
        or registry.get("snapshot_sha256") != V8_SOURCE_SNAPSHOT_SHA256
        or registry.get("concept_count") != V8_CONCEPT_COUNT
    ):
        raise ConceptClosureError("canonical v8 concept registry metadata mismatch")
    if (
        route_map.get("schema_id") != "crossframe.promax.v8.route-map"
        or route_map.get("framework_version") != "v8.0"
        or route_map.get("snapshot_sha256") != V8_SOURCE_SNAPSHOT_SHA256
        or route_map.get("route_count") != 16
    ):
        raise ConceptClosureError("canonical v8 route map metadata mismatch")
    if normalized.get("registry_sha256") != V8_CONTROL_ASSET_SHA256["concept_registry"]:
        raise ConceptClosureError("concept disposition is bound to another registry")

    raw_concepts = registry.get("concepts")
    raw_routes = route_map.get("routes")
    if not isinstance(raw_concepts, list) or len(raw_concepts) != V8_CONCEPT_COUNT:
        raise ConceptClosureError("canonical registry must contain exactly 709 concepts")
    if not isinstance(raw_routes, list) or len(raw_routes) != 16:
        raise ConceptClosureError("canonical route map must contain exactly 16 routes")

    concepts: dict[str, Mapping[str, object]] = {}
    for concept in raw_concepts:
        if not isinstance(concept, Mapping):
            raise ConceptClosureError("canonical concept record must be an object")
        concept_id = concept.get("concept_id")
        if not isinstance(concept_id, str) or concept_id in concepts:
            raise ConceptClosureError(f"invalid canonical concept id: {concept_id!r}")
        concepts[concept_id] = concept
    routes: dict[str, Mapping[str, object]] = {}
    for route in raw_routes:
        if not isinstance(route, Mapping):
            raise ConceptClosureError("canonical route record must be an object")
        route_id = route.get("route_id")
        if not isinstance(route_id, str) or route_id in routes:
            raise ConceptClosureError(f"invalid canonical route id: {route_id!r}")
        routes[route_id] = route

    required_routes = _checked_string_sequence(
        required_route_ids,
        field="required_route_ids",
    )
    unknown_required_routes = set(required_routes) - set(routes)
    if unknown_required_routes:
        raise ConceptClosureError(
            f"unknown required routes: {sorted(unknown_required_routes)!r}"
        )
    document_routes = normalized.get("route_ids")
    if not isinstance(document_routes, list) or set(document_routes) != set(required_routes):
        raise ConceptClosureError(
            "concept disposition route_ids must exactly match required_route_ids"
        )

    raw_dispositions = normalized.get("dispositions")
    if not isinstance(raw_dispositions, list):
        raise ConceptClosureError("concept dispositions must be an array")
    dispositions: dict[str, Mapping[str, object]] = {}
    for disposition in raw_dispositions:
        if not isinstance(disposition, Mapping):
            raise ConceptClosureError("concept disposition record must be an object")
        concept_id = disposition.get("concept_id")
        if not isinstance(concept_id, str) or concept_id in dispositions:
            raise ConceptClosureError(
                f"duplicate or invalid concept disposition id: {concept_id!r}"
            )
        dispositions[concept_id] = disposition
    if set(dispositions) != set(concepts) or len(dispositions) != V8_CONCEPT_COUNT:
        missing = sorted(set(concepts) - set(dispositions))
        extra = sorted(set(dispositions) - set(concepts))
        raise ConceptClosureError(
            f"concept terminal inventory mismatch; missing={missing[:5]!r}, extra={extra[:5]!r}"
        )
    if normalized.get("closure_complete") is not True:
        raise ConceptClosureError("concept closure_complete must be true")
    if normalized.get("unchecked_concept_ids") != []:
        raise ConceptClosureError("concept closure cannot retain unchecked concepts")

    for concept_id, disposition in dispositions.items():
        concept = concepts[concept_id]
        status = disposition.get("status")
        if status not in TERMINAL_CONCEPT_STATUSES:
            raise ConceptClosureError(
                f"concept does not have a terminal disposition: {concept_id}"
            )
        expected_neighbors = concept.get("required_neighbor_ids")
        if not isinstance(expected_neighbors, list) or disposition.get(
            "required_neighbor_ids"
        ) != expected_neighbors:
            raise ConceptClosureError(
                f"required-neighbor closure mismatch for {concept_id}"
            )
        expected_misuses = _required_misuse_exclusions(concept)
        if disposition.get("misuses_excluded") != expected_misuses:
            raise ConceptClosureError(f"misuse exclusion mismatch for {concept_id}")
        if status in {"applied", "tested_rejected"} and not disposition.get(
            "evidence_refs"
        ):
            raise ConceptClosureError(
                f"evidence-bearing terminal status lacks evidence refs: {concept_id}"
            )

    for route_id in required_routes:
        route = routes[route_id]
        for field in ("required_concept_ids", "neighbor_closure_ids"):
            route_concepts = route.get(field)
            if not isinstance(route_concepts, list) or any(
                not isinstance(item, str) for item in route_concepts
            ):
                raise ConceptClosureError(f"route {route_id} has invalid {field}")
            missing = set(route_concepts) - set(dispositions)
            if missing:
                raise ConceptClosureError(
                    f"route {route_id} lacks terminal {field}: {sorted(missing)[:5]!r}"
                )
    return normalized
