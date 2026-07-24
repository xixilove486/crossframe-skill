from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Mapping, Sequence

from promax_runtime.artifacts import (
    build_artifact_manifest,
    build_capability_disclosure,
    initialize_run,
    inventory_artifacts,
)
from promax_runtime.jsonio import canonical_json_bytes, load_json, sha256_json
from promax_runtime.position import selection_review_basis_sha256
from promax_runtime.prose import PROSE_REVIEW_DIMENSION_IDS
from promax_runtime.schemas import validate_instance
from promax_runtime.source_integrity import (
    V8_SOURCE_SNAPSHOT_SHA256,
    load_canonical_read_targets,
    sha256_file,
)
from promax_runtime.retrieval import RETRIEVAL_DIRECTIONS
from promax_runtime.state_machine import (
    RunBinding,
    seal_phase_event,
    validate_phase_history,
)


FIXTURE_CATALOG = Path("tests/fixtures/promax-runtime/scenarios.json")
FIXTURE_CLASSES = {"positive", "incomplete", "adversarial"}
FIXTURE_CONCEPT_ID = "V8-CANON-ACTOR-STATE"
CENTRAL_CLAIM_STATEMENT = (
    "A bounded transfer mechanism best explains the observed structural update."
)
STANCE_NEUTRAL_SEMANTIC_PAYLOAD = {
    "analysis_object": "Fixture analysis object",
    "proposition_under_test": CENTRAL_CLAIM_STATEMENT,
    "time_window": "P90D",
}
OPTION_IDS_BY_OPTION_KIND = (
    ("probe_action", "OPTION-PROBE"),
    ("active_action", "OPTION-ACTIVE"),
    ("maintain_status_quo", "OPTION-STATUS-QUO"),
    ("delayed_action", "OPTION-DELAYED"),
    ("exit_or_transfer", "OPTION-EXIT"),
    ("no_action", "OPTION-NO-ACTION"),
)
LOW_INFORMATION_RANKING = tuple(
    option_id for _option_kind, option_id in OPTION_IDS_BY_OPTION_KIND
)
HOUSE_OPTION_KIND_RANKING = tuple(
    option_kind for option_kind, _option_id in OPTION_IDS_BY_OPTION_KIND
)
LOW_INFORMATION_EVALUATION_DIMENSIONS = (
    "structural explanatory power",
    "reversibility",
    "risk",
)
VALIDATOR_VERSIONS = {
    "schema": "1.0.0",
    "source-integrity": "1.0.0",
    "version-isolation": "1.0.0",
    "concept-closure": "1.0.0",
    "claim-path": "1.0.0",
    "retrieval": "1.0.0",
    "position": "1.0.0",
    "output": "1.0.0",
    "prose": "1.0.0",
    "manifest": "1.0.0",
    "state-machine": "1.0.0",
    "continuation": "1.0.0",
}


def _shift_iso_timestamp(value: str, *, seconds: int) -> str:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("fixture timestamps must include a timezone")
    shifted = parsed.astimezone(timezone.utc) + timedelta(seconds=seconds)
    return shifted.isoformat(timespec="seconds").replace("+00:00", "Z")


def _build_stance_neutral_problem() -> dict[str, object]:
    payload = copy.deepcopy(STANCE_NEUTRAL_SEMANTIC_PAYLOAD)
    return {
        **payload,
        "evidence_cutoff": "2026-07-23T00:00:00Z",
        "semantic_key_sha256": sha256_json(payload),
    }


def _build_recommendation_options() -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    for index, (option_kind, option_id) in enumerate(
        OPTION_IDS_BY_OPTION_KIND,
        start=1,
    ):
        option: dict[str, object] = {
            "option_id": option_id,
            "option_kind": option_kind,
            "description": f"Fixture option {index}: {option_kind}",
            "forecast_refs": ["FORECAST-FIXTURE-1"],
            "normative_premise_refs": ["N1", "N2"],
            "affected_position_refs": ["POSITION-AFFECTED-1"],
            "rights_floor_refs": ["PF-1"],
            "expected_paths": [f"PATH-FIXTURE-{index}"],
            "worst_acceptable_outcome": "Damage remains below the frozen ceiling",
            "cross_circle_spillovers": ["Record adjacent-circle spillovers"],
            "distribution_of_costs_and_benefits": "Record costs and benefits by affected position",
            "information_value": "Produces discriminating evidence for the next review",
            "lock_in_risk": "Low lock-in with explicit escalation conditions",
            "reversibility": "Can stop and return to the frozen state",
            "resource_cost": "Requires bounded resources",
            "authorized_actor_ref": "UNRESOLVED-DECISION-ACTOR",
            "authorization_record_ref": "UNRESOLVED-AUTHORIZATION-SOURCE",
            "stop_conditions": ["Stop when the registered boundary evidence fails"],
            "rollback_and_remedy": ["Return to the frozen pre-action state and remedy harm"],
        }
        options.append(option)
    return options


def _build_selection_review_wrapper(
    *,
    option_ids: Sequence[str],
    evaluation_dimensions: Sequence[str],
    preferred_option_id: str,
    reviewed_at: str,
) -> dict[str, object]:
    return {
        "wrapper_schema_id": "crossframe.promax.selection-review-wrapper",
        "wrapper_schema_version": 1,
        "wrapper_role": "promax_machine_verification_wrapper_not_v8_source_schema",
        "source_paragraph_refs": [
            "V8-P3561",
            "V8-P3564",
            "V8-P3569",
            "V8-P3570",
            "V8-P3571",
            "V8-P3572",
            "V8-P3574",
            "V8-P3575",
            "V8-P3580",
            "V8-P3581",
            "V8-P3584",
            "V8-P3587",
            "V8-P3588",
            "V8-P3589",
            "V8-P3596",
            "V8-P3598",
            "V8-P3599",
            "V8-P3601",
            "V8-P3602",
        ],
        "selection_type": "SEL-AGT",
        "selection_status": "under_review",
        "public_value_premises": [
            {
                "normative_principle_id": "N1",
                "role": "veto_gate",
                "statement": "解释不授权处置",
            },
            {
                "normative_principle_id": "N2",
                "role": "constraint",
                "statement": "保护不得降级",
            },
        ],
        "value_conflicts": [
            {
                "conflict_id": "VALUE-CONFLICT-FIXTURE-1",
                "premise_ids": ["N1", "N2"],
                "affected_position_refs": ["POSITION-AFFECTED-1"],
                "dissent_refs": ["DISSENT-FIXTURE-1"],
                "decision_rule": "Keep the choice under review while protection remains unresolved.",
                "status": "open",
            }
        ],
        "unresolved_dissent_refs": ["DISSENT-FIXTURE-1"],
        "rights_floor": ["PF-1"],
        "affected_positions": ["POSITION-AFFECTED-1"],
        "low_power_position_ids": ["POSITION-AFFECTED-1"],
        "jurisdiction_review_boundary": {
            "boundary_role": "promax_review_boundary_not_atomic_v8_j_tuple",
            "reviewed_option_id": preferred_option_id,
            "decision_actor_ref": "UNRESOLVED-DECISION-ACTOR",
            "authorization_source_ref": "UNRESOLVED-AUTHORIZATION-SOURCE",
            "jurisdiction_ref": "UNRESOLVED-JURISDICTION",
            "scope": "analysis_only",
            "valid_from": "2026-07-23T00:00:00Z",
            "valid_until": "2026-07-24T00:00:00Z",
            "authorization_status": "not_authorized",
        },
        "procedure_states": {
            "O1": "complete",
            "O2": "complete",
            "O3": "in_review",
            "O4": "not_started",
        },
        "least_harm": {
            "principle_id": "NSP-LEAST-HARM",
            "principle_version": "v8",
            "selected_option_id": preferred_option_id,
            "compared_option_ids": list(option_ids),
            "evaluation_dimensions": list(evaluation_dimensions),
            "sufficient_reason": "The low-information result is only a pending preference for the narrow reversible probe.",
            "evidence_refs": [],
            "reviewer_ref": "REVIEWER-INDEPENDENT-1",
            "reviewed_at": reviewed_at,
            "status": "pending",
        },
        "proportionality": {
            "principle_id": "NSP-PROPORTIONALITY",
            "principle_version": "v8",
            "selected_option_id": preferred_option_id,
            "compared_option_ids": list(option_ids),
            "evaluation_dimensions": list(evaluation_dimensions),
            "sufficient_reason": "Suitability, necessity, rights cost, intensity, scope, and duration remain pending review.",
            "evidence_refs": [],
            "reviewer_ref": "REVIEWER-INDEPENDENT-1",
            "reviewed_at": reviewed_at,
            "status": "pending",
        },
        "declared_low_information_house_policy_eligibility": {
            "case_specific_facts_present": False,
            "choice_changing_retrieval_evidence_present": False,
            "basis": "The fixture supplies neither case facts nor choice-changing retrieval evidence.",
        },
        "ranking_support": [],
    }


