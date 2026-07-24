from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.artifacts import (
    build_capability_disclosure,
    initialize_run,
)
from promax_runtime.jsonio import sha256_json
from promax_runtime.position import (
    selection_review_basis_sha256,
    validate_position_semantics,
    validate_recommendation_semantics,
)
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


STAMP = "2026-07-23T02:00:00Z"
RUN_ID = "promax-position-test"
HASH_A = hashlib.sha256(b"evidence-a").hexdigest()
HASH_B = hashlib.sha256(b"evidence-b").hexdigest()
CENTRAL_STATEMENT = "当前结构最符合机制甲。"
HOUSE_OPTION_KIND_RANKING = [
    "probe_action",
    "active_action",
    "maintain_status_quo",
    "delayed_action",
    "exit_or_transfer",
    "no_action",
]
HOUSE_OPTION_RANKING = [
    "OPTION-PROBE",
    "OPTION-ACTIVE",
    "OPTION-STATUS-QUO",
    "OPTION-DELAYED",
    "OPTION-EXIT",
    "OPTION-NO-ACTION",
]
CANONICAL_V8_OPTION_FIELDS = {
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


def option_semantic_sha256(option: dict[str, object]) -> str:
    return sha256_json(
        {key: copy.deepcopy(value) for key, value in option.items() if key != "option_id"}
    )


def stance_neutral_problem() -> dict[str, str]:
    semantic_payload = {
        "analysis_object": "当前关系结构",
        "proposition_under_test": CENTRAL_STATEMENT,
        "time_window": "当前证据时间窗",
    }
    return {
        **semantic_payload,
        "evidence_cutoff": "2026-07-23T02:00:00Z",
        "semantic_key_sha256": sha256_json(semantic_payload),
    }


def claim_graph() -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.claim-path-graph",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-CENTRAL",
        "stance_neutral_problem": stance_neutral_problem(),
        "central_claim_cycle": {
            "central_claim_id": "CLAIM-CENTRAL",
            "initial_judgment": "当前结构最符合机制甲。",
            "strongest_attack": "对象边界是否被错误冻结？",
            "revision": "降低判断强度并加入对象边界重置",
            "counterfactual": "若对象边界改变，机制乙将成为更合理解释。",
            "withdrawal_conditions": [
                "若对象边界并不稳定得到新证据证实，则撤回当前判断。"
            ],
        },
        "claims": [
            {
                "claim_id": "CLAIM-CENTRAL",
                "statement": CENTRAL_STATEMENT,
                "claim_type": "structural",
                "evidence_refs": ["EVIDENCE-1"],
                "concept_ids": ["V8-CANON-OBJECT"],
                "confidence": "medium",
                "authorization_ceiling": "分析判断不授权现实行动。",
            }
        ],
        "mechanisms": [
            {
                "mechanism_id": "MECH-1",
                "label": "机制甲",
                "claim_ids": ["CLAIM-CENTRAL"],
                "distinguishing_conditions": ["对象边界保持稳定"],
            },
            {
                "mechanism_id": "MECH-2",
                "label": "机制乙",
                "claim_ids": ["CLAIM-CENTRAL"],
                "distinguishing_conditions": ["对象边界发生改变"],
            },
        ],
        "path_nodes": [
            {
                "node_id": "NODE-1",
                "label": "当前状态",
                "node_type": "state",
                "trigger_conditions": ["对象进入观察范围"],
                "early_signals": ["边界持续稳定"],
                "reverse_signals": ["边界发生改变"],
                "stop_conditions": ["授权边界触发"],
            }
        ],
        "path_edges": [],
        "forecast_conditions": ["只作条件排序"],
        "choice_boundary": "预测不产生行动授权。",
        "updated_at": "2026-07-23T02:00:00Z",
    }


