from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime.deliverables import (
    validate_continuation_lineage,
    validate_output_bundle,
)
from promax_runtime.artifacts import (
    ROLE_IDS,
    build_capability_disclosure,
    build_role_plan,
)
from promax_runtime.jsonio import sha256_json
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


RUN_ID = "promax-output-test"
STAMP = "2026-07-23T06:00:00Z"
RUN_NONCE = "n" * 64
REQUEST_SHA256 = hashlib.sha256(b"promax-output-request").hexdigest()
CENTRAL_STATEMENT = "当前结构最符合机制甲。"
OPTION_IDS_BY_OPTION_KIND = (
    ("active_action", "OPTION-ACTIVE"),
    ("delayed_action", "OPTION-DELAYED"),
    ("probe_action", "OPTION-PROBE"),
    ("exit_or_transfer", "OPTION-EXIT"),
    ("maintain_status_quo", "OPTION-STATUS-QUO"),
    ("no_action", "OPTION-NO-ACTION"),
)
LOW_INFORMATION_RANKING = (
    "OPTION-PROBE",
    "OPTION-ACTIVE",
    "OPTION-STATUS-QUO",
    "OPTION-DELAYED",
    "OPTION-EXIT",
    "OPTION-NO-ACTION",
)
SELECTION_SOURCE_REFS = (
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


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def string_leaves(value: object) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for child in value.values():
            result.extend(string_leaves(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(string_leaves(child))
        return result
    return [value] if isinstance(value, str) and value else []


def stance_neutral_problem() -> dict[str, str]:
    semantic_payload = {
        "analysis_object": "当前结构",
        "proposition_under_test": CENTRAL_STATEMENT,
        "time_window": "本轮冻结时间窗",
    }
    return {
        **semantic_payload,
        "evidence_cutoff": "2026-07-23T02:00:00Z",
        "semantic_key_sha256": sha256_json(semantic_payload),
    }


def run_contract(
    recommendation_required: bool = True,
    *,
    mode: str = "promax-complete",
) -> dict[str, object]:
    capabilities = build_capability_disclosure(
        subagents_available=False,
        max_parallelism=0,
        validator_ids=("schema",),
    )
    return {
        "schema_id": "crossframe.promax.v8.run-contract",
        "schema_version": 1,
        "framework_version": "v8.0",
        "run_id": RUN_ID,
        "run_nonce": RUN_NONCE,
        "request_sha256": REQUEST_SHA256,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "mode": mode,
        "recommendation_required": recommendation_required,
        "blocker": None,
        "requested_skill_names": ["crossframe-promax"],
        "routing_conflict": {
            "detected": False,
            "conflicting_names": [],
            "resolved_to": "crossframe-promax",
            "priority_rule": "routing-priority-crossframe-promax-over-crossframe-max-no-fallback",
            "fallback_allowed": False,
        },
        "capabilities": capabilities,
        "orchestration_mode": "single-agent-separated",
        "role_plan": build_role_plan(capabilities),
        "budgets": {
            "paragraphs": 3863,
            "tables": 117,
            "registry_concepts": 709,
            "minimum_red_team_rounds": 2,
            "minimum_no_novelty_rounds": 2,
        },
        "completion_criteria": [
            "source-closure",
            "concept-closure",
            "claim-path-closure",
            "retrieval-and-counterexample-closure",
            "position-lock",
            "output-and-validator-closure",
        ],
        "created_at": STAMP,
    }


def position() -> dict[str, object]:
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
        "primary_reasons": ["当前结构最符合机制甲。"],
        "runner_up_explanation": "机制乙在对象边界改变时成为次优解释。",
        "strongest_counterevidence": ["对象边界并不稳定"],
        "why_not_adopted": ["现有证据尚未证明对象边界已经改变"],
        "withdrawal_conditions": [
            "若对象边界并不稳定得到新证据证实，则撤回当前判断。"
        ],
        "action_ceiling": "不授权现实行动，现实处置需另行授权。",
        "locked_at": "2026-07-23T04:00:00Z",
    }


def selection_review_wrapper(
    *,
    option_ids: list[str],
    evaluation_dimensions: list[str],
) -> dict[str, object]:
    base_review = {
        "principle_version": "v8",
        "selected_option_id": "OPTION-PROBE",
        "compared_option_ids": [*option_ids],
        "evaluation_dimensions": [*evaluation_dimensions],
        "sufficient_reason": "低信息条件下只形成待复核的可逆探针偏好。",
        "evidence_refs": [],
        "reviewer_ref": "REVIEWER-INDEPENDENT-1",
        "reviewed_at": "2026-07-23T04:30:00Z",
        "status": "pending",
    }
    return {
        "wrapper_schema_id": "crossframe.promax.selection-review-wrapper",
        "wrapper_schema_version": 1,
        "wrapper_role": "promax_machine_verification_wrapper_not_v8_source_schema",
        "source_paragraph_refs": [*SELECTION_SOURCE_REFS],
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
                "decision_rule": "保护条件未解决时继续审议。",
                "status": "open",
            }
        ],
        "unresolved_dissent_refs": ["DISSENT-1"],
        "rights_floor": ["PF-1"],
        "affected_positions": ["POSITION-AFFECTED-1"],
        "low_power_position_ids": ["POSITION-AFFECTED-1"],
        "jurisdiction_review_boundary": {
            "boundary_role": "promax_review_boundary_not_atomic_v8_j_tuple",
            "reviewed_option_id": "OPTION-PROBE",
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
            "basis": "没有个案事实，也没有改变选择的检索证据。",
        },
        "ranking_support": [],
    }