def _recommendation_ranking_projections(
    options: Sequence[Mapping[str, object]],
) -> tuple[list[str], list[str]]:
    options_by_id = {str(option["option_id"]): option for option in options}
    return (
        [str(options_by_id[option_id]["option_kind"]) for option_id in LOW_INFORMATION_RANKING],
        [
            sha256_json(
                {
                    key: copy.deepcopy(value)
                    for key, value in options_by_id[option_id].items()
                    if key != "option_id"
                }
            )
            for option_id in LOW_INFORMATION_RANKING
        ],
    )


def build_read_events(
    repo: Path | str,
    *,
    run_id: str,
    read_at: str,
) -> list[dict[str, object]]:
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be substantive")
    if not isinstance(read_at, str) or not read_at.strip():
        raise ValueError("read_at must be substantive")
    return [
        {
            "schema_id": "crossframe.promax.v8.read-event",
            "schema_version": 1,
            "event_id": f"read-event-{sequence:06d}",
            "run_id": run_id,
            "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "sequence": sequence,
            "source_kind": target["source_kind"],
            "source_anchor": target["source_anchor"],
            "source_file": target["source_file"],
            "content_sha256": target["content_sha256"],
            "read_at": read_at,
        }
        for sequence, target in enumerate(
            load_canonical_read_targets(repo), start=1
        )
    ]


def _unique_strings(*values: object) -> list[str]:
    result: list[str] = []
    for value in values:
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise ValueError("canonical concept string arrays are malformed")
        for item in value:
            if item not in result:
                result.append(item)
    return result


def _string_leaves(value: object) -> list[str]:
    if isinstance(value, Mapping):
        result: list[str] = []
        for child in value.values():
            result.extend(_string_leaves(child))
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = []
        for child in value:
            result.extend(_string_leaves(child))
        return result
    return [value] if isinstance(value, str) and value.strip() else []


def build_concept_disposition(
    repo: Path | str,
    *,
    run_id: str,
    completed_at: str,
    route_ids: Sequence[str] | None = None,
    applied_concept_ids: Sequence[str] = (),
) -> dict[str, object]:
    root = Path(repo).resolve()
    registry_path = (
        root
        / "skills"
        / "crossframe-promax"
        / "references"
        / "concept-registry"
        / "v8-concept-registry.json"
    )
    route_path = (
        root
        / "skills"
        / "crossframe-promax"
        / "references"
        / "v8-route-map.json"
    )
    registry = load_json(registry_path)
    routes = load_json(route_path)
    if not isinstance(registry, dict) or not isinstance(routes, dict):
        raise ValueError("canonical registry and route map must be objects")
    raw_concepts = registry.get("concepts")
    raw_routes = routes.get("routes")
    if not isinstance(raw_concepts, list) or len(raw_concepts) != 709:
        raise ValueError("canonical concept inventory must contain 709 records")
    if not isinstance(raw_routes, list) or not raw_routes:
        raise ValueError("canonical route inventory is empty")
    available_routes = {
        route.get("route_id")
        for route in raw_routes
        if isinstance(route, Mapping) and isinstance(route.get("route_id"), str)
    }
    selected_routes = (
        list(route_ids)
        if route_ids is not None
        else [str(raw_routes[0]["route_id"])]
    )
    if not selected_routes or len(set(selected_routes)) != len(selected_routes):
        raise ValueError("fixture route_ids must be nonempty and unique")
    if any(route_id not in available_routes for route_id in selected_routes):
        raise ValueError("fixture route_id is absent from the canonical route map")
    concept_ids = {
        concept.get("concept_id")
        for concept in raw_concepts
        if isinstance(concept, Mapping)
        and isinstance(concept.get("concept_id"), str)
    }
    if len(concept_ids) != 709:
        raise ValueError("canonical concept identities are not unique")
    applied = set(applied_concept_ids)
    if applied - concept_ids:
        raise ValueError("applied fixture concept is absent from the registry")

    dispositions: list[dict[str, object]] = []
    for concept in raw_concepts:
        if not isinstance(concept, Mapping):
            raise ValueError("canonical concept record must be an object")
        concept_id = concept.get("concept_id")
        if not isinstance(concept_id, str):
            raise ValueError("canonical concept_id must be text")
        is_applied = concept_id in applied
        neighbors = concept.get("required_neighbor_ids")
        if not isinstance(neighbors, list) or not all(
            isinstance(item, str) for item in neighbors
        ):
            raise ValueError("canonical concept neighbors are malformed")
        excluded_misuses = _unique_strings(
            concept.get("common_misuses"),
            concept.get("forbidden_substitutions_or_generalizations"),
        )
        dispositions.append(
            {
                "concept_id": concept_id,
                "status": "applied" if is_applied else "not_applicable",
                "rationale": (
                    "Applied to the fixture object using the exact registered definition."
                    if is_applied
                    else "Checked against the exact registered definition and excluded for the fixture object."
                ),
                "evidence_refs": ["EVIDENCE-FIXTURE-1"] if is_applied else [],
                "required_neighbor_ids": list(neighbors),
                "misuses_excluded": excluded_misuses,
                "output_section_ids": ["SECTION-CONCEPTS"] if is_applied else [],
                "pending_evidence": [],
            }
        )
    return {
        "schema_id": "crossframe.promax.v8.concept-disposition",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "registry_sha256": sha256_file(registry_path),
        "route_ids": selected_routes,
        "dispositions": dispositions,
        "unchecked_concept_ids": [],
        "closure_complete": True,
        "completed_at": completed_at,
    }


def build_claim_path_graph(
    *,
    run_id: str,
    updated_at: str,
    concept_ids: Sequence[str] = (FIXTURE_CONCEPT_ID,),
) -> dict[str, object]:
    central_claim_id = "CLAIM-CENTRAL"
    mechanism_ids = ["MECH-1", "MECH-2", "MECH-3"]
    return {
        "schema_id": "crossframe.promax.v8.claim-path-graph",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": central_claim_id,
        "stance_neutral_problem": _build_stance_neutral_problem(),
        "central_claim_cycle": {
            "central_claim_id": central_claim_id,
            "initial_judgment": "The bounded transfer mechanism is the leading conditional explanation.",
            "strongest_attack": "Selection effects could reproduce the observations without transfer.",
            "revision": "Retain the claim only where temporal order and transfer evidence are observed.",
            "counterfactual": "Without the transfer channel, the downstream state should not update.",
            "withdrawal_conditions": [
                "Withdraw when the selection baseline explains the observations out of sample."
            ],
        },
        "claims": [
            {
                "claim_id": central_claim_id,
                "statement": CENTRAL_CLAIM_STATEMENT,
                "claim_type": "mechanistic",
                "evidence_refs": [
                    "EVIDENCE-FIXTURE-1",
                    "EVIDENCE-FIXTURE-2",
                ],
                "concept_ids": list(concept_ids),
                "confidence": "medium",
                "authorization_ceiling": "Diagnostic comparison only; no action is authorized.",
            }
        ],
        "mechanisms": [
            {
                "mechanism_id": mechanism_id,
                "label": f"Competing mechanism {index}",
                "claim_ids": [central_claim_id],
                "distinguishing_conditions": [
                    f"Observable discriminator for mechanism {index}"
                ],
            }
            for index, mechanism_id in enumerate(mechanism_ids, start=1)
        ],
        "path_nodes": [
            {
                "node_id": "NODE-START",
                "label": "Observed starting state",
                "node_type": "state",
                "trigger_conditions": ["The registered transfer channel becomes active"],
                "early_signals": ["A directional update appears at the interface"],
                "reverse_signals": ["The update precedes activation of the channel"],
                "stop_conditions": ["The channel is absent or the object boundary changes"],
            },
            {
                "node_id": "NODE-OUTCOME",
                "label": "Conditional downstream outcome",
                "node_type": "outcome",
                "trigger_conditions": ["The branch condition remains satisfied"],
                "early_signals": [],
                "reverse_signals": [],
                "stop_conditions": ["The outcome is observed or the horizon ends"],
            },
        ],
        "path_edges": [
            {
                "edge_id": "EDGE-1",
                "from_node_id": "NODE-START",
                "to_node_id": "NODE-OUTCOME",
                "mechanism_ids": mechanism_ids,
                "condition": "The early signal persists and no reverse signal appears.",
                "outcome_writeback": "Write the outcome to claim confidence and path rank.",
            }
        ],
        "forecast_conditions": ["The object identity criterion remains unchanged"],
        "choice_boundary": "The graph informs diagnosis and does not authorize intervention.",
        "updated_at": updated_at,
    }


