from __future__ import annotations

import copy
from dataclasses import fields
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Mapping, get_type_hints

from tests.pytest_import_guard import pytest
from jsonschema import ValidationError


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.errors import UltraSchemaError
from ultra_runtime.schemas import (
    compute_artifact_content_sha256,
    validate_phase_artifact,
)
from ultra_runtime import transformations as runtime


RUN_ID = "ultra-world-fixture-run"
EVIDENCE_ARTIFACT_SHA256 = (
    "b2e92cdb80bc8c497b8d215ac490a418d68c7142484f6af0f073c18df8794981"
)
WORLD_ARTIFACT_SHA256 = (
    "29b324b8f6d3596b2e9df7c1d23adfd9f17fcd5b55a7f73113a09ebd292f6ce5"
)
RELATION_REFS_SHA256 = (
    "cd8b59e7c3877cb26c778f2a41d7dba6604e1288d54b7aa846292bcbdf5ab60a"
)
RAC_ONLY_RELATION_REFS_SHA256 = (
    "149f998f82aa28ea1913ace1ab39f4a223adad019ff1359e14f8b0869650cb7f"
)
TRANSFORMATION_CONTENT_SHA256 = (
    "7b8cd6d0e45d8adb807667cc4e768206890661f7fb8484eb012ed7ea01e68208"
)
TRANSFORMATION_ARTIFACT_SHA256 = (
    "196e169890e2900713d0a9b42d46779ea59e2c26faf6f542cc7a9269c72abe1c"
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
AXES = ("A", "X", "T", "O", "C", "R", "I", "N", "J")
RELATION_KEYS = tuple(f"RELATION-AUTHORITY-{index:02d}" for index in range(1, 6))


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


class EqualityOverridingTextStr(str):
    def __eq__(self, other: object) -> bool:
        return str.__eq__(self, other)

    def __ne__(self, other: object) -> bool:
        return str.__ne__(self, other)

    __hash__ = str.__hash__


def test_transformation_public_introspection_contract_is_frozen() -> None:
    authority_fields = (
        "world_volume_artifact_sha256",
        "normalized_states",
        "comparator_results",
        "verification_artifacts",
        "comparison_payloads",
        "j_authorization_tuples",
        "independent_reviews",
    )
    assert tuple(field.name for field in fields(runtime.TransformationAuthorities)) == (
        authority_fields
    )

    positional = inspect.Parameter.POSITIONAL_OR_KEYWORD
    keyword_only = inspect.Parameter.KEYWORD_ONLY
    constructor_parameters = tuple(
        inspect.signature(runtime.TransformationAuthorities).parameters.values()
    )
    assert tuple(parameter.name for parameter in constructor_parameters) == authority_fields
    assert all(parameter.kind is positional for parameter in constructor_parameters)
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in constructor_parameters
    )
    expected_signatures = {
        runtime.validate_transformations: (
            ("document", positional),
            ("source_volume", keyword_only),
            ("evidence_ledger", keyword_only),
            ("expected_run_id", keyword_only),
            ("expected_version_binding", keyword_only),
            ("expected_evidence_artifact_sha256", keyword_only),
            ("expected_world_volume_artifact_sha256", keyword_only),
            ("relation_refs", keyword_only),
            ("expected_relation_refs_sha256", keyword_only),
            ("authorities", keyword_only),
            ("expected_authorities_sha256", keyword_only),
        ),
        runtime.validate_cascade: (
            ("cascade", positional),
            ("volume", positional),
            ("evidence_ledger", keyword_only),
            ("expected_run_id", keyword_only),
            ("expected_version_binding", keyword_only),
            ("expected_evidence_artifact_sha256", keyword_only),
            ("relation_refs", keyword_only),
            ("expected_relation_refs_sha256", keyword_only),
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
    assert get_type_hints(runtime.validate_cascade)["return"] == tuple[str, ...]


AUTHORITY_HASHES = {
    "valid": "778cf8191f4e83bfad8547717c2fa9bfd9306e7448d4d4921f68ff01053e8fd3",
    "unknown": "706021f38274ae31b4ea4c7fa5a968a11feb44ee53ad6ffab602a82d2e0c8358",
    "bilateral-na": "1d3b3a833f86f78d411e6546fa9466814e04d3e198ab9363fd7ebfb3cd5a1b71",
    "bilateral-na-mismatch": "01649b9d63076cd50ac574ebf139b7b38e79c6e4b683e4cd9c62a804a4d5e6a8",
    "j-expand": "8e3b030623e371341edf161c64902035b13091f0a2a21ee05f646cd03f7666d7",
    "j-review-invalid": "59b472c886ed206370cf696bab8879bdf78f10c30576be7dcecda9e13d34a4a2",
    "j-diff-stale": "3e6300e650890980aa3702371122dede11fa7b204f02a795935c0d360362149e",
    "j-cartesian": "61cb5e8edc10f6b93f4274b977a02c652a1c20be0045245153227f98ca9b4e54",
    "false-expand": "bcc949a22e54663e22163345429918d256e671c63a6948ed65dcaac2431c9976",
    "u4-mismatch": "6a317a596a852cfed87c23cfca56be95fb4f7429bf633c9e2a70cd48208315df",
    "normalized-state-hash-mismatch": "45802274d0e4c01bc918b219f73cfdaa0c715a5e73a7fd9b1516dd01f43237f2",
    "payload-hash-mismatch": "f273e96ff43fab12077badb055b9a96093baf46e7a064aca2b8e598fb1843d8a",
    "verification-chain-mismatch": "352577237efedffe2a8cf453ed4e014008ec14dab4a25705a93f6f707e81234b",
    "j-unilateral-na": "f25a292d0adf4bd78b8019293c25cf19da8ac68dc7c29f5884a3449dbea6a1ac",
    "j-set-equal": "716becc582f797a6f0e2c46e09bcf9e5e42275dcdd9c87dafa82d9f8f7ee2254",
    "j-permutation": "d7fe9673b0ab16b4df2a1c58e75467315523f1e90dc34b8e028f2e2e7512a4df",
    "j-validity-forever": "a440e572cb16d1023e5577036a5cd602b2d7a24557fc8827f0dd9a4107347975",
    "j-empty-revocations": "5455001ee6d3c399d527f151f49fc8c5794258569a151c9a58e6a59d1b214538",
    "j-shared-review": "23bcb66eb5b8f60eab448db4661e5720759ed931b878c0b238fdad5c841ef547",
    "j-self-review": "2b84f096751d67f492f47734da52d6c85ff083c23233a2ce03fa05c051e25bae",
    "j-empty-review-evidence": "8f8f6c490b13bee7c11cbbb4e39f3fecdb09046a4da39fc88d309770c3c0a0be",
    "deep-equality-false": "ef3c938502ba8d442839e710b1b3de1cf0d6a6b097e4333dd0e459aa84896285",
    "deep-equality-swapped-refs": "1641402c6f1a4ed2733bc70c9c568b44651be51d0ead33137fcdfca9882994f9",
    "deep-equality-stale-hashes": "1daa7cfb4673143b70df524cc5b9869e900457de15b917725aaa0f45ca45b9b9",
    "deep-equality-unequal-equal": "779dbf7ea8fb63091bbbac90531c640ba261988a04ab1be3bcf76d9ee7cb3b06",
    "deep-equality-unequal-expands": "64b05d38091005cf8febb4b6759859485a9a5f199af33670f3d4f3dee82e1b7f",
}
NONFLATTENING_HASHES = {
    "component-cross-duplicate": (
        "49cd7cd2b98e597aab4326f9675dfcc21e31c1c21ef69f26be5cdb70de3d506c",
        "9943ee324468661788b002032e7553cb1232a880251f5df1235e9899e976b527",
    ),
    "component-within-duplicate": (
        "b35225c7990e94c3c06cedd906613f69dfa69c2067e569ed81062e92f403fba3",
        "16d08041676c03ab4f46e26a5efce6350eb2c1bf5a8799dd76f307e06d6e767d",
    ),
    "variable-duplicate": (
        "6d88d703e414d3350b6f17678d97609f1d090ccb57e07d48392a8151104f08fa",
        "27b3a9dc3e4b64204cd963228dbfdafbbdffc4c1336033cdcd30ed28203a9e85",
    ),
    "condition-duplicate": (
        "c01154caa67adc39385c06a6c27664de0b32fa7a2661c7331bbe15905b8c5449",
        "f5d1ec0984935e9c3ef7f87676b1fa982844f52614263e1912f4142caa26210b",
    ),
    "effect-empty-refs": (
        "58315efc85577d4f03da012bd78f45a3720b4a3a704d2be23e8a9e4a9e37bf60",
        "9f9a78ef440879d0eddab5220871d9d67d8629c54ecbe7c6601d1207c5b8584b",
    ),
    "effect-unknown-refs": (
        "fcf0339570f4b0dfb9a02ae8d1140d28f423527a052a6c9570b276c3b94f5fee",
        "91bbdf56efe619945d8f0ca54180afdc4895dcbe7ff68ab9c365b60bb7dfa296",
    ),
    "effect-duplicate-refs": (
        "20521e34bd90b8e4b911a140fc8d4994ec77ff817b8eae65f84469648b97d570",
        "dd55e1af01461acf30b482843e2eb3250cf3f36abe04a7bea48534b1ba3434f2",
    ),
    "effect-orphan-variable": (
        "229a1f1b7328a982d31d7007f59e31add821fc47c6a2ed366188ac64635e569c",
        "fea7091073528f9b6620483947e857a1e2a3de83d14d05a78044195e5f12ddd5",
    ),
    "effect-cross-location": (
        "441657bbb8b3c757b93402172e7b0aed5171b1d8d63998cf451ee43ea1216863",
        "5a70db8e7cfbe9dd7047f42764436b7f3340397e0542980a8658e50f2f816665",
    ),
    "non-scale-vacuous": (
        "045d8445f1586a1fbfba297fc420e683307d9ee6a7ca9b628cc4476ebe82ea0a",
        "e45f084f5473ddcf19eef8966b43c796afcbecfd4e17f8faf4f44775fd274b1a",
    ),
}
PARTIAL_ORDER_HASHES = {
    "bidirectional-conflict": {
        "authority": "f32e51d906e729bac194b8ed13e7036353aba5170112667e284b4993082237c6",
        "content": "506b8b8bccd3a245988e50a22ab2cd0609eda54b89c05dfa30c224ebac38b978",
        "artifact": "2c422365d682c59cb052ebb570db571ca6edf0616da0458c61ee696ccca32a43",
    },
    "transitivity-conflict": {
        "authority": "2522cbddf49f841ac11bbae674594205b2dca48ca18dbc3c7ccfdeb4cd5b846b",
        "content": "22dee824c1981d31d69865364f735bee60deeb1f3d42ea99e2fa0dc3e53e9c76",
        "artifact": "c97a353724112448a193799d0c3ffac799213ed36c245fbe80fc66b3e488ffc8",
    },
    "version-witness-conflict": {
        "authority": "d450bd2b1e0fdfc32cff8a8163d44c8c08fb5e95be9c91f7fe4e003452e474a0",
        "content": "182e9905bc17dd6511aeed82fc99851e7b4f61c636ca727b53ea62432f23ab60",
        "artifact": "ccbf44617807a19597e57b5bf1e62300ae3a2a4b4b0e4e08e9d7eb073d6bb8d5",
    },
    "auxiliary-mapping-conflict": {
        "authority": "276eae2a1651058db6fbbcfe23d0dc60c5ce02ec9401eb582a4bf178febce3eb",
        "content": "e6b0dfc4d1afe31a1240b2b755799494677e3a0a575d4a0de0d8820eb448d41b",
        "artifact": "85f3f82bca1f77262b561e5527df8934a2d896dffa3b9704e911e4071e86a9f6",
    },
}


def load_fixture(name: str) -> dict[str, Any]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def rehash_artifact(value: Mapping[str, object]) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(value))
    snapshot["content_sha256"] = compute_artifact_content_sha256(snapshot)
    return snapshot


def relation_authority(world: Mapping[str, object]) -> dict[str, dict[str, object]]:
    records = [
        *(("Rac", record) for record in world["memberships"]),
        *(("Rcc", record) for record in world["circle_relations"]),
    ]
    assert len(records) <= len(RELATION_KEYS)
    return {
        key: {
            "relation_kind": relation_kind,
            "record_sha256": canonical_sha256(record),
            "record": copy.deepcopy(record),
        }
        for key, (relation_kind, record) in zip(
            RELATION_KEYS[: len(records)], records, strict=True
        )
    }


def authorization_tuple(
    *,
    source_ref: str,
    subject_ref: str,
    object_ref: str,
    action_ref: str,
    jurisdiction: str,
    evidence_refs: list[str],
    review_ref: str,
) -> dict[str, object]:
    return {
        "source_ref": source_ref,
        "decision_subject_ref": subject_ref,
        "object_ref": object_ref,
        "action_ref": action_ref,
        "jurisdiction": jurisdiction,
        "validity_period": {
            "start_time": "2026-08-01T00:00:00Z",
            "end_time": None,
        },
        "revocation_conditions": ["the named authority is revoked"],
        "evidence_refs": evidence_refs,
        "independent_review_ref": review_ref,
    }


def tuple_authority(tuple_value: Mapping[str, object]) -> dict[str, object]:
    return {
        "authorization_tuple": copy.deepcopy(dict(tuple_value)),
        "authorization_tuple_sha256": canonical_sha256(tuple_value),
        "normalization_status": "normalized",
        "validity_status": "valid",
    }


def make_authority_payload(
    world: Mapping[str, object],
    *,
    variant: str = "valid",
) -> dict[str, object]:
    transform_id = "TRANSFORM-SCALE-PRIMARY"
    location_ref = "POS-TEAM-MANAGER"
    position = next(
        record for record in world["positions"] if record["position_id"] == location_ref
    )
    profile = position["scale_profile"]
    tuples: list[dict[str, object]] = []
    reviews: dict[str, dict[str, object]] = {}
    source_j_hashes: list[str] = []
    target_j_hashes: list[str] = []
    j_tuple_variants = {
        "j-expand",
        "j-review-invalid",
        "j-diff-stale",
        "j-cartesian",
        "j-set-equal",
        "j-permutation",
        "j-validity-forever",
        "j-empty-revocations",
        "j-shared-review",
        "j-self-review",
        "j-empty-review-evidence",
    }
    if variant in j_tuple_variants:
        tuple_one = authorization_tuple(
            source_ref="EVIDENCE-ROSTER-ATLAS",
            subject_ref=location_ref,
            object_ref="CIRCLE-TEAM",
            action_ref="ACTION-ALLOCATE-BUDGET",
            jurisdiction="Atlas manager mandate",
            evidence_refs=["EVIDENCE-ROSTER-ATLAS"],
            review_ref="REVIEW-AUTHORITY-01",
        )
        tuple_two = authorization_tuple(
            source_ref="EVIDENCE-ASSOCIATION-CHARTER",
            subject_ref=location_ref,
            object_ref="CIRCLE-ASSOCIATION",
            action_ref="ACTION-ISSUE-BOUNDED-DELEGATION",
            jurisdiction="Association charter delegation",
            evidence_refs=["EVIDENCE-ROSTER-ATLAS", "EVIDENCE-ASSOCIATION-CHARTER"],
            review_ref="REVIEW-AUTHORITY-02",
        )
        if variant == "j-validity-forever":
            tuple_two["validity_period"] = "forever"
        elif variant == "j-empty-revocations":
            tuple_two["revocation_conditions"] = []
        elif variant == "j-shared-review":
            tuple_two["independent_review_ref"] = "REVIEW-AUTHORITY-01"
        tuples = [tuple_authority(tuple_one), tuple_authority(tuple_two)]
        tuple_hashes = sorted(record["authorization_tuple_sha256"] for record in tuples)
        if variant in {"j-set-equal", "j-permutation"}:
            source_j_hashes = list(tuple_hashes)
            target_j_hashes = list(tuple_hashes)
            if variant == "j-permutation":
                target_j_hashes.reverse()
        else:
            source_j_hashes = [tuples[0]["authorization_tuple_sha256"]]
            target_j_hashes = list(tuple_hashes)
        for index, tuple_record in enumerate(tuples, start=1):
            review_ref = tuple_record["authorization_tuple"][
                "independent_review_ref"
            ]
            review_payload = {
                "review_scope": "one normalized atomic authorization tuple",
                "review_index": index,
            }
            reviews[review_ref] = {
                "independent_review_ref": review_ref,
                "reviewer_ref": f"INDEPENDENT-REVIEWER-{index:02d}",
                "authorization_tuple_sha256": tuple_record["authorization_tuple_sha256"],
                "decision": "valid",
                "evidence_refs": list(
                    tuple_record["authorization_tuple"]["evidence_refs"]
                ),
                "review_payload": review_payload,
                "review_sha256": canonical_sha256(review_payload),
            }
        if variant == "j-review-invalid":
            reviews["REVIEW-AUTHORITY-02"]["decision"] = "invalid"
        if variant == "j-self-review":
            reviews["REVIEW-AUTHORITY-02"]["reviewer_ref"] = location_ref
        if variant == "j-empty-review-evidence":
            reviews["REVIEW-AUTHORITY-02"]["evidence_refs"] = []

    normalized_states: list[dict[str, object]] = []
    comparator_results: dict[str, dict[str, object]] = {}
    verification_artifacts: dict[str, dict[str, object]] = {}
    comparison_payloads: dict[str, dict[str, object]] = {}
    for axis_id in AXES:
        source_status = target_status = "recorded"
        source_result = target_result = "applicable"
        source_criterion: str | None = f"APPLICABILITY-SCALE-PRIMARY-{axis_id}"
        target_criterion: str | None = source_criterion
        source_ref: str | None = f"NSTATE-SCALE-PRIMARY-{axis_id}-SOURCE"
        target_ref: str | None = f"NSTATE-SCALE-PRIMARY-{axis_id}-TARGET"
        source_state: dict[str, object] | None = {
            "location_ref": location_ref,
            "axis_id": axis_id,
            "value": profile[axis_id],
        }
        target_state = copy.deepcopy(source_state)
        relation = "equal"
        comparator_id = "builtin:deep-equality"
        payload_kind = "deep-equality"

        if axis_id == "J":
            assert source_state is not None and target_state is not None
            source_state["authorization_tuple_sha256s"] = list(source_j_hashes)
            target_state["authorization_tuple_sha256s"] = list(target_j_hashes)
            if variant in {
                "j-expand",
                "j-review-invalid",
                "j-diff-stale",
                "j-cartesian",
                "j-validity-forever",
                "j-empty-revocations",
                "j-shared-review",
                "j-self-review",
                "j-empty-review-evidence",
            }:
                relation = "expands"
                comparator_id = "COMPARATOR-J-AUTHORIZATION"
                payload_kind = "authorization-difference"
            elif variant == "j-permutation":
                relation = "incomparable"
                comparator_id = "COMPARATOR-J-AUTHORIZATION"
                payload_kind = "authorization-difference"
        if variant == "j-unilateral-na" and axis_id == "J":
            source_status = "not_applicable"
            source_result = "not_applicable"
            source_criterion = "APPLICABILITY-J-SOURCE-NOT-APPLICABLE"
            source_ref = None
            source_state = None
            relation = "incomparable"
            comparator_id = "COMPARATOR-J-APPLICABILITY-DOMAIN"
            payload_kind = "set"
        if variant == "unknown" and axis_id == "A":
            source_status = "unknown"
            source_result = "unknown"
            source_criterion = None
            source_ref = None
            source_state = None
            relation = "unknown"
        if variant.startswith("bilateral-na") and axis_id == "A":
            source_status = target_status = "not_applicable"
            source_result = target_result = "not_applicable"
            source_criterion = "APPLICABILITY-NOT-APPLICABLE-A"
            target_criterion = source_criterion
            if variant == "bilateral-na-mismatch":
                target_criterion = "APPLICABILITY-DIFFERENT-A"
            source_ref = target_ref = None
            source_state = target_state = None
            comparator_id = "COMPARATOR-BILATERAL-APPLICABILITY"
            payload_kind = "set"
        if variant == "false-expand" and axis_id == "A":
            relation = "expands"
            comparator_id = "COMPARATOR-FALSE-EXPANSION"
            payload_kind = "mapping"
        if variant == "u4-mismatch" and axis_id == "A":
            assert source_state is not None and target_state is not None
            source_state["value"] = "internally synchronized stale scale value"
            target_state["value"] = "internally synchronized stale scale value"

        source_sha = None if source_state is None else canonical_sha256(source_state)
        target_sha = None if target_state is None else canonical_sha256(target_state)
        normalized_states.extend(
            [
                {
                    "transform_id": transform_id,
                    "side": "source",
                    "location_ref": location_ref,
                    "axis_id": axis_id,
                    "status": source_status,
                    "applicability_criterion_id": source_criterion,
                    "applicability_result": source_result,
                    "evidence_refs": (
                        ["EVIDENCE-ROSTER-ATLAS"]
                        if source_status != "unknown"
                        else []
                    ),
                    "normalized_state_ref": source_ref,
                    "normalized_state_sha256": source_sha,
                    "normalized_state": source_state,
                },
                {
                    "transform_id": transform_id,
                    "side": "target",
                    "location_ref": location_ref,
                    "axis_id": axis_id,
                    "status": target_status,
                    "applicability_criterion_id": target_criterion,
                    "applicability_result": target_result,
                    "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
                    "normalized_state_ref": target_ref,
                    "normalized_state_sha256": target_sha,
                    "normalized_state": target_state,
                },
            ]
        )
        if relation == "unknown":
            continue

        payload_ref = f"PAYLOAD-SCALE-PRIMARY-{axis_id}"
        result_ref = f"RESULT-SCALE-PRIMARY-{axis_id}"
        verification_ref = f"VERIFY-SCALE-PRIMARY-{axis_id}"
        if payload_kind == "deep-equality":
            payload_body: dict[str, object] = {
                "source_normalized_state_ref": source_ref,
                "target_normalized_state_ref": target_ref,
                "source_normalized_state_sha256": source_sha,
                "target_normalized_state_sha256": target_sha,
                "deep_equal": True,
            }
        elif payload_kind == "authorization-difference":
            tuples_by_hash = {
                record["authorization_tuple_sha256"]: record["authorization_tuple"]
                for record in tuples
            }
            source_tuples = [
                copy.deepcopy(tuples_by_hash[tuple_hash])
                for tuple_hash in source_j_hashes
            ]
            target_tuples = [
                copy.deepcopy(tuples_by_hash[tuple_hash])
                for tuple_hash in target_j_hashes
            ]
            source_tuple_set = set(source_j_hashes)
            new_target_tuples = [
                copy.deepcopy(tuples_by_hash[tuple_hash])
                for tuple_hash in target_j_hashes
                if tuple_hash not in source_tuple_set
            ]
            if variant == "j-diff-stale":
                new_target_tuples = [copy.deepcopy(tuples[0]["authorization_tuple"])]
            if variant == "j-cartesian":
                new_target_tuples[0]["object_ref"] = [
                    "CIRCLE-TEAM",
                    "CIRCLE-ASSOCIATION",
                ]
                new_target_tuples[0]["action_ref"] = [
                    "ACTION-ALLOCATE-BUDGET",
                    "ACTION-ISSUE-BOUNDED-DELEGATION",
                ]
            payload_body = {
                "source_tuples": source_tuples,
                "target_tuples": target_tuples,
                "new_target_tuples": new_target_tuples,
            }
        elif payload_kind == "mapping":
            payload_body = {"claimed_relation": relation}
        else:
            payload_body = {"applicability_criterion_id": source_criterion}
        verification_payload = {
            "axis_id": axis_id,
            "comparison_payload_ref": payload_ref,
            "source_normalized_state_ref": source_ref,
            "target_normalized_state_ref": target_ref,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "relation": relation,
            "deep_equal": relation == "equal" and payload_kind == "deep-equality",
        }
        verification_hash = canonical_sha256(verification_payload)
        comparison_payloads[payload_ref] = {
            "payload_ref": payload_ref,
            "payload_kind": payload_kind,
            "axis_id": axis_id,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "payload": payload_body,
            "payload_sha256": canonical_sha256(payload_body),
        }
        verification_artifacts[verification_ref] = {
            "verification_artifact_ref": verification_ref,
            "verifier_id": (
                "VERIFIER-DEEP-EQUALITY"
                if comparator_id == "builtin:deep-equality"
                else "VERIFIER-AUTHORITY-COMPARISON"
            ),
            "comparator_result_ref": result_ref,
            "comparison_payload_ref": payload_ref,
            "axis_id": axis_id,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "relation": relation,
            "artifact_payload": verification_payload,
            "verification_hash": verification_hash,
        }
        comparator_results[result_ref] = {
            "comparator_result_ref": result_ref,
            "axis_id": axis_id,
            "comparator_id": comparator_id,
            "comparator_version": "1.0.0",
            "source_status": source_status,
            "target_status": target_status,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "relation": relation,
            "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
            "comparison_payload_ref": payload_ref,
            "verification_artifact_ref": verification_ref,
            "verification_hash": verification_hash,
            "validation_status": "valid",
        }

    payload = {
        "world_volume_artifact_sha256": WORLD_ARTIFACT_SHA256,
        "normalized_states": normalized_states,
        "comparator_results": comparator_results,
        "verification_artifacts": verification_artifacts,
        "comparison_payloads": comparison_payloads,
        "j_authorization_tuples": tuples,
        "independent_reviews": reviews,
    }
    if variant == "normalized-state-hash-mismatch":
        stale_hash = "a" * 64
        state = next(
            record
            for record in normalized_states
            if record["axis_id"] == "A" and record["side"] == "source"
        )
        state["normalized_state_sha256"] = stale_hash
        comparator_results["RESULT-SCALE-PRIMARY-A"]["source_state_sha256"] = stale_hash
        comparison_payloads["PAYLOAD-SCALE-PRIMARY-A"]["source_state_sha256"] = stale_hash
        verification_artifacts["VERIFY-SCALE-PRIMARY-A"]["source_state_sha256"] = stale_hash
    elif variant == "payload-hash-mismatch":
        comparison_payloads["PAYLOAD-SCALE-PRIMARY-A"]["payload_sha256"] = "b" * 64
    elif variant == "verification-chain-mismatch":
        verification_artifacts["VERIFY-SCALE-PRIMARY-A"]["artifact_payload"][
            "deep_equal"
        ] = False
    elif variant in {
        "deep-equality-false",
        "deep-equality-swapped-refs",
        "deep-equality-stale-hashes",
    }:
        comparison = comparison_payloads["PAYLOAD-SCALE-PRIMARY-A"]
        body = comparison["payload"]
        if variant == "deep-equality-false":
            body["deep_equal"] = False
        elif variant == "deep-equality-swapped-refs":
            body["source_normalized_state_ref"], body[
                "target_normalized_state_ref"
            ] = (
                body["target_normalized_state_ref"],
                body["source_normalized_state_ref"],
            )
        else:
            body["source_normalized_state_sha256"] = "a" * 64
            body["target_normalized_state_sha256"] = "b" * 64
        comparison["payload_sha256"] = canonical_sha256(body)
    elif variant in {
        "deep-equality-unequal-equal",
        "deep-equality-unequal-expands",
    }:
        target_location = "POS-FAMILY-MEMBER"
        target_position = next(
            record
            for record in world["positions"]
            if record["position_id"] == target_location
        )
        target_profile = target_position["scale_profile"]
        for axis_id in AXES:
            target = next(
                record
                for record in normalized_states
                if record["axis_id"] == axis_id and record["side"] == "target"
            )
            target["location_ref"] = target_location
            target["normalized_state"]["location_ref"] = target_location
            target["normalized_state"]["value"] = target_profile[axis_id]
            target_sha = canonical_sha256(target["normalized_state"])
            target["normalized_state_sha256"] = target_sha
            result = comparator_results[f"RESULT-SCALE-PRIMARY-{axis_id}"]
            comparison = comparison_payloads[f"PAYLOAD-SCALE-PRIMARY-{axis_id}"]
            verification = verification_artifacts[f"VERIFY-SCALE-PRIMARY-{axis_id}"]
            relation = (
                "expands"
                if variant == "deep-equality-unequal-expands" and axis_id == "A"
                else "equal"
            )
            comparison["target_state_sha256"] = target_sha
            comparison["payload"]["target_normalized_state_sha256"] = target_sha
            comparison["payload"]["deep_equal"] = relation == "equal"
            comparison["payload_sha256"] = canonical_sha256(comparison["payload"])
            result["target_state_sha256"] = target_sha
            result["relation"] = relation
            verification["target_state_sha256"] = target_sha
            verification["relation"] = relation
            verification["artifact_payload"]["target_state_sha256"] = target_sha
            verification["artifact_payload"]["relation"] = relation
            verification["artifact_payload"]["deep_equal"] = relation == "equal"
            verification["verification_hash"] = canonical_sha256(
                verification["artifact_payload"]
            )
            result["verification_hash"] = verification["verification_hash"]
    return payload


def authority_mapping(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "world_volume_artifact_sha256": payload["world_volume_artifact_sha256"],
        "normalized_states": list(payload["normalized_states"]),
        "comparator_results": dict(payload["comparator_results"]),
        "verification_artifacts": dict(payload["verification_artifacts"]),
        "comparison_payloads": dict(payload["comparison_payloads"]),
        "j_authorization_tuples": list(payload["j_authorization_tuples"]),
        "independent_reviews": dict(payload["independent_reviews"]),
    }


def make_authorities(payload: Mapping[str, object]) -> object:
    authority_type = getattr(runtime, "TransformationAuthorities", None)
    assert authority_type is not None, "TransformationAuthorities must be public"
    return authority_type(**copy.deepcopy(dict(payload)))


def replace_authority_hash_role(
    payload: dict[str, object], role: str
) -> None:
    axis_id = "A"
    if role == "world-artifact":
        record = payload
        field = "world_volume_artifact_sha256"
    elif role == "normalized-state":
        record = next(
            item
            for item in payload["normalized_states"]
            if item["axis_id"] == axis_id and item["side"] == "source"
        )
        field = "normalized_state_sha256"
    elif role == "comparator-source-state":
        record = payload["comparator_results"][f"RESULT-SCALE-PRIMARY-{axis_id}"]
        field = "source_state_sha256"
    elif role == "comparator-verification":
        record = payload["comparator_results"][f"RESULT-SCALE-PRIMARY-{axis_id}"]
        field = "verification_hash"
    elif role == "verification-source-state":
        record = payload["verification_artifacts"][f"VERIFY-SCALE-PRIMARY-{axis_id}"]
        field = "source_state_sha256"
    elif role == "verification-hash":
        record = payload["verification_artifacts"][f"VERIFY-SCALE-PRIMARY-{axis_id}"]
        field = "verification_hash"
    elif role == "payload-source-state":
        record = payload["comparison_payloads"][f"PAYLOAD-SCALE-PRIMARY-{axis_id}"]
        field = "source_state_sha256"
    elif role == "payload-hash":
        record = payload["comparison_payloads"][f"PAYLOAD-SCALE-PRIMARY-{axis_id}"]
        field = "payload_sha256"
    elif role == "deep-equality-payload-state":
        record = payload["comparison_payloads"][f"PAYLOAD-SCALE-PRIMARY-{axis_id}"][
            "payload"
        ]
        field = "source_normalized_state_sha256"
    elif role == "verification-payload-state":
        record = payload["verification_artifacts"][f"VERIFY-SCALE-PRIMARY-{axis_id}"][
            "artifact_payload"
        ]
        field = "source_state_sha256"
    else:
        raise AssertionError(f"unknown authority hash role: {role}")
    value = record[field]
    assert isinstance(value, str)
    record[field] = AlwaysEqualStr(value)


def replace_j_authority_hash_role(
    payload: dict[str, object], role: str
) -> None:
    tuple_record = payload["j_authorization_tuples"][0]
    review = next(iter(payload["independent_reviews"].values()))
    if role == "tuple-hash":
        value = tuple_record["authorization_tuple_sha256"]
        tuple_record["authorization_tuple_sha256"] = AlwaysEqualStr(value)
    elif role == "normalized-j-set":
        normalized = next(
            item
            for item in payload["normalized_states"]
            if item["axis_id"] == "J" and item["side"] == "source"
        )
        hashes = normalized["normalized_state"]["authorization_tuple_sha256s"]
        value = hashes[0]
        hashes[0] = AlwaysEqualStr(value)
    elif role == "review-tuple-hash":
        value = review["authorization_tuple_sha256"]
        review["authorization_tuple_sha256"] = AlwaysEqualStr(value)
    elif role == "review-hash":
        value = review["review_sha256"]
        review["review_sha256"] = AlwaysEqualStr(value)
    else:
        raise AssertionError(f"unknown J authority hash role: {role}")


def replace_axis_from_authority(
    document: Mapping[str, object],
    payload: Mapping[str, object],
    axis_id: str,
) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(document))
    transform = next(
        record
        for record in snapshot["transformations"]
        if record["transform_id"] == "TRANSFORM-SCALE-PRIMARY"
    )
    difference = next(
        record for record in transform["axis_differences"] if record["axis_id"] == axis_id
    )
    state_records = {
        record["side"]: record
        for record in payload["normalized_states"]
        if record["transform_id"] == transform["transform_id"]
        and record["axis_id"] == axis_id
    }
    for side in ("source", "target"):
        authority = state_records[side]
        difference[f"{side}_state"] = {
            "status": authority["status"],
            "normalized_state_ref": authority["normalized_state_ref"],
            "normalized_state_sha256": authority["normalized_state_sha256"],
            "description": f"Externally frozen {side} {axis_id} authority state.",
        }
    result_ref = f"RESULT-SCALE-PRIMARY-{axis_id}"
    result = payload["comparator_results"].get(result_ref)
    if result is None:
        difference["relation"] = "unknown"
        difference["order_witness"] = {
            "comparator_id": None,
            "comparator_version": None,
            "verifier_id": None,
            "evidence_refs": [],
            "comparison_payload": {
                "payload_kind": None,
                "payload_ref": None,
                "payload_sha256": None,
                "description": "No resolvable witness exists for the missing axis material.",
            },
            "comparator_result_ref": None,
            "verification_artifact_ref": None,
            "verification_hash": None,
            "validation_status": "missing",
        }
    else:
        payload_record = payload["comparison_payloads"][result["comparison_payload_ref"]]
        verification = payload["verification_artifacts"][
            result["verification_artifact_ref"]
        ]
        difference["relation"] = result["relation"]
        difference["order_witness"] = {
            "comparator_id": result["comparator_id"],
            "comparator_version": result["comparator_version"],
            "verifier_id": verification["verifier_id"],
            "evidence_refs": list(result["evidence_refs"]),
            "comparison_payload": {
                "payload_kind": payload_record["payload_kind"],
                "payload_ref": payload_record["payload_ref"],
                "payload_sha256": payload_record["payload_sha256"],
                "description": f"Externally frozen comparison payload for {axis_id}.",
            },
            "comparator_result_ref": result_ref,
            "verification_artifact_ref": verification["verification_artifact_ref"],
            "verification_hash": verification["verification_hash"],
            "validation_status": "valid",
        }
    relations = {record["relation"] for record in transform["axis_differences"]}
    if "incomparable" in relations:
        transform["transformation_class"] = "horizontal_or_incomparable"
    elif "expands" in relations and "contracts" in relations:
        transform["transformation_class"] = "mixed"
    elif "unknown" in relations:
        transform["transformation_class"] = "unresolved"
    elif relations == {"equal"}:
        transform["transformation_class"] = "all_equal"
    elif relations <= {"equal", "expands"}:
        transform["transformation_class"] = "elevation"
    else:
        transform["transformation_class"] = "reduction"
    return rehash_artifact(snapshot)


