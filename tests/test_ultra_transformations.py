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
    "dd16c63fde4626d4db4c82736f67e18ecaed9b5817d2f5cb342bc23ccc947982"
)
WORLD_ARTIFACT_SHA256 = (
    "053716f0de6b642d2bc53b82862761c5815402005ecaad3e2f0abfc5103cc746"
)
RELATION_REFS_SHA256 = (
    "cd8b59e7c3877cb26c778f2a41d7dba6604e1288d54b7aa846292bcbdf5ab60a"
)
RAC_ONLY_RELATION_REFS_SHA256 = (
    "149f998f82aa28ea1913ace1ab39f4a223adad019ff1359e14f8b0869650cb7f"
)
TRANSFORMATION_CONTENT_SHA256 = (
    "8176d8cf91995fb239cfc6c8fb15f8f60f6150e27559e336e4b9bc9f0f60528a"
)
TRANSFORMATION_ARTIFACT_SHA256 = (
    "76bc58745c59ea40566e17ad2324cfbd737d4f7fcd4a92ce2c179b42f8288084"
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
    "runtime_version": "1.1.0",
    "artifact_schema_version": 2,
    "compiler_version": "1.0.0",
    "validator_version": "1.1.0",
    "article_contract_version": "1.1.0",
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
    "valid": "8c5959e3d0335decfcafd46f0b476792c3dbf6efa89c6bfe6edad037326908de",
    "unknown": "48b0e0e0678e4f9ad70b7bfa7e0221ca6dff4baaf91998bc5d1d1ff1c4400e26",
    "bilateral-na": "68b013425b8ce19b2207493c07e3274a616dc696c037db27686886137c23cde4",
    "bilateral-na-mismatch": "6a25399f308305a1f0dbd8881b710dc0b98d3d7cafab30b60a2bd9070ed6b7a1",
    "j-expand": "df00b1647baf2a7a6da6b2aa3efb8f8b60a65c3c471e03036ab5b5d9b354aa10",
    "j-review-invalid": "88d1160604f5555765f23f69256610e73d24bd3db211755fc06439781906509c",
    "j-diff-stale": "4bcc33fad10258cf1004992fa9d612317d332ef833d9163f14de9b77b65ac92d",
    "j-cartesian": "ae693dadf74005532147e225429b061556eac36a590090772ef7c9ecae7983c2",
    "false-expand": "265e9cd8f350eab96744ba1084aa7aef10cc8db4e5dc03c5c6f7cfea2a7fadcb",
    "u4-mismatch": "c25410e09938374f9113e741a35d0021c846080f8c9329f5c7e9d3e3b8159be8",
    "normalized-state-hash-mismatch": "6ce614b5415c0afb25ef466aee53f9e0b4de02c1c22d19f0626f4fa4cd60707a",
    "payload-hash-mismatch": "78830aa32b7d338cca1d38f0462fc5eb6b8ace360537994120e8f12e1d9bb0be",
    "verification-chain-mismatch": "91912c4e68efa42199e66f529617281a646335b31a634727339e798619b41194",
    "j-unilateral-na": "8271880b84e75b2bc17306621729e2e2663ca467ac02a8d259197eec648b5e27",
    "j-set-equal": "71ce3e6775514f090ebc67437bad2400fc3e7692193098c6dbdbe8254e92d71c",
    "j-permutation": "5f9b398afb962e4610318b8ca52756a4cb53519d87028f911f44d82bf6d2bd5e",
    "j-validity-forever": "e4376fe13d3db600d104c69a84880f32d74143b30d359fcb4ab4155784811f78",
    "j-empty-revocations": "c93b2945c2dcf770c4472227dc59e0ef59015e48a10151a9a8579ff21939e8f3",
    "j-shared-review": "bafc6f596ad4de0a621e3de3fb0e6b5b58d3636b2af1f0c1fb5738877ef382eb",
    "j-self-review": "068baff6063367d7bf4a720a3273d4aa01247c2bf05df5a36f6ab43caf03134e",
    "j-empty-review-evidence": "30ddb744d334e9e55231b9874ea8698d43bfbe6377bcec55923369a895fde8e4",
    "deep-equality-false": "ae7e63df525f51c560673c9f2de717cb31938657c6a92df270870bfa07c69856",
    "deep-equality-swapped-refs": "f26aed60a9fa266cb0ce026ca9a94d38a3440b0f885a1fb463e0d4cd8fcc644b",
    "deep-equality-stale-hashes": "6344148003a17dfa2330eafd9184ef214a0fcf3e97dd7fd6cada9637d02d7d18",
    "deep-equality-unequal-equal": "959e3e28d1933da8036595e5c94a7e4552565917dd424192772f772723a54696",
    "deep-equality-unequal-expands": "5dc570038695f7b31f517f136b092b79891e1bb7ef445f4d0f131ce14b3a6a2b",
}
NONFLATTENING_HASHES = {
    "component-cross-duplicate": (
        "fb77839a613cf62657d0edede7b431816939424d08e2fa6c8fb0154899a1511c",
        "3ac9408cce50b1fda071ebaac751e8dee45184447403761b91583b9e15b5ddc1",
    ),
    "component-within-duplicate": (
        "8737a05293b0294ee7811628ba8df7a171fb288d9aa05eeb09b7955811250fad",
        "284e9fae0623de4fcfa92e6f728f5649215b545a177b15b6beac42e3228b0adf",
    ),
    "variable-duplicate": (
        "dc6549a83236abd3cee160eda897e00a3f08eaf1d781a970f5e6621f06dfc562",
        "b10058f2a17d93d948358f111abbe841c299638add1b53a4873a4d38a6156543",
    ),
    "condition-duplicate": (
        "62d80ea15bd6c5d8c9cbd37c8ccbcf2e5cdbd20ece023d489579b81f15f66341",
        "70faa45abe3871dbbdd7b7bb5cf6e0b118f25050dc6abb8bf7afb8bcda0f17b9",
    ),
    "effect-empty-refs": (
        "c53bf7a9273cae5cd7bac5fc6c863bddd3503110675d0a653506d56aa6923689",
        "82110f6f7d9b2fd6cd38eb6259027012c446b206f5f395b35159e3dc21930ac6",
    ),
    "effect-unknown-refs": (
        "ee29f46fad00c46f57bad5976c404a3ee5dea61a51516e47e9a351f48e93a5ce",
        "7ac9c4180b3238149746cb18a339eeacad7c59a49d9164b16203db787c36d8eb",
    ),
    "effect-duplicate-refs": (
        "8b7faae725e81932776968eb782cac36b6c7e56fafb2c1122011ecbbdaa1992a",
        "2679815d37905a434db4310ced960962d9fa588455b4f1fc5403cad69954ae13",
    ),
    "effect-orphan-variable": (
        "8e2c15b6a762316e27c04df488a9159997e8294c5fca61cb39c8fe745c541460",
        "50d60bc19a57d433632b395328ae5175df4dce6ca760477db47d733455a63974",
    ),
    "effect-cross-location": (
        "183c26015b8968ffcdecd9ae6942369ed2fe69acdc4a58d7c5c1aab0c2fcafca",
        "b921b49155745ec0ba7b6c50a5ccd833303e41d13738616ad3dc32e35035bdf5",
    ),
    "non-scale-vacuous": (
        "f3fe0a6b6be18c4f4ad7a9d783579f17da4e409dff94b69a47b084851c31e291",
        "1074083e864a73334b78bee728596119fc4afefd97b3429ecf8a5a66001dd79e",
    ),
}
PARTIAL_ORDER_HASHES = {
    "bidirectional-conflict": {
        "authority": "d99a701b2a868867fa8ef801500642b43365eda385124ecb2c594c84b722be84",
        "content": "05acd005d04c7b25a5f2948d9313a78388585367d3fb10bc88017bc0413c382b",
        "artifact": "41f677fe4c5f0869ec0da10c37b076358da029b56252a132e5ade836c8ed2326",
    },
    "transitivity-conflict": {
        "authority": "f13d10111649e23ce771f2e49a5e07c77a8a91beebd50e9523aec32e29bccf8c",
        "content": "e38c8a01a67caf042e2548231d33b0d97ff88fe5a43a573145805426c339eba0",
        "artifact": "332b664c636d5834a3d4dba047cc165e42ef893b135f6bae41613b8f569784b4",
    },
    "version-witness-conflict": {
        "authority": "0269f84b649cbb6318dbe54c4954dd8730834ac7bd9a5e0287ff49e55c79dd42",
        "content": "5324a905d50e1df2b7c84cf3e0a3e9bdce6fc84334f116ee907092d3cbf98958",
        "artifact": "4595d0bfb438521c4cc8a46067aaa04e4658776eabe0b68b8973efe676f567d2",
    },
    "auxiliary-mapping-conflict": {
        "authority": "3e04cf8e017ce4e9f5ca9604d207db95c1efb2660d46199d0ee4ac8ed1fd183a",
        "content": "d88014ebd0ffccc39eaba9e35b020d56b6e2403cc2a4f575b6b2e081538a0566",
        "artifact": "81cdea2ed2b75dbcf0d2a6dade6d46c525ba40e08b18afd14e170d17bd6f5a50",
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