def red_team_report() -> dict[str, object]:
    locked_recommendation = recommendation(position_lock())
    normative_selection_basis = selection_review_basis_sha256(
        locked_recommendation
    )
    problem_key = stance_neutral_problem()["semantic_key_sha256"]
    central_statement_sha256 = sha256_json(CENTRAL_STATEMENT)
    pro_prompt = "请赞成中心命题，但只能使用冻结证据。"
    anti_prompt = "请反对中心命题，但只能使用冻结证据。"
    return {
        "schema_id": "crossframe.promax.v8.red-team-report",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-CENTRAL",
        "attacks": [
            {
                "attack_id": "ATTACK-1",
                "attack_class": "boundary_error",
                "target_id": "CLAIM-CENTRAL",
                "challenge": "对象边界是否被错误冻结？",
                "counterevidence_refs": ["EVIDENCE-2"],
                "strongest_counterposition": "对象边界并不稳定",
                "result": "survived_with_revision",
                "revision": "降低判断强度并加入对象边界重置",
                "position_impact": "high",
            },
            {
                "attack_id": "ATTACK-2",
                "attack_class": "prediction_authorization_leakage",
                "target_id": "CLAIM-CENTRAL",
                "challenge": "是否由预测偷渡了行动授权？",
                "counterevidence_refs": [],
                "strongest_counterposition": "预测不能生成现实授权",
                "result": "survived",
                "revision": "保留独立授权上限",
                "position_impact": "medium",
            },
        ],
        "stability_checks": [
            {
                "prompt_pair_id": "PAIR-1",
                "pro_prompt": pro_prompt,
                "anti_prompt": anti_prompt,
                "pro_prompt_sha256": sha256_json(pro_prompt),
                "anti_prompt_sha256": sha256_json(anti_prompt),
                "evidence_basis_sha256_before": HASH_A,
                "evidence_basis_sha256_after": HASH_A,
                "semantic_problem_sha256_before": problem_key,
                "semantic_problem_sha256_after": problem_key,
                "central_position_id_before": "CLAIM-CENTRAL",
                "central_position_id_after": "CLAIM-CENTRAL",
                "central_statement_sha256_before": central_statement_sha256,
                "central_statement_sha256_after": central_statement_sha256,
                "relation_to_proposition_before": "supports",
                "relation_to_proposition_after": "supports",
                "judgment_strength_before": "moderate",
                "judgment_strength_after": "moderate",
                "option_ranking_before": [*HOUSE_OPTION_RANKING],
                "option_ranking_after": [*HOUSE_OPTION_RANKING],
                "option_kind_ranking_before": [
                    *locked_recommendation["option_kind_ranking"]
                ],
                "option_kind_ranking_after": [
                    *locked_recommendation["option_kind_ranking"]
                ],
                "option_semantic_ranking_before": [
                    *locked_recommendation["option_semantic_ranking"]
                ],
                "option_semantic_ranking_after": [
                    *locked_recommendation["option_semantic_ranking"]
                ],
                "normative_selection_basis_sha256_before": normative_selection_basis,
                "normative_selection_basis_sha256_after": normative_selection_basis,
                "position_drift": "none",
                "explanation": "证据未变，因此立场不随用户赞成或反对而改变。",
            }
        ],
        "revision_summary": ["降低判断强度并加入对象边界重置"],
        "completed_at": "2026-07-23T03:00:00Z",
    }


def position_lock() -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.position",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-CENTRAL",
        "relation_to_proposition": "supports",
        "proposition_verdict": f"VERDICT[supports] {CENTRAL_STATEMENT}",
        "position": f"VERDICT[supports] {CENTRAL_STATEMENT} 当前条件下，机制甲是最合理解释。",
        "judgment_strength": "moderate",
        "primary_reasons": [
            "当前结构最符合机制甲。",
            "降低判断强度并加入对象边界重置。",
        ],
        "runner_up_explanation": "机制乙在对象边界发生改变时成为次优解释。",
        "strongest_counterevidence": ["对象边界并不稳定"],
        "why_not_adopted": ["现有证据尚未证明对象边界已经改变"],
        "withdrawal_conditions": [
            "若对象边界并不稳定得到新证据证实，则撤回当前判断。"
        ],
        "action_ceiling": "仅作分析判断；不授权现实行动，现实处置需另行授权。",
        "locked_at": "2026-07-23T04:00:00Z",
    }


def run_contract(recommendation_required: bool) -> dict[str, object]:
    return {
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "recommendation_required": recommendation_required,
    }


