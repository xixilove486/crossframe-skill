from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pytest
from jsonschema import ValidationError


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import (
    compute_artifact_content_sha256,
    validate_phase_artifact,
)
from ultra_runtime.world_volume import (
    StateDiff,
    WorldVolumeError,
    apply_event,
    validate_world_volume,
)


RUN_ID = "ultra-world-fixture-run"
EVIDENCE_ARTIFACT_SHA256 = (
    "b2e92cdb80bc8c497b8d215ac490a418d68c7142484f6af0f073c18df8794981"
)
EVIDENCE_CONTENT_SHA256 = (
    "3b59c571ff33f09c23704b4f3ada5f4941c718b6f28e7225f5de1f804dc94985"
)
WORLD_CONTENT_SHA256 = (
    "0d0b71596320e3fe26babbe42e1a87507d873a905ce0d20b75427054753a1f07"
)
WORLD_ARTIFACT_SHA256 = (
    "29b324b8f6d3596b2e9df7c1d23adfd9f17fcd5b55a7f73113a09ebd292f6ce5"
)
RELATION_REFS_SHA256 = (
    "cd8b59e7c3877cb26c778f2a41d7dba6604e1288d54b7aa846292bcbdf5ab60a"
)
RELATION_KEY_ALIAS_SHA256 = (
    "46fac6726483e68059a2c02178ffca2d29d897b1bebf31c6e915dd618c800b59"
)
VERSION_BINDING: dict[str, object] = {
    "framework_version": "8.2",
    "framework_revision": "v8.2-r1",
    "framework_raw_sha256": (
        "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
    ),
    "framework_semantic_sha256": (
        "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
    ),
    "runtime_version": "1.0.0",
    "artifact_schema_version": 1,
    "compiler_version": "1.0.0",
    "validator_version": "1.0.0",
    "article_contract_version": "1.0.0",
    "source_tree_sha256": (
        "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
    ),
}
RELATION_KEYS = (
    "RELATION-AUTHORITY-01",
    "RELATION-AUTHORITY-02",
    "RELATION-AUTHORITY-03",
    "RELATION-AUTHORITY-04",
    "RELATION-AUTHORITY-05",
)


class AlwaysEqual:
    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


class AlwaysEqualStr(str):
    def __new__(cls, value: str = "0" * 64) -> AlwaysEqualStr:
        return super().__new__(cls, value)

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    __hash__ = str.__hash__


class RelationKeyAlias(str):
    def __new__(cls, serialized: str, lookup: str) -> RelationKeyAlias:
        instance = super().__new__(cls, serialized)
        instance.lookup = lookup
        return instance

    def __eq__(self, other: object) -> bool:
        if type(other) is str:
            return other == self.lookup
        return str.__eq__(self, other)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.lookup)

    def __reduce__(self) -> tuple[type[RelationKeyAlias], tuple[str, str]]:
        return type(self), (str(self), self.lookup)


def load_fixture(name: str) -> dict[str, Any]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def test_world_public_introspection_contract_is_frozen() -> None:
    positional = inspect.Parameter.POSITIONAL_OR_KEYWORD
    keyword_only = inspect.Parameter.KEYWORD_ONLY
    shared_authorities = (
        ("evidence_ledger", keyword_only),
        ("expected_run_id", keyword_only),
        ("expected_version_binding", keyword_only),
        ("expected_evidence_artifact_sha256", keyword_only),
        ("relation_refs", keyword_only),
        ("expected_relation_refs_sha256", keyword_only),
    )
    expected_signatures = {
        validate_world_volume: (("volume", positional), *shared_authorities),
        apply_event: (
            ("volume", positional),
            ("event", positional),
            *shared_authorities,
        ),
    }

    for function, expected_parameters in expected_signatures.items():
        parameters = tuple(inspect.signature(function).parameters.values())
        assert tuple((parameter.name, parameter.kind) for parameter in parameters) == (
            expected_parameters
        )
        assert all(
            parameter.default is inspect.Parameter.empty for parameter in parameters
        )


def rehash_artifact(value: Mapping[str, object]) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(value))
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return snapshot


def make_relation_refs(volume: Mapping[str, object]) -> dict[str, dict[str, object]]:
    memberships = volume["memberships"]
    circle_relations = volume["circle_relations"]
    assert isinstance(memberships, list)
    assert isinstance(circle_relations, list)
    records = [
        *(('Rac', record) for record in memberships),
        *(('Rcc', record) for record in circle_relations),
    ]
    assert len(records) == len(RELATION_KEYS)
    return {
        key: {
            "relation_kind": relation_kind,
            "record_sha256": canonical_sha256(record),
            "record": copy.deepcopy(record),
        }
        for key, (relation_kind, record) in zip(RELATION_KEYS, records, strict=True)
    }


