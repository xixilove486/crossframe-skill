from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from .errors import UltraSchemaError
from .evidence import EvidenceValidationError, validate_evidence_entry
from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import build_schema_registry, validate_phase_artifact


_AXES = frozenset("AXTOCRINJ")
_CLOCK_KINDS = frozenset(
    {"immediate", "interaction", "organizational", "institutional", "long-term"}
)
_DISTRIBUTION_KINDS = frozenset(
    {"power", "constraint", "exit", "burden", "spillover"}
)
_IDENTITY_STRENGTH = {
    "unknown": 0,
    "user-claim": 0,
    "model-candidate": 0,
    "simulated": 0,
    "inferred": 1,
    "competing": 1,
    "reported": 2,
    "observed": 3,
}
_CLOCK_DELTA_RE = re.compile(
    r"^P(?:(?P<days>[1-9]\d{0,8})D)?"
    r"(?:T(?:(?P<hours>[1-9]|1\d|2[0-3])H)?"
    r"(?:(?P<minutes>[1-9]|[1-5]\d)M)?"
    r"(?:(?P<seconds>[1-9]|[1-5]\d)S)?)?$"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_WORLD_SCHEMA_ID = "https://crossframe.local/schemas/ultra-world-volume.schema.json"


class WorldVolumeError(ValueError):
    """Raised when a sealed Omega artifact violates its frozen authorities."""


@dataclass(frozen=True, slots=True)
class StateDiff:
    source_volume_sha256: str
    event_id: str
    changed_positions: tuple[str, ...]
    unchanged_positions: tuple[str, ...]
    changed_relations: tuple[str, ...]
    advanced_clocks: tuple[str, ...]
    inherited_unknown_ids: tuple[str, ...]
    inherited_residual_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _WorldAuthority:
    evidence_ids: frozenset[str]
    evidence_entries: Mapping[str, Mapping[str, Any]]
    source_refs: frozenset[str]
    relation_refs: Mapping[str, Mapping[str, Any]]


def _require_native_json(value: object, *, label: str) -> None:
    value_type = type(value)
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise WorldVolumeError(f"{label} has a non-native JSON object key")
            _require_native_json(item, label=label)
        return
    if value_type is list:
        for item in value:
            _require_native_json(item, label=label)
        return
    if value_type in {str, int, float, bool, type(None)}:
        return
    raise WorldVolumeError(f"{label} contains a non-native JSON value")


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise WorldVolumeError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise WorldVolumeError(f"{label} cannot be snapshotted: {error}") from error
    _require_native_json(snapshot, label=label)
    return snapshot


def _canonical_sha256(value: object) -> str:
    try:
        return sha256_bytes(canonical_json_bytes(value))
    except (MemoryError, RecursionError, TypeError, ValueError) as error:
        raise WorldVolumeError(f"authority is not canonical JSON: {error}") from error


def _require_sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise WorldVolumeError(f"{label} must be a lowercase 64-hex SHA-256")
    return value


def _validated_public_authorities(
    *,
    expected_run_id: object,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: object,
    expected_relation_refs_sha256: object,
) -> tuple[str, dict[str, Any], str, str]:
    if type(expected_run_id) is not str or not expected_run_id:
        raise WorldVolumeError("expected_run_id must be a nonempty native string")
    binding = _snapshot_mapping(
        expected_version_binding, label="expected version binding"
    )
    evidence_hash = _require_sha256(
        expected_evidence_artifact_sha256,
        label="expected evidence artifact hash",
    )
    relation_hash = _require_sha256(
        expected_relation_refs_sha256,
        label="expected relation authority hash",
    )
    return expected_run_id, binding, evidence_hash, relation_hash


def _require_unique(values: Sequence[str], *, label: str) -> None:
    if len(values) != len(set(values)):
        raise WorldVolumeError(f"duplicate {label} identifier")


def _by_id(
    records: Sequence[Mapping[str, Any]], field: str, *, label: str
) -> dict[str, Mapping[str, Any]]:
    identifiers = [record[field] for record in records]
    _require_unique(identifiers, label=label)
    return dict(zip(identifiers, records, strict=True))


def _represented(volume: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(volume["actors"]) + tuple(volume["circles"]) + tuple(
        volume["positions"]
    )


def _state_catalogs(
    volume: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    material: dict[str, Mapping[str, Any]] = {}
    meaning: dict[str, Mapping[str, Any]] = {}
    for location in _represented(volume):
        for field, catalog in (("M_state", material), ("Psi_state", meaning)):
            state = location[field]
            state_id = state["state_id"]
            if state_id in catalog:
                raise WorldVolumeError(f"duplicate local {field} identifier")
            catalog[state_id] = state
    return material, meaning


@lru_cache(maxsize=2)
def _relation_record_validator(relation_kind: str) -> Draft202012Validator:
    definition = "membership" if relation_kind == "Rac" else "circleRelation"
    return Draft202012Validator(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": f"{_WORLD_SCHEMA_ID}#/$defs/{definition}",
        },
        registry=build_schema_registry(),
        format_checker=FormatChecker(),
    )


def _validate_prospective_relation(
    volume: Mapping[str, Any],
    *,
    relation_kind: str,
    current_record: Mapping[str, Any],
    prospective_record: Mapping[str, Any],
    channel: Mapping[str, Any],
    authority: _WorldAuthority,
) -> None:
    try:
        _relation_record_validator(relation_kind).validate(prospective_record)
    except ValidationError as error:
        raise WorldVolumeError(
            f"prospective {relation_kind} record violates the frozen schema: {error}"
        ) from error

    actors = _by_id(volume["actors"], "actor_id", label="actor")
    circles = _by_id(volume["circles"], "circle_id", label="circle")
    positions = _by_id(volume["positions"], "position_id", label="position")
    channels = _by_id(volume["channels"], "channel_id", label="channel")
    target_position = positions[channel["to_position_id"]]
    source_position = positions[channel["from_position_id"]]

    records_field = "memberships" if relation_kind == "Rac" else "circle_relations"
    current_matches = [
        index
        for index, record in enumerate(volume[records_field])
        if record == current_record
    ]
    if len(current_matches) != 1:
        raise WorldVolumeError("prospective relation cannot replace one exact frozen record")
    prospective_records = [copy.deepcopy(record) for record in volume[records_field]]
    prospective_records[current_matches[0]] = copy.deepcopy(dict(prospective_record))
    encoded_records = [canonical_json_bytes(record) for record in prospective_records]
    if len(encoded_records) != len(set(encoded_records)):
        raise WorldVolumeError("prospective relation creates a duplicate typed record")

    if relation_kind == "Rac":
        actor_ref = prospective_record["actor_ref"]
        circle_ref = prospective_record["circle_ref"]
        roles = prospective_record["roles"]
        if actor_ref not in actors or circle_ref not in circles:
            raise WorldVolumeError("prospective Rac has an unknown actor or circle")
        if not roles or len(roles) != len(set(roles)):
            raise WorldVolumeError("prospective Rac roles must be nonempty and unique")
        position_tuples = {
            (position["actor_id"], position["circle_id"], position["role_id"])
            for position in positions.values()
        }
        membership_tuples = [
            (record["actor_ref"], record["circle_ref"], role)
            for record in prospective_records
            for role in record["roles"]
        ]
        if (
            len(membership_tuples) != len(set(membership_tuples))
            or set(membership_tuples) != position_tuples
        ):
            raise WorldVolumeError("prospective Rac no longer matches Omega positions")
        _validate_evidence_status(
            prospective_record, entries=authority.evidence_entries
        )
        source_refs = set(prospective_record["source_refs"])
        lineage_sources = {
            source_ref
            for evidence_id in prospective_record["evidence_status"]["source_lineage"]
            for source_ref in authority.evidence_entries[evidence_id]["source_refs"]
        }
        if not source_refs or not source_refs.issubset(lineage_sources):
            raise WorldVolumeError("prospective Rac source lineage is unresolved")
        local = (
            actor_ref == target_position["actor_id"]
            and circle_ref == target_position["circle_id"]
            and target_position["role_id"] in roles
        )
    else:
        source_circle = prospective_record["source_circle_ref"]
        target_circle = prospective_record["target_circle_ref"]
        if source_circle not in circles or target_circle not in circles:
            raise WorldVolumeError("prospective Rcc has an unknown circle endpoint")
        record_channel_ref = prospective_record["channel"]
        if record_channel_ref is not None:
            record_channel = channels.get(record_channel_ref)
            if record_channel is None:
                raise WorldVolumeError("prospective Rcc has an unknown channel")
            record_source = positions[record_channel["from_position_id"]]
            record_target = positions[record_channel["to_position_id"]]
            if (
                record_source["circle_id"] != source_circle
                or record_target["circle_id"] != target_circle
            ):
                raise WorldVolumeError(
                    "prospective Rcc channel does not connect its directed circles"
                )
        if not set(prospective_record["evidence_refs"]).issubset(
            authority.evidence_ids
        ) or not set(prospective_record["counterexample_refs"]).issubset(
            authority.evidence_ids
        ):
            raise WorldVolumeError("prospective Rcc evidence is unresolved")
        interface_locations = set(actors) | set(circles) | set(positions) | set(channels)
        if any(
            location not in interface_locations
            for location in prospective_record["shared_members_or_interfaces"]
        ):
            raise WorldVolumeError("prospective Rcc interface location is unknown")
        local = (
            source_circle == source_position["circle_id"]
            and target_circle == target_position["circle_id"]
            and (
                record_channel_ref is None
                or record_channel_ref == channel["channel_id"]
            )
        )
    if not local:
        raise WorldVolumeError("prospective relation is not local to its channel")


def _validate_evidence_status(
    record: Mapping[str, Any],
    *,
    entries: Mapping[str, Mapping[str, Any]],
) -> None:
    status = record["evidence_status"]
    lineage = tuple(status["source_lineage"])
    if not lineage or len(lineage) != len(set(lineage)):
        raise WorldVolumeError("evidence source_lineage must be nonempty and unique")
    unknown = set(lineage) - set(entries)
    if unknown:
        raise WorldVolumeError(
            f"evidence source_lineage does not resolve U3: {sorted(unknown)!r}"
        )
    source_identities = {entries[evidence_id]["identity"] for evidence_id in lineage}
    information_identity = status["information_identity"]
    if information_identity not in _IDENTITY_STRENGTH or any(
        identity not in _IDENTITY_STRENGTH for identity in source_identities
    ):
        raise WorldVolumeError("unknown evidence identity")
    weakest = min(_IDENTITY_STRENGTH[identity] for identity in source_identities)
    if _IDENTITY_STRENGTH[information_identity] > weakest:
        raise WorldVolumeError("evidence identity is promoted beyond its U3 lineage")
    if status["status"] == "observed" and (
        information_identity != "observed" or source_identities != {"observed"}
    ):
        raise WorldVolumeError("observed state requires only observed U3 lineage")


def _validate_evidence_authority(
    volume: Mapping[str, Any],
    evidence_ledger: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
) -> tuple[dict[str, Mapping[str, Any]], frozenset[str]]:
    evidence_snapshot = _snapshot_mapping(
        evidence_ledger, label="U3 evidence authority"
    )
    try:
        evidence = validate_phase_artifact(
            "ultra-evidence-ledger.schema.json",
            evidence_snapshot,
            expected_schema_id="crossframe.ultra.v82.evidence-ledger",
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_phase_id="U3",
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise WorldVolumeError(f"invalid U3 evidence authority: {error}") from error
    if _canonical_sha256(evidence) != expected_evidence_artifact_sha256:
        raise WorldVolumeError("U3 full artifact hash differs from external authority")
    if volume["evidence_artifact_sha256"] != expected_evidence_artifact_sha256:
        raise WorldVolumeError("world volume carries the wrong U3 artifact hash")
    if volume["evidence_content_sha256"] != evidence["content_sha256"]:
        raise WorldVolumeError("world volume carries the wrong U3 content hash")

    entries: dict[str, Mapping[str, Any]] = {}
    source_refs: set[str] = set()
    for entry in evidence["entries"]:
        try:
            validated = validate_evidence_entry(
                entry, evidence_cutoff=evidence["evidence_cutoff"]
            )
        except EvidenceValidationError as error:
            raise WorldVolumeError(f"invalid U3 evidence entry: {error}") from error
        evidence_id = str(validated["evidence_id"])
        if evidence_id in entries:
            raise WorldVolumeError("duplicate U3 evidence identifier")
        entries[evidence_id] = validated
        source_refs.update(str(value) for value in validated["source_refs"])
    return entries, frozenset(source_refs)


def _validate_relation_authority(
    volume: Mapping[str, Any],
    relation_refs: Mapping[str, Mapping[str, object]],
    *,
    expected_relation_refs_sha256: str,
) -> dict[str, Mapping[str, Any]]:
    registry = _snapshot_mapping(relation_refs, label="relation authority")
    if _canonical_sha256(registry) != expected_relation_refs_sha256:
        raise WorldVolumeError("relation authority differs from its external seal")

    promoted = [
        *(("Rac", record) for record in volume["memberships"]),
        *(("Rcc", record) for record in volume["circle_relations"]),
    ]
    if len(registry) != len(promoted):
        raise WorldVolumeError("relation authority does not give one-to-one coverage")

    matched_indices: set[int] = set()
    validated: dict[str, Mapping[str, Any]] = {}
    for opaque_ref, authority in registry.items():
        if type(opaque_ref) is not str or not opaque_ref:
            raise WorldVolumeError("relation authority keys must be opaque strings")
        if not isinstance(authority, Mapping) or set(authority) != {
            "relation_kind",
            "record_sha256",
            "record",
        }:
            raise WorldVolumeError("relation authority record has an invalid shape")
        kind = authority["relation_kind"]
        record = authority["record"]
        if kind not in {"Rac", "Rcc"} or not isinstance(record, Mapping):
            raise WorldVolumeError("relation authority kind or record is invalid")
        record_hash = _require_sha256(
            authority["record_sha256"], label="relation authority record hash"
        )
        if record_hash != _canonical_sha256(record):
            raise WorldVolumeError("relation authority record hash is stale")
        matches = [
            index
            for index, (promoted_kind, promoted_record) in enumerate(promoted)
            if promoted_kind == kind and promoted_record == record
        ]
        if len(matches) != 1 or matches[0] in matched_indices:
            raise WorldVolumeError("relation authority is not exact one-to-one coverage")
        matched_indices.add(matches[0])
        validated[opaque_ref] = authority
    if len(matched_indices) != len(promoted):
        raise WorldVolumeError("relation authority omits a promoted relation")
    return validated


def validate_unique_ids(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    groups = (
        (snapshot["actors"], "actor_id", "actor"),
        (snapshot["circles"], "circle_id", "circle"),
        (snapshot["positions"], "position_id", "position"),
        (snapshot["clocks"], "clock_id", "clock"),
        (snapshot["channels"], "channel_id", "channel"),
        (snapshot["events"], "event_id", "event"),
        (snapshot["local_distributions"], "distribution_id", "distribution"),
        (snapshot["unknowns"], "unknown_id", "unknown"),
        (snapshot["residuals"], "residual_id", "residual"),
    )
    stable_ids: list[str] = []
    for records, field, label in groups:
        identifiers = [record[field] for record in records]
        _require_unique(identifiers, label=label)
        stable_ids.extend(identifiers)
    material, meaning = _state_catalogs(snapshot)
    stable_ids.extend(material)
    stable_ids.extend(meaning)
    _require_unique(stable_ids, label="cross-volume stable")
    for location in _represented(snapshot):
        for state_field in ("M_state", "Psi_state"):
            names = [item["name"] for item in location[state_field]["variables"]]
            _require_unique(names, label=f"{state_field} variable")


def _validate_containment(volume: Mapping[str, Any], circle_ids: set[str]) -> None:
    parents: dict[str, set[str]] = {circle_id: set() for circle_id in circle_ids}
    edges: set[tuple[str, str]] = set()
    for edge in volume["containment_relations"]:
        child = edge["child_circle_id"]
        parent = edge["parent_circle_id"]
        if child not in circle_ids or parent not in circle_ids or child == parent:
            raise WorldVolumeError("containment edge has invalid endpoints")
        pair = (child, parent)
        if pair in edges:
            raise WorldVolumeError("duplicate containment edge")
        edges.add(pair)
        parents[child].add(parent)

    visiting: set[str] = set()
    memo: dict[str, set[str]] = {}

    def ancestors(circle_id: str) -> set[str]:
        if circle_id in memo:
            return set(memo[circle_id])
        if circle_id in visiting:
            raise WorldVolumeError("containment graph contains a cycle")
        visiting.add(circle_id)
        result: set[str] = set()
        for parent in parents[circle_id]:
            result.add(parent)
            result.update(ancestors(parent))
        visiting.remove(circle_id)
        memo[circle_id] = set(result)
        return result

    closure = volume["containment_closure"]
    closure_ids = [record["circle_id"] for record in closure]
    if len(closure_ids) != len(set(closure_ids)) or set(closure_ids) != circle_ids:
        raise WorldVolumeError("containment closure must cover each circle exactly once")
    for record in closure:
        declared = record["ancestor_circle_ids"]
        if len(declared) != len(set(declared)):
            raise WorldVolumeError("containment closure repeats an ancestor")
        if set(declared) != ancestors(record["circle_id"]):
            raise WorldVolumeError("containment closure differs from the edge closure")


def _validate_topology(
    volume: Mapping[str, Any], authority: _WorldAuthority
) -> None:
    actors = _by_id(volume["actors"], "actor_id", label="actor")
    circles = _by_id(volume["circles"], "circle_id", label="circle")
    positions = _by_id(volume["positions"], "position_id", label="position")
    channels = _by_id(volume["channels"], "channel_id", label="channel")
    clocks = _by_id(volume["clocks"], "clock_id", label="clock")
    actor_ids = set(actors)
    circle_ids = set(circles)
    position_ids = set(positions)

    if set(volume["object_boundary"]["object_ids"]) != actor_ids | circle_ids:
        raise WorldVolumeError("object boundary must exactly cover actors and circles")

    membership_tuples: list[tuple[str, str, str]] = []
    membership_records: set[bytes] = set()
    for membership in volume["memberships"]:
        actor_ref = membership["actor_ref"]
        circle_ref = membership["circle_ref"]
        if actor_ref not in actors or circle_ref not in circles:
            raise WorldVolumeError("Rac membership has an unknown actor or circle")
        if not membership["roles"] or len(membership["roles"]) != len(
            set(membership["roles"])
        ):
            raise WorldVolumeError("Rac roles must be nonempty and unique")
        for role in membership["roles"]:
            membership_tuples.append((actor_ref, circle_ref, role))
        encoded = canonical_json_bytes(membership)
        if encoded in membership_records:
            raise WorldVolumeError("duplicate Rac membership record")
        membership_records.add(encoded)
        _validate_evidence_status(membership, entries=authority.evidence_entries)
        source_refs = set(membership["source_refs"])
        lineage_sources = {
            source_ref
            for evidence_id in membership["evidence_status"]["source_lineage"]
            for source_ref in authority.evidence_entries[evidence_id]["source_refs"]
        }
        if not source_refs or not source_refs.issubset(lineage_sources):
            raise WorldVolumeError("Rac source refs do not resolve their U3 lineage")

    position_tuples: list[tuple[str, str, str]] = []
    for position in positions.values():
        if position["actor_id"] not in actors or position["circle_id"] not in circles:
            raise WorldVolumeError("position has an unknown actor or circle")
        position_tuples.append(
            (position["actor_id"], position["circle_id"], position["role_id"])
        )
    if len(membership_tuples) != len(set(membership_tuples)) or set(
        membership_tuples
    ) != set(position_tuples):
        raise WorldVolumeError("Rac actor/circle/role coverage differs from positions")

    _validate_containment(volume, circle_ids)

    circle_relation_records: set[bytes] = set()
    for relation in volume["circle_relations"]:
        if (
            relation["source_circle_ref"] not in circles
            or relation["target_circle_ref"] not in circles
        ):
            raise WorldVolumeError("Rcc relation has an unknown circle endpoint")
        if relation["direction"] != "directed":
            raise WorldVolumeError("Rcc relation must preserve directed identity")
        if relation["channel"] is not None:
            channel = channels.get(relation["channel"])
            if channel is None:
                raise WorldVolumeError("Rcc relation names an unknown channel")
            source_position = positions[channel["from_position_id"]]
            target_position = positions[channel["to_position_id"]]
            if (
                source_position["circle_id"] != relation["source_circle_ref"]
                or target_position["circle_id"] != relation["target_circle_ref"]
            ):
                raise WorldVolumeError(
                    "Rcc channel endpoints do not connect its directed circles"
                )
        if not set(relation["evidence_refs"]).issubset(
            authority.evidence_ids
        ) or not set(relation["counterexample_refs"]).issubset(
            authority.evidence_ids
        ):
            raise WorldVolumeError("Rcc evidence or counterexample does not resolve U3")
        interface_locations = actor_ids | circle_ids | position_ids | set(channels)
        if any(
            location not in interface_locations
            for location in relation["shared_members_or_interfaces"]
        ):
            raise WorldVolumeError("Rcc interface location is unknown")
        encoded = canonical_json_bytes(relation)
        if encoded in circle_relation_records:
            raise WorldVolumeError("duplicate Rcc relation record")
        circle_relation_records.add(encoded)

    valid_clock_scopes = actor_ids | circle_ids | position_ids | {volume["volume_id"]}
    for clock in clocks.values():
        if clock["scope_id"] not in valid_clock_scopes:
            raise WorldVolumeError("clock scope is unknown")
    if {clock["kind"] for clock in clocks.values()} != _CLOCK_KINDS:
        raise WorldVolumeError("Omega must expose all five clock kinds")

    for location in _represented(volume):
        if not location["identity_criteria"].strip():
            raise WorldVolumeError("represented location lacks K identity criteria")
        if set(location["scale_profile"]) != _AXES:
            raise WorldVolumeError("represented location lacks the nine scale axes")
        _validate_evidence_status(location, entries=authority.evidence_entries)
        for state_field in ("M_state", "Psi_state"):
            variables = location[state_field]["variables"]
            if not variables:
                raise WorldVolumeError("represented location lacks local state")
            for variable in variables:
                if variable["clock_id"] not in clocks:
                    raise WorldVolumeError("local state variable names an unknown clock")

    for channel in channels.values():
        if (
            channel["from_position_id"] not in positions
            or channel["to_position_id"] not in positions
        ):
            raise WorldVolumeError("channel has an unknown position endpoint")
        mapping = channel["identity_mapping"]
        if (
            mapping["source_k_ref"] != channel["from_position_id"]
            or mapping["target_k_ref"] != channel["to_position_id"]
            or mapping["preserves_identity"] is not True
        ):
            raise WorldVolumeError("channel K mapping does not preserve its endpoints")
        acl = channel["acl"]
        if any(value not in positions for value in acl["authorized_position_ids"]):
            raise WorldVolumeError("channel ACL names an unknown position")
        if channel["from_position_id"] not in acl["authorized_position_ids"]:
            raise WorldVolumeError("channel ACL excludes its real source position")
        for field in (channel["evidence_ids"], acl["authorization_evidence_ids"]):
            if not field or not set(field).issubset(authority.evidence_ids):
                raise WorldVolumeError("channel evidence does not resolve U3")


def _validate_distributions(
    volume: Mapping[str, Any], relation_refs: Mapping[str, Mapping[str, Any]]
) -> None:
    material, meaning = _state_catalogs(volume)
    channels = {record["channel_id"] for record in volume["channels"]}
    allowed = {
        "power": {
            key
            for key, value in relation_refs.items()
            if value["relation_kind"] == "Rac"
        },
        "exit": {
            key
            for key, value in relation_refs.items()
            if value["relation_kind"] == "Rac"
        },
        "constraint": channels,
        "burden": set(material),
        "spillover": set(meaning),
    }
    observed: set[str] = set()
    for distribution in volume["local_distributions"]:
        kind = distribution["kind"]
        observed.add(kind)
        if distribution["location_ref"] not in allowed[kind]:
            raise WorldVolumeError(f"{kind} distribution has the wrong location kind")
    if observed != _DISTRIBUTION_KINDS:
        raise WorldVolumeError("local distributions omit a required local effect kind")

    distributions = {
        record["distribution_id"]: record for record in volume["local_distributions"]
    }
    constraint_ids = {
        record["distribution_id"]
        for record in volume["local_distributions"]
        if record["kind"] == "constraint"
    }
    referenced_constraints: list[str] = []
    for channel in volume["channels"]:
        distribution_id = channel["constraint_distribution"]
        distribution = distributions.get(distribution_id)
        if (
            distribution is None
            or distribution["kind"] != "constraint"
            or distribution["location_ref"] != channel["channel_id"]
        ):
            raise WorldVolumeError(
                "channel constraint_distribution is not its exact local constraint"
            )
        referenced_constraints.append(distribution_id)
    if (
        len(referenced_constraints) != len(set(referenced_constraints))
        or set(referenced_constraints) != constraint_ids
    ):
        raise WorldVolumeError(
            "constraint distributions and channels are not one-to-one"
        )

    locations = {
        volume["volume_id"],
        *(record["actor_id"] for record in volume["actors"]),
        *(record["circle_id"] for record in volume["circles"]),
        *(record["position_id"] for record in volume["positions"]),
        *(record["clock_id"] for record in volume["clocks"]),
        *(record["channel_id"] for record in volume["channels"]),
        *(record["event_id"] for record in volume["events"]),
        *(record["distribution_id"] for record in volume["local_distributions"]),
        *material,
        *meaning,
        *relation_refs,
    }
    for record in (*volume["unknowns"], *volume["residuals"]):
        if record["location_ref"] not in locations:
            raise WorldVolumeError("unknown or residual location is unresolved")


def _is_positive_clock_delta(value: object) -> bool:
    if not isinstance(value, str):
        return False
    match = _CLOCK_DELTA_RE.fullmatch(value)
    if match is None:
        return False
    return any(match.group(name) for name in ("days", "hours", "minutes", "seconds"))


def _valid_event_channels(
    volume: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    evidence_ids: frozenset[str],
) -> dict[str, Mapping[str, Any]]:
    positions = {record["position_id"] for record in volume["positions"]}
    channels = _by_id(volume["channels"], "channel_id", label="channel")
    channel_ids = list(event["channel_ids"])
    condition_ids = [record["channel_id"] for record in event["channel_conditions"]]
    if len(channel_ids) != len(set(channel_ids)):
        raise WorldVolumeError("event channel_ids must be unique")
    if len(condition_ids) != len(set(condition_ids)) or set(condition_ids) != set(
        channel_ids
    ):
        raise WorldVolumeError("event channel conditions must exactly cover channel_ids")
    if any(channel_id not in channels for channel_id in channel_ids):
        raise WorldVolumeError("event names an unknown channel")
    if event["target_volume_id"] != volume["volume_id"]:
        raise WorldVolumeError("event targets the wrong Omega volume")
    targets = event["target_position_ids"]
    if len(targets) != len(set(targets)) or any(target not in positions for target in targets):
        raise WorldVolumeError("event has duplicate or unknown target positions")
    source = event["source_position_id"]
    if source is not None and source not in positions:
        raise WorldVolumeError("event source position is unknown")
    if event["origin_kind"] == "endogenous" and source is None:
        raise WorldVolumeError("endogenous event requires a source position")

    conditions = {record["channel_id"]: record for record in event["channel_conditions"]}
    candidates: dict[str, Mapping[str, Any]] = {}
    for channel_id in channel_ids:
        channel = channels[channel_id]
        condition = conditions[channel_id]
        condition_evidence = set(condition["evidence_ids"])
        channel_evidence = set(channel["evidence_ids"])
        acl = channel["acl"]
        acl_evidence = set(acl["authorization_evidence_ids"])
        if not condition_evidence.issubset(evidence_ids):
            raise WorldVolumeError("event condition evidence does not resolve U3")
        mapping = channel["identity_mapping"]
        static_valid = (
            channel["active"] is True
            and channel["to_position_id"] in targets
            and mapping["preserves_identity"] is True
            and mapping["source_k_ref"] == channel["from_position_id"]
            and mapping["target_k_ref"] == channel["to_position_id"]
            and channel["from_position_id"] in acl["authorized_position_ids"]
            and bool(channel_evidence)
            and bool(acl_evidence)
            and channel_evidence.issubset(evidence_ids)
            and acl_evidence.issubset(evidence_ids)
        )
        condition_valid = (
            condition["threshold_met"] is True
            and condition["identity_preserved"] is True
            and condition["acl_authorized"] is True
            and bool(condition_evidence)
            and condition_evidence.issubset(channel_evidence)
            and condition_evidence.issubset(acl_evidence)
        )
        if static_valid and condition_valid:
            candidates[channel_id] = channel

    if source is None:
        return {}
    reachable = {source}
    validated: dict[str, Mapping[str, Any]] = {}
    pending = list(channel_ids)
    changed = True
    while changed:
        changed = False
        for channel_id in pending:
            channel = candidates.get(channel_id)
            if channel is None or channel_id in validated:
                continue
            if channel["from_position_id"] in reachable:
                validated[channel_id] = channel
                reachable.add(channel["to_position_id"])
                changed = True
    return validated


def _evaluate_event(
    volume: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    authority: _WorldAuthority,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    positions = _by_id(volume["positions"], "position_id", label="position")
    clocks = _by_id(volume["clocks"], "clock_id", label="clock")
    valid_channels = _valid_event_channels(
        volume, event, evidence_ids=authority.evidence_ids
    )
    changed_positions: set[str] = set()
    state_changed_positions: set[str] = set()
    relation_changed_positions: set[str] = set()
    variable_clock_ids: set[str] = set()

    for update_field, state_field in (("M_updates", "M_state"), ("Psi_updates", "Psi_state")):
        seen_positions: set[str] = set()
        for update in event[update_field]:
            position_id = update["position_id"]
            channel_id = update["via_channel_id"]
            channel = valid_channels.get(channel_id)
            position = positions.get(position_id)
            if (
                position is None
                or channel is None
                or channel["to_position_id"] != position_id
                or position_id in seen_positions
            ):
                raise WorldVolumeError(f"{update_field} is not local to one valid channel")
            seen_positions.add(position_id)
            state = position[state_field]
            if update["state_id"] != state["state_id"]:
                raise WorldVolumeError(f"{update_field} names the wrong local state")
            variables = {record["name"]: record for record in state["variables"]}
            changed_names: set[str] = set()
            for change in update["variable_changes"]:
                name = change["name"]
                variable = variables.get(name)
                if variable is None or name in changed_names:
                    raise WorldVolumeError(f"{update_field} names an unknown or repeated variable")
                changed_names.add(name)
                if (
                    change["source_value"] != variable["value"]
                    or change["unit"] != variable["unit"]
                    or change["clock_id"] != variable["clock_id"]
                    or change["target_value"] == change["source_value"]
                ):
                    raise WorldVolumeError(f"{update_field} does not match current local state")
                variable_clock_ids.add(change["clock_id"])
            changed_positions.add(position_id)
            state_changed_positions.add(position_id)

    changed_relations: list[str] = []
    for update in event["relation_updates"]:
        relation_ref = update["relation_ref"]
        if relation_ref in changed_relations:
            raise WorldVolumeError("event repeats a relation update")
        relation = authority.relation_refs.get(relation_ref)
        channel = valid_channels.get(update["via_channel_id"])
        if relation is None or channel is None:
            raise WorldVolumeError("relation update lacks frozen authority or a valid channel")
        if update["relation_kind"] != relation["relation_kind"]:
            raise WorldVolumeError("relation update kind differs from frozen authority")
        record = relation["record"]
        field = update["field_name"]
        if (
            field not in record
            or update["source_value"] != record[field]
            or update["target_value"] == update["source_value"]
        ):
            raise WorldVolumeError("relation update does not match the current relation")
        prospective_record = copy.deepcopy(dict(record))
        prospective_record[field] = copy.deepcopy(update["target_value"])
        _validate_prospective_relation(
            volume,
            relation_kind=relation["relation_kind"],
            current_record=record,
            prospective_record=prospective_record,
            channel=channel,
            authority=authority,
        )
        changed_relations.append(relation_ref)
        changed_positions.add(channel["to_position_id"])
        relation_changed_positions.add(channel["to_position_id"])

    advanced_clocks: list[str] = []
    local_scopes = set(changed_positions)
    for position_id in changed_positions:
        local_scopes.add(positions[position_id]["actor_id"])
        local_scopes.add(positions[position_id]["circle_id"])
    relation_only_positions = relation_changed_positions - state_changed_positions

    def position_scopes(position_id: str) -> set[str]:
        position = positions[position_id]
        return {position_id, position["actor_id"], position["circle_id"]}

    for delta in event["clock_deltas"]:
        clock_id = delta["clock_id"]
        clock = clocks.get(clock_id)
        relation_local = clock is not None and any(
            clock["scope_id"] in position_scopes(position_id)
            for position_id in relation_only_positions
        )
        if (
            clock is None
            or clock_id in advanced_clocks
            or not _is_positive_clock_delta(delta["delta"])
            or clock["scope_id"] not in local_scopes
            or (clock_id not in variable_clock_ids and not relation_local)
        ):
            raise WorldVolumeError("clock delta is stale, duplicate, or non-local")
        advanced_clocks.append(clock_id)
    if not variable_clock_ids.issubset(advanced_clocks):
        raise WorldVolumeError("changed state variables lack exact clock delta coverage")
    for position_id in relation_only_positions:
        if not any(
            clocks[clock_id]["scope_id"] in position_scopes(position_id)
            for clock_id in advanced_clocks
        ):
            raise WorldVolumeError("relation-only changed position lacks a local clock delta")

    position_order = [record["position_id"] for record in volume["positions"]]
    ordered_changed = tuple(
        position_id for position_id in position_order if position_id in changed_positions
    )
    return ordered_changed, tuple(changed_relations), tuple(advanced_clocks)


def validate_relation_endpoints(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    actors = {record["actor_id"] for record in snapshot["actors"]}
    circles = {record["circle_id"] for record in snapshot["circles"]}
    positions = {record["position_id"] for record in snapshot["positions"]}
    for position in snapshot["positions"]:
        if position["actor_id"] not in actors or position["circle_id"] not in circles:
            raise WorldVolumeError("position has an unknown endpoint")
    for channel in snapshot["channels"]:
        if channel["from_position_id"] not in positions or channel["to_position_id"] not in positions:
            raise WorldVolumeError("channel has an unknown endpoint")


def validate_membership_bases(volume: Mapping[str, object]) -> None:
    for membership in dict(volume)["memberships"]:
        if not membership["membership_basis"].strip():
            raise WorldVolumeError("Rac membership basis must be explicit")


def validate_local_state_coverage(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    _state_catalogs(snapshot)
    for location in _represented(snapshot):
        if not location["M_state"]["variables"] or not location["Psi_state"]["variables"]:
            raise WorldVolumeError("represented location lacks local M or Psi state")


def validate_scale_profiles(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    if any(set(location["scale_profile"]) != _AXES for location in _represented(snapshot)):
        raise WorldVolumeError("represented location lacks the nine scale axes")
    if {clock["kind"] for clock in snapshot["clocks"]} != _CLOCK_KINDS:
        raise WorldVolumeError("Omega lacks an asynchronous clock kind")


def validate_world_volume(
    volume: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
    relation_refs: Mapping[str, Mapping[str, object]],
    expected_relation_refs_sha256: str,
) -> None:
    (
        expected_run_id,
        expected_version_binding,
        expected_evidence_artifact_sha256,
        expected_relation_refs_sha256,
    ) = _validated_public_authorities(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
    )
    snapshot = _snapshot_mapping(volume, label="world volume")
    try:
        snapshot = validate_phase_artifact(
            "ultra-world-volume.schema.json",
            snapshot,
            expected_schema_id="crossframe.ultra.v82.world-volume",
            expected_run_id=expected_run_id,
            expected_version_binding=expected_version_binding,
            expected_phase_id="U4",
        )
    except (ValidationError, UltraSchemaError, TypeError, ValueError) as error:
        raise WorldVolumeError(f"invalid U4 world volume: {error}") from error

    evidence_entries, source_refs = _validate_evidence_authority(
        snapshot,
        evidence_ledger,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
    )
    validated_relations = _validate_relation_authority(
        snapshot,
        relation_refs,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
    )
    authority = _WorldAuthority(
        evidence_ids=frozenset(evidence_entries),
        evidence_entries=evidence_entries,
        source_refs=source_refs,
        relation_refs=validated_relations,
    )
    validate_unique_ids(snapshot)
    validate_membership_bases(snapshot)
    _validate_topology(snapshot, authority)
    _validate_distributions(snapshot, validated_relations)
    for event in snapshot["events"]:
        _evaluate_event(snapshot, event, authority=authority)


def apply_event(
    volume: Mapping[str, object],
    event: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
    expected_run_id: str,
    expected_version_binding: Mapping[str, object],
    expected_evidence_artifact_sha256: str,
    relation_refs: Mapping[str, Mapping[str, object]],
    expected_relation_refs_sha256: str,
) -> StateDiff:
    (
        expected_run_id,
        expected_version_binding,
        expected_evidence_artifact_sha256,
        expected_relation_refs_sha256,
    ) = _validated_public_authorities(
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
    )
    snapshot = _snapshot_mapping(volume, label="world volume")
    event_snapshot = _snapshot_mapping(event, label="event")
    validate_world_volume(
        snapshot,
        evidence_ledger=evidence_ledger,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
        relation_refs=relation_refs,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
    )
    evidence_entries, source_refs = _validate_evidence_authority(
        snapshot,
        evidence_ledger,
        expected_run_id=expected_run_id,
        expected_version_binding=expected_version_binding,
        expected_evidence_artifact_sha256=expected_evidence_artifact_sha256,
    )
    validated_relations = _validate_relation_authority(
        snapshot,
        relation_refs,
        expected_relation_refs_sha256=expected_relation_refs_sha256,
    )
    authority = _WorldAuthority(
        evidence_ids=frozenset(evidence_entries),
        evidence_entries=evidence_entries,
        source_refs=source_refs,
        relation_refs=validated_relations,
    )

    event_id = event_snapshot.get("event_id")
    matches = [
        stored
        for stored in snapshot["events"]
        if stored["event_id"] == event_id and stored == event_snapshot
    ]
    if len(matches) != 1:
        raise WorldVolumeError("event must deep-equal one frozen model-authored event")
    changed_positions, changed_relations, advanced_clocks = _evaluate_event(
        snapshot, event_snapshot, authority=authority
    )
    changed_set = set(changed_positions)
    unchanged = tuple(
        record["position_id"]
        for record in snapshot["positions"]
        if record["position_id"] not in changed_set
    )
    return StateDiff(
        source_volume_sha256=_canonical_sha256(snapshot),
        event_id=str(event_id),
        changed_positions=changed_positions,
        unchanged_positions=unchanged,
        changed_relations=changed_relations,
        advanced_clocks=advanced_clocks,
        inherited_unknown_ids=tuple(record["unknown_id"] for record in snapshot["unknowns"]),
        inherited_residual_ids=tuple(record["residual_id"] for record in snapshot["residuals"]),
    )


__all__ = (
    "StateDiff",
    "WorldVolumeError",
    "apply_event",
    "validate_local_state_coverage",
    "validate_membership_bases",
    "validate_relation_endpoints",
    "validate_scale_profiles",
    "validate_unique_ids",
    "validate_world_volume",
)