def build_retrieval_ledger(
    *,
    run_id: str,
    completed_at: str,
    central_claim_id: str = "CLAIM-CENTRAL",
    network_available: bool = True,
) -> dict[str, object]:
    relations = {
        "support": "supports",
        "reverse": "refutes",
        "failure": "refutes",
        "alternative_mechanism": "alternative_mechanism",
        "affected_or_low_power": "affected_position",
    }
    source_records = (
        ("https://www.nist.gov/", "NIST", "National Institute of Standards and Technology"),
        ("https://www.who.int/", "WHO", "World Health Organization"),
        ("https://www.oecd.org/", "OECD", "Organisation for Economic Co-operation and Development"),
        ("https://www.un.org/", "United Nations", "United Nations"),
        ("https://www.worldbank.org/", "World Bank", "World Bank"),
    )
    entries: list[dict[str, object]] = []
    for index, direction in enumerate(RETRIEVAL_DIRECTIONS, start=1):
        url, title, publisher = source_records[index - 1]
        sources: list[dict[str, object]] = []
        if network_available:
            sources.append(
                {
                    "url": url,
                    "title": title,
                    "publisher": publisher,
                    "published_at": "2026-07-20",
                    "event_date": "2026-07-19",
                    "source_type": "official",
                    "interest_relevance": "The publisher identity is retained for source-interest evaluation.",
                    "independence_group": f"fixture-origin-{index}",
                    "duplicate_relation": "independent",
                    "duplicate_of_url": None,
                }
            )
        entries.append(
            {
                "retrieval_id": f"RETRIEVAL-{index}",
                "round": 1 if index <= 3 else 2,
                "direction": direction,
                "claim_relation": relations[direction],
                "query": f"Auditable fixture query for {direction}",
                "tool": "verified-web-retrieval",
                "retrieved_at": completed_at,
                "sources": sources,
                "claim_ids": [central_claim_id],
                "finding": f"Structured fixture finding for {direction}",
                "cannot_prove": [
                    "This query cannot alone prove the full mechanism or authorize action."
                ],
                "stop_reason": "The registered direction has an auditable result for this round.",
            }
        )
    return {
        "schema_id": "crossframe.promax.v8.retrieval-ledger",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "entries": entries,
        "saturation_rounds": [
            {
                "round": 1,
                "substantive_novelty": False,
                "changed_claim_ids": [],
                "stop_reason": "No claim, concept state, path rank, or action ceiling changed.",
            },
            {
                "round": 2,
                "substantive_novelty": False,
                "changed_claim_ids": [],
                "stop_reason": "A second consecutive round produced no substantive change.",
            },
        ],
        "network_available": network_available,
        "completed_at": completed_at,
    }


def build_local_world_model(
    *,
    run_id: str,
    locked_at: str,
) -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.local-world-model",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "phase_id": "P3",
        "object_boundary": {
            "object_id": "OBJ-FIXTURE-1",
            "name": "Fixture analysis object",
            "in_scope": ["Observed structural relations"],
            "out_of_scope": ["Unauthorized real-world action"],
        },
        "actor_records": [
            {
                "actor_id": "ACTOR-FIXTURE-1",
                "label": "Fixture actor",
                "roles": ["Decision participant"],
                "observed_state": ["A preference was expressed"],
                "inferred_state": ["Conditional hypothesis only"],
                "inference_limits": [
                    "One act cannot establish a stable personality judgment"
                ],
            }
        ],
        "circle_candidates": [
            {
                "circle_id": "CIRCLE-FIXTURE-1",
                "label": "Candidate circle",
                "membership_basis": ["Observable interaction"],
                "reification_risks": ["A label does not establish an entity"],
            }
        ],
        "scale_profile": {
            "focal_scale": "Actor and organization interface",
            "included_scales": ["actor", "organization"],
            "excluded_scales": ["unsupported historical stage"],
            "transformation_limits": [
                "Cross-scale claims require explicit transformation conditions"
            ],
        },
        "material_channel": {
            "state": ["Resource constraint"],
            "observables": ["Budget"],
            "unknowns": ["Hidden cost"],
        },
        "experiential_meaning_channel": {
            "state": ["Competing interpretations"],
            "observables": ["Public statement"],
            "unknowns": ["Unexpressed experience"],
        },
        "M_state": {
            "description": "Material and structural state",
            "evidence_refs": ["EVIDENCE-FIXTURE-1"],
            "uncertainties": ["Measurement error"],
        },
        "Psi_state": {
            "description": "Experiential and meaning state",
            "evidence_refs": ["EVIDENCE-FIXTURE-2"],
            "uncertainties": ["Interpretive competition"],
        },
        "clocks": [
            {
                "clock_id": "CLOCK-FIXTURE-1",
                "label": "Decision clock",
                "current_time": locked_at,
                "horizon": "P90D",
                "lag": "P7D",
            }
        ],
        "events": [
            {
                "event_id": "EVENT-FIXTURE-1",
                "event_type": "observed",
                "time": locked_at,
                "description": "The fixture request entered analysis",
                "evidence_refs": ["EVIDENCE-FIXTURE-1"],
            }
        ],
        "evidence_cutoff": locked_at,
        "unknowns": [
            {
                "unknown_id": "UNKNOWN-FIXTURE-1",
                "question": "Which evidence would most change the path ordering?",
                "decision_impact": "It may change the preferred option",
                "retrieval_plan": "Search reverse and failure cases",
            }
        ],
        "residuals": [
            {
                "residual_id": "RESIDUAL-FIXTURE-1",
                "description": "Residual outside the current model",
                "handling": "Keep it explicit and unabsorbed",
            }
        ],
        "identity_criteria": [
            {
                "criterion": "Object boundary remains stable over the horizon",
                "test": "Refreeze the object when the boundary changes",
            }
        ],
        "action_limits": ["Analysis does not automatically authorize action"],
        "authorization_limits": [
            "An authorized decision maker must separately approve real action"
        ],
        "locked_at": locked_at,
    }


def build_red_team_report(
    *,
    run_id: str,
    completed_at: str,
    recommendation_locked_at: str | None = None,
    central_claim_id: str = "CLAIM-CENTRAL",
    evidence_basis_sha256: str | None = None,
) -> dict[str, object]:
    evidence_hash = evidence_basis_sha256 or sha256_json(
        {"evidence": "fixture-evidence-set"}
    )
    problem_key_sha256 = _build_stance_neutral_problem()["semantic_key_sha256"]
    central_statement_sha256 = sha256_json(CENTRAL_CLAIM_STATEMENT)
    options = _build_recommendation_options()
    option_kind_ranking, option_semantic_ranking = (
        _recommendation_ranking_projections(options)
    )
    evaluation_dimensions = [*LOW_INFORMATION_EVALUATION_DIMENSIONS]
    selection_basis_sha256 = selection_review_basis_sha256(
        {
            "options": options,
            "evaluation_dimensions": evaluation_dimensions,
            "preferred_option_id": "OPTION-PROBE",
            "ranking_policy": "promax_low_information_house_policy_not_v8",
            "ranking_evidence_refs": [],
            "locked_at": (
                recommendation_locked_at
                or _shift_iso_timestamp(completed_at, seconds=1)
            ),
            "selection_review_wrapper": _build_selection_review_wrapper(
                option_ids=[
                    str(option["option_id"]) for option in options
                ],
                evaluation_dimensions=evaluation_dimensions,
                preferred_option_id="OPTION-PROBE",
                reviewed_at=completed_at,
            ),
        }
    )
    pro_prompt = "fixture-pro-prompt"
    anti_prompt = "fixture-anti-prompt"
    return {
        "schema_id": "crossframe.promax.v8.red-team-report",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": central_claim_id,
        "attacks": [
            {
                "attack_id": "ATTACK-BOUNDARY",
                "attack_class": "boundary_error",
                "target_id": central_claim_id,
                "challenge": "Was the object boundary frozen incorrectly?",
                "counterevidence_refs": ["EVIDENCE-FIXTURE-2"],
                "strongest_counterposition": "The object boundary may be unstable.",
                "result": "survived_with_revision",
                "revision": "Reduce judgment strength and refreeze the object if its boundary changes.",
                "position_impact": "high",
            },
            {
                "attack_id": "ATTACK-AUTHORIZATION",
                "attack_class": "prediction_authorization_leakage",
                "target_id": central_claim_id,
                "challenge": "Did the forecast improperly grant action authority?",
                "counterevidence_refs": [],
                "strongest_counterposition": "Prediction cannot create real-world authorization.",
                "result": "survived",
                "revision": "Keep an independent authorization ceiling.",
                "position_impact": "medium",
            },
        ],
        "stability_checks": [
            {
                "prompt_pair_id": "PAIR-FIXTURE-1",
                "pro_prompt": pro_prompt,
                "anti_prompt": anti_prompt,
                "pro_prompt_sha256": sha256_json(pro_prompt),
                "anti_prompt_sha256": sha256_json(anti_prompt),
                "evidence_basis_sha256_before": evidence_hash,
                "evidence_basis_sha256_after": evidence_hash,
                "semantic_problem_sha256_before": problem_key_sha256,
                "semantic_problem_sha256_after": problem_key_sha256,
                "central_position_id_before": central_claim_id,
                "central_position_id_after": central_claim_id,
                "central_statement_sha256_before": central_statement_sha256,
                "central_statement_sha256_after": central_statement_sha256,
                "relation_to_proposition_before": "supports",
                "relation_to_proposition_after": "supports",
                "judgment_strength_before": "moderate",
                "judgment_strength_after": "moderate",
                "option_ranking_before": [
                    *LOW_INFORMATION_RANKING,
                ],
                "option_ranking_after": [
                    *LOW_INFORMATION_RANKING,
                ],
                "option_kind_ranking_before": [*option_kind_ranking],
                "option_kind_ranking_after": [*option_kind_ranking],
                "option_semantic_ranking_before": [*option_semantic_ranking],
                "option_semantic_ranking_after": [*option_semantic_ranking],
                "normative_selection_basis_sha256_before": selection_basis_sha256,
                "normative_selection_basis_sha256_after": selection_basis_sha256,
                "position_drift": "none",
                "explanation": "The evidence did not change, so user stance did not change the position.",
            }
        ],
        "revision_summary": [
            "Reduce judgment strength and refreeze the object if its boundary changes."
        ],
        "completed_at": completed_at,
    }


