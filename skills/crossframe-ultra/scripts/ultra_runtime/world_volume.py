from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
import re
from typing import Any

from jsonschema import ValidationError

from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import validate_instance
from .evidence import EvidenceValidationError, validate_evidence_entry


_CLOCK_KINDS = frozenset(
    {
        "immediate",
        "interaction",
        "organizational",
        "institutional",
        "long-term",
    }
)
_DISTRIBUTION_KINDS = frozenset(
    {"power", "constraint", "exit", "burden", "spillover"}
)
_EVIDENCE_IDENTITY_STRENGTH = {
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
    r"^P"
    r"(?:(?P<days>[1-9]\d{0,8})D)?"
    r"(?:T"
    r"(?:(?P<hours>[1-9]|1\d|2[0-3])H)?"
    r"(?:(?P<minutes>[1-9]|[1-5]\d)M)?"
    r"(?:(?P<seconds>[1-9]|[1-5]\d)S)?"
    r")?$"
)


class WorldVolumeError(ValueError):
    """Raised when a model-authored Omega artifact violates local topology."""


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


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise WorldVolumeError(f"{label} must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(value))
    except Exception as error:
        raise WorldVolumeError(f"{label} cannot be snapshotted: {error}") from error
    return snapshot


def _require_unique(values: Sequence[str], *, label: str) -> None:
    if len(values) != len(set(values)):
        raise WorldVolumeError(f"duplicate {label} identifier")


def _records_by_id(
    records: Sequence[Mapping[str, Any]],
    field: str,
    *,
    label: str,
) -> dict[str, Mapping[str, Any]]:
    identifiers = [record[field] for record in records]
    _require_unique(identifiers, label=label)
    return dict(zip(identifiers, records, strict=True))


def _represented_records(volume: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(volume["actors"]) + tuple(volume["circles"]) + tuple(
        volume["positions"]
    )


def _local_state_ids(volume: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    material_ids = {
        record["M_state"]["state_id"] for record in _represented_records(volume)
    }
    meaning_ids = {
        record["Psi_state"]["state_id"] for record in _represented_records(volume)
    }
    return material_ids, meaning_ids


def validate_unique_ids(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    identity_groups = (
        (snapshot["actors"], "actor_id", "actor"),
        (snapshot["circles"], "circle_id", "circle"),
        (snapshot["positions"], "position_id", "position"),
        (snapshot["memberships"], "membership_id", "membership"),
        (snapshot["circle_relations"], "relation_id", "circle relation"),
        (snapshot["clocks"], "clock_id", "clock"),
        (snapshot["channels"], "channel_id", "channel"),
        (snapshot["events"], "event_id", "event"),
        (
            snapshot["local_distributions"],
            "distribution_id",
            "local distribution",
        ),
        (snapshot["unknowns"], "unknown_id", "unknown"),
        (snapshot["residuals"], "residual_id", "residual"),
    )
    stable_ids: list[str] = []
    for records, field, label in identity_groups:
        identifiers = [record[field] for record in records]
        _require_unique(identifiers, label=label)
        stable_ids.extend(identifiers)

    material_ids, meaning_ids = _local_state_ids(snapshot)
    expected_state_count = len(_represented_records(snapshot))
    if len(material_ids) != expected_state_count:
        raise WorldVolumeError("duplicate local M state identifier")
    if len(meaning_ids) != expected_state_count:
        raise WorldVolumeError("duplicate local Psi state identifier")
    stable_ids.extend(sorted(material_ids))
    stable_ids.extend(sorted(meaning_ids))
    _require_unique(stable_ids, label="cross-volume stable")

    for record in _represented_records(snapshot):
        for state_field in ("M_state", "Psi_state"):
            names = [
                variable["name"] for variable in record[state_field]["variables"]
            ]
            _require_unique(names, label=f"{state_field} variable")


def _all_location_ids(volume: Mapping[str, Any]) -> set[str]:
    material_ids, meaning_ids = _local_state_ids(volume)
    return {
        volume["volume_id"],
        *volume["object_boundary"]["object_ids"],
        *(record["actor_id"] for record in volume["actors"]),
        *(record["circle_id"] for record in volume["circles"]),
        *(record["position_id"] for record in volume["positions"]),
        *(record["membership_id"] for record in volume["memberships"]),
        *(record["relation_id"] for record in volume["circle_relations"]),
        *(record["clock_id"] for record in volume["clocks"]),
        *(record["channel_id"] for record in volume["channels"]),
        *(record["event_id"] for record in volume["events"]),
        *material_ids,
        *meaning_ids,
    }


def validate_relation_endpoints(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    actors = {record["actor_id"] for record in snapshot["actors"]}
    circles = {record["circle_id"] for record in snapshot["circles"]}
    positions = {
        record["position_id"]: record for record in snapshot["positions"]
    }
    memberships = {
        (
            record["actor_id"],
            record["circle_id"],
            record["role_id"],
        ): record
        for record in snapshot["memberships"]
    }
    if len(memberships) != len(snapshot["memberships"]):
        raise WorldVolumeError("duplicate actor-circle-role membership mapping")

    boundary_ids = set(snapshot["object_boundary"]["object_ids"])
    if boundary_ids != actors | circles:
        raise WorldVolumeError(
            "object boundary must exactly enumerate represented actors and circles"
        )

    for position in positions.values():
        actor_id = position["actor_id"]
        circle_id = position["circle_id"]
        role_id = position["role_id"]
        if actor_id not in actors or circle_id not in circles:
            raise WorldVolumeError("position references an unknown actor or circle")
        if (actor_id, circle_id, role_id) not in memberships:
            raise WorldVolumeError("position lacks its exact Rac membership mapping")

    position_keys = {
        (record["actor_id"], record["circle_id"], record["role_id"])
        for record in positions.values()
    }
    if set(memberships) != position_keys:
        raise WorldVolumeError(
            "every Rac membership must have one exact represented position"
        )

    containment_edges: set[tuple[str, str, str]] = set()
    for relation in snapshot["containment_relations"]:
        child = relation["child_circle_id"]
        parent = relation["parent_circle_id"]
        if child not in circles or parent not in circles or child == parent:
            raise WorldVolumeError("containment relation has invalid circle endpoints")
        edge = (child, parent, relation["basis"])
        if edge in containment_edges:
            raise WorldVolumeError("duplicate local containment relation")
        containment_edges.add(edge)

    for relation in snapshot["circle_relations"]:
        if (
            relation["from_circle_id"] not in circles
            or relation["to_circle_id"] not in circles
        ):
            raise WorldVolumeError("circle relation has an unknown endpoint")

    channels = _records_by_id(
        snapshot["channels"], "channel_id", label="channel"
    )
    for channel in channels.values():
        if (
            channel["from_position_id"] not in positions
            or channel["to_position_id"] not in positions
        ):
            raise WorldVolumeError("channel has an unknown position endpoint")

    for event in snapshot["events"]:
        if event["source_position_id"] not in positions:
            raise WorldVolumeError("event source position is unknown")
        if any(target not in positions for target in event["target_position_ids"]):
            raise WorldVolumeError("event target position is unknown")
        if any(channel_id not in channels for channel_id in event["channel_ids"]):
            raise WorldVolumeError("event channel is unknown")

    locations = _all_location_ids(snapshot)
    for record in (*snapshot["unknowns"], *snapshot["residuals"]):
        if record["location_ref"] not in locations:
            raise WorldVolumeError("unknown or residual has an unknown location")

    clock_scopes = actors | circles | set(positions)
    if any(clock["scope_id"] not in clock_scopes for clock in snapshot["clocks"]):
        raise WorldVolumeError("clock scope must be an actor, circle, or position")


def validate_membership_bases(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    containment_bases = {
        "membership",
        "role",
        "contract",
        "resource-accounting",
        "jurisdiction",
        "space",
    }
    for circle in snapshot["circles"]:
        if not circle["membership_basis"].strip():
            raise WorldVolumeError("circle membership basis must be explicit")
    for membership in snapshot["memberships"]:
        if not membership["basis"].strip():
            raise WorldVolumeError("Rac membership basis must be explicit")
    for containment in snapshot["containment_relations"]:
        if containment["basis"] not in containment_bases:
            raise WorldVolumeError("containment basis must use the closed basis set")
    for relation in snapshot["circle_relations"]:
        if relation["direction"] != "directed":
            raise WorldVolumeError("circle relations must be one directed edge")


def validate_local_state_coverage(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    forbidden = {"power", "constraint", "exit", "burden", "spillover"}
    for record in _represented_records(snapshot):
        if not record["identity_criteria"].strip():
            raise WorldVolumeError("every represented location requires K criteria")
        evidence_status = record["evidence_status"]
        if forbidden.intersection(evidence_status):
            raise WorldVolumeError("W cannot carry local distribution state")
        for state_field in ("M_state", "Psi_state"):
            variables = record[state_field]["variables"]
            if not variables:
                raise WorldVolumeError(f"every represented location requires {state_field}")

    material_ids, meaning_ids = _local_state_ids(snapshot)
    membership_ids = {
        record["membership_id"] for record in snapshot["memberships"]
    }
    channel_ids = {record["channel_id"] for record in snapshot["channels"]}
    allowed_locations = {
        "power": membership_ids,
        "exit": membership_ids,
        "constraint": channel_ids,
        "burden": material_ids,
        "spillover": meaning_ids,
    }
    observed_kinds: set[str] = set()
    for distribution in snapshot["local_distributions"]:
        kind = distribution["kind"]
        observed_kinds.add(kind)
        if distribution["location_ref"] not in allowed_locations[kind]:
            raise WorldVolumeError(
                f"local distribution {kind!r} has an invalid location"
            )
    if observed_kinds != _DISTRIBUTION_KINDS:
        raise WorldVolumeError(
            "local distributions must explicitly cover power, constraint, exit, "
            "burden, and spillover"
        )


def validate_scale_profiles(volume: Mapping[str, object]) -> None:
    snapshot = dict(volume)
    axes = {
        "spatial",
        "temporal",
        "organizational",
        "institutional",
        "material",
        "informational",
        "relational",
        "power",
        "risk",
    }
    for record in _represented_records(snapshot):
        if set(record["scale_profile"]) != axes:
            raise WorldVolumeError("every represented location requires nine SP axes")
    if {clock["kind"] for clock in snapshot["clocks"]} != _CLOCK_KINDS:
        raise WorldVolumeError("Omega requires all five asynchronous clock kinds")


def _validate_evidence_authority(
    volume: Mapping[str, Any],
    evidence_ledger: Mapping[str, object],
) -> None:
    evidence_snapshot = _snapshot_mapping(
        evidence_ledger,
        label="preceding U3 evidence ledger",
    )
    try:
        validate_instance("ultra-evidence-ledger.schema.json", evidence_snapshot)
    except (ValidationError, TypeError, ValueError) as error:
        message = getattr(error, "message", str(error))
        raise WorldVolumeError(
            f"preceding U3 evidence ledger is invalid: {message}"
        ) from error
    if evidence_snapshot["phase_id"] != "U3":
        raise WorldVolumeError("world volume must bind a preceding U3 evidence ledger")
    if evidence_snapshot["run_id"] != volume["run_id"]:
        raise WorldVolumeError("world volume and U3 evidence ledger must share a run")
    if evidence_snapshot["version_binding"] != volume["version_binding"]:
        raise WorldVolumeError(
            "world volume and U3 evidence ledger must share version authority"
        )
    validated_entries: dict[str, Mapping[str, object]] = {}
    for entry in evidence_snapshot["entries"]:
        try:
            validated_entry = validate_evidence_entry(
                entry,
                evidence_cutoff=evidence_snapshot["evidence_cutoff"],
            )
        except EvidenceValidationError as error:
            raise WorldVolumeError(
                f"preceding U3 evidence entry is invalid: {error}"
            ) from error
        validated_entries[str(validated_entry["evidence_id"])] = validated_entry

    for record in _represented_records(volume):
        evidence_status = record["evidence_status"]
        lineage = evidence_status["source_lineage"]
        unknown = set(lineage) - set(validated_entries)
        if unknown:
            raise WorldVolumeError(
                "W source_lineage must bind frozen U3 evidence authority: "
                f"{sorted(unknown)!r}"
            )
        source_identities = {
            str(validated_entries[evidence_id]["identity"])
            for evidence_id in lineage
        }
        information_identity = evidence_status["information_identity"]
        source_strength = min(
            _EVIDENCE_IDENTITY_STRENGTH[identity]
            for identity in source_identities
        )
        if _EVIDENCE_IDENTITY_STRENGTH[information_identity] > source_strength:
            raise WorldVolumeError(
                "W information_identity cannot be stronger than its U3 lineage"
            )
        if evidence_status["status"] == "observed" and (
            information_identity != "observed" or source_identities != {"observed"}
        ):
            raise WorldVolumeError(
                "W observed status requires only observed U3 evidence lineage"
            )


def validate_world_volume(
    volume: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
) -> None:
    snapshot = _snapshot_mapping(volume, label="world volume")
    try:
        validate_instance("ultra-world-volume.schema.json", snapshot)
    except (ValidationError, TypeError, ValueError) as error:
        message = getattr(error, "message", str(error))
        raise WorldVolumeError(f"world volume schema validation failed: {message}") from error
    validate_unique_ids(snapshot)
    validate_relation_endpoints(snapshot)
    validate_membership_bases(snapshot)
    validate_local_state_coverage(snapshot)
    validate_scale_profiles(snapshot)
    _validate_evidence_authority(snapshot, evidence_ledger)
    for event in snapshot["events"]:
        changed_positions = _reachable_positions(snapshot, event)
        _validate_event_declarations(snapshot, event, changed_positions)


def _reachable_positions(
    volume: Mapping[str, Any],
    event: Mapping[str, Any],
) -> tuple[str, ...]:
    channels_by_id = {
        channel["channel_id"]: channel for channel in volume["channels"]
    }
    selected: list[Mapping[str, Any]] = []
    for channel_id in event["channel_ids"]:
        channel = channels_by_id.get(channel_id)
        if channel is None:
            raise WorldVolumeError(f"event references unknown channel {channel_id!r}")
        if channel["active"] is not True:
            raise WorldVolumeError(f"event channel {channel_id!r} is inactive")
        selected.append(channel)

    adjacency: dict[str, list[str]] = {}
    for channel in selected:
        adjacency.setdefault(channel["from_position_id"], []).append(
            channel["to_position_id"]
        )

    source = event["source_position_id"]
    queue = deque([source])
    visited = {source}
    while queue:
        current = queue.popleft()
        for target in adjacency.get(current, ()):  # directed Q only
            if target not in visited:
                visited.add(target)
                queue.append(target)

    if any(
        channel["from_position_id"] not in visited
        or channel["to_position_id"] not in visited
        for channel in selected
    ):
        raise WorldVolumeError(
            "every declared event channel must be connected to the event source"
        )

    position_order = [record["position_id"] for record in volume["positions"]]
    reachable = tuple(
        position_id
        for position_id in position_order
        if position_id != source and position_id in visited
    )
    declared_targets = tuple(event["target_position_ids"])
    if set(reachable) != set(declared_targets):
        raise WorldVolumeError(
            "event targets must exactly equal positions reachable through its real channels"
        )
    return tuple(
        position_id for position_id in position_order if position_id in declared_targets
    )


def _is_positive_clock_delta(value: object) -> bool:
    if not isinstance(value, str):
        return False
    matched = _CLOCK_DELTA_RE.fullmatch(value)
    if matched is None:
        return False
    if not any(matched.group(name) for name in ("days", "hours", "minutes", "seconds")):
        return False
    if "T" in value and not any(
        matched.group(name) for name in ("hours", "minutes", "seconds")
    ):
        return False
    return True


def _validate_event_declarations(
    volume: Mapping[str, Any],
    event: Mapping[str, Any],
    changed_positions: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    required_event_fields = {
        "event_id",
        "source_position_id",
        "target_position_ids",
        "channel_ids",
        "M_updates",
        "Psi_updates",
        "relation_updates",
        "clock_deltas",
    }
    if set(event) != required_event_fields:
        raise WorldVolumeError(
            "event must declare every local state, relation, and clock update"
        )
    positions = {
        record["position_id"]: record for record in volume["positions"]
    }
    declared_channels = {
        channel["channel_id"]: channel for channel in volume["channels"]
    }
    selected_channel_ids = set(event["channel_ids"])
    changed_set = set(changed_positions)

    def validate_state_updates(field: str, state_field: str) -> None:
        updates = event[field]
        update_positions = [update["position_id"] for update in updates]
        if len(update_positions) != len(set(update_positions)):
            raise WorldVolumeError(f"event {field} contains duplicate position updates")
        if set(update_positions) != changed_set:
            raise WorldVolumeError(
                f"event {field} must declare one local update for every target"
            )
        for update in updates:
            position_id = update["position_id"]
            position = positions.get(position_id)
            if position is None or update["state_id"] != position[state_field]["state_id"]:
                raise WorldVolumeError(
                    f"event {field} does not bind the declared local {state_field} state"
                )
            declared_variables = {
                variable["name"] for variable in position[state_field]["variables"]
            }
            if not set(update["changed_variable_names"]).issubset(declared_variables):
                raise WorldVolumeError(
                    f"event {field} names an unknown local state variable"
                )
            channel_id = update["via_channel_id"]
            channel = declared_channels.get(channel_id)
            if (
                channel_id not in selected_channel_ids
                or channel is None
                or channel["to_position_id"] != position_id
            ):
                raise WorldVolumeError(
                    f"event {field} update lacks its reachable declared channel"
                )

    validate_state_updates("M_updates", "M_state")
    validate_state_updates("Psi_updates", "Psi_state")

    changed_relation_ids: list[str] = []
    memberships = {
        record["membership_id"]: record for record in volume["memberships"]
    }
    relations = {
        record["relation_id"]: record for record in volume["circle_relations"]
    }
    for update in event["relation_updates"]:
        channel_id = update["via_channel_id"]
        channel = declared_channels.get(channel_id)
        if channel_id not in selected_channel_ids or channel is None:
            raise WorldVolumeError("event relation update lacks a declared channel")
        target = positions[channel["to_position_id"]]
        relation_id = update["relation_id"]
        if update["relation_kind"] == "Rac":
            membership = memberships.get(relation_id)
            if membership is None:
                raise WorldVolumeError("event Rac update names an unknown membership")
            if (
                membership["actor_id"] != target["actor_id"]
                or membership["circle_id"] != target["circle_id"]
                or membership["role_id"] != target["role_id"]
            ):
                raise WorldVolumeError("event Rac update is not local to its channel target")
        else:
            relation = relations.get(relation_id)
            if relation is None:
                raise WorldVolumeError("event Rcc update names an unknown circle relation")
            if target["circle_id"] not in {
                relation["from_circle_id"],
                relation["to_circle_id"],
            }:
                raise WorldVolumeError("event Rcc update is not local to its channel target")
        changed_relation_ids.append(relation_id)
    if len(changed_relation_ids) != len(set(changed_relation_ids)):
        raise WorldVolumeError("event relation updates must be unique")

    target_actor_ids = {positions[position_id]["actor_id"] for position_id in changed_set}
    target_circle_ids = {positions[position_id]["circle_id"] for position_id in changed_set}
    permitted_clock_scopes = changed_set | target_actor_ids | target_circle_ids
    clocks = {clock["clock_id"]: clock for clock in volume["clocks"]}
    advanced_clocks: list[str] = []
    for clock_delta in event["clock_deltas"]:
        clock_id = clock_delta["clock_id"]
        clock = clocks.get(clock_id)
        if clock is None:
            raise WorldVolumeError("event clock delta names an unknown clock")
        if not _is_positive_clock_delta(clock_delta["delta"]):
            raise WorldVolumeError(
                "event clock delta must be a positive ISO-8601 duration"
            )
        if clock["scope_id"] not in permitted_clock_scopes:
            raise WorldVolumeError("event clock delta is outside the local update scope")
        advanced_clocks.append(clock_id)
    if len(advanced_clocks) != len(set(advanced_clocks)):
        raise WorldVolumeError("event clock deltas must be unique")
    return tuple(changed_relation_ids), tuple(advanced_clocks)


def apply_event(
    volume: Mapping[str, object],
    event: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
) -> StateDiff:
    snapshot = _snapshot_mapping(volume, label="world volume")
    validate_world_volume(snapshot, evidence_ledger=evidence_ledger)
    event_snapshot = _snapshot_mapping(event, label="event")

    stored_events = {
        record["event_id"]: record for record in snapshot["events"]
    }
    event_id = event_snapshot.get("event_id")
    if not isinstance(event_id, str) or stored_events.get(event_id) != event_snapshot:
        raise WorldVolumeError("event must match one frozen model-authored event")

    changed_positions = _reachable_positions(snapshot, event_snapshot)
    changed_relations, advanced_clocks = _validate_event_declarations(
        snapshot,
        event_snapshot,
        changed_positions,
    )
    changed_set = set(changed_positions)
    unchanged_positions = tuple(
        record["position_id"]
        for record in snapshot["positions"]
        if record["position_id"] not in changed_set
    )
    return StateDiff(
        source_volume_sha256=sha256_bytes(canonical_json_bytes(snapshot)),
        event_id=event_id,
        changed_positions=changed_positions,
        unchanged_positions=unchanged_positions,
        changed_relations=changed_relations,
        advanced_clocks=advanced_clocks,
        inherited_unknown_ids=tuple(
            record["unknown_id"] for record in snapshot["unknowns"]
        ),
        inherited_residual_ids=tuple(
            record["residual_id"] for record in snapshot["residuals"]
        ),
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
