from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from datetime import date as calendar_date
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from . import constants as runtime_constants
from .errors import UltraCompatibilityError, UltraSchemaError
from .jsonio import (
    DEFAULT_MAX_JSON_BYTES,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)


SCHEMA_NAMES = (
    "ultra-action-ranking.schema.json",
    "ultra-artifact-manifest.schema.json",
    "ultra-article-review.schema.json",
    "ultra-claim-mechanism-graph.schema.json",
    "ultra-common.schema.json",
    "ultra-compatibility-matrix.schema.json",
    "ultra-concept-disposition.schema.json",
    "ultra-concept-registry.schema.json",
    "ultra-contract-map.schema.json",
    "ultra-evidence-ledger.schema.json",
    "ultra-forecast-ledger.schema.json",
    "ultra-framework-gap-ledger.schema.json",
    "ultra-order-evaluation.schema.json",
    "ultra-output-plan.schema.json",
    "ultra-phase-event.schema.json",
    "ultra-read-event.schema.json",
    "ultra-recovery-checkpoint.schema.json",
    "ultra-recursive-lineage.schema.json",
    "ultra-red-team-report.schema.json",
    "ultra-release-manifest.schema.json",
    "ultra-repair-plan.schema.json",
    "ultra-retrieval-ledger.schema.json",
    "ultra-route-map.schema.json",
    "ultra-run-contract.schema.json",
    "ultra-run-status.schema.json",
    "ultra-semantic-coverage.schema.json",
    "ultra-source-lock.schema.json",
    "ultra-source-manifest.schema.json",
    "ultra-transformation-ledger.schema.json",
    "ultra-validator-report.schema.json",
    "ultra-verdict.schema.json",
    "ultra-world-volume.schema.json",
)
_SCHEMA_NAME_SET = frozenset(SCHEMA_NAMES)
_FORMAT_CHECKER = FormatChecker()
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_REVISION_RE = re.compile(r"v(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)-r(?P<revision>0|[1-9][0-9]*)")
_RFC3339_RE = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"[Tt](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.[0-9]+)?"
    r"(?P<zone>[Zz]|(?P<sign>[+-])(?P<offset_hour>[0-9]{2}):(?P<offset_minute>[0-9]{2}))"
)
_COMPATIBILITY_RESULTS = frozenset(
    {"resume", "read-only", "fork-required", "reject"}
)
_RULE_RESULTS = {
    "known-migration": "fork-required",
    "mismatch-subset": "read-only",
    "exact": "resume",
    "fallback": "reject",
}
_MIGRATION_MISMATCH_FIELDS = frozenset(
    {"framework_revision", "artifact_schema_version"}
)
_READ_ONLY_MISMATCH_FIELDS = frozenset(
    {"runtime_version", "validator_version"}
)


@_FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_date_time(value: object) -> bool:
    if not isinstance(value, str):
        return True
    match = _RFC3339_RE.fullmatch(value)
    if match is None:
        return False
    try:
        calendar_date.fromisoformat(match.group("date"))
    except ValueError:
        return False
    if int(match.group("hour")) > 23 or int(match.group("minute")) > 59:
        return False
    if int(match.group("second")) > 60:
        return False
    if match.group("zone").casefold() != "z":
        if int(match.group("offset_hour")) > 23:
            return False
        if int(match.group("offset_minute")) > 59:
            return False
    return True


def schema_root() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas"


def _compatibility_matrix_path() -> Path:
    return Path(__file__).resolve().parents[2] / "references" / "compatibility-matrix.json"


def _checked_schema_name(schema_name: str) -> str:
    if not isinstance(schema_name, str) or not schema_name:
        raise UltraSchemaError("schema name must be a non-empty string")
    if (
        "/" in schema_name
        or "\\" in schema_name
        or Path(schema_name).name != schema_name
    ):
        raise UltraSchemaError(f"schema name must be a safe basename: {schema_name!r}")
    if schema_name not in _SCHEMA_NAME_SET:
        raise UltraSchemaError(f"unknown Ultra schema: {schema_name!r}")
    return schema_name