def replace_scale_from_authority(
    document: Mapping[str, object],
    payload: Mapping[str, object],
) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(document))
    for axis_id in AXES:
        snapshot = replace_axis_from_authority(snapshot, payload, axis_id)
    transform = next(
        record
        for record in snapshot["transformations"]
        if record["transform_id"] == "TRANSFORM-SCALE-PRIMARY"
    )
    target = next(
        record
        for record in payload["normalized_states"]
        if record["axis_id"] == "A" and record["side"] == "target"
    )
    transform["output_identity"]["location_ref"] = target["location_ref"]
    return rehash_artifact(snapshot)


def append_scale_comparison(
    document: Mapping[str, object],
    payload: Mapping[str, object],
    world: Mapping[str, object],
    *,
    transform_id: str,
    source_location: str,
    target_location: str,
    axis_relations: Mapping[str, str],
    comparator_version: str = "1.0.0",
    mapping_authority: str = "MAPPING-PARTIAL-ORDER",
) -> tuple[dict[str, Any], dict[str, object]]:
    snapshot = copy.deepcopy(dict(document))
    authority = copy.deepcopy(dict(payload))
    positions = {
        record["position_id"]: record for record in world["positions"]
    }
    source_position = positions[source_location]
    target_position = positions[target_location]
    template = next(
        record
        for record in snapshot["transformations"]
        if record["transform_id"] == "TRANSFORM-SCALE-PRIMARY"
    )
    transform = copy.deepcopy(template)
    transform["transform_id"] = transform_id
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
    ):
        transform[field] = []
    transform["input_identity"]["location_ref"] = source_location
    transform["input_identity"]["value"] = source_position["identity_criteria"]
    transform["output_identity"]["location_ref"] = target_location
    transform["output_identity"]["value"] = target_position["identity_criteria"]

    normalized_states = authority["normalized_states"]
    results = authority["comparator_results"]
    payloads = authority["comparison_payloads"]
    verifications = authority["verification_artifacts"]
    relations: set[str] = set()
    for difference in transform["axis_differences"]:
        axis_id = difference["axis_id"]
        source_state: dict[str, object] = {
            "location_ref": source_location,
            "axis_id": axis_id,
            "value": source_position["scale_profile"][axis_id],
        }
        target_state: dict[str, object] = {
            "location_ref": target_location,
            "axis_id": axis_id,
            "value": target_position["scale_profile"][axis_id],
        }
        if axis_id == "J":
            source_state["authorization_tuple_sha256s"] = []
            target_state["authorization_tuple_sha256s"] = []
        relation = (
            "equal"
            if source_state == target_state
            else axis_relations.get(axis_id, "incomparable")
        )
        if axis_id == "J" and source_state != target_state:
            relation = "incomparable"
        relations.add(relation)
        source_ref = f"NSTATE-{transform_id}-{axis_id}-SOURCE"
        target_ref = f"NSTATE-{transform_id}-{axis_id}-TARGET"
        source_sha = canonical_sha256(source_state)
        target_sha = canonical_sha256(target_state)
        normalized_states.extend(
            [
                {
                    "transform_id": transform_id,
                    "side": "source",
                    "location_ref": source_location,
                    "axis_id": axis_id,
                    "status": "recorded",
                    "applicability_criterion_id": f"APPLICABILITY-{transform_id}-{axis_id}",
                    "applicability_result": "applicable",
                    "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
                    "normalized_state_ref": source_ref,
                    "normalized_state_sha256": source_sha,
                    "normalized_state": source_state,
                },
                {
                    "transform_id": transform_id,
                    "side": "target",
                    "location_ref": target_location,
                    "axis_id": axis_id,
                    "status": "recorded",
                    "applicability_criterion_id": f"APPLICABILITY-{transform_id}-{axis_id}",
                    "applicability_result": "applicable",
                    "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
                    "normalized_state_ref": target_ref,
                    "normalized_state_sha256": target_sha,
                    "normalized_state": target_state,
                },
            ]
        )
        result_ref = f"RESULT-{transform_id}-{axis_id}"
        payload_ref = f"PAYLOAD-{transform_id}-{axis_id}"
        verification_ref = f"VERIFY-{transform_id}-{axis_id}"
        payload_body = {
            "mapping_authority": mapping_authority,
            "axis_id": axis_id,
        }
        verification_body = {
            "mapping_authority": mapping_authority,
            "axis_id": axis_id,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "relation": relation,
        }
        verification_hash = canonical_sha256(verification_body)
        payloads[payload_ref] = {
            "payload_ref": payload_ref,
            "payload_kind": "mapping",
            "axis_id": axis_id,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "payload": payload_body,
            "payload_sha256": canonical_sha256(payload_body),
        }
        verifications[verification_ref] = {
            "verification_artifact_ref": verification_ref,
            "verifier_id": "VERIFIER-PARTIAL-ORDER",
            "comparator_result_ref": result_ref,
            "comparison_payload_ref": payload_ref,
            "axis_id": axis_id,
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "relation": relation,
            "artifact_payload": verification_body,
            "verification_hash": verification_hash,
        }
        results[result_ref] = {
            "comparator_result_ref": result_ref,
            "axis_id": axis_id,
            "comparator_id": "COMPARATOR-PARTIAL-ORDER",
            "comparator_version": comparator_version,
            "source_status": "recorded",
            "target_status": "recorded",
            "source_state_sha256": source_sha,
            "target_state_sha256": target_sha,
            "relation": relation,
            "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
            "comparison_payload_ref": payload_ref,
            "verification_artifact_ref": verification_ref,
            "verification_hash": verification_hash,
            "validation_status": "valid",
        }
        difference["source_state"] = {
            "status": "recorded",
            "normalized_state_ref": source_ref,
            "normalized_state_sha256": source_sha,
            "description": f"Externally frozen source {axis_id} authority state.",
        }
        difference["target_state"] = {
            "status": "recorded",
            "normalized_state_ref": target_ref,
            "normalized_state_sha256": target_sha,
            "description": f"Externally frozen target {axis_id} authority state.",
        }
        difference["relation"] = relation
        difference["order_witness"] = {
            "comparator_id": "COMPARATOR-PARTIAL-ORDER",
            "comparator_version": comparator_version,
            "verifier_id": "VERIFIER-PARTIAL-ORDER",
            "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
            "comparison_payload": {
                "payload_kind": "mapping",
                "payload_ref": payload_ref,
                "payload_sha256": canonical_sha256(payload_body),
                "description": f"Externally frozen mapping payload for {axis_id}.",
            },
            "comparator_result_ref": result_ref,
            "verification_artifact_ref": verification_ref,
            "verification_hash": verification_hash,
            "validation_status": "valid",
        }
    if "incomparable" in relations:
        transform["transformation_class"] = "horizontal_or_incomparable"
    elif "expands" in relations and "contracts" in relations:
        transform["transformation_class"] = "mixed"
    elif "unknown" in relations:
        transform["transformation_class"] = "unresolved"
    elif relations == {"equal"}:
        transform["transformation_class"] = "all_equal"
    elif relations <= {"equal", "expands"}:
        transform["transformation_class"] = "elevation"
    else:
        transform["transformation_class"] = "reduction"
    snapshot["transformations"].append(transform)
    return rehash_artifact(snapshot), authority


