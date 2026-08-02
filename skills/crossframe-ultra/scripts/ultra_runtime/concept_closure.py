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

from jsonschema import ValidationError

from .schemas import validate_instance


_RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
_SEMANTIC_SHA256 = (
    "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
)
_REGISTRY_SHA256 = (
    "8c88d2b3d47c378b7beccd74082f8b460f5e91780f18aae1fd74d3a26242ff6d"
)
_ROUTE_MAP_SHA256 = (
    "2e01bf18eb740daa8d9a07cb8bf3c78e467ee76baadcbdf12e697ad4be415b4a"
)
_TERMINAL_STATUSES = frozenset(
    {"applied", "tested-rejected", "not-applicable", "unknown-pending"}
)
_RETAINED_STATUSES = frozenset({"applied", "tested-rejected"})
_ROMAN_ORDINAL_TOKEN_RE = re.compile(
    r"(?<![^\W_])"
    r"(?:[\(\[\{]\s*)?"
    r"(?=[mdclxvi])"
    r"m{0,3}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})"
    r"\s*(?:[\)\]\}])?"
    r"(?![^\W_])"
)


class ConceptClosureError(ValueError):
    """Raised when dispositions claim closure without traversing authority."""


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ConceptClosureError(f"{label} must be a mapping")
    try:
        return copy.deepcopy(dict(value))
    except Exception as error:
        raise ConceptClosureError(f"{label} cannot be snapshotted: {error}") from error


