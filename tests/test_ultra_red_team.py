from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "ultra-runtime"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))

from tests.test_ultra_recursion import state_registry
from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import compute_artifact_content_sha256, validate_instance


RUN_ID = "ultra-world-fixture-run"
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
CLAIM_GRAPH_SHA256 = (
    "40d6e4d2b7cbf2ce41ea0861513e0d01c14cfa0fe8ad50382c073f9aa116cb19"
)
LINEAGE_SHA256 = "f7a619cb2bac6cbbd9d8f62b90980520b7705a66d1b6dbbb80c3439f79ff6141"
ORDER_EVALUATION_SHA256 = (
    "d8b2ee28b8f31c7fdbc5816f37b9f85e2b80a2ad60025f8803b933e67aca8262"
)


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


def runtime():
    return importlib.import_module("ultra_runtime.recursion")


def authority_kwargs(
    *,
    graph: Mapping[str, object] | None = None,
    lineage: Mapping[str, object] | None = None,
    evaluation: Mapping[str, object] | None = None,
    registry: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    accepted_graph = copy.deepcopy(
        dict(graph or load_fixture("claim-mechanism-graph-valid.json"))
    )
    accepted_lineage = copy.deepcopy(
        dict(lineage or load_fixture("recursive-lineage-valid.json"))
    )
    accepted_evaluation = copy.deepcopy(
        dict(evaluation or load_fixture("order-evaluation-valid.json"))
    )
    return {
        "claim_mechanism_graph": accepted_graph,
        "recursive_lineage": accepted_lineage,
        "order_evaluation": accepted_evaluation,
        "recursive_state_artifacts": registry or state_registry(),
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_claim_mechanism_graph_artifact_sha256": canonical_sha256(
            accepted_graph
        ),
        "expected_recursive_lineage_artifact_sha256": canonical_sha256(
            accepted_lineage
        ),
        "expected_order_evaluation_artifact_sha256": canonical_sha256(
            accepted_evaluation
        ),
    }


def validate_report(
    report: Mapping[str, object],
    *,
    graph: Mapping[str, object] | None = None,
    lineage: Mapping[str, object] | None = None,
    evaluation: Mapping[str, object] | None = None,
    registry: Mapping[str, Mapping[str, object]] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    kwargs = authority_kwargs(
        graph=graph,
        lineage=lineage,
        evaluation=evaluation,
        registry=registry,
    )
    kwargs.update(overrides)
    return runtime()._validate_red_team_report(report, **kwargs)


def seal_report(
    report: Mapping[str, object],
    *,
    graph: Mapping[str, object] | None = None,
    lineage: Mapping[str, object] | None = None,
    evaluation: Mapping[str, object] | None = None,
    registry: Mapping[str, Mapping[str, object]] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    kwargs = authority_kwargs(
        graph=graph,
        lineage=lineage,
        evaluation=evaluation,
        registry=registry,
    )
    kwargs.update(overrides)
    return runtime()._seal_red_team_report(report, **kwargs)


def test_red_team_validation_remains_a_private_producer_boundary() -> None:
    assert not hasattr(runtime(), "validate_red_team_report")


def test_valid_red_team_report_binds_exact_u6_u7_u8_authority() -> None:
    report = load_fixture("red-team-report-valid.json")
    before_report = copy.deepcopy(report)
    kwargs = authority_kwargs()
    before_authority = copy.deepcopy(kwargs)
    assert runtime()._validate_red_team_report(report, **kwargs) == report
    assert report == before_report
    assert kwargs == before_authority
    validate_instance("ultra-red-team-report.schema.json", report)
    assert report["claim_mechanism_graph_artifact_sha256"] == CLAIM_GRAPH_SHA256
    assert report["recursive_lineage_artifact_sha256"] == LINEAGE_SHA256
    assert report["order_evaluation_artifact_sha256"] == ORDER_EVALUATION_SHA256
    assert len(
        {
            report["claim_mechanism_graph_artifact_sha256"],
            report["recursive_lineage_artifact_sha256"],
            report["order_evaluation_artifact_sha256"],
        }
    ) == 3


def test_red_team_producer_seals_only_after_order_evaluation_is_sealed() -> None:
    expected = load_fixture("red-team-report-valid.json")
    candidate = copy.deepcopy(expected)
    candidate.pop("content_sha256")
    before = copy.deepcopy(candidate)
    assert seal_report(candidate) == expected
    assert candidate == before

    unsealed_evaluation = load_fixture("order-evaluation-valid.json")
    unsealed_evaluation.pop("content_sha256")
    with pytest.raises(ValueError, match="order evaluation"):
        seal_report(candidate, evaluation=unsealed_evaluation)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("expected_claim_mechanism_graph_artifact_sha256", LINEAGE_SHA256),
        ("expected_recursive_lineage_artifact_sha256", ORDER_EVALUATION_SHA256),
        ("expected_order_evaluation_artifact_sha256", CLAIM_GRAPH_SHA256),
    ),
)
def test_red_team_rejects_swapped_or_stale_expected_authority(
    field: str, value: str
) -> None:
    with pytest.raises(ValueError, match="authority"):
        validate_report(load_fixture("red-team-report-valid.json"), **{field: value})


