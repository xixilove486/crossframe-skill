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
    "runtime_version": "1.0.0",
    "artifact_schema_version": 1,
    "compiler_version": "1.0.0",
    "validator_version": "1.0.0",
    "article_contract_version": "1.0.0",
    "source_tree_sha256": (
        "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
    ),
}
CLAIM_GRAPH_SHA256 = (
    "cc5e6dfb83bed1ead965f5c87f6e990a65d546e384622fd17fc53a02ae7a409c"
)
LINEAGE_SHA256 = "032ec27a6d3a6ddf353927a27a5e1df2d3b5efaf8573878f65d7c2cfb8a4e9aa"


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
) -> dict[str, object]:
    accepted_graph = copy.deepcopy(
        dict(graph or load_fixture("claim-mechanism-graph-valid.json"))
    )
    accepted_lineage = copy.deepcopy(
        dict(lineage or load_fixture("recursive-lineage-valid.json"))
    )
    return {
        "claim_mechanism_graph": accepted_graph,
        "recursive_lineage": accepted_lineage,
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_claim_mechanism_graph_artifact_sha256": canonical_sha256(
            accepted_graph
        ),
        "expected_recursive_lineage_artifact_sha256": canonical_sha256(
            accepted_lineage
        ),
    }


def validate_evaluation(
    evaluation: Mapping[str, object],
    *,
    graph: Mapping[str, object] | None = None,
    lineage: Mapping[str, object] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    kwargs = authority_kwargs(graph=graph, lineage=lineage)
    kwargs.update(overrides)
    return runtime()._validate_order_evaluation(evaluation, **kwargs)


def seal_evaluation(
    evaluation: Mapping[str, object],
    *,
    graph: Mapping[str, object] | None = None,
    lineage: Mapping[str, object] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    kwargs = authority_kwargs(graph=graph, lineage=lineage)
    kwargs.update(overrides)
    return runtime()._seal_order_evaluation(evaluation, **kwargs)


def test_order_evaluation_remains_private_and_uses_frozen_stop_kinds() -> None:
    module = runtime()
    assert not hasattr(module, "validate_order_evaluation")
    assert module.STOP_KINDS == (
        "order-limit",
        "baseline-wins",
        "no-material-state-change",
        "local-predictability-exhausted",
        "evidence-boundary",
    )


def test_valid_order_evaluation_binds_exact_sealed_u6_u7_authority() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    before = copy.deepcopy(evaluation)
    assert validate_evaluation(evaluation) == evaluation
    assert evaluation == before
    validate_instance("ultra-order-evaluation.schema.json", evaluation)
    assert evaluation["claim_mechanism_graph_artifact_sha256"] == CLAIM_GRAPH_SHA256
    assert evaluation["recursive_lineage_artifact_sha256"] == LINEAGE_SHA256
    assert CLAIM_GRAPH_SHA256 != LINEAGE_SHA256


def test_order_evaluation_producer_seals_after_external_hashes_match() -> None:
    expected = load_fixture("order-evaluation-valid.json")
    candidate = copy.deepcopy(expected)
    candidate.pop("content_sha256")
    before = copy.deepcopy(candidate)
    assert seal_evaluation(candidate) == expected
    assert candidate == before


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("expected_claim_mechanism_graph_artifact_sha256", LINEAGE_SHA256),
        ("expected_recursive_lineage_artifact_sha256", CLAIM_GRAPH_SHA256),
    ),
)
def test_order_evaluation_rejects_swapped_or_stale_expected_authority(
    field: str, value: str
) -> None:
    with pytest.raises(ValueError, match="authority"):
        validate_evaluation(
            load_fixture("order-evaluation-valid.json"), **{field: value}
        )


def test_order_evaluation_cannot_self_select_a_substituted_lineage() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["recursive_lineage_artifact_sha256"] = "f" * 64
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="full artifact hash|lineage authority"):
        validate_evaluation(
            evaluation,
            expected_recursive_lineage_artifact_sha256="f" * 64,
        )


def test_every_evaluated_order_covers_each_frozen_branch_kind() -> None:
    evaluation = validate_evaluation(load_fixture("order-evaluation-valid.json"))
    for order in evaluation["evaluations"]:
        assert {item["branch_kind"] for item in order["branch_coverage"]} == {
            "main",
            "strongest-rival",
            "mixture",
            "residual",
        }
        assert {
            "explanation_gain",
            "forecast_gain",
            "added_assumptions",
            "added_losses",
            "local_predictability",
            "continuation_value",
        }.issubset(order)