def partial_order_variant(
    document: Mapping[str, object],
    payload: Mapping[str, object],
    world: Mapping[str, object],
    variant: str,
) -> tuple[dict[str, Any], dict[str, object]]:
    snapshot = copy.deepcopy(dict(document))
    authority = copy.deepcopy(dict(payload))

    def append(
        transform_id: str,
        source: str,
        target: str,
        relation: str,
        *,
        version: str = "1.0.0",
        mapping: str = "MAPPING-PARTIAL-ORDER",
    ) -> None:
        nonlocal snapshot, authority
        snapshot, authority = append_scale_comparison(
            snapshot,
            authority,
            world,
            transform_id=transform_id,
            source_location=source,
            target_location=target,
            axis_relations={"A": relation},
            comparator_version=version,
            mapping_authority=mapping,
        )

    team = "POS-TEAM-MANAGER"
    family = "POS-FAMILY-MEMBER"
    association = "POS-ASSOCIATION-DELEGATE"
    if variant == "bidirectional-conflict":
        append("TRANSFORM-ORDER-TEAM-FAMILY", team, family, "expands")
        append("TRANSFORM-ORDER-FAMILY-TEAM", family, team, "expands")
    elif variant == "transitivity-conflict":
        append("TRANSFORM-ORDER-TEAM-FAMILY", team, family, "expands")
        append("TRANSFORM-ORDER-FAMILY-ASSOCIATION", family, association, "expands")
        append("TRANSFORM-ORDER-TEAM-ASSOCIATION", team, association, "contracts")
    elif variant == "version-witness-conflict":
        append("TRANSFORM-ORDER-TEAM-FAMILY", team, family, "expands")
        append(
            "TRANSFORM-ORDER-FAMILY-ASSOCIATION",
            family,
            association,
            "expands",
            version="2.0.0",
        )
        append("TRANSFORM-ORDER-TEAM-ASSOCIATION", team, association, "expands")
    elif variant == "auxiliary-mapping-conflict":
        append(
            "TRANSFORM-ORDER-TEAM-FAMILY-ONE",
            team,
            family,
            "expands",
            mapping="MAPPING-AUTHORITY-ONE",
        )
        append(
            "TRANSFORM-ORDER-TEAM-FAMILY-TWO",
            team,
            family,
            "expands",
            mapping="MAPPING-AUTHORITY-TWO",
        )
    else:
        raise AssertionError(f"unknown partial-order variant: {variant}")
    return snapshot, authority