def recommendation(position_record: dict[str, object]) -> dict[str, object]:
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
            "information_value": "记录方案产生的辨识信息",
            "lock_in_risk": "保持低锁定并登记升级条件",
            "reversibility": "可停止并回到冻结状态",
            "resource_cost": "需要受限资源投入",
            "authorized_actor_ref": "UNRESOLVED-DECISION-ACTOR",
            "authorization_record_ref": "UNRESOLVED-AUTHORIZATION-SOURCE",
            "stop_conditions": ["边界证据失效时停止"],
            "rollback_and_remedy": ["回到冻结前状态并修复损害"],
        }
        for index, (kind, option_id) in enumerate(
            OPTION_IDS_BY_OPTION_KIND,
            start=1,
        )
    ]
    options_by_id = {option["option_id"]: option for option in options}
    evaluation_dimensions = ["结构解释力", "可逆性", "风险"]
    return {
        "schema_id": "crossframe.promax.v8.recommendation",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "position_sha256": sha256_json(position_record),
        "options": options,
        "evaluation_dimensions": evaluation_dimensions,
        "ranking": [*LOW_INFORMATION_RANKING],
        "ranking_policy": "promax_low_information_house_policy_not_v8",
        "ranking_evidence_refs": [],
        "selection_review_wrapper": selection_review_wrapper(
            option_ids=list(options_by_id),
            evaluation_dimensions=evaluation_dimensions,
        ),
        "option_kind_ranking": [
            options_by_id[option_id]["option_kind"]
            for option_id in LOW_INFORMATION_RANKING
        ],
        "option_record_hashes": [
            {"option_id": option_id, "record_sha256": sha256_json(option)}
            for option_id, option in options_by_id.items()
        ],
        "option_semantic_ranking": [
            sha256_json(
                {
                    key: value
                    for key, value in options_by_id[option_id].items()
                    if key != "option_id"
                }
            )
            for option_id in LOW_INFORMATION_RANKING
        ],
        "preferred_option_id": "OPTION-PROBE",
        "second_option_id": "OPTION-ACTIVE",
        "no_action_option_id": "OPTION-NO-ACTION",
        "switch_conditions": ["对象边界改变时切换到 OPTION-ACTIVE"],
        "inaction_consequences": ["不行动会继续累积机会成本"],
        "authorization_status": "conditional_recommendation_only",
        "locked_at": "2026-07-23T05:00:00Z",
    }


def concept_registry() -> dict[str, object]:
    return {
        "concepts": [
            {
                "concept_id": "V8-CANON-OBJECT",
                "authoritative_name_zh": "对象边界",
                "definition": "对象由被分析关系与排除范围共同界定。",
                "required_neighbor_ids": ["V8-CANON-BOUNDARY"],
            },
            {
                "concept_id": "V8-CANON-BOUNDARY",
                "authoritative_name_zh": "边界约束",
                "definition": "边界约束说明对象何时需要重新冻结。",
                "required_neighbor_ids": ["V8-CANON-OBJECT"],
            },
        ]
    }