def build_position_lock(
    *,
    run_id: str,
    locked_at: str,
    central_claim_id: str = "CLAIM-CENTRAL",
) -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.position",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": central_claim_id,
        "relation_to_proposition": "supports",
        "proposition_verdict": f"VERDICT[supports] {CENTRAL_CLAIM_STATEMENT}",
        "position": f"VERDICT[supports] {CENTRAL_CLAIM_STATEMENT} Current evidence favors the bounded transfer mechanism.",
        "judgment_strength": "moderate",
        "primary_reasons": [
            CENTRAL_CLAIM_STATEMENT,
            "Reduce judgment strength and refreeze the object if its boundary changes.",
        ],
        "runner_up_explanation": "Competing mechanism 2 becomes the runner-up when the object boundary changes.",
        "strongest_counterevidence": ["The object boundary may be unstable."],
        "why_not_adopted": [
            "Current evidence does not show that the registered boundary has changed."
        ],
        "withdrawal_conditions": [
            "If The object boundary may be unstable. is confirmed, withdraw the current judgment."
        ],
        "action_ceiling": "Analysis only; real-world action is not authorized and requires separate authorization.",
        "locked_at": locked_at,
    }


def build_recommendation_lock(
    position: Mapping[str, object],
    *,
    run_id: str,
    locked_at: str,
) -> dict[str, object]:
    options = _build_recommendation_options()
    option_kind_ranking, option_semantic_ranking = (
        _recommendation_ranking_projections(options)
    )
    options_by_id = {str(option["option_id"]): option for option in options}
    evaluation_dimensions = [*LOW_INFORMATION_EVALUATION_DIMENSIONS]
    return {
        "schema_id": "crossframe.promax.v8.recommendation",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "position_sha256": sha256_json(dict(position)),
        "options": options,
        "evaluation_dimensions": evaluation_dimensions,
        "ranking": [*LOW_INFORMATION_RANKING],
        "ranking_policy": "promax_low_information_house_policy_not_v8",
        "ranking_evidence_refs": [],
        "selection_review_wrapper": _build_selection_review_wrapper(
            option_ids=list(options_by_id),
            evaluation_dimensions=evaluation_dimensions,
            preferred_option_id="OPTION-PROBE",
            reviewed_at=_shift_iso_timestamp(locked_at, seconds=-60),
        ),
        "option_kind_ranking": option_kind_ranking,
        "option_record_hashes": [
            {"option_id": option_id, "record_sha256": sha256_json(option)}
            for option_id, option in options_by_id.items()
        ],
        "option_semantic_ranking": option_semantic_ranking,
        "preferred_option_id": "OPTION-PROBE",
        "second_option_id": "OPTION-ACTIVE",
        "no_action_option_id": "OPTION-NO-ACTION",
        "switch_conditions": [
            "Switch to OPTION-ACTIVE when the object boundary changes."
        ],
        "inaction_consequences": ["Inaction continues to accumulate opportunity cost"],
        "authorization_status": "conditional_recommendation_only",
        "locked_at": locked_at,
    }


def build_output_plan(
    *,
    run_id: str,
    locked_at: str,
    concept_ids: Sequence[str] = (FIXTURE_CONCEPT_ID,),
    central_claim_id: str = "CLAIM-CENTRAL",
) -> dict[str, object]:
    example_ids = [
        f"EX-M{mechanism}-S{example}"
        for mechanism in range(1, 4)
        for example in range(1, 3)
    ]
    counterexample_ids = [
        f"EX-M{mechanism}-F1" for mechanism in range(1, 4)
    ]
    section_id = "SECTION-CONCEPTS"
    core_concept_ids = list(concept_ids[:1])
    atlas_only_concept_ids = list(concept_ids[1:])
    return {
        "schema_id": "crossframe.promax.v8.output-plan",
        "schema_version": 2,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "sections": [
            {
                "section_id": section_id,
                "title": "中心判断、v8 概念、机制、案例与反例",
                "concept_ids": list(concept_ids),
                "claim_ids": [central_claim_id],
                "mechanism_ids": ["MECH-1", "MECH-2", "MECH-3"],
                "path_node_ids": ["NODE-START", "NODE-OUTCOME"],
                "example_ids": example_ids,
                "counterexample_ids": counterexample_ids,
                "judgment_ids": ["POSITION-LOCK", "RECOMMENDATION-LOCK"],
                "artifact_paths": [
                    "promax-dossier.md",
                    "promax-concept-atlas.md",
                    "promax-case-and-countercase.md",
                    "promax-essay.md",
                ],
            }
        ],
        "reader_projection": {
            "article_type": "public-commentary",
            "house_voice_id": "crossframe-promax",
            "thesis_claim_id": central_claim_id,
            "core_concept_ids": core_concept_ids,
            "atlas_only_concept_ids": atlas_only_concept_ids,
            "selected_techniques": [
                {
                    "technique_id": "event-association",
                    "tier": "core",
                    "paragraph_action": "由现实事件进入其背后的成本与承担关系",
                    "section_ids": [section_id],
                },
                {
                    "technique_id": "layered-argument",
                    "tier": "core",
                    "paragraph_action": "把事实、机制、反方、判断与行动边界分层推进",
                    "section_ids": [section_id],
                },
                {
                    "technique_id": "positive-negative-contrast",
                    "tier": "core",
                    "paragraph_action": "在同一标准下对照中心解释与竞争解释",
                    "section_ids": [section_id],
                },
            ],
            "reader_beats": [
                {
                    "beat_id": "BEAT-REALITY-ENTRY",
                    "function": "现实入口与中心命题",
                    "section_ids": [section_id],
                    "claim_ids": [central_claim_id],
                    "mechanism_ids": ["MECH-1"],
                    "evidence_refs": ["EVIDENCE-FIXTURE-1"],
                    "core_concept_ids": core_concept_ids,
                    "technique_ids": [
                        "event-association",
                        "layered-argument",
                    ],
                },
                {
                    "beat_id": "BEAT-COMPARISON",
                    "function": "竞争机制的同维比较与证据边界",
                    "section_ids": [section_id],
                    "claim_ids": [central_claim_id],
                    "mechanism_ids": ["MECH-1", "MECH-2", "MECH-3"],
                    "evidence_refs": [
                        "EVIDENCE-FIXTURE-1",
                        "EVIDENCE-FIXTURE-2",
                    ],
                    "core_concept_ids": core_concept_ids,
                    "technique_ids": [
                        "layered-argument",
                        "positive-negative-contrast",
                    ],
                },
                {
                    "beat_id": "BEAT-COUNTER-BOUNDARY",
                    "function": "最强反方、撤回条件与行动边界",
                    "section_ids": [section_id],
                    "claim_ids": [central_claim_id],
                    "mechanism_ids": ["MECH-2"],
                    "evidence_refs": ["EVIDENCE-FIXTURE-2"],
                    "core_concept_ids": core_concept_ids,
                    "technique_ids": ["positive-negative-contrast"],
                },
            ],
        },
        "required_artifacts": [
            "promax-dossier.md",
            "promax-concept-atlas.md",
            "promax-case-and-countercase.md",
            "promax-essay.md",
        ],
        "unexpanded_branch_ids": [],
        "coverage_complete": True,
        "locked_at": locked_at,
    }


def _canonical_concept(repo: Path | str, concept_id: str) -> Mapping[str, object]:
    root = Path(repo).resolve()
    registry = load_json(
        root
        / "skills"
        / "crossframe-promax"
        / "references"
        / "concept-registry"
        / "v8-concept-registry.json"
    )
    if not isinstance(registry, Mapping):
        raise ValueError("canonical concept registry must be an object")
    concepts = registry.get("concepts")
    if not isinstance(concepts, list):
        raise ValueError("canonical concept registry has no concept array")
    for concept in concepts:
        if isinstance(concept, Mapping) and concept.get("concept_id") == concept_id:
            return concept
    raise ValueError(f"canonical concept is absent: {concept_id}")