def nonflattening_variant(
    document: Mapping[str, object], variant: str
) -> dict[str, Any]:
    snapshot = copy.deepcopy(dict(document))
    transform = next(
        record
        for record in snapshot["transformations"]
        if record["transform_id"] == "TRANSFORM-CIRCLE-RELATION"
    )
    if variant == "component-cross-duplicate":
        duplicate = copy.deepcopy(transform["preserved"][0])
        duplicate["description"] = "A conflicting changed description reuses the preserved ID."
        transform["changed"].append(duplicate)
    elif variant == "component-within-duplicate":
        transform["changed"].append(copy.deepcopy(transform["changed"][0]))
    elif variant == "variable-duplicate":
        transform["effective_variables"].append(
            copy.deepcopy(transform["effective_variables"][0])
        )
    elif variant == "condition-duplicate":
        transform["return_conditions"].append(
            copy.deepcopy(transform["return_conditions"][0])
        )
    elif variant == "effect-empty-refs":
        transform["location_effects"][0]["variable_refs"] = []
    elif variant == "effect-unknown-refs":
        transform["location_effects"][0]["variable_refs"] = ["VAR-MISSING"]
    elif variant == "effect-duplicate-refs":
        variable_ref = transform["location_effects"][0]["variable_refs"][0]
        transform["location_effects"][0]["variable_refs"] = [
            variable_ref,
            variable_ref,
        ]
    elif variant == "effect-orphan-variable":
        variable = copy.deepcopy(transform["effective_variables"][0])
        variable["variable_ref"] = "VAR-CIRCLE-TEAM-BUDGET-ORPHAN"
        transform["effective_variables"].append(variable)
    elif variant == "effect-cross-location":
        transform["location_effects"][0]["location_ref"] = "POS-FAMILY-MEMBER"
    elif variant == "non-scale-vacuous":
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
        ):
            transform[field] = []
    else:
        raise AssertionError(f"unknown nonflattening variant: {variant}")
    return rehash_artifact(snapshot)