def test_applicable_branch_must_resolve_at_the_evaluated_order() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["evaluations"][1]["branch_coverage"][0]["branch_ids"] = [
        "BRANCH-RIVAL"
    ]
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="branch.*order|branch kind"):
        validate_evaluation(evaluation)


def test_not_applicable_branch_requires_a_bounded_evidence_or_residual_record() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    record = evaluation["evaluations"][1]["branch_coverage"][1]["not_applicable"]
    record["evidence_refs"] = []
    record["residual_ids"] = []
    evaluation = rehash_artifact(evaluation)
    validate_instance("ultra-order-evaluation.schema.json", evaluation)
    with pytest.raises(ValueError, match="not-applicable"):
        validate_evaluation(evaluation)


def test_existing_branch_at_an_order_cannot_be_declared_not_applicable() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    record = evaluation["evaluations"][0]["branch_coverage"][0]
    record.update(
        {
            "applicability": "not-applicable",
            "branch_ids": [],
            "not_applicable": {
                "reason": "Incorrectly omitted.",
                "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
                "residual_ids": [],
            },
        }
    )
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="existing.*branch|not-applicable"):
        validate_evaluation(evaluation)


@pytest.mark.parametrize(
    "field",
    (
        "explanation_gain",
        "forecast_gain",
        "added_assumptions",
        "added_losses",
        "local_predictability",
        "continuation_value",
    ),
)
def test_all_six_simple_baseline_dimensions_are_required(field: str) -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    del evaluation["evaluations"][0][field]
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="order evaluation"):
        validate_evaluation(evaluation)


def test_deeper_order_cannot_add_an_evidence_grade_to_lineage_node() -> None:
    lineage = load_fixture("recursive-lineage-valid.json")
    lineage["nodes"][-1]["evidence_grade"] = "high-by-depth"
    lineage = rehash_artifact(lineage)
    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["recursive_lineage_artifact_sha256"] = canonical_sha256(lineage)
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="recursive lineage"):
        validate_evaluation(evaluation, lineage=lineage)


@pytest.mark.parametrize("stop_kind", ("resource-exhaustion", "tool-failure"))
def test_operational_failure_is_not_a_theoretical_stop_kind(stop_kind: str) -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["evaluations"][-1]["stop_kind"] = stop_kind
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="order evaluation"):
        validate_evaluation(evaluation)


def test_no_order_may_follow_a_declared_stop() -> None:
    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["evaluations"][0]["continue_recursive"] = False
    evaluation["evaluations"][0]["stop_kind"] = "baseline-wins"
    evaluation = rehash_artifact(evaluation)
    with pytest.raises(ValueError, match="follow.*stop|continuation"):
        validate_evaluation(evaluation)


def test_maximum_order_cannot_continue_or_omit_its_evaluation() -> None:
    continuing = load_fixture("order-evaluation-valid.json")
    continuing["evaluations"][-1]["continue_recursive"] = True
    continuing["evaluations"][-1]["stop_kind"] = None
    continuing = rehash_artifact(continuing)
    with pytest.raises(ValueError, match="maximum order|continuation"):
        validate_evaluation(continuing)

    missing = load_fixture("order-evaluation-valid.json")
    missing["evaluations"] = missing["evaluations"][:-1]
    missing = rehash_artifact(missing)
    with pytest.raises(ValueError, match="maximum order|every lineage order"):
        validate_evaluation(missing)


def test_partial_u6_ranking_with_null_tail_does_not_break_order_evaluation() -> None:
    graph = load_fixture("claim-mechanism-graph-valid.json")
    graph["partial_ranking_justification"] = (
        "The frozen evidence orders the leading paths but leaves the tail tied."
    )
    for explanation, rank in zip(
        graph["explanations"], (1, 2, None, None), strict=True
    ):
        explanation["rank"] = rank
    graph = rehash_artifact(graph)
    graph_hash = canonical_sha256(graph)

    lineage = load_fixture("recursive-lineage-valid.json")
    lineage["claim_mechanism_graph_artifact_sha256"] = graph_hash
    lineage = rehash_artifact(lineage)
    lineage_hash = canonical_sha256(lineage)

    evaluation = load_fixture("order-evaluation-valid.json")
    evaluation["claim_mechanism_graph_artifact_sha256"] = graph_hash
    evaluation["recursive_lineage_artifact_sha256"] = lineage_hash
    evaluation = rehash_artifact(evaluation)

    assert validate_evaluation(
        evaluation, graph=graph, lineage=lineage
    ) == evaluation
