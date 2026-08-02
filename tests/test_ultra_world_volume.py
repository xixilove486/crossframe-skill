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

from ultra_runtime.world_volume import (
    StateDiff,
    WorldVolumeError,
    apply_event,
    validate_world_volume,
)


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture
def valid_volume() -> dict[str, object]:
    return load_fixture("world-volume-valid.json")


@pytest.fixture
def evidence_ledger() -> dict[str, object]:
    return load_fixture("evidence-ledger-valid.json")


def test_valid_volume_preserves_multicircle_locality_and_source_faithful_wk(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    validate_world_volume(valid_volume, evidence_ledger=evidence_ledger)

    positions = valid_volume["positions"]
    assert isinstance(positions, list)
    assert [position["role_id"] for position in positions] == [
        "ROLE-FAMILY-MEMBER",
        "ROLE-TEAM-MANAGER",
        "ROLE-ASSOCIATION-DELEGATE",
    ]

    relations = valid_volume["circle_relations"]
    assert isinstance(relations, list)
    assert {
        (
            relation["from_circle_id"],
            relation["to_circle_id"],
            relation["relation_type"],
            relation["direction"],
        )
        for relation in relations
    } == {
        (
            "CIRCLE-TEAM",
            "CIRCLE-ASSOCIATION",
            "resource-transfer",
            "directed",
        ),
        (
            "CIRCLE-TEAM",
            "CIRCLE-ASSOCIATION",
            "information-reporting",
            "directed",
        ),
    }

    containments = valid_volume["containment_relations"]
    assert isinstance(containments, list)
    assert {
        (item["child_circle_id"], item["parent_circle_id"], item["basis"])
        for item in containments
    } == {
        ("CIRCLE-TEAM", "CIRCLE-FAMILY", "resource-accounting"),
        ("CIRCLE-TEAM", "CIRCLE-ASSOCIATION", "contract"),
    }

    represented = [
        *valid_volume["actors"],
        *valid_volume["circles"],
        *positions,
    ]
    scale_axes = {
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
    forbidden_wk_overloads = {
        "power",
        "constraint",
        "exit",
        "burden",
        "spillover",
    }
    for item in represented:
        assert set(item["scale_profile"]) == scale_axes
        assert item["identity_criteria"].strip()
        evidence_status = item["evidence_status"]
        assert set(evidence_status) == {
            "status",
            "information_identity",
            "source_lineage",
            "visibility",
        }
        assert forbidden_wk_overloads.isdisjoint(evidence_status)

    clocks = valid_volume["clocks"]
    assert isinstance(clocks, list)
    assert {clock["kind"] for clock in clocks} == {
        "immediate",
        "interaction",
        "organizational",
        "institutional",
        "long-term",
    }

    distributions = valid_volume["local_distributions"]
    assert isinstance(distributions, list)
    assert {distribution["kind"] for distribution in distributions} == {
        "power",
        "constraint",
        "exit",
        "burden",
        "spillover",
    }


def test_flattened_global_fixture_is_rejected(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    invalid = load_fixture("world-volume-flat-invalid.json")
    mutation = invalid["mutation"]
    assert isinstance(mutation, dict)
    flattened = copy.deepcopy(valid_volume)
    flattened.update(copy.deepcopy(mutation))

    with pytest.raises(WorldVolumeError, match="schema|global|flatten"):
        validate_world_volume(flattened, evidence_ledger=evidence_ledger)


@pytest.mark.parametrize(
    "mutation",
    (
        "global-M",
        "global-Psi",
        "global-scale",
        "single-parent",
        "averaged-circle",
        "missing-membership-basis",
        "relation-without-direction",
        "channel-without-endpoint",
        "position-without-K",
        "actor-without-local-M",
        "circle-without-local-Psi",
        "position-without-W",
    ),
)
def test_flattening_and_local_coverage_fail_closed(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    if mutation == "global-M":
        broken["global_M"] = copy.deepcopy(broken["positions"][0]["M_state"])
    elif mutation == "global-Psi":
        broken["global_Psi"] = copy.deepcopy(
            broken["positions"][0]["Psi_state"]
        )
    elif mutation == "global-scale":
        broken["global_scale_label"] = "organization"
    elif mutation == "single-parent":
        broken["circles"][1]["parent_id"] = "CIRCLE-FAMILY"
    elif mutation == "averaged-circle":
        broken["circles"][1]["averaged_state"] = {
            "source_position_ids": ["POS-FAMILY-MEMBER", "POS-TEAM-MANAGER"]
        }
    elif mutation == "missing-membership-basis":
        del broken["memberships"][0]["basis"]
    elif mutation == "relation-without-direction":
        del broken["circle_relations"][0]["direction"]
    elif mutation == "channel-without-endpoint":
        del broken["channels"][0]["to_position_id"]
    elif mutation == "position-without-K":
        del broken["positions"][0]["identity_criteria"]
    elif mutation == "actor-without-local-M":
        del broken["actors"][0]["M_state"]
    elif mutation == "circle-without-local-Psi":
        del broken["circles"][0]["Psi_state"]
    elif mutation == "position-without-W":
        del broken["positions"][0]["evidence_status"]
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)

    with pytest.raises(WorldVolumeError):
        validate_world_volume(broken, evidence_ledger=evidence_ledger)


def test_identity_and_graph_references_are_not_self_reported(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    mutations: list[dict[str, object]] = []

    duplicate_position = copy.deepcopy(valid_volume)
    duplicate_position["positions"].append(
        copy.deepcopy(duplicate_position["positions"][0])
    )
    mutations.append(duplicate_position)

    unknown_actor = copy.deepcopy(valid_volume)
    unknown_actor["positions"][0]["actor_id"] = "ACTOR-MISSING"
    mutations.append(unknown_actor)

    missing_membership = copy.deepcopy(valid_volume)
    missing_membership["memberships"].pop(0)
    mutations.append(missing_membership)

    bad_containment = copy.deepcopy(valid_volume)
    bad_containment["containment_relations"][0]["parent_circle_id"] = (
        "CIRCLE-MISSING"
    )
    mutations.append(bad_containment)

    unknown_location = copy.deepcopy(valid_volume)
    unknown_location["unknowns"][0]["location_ref"] = "CHANNEL-MISSING"
    mutations.append(unknown_location)

    for broken in mutations:
        with pytest.raises(WorldVolumeError):
            validate_world_volume(broken, evidence_ledger=evidence_ledger)


@pytest.mark.parametrize(
    ("kind", "bad_location"),
    (
        ("power", "CHANNEL-FAMILY-TEAM"),
        ("exit", "M-POS-TEAM"),
        ("constraint", "MEMBERSHIP-TEAM"),
        ("burden", "PSI-POS-TEAM"),
        ("spillover", "M-POS-TEAM"),
    ),
)
def test_local_distributions_bind_their_exact_rac_q_m_or_psi_location(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    kind: str,
    bad_location: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    distribution = next(
        item for item in broken["local_distributions"] if item["kind"] == kind
    )
    distribution["location_ref"] = bad_location

    with pytest.raises(WorldVolumeError, match="location|distribution"):
        validate_world_volume(broken, evidence_ledger=evidence_ledger)


def test_w_and_k_cannot_carry_power_or_distribution_state(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    overloaded_w = copy.deepcopy(valid_volume)
    overloaded_w["positions"][0]["evidence_status"]["power"] = "high"

    overloaded_k = copy.deepcopy(valid_volume)
    overloaded_k["positions"][0]["identity_criteria"] = {
        "criterion": "same role",
        "burden": "high",
    }

    for broken in (overloaded_w, overloaded_k):
        with pytest.raises(WorldVolumeError):
            validate_world_volume(broken, evidence_ledger=evidence_ledger)


def test_u4_w_lineage_requires_preceding_u3_evidence_authority(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    forged = copy.deepcopy(valid_volume)
    forged["positions"][0]["evidence_status"]["source_lineage"] = [
        "EVIDENCE-NOT-FROZEN"
    ]

    with pytest.raises(WorldVolumeError, match="U3|lineage|evidence"):
        validate_world_volume(forged, evidence_ledger=evidence_ledger)

    with pytest.raises(TypeError):
        validate_world_volume(valid_volume)


@pytest.mark.parametrize(
    "mutation",
    (
        "user-claim-promoted-to-observed",
        "unknown-promoted-to-observed",
        "observed-without-observed-at",
    ),
)
def test_u4_w_lineage_reuses_u3_runtime_identity_validation(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    broken_volume = copy.deepcopy(valid_volume)
    broken_evidence = copy.deepcopy(evidence_ledger)
    observed_position = broken_volume["positions"][1]

    if mutation == "user-claim-promoted-to-observed":
        observed_position["evidence_status"]["source_lineage"] = [
            "EVIDENCE-ASSOCIATION-CHARTER"
        ]
    elif mutation == "unknown-promoted-to-observed":
        broken_evidence["entries"][1]["identity"] = "unknown"
    elif mutation == "observed-without-observed-at":
        broken_evidence["entries"][1]["observed_at"] = None
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)

    with pytest.raises(WorldVolumeError, match="evidence|identity|observed|U3"):
        validate_world_volume(broken_volume, evidence_ledger=broken_evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("containment_basis", "classification"),
        ("circle_direction", "bidirectional"),
    ),
)
def test_containment_and_circle_relations_stay_explicitly_directed_and_closed(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    field: str,
    value: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    if field == "containment_basis":
        broken["containment_relations"][0]["basis"] = value
    else:
        broken["circle_relations"][0]["direction"] = value

    with pytest.raises(WorldVolumeError, match="basis|directed|schema"):
        validate_world_volume(broken, evidence_ledger=evidence_ledger)


def test_event_updates_only_reachable_positions_and_preserves_input(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    frozen_input = copy.deepcopy(valid_volume)
    event = copy.deepcopy(valid_volume["events"][0])

    result = apply_event(valid_volume, event, evidence_ledger=evidence_ledger)

    assert isinstance(result, StateDiff)
    assert len(result.source_volume_sha256) == 64
    assert result.event_id == "EVENT-FAMILY-DEMAND"
    assert result.changed_positions == ("POS-TEAM-MANAGER",)
    assert result.unchanged_positions == (
        "POS-FAMILY-MEMBER",
        "POS-ASSOCIATION-DELEGATE",
    )
    assert result.changed_relations == (
        "MEMBERSHIP-TEAM",
        "REL-TEAM-ASSOCIATION-RESOURCE",
    )
    assert result.advanced_clocks == (
        "CLOCK-IMMEDIATE",
        "CLOCK-ORGANIZATIONAL",
    )
    assert result.inherited_unknown_ids == ("UNKNOWN-CHANNEL-LATENCY",)
    assert result.inherited_residual_ids == (
        "RESIDUAL-ASSOCIATION-RESPONSE",
    )
    assert valid_volume == frozen_input


def test_event_diff_is_deterministic_for_equivalent_mapping_order(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    event = copy.deepcopy(valid_volume["events"][0])
    reordered = dict(reversed(list(valid_volume.items())))

    assert apply_event(
        valid_volume, event, evidence_ledger=evidence_ledger
    ) == apply_event(reordered, event, evidence_ledger=evidence_ledger)


def test_event_rejects_a_declared_channel_disconnected_from_its_source(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken["channels"].append(
        {
            "channel_id": "CHANNEL-ASSOCIATION-SELF",
            "from_position_id": "POS-ASSOCIATION-DELEGATE",
            "to_position_id": "POS-ASSOCIATION-DELEGATE",
            "channel_type": "internal-review",
            "active": True,
            "capacity": "one review per month",
            "delay": "P1D",
            "threshold": "one filed motion",
            "constraint_distribution": "Only the association position is constrained.",
            "access_distribution": "Only the association position has access.",
        }
    )
    event = copy.deepcopy(broken["events"][0])
    event["channel_ids"].append("CHANNEL-ASSOCIATION-SELF")
    broken["events"][0] = copy.deepcopy(event)

    with pytest.raises(WorldVolumeError, match="channel|connected|source"):
        apply_event(broken, event, evidence_ledger=evidence_ledger)


@pytest.mark.parametrize(
    "mutation",
    (
        "unreachable-target",
        "inactive-channel",
        "undeclared-channel",
        "reversed-channel",
        "unknown-source",
    ),
)
def test_event_cannot_cross_an_unvalidated_channel(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    broken_volume = copy.deepcopy(valid_volume)
    event = copy.deepcopy(valid_volume["events"][0])
    if mutation == "unreachable-target":
        event["target_position_ids"] = ["POS-ASSOCIATION-DELEGATE"]
    elif mutation == "inactive-channel":
        broken_volume["channels"][0]["active"] = False
    elif mutation == "undeclared-channel":
        event["channel_ids"] = ["CHANNEL-MISSING"]
    elif mutation == "reversed-channel":
        channel = broken_volume["channels"][0]
        channel["from_position_id"], channel["to_position_id"] = (
            channel["to_position_id"],
            channel["from_position_id"],
        )
    elif mutation == "unknown-source":
        event["source_position_id"] = "POS-MISSING"
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)

    with pytest.raises(WorldVolumeError, match="event|channel|reachable|source"):
        apply_event(broken_volume, event, evidence_ledger=evidence_ledger)


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-material-update",
        "mismatched-meaning-target",
        "unknown-state-variable",
        "unknown-relation",
        "wrong-relation-kind",
        "unreachable-update-channel",
        "unknown-clock",
        "clock-outside-update",
    ),
)
def test_event_declares_and_binds_each_local_update(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    mutation: str,
) -> None:
    volume = copy.deepcopy(valid_volume)
    event = copy.deepcopy(valid_volume["events"][0])
    if mutation == "missing-material-update":
        event["M_updates"] = []
    elif mutation == "mismatched-meaning-target":
        event["Psi_updates"][0]["position_id"] = "POS-FAMILY-MEMBER"
    elif mutation == "unknown-state-variable":
        event["M_updates"][0]["changed_variable_names"] = ["not-declared"]
    elif mutation == "unknown-relation":
        event["relation_updates"][0]["relation_id"] = "RELATION-MISSING"
    elif mutation == "wrong-relation-kind":
        event["relation_updates"][1]["relation_kind"] = "Rac"
    elif mutation == "unreachable-update-channel":
        event["M_updates"][0]["via_channel_id"] = "CHANNEL-NOT-DECLARED"
    elif mutation == "unknown-clock":
        event["clock_deltas"][0]["clock_id"] = "CLOCK-MISSING"
    elif mutation == "clock-outside-update":
        event["clock_deltas"][0]["clock_id"] = "CLOCK-INTERACTION"
    else:  # pragma: no cover - parametrization exhausts cases
        raise AssertionError(mutation)
    volume["events"][0] = event

    with pytest.raises(WorldVolumeError, match="schema|event|update|relation|clock|channel"):
        apply_event(volume, event, evidence_ledger=evidence_ledger)


@pytest.mark.parametrize("delta", ("no advance occurred", "P0D", "PT0S"))
def test_state_diff_rejects_non_advancing_clock_deltas(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    delta: str,
) -> None:
    volume = copy.deepcopy(valid_volume)
    event = copy.deepcopy(volume["events"][0])
    event["clock_deltas"][0]["delta"] = delta
    volume["events"][0] = event

    with pytest.raises(WorldVolumeError, match="clock|advance|delta|duration"):
        apply_event(volume, event, evidence_ledger=evidence_ledger)


def test_state_diff_reports_only_canonical_deterministic_clock_advances(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
) -> None:
    volume = copy.deepcopy(valid_volume)
    event = copy.deepcopy(volume["events"][0])
    event["clock_deltas"] = [
        {"clock_id": "CLOCK-IMMEDIATE", "delta": "PT1H30M"},
        {"clock_id": "CLOCK-ORGANIZATIONAL", "delta": "P1DT2H3M4S"},
    ]
    volume["events"][0] = event

    assert apply_event(
        volume,
        event,
        evidence_ledger=evidence_ledger,
    ).advanced_clocks == ("CLOCK-IMMEDIATE", "CLOCK-ORGANIZATIONAL")


@pytest.mark.parametrize(
    "delta",
    (
        "P1.5Y2M",
        "P1W1D",
        "PT1.5H30M",
        "P0D",
        "-PT1H",
        "P01D",
        "PT1H0M",
        "PT24H",
        "PT60M",
        "PT1M60S",
        "P1000000000D",
    ),
)
def test_state_diff_rejects_noncanonical_or_unbounded_clock_deltas(
    valid_volume: dict[str, object],
    evidence_ledger: dict[str, object],
    delta: str,
) -> None:
    volume = copy.deepcopy(valid_volume)
    event = copy.deepcopy(volume["events"][0])
    event["clock_deltas"][0]["delta"] = delta
    volume["events"][0] = event

    with pytest.raises(WorldVolumeError, match="clock|advance|delta|duration"):
        apply_event(volume, event, evidence_ledger=evidence_ledger)