def concept_disposition() -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.concept-disposition",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "registry_sha256": "a" * 64,
        "route_ids": ["V8-ROUTE-01-GENERAL"],
        "dispositions": [
            {
                "concept_id": "V8-CANON-OBJECT",
                "status": "applied",
                "rationale": "对象边界直接决定本轮分析范围。",
                "evidence_refs": ["EVIDENCE-1"],
                "required_neighbor_ids": ["V8-CANON-BOUNDARY"],
                "misuses_excluded": ["命名不等于实体存在"],
                "output_section_ids": ["SECTION-1"],
                "pending_evidence": [],
            },
            {
                "concept_id": "V8-CANON-BOUNDARY",
                "status": "applied",
                "rationale": "边界约束决定何时重置对象。",
                "evidence_refs": ["EVIDENCE-2"],
                "required_neighbor_ids": ["V8-CANON-OBJECT"],
                "misuses_excluded": ["边界不是永久不变"],
                "output_section_ids": ["SECTION-1"],
                "pending_evidence": [],
            },
        ],
        "unchecked_concept_ids": [],
        "closure_complete": True,
        "completed_at": "2026-07-23T03:00:00Z",
    }


def claim_graph() -> dict[str, object]:
    return {
        "central_claim_id": "CLAIM-CENTRAL",
        "stance_neutral_problem": stance_neutral_problem(),
        "claims": [
            {
                "claim_id": "CLAIM-CENTRAL",
                "statement": CENTRAL_STATEMENT,
                "concept_ids": ["V8-CANON-OBJECT"],
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
    }


def output_plan(recommendation_required: bool = True) -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.output-plan",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "sections": [
            {
                "section_id": "SECTION-1",
                "title": "中心判断与概念解释",
                "concept_ids": ["V8-CANON-OBJECT", "V8-CANON-BOUNDARY"],
                "claim_ids": ["CLAIM-CENTRAL"],
                "example_ids": [
                    "EX-M1-S1",
                    "EX-M1-S2",
                    "EX-M2-S1",
                    "EX-M2-S2",
                ],
                "counterexample_ids": ["EX-M1-F1", "EX-M2-F1"],
                "judgment_ids": (
                    ["POSITION-LOCK", "RECOMMENDATION-LOCK"]
                    if recommendation_required
                    else ["POSITION-LOCK"]
                ),
                "artifact_paths": [
                    "promax-concept-atlas.md",
                    "promax-case-and-countercase.md",
                    "promax-essay.md",
                ],
            }
        ],
        "required_artifacts": [
            "promax-dossier.md",
            "promax-concept-atlas.md",
            "promax-case-and-countercase.md",
            "promax-essay.md",
        ],
        "unexpanded_branch_ids": [],
        "coverage_complete": True,
        "locked_at": STAMP,
    }


def case_text() -> str:
    return """# 案例与反例

## EX-M1-S1 | mechanism=MECH-1 | relation=similar | type=structural_analogy
相似结构：机制甲在对象边界保持稳定时，因为输入边界连续而维持同一种解释。

## EX-M1-S2 | mechanism=MECH-1 | relation=similar | type=conditional_scenario
条件情景：当对象边界保持稳定，机制甲会产生相似路径并保留早期信号。

## EX-M1-F1 | mechanism=MECH-1 | relation=failure | type=real_case
失效反例：机制甲遇到对象边界发生改变时不再成立，必须停止并重置对象。

## EX-M2-S1 | mechanism=MECH-2 | relation=similar | type=user_material
用户材料例子：机制乙在对象边界发生改变时，因为关系重组而成为相似解释。

## EX-M2-S2 | mechanism=MECH-2 | relation=similar | type=structural_analogy
结构类比：当对象边界发生改变，机制乙产生相似的重新分组路径。

## EX-M2-F1 | mechanism=MECH-2 | relation=failure | type=conditional_scenario
失效反例：机制乙在对象边界保持稳定时缺乏区分力，因此不成立并退出排序。
"""