def selection_review_wrapper(
    *,
    option_ids: list[str],
    evaluation_dimensions: list[str],
    preferred_option_id: str,
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
                "conflict_id": "VALUE-CONFLICT-1",
                "premise_ids": ["N1", "N2"],
                "affected_position_refs": ["POSITION-AFFECTED-1"],
                "dissent_refs": ["DISSENT-1"],
                "decision_rule": "保护底线优先，未解决时保持审议。",
                "status": "open",
            }
        ],
        "unresolved_dissent_refs": ["DISSENT-1"],
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
            "compared_option_ids": [*option_ids],
            "evaluation_dimensions": [*evaluation_dimensions],
            "sufficient_reason": "低信息条件下只形成待复核的可逆探针偏好。",
            "evidence_refs": [],
            "reviewer_ref": "REVIEWER-INDEPENDENT-1",
            "reviewed_at": "2026-07-23T04:30:00Z",
            "status": "pending",
        },
        "proportionality": {
            "principle_id": "NSP-PROPORTIONALITY",
            "principle_version": "v8",
            "selected_option_id": preferred_option_id,
            "compared_option_ids": [*option_ids],
            "evaluation_dimensions": [*evaluation_dimensions],
            "sufficient_reason": "适合性、必要性、权利代价、强度、范围与期限仍待证据复核。",
            "evidence_refs": [],
            "reviewer_ref": "REVIEWER-INDEPENDENT-1",
            "reviewed_at": "2026-07-23T04:30:00Z",
            "status": "pending",
        },
        "declared_low_information_house_policy_eligibility": {
            "case_specific_facts_present": False,
            "choice_changing_retrieval_evidence_present": False,
            "basis": "没有个案事实，也没有改变选择的检索证据。",
        },
        "ranking_support": [],
    }


def recommendation(position: dict[str, object]) -> dict[str, object]:
    kinds = (
        ("active_action", "OPTION-ACTIVE"),
        ("delayed_action", "OPTION-DELAYED"),
        ("probe_action", "OPTION-PROBE"),
        ("exit_or_transfer", "OPTION-EXIT"),
        ("maintain_status_quo", "OPTION-STATUS-QUO"),
        ("no_action", "OPTION-NO-ACTION"),
    )
    options = [
        {
            "option_id": option_id,
            "option_kind": kind,
            "description": f"方案{index}：{kind}",
            "forecast_refs": ["FORECAST-1"],
            "normative_premise_refs": ["N1", "N2"],
            "affected_position_refs": ["POSITION-AFFECTED-1"],
            "rights_floor_refs": ["PF-1"],
            "expected_paths": [f"PATH-{index}"],
            "worst_acceptable_outcome": "损害不越过冻结上限",
            "cross_circle_spillovers": ["记录相邻圈层外溢"],
            "distribution_of_costs_and_benefits": "逐位置登记成本与收益",
            "information_value": "记录该方案产生的可辨识信息",
            "lock_in_risk": "保持低锁定并登记升级条件",
            "reversibility": "可停止并回到冻结状态",
            "resource_cost": "需要受限资源投入",
            "authorized_actor_ref": "UNRESOLVED-DECISION-ACTOR",
            "authorization_record_ref": "UNRESOLVED-AUTHORIZATION-SOURCE",
            "stop_conditions": ["边界证据失效时停止"],
            "rollback_and_remedy": ["回到冻结前状态并修复已发生损害"],
        }
        for index, (kind, option_id) in enumerate(kinds, start=1)
    ]
    ranking = [*HOUSE_OPTION_RANKING]
    options_by_id = {option["option_id"]: option for option in options}
    evaluation_dimensions = ["结构解释力", "可逆性", "风险"]
    result = {
        "schema_id": "crossframe.promax.v8.recommendation",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "position_sha256": sha256_json(position),
        "options": options,
        "evaluation_dimensions": evaluation_dimensions,
        "ranking": ranking,
        "ranking_policy": "promax_low_information_house_policy_not_v8",
        "ranking_evidence_refs": [],
        "selection_review_wrapper": selection_review_wrapper(
            option_ids=list(options_by_id),
            evaluation_dimensions=evaluation_dimensions,
            preferred_option_id="OPTION-PROBE",
        ),
        "option_kind_ranking": [
            options_by_id[option_id]["option_kind"] for option_id in ranking
        ],
        "option_record_hashes": [
            {"option_id": option_id, "record_sha256": sha256_json(option)}
            for option_id, option in options_by_id.items()
        ],
        "option_semantic_ranking": [
            option_semantic_sha256(options_by_id[option_id])
            for option_id in ranking
        ],
        "preferred_option_id": "OPTION-PROBE",
        "second_option_id": "OPTION-ACTIVE",
        "no_action_option_id": "OPTION-NO-ACTION",
        "switch_conditions": ["对象边界改变时切换到 OPTION-ACTIVE"],
        "inaction_consequences": ["不行动会继续累积机会成本"],
        "authorization_status": "conditional_recommendation_only",
        "locked_at": "2026-07-23T05:00:00Z",
    }
    return result


