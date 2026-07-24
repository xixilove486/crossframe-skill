from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator

from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "skills/crossframe-promax/schemas"
RUNTIME_MODULE_PATH = (
    ROOT / "skills/crossframe-promax/scripts/promax_runtime/schemas.py"
)
SOURCE_SNAPSHOT_SHA256 = (
    "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
RUN_ID = "promax-run-20260723-0001"
RUN_NONCE = "n" * 48
STAMP = "2026-07-23T00:00:00Z"
CENTRAL_STATEMENT = "当前结构更符合机制甲。"
HOUSE_OPTION_RANKING = (
    "OPTION-PROBE",
    "OPTION-ACTIVE",
    "OPTION-STATUS-QUO",
    "OPTION-DELAYED",
    "OPTION-EXIT",
    "OPTION-NO-ACTION",
)
HOUSE_OPTION_KIND_RANKING = (
    "probe_action",
    "active_action",
    "maintain_status_quo",
    "delayed_action",
    "exit_or_transfer",
    "no_action",
)

EXPECTED_RUNTIME_SCHEMAS = (
    "promax-artifact-manifest.schema.json",
    "promax-claim-path-graph.schema.json",
    "promax-common.schema.json",
    "promax-concept-disposition.schema.json",
    "promax-continuation-ledger.schema.json",
    "promax-local-world-model.schema.json",
    "promax-output-plan.schema.json",
    "promax-phase-event.schema.json",
    "promax-position.schema.json",
    "promax-read-event.schema.json",
    "promax-recommendation.schema.json",
    "promax-red-team-report.schema.json",
    "promax-repair-plan.schema.json",
    "promax-retrieval-ledger.schema.json",
    "promax-run-contract.schema.json",
    "promax-source-snapshot.schema.json",
    "promax-validator-report.schema.json",
)
EXPECTED_SCHEMA_IDS = {
    name: f"https://crossframe.local/schemas/{name}"
    for name in EXPECTED_RUNTIME_SCHEMAS
}
ALLOWED_MODES = {
    "promax-artifact-run",
    "promax-complete",
    "promax-design-review",
    "promax-blocked/progress",
}
ROLE_IDS = (
    "v8_source_concept_auditor",
    "external_case_researcher",
    "counterexample_auditor",
    "position_adjudicator",
    "longform_writer",
)
MODEL_AUTHORED_SCHEMAS = (
    "promax-local-world-model.schema.json",
    "promax-concept-disposition.schema.json",
    "promax-claim-path-graph.schema.json",
    "promax-retrieval-ledger.schema.json",
    "promax-red-team-report.schema.json",
    "promax-position.schema.json",
    "promax-recommendation.schema.json",
    "promax-output-plan.schema.json",
    "promax-repair-plan.schema.json",
)
HIDDEN_THOUGHT_FIELD_NAMES = (
    "chain_of_thought",
    "hidden_chain_of_thought",
    "private_reasoning",
    "internal_monologue",
    "scratchpad",
)


def fixture_sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stance_neutral_problem() -> dict[str, str]:
    semantic_payload = {
        "analysis_object": "当前结构",
        "proposition_under_test": CENTRAL_STATEMENT,
        "time_window": "本轮冻结时间窗",
    }
    return {
        **semantic_payload,
        "evidence_cutoff": STAMP,
        "semantic_key_sha256": fixture_sha256_json(semantic_payload),
    }


def load_runtime_module() -> ModuleType:
    if not RUNTIME_MODULE_PATH.is_file():
        raise AssertionError(f"missing runtime schema module: {RUNTIME_MODULE_PATH}")
    runtime_scripts = str(RUNTIME_MODULE_PATH.parents[1])
    if runtime_scripts not in sys.path:
        sys.path.insert(0, runtime_scripts)
    return importlib.import_module("promax_runtime.schemas")


def artifact(path: str, sha256: str = HASH_A) -> dict[str, Any]:
    return {
        "path": path,
        "sha256": sha256,
        "media_type": "application/json",
    }


def role_plan_record(
    role_id: str,
    sequence: int,
    execution_mode: str,
) -> dict[str, Any]:
    return {
        "role_id": role_id,
        "sequence": sequence,
        "execution_mode": execution_mode,
        "exchange_protocol": "structured-artifacts-only",
    }


def role_record(
    role_id: str,
    sequence: int,
    execution_mode: str,
) -> dict[str, Any]:
    record = {
        **role_plan_record(role_id, sequence, execution_mode),
        "input_artifacts": [artifact(f"inputs/{sequence}.json", HASH_A)],
        "observed_input_artifacts": [
            artifact(f"inputs/{sequence}.json", HASH_A)
        ],
        "output_artifacts": [artifact(f"outputs/{sequence}.json", HASH_B)],
        "status": "completed",
    }
    if execution_mode == "multi-agent-isolated":
        record.update(
            {
                "agent_id": f"schema-agent-{sequence}",
                "execution_attestation": {
                    "run_id": RUN_ID,
                    "request_sha256": HASH_A,
                    "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
                    "completed_at": STAMP,
                    "observed_input_artifacts": [
                        artifact(f"inputs/{sequence}.json", HASH_A)
                    ],
                    "produced_output_artifacts": [
                        artifact(f"outputs/{sequence}.json", HASH_B)
                    ],
                    "claim_sha256": HASH_C,
                },
            }
        )
    return record


def capabilities(subagents: bool) -> dict[str, Any]:
    return {
        "files": {
            "available": True,
            "readable": True,
            "writable": True,
            "limitations": [],
        },
        "network": {
            "available": True,
            "live_retrieval": True,
            "limitations": [],
        },
        "subagents": {
            "available": subagents,
            "isolated_roles": subagents,
            "max_parallelism": 4 if subagents else 0,
            "limitations": [] if subagents else ["subagent API unavailable"],
        },
        "validators": {
            "available": True,
            "executable": True,
            "validator_ids": ["schema", "source-integrity", "state-machine"],
            "limitations": [],
        },
    }


def run_contract(
    *,
    conflict: bool = False,
    subagents: bool = True,
    mode: str = "promax-artifact-run",
) -> dict[str, Any]:
    execution_mode = (
        "multi-agent-isolated" if subagents else "single-agent-separated"
    )
    requested_names = ["crossframe-promax"]
    conflicting_names: list[str] = []
    if conflict:
        requested_names.append("crossframe-max")
        conflicting_names = ["crossframe-promax", "crossframe-max"]
    return {
        "schema_id": "crossframe.promax.v8.run-contract",
        "schema_version": 1,
        "framework_version": "v8.0",
        "run_id": RUN_ID,
        "run_nonce": RUN_NONCE,
        "request_sha256": HASH_A,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "mode": mode,
        "recommendation_required": False,
        "blocker": (
            {
                "category": "source_unavailable",
                "detail": "the frozen v8 source cannot be accessed",
            }
            if mode == "promax-blocked/progress"
            else None
        ),
        "requested_skill_names": requested_names,
        "routing_conflict": {
            "detected": conflict,
            "conflicting_names": conflicting_names,
            "resolved_to": "crossframe-promax",
            "priority_rule": "routing-priority-crossframe-promax-over-crossframe-max-no-fallback",
            "fallback_allowed": False,
        },
        "capabilities": capabilities(subagents),
        "orchestration_mode": execution_mode,
        "role_plan": [
            role_plan_record(role_id, index, execution_mode)
            for index, role_id in enumerate(ROLE_IDS, start=1)
        ],
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


def source_snapshot() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.source-snapshot",
        "schema_version": 1,
        "framework_version": "v8.0",
        "snapshot_id": "crossframe-promax-v8-source-3186805a",
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "source_manifest_sha256": HASH_A,
        "concept_registry_sha256": HASH_B,
        "contract_map_sha256": HASH_C,
        "route_map_sha256": HASH_D,
        "paragraph_count": 3863,
        "non_whitespace_chars": 155721,
        "table_count": 117,
        "section_count": 16,
        "verified_at": STAMP,
    }


def phase_event() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.phase-event",
        "schema_version": 1,
        "event_index": 0,
        "event_type": "phase_sealed",
        "run_id": RUN_ID,
        "run_nonce": RUN_NONCE,
        "request_sha256": HASH_A,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "phase_id": "P0",
        "status": "completed",
        "parent_phase_sha256": None,
        "input_phase_hashes": {},
        "input_artifact_hashes": {},
        "output_artifact_hashes": {"promax-run-contract.json": HASH_B},
        "previous_event_sha256": None,
        "invalidated_phases": [],
        "reset_reason": None,
        "event_sha256": HASH_C,
    }