def deliverables() -> dict[str, str]:
    locked_position = position()
    locked_recommendation = recommendation(locked_position)
    options_by_id = {
        option["option_id"]: option for option in locked_recommendation["options"]
    }
    ranking = locked_recommendation["ranking"]
    wrapper = locked_recommendation["selection_review_wrapper"]
    eligibility_line = (
        "declared_low_information_house_policy_eligibility: "
        "case_specific_facts_present=false; "
        "choice_changing_retrieval_evidence_present=false"
    )
    dossier_wrapper_line = "；".join(
        [
            str(wrapper["wrapper_schema_id"]),
            str(wrapper["wrapper_role"]),
            *[str(item) for item in wrapper["source_paragraph_refs"]],
            str(wrapper["selection_type"]),
            str(wrapper["selection_status"]),
            str(wrapper["jurisdiction_review_boundary"]["boundary_role"]),
            str(wrapper["least_harm"]["principle_id"]),
            str(wrapper["least_harm"]["status"]),
            str(wrapper["proportionality"]["principle_id"]),
            str(wrapper["proportionality"]["status"]),
        ]
    )
    essay_wrapper_line = "；".join(dict.fromkeys(string_leaves(wrapper)))
    dossier = (
        "# 推演档案\n"
        f"{CENTRAL_STATEMENT} 方案全集包括 {'、'.join(ranking)}。\n"
        "ranking_policy=promax_low_information_house_policy_not_v8。\n"
        "PROMAX-HOUSE-POLICY-NOT-V8：这是 ProMax 的低信息排序政策，不是 v8 概念、规范前提或 v8 自动结论；ranking_evidence_refs=[]。\n"
        f"规范选择审查包装层：{dossier_wrapper_line}。\n"
        f"{eligibility_line}\n"
    )
    atlas = """# 概念图谱
## V8-CANON-OBJECT 对象边界
对象由被分析关系与排除范围共同界定。对象边界直接决定本轮分析范围；它与边界约束相邻。误用边界：命名不等于实体存在。

## V8-CANON-BOUNDARY 边界约束
边界约束说明对象何时需要重新冻结。边界约束决定何时重置对象；它与对象边界相邻。误用边界：边界不是永久不变。
"""
    option_details = "\n".join(
        "；".join(
            [
                f"{option_id} {options_by_id[option_id]['description']}",
                f"option_kind={options_by_id[option_id]['option_kind']}",
                *[
                    f"{field}="
                    + "、".join(str(item) for item in options_by_id[option_id][field])
                    for field in (
                        "forecast_refs",
                        "normative_premise_refs",
                        "affected_position_refs",
                        "rights_floor_refs",
                        "expected_paths",
                        "cross_circle_spillovers",
                        "stop_conditions",
                        "rollback_and_remedy",
                    )
                ],
                *[
                    f"{field}={options_by_id[option_id][field]}"
                    for field in (
                        "worst_acceptable_outcome",
                        "distribution_of_costs_and_benefits",
                        "information_value",
                        "lock_in_risk",
                        "reversibility",
                        "resource_cost",
                        "authorized_actor_ref",
                        "authorization_record_ref",
                    )
                ],
            ]
        )
        for option_id in ranking
    )
    essay = f"""# 中心判断
{locked_position['position']} 判断强度：moderate。当前结构最符合机制甲。机制乙在对象边界改变时成为次优解释。

对象边界是本轮判断的起点：对象由被分析关系与排除范围共同界定。对象边界直接决定本轮分析范围，并与边界约束共同工作；命名不等于实体存在。

边界约束说明对象何时需要重新冻结。边界约束决定何时重置对象，边界不是永久不变。

最强反例是对象边界并不稳定。现有证据尚未证明对象边界已经改变。若对象边界并不稳定得到新证据证实，则撤回当前判断。不授权现实行动，现实处置需另行授权。

评价维度包括结构解释力、可逆性、风险。
{option_details}
ranking_policy=promax_low_information_house_policy_not_v8。PROMAX-HOUSE-POLICY-NOT-V8：这是 ProMax 的低信息排序政策，不是 v8 概念、规范前提或 v8 自动结论；ranking_evidence_refs=[]。
selection_review_wrapper 完整公开语义：{essay_wrapper_line}。
{eligibility_line}
O1=complete；O2=complete；O3=in_review；O4=not_started。
我明确首选 OPTION-PROBE；次选 OPTION-ACTIVE。对象边界改变时切换到 OPTION-ACTIVE；不行动会继续累积机会成本；所有建议仅是 conditional_recommendation_only。
"""
    return {
        "promax-dossier.md": dossier,
        "promax-concept-atlas.md": atlas,
        "promax-case-and-countercase.md": case_text(),
        "promax-essay.md": essay,
    }