def test_red_team_cannot_self_select_an_order_evaluation_hash() -> None:
    report = load_fixture("red-team-report-valid.json")
    report["order_evaluation_artifact_sha256"] = "f" * 64
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="full artifact hash|order evaluation authority"):
        validate_report(
            report,
            expected_order_evaluation_artifact_sha256="f" * 64,
        )


def test_report_rejects_a_substituted_sealed_order_evaluation() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["evaluations"][0]["rationale"] = (
        "A substituted evaluation with a different sealed payload."
    )
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="order evaluation authority"):
        validate_report(
            load_fixture("red-team-report-valid.json"), evaluation=evaluation
        )


def test_red_team_cannot_change_recursive_state_evidence_identity() -> None:
    report = load_fixture("red-team-report-valid.json")
    report["attacks"][0]["evidence_identity"] = "observed"
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="evidence identity"):
        validate_report(report)


def test_report_requires_the_sealed_state_behind_each_recursive_target() -> None:
    registry = state_registry()
    lineage = load_fixture("recursive-lineage-valid.json")
    target_hash = next(
        node["recursive_state_artifact_sha256"]
        for node in lineage["nodes"]
        if node["node_id"] == "NODE-MAIN-ORDER-2"
    )
    registry.pop(target_hash)
    with pytest.raises(ValueError, match="sealed recursive-state artifact"):
        validate_report(load_fixture("red-team-report-valid.json"), registry=registry)


def test_attack_target_must_resolve_in_its_declared_identity_role() -> None:
    report = load_fixture("red-team-report-valid.json")
    report["attacks"][0]["target"] = {
        "recursive_node_id": "NODE-NOT-SEALED"
    }
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="attack target"):
        validate_report(report)


def test_red_team_requires_exact_simple_baseline_comparisons() -> None:
    report = load_fixture("red-team-report-valid.json")
    report["baseline_comparisons"][1]["baseline_ref"] = "BASELINE-ORDER-1"
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="baseline comparison"):
        validate_report(report)


def test_unresolved_item_must_name_an_existing_challenge() -> None:
    report = load_fixture("red-team-report-valid.json")
    report["unresolved_items"][0]["challenge_id"] = "ATTACK-NOT-DECLARED"
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="unresolved.*challenge"):
        validate_report(report)


def test_sensitivity_and_attack_identities_must_be_unique_and_role_distinct() -> None:
    report = load_fixture("red-team-report-valid.json")
    duplicate = copy.deepcopy(report["sensitivity_checks"][0])
    report["sensitivity_checks"].append(duplicate)
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="sensitivity.*unique"):
        validate_report(report)

    reused = load_fixture("red-team-report-valid.json")
    reused["sensitivity_checks"][0]["check_id"] = reused["attacks"][0]["attack_id"]
    reused = rehash_artifact(reused)
    with pytest.raises(ValueError, match="identity roles"):
        validate_report(reused)


@pytest.mark.parametrize(
    ("unresolved", "attack_result", "overall"),
    (
        ([], "survives", "needs-attention"),
        ([], "reject", "survives"),
        ([], "revise", "survives"),
    ),
)
def test_overall_status_must_match_attack_and_unresolved_outcomes(
    unresolved: list[object], attack_result: str, overall: str
) -> None:
    report = load_fixture("red-team-report-valid.json")
    report["unresolved_items"] = unresolved
    for attack in report["attacks"]:
        attack["result"] = attack_result
    report["overall_status"] = overall
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="overall status"):
        validate_report(report)


def test_schema_boundary_prevents_red_team_from_rewriting_upstream_state() -> None:
    report = load_fixture("red-team-report-valid.json")
    report["rewritten_recursive_state"] = {
        "node_id": "NODE-MAIN-ORDER-2",
        "evidence_identity": "observed",
    }
    report = rehash_artifact(report)
    with pytest.raises(ValueError, match="red-team report"):
        validate_report(report)