def transformation_kwargs(
    *,
    world: Mapping[str, object],
    evidence: Mapping[str, object],
    relations: Mapping[str, Mapping[str, object]],
    payload: Mapping[str, object],
    expected_authorities_sha256: str,
) -> dict[str, object]:
    return {
        "source_volume": world,
        "evidence_ledger": evidence,
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_evidence_artifact_sha256": EVIDENCE_ARTIFACT_SHA256,
        "expected_world_volume_artifact_sha256": WORLD_ARTIFACT_SHA256,
        "relation_refs": relations,
        "expected_relation_refs_sha256": RELATION_REFS_SHA256,
        "authorities": make_authorities(payload),
        "expected_authorities_sha256": expected_authorities_sha256,
    }


@pytest.fixture
def world() -> dict[str, Any]:
    return load_fixture("world-volume-valid.json")


@pytest.fixture
def evidence() -> dict[str, Any]:
    authority = load_fixture("evidence-ledger-valid.json")
    authority["run_id"] = RUN_ID
    return rehash_artifact(authority)


@pytest.fixture
def ledger() -> dict[str, Any]:
    return load_fixture("transformation-valid.json")


def test_transformation_fixture_is_real_schema_valid_u5_with_more_than_three_records(
    ledger: dict[str, Any],
) -> None:
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        ledger,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    assert ledger["content_sha256"] == TRANSFORMATION_CONTENT_SHA256
    assert canonical_sha256(ledger) == TRANSFORMATION_ARTIFACT_SHA256
    assert len(ledger["transformations"]) == 4
    assert {record["kind"] for record in ledger["transformations"]} == {
        "scale",
        "circle-relation",
        "representation-translation",
    }