def manifest(
    contents: dict[str, str],
    contract: dict[str, object] | None = None,
) -> dict[str, object]:
    contract = contract or run_contract()
    role_records = []
    for index, role_id in enumerate(ROLE_IDS, start=1):
        input_ref = {
            "path": f"inputs/{index}.json",
            "sha256": "a" * 64,
            "media_type": "application/json",
        }
        role_records.append(
            {
                "role_id": role_id,
                "sequence": index,
                "execution_mode": "single-agent-separated",
                "exchange_protocol": "structured-artifacts-only",
                "input_artifacts": [input_ref],
                "observed_input_artifacts": [input_ref],
                "output_artifacts": [
                    {
                        "path": f"outputs/{index}.json",
                        "sha256": "c" * 64,
                        "media_type": "application/json",
                    }
                ],
                "status": "completed",
            }
        )
    body: dict[str, object] = {
        "schema_id": "crossframe.promax.v8.artifact-manifest",
        "schema_version": 1,
        "run_id": RUN_ID,
        "run_nonce": contract["run_nonce"],
        "request_sha256": contract["request_sha256"],
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "run_contract_sha256": sha256_json(contract),
        "mode": contract["mode"],
        "orchestration_mode": contract["orchestration_mode"],
        "role_records": role_records,
        "phase_chain_head_sha256": "b" * 64,
        "artifacts": [
            {
                "path": path,
                "sha256": text_sha(text),
                "media_type": "text/markdown",
                "generating_phase": "P10",
                "input_artifact_sha256s": ["a" * 64],
                "status": "current",
            }
            for path, text in sorted(contents.items())
        ],
        "generated_at": "2026-07-23T06:15:00Z",
    }
    return {**body, "manifest_sha256": sha256_json(body)}


def continuation_ledger(
    manifest_record: dict[str, object],
    contents: dict[str, str],
) -> dict[str, object]:
    return {
        "schema_id": "crossframe.promax.v8.continuation-ledger",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "parent_manifest_sha256": manifest_record["manifest_sha256"],
        "continuations": [
            {
                "continuation_id": "CONT-1",
                "sequence": 1,
                "parent_artifact_sha256": text_sha(contents["promax-essay.md"]),
                "resume_from_phase": "P10",
                "pending_artifact_paths": ["promax-essay-part-2.md"],
                "reason": "平台输出边界先耗尽",
                "status": "pending",
            }
        ],
        "updated_at": "2026-07-23T06:30:00Z",
    }


def valid_bundle() -> dict[str, object]:
    content = deliverables()
    contract = run_contract()
    manifest_record = manifest(content, contract)
    position_record = position()
    return {
        "run_contract": contract,
        "position": position_record,
        "recommendation": recommendation(position_record),
        "output_plan": output_plan(),
        "concept_disposition": concept_disposition(),
        "claim_path_graph": claim_graph(),
        "concept_registry": concept_registry(),
        "deliverables": content,
        "manifest": manifest_record,
        "continuation_ledger": continuation_ledger(manifest_record, content),
    }


def refresh_delivery_bindings(bundle: dict[str, object]) -> None:
    bundle["manifest"] = manifest(bundle["deliverables"], bundle["run_contract"])
    bundle["continuation_ledger"] = continuation_ledger(
        bundle["manifest"], bundle["deliverables"]
    )