def read_event() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.read-event",
        "schema_version": 1,
        "event_id": "read-event-000001",
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "sequence": 1,
        "source_kind": "paragraph",
        "source_anchor": "V8-P0001",
        "source_file": "00-source-envelope.md",
        "content_sha256": HASH_A,
        "read_at": STAMP,
    }


def local_world_model() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.local-world-model",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "phase_id": "P3",
        "object_boundary": {
            "object_id": "OBJ-1",
            "name": "被分析对象",
            "in_scope": ["对象内部结构"],
            "out_of_scope": ["未经授权的现实行动"],
        },
        "actor_records": [
            {
                "actor_id": "ACTOR-1",
                "label": "行动者甲",
                "roles": ["决策参与者"],
                "observed_state": ["已表达偏好"],
                "inferred_state": ["条件性假设"],
                "inference_limits": ["不得由一次行为推定稳定人格"],
            }
        ],
        "circle_candidates": [
            {
                "circle_id": "CIRCLE-1",
                "label": "候选圈层",
                "membership_basis": ["可观察互动"],
                "reification_risks": ["命名不等于实体存在"],
            }
        ],
        "scale_profile": {
            "focal_scale": "个体与组织接口",
            "included_scales": ["个体", "组织"],
            "excluded_scales": ["无证据支持的文明阶段"],
            "transformation_limits": ["跨尺度结论必须补充尺度条件"],
        },
        "material_channel": {
            "state": ["资源约束"],
            "observables": ["预算"],
            "unknowns": ["隐性成本"],
        },
        "experiential_meaning_channel": {
            "state": ["意义解释存在分歧"],
            "observables": ["公开陈述"],
            "unknowns": ["未表达体验"],
        },
        "M_state": {
            "description": "材料与结构状态",
            "evidence_refs": ["EVIDENCE-1"],
            "uncertainties": ["测量误差"],
        },
        "Psi_state": {
            "description": "体验与意义状态",
            "evidence_refs": ["EVIDENCE-2"],
            "uncertainties": ["解释竞争"],
        },
        "clocks": [
            {
                "clock_id": "CLOCK-1",
                "label": "决策时钟",
                "current_time": STAMP,
                "horizon": "P90D",
                "lag": "P7D",
            }
        ],
        "events": [
            {
                "event_id": "EVENT-1",
                "event_type": "observed",
                "time": STAMP,
                "description": "请求进入分析",
                "evidence_refs": ["EVIDENCE-1"],
            }
        ],
        "evidence_cutoff": STAMP,
        "unknowns": [
            {
                "unknown_id": "UNKNOWN-1",
                "question": "哪项信息最能改变路径排序？",
                "decision_impact": "可能改变首选建议",
                "retrieval_plan": "检索反向与失败案例",
            }
        ],
        "residuals": [
            {
                "residual_id": "RESIDUAL-1",
                "description": "模型外剩余",
                "handling": "保留为不可吸收残差",
            }
        ],
        "identity_criteria": [
            {
                "criterion": "跨时间保持的对象边界",
                "test": "边界变化时重新冻结对象",
            }
        ],
        "action_limits": ["分析不自动授权行动"],
        "authorization_limits": ["现实行动必须由有权主体另行授权"],
        "locked_at": STAMP,
    }


def concept_disposition() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.concept-disposition",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "registry_sha256": HASH_A,
        "route_ids": ["V8-ROUTE-01-GENERAL-STRUCTURE"],
        "dispositions": [
            {
                "concept_id": "V8-CANON-OBJECT",
                "status": "applied",
                "rationale": "对象边界直接参与当前推演。",
                "evidence_refs": ["EVIDENCE-1"],
                "required_neighbor_ids": ["V8-CANON-BOUNDARY"],
                "misuses_excluded": ["命名即实体化"],
                "output_section_ids": ["SECTION-1"],
                "pending_evidence": [],
            }
        ],
        "unchecked_concept_ids": [],
        "closure_complete": True,
        "completed_at": STAMP,
    }


def claim_path_graph() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.claim-path-graph",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-CENTRAL",
        "stance_neutral_problem": stance_neutral_problem(),
        "central_claim_cycle": {
            "central_claim_id": "CLAIM-CENTRAL",
            "initial_judgment": CENTRAL_STATEMENT,
            "strongest_attack": "选择偏差可能产生同样的观察。",
            "revision": "仅在时间顺序与传导证据同时存在时保留判断。",
            "counterfactual": "若传导通道不存在，下游状态不应按该路径更新。",
            "withdrawal_conditions": ["简单基线在样本外解释力相同时撤回"],
        },
        "claims": [
            {
                "claim_id": "CLAIM-CENTRAL",
                "statement": CENTRAL_STATEMENT,
                "claim_type": "structural",
                "evidence_refs": ["EVIDENCE-1"],
                "concept_ids": ["V8-CANON-OBJECT"],
                "confidence": "medium",
                "authorization_ceiling": "分析判断，不授权现实行动",
            }
        ],
        "mechanisms": [
            {
                "mechanism_id": "MECH-1",
                "label": "机制甲",
                "claim_ids": ["CLAIM-CENTRAL"],
                "distinguishing_conditions": ["条件甲"],
            },
            {
                "mechanism_id": "MECH-2",
                "label": "机制乙",
                "claim_ids": ["CLAIM-CENTRAL"],
                "distinguishing_conditions": ["条件乙"],
            },
        ],
        "path_nodes": [
            {
                "node_id": "NODE-1",
                "label": "当前状态",
                "node_type": "state",
                "trigger_conditions": ["请求已冻结"],
                "early_signals": ["证据出现"],
                "reverse_signals": ["反向证据出现"],
                "stop_conditions": ["授权边界触发"],
            }
        ],
        "path_edges": [],
        "forecast_conditions": ["仅作条件化排序"],
        "choice_boundary": "预测不产生授权",
        "updated_at": STAMP,
    }