@pytest.fixture
def valid_volume() -> dict[str, Any]:
    return load_fixture("world-volume-valid.json")


@pytest.fixture
def evidence_ledger() -> dict[str, Any]:
    authority = load_fixture("evidence-ledger-valid.json")
    authority["run_id"] = RUN_ID
    return rehash_artifact(authority)


@pytest.fixture
def relation_refs(valid_volume: Mapping[str, object]) -> dict[str, dict[str, object]]:
    return make_relation_refs(valid_volume)


def authority_kwargs(
    evidence_ledger: Mapping[str, object],
    relation_refs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "evidence_ledger": evidence_ledger,
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_evidence_artifact_sha256": EVIDENCE_ARTIFACT_SHA256,
        "relation_refs": relation_refs,
        "expected_relation_refs_sha256": RELATION_REFS_SHA256,
    }


def validate(
    volume: Mapping[str, object],
    evidence_ledger: Mapping[str, object],
    relation_refs: Mapping[str, Mapping[str, object]],
) -> None:
    validate_world_volume(
        volume,
        **authority_kwargs(evidence_ledger, relation_refs),
    )


def test_world_fixture_is_a_real_frozen_u4_artifact(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    validate_phase_artifact(
        "ultra-world-volume.schema.json",
        valid_volume,
        expected_schema_id="crossframe.ultra.v82.world-volume",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U4",
    )
    validate(valid_volume, evidence_ledger, relation_refs)
    assert valid_volume["content_sha256"] == WORLD_CONTENT_SHA256
    assert canonical_sha256(valid_volume) == WORLD_ARTIFACT_SHA256
    assert valid_volume["evidence_content_sha256"] == EVIDENCE_CONTENT_SHA256
    assert valid_volume["evidence_artifact_sha256"] == EVIDENCE_ARTIFACT_SHA256


def test_volume_preserves_multicircle_roles_relations_and_local_axes(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    validate(valid_volume, evidence_ledger, relation_refs)
    assert {position["role_id"] for position in valid_volume["positions"]} == {
        "ROLE-FAMILY-MEMBER",
        "ROLE-MANAGER",
        "ROLE-DELEGATE",
    }
    assert {
        (
            record["source_circle_ref"],
            record["target_circle_ref"],
            record["relation_type"],
        )
        for record in valid_volume["circle_relations"]
    } == {
        ("CIRCLE-TEAM", "CIRCLE-ASSOCIATION", "桥接"),
        ("CIRCLE-TEAM", "CIRCLE-ASSOCIATION", "竞争"),
    }
    represented = [
        *valid_volume["actors"],
        *valid_volume["circles"],
        *valid_volume["positions"],
    ]
    for record in represented:
        assert set(record["scale_profile"]) == set("AXTOCRINJ")
        assert record["M_state"]["variables"]
        assert record["Psi_state"]["variables"]
        assert record["identity_criteria"].strip()
    assert {clock["kind"] for clock in valid_volume["clocks"]} == {
        "immediate",
        "interaction",
        "organizational",
        "institutional",
        "long-term",
    }


def test_local_distributions_use_opaque_rac_q_m_and_psi_refs(
    valid_volume: dict[str, Any],
) -> None:
    by_kind = {record["kind"]: record["location_ref"] for record in valid_volume["local_distributions"] if record["kind"] != "constraint"}
    assert by_kind == {
        "power": "RELATION-AUTHORITY-02",
        "exit": "RELATION-AUTHORITY-01",
        "burden": "M-POS-TEAM",
        "spillover": "PSI-POS-ASSOCIATION",
    }
    assert {
        record["location_ref"]
        for record in valid_volume["local_distributions"]
        if record["kind"] == "constraint"
    } == {"CHANNEL-TEAM-SELF", "CHANNEL-TEAM-ASSOCIATION"}


def test_flattened_volume_is_rejected(
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    flattened = load_fixture("world-volume-flat-invalid.json")
    flattened["global_M_state"]["resources"] = "mutated global average"
    flattened = rehash_artifact(flattened)
    assert flattened["content_sha256"] == compute_artifact_content_sha256(flattened)
    with pytest.raises(ValidationError) as schema_error:
        validate_phase_artifact(
            "ultra-world-volume.schema.json",
            flattened,
            expected_schema_id="crossframe.ultra.v82.world-volume",
            expected_run_id=RUN_ID,
            expected_version_binding=VERSION_BINDING,
            expected_phase_id="U4",
        )
    assert schema_error.value.validator == "required"
    assert "actors" in schema_error.value.message
    with pytest.raises(WorldVolumeError, match="invalid U4 world volume"):
        validate(
            flattened,
            evidence_ledger,
            relation_refs,
        )


@pytest.mark.parametrize(
    ("keyword", "replacement"),
    [
        ("expected_run_id", "another-run"),
        ("expected_version_binding", {**VERSION_BINDING, "validator_version": "9"}),
        ("expected_evidence_artifact_sha256", "f" * 64),
        ("expected_relation_refs_sha256", "e" * 64),
    ],
)
def test_external_expected_authority_cannot_be_self_selected(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    keyword: str,
    replacement: object,
) -> None:
    kwargs = authority_kwargs(evidence_ledger, relation_refs)
    kwargs[keyword] = replacement
    with pytest.raises(WorldVolumeError):
        validate_world_volume(valid_volume, **kwargs)


@pytest.mark.parametrize(
    "attacker",
    [AlwaysEqual(), AlwaysEqualStr()],
    ids=("arbitrary-always-equal", "always-equal-str-subclass"),
)
@pytest.mark.parametrize(
    "keyword",
    ("expected_evidence_artifact_sha256", "expected_relation_refs_sha256"),
)
@pytest.mark.parametrize("public_api", ("validate", "apply"))
def test_world_public_hash_authority_rejects_equality_attackers(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    attacker: object,
    keyword: str,
    public_api: str,
) -> None:
    kwargs = authority_kwargs(evidence_ledger, relation_refs)
    kwargs[keyword] = attacker
    with pytest.raises(WorldVolumeError):
        if public_api == "validate":
            validate_world_volume(valid_volume, **kwargs)
        else:
            apply_event(valid_volume, valid_volume["events"][0], **kwargs)


@pytest.mark.parametrize(
    ("keyword", "replacement"),
    [
        ("expected_evidence_artifact_sha256", "A" * 64),
        ("expected_evidence_artifact_sha256", "0" * 63),
        ("expected_relation_refs_sha256", "A" * 64),
        ("expected_relation_refs_sha256", "0" * 63),
    ],
)
def test_world_public_hash_authority_requires_lowercase_64_hex(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    keyword: str,
    replacement: str,
) -> None:
    kwargs = authority_kwargs(evidence_ledger, relation_refs)
    kwargs[keyword] = replacement
    with pytest.raises(WorldVolumeError):
        validate_world_volume(valid_volume, **kwargs)


@pytest.mark.parametrize("public_api", ("validate", "apply"))
@pytest.mark.parametrize("authority_kind", ("run-id", "version-binding"))
def test_world_public_scalar_authority_rejects_equality_overrides(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    public_api: str,
    authority_kind: str,
) -> None:
    kwargs = authority_kwargs(evidence_ledger, relation_refs)
    if authority_kind == "run-id":
        kwargs["expected_run_id"] = AlwaysEqualStr("attacker-run")
    else:
        kwargs["expected_version_binding"] = {
            **VERSION_BINDING,
            "validator_version": AlwaysEqualStr("attacker-version"),
        }
    with pytest.raises(WorldVolumeError):
        if public_api == "validate":
            validate_world_volume(valid_volume, **kwargs)
        else:
            apply_event(valid_volume, valid_volume["events"][0], **kwargs)


@pytest.mark.parametrize("public_api", ("validate", "apply"))
@pytest.mark.parametrize("artifact_name", ("volume", "evidence"))
@pytest.mark.parametrize("artifact_field", ("run-id", "version-binding"))
def test_world_artifact_authority_fields_reject_str_subclasses(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    public_api: str,
    artifact_name: str,
    artifact_field: str,
) -> None:
    attacked_volume = copy.deepcopy(valid_volume)
    attacked_evidence = copy.deepcopy(evidence_ledger)
    attacked = attacked_volume if artifact_name == "volume" else attacked_evidence
    preserve_canonical_text = artifact_name == "evidence"
    if artifact_field == "run-id":
        text = attacked["run_id"] if preserve_canonical_text else "attacker-run"
        attacked["run_id"] = AlwaysEqualStr(text)
    else:
        text = (
            attacked["version_binding"]["runtime_version"]
            if preserve_canonical_text
            else "attacker-runtime"
        )
        attacked["version_binding"]["runtime_version"] = AlwaysEqualStr(text)
    if artifact_name == "volume":
        attacked_volume = rehash_artifact(attacked_volume)
    else:
        attacked_evidence = rehash_artifact(attacked_evidence)
    kwargs = authority_kwargs(attacked_evidence, relation_refs)
    with pytest.raises(WorldVolumeError):
        if public_api == "validate":
            validate_world_volume(attacked_volume, **kwargs)
        else:
            apply_event(
                attacked_volume,
                attacked_volume["events"][0],
                **kwargs,
            )


@pytest.mark.parametrize(
    "attacker", [AlwaysEqual(), AlwaysEqualStr()], ids=("object", "str-subclass")
)
def test_mutated_resealed_u3_and_u4_cannot_use_equality_as_external_hash_authority(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    attacker: object,
) -> None:
    mutated_evidence = copy.deepcopy(evidence_ledger)
    mutated_evidence["entries"][0]["statement"] = "attacker-controlled replacement"
    mutated_evidence = rehash_artifact(mutated_evidence)
    resealed_volume = copy.deepcopy(valid_volume)
    resealed_volume["evidence_artifact_sha256"] = canonical_sha256(mutated_evidence)
    resealed_volume["evidence_content_sha256"] = mutated_evidence["content_sha256"]
    resealed_volume = rehash_artifact(resealed_volume)
    kwargs = authority_kwargs(mutated_evidence, relation_refs)
    kwargs["expected_evidence_artifact_sha256"] = attacker

    with pytest.raises(WorldVolumeError):
        validate_world_volume(resealed_volume, **kwargs)


def test_relation_record_hash_rejects_equality_overriding_str_subclass(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    attacked = copy.deepcopy(relation_refs)
    record_hash = attacked[RELATION_KEYS[0]]["record_sha256"]
    assert isinstance(record_hash, str)
    attacked[RELATION_KEYS[0]]["record_sha256"] = AlwaysEqualStr(record_hash)
    assert canonical_sha256(attacked) == RELATION_REFS_SHA256

    with pytest.raises(WorldVolumeError):
        validate_world_volume(
            valid_volume,
            **authority_kwargs(evidence_ledger, attacked),
        )


def test_relation_registry_keys_reject_hash_and_equality_overriding_aliases(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    attacked: dict[str, dict[str, object]] = {}
    for index, lookup in enumerate(RELATION_KEYS):
        serialized = RELATION_KEYS[index - 1]
        attacked[RelationKeyAlias(serialized, lookup)] = copy.deepcopy(
            relation_refs[lookup]
        )
    assert len(attacked) == len(RELATION_KEYS)
    assert all(attacked[key] == relation_refs[key] for key in RELATION_KEYS)
    assert canonical_sha256(attacked) == RELATION_KEY_ALIAS_SHA256
    kwargs = authority_kwargs(evidence_ledger, attacked)
    kwargs["expected_relation_refs_sha256"] = RELATION_KEY_ALIAS_SHA256

    with pytest.raises(WorldVolumeError):
        validate_world_volume(valid_volume, **kwargs)


@pytest.mark.parametrize("role", ("relation-kind", "record-value"))
def test_relation_authority_nested_strings_require_native_json(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    role: str,
) -> None:
    attacked = copy.deepcopy(relation_refs)
    authority = attacked[RELATION_KEYS[0]]
    if role == "relation-kind":
        value = authority["relation_kind"]
        authority["relation_kind"] = AlwaysEqualStr(value)
    else:
        value = authority["record"]["actual_participation"]
        authority["record"]["actual_participation"] = AlwaysEqualStr(value)
    assert canonical_sha256(attacked) == RELATION_REFS_SHA256

    with pytest.raises(WorldVolumeError):
        validate_world_volume(
            valid_volume,
            **authority_kwargs(evidence_ledger, attacked),
        )


def test_mutated_rehashed_u3_artifact_is_still_rejected(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    stale = copy.deepcopy(evidence_ledger)
    stale["entries"][0]["statement"] = "replacement statement"
    stale = rehash_artifact(stale)
    with pytest.raises(WorldVolumeError):
        validate(valid_volume, stale, relation_refs)


def test_swapped_upstream_content_and_artifact_roles_are_rejected(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    swapped = copy.deepcopy(valid_volume)
    swapped["evidence_artifact_sha256"] = EVIDENCE_CONTENT_SHA256
    swapped["evidence_content_sha256"] = EVIDENCE_ARTIFACT_SHA256
    swapped = rehash_artifact(swapped)
    with pytest.raises(WorldVolumeError):
        validate(swapped, evidence_ledger, relation_refs)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "wrong-kind", "wrong-record-hash"])
def test_relation_authority_is_exact_one_to_one_external_coverage(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    mutation: str,
) -> None:
    broken = copy.deepcopy(relation_refs)
    if mutation == "missing":
        broken.pop(RELATION_KEYS[-1])
    elif mutation == "extra":
        broken["OPAQUE-EXTRA"] = copy.deepcopy(broken[RELATION_KEYS[0]])
    elif mutation == "duplicate":
        broken[RELATION_KEYS[-1]] = copy.deepcopy(broken[RELATION_KEYS[0]])
    elif mutation == "wrong-kind":
        broken[RELATION_KEYS[0]]["relation_kind"] = "Rcc"
    else:
        broken[RELATION_KEYS[0]]["record_sha256"] = "a" * 64
    kwargs = authority_kwargs(evidence_ledger, broken)
    kwargs["expected_relation_refs_sha256"] = canonical_sha256(broken)
    with pytest.raises(WorldVolumeError):
        validate_world_volume(valid_volume, **kwargs)


def test_relation_registry_cannot_replace_a_record_and_self_rehash(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    broken = copy.deepcopy(relation_refs)
    record = broken[RELATION_KEYS[1]]["record"]
    assert isinstance(record, dict)
    record["actual_participation"] = "replacement participation"
    broken[RELATION_KEYS[1]]["record_sha256"] = canonical_sha256(record)
    kwargs = authority_kwargs(evidence_ledger, broken)
    kwargs["expected_relation_refs_sha256"] = canonical_sha256(broken)
    with pytest.raises(WorldVolumeError):
        validate_world_volume(valid_volume, **kwargs)


def test_relation_registry_cannot_rename_all_keys_and_reseal_the_volume(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    renamed = {
        f"OPAQUE-RENAMED-{index:02d}": copy.deepcopy(relation_refs[old_key])
        for index, old_key in enumerate(RELATION_KEYS, start=1)
    }
    replacements = dict(zip(RELATION_KEYS, renamed, strict=True))
    resealed = copy.deepcopy(valid_volume)
    for distribution in resealed["local_distributions"]:
        location_ref = distribution["location_ref"]
        if location_ref in replacements:
            distribution["location_ref"] = replacements[location_ref]
    for event in resealed["events"]:
        for update in event["relation_updates"]:
            update["relation_ref"] = replacements[update["relation_ref"]]
    resealed = rehash_artifact(resealed)
    with pytest.raises(WorldVolumeError):
        validate_world_volume(
            resealed,
            **authority_kwargs(evidence_ledger, renamed),
        )


def test_membership_coverage_uses_actor_circle_and_role_not_an_invented_id(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    assert all("membership_id" not in record for record in valid_volume["memberships"])
    broken = copy.deepcopy(valid_volume)
    broken["positions"][1]["role_id"] = "ROLE-NOT-IN-RAC"
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize(
    ("location", "field", "replacement"),
    [
        (("actors", 0, "evidence_status"), "source_lineage", ["EVIDENCE-MISSING"]),
        (("channels", 0), "evidence_ids", ["EVIDENCE-MISSING"]),
        (("channels", 0, "acl"), "authorization_evidence_ids", ["EVIDENCE-MISSING"]),
        (("events", 0, "channel_conditions", 1), "evidence_ids", ["EVIDENCE-MISSING"]),
    ],
)
def test_all_represented_channel_and_condition_evidence_resolves_u3(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    location: tuple[object, ...],
    field: str | None,
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    cursor: Any = broken
    for key in location:
        cursor = cursor[key]
    assert field is not None
    cursor[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_user_claim_lineage_cannot_be_promoted_to_observed(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
) -> None:
    broken = copy.deepcopy(valid_volume)
    for record in (
        broken["circles"][2],
        broken["positions"][2],
        broken["memberships"][2],
    ):
        record["evidence_status"]["status"] = "observed"
        record["evidence_status"]["information_identity"] = "observed"
    broken = rehash_artifact(broken)
    broken_relations = make_relation_refs(broken)
    kwargs = authority_kwargs(evidence_ledger, broken_relations)
    kwargs["expected_relation_refs_sha256"] = canonical_sha256(broken_relations)
    with pytest.raises(WorldVolumeError):
        validate_world_volume(broken, **kwargs)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("positions", 0, "actor_id"), "ACTOR-MISSING"),
        (("positions", 0, "circle_id"), "CIRCLE-MISSING"),
        (("positions", 0, "role_id"), "ROLE-MISSING"),
        (("channels", 0, "to_position_id"), "POS-MISSING"),
        (("clocks", 0, "scope_id"), "SCOPE-MISSING"),
        (("unknowns", 0, "location_ref"), "LOCATION-MISSING"),
        (("residuals", 0, "location_ref"), "LOCATION-MISSING"),
    ],
)
def test_all_local_endpoints_scopes_and_locations_resolve(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    path: tuple[object, ...],
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    cursor: Any = broken
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("source_circle_ref", "CIRCLE-MISSING"),
        ("target_circle_ref", "CIRCLE-MISSING"),
        ("channel", "CHANNEL-MISSING"),
        ("channel", "CHANNEL-TEAM-SELF"),
        ("evidence_refs", ["EVIDENCE-MISSING"]),
    ],
)
def test_rcc_endpoint_channel_and_evidence_resolve_external_world_authority(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken["circle_relations"][0][field] = replacement
    broken = rehash_artifact(broken)
    broken_relations = make_relation_refs(broken)
    kwargs = authority_kwargs(evidence_ledger, broken_relations)
    kwargs["expected_relation_refs_sha256"] = canonical_sha256(broken_relations)
    with pytest.raises(WorldVolumeError):
        validate_world_volume(broken, **kwargs)


@pytest.mark.parametrize(
    ("distribution_index", "replacement"),
    [
        (0, "CHANNEL-TEAM-SELF"),
        (3, "POS-FAMILY-MEMBER"),
        (1, "RELATION-AUTHORITY-02"),
        (4, "PSI-POS-TEAM"),
        (5, "M-POS-ASSOCIATION"),
    ],
)
def test_distribution_kind_resolves_only_exact_rac_q_m_or_psi_location(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    distribution_index: int,
    replacement: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken["local_distributions"][distribution_index]["location_ref"] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize(
    "constraint_distribution",
    ["DIST-MISSING", "DIST-POWER-TEAM"],
)
def test_each_channel_and_constraint_distribution_are_exactly_bidirectional(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    constraint_distribution: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken["channels"][0]["constraint_distribution"] = constraint_distribution
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize(
    ("target", "field", "replacement"),
    [
        ("identity", "source_k_ref", "POS-FAMILY-MEMBER"),
        ("acl", "authorized_position_ids", ["POS-ASSOCIATION-DELEGATE"]),
    ],
)
def test_threshold_false_channel_still_requires_static_k_and_acl_authority(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    target: str,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    channel = broken["channels"][1]
    record = channel["identity_mapping"] if target == "identity" else channel["acl"]
    record[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize("mutation", ["missing-ancestor", "extra-ancestor", "cycle", "missing-circle", "duplicate-edge"])
def test_containment_closure_is_recomputed_with_multi_parent_support(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    mutation: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    if mutation == "missing-ancestor":
        broken["containment_closure"][2]["ancestor_circle_ids"].pop()
    elif mutation == "extra-ancestor":
        broken["containment_closure"][0]["ancestor_circle_ids"].append("CIRCLE-FAMILY")
    elif mutation == "cycle":
        broken["containment_relations"].append(
            {"child_circle_id": "CIRCLE-FAMILY", "parent_circle_id": "CIRCLE-TEAM", "basis": "成员"}
        )
    elif mutation == "missing-circle":
        broken["containment_closure"].pop(0)
    else:
        broken["containment_relations"].append(copy.deepcopy(broken["containment_relations"][0]))
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize(
    ("section", "index", "field", "replacement"),
    [
        ("channels", 0, "active", False),
        ("channels", 0, "from_position_id", "POS-FAMILY-MEMBER"),
        ("channels", 0, "evidence_ids", []),
        ("events", 0, "target_volume_id", "OMEGA-OTHER"),
    ],
)
def test_event_path_revalidates_static_channel_and_target_authority(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    section: str,
    index: int,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken[section][index][field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize(
    ("target", "field", "replacement"),
    [
        ("condition", "identity_preserved", False),
        ("condition", "acl_authorized", False),
        ("condition", "evidence_ids", ["EVIDENCE-INTERVIEW-ONE"]),
        ("channel", "evidence_ids", ["EVIDENCE-INTERVIEW-ONE"]),
        ("acl", "authorized_position_ids", ["POS-ASSOCIATION-DELEGATE"]),
        ("identity", "preserves_identity", False),
        ("identity", "source_k_ref", "POS-FAMILY-MEMBER"),
    ],
)
def test_channel_execution_revalidates_threshold_identity_acl_and_evidence(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    target: str,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    if target == "condition":
        record = broken["events"][0]["channel_conditions"][1]
    elif target == "channel":
        record = broken["channels"][0]
    elif target == "acl":
        record = broken["channels"][0]["acl"]
    else:
        record = broken["channels"][0]["identity_mapping"]
    record[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


@pytest.mark.parametrize("mutation", ["missing-condition", "extra-condition", "duplicate-condition", "missing-channel-id"])
def test_event_channel_ids_and_conditions_are_exactly_one_to_one(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    mutation: str,
) -> None:
    broken = copy.deepcopy(valid_volume)
    event = broken["events"][0]
    if mutation == "missing-condition":
        event["channel_conditions"].pop(0)
    elif mutation == "extra-condition":
        extra = copy.deepcopy(event["channel_conditions"][1])
        extra["channel_id"] = "CHANNEL-NOT-IN-EVENT"
        event["channel_conditions"].append(extra)
    elif mutation == "duplicate-condition":
        event["channel_conditions"].append(copy.deepcopy(event["channel_conditions"][1]))
    else:
        event["channel_ids"].pop(0)
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_event_updates_only_positions_reachable_over_its_valid_channel(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    event = valid_volume["events"][0]
    result = apply_event(
        valid_volume,
        event,
        **authority_kwargs(evidence_ledger, relation_refs),
    )
    assert result == StateDiff(
        source_volume_sha256=WORLD_ARTIFACT_SHA256,
        event_id="WORLD-EVENT-LOCAL",
        changed_positions=("POS-TEAM-MANAGER",),
        unchanged_positions=("POS-FAMILY-MEMBER", "POS-ASSOCIATION-DELEGATE"),
        changed_relations=(),
        advanced_clocks=("CLOCK-INTERACTION",),
        inherited_unknown_ids=("UNKNOWN-ADAPTATION",),
        inherited_residual_ids=("RESIDUAL-PEER-EFFECT",),
    )


def test_all_invalid_channels_allow_only_a_true_noop(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    invalid_updates = copy.deepcopy(valid_volume)
    invalid_updates["events"][0]["channel_conditions"][1]["threshold_met"] = False
    invalid_updates = rehash_artifact(invalid_updates)
    with pytest.raises(WorldVolumeError):
        validate(invalid_updates, evidence_ledger, relation_refs)

    noop = copy.deepcopy(invalid_updates)
    event = noop["events"][0]
    event["M_updates"] = []
    event["clock_deltas"] = []
    noop = rehash_artifact(noop)
    noop_relations = make_relation_refs(noop)
    result = apply_event(
        noop,
        noop["events"][0],
        **authority_kwargs(evidence_ledger, noop_relations),
    )
    assert result.changed_positions == ()
    assert result.unchanged_positions == (
        "POS-FAMILY-MEMBER",
        "POS-TEAM-MANAGER",
        "POS-ASSOCIATION-DELEGATE",
    )
    assert result.advanced_clocks == ()


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("state_id",), "M-POS-FAMILY"),
        (("position_id",), "POS-FAMILY-MEMBER"),
        (("via_channel_id",), "CHANNEL-TEAM-ASSOCIATION"),
        (("variable_changes", 0, "source_value"), 999),
        (("variable_changes", 0, "unit"), "percent"),
        (("variable_changes", 0, "clock_id"), "CLOCK-IMMEDIATE"),
        (("variable_changes", 0, "name"), "missing-variable"),
    ],
)
def test_state_updates_match_real_local_source_state(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    path: tuple[object, ...],
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    cursor: Any = broken["events"][0]["M_updates"][0]
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_relation_update_resolves_only_the_external_opaque_ref(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    volume = copy.deepcopy(valid_volume)
    relation_record = relation_refs[RELATION_KEYS[1]]["record"]
    assert isinstance(relation_record, dict)
    volume["events"][0]["relation_updates"] = [
        {
            "relation_kind": "Rac",
            "relation_ref": RELATION_KEYS[1],
            "field_name": "actual_participation",
            "source_value": relation_record["actual_participation"],
            "target_value": "reviewed current participation",
            "via_channel_id": "CHANNEL-TEAM-SELF",
        }
    ]
    volume = rehash_artifact(volume)
    volume_relations = make_relation_refs(volume)
    result = apply_event(
        volume,
        volume["events"][0],
        **authority_kwargs(evidence_ledger, volume_relations),
    )
    assert result.changed_relations == (RELATION_KEYS[1],)


def test_relation_update_validates_the_prospective_typed_record_and_locality(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    broken = copy.deepcopy(valid_volume)
    relation_record = relation_refs[RELATION_KEYS[1]]["record"]
    assert isinstance(relation_record, dict)
    broken["events"][0]["relation_updates"] = [
        {
            "relation_kind": "Rac",
            "relation_ref": RELATION_KEYS[1],
            "field_name": "circle_ref",
            "source_value": relation_record["circle_ref"],
            "target_value": "CIRCLE-MISSING",
            "via_channel_id": "CHANNEL-TEAM-SELF",
        }
    ]
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_every_changed_state_variable_requires_its_declared_clock_delta(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken["events"][0]["clock_deltas"] = []
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_relation_only_position_requires_an_advanced_local_clock(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    broken = copy.deepcopy(valid_volume)
    event = broken["events"][0]
    relation_record = relation_refs[RELATION_KEYS[1]]["record"]
    assert isinstance(relation_record, dict)
    event["M_updates"] = []
    event["Psi_updates"] = []
    event["relation_updates"] = [
        {
            "relation_kind": "Rac",
            "relation_ref": RELATION_KEYS[1],
            "field_name": "actual_participation",
            "source_value": relation_record["actual_participation"],
            "target_value": "reviewed current participation",
            "via_channel_id": "CHANNEL-TEAM-SELF",
        }
    ]
    event["clock_deltas"] = []
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_relation_only_position_accepts_one_externally_declared_local_clock(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    volume = copy.deepcopy(valid_volume)
    event = volume["events"][0]
    relation_record = relation_refs[RELATION_KEYS[1]]["record"]
    assert isinstance(relation_record, dict)
    event["M_updates"] = []
    event["Psi_updates"] = []
    event["relation_updates"] = [
        {
            "relation_kind": "Rac",
            "relation_ref": RELATION_KEYS[1],
            "field_name": "actual_participation",
            "source_value": relation_record["actual_participation"],
            "target_value": "reviewed current participation",
            "via_channel_id": "CHANNEL-TEAM-SELF",
        }
    ]
    event["clock_deltas"] = [
        {"clock_id": "CLOCK-INTERACTION", "delta": "PT1H"}
    ]
    volume = rehash_artifact(volume)
    result = apply_event(
        volume,
        volume["events"][0],
        **authority_kwargs(evidence_ledger, relation_refs),
    )
    assert result.changed_positions == ("POS-TEAM-MANAGER",)
    assert result.changed_relations == (RELATION_KEYS[1],)
    assert result.advanced_clocks == ("CLOCK-INTERACTION",)


def test_rcc_counterexamples_resolve_the_sealed_runtime_evidence_authority(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
) -> None:
    broken = copy.deepcopy(valid_volume)
    broken["circle_relations"][0]["counterexample_refs"] = ["EVIDENCE-MISSING"]
    broken = rehash_artifact(broken)
    broken_relations = make_relation_refs(broken)
    kwargs = authority_kwargs(evidence_ledger, broken_relations)
    kwargs["expected_relation_refs_sha256"] = canonical_sha256(broken_relations)
    with pytest.raises(WorldVolumeError):
        validate_world_volume(broken, **kwargs)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("relation_kind", "Rcc"),
        ("relation_ref", "RAC-ACTOR-ONE-CIRCLE-TEAM"),
        ("field_name", "missing-field"),
        ("source_value", "stale participation"),
        ("via_channel_id", "CHANNEL-TEAM-ASSOCIATION"),
    ],
)
def test_relation_update_rejects_stale_or_invented_authority(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(valid_volume)
    relation_record = relation_refs[RELATION_KEYS[1]]["record"]
    assert isinstance(relation_record, dict)
    update = {
        "relation_kind": "Rac",
        "relation_ref": RELATION_KEYS[1],
        "field_name": "actual_participation",
        "source_value": relation_record["actual_participation"],
        "target_value": "reviewed current participation",
        "via_channel_id": "CHANNEL-TEAM-SELF",
    }
    update[field] = replacement
    broken["events"][0]["relation_updates"] = [update]
    broken = rehash_artifact(broken)
    with pytest.raises(WorldVolumeError):
        validate(broken, evidence_ledger, relation_refs)


def test_apply_event_requires_exact_frozen_model_authored_event(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    event = copy.deepcopy(valid_volume["events"][0])
    event["event_id"] = "MODEL-DID-NOT-AUTHOR-THIS"
    with pytest.raises(WorldVolumeError):
        apply_event(
            valid_volume,
            event,
            **authority_kwargs(evidence_ledger, relation_refs),
        )


def test_apply_event_rejects_non_native_event_string_even_when_text_matches(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    event = copy.deepcopy(valid_volume["events"][0])
    event["event_id"] = AlwaysEqualStr(event["event_id"])
    with pytest.raises(WorldVolumeError):
        apply_event(
            valid_volume,
            event,
            **authority_kwargs(evidence_ledger, relation_refs),
        )


def reverse_mapping_key_order(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: reverse_mapping_key_order(item)
            for key, item in reversed(tuple(value.items()))
        }
    if isinstance(value, list):
        return [reverse_mapping_key_order(item) for item in value]
    return copy.deepcopy(value)


def test_key_order_is_deterministic_and_validate_apply_never_mutate_inputs(
    valid_volume: dict[str, Any],
    evidence_ledger: dict[str, Any],
    relation_refs: dict[str, dict[str, object]],
) -> None:
    reordered_volume = reverse_mapping_key_order(valid_volume)
    reordered_evidence = reverse_mapping_key_order(evidence_ledger)
    reordered_relations = reverse_mapping_key_order(relation_refs)
    assert isinstance(reordered_volume, dict)
    assert isinstance(reordered_evidence, dict)
    assert isinstance(reordered_relations, dict)
    before = copy.deepcopy(
        (reordered_volume, reordered_evidence, reordered_relations)
    )
    validate_world_volume(
        reordered_volume,
        **authority_kwargs(reordered_evidence, reordered_relations),
    )
    result = apply_event(
        reordered_volume,
        reordered_volume["events"][0],
        **authority_kwargs(reordered_evidence, reordered_relations),
    )
    assert result.source_volume_sha256 == WORLD_ARTIFACT_SHA256
    assert (reordered_volume, reordered_evidence, reordered_relations) == before