class ProMaxOutputBundleTests(unittest.TestCase):
    def test_semantically_complete_bundle_passes_with_length_only_as_anomaly(self) -> None:
        result = validate_output_bundle(**valid_bundle())
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(
            set(result["covered_concept_ids"]),
            {"V8-CANON-OBJECT", "V8-CANON-BOUNDARY"},
        )

    def test_applied_concept_without_registered_misuses_does_not_require_fabrication(self) -> None:
        bundle = valid_bundle()
        object_record = bundle["concept_registry"]["concepts"][0]
        object_record["common_misuses"] = []
        object_record["forbidden_substitutions_or_generalizations"] = []
        object_disposition = bundle["concept_disposition"]["dispositions"][0]
        object_disposition["misuses_excluded"] = []

        result = validate_output_bundle(**bundle)

        self.assertEqual(result["status"], "valid")
        self.assertIn("V8-CANON-OBJECT", result["covered_concept_ids"])

    def test_not_requested_recommendation_remains_closed_through_final_artifacts(self) -> None:
        bundle = valid_bundle()
        bundle["run_contract"]["recommendation_required"] = False
        bundle["recommendation"] = {"status": "not_requested"}
        bundle["output_plan"] = output_plan(False)
        bundle["deliverables"]["promax-dossier.md"] = "# 推演档案\n当前结构最符合机制甲。\n"
        essay = bundle["deliverables"]["promax-essay.md"]
        bundle["deliverables"]["promax-essay.md"] = essay[: essay.index("评价维度")]
        bundle["manifest"] = manifest(bundle["deliverables"], bundle["run_contract"])
        bundle["continuation_ledger"] = continuation_ledger(
            bundle["manifest"], bundle["deliverables"]
        )
        self.assertEqual(validate_output_bundle(**bundle)["status"], "valid")

        fabricated = copy.deepcopy(bundle)
        fabricated["deliverables"]["promax-essay.md"] += "我建议优先选择 OPTION-PROBE。"
        fabricated["manifest"] = manifest(
            fabricated["deliverables"], fabricated["run_contract"]
        )
        fabricated["continuation_ledger"] = continuation_ledger(
            fabricated["manifest"], fabricated["deliverables"]
        )
        with self.assertRaises(ValueError):
            validate_output_bundle(**fabricated)

    def test_formal_run_plan_and_manifest_schemas_are_hard_prerequisites(self) -> None:
        cases: list[dict[str, object]] = []

        invalid_run = valid_bundle()
        invalid_run["run_contract"].pop("schema_id")
        invalid_run["manifest"] = manifest(
            invalid_run["deliverables"], invalid_run["run_contract"]
        )
        invalid_run["continuation_ledger"] = continuation_ledger(
            invalid_run["manifest"], invalid_run["deliverables"]
        )
        cases.append(invalid_run)

        invalid_plan = valid_bundle()
        invalid_plan["output_plan"].pop("locked_at")
        cases.append(invalid_plan)

        invalid_manifest = valid_bundle()
        invalid_manifest["manifest"].pop("generated_at")
        unsigned = dict(invalid_manifest["manifest"])
        unsigned.pop("manifest_sha256")
        invalid_manifest["manifest"]["manifest_sha256"] = sha256_json(unsigned)
        invalid_manifest["continuation_ledger"]["parent_manifest_sha256"] = (
            invalid_manifest["manifest"]["manifest_sha256"]
        )
        cases.append(invalid_manifest)

        for bundle in cases:
            with self.subTest(bundle=bundle):
                with self.assertRaises(Exception):
                    validate_output_bundle(**bundle)

    def test_complete_mode_requires_a_closed_output_plan(self) -> None:
        for coverage_complete, unexpanded in (
            (False, []),
            (False, ["BRANCH-UNEXPANDED"]),
        ):
            bundle = valid_bundle()
            bundle["output_plan"]["coverage_complete"] = coverage_complete
            bundle["output_plan"]["unexpanded_branch_ids"] = unexpanded
            with self.subTest(
                coverage_complete=coverage_complete,
                unexpanded=unexpanded,
            ):
                with self.assertRaises(ValueError):
                    validate_output_bundle(**bundle)

    def test_essay_covers_strength_dimensions_and_every_option_field(self) -> None:
        cases: list[dict[str, object]] = []

        no_strength = valid_bundle()
        no_strength["deliverables"]["promax-essay.md"] = no_strength[
            "deliverables"
        ]["promax-essay.md"].replace("判断强度：moderate。", "")
        refresh_delivery_bindings(no_strength)
        cases.append(no_strength)

        no_dimension = valid_bundle()
        no_dimension["deliverables"]["promax-essay.md"] = no_dimension[
            "deliverables"
        ]["promax-essay.md"].replace("可逆性", "可调整程度")
        refresh_delivery_bindings(no_dimension)
        cases.append(no_dimension)

        unique_option_field = valid_bundle()
        unique_option_field["recommendation"]["options"][0]["information_value"] = (
            "OPTION-ACTIVE 独有信息价值"
        )
        cases.append(unique_option_field)

        for bundle in cases:
            with self.subTest(bundle=bundle):
                with self.assertRaises(ValueError):
                    validate_output_bundle(**bundle)

    def test_output_plan_judgment_ids_exactly_follow_recommendation_intent(self) -> None:
        missing_position = valid_bundle()
        missing_position["output_plan"]["sections"][0]["judgment_ids"] = [
            "RECOMMENDATION-LOCK"
        ]

        missing_recommendation = valid_bundle()
        missing_recommendation["output_plan"]["sections"][0]["judgment_ids"] = [
            "POSITION-LOCK"
        ]

        fabricated_recommendation = valid_bundle()
        fabricated_recommendation["run_contract"]["recommendation_required"] = False
        fabricated_recommendation["recommendation"] = {"status": "not_requested"}
        fabricated_recommendation["deliverables"]["promax-dossier.md"] = (
            "# 推演档案\n当前结构最符合机制甲。\n"
        )
        essay = fabricated_recommendation["deliverables"]["promax-essay.md"]
        fabricated_recommendation["deliverables"]["promax-essay.md"] = essay[
            : essay.index("评价维度")
        ]
        refresh_delivery_bindings(fabricated_recommendation)

        for bundle in (
            missing_position,
            missing_recommendation,
            fabricated_recommendation,
        ):
            with self.subTest(bundle=bundle):
                with self.assertRaises(ValueError):
                    validate_output_bundle(**bundle)

    def test_marker_stuffing_and_long_repetition_cannot_replace_semantics(self) -> None:
        bundle = valid_bundle()
        bundle["deliverables"]["promax-essay.md"] = (
            "V8-CANON-OBJECT V8-CANON-BOUNDARY CLAIM-CENTRAL MECH-1 POSITION-LOCK "
            * 1000
        )
        bundle["manifest"] = manifest(bundle["deliverables"], bundle["run_contract"])
        bundle["continuation_ledger"] = continuation_ledger(
            bundle["manifest"], bundle["deliverables"]
        )
        with self.assertRaises(ValueError):
            validate_output_bundle(**bundle)

    def test_marker_ledger_cannot_replace_continuous_semantic_paragraphs(self) -> None:
        bundle = valid_bundle()
        bundle["deliverables"]["promax-essay.md"] = """# Marker Ledger
position:当前条件下，机制甲是最合理解释。
strength:moderate
reasons:当前结构最符合机制甲。
runner_up:机制乙在对象边界改变时成为次优解释。
counterevidence:对象边界并不稳定
why_not:现有证据尚未证明对象边界已经改变
withdrawal:若对象边界并不稳定得到新证据证实，则撤回当前判断。
action_ceiling:不授权现实行动，现实处置需另行授权。
V8-CANON-OBJECT:对象边界
definition:对象由被分析关系与排除范围共同界定。
V8-CANON-BOUNDARY:边界约束
definition:边界约束说明对象何时需要重新冻结。
CLAIM-CENTRAL:当前结构最符合机制甲。
dimensions:结构解释力|可逆性|风险
OPTION-PROBE:方案3：probe
OPTION-PROACTIVE:方案1：proactive_action
OPTION-STATUS-QUO:方案5：status_quo
OPTION-DELAY:方案2：delay
OPTION-EXIT:方案4：exit_or_transfer
OPTION-INACTION:方案6：inaction
benefits:保留结构收益
costs:承担可比较成本
risks:存在条件性风险
authorization:requires_authorized_decision_maker
stop:边界证据失效时停止
rollback:回到冻结前状态
preferred:首选 OPTION-PROBE
second:次选 OPTION-PROACTIVE
switch:对象边界改变时切换到 OPTION-PROACTIVE
inaction:不行动会继续累积机会成本
authorization:conditional_recommendation_only
"""
        self.assertGreaterEqual(len(bundle["deliverables"]["promax-essay.md"]), 750)
        self.assertLessEqual(len(bundle["deliverables"]["promax-essay.md"]), 1_000)
        refresh_delivery_bindings(bundle)
        with self.assertRaisesRegex(
            ValueError,
            "locked position field|continuous semantic paragraph",
        ):
            validate_output_bundle(**bundle)

    def test_every_applied_concept_requires_definition_role_misuse_and_neighbor_semantics(self) -> None:
        bundle = valid_bundle()
        bundle["deliverables"]["promax-concept-atlas.md"] = (
            "# 图谱\nV8-CANON-OBJECT V8-CANON-BOUNDARY 对象边界 边界约束"
        )
        bundle["manifest"] = manifest(bundle["deliverables"], bundle["run_contract"])
        bundle["continuation_ledger"] = continuation_ledger(
            bundle["manifest"], bundle["deliverables"]
        )
        with self.assertRaises(ValueError):
            validate_output_bundle(**bundle)

    def test_each_mechanism_needs_two_typed_similar_examples_and_one_typed_failure(self) -> None:
        for mutation in ("untyped", "one-similar", "no-failure"):
            bundle = valid_bundle()
            cases = bundle["deliverables"]["promax-case-and-countercase.md"]
            if mutation == "untyped":
                cases = cases.replace("type=structural_analogy", "type=unknown", 1)
            elif mutation == "one-similar":
                start = cases.index("## EX-M1-S2")
                end = cases.index("## EX-M1-F1")
                cases = cases[:start] + cases[end:]
            else:
                start = cases.index("## EX-M2-F1")
                cases = cases[:start]
            bundle["deliverables"]["promax-case-and-countercase.md"] = cases
            bundle["manifest"] = manifest(
                bundle["deliverables"], bundle["run_contract"]
            )
            bundle["continuation_ledger"] = continuation_ledger(
                bundle["manifest"], bundle["deliverables"]
            )
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    validate_output_bundle(**bundle)

    def test_plan_content_and_manifest_are_bidirectionally_fresh(self) -> None:
        mutations: list[dict[str, object]] = []

        missing_plan_concept = valid_bundle()
        missing_plan_concept["output_plan"]["sections"][0]["concept_ids"] = [
            "V8-CANON-OBJECT"
        ]
        mutations.append(missing_plan_concept)

        stale_essay = valid_bundle()
        stale_essay["manifest"]["artifacts"][-1]["sha256"] = "f" * 64
        body = dict(stale_essay["manifest"])
        body.pop("manifest_sha256")
        stale_essay["manifest"]["manifest_sha256"] = sha256_json(body)
        mutations.append(stale_essay)

        missing_position = valid_bundle()
        missing_position["deliverables"]["promax-essay.md"] = (
            missing_position["deliverables"]["promax-essay.md"].replace(
                position()["position"], "判断暂不表达"
            )
        )
        missing_position["manifest"] = manifest(
            missing_position["deliverables"], missing_position["run_contract"]
        )
        missing_position["continuation_ledger"] = continuation_ledger(
            missing_position["manifest"], missing_position["deliverables"]
        )
        mutations.append(missing_position)

        for bundle in mutations:
            with self.subTest(bundle=bundle):
                with self.assertRaises(ValueError):
                    validate_output_bundle(**bundle)