def _load_object(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        value = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConceptClosureError(f"cannot load {label}: {error}") from error
    if not isinstance(value, dict):
        raise ConceptClosureError(f"{label} must be a JSON object")
    return raw, value


def _authority_paths(repo: Path | str) -> tuple[Path, Path]:
    if not isinstance(repo, (str, Path)):
        raise ConceptClosureError("repo must be a path")
    root = Path(repo).resolve()
    references = root / "skills" / "crossframe-ultra" / "references"
    return (
        references / "concept-registry" / "v8.2-concept-registry.json",
        references / "v8.2-route-map.json",
    )


def _validate_authority_metadata(
    registry: Mapping[str, Any],
    route_map: Mapping[str, Any],
) -> None:
    if (
        registry.get("schema_id")
        != "crossframe.ultra.v8.2.concept-registry"
        or registry.get("framework_version") != "v8.2"
        or registry.get("framework_revision") != "v8.2"
        or registry.get("raw_sha256") != _RAW_SHA256
        or registry.get("semantic_sha256") != _SEMANTIC_SHA256
        or registry.get("concept_count") != 9
    ):
        raise ConceptClosureError("promoted v8.2 concept registry metadata mismatch")
    if (
        route_map.get("schema_id") != "crossframe.ultra.v8.2.route-map"
        or route_map.get("framework_version") != "v8.2"
        or route_map.get("framework_revision") != "v8.2"
        or route_map.get("raw_sha256") != _RAW_SHA256
        or route_map.get("semantic_sha256") != _SEMANTIC_SHA256
        or route_map.get("route_count") != 9
    ):
        raise ConceptClosureError("promoted v8.2 route map metadata mismatch")
    try:
        validate_instance("ultra-concept-registry.schema.json", dict(registry))
        validate_instance("ultra-route-map.schema.json", dict(route_map))
    except ValidationError as error:
        raise ConceptClosureError(
            f"promoted v8.2 authority violates its schema: {error.message}"
        ) from error


def _records_by_id(
    records: object,
    *,
    field: str,
    label: str,
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise ConceptClosureError(f"{label} records must be an array")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise ConceptClosureError(f"{label} record must be an object")
        identifier = record.get(field)
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise ConceptClosureError(f"duplicate or invalid {label} ID: {identifier!r}")
        result[identifier] = record
    return result


def _checked_ids(value: Collection[str], *, label: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ConceptClosureError(f"{label} must be a collection of identifiers")
    try:
        identifiers = tuple(value)
    except Exception as error:
        raise ConceptClosureError(f"{label} cannot be read: {error}") from error
    if any(not isinstance(item, str) or not item for item in identifiers):
        raise ConceptClosureError(f"{label} must contain non-empty string IDs")
    if len(identifiers) != len(set(identifiers)):
        raise ConceptClosureError(f"{label} must not contain duplicates")
    return identifiers


def _route_neighbor_closure(
    concepts: Mapping[str, Mapping[str, Any]],
    routes: Mapping[str, Mapping[str, Any]],
    required_route_ids: tuple[str, ...],
) -> frozenset[str]:
    missing_routes = set(required_route_ids) - set(routes)
    if missing_routes:
        raise ConceptClosureError(
            f"unknown required route IDs: {sorted(missing_routes)!r}"
        )
    queue: deque[str] = deque()
    for route_id in required_route_ids:
        route_concepts = routes[route_id].get("concept_ids")
        if not isinstance(route_concepts, list):
            raise ConceptClosureError(f"route {route_id!r} has no concept closure")
        queue.extend(route_concepts)

    closure: set[str] = set()
    while queue:
        concept_id = queue.popleft()
        if concept_id in closure:
            continue
        concept = concepts.get(concept_id)
        if concept is None:
            raise ConceptClosureError(
                f"route or neighbor references unknown concept {concept_id!r}"
            )
        closure.add(concept_id)
        neighbors = concept.get("required_neighbors")
        if not isinstance(neighbors, list):
            raise ConceptClosureError(
                f"concept {concept_id!r} has invalid required neighbors"
            )
        queue.extend(neighbors)
    return frozenset(closure)


def _normalized_rationale(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"\bv82[\s._:-]*m0*\d+\b", "<concept-id>", normalized)
    normalized = _ROMAN_ORDINAL_TOKEN_RE.sub("", normalized)
    normalized = re.sub(r"\b\d+\b", "<number>", normalized)
    normalized = re.sub(r"[\W_]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def validate_concept_closure(
    document: Mapping[str, object],
    *,
    repo: Path | str,
    required_route_ids: Collection[str],
) -> frozenset[str]:
    snapshot = _snapshot_mapping(document, label="concept disposition")
    try:
        validate_instance("ultra-concept-disposition.schema.json", snapshot)
    except (ValidationError, TypeError, ValueError) as error:
        message = getattr(error, "message", str(error))
        raise ConceptClosureError(
            f"concept disposition schema validation failed: {message}"
        ) from error

    registry_path, route_path = _authority_paths(repo)
    registry_raw, registry = _load_object(registry_path, label="v8.2 registry")
    route_raw, route_map = _load_object(route_path, label="v8.2 route map")
    registry_sha256 = hashlib.sha256(registry_raw).hexdigest()
    route_sha256 = hashlib.sha256(route_raw).hexdigest()
    if registry_sha256 != _REGISTRY_SHA256:
        raise ConceptClosureError("promoted v8.2 registry hash mismatch")
    if route_sha256 != _ROUTE_MAP_SHA256:
        raise ConceptClosureError("promoted v8.2 route-map hash mismatch")
    _validate_authority_metadata(registry, route_map)

    if snapshot["registry_sha256"] != registry_sha256:
        raise ConceptClosureError("concept disposition binds another registry")

    concepts = _records_by_id(
        registry.get("concepts"),
        field="concept_id",
        label="concept",
    )
    routes = _records_by_id(
        route_map.get("routes"),
        field="route_id",
        label="route",
    )
    if set(concepts) != {f"V82-M{number:02d}" for number in range(1, 10)}:
        raise ConceptClosureError("promoted registry must contain V82-M01 through M09")

    checked_routes = _checked_ids(required_route_ids, label="required_route_ids")
    if not checked_routes:
        raise ConceptClosureError("at least one required route must be declared")
    required_concepts = _route_neighbor_closure(concepts, routes, checked_routes)

    dispositions = _records_by_id(
        snapshot["dispositions"],
        field="concept_id",
        label="disposition",
    )
    if set(dispositions) != set(concepts):
        missing = sorted(set(concepts) - set(dispositions))
        extra = sorted(set(dispositions) - set(concepts))
        raise ConceptClosureError(
            f"concept disposition inventory mismatch; missing={missing!r}, extra={extra!r}"
        )
    if snapshot["closure_complete"] is not True:
        raise ConceptClosureError("concept closure_complete must be true")
    if snapshot["unvisited_concept_ids"] != []:
        raise ConceptClosureError("concept closure cannot retain unvisited concepts")

    retained_units: set[str] = set()
    rationales: set[str] = set()
    for concept_id, disposition in dispositions.items():
        concept = concepts[concept_id]
        status = disposition["status"]
        if status not in _TERMINAL_STATUSES:
            raise ConceptClosureError(
                f"concept {concept_id} lacks a terminal disposition"
            )
        if disposition["route_required"] is not (concept_id in required_concepts):
            raise ConceptClosureError(
                f"route-required closure mismatch for {concept_id}"
            )
        expected_neighbors = concept["required_neighbors"]
        if disposition["neighbor_concept_ids"] != expected_neighbors:
            raise ConceptClosureError(
                f"required-neighbor closure mismatch for {concept_id}"
            )

        rationale = _normalized_rationale(disposition["rationale"])
        if rationale in rationales:
            raise ConceptClosureError("copied boilerplate rationale is not independent")
        rationales.add(rationale)

        semantic_units = tuple(disposition["semantic_unit_ids"])
        if status in _RETAINED_STATUSES:
            if not semantic_units:
                raise ConceptClosureError(
                    f"retained concept {concept_id} lacks an article semantic unit"
                )
            retained_units.update(semantic_units)
        elif status == "not-applicable" and semantic_units:
            raise ConceptClosureError(
                f"not-applicable concept {concept_id} cannot claim article units"
            )
        elif status == "unknown-pending" and not (
            disposition["condition_branch"] or disposition["evidence_plan"]
        ):
            raise ConceptClosureError(
                f"unknown-pending concept {concept_id} lacks a condition or evidence plan"
            )
    return frozenset(retained_units)


__all__ = ("ConceptClosureError", "validate_concept_closure")