def retrieval_ledger() -> dict[str, Any]:
    directions = (
        "support",
        "reverse",
        "failure",
        "alternative_mechanism",
        "affected_or_low_power",
    )
    relations = {
        "support": "supports",
        "reverse": "refutes",
        "failure": "refutes",
        "alternative_mechanism": "alternative_mechanism",
        "affected_or_low_power": "affected_position",
    }
    return {
        "schema_id": "crossframe.promax.v8.retrieval-ledger",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "entries": [
            {
                "retrieval_id": f"RETRIEVAL-{index}",
                "round": 1 if index <= 3 else 2,
                "direction": direction,
                "claim_relation": relations[direction],
                "query": f"结构案例 {direction}",
                "tool": "web-search",
                "retrieved_at": STAMP,
                "sources": [
                    {
                        "url": f"https://example.test/{index}",
                        "title": f"来源 {index}",
                        "publisher": "Example",
                        "published_at": "2026-07-01",
                        "event_date": "2026-06-01",
                        "source_type": "primary",
                        "interest_relevance": "无直接利益关系",
                        "independence_group": f"GROUP-{index}",
                        "duplicate_relation": "independent",
                        "duplicate_of_url": None,
                    }
                ],
                "claim_ids": ["CLAIM-CENTRAL"],
                "finding": "用于压力测试，不替代 v8 定义。",
                "cannot_prove": ["不能单独证明授权"],
                "stop_reason": "该方向已返回可审计结果",
            }
            for index, direction in enumerate(directions, start=1)
        ],
        "saturation_rounds": [
            {
                "round": 1,
                "substantive_novelty": False,
                "changed_claim_ids": [],
                "stop_reason": "无实质新增，待连续第二轮确认",
            },
            {
                "round": 2,
                "substantive_novelty": False,
                "changed_claim_ids": [],
                "stop_reason": "连续两轮无实质新增",
            },
        ],
        "network_available": True,
        "completed_at": STAMP,
    }


def red_team_report() -> dict[str, Any]:
    locked_recommendation = recommendation()
    problem_key_sha256 = stance_neutral_problem()["semantic_key_sha256"]
    central_statement_sha256 = fixture_sha256_json(CENTRAL_STATEMENT)
    pro_prompt = "请赞成中心命题，但只能使用冻结证据。"
    anti_prompt = "请反对中心命题，但只能使用冻结证据。"
    return {
        "schema_id": "crossframe.promax.v8.red-team-report",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-CENTRAL",
        "attacks": [
            {
                "attack_id": "ATTACK-1",
                "attack_class": "object_reification",
                "target_id": "CLAIM-CENTRAL",
                "challenge": "对象是否因命名而被实体化？",
                "counterevidence_refs": ["EVIDENCE-2"],
                "strongest_counterposition": "对象边界并不稳定。",
                "result": "survived_with_revision",
                "revision": "降低判断强度并增加边界重置条件。",
                "position_impact": "medium",
            }
        ],
        "stability_checks": [
            {
                "prompt_pair_id": "PAIR-1",
                "pro_prompt": pro_prompt,
                "anti_prompt": anti_prompt,
                "pro_prompt_sha256": fixture_sha256_json(pro_prompt),
                "anti_prompt_sha256": fixture_sha256_json(anti_prompt),
                "evidence_basis_sha256_before": HASH_C,
                "evidence_basis_sha256_after": HASH_C,
                "semantic_problem_sha256_before": problem_key_sha256,
                "semantic_problem_sha256_after": problem_key_sha256,
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
                "option_kind_ranking_before": [*HOUSE_OPTION_KIND_RANKING],
                "option_kind_ranking_after": [*HOUSE_OPTION_KIND_RANKING],
                "option_semantic_ranking_before": [
                    *locked_recommendation["option_semantic_ranking"]
                ],
                "option_semantic_ranking_after": [
                    *locked_recommendation["option_semantic_ranking"]
                ],
                "normative_selection_basis_sha256_before": HASH_D,
                "normative_selection_basis_sha256_after": HASH_D,
                "position_drift": "none",
                "explanation": "材料未变，中心判断不随用户表态漂移。",
            }
        ],
        "revision_summary": ["增加对象边界撤回条件"],
        "completed_at": STAMP,
    }


def position() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.position",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "central_claim_id": "CLAIM-CENTRAL",
        "relation_to_proposition": "supports",
        "proposition_verdict": f"VERDICT[supports] {CENTRAL_STATEMENT}",
        "position": f"VERDICT[supports] {CENTRAL_STATEMENT} 当前条件下机制甲最合理。",
        "judgment_strength": "moderate",
        "primary_reasons": ["机制甲解释更多已知结构"],
        "runner_up_explanation": "机制乙在边界变化时成为次优解释。",
        "strongest_counterevidence": ["对象边界可能不稳定"],
        "why_not_adopted": ["现有材料尚未显示边界已失效"],
        "withdrawal_conditions": ["新证据证明对象边界不可维持"],
        "action_ceiling": "仅支持条件化建议，不授权现实处置",
        "locked_at": STAMP,
    }


def selection_review_wrapper(
    *,
    option_ids: list[str],
    evaluation_dimensions: list[str],
    preferred_option_id: str,
) -> dict[str, Any]:
    principle_review = {
        "principle_version": "v8",
        "selected_option_id": preferred_option_id,
        "compared_option_ids": [*option_ids],
        "evaluation_dimensions": [*evaluation_dimensions],
        "sufficient_reason": "低信息条件下仅形成待复核的可逆探针偏好。",
        "evidence_refs": [],
        "reviewer_ref": "REVIEWER-INDEPENDENT-1",
        "reviewed_at": STAMP,
        "status": "pending",
    }
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
            "reviewed_option_id": preferred_option_id,
            "decision_actor_ref": "UNRESOLVED-DECISION-ACTOR",
            "authorization_source_ref": "UNRESOLVED-AUTHORIZATION-SOURCE",
            "jurisdiction_ref": "UNRESOLVED-JURISDICTION",
            "scope": "analysis_only",
            "valid_from": STAMP,
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
            **principle_review,
            "principle_id": "NSP-LEAST-HARM",
        },
        "proportionality": {
            **principle_review,
            "principle_id": "NSP-PROPORTIONALITY",
        },
        "declared_low_information_house_policy_eligibility": {
            "case_specific_facts_present": False,
            "choice_changing_retrieval_evidence_present": False,
            "basis": "没有个案事实或改变选择的检索证据。",
        },
        "ranking_support": [],
    }


def recommendation() -> dict[str, Any]:
    option_kinds = (
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
            "option_kind": option_kind,
            "description": f"方案 {index}",
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
            "stop_conditions": ["风险超过上限"],
            "rollback_and_remedy": ["回到冻结状态并修复损害"],
        }
        for index, (option_kind, option_id) in enumerate(option_kinds, start=1)
    ]
    options_by_id = {option["option_id"]: option for option in options}
    evaluation_dimensions = ["结构解释力", "可逆性", "风险"]
    return {
        "schema_id": "crossframe.promax.v8.recommendation",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "position_sha256": HASH_A,
        "options": options,
        "evaluation_dimensions": evaluation_dimensions,
        "ranking": [*HOUSE_OPTION_RANKING],
        "ranking_policy": "promax_low_information_house_policy_not_v8",
        "ranking_evidence_refs": [],
        "selection_review_wrapper": selection_review_wrapper(
            option_ids=list(options_by_id),
            evaluation_dimensions=evaluation_dimensions,
            preferred_option_id="OPTION-PROBE",
        ),
        "option_kind_ranking": [
            options_by_id[option_id]["option_kind"]
            for option_id in HOUSE_OPTION_RANKING
        ],
        "option_record_hashes": [
            {"option_id": option_id, "record_sha256": fixture_sha256_json(option)}
            for option_id, option in options_by_id.items()
        ],
        "option_semantic_ranking": [
            fixture_sha256_json(
                {
                    key: value
                    for key, value in options_by_id[option_id].items()
                    if key != "option_id"
                }
            )
            for option_id in HOUSE_OPTION_RANKING
        ],
        "preferred_option_id": "OPTION-PROBE",
        "second_option_id": "OPTION-ACTIVE",
        "no_action_option_id": "OPTION-NO-ACTION",
        "switch_conditions": ["边界失效时切换到 OPTION-ACTIVE"],
        "inaction_consequences": ["机会成本继续累积"],
        "authorization_status": "conditional_recommendation_only",
        "locked_at": STAMP,
    }


