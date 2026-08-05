from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
from datetime import date as calendar_date
from decimal import Decimal
import re
from typing import Any

from jsonschema import ValidationError

from .errors import UltraSchemaError
from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import validate_phase_artifact
from .world_volume import WorldVolumeError, validate_world_volume


_AXES = tuple("AXTOCRINJ")
_AXIS_SET = frozenset(_AXES)
_TRANSFORM_KINDS = frozenset(
    {"scale", "circle-relation", "representation-translation"}
)
_PAYLOAD_KINDS = frozenset(
    {
        "mapping",
        "set",
        "interval",
        "graph",
        "authorization-difference",
        "deep-equality",
    }
)
_NORMALIZED_STATE_FIELDS = frozenset(
    {
        "transform_id",
        "side",
        "location_ref",
        "axis_id",
        "status",
        "applicability_criterion_id",
        "applicability_result",
        "evidence_refs",
        "normalized_state_ref",
        "normalized_state_sha256",
        "normalized_state",
    }
)
_COMPARATOR_RESULT_FIELDS = frozenset(
    {
        "comparator_result_ref",
        "axis_id",
        "comparator_id",
        "comparator_version",
        "source_status",
        "target_status",
        "source_state_sha256",
        "target_state_sha256",
        "relation",
        "evidence_refs",
        "comparison_payload_ref",
        "verification_artifact_ref",
        "verification_hash",
        "validation_status",
    }
)
_VERIFICATION_FIELDS = frozenset(
    {
        "verification_artifact_ref",
        "verifier_id",
        "comparator_result_ref",
        "comparison_payload_ref",
        "axis_id",
        "source_state_sha256",
        "target_state_sha256",
        "relation",
        "artifact_payload",
        "verification_hash",
    }
)
_PAYLOAD_FIELDS = frozenset(
    {
        "payload_ref",
        "payload_kind",
        "axis_id",
        "source_state_sha256",
        "target_state_sha256",
        "payload",
        "payload_sha256",
    }
)
_TUPLE_FIELDS = frozenset(
    {
        "source_ref",
        "decision_subject_ref",
        "object_ref",
        "action_ref",
        "jurisdiction",
        "validity_period",
        "revocation_conditions",
        "evidence_refs",
        "independent_review_ref",
    }
)
_RFC3339_RE = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"[Tt](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<zone>[Zz]|(?P<sign>[+-])(?P<offset_hour>[0-9]{2}):(?P<offset_minute>[0-9]{2}))"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class TransformationError(ValueError):
    """Raised when a transformation hides identity, authority, or local effects."""


class ChannelContinuityError(TransformationError):
    """Raised when a cascade hop lacks a revalidated real channel."""