def _validate_common_current_binding(document: Mapping[str, Any]) -> None:
    try:
        properties = document["$defs"]["currentVersionBinding"]["allOf"][1][
            "properties"
        ]
        schema_binding = {
            field: definition["const"]
            for field, definition in properties.items()
        }
    except (KeyError, TypeError) as error:
        raise UltraSchemaError(
            "Ultra common schema does not expose a closed current version binding"
        ) from error
    expected = runtime_constants.current_version_binding()
    if tuple(schema_binding) != runtime_constants.VERSION_BINDING_FIELDS:
        raise UltraSchemaError(
            "Ultra common schema version binding fields drift from constants"
        )
    if schema_binding != expected:
        raise UltraSchemaError(
            "Ultra common schema current version binding drifts from constants"
        )


def _validate_schema_document(
    schema_name: str,
    document: dict[str, Any],
) -> dict[str, Any]:
    try:
        Draft202012Validator.check_schema(document)
    except (MemoryError, RecursionError) as error:
        raise UltraSchemaError(
            f"Ultra schema resource limit exceeded for {schema_name!r}"
        ) from error
    except Exception as error:
        raise UltraSchemaError(f"invalid Ultra schema {schema_name!r}: {error}") from error
    if schema_name == "ultra-common.schema.json":
        _validate_common_current_binding(document)
    return document


def _load_schema_cached(schema_name: str) -> dict[str, Any]:
    checked_name = _checked_schema_name(schema_name)
    path = schema_root() / checked_name
    try:
        document = load_json_object(path)
    except (OSError, TypeError, ValueError) as error:
        raise UltraSchemaError(f"cannot load Ultra schema {checked_name!r}: {error}") from error
    return _validate_schema_document(checked_name, document)


def load_schema(schema_name: str) -> dict[str, Any]:
    try:
        return copy.deepcopy(_load_schema_cached(schema_name))
    except (MemoryError, RecursionError) as error:
        raise UltraSchemaError(
            f"Ultra schema resource limit exceeded for {schema_name!r}"
        ) from error


def _current_binding_token() -> tuple[tuple[str, object], ...]:
    binding = runtime_constants.current_version_binding()
    return tuple(
        (field, binding[field]) for field in runtime_constants.VERSION_BINDING_FIELDS
    )


def _read_schema_snapshot() -> tuple[tuple[str, bytes], ...]:
    root = schema_root()
    snapshot: list[tuple[str, bytes]] = []
    for schema_name in SCHEMA_NAMES:
        path = root / schema_name
        try:
            if path.stat().st_size > DEFAULT_MAX_JSON_BYTES:
                raise UltraSchemaError(
                    f"Ultra schema exceeds the JSON byte limit: {schema_name!r}"
                )
            raw = path.read_bytes()
        except MemoryError as error:
            raise UltraSchemaError(
                f"Ultra schema resource limit exceeded for {schema_name!r}"
            ) from error
        except OSError as error:
            raise UltraSchemaError(
                f"cannot read Ultra schema {schema_name!r}: {error}"
            ) from error
        if len(raw) > DEFAULT_MAX_JSON_BYTES:
            raise UltraSchemaError(
                f"Ultra schema exceeds the JSON byte limit: {schema_name!r}"
            )
        snapshot.append((schema_name, raw))
    return tuple(snapshot)


