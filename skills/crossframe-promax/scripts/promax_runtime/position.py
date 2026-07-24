from __future__ import annotations

import copy
from datetime import datetime
import re
from typing import Mapping, Sequence

from .jsonio import sha256_json
from .validation import validate_bound_document


_IMPACT_RANK = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "decisive": 4,
}
_ACTION_DENIAL_MARKERS = (
    "不授权",
    "不得授权",
    "未经授权",
    "需另行授权",
    "需要另行授权",
    "仅作分析",
    "analysis only",
    "not authorized",
    "requires separate authorization",
)
_ACTION_GRANT_MARKERS = (
    "已授权",
    "授权立即",
    "立即采取现实行动",
    "authorized to",
    "permission granted",
    "must act now",
)
_CONDITIONAL_MARKERS = ("若", "如果", "一旦", "when ", "if ", "unless ")
_WITHDRAWAL_MARKERS = ("撤回", "调整", "降级", "改变", "withdraw", "revise")
_EXPLANATION_MARKERS = (
    "若",
    "如果",
    "一旦",
    "条件",
    "因为",
    "由于",
    "在",
    "when ",
    "if ",
    "unless ",
    "because",
)
_POSITIVE_DRIFT_CLAIMS = (
    "均改变",
    "发生改变",
    "已经改变",
    "改变了",
    "发生漂移",
    "不同判断",
    "position changed",
    "ranking changed",
    "different position",
    "different ranking",
)
_REQUIRED_OPTION_KINDS = frozenset(
    {
        "maintain_status_quo",
        "active_action",
        "delayed_action",
        "probe_action",
        "exit_or_transfer",
        "no_action",
    }
)
_HOUSE_OPTION_KIND_RANKING = (
    "probe_action",
    "active_action",
    "maintain_status_quo",
    "delayed_action",
    "exit_or_transfer",
    "no_action",
)
_STANCE_NEUTRAL_PROBLEM_FIELDS = (
    "analysis_object",
    "proposition_under_test",
    "time_window",
)
_SELECTION_REVIEW_SOURCE_PARAGRAPHS = (
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
)