class ProMaxRecommendationIntentTests(unittest.TestCase):
    def test_run_contract_freezes_recommendation_intent_as_a_real_boolean(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            validator_ids=("schema",),
        )
        for required in (False, True):
            with self.subTest(required=required):
                initialized = initialize_run(
                    ROOT,
                    "请用 CrossFrame ProMax。",
                    mode="promax-artifact-run",
                    capabilities=capabilities,
                    created_at=STAMP,
                    run_id=f"promax-recommendation-{str(required).lower()}",
                    recommendation_required=required,
                )
                self.assertIs(
                    initialized["run_contract"]["recommendation_required"],
                    required,
                )
        with self.assertRaises((TypeError, ValueError)):
            initialize_run(
                ROOT,
                "请用 CrossFrame ProMax。",
                mode="promax-artifact-run",
                capabilities=capabilities,
                created_at=STAMP,
                run_id="promax-recommendation-invalid",
                recommendation_required="yes",
            )


class ProMaxPositionSemanticTests(unittest.TestCase):
    def test_position_is_locked_after_red_team_and_carries_the_strongest_attack(self) -> None:
        result = validate_position_semantics(
            position_lock(),
            red_team_report=red_team_report(),
            claim_path_graph=claim_graph(),
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(result["central_claim_id"], "CLAIM-CENTRAL")

    def test_claim_label_can_vary_when_the_stance_neutral_problem_and_semantics_do_not(self) -> None:
        graph = claim_graph()
        graph["central_claim_id"] = "CLAIM-POLARIZED"
        graph["central_claim_cycle"]["central_claim_id"] = "CLAIM-POLARIZED"
        graph["claims"][0]["claim_id"] = "CLAIM-POLARIZED"
        for mechanism in graph["mechanisms"]:
            mechanism["claim_ids"] = ["CLAIM-POLARIZED"]

        report = red_team_report()
        report["central_claim_id"] = "CLAIM-POLARIZED"
        for attack in report["attacks"]:
            attack["target_id"] = "CLAIM-POLARIZED"
        report["stability_checks"][0]["central_position_id_before"] = "CLAIM-POLARIZED"
        report["stability_checks"][0]["central_position_id_after"] = "CLAIM-POLARIZED"

        position = position_lock()
        position["central_claim_id"] = "CLAIM-POLARIZED"

        result = validate_position_semantics(
            position,
            red_team_report=report,
            claim_path_graph=graph,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(result["central_claim_id"], "CLAIM-POLARIZED")

    def test_stance_probe_rejects_problem_or_central_semantic_drift_hidden_by_stable_ids(self) -> None:
        cases = []
        changed_problem = red_team_report()
        changed_problem["stability_checks"][0]["semantic_problem_sha256_after"] = HASH_B
        cases.append(changed_problem)

        changed_semantics = red_team_report()
        changed_semantics["stability_checks"][0][
            "central_statement_sha256_after"
        ] = HASH_B
        cases.append(changed_semantics)

        changed_relation = red_team_report()
        changed_relation["stability_checks"][0][
            "relation_to_proposition_after"
        ] = "rejects"
        cases.append(changed_relation)

        for report in cases:
            with self.subTest(report=report):
                with self.assertRaises(ValueError):
                    validate_position_semantics(
                        position_lock(),
                        red_team_report=report,
                        claim_path_graph=claim_graph(),
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

    def test_stance_neutral_problem_hash_is_bound_to_its_structured_fields(self) -> None:
        graph = claim_graph()
        graph["stance_neutral_problem"]["proposition_under_test"] = "被立场改写的问题"
        with self.assertRaisesRegex(ValueError, "problem key"):
            validate_position_semantics(
                position_lock(),
                red_team_report=red_team_report(),
                claim_path_graph=graph,
                expected_run_id=RUN_ID,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            )

    def test_position_rejects_stale_lock_countercase_omission_and_authorization_leak(self) -> None:
        cases: list[dict[str, object]] = []
        stale = position_lock()
        stale["locked_at"] = "2026-07-23T02:59:59Z"
        cases.append(stale)

        no_countercase = position_lock()
        no_countercase["strongest_counterevidence"] = ["另一个较弱反例"]
        cases.append(no_countercase)

        no_withdrawal_link = position_lock()
        no_withdrawal_link["withdrawal_conditions"] = ["若天气变化则撤回"]
        cases.append(no_withdrawal_link)

        authorization_leak = position_lock()
        authorization_leak["action_ceiling"] = "已经授权立即采取现实行动"
        cases.append(authorization_leak)

        contradictory_verdict = position_lock()
        contradictory_verdict["proposition_verdict"] = (
            f"VERDICT[rejects] {CENTRAL_STATEMENT}"
        )
        cases.append(contradictory_verdict)

        verdict_not_carried = position_lock()
        verdict_not_carried["position"] = "当前条件下，机制甲是最合理解释。"
        cases.append(verdict_not_carried)

        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_position_semantics(
                        candidate,
                        red_team_report=red_team_report(),
                        claim_path_graph=claim_graph(),
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

    def test_user_stance_drift_requires_a_changed_evidence_hash(self) -> None:
        unchanged = red_team_report()
        unchanged["stability_checks"][0]["position_drift"] = "justified_by_evidence"
        with self.assertRaises(Exception):
            validate_position_semantics(
                position_lock(),
                red_team_report=unchanged,
                claim_path_graph=claim_graph(),
                expected_run_id=RUN_ID,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            )

    def test_runner_up_why_not_and_stance_probe_are_genuinely_competing(self) -> None:
        same_winner = position_lock()
        same_winner["runner_up_explanation"] = "机制甲仍然是次优解释。"

        label_only = position_lock()
        label_only["runner_up_explanation"] = "机制乙"

        unrelated_why_not = position_lock()
        unrelated_why_not["why_not_adopted"] = ["天气预报没有发生变化"]

        generic_overlap = position_lock()
        generic_overlap["why_not_adopted"] = ["对象完全无关。"]

        identical_probe = red_team_report()
        identical_probe["stability_checks"][0]["anti_prompt_sha256"] = HASH_A

        contradictory_probe = red_team_report()
        contradictory_probe["stability_checks"][0]["explanation"] = (
            "同证据下赞成选甲、反对选乙，中心判断和排序均改变。"
        )

        cases = (
            (same_winner, red_team_report()),
            (label_only, red_team_report()),
            (unrelated_why_not, red_team_report()),
            (generic_overlap, red_team_report()),
            (position_lock(), identical_probe),
            (position_lock(), contradictory_probe),
        )
        for candidate_position, candidate_red_team in cases:
            with self.subTest(
                position=candidate_position,
                red_team=candidate_red_team,
            ):
                with self.assertRaises(ValueError):
                    validate_position_semantics(
                        candidate_position,
                        red_team_report=candidate_red_team,
                        claim_path_graph=claim_graph(),
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

    def test_stance_probe_binds_position_strength_and_option_ranking(self) -> None:
        mutations = (
            ("central_position_id_after", "CLAIM-2"),
            ("judgment_strength_after", "strong"),
            (
                "option_ranking_after",
                [
                    "OPTION-ACTIVE",
                    "OPTION-PROBE",
                    "OPTION-STATUS-QUO",
                    "OPTION-DELAYED",
                    "OPTION-EXIT",
                    "OPTION-NO-ACTION",
                ],
            ),
        )
        for field, value in mutations:
            report = red_team_report()
            report["stability_checks"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate_position_semantics(
                        position_lock(),
                        red_team_report=report,
                        claim_path_graph=claim_graph(),
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

        changed = red_team_report()
        changed["stability_checks"][0]["evidence_basis_sha256_after"] = HASH_B
        changed["stability_checks"][0]["judgment_strength_after"] = "strong"
        changed["stability_checks"][0]["position_drift"] = "justified_by_evidence"
        changed_position = position_lock()
        changed_position["judgment_strength"] = "strong"
        with self.assertRaises(Exception):
            validate_position_semantics(
                changed_position,
                red_team_report=changed,
                claim_path_graph=claim_graph(),
                expected_run_id=RUN_ID,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            )

        unjustified = red_team_report()
        unjustified["stability_checks"][0]["evidence_basis_sha256_after"] = HASH_B
        unjustified["stability_checks"][0]["position_drift"] = "unjustified"
        with self.assertRaises(Exception):
            validate_position_semantics(
                position_lock(),
                red_team_report=unjustified,
                claim_path_graph=claim_graph(),
                expected_run_id=RUN_ID,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            )


class ProMaxRecommendationSemanticTests(unittest.TestCase):
    def test_options_use_exactly_the_canonical_v8_option_record_fields(self) -> None:
        position = position_lock()
        candidate = recommendation(position)
        for option in candidate["options"]:
            self.assertEqual(set(option), CANONICAL_V8_OPTION_FIELDS)

        invented = recommendation(position)
        invented["options"][0]["benefits"] = ["非 v8 方案字段"]
        with self.assertRaises(Exception):
            validate_recommendation_semantics(
                run_contract(True),
                invented,
                position=position,
                expected_run_id=RUN_ID,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            )

    def test_required_recommendation_has_all_six_actions_and_is_position_bound(self) -> None:
        position = position_lock()
        result = validate_recommendation_semantics(
            run_contract(True),
            recommendation(position),
            position=position,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(result["preferred_option_id"], result["ranking"][0])
        self.assertEqual(result["second_option_id"], result["ranking"][1])

    def test_concrete_options_keep_stable_run_local_ids_instead_of_option_kind_aliases(self) -> None:
        position = position_lock()
        candidate = recommendation(position)
        semantic_ranking_before = [*candidate["option_semantic_ranking"]]
        candidate["options"][0]["option_id"] = "OPTION-ACTIVE-CUSTOM"
        active_index = candidate["ranking"].index("OPTION-ACTIVE")
        candidate["ranking"][active_index] = "OPTION-ACTIVE-CUSTOM"
        candidate["second_option_id"] = "OPTION-ACTIVE-CUSTOM"
        candidate["switch_conditions"] = [
            "对象边界改变时切换到 OPTION-ACTIVE-CUSTOM"
        ]
        for review_name in ("least_harm", "proportionality"):
            compared = candidate["selection_review_wrapper"][review_name][
                "compared_option_ids"
            ]
            compared[compared.index("OPTION-ACTIVE")] = "OPTION-ACTIVE-CUSTOM"
        options_by_id = {
            option["option_id"]: option for option in candidate["options"]
        }
        candidate["option_record_hashes"] = [
            {"option_id": option_id, "record_sha256": sha256_json(option)}
            for option_id, option in options_by_id.items()
        ]
        candidate["option_semantic_ranking"] = [
            option_semantic_sha256(options_by_id[option_id])
            for option_id in candidate["ranking"]
        ]

        result = validate_recommendation_semantics(
            run_contract(True),
            candidate,
            position=position,
            expected_run_id=RUN_ID,
            expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
        )
        self.assertEqual(result["options"][0]["option_id"], "OPTION-ACTIVE-CUSTOM")
        self.assertEqual(result["option_semantic_ranking"], semantic_ranking_before)

    def test_selection_review_wrapper_closes_the_normative_ranking_bridge(self) -> None:
        position = position_lock()
        valid = recommendation(position)
        candidates: list[dict[str, object]] = []

        hidden_rights_floor = copy.deepcopy(valid)
        hidden_rights_floor["selection_review_wrapper"]["rights_floor"] = ["PF-2"]
        candidates.append(hidden_rights_floor)

        missing_no_action_comparison = copy.deepcopy(valid)
        missing_no_action_comparison["selection_review_wrapper"]["least_harm"][
            "compared_option_ids"
        ].remove("OPTION-NO-ACTION")
        candidates.append(missing_no_action_comparison)

        self_review = copy.deepcopy(valid)
        self_review["selection_review_wrapper"]["least_harm"]["reviewer_ref"] = (
            self_review["selection_review_wrapper"]["jurisdiction_review_boundary"][
                "decision_actor_ref"
            ]
        )
        candidates.append(self_review)

        duplicate_normative_id = copy.deepcopy(valid)
        duplicate_normative_id["selection_review_wrapper"][
            "public_value_premises"
        ].append(
            {
                "normative_principle_id": "N2",
                "role": "target",
                "statement": "保护不得降级",
            }
        )
        candidates.append(duplicate_normative_id)

        incomplete_evidence_matrix = copy.deepcopy(valid)
        incomplete_evidence_matrix["ranking_policy"] = (
            "evidence_bound_case_comparison"
        )
        incomplete_evidence_matrix["ranking_evidence_refs"] = ["RET-1"]
        incomplete_evidence_matrix["selection_review_wrapper"][
            "declared_low_information_house_policy_eligibility"
        ]["case_specific_facts_present"] = True
        incomplete_evidence_matrix["selection_review_wrapper"][
            "ranking_support"
        ] = [
            {
                "option_id": "OPTION-PROBE",
                "evaluation_dimension": "结构解释力",
                "evidence_refs": ["RET-1"],
                "support_reason": "仅填一格不能替代完整的方案×维度矩阵。",
            }
        ]
        candidates.append(incomplete_evidence_matrix)

        for candidate in candidates:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_recommendation_semantics(
                        run_contract(True),
                        candidate,
                        position=position,
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

    def test_recommendation_binds_option_semantics_kind_ranking_and_policy_evidence(self) -> None:
        position = position_lock()
        candidates = []

        stale_semantics = recommendation(position)
        stale_semantics["options"][0]["description"] = "已被静默改写的具体方案"
        candidates.append(stale_semantics)

        false_projection = recommendation(position)
        false_projection["option_kind_ranking"][0:2] = [
            "active_action",
            "probe_action",
        ]
        candidates.append(false_projection)

        unsupported_evidence_policy = recommendation(position)
        unsupported_evidence_policy["ranking_policy"] = "evidence_bound_case_comparison"
        unsupported_evidence_policy["ranking_evidence_refs"] = ["RET-1"]
        unsupported_evidence_policy["selection_review_wrapper"][
            "declared_low_information_house_policy_eligibility"
        ]["case_specific_facts_present"] = True
        unsupported_evidence_policy["selection_review_wrapper"][
            "ranking_support"
        ] = [
            {
                "option_id": "OPTION-PROBE",
                "evaluation_dimension": "结构解释力",
                "evidence_refs": ["RET-1"],
                "support_reason": "只有单格支持，矩阵不完整。",
            }
        ]
        candidates.append(unsupported_evidence_policy)

        stale_record_binding = recommendation(position)
        next(
            record
            for record in stale_record_binding["option_record_hashes"]
            if record["option_id"] == "OPTION-ACTIVE"
        )["record_sha256"] = HASH_B
        candidates.append(stale_record_binding)

        for candidate in candidates:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_recommendation_semantics(
                        run_contract(True),
                        candidate,
                        position=position,
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

    def test_not_requested_branch_is_exact_and_cannot_hide_or_fabricate_advice(self) -> None:
        self.assertEqual(
            validate_recommendation_semantics(
                run_contract(False),
                {"status": "not_requested"},
                position=position_lock(),
                expected_run_id=RUN_ID,
                expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
            ),
            {"status": "not_requested"},
        )
        for required, candidate in (
            (True, {"status": "not_requested"}),
            (False, recommendation(position_lock())),
            (False, {"status": "not_requested", "advice": "偷偷建议"}),
        ):
            with self.subTest(required=required):
                with self.assertRaises(ValueError):
                    validate_recommendation_semantics(
                        run_contract(required),
                        candidate,
                        position=position_lock(),
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )

    def test_recommendation_rejects_bad_ranking_switch_position_hash_and_authorization(self) -> None:
        position = position_lock()
        valid = recommendation(position)
        cases: list[dict[str, object]] = []

        bad_ranking = copy.deepcopy(valid)
        bad_ranking["ranking"][0], bad_ranking["ranking"][1] = (
            bad_ranking["ranking"][1],
            bad_ranking["ranking"][0],
        )
        cases.append(bad_ranking)

        bad_switch = copy.deepcopy(valid)
        bad_switch["switch_conditions"] = ["边界改变时再看"]
        cases.append(bad_switch)

        stale_position = copy.deepcopy(valid)
        stale_position["position_sha256"] = HASH_B
        cases.append(stale_position)

        authorized = copy.deepcopy(valid)
        authorized["authorization_status"] = "authorized"
        cases.append(authorized)

        missing_kind = copy.deepcopy(valid)
        missing_kind["options"][-1]["option_kind"] = "maintain_status_quo"
        cases.append(missing_kind)

        wrong_no_action_pointer = copy.deepcopy(valid)
        wrong_no_action_pointer["no_action_option_id"] = "OPTION-PROBE"
        cases.append(wrong_no_action_pointer)

        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(Exception):
                    validate_recommendation_semantics(
                        run_contract(True),
                        candidate,
                        position=position,
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )


if __name__ == "__main__":
    unittest.main()