@lru_cache(maxsize=4)
def _schema_documents_cached(
    binding_token: tuple[tuple[str, object], ...],
    snapshot: tuple[tuple[str, bytes], ...],
) -> tuple[tuple[str, dict[str, Any]], ...]:
    if binding_token != _current_binding_token():
        raise UltraSchemaError("schema cache key is not the current constants authority")
    documents: list[tuple[str, dict[str, Any]]] = []
    for schema_name, raw in snapshot:
        try:
            document = load_json_object_bytes(raw, source=schema_name)
        except (TypeError, ValueError) as error:
            raise UltraSchemaError(
                f"cannot load Ultra schema {schema_name!r}: {error}"
            ) from error
        documents.append(
            (schema_name, _validate_schema_document(schema_name, document))
        )
    return tuple(documents)


def _current_schema_documents() -> tuple[tuple[str, dict[str, Any]], ...]:
    return _schema_documents_cached(
        _current_binding_token(),
        _read_schema_snapshot(),
    )


def _make_schema_registry(
    *,
    isolate_contents: bool,
    documents: tuple[tuple[str, dict[str, Any]], ...],
) -> Registry[Any]:
    resources: list[tuple[str, Resource[Any]]] = []
    seen_ids: set[str] = set()
    for schema_name, stored_schema in documents:
        schema = stored_schema
        if isolate_contents:
            schema = copy.deepcopy(schema)
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise UltraSchemaError(f"Ultra schema has no usable $id: {schema_name!r}")
        if schema_id in seen_ids:
            raise UltraSchemaError(f"duplicate Ultra schema $id: {schema_id!r}")
        if not schema_id.startswith("https://crossframe.local/schemas/ultra-"):
            raise UltraSchemaError(f"non-Ultra schema $id: {schema_id!r}")
        seen_ids.add(schema_id)
        resources.append((schema_id, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


@lru_cache(maxsize=4)
def _internal_schema_registry_cached(
    binding_token: tuple[tuple[str, object], ...],
    snapshot: tuple[tuple[str, bytes], ...],
) -> Registry[Any]:
    documents = _schema_documents_cached(binding_token, snapshot)
    return _make_schema_registry(isolate_contents=False, documents=documents)


def _internal_schema_registry() -> Registry[Any]:
    binding_token = _current_binding_token()
    snapshot = _read_schema_snapshot()
    return _internal_schema_registry_cached(binding_token, snapshot)


def build_schema_registry() -> Registry[Any]:
    return _make_schema_registry(
        isolate_contents=True,
        documents=_current_schema_documents(),
    )


@lru_cache(maxsize=128)
def _validator_for_cached(
    schema_name: str,
    binding_token: tuple[tuple[str, object], ...],
    snapshot: tuple[tuple[str, bytes], ...],
) -> Draft202012Validator:
    documents = dict(_schema_documents_cached(binding_token, snapshot))
    return Draft202012Validator(
        documents[schema_name],
        registry=_internal_schema_registry_cached(binding_token, snapshot),
        format_checker=_FORMAT_CHECKER,
    )


def _validator_for(schema_name: str) -> Draft202012Validator:
    checked_name = _checked_schema_name(schema_name)
    binding_token = _current_binding_token()
    snapshot = _read_schema_snapshot()
    return _validator_for_cached(checked_name, binding_token, snapshot)


def validate_instance(schema_name: str, instance: Mapping[str, Any]) -> None:
    try:
        _validator_for(schema_name).validate(instance)
    except ValidationError as error:
        if "version_binding" in error.absolute_path:
            raise ValidationError(
                f"version authority binding mismatch: {error.message}"
            ) from error
        raise


def compute_artifact_content_sha256(artifact: Mapping[str, Any]) -> str:
    if not isinstance(artifact, Mapping):
        raise UltraSchemaError("artifact must be an object")
    try:
        payload = copy.deepcopy(dict(artifact))
        payload.pop("content_sha256", None)
        return sha256_bytes(canonical_json_bytes(payload))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise UltraSchemaError(
            f"artifact payload is not bounded canonical JSON: {error}"
        ) from error


def _validate_compatibility_matrix_policy(document: Mapping[str, Any]) -> None:
    rules = document["rules"]
    rule_ids = [rule["rule_id"] for rule in rules]
    if len(rule_ids) != len(set(rule_ids)):
        raise UltraCompatibilityError(
            "Ultra compatibility matrix rule_id values must be unique"
        )

    priorities = [rule["priority"] for rule in rules]
    if len(priorities) != len(set(priorities)):
        raise UltraCompatibilityError(
            "Ultra compatibility matrix priorities must be unique"
        )
    if priorities != sorted(priorities):
        raise UltraCompatibilityError(
            "Ultra compatibility matrix priorities must be strictly increasing"
        )

    fallback_rules = [
        rule for rule in rules if rule["match_kind"] == "fallback"
    ]
    if len(fallback_rules) != 1:
        raise UltraCompatibilityError(
            "Ultra compatibility matrix must contain exactly one fallback rule"
        )
    if rules[-1] is not fallback_rules[0]:
        raise UltraCompatibilityError(
            "Ultra compatibility matrix fallback rule must be last"
        )

    for rule in rules:
        match_kind = rule["match_kind"]
        expected_result = _RULE_RESULTS.get(match_kind)
        if expected_result is None or rule["result"] != expected_result:
            raise UltraCompatibilityError(
                "Ultra compatibility matrix contains an unsafe rule/result policy"
            )

        mismatch_fields = frozenset(rule["allowed_mismatch_fields"])
        if match_kind == "known-migration":
            if len(mismatch_fields) != 1 or not mismatch_fields.issubset(
                _MIGRATION_MISMATCH_FIELDS
            ):
                raise UltraCompatibilityError(
                    "Ultra compatibility migration rules must bind one migration field"
                )
        elif match_kind == "mismatch-subset":
            if not mismatch_fields or not mismatch_fields.issubset(
                _READ_ONLY_MISMATCH_FIELDS
            ):
                raise UltraCompatibilityError(
                    "Ultra read-only rules may only vary runtime or validator versions"
                )
        elif mismatch_fields:
            raise UltraCompatibilityError(
                "Ultra exact and fallback rules cannot allow mismatch fields"
            )


def _load_compatibility_matrix_cached() -> dict[str, Any]:
    path = _compatibility_matrix_path()
    try:
        document = load_json_object(path)
    except (OSError, TypeError, ValueError) as error:
        raise UltraCompatibilityError(
            f"cannot load Ultra compatibility matrix: {error}"
        ) from error
    try:
        validate_instance("ultra-compatibility-matrix.schema.json", document)
    except (ValidationError, UltraSchemaError) as error:
        raise UltraCompatibilityError(
            "Ultra compatibility matrix is invalid: "
            f"{getattr(error, 'message', str(error))}"
        ) from error
    if document["content_sha256"] != compute_artifact_content_sha256(document):
        raise UltraCompatibilityError(
            "Ultra compatibility matrix content_sha256 does not match its payload"
        )
    if document["version_binding"] != runtime_constants.current_version_binding():
        raise UltraCompatibilityError(
            "Ultra compatibility matrix version binding drifts from constants"
        )
    if tuple(document["binding_fields"]) != runtime_constants.VERSION_BINDING_FIELDS:
        raise UltraCompatibilityError(
            "Ultra compatibility matrix binding fields drift from constants"
        )
    _validate_compatibility_matrix_policy(document)
    return document


def load_compatibility_matrix() -> dict[str, Any]:
    try:
        return copy.deepcopy(_load_compatibility_matrix_cached())
    except (MemoryError, RecursionError) as error:
        raise UltraCompatibilityError(
            "Ultra compatibility matrix resource limit exceeded"
        ) from error


def _binding_validator() -> Draft202012Validator:
    binding_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "https://crossframe.local/schemas/ultra-common.schema.json#/$defs/versionBinding",
    }
    return Draft202012Validator(
        binding_schema,
        registry=_internal_schema_registry(),
        format_checker=_FORMAT_CHECKER,
    )


def _current_binding_validator() -> Draft202012Validator:
    binding_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "https://crossframe.local/schemas/ultra-common.schema.json#/$defs/currentVersionBinding",
    }
    return Draft202012Validator(
        binding_schema,
        registry=_internal_schema_registry(),
        format_checker=_FORMAT_CHECKER,
    )


