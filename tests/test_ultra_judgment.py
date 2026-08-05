from __future__ import annotations

import copy
import hashlib
import importlib
import inspect
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

from tests.test_ultra_claim_mechanism import make_evidence_ledger
from tests.test_ultra_recursion import state_registry
from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.schemas import compute_artifact_content_sha256


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
    return importlib.import_module("ultra_runtime.judgment")


def authority_bundle() -> dict[str, Any]:
    evidence = make_evidence_ledger()
    graph = load_fixture("claim-mechanism-graph-valid.json")
    lineage = load_fixture("recursive-lineage-valid.json")
    order_evaluation = load_fixture("order-evaluation-valid.json")
    red_team = load_fixture("red-team-report-valid.json")
    states = state_registry()
    return {
        "evidence": evidence,
        "graph": graph,
        "lineage": lineage,
        "order_evaluation": order_evaluation,
        "red_team": red_team,
        "states": states,
    }


def authority_kwargs(
    bundle: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    accepted = dict(bundle or authority_bundle())
    return {
        "evidence_ledger": accepted["evidence"],
        "recursive_lineage": accepted["lineage"],
        "claim_mechanism_graph": accepted["graph"],
        "order_evaluation": accepted["order_evaluation"],
        "red_team_report": accepted["red_team"],
        "recursive_state_artifacts": accepted["states"],
        "expected_run_id": RUN_ID,
        "expected_version_binding": VERSION_BINDING,
        "expected_evidence_ledger_artifact_sha256": canonical_sha256(
            accepted["evidence"]
        ),
        "expected_claim_mechanism_graph_artifact_sha256": canonical_sha256(
            accepted["graph"]
        ),
        "expected_recursive_lineage_artifact_sha256": canonical_sha256(
            accepted["lineage"]
        ),
        "expected_order_evaluation_artifact_sha256": canonical_sha256(
            accepted["order_evaluation"]
        ),
        "expected_red_team_report_artifact_sha256": canonical_sha256(
            accepted["red_team"]
        ),
    }


def validate_with_authority(
    verdict: Mapping[str, object],
    bundle: Mapping[str, Any] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    kwargs = authority_kwargs(bundle)
    kwargs.update(overrides)
    return runtime()._validate_verdict_with_authority(verdict, **kwargs)


def seal_with_authority(
    verdict: Mapping[str, object],
    bundle: Mapping[str, Any] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    kwargs = authority_kwargs(bundle)
    kwargs.update(overrides)
    return runtime()._seal_verdict_bundle(verdict, **kwargs)


def five_by_kind(verdict: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["kind"]: item for item in verdict["five_verdicts"]}


def test_public_verdict_signature_is_unchanged_and_returns_none() -> None:
    module = runtime()
    signature = inspect.signature(module.validate_verdict_bundle)
    assert tuple(signature.parameters) == ("verdict", "evidence", "lineage")

    verdict = load_fixture("verdict-valid.json")
    bundle = authority_bundle()
    originals = copy.deepcopy((verdict, bundle["evidence"], bundle["lineage"]))
    assert (
        module.validate_verdict_bundle(
            verdict, bundle["evidence"], bundle["lineage"]
        )
        is None
    )
    assert (verdict, bundle["evidence"], bundle["lineage"]) == originals


def test_valid_low_evidence_verdict_binds_every_sealed_authority() -> None:
    verdict = load_fixture("verdict-valid.json")
    validated = validate_with_authority(verdict)
    assert validated == verdict
    assert validated["main_verdict"]["confidence"] == "low"
    assert validated["assumptions"]
    assert validated["main_verdict"]["reversal_conditions"]


def test_private_producer_recomputes_content_and_full_artifact_hashes() -> None:
    verdict = load_fixture("verdict-valid.json")
    unsealed = copy.deepcopy(verdict)
    unsealed.pop("content_sha256")
    sealed = seal_with_authority(unsealed)
    assert sealed == verdict

    stale_report_bundle = authority_bundle()
    stale_report_bundle["red_team"] = copy.deepcopy(stale_report_bundle["red_team"])
    stale_report_bundle["red_team"]["overall_status"] = "survives"
    with pytest.raises(ValueError):
        validate_with_authority(verdict, stale_report_bundle)


@pytest.mark.parametrize(
    "expected_field",
    (
        "expected_evidence_ledger_artifact_sha256",
        "expected_claim_mechanism_graph_artifact_sha256",
        "expected_recursive_lineage_artifact_sha256",
        "expected_order_evaluation_artifact_sha256",
        "expected_red_team_report_artifact_sha256",
    ),
)
def test_verdict_cannot_self_select_or_swap_external_authority(
    expected_field: str,
) -> None:
    with pytest.raises(ValueError):
        validate_with_authority(
            load_fixture("verdict-valid.json"),
            **{expected_field: "f" * 64},
        )


def test_substituted_sealed_u8_report_does_not_authorize_existing_verdict() -> None:
    bundle = authority_bundle()
    substituted = copy.deepcopy(bundle["red_team"])
    substituted["attacks"][0]["challenge"] = (
        "A substituted report cannot inherit the original report authority."
    )
    bundle["red_team"] = rehash_artifact(substituted)
    with pytest.raises(ValueError):
        validate_with_authority(load_fixture("verdict-valid.json"), bundle)


def test_evasive_complexity_without_a_ranking_is_rejected() -> None:
    bundle = authority_bundle()
    with pytest.raises(ValueError):
        runtime().validate_verdict_bundle(
            load_fixture("verdict-evasive-invalid.json"),
            bundle["evidence"],
            bundle["lineage"],
        )


def test_best_current_requires_exact_total_explanation_ranking() -> None:
    verdict = load_fixture("verdict-valid.json")
    verdict["explanation_ranking"][-1]["rank"] = 1
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_exact_non_decidability_allows_only_a_contiguous_partial_prefix() -> None:
    verdict = load_fixture("verdict-valid.json")
    verdict["judgment_kind"] = "non-decidability"
    verdict["main_verdict"] = None
    verdict["non_decidability"] = {
        "missing_proposition": (
            "Whether the local review channel remains active after the cutoff."
        ),
        "missing_comparison_rule": None,
    }
    verdict["partial_ranking_justification"] = (
        "The frozen material ranks only the first two explanations."
    )
    verdict["explanation_ranking"][2]["rank"] = None
    verdict["explanation_ranking"][3]["rank"] = None
    verdict = rehash_artifact(verdict)
    assert validate_with_authority(verdict) == verdict

    verdict["explanation_ranking"][1]["rank"] = 3
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_five_lock_ids_are_unique_and_disjoint_from_every_identity_domain() -> None:
    verdict = load_fixture("verdict-valid.json")
    five_by_kind(verdict)["fact"]["verdict_id"] = "CLAIM-CHANNEL-CONSTRAINT"
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_high_confidence_cannot_hide_a_decisive_unknown() -> None:
    verdict = load_fixture("verdict-valid.json")
    verdict["main_verdict"]["confidence"] = "high"
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_user_claim_alone_cannot_authorize_a_factual_lock() -> None:
    verdict = load_fixture("verdict-valid.json")
    fact = five_by_kind(verdict)["fact"]
    fact["evidence_refs"] = ["EVIDENCE-ASSOCIATION-CHARTER"]
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_unsupported_contradiction_is_not_rhetorical_toughness() -> None:
    verdict = load_fixture("verdict-valid.json")
    fact = five_by_kind(verdict)["fact"]
    fact["evidence_refs"] = []
    fact["claim_ids"] = []
    fact["mechanism_ids"] = []
    fact["recursive_node_ids"] = []
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_factual_lock_cannot_borrow_structural_refs_without_evidence() -> None:
    verdict = load_fixture("verdict-valid.json")
    five_by_kind(verdict)["fact"]["evidence_refs"] = []
    verdict = rehash_artifact(verdict)

    with pytest.raises(ValueError, match="material support|evidence_refs"):
        validate_with_authority(verdict)


def test_factual_lock_cannot_repeat_an_evidence_cannot_prove_scope() -> None:
    bundle = authority_bundle()
    verdict = load_fixture("verdict-valid.json")
    roster = next(
        entry
        for entry in bundle["evidence"]["entries"]
        if entry["evidence_id"] == "EVIDENCE-ROSTER-ATLAS"
    )
    five_by_kind(verdict)["fact"]["proposition"] = roster["cannot_prove"]
    verdict = rehash_artifact(verdict)

    with pytest.raises(
        ValueError,
        match="supported_claim|cannot_prove|support scope",
    ):
        validate_with_authority(verdict, bundle)


def test_value_lock_cannot_be_reused_as_factual_evidence() -> None:
    verdict = load_fixture("verdict-valid.json")
    fact = five_by_kind(verdict)["fact"]
    fact["evidence_refs"] = ["VERDICT-VALUE"]
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


def test_simulated_recursive_node_cannot_become_a_factual_lock() -> None:
    verdict = load_fixture("verdict-valid.json")
    fact = five_by_kind(verdict)["fact"]
    fact["recursive_node_ids"] = ["NODE-MAIN-ORDER-2"]
    verdict = rehash_artifact(verdict)
    with pytest.raises(ValueError):
        validate_with_authority(verdict)


ACTION_KINDS = (
    "active",
    "delay",
    "probe",
    "exit-or-transfer",
    "maintain-status-quo",
    "no-action",
)


def make_action_ranking(
    verdict: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    accepted_verdict = dict(verdict or load_fixture("verdict-valid.json"))
    authorization_id = five_by_kind(accepted_verdict)["authorization"]["verdict_id"]
    action: dict[str, Any] = {
        "schema_id": "crossframe.ultra.v82.action-ranking",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": copy.deepcopy(VERSION_BINDING),
        "generated_at": "2026-08-02T11:15:00Z",
        "phase_id": "U9",
        "verdict_artifact_sha256": canonical_sha256(accepted_verdict),
        "considered_verdict_ids": [
            item["verdict_id"] for item in accepted_verdict["five_verdicts"]
        ],
        "requested_choice": True,
        "options": [
            {
                "option_id": f"OPTION-{kind.upper()}",
                "kind": kind,
                "description": f"Compare the {kind} option independently.",
                "authorized": kind == "probe",
                "authorization_verdict_id": (
                    authorization_id if kind == "probe" else None
                ),
                "benefits": ["adds bounded information"],
                "harms": ["uses a bounded coordination interval"],
                "requirements": ["preserve the sealed evidence cutoff"],
                "rollback": "Return to the frozen baseline after one review cycle.",
            }
            for kind in ACTION_KINDS
        ],
        "ranking": [
            "OPTION-PROBE",
            "OPTION-DELAY",
            "OPTION-ACTIVE",
            "OPTION-MAINTAIN-STATUS-QUO",
            "OPTION-EXIT-OR-TRANSFER",
            "OPTION-NO-ACTION",
        ],
        "preferred_option_id": "OPTION-PROBE",
        "second_option_id": "OPTION-DELAY",
        "switch_conditions": [
            "Switch if the authorization lock is withdrawn."
        ],
        "stop_conditions": [
            "Stop if the bounded harm threshold is exceeded."
        ],
        "no_action_consequences": [
            "The decisive adaptation unknown remains unresolved."
        ],
    }
    return rehash_artifact(action)


def validate_action(
    action: Mapping[str, object],
    verdict: Mapping[str, object] | None = None,
    **overrides: object,
) -> dict[str, Any]:
    accepted_verdict = verdict or load_fixture("verdict-valid.json")
    bundle = authority_bundle()
    kwargs: dict[str, object] = {
        "verdict": accepted_verdict,
        "evidence": bundle["evidence"],
        "lineage": bundle["lineage"],
        "expected_verdict_artifact_sha256": canonical_sha256(accepted_verdict),
    }
    kwargs.update(overrides)
    return runtime()._validate_action_ranking(action, **kwargs)


def test_action_ranking_adds_no_public_runtime_entry_point() -> None:
    module = runtime()
    assert not hasattr(module, "validate_action_ranking")
    assert not hasattr(module, "seal_action_ranking")


def test_action_ranking_is_sealed_only_after_the_verdict() -> None:
    action = make_action_ranking()
    assert validate_action(action) == action

    unsealed = copy.deepcopy(action)
    unsealed.pop("content_sha256")
    bundle = authority_bundle()
    verdict = load_fixture("verdict-valid.json")
    sealed = runtime()._seal_action_ranking(
        unsealed,
        verdict=verdict,
        evidence=bundle["evidence"],
        lineage=bundle["lineage"],
        expected_verdict_artifact_sha256=canonical_sha256(verdict),
    )
    assert sealed == action


def test_action_considers_exactly_the_five_bound_lock_ids() -> None:
    action = make_action_ranking()
    action["considered_verdict_ids"][-1] = "VERDICT-FOREIGN"
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action)


@pytest.mark.parametrize("wrong_kind", ("prediction", "responsibility"))
def test_prediction_or_responsibility_lock_is_not_permission(
    wrong_kind: str,
) -> None:
    verdict = load_fixture("verdict-valid.json")
    action = make_action_ranking(verdict)
    probe = next(item for item in action["options"] if item["kind"] == "probe")
    probe["authorization_verdict_id"] = five_by_kind(verdict)[wrong_kind][
        "verdict_id"
    ]
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action, verdict)


def test_unauthorized_option_cannot_carry_an_authorization_reference() -> None:
    action = make_action_ranking()
    delay = next(item for item in action["options"] if item["kind"] == "delay")
    delay["authorization_verdict_id"] = "VERDICT-AUTHORIZATION"
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action)


def test_direct_choice_request_requires_a_real_preferred_and_second_option() -> None:
    action = make_action_ranking()
    action["preferred_option_id"] = "OPTION-NOT-CONSIDERED"
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action)

    action = make_action_ranking()
    action["second_option_id"] = action["preferred_option_id"]
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action)


