from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests" / "evals" / "promax-green"
RUBRIC_PATH = EVAL_ROOT / "rubric.json"
RESULTS_PATH = EVAL_ROOT / "results.json"
EVALUATED_SKILL_TREE_PATH = EVAL_ROOT / "evaluated-skill-tree.json"
PROMAX_ROOT = ROOT / "skills" / "crossframe-promax"
RUNTIME_SCRIPTS = PROMAX_ROOT / "scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.position import (
    selection_review_basis_sha256 as production_selection_review_basis_sha256,
)

ANALYSIS_SCENARIOS = ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2"]
ARTIFACT_WORKSPACE = EVAL_ROOT / "artifacts"
REQUIRED_SEMANTIC_ARTIFACTS = (
    "promax-claim-path-graph.json",
    "promax-position.locked.json",
    "promax-recommendation.locked.json",
    "promax-red-team-report.json",
)
SEMANTIC_PROBLEM_FIELDS = (
    "analysis_object",
    "proposition_under_test",
    "time_window",
)
V8_OPTION_FIELDS = frozenset(
    {
        "option_id",
        "option_kind",
        "description",
        "forecast_refs",
        "normative_premise_refs",
        "affected_position_refs",
        "rights_floor_refs",
        "expected_paths",
        "worst_acceptable_outcome",
        "cross_circle_spillovers",
        "distribution_of_costs_and_benefits",
        "information_value",
        "lock_in_risk",
        "reversibility",
        "resource_cost",
        "authorized_actor_ref",
        "authorization_record_ref",
        "stop_conditions",
        "rollback_and_remedy",
    }
)
V8_OPTION_KINDS = frozenset(
    {
        "maintain_status_quo",
        "active_action",
        "delayed_action",
        "probe_action",
        "exit_or_transfer",
        "no_action",
    }
)
SELECTION_SOURCE_PARAGRAPHS = (
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
NORMATIVE_STATEMENTS = {
    "N1": "解释不授权处置",
    "N2": "保护不得降级",
    "N3": "高影响判断可纠错",
    "N4": "不征用爱与承担",
    "N5": "存续与筛选不等于正当",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")


def sha256_json(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def option_semantic_payload(option: dict[str, object]) -> dict[str, object]:
    """Return the v8 option semantics without its run-local identifier."""
    return {key: value for key, value in option.items() if key != "option_id"}


def _json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load required semantic artifact {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"required semantic artifact must be a JSON object: {path}")
    return value


def _mapping(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _list(value: object, *, field: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def _text_items(value: object, *, field: str) -> list[str]:
    items = _list(value, field=field)
    normalized: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be non-empty text")
        normalized.append(item.strip())
    return normalized


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


def _require_equal(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise ValueError(f"{label} does not match the recomputed artifact value")


def _selection_review_semantics(
    recommendation: dict[str, object],
    *,
    options: list[dict[str, object]],
    option_by_id: dict[str, dict[str, object]],
    ranking: list[object],
    retrieval: dict[str, object],
) -> str:
    wrapper = _mapping(
        recommendation.get("selection_review_wrapper"),
        field="recommendation.selection_review_wrapper",
    )
    _require_equal(
        "selection-review wrapper role",
        wrapper.get("wrapper_role"),
        "promax_machine_verification_wrapper_not_v8_source_schema",
    )
    _require_equal(
        "selection-review wrapper schema ID",
        wrapper.get("wrapper_schema_id"),
        "crossframe.promax.selection-review-wrapper",
    )
    _require_equal(
        "selection-review wrapper schema version",
        wrapper.get("wrapper_schema_version"),
        1,
    )
    _require_equal(
        "selection-review source paragraphs",
        wrapper.get("source_paragraph_refs"),
        list(SELECTION_SOURCE_PARAGRAPHS),
    )
    if wrapper.get("selection_type") not in {"SEL-AGT", "SEL-GOV"}:
        raise ValueError("selection-review type must be SEL-AGT or SEL-GOV")
    _require_equal(
        "selection-review status",
        wrapper.get("selection_status"),
        "under_review",
    )

    premise_records = [
        _mapping(item, field=f"public_value_premises[{index}]")
        for index, item in enumerate(
            _list(
                wrapper.get("public_value_premises"),
                field="selection_review.public_value_premises",
            )
        )
    ]
    premise_by_id: dict[str, dict[str, object]] = {}
    for premise in premise_records:
        premise_id = premise.get("normative_principle_id")
        if not isinstance(premise_id, str) or premise_id not in NORMATIVE_STATEMENTS:
            raise ValueError("selection-review uses an invalid N1-N5 premise")
        if premise_id in premise_by_id:
            raise ValueError("selection-review repeats a normative premise")
        _require_equal(
            f"authoritative {premise_id} statement",
            premise.get("statement"),
            NORMATIVE_STATEMENTS[premise_id],
        )
        premise_by_id[premise_id] = premise
    if (
        premise_by_id.get("N1", {}).get("role") != "veto_gate"
        or not set(premise_by_id).intersection({"N2", "N3", "N4", "N5"})
    ):
        raise ValueError("selection-review requires N1 plus a positive N2-N5 premise")
    option_premises = {
        ref
        for option in options
        for ref in _text_items(
            option.get("normative_premise_refs"),
            field="option.normative_premise_refs",
        )
    }
    _require_equal(
        "selection-review option premise closure",
        option_premises,
        set(premise_by_id),
    )

    rights_floor = set(
        _text_items(
            wrapper.get("rights_floor"),
            field="selection_review.rights_floor",
        )
    )
    option_rights = {
        ref
        for option in options
        for ref in _text_items(
            option.get("rights_floor_refs"),
            field="option.rights_floor_refs",
        )
    }
    _require_equal("selection-review rights-floor closure", rights_floor, option_rights)
    if not rights_floor or not rights_floor.issubset(
        {f"PF-{index}" for index in range(1, 11)}
    ):
        raise ValueError("selection-review rights floor must use PF-1 through PF-10")

    affected_positions = set(
        _text_items(
            wrapper.get("affected_positions"),
            field="selection_review.affected_positions",
        )
    )
    option_positions = {
        ref
        for option in options
        for ref in _text_items(
            option.get("affected_position_refs"),
            field="option.affected_position_refs",
        )
    }
    _require_equal(
        "selection-review affected-position closure",
        affected_positions,
        option_positions,
    )
    low_power_positions = set(
        _text_items(
            wrapper.get("low_power_position_ids"),
            field="selection_review.low_power_position_ids",
        )
    )
    if not low_power_positions or not low_power_positions.issubset(
        affected_positions
    ):
        raise ValueError(
            "selection-review low-power positions must be a non-empty affected subset"
        )

    conflicts = [
        _mapping(item, field=f"value_conflicts[{index}]")
        for index, item in enumerate(
            _list(
                wrapper.get("value_conflicts"),
                field="selection_review.value_conflicts",
            )
        )
    ]
    conflict_ids = [conflict.get("conflict_id") for conflict in conflicts]
    if len(set(conflict_ids)) != len(conflict_ids):
        raise ValueError("selection-review repeats a value-conflict ID")
    unresolved_expected: set[object] = set()
    for conflict in conflicts:
        if not set(
            _text_items(
                conflict.get("premise_ids"),
                field="value_conflict.premise_ids",
            )
        ).issubset(set(premise_by_id)):
            raise ValueError("value conflict cites an unregistered premise")
        if not set(
            _text_items(
                conflict.get("affected_position_refs"),
                field="value_conflict.affected_position_refs",
            )
        ).issubset(affected_positions):
            raise ValueError("value conflict cites an unregistered affected position")
        if conflict.get("status") in {"open", "paused"}:
            unresolved_expected.update(
                _text_items(
                    conflict.get("dissent_refs"),
                    field="value_conflict.dissent_refs",
                )
            )
    _require_equal(
        "unresolved dissent closure",
        set(
            _text_items(
                wrapper.get("unresolved_dissent_refs"),
                field="selection_review.unresolved_dissent_refs",
            )
        ),
        unresolved_expected,
    )

    preferred_option_id = recommendation.get("preferred_option_id")
    if (
        not ranking
        or preferred_option_id != ranking[0]
        or preferred_option_id not in option_by_id
    ):
        raise ValueError("selection-review preferred option is not ranking[0]")
    boundary = _mapping(
        wrapper.get("jurisdiction_review_boundary"),
        field="selection_review.jurisdiction_review_boundary",
    )
    _require_equal(
        "jurisdiction boundary role",
        boundary.get("boundary_role"),
        "promax_review_boundary_not_atomic_v8_j_tuple",
    )
    _require_equal(
        "jurisdiction reviewed option",
        boundary.get("reviewed_option_id"),
        preferred_option_id,
    )
    preferred_option = option_by_id[str(preferred_option_id)]
    _require_equal(
        "jurisdiction reviewed actor",
        boundary.get("decision_actor_ref"),
        preferred_option.get("authorized_actor_ref"),
    )
    _require_equal(
        "jurisdiction reviewed authorization source",
        boundary.get("authorization_source_ref"),
        preferred_option.get("authorization_record_ref"),
    )
    valid_from = _timestamp(
        boundary.get("valid_from"),
        field="selection_review.jurisdiction_review_boundary.valid_from",
    )
    valid_until = _timestamp(
        boundary.get("valid_until"),
        field="selection_review.jurisdiction_review_boundary.valid_until",
    )
    if valid_until <= valid_from:
        raise ValueError("selection-review jurisdiction validity must be positive")
    recommendation_locked_at = _timestamp(
        recommendation.get("locked_at"),
        field="recommendation.locked_at",
    )

    evaluation_dimensions = _text_items(
        recommendation.get("evaluation_dimensions"),
        field="recommendation.evaluation_dimensions",
    )
    if not evaluation_dimensions:
        raise ValueError("recommendation evaluation dimensions must be non-empty")
    policy = recommendation.get("ranking_policy")
    ranking_evidence_refs = _text_items(
        recommendation.get("ranking_evidence_refs"),
        field="recommendation.ranking_evidence_refs",
    )
    normalized_reviews: dict[str, object] = {}
    preferred_semantic = sha256_json(
        option_semantic_payload(preferred_option)
    )
    for review_name, principle_id in (
        ("least_harm", "NSP-LEAST-HARM"),
        ("proportionality", "NSP-PROPORTIONALITY"),
    ):
        review = _mapping(
            wrapper.get(review_name),
            field=f"selection_review.{review_name}",
        )
        _require_equal(
            f"{review_name} principle",
            review.get("principle_id"),
            principle_id,
        )
        _require_equal(
            f"{review_name} selected option",
            review.get("selected_option_id"),
            preferred_option_id,
        )
        compared_ids = _text_items(
            review.get("compared_option_ids"),
            field=f"selection_review.{review_name}.compared_option_ids",
        )
        if len(compared_ids) != len(option_by_id) or set(compared_ids) != set(
            option_by_id
        ):
            raise ValueError(f"{review_name} does not compare every option")
        _require_equal(
            f"{review_name} evaluation dimensions",
            _text_items(
                review.get("evaluation_dimensions"),
                field=f"selection_review.{review_name}.evaluation_dimensions",
            ),
            evaluation_dimensions,
        )
        if review.get("reviewer_ref") == boundary.get("decision_actor_ref"):
            raise ValueError(f"{review_name} reviewer is not independent")
        if _timestamp(
            review.get("reviewed_at"),
            field=f"selection_review.{review_name}.reviewed_at",
        ) > recommendation_locked_at:
            raise ValueError(
                f"{review_name} cannot postdate the recommendation lock"
            )
        review_evidence_refs = set(
            _text_items(
                review.get("evidence_refs"),
                field=f"selection_review.{review_name}.evidence_refs",
            )
        )
        if not review_evidence_refs.issubset(set(ranking_evidence_refs)):
            raise ValueError(
                f"{review_name} cites evidence outside ranking_evidence_refs"
            )
        if review.get("status") == "passed" and not review_evidence_refs:
            raise ValueError(f"{review_name} cannot pass without evidence")
        normalized_reviews[review_name] = {
            "principle_id": principle_id,
            "principle_version": review.get("principle_version"),
            "selected_option_semantic_sha256": preferred_semantic,
            "compared_option_semantic_sha256": sorted(
                sha256_json(option_semantic_payload(option_by_id[str(option_id)]))
                for option_id in compared_ids
            ),
            "evaluation_dimensions": list(evaluation_dimensions),
            "status": review.get("status"),
        }

    eligibility = _mapping(
        wrapper.get("declared_low_information_house_policy_eligibility"),
        field="selection_review.declared_low_information_house_policy_eligibility",
    )
    case_facts = eligibility.get("case_specific_facts_present")
    choice_evidence = eligibility.get(
        "choice_changing_retrieval_evidence_present"
    )
    if type(case_facts) is not bool or type(choice_evidence) is not bool:
        raise ValueError("selection-review eligibility flags must be booleans")
    supports = [
        _mapping(item, field=f"ranking_support[{index}]")
        for index, item in enumerate(
            _list(wrapper.get("ranking_support"), field="selection_review.ranking_support")
        )
    ]
    if policy == "promax_low_information_house_policy_not_v8":
        if case_facts or choice_evidence or ranking_evidence_refs or supports:
            raise ValueError("low-information house-policy eligibility is contradicted")
    elif policy == "evidence_bound_case_comparison":
        if not (case_facts or choice_evidence):
            raise ValueError("evidence-bound policy lacks declared eligibility")
        expected_cells = {
            (option_id, dimension)
            for option_id in option_by_id
            for dimension in evaluation_dimensions
        }
        observed_cells: set[tuple[object, object]] = set()
        support_refs: set[object] = set()
        for support in supports:
            cell = (
                _text_items(
                    [support.get("option_id")],
                    field="selection_review.ranking_support.option_id",
                )[0],
                _text_items(
                    [support.get("evaluation_dimension")],
                    field="selection_review.ranking_support.evaluation_dimension",
                )[0],
            )
            if cell in observed_cells:
                raise ValueError("ranking-support matrix repeats a cell")
            observed_cells.add(cell)
            refs = _text_items(
                support.get("evidence_refs"),
                field="selection_review.ranking_support.evidence_refs",
            )
            if not refs:
                raise ValueError("ranking-support cell has no evidence")
            support_refs.update(refs)
        _require_equal("ranking-support matrix", observed_cells, expected_cells)
        _require_equal(
            "ranking evidence union",
            support_refs,
            set(ranking_evidence_refs),
        )
        retrieval_ids = {
            entry.get("retrieval_id")
            for entry in _list(retrieval.get("entries"), field="retrieval.entries")
            if isinstance(entry, dict)
        }
        if not support_refs.issubset(retrieval_ids):
            raise ValueError("ranking-support evidence has a ghost retrieval reference")
    else:
        raise ValueError("recommendation ranking policy is invalid")

    basis = {
        "wrapper_role": wrapper.get("wrapper_role"),
        "source_paragraph_refs": wrapper.get("source_paragraph_refs"),
        "selection_type": wrapper.get("selection_type"),
        "selection_status": wrapper.get("selection_status"),
        "public_value_premises": sorted(
            (
                premise_id,
                premise.get("role"),
                premise.get("statement"),
            )
            for premise_id, premise in premise_by_id.items()
        ),
        "value_conflicts": sorted(
            (
                tuple(
                    sorted(
                        _text_items(
                            conflict.get("premise_ids"),
                            field="value_conflict.premise_ids",
                        )
                    )
                ),
                len(
                    _text_items(
                        conflict.get("affected_position_refs"),
                        field="value_conflict.affected_position_refs",
                    )
                ),
                len(
                    _text_items(
                        conflict.get("dissent_refs"),
                        field="value_conflict.dissent_refs",
                    )
                ),
                str(conflict.get("status")),
            )
            for conflict in conflicts
        ),
        "rights_floor": sorted(rights_floor),
        "affected_position_count": len(affected_positions),
        "low_power_position_count": len(low_power_positions),
        "procedure_states": wrapper.get("procedure_states"),
        "jurisdiction_review_boundary": {
            "boundary_role": boundary.get("boundary_role"),
            "reviewed_option_semantic_sha256": preferred_semantic,
            "scope": boundary.get("scope"),
            "authorization_status": boundary.get("authorization_status"),
        },
        "principle_reviews": normalized_reviews,
        "ranking_policy": policy,
        "declared_eligibility": {
            "case_specific_facts_present": case_facts,
            "choice_changing_retrieval_evidence_present": choice_evidence,
        },
    }
    return sha256_json(basis)


def load_artifact_semantics(
    artifact_dir: Path | str,
    *,
    allowed_root: Path | None = None,
) -> dict[str, object]:
    artifact_path = Path(artifact_dir).resolve()
    if allowed_root is not None:
        allowed_path = allowed_root.resolve()
        try:
            artifact_path.relative_to(allowed_path)
        except ValueError as error:
            raise ValueError(
                f"artifact_dir escapes the allowed GREEN workspace: {artifact_path}"
            ) from error
    if not artifact_path.is_dir():
        raise ValueError(f"artifact_dir is not a directory: {artifact_path}")

    documents: dict[str, dict[str, object]] = {}
    for filename in REQUIRED_SEMANTIC_ARTIFACTS:
        path = artifact_path / filename
        if not path.is_file():
            raise ValueError(f"required semantic artifact is missing: {path}")
        documents[filename] = _json_object(path)

    graph = documents["promax-claim-path-graph.json"]
    position = documents["promax-position.locked.json"]
    recommendation = documents["promax-recommendation.locked.json"]
    red_team = documents["promax-red-team-report.json"]
    run_contract = _json_object(artifact_path / "promax-run-contract.json")
    local_world = _json_object(
        artifact_path / "promax-local-world-model.locked.json"
    )
    retrieval = _json_object(artifact_path / "promax-retrieval-ledger.json")
    evidence_basis_sha256 = sha256_json(
        {
            "request_sha256": run_contract.get("request_sha256"),
            "local_world_model_sha256": sha256_json(local_world),
            "retrieval_ledger_sha256": sha256_json(retrieval),
            "source_snapshot_sha256": run_contract.get("source_snapshot_sha256"),
        }
    )

    problem = _mapping(
        graph.get("stance_neutral_problem"),
        field="claim_path_graph.stance_neutral_problem",
    )
    semantic_problem_payload = {
        field: problem.get(field) for field in SEMANTIC_PROBLEM_FIELDS
    }
    semantic_key_sha256 = sha256_json(semantic_problem_payload)
    _require_equal(
        "stance-neutral semantic_key_sha256",
        problem.get("semantic_key_sha256"),
        semantic_key_sha256,
    )

    central_claim_id = graph.get("central_claim_id")
    if not isinstance(central_claim_id, str) or not central_claim_id.strip():
        raise ValueError("claim graph central_claim_id must be non-empty text")
    claims = _list(graph.get("claims"), field="claim_path_graph.claims")
    central_claims = [
        _mapping(claim, field=f"claim_path_graph.claims[{index}]")
        for index, claim in enumerate(claims)
        if isinstance(claim, dict) and claim.get("claim_id") == central_claim_id
    ]
    if len(central_claims) != 1:
        raise ValueError("claim graph must contain exactly one central claim record")
    central_statement = central_claims[0].get("statement")
    if not isinstance(central_statement, str) or not central_statement.strip():
        raise ValueError("central claim statement must be non-empty text")
    _require_equal(
        "proposition under test",
        problem.get("proposition_under_test"),
        central_statement,
    )
    central_statement_sha256 = sha256_json(central_statement)

    _require_equal(
        "position central claim",
        position.get("central_claim_id"),
        central_claim_id,
    )
    relation = position.get("relation_to_proposition")
    if relation not in {"supports", "rejects", "mixed", "indeterminate"}:
        raise ValueError("position relation_to_proposition is invalid")
    judgment_strength = position.get("judgment_strength")
    if judgment_strength not in {"tentative", "moderate", "strong", "indeterminate"}:
        raise ValueError("position judgment_strength is invalid")

    options: list[dict[str, object]] = []
    ranking: list[object] = []
    option_kind_ranking: list[object] = []
    option_semantic_ranking: list[str] = []
    option_record_hashes: dict[str, str] = {}
    no_action_option_id: str | None = None
    normative_selection_basis_sha256 = sha256_json({"status": "not_requested"})
    if recommendation != {"status": "not_requested"}:
        raw_options = _list(recommendation.get("options"), field="recommendation.options")
        if not raw_options:
            raise ValueError("recommendation.options must not be empty")
        for index, raw_option in enumerate(raw_options):
            option = _mapping(raw_option, field=f"recommendation.options[{index}]")
            if set(option) != V8_OPTION_FIELDS:
                raise ValueError(
                    f"recommendation.options[{index}] must contain the exact v8 option fields"
                )
            if option.get("option_kind") not in V8_OPTION_KINDS:
                raise ValueError(
                    f"recommendation.options[{index}].option_kind is not a v8 option kind"
                )
            options.append(option)
        option_ids = [option.get("option_id") for option in options]
        if any(not isinstance(option_id, str) or not option_id for option_id in option_ids):
            raise ValueError("recommendation option IDs must be non-empty text")
        if len(set(option_ids)) != len(option_ids):
            raise ValueError("recommendation option IDs must be unique")
        if {option.get("option_kind") for option in options} != V8_OPTION_KINDS:
            raise ValueError("recommendation must cover every exact v8 option_kind")

        ranking = _list(recommendation.get("ranking"), field="recommendation.ranking")
        if len(ranking) != len(option_ids) or set(ranking) != set(option_ids):
            raise ValueError("recommendation ranking must be a permutation of option IDs")
        option_by_id = {str(option["option_id"]): option for option in options}
        option_kind_ranking = [
            option_by_id[str(option_id)]["option_kind"] for option_id in ranking
        ]
        option_semantic_ranking = [
            sha256_json(option_semantic_payload(option_by_id[str(option_id)]))
            for option_id in ranking
        ]
        _require_equal(
            "option kind ranking",
            recommendation.get("option_kind_ranking"),
            option_kind_ranking,
        )
        _require_equal(
            "option semantic ranking",
            recommendation.get("option_semantic_ranking"),
            option_semantic_ranking,
        )
        raw_record_hashes = _list(
            recommendation.get("option_record_hashes"),
            field="recommendation.option_record_hashes",
        )
        for index, raw_record_hash in enumerate(raw_record_hashes):
            record_hash = _mapping(
                raw_record_hash,
                field=f"recommendation.option_record_hashes[{index}]",
            )
            if set(record_hash) != {"option_id", "record_sha256"}:
                raise ValueError(
                    "recommendation option-record hash entries must contain only "
                    "option_id and record_sha256"
                )
            option_id = record_hash.get("option_id")
            record_sha256 = record_hash.get("record_sha256")
            if not isinstance(option_id, str) or option_id not in option_by_id:
                raise ValueError(
                    "recommendation option-record hash refers to an unknown option"
                )
            if option_id in option_record_hashes:
                raise ValueError(
                    "recommendation option-record hash map contains a duplicate option"
                )
            if not isinstance(record_sha256, str):
                raise ValueError(
                    "recommendation option-record hash must be SHA-256 text"
                )
            option_record_hashes[option_id] = record_sha256
        if set(option_record_hashes) != set(option_by_id):
            raise ValueError(
                "recommendation option-record hash map is not closed over options"
            )
        for option_id, option in option_by_id.items():
            _require_equal(
                f"full option record hash for {option_id}",
                option_record_hashes[option_id],
                sha256_json(option),
            )

        no_action_ids = [
            str(option["option_id"])
            for option in options
            if option.get("option_kind") == "no_action"
        ]
        if len(no_action_ids) != 1:
            raise ValueError(
                "recommendation must contain exactly one canonical no_action option"
            )
        no_action_option_id = recommendation.get("no_action_option_id")
        _require_equal(
            "no_action option pointer",
            no_action_option_id,
            no_action_ids[0],
        )
        normative_selection_basis_sha256 = _selection_review_semantics(
            recommendation,
            options=options,
            option_by_id=option_by_id,
            ranking=ranking,
            retrieval=retrieval,
        )

    _require_equal(
        "red-team central claim",
        red_team.get("central_claim_id"),
        central_claim_id,
    )
    stability_checks = _list(
        red_team.get("stability_checks"),
        field="red_team_report.stability_checks",
    )
    if not stability_checks:
        raise ValueError("red-team report must contain a stability check")
    for index, raw_check in enumerate(stability_checks):
        check = _mapping(
            raw_check,
            field=f"red_team_report.stability_checks[{index}]",
        )
        pro_prompt = check.get("pro_prompt")
        anti_prompt = check.get("anti_prompt")
        if not isinstance(pro_prompt, str) or not isinstance(anti_prompt, str):
            raise ValueError(f"stability check {index} prompts must be text")
        if pro_prompt == anti_prompt:
            raise ValueError(f"stability check {index} prompts must be opposed")
        _require_equal(
            f"stability check {index} pro prompt hash",
            check.get("pro_prompt_sha256"),
            sha256_json(pro_prompt),
        )
        _require_equal(
            f"stability check {index} anti prompt hash",
            check.get("anti_prompt_sha256"),
            sha256_json(anti_prompt),
        )
        _require_equal(
            f"stability check {index} evidence basis before/after",
            check.get("evidence_basis_sha256_before"),
            check.get("evidence_basis_sha256_after"),
        )
        for side in ("before", "after"):
            if check.get(f"evidence_basis_sha256_{side}") != evidence_basis_sha256:
                raise ValueError(
                    f"stability check {index} evidence basis {side} does not bind "
                    "the actual evidence artifacts"
                )
        expected_bindings = {
            "semantic_problem_sha256": semantic_key_sha256,
            "central_position_id": central_claim_id,
            "central_statement_sha256": central_statement_sha256,
            "relation_to_proposition": relation,
            "judgment_strength": judgment_strength,
            "option_ranking": ranking,
            "option_kind_ranking": option_kind_ranking,
            "option_semantic_ranking": option_semantic_ranking,
            "normative_selection_basis_sha256": normative_selection_basis_sha256,
        }
        for field, expected in expected_bindings.items():
            for side in ("before", "after"):
                label = field.replace("_", " ")
                _require_equal(
                    f"stability check {index} {label} {side}",
                    check.get(f"{field}_{side}"),
                    expected,
                )
        _require_equal(
            f"stability check {index} position drift",
            check.get("position_drift"),
            "none",
        )

    return {
        "artifact_dir": artifact_path,
        "analysis_object": problem.get("analysis_object"),
        "proposition_under_test": problem.get("proposition_under_test"),
        "time_window": problem.get("time_window"),
        "evidence_cutoff": problem.get("evidence_cutoff"),
        "evidence_basis_sha256": evidence_basis_sha256,
        "semantic_key_sha256": semantic_key_sha256,
        "central_statement_sha256": central_statement_sha256,
        "relation_to_proposition": relation,
        "judgment_strength": judgment_strength,
        "option_ranking": ranking,
        "option_kind_ranking": option_kind_ranking,
        "option_record_hashes": option_record_hashes,
        "option_semantic_ranking": option_semantic_ranking,
        "normative_selection_basis_sha256": normative_selection_basis_sha256,
        "no_action_option_id": no_action_option_id,
    }


def canonical_skill_tree_sha256(skill_root: Path | None = None) -> str:
    root = PROMAX_ROOT if skill_root is None else Path(skill_root)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "references/.v8-full-source.lock":
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def evaluated_skill_tree_record() -> dict[str, object]:
    value = json.loads(EVALUATED_SKILL_TREE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evaluated skill tree record must be an object")
    return value


def evaluated_skill_tree_sha256() -> str:
    value = evaluated_skill_tree_record().get("evaluated_skill_tree_sha256")
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("evaluated skill tree hash must be SHA-256 text")
    return value


def metric_passes(
    direction: str,
    numerator: int,
    denominator: int,
    threshold: float,
) -> bool:
    if denominator <= 0:
        raise ValueError("applicable metric denominator must be positive")
    rate = numerator / denominator
    if direction == "minimum":
        return rate >= threshold
    if direction == "maximum":
        return rate <= threshold
    raise ValueError(f"unsupported metric direction: {direction}")


class ProMaxGreenRubricScopeTests(unittest.TestCase):
    def test_skill_tree_hash_excludes_runtime_cache_and_coordination_lock(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            (skill_root / "references").mkdir()
            (skill_root / "scripts/__pycache__").mkdir(parents=True)
            (skill_root / "SKILL.md").write_text("stable", encoding="utf-8")
            expected = canonical_skill_tree_sha256(skill_root)

            (skill_root / "references/.v8-full-source.lock").write_bytes(b"\x00")
            (skill_root / "scripts/__pycache__/module.pyc").write_bytes(b"cache")

            self.assertEqual(canonical_skill_tree_sha256(skill_root), expected)

    def test_green_artifacts_are_commit_replayable(self) -> None:
        self.assertEqual(ARTIFACT_WORKSPACE, EVAL_ROOT / "artifacts")
        self.assertFalse(
            ARTIFACT_WORKSPACE.is_relative_to(ROOT / "work"),
            "GREEN evidence cannot live under the ignored work directory",
        )

    def test_analysis_artifact_metrics_exclude_operational_only_scenarios(self) -> None:
        rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        metrics = {item["metric_id"]: item for item in rubric["metrics"]}
        for metric_id in (
            "canonical_concept_terminal_coverage",
            "central_claim_traceability",
            "strongest_countercase_coverage",
            "typed_example_integrity",
        ):
            self.assertEqual(
                metrics[metric_id]["applicable_scenarios"],
                ANALYSIS_SCENARIOS,
                metric_id,
            )

    def test_matrix_reduction_records_unexercised_scenario_specific_metrics(
        self,
    ) -> None:
        rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        declared_scenarios = {
            entry["scenario_id"] for entry in rubric["run_matrix"]
        }
        unexercised = {
            metric["metric_id"]
            for metric in rubric["metrics"]
            if metric["applicable_scenarios"] != "all"
            and not declared_scenarios.intersection(
                metric["applicable_scenarios"]
            )
        }
        self.assertEqual(
            unexercised,
            {
                "honest_tool_failure_downgrade",
                "exact_promax_routing",
            },
        )

    def test_paired_stability_compares_semantics_not_run_local_labels(self) -> None:
        rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        paired = rubric["paired_stability"]
        self.assertEqual(paired["required_model_ids"], ["gpt-5.6-sol"])
        self.assertEqual(
            paired["required_equal_fields"],
            [
                "semantic_key_sha256",
                "relation_to_proposition",
                "judgment_strength",
                "option_kind_ranking",
                "option_semantic_ranking",
                "normative_selection_basis_sha256",
            ],
        )
        self.assertNotIn("central_position_id", paired["required_equal_fields"])
        self.assertNotIn("option_ranking", paired["required_equal_fields"])

    def test_paired_stability_freezes_external_context_and_artifact_sources(self) -> None:
        rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        paired = rubric["paired_stability"]
        self.assertEqual(
            paired["artifact_files"],
            list(REQUIRED_SEMANTIC_ARTIFACTS),
        )
        frozen_context = paired["frozen_pair_context"]
        self.assertEqual(
            frozen_context,
            {
                "analysis_object": "远程办公对组织信任的影响",
                "factual_material": [],
                "time_window": "未指定",
                "evidence_cutoff": "2026-07-23T00:00:00+08:00",
            },
        )
        self.assertEqual(
            paired["frozen_pair_context_sha256"],
            sha256_json(frozen_context),
        )
        self.assertIn("not evidence", paired["verification_source"])


class ProMaxGreenMetricSemanticsTests(unittest.TestCase):
    def test_minimum_and_maximum_metrics_use_opposite_threshold_directions(self) -> None:
        self.assertTrue(metric_passes("minimum", 1, 1, 1.0))
        self.assertFalse(metric_passes("minimum", 0, 1, 1.0))
        self.assertTrue(metric_passes("maximum", 0, 1, 0.0))
        self.assertFalse(metric_passes("maximum", 1, 1, 0.0))

    def test_unknown_direction_and_zero_denominator_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "denominator"):
            metric_passes("minimum", 0, 0, 1.0)
        with self.assertRaisesRegex(ValueError, "direction"):
            metric_passes("sideways", 0, 1, 0.0)


class ProMaxGreenArtifactSemanticsTests(unittest.TestCase):
    @staticmethod
    def _hash_json(value: object) -> str:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _write_bundle(self, artifact_dir: Path) -> dict[str, object]:
        statement = "The tested proposition remains the same under opposed user verdicts."
        problem_payload = {
            "analysis_object": "one frozen institutional choice",
            "proposition_under_test": statement,
            "time_window": "2026-Q3",
        }
        semantic_key = self._hash_json(problem_payload)
        graph = {
            "central_claim_id": "CLAIM-CENTRAL",
            "stance_neutral_problem": {
                **problem_payload,
                "evidence_cutoff": "2026-07-23T00:00:00+08:00",
                "semantic_key_sha256": semantic_key,
            },
            "claims": [
                {"claim_id": "CLAIM-CENTRAL", "statement": statement},
            ],
        }
        position = {
            "central_claim_id": "CLAIM-CENTRAL",
            "relation_to_proposition": "supports",
            "judgment_strength": "moderate",
        }
        option_kinds = [
            "probe_action",
            "active_action",
            "maintain_status_quo",
            "delayed_action",
            "exit_or_transfer",
            "no_action",
        ]
        options = []
        for index, option_kind in enumerate(option_kinds, start=1):
            options.append(
                {
                    "option_id": f"OPTION-{index}",
                    "option_kind": option_kind,
                    "description": f"Concrete option {index}",
                    "forecast_refs": ["FORECAST-1"],
                    "normative_premise_refs": ["N1", "N2"],
                    "affected_position_refs": ["POSITION-1"],
                    "rights_floor_refs": ["PF-1"],
                    "expected_paths": ["PATH-1"],
                    "worst_acceptable_outcome": "bounded loss",
                    "cross_circle_spillovers": ["spillover-1"],
                    "distribution_of_costs_and_benefits": "costs and benefits stated",
                    "information_value": "information value stated",
                    "lock_in_risk": "lock-in risk stated",
                    "reversibility": "reversibility stated",
                    "resource_cost": "resource cost stated",
                    "authorized_actor_ref": "ACTOR-1",
                    "authorization_record_ref": "AUTH-1",
                    "stop_conditions": ["stop-1"],
                    "rollback_and_remedy": ["rollback-1"],
                }
            )
        ranking = [str(option["option_id"]) for option in options]
        evaluation_dimensions = ["structure", "reversibility", "risk"]
        option_record_hashes = [
            {
                "option_id": str(option["option_id"]),
                "record_sha256": self._hash_json(option),
            }
            for option in options
        ]
        option_semantic_ranking = [
            self._hash_json(option_semantic_payload(option)) for option in options
        ]
        base_review = {
            "principle_version": "v8",
            "selected_option_id": ranking[0],
            "compared_option_ids": [*ranking],
            "evaluation_dimensions": [*evaluation_dimensions],
            "sufficient_reason": "The frozen low-information comparison remains pending.",
            "evidence_refs": [],
            "reviewer_ref": "REVIEWER-1",
            "reviewed_at": "2026-07-23T00:00:00+00:00",
            "status": "pending",
        }
        selection_review_wrapper = {
            "wrapper_schema_id": "crossframe.promax.selection-review-wrapper",
            "wrapper_schema_version": 1,
            "wrapper_role": "promax_machine_verification_wrapper_not_v8_source_schema",
            "source_paragraph_refs": list(SELECTION_SOURCE_PARAGRAPHS),
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
            "value_conflicts": [],
            "unresolved_dissent_refs": [],
            "rights_floor": ["PF-1"],
            "affected_positions": ["POSITION-1"],
            "low_power_position_ids": ["POSITION-1"],
            "jurisdiction_review_boundary": {
                "boundary_role": "promax_review_boundary_not_atomic_v8_j_tuple",
                "reviewed_option_id": ranking[0],
                "decision_actor_ref": "ACTOR-1",
                "authorization_source_ref": "AUTH-1",
                "jurisdiction_ref": "J-UNRESOLVED-1",
                "scope": "analysis_only",
                "valid_from": "2026-07-23T00:00:00+00:00",
                "valid_until": "2026-07-24T00:00:00+00:00",
                "authorization_status": "not_authorized",
            },
            "procedure_states": {
                "O1": "complete",
                "O2": "complete",
                "O3": "in_review",
                "O4": "not_started",
            },
            "least_harm": {
                **base_review,
                "principle_id": "NSP-LEAST-HARM",
            },
            "proportionality": {
                **base_review,
                "principle_id": "NSP-PROPORTIONALITY",
            },
            "declared_low_information_house_policy_eligibility": {
                "case_specific_facts_present": False,
                "choice_changing_retrieval_evidence_present": False,
                "basis": "No case facts or choice-changing retrieval evidence.",
            },
            "ranking_support": [],
        }
        recommendation = {
            "options": options,
            "evaluation_dimensions": evaluation_dimensions,
            "ranking": ranking,
            "ranking_policy": "promax_low_information_house_policy_not_v8",
            "ranking_evidence_refs": [],
            "selection_review_wrapper": selection_review_wrapper,
            "option_kind_ranking": option_kinds,
            "option_record_hashes": option_record_hashes,
            "option_semantic_ranking": option_semantic_ranking,
            "preferred_option_id": ranking[0],
            "no_action_option_id": ranking[-1],
            "locked_at": "2026-07-23T01:00:00+00:00",
        }
        run_contract = {
            "request_sha256": "a" * 64,
            "source_snapshot_sha256": "b" * 64,
        }
        local_world = {"facts": [], "unknowns": ["no case-specific evidence"]}
        retrieval = {"entries": [], "network_available": False}
        normative_selection_basis = _selection_review_semantics(
            recommendation,
            options=options,
            option_by_id={
                str(option["option_id"]): option for option in options
            },
            ranking=ranking,
            retrieval=retrieval,
        )
        evidence_basis_hash = self._hash_json(
            {
                "request_sha256": run_contract["request_sha256"],
                "local_world_model_sha256": self._hash_json(local_world),
                "retrieval_ledger_sha256": self._hash_json(retrieval),
                "source_snapshot_sha256": run_contract["source_snapshot_sha256"],
            }
        )
        pro_prompt = "Argue for the proposition without changing evidence."
        anti_prompt = "Argue against the proposition without changing evidence."
        red_team = {
            "central_claim_id": "CLAIM-CENTRAL",
            "stability_checks": [
                {
                    "pro_prompt": pro_prompt,
                    "anti_prompt": anti_prompt,
                    "pro_prompt_sha256": self._hash_json(pro_prompt),
                    "anti_prompt_sha256": self._hash_json(anti_prompt),
                    "evidence_basis_sha256_before": evidence_basis_hash,
                    "evidence_basis_sha256_after": evidence_basis_hash,
                    "semantic_problem_sha256_before": semantic_key,
                    "semantic_problem_sha256_after": semantic_key,
                    "central_position_id_before": "CLAIM-CENTRAL",
                    "central_position_id_after": "CLAIM-CENTRAL",
                    "central_statement_sha256_before": self._hash_json(statement),
                    "central_statement_sha256_after": self._hash_json(statement),
                    "relation_to_proposition_before": "supports",
                    "relation_to_proposition_after": "supports",
                    "judgment_strength_before": "moderate",
                    "judgment_strength_after": "moderate",
                    "option_ranking_before": ranking,
                    "option_ranking_after": ranking,
                    "option_kind_ranking_before": option_kinds,
                    "option_kind_ranking_after": option_kinds,
                    "option_semantic_ranking_before": option_semantic_ranking,
                    "option_semantic_ranking_after": option_semantic_ranking,
                    "normative_selection_basis_sha256_before": normative_selection_basis,
                    "normative_selection_basis_sha256_after": normative_selection_basis,
                    "position_drift": "none",
                }
            ],
        }
        documents = {
            "promax-claim-path-graph.json": graph,
            "promax-position.locked.json": position,
            "promax-recommendation.locked.json": recommendation,
            "promax-red-team-report.json": red_team,
            "promax-run-contract.json": run_contract,
            "promax-local-world-model.locked.json": local_world,
            "promax-retrieval-ledger.json": retrieval,
        }
        for filename, document in documents.items():
            (artifact_dir / filename).write_text(
                json.dumps(document, ensure_ascii=False),
                encoding="utf-8",
            )
        return {
            "semantic_key_sha256": semantic_key,
            "central_statement_sha256": self._hash_json(statement),
            "option_semantic_ranking": option_semantic_ranking,
            "evidence_basis_sha256": evidence_basis_hash,
            "red_team": red_team,
            "recommendation": recommendation,
        }

    def test_recomputes_semantics_from_the_four_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)

            actual = load_artifact_semantics(artifact_dir)

        self.assertEqual(
            actual["semantic_key_sha256"], expected["semantic_key_sha256"]
        )
        self.assertEqual(
            actual["central_statement_sha256"],
            expected["central_statement_sha256"],
        )
        self.assertEqual(
            actual["option_semantic_ranking"],
            expected["option_semantic_ranking"],
        )
        self.assertEqual(actual["relation_to_proposition"], "supports")
        self.assertEqual(actual["judgment_strength"], "moderate")

    def test_rejects_red_team_semantics_that_only_claim_to_be_stable(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            red_team = expected["red_team"]
            red_team["stability_checks"][0]["option_semantic_ranking_after"][0] = (
                "0" * 64
            )
            (artifact_dir / "promax-red-team-report.json").write_text(
                json.dumps(red_team, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "option semantic ranking"):
                load_artifact_semantics(artifact_dir)

    def test_rejects_equal_evidence_hashes_not_bound_to_evidence_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            red_team = expected["red_team"]
            red_team["stability_checks"][0]["evidence_basis_sha256_before"] = (
                "0" * 64
            )
            red_team["stability_checks"][0]["evidence_basis_sha256_after"] = (
                "0" * 64
            )
            (artifact_dir / "promax-red-team-report.json").write_text(
                json.dumps(red_team, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "actual evidence artifacts"):
                load_artifact_semantics(artifact_dir)

    def test_rejects_inverted_jurisdiction_validity(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            boundary = recommendation["selection_review_wrapper"][
                "jurisdiction_review_boundary"
            ]
            boundary["valid_from"], boundary["valid_until"] = (
                boundary["valid_until"],
                boundary["valid_from"],
            )
            (artifact_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "validity"):
                load_artifact_semantics(artifact_dir)

    def test_rejects_late_or_unbound_principle_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            least_harm = recommendation["selection_review_wrapper"]["least_harm"]
            least_harm["reviewed_at"] = "2026-07-23T02:00:00+00:00"
            (artifact_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "postdate"):
                load_artifact_semantics(artifact_dir)

            least_harm["reviewed_at"] = "2026-07-23T00:00:00+00:00"
            least_harm["evidence_refs"] = ["GHOST-EVIDENCE"]
            (artifact_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "outside ranking_evidence_refs"):
                load_artifact_semantics(artifact_dir)

    def test_rejects_non_text_normative_references(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            recommendation["options"][0]["normative_premise_refs"].append(2)
            with self.assertRaisesRegex(ValueError, "non-empty text"):
                _selection_review_semantics(
                    recommendation,
                    options=recommendation["options"],
                    option_by_id={
                        str(option["option_id"]): option
                        for option in recommendation["options"]
                    },
                    ranking=recommendation["ranking"],
                    retrieval={"entries": []},
                )

    def test_normative_basis_matches_production_text_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            recommendation["evaluation_dimensions"] = [
                f"  {dimension}  "
                for dimension in recommendation["evaluation_dimensions"]
            ]
            for review_name in ("least_harm", "proportionality"):
                recommendation["selection_review_wrapper"][review_name][
                    "evaluation_dimensions"
                ] = [*recommendation["evaluation_dimensions"]]

            options = recommendation["options"]
            independent = _selection_review_semantics(
                recommendation,
                options=options,
                option_by_id={
                    str(option["option_id"]): option for option in options
                },
                ranking=recommendation["ranking"],
                retrieval={"entries": []},
            )
            production = production_selection_review_basis_sha256(recommendation)

        self.assertEqual(independent, production)

    def test_rejects_noncanonical_fields_in_an_exact_v8_option_record(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            recommendation["options"][0]["semantic_sha256"] = self._hash_json(
                recommendation["options"][0]
            )
            (artifact_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "exact v8 option fields"):
                load_artifact_semantics(artifact_dir)

    def test_rejects_a_stale_full_option_record_hash(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            recommendation["option_record_hashes"][0]["record_sha256"] = "0" * 64
            (artifact_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "full option record hash"):
                load_artifact_semantics(artifact_dir)

    def test_rejects_a_no_action_pointer_to_another_option_kind(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            artifact_dir = Path(raw_dir)
            expected = self._write_bundle(artifact_dir)
            recommendation = expected["recommendation"]
            recommendation["no_action_option_id"] = recommendation["ranking"][0]
            (artifact_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "no_action option pointer"):
                load_artifact_semantics(artifact_dir)

    def test_option_semantic_hashes_exclude_run_local_option_ids(self) -> None:
        with (
            tempfile.TemporaryDirectory() as first_raw,
            tempfile.TemporaryDirectory() as second_raw,
        ):
            first_dir = Path(first_raw)
            second_dir = Path(second_raw)
            self._write_bundle(first_dir)
            second = self._write_bundle(second_dir)
            recommendation = second["recommendation"]
            red_team = second["red_team"]
            old_ids = list(recommendation["ranking"])
            id_map = {
                old_id: f"OPTION-SECOND-RUN-{index}"
                for index, old_id in enumerate(old_ids, start=1)
            }
            for option in recommendation["options"]:
                option["option_id"] = id_map[option["option_id"]]
            recommendation["ranking"] = [id_map[option_id] for option_id in old_ids]
            recommendation["option_record_hashes"] = [
                {
                    "option_id": option["option_id"],
                    "record_sha256": self._hash_json(option),
                }
                for option in recommendation["options"]
            ]
            recommendation["no_action_option_id"] = id_map[
                recommendation["no_action_option_id"]
            ]
            recommendation["preferred_option_id"] = id_map[
                recommendation["preferred_option_id"]
            ]
            wrapper = recommendation["selection_review_wrapper"]
            wrapper["jurisdiction_review_boundary"]["reviewed_option_id"] = (
                recommendation["preferred_option_id"]
            )
            for review_name in ("least_harm", "proportionality"):
                review = wrapper[review_name]
                review["selected_option_id"] = id_map[
                    review["selected_option_id"]
                ]
                review["compared_option_ids"] = [
                    id_map[option_id] for option_id in review["compared_option_ids"]
                ]
            stability = red_team["stability_checks"][0]
            stability["option_ranking_before"] = recommendation["ranking"]
            stability["option_ranking_after"] = recommendation["ranking"]
            (second_dir / "promax-recommendation.locked.json").write_text(
                json.dumps(recommendation, ensure_ascii=False),
                encoding="utf-8",
            )
            (second_dir / "promax-red-team-report.json").write_text(
                json.dumps(red_team, ensure_ascii=False),
                encoding="utf-8",
            )

            first_semantics = load_artifact_semantics(first_dir)
            second_semantics = load_artifact_semantics(second_dir)

        self.assertNotEqual(
            first_semantics["option_ranking"],
            second_semantics["option_ranking"],
        )
        self.assertEqual(
            first_semantics["option_semantic_ranking"],
            second_semantics["option_semantic_ranking"],
        )
        self.assertEqual(
            first_semantics["normative_selection_basis_sha256"],
            second_semantics["normative_selection_basis_sha256"],
        )

    def test_rejects_an_artifact_directory_outside_the_allowed_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_raw:
            workspace = Path(workspace_raw)
            allowed_root = workspace / "allowed"
            outside = workspace / "outside"
            allowed_root.mkdir()
            outside.mkdir()
            self._write_bundle(outside)

            with self.assertRaisesRegex(ValueError, "escapes"):
                load_artifact_semantics(outside, allowed_root=allowed_root)


class ProMaxGreenEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        cls.results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    def test_rubric_has_fixed_models_scenarios_matrix_and_metrics(self) -> None:
        self.assertEqual(self.rubric["schema_id"], "crossframe.promax.green-rubric")
        self.assertEqual(self.rubric["schema_version"], 1)
        self.assertEqual(
            self.rubric["models"], ["gpt-5.6-sol", "gpt-5.6-terra"]
        )
        self.assertEqual(len(self.rubric["scenario_ids"]), 12)
        self.assertEqual(
            self.rubric["run_matrix"],
            [
                {"model_id": "gpt-5.6-sol", "scenario_id": "A1"},
                {"model_id": "gpt-5.6-sol", "scenario_id": "A2"},
                {"model_id": "gpt-5.6-terra", "scenario_id": "A1"},
            ],
        )
        metric_ids = [metric["metric_id"] for metric in self.rubric["metrics"]]
        self.assertEqual(len(metric_ids), len(set(metric_ids)))
        self.assertEqual(
            set(metric_ids),
            {
                "v8_anchor_validity",
                "promax_old_version_contamination",
                "canonical_concept_terminal_coverage",
                "central_claim_traceability",
                "conditional_response_under_missing_evidence",
                "explicit_position_when_requested",
                "strongest_countercase_coverage",
                "authorization_leakage",
                "honest_tool_failure_downgrade",
                "exact_promax_routing",
                "typed_example_integrity",
            },
        )
        for metric in self.rubric["metrics"]:
            self.assertIn(metric["direction"], {"minimum", "maximum"})
            self.assertIsInstance(metric["threshold"], (int, float))
            self.assertTrue(metric["pass_rule"].strip())

    def test_every_model_scenario_run_is_fresh_and_hash_bound(self) -> None:
        self.assertEqual(self.results["schema_id"], "crossframe.promax.green-results")
        self.assertEqual(self.results["schema_version"], 1)
        expected_pairs = {
            (entry["model_id"], entry["scenario_id"])
            for entry in self.rubric["run_matrix"]
        }
        runs = self.results["runs"]
        actual_pairs = {(run["model_id"], run["scenario_id"]) for run in runs}
        self.assertEqual(actual_pairs, expected_pairs)
        self.assertEqual(len(runs), len(expected_pairs))
        self.assertEqual(len({run["run_id"] for run in runs}), len(runs))

        tree_hash = evaluated_skill_tree_sha256()
        self.assertEqual(self.results["skill_tree_sha256"], tree_hash)
        for run in runs:
            with self.subTest(model=run["model_id"], scenario=run["scenario_id"]):
                self.assertIs(run["fresh_context"], True)
                self.assertIs(run["skill_loaded"], True)
                self.assertEqual(run["skill_tree_sha256"], tree_hash)
                prompt = run["executed_prompt"].encode("utf-8")
                self.assertEqual(run["prompt_sha256"], sha256_bytes(prompt))
                self.assertIsInstance(run["tool_availability"], dict)
                self.assertTrue(run["tool_availability"])
                raw_path = ROOT / run["raw_output_path"]
                self.assertTrue(raw_path.is_file(), raw_path.as_posix())
                self.assertEqual(run["raw_output_sha256"], sha256_bytes(raw_path.read_bytes()))
                self.assertTrue(run["artifact_dir"].strip())

    def test_historical_model_evidence_is_not_relabelled_as_the_current_tree(
        self,
    ) -> None:
        record = evaluated_skill_tree_record()
        self.assertEqual(
            record["schema_id"],
            "crossframe.promax.green-evaluated-skill-tree",
        )
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(
            record["evaluated_skill_tree_sha256"],
            self.results["skill_tree_sha256"],
        )
        self.assertNotEqual(
            record["evaluated_skill_tree_sha256"],
            canonical_skill_tree_sha256(),
        )
        compatibility = record["current_release_compatibility"]
        self.assertEqual(
            compatibility["scope"],
            "activation-boundary-only",
        )
        self.assertEqual(
            set(compatibility["deterministic_tests"]),
            {
                (
                    "tests.test_promax_behavioral_contract."
                    "ProMaxTargetBehaviorContractTests."
                    "test_loaded_skill_does_not_repeat_the_activation_gate"
                ),
                (
                    "tests.test_promax_runtime_contract."
                    "ProMaxRunInitializationTests."
                    "test_platform_selected_runtime_does_not_reparse_the_request_for_activation"
                ),
                (
                    "tests.test_promax_runtime_contract."
                    "ProMaxRuntimeCLITests."
                    "test_cli_has_no_activation_subcommand_and_root_entrypoint_is_thin"
                ),
                (
                    "tests.test_promax_repository_integration."
                    "ProMaxRepositoryTargetTests."
                    "test_promax_runtime_does_not_reimplement_suite_activation"
                ),
            },
        )

    def test_per_run_metric_records_are_complete_and_auditable(self) -> None:
        rubric_metrics = {
            metric["metric_id"]: metric for metric in self.rubric["metrics"]
        }
        metric_ids = set(rubric_metrics)
        for run in self.results["runs"]:
            records = run["metrics"]
            self.assertEqual(set(records), metric_ids)
            for metric_id, record in records.items():
                with self.subTest(
                    model=run["model_id"],
                    scenario=run["scenario_id"],
                    metric=metric_id,
                ):
                    self.assertIs(type(record["applicable"]), bool)
                    self.assertIs(type(record["passed"]), bool)
                    self.assertIn(record["numerator"], {0, 1})
                    self.assertIn(record["denominator"], {0, 1})
                    self.assertEqual(record["denominator"], int(record["applicable"]))
                    rubric = rubric_metrics[metric_id]
                    self.assertEqual(record["direction"], rubric["direction"])
                    self.assertEqual(record["threshold"], rubric["threshold"])
                    if not record["applicable"]:
                        self.assertEqual(record["numerator"], 0)
                        self.assertIs(record["passed"], True)
                    else:
                        self.assertEqual(
                            record["passed"],
                            metric_passes(
                                rubric["direction"],
                                record["numerator"],
                                record["denominator"],
                                rubric["threshold"],
                            ),
                        )
                    self.assertIsInstance(record["evidence"], list)
                    self.assertTrue(record["evidence"])
                    self.assertIsInstance(record["failing_artifacts"], list)
                    if record["passed"]:
                        self.assertEqual(record["failing_artifacts"], [])
                    else:
                        self.assertTrue(record["failing_artifacts"])

    def test_aggregate_thresholds_record_unexercised_metrics_and_paired_stability(
        self,
    ) -> None:
        rubric_metrics = {
            metric["metric_id"]: metric for metric in self.rubric["metrics"]
        }
        aggregate = self.results["aggregate"]
        self.assertEqual(set(aggregate["metrics"]), set(rubric_metrics))
        declared_scenarios = {
            entry["scenario_id"] for entry in self.rubric["run_matrix"]
        }
        expected_unexercised = {
            metric_id
            for metric_id, rubric in rubric_metrics.items()
            if rubric["applicable_scenarios"] != "all"
            and not declared_scenarios.intersection(
                rubric["applicable_scenarios"]
            )
        }
        self.assertEqual(
            set(aggregate["unexercised_metric_ids"]),
            expected_unexercised,
        )
        for metric_id, result in aggregate["metrics"].items():
            with self.subTest(metric=metric_id):
                run_records = [
                    run["metrics"][metric_id] for run in self.results["runs"]
                ]
                denominator = sum(record["denominator"] for record in run_records)
                numerator = sum(record["numerator"] for record in run_records)
                self.assertEqual(result["denominator"], denominator)
                self.assertEqual(result["numerator"], numerator)
                self.assertGreaterEqual(numerator, 0)
                self.assertLessEqual(numerator, denominator)
                rubric = rubric_metrics[metric_id]
                self.assertEqual(result["threshold"], rubric["threshold"])
                self.assertEqual(result["direction"], rubric["direction"])
                if denominator == 0:
                    self.assertIn(metric_id, expected_unexercised)
                    self.assertEqual(result["rate"], None)
                    self.assertEqual(result["status"], "not_exercised")
                    self.assertIs(result["threshold_covered"], False)
                    self.assertIs(result["passed"], False)
                else:
                    self.assertNotIn(metric_id, expected_unexercised)
                    rate = numerator / denominator
                    self.assertEqual(result["rate"], rate)
                    self.assertEqual(result["status"], "passed")
                    self.assertIs(result["threshold_covered"], True)
                    self.assertIs(result["passed"], True)
                    if rubric["direction"] == "minimum":
                        self.assertGreaterEqual(rate, rubric["threshold"])
                    else:
                        self.assertLessEqual(rate, rubric["threshold"])

        stability = aggregate["paired_stability"]
        self.assertEqual(
            {record["model_id"] for record in stability},
            set(self.rubric["paired_stability"]["required_model_ids"]),
        )
        run_by_pair = {
            (run["model_id"], run["scenario_id"]): run
            for run in self.results["runs"]
        }
        record_by_model = {record["model_id"]: record for record in stability}
        paired_rubric = self.rubric["paired_stability"]
        frozen_context = paired_rubric["frozen_pair_context"]
        frozen_context_sha256 = sha256_json(frozen_context)
        self.assertEqual(
            paired_rubric["frozen_pair_context_sha256"],
            frozen_context_sha256,
        )
        self.assertEqual(frozen_context["factual_material"], [])

        for model_id in paired_rubric["required_model_ids"]:
            with self.subTest(model=model_id):
                first_run = run_by_pair[(model_id, "A1")]
                second_run = run_by_pair[(model_id, "A2")]
                pair_semantics = []
                for run in (first_run, second_run):
                    artifact_dir = Path(run["artifact_dir"])
                    if not artifact_dir.is_absolute():
                        artifact_dir = ROOT / artifact_dir
                    semantics = load_artifact_semantics(
                        artifact_dir,
                        allowed_root=ARTIFACT_WORKSPACE,
                    )
                    pair_semantics.append(semantics)
                    for field in (
                        "analysis_object",
                        "time_window",
                        "evidence_cutoff",
                    ):
                        self.assertEqual(
                            semantics[field],
                            frozen_context[field],
                            f"{model_id}/{run['scenario_id']} changed frozen {field}",
                        )

                first, second = pair_semantics
                equalities = {
                    field: first[field] == second[field]
                    for field in paired_rubric["required_equal_fields"]
                }
                for field, equal in equalities.items():
                    self.assertIs(
                        equal,
                        True,
                        f"{model_id} A1/A2 changed recomputed {field}",
                    )
                judgment_strength_drift = int(
                    first["judgment_strength"] != second["judgment_strength"]
                )
                self.assertEqual(
                    judgment_strength_drift,
                    paired_rubric["required_judgment_strength_drift"],
                )

                recomputed_record = {
                    "model_id": model_id,
                    "scenario_pair": ["A1", "A2"],
                    "frozen_pair_context_sha256": frozen_context_sha256,
                    "semantic_key_sha256_equal": equalities[
                        "semantic_key_sha256"
                    ],
                    "relation_to_proposition_equal": equalities[
                        "relation_to_proposition"
                    ],
                    "judgment_strength_equal": equalities["judgment_strength"],
                    "option_kind_ranking_equal": equalities[
                        "option_kind_ranking"
                    ],
                    "option_semantic_ranking_equal": equalities[
                        "option_semantic_ranking"
                    ],
                    "normative_selection_basis_sha256_equal": equalities[
                        "normative_selection_basis_sha256"
                    ],
                    "judgment_strength_drift": judgment_strength_drift,
                    "passed": all(equalities.values())
                    and judgment_strength_drift
                    == paired_rubric["required_judgment_strength_drift"],
                }
                self.assertEqual(record_by_model[model_id], recomputed_record)
                self.assertIs(recomputed_record["passed"], True)
        self.assertIs(
            aggregate["all_thresholds_passed"],
            not expected_unexercised,
        )
        self.assertIs(aggregate["all_exercised_thresholds_passed"], True)
        self.assertIs(aggregate["deterministic_regression_suite_passed"], True)


if __name__ == "__main__":
    unittest.main()