def output_plan() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.output-plan",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "sections": [
            {
                "section_id": "SECTION-1",
                "title": "中心判断",
                "concept_ids": ["V8-CANON-OBJECT"],
                "claim_ids": ["CLAIM-CENTRAL"],
                "example_ids": ["EXAMPLE-1", "EXAMPLE-2"],
                "counterexample_ids": ["COUNTEREXAMPLE-1"],
                "judgment_ids": ["POSITION-1"],
                "artifact_paths": ["promax-essay.md"],
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


def continuation_ledger() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.continuation-ledger",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "parent_manifest_sha256": HASH_A,
        "continuations": [
            {
                "continuation_id": "CONT-1",
                "sequence": 1,
                "parent_artifact_sha256": HASH_B,
                "resume_from_phase": "P10",
                "pending_artifact_paths": ["promax-essay-part-2.md"],
                "reason": "平台输出边界先耗尽",
                "status": "pending",
            }
        ],
        "updated_at": STAMP,
    }


def artifact_manifest() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.artifact-manifest",
        "schema_version": 1,
        "run_id": RUN_ID,
        "run_nonce": RUN_NONCE,
        "request_sha256": HASH_A,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "run_contract_sha256": HASH_A,
        "mode": "promax-complete",
        "orchestration_mode": "multi-agent-isolated",
        "role_records": [
            role_record(role_id, index, "multi-agent-isolated")
            for index, role_id in enumerate(ROLE_IDS, start=1)
        ],
        "phase_chain_head_sha256": HASH_B,
        "artifacts": [
            {
                "path": "promax-position.locked.json",
                "sha256": HASH_C,
                "media_type": "application/json",
                "generating_phase": "P8",
                "input_artifact_sha256s": [HASH_A, HASH_B],
                "status": "current",
            }
        ],
        "generated_at": STAMP,
        "manifest_sha256": HASH_D,
    }


def validator_report() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.validator-report",
        "schema_version": 1,
        "run_id": RUN_ID,
        "run_nonce": RUN_NONCE,
        "request_sha256": HASH_A,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "phase_chain_head_sha256": HASH_B,
        "manifest_sha256": HASH_C,
        "validator_set_sha256": HASH_D,
        "validation_attempt": 1,
        "current_artifact_hashes": [
            artifact("promax-position.locked.json", HASH_A),
            artifact("promax-essay.md", HASH_B),
        ],
        "checks": [
            {
                "validator_id": "source-integrity",
                "status": "pass",
                "checked_artifact_paths": ["promax-source-snapshot.json"],
                "failure_codes": [],
            }
        ],
        "overall_status": "pass",
        "completion_status": "promax-complete",
        "validated_at": STAMP,
        "report_sha256": HASH_A,
    }


def repair_plan() -> dict[str, Any]:
    return {
        "schema_id": "crossframe.promax.v8.repair-plan",
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_snapshot_sha256": SOURCE_SNAPSHOT_SHA256,
        "failed_report_sha256": HASH_A,
        "failures": [
            {
                "error_type": "stale_position",
                "artifact": "promax-position.locked.json",
                "affected_phase": "P8",
                "downstream_reset": ["P8", "P9", "P10", "P11"],
                "repair_action": "rebuild_position_and_downstream",
            }
        ],
        "reset_from_phase": "P8",
        "invalidated_phases": ["P8", "P9", "P10", "P11"],
        "repair_actions": [
            {
                "action_id": "REPAIR-1",
                "phase_id": "P8",
                "description": "重新冻结立场并重建下游产物",
                "expected_output_paths": ["promax-position.locked.json"],
            }
        ],
        "validation_state": "not_run",
        "manifest_regeneration_required": True,
        "revalidation_required": True,
        "revalidation_scope": "full-validator-set",
        "created_at": STAMP,
    }


def minimal_instances() -> dict[str, dict[str, Any]]:
    return {
        "promax-artifact-manifest.schema.json": artifact_manifest(),
        "promax-claim-path-graph.schema.json": claim_path_graph(),
        "promax-concept-disposition.schema.json": concept_disposition(),
        "promax-continuation-ledger.schema.json": continuation_ledger(),
        "promax-local-world-model.schema.json": local_world_model(),
        "promax-output-plan.schema.json": output_plan(),
        "promax-phase-event.schema.json": phase_event(),
        "promax-position.schema.json": position(),
        "promax-read-event.schema.json": read_event(),
        "promax-recommendation.schema.json": recommendation(),
        "promax-red-team-report.schema.json": red_team_report(),
        "promax-repair-plan.schema.json": repair_plan(),
        "promax-retrieval-ledger.schema.json": retrieval_ledger(),
        "promax-run-contract.schema.json": run_contract(),
        "promax-source-snapshot.schema.json": source_snapshot(),
        "promax-validator-report.schema.json": validator_report(),
    }