def test_action_ranking_must_cover_each_option_exactly_once() -> None:
    action = make_action_ranking()
    action["ranking"][-1] = action["ranking"][0]
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action)


def make_gap_ledger(
    action: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    bundle = authority_bundle()
    verdict = load_fixture("verdict-valid.json")
    accepted_action = dict(action or make_action_ranking(verdict))
    gap: dict[str, Any] = {
        "schema_id": "crossframe.ultra.v82.framework-gap-ledger",
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": copy.deepcopy(VERSION_BINDING),
        "generated_at": "2026-08-02T11:20:00Z",
        "phase_id": "U10",
        "evidence_ledger_artifact_sha256": canonical_sha256(bundle["evidence"]),
        "claim_mechanism_graph_artifact_sha256": canonical_sha256(
            bundle["graph"]
        ),
        "recursive_lineage_artifact_sha256": canonical_sha256(bundle["lineage"]),
        "order_evaluation_artifact_sha256": canonical_sha256(
            bundle["order_evaluation"]
        ),
        "red_team_report_artifact_sha256": canonical_sha256(bundle["red_team"]),
        "verdict_artifact_sha256": canonical_sha256(verdict),
        "action_ranking_artifact_sha256": canonical_sha256(accepted_action),
        "forecast_ledger_artifact_sha256": "a" * 64,
        "candidates": [
            {
                "gap_id": "GAP-LATENCY-CALIBRATION",
                "description": "The current framework has no calibrated latency prior.",
                "evidence_refs": ["EVIDENCE-ROSTER-ATLAS"],
                "claim_ids": ["CLAIM-CHANNEL-CONSTRAINT"],
                "mechanism_ids": ["MECHANISM-REVIEW-CHANNEL"],
                "recursive_node_ids": ["NODE-MAIN-ORDER-1"],
                "route_ids": ["ROUTE-CHANNEL"],
                "concept_ids": ["V82-CONCEPT-CHANNEL"],
                "future_revision_proposal": (
                    "Consider a latency calibration contract in a future revision."
                ),
                "status": "candidate",
            }
        ],
        "isolated_from_current_reasoning": True,
    }
    return rehash_artifact(gap)


def validate_gap(gap: Mapping[str, object]) -> dict[str, Any]:
    bundle = authority_bundle()
    verdict = load_fixture("verdict-valid.json")
    action = make_action_ranking(verdict)
    return runtime()._validate_framework_gap_isolation(
        gap,
        claim_mechanism_graph=bundle["graph"],
        verdict=verdict,
        action_ranking=action,
    )


def test_u10_gap_remains_an_isolated_future_candidate() -> None:
    gap = make_gap_ledger()
    assert validate_gap(gap) == gap

    captured = copy.deepcopy(gap)
    captured["isolated_from_current_reasoning"] = False
    captured = rehash_artifact(captured)
    with pytest.raises(ValueError):
        validate_gap(captured)


def test_gap_identity_cannot_become_current_u6_or_u9_authority() -> None:
    gap = make_gap_ledger()
    gap["candidates"][0]["gap_id"] = "MECHANISM-REVIEW-CHANNEL"
    gap = rehash_artifact(gap)
    with pytest.raises(ValueError):
        validate_gap(gap)

    action = make_action_ranking()
    probe = next(item for item in action["options"] if item["kind"] == "probe")
    probe["authorization_verdict_id"] = "GAP-LATENCY-CALIBRATION"
    action = rehash_artifact(action)
    with pytest.raises(ValueError):
        validate_action(action)