class ProMaxContinuationTests(unittest.TestCase):
    def test_continuation_is_bound_to_current_manifest_parent_artifact_and_p10(self) -> None:
        bundle = valid_bundle()
        result = validate_continuation_lineage(
            bundle["continuation_ledger"],
            manifest=bundle["manifest"],
            deliverables=bundle["deliverables"],
        )
        self.assertEqual(result["continuations"][0]["sequence"], 1)

    def test_wrong_parent_manifest_artifact_phase_or_sequence_is_rejected(self) -> None:
        for field, replacement in (
            ("parent_manifest_sha256", "f" * 64),
            ("parent_artifact_sha256", "e" * 64),
            ("resume_from_phase", "P9"),
            ("sequence", 2),
        ):
            bundle = valid_bundle()
            if field == "parent_manifest_sha256":
                bundle["continuation_ledger"][field] = replacement
            else:
                bundle["continuation_ledger"]["continuations"][0][field] = replacement
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate_continuation_lineage(
                        bundle["continuation_ledger"],
                        manifest=bundle["manifest"],
                        deliverables=bundle["deliverables"],
                    )

    def test_parent_artifact_must_have_been_generated_in_p10(self) -> None:
        bundle = valid_bundle()
        essay_hash = text_sha(bundle["deliverables"]["promax-essay.md"])
        for record in bundle["manifest"]["artifacts"]:
            if record["sha256"] == essay_hash:
                record["generating_phase"] = "P9"
        unsigned = dict(bundle["manifest"])
        unsigned.pop("manifest_sha256")
        bundle["manifest"]["manifest_sha256"] = sha256_json(unsigned)
        bundle["continuation_ledger"]["parent_manifest_sha256"] = bundle[
            "manifest"
        ]["manifest_sha256"]
        with self.assertRaises(ValueError):
            validate_continuation_lineage(
                bundle["continuation_ledger"],
                manifest=bundle["manifest"],
                deliverables=bundle["deliverables"],
            )


if __name__ == "__main__":
    unittest.main()
