from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from ultra_runtime.transformations import (
    ChannelContinuityError,
    TransformationError,
    validate_cascade,
    validate_transformations,
)


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture
def valid_volume() -> dict[str, object]:
    return load_fixture("world-volume-valid.json")


@pytest.fixture
def valid_ledger() -> dict[str, object]:
    return load_fixture("transformation-valid.json")


@pytest.fixture
def evidence_ledger() -> dict[str, object]:
    return load_fixture("evidence-ledger-valid.json")


def test_scale_relation_and_representation_transforms_remain_separate(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    result = validate_transformations(
        valid_ledger,
        source_volume=valid_volume,
        evidence_ledger=evidence_ledger,
    )

    assert result == (
        "TRANSFORM-SCALE",
        "TRANSFORM-CIRCLE-RELATION",
        "TRANSFORM-REPRESENTATION",
    )
    transformations = valid_ledger["transformations"]
    assert isinstance(transformations, list)
    assert {transform["kind"] for transform in transformations} == {
        "scale",
        "circle-relation",
        "representation-translation",
    }
    assert {
        effect["effect_kind"]
        for transform in transformations
        for effect in transform["location_effects"]
    } == {"gain", "damage", "exit-cost", "spillover"}


@pytest.mark.parametrize(
    "mutation",
    (
        "net-effect-kind",
        "missing-kind",
        "no-location-effects",
        "unknown-effect-location",
        "unknown-loss-location",
        "duplicate-transform-id",
        "duplicate-loss-id",
        "duplicate-effect-id",
        "same-input-output",
        "no-declared-difference",
    ),
)
def test_net_effect_or_unlocated_transform_fails_closed(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    broken = copy.deepcopy(valid_ledger)
    transforms = broken["transformations"]
    if mutation == "net-effect-kind":
        transforms[0]["kind"] = "net-effect"
    elif mutation == "missing-kind":
        transforms.pop()
    elif mutation == "no-location-effects":
        transforms[0]["location_effects"] = []
    elif mutation == "unknown-effect-location":
        transforms[0]["location_effects"][0]["location_ref"] = "POS-MISSING"
    elif mutation == "unknown-loss-location":
        transforms[0]["task_relative_loss"][0]["location_ref"] = "POS-MISSING"
    elif mutation == "duplicate-transform-id":
        transforms[1]["transform_id"] = transforms[0]["transform_id"]
    elif mutation == "duplicate-loss-id":
        transforms[1]["task_relative_loss"][0]["loss_id"] = (
            transforms[0]["task_relative_loss"][0]["loss_id"]
        )
    elif mutation == "duplicate-effect-id":
        transforms[1]["location_effects"][0]["effect_id"] = (
            transforms[0]["location_effects"][0]["effect_id"]
        )
    elif mutation == "same-input-output":
        transforms[0]["output_identity"] = transforms[0]["input_identity"]
    elif mutation == "no-declared-difference":
        for field in ("changed", "folded", "omitted", "unknown"):
            transforms[0][field] = []
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)

    with pytest.raises(TransformationError):
        validate_transformations(
            broken,
            source_volume=valid_volume,
            evidence_ledger=evidence_ledger,
        )


def test_transform_validation_does_not_mutate_model_authored_ledger(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    original = copy.deepcopy(valid_ledger)

    validate_transformations(
        valid_ledger,
        source_volume=valid_volume,
        evidence_ledger=evidence_ledger,
    )

    assert valid_ledger == original


def test_transform_validation_requires_the_exact_source_volume(
    valid_ledger: dict[str, object],
) -> None:
    with pytest.raises(TypeError):
        validate_transformations(valid_ledger)


def test_transform_kind_labels_cannot_be_swapped(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    broken = copy.deepcopy(valid_ledger)
    broken["transformations"][0]["kind"] = "representation-translation"
    broken["transformations"][2]["kind"] = "scale"

    with pytest.raises(TransformationError, match="kind|identity|scale|representation"):
        validate_transformations(
            broken,
            source_volume=valid_volume,
            evidence_ledger=evidence_ledger,
        )


@pytest.mark.parametrize(
    ("input_identity", "output_identity"),
    (
        ("FORGED-SOURCE@reported", "ARTICLE-UNIT-M02@model-candidate"),
        ("SOURCE-INTERVIEW-ONE@reported", "FORGED-ARTICLE-UNIT@model-candidate"),
    ),
)
def test_representation_transform_binds_authorized_source_and_output_identities(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    input_identity: str,
    output_identity: str,
) -> None:
    broken = copy.deepcopy(valid_ledger)
    representation = broken["transformations"][2]
    representation["input_identity"] = input_identity
    representation["output_identity"] = output_identity

    with pytest.raises(TransformationError, match="representation|source|output|identity"):
        validate_transformations(
            broken,
            source_volume=valid_volume,
            evidence_ledger=evidence_ledger,
        )


def test_representation_transform_allows_a_u4_represented_output_identity(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    ledger = copy.deepcopy(valid_ledger)
    representation = ledger["transformations"][2]
    representation["input_identity"] = "SOURCE-ROSTER-ATLAS@observed"
    representation["output_identity"] = "POS-TEAM-MANAGER@observed"

    assert validate_transformations(
        ledger,
        source_volume=valid_volume,
        evidence_ledger=evidence_ledger,
    )[-1] == "TRANSFORM-REPRESENTATION"


def test_transform_ledger_binds_the_exact_source_volume_and_residuals(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    assert validate_transformations(
        valid_ledger,
        source_volume=valid_volume,
        evidence_ledger=evidence_ledger,
    ) == (
        "TRANSFORM-SCALE",
        "TRANSFORM-CIRCLE-RELATION",
        "TRANSFORM-REPRESENTATION",
    )

    wrong_hash = copy.deepcopy(valid_ledger)
    wrong_hash["source_volume_sha256"] = "e" * 64
    unknown_residual = copy.deepcopy(valid_ledger)
    unknown_residual["transformations"][0]["residual_ids"] = ["RESIDUAL-MISSING"]
    for broken in (wrong_hash, unknown_residual):
        with pytest.raises(TransformationError, match="source|residual|bind"):
            validate_transformations(
                broken,
                source_volume=valid_volume,
                evidence_ledger=evidence_ledger,
            )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("run_id", "other-run"),
        ("source_tree_sha256", "d" * 64),
    ),
)
def test_u5_transformation_ledger_binds_u3_u4_run_and_every_version_field(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    field: str,
    value: str,
) -> None:
    broken = copy.deepcopy(valid_ledger)
    if field == "run_id":
        broken[field] = value
    else:
        broken["version_binding"][field] = value

    with pytest.raises(TransformationError, match="run|version|authority|bind"):
        validate_transformations(
            broken,
            source_volume=valid_volume,
            evidence_ledger=evidence_ledger,
        )


@pytest.mark.parametrize("mutation", ("run", "version"))
def test_u5_rejects_u3_and_u4_that_agree_with_each_other_but_not_u5(
    valid_ledger: dict[str, object],
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    volume = copy.deepcopy(valid_volume)
    evidence = copy.deepcopy(evidence_ledger)
    if mutation == "run":
        volume["run_id"] = "other-run"
        evidence["run_id"] = "other-run"
    else:
        volume["version_binding"]["source_tree_sha256"] = "d" * 64
        evidence["version_binding"]["source_tree_sha256"] = "d" * 64

    with pytest.raises(TransformationError, match="run|version|authority|bind"):
        validate_transformations(
            valid_ledger,
            source_volume=volume,
            evidence_ledger=evidence,
        )


def test_one_hop_cascade_binds_the_real_local_channel(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    cascade = {
        "cascade_id": "CASCADE-ONE-HOP",
        "hops": [
            {
                "hop_id": "HOP-ONE",
                "from_position_id": "POS-FAMILY-MEMBER",
                "to_position_id": "POS-TEAM-MANAGER",
                "channel_id": "CHANNEL-FAMILY-TEAM",
                "boundary_validated": True,
                "representation_qualified": True,
            }
        ],
    }

    assert validate_cascade(
        cascade,
        valid_volume,
        evidence_ledger=evidence_ledger,
    ) == ("CHANNEL-FAMILY-TEAM",)


def test_each_cross_circle_hop_is_revalidated(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    cascade_with_valid_first_hop_and_missing_second_hop = {
        "cascade_id": "CASCADE-MISSING-SECOND-CHANNEL",
        "hops": [
            {
                "hop_id": "HOP-ONE",
                "from_position_id": "POS-FAMILY-MEMBER",
                "to_position_id": "POS-TEAM-MANAGER",
                "channel_id": "CHANNEL-FAMILY-TEAM",
                "boundary_validated": True,
                "representation_qualified": True,
            },
            {
                "hop_id": "HOP-TWO",
                "from_position_id": "POS-TEAM-MANAGER",
                "to_position_id": "POS-ASSOCIATION-DELEGATE",
                "channel_id": "CHANNEL-NOT-DECLARED",
                "boundary_validated": True,
                "representation_qualified": True,
            },
        ],
    }

    with pytest.raises(ChannelContinuityError, match="HOP-TWO|channel"):
        validate_cascade(
            cascade_with_valid_first_hop_and_missing_second_hop,
            valid_volume,
            evidence_ledger=evidence_ledger,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "disconnected-hop",
        "wrong-channel-endpoints",
        "inactive-channel",
        "boundary-not-validated",
        "representation-not-qualified",
        "duplicate-hop-id",
    ),
)
def test_cascade_revalidates_continuity_boundary_and_representation_per_hop(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    volume = copy.deepcopy(valid_volume)
    hop = {
        "hop_id": "HOP-ONE",
        "from_position_id": "POS-FAMILY-MEMBER",
        "to_position_id": "POS-TEAM-MANAGER",
        "channel_id": "CHANNEL-FAMILY-TEAM",
        "boundary_validated": True,
        "representation_qualified": True,
    }
    cascade = {"cascade_id": "CASCADE-BROKEN", "hops": [hop]}
    if mutation == "disconnected-hop":
        cascade["hops"].append(
            {
                **hop,
                "hop_id": "HOP-TWO",
                "from_position_id": "POS-FAMILY-MEMBER",
            }
        )
    elif mutation == "wrong-channel-endpoints":
        hop["to_position_id"] = "POS-ASSOCIATION-DELEGATE"
    elif mutation == "inactive-channel":
        volume["channels"][0]["active"] = False
    elif mutation == "boundary-not-validated":
        hop["boundary_validated"] = False
    elif mutation == "representation-not-qualified":
        hop["representation_qualified"] = False
    elif mutation == "duplicate-hop-id":
        cascade["hops"].append(copy.deepcopy(hop))
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)

    with pytest.raises(ChannelContinuityError):
        validate_cascade(cascade, volume, evidence_ledger=evidence_ledger)