def _snapshot_mapping(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    try:
        return copy.deepcopy(dict(value))
    except (Exception, MemoryError, RecursionError):
        try:
            return dict(value)
        except Exception:
            return None


def validate_phase_artifact(
    schema_name: str,
    artifact: Mapping[str, Any],
    *,
    expected_schema_id: str,
    expected_run_id: str,
    expected_version_binding: Mapping[str, Any],
    expected_phase_id: str,
) -> dict[str, Any]:
    snapshot = _snapshot_mapping(artifact)
    expected_binding = _snapshot_mapping(expected_version_binding)
    if snapshot is None:
        raise UltraSchemaError("phase artifact must be an object")
    if expected_binding is None:
        raise UltraSchemaError("expected version binding must be an object")
    if not isinstance(expected_schema_id, str) or not expected_schema_id:
        raise UltraSchemaError("expected schema authority must be explicit")
    if not isinstance(expected_run_id, str) or not expected_run_id:
        raise UltraSchemaError("expected run_id must be explicit")
    if expected_phase_id not in runtime_constants.PHASES:
        raise UltraSchemaError("expected phase_id must be a current Ultra phase")
    current_binding = runtime_constants.current_version_binding()
    if expected_binding != current_binding:
        raise UltraSchemaError(
            "expected version binding differs from the current constants authority"
        )
    validate_instance(schema_name, snapshot)
    if snapshot.get("schema_id") != expected_schema_id:
        raise UltraSchemaError("phase artifact schema authority does not match expected")
    if snapshot.get("run_id") != expected_run_id:
        raise UltraSchemaError("phase artifact run_id does not match expected")
    if snapshot.get("version_binding") != expected_binding:
        raise UltraSchemaError("phase artifact full version binding does not match expected")
    if snapshot.get("phase_id") != expected_phase_id:
        raise UltraSchemaError("phase artifact phase_id does not match expected")
    if snapshot.get("content_sha256") != compute_artifact_content_sha256(snapshot):
        raise UltraSchemaError("phase artifact content_sha256 does not match its payload")
    return snapshot


def _is_valid_binding(value: object) -> bool:
    snapshot = _snapshot_mapping(value)
    if snapshot is None:
        return False
    try:
        _binding_validator().validate(snapshot)
    except ValidationError:
        return False
    return True


def _is_valid_current_binding(value: object) -> bool:
    snapshot = _snapshot_mapping(value)
    if snapshot is None:
        return False
    try:
        _current_binding_validator().validate(snapshot)
    except ValidationError:
        return False
    return True


def _known_migration(
    recorded_binding: Mapping[str, Any],
    current_binding: Mapping[str, Any],
    matrix: Mapping[str, Any],
) -> bool:
    migrations = matrix["known_migrations"]
    return any(
        dict(record["from_binding"]) == dict(recorded_binding)
        and dict(record["to_binding"]) == dict(current_binding)
        for migration_kind in ("framework_revisions", "artifact_schemas")
        for record in migrations[migration_kind]
    )


def _matches_rule(
    rule: Mapping[str, Any],
    mismatches: frozenset[str],
    known_migration: bool,
) -> bool:
    match_kind = rule["match_kind"]
    allowed = frozenset(rule["allowed_mismatch_fields"])
    if match_kind == "known-migration":
        return known_migration and bool(mismatches) and mismatches.issubset(allowed)
    if match_kind == "mismatch-subset":
        return bool(mismatches) and mismatches.issubset(allowed)
    if match_kind == "exact":
        return not mismatches
    if match_kind == "fallback":
        return True
    return False


def resolve_compatibility(
    recorded_binding: Mapping[str, Any],
    current_binding: Mapping[str, Any] | None = None,
) -> str:
    recorded_snapshot = _snapshot_mapping(recorded_binding)
    if current_binding is None:
        if recorded_snapshot is None or set(recorded_snapshot) != {
            "recorded",
            "current",
        }:
            return "reject"
        candidate_recorded = _snapshot_mapping(recorded_snapshot["recorded"])
        candidate_current = _snapshot_mapping(recorded_snapshot["current"])
        if candidate_recorded is None or candidate_current is None:
            return "reject"
        recorded_binding = candidate_recorded
        current_binding = candidate_current
    else:
        current_snapshot = _snapshot_mapping(current_binding)
        if recorded_snapshot is None or current_snapshot is None:
            return "reject"
        recorded_binding = recorded_snapshot
        current_binding = current_snapshot

    if not _is_valid_binding(recorded_binding) or not _is_valid_current_binding(
        current_binding
    ):
        return "reject"

    matrix = _load_compatibility_matrix_cached()
    binding_fields = tuple(matrix["binding_fields"])
    if set(recorded_binding) != set(binding_fields) or set(current_binding) != set(
        binding_fields
    ):
        return "reject"
    if dict(current_binding) != dict(matrix["version_binding"]):
        return "reject"
    mismatches = frozenset(
        field
        for field in binding_fields
        if recorded_binding[field] != current_binding[field]
    )
    migration_is_known = _known_migration(recorded_binding, current_binding, matrix)

    for rule in sorted(matrix["rules"], key=lambda item: item["priority"]):
        if _matches_rule(rule, mismatches, migration_is_known):
            result = rule["result"]
            return result if result in _COMPATIBILITY_RESULTS else "reject"
    return "reject"


def resolve_source_revision_promotion(
    *,
    current_revision: str,
    current_raw_sha256: str,
    current_semantic_sha256: str,
    candidate_raw_sha256: str,
    candidate_semantic_sha256: str,
) -> dict[str, Any]:
    revision_match = (
        _REVISION_RE.fullmatch(current_revision)
        if isinstance(current_revision, str)
        else None
    )
    hashes = (
        current_raw_sha256,
        current_semantic_sha256,
        candidate_raw_sha256,
        candidate_semantic_sha256,
    )
    if revision_match is None or any(
        not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None
        for value in hashes
    ):
        raise UltraCompatibilityError("source revision promotion inputs are malformed")

    policies = _load_compatibility_matrix_cached()["source_revision_promotion"]
    if candidate_semantic_sha256 == current_semantic_sha256:
        policy = policies["same_semantic"]
        action = (
            policy["action"]
            if candidate_raw_sha256 != current_raw_sha256
            else "no-change"
        )
        return {
            "action": action,
            "current_revision": current_revision,
            "target_revision": current_revision,
            "alternate_raw_sha256": (
                candidate_raw_sha256
                if candidate_raw_sha256 != current_raw_sha256
                else None
            ),
            "build_beside_current": policy["build_beside_current"],
            "requires_validation": policy["requires_validation"],
            "promote_stable_after_validation": policy[
                "promote_stable_after_validation"
            ],
            "overwrite_existing_release": policy["overwrite_existing_release"],
        }

    policy = policies["changed_semantic"]
    next_revision = int(revision_match.group("revision")) + 1
    target_revision = (
        f"v{revision_match.group('major')}.{revision_match.group('minor')}-r{next_revision}"
    )
    return {
        "action": policy["action"],
        "current_revision": current_revision,
        "target_revision": target_revision,
        "alternate_raw_sha256": None,
        "build_beside_current": policy["build_beside_current"],
        "requires_validation": policy["requires_validation"],
        "promote_stable_after_validation": policy[
            "promote_stable_after_validation"
        ],
        "overwrite_existing_release": policy["overwrite_existing_release"],
    }