def _timestamp(value: object, *, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def _mapping_items(value: object, *, field: str) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be an array")
    items: list[Mapping[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"{field}[{index}] must be an object")
        items.append(item)
    return items


def _text_items(value: object, *, field: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be non-empty text")
        result.append(item.strip())
    return result


def _contains_any(text: str, markers: Sequence[str]) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in markers)


def _all_text(value: object) -> list[str]:
    if isinstance(value, Mapping):
        result: list[str] = []
        for key, child in value.items():
            result.append(str(key))
            result.extend(_all_text(child))
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = []
        for child in value:
            result.extend(_all_text(child))
        return result
    return [value] if isinstance(value, str) else []


def _semantic_tokens(text: str) -> set[str]:
    tokens = {
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+", text)
        if len(token) >= 4
    }
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        for width in (4, 5, 6):
            tokens.update(
                run[index : index + width]
                for index in range(max(0, len(run) - width + 1))
            )
    return tokens


def _option_semantic_payload(option: Mapping[str, object]) -> dict[str, object]:
    return {
        key: copy.deepcopy(value)
        for key, value in option.items()
        if key != "option_id"
    }


def _validate_selection_review_wrapper(
    recommendation: Mapping[str, object],
    *,
    options: Sequence[Mapping[str, object]],
    option_ids: Sequence[str],
    evaluation_dimensions: Sequence[str],
    preferred_option_id: str,
    ranking_policy: object,
    ranking_evidence_refs: Sequence[str],
) -> str:
    wrapper = recommendation.get("selection_review_wrapper")
    if not isinstance(wrapper, Mapping):
        raise ValueError("recommendation is missing the ProMax selection-review wrapper")
    if tuple(wrapper.get("source_paragraph_refs", ())) != _SELECTION_REVIEW_SOURCE_PARAGRAPHS:
        raise ValueError("selection-review wrapper is not bound to its exact v8 paragraph basis")

    premises = _mapping_items(
        wrapper.get("public_value_premises"),
        field="selection_review_wrapper.public_value_premises",
    )
    premise_ids = [
        premise.get("normative_principle_id") for premise in premises
    ]
    if (
        any(not isinstance(premise_id, str) for premise_id in premise_ids)
        or len(set(premise_ids)) != len(premise_ids)
        or "N1" not in premise_ids
        or not any(premise_id in {"N2", "N3", "N4", "N5"} for premise_id in premise_ids)
    ):
        raise ValueError(
            "selection-review wrapper requires unique N1 plus at least one positive N2-N5 premise"
        )
    n1_records = [
        premise
        for premise in premises
        if premise.get("normative_principle_id") == "N1"
    ]
    if len(n1_records) != 1 or n1_records[0].get("role") != "veto_gate":
        raise ValueError("N1 must be the unique veto gate in public_value_premises")

    option_premise_refs: set[str] = set()
    option_rights_floor: set[str] = set()
    option_affected_positions: set[str] = set()
    options_by_id = {
        str(option.get("option_id")): option
        for option in options
        if isinstance(option.get("option_id"), str)
    }
    for index, option in enumerate(options):
        refs = _text_items(
            option.get("normative_premise_refs"),
            field=f"recommendation.options[{index}].normative_premise_refs",
        )
        if not set(refs).issubset(set(premise_ids)):
            raise ValueError("an option cites an unregistered public value premise")
        option_premise_refs.update(refs)
        option_rights_floor.update(
            _text_items(
                option.get("rights_floor_refs"),
                field=f"recommendation.options[{index}].rights_floor_refs",
            )
        )
        option_affected_positions.update(
            _text_items(
                option.get("affected_position_refs"),
                field=f"recommendation.options[{index}].affected_position_refs",
            )
        )
    if option_premise_refs != set(premise_ids):
        raise ValueError(
            "public_value_premises must equal the normative premises used by the options"
        )

    rights_floor = set(
        _text_items(
            wrapper.get("rights_floor"),
            field="selection_review_wrapper.rights_floor",
        )
    )
    affected_positions = set(
        _text_items(
            wrapper.get("affected_positions"),
            field="selection_review_wrapper.affected_positions",
        )
    )
    low_power_positions = set(
        _text_items(
            wrapper.get("low_power_position_ids"),
            field="selection_review_wrapper.low_power_position_ids",
        )
    )
    if rights_floor != option_rights_floor:
        raise ValueError("selection-review rights_floor is not closed over option records")
    if not rights_floor.issubset({f"PF-{index}" for index in range(1, 11)}):
        raise ValueError("selection-review rights_floor may contain only PF-1 through PF-10")
    if affected_positions != option_affected_positions:
        raise ValueError(
            "selection-review affected_positions is not closed over option records"
        )
    if not low_power_positions.issubset(affected_positions):
        raise ValueError("low_power_position_ids must be a subset of affected_positions")

    conflicts = _mapping_items(
        wrapper.get("value_conflicts"),
        field="selection_review_wrapper.value_conflicts",
    )
    conflict_ids = [conflict.get("conflict_id") for conflict in conflicts]
    if len(set(conflict_ids)) != len(conflict_ids):
        raise ValueError("selection-review value-conflict IDs must be unique")
    expected_unresolved_dissent: set[str] = set()
    for conflict in conflicts:
        if not set(
            _text_items(
                conflict.get("premise_ids"),
                field="selection_review_wrapper.value_conflicts.premise_ids",
            )
        ).issubset(set(premise_ids)):
            raise ValueError("a value conflict cites an unregistered normative premise")
        if not set(
            _text_items(
                conflict.get("affected_position_refs"),
                field="selection_review_wrapper.value_conflicts.affected_position_refs",
            )
        ).issubset(affected_positions):
            raise ValueError("a value conflict cites an unregistered affected position")
        dissent_refs = set(
            _text_items(
                conflict.get("dissent_refs"),
                field="selection_review_wrapper.value_conflicts.dissent_refs",
            )
        )
        if conflict.get("status") in {"open", "paused"}:
            expected_unresolved_dissent.update(dissent_refs)
    unresolved_dissent = set(
        _text_items(
            wrapper.get("unresolved_dissent_refs"),
            field="selection_review_wrapper.unresolved_dissent_refs",
        )
    )
    if unresolved_dissent != expected_unresolved_dissent:
        raise ValueError(
            "unresolved_dissent_refs must equal dissent preserved by open or paused conflicts"
        )

    jurisdiction = wrapper.get("jurisdiction_review_boundary")
    if not isinstance(jurisdiction, Mapping):
        raise ValueError("selection-review jurisdiction_review_boundary must be structured")
    valid_from = _timestamp(
        jurisdiction.get("valid_from"),
        field="selection_review_wrapper.jurisdiction_review_boundary.valid_from",
    )
    valid_until = _timestamp(
        jurisdiction.get("valid_until"),
        field="selection_review_wrapper.jurisdiction_review_boundary.valid_until",
    )
    if valid_until <= valid_from:
        raise ValueError("selection-review jurisdiction validity must have positive duration")
    decision_actor_ref = jurisdiction.get("decision_actor_ref")
    if jurisdiction.get("reviewed_option_id") != preferred_option_id:
        raise ValueError(
            "jurisdiction review boundary is not bound to the preferred option"
        )
    preferred_options = [
        option for option in options if option.get("option_id") == preferred_option_id
    ]
    if len(preferred_options) != 1:
        raise ValueError("preferred option is not uniquely resolvable")
    preferred_option = preferred_options[0]
    if preferred_option.get("authorized_actor_ref") != decision_actor_ref:
        raise ValueError(
            "jurisdiction review actor differs from the preferred option actor reference"
        )
    if (
        preferred_option.get("authorization_record_ref")
        != jurisdiction.get("authorization_source_ref")
    ):
        raise ValueError(
            "jurisdiction authorization source differs from the preferred option record reference"
        )

    recommendation_locked_at = _timestamp(
        recommendation.get("locked_at"),
        field="recommendation.locked_at",
    )
    normalized_reviews: dict[str, object] = {}
    preferred_semantic_sha256 = sha256_json(
        _option_semantic_payload(preferred_option)
    )
    for review_name in ("least_harm", "proportionality"):
        review = wrapper.get(review_name)
        if not isinstance(review, Mapping):
            raise ValueError(f"selection-review {review_name} must be structured")
        compared = _text_items(
            review.get("compared_option_ids"),
            field=f"selection_review_wrapper.{review_name}.compared_option_ids",
        )
        if len(compared) != len(option_ids) or set(compared) != set(option_ids):
            raise ValueError(
                f"selection-review {review_name} must compare every option including no_action"
            )
        if review.get("selected_option_id") != preferred_option_id:
            raise ValueError(
                f"selection-review {review_name} is not bound to the preferred option"
            )
        dimensions = _text_items(
            review.get("evaluation_dimensions"),
            field=f"selection_review_wrapper.{review_name}.evaluation_dimensions",
        )
        if list(dimensions) != list(evaluation_dimensions):
            raise ValueError(
                f"selection-review {review_name} dimensions differ from the recommendation"
            )
        if review.get("reviewer_ref") == decision_actor_ref:
            raise ValueError(
                f"selection-review {review_name} reviewer must be independent of the decision actor"
            )
        if _timestamp(
            review.get("reviewed_at"),
            field=f"selection_review_wrapper.{review_name}.reviewed_at",
        ) > recommendation_locked_at:
            raise ValueError(
                f"selection-review {review_name} cannot postdate the recommendation lock"
            )
        review_evidence_refs = set(
            _text_items(
                review.get("evidence_refs"),
                field=f"selection_review_wrapper.{review_name}.evidence_refs",
            )
        )
        if not review_evidence_refs.issubset(set(ranking_evidence_refs)):
            raise ValueError(
                f"selection-review {review_name} cites evidence outside ranking_evidence_refs"
            )
        if review.get("status") == "passed" and not review_evidence_refs:
            raise ValueError(
                f"selection-review {review_name} cannot pass without evidence"
            )
        normalized_reviews[review_name] = {
            "principle_id": review.get("principle_id"),
            "principle_version": review.get("principle_version"),
            "selected_option_semantic_sha256": preferred_semantic_sha256,
            "compared_option_semantic_sha256": sorted(
                sha256_json(
                    _option_semantic_payload(options_by_id[option_id])
                )
                for option_id in compared
            ),
            "evaluation_dimensions": list(dimensions),
            "status": review.get("status"),
        }

    eligibility = wrapper.get(
        "declared_low_information_house_policy_eligibility"
    )
    if not isinstance(eligibility, Mapping):
        raise ValueError("selection-review house-policy eligibility must be structured")
    case_facts_present = eligibility.get("case_specific_facts_present")
    choice_evidence_present = eligibility.get(
        "choice_changing_retrieval_evidence_present"
    )
    if type(case_facts_present) is not bool or type(choice_evidence_present) is not bool:
        raise ValueError("selection-review house-policy eligibility flags must be booleans")
    supports = _mapping_items(
        wrapper.get("ranking_support"),
        field="selection_review_wrapper.ranking_support",
    )

    if ranking_policy == "promax_low_information_house_policy_not_v8":
        if case_facts_present or choice_evidence_present or supports:
            raise ValueError(
                "the low-information house policy is ineligible when case facts, choice-changing evidence, or ranking support exists"
            )
    elif ranking_policy == "evidence_bound_case_comparison":
        if not (case_facts_present or choice_evidence_present):
            raise ValueError(
                "evidence-bound comparison requires case facts or choice-changing retrieval evidence"
            )
        expected_cells = {
            (option_id, dimension)
            for option_id in option_ids
            for dimension in evaluation_dimensions
        }
        observed_cells: set[tuple[str, str]] = set()
        support_evidence_refs: set[str] = set()
        for support in supports:
            option_id = _text_items(
                [support.get("option_id")],
                field="selection_review_wrapper.ranking_support.option_id",
            )[0]
            dimension = _text_items(
                [support.get("evaluation_dimension")],
                field="selection_review_wrapper.ranking_support.evaluation_dimension",
            )[0]
            cell = (option_id, dimension)
            if cell in observed_cells:
                raise ValueError("ranking-support matrix contains a duplicate cell")
            observed_cells.add(cell)
            support_evidence_refs.update(
                _text_items(
                    support.get("evidence_refs"),
                    field="selection_review_wrapper.ranking_support.evidence_refs",
                )
            )
        if observed_cells != expected_cells:
            raise ValueError(
                "evidence-bound ranking support must cover the complete option-by-dimension matrix"
            )
        if support_evidence_refs != set(ranking_evidence_refs):
            raise ValueError(
                "ranking_evidence_refs must equal the evidence used by the ranking-support matrix"
            )
    basis = {
        "wrapper_role": wrapper.get("wrapper_role"),
        "source_paragraph_refs": list(_SELECTION_REVIEW_SOURCE_PARAGRAPHS),
        "selection_type": wrapper.get("selection_type"),
        "selection_status": wrapper.get("selection_status"),
        "public_value_premises": sorted(
            (
                str(premise.get("normative_principle_id")),
                str(premise.get("role")),
                str(premise.get("statement")),
            )
            for premise in premises
        ),
        "value_conflicts": sorted(
            (
                tuple(
                    sorted(
                        _text_items(
                            conflict.get("premise_ids"),
                            field="selection_review_wrapper.value_conflicts.premise_ids",
                        )
                    )
                ),
                len(
                    _text_items(
                        conflict.get("affected_position_refs"),
                        field="selection_review_wrapper.value_conflicts.affected_position_refs",
                    )
                ),
                len(
                    _text_items(
                        conflict.get("dissent_refs"),
                        field="selection_review_wrapper.value_conflicts.dissent_refs",
                    )
                ),
                str(conflict.get("status")),
            )
            for conflict in conflicts
        ),
        "rights_floor": sorted(rights_floor),
        "affected_position_count": len(affected_positions),
        "low_power_position_count": len(low_power_positions),
        "procedure_states": copy.deepcopy(wrapper.get("procedure_states")),
        "jurisdiction_review_boundary": {
            "boundary_role": jurisdiction.get("boundary_role"),
            "reviewed_option_semantic_sha256": preferred_semantic_sha256,
            "scope": jurisdiction.get("scope"),
            "authorization_status": jurisdiction.get("authorization_status"),
        },
        "principle_reviews": normalized_reviews,
        "ranking_policy": ranking_policy,
        "declared_eligibility": {
            "case_specific_facts_present": case_facts_present,
            "choice_changing_retrieval_evidence_present": choice_evidence_present,
        },
    }
    return sha256_json(basis)


def selection_review_basis_sha256(
    recommendation: Mapping[str, object],
) -> str:
    options = _mapping_items(
        recommendation.get("options"),
        field="recommendation.options",
    )
    option_ids = _text_items(
        [option.get("option_id") for option in options],
        field="recommendation option IDs",
    )
    evaluation_dimensions = _text_items(
        recommendation.get("evaluation_dimensions"),
        field="recommendation.evaluation_dimensions",
    )
    preferred_option_id = recommendation.get("preferred_option_id")
    if not isinstance(preferred_option_id, str) or not preferred_option_id:
        raise ValueError("recommendation preferred_option_id must be text")
    ranking_evidence_refs = _text_items(
        recommendation.get("ranking_evidence_refs"),
        field="recommendation.ranking_evidence_refs",
    )
    return _validate_selection_review_wrapper(
        recommendation,
        options=options,
        option_ids=option_ids,
        evaluation_dimensions=evaluation_dimensions,
        preferred_option_id=preferred_option_id,
        ranking_policy=recommendation.get("ranking_policy"),
        ranking_evidence_refs=ranking_evidence_refs,
    )


def _validate_stance_neutral_problem(graph: Mapping[str, object]) -> str:
    problem = graph.get("stance_neutral_problem")
    if not isinstance(problem, Mapping):
        raise ValueError("claim graph is missing the stance-neutral problem key")
    payload = {
        field: copy.deepcopy(problem.get(field))
        for field in _STANCE_NEUTRAL_PROBLEM_FIELDS
    }
    expected = sha256_json(payload)
    actual = problem.get("semantic_key_sha256")
    if actual != expected:
        raise ValueError("stance-neutral problem key does not match its structured fields")
    return expected


def validate_position_lock(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    return validate_bound_document(
        "promax-position.schema.json",
        document,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )


def validate_recommendation_lock(
    document: Mapping[str, object],
    *,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    return validate_bound_document(
        "promax-recommendation.schema.json",
        document,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )


def validate_position_semantics(
    document: Mapping[str, object],
    *,
    red_team_report: Mapping[str, object],
    claim_path_graph: Mapping[str, object],
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    """Validate the evidence-bound position created after adversarial review."""

    position = validate_position_lock(
        document,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )
    red_team = validate_bound_document(
        "promax-red-team-report.schema.json",
        red_team_report,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )
    graph = validate_bound_document(
        "promax-claim-path-graph.schema.json",
        claim_path_graph,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )

    central_claim_id = graph.get("central_claim_id")
    if (
        position.get("central_claim_id") != central_claim_id
        or red_team.get("central_claim_id") != central_claim_id
    ):
        raise ValueError("position, red-team report, and claim graph disagree on the central claim")

    graph_time = _timestamp(graph.get("updated_at"), field="claim_path_graph.updated_at")
    red_time = _timestamp(red_team.get("completed_at"), field="red_team_report.completed_at")
    locked_time = _timestamp(position.get("locked_at"), field="position.locked_at")
    if red_time < graph_time:
        raise ValueError("red-team report predates the claim graph it attacks")
    if locked_time <= red_time:
        raise ValueError("position.locked_at must be later than red-team completion")

    claims = _mapping_items(graph.get("claims"), field="claim_path_graph.claims")
    central_claims = [claim for claim in claims if claim.get("claim_id") == central_claim_id]
    if len(central_claims) != 1:
        raise ValueError("claim graph must contain exactly one central claim record")
    statement = central_claims[0].get("statement")
    reasons = _text_items(position.get("primary_reasons"), field="position.primary_reasons")
    position_text = str(position.get("position", ""))
    if not isinstance(statement, str) or not statement.strip():
        raise ValueError("central claim statement is missing")
    if statement not in "\n".join([position_text, *reasons]):
        raise ValueError("locked position does not carry its central claim statement")
    expected_verdict = (
        f"VERDICT[{position.get('relation_to_proposition')}] {statement}"
    )
    if position.get("proposition_verdict") != expected_verdict:
        raise ValueError(
            "proposition_verdict must exactly bind relation_to_proposition and the central statement"
        )
    if not position_text.startswith(expected_verdict):
        raise ValueError("position must begin with the complete proposition_verdict")
    problem_key_sha256 = _validate_stance_neutral_problem(graph)
    stance_neutral_problem = graph.get("stance_neutral_problem")
    if (
        not isinstance(stance_neutral_problem, Mapping)
        or stance_neutral_problem.get("proposition_under_test") != statement
    ):
        raise ValueError(
            "stance-neutral proposition under test must equal the central claim statement"
        )
    central_statement_sha256 = sha256_json(statement)

    attacks = _mapping_items(red_team.get("attacks"), field="red_team_report.attacks")
    if not attacks:
        raise ValueError("red-team report must contain at least one attack")
    try:
        strongest = max(attacks, key=lambda item: _IMPACT_RANK[str(item.get("position_impact"))])
    except KeyError as error:
        raise ValueError("red-team attack has an invalid position impact") from error
    counterposition = strongest.get("strongest_counterposition")
    if not isinstance(counterposition, str) or not counterposition.strip():
        raise ValueError("strongest attack has no counterposition")
    counters = _text_items(
        position.get("strongest_counterevidence"),
        field="position.strongest_counterevidence",
    )
    if not any(counterposition in item or item in counterposition for item in counters):
        raise ValueError("position omits the strongest red-team counterposition")
    why_not = _text_items(
        position.get("why_not_adopted"),
        field="position.why_not_adopted",
    )
    counter_tokens = _semantic_tokens("\n".join([counterposition, *counters]))
    if not counter_tokens or not any(
        _semantic_tokens(reason) & counter_tokens for reason in why_not
    ):
        raise ValueError(
            "why_not_adopted is not semantically tied to the strongest counterposition"
        )

    withdrawals = _text_items(
        position.get("withdrawal_conditions"),
        field="position.withdrawal_conditions",
    )
    linked_withdrawals = [item for item in withdrawals if counterposition in item]
    if not linked_withdrawals:
        raise ValueError("withdrawal conditions are not tied to the strongest counterposition")
    if not all(
        _contains_any(item, _CONDITIONAL_MARKERS)
        and _contains_any(item, _WITHDRAWAL_MARKERS)
        for item in linked_withdrawals
    ):
        raise ValueError("strongest-counter withdrawal must state a conditional judgment change")

    revision = strongest.get("revision")
    if (
        strongest.get("result") == "survived_with_revision"
        and isinstance(revision, str)
        and revision.strip()
        and revision not in "\n".join([*reasons, *withdrawals])
    ):
        raise ValueError("locked position does not carry the strongest attack revision")

    mechanisms = _mapping_items(graph.get("mechanisms"), field="claim_path_graph.mechanisms")
    labels = [item.get("label") for item in mechanisms if isinstance(item.get("label"), str)]
    runner_up = str(position.get("runner_up_explanation", ""))
    runner_labels = {label for label in labels if label in runner_up}
    leading_text = "\n".join([statement, position_text, *reasons])
    leading_labels = {label for label in labels if label in leading_text}
    runner_remainder = runner_up
    for label in runner_labels:
        runner_remainder = runner_remainder.replace(label, "")
    runner_remainder = re.sub(r"[\s\W_]+", "", runner_remainder)
    if (
        len(labels) < 2
        or not runner_labels
        or not (runner_labels - leading_labels)
        or len(runner_remainder) < 8
        or not _contains_any(runner_up, _EXPLANATION_MARKERS)
    ):
        raise ValueError("runner-up explanation must name a competing mechanism")

    action_ceiling = str(position.get("action_ceiling", ""))
    if not _contains_any(action_ceiling, _ACTION_DENIAL_MARKERS):
        raise ValueError("action ceiling must explicitly preserve the authorization boundary")
    if _contains_any(action_ceiling, _ACTION_GRANT_MARKERS):
        raise ValueError("position analysis may not grant real-world authorization")

    checks = _mapping_items(
        red_team.get("stability_checks"),
        field="red_team_report.stability_checks",
    )
    for index, check in enumerate(checks):
        pro_prompt = check.get("pro_prompt")
        anti_prompt = check.get("anti_prompt")
        if not isinstance(pro_prompt, str) or not isinstance(anti_prompt, str):
            raise ValueError(f"stability check {index} must preserve both prompt texts")
        if (
            check.get("pro_prompt_sha256") != sha256_json(pro_prompt)
            or check.get("anti_prompt_sha256") != sha256_json(anti_prompt)
        ):
            raise ValueError(
                f"stability check {index} prompt hashes are not derived from prompt text"
            )
        if pro_prompt == anti_prompt:
            raise ValueError(
                f"stability check {index} must use distinct pro and anti prompts"
            )
        before = check.get("evidence_basis_sha256_before")
        after = check.get("evidence_basis_sha256_after")
        drift = check.get("position_drift")
        before_problem_key = check.get("semantic_problem_sha256_before")
        after_problem_key = check.get("semantic_problem_sha256_after")
        before_position = check.get("central_position_id_before")
        after_position = check.get("central_position_id_after")
        before_statement = check.get("central_statement_sha256_before")
        after_statement = check.get("central_statement_sha256_after")
        before_relation = check.get("relation_to_proposition_before")
        after_relation = check.get("relation_to_proposition_after")
        before_strength = check.get("judgment_strength_before")
        after_strength = check.get("judgment_strength_after")
        before_ranking = _text_items(
            check.get("option_ranking_before"),
            field=f"red_team_report.stability_checks[{index}].option_ranking_before",
        )
        after_ranking = _text_items(
            check.get("option_ranking_after"),
            field=f"red_team_report.stability_checks[{index}].option_ranking_after",
        )
        before_option_kind_ranking = _text_items(
            check.get("option_kind_ranking_before"),
            field=f"red_team_report.stability_checks[{index}].option_kind_ranking_before",
        )
        after_option_kind_ranking = _text_items(
            check.get("option_kind_ranking_after"),
            field=f"red_team_report.stability_checks[{index}].option_kind_ranking_after",
        )
        before_semantic_ranking = _text_items(
            check.get("option_semantic_ranking_before"),
            field=f"red_team_report.stability_checks[{index}].option_semantic_ranking_before",
        )
        after_semantic_ranking = _text_items(
            check.get("option_semantic_ranking_after"),
            field=f"red_team_report.stability_checks[{index}].option_semantic_ranking_after",
        )
        before_selection_basis = check.get(
            "normative_selection_basis_sha256_before"
        )
        after_selection_basis = check.get(
            "normative_selection_basis_sha256_after"
        )
        if before != after:
            raise ValueError(
                f"stability check {index} must compare opposed prompts over identical evidence"
            )
        expected_bindings = (
            (before_problem_key, problem_key_sha256, "before-problem key"),
            (after_problem_key, problem_key_sha256, "after-problem key"),
            (before_position, position.get("central_claim_id"), "before-position"),
            (after_position, position.get("central_claim_id"), "after-position"),
            (before_statement, central_statement_sha256, "before-statement"),
            (after_statement, central_statement_sha256, "after-statement"),
            (
                before_relation,
                position.get("relation_to_proposition"),
                "before-relation",
            ),
            (
                after_relation,
                position.get("relation_to_proposition"),
                "after-relation",
            ),
            (before_strength, position.get("judgment_strength"), "before-strength"),
            (after_strength, position.get("judgment_strength"), "after-strength"),
        )
        for observed, expected, label in expected_bindings:
            if observed != expected:
                raise ValueError(
                    f"stability check {index} {label} does not bind the frozen judgment"
                )
        state_changed = (
            before_ranking != after_ranking
            or before_option_kind_ranking != after_option_kind_ranking
            or before_semantic_ranking != after_semantic_ranking
            or before_selection_basis != after_selection_basis
        )
        if drift != "none" or state_changed:
            raise ValueError(
                f"stability check {index} changes state inside a same-evidence stance probe"
            )
        explanation = str(check.get("explanation", ""))
        if not state_changed and _contains_any(explanation, _POSITIVE_DRIFT_CLAIMS):
            raise ValueError(
                f"stability check {index} explanation contradicts its frozen probe states"
            )

    return copy.deepcopy(position)


def validate_recommendation_semantics(
    run_contract: Mapping[str, object],
    recommendation: Mapping[str, object],
    *,
    position: Mapping[str, object],
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    """Validate the closed recommendation/not-requested branch for one run."""

    if not isinstance(run_contract, Mapping):
        raise ValueError("run contract must be a structured object")
    if run_contract.get("run_id") != expected_run_id:
        raise ValueError("run contract is bound to a different run")
    if run_contract.get("source_snapshot_sha256") != expected_source_snapshot_sha256:
        raise ValueError("run contract is bound to a different source snapshot")
    required = run_contract.get("recommendation_required")
    if type(required) is not bool:
        raise ValueError("run contract recommendation_required must be a real boolean")
    if not isinstance(recommendation, Mapping):
        raise ValueError("recommendation artifact must be a structured object")
    normalized_input = copy.deepcopy(dict(recommendation))
    if not required:
        if normalized_input != {"status": "not_requested"}:
            raise ValueError(
                "recommendation_required=false requires the exact closed not_requested artifact"
            )
        return normalized_input
    if normalized_input == {"status": "not_requested"}:
        raise ValueError("a required recommendation cannot use the not_requested branch")

    locked_position = validate_position_lock(
        position,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )
    normalized = validate_recommendation_lock(
        normalized_input,
        expected_run_id=expected_run_id,
        expected_source_snapshot_sha256=expected_source_snapshot_sha256,
    )
    if normalized.get("position_sha256") != sha256_json(locked_position):
        raise ValueError("recommendation is bound to a stale or different position")
    if _timestamp(normalized.get("locked_at"), field="recommendation.locked_at") <= _timestamp(
        locked_position.get("locked_at"), field="position.locked_at"
    ):
        raise ValueError("recommendation must be locked after the position")

    options = _mapping_items(normalized.get("options"), field="recommendation.options")
    option_ids = [item.get("option_id") for item in options]
    if any(not isinstance(item, str) for item in option_ids) or len(set(option_ids)) != len(option_ids):
        raise ValueError("recommendation option IDs must be unique text")
    option_kinds = {item.get("option_kind") for item in options}
    if option_kinds != _REQUIRED_OPTION_KINDS:
        raise ValueError("recommendation must cover all six canonical v8 option kinds")

    ranking = _text_items(normalized.get("ranking"), field="recommendation.ranking")
    if len(ranking) != len(option_ids) or set(ranking) != set(option_ids):
        raise ValueError("recommendation ranking must be a permutation of every option")
    evaluation_dimensions = _text_items(
        normalized.get("evaluation_dimensions"),
        field="recommendation.evaluation_dimensions",
    )
    if len(set(evaluation_dimensions)) != len(evaluation_dimensions):
        raise ValueError("recommendation evaluation dimensions must be unique")
    options_by_id = {str(item["option_id"]): item for item in options}
    expected_option_kind_ranking = [
        str(options_by_id[option_id].get("option_kind")) for option_id in ranking
    ]
    option_kind_ranking = _text_items(
        normalized.get("option_kind_ranking"),
        field="recommendation.option_kind_ranking",
    )
    if option_kind_ranking != expected_option_kind_ranking:
        raise ValueError("recommendation option-kind ranking is not a projection of ranking")
    raw_record_hashes = _mapping_items(
        normalized.get("option_record_hashes"),
        field="recommendation.option_record_hashes",
    )
    record_hashes = {
        record.get("option_id"): record.get("record_sha256")
        for record in raw_record_hashes
        if isinstance(record.get("option_id"), str)
    }
    if (
        len(record_hashes) != len(raw_record_hashes)
        or set(record_hashes) != set(options_by_id)
    ):
        raise ValueError("recommendation option-record hash map is not closed over options")
    for option_id, option in options_by_id.items():
        if record_hashes.get(option_id) != sha256_json(option):
            raise ValueError(
                f"recommendation option-record hash is stale for {option_id}"
            )
    expected_semantic_ranking = [
        sha256_json(_option_semantic_payload(options_by_id[option_id]))
        for option_id in ranking
    ]
    semantic_ranking = _text_items(
        normalized.get("option_semantic_ranking"),
        field="recommendation.option_semantic_ranking",
    )
    if semantic_ranking != expected_semantic_ranking:
        raise ValueError("recommendation semantic ranking is not a projection of ranking")

    ranking_policy = normalized.get("ranking_policy")
    ranking_evidence_refs = _text_items(
        normalized.get("ranking_evidence_refs"),
        field="recommendation.ranking_evidence_refs",
    )
    if ranking_policy == "promax_low_information_house_policy_not_v8":
        if len(options) != 6 or tuple(option_kind_ranking) != _HOUSE_OPTION_KIND_RANKING:
            raise ValueError(
                "ProMax low-information house policy requires exactly six options in its declared option-kind order"
            )
        if ranking_evidence_refs:
            raise ValueError(
                "ProMax low-information house policy cannot claim case-specific ranking evidence"
            )
    elif ranking_policy == "evidence_bound_case_comparison":
        if not ranking_evidence_refs:
            raise ValueError("evidence-bound ranking requires evidence references")
    else:
        raise ValueError("recommendation ranking policy is invalid")
    preferred = normalized.get("preferred_option_id")
    second = normalized.get("second_option_id")
    if preferred != ranking[0] or second != ranking[1] or preferred == second:
        raise ValueError("preferred and second options must match ranking positions one and two")
    no_action_ids = [
        str(option["option_id"])
        for option in options
        if option.get("option_kind") == "no_action"
    ]
    if len(no_action_ids) != 1 or normalized.get("no_action_option_id") != no_action_ids[0]:
        raise ValueError(
            "no_action_option_id must uniquely identify the canonical no_action option"
        )
    _validate_selection_review_wrapper(
        normalized,
        options=options,
        option_ids=[str(option_id) for option_id in option_ids],
        evaluation_dimensions=evaluation_dimensions,
        preferred_option_id=str(preferred),
        ranking_policy=ranking_policy,
        ranking_evidence_refs=ranking_evidence_refs,
    )

    switch_conditions = _text_items(
        normalized.get("switch_conditions"), field="recommendation.switch_conditions"
    )
    if not any(str(second) in condition for condition in switch_conditions):
        raise ValueError("switch conditions must identify the ranked second option")
    _text_items(
        normalized.get("inaction_consequences"),
        field="recommendation.inaction_consequences",
    )

    if normalized.get("authorization_status") == "authorized":
        raise ValueError("analysis cannot grant recommendation authorization")
    for option in options:
        _text_items(option.get("stop_conditions"), field="recommendation option stop_conditions")
        _text_items(
            option.get("rollback_and_remedy"),
            field="recommendation option rollback_and_remedy",
        )
    joined_text = "\n".join(_all_text(normalized))
    if _contains_any(joined_text, _ACTION_GRANT_MARKERS):
        raise ValueError("recommendation text leaks real-world authorization")

    return copy.deepcopy(normalized)