@dataclass(frozen=True, slots=True)
class TransformationAuthorities:
    world_volume_artifact_sha256: str
    normalized_states: Sequence[Mapping[str, object]]
    comparator_results: Mapping[str, Mapping[str, object]]
    verification_artifacts: Mapping[str, Mapping[str, object]]
    comparison_payloads: Mapping[str, Mapping[str, object]]
    j_authorization_tuples: Sequence[Mapping[str, object]]
    independent_reviews: Mapping[str, Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class _Context:
    world: Mapping[str, Any]
    evidence: Mapping[str, Any]
    relations: Mapping[str, Mapping[str, Any]]
    evidence_ids: frozenset[str]
    source_refs: frozenset[str]
    represented: Mapping[str, Mapping[str, Any]]
    locations: frozenset[str]
    general_refs: frozenset[str]
    unknown_ids: frozenset[str]
    residuals: Mapping[str, Mapping[str, Any]]
    state_owners: Mapping[str, tuple[str, str, Mapping[str, Any]]]
    clocks: Mapping[str, Mapping[str, Any]]
    channels: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class _AuthorityBundle:
    mapping: Mapping[str, Any]
    normalized: tuple[Mapping[str, Any], ...]
    results: Mapping[str, Mapping[str, Any]]
    verifications: Mapping[str, Mapping[str, Any]]
    payloads: Mapping[str, Mapping[str, Any]]
    tuples: Mapping[str, Mapping[str, Any]]
    reviews: Mapping[str, Mapping[str, Any]]


def _require_native_json(value: object, *, label: str) -> None:
    value_type = type(value)
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TransformationError(
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
    raise TransformationError(f"{label} contains a non-native JSON value")


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TransformationError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise TransformationError(f"{label} cannot be snapshotted: {error}") from error
    _require_native_json(snapshot, label=label)
    return snapshot


def _canonical_sha256(value: object) -> str:
    try:
        return sha256_bytes(canonical_json_bytes(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise TransformationError(f"authority is not canonical JSON: {error}") from error


def _require_sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise TransformationError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _require_optional_sha256(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _require_sha256(value, label=label)


def _validated_public_authorities(
    *,
    expected_run_id: object,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: object,
    expected_world_volume_artifact_sha256: object,
    expected_relation_refs_sha256: object,
    expected_authorities_sha256: object,
) -> tuple[str, dict[str, Any], str, str, str, str]:
    if type(expected_run_id) is not str or not expected_run_id:
        raise TransformationError("expected_run_id must be a nonempty native string")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected version binding"
    )
    evidence_hash = _require_sha256(
        expected_evidence_artifact_sha256,
        label="expected evidence artifact hash",
    )
    world_hash = _require_sha256(
        expected_world_volume_artifact_sha256,
        label="expected world-volume artifact hash",
    )
    relation_hash = _require_sha256(
        expected_relation_refs_sha256,
        label="expected relation authority hash",
    )
    authority_hash = _require_sha256(
        expected_authorities_sha256,
        label="expected transformation authority hash",
    )
    return (
        expected_run_id,
        binding,
        evidence_hash,
        world_hash,
        relation_hash,
        authority_hash,
    )


def _unique(values: Sequence[str], *, label: str) -> None:
    if len(values) != len(set(values)):
        raise TransformationError(f"duplicate {label} identifier")


def _mapping_registry(
    value: Mapping[str, Mapping[str, object]], *, label: str
) -> dict[str, Mapping[str, Any]]:
    snapshot = _snapshot_mapping(value, label=label)
    for key, record in snapshot.items():
        if not isinstance(key, str) or not key or not isinstance(record, Mapping):
            raise TransformationError(f"{label} has an invalid key or record")
    return snapshot


def _build_context(
    source_volume: Mapping[str, object],
    evidence_ledger: Mapping[str, object],
    relation_refs: Mapping[str, Mapping[str, object]],
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
    expected_world_volume_artifact_sha256: str,
    expected_relation_refs_sha256: str,
) -> _Context:
    world = _snapshot_mapping(source_volume, label="source world volume")
    evidence = _snapshot_mapping(evidence_ledger, label="U3 evidence ledger")
    relations = _mapping_registry(relation_refs, label="relation authority")
    try:
        validate_world_volume(
            world,
            evidence_ledger=evidence,
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
            relation_refs=relations,
            expected_relation_refs_sha256=expected_relation_refs_sha256,
        )
    except WorldVolumeError as error:
        raise TransformationError(f"invalid U4 source volume: {error}") from error
    if _canonical_sha256(world) != expected_world_volume_artifact_sha256:
        raise TransformationError("U4 full artifact hash differs from external authority")

    evidence_ids = frozenset(record["evidence_id"] for record in evidence["entries"])
    source_refs = frozenset(
        source_ref
        for record in evidence["entries"]
        for source_ref in record["source_refs"]
    )
    represented: dict[str, Mapping[str, Any]] = {}
    for section, field in (
        ("actors", "actor_id"),
        ("circles", "circle_id"),
        ("positions", "position_id"),
    ):
        represented.update({record[field]: record for record in world[section]})
    state_owners: dict[str, tuple[str, str, Mapping[str, Any]]] = {}
    for location_ref, location in represented.items():
        for state_kind, field in (("M", "M_state"), ("Psi", "Psi_state")):
            state = location[field]
            state_owners[state["state_id"]] = (location_ref, state_kind, state)
    clocks = {record["clock_id"]: record for record in world["clocks"]}
    channels = {record["channel_id"]: record for record in world["channels"]}
    residuals = {record["residual_id"]: record for record in world["residuals"]}
    unknown_ids = frozenset(record["unknown_id"] for record in world["unknowns"])
    locations = frozenset(
        {
            world["volume_id"],
            *represented,
            *state_owners,
            *clocks,
            *channels,
            *relations,
            *(record["distribution_id"] for record in world["local_distributions"]),
        }
    )
    general_refs = frozenset(
        {
            *locations,
            *evidence_ids,
            *source_refs,
            *unknown_ids,
            *residuals,
        }
    )
    return _Context(
        world=world,
        evidence=evidence,
        relations=relations,
        evidence_ids=evidence_ids,
        source_refs=source_refs,
        represented=represented,
        locations=locations,
        general_refs=general_refs,
        unknown_ids=unknown_ids,
        residuals=residuals,
        state_owners=state_owners,
        clocks=clocks,
        channels=channels,
    )


def _authority_mapping(authorities: TransformationAuthorities) -> dict[str, Any]:
    if type(authorities) is not TransformationAuthorities:
        raise TransformationError("authorities must use TransformationAuthorities")
    try:
        mapping = copy.deepcopy(
            {
                "world_volume_artifact_sha256": authorities.world_volume_artifact_sha256,
                "normalized_states": list(authorities.normalized_states),
                "comparator_results": dict(authorities.comparator_results),
                "verification_artifacts": dict(authorities.verification_artifacts),
                "comparison_payloads": dict(authorities.comparison_payloads),
                "j_authorization_tuples": list(authorities.j_authorization_tuples),
                "independent_reviews": dict(authorities.independent_reviews),
            }
        )
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise TransformationError(f"authority bundle cannot be snapshotted: {error}") from error
    _require_native_json(mapping, label="transformation authority bundle")
    return mapping


def _validate_authority_hash_fields(value: object) -> None:
    required_hash_fields = {
        "world_volume_artifact_sha256",
        "payload_sha256",
        "verification_hash",
        "authorization_tuple_sha256",
        "review_sha256",
        "source_normalized_state_sha256",
        "target_normalized_state_sha256",
    }
    optional_hash_fields = {
        "normalized_state_sha256",
        "source_state_sha256",
        "target_state_sha256",
    }
    if type(value) is dict:
        for key, item in value.items():
            if key in required_hash_fields:
                _require_sha256(item, label=f"authority {key}")
            elif key in optional_hash_fields:
                _require_optional_sha256(item, label=f"authority {key}")
            elif key == "authorization_tuple_sha256s":
                if type(item) is not list:
                    raise TransformationError(
                        "authorization_tuple_sha256s must be a native JSON array"
                    )
                for tuple_hash in item:
                    _require_sha256(
                        tuple_hash, label="normalized J authorization tuple hash"
                    )
            _validate_authority_hash_fields(item)
    elif type(value) is list:
        for item in value:
            _validate_authority_hash_fields(item)


def _rfc3339_instant(value: object) -> Decimal | None:
    if not isinstance(value, str):
        return None
    match = _RFC3339_RE.fullmatch(value)
    if match is None:
        return None
    try:
        day = calendar_date.fromisoformat(match.group("date"))
    except ValueError:
        return None
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    if hour > 23 or minute > 59 or second > 60:
        return None
    fraction = match.group("fraction")
    fractional_seconds = Decimal(0 if fraction is None else f"0.{fraction}")
    offset_seconds = 0
    if match.group("zone").casefold() != "z":
        offset_hour = int(match.group("offset_hour"))
        offset_minute = int(match.group("offset_minute"))
        if offset_hour > 23 or offset_minute > 59:
            return None
        offset_seconds = (offset_hour * 60 + offset_minute) * 60
        if match.group("sign") == "-":
            offset_seconds = -offset_seconds
    local_seconds = Decimal(
        day.toordinal() * 86400 + hour * 3600 + minute * 60 + second
    )
    return local_seconds + fractional_seconds - Decimal(offset_seconds)


def _validate_j_authorities(
    mapping: Mapping[str, Any], context: _Context
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    tuples: dict[str, Mapping[str, Any]] = {}
    review_refs: list[str] = []
    for item in mapping["j_authorization_tuples"]:
        if not isinstance(item, Mapping) or set(item) != {
            "authorization_tuple",
            "authorization_tuple_sha256",
            "normalization_status",
            "validity_status",
        }:
            raise TransformationError("J authorization authority has an invalid shape")
        value = item["authorization_tuple"]
        if not isinstance(value, Mapping) or set(value) != _TUPLE_FIELDS:
            raise TransformationError("J authorization tuple is not atomic and exact")
        scalar_fields = (
            "source_ref",
            "decision_subject_ref",
            "object_ref",
            "action_ref",
            "jurisdiction",
            "independent_review_ref",
        )
        if any(
            not isinstance(value[field], str) or not value[field]
            for field in scalar_fields
        ):
            raise TransformationError("J tuple authority refs must be nonempty scalars")
        validity = value["validity_period"]
        if not isinstance(validity, Mapping) or set(validity) != {
            "start_time",
            "end_time",
        }:
            raise TransformationError("J validity_period has an invalid exact shape")
        start_time = _rfc3339_instant(validity["start_time"])
        end_value = validity["end_time"]
        end_time = None if end_value is None else _rfc3339_instant(end_value)
        if start_time is None or (end_value is not None and end_time is None):
            raise TransformationError("J validity_period is not RFC3339")
        if end_time is not None and end_time < start_time:
            raise TransformationError("J validity_period ends before it starts")
        revocations = value["revocation_conditions"]
        evidence_refs = value["evidence_refs"]
        if (
            not isinstance(revocations, list)
            or not revocations
            or len(revocations) != len(set(revocations))
            or any(not isinstance(item, str) or not item for item in revocations)
            or not isinstance(evidence_refs, list)
            or not evidence_refs
            or len(evidence_refs) != len(set(evidence_refs))
            or any(not isinstance(item, str) or not item for item in evidence_refs)
        ):
            raise TransformationError("J revocation and evidence lists must be nonempty and unique")
        tuple_hash = item["authorization_tuple_sha256"]
        if tuple_hash != _canonical_sha256(value) or tuple_hash in tuples:
            raise TransformationError("J tuple hash is stale or repeated")
        if item["normalization_status"] != "normalized" or item["validity_status"] != "valid":
            raise TransformationError("J tuple is not independently normalized and valid")
        if value["source_ref"] not in context.evidence_ids | context.source_refs:
            raise TransformationError("J tuple source_ref does not resolve U3")
        if value["decision_subject_ref"] not in context.locations:
            raise TransformationError("J tuple decision subject does not resolve U4")
        if value["object_ref"] not in context.general_refs:
            raise TransformationError("J tuple object does not resolve U3/U4")
        if not set(evidence_refs).issubset(context.evidence_ids):
            raise TransformationError("J tuple evidence does not resolve U3")
        tuples[tuple_hash] = item
        review_refs.append(value["independent_review_ref"])

    if len(review_refs) != len(set(review_refs)):
        raise TransformationError("J tuples must bind distinct independent reviews")

    reviews = _mapping_registry(
        mapping["independent_reviews"], label="independent review authority"
    )
    if set(reviews) != set(review_refs):
        raise TransformationError("independent reviews do not exactly cover J tuples")
    for key, review in reviews.items():
        if set(review) != {
            "independent_review_ref",
            "reviewer_ref",
            "authorization_tuple_sha256",
            "decision",
            "evidence_refs",
            "review_payload",
            "review_sha256",
        }:
            raise TransformationError("independent review has an invalid shape")
        tuple_hash = review["authorization_tuple_sha256"]
        tuple_value = (
            tuples.get(tuple_hash, {}).get("authorization_tuple")
            if isinstance(tuples.get(tuple_hash), Mapping)
            else None
        )
        review_evidence = review["evidence_refs"]
        if (
            review["independent_review_ref"] != key
            or tuple_hash not in tuples
            or tuples[tuple_hash]["authorization_tuple"]["independent_review_ref"] != key
            or not isinstance(review["reviewer_ref"], str)
            or not review["reviewer_ref"]
            or review["decision"] != "valid"
            or not isinstance(review_evidence, list)
            or not review_evidence
            or len(review_evidence) != len(set(review_evidence))
            or any(not isinstance(item, str) or not item for item in review_evidence)
            or not isinstance(review["review_payload"], Mapping)
            or not review["review_payload"]
            or review["review_sha256"] != _canonical_sha256(review["review_payload"])
            or not set(review_evidence).issubset(context.evidence_ids)
            or review["reviewer_ref"] == tuple_value["decision_subject_ref"]
            or review["reviewer_ref"] == tuple_value["source_ref"]
        ):
            raise TransformationError("independent J review is stale or invalid")
    return tuples, reviews


def _validate_authority_bundle(
    authorities: TransformationAuthorities,
    *,
    expected_authorities_sha256: str,
    expected_world_volume_artifact_sha256: str,
    context: _Context,
) -> _AuthorityBundle:
    mapping = _authority_mapping(authorities)
    _validate_authority_hash_fields(mapping)
    if _canonical_sha256(mapping) != expected_authorities_sha256:
        raise TransformationError("transformation authority bundle differs from external seal")
    if mapping["world_volume_artifact_sha256"] != expected_world_volume_artifact_sha256:
        raise TransformationError("authority bundle binds the wrong U4 artifact")

    normalized_raw = mapping["normalized_states"]
    if not isinstance(normalized_raw, Sequence) or isinstance(normalized_raw, (str, bytes)):
        raise TransformationError("normalized_states must be an ordered sequence")
    normalized: list[Mapping[str, Any]] = []
    normalized_refs: set[str] = set()
    for record in normalized_raw:
        if not isinstance(record, Mapping) or set(record) != _NORMALIZED_STATE_FIELDS:
            raise TransformationError("normalized state has an invalid exact shape")
        if record["axis_id"] not in _AXIS_SET or record["side"] not in {"source", "target"}:
            raise TransformationError("normalized state has an invalid axis or side")
        if not set(record["evidence_refs"]).issubset(context.evidence_ids):
            raise TransformationError("normalized state evidence does not resolve U3")
        status = record["status"]
        state = record["normalized_state"]
        state_ref = record["normalized_state_ref"]
        state_hash = record["normalized_state_sha256"]
        result = record["applicability_result"]
        criterion = record["applicability_criterion_id"]
        if status == "recorded":
            if (
                result != "applicable"
                or not isinstance(state, Mapping)
                or not isinstance(state_ref, str)
                or not state_ref
                or state_hash != _canonical_sha256(state)
                or state_ref in normalized_refs
            ):
                raise TransformationError("recorded normalized state is stale or incomplete")
            normalized_refs.add(state_ref)
        elif status == "not_applicable":
            if (
                result != "not_applicable"
                or not isinstance(criterion, str)
                or not criterion
                or not record["evidence_refs"]
                or state is not None
                or state_ref is not None
                or state_hash is not None
            ):
                raise TransformationError("not-applicable state lacks bilateral authority")
        else:
            if (
                result != "unknown"
                or state is not None
                or state_ref is not None
                or state_hash is not None
            ):
                raise TransformationError("missing normalized material must remain unknown")
        normalized.append(record)

    results = _mapping_registry(mapping["comparator_results"], label="comparator results")
    verifications = _mapping_registry(
        mapping["verification_artifacts"], label="verification artifacts"
    )
    payloads = _mapping_registry(mapping["comparison_payloads"], label="comparison payloads")
    for key, payload in payloads.items():
        if (
            set(payload) != _PAYLOAD_FIELDS
            or payload["payload_ref"] != key
            or payload["payload_kind"] not in _PAYLOAD_KINDS
            or payload["payload_sha256"] != _canonical_sha256(payload["payload"])
        ):
            raise TransformationError("comparison payload is stale or malformed")
    for key, verification in verifications.items():
        if (
            set(verification) != _VERIFICATION_FIELDS
            or verification["verification_artifact_ref"] != key
            or verification["verification_hash"]
            != _canonical_sha256(verification["artifact_payload"])
        ):
            raise TransformationError("verification artifact is stale or malformed")
    for key, result in results.items():
        if set(result) != _COMPARATOR_RESULT_FIELDS or result["comparator_result_ref"] != key:
            raise TransformationError("comparator result has an invalid exact shape")
        payload = payloads.get(result["comparison_payload_ref"])
        verification = verifications.get(result["verification_artifact_ref"])
        if payload is None or verification is None:
            raise TransformationError("comparator result has an unresolved witness")
        if (
            result["validation_status"] != "valid"
            or result["axis_id"] != payload["axis_id"]
            or result["source_state_sha256"] != payload["source_state_sha256"]
            or result["target_state_sha256"] != payload["target_state_sha256"]
            or verification["comparator_result_ref"] != key
            or verification["comparison_payload_ref"] != result["comparison_payload_ref"]
            or verification["axis_id"] != result["axis_id"]
            or verification["source_state_sha256"] != result["source_state_sha256"]
            or verification["target_state_sha256"] != result["target_state_sha256"]
            or verification["relation"] != result["relation"]
            or result["verification_hash"] != verification["verification_hash"]
            or not set(result["evidence_refs"]).issubset(context.evidence_ids)
        ):
            raise TransformationError("comparator, payload, and verification chain diverge")

    tuples, reviews = _validate_j_authorities(mapping, context)
    return _AuthorityBundle(
        mapping=mapping,
        normalized=tuple(normalized),
        results=results,
        verifications=verifications,
        payloads=payloads,
        tuples=tuples,
        reviews=reviews,
    )


def _validate_identity(
    identity: Mapping[str, Any], *, kind: str, side: str, context: _Context
) -> None:
    location = identity["location_ref"]
    if not set(identity["evidence_ids"]).issubset(context.evidence_ids):
        raise TransformationError("transformation identity evidence does not resolve U3")
    if kind == "scale":
        if identity["identity_type"] != "scale-state" or location not in context.represented:
            raise TransformationError("scale identity does not resolve a U4 scale location")
    elif kind == "circle-relation":
        relation = context.relations.get(location)
        if (
            identity["identity_type"] != "circle-relation"
            or relation is None
            or relation["relation_kind"] != "Rcc"
            or identity["value"] != relation["record_sha256"]
        ):
            raise TransformationError("circle-relation identity differs from Rcc authority")
    elif side == "input":
        entry = next(
            (record for record in context.evidence["entries"] if record["evidence_id"] == location),
            None,
        )
        if (
            identity["identity_type"] != "source-representation"
            or entry is None
            or identity["value"] != entry["identity"]
        ):
            raise TransformationError("representation input does not resolve U3 identity")
    else:
        represented = context.represented.get(location)
        if (
            identity["identity_type"] != "represented-state"
            or represented is None
            or identity["value"] != represented["identity_criteria"]
        ):
            raise TransformationError("representation output does not resolve U4 identity")


def _normalized_relation(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    *,
    axis_id: str,
    declared_relation: str | None,
) -> str:
    source_status = source["status"]
    target_status = target["status"]
    unknown_statuses = {"unknown", "not_observable", "withheld_for_protection"}
    if source_status in unknown_statuses or target_status in unknown_statuses:
        return "unknown"
    if source_status == "not_applicable" and target_status == "not_applicable":
        if source["applicability_criterion_id"] != target["applicability_criterion_id"]:
            raise TransformationError("bilateral N/A uses different applicability criteria")
        return "equal"
    if source_status == "not_applicable" or target_status == "not_applicable":
        return "incomparable"
    source_state = source["normalized_state"]
    target_state = target["normalized_state"]
    if source_state == target_state:
        return "equal"
    if axis_id == "J":
        source_hashes = source_state["authorization_tuple_sha256s"]
        target_hashes = target_state["authorization_tuple_sha256s"]
        source_set = set(source_hashes)
        target_set = set(target_hashes)
        if source_set < target_set:
            return "expands"
        if target_set < source_set:
            return "contracts"
        return "incomparable"
    if declared_relation == "equal":
        raise TransformationError("unequal normalized states cannot claim equality")
    return declared_relation or "incomparable"


def _validate_j_payload(
    payload: Mapping[str, Any],
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    bundle: _AuthorityBundle,
) -> None:
    if payload["payload_kind"] != "authorization-difference":
        raise TransformationError("J authorization change lacks an authorization-difference payload")
    source_hashes = source["normalized_state"]["authorization_tuple_sha256s"]
    target_hashes = target["normalized_state"]["authorization_tuple_sha256s"]
    source_tuples = [bundle.tuples[value]["authorization_tuple"] for value in source_hashes]
    target_tuples = [bundle.tuples[value]["authorization_tuple"] for value in target_hashes]
    source_set = set(source_hashes)
    new_tuples = [
        bundle.tuples[value]["authorization_tuple"]
        for value in target_hashes
        if value not in source_set
    ]
    body = payload["payload"]
    if not isinstance(body, Mapping) or set(body) != {
        "source_tuples",
        "target_tuples",
        "new_target_tuples",
    }:
        raise TransformationError("J authorization difference has an invalid shape")
    if (
        body["source_tuples"] != source_tuples
        or body["target_tuples"] != target_tuples
        or body["new_target_tuples"] != new_tuples
    ):
        raise TransformationError("J authorization difference is stale or Cartesianized")


def _validate_builtin_deep_equality(
    *,
    payload: Mapping[str, Any],
    verification: Mapping[str, Any],
    result: Mapping[str, Any],
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> None:
    equal = source["normalized_state"] == target["normalized_state"]
    expected_payload = {
        "source_normalized_state_ref": source["normalized_state_ref"],
        "target_normalized_state_ref": target["normalized_state_ref"],
        "source_normalized_state_sha256": source["normalized_state_sha256"],
        "target_normalized_state_sha256": target["normalized_state_sha256"],
        "deep_equal": equal,
    }
    expected_verification = {
        "axis_id": result["axis_id"],
        "comparison_payload_ref": payload["payload_ref"],
        "source_normalized_state_ref": source["normalized_state_ref"],
        "target_normalized_state_ref": target["normalized_state_ref"],
        "source_state_sha256": source["normalized_state_sha256"],
        "target_state_sha256": target["normalized_state_sha256"],
        "relation": result["relation"],
        "deep_equal": equal,
    }
    if (
        source["status"] != "recorded"
        or target["status"] != "recorded"
        or payload["payload_kind"] != "deep-equality"
        or payload["payload"] != expected_payload
        or verification["artifact_payload"] != expected_verification
        or not equal
        or result["relation"] != "equal"
    ):
        raise TransformationError(
            "builtin deep equality payload, result, and verification diverge"
        )


def _classification(relations: set[str]) -> str:
    if "incomparable" in relations:
        return "horizontal_or_incomparable"
    if "expands" in relations and "contracts" in relations:
        return "mixed"
    if "unknown" in relations:
        return "unresolved"
    if relations == {"equal"}:
        return "all_equal"
    if relations <= {"equal", "expands"}:
        return "elevation"
    return "reduction"


def _validate_scale_transform(
    transform: Mapping[str, Any],
    *,
    context: _Context,
    bundle: _AuthorityBundle,
    used_normalized: set[tuple[str, str, str]],
    used_results: set[str],
    used_payloads: set[str],
    used_verifications: set[str],
    used_tuples: set[str],
) -> None:
    transform_id = transform["transform_id"]
    differences = transform["axis_differences"]
    axis_ids = [record["axis_id"] for record in differences]
    if len(differences) != 9 or len(axis_ids) != len(set(axis_ids)) or set(axis_ids) != _AXIS_SET:
        raise TransformationError("scale transform must contain nine unique axis differences")
    normalized_index: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for record in bundle.normalized:
        key = (record["transform_id"], record["side"], record["axis_id"])
        if key in normalized_index:
            raise TransformationError("duplicate normalized transform/side/axis authority")
        normalized_index[key] = record

    source_location = transform["input_identity"]["location_ref"]
    target_location = transform["output_identity"]["location_ref"]
    relations: set[str] = set()
    for difference in differences:
        axis_id = difference["axis_id"]
        source_key = (transform_id, "source", axis_id)
        target_key = (transform_id, "target", axis_id)
        source = normalized_index.get(source_key)
        target = normalized_index.get(target_key)
        if source is None or target is None:
            raise TransformationError("scale axis lacks source or target normalized authority")
        used_normalized.update((source_key, target_key))
        if source["location_ref"] != source_location or target["location_ref"] != target_location:
            raise TransformationError("normalized state location differs from scale identity")
        for record, location_ref in ((source, source_location), (target, target_location)):
            if record["status"] == "recorded":
                state = record["normalized_state"]
                expected = {
                    "location_ref": location_ref,
                    "axis_id": axis_id,
                    "value": context.represented[location_ref]["scale_profile"][axis_id],
                }
                if axis_id == "J":
                    expected["authorization_tuple_sha256s"] = state.get(
                        "authorization_tuple_sha256s"
                    )
                    hashes = expected["authorization_tuple_sha256s"]
                    if (
                        not isinstance(hashes, list)
                        or len(hashes) != len(set(hashes))
                        or hashes != sorted(hashes)
                        or any(value not in bundle.tuples for value in hashes)
                    ):
                        raise TransformationError(
                            "J normalized tuple hashes are not a canonical resolved set"
                        )
                    used_tuples.update(hashes)
                if state != expected:
                    raise TransformationError("normalized state differs from exact U4 scale value")

        for side, authority in (("source", source), ("target", target)):
            ledger_state = difference[f"{side}_state"]
            if (
                ledger_state["status"] != authority["status"]
                or ledger_state["normalized_state_ref"] != authority["normalized_state_ref"]
                or ledger_state["normalized_state_sha256"] != authority["normalized_state_sha256"]
            ):
                raise TransformationError("ledger scale state differs from normalized authority")

        witness = difference["order_witness"]
        result_ref = witness["comparator_result_ref"]
        result = bundle.results.get(result_ref) if result_ref is not None else None
        actual_relation = _normalized_relation(
            source,
            target,
            axis_id=axis_id,
            declared_relation=None if result is None else result["relation"],
        )
        if actual_relation == "unknown":
            payload_witness = witness["comparison_payload"]
            if (
                difference["relation"] != "unknown"
                or result is not None
                or witness["comparator_id"] is not None
                or witness["comparator_version"] is not None
                or witness["verifier_id"] is not None
                or witness["evidence_refs"] != []
                or payload_witness["payload_kind"] is not None
                or payload_witness["payload_ref"] is not None
                or payload_witness["payload_sha256"] is not None
                or witness["verification_artifact_ref"] is not None
                or witness["verification_hash"] is not None
                or witness["validation_status"] != "missing"
            ):
                raise TransformationError("unknown axis must have no comparator witness")
            relations.add("unknown")
            continue
        if result is None:
            raise TransformationError("resolved scale axis lacks a comparator result")
        payload = bundle.payloads[result["comparison_payload_ref"]]
        verification = bundle.verifications[result["verification_artifact_ref"]]
        if (
            result["axis_id"] != axis_id
            or result["source_status"] != source["status"]
            or result["target_status"] != target["status"]
            or result["source_state_sha256"] != source["normalized_state_sha256"]
            or result["target_state_sha256"] != target["normalized_state_sha256"]
            or result["relation"] != actual_relation
            or difference["relation"] != actual_relation
            or witness["comparator_id"] != result["comparator_id"]
            or witness["comparator_version"] != result["comparator_version"]
            or witness["verifier_id"] != verification["verifier_id"]
            or witness["evidence_refs"] != result["evidence_refs"]
            or witness["comparison_payload"]["payload_kind"] != payload["payload_kind"]
            or witness["comparison_payload"]["payload_ref"] != payload["payload_ref"]
            or witness["comparison_payload"]["payload_sha256"] != payload["payload_sha256"]
            or witness["verification_artifact_ref"] != verification["verification_artifact_ref"]
            or witness["verification_hash"] != verification["verification_hash"]
            or witness["validation_status"] != "valid"
        ):
            raise TransformationError("ledger scale witness differs from external authority")
        if result["comparator_id"] == "builtin:deep-equality":
            _validate_builtin_deep_equality(
                payload=payload,
                verification=verification,
                result=result,
                source=source,
                target=target,
            )
        if (
            axis_id == "J"
            and source["status"] == "recorded"
            and target["status"] == "recorded"
            and actual_relation in {"expands", "contracts"}
        ):
            _validate_j_payload(payload, source, target, bundle)
        used_results.add(result_ref)
        used_payloads.add(payload["payload_ref"])
        used_verifications.add(verification["verification_artifact_ref"])
        relations.add(actual_relation)
    if transform["transformation_class"] != _classification(relations):
        raise TransformationError("scale transformation_class was not recomputed")


def _validate_partial_order_invariants(
    transformations: Sequence[Mapping[str, Any]],
    bundle: _AuthorityBundle,
) -> None:
    normalized = {
        (record["transform_id"], record["side"], record["axis_id"]): record
        for record in bundle.normalized
    }
    entries: list[dict[str, Any]] = []
    for transform in transformations:
        if transform["kind"] != "scale":
            continue
        transform_id = transform["transform_id"]
        for difference in transform["axis_differences"]:
            axis_id = difference["axis_id"]
            source = normalized[(transform_id, "source", axis_id)]
            target = normalized[(transform_id, "target", axis_id)]
            if source["status"] != "recorded" or target["status"] != "recorded":
                continue
            result_ref = difference["order_witness"]["comparator_result_ref"]
            if result_ref is None:
                continue
            result = bundle.results[result_ref]
            payload = bundle.payloads[result["comparison_payload_ref"]]
            verification = bundle.verifications[result["verification_artifact_ref"]]
            entries.append(
                {
                    "axis_id": axis_id,
                    "source_hash": source["normalized_state_sha256"],
                    "target_hash": target["normalized_state_sha256"],
                    "relation": result["relation"],
                    "witness_signature": (
                        result["comparator_id"],
                        result["comparator_version"],
                        payload["payload_kind"],
                        verification["verifier_id"],
                    ),
                    "auxiliary_signature": payload["payload_sha256"],
                }
            )

    by_pair: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for entry in entries:
        key = (entry["axis_id"], entry["source_hash"], entry["target_hash"])
        by_pair.setdefault(key, []).append(entry)
        if (
            entry["source_hash"] == entry["target_hash"]
            and entry["relation"] != "equal"
        ):
            raise TransformationError("normalized partial order is not reflexive")

    ordered_relations = {"equal", "expands", "contracts"}
    unresolved_relations = {"incomparable", "unknown"}
    for records in by_pair.values():
        relations = {record["relation"] for record in records}
        auxiliary = {record["auxiliary_signature"] for record in records}
        witnesses = {record["witness_signature"] for record in records}
        if (
            (len(auxiliary) > 1 or len(witnesses) > 1)
            and any(relation in ordered_relations for relation in relations)
        ):
            raise TransformationError(
                "auxiliary mapping conflict must remain incomparable or unknown"
            )
        if len(relations) > 1 and not relations.issubset(unresolved_relations):
            raise TransformationError("same normalized pair has inconsistent order results")

    reverse_relation = {
        "equal": "equal",
        "expands": "contracts",
        "contracts": "expands",
    }
    for entry in entries:
        relation = entry["relation"]
        if relation not in ordered_relations:
            continue
        reverse = by_pair.get(
            (entry["axis_id"], entry["target_hash"], entry["source_hash"]),
            [],
        )
        for reverse_entry in reverse:
            reverse_value = reverse_entry["relation"]
            if reverse_value in unresolved_relations:
                if reverse_entry["witness_signature"] == entry["witness_signature"]:
                    raise TransformationError(
                        "bidirectional normalized order has an unexplained incomparable result"
                    )
                continue
            if (
                reverse_value != reverse_relation[relation]
                or reverse_entry["witness_signature"] != entry["witness_signature"]
            ):
                raise TransformationError(
                    "bidirectional normalized order violates antisymmetry or witness consistency"
                )

    def composed_relation(left: str, right: str) -> str | None:
        if left == "equal":
            return right
        if right == "equal":
            return left
        if left == right and left in {"expands", "contracts"}:
            return left
        return None

    for left in entries:
        if left["relation"] not in ordered_relations:
            continue
        for right in entries:
            if (
                right["relation"] not in ordered_relations
                or left["axis_id"] != right["axis_id"]
                or left["target_hash"] != right["source_hash"]
                or left["source_hash"] == left["target_hash"]
                or right["source_hash"] == right["target_hash"]
            ):
                continue
            expected = composed_relation(left["relation"], right["relation"])
            if expected is None:
                continue
            direct_records = by_pair.get(
                (left["axis_id"], left["source_hash"], right["target_hash"]),
                [],
            )
            for direct in direct_records:
                composable = (
                    left["witness_signature"]
                    == right["witness_signature"]
                    == direct["witness_signature"]
                    and left["auxiliary_signature"]
                    == right["auxiliary_signature"]
                    == direct["auxiliary_signature"]
                )
                if composable:
                    if direct["relation"] != expected:
                        raise TransformationError(
                            "composable normalized order violates transitivity"
                        )
                elif direct["relation"] in ordered_relations:
                    raise TransformationError(
                        "noncomposable version or witness cannot claim transitive order"
                    )


def _validate_nonflattening_records(
    transformations: Sequence[Mapping[str, Any]], context: _Context
) -> None:
    component_ids: list[str] = []
    loss_ids: list[str] = []
    effect_ids: list[str] = []
    variable_ids: list[str] = []
    condition_ids: list[str] = []
    for transform in transformations:
        local_component_ids = [
            record["component_id"]
            for section in ("preserved", "changed", "folded", "omitted", "unknown")
            for record in transform[section]
        ]
        _unique(local_component_ids, label="local component")
        component_ids.extend(local_component_ids)
        local_components = set(local_component_ids)
        for section in ("preserved", "changed", "folded", "omitted", "unknown"):
            for component in transform[section]:
                if component["location_ref"] not in context.locations:
                    raise TransformationError("component location does not resolve U4")
                if not set(component["source_refs"]).issubset(context.general_refs) or not set(
                    component["target_refs"]
                ).issubset(context.general_refs):
                    raise TransformationError("component source or target ref is unresolved")
                if not set(component["evidence_ids"]).issubset(context.evidence_ids):
                    raise TransformationError("component evidence does not resolve U3")
                unknown_id = component["unknown_id"]
                if unknown_id is not None and unknown_id not in context.unknown_ids:
                    raise TransformationError("component unknown_id does not resolve U4")
                if section == "unknown" and unknown_id is None:
                    raise TransformationError("unknown component lacks its U4 unknown_id")

        local_variable_ids = [
            record["variable_ref"] for record in transform["effective_variables"]
        ]
        _unique(local_variable_ids, label="local effective variable")
        variable_ids.extend(local_variable_ids)
        local_variables = set(local_variable_ids)
        local_variable_locations = {
            record["variable_ref"]: record["location_ref"]
            for record in transform["effective_variables"]
        }
        for variable in transform["effective_variables"]:
            owner = context.state_owners.get(variable["state_id"])
            state_variable = None
            if owner is not None:
                state_variable = next(
                    (
                        item
                        for item in owner[2]["variables"]
                        if item["name"] == variable["variable_name"]
                    ),
                    None,
                )
            if (
                owner is None
                or owner[0] != variable["location_ref"]
                or owner[1] != variable["state_kind"]
                or state_variable is None
                or state_variable["clock_id"] != variable["clock_id"]
                or not set(variable["evidence_ids"]).issubset(context.evidence_ids)
            ):
                raise TransformationError("effective variable does not resolve exact U4 state")

        for loss in transform["task_relative_loss"]:
            loss_ids.append(loss["loss_id"])
            if (
                loss["location_ref"] not in context.locations
                or not set(loss["affected_component_ids"]).issubset(local_components)
                or not set(loss["evidence_ids"]).issubset(context.evidence_ids)
            ):
                raise TransformationError("task-relative loss has an unresolved nested ref")
        affected_variables: set[str] = set()
        for effect in transform["location_effects"]:
            effect_ids.append(effect["effect_id"])
            effect_variables = list(effect["variable_refs"])
            if (
                effect["location_ref"] not in context.locations
                or not effect_variables
                or len(effect_variables) != len(set(effect_variables))
                or not set(effect_variables).issubset(local_variables)
                or any(
                    local_variable_locations[variable_ref]
                    != effect["location_ref"]
                    for variable_ref in effect_variables
                    if variable_ref in local_variable_locations
                )
                or not set(effect["evidence_ids"]).issubset(context.evidence_ids)
            ):
                raise TransformationError("location effect has an unresolved nested ref")
            affected_variables.update(effect_variables)

        if transform["kind"] != "scale" and affected_variables != local_variables:
            raise TransformationError(
                "non-scale effective variables lack exact location-effect coverage"
            )

        local_condition_ids = [
            record["condition_id"] for record in transform["return_conditions"]
        ]
        _unique(local_condition_ids, label="local return condition")
        condition_ids.extend(local_condition_ids)
        local_conditions = set(local_condition_ids)
        for residual in transform["residuals"]:
            authority = context.residuals.get(residual["residual_id"])
            if (
                authority is None
                or residual["location_ref"] != authority["location_ref"]
                or not set(residual["evidence_ids"]).issubset(context.evidence_ids)
                or not set(residual["return_condition_ids"]).issubset(local_conditions)
            ):
                raise TransformationError("residual does not resolve exact U4 authority")
        local_residuals = {record["residual_id"] for record in transform["residuals"]}
        for condition in transform["return_conditions"]:
            if (
                not set(condition["trigger_refs"]).issubset(
                    context.general_refs | local_residuals
                )
                or not set(condition["required_variable_refs"]).issubset(local_variables)
                or not set(condition["evidence_ids"]).issubset(context.evidence_ids)
            ):
                raise TransformationError("return condition has an unresolved nested ref")

        if transform["kind"] != "scale" and (
            transform["changed"]
            or transform["folded"]
            or transform["omitted"]
            or transform["task_relative_loss"]
            or transform["effective_variables"]
        ) and not transform["location_effects"]:
            raise TransformationError(
                "non-scale transformation flattens local gain, damage, exit cost, or spillover"
            )
        if transform["kind"] != "scale" and not any(
            transform[field]
            for field in (
                "preserved",
                "changed",
                "folded",
                "omitted",
                "unknown",
                "task_relative_loss",
                "location_effects",
                "effective_variables",
                "residuals",
                "return_conditions",
            )
        ):
            raise TransformationError(
                "non-scale transformation has a vacuous closed audit surface"
            )
    _unique(component_ids, label="component")
    _unique(loss_ids, label="loss")
    _unique(effect_ids, label="effect")
    _unique(variable_ids, label="effective variable")
    _unique(condition_ids, label="return condition")


def validate_transformations(
    document: Mapping[str, object],
    *,
    source_volume: Mapping[str, object],
    evidence_ledger: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
    expected_world_volume_artifact_sha256: str,
    relation_refs: Mapping[str, Mapping[str, object]],
    expected_relation_refs_sha256: str,
    authorities: TransformationAuthorities,
    expected_authorities_sha256: str,
) -> tuple[str, ...]:
    (
        expected_run_id,
        expected_version_binding,
        expected_evidence_artifact_sha256,
        expected_world_volume_artifact_sha256,
        expected_relation_refs_sha256,
        expected_authorities_sha256,
    ) = _validated_public_authorities(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        expected_world_volume_artifact_sha256=expected_world_volume_artifact_sha256,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
        expected_authorities_sha256=expected_authorities_sha256,
    )
    context = _build_context(
        source_volume,
        evidence_ledger,
        relation_refs,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        expected_world_volume_artifact_sha256=expected_world_volume_artifact_sha256,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
    )
    snapshot = _snapshot_mapping(document, label="transformation ledger")
    try:
        snapshot = validate_phase_artifact(
            "ultra-transformation-ledger.schema.json",
            snapshot,
            expected_schema_id="crossframe.ultra.v82.transformation-ledger",
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_phase_id="U5",
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise TransformationError(f"invalid U5 transformation ledger: {error}") from error
    if (
        snapshot["evidence_artifact_sha256"] != expected_evidence_artifact_sha256
        or snapshot["evidence_content_sha256"] != context.evidence["content_sha256"]
        or snapshot["world_volume_artifact_sha256"]
        != expected_world_volume_artifact_sha256
        or snapshot["world_volume_content_sha256"] != context.world["content_sha256"]
    ):
        raise TransformationError("U5 upstream artifact/content hash chain is stale")

    bundle = _validate_authority_bundle(
        authorities,
        expected_authorities_sha256=expected_authorities_sha256,
        expected_world_volume_artifact_sha256=expected_world_volume_artifact_sha256,
        context=context,
    )
    transformations = snapshot["transformations"]
    transform_ids = [record["transform_id"] for record in transformations]
    _unique(transform_ids, label="transformation")
    if {record["kind"] for record in transformations} != _TRANSFORM_KINDS:
        raise TransformationError("U5 must retain all three transformation kinds")
    for transform in transformations:
        _validate_identity(transform["input_identity"], kind=transform["kind"], side="input", context=context)
        _validate_identity(transform["output_identity"], kind=transform["kind"], side="output", context=context)
        if transform["kind"] != "scale" and transform["axis_differences"]:
            raise TransformationError("non-scale transform cannot impersonate scale axes")

    used_normalized: set[tuple[str, str, str]] = set()
    used_results: set[str] = set()
    used_payloads: set[str] = set()
    used_verifications: set[str] = set()
    used_tuples: set[str] = set()
    for transform in transformations:
        if transform["kind"] == "scale":
            _validate_scale_transform(
                transform,
                context=context,
                bundle=bundle,
                used_normalized=used_normalized,
                used_results=used_results,
                used_payloads=used_payloads,
                used_verifications=used_verifications,
                used_tuples=used_tuples,
            )
    _validate_partial_order_invariants(transformations, bundle)
    all_normalized = {
        (record["transform_id"], record["side"], record["axis_id"])
        for record in bundle.normalized
    }
    if used_normalized != all_normalized:
        raise TransformationError("normalized authority coverage is missing or orphaned")
    if used_results != set(bundle.results):
        raise TransformationError("comparator result registry has missing or orphaned records")
    if used_payloads != set(bundle.payloads) or used_verifications != set(bundle.verifications):
        raise TransformationError("comparison witness registries have missing or orphaned records")
    if used_tuples != set(bundle.tuples):
        raise TransformationError("J tuple registry has missing or orphaned authority")
    _validate_nonflattening_records(transformations, context)
    return tuple(transform_ids)


def _checked_hops(cascade: Mapping[str, object]) -> tuple[dict[str, Any], ...]:
    snapshot = _snapshot_mapping(cascade, label="cascade")
    if set(snapshot) != {"cascade_id", "hops"}:
        raise ChannelContinuityError("cascade must contain only cascade_id and hops")
    if not isinstance(snapshot["cascade_id"], str) or not snapshot["cascade_id"]:
        raise ChannelContinuityError("cascade_id must be explicit")
    raw_hops = snapshot["hops"]
    if not isinstance(raw_hops, Sequence) or isinstance(raw_hops, (str, bytes)) or not raw_hops:
        raise ChannelContinuityError("cascade hops must be a nonempty sequence")
    required = {
        "hop_id",
        "from_position_id",
        "to_position_id",
        "channel_id",
        "boundary_validated",
        "representation_qualified",
        "threshold_met",
        "identity_preserved",
        "acl_authorized",
        "evidence_ids",
    }
    hops: list[dict[str, Any]] = []
    for ordinal, value in enumerate(raw_hops, start=1):
        if not isinstance(value, Mapping) or set(value) != required:
            raise ChannelContinuityError(f"cascade hop {ordinal} has an invalid exact shape")
        hop = copy.deepcopy(dict(value))
        for field in (
            "boundary_validated",
            "representation_qualified",
            "threshold_met",
            "identity_preserved",
            "acl_authorized",
        ):
            if hop[field] is not True:
                raise ChannelContinuityError(f"cascade hop {ordinal} fails {field}")
        hops.append(hop)
    _unique([hop["hop_id"] for hop in hops], label="cascade hop")
    return tuple(hops)


def validate_cascade(
    cascade: Mapping[str, object],
    volume: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
    relation_refs: Mapping[str, Mapping[str, object]],
    expected_relation_refs_sha256: str,
) -> tuple[str, ...]:
    try:
        world = _snapshot_mapping(volume, label="cascade source volume")
        evidence = _snapshot_mapping(evidence_ledger, label="cascade evidence ledger")
        frozen_relations = _snapshot_mapping(
            relation_refs, label="cascade relation authority"
        )
        hops = _checked_hops(cascade)
        validate_world_volume(
            world,
            evidence_ledger=evidence,
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
            relation_refs=frozen_relations,
            expected_relation_refs_sha256=expected_relation_refs_sha256,
        )
    except ChannelContinuityError:
        raise
    except (TransformationError, WorldVolumeError) as error:
        raise ChannelContinuityError(f"invalid cascade source volume: {error}") from error
    positions = {
        record["position_id"]: record for record in world["positions"]
    }
    channels = {record["channel_id"]: record for record in world["channels"]}
    evidence_ids = {record["evidence_id"] for record in evidence["entries"]}
    previous_target: str | None = None
    ordered_channels: list[str] = []
    for hop in hops:
        source = hop["from_position_id"]
        target = hop["to_position_id"]
        channel = channels.get(hop["channel_id"])
        if source not in positions or target not in positions or channel is None:
            raise ChannelContinuityError("cascade hop has an unresolved endpoint or channel")
        if previous_target is not None and source != previous_target:
            raise ChannelContinuityError("cascade hop is disconnected from its predecessor")
        source_circle = positions[source]["circle_id"]
        target_circle = positions[target]["circle_id"]
        if source_circle != target_circle:
            has_boundary_authority = any(
                authority["relation_kind"] == "Rcc"
                and authority["record"]["source_circle_ref"] == source_circle
                and authority["record"]["target_circle_ref"] == target_circle
                and authority["record"]["channel"]
                in {None, channel["channel_id"]}
                for authority in frozen_relations.values()
            )
            if not has_boundary_authority:
                raise ChannelContinuityError(
                    "cross-circle cascade hop lacks frozen Rcc boundary authority"
                )
        mapping = channel["identity_mapping"]
        acl = channel["acl"]
        hop_evidence = set(hop["evidence_ids"])
        if (
            channel["active"] is not True
            or channel["from_position_id"] != source
            or channel["to_position_id"] != target
            or mapping["source_k_ref"] != source
            or mapping["target_k_ref"] != target
            or mapping["preserves_identity"] is not True
            or source not in acl["authorized_position_ids"]
            or not hop_evidence
            or not hop_evidence.issubset(evidence_ids)
            or not hop_evidence.issubset(set(channel["evidence_ids"]))
            or not hop_evidence.issubset(set(acl["authorization_evidence_ids"]))
        ):
            raise ChannelContinuityError("cascade hop fails channel, K, ACL, or evidence authority")
        ordered_channels.append(channel["channel_id"])
        previous_target = target
    return tuple(ordered_channels)


__all__ = (
    "ChannelContinuityError",
    "TransformationAuthorities",
    "TransformationError",
    "validate_cascade",
    "validate_transformations",
)