def build_deliverables(
    repo: Path | str,
    *,
    concept_id: str = FIXTURE_CONCEPT_ID,
    position: Mapping[str, object] | None = None,
    recommendation: Mapping[str, object] | None = None,
) -> dict[str, str]:
    concept = _canonical_concept(repo, concept_id)
    name = str(concept["authoritative_name_zh"])
    definition = str(concept["definition"])
    neighbor_ids = concept.get("required_neighbor_ids")
    if not isinstance(neighbor_ids, list) or not all(
        isinstance(item, str) for item in neighbor_ids
    ):
        raise ValueError("canonical concept neighbors are malformed")
    neighbor_lines: list[str] = []
    for neighbor_id in neighbor_ids:
        neighbor = _canonical_concept(repo, neighbor_id)
        neighbor_lines.append(
            f"- {neighbor_id} {neighbor['authoritative_name_zh']}：作为必需邻接概念共同限定本轮解释。"
        )

    rationale = "Applied to the fixture object using the exact registered definition."
    misuses = _unique_strings(
        concept.get("common_misuses"),
        concept.get("forbidden_substitutions_or_generalizations"),
    )
    if not misuses:
        raise ValueError("fixture concept must carry a source-defined misuse boundary")
    atlas = "\n".join(
        [
            "# CrossFrame ProMax v8 概念图谱",
            "",
            f"## {concept_id} {name}",
            "",
            f"v8 权威定义：{definition}",
            f"本轮对象角色：{rationale}",
            "已排除误用：",
            *[f"- {misuse}" for misuse in misuses],
            "必需邻接概念：",
            *neighbor_lines,
            "",
        ]
    )

    case_sections: list[str] = ["# CrossFrame ProMax v8 案例与反例", ""]
    case_types = ("structural_analogy", "conditional_scenario")
    for mechanism in range(1, 4):
        mechanism_id = f"MECH-{mechanism}"
        label = f"Competing mechanism {mechanism}"
        condition = f"Observable discriminator for mechanism {mechanism}"
        for example, case_type in enumerate(case_types, start=1):
            case_sections.extend(
                [
                    f"## EX-M{mechanism}-S{example} | mechanism={mechanism_id} | relation=similar | type={case_type}",
                    f"相似结构：{label} 在 {condition} 出现时，因为区分条件成立而形成可比较的条件路径。",
                    "",
                ]
            )
        case_sections.extend(
            [
                f"## EX-M{mechanism}-F1 | mechanism={mechanism_id} | relation=failure | type=conditional_scenario",
                f"失效反例：当 {condition} 不成立时，{label} 缺少区分力，必须停止并退出排序。",
                "",
            ]
        )
    cases = "\n".join(case_sections)

    claim = CENTRAL_CLAIM_STATEMENT
    if position is None:
        position = build_position_lock(
            run_id="promax-fixture-deliverable",
            locked_at="2026-07-23T01:10:00Z",
        )
    if recommendation is None:
        recommendation = build_recommendation_lock(
            position,
            run_id="promax-fixture-deliverable",
            locked_at="2026-07-23T01:20:00Z",
        )
    raw_options = recommendation.get("options")
    raw_selection_review = recommendation.get("selection_review_wrapper")
    if not isinstance(raw_options, list) or not all(
        isinstance(option, Mapping) for option in raw_options
    ):
        raise ValueError("fixture recommendation options are malformed")
    if not isinstance(raw_selection_review, Mapping):
        raise ValueError("fixture recommendation selection review is malformed")
    recommendation_options = [
        copy.deepcopy(dict(option)) for option in raw_options
    ]
    selection_review = copy.deepcopy(dict(raw_selection_review))
    eligibility_line = (
        "declared_low_information_house_policy_eligibility: "
        "case_specific_facts_present=false; "
        "choice_changing_retrieval_evidence_present=false"
    )
    dossier_selection_line = "；".join(
        [
            str(selection_review["wrapper_schema_id"]),
            str(selection_review["wrapper_role"]),
            *[
                str(item)
                for item in selection_review["source_paragraph_refs"]
            ],
            str(selection_review["selection_type"]),
            str(selection_review["selection_status"]),
            str(
                selection_review["jurisdiction_review_boundary"][
                    "boundary_role"
                ]
            ),
            str(selection_review["least_harm"]["principle_id"]),
            str(selection_review["least_harm"]["status"]),
            str(selection_review["proportionality"]["principle_id"]),
            str(selection_review["proportionality"]["status"]),
        ]
    )
    option_descriptions = [str(option["description"]) for option in recommendation_options]
    dossier = "\n".join(
        [
            "# CrossFrame ProMax v8 推演档案",
            "",
            f"中心主张：{claim}",
            "本档案登记三个竞争机制、五向检索、两轮无新颖性收敛、最强反驳与撤回条件。",
            "建议全集："
            + "；".join(
                f"{option_id} {description}"
                for (_kind, option_id), description in zip(
                    OPTION_IDS_BY_OPTION_KIND,
                    option_descriptions,
                    strict=True,
                )
            )
            + "。",
            "ranking_policy=promax_low_information_house_policy_not_v8。",
            "PROMAX-HOUSE-POLICY-NOT-V8：这是 ProMax 的低信息排序政策，不是 v8 概念、规范前提或 v8 自动结论；ranking_evidence_refs=[]。",
            f"规范选择审查包装层：{dossier_selection_line}。",
            eligibility_line,
            "",
            "## P8 立场锁完整语义",
            *dict.fromkeys(_string_leaves(position)),
            "",
            "## P8 建议锁完整语义",
            *dict.fromkeys(_string_leaves(recommendation)),
            "",
        ]
    )
    essay = "\n".join(
        [
            "# 转移发生时，谁在承担变化",
            "",
            "一个变化沿着接口传到下游时，最容易被忽略的往往不是结果，而是变化究竟从哪里开始、由谁承受。"
            "这正是 bounded transfer mechanism 值得检验的现实入口：它可能解释方向性的更新，"
            "却不能因为听起来连贯就自动成为事实。",
            "",
            f"{name}提醒我们先区分行动者是如何被登记的，以及这种登记是否真的覆盖了变化中的承担者。"
            "如果对象边界稳定、转移通道先于下游变化出现，而且方向性信号持续，那么转移机制是当前较强的条件解释。"
            "但这仍是一种需要继续受证据约束的判断，不是给对象贴上的永久标签。",
            "",
            "同一组现象也可能来自选择效应、边界漂移或第三种竞争机制。三种解释必须在相同时间顺序、"
            "相同反向信号和相同失效条件下比较；只挑对自己有利的案例，不足以证明转移发生。",
            "",
            "最强的反对意见是：对象边界本身可能不稳定，所谓转移只是重新划分对象后的视觉效果。"
            "当前材料尚未显示边界已经改变，所以这个反方还不足以取代中心解释；一旦边界变化得到确认，"
            "就应撤回当前判断，重新冻结对象，并把竞争解释提升为首要候选。",
            "",
            "在信息仍有限时，更稳妥的次序是先做可撤回的小范围探查，再根据对象边界是否变化决定是否扩大行动。"
            "维持现状、延后、退出和不行动都必须放在同一组解释力、可逆性与风险尺度上比较。"
            "不行动也会累积机会成本，但这并不把分析变成授权。",
            "",
            "Analysis only; real-world action is not authorized and requires separate authorization."
            "判断的价值不在于证明自己永远正确，而在于让承担验证代价的人能够看见停止、撤回与补救的入口。",
            "",
        ]
    )
    return {
        "promax-dossier.md": dossier,
        "promax-concept-atlas.md": atlas,
        "promax-case-and-countercase.md": cases,
        "promax-essay.md": essay,
    }


