from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
import re
from typing import Any

from jsonschema import ValidationError

from .jsonio import canonical_json_bytes, sha256_bytes
from .schemas import validate_instance
from .world_volume import WorldVolumeError, validate_world_volume


_TRANSFORM_KINDS = frozenset(
    {"scale", "circle-relation", "representation-translation"}
)
_EFFECT_KINDS = frozenset({"gain", "damage", "exit-cost", "spillover"})
_ARTICLE_UNIT_ID_RE = re.compile(r"ARTICLE-UNIT-[A-Za-z0-9._:-]+\Z")


class TransformationError(ValueError):
    """Raised when a transformation ledger hides identity or local effects."""


class ChannelContinuityError(TransformationError):
    """Raised when a cascade hop lacks a revalidated real channel."""


def _snapshot_mapping(value: Mapping[str, object], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TransformationError(f"{label} must be a mapping")
    try:
        return copy.deepcopy(dict(value))
    except Exception as error:
        raise TransformationError(f"{label} cannot be snapshotted: {error}") from error


def _volume_bindings(
    source_volume: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
) -> tuple[
    dict[str, Any],
    frozenset[str],
    frozenset[str],
    frozenset[str],
    frozenset[str],
    frozenset[str],
    frozenset[tuple[str, str]],
    dict[str, str],
]:
    if not isinstance(source_volume, Mapping):
        raise TransformationError("source_volume must be a mapping")
    try:
        snapshot = copy.deepcopy(dict(source_volume))
        validate_world_volume(snapshot, evidence_ledger=evidence_ledger)
    except (WorldVolumeError, TypeError, ValueError) as error:
        raise TransformationError(f"source volume is invalid: {error}") from error

    represented = (
        tuple(snapshot["actors"])
        + tuple(snapshot["circles"])
        + tuple(snapshot["positions"])
    )
    locations = {
        *(record["actor_id"] for record in snapshot["actors"]),
        *(record["circle_id"] for record in snapshot["circles"]),
        *(record["position_id"] for record in snapshot["positions"]),
        *(record["membership_id"] for record in snapshot["memberships"]),
        *(record["relation_id"] for record in snapshot["circle_relations"]),
        *(record["channel_id"] for record in snapshot["channels"]),
        *(record["M_state"]["state_id"] for record in represented),
        *(record["Psi_state"]["state_id"] for record in represented),
    }
    residual_ids = {
        record["residual_id"] for record in snapshot["residuals"]
    }
    represented_ids = {
        *(record["actor_id"] for record in snapshot["actors"]),
        *(record["circle_id"] for record in snapshot["circles"]),
        *(record["position_id"] for record in snapshot["positions"]),
    }
    relation_ids = {
        record["relation_id"] for record in snapshot["circle_relations"]
    }
    scale_qualifiers = {
        *(key for record in represented for key in record["scale_profile"]),
        *(
            value
            for record in represented
            for value in record["scale_profile"].values()
        ),
        *(record["kind"] for record in snapshot["clocks"]),
    }
    evidence_snapshot = copy.deepcopy(dict(evidence_ledger))
    source_ref_identities = frozenset(
        (source_ref, entry["identity"])
        for entry in evidence_snapshot["entries"]
        for source_ref in entry["source_refs"]
    )
    represented_identities = {
        record["actor_id"]: record["evidence_status"]["information_identity"]
        for record in snapshot["actors"]
    }
    represented_identities.update(
        {
            record["circle_id"]: record["evidence_status"]["information_identity"]
            for record in snapshot["circles"]
        }
    )
    represented_identities.update(
        {
            record["position_id"]: record["evidence_status"]["information_identity"]
            for record in snapshot["positions"]
        }
    )
    return (
        snapshot,
        frozenset(locations),
        frozenset(residual_ids),
        frozenset(represented_ids),
        frozenset(relation_ids),
        frozenset(scale_qualifiers),
        source_ref_identities,
        represented_identities,
    )


def _qualified_identity(value: str, *, label: str) -> tuple[str, str]:
    prefix, separator, qualifier = value.rpartition("@")
    if not separator or not prefix or not qualifier:
        raise TransformationError(f"{label} must be a qualified identity")
    return prefix, qualifier


def _validate_transform_kind(
    record: Mapping[str, Any],
    *,
    represented_ids: frozenset[str],
    relation_ids: frozenset[str],
    scale_qualifiers: frozenset[str],
    source_ref_identities: frozenset[tuple[str, str]],
    represented_identities: Mapping[str, str],
) -> None:
    kind = record["kind"]
    input_identity = record["input_identity"]
    output_identity = record["output_identity"]
    if kind == "circle-relation":
        if input_identity not in relation_ids or output_identity not in relation_ids:
            raise TransformationError(
                f"transform {record['transform_id']!r} kind does not match "
                "declared circle-relation identities"
            )
        return

    input_prefix, input_qualifier = _qualified_identity(
        input_identity,
        label=f"transform {record['transform_id']!r} input",
    )
    output_prefix, output_qualifier = _qualified_identity(
        output_identity,
        label=f"transform {record['transform_id']!r} output",
    )
    if kind == "scale":
        if (
            input_prefix not in represented_ids
            or output_prefix not in represented_ids
            or input_qualifier not in scale_qualifiers
            or output_qualifier not in scale_qualifiers
        ):
            raise TransformationError(
                f"transform {record['transform_id']!r} kind does not match "
                "source-volume scale identities"
            )
        return

    if (input_prefix, input_qualifier) not in source_ref_identities:
        raise TransformationError(
            f"transform {record['transform_id']!r} kind does not match "
            "authorized U3 source representation identity"
        )
    if output_prefix in represented_identities:
        if output_qualifier != represented_identities[output_prefix]:
            raise TransformationError(
                f"transform {record['transform_id']!r} kind does not match "
                "the represented U4 identity"
            )
        return
    if (
        _ARTICLE_UNIT_ID_RE.fullmatch(output_prefix) is None
        or output_qualifier != "model-candidate"
    ):
        raise TransformationError(
            f"transform {record['transform_id']!r} kind does not match "
            "an authorized representation output identity"
        )


def validate_transformations(
    document: Mapping[str, object],
    *,
    source_volume: Mapping[str, object],
    evidence_ledger: Mapping[str, object],
) -> tuple[str, ...]:
    snapshot = _snapshot_mapping(document, label="transformation ledger")
    evidence_snapshot = _snapshot_mapping(
        evidence_ledger,
        label="preceding U3 evidence ledger",
    )
    try:
        validate_instance("ultra-transformation-ledger.schema.json", snapshot)
    except (ValidationError, TypeError, ValueError) as error:
        message = getattr(error, "message", str(error))
        raise TransformationError(
            f"transformation ledger schema validation failed: {message}"
        ) from error

    (
        volume_snapshot,
        locations,
        residual_ids,
        represented_ids,
        relation_ids,
        scale_qualifiers,
        source_ref_identities,
        represented_identities,
    ) = _volume_bindings(source_volume, evidence_ledger=evidence_snapshot)
    if (
        snapshot["run_id"] != volume_snapshot["run_id"]
        or snapshot["run_id"] != evidence_snapshot["run_id"]
    ):
        raise TransformationError(
            "transformation ledger, U4 world volume, and U3 evidence ledger must share a run"
        )
    if (
        snapshot["version_binding"] != volume_snapshot["version_binding"]
        or snapshot["version_binding"] != evidence_snapshot["version_binding"]
    ):
        raise TransformationError(
            "transformation ledger, U4 world volume, and U3 evidence ledger must share full version authority"
        )
    if snapshot["source_volume_sha256"] != sha256_bytes(
        canonical_json_bytes(volume_snapshot)
    ):
        raise TransformationError(
            "transformation ledger does not bind the exact source volume"
        )
    transformations = snapshot["transformations"]
    transform_ids = [record["transform_id"] for record in transformations]
    if len(transform_ids) != len(set(transform_ids)):
        raise TransformationError("transformation IDs must be unique")
    if {record["kind"] for record in transformations} != _TRANSFORM_KINDS:
        raise TransformationError(
            "scale, circle-relation, and representation-translation records "
            "must remain separate and complete"
        )

    loss_ids: list[str] = []
    effect_ids: list[str] = []
    effect_kinds: set[str] = set()
    for record in transformations:
        _validate_transform_kind(
            record,
            represented_ids=represented_ids,
            relation_ids=relation_ids,
            scale_qualifiers=scale_qualifiers,
            source_ref_identities=source_ref_identities,
            represented_identities=represented_identities,
        )
        if record["input_identity"] == record["output_identity"]:
            raise TransformationError(
                f"transform {record['transform_id']!r} does not change representation"
            )
        if not any(
            record[field] for field in ("changed", "folded", "omitted", "unknown")
        ):
            raise TransformationError(
                f"transform {record['transform_id']!r} declares no difference"
            )

        for loss in record["task_relative_loss"]:
            loss_ids.append(loss["loss_id"])
            if loss["location_ref"] not in locations:
                raise TransformationError(
                    f"loss {loss['loss_id']!r} has an unknown location"
                )
        for effect in record["location_effects"]:
            effect_ids.append(effect["effect_id"])
            effect_kinds.add(effect["effect_kind"])
            if effect["location_ref"] not in locations:
                raise TransformationError(
                    f"effect {effect['effect_id']!r} has an unknown location"
                )
        missing_residuals = set(record["residual_ids"]) - residual_ids
        if missing_residuals:
            raise TransformationError(
                f"transform {record['transform_id']!r} references unknown "
                f"residuals: {sorted(missing_residuals)!r}"
            )

    if len(loss_ids) != len(set(loss_ids)):
        raise TransformationError("task-relative loss IDs must be globally unique")
    if len(effect_ids) != len(set(effect_ids)):
        raise TransformationError("location effect IDs must be globally unique")
    if effect_kinds != _EFFECT_KINDS:
        raise TransformationError(
            "location effects must explicitly retain gain, damage, exit-cost, "
            "and spillover distributions"
        )
    return tuple(transform_ids)


def _checked_hops(cascade: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    if set(cascade) != {"cascade_id", "hops"}:
        raise ChannelContinuityError(
            "cascade must contain only cascade_id and explicit hops"
        )
    cascade_id = cascade.get("cascade_id")
    raw_hops = cascade.get("hops")
    if not isinstance(cascade_id, str) or not cascade_id:
        raise ChannelContinuityError("cascade_id must be a non-empty string")
    if (
        not isinstance(raw_hops, Sequence)
        or isinstance(raw_hops, (str, bytes))
        or not raw_hops
    ):
        raise ChannelContinuityError("cascade hops must be a non-empty sequence")

    required = {
        "hop_id",
        "from_position_id",
        "to_position_id",
        "channel_id",
        "boundary_validated",
        "representation_qualified",
    }
    hops: list[dict[str, object]] = []
    for ordinal, value in enumerate(raw_hops, start=1):
        if not isinstance(value, Mapping):
            raise ChannelContinuityError(f"cascade hop {ordinal} must be a mapping")
        hop = dict(value)
        if set(hop) != required:
            raise ChannelContinuityError(
                f"cascade hop {ordinal} must declare every validation field"
            )
        if any(
            not isinstance(hop[field], str) or not hop[field]
            for field in (
                "hop_id",
                "from_position_id",
                "to_position_id",
                "channel_id",
            )
        ):
            raise ChannelContinuityError(
                f"cascade hop {ordinal} contains an invalid identifier"
            )
        if hop["boundary_validated"] is not True:
            raise ChannelContinuityError(
                f"cascade hop {hop['hop_id']} has no validated boundary"
            )
        if hop["representation_qualified"] is not True:
            raise ChannelContinuityError(
                f"cascade hop {hop['hop_id']} lacks representation qualification"
            )
        hops.append(hop)
    hop_ids = [hop["hop_id"] for hop in hops]
    if len(hop_ids) != len(set(hop_ids)):
        raise ChannelContinuityError("cascade hop IDs must be unique")
    return tuple(hops)


def validate_cascade(
    cascade: Mapping[str, object],
    volume: Mapping[str, object],
    *,
    evidence_ledger: Mapping[str, object],
) -> tuple[str, ...]:
    try:
        validate_world_volume(volume, evidence_ledger=evidence_ledger)
    except WorldVolumeError as error:
        raise ChannelContinuityError(
            f"cascade source volume is invalid: {error}"
        ) from error
    cascade_snapshot = _snapshot_mapping(cascade, label="cascade")
    hops = _checked_hops(cascade_snapshot)

    positions = {
        record["position_id"] for record in volume["positions"]
    }
    channels = {
        record["channel_id"]: record for record in volume["channels"]
    }
    previous_target: str | None = None
    channel_ids: list[str] = []
    for hop in hops:
        hop_id = hop["hop_id"]
        source = hop["from_position_id"]
        target = hop["to_position_id"]
        if source not in positions or target not in positions:
            raise ChannelContinuityError(
                f"cascade hop {hop_id} has an unknown position"
            )
        if previous_target is not None and source != previous_target:
            raise ChannelContinuityError(
                f"cascade hop {hop_id} is disconnected from the previous hop"
            )
        channel = channels.get(hop["channel_id"])
        if channel is None:
            raise ChannelContinuityError(
                f"cascade hop {hop_id} channel is not declared"
            )
        if channel["active"] is not True:
            raise ChannelContinuityError(
                f"cascade hop {hop_id} channel is inactive"
            )
        if (
            channel["from_position_id"] != source
            or channel["to_position_id"] != target
        ):
            raise ChannelContinuityError(
                f"cascade hop {hop_id} does not match its directed channel endpoints"
            )
        channel_ids.append(channel["channel_id"])
        previous_target = target
    return tuple(channel_ids)


__all__ = (
    "ChannelContinuityError",
    "TransformationError",
    "validate_cascade",
    "validate_transformations",
)