def test_valid_external_authority_bundle_has_independent_frozen_seal(
    world: dict[str, Any],
) -> None:
    payload = make_authority_payload(world)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES["valid"]
    assert len(payload["normalized_states"]) == 18
    assert len(payload["comparator_results"]) == 9


def test_valid_transformations_resolve_all_external_authority_and_preserve_inputs(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    before = copy.deepcopy((ledger, world, evidence, relations, payload))
    ids = runtime.validate_transformations(
        ledger,
        **transformation_kwargs(
            world=world,
            evidence=evidence,
            relations=relations,
            payload=payload,
            expected_authorities_sha256=AUTHORITY_HASHES["valid"],
        ),
    )
    assert ids == tuple(record["transform_id"] for record in ledger["transformations"])
    assert (ledger, world, evidence, relations, payload) == before


@pytest.mark.parametrize(
    ("keyword", "replacement"),
    [
        ("expected_run_id", "wrong-run"),
        ("expected_version_binding", {**VERSION_BINDING, "validator_version": "9"}),
        ("expected_evidence_artifact_sha256", "a" * 64),
        ("expected_world_volume_artifact_sha256", "b" * 64),
        ("expected_relation_refs_sha256", "c" * 64),
        ("expected_authorities_sha256", "d" * 64),
    ],
)
def test_transform_producer_rejects_wrong_external_expected_authority(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    keyword: str,
    replacement: object,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    kwargs = transformation_kwargs(
        world=world,
        evidence=evidence,
        relations=relations,
        payload=payload,
        expected_authorities_sha256=AUTHORITY_HASHES["valid"],
    )
    kwargs[keyword] = replacement
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(ledger, **kwargs)


@pytest.mark.parametrize(
    "attacker",
    [AlwaysEqual(), AlwaysEqualStr()],
    ids=("arbitrary-always-equal", "always-equal-str-subclass"),
)
@pytest.mark.parametrize(
    "keyword",
    (
        "expected_evidence_artifact_sha256",
        "expected_world_volume_artifact_sha256",
        "expected_relation_refs_sha256",
        "expected_authorities_sha256",
    ),
)
def test_transform_public_hash_authority_rejects_equality_attackers(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    attacker: object,
    keyword: str,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    kwargs = transformation_kwargs(
        world=world,
        evidence=evidence,
        relations=relations,
        payload=payload,
        expected_authorities_sha256=AUTHORITY_HASHES["valid"],
    )
    kwargs[keyword] = attacker
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(ledger, **kwargs)


@pytest.mark.parametrize(
    "keyword",
    (
        "expected_evidence_artifact_sha256",
        "expected_world_volume_artifact_sha256",
        "expected_relation_refs_sha256",
        "expected_authorities_sha256",
    ),
)
def test_transform_public_hash_authority_requires_lowercase_64_hex(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    keyword: str,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    kwargs = transformation_kwargs(
        world=world,
        evidence=evidence,
        relations=relations,
        payload=payload,
        expected_authorities_sha256=AUTHORITY_HASHES["valid"],
    )
    kwargs[keyword] = "A" * 64
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(ledger, **kwargs)


@pytest.mark.parametrize("authority_kind", ("run-id", "version-binding"))
def test_transform_public_scalar_authority_rejects_equality_overrides(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    authority_kind: str,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    kwargs = transformation_kwargs(
        world=world,
        evidence=evidence,
        relations=relations,
        payload=payload,
        expected_authorities_sha256=AUTHORITY_HASHES["valid"],
    )
    if authority_kind == "run-id":
        kwargs["expected_run_id"] = AlwaysEqualStr("attacker-run")
    else:
        kwargs["expected_version_binding"] = {
            **VERSION_BINDING,
            "validator_version": AlwaysEqualStr("attacker-version"),
        }
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(ledger, **kwargs)


@pytest.mark.parametrize("artifact_name", ("document", "source-volume", "evidence"))
@pytest.mark.parametrize("artifact_field", ("run-id", "version-binding"))
def test_transform_artifact_authority_fields_require_native_json_strings(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    artifact_name: str,
    artifact_field: str,
) -> None:
    attacked_ledger = copy.deepcopy(ledger)
    attacked_world = copy.deepcopy(world)
    attacked_evidence = copy.deepcopy(evidence)
    target = {
        "document": attacked_ledger,
        "source-volume": attacked_world,
        "evidence": attacked_evidence,
    }[artifact_name]
    preserve_canonical_text = artifact_name != "document"
    if artifact_field == "run-id":
        text = target["run_id"] if preserve_canonical_text else "attacker-run"
        target["run_id"] = AlwaysEqualStr(text)
    else:
        text = (
            target["version_binding"]["runtime_version"]
            if preserve_canonical_text
            else "attacker-runtime"
        )
        target["version_binding"]["runtime_version"] = AlwaysEqualStr(text)
    if artifact_name == "document":
        attacked_ledger = rehash_artifact(attacked_ledger)
    elif artifact_name == "source-volume":
        attacked_world = rehash_artifact(attacked_world)
    else:
        attacked_evidence = rehash_artifact(attacked_evidence)

    relations = relation_authority(attacked_world)
    payload = make_authority_payload(world)
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            attacked_ledger,
            **transformation_kwargs(
                world=attacked_world,
                evidence=attacked_evidence,
                relations=relations,
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


@pytest.mark.parametrize(
    "role",
    (
        "world-artifact",
        "normalized-state",
        "comparator-source-state",
        "comparator-verification",
        "verification-source-state",
        "verification-hash",
        "payload-source-state",
        "payload-hash",
        "deep-equality-payload-state",
        "verification-payload-state",
    ),
)
def test_transformation_authority_hash_roles_reject_str_subclasses(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    role: str,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    replace_authority_hash_role(payload, role)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES["valid"]
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            ledger,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relations,
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


@pytest.mark.parametrize(
    "role", ("tuple-hash", "normalized-j-set", "review-tuple-hash", "review-hash")
)
def test_j_authority_hash_roles_reject_str_subclasses(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    role: str,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world, variant="j-expand")
    replace_j_authority_hash_role(payload, role)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES["j-expand"]
    synchronized = replace_axis_from_authority(ledger, payload, "J")
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            synchronized,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relations,
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["j-expand"],
            ),
        )


@pytest.mark.parametrize("role", ("normalized-axis", "comparator-registry-key"))
def test_transformation_authority_nested_strings_require_native_json(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    role: str,
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    if role == "normalized-axis":
        axis = payload["normalized_states"][0]["axis_id"]
        payload["normalized_states"][0]["axis_id"] = AlwaysEqualStr(axis)
    else:
        registry = payload["comparator_results"]
        key = next(iter(registry))
        payload["comparator_results"] = {
            (
                EqualityOverridingTextStr(key) if item_key == key else item_key
            ): value
            for item_key, value in registry.items()
        }
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES["valid"]
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            ledger,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relations,
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


def test_swapped_or_stale_upstream_artifact_roles_are_rejected(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    broken = copy.deepcopy(ledger)
    broken["evidence_artifact_sha256"], broken["evidence_content_sha256"] = (
        broken["evidence_content_sha256"],
        broken["evidence_artifact_sha256"],
    )
    broken["world_volume_artifact_sha256"], broken["world_volume_content_sha256"] = (
        broken["world_volume_content_sha256"],
        broken["world_volume_artifact_sha256"],
    )
    broken = rehash_artifact(broken)
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            broken,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relations,
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


def test_authority_bundle_cannot_rename_refs_and_self_rehash(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    renamed = copy.deepcopy(payload)
    renamed["comparator_results"] = {
        f"RENAMED-{key}": {**record, "comparator_result_ref": f"RENAMED-{key}"}
        for key, record in payload["comparator_results"].items()
    }
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            ledger,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relations,
                payload=renamed,
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


@pytest.mark.parametrize(
    ("target", "field", "replacement"),
    [
        ("source_state", "normalized_state_sha256", "a" * 64),
        ("target_state", "normalized_state_ref", "NSTATE-STOLEN"),
        ("order_witness", "comparator_version", "2.0.0"),
        ("order_witness", "comparator_result_ref", "RESULT-STOLEN"),
        ("order_witness", "verification_artifact_ref", "VERIFY-STOLEN"),
        ("order_witness", "verification_hash", "b" * 64),
    ],
)
def test_scale_ledger_fields_must_align_with_external_axis_authority(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    target: str,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(ledger)
    difference = broken["transformations"][0]["axis_differences"][0]
    difference[target][field] = replacement
    broken = rehash_artifact(broken)
    relations = relation_authority(world)
    payload = make_authority_payload(world)
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            broken,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relations,
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


@pytest.mark.parametrize(
    "variant",
    [
        "normalized-state-hash-mismatch",
        "payload-hash-mismatch",
        "verification-chain-mismatch",
    ],
)
def test_externally_sealed_synchronized_bundle_still_recomputes_internal_hash_chain(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    payload = make_authority_payload(world, variant=variant)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES[variant]
    document = replace_axis_from_authority(ledger, payload, "A")
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES[variant],
            ),
        )


@pytest.mark.parametrize(
    "variant",
    [
        "deep-equality-false",
        "deep-equality-swapped-refs",
        "deep-equality-stale-hashes",
    ],
)
def test_builtin_deep_equality_payload_semantics_cross_align_all_authorities(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    payload = make_authority_payload(world, variant=variant)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES[variant]
    document = replace_axis_from_authority(ledger, payload, "A")
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES[variant],
            ),
        )


@pytest.mark.parametrize(
    "variant",
    ["deep-equality-unequal-equal", "deep-equality-unequal-expands"],
)
def test_builtin_deep_equality_cannot_order_nonidentical_normalized_states(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    payload = make_authority_payload(world, variant=variant)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES[variant]
    document = replace_scale_from_authority(ledger, payload)
    if variant == "deep-equality-unequal-expands":
        with pytest.raises((ValidationError, UltraSchemaError)):
            validate_phase_artifact(
                "ultra-transformation-ledger.schema.json",
                document,
                expected_schema_id="crossframe.ultra.v82.transformation-ledger",
                expected_run_id=RUN_ID,
                expected_version_binding=VERSION_BINDING,
                expected_phase_id="U5",
            )
        return
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES[variant],
            ),
        )


def test_identical_normalized_states_cannot_claim_expansion_even_after_reseal(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    payload = make_authority_payload(world, variant="false-expand")
    broken = replace_axis_from_authority(ledger, payload, "A")
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            broken,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["false-expand"],
            ),
        )


def test_fully_synchronized_normalized_state_still_must_equal_u4_scale_value(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    payload = make_authority_payload(world, variant="u4-mismatch")
    document = replace_axis_from_authority(ledger, payload, "A")
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES["u4-mismatch"],
            ),
        )


def test_unknown_axis_has_no_registry_witness_and_recomputes_unresolved_class(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    payload = make_authority_payload(world, variant="unknown")
    document = replace_axis_from_authority(ledger, payload, "A")
    ids = runtime.validate_transformations(
        document,
        **transformation_kwargs(
            world=world,
            evidence=evidence,
            relations=relation_authority(world),
            payload=payload,
            expected_authorities_sha256=AUTHORITY_HASHES["unknown"],
        ),
    )
    assert ids[0] == "TRANSFORM-SCALE-PRIMARY"
    assert document["transformations"][0]["transformation_class"] == "unresolved"


def test_bilateral_na_requires_the_same_external_applicability_criterion(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    valid_payload = make_authority_payload(world, variant="bilateral-na")
    valid_document = replace_axis_from_authority(ledger, valid_payload, "A")
    runtime.validate_transformations(
        valid_document,
        **transformation_kwargs(
            world=world,
            evidence=evidence,
            relations=relation_authority(world),
            payload=valid_payload,
            expected_authorities_sha256=AUTHORITY_HASHES["bilateral-na"],
        ),
    )

    invalid_payload = make_authority_payload(world, variant="bilateral-na-mismatch")
    invalid_document = replace_axis_from_authority(ledger, invalid_payload, "A")
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            invalid_document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=invalid_payload,
                expected_authorities_sha256=AUTHORITY_HASHES[
                    "bilateral-na-mismatch"
                ],
            ),
        )


def test_j_expansion_uses_atomic_tuple_set_difference_and_independent_reviews(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    payload = make_authority_payload(world, variant="j-expand")
    document = replace_axis_from_authority(ledger, payload, "J")
    ids = runtime.validate_transformations(
        document,
        **transformation_kwargs(
            world=world,
            evidence=evidence,
            relations=relation_authority(world),
            payload=payload,
            expected_authorities_sha256=AUTHORITY_HASHES["j-expand"],
        ),
    )
    assert ids[0] == "TRANSFORM-SCALE-PRIMARY"
    assert document["transformations"][0]["transformation_class"] == "elevation"


def test_j_unilateral_not_applicable_uses_only_applicability_domain_authority(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    payload = make_authority_payload(world, variant="j-unilateral-na")
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES[
        "j-unilateral-na"
    ]
    document = replace_axis_from_authority(ledger, payload, "J")
    runtime.validate_transformations(
        document,
        **transformation_kwargs(
            world=world,
            evidence=evidence,
            relations=relation_authority(world),
            payload=payload,
            expected_authorities_sha256=AUTHORITY_HASHES["j-unilateral-na"],
        ),
    )
    assert document["transformations"][0]["transformation_class"] == (
        "horizontal_or_incomparable"
    )


def test_j_canonical_tuple_set_is_equal_and_permutation_is_rejected(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    equal_payload = make_authority_payload(world, variant="j-set-equal")
    assert canonical_sha256(authority_mapping(equal_payload)) == AUTHORITY_HASHES[
        "j-set-equal"
    ]
    equal_document = replace_axis_from_authority(ledger, equal_payload, "J")
    runtime.validate_transformations(
        equal_document,
        **transformation_kwargs(
            world=world,
            evidence=evidence,
            relations=relation_authority(world),
            payload=equal_payload,
            expected_authorities_sha256=AUTHORITY_HASHES["j-set-equal"],
        ),
    )
    assert equal_document["transformations"][0]["transformation_class"] == "all_equal"

    permutation = make_authority_payload(world, variant="j-permutation")
    assert canonical_sha256(authority_mapping(permutation)) == AUTHORITY_HASHES[
        "j-permutation"
    ]
    permutation_document = replace_axis_from_authority(ledger, permutation, "J")
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            permutation_document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=permutation,
                expected_authorities_sha256=AUTHORITY_HASHES["j-permutation"],
            ),
        )


@pytest.mark.parametrize("variant", ["j-review-invalid", "j-diff-stale", "j-cartesian"])
def test_j_expansion_rejects_invalid_review_stale_difference_or_cartesian_tuple(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    payload = make_authority_payload(world, variant=variant)
    document = replace_axis_from_authority(ledger, payload, "J")
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES[variant],
            ),
        )


@pytest.mark.parametrize(
    "variant",
    [
        "j-validity-forever",
        "j-empty-revocations",
        "j-shared-review",
        "j-self-review",
        "j-empty-review-evidence",
    ],
)
def test_j_atomic_tuple_and_review_gate_rejects_externally_sealed_invalid_authority(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    payload = make_authority_payload(world, variant=variant)
    assert canonical_sha256(authority_mapping(payload)) == AUTHORITY_HASHES[variant]
    document = replace_axis_from_authority(ledger, payload, "J")
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=AUTHORITY_HASHES[variant],
            ),
        )


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    [
        ("input_identity", "location_ref", "RELATION-MISSING"),
        ("output_identity", "value", "0" * 64),
        ("preserved", "source_refs", ["SOURCE-MISSING"]),
        ("unknown", "unknown_id", "UNKNOWN-MISSING"),
        ("task_relative_loss", "affected_component_ids", ["COMP-MISSING"]),
        ("location_effects", "variable_refs", ["VAR-MISSING"]),
        ("effective_variables", "state_id", "M-MISSING"),
        ("residuals", "residual_id", "RESIDUAL-MISSING"),
        ("return_conditions", "required_variable_refs", ["VAR-MISSING"]),
    ],
)
def test_all_nonflattening_identity_and_nested_refs_resolve_u3_u4(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    section: str,
    field: str,
    replacement: object,
) -> None:
    broken = copy.deepcopy(ledger)
    transform = broken["transformations"][1]
    target = transform[section]
    if isinstance(target, list):
        target = target[0]
    target[field] = replacement
    broken = rehash_artifact(broken)
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            broken,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=make_authority_payload(world),
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


def test_schema_valid_net_effect_only_non_scale_transform_is_rejected_at_runtime(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    broken = copy.deepcopy(ledger)
    circle_transform = broken["transformations"][1]
    assert circle_transform["changed"]
    assert circle_transform["task_relative_loss"]
    assert circle_transform["effective_variables"]
    circle_transform["location_effects"] = []
    broken = rehash_artifact(broken)
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            broken,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=make_authority_payload(world),
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


@pytest.mark.parametrize(
    "variant",
    [
        "component-cross-duplicate",
        "component-within-duplicate",
        "variable-duplicate",
        "condition-duplicate",
        "effect-empty-refs",
        "effect-unknown-refs",
        "effect-orphan-variable",
        "effect-cross-location",
        "non-scale-vacuous",
    ],
)
def test_nonflattening_partitions_and_location_effect_coverage_are_exact(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    broken = nonflattening_variant(ledger, variant)
    expected_content, expected_artifact = NONFLATTENING_HASHES[variant]
    assert broken["content_sha256"] == expected_content
    assert canonical_sha256(broken) == expected_artifact
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        broken,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            broken,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=make_authority_payload(world),
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


def test_duplicate_location_effect_refs_are_rejected_by_the_frozen_schema(
    ledger: dict[str, Any],
) -> None:
    broken = nonflattening_variant(ledger, "effect-duplicate-refs")
    expected_content, expected_artifact = NONFLATTENING_HASHES[
        "effect-duplicate-refs"
    ]
    assert broken["content_sha256"] == expected_content
    assert canonical_sha256(broken) == expected_artifact
    with pytest.raises((ValidationError, UltraSchemaError)):
        validate_phase_artifact(
            "ultra-transformation-ledger.schema.json",
            broken,
            expected_schema_id="crossframe.ultra.v82.transformation-ledger",
            expected_run_id=RUN_ID,
            expected_version_binding=VERSION_BINDING,
            expected_phase_id="U5",
        )


def test_transform_ids_are_unique_and_classification_is_recomputed(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    duplicate = copy.deepcopy(ledger)
    duplicate["transformations"][3]["transform_id"] = duplicate["transformations"][2]["transform_id"]
    duplicate = rehash_artifact(duplicate)
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            duplicate,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=make_authority_payload(world),
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )

    wrong_class = copy.deepcopy(ledger)
    wrong_class["transformations"][0]["transformation_class"] = "elevation"
    wrong_class = rehash_artifact(wrong_class)
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            wrong_class,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=make_authority_payload(world),
                expected_authorities_sha256=AUTHORITY_HASHES["valid"],
            ),
        )


@pytest.mark.parametrize(
    "variant",
    [
        "bidirectional-conflict",
        "transitivity-conflict",
        "version-witness-conflict",
        "auxiliary-mapping-conflict",
    ],
)
def test_cross_record_partial_order_requires_composable_versions_and_witnesses(
    ledger: dict[str, Any],
    world: dict[str, Any],
    evidence: dict[str, Any],
    variant: str,
) -> None:
    document, payload = partial_order_variant(
        ledger,
        make_authority_payload(world),
        world,
        variant,
    )
    expected = PARTIAL_ORDER_HASHES[variant]
    assert canonical_sha256(authority_mapping(payload)) == expected["authority"]
    assert document["content_sha256"] == expected["content"]
    assert canonical_sha256(document) == expected["artifact"]
    validate_phase_artifact(
        "ultra-transformation-ledger.schema.json",
        document,
        expected_schema_id="crossframe.ultra.v82.transformation-ledger",
        expected_run_id=RUN_ID,
        expected_version_binding=VERSION_BINDING,
        expected_phase_id="U5",
    )
    with pytest.raises(runtime.TransformationError):
        runtime.validate_transformations(
            document,
            **transformation_kwargs(
                world=world,
                evidence=evidence,
                relations=relation_authority(world),
                payload=payload,
                expected_authorities_sha256=expected["authority"],
            ),
        )


def valid_cascade() -> dict[str, object]:
    return {
        "cascade_id": "CASCADE-FIXTURE",
        "hops": [
            {
                "hop_id": "CASCADE-HOP-01",
                "from_position_id": "POS-TEAM-MANAGER",
                "to_position_id": "POS-TEAM-MANAGER",
                "channel_id": "CHANNEL-TEAM-SELF",
                "boundary_validated": True,
                "representation_qualified": True,
                "threshold_met": True,
                "identity_preserved": True,
                "acl_authorized": True,
                "evidence_ids": ["EVIDENCE-ROSTER-ATLAS"],
            },
            {
                "hop_id": "CASCADE-HOP-02",
                "from_position_id": "POS-TEAM-MANAGER",
                "to_position_id": "POS-ASSOCIATION-DELEGATE",
                "channel_id": "CHANNEL-TEAM-ASSOCIATION",
                "boundary_validated": True,
                "representation_qualified": True,
                "threshold_met": True,
                "identity_preserved": True,
                "acl_authorized": True,
                "evidence_ids": [
                    "EVIDENCE-ROSTER-ATLAS",
                    "EVIDENCE-ASSOCIATION-CHARTER",
                ],
            },
        ],
    }


def cascade_kwargs(
    world: Mapping[str, object],
    evidence: Mapping[str, object],
    relations: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "evidence_ledger": evidence,
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_evidence_artifact_sha256": EVIDENCE_ARTIFACT_SHA256,
        "relation_refs": relations,
        "expected_relation_refs_sha256": RELATION_REFS_SHA256,
    }


def test_valid_cascade_revalidates_each_hop_and_returns_ordered_channels_without_mutation(
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    cascade = valid_cascade()
    relations = relation_authority(world)
    before = copy.deepcopy((cascade, world, evidence, relations))
    assert runtime.validate_cascade(
        cascade,
        world,
        **cascade_kwargs(world, evidence, relations),
    ) == ("CHANNEL-TEAM-SELF", "CHANNEL-TEAM-ASSOCIATION")
    assert (cascade, world, evidence, relations) == before


@pytest.mark.parametrize(
    "attacker",
    [AlwaysEqual(), AlwaysEqualStr()],
    ids=("arbitrary-always-equal", "always-equal-str-subclass"),
)
@pytest.mark.parametrize(
    "keyword",
    ("expected_evidence_artifact_sha256", "expected_relation_refs_sha256"),
)
def test_cascade_public_hash_authority_rejects_equality_attackers(
    world: dict[str, Any],
    evidence: dict[str, Any],
    attacker: object,
    keyword: str,
) -> None:
    relations = relation_authority(world)
    kwargs = cascade_kwargs(world, evidence, relations)
    kwargs[keyword] = attacker
    with pytest.raises(runtime.ChannelContinuityError):
        runtime.validate_cascade(valid_cascade(), world, **kwargs)


@pytest.mark.parametrize("authority_kind", ("run-id", "version-binding"))
def test_cascade_public_scalar_authority_rejects_equality_overrides(
    world: dict[str, Any],
    evidence: dict[str, Any],
    authority_kind: str,
) -> None:
    relations = relation_authority(world)
    kwargs = cascade_kwargs(world, evidence, relations)
    if authority_kind == "run-id":
        kwargs["expected_run_id"] = AlwaysEqualStr("attacker-run")
    else:
        kwargs["expected_version_binding"] = {
            **VERSION_BINDING,
            "validator_version": AlwaysEqualStr("attacker-version"),
        }
    with pytest.raises(runtime.ChannelContinuityError):
        runtime.validate_cascade(valid_cascade(), world, **kwargs)


@pytest.mark.parametrize("artifact_name", ("volume", "evidence"))
@pytest.mark.parametrize("artifact_field", ("run-id", "version-binding"))
def test_cascade_artifact_authority_fields_require_native_json_strings(
    world: dict[str, Any],
    evidence: dict[str, Any],
    artifact_name: str,
    artifact_field: str,
) -> None:
    attacked_world = copy.deepcopy(world)
    attacked_evidence = copy.deepcopy(evidence)
    target = attacked_world if artifact_name == "volume" else attacked_evidence
    preserve_canonical_text = artifact_name == "evidence"
    if artifact_field == "run-id":
        text = target["run_id"] if preserve_canonical_text else "attacker-run"
        target["run_id"] = AlwaysEqualStr(text)
    else:
        text = (
            target["version_binding"]["runtime_version"]
            if preserve_canonical_text
            else "attacker-runtime"
        )
        target["version_binding"]["runtime_version"] = AlwaysEqualStr(text)
    if artifact_name == "volume":
        attacked_world = rehash_artifact(attacked_world)
    else:
        attacked_evidence = rehash_artifact(attacked_evidence)
    relations = relation_authority(attacked_world)

    with pytest.raises(runtime.ChannelContinuityError):
        runtime.validate_cascade(
            valid_cascade(),
            attacked_world,
            **cascade_kwargs(attacked_world, attacked_evidence, relations),
        )


def test_cross_circle_cascade_requires_externally_sealed_rcc_boundary_authority(
    world: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    without_rcc = copy.deepcopy(world)
    without_rcc["circle_relations"] = []
    without_rcc = rehash_artifact(without_rcc)
    relations = relation_authority(without_rcc)
    assert canonical_sha256(relations) == RAC_ONLY_RELATION_REFS_SHA256
    kwargs = cascade_kwargs(without_rcc, evidence, relations)
    kwargs["expected_relation_refs_sha256"] = RAC_ONLY_RELATION_REFS_SHA256

    same_circle = valid_cascade()
    same_circle["hops"] = [same_circle["hops"][0]]
    assert runtime.validate_cascade(
        same_circle,
        without_rcc,
        **kwargs,
    ) == ("CHANNEL-TEAM-SELF",)

    with pytest.raises(runtime.ChannelContinuityError):
        runtime.validate_cascade(
            valid_cascade(),
            without_rcc,
            **kwargs,
        )


@pytest.mark.parametrize(
    ("mutation", "replacement"),
    [
        ("missing-second-channel", "CHANNEL-MISSING"),
        ("threshold", False),
        ("acl", False),
        ("identity", False),
        ("boundary", False),
        ("representation", False),
        ("evidence-unknown", ["EVIDENCE-MISSING"]),
        ("evidence-mismatch", ["EVIDENCE-INTERVIEW-ONE"]),
        ("endpoint", "POS-FAMILY-MEMBER"),
        ("disconnected", "POS-FAMILY-MEMBER"),
    ],
)
def test_each_cascade_hop_rejects_missing_threshold_acl_identity_evidence_or_continuity(
    world: dict[str, Any],
    evidence: dict[str, Any],
    mutation: str,
    replacement: object,
) -> None:
    cascade = valid_cascade()
    second = cascade["hops"][1]
    if mutation == "missing-second-channel":
        second["channel_id"] = replacement
    elif mutation == "threshold":
        second["threshold_met"] = replacement
    elif mutation == "acl":
        second["acl_authorized"] = replacement
    elif mutation == "identity":
        second["identity_preserved"] = replacement
    elif mutation == "boundary":
        second["boundary_validated"] = replacement
    elif mutation == "representation":
        second["representation_qualified"] = replacement
    elif mutation.startswith("evidence"):
        second["evidence_ids"] = replacement
    elif mutation == "endpoint":
        second["to_position_id"] = replacement
    else:
        second["from_position_id"] = replacement
    relations = relation_authority(world)
    with pytest.raises(runtime.ChannelContinuityError):
        runtime.validate_cascade(
            cascade,
            world,
            **cascade_kwargs(world, evidence, relations),
        )