def build_prose_review(
    *,
    run_id: str,
    reviewed_at: str,
    essay: str,
    position: Mapping[str, object],
    output_plan: Mapping[str, object],
) -> dict[str, object]:
    projection = output_plan.get("reader_projection")
    if not isinstance(projection, Mapping):
        raise ValueError("fixture prose review requires a reader_projection")
    techniques = projection.get("selected_techniques")
    beats = projection.get("reader_beats")
    if not isinstance(techniques, list) or not all(
        isinstance(item, Mapping) for item in techniques
    ):
        raise ValueError("fixture prose techniques are malformed")
    if not isinstance(beats, list) or not all(
        isinstance(item, Mapping) for item in beats
    ):
        raise ValueError("fixture prose reader beats are malformed")
    excerpts = [
        line.strip()
        for line in essay.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not excerpts:
        raise ValueError("fixture essay lacks reviewable prose")
    sentence_excerpts = [
        sentence.strip()
        for paragraph in excerpts
        for sentence in re.split(r"(?<=[。！？.!?])", paragraph)
        if sentence.strip()
    ]
    dimension_excerpt_indexes = {
        "reality_entry": 0,
        "argument_dependency": 3,
        "v8_concept_fidelity": 2,
        "evidence_binding": 6,
        "strongest_counterposition": 7,
        "fair_comparison": 10,
        "position_recommendation_consistency": 9,
        "withdrawal_action_boundary": 8,
        "house_voice": 13,
        "model_flavor_independence": 4,
        "audit_leakage": 11,
    }
    if set(dimension_excerpt_indexes) != set(PROSE_REVIEW_DIMENSION_IDS):
        raise ValueError(
            "fixture prose review dimension mapping is incomplete"
        )
    prose_passes = len(sentence_excerpts) > max(
        dimension_excerpt_indexes.values()
    )

    def bounded_unique_excerpt(candidate: str) -> str:
        normalized = candidate.strip()
        if (
            8 <= len(re.findall(r"\w", normalized))
            and len(normalized) <= 240
            and essay.count(normalized) == 1
        ):
            return normalized
        for width in (240, 200, 160, 120, 80, 40, 20):
            fallback = essay[:width].strip()
            if (
                8 <= len(re.findall(r"\w", fallback))
                and len(fallback) <= 240
                and essay.count(fallback) == 1
            ):
                return fallback
        raise ValueError("fixture essay lacks a bounded unique review excerpt")

    return {
        "schema_id": "crossframe.promax.v8.prose-review",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "essay_sha256": hashlib.sha256(essay.encode("utf-8")).hexdigest(),
        "position_sha256": sha256_json(dict(position)),
        "output_plan_sha256": sha256_json(dict(output_plan)),
        "article_type": projection["article_type"],
        "technique_ids": [
            str(technique["technique_id"]) for technique in techniques
        ],
        "required_beat_mappings": [
            {
                "beat_id": beat["beat_id"],
                "section_ids": list(beat["section_ids"]),
                "evidence_excerpts": [
                    bounded_unique_excerpt(
                        sentence_excerpts[index % len(sentence_excerpts)]
                    )
                ],
            }
            for index, beat in enumerate(beats)
        ],
        "dimensions": {
            dimension_id: {
                "status": "pass" if prose_passes else "fail",
                "evidence_excerpts": (
                    [sentence_excerpts[dimension_excerpt_indexes[dimension_id]]]
                    if prose_passes
                    else []
                ),
                "repair_target": (
                    None
                    if prose_passes
                    else f"Rewrite prose to supply evidence for {dimension_id}."
                ),
            }
            for dimension_id in PROSE_REVIEW_DIMENSION_IDS
        },
        "overall_status": "pass" if prose_passes else "fail",
        "reviewed_at": reviewed_at,
    }


def _json_bytes(value: object) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _jsonl_bytes(records: Sequence[Mapping[str, object]]) -> bytes:
    return b"".join(canonical_json_bytes(dict(record)) + b"\n" for record in records)


def _write_bytes(root: Path, relative_path: str, body: bytes) -> str:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def _write_json(root: Path, relative_path: str, value: object) -> str:
    return _write_bytes(root, relative_path, _json_bytes(value))


def _artifact_ref(path: str, digest: str) -> dict[str, object]:
    suffix = Path(path).suffix.casefold()
    media_type = {
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".md": "text/markdown",
    }.get(suffix, "application/octet-stream")
    return {"path": path, "sha256": digest, "media_type": media_type}


def _scenario_record(repo: Path | str, scenario_id: str) -> Mapping[str, object]:
    catalog = load_scenario_catalog(repo)
    for scenario in catalog["scenarios"]:
        if scenario.get("scenario_id") == scenario_id:
            return scenario
    raise ValueError(f"unknown fixture scenario: {scenario_id}")


def _apply_pre_manifest_mutation(
    mutation: str | None,
    *,
    source_snapshot: dict[str, object],
    read_events: list[dict[str, object]],
    claim_graph: dict[str, object],
    retrieval: dict[str, object],
    red_team: dict[str, object],
    position: dict[str, object],
    recommendation: dict[str, object],
    deliverables: dict[str, str],
) -> None:
    if mutation in {
        None,
        "record_network_unavailable_with_empty_sources",
        "replay_phase_event_from_another_run",
        "change_artifact_after_manifest",
        "attach_continuation_to_noncurrent_manifest",
    }:
        return
    if mutation == "replace_semantic_content_with_identifiers":
        deliverables["promax-concept-atlas.md"] = (
            "# IDs only\n\n## V8-CANON-U01\nV8-CANON-U01 SECTION-CONCEPTS\n"
        )
        deliverables["promax-essay.md"] = (
            "# IDs only\n" + " V8-CANON-U01 CLAIM-CENTRAL MECH-1 MECH-2 MECH-3" * 120
        )
        return
    if mutation == "blank_strongest_attack":
        claim_graph["central_claim_cycle"]["strongest_attack"] = ""
        return
    if mutation == "duplicate_read_anchor_to_preserve_count":
        duplicate = copy.deepcopy(read_events[0])
        duplicate["event_id"] = read_events[1]["event_id"]
        duplicate["sequence"] = read_events[1]["sequence"]
        duplicate["read_at"] = read_events[1]["read_at"]
        read_events[1] = duplicate
        return
    if mutation == "mutate_source_content_without_changing_counts":
        source_snapshot["source_manifest_sha256"] = "0" * 64
        return
    if mutation == "replace_network_source_with_file_uri":
        retrieval["entries"][0]["sources"][0]["url"] = "file:///fixture/not-network"
        return
    if mutation == "declare_same_origin_sources_independent":
        original = retrieval["entries"][0]["sources"][0]
        duplicate = copy.deepcopy(original)
        duplicate["url"] = "https://www.nist.gov/fixture-duplicate"
        duplicate["title"] = "NIST duplicate-origin fixture"
        duplicate["independence_group"] = "fixture-origin-falsely-independent"
        duplicate["duplicate_relation"] = "independent"
        duplicate["duplicate_of_url"] = None
        retrieval["entries"][0]["sources"].append(duplicate)
        return
    if mutation == "remove_reverse_retrieval":
        retrieval["entries"] = [
            entry for entry in retrieval["entries"] if entry["direction"] != "reverse"
        ]
        return
    if mutation == "remove_inaction_option":
        recommendation["options"] = [
            option
            for option in recommendation["options"]
            if option["option_kind"] != "no_action"
        ]
        recommendation["ranking"] = [
            option_id
            for option_id in recommendation["ranking"]
            if option_id != "OPTION-NO-ACTION"
        ]
        return
    if mutation == "record_position_drift_without_new_evidence":
        red_team["stability_checks"][0]["relation_to_proposition_after"] = "rejects"
        red_team["stability_checks"][0]["explanation"] = (
            "The position changed only because the user stance changed."
        )
        return
    if mutation == "claim_unheld_execution_authority":
        position["action_ceiling"] = "Authorized to execute the preferred option immediately."
        deliverables["promax-essay.md"] = deliverables["promax-essay.md"].replace(
            "Analysis only; real-world action is not authorized and requires separate authorization.",
            position["action_ceiling"],
        )
        return
    if mutation == "remove_example_type":
        deliverables["promax-case-and-countercase.md"] = deliverables[
            "promax-case-and-countercase.md"
        ].replace(" | type=structural_analogy", "", 1)
        return
    raise ValueError(f"unsupported pre-manifest fixture mutation: {mutation}")


def _materialize_into(
    repo: Path,
    stage: Path,
    scenario: Mapping[str, object],
) -> dict[str, object]:
    scenario_id = str(scenario["scenario_id"])
    mutation = scenario.get("mutation")
    run_id = f"promax-fixture-{scenario_id}"
    incomplete = scenario_id == "artifact-incomplete"
    mode = "promax-artifact-run" if incomplete else "promax-complete"
    stamps = {
        "created": "2026-07-23T00:00:00Z",
        "read": "2026-07-23T00:10:00Z",
        "world": "2026-07-23T00:30:00Z",
        "concept": "2026-07-23T00:40:00Z",
        "claim": "2026-07-23T00:50:00Z",
        "retrieval": "2026-07-23T01:00:00Z",
        "red_team": "2026-07-23T01:10:00Z",
        "position": "2026-07-23T01:20:00Z",
        "recommendation": "2026-07-23T01:30:00Z",
        "plan": "2026-07-23T01:40:00Z",
        "review": "2026-07-23T01:50:00Z",
        "manifest": "2026-07-23T02:00:00Z",
        "continuation": "2026-07-23T02:10:00Z",
    }
    capabilities = build_capability_disclosure(
        subagents_available=False,
        max_parallelism=0,
        validator_ids=tuple(VALIDATOR_VERSIONS),
        network_available=not incomplete,
        live_retrieval=not incomplete,
    )
    initialized = initialize_run(
        repo,
        f"Use CrossFrame ProMax for deterministic fixture {scenario_id}",
        mode=mode,
        capabilities=capabilities,
        created_at=stamps["created"],
        run_id=run_id,
        recommendation_required=True,
    )
    run_contract = copy.deepcopy(initialized["run_contract"])
    run_contract["run_nonce"] = hashlib.sha256(
        f"crossframe-promax-v8-fixture:{scenario_id}".encode("utf-8")
    ).hexdigest()
    validate_instance("promax-run-contract.schema.json", run_contract)
    source_snapshot = copy.deepcopy(initialized["source_snapshot"])
    read_events = build_read_events(repo, run_id=run_id, read_at=stamps["read"])
    local_world = build_local_world_model(run_id=run_id, locked_at=stamps["world"])
    concept_disposition = build_concept_disposition(
        repo,
        run_id=run_id,
        completed_at=stamps["concept"],
        applied_concept_ids=(FIXTURE_CONCEPT_ID,),
    )
    claim_graph = build_claim_path_graph(run_id=run_id, updated_at=stamps["claim"])
    retrieval = build_retrieval_ledger(
        run_id=run_id,
        completed_at=stamps["retrieval"],
        network_available=not incomplete,
    )
    evidence_basis_sha256 = sha256_json(
        {
            "request_sha256": run_contract["request_sha256"],
            "source_snapshot_sha256": run_contract["source_snapshot_sha256"],
            "local_world_model_sha256": sha256_json(local_world),
            "retrieval_ledger_sha256": sha256_json(retrieval),
        }
    )
    red_team = build_red_team_report(
        run_id=run_id,
        completed_at=stamps["red_team"],
        recommendation_locked_at=stamps["recommendation"],
        evidence_basis_sha256=evidence_basis_sha256,
    )
    position = build_position_lock(run_id=run_id, locked_at=stamps["position"])
    recommendation = build_recommendation_lock(
        position,
        run_id=run_id,
        locked_at=stamps["recommendation"],
    )
    output_plan = build_output_plan(run_id=run_id, locked_at=stamps["plan"])
    deliverables = build_deliverables(
        repo,
        position=position,
        recommendation=recommendation,
    )

    _apply_pre_manifest_mutation(
        mutation if isinstance(mutation, str) else None,
        source_snapshot=source_snapshot,
        read_events=read_events,
        claim_graph=claim_graph,
        retrieval=retrieval,
        red_team=red_team,
        position=position,
        recommendation=recommendation,
        deliverables=deliverables,
    )
    prose_review = build_prose_review(
        run_id=run_id,
        reviewed_at=stamps["review"],
        essay=deliverables["promax-essay.md"],
        position=position,
        output_plan=output_plan,
    )
    validate_instance("promax-prose-review.schema.json", prose_review)

    worldview = (
        "# CrossFrame ProMax v8 世界观胶囊\n\n"
        "本运行只以冻结的 v8 源快照、709 项终态概念处置和显式对象边界为知识平面。\n"
        "缺失证据形成条件分支；证据不自动产生现实授权；用户立场仅作为待检验假设。\n"
    )
    continuation_index = (
        "# CrossFrame ProMax v8 续写索引\n\n"
        "当前完整工件已闭合；若平台边界截断，续写只能从 P10 与当前 manifest 重新绑定。\n"
    )

    values: dict[str, object] = {
        "promax-run-contract.json": run_contract,
        "promax-source-snapshot.json": source_snapshot,
        "promax-local-world-model.locked.json": local_world,
        "promax-concept-disposition-ledger.json": concept_disposition,
        "promax-claim-path-graph.json": claim_graph,
        "promax-retrieval-ledger.json": retrieval,
        "promax-red-team-report.json": red_team,
        "promax-position.locked.json": position,
        "promax-recommendation.locked.json": recommendation,
        "promax-output-plan.locked.json": output_plan,
        "promax-prose-review.json": prose_review,
    }
    digests: dict[str, str] = {
        path: _write_json(stage, path, value) for path, value in values.items()
    }
    digests["promax-read-events.jsonl"] = _write_bytes(
        stage,
        "promax-read-events.jsonl",
        _jsonl_bytes(read_events),
    )
    digests["promax-worldview-capsule.locked.md"] = _write_bytes(
        stage,
        "promax-worldview-capsule.locked.md",
        worldview.encode("utf-8"),
    )
    for path, text in deliverables.items():
        digests[path] = _write_bytes(stage, path, text.encode("utf-8"))
    digests["promax-continuation-index.md"] = _write_bytes(
        stage,
        "promax-continuation-index.md",
        continuation_index.encode("utf-8"),
    )

    binding = RunBinding(
        run_id=run_contract["run_id"],
        run_nonce=run_contract["run_nonce"],
        request_sha256=run_contract["request_sha256"],
        source_snapshot_sha256=run_contract["source_snapshot_sha256"],
    )
    phase_specs = (
        (
            "P0",
            {},
            {
                "promax-run-contract.json": digests["promax-run-contract.json"],
                "promax-source-snapshot.json": digests["promax-source-snapshot.json"],
            },
        ),
        (
            "P1",
            {"promax-source-snapshot.json": digests["promax-source-snapshot.json"]},
            {"promax-read-events.jsonl": digests["promax-read-events.jsonl"]},
        ),
        (
            "P2",
            {"promax-read-events.jsonl": digests["promax-read-events.jsonl"]},
            {
                "promax-worldview-capsule.locked.md": digests[
                    "promax-worldview-capsule.locked.md"
                ]
            },
        ),
        (
            "P3",
            {
                "promax-worldview-capsule.locked.md": digests[
                    "promax-worldview-capsule.locked.md"
                ]
            },
            {
                "promax-local-world-model.locked.json": digests[
                    "promax-local-world-model.locked.json"
                ]
            },
        ),
        (
            "P4",
            {
                "promax-local-world-model.locked.json": digests[
                    "promax-local-world-model.locked.json"
                ]
            },
            {
                "promax-concept-disposition-ledger.json": digests[
                    "promax-concept-disposition-ledger.json"
                ]
            },
        ),
        (
            "P5",
            {
                "promax-concept-disposition-ledger.json": digests[
                    "promax-concept-disposition-ledger.json"
                ]
            },
            {"promax-claim-path-graph.json": digests["promax-claim-path-graph.json"]},
        ),
        (
            "P6",
            {"promax-claim-path-graph.json": digests["promax-claim-path-graph.json"]},
            {"promax-retrieval-ledger.json": digests["promax-retrieval-ledger.json"]},
        ),
        (
            "P7",
            {"promax-retrieval-ledger.json": digests["promax-retrieval-ledger.json"]},
            {"promax-red-team-report.json": digests["promax-red-team-report.json"]},
        ),
        (
            "P8",
            {"promax-red-team-report.json": digests["promax-red-team-report.json"]},
            {
                "promax-position.locked.json": digests["promax-position.locked.json"],
                "promax-recommendation.locked.json": digests[
                    "promax-recommendation.locked.json"
                ],
            },
        ),
        (
            "P9",
            {
                "promax-position.locked.json": digests["promax-position.locked.json"],
                "promax-recommendation.locked.json": digests[
                    "promax-recommendation.locked.json"
                ],
            },
            {"promax-output-plan.locked.json": digests["promax-output-plan.locked.json"]},
        ),
        (
            "P10",
            {"promax-output-plan.locked.json": digests["promax-output-plan.locked.json"]},
            {
                path: digests[path]
                for path in (
                    "promax-dossier.md",
                    "promax-concept-atlas.md",
                    "promax-case-and-countercase.md",
                    "promax-essay.md",
                    "promax-continuation-index.md",
                    "promax-prose-review.json",
                )
            },
        ),
    )
    phase_events: list[dict[str, object]] = []
    state = validate_phase_history(phase_events, expected_binding=binding)
    for phase_id, inputs, outputs in phase_specs:
        event = seal_phase_event(
            state,
            phase_id,
            input_artifact_hashes=inputs,
            output_artifact_hashes=outputs,
        )
        phase_events.append(event)
        state = validate_phase_history(phase_events, expected_binding=binding)
    if state.chain_head_sha256 is None or state.next_phase_id != "P11":
        raise RuntimeError("fixture phase history did not close through P10")
    phase_log_records = list(phase_events)
    if mutation == "replay_phase_event_from_another_run":
        phase_log_records.append(copy.deepcopy(phase_log_records[-1]))
    _write_bytes(
        stage,
        "promax-phase-events.jsonl",
        _jsonl_bytes(phase_log_records),
    )

    metadata: dict[str, dict[str, object]] = {
        "promax-source-snapshot.json": {
            "generating_phase": "P0",
            "input_artifact_sha256s": [],
            "status": "current",
        },
        "promax-read-events.jsonl": {
            "generating_phase": "P1",
            "input_artifact_sha256s": [digests["promax-source-snapshot.json"]],
            "status": "current",
        },
        "promax-worldview-capsule.locked.md": {
            "generating_phase": "P2",
            "input_artifact_sha256s": [digests["promax-read-events.jsonl"]],
            "status": "current",
        },
        "promax-local-world-model.locked.json": {
            "generating_phase": "P3",
            "input_artifact_sha256s": [digests["promax-worldview-capsule.locked.md"]],
            "status": "current",
        },
        "promax-concept-disposition-ledger.json": {
            "generating_phase": "P4",
            "input_artifact_sha256s": [digests["promax-local-world-model.locked.json"]],
            "status": "current",
        },
        "promax-claim-path-graph.json": {
            "generating_phase": "P5",
            "input_artifact_sha256s": [digests["promax-concept-disposition-ledger.json"]],
            "status": "current",
        },
        "promax-retrieval-ledger.json": {
            "generating_phase": "P6",
            "input_artifact_sha256s": [digests["promax-claim-path-graph.json"]],
            "status": "current",
        },
        "promax-red-team-report.json": {
            "generating_phase": "P7",
            "input_artifact_sha256s": [digests["promax-retrieval-ledger.json"]],
            "status": "current",
        },
        "promax-position.locked.json": {
            "generating_phase": "P8",
            "input_artifact_sha256s": [digests["promax-red-team-report.json"]],
            "status": "current",
        },
        "promax-recommendation.locked.json": {
            "generating_phase": "P8",
            "input_artifact_sha256s": [digests["promax-position.locked.json"]],
            "status": "current",
        },
        "promax-output-plan.locked.json": {
            "generating_phase": "P9",
            "input_artifact_sha256s": [
                digests["promax-position.locked.json"],
                digests["promax-recommendation.locked.json"],
            ],
            "status": "current",
        },
    }
    for path in (
        "promax-dossier.md",
        "promax-concept-atlas.md",
        "promax-case-and-countercase.md",
        "promax-essay.md",
        "promax-continuation-index.md",
    ):
        metadata[path] = {
            "generating_phase": "P10",
            "input_artifact_sha256s": [digests["promax-output-plan.locked.json"]],
            "status": "current",
        }
    metadata["promax-prose-review.json"] = {
        "generating_phase": "P10",
        "input_artifact_sha256s": [
            digests["promax-essay.md"],
            digests["promax-position.locked.json"],
            digests["promax-output-plan.locked.json"],
        ],
        "status": "current",
    }
    inventory = inventory_artifacts(stage, metadata)
    role_bindings = (
        (
            ("promax-local-world-model.locked.json",),
            ("promax-concept-disposition-ledger.json",),
        ),
        (("promax-claim-path-graph.json",), ("promax-retrieval-ledger.json",)),
        (("promax-retrieval-ledger.json",), ("promax-red-team-report.json",)),
        (("promax-red-team-report.json",), ("promax-position.locked.json",)),
        (("promax-output-plan.locked.json",), ("promax-essay.md",)),
        (
            (
                "promax-essay.md",
                "promax-position.locked.json",
                "promax-output-plan.locked.json",
            ),
            ("promax-prose-review.json",),
        ),
    )
    role_records: list[dict[str, object]] = []
    for plan, (input_paths, output_paths) in zip(
        run_contract["role_plan"], role_bindings
    ):
        input_refs = [
            _artifact_ref(input_path, digests[input_path])
            for input_path in input_paths
        ]
        output_refs = [
            _artifact_ref(output_path, digests[output_path])
            for output_path in output_paths
        ]
        role_records.append(
            {
                **copy.deepcopy(plan),
                "input_artifacts": input_refs,
                "observed_input_artifacts": copy.deepcopy(input_refs),
                "output_artifacts": output_refs,
                "status": "completed",
            }
        )
    manifest = build_artifact_manifest(
        run_contract,
        phase_chain_head_sha256=state.chain_head_sha256,
        artifacts=inventory,
        role_records=role_records,
        generated_at=stamps["manifest"],
    )
    _write_json(stage, "promax-artifact-manifest.json", manifest)
    continuation = {
        "schema_id": "crossframe.promax.v8.continuation-ledger",
        "schema_version": 1,
        "run_id": run_id,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "parent_manifest_sha256": manifest["manifest_sha256"],
        "continuations": [],
        "updated_at": stamps["continuation"],
    }
    if mutation == "attach_continuation_to_noncurrent_manifest":
        continuation["parent_manifest_sha256"] = "f" * 64
    _write_json(stage, "promax-continuation-ledger.json", continuation)
    final_chat = {
        "run_status": (
            "promax-artifact-incomplete:network-unavailable"
            if incomplete
            else mode
        ),
        "center_judgment_summary": position["position"],
        "key_withdrawal_conditions": position["withdrawal_conditions"],
        "artifact_links": list(output_plan["required_artifacts"]),
        "continuation_entry": None,
    }
    _write_json(stage, "promax-final-chat.json", final_chat)

    if mutation == "change_artifact_after_manifest":
        with (stage / "promax-essay.md").open("ab") as handle:
            handle.write(b"\nchanged after manifest\n")

    return {
        "status": "ok",
        "scenario_id": scenario_id,
        "fixture_class": scenario["fixture_class"],
        "mutation": mutation,
        "mode": mode,
        "run_id": run_id,
        "phase_chain_head_sha256": state.chain_head_sha256,
        "manifest_sha256": manifest["manifest_sha256"],
    }


def materialize_fixture(
    repo: Path | str,
    *,
    scenario_id: str,
    output: Path | str,
) -> dict[str, object]:
    root = Path(repo).resolve()
    target = Path(output).resolve()
    if target.exists():
        raise ValueError("fixture output path must not already exist")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{target.name}.stage-",
            dir=str(target.parent),
        )
    )
    try:
        status = _materialize_into(root, stage, _scenario_record(root, scenario_id))
        stage.replace(target)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return {**status, "workspace": str(target)}