def walk_dict_paths(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(value, dict):
        yield path
        for key, child in value.items():
            yield from walk_dict_paths(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_dict_paths(child, path + (index,))


def dict_at(value: Any, path: tuple[Any, ...]) -> dict[str, Any]:
    cursor = value
    for part in path:
        cursor = cursor[part]
    if not isinstance(cursor, dict):
        raise AssertionError(f"path is not an object: {path!r}")
    return cursor


def walk_schema_nodes(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_schema_nodes(child)


class ProMaxRuntimeSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = load_runtime_module()

    def assertValid(self, schema_name: str, instance: Any) -> None:
        try:
            self.runtime.validate_instance(schema_name, instance)
        except ValidationError as error:
            self.fail(f"{schema_name} rejected valid instance: {error.message}")

    def assertInvalid(self, schema_name: str, instance: Any) -> None:
        with self.assertRaises(ValidationError, msg=schema_name):
            self.runtime.validate_instance(schema_name, instance)

    def test_exact_runtime_schema_inventory_and_ids(self) -> None:
        actual = tuple(
            sorted(
                path.name
                for path in SCHEMA_DIR.glob("promax-*.schema.json")
                if path.is_file()
            )
        )
        self.assertEqual(actual, EXPECTED_RUNTIME_SCHEMAS)
        self.assertEqual(
            tuple(self.runtime.available_schema_names()),
            tuple(sorted(path.name for path in SCHEMA_DIR.glob("*.schema.json"))),
        )
        for name, expected_id in EXPECTED_SCHEMA_IDS.items():
            with self.subTest(schema=name):
                self.assertEqual(self.runtime.load_schema(name)["$id"], expected_id)

    def test_all_runtime_schemas_are_valid_draft_2020_12_and_closed(self) -> None:
        for name in EXPECTED_RUNTIME_SCHEMAS:
            schema = self.runtime.load_schema(name)
            with self.subTest(schema=name):
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                Draft202012Validator.check_schema(schema)
                for node in walk_schema_nodes(schema):
                    if node.get("type") == "object":
                        additional = node.get("additionalProperties")
                        if additional is False:
                            continue
                        self.assertEqual(
                            node.get("propertyNames"),
                            {"$ref": "#/$defs/relativePath"},
                            f"open object schema in {name}: {json.dumps(node)[:240]}",
                        )
                        self.assertEqual(
                            additional,
                            {"$ref": "#/$defs/sha256"},
                            f"untyped object values in {name}: {json.dumps(node)[:240]}",
                        )

    def test_loader_builds_offline_registry_and_resolves_all_local_refs(self) -> None:
        registry = self.runtime.build_registry()
        self.assertIsNotNone(registry)
        for name, instance in minimal_instances().items():
            with self.subTest(schema=name):
                validator = self.runtime.validator_for(name)
                self.assertIsInstance(validator, Draft202012Validator)
                self.assertEqual(list(validator.iter_errors(instance)), [])

    def test_runtime_validator_enforces_declared_date_time_date_and_uri_formats(self) -> None:
        bad_timestamp = source_snapshot()
        bad_timestamp["verified_at"] = "2026-99-99 25:61"
        self.assertInvalid("promax-source-snapshot.schema.json", bad_timestamp)

        bad_date = retrieval_ledger()
        bad_date["entries"][0]["sources"][0]["published_at"] = "2026-02-30"
        self.assertInvalid("promax-retrieval-ledger.schema.json", bad_date)

        bad_uri = retrieval_ledger()
        bad_uri["entries"][0]["sources"][0]["url"] = "not a URI"
        self.assertInvalid("promax-retrieval-ledger.schema.json", bad_uri)

        bad_created_at = run_contract()
        bad_created_at["created_at"] = "2026-07-23T00:00:00"
        self.assertInvalid("promax-run-contract.schema.json", bad_created_at)

        bad_cutoff = local_world_model()
        bad_cutoff["evidence_cutoff"] = "2026-07-23T00:00:00"
        self.assertInvalid("promax-local-world-model.schema.json", bad_cutoff)

    def test_pattern_bound_hashes_ids_names_and_files_reject_line_terminator_suffixes(self) -> None:
        for suffix in ("\n", "\r", "\u2028"):
            cases: list[tuple[str, dict[str, Any]]] = []

            bad_hash = run_contract()
            bad_hash["request_sha256"] = HASH_A + suffix
            cases.append(("promax-run-contract.schema.json", bad_hash))

            bad_run_id = run_contract()
            bad_run_id["run_id"] = RUN_ID + suffix
            cases.append(("promax-run-contract.schema.json", bad_run_id))

            bad_nonce = run_contract()
            bad_nonce["run_nonce"] = RUN_NONCE + suffix
            cases.append(("promax-run-contract.schema.json", bad_nonce))

            bad_snapshot_name = source_snapshot()
            bad_snapshot_name["snapshot_id"] += suffix
            cases.append(("promax-source-snapshot.schema.json", bad_snapshot_name))

            bad_read_id = read_event()
            bad_read_id["event_id"] += suffix
            cases.append(("promax-read-event.schema.json", bad_read_id))

            bad_anchor = read_event()
            bad_anchor["source_anchor"] += suffix
            cases.append(("promax-read-event.schema.json", bad_anchor))

            bad_source_file = read_event()
            bad_source_file["source_file"] += suffix
            cases.append(("promax-read-event.schema.json", bad_source_file))

            bad_route_id = concept_disposition()
            bad_route_id["route_ids"][0] += suffix
            cases.append(("promax-concept-disposition.schema.json", bad_route_id))

            bad_actor_id = local_world_model()
            bad_actor_id["actor_records"][0]["actor_id"] += suffix
            cases.append(("promax-local-world-model.schema.json", bad_actor_id))

            bad_claim_id = claim_path_graph()
            bad_claim_id["central_claim_id"] += suffix
            cases.append(("promax-claim-path-graph.schema.json", bad_claim_id))

            for schema_name, instance in cases:
                with self.subTest(schema=schema_name, suffix=repr(suffix)):
                    self.assertInvalid(schema_name, instance)

    def test_artifact_paths_are_canonical_relative_posix_in_refs_and_hash_maps(self) -> None:
        common = self.runtime.load_schema("promax-common.schema.json")
        relative_path = common["$defs"]["relativePath"]
        artifact_hash_map = common["$defs"]["artifactHashMap"]
        self.assertEqual(relative_path["format"], "promax-relative-path")
        self.assertEqual(
            artifact_hash_map["propertyNames"],
            {"$ref": "#/$defs/relativePath"},
        )
        self.assertNotIn("patternProperties", artifact_hash_map)

        invalid_paths = (
            "artifacts/trailing-dot.",
            "artifacts/trailing-space ",
            "artifacts/segment./file.json",
            "artifacts/segment /file.json",
            ".",
            "..",
            "./artifact.json",
            "artifacts/./file.json",
            "artifacts/../file.json",
            "artifacts//file.json",
            "artifacts/",
            "/artifacts/file.json",
            "C:x.json",
            "C:/x.json",
            "artifacts/name:stream",
            "artifacts\\file.json",
            " ",
            "artifacts/file\n.json",
            "artifacts/file\x00.json",
            "artifacts/file\x1f.json",
            "artifacts/file\x7f.json",
            "artifacts/file\x85.json",
            "artifacts/file\u200b.json",
            "artifacts/file\u200d.json",
            "artifacts/file\u2028.json",
            "artifacts/file\u2029.json",
            "artifacts/file\u202e.json",
            "artifacts/file\ufeff.json",
            "artifacts/cafe\u0301.json",
            "artifacts/hidden-reasoning.json",
            "artifacts/private/scratchpad.json",
            "CON.json",
            "artifacts/prn.txt",
            "artifacts/AUX.log",
            "artifacts/nul",
            "artifacts/clock$.json",
            "artifacts/conin$.txt",
            "artifacts/CONOUT$.txt",
            *(f"artifacts/COM{number}.json" for number in range(1, 10)),
            *(f"artifacts/lpt{number}.json" for number in range(1, 10)),
        )
        for bad_path in invalid_paths:
            manifest = artifact_manifest()
            manifest["artifacts"][0]["path"] = bad_path
            event = phase_event()
            event["output_artifact_hashes"] = {bad_path: HASH_B}
            with self.subTest(path=repr(bad_path), surface="relativePath"):
                self.assertInvalid("promax-artifact-manifest.schema.json", manifest)
            with self.subTest(path=repr(bad_path), surface="artifactHashMap"):
                self.assertInvalid("promax-phase-event.schema.json", event)

        valid_paths = (
            "promax-run-contract.json",
            "artifacts/p8/promax-position.locked.json",
            "artifacts/.metadata.json",
            "artifacts/a..b/structure_evidence-01.json",
            "artifacts/结构-证据_01.json",
            "artifacts/caf\u00e9.json",
            "artifacts/com10.json",
            "artifacts/lpt10.json",
            "artifacts/context.json",
        )
        for valid_path in valid_paths:
            manifest = artifact_manifest()
            manifest["artifacts"][0]["path"] = valid_path
            event = phase_event()
            event["output_artifact_hashes"] = {valid_path: HASH_B}
            with self.subTest(path=valid_path, surface="relativePath"):
                self.assertValid("promax-artifact-manifest.schema.json", manifest)
            with self.subTest(path=valid_path, surface="artifactHashMap"):
                self.assertValid("promax-phase-event.schema.json", event)

    def test_unknown_schema_names_and_path_traversal_are_rejected(self) -> None:
        for name in (
            "missing.schema.json",
            "../promax-run-contract.schema.json",
            "promax-run-contract.schema.json/extra",
            "",
        ):
            with self.subTest(name=name):
                with self.assertRaises((KeyError, ValueError)):
                    self.runtime.load_schema(name)

    def test_run_contract_allows_exactly_four_modes(self) -> None:
        schema = self.runtime.load_schema("promax-run-contract.schema.json")
        mode_schema = schema["properties"]["mode"]
        self.assertEqual(set(mode_schema["enum"]), ALLOWED_MODES)
        self.assertEqual(len(mode_schema["enum"]), 4)
        for mode in ALLOWED_MODES:
            with self.subTest(mode=mode):
                self.assertValid(
                    "promax-run-contract.schema.json", run_contract(mode=mode)
                )
        for forbidden in (
            "brief",
            "fast",
            "promax-brief",
            "promax-lite",
            "self-downgrade",
            "crossframe-max",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertInvalid(
                    "promax-run-contract.schema.json", run_contract(mode=forbidden)
                )

    def test_blocked_progress_requires_one_authorized_blocker_and_no_other_mode_accepts_it(self) -> None:
        blocked = run_contract(mode="promax-blocked/progress")
        self.assertValid("promax-run-contract.schema.json", blocked)

        missing = copy.deepcopy(blocked)
        missing["blocker"] = None
        self.assertInvalid("promax-run-contract.schema.json", missing)

        for category in (
            "source_unavailable",
            "filesystem_unwritable",
            "required_tool_forbidden",
            "user_stopped",
            "safety_boundary",
        ):
            candidate = copy.deepcopy(blocked)
            candidate["blocker"]["category"] = category
            with self.subTest(category=category):
                self.assertValid("promax-run-contract.schema.json", candidate)

        invented = copy.deepcopy(blocked)
        invented["blocker"]["category"] = "budget_exhausted"
        self.assertInvalid("promax-run-contract.schema.json", invented)

        empty_detail = copy.deepcopy(blocked)
        empty_detail["blocker"]["detail"] = ""
        self.assertInvalid("promax-run-contract.schema.json", empty_detail)

        self_downgrade = run_contract(mode="promax-artifact-run")
        self_downgrade["blocker"] = copy.deepcopy(blocked["blocker"])
        self.assertInvalid("promax-run-contract.schema.json", self_downgrade)

    def test_run_contract_freezes_both_routing_conflict_branches(self) -> None:
        single = run_contract(conflict=False)
        both = run_contract(conflict=True)
        self.assertValid("promax-run-contract.schema.json", single)
        self.assertValid("promax-run-contract.schema.json", both)

        missed = copy.deepcopy(both)
        missed["routing_conflict"]["detected"] = False
        self.assertInvalid("promax-run-contract.schema.json", missed)

        omitted = copy.deepcopy(both)
        omitted["routing_conflict"]["conflicting_names"] = ["crossframe-promax"]
        self.assertInvalid("promax-run-contract.schema.json", omitted)

        false_conflict = copy.deepcopy(single)
        false_conflict["routing_conflict"]["detected"] = True
        false_conflict["routing_conflict"]["conflicting_names"] = [
            "crossframe-promax",
            "crossframe-max",
        ]
        self.assertInvalid("promax-run-contract.schema.json", false_conflict)

        for field, bad_value in (
            ("resolved_to", "crossframe-max"),
            ("priority_rule", "crossframe-max-over-crossframe-promax"),
            ("fallback_allowed", True),
        ):
            broken = copy.deepcopy(both)
            broken["routing_conflict"][field] = bad_value
            with self.subTest(field=field):
                self.assertInvalid("promax-run-contract.schema.json", broken)

        newline_alias = copy.deepcopy(both)
        newline_alias["requested_skill_names"][1] = "crossframe-max\n"
        newline_alias["routing_conflict"]["conflicting_names"][1] = "crossframe-max\n"
        self.assertInvalid("promax-run-contract.schema.json", newline_alias)

    def test_run_contract_requires_a_boolean_recommendation_request_switch(self) -> None:
        requested = run_contract()
        requested["recommendation_required"] = True
        self.assertValid("promax-run-contract.schema.json", requested)

        not_requested = run_contract()
        not_requested["recommendation_required"] = False
        self.assertValid("promax-run-contract.schema.json", not_requested)

        missing = run_contract()
        del missing["recommendation_required"]
        self.assertInvalid("promax-run-contract.schema.json", missing)

        wrong_type = run_contract()
        wrong_type["recommendation_required"] = "false"
        self.assertInvalid("promax-run-contract.schema.json", wrong_type)

    def test_recommendation_schema_has_an_exact_closed_not_requested_branch(self) -> None:
        self.assertValid(
            "promax-recommendation.schema.json",
            {"status": "not_requested"},
        )
        self.assertValid("promax-recommendation.schema.json", recommendation())
        self.assertInvalid(
            "promax-recommendation.schema.json",
            {"status": "not_requested", "advice": "不得夹带建议"},
        )
        self.assertInvalid(
            "promax-recommendation.schema.json",
            {"status": "requested"},
        )

    def test_recommendation_schema_closes_the_selection_review_wrapper(self) -> None:
        valid = recommendation()
        cases: list[dict[str, Any]] = []

        missing = copy.deepcopy(valid)
        del missing["selection_review_wrapper"]
        cases.append(missing)

        invented = copy.deepcopy(valid)
        invented["selection_review_wrapper"]["v8_native_schema"] = True
        cases.append(invented)

        system_selection = copy.deepcopy(valid)
        system_selection["selection_review_wrapper"]["selection_type"] = "SEL-SYS"
        cases.append(system_selection)

        execution_started = copy.deepcopy(valid)
        execution_started["selection_review_wrapper"]["procedure_states"]["O4"] = (
            "complete"
        )
        cases.append(execution_started)

        non_v8_floor = copy.deepcopy(valid)
        non_v8_floor["selection_review_wrapper"]["rights_floor"] = ["PF-11"]
        cases.append(non_v8_floor)

        false_house_eligibility = copy.deepcopy(valid)
        false_house_eligibility["selection_review_wrapper"][
            "declared_low_information_house_policy_eligibility"
        ]["case_specific_facts_present"] = True
        cases.append(false_house_eligibility)

        unbound_source = copy.deepcopy(valid)
        unbound_source["selection_review_wrapper"]["source_paragraph_refs"].pop()
        cases.append(unbound_source)

        for candidate in cases:
            with self.subTest(candidate=candidate):
                self.assertInvalid(
                    "promax-recommendation.schema.json",
                    candidate,
                )

    def test_capability_disclosure_is_structured_and_exact(self) -> None:
        valid = run_contract()
        self.assertEqual(
            set(valid["capabilities"]),
            {"files", "network", "subagents", "validators"},
        )
        self.assertValid("promax-run-contract.schema.json", valid)
        for key in ("files", "network", "subagents", "validators"):
            missing = copy.deepcopy(valid)
            del missing["capabilities"][key]
            with self.subTest(missing=key):
                self.assertInvalid("promax-run-contract.schema.json", missing)
        free_text = copy.deepcopy(valid)
        free_text["capabilities"]["network"] = "available"
        self.assertInvalid("promax-run-contract.schema.json", free_text)

    def test_role_plan_matches_subagent_capability_without_fabricating_outputs(self) -> None:
        multi = run_contract(subagents=True)
        single = run_contract(subagents=False)
        self.assertValid("promax-run-contract.schema.json", multi)
        self.assertValid("promax-run-contract.schema.json", single)
        self.assertEqual({record["role_id"] for record in multi["role_plan"]}, set(ROLE_IDS))
        for planned in multi["role_plan"]:
            self.assertNotIn("status", planned)
            self.assertNotIn("input_artifacts", planned)
            self.assertNotIn("output_artifacts", planned)

        skipped = copy.deepcopy(multi)
        skipped["role_plan"].pop()
        self.assertInvalid("promax-run-contract.schema.json", skipped)

        duplicated = copy.deepcopy(multi)
        duplicated["role_plan"][-1] = copy.deepcopy(duplicated["role_plan"][0])
        self.assertInvalid("promax-run-contract.schema.json", duplicated)

        false_isolation = copy.deepcopy(multi)
        false_isolation["orchestration_mode"] = "single-agent-separated"
        for record in false_isolation["role_plan"]:
            record["execution_mode"] = "single-agent-separated"
        self.assertInvalid("promax-run-contract.schema.json", false_isolation)

        false_independence = copy.deepcopy(single)
        false_independence["orchestration_mode"] = "multi-agent-isolated"
        for record in false_independence["role_plan"]:
            record["execution_mode"] = "multi-agent-isolated"
        self.assertInvalid("promax-run-contract.schema.json", false_independence)

        unstructured = copy.deepcopy(multi)
        unstructured["role_plan"][1]["free_memory_summary"] = "trust me"
        self.assertInvalid("promax-run-contract.schema.json", unstructured)

        wrong_protocol = copy.deepcopy(multi)
        wrong_protocol["role_plan"][1]["exchange_protocol"] = "free-memory-summary"
        self.assertInvalid("promax-run-contract.schema.json", wrong_protocol)

    def test_manifest_records_actual_structured_role_exchanges(self) -> None:
        valid = artifact_manifest()
        self.assertValid("promax-artifact-manifest.schema.json", valid)
        self.assertEqual({record["role_id"] for record in valid["role_records"]}, set(ROLE_IDS))

        skipped = copy.deepcopy(valid)
        skipped["role_records"].pop()
        self.assertInvalid("promax-artifact-manifest.schema.json", skipped)

        unstructured = copy.deepcopy(valid)
        unstructured["role_records"][1]["free_memory_summary"] = "trust me"
        self.assertInvalid("promax-artifact-manifest.schema.json", unstructured)

        wrong_protocol = copy.deepcopy(valid)
        wrong_protocol["role_records"][1]["exchange_protocol"] = "free-memory-summary"
        self.assertInvalid("promax-artifact-manifest.schema.json", wrong_protocol)

        observed_unhashed = copy.deepcopy(valid)
        del observed_unhashed["role_records"][0]["observed_input_artifacts"][0][
            "sha256"
        ]
        self.assertInvalid("promax-artifact-manifest.schema.json", observed_unhashed)

        undeclared_but_structured = copy.deepcopy(valid)
        undeclared_but_structured["role_records"][0]["observed_input_artifacts"] = [
            artifact("undeclared.json", HASH_D)
        ]
        self.assertValid(
            "promax-artifact-manifest.schema.json", undeclared_but_structured
        )

    def test_source_snapshot_is_exactly_v8_and_not_a_lineage_alias(self) -> None:
        valid = source_snapshot()
        self.assertValid("promax-source-snapshot.schema.json", valid)
        for field, bad_value in (
            ("framework_version", "v7.0"),
            ("source_snapshot_sha256", HASH_A),
            ("paragraph_count", 3862),
            ("table_count", 116),
            ("section_count", 15),
        ):
            broken = copy.deepcopy(valid)
            broken[field] = bad_value
            with self.subTest(field=field):
                self.assertInvalid("promax-source-snapshot.schema.json", broken)

    def test_p3_world_model_requires_every_frozen_structure(self) -> None:
        schema = self.runtime.load_schema("promax-local-world-model.schema.json")
        required = set(schema["required"])
        expected = {
            "object_boundary",
            "actor_records",
            "circle_candidates",
            "scale_profile",
            "material_channel",
            "experiential_meaning_channel",
            "M_state",
            "Psi_state",
            "clocks",
            "events",
            "evidence_cutoff",
            "unknowns",
            "residuals",
            "identity_criteria",
            "action_limits",
            "authorization_limits",
        }
        self.assertTrue(expected.issubset(required))
        valid = local_world_model()
        self.assertValid("promax-local-world-model.schema.json", valid)
        for field in expected:
            broken = copy.deepcopy(valid)
            del broken[field]
            with self.subTest(missing=field):
                self.assertInvalid("promax-local-world-model.schema.json", broken)

    def test_validator_report_binds_every_anti_replay_input(self) -> None:
        required = {
            "run_id",
            "run_nonce",
            "request_sha256",
            "source_snapshot_sha256",
            "phase_chain_head_sha256",
            "manifest_sha256",
            "validator_set_sha256",
            "validation_attempt",
            "current_artifact_hashes",
        }
        schema = self.runtime.load_schema("promax-validator-report.schema.json")
        self.assertTrue(required.issubset(set(schema["required"])))
        valid = validator_report()
        self.assertValid("promax-validator-report.schema.json", valid)
        for field in required:
            broken = copy.deepcopy(valid)
            del broken[field]
            with self.subTest(missing=field):
                self.assertInvalid("promax-validator-report.schema.json", broken)
        replay = copy.deepcopy(valid)
        replay["run_nonce"] = "old"
        self.assertInvalid("promax-validator-report.schema.json", replay)

    def test_validator_report_overall_status_matches_individual_checks(self) -> None:
        valid = validator_report()
        self.assertValid("promax-validator-report.schema.json", valid)

        pass_with_failure = copy.deepcopy(valid)
        pass_with_failure["checks"][0]["status"] = "fail"
        pass_with_failure["checks"][0]["failure_codes"] = ["SOURCE_STALE"]
        self.assertInvalid("promax-validator-report.schema.json", pass_with_failure)

        fail_without_failure = copy.deepcopy(valid)
        fail_without_failure["overall_status"] = "fail"
        fail_without_failure["completion_status"] = "promax-artifact-incomplete:validation-failed"
        self.assertInvalid("promax-validator-report.schema.json", fail_without_failure)

        blocked_without_blocked_check = copy.deepcopy(valid)
        blocked_without_blocked_check["overall_status"] = "blocked"
        blocked_without_blocked_check["completion_status"] = "promax-blocked/progress"
        self.assertInvalid(
            "promax-validator-report.schema.json", blocked_without_blocked_check
        )

        blocked_with_failure = copy.deepcopy(valid)
        blocked_with_failure["overall_status"] = "blocked"
        blocked_with_failure["completion_status"] = "promax-blocked/progress"
        blocked_with_failure["checks"][0]["status"] = "blocked"
        blocked_with_failure["checks"][0]["failure_codes"] = ["TOOL_BLOCKED"]
        failed_check = copy.deepcopy(blocked_with_failure["checks"][0])
        failed_check["validator_id"] = "state-machine"
        failed_check["status"] = "fail"
        failed_check["failure_codes"] = ["STATE_INVALID"]
        blocked_with_failure["checks"].append(failed_check)
        self.assertInvalid(
            "promax-validator-report.schema.json", blocked_with_failure
        )

    def test_substantive_strings_reject_whitespace_only_values(self) -> None:
        cases: list[tuple[str, dict[str, Any]]] = []

        blocked = run_contract(mode="promax-blocked/progress")
        blocked["blocker"]["detail"] = " \t\n"
        cases.append(("promax-run-contract.schema.json", blocked))

        concept = concept_disposition()
        concept["dispositions"][0]["rationale"] = " \t"
        cases.append(("promax-concept-disposition.schema.json", concept))

        graph = claim_path_graph()
        graph["claims"][0]["statement"] = "\n\t"
        cases.append(("promax-claim-path-graph.schema.json", graph))

        world = local_world_model()
        world["object_boundary"]["name"] = " \u2028"
        cases.append(("promax-local-world-model.schema.json", world))

        attack = red_team_report()
        attack["attacks"][0]["challenge"] = "   "
        cases.append(("promax-red-team-report.schema.json", attack))

        locked_position = position()
        locked_position["position"] = "\t\n"
        cases.append(("promax-position.schema.json", locked_position))

        rec = recommendation()
        rec["options"][0]["description"] = "  "
        cases.append(("promax-recommendation.schema.json", rec))

        repair = repair_plan()
        repair["repair_actions"][0]["description"] = "\r\n"
        cases.append(("promax-repair-plan.schema.json", repair))

        retrieval = retrieval_ledger()
        retrieval["entries"][0]["finding"] = "\t"
        cases.append(("promax-retrieval-ledger.schema.json", retrieval))

        for schema_name, instance in cases:
            with self.subTest(schema=schema_name):
                self.assertInvalid(schema_name, instance)

    def test_each_retrieval_query_has_its_own_stop_reason(self) -> None:
        valid = retrieval_ledger()
        self.assertValid("promax-retrieval-ledger.schema.json", valid)
        missing = copy.deepcopy(valid)
        del missing["entries"][0]["stop_reason"]
        self.assertInvalid("promax-retrieval-ledger.schema.json", missing)

    def test_claim_cycle_is_explicit_closed_and_substantive(self) -> None:
        self.assertValid("promax-claim-path-graph.schema.json", claim_path_graph())
        missing = claim_path_graph()
        missing.pop("central_claim_cycle")
        self.assertInvalid("promax-claim-path-graph.schema.json", missing)

        hidden = claim_path_graph()
        hidden["central_claim_cycle"]["phase_marker"] = "initial-attack-revision"
        self.assertInvalid("promax-claim-path-graph.schema.json", hidden)

        blank = claim_path_graph()
        blank["central_claim_cycle"]["strongest_attack"] = " "
        self.assertInvalid("promax-claim-path-graph.schema.json", blank)

    def test_retrieval_uses_exact_directions_and_structured_source_relations(self) -> None:
        self.assertValid("promax-retrieval-ledger.schema.json", retrieval_ledger())
        for legacy in ("failure_case", "affected_or_low_power_position"):
            document = retrieval_ledger()
            document["entries"][0]["direction"] = legacy
            with self.subTest(legacy=legacy):
                self.assertInvalid("promax-retrieval-ledger.schema.json", document)

        missing_relation = retrieval_ledger()
        missing_relation["entries"][0].pop("claim_relation")
        self.assertInvalid("promax-retrieval-ledger.schema.json", missing_relation)

        missing_round = retrieval_ledger()
        missing_round["entries"][0].pop("round")
        self.assertInvalid("promax-retrieval-ledger.schema.json", missing_round)

        independent_with_parent = retrieval_ledger()
        source_record = independent_with_parent["entries"][0]["sources"][0]
        source_record["duplicate_of_url"] = "https://example.test/2"
        self.assertInvalid(
            "promax-retrieval-ledger.schema.json", independent_with_parent
        )

        dependent_without_parent = retrieval_ledger()
        source_record = dependent_without_parent["entries"][0]["sources"][0]
        source_record["duplicate_relation"] = "derived"
        self.assertInvalid("promax-retrieval-ledger.schema.json", dependent_without_parent)

    def test_stance_stability_checks_bind_before_and_after_evidence(self) -> None:
        self.assertValid("promax-red-team-report.schema.json", red_team_report())
        for field in (
            "evidence_basis_sha256_before",
            "evidence_basis_sha256_after",
            "pro_prompt",
            "anti_prompt",
        ):
            document = red_team_report()
            document["stability_checks"][0].pop(field)
            with self.subTest(field=field):
                self.assertInvalid("promax-red-team-report.schema.json", document)

    def test_p3_clock_horizon_and_lag_are_strict_iso_8601_durations(self) -> None:
        for duration in ("P90D", "PT6H", "P2W", "P1Y2M3DT4H5M6.5S"):
            valid = local_world_model()
            valid["clocks"][0]["horizon"] = duration
            valid["clocks"][0]["lag"] = duration
            with self.subTest(valid=duration):
                self.assertValid("promax-local-world-model.schema.json", valid)

        for duration in (
            "P",
            "PT",
            "90D",
            "P1Q",
            "P1DT",
            "P1D2H",
            "P1W2D",
            "P-1D",
            "P1.2.3D",
            "P1D\n",
        ):
            invalid = local_world_model()
            invalid["clocks"][0]["horizon"] = duration
            with self.subTest(invalid=repr(duration)):
                self.assertInvalid("promax-local-world-model.schema.json", invalid)

    def test_model_authored_objects_reject_hidden_thought_fields_recursively(self) -> None:
        fixtures = minimal_instances()
        for schema_name in MODEL_AUTHORED_SCHEMAS:
            valid = fixtures[schema_name]
            self.assertValid(schema_name, valid)
            paths = tuple(walk_dict_paths(valid))
            self.assertTrue(paths, schema_name)
            for path in paths:
                broken = copy.deepcopy(valid)
                dict_at(broken, path)["chain_of_thought"] = "hidden reasoning"
                with self.subTest(schema=schema_name, path=path):
                    self.assertInvalid(schema_name, broken)
            for field_name in HIDDEN_THOUGHT_FIELD_NAMES:
                broken = copy.deepcopy(valid)
                broken[field_name] = "hidden reasoning"
                with self.subTest(schema=schema_name, field=field_name):
                    self.assertInvalid(schema_name, broken)

    def test_model_artifact_schemas_have_nontrivial_semantic_contracts(self) -> None:
        expected_required = {
            "promax-concept-disposition.schema.json": {
                "registry_sha256",
                "route_ids",
                "dispositions",
                "unchecked_concept_ids",
                "closure_complete",
            },
            "promax-claim-path-graph.schema.json": {
                "central_claim_id",
                "claims",
                "mechanisms",
                "path_nodes",
                "path_edges",
                "forecast_conditions",
                "choice_boundary",
            },
            "promax-retrieval-ledger.schema.json": {
                "entries",
                "saturation_rounds",
                "network_available",
            },
            "promax-red-team-report.schema.json": {
                "central_claim_id",
                "attacks",
                "stability_checks",
                "revision_summary",
            },
            "promax-position.schema.json": {
                "position",
                "judgment_strength",
                "primary_reasons",
                "runner_up_explanation",
                "strongest_counterevidence",
                "why_not_adopted",
                "withdrawal_conditions",
                "action_ceiling",
            },
            "promax-recommendation.schema.json": {
                "options",
                "evaluation_dimensions",
                "ranking",
                "ranking_policy",
                "ranking_evidence_refs",
                "selection_review_wrapper",
                "option_kind_ranking",
                "option_record_hashes",
                "option_semantic_ranking",
                "preferred_option_id",
                "second_option_id",
                "no_action_option_id",
                "switch_conditions",
                "inaction_consequences",
                "authorization_status",
            },
            "promax-output-plan.schema.json": {
                "sections",
                "required_artifacts",
                "unexpanded_branch_ids",
                "coverage_complete",
            },
            "promax-repair-plan.schema.json": {
                "failed_report_sha256",
                "failures",
                "reset_from_phase",
                "invalidated_phases",
                "repair_actions",
                "validation_state",
                "manifest_regeneration_required",
                "revalidation_required",
                "revalidation_scope",
            },
        }
        fixtures = minimal_instances()
        for schema_name, fields in expected_required.items():
            schema = self.runtime.load_schema(schema_name)
            with self.subTest(schema=schema_name):
                required = schema.get("required")
                if schema_name == "promax-recommendation.schema.json":
                    required = schema["$defs"]["fullRecommendation"]["required"]
                self.assertTrue(fields.issubset(set(required)))
                self.assertValid(schema_name, fixtures[schema_name])


if __name__ == "__main__":
    unittest.main()