def load_scenario_catalog(repo: Path | str) -> dict[str, object]:
    root = Path(repo).resolve()
    data = load_json(root / FIXTURE_CATALOG)
    if not isinstance(data, dict) or set(data) != {"schema_version", "scenarios"}:
        raise ValueError("fixture catalog must be one closed JSON object")
    if data.get("schema_version") != 1:
        raise ValueError("unsupported fixture catalog schema_version")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("fixture catalog scenarios must be a nonempty array")
    seen: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("each fixture scenario must be an object")
        fixture_class = scenario.get("fixture_class")
        expected_key = (
            "expected_error_type"
            if fixture_class == "adversarial"
            else "expected_outcome"
        )
        expected_fields = {
            "scenario_id",
            "fixture_class",
            "mutation",
            expected_key,
        }
        if set(scenario) != expected_fields:
            raise ValueError("fixture scenario fields are not closed")
        scenario_id = scenario.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError("fixture scenario_id must be substantive")
        if scenario_id in seen:
            raise ValueError("fixture scenario_id values must be unique")
        seen.add(scenario_id)
        if fixture_class not in FIXTURE_CLASSES:
            raise ValueError("fixture_class is unsupported")
        mutation = scenario.get("mutation")
        if fixture_class == "positive":
            if mutation is not None:
                raise ValueError("positive fixture cannot declare a mutation")
        elif not isinstance(mutation, str) or not mutation.strip():
            raise ValueError("non-positive fixture must declare one mutation")
        expected = scenario.get(expected_key)
        if not isinstance(expected, str) or not expected.strip():
            raise ValueError("fixture scenario must declare a substantive outcome")
    if {scenario["fixture_class"] for scenario in scenarios} != FIXTURE_CLASSES:
        raise ValueError("fixture catalog must include every fixture class")
    return data


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize deterministic CrossFrame ProMax v8 runtime fixtures"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_parser = subparsers.add_parser("list", help="list fixture scenarios")
    list_parser.add_argument("--repo", type=Path, default=Path.cwd())
    materialize_parser = subparsers.add_parser(
        "materialize", help="materialize one deterministic fixture workspace"
    )
    materialize_parser.add_argument("--repo", type=Path, default=Path.cwd())
    materialize_parser.add_argument("--scenario", required=True)
    materialize_parser.add_argument("--output", type=Path, required=True)
    materialize_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "list":
        catalog = load_scenario_catalog(args.repo)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "scenario_ids": [
                        scenario["scenario_id"] for scenario in catalog["scenarios"]
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "materialize":
        status = materialize_fixture(
            args.repo,
            scenario_id=args.scenario,
            output=args.output,
        )
        if args.json:
            print(json.dumps(status, ensure_ascii=False, sort_keys=True))
        else:
            print(f"materialized {status['scenario_id']} at {status['workspace']}")
        return 0
    raise AssertionError("unreachable fixture factory command")


if __name__ == "__main__":
    raise SystemExit(main())
