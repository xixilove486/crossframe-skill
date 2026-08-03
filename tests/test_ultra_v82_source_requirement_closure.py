from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills" / "crossframe-ultra"
CONTRACT_ROOT = ULTRA / "references" / "concept-contracts"

M02_FROZEN_REGISTRATION_MATCH_FIELDS = (
    "operator_id",
    "selected_operator_branch",
    "claim_mode",
    "root_subtype",
    "success_criterion_id",
    "d3_e5_mapping_ref",
    "comparison_model_ref",
    "positive_decision_rule_ref",
    "positive_threshold",
    "null_decision_rule_ref",
    "equivalence_or_sufficiency_test_ref",
    "power_or_sensitivity_ref",
    "tolerance_ref",
)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def machine_requirements() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    contract_map = load_json(CONTRACT_ROOT / "v8.2-contract-map.json")
    for entry in contract_map["contracts"]:
        assert isinstance(entry, dict)
        document = load_json(CONTRACT_ROOT / str(entry["file"]))
        for requirement in document.get("machine_requirements", []):
            assert isinstance(requirement, dict)
            requirement_id = requirement["requirement_id"]
            assert isinstance(requirement_id, str)
            assert requirement_id not in result
            result[requirement_id] = requirement
    return result


def load_checker():
    path = ULTRA / "scripts" / "check_crossframe_ultra_v82_knowledge.py"
    spec = importlib.util.spec_from_file_location("ultra_requirement_checker", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_source_and_curated_inventories_stay_layered_and_sp_axes_are_source_exact() -> None:
    source_manifest = load_json(ULTRA / "references" / "source-manifest.json")
    registry = load_json(
        ULTRA / "references" / "concept-registry" / "v8.2-concept-registry.json"
    )
    contract_map = load_json(CONTRACT_ROOT / "v8.2-contract-map.json")

    assert (source_manifest["concept_count"], source_manifest["contract_count"]) == (
        349,
        8,
    )
    assert (registry["concept_count"], contract_map["contract_count"]) == (9, 5)

    requirement = machine_requirements()["V82-REQ-SP-AXES"]
    assert requirement["requirement_type"] == "scale_profile"
    assert requirement["source_refs"] == [
        "V82-P0870",
        "V82-T012",
        "V82-P0875",
        "V82-P0876",
        "V82-P0877",
        "V82-P0878",
        "V82-P0879",
        "V82-P0880",
        "V82-P0881",
        "V82-P0882",
        "V82-P0883",
        "V82-P0884",
        "V82-P0885",
        "V82-P0886",
        "V82-P0887",
        "V82-P0888",
        "V82-P0889",
        "V82-P0890",
        "V82-P0891",
        "V82-P0892",
        "V82-P0893",
        "V82-P0894",
        "V82-P0895",
        "V82-P0896",
        "V82-P0897",
        "V82-P0898",
        "V82-P0899",
        "V82-P0900",
        "V82-P0901",
        "V82-P0902",
        "V82-P0903",
        "V82-P0904",
        "V82-P0905",
        "V82-P0906",
        "V82-P0907",
        "V82-P0908",
        "V82-P0909",
        "V82-P0910",
        "V82-P0911",
        "V82-P0912",
        "V82-P0913",
        "V82-P0914",
        "V82-P0916",
        "V82-P0917",
        "V82-P0918",
        "V82-P0919",
        "V82-P0920",
        "V82-P0921",
        "V82-P0922",
        "V82-P0923",
        "V82-P0924",
    ]
    assert "V82-T012" in requirement["source_refs"]
    assert requirement["axes"] == [
        {
            "axis_id": "A",
            "canonical_zh": "聚合层次",
            "state_field_core": "单位、成员集、分区、聚合规则、权重、排除项",
            "expands_computational_witness": "目标总体覆盖源总体，目标分区是源分区的登记粗化",
            "non_substitution_boundary": "不得由 O、X、I 或 J 替代",
            "source_refs": ["V82-P0875", "V82-P0876", "V82-P0877", "V82-P0878"],
        },
        {
            "axis_id": "X",
            "canonical_zh": "空间范围",
            "state_field_core": "坐标系、空间集合、边界通道、外部连接",
            "expands_computational_witness": "坐标对齐后源空间是真子集",
            "non_substitution_boundary": "不得由 A、O、I 或 J 替代",
            "source_refs": ["V82-P0879", "V82-P0880", "V82-P0881", "V82-P0882"],
        },
        {
            "axis_id": "T",
            "canonical_zh": "时间跨度",
            "state_field_core": "时间基准、窗口角色、起止点、时滞模型",
            "expands_computational_witness": "同一基准与角色下目标区间真包含源区间",
            "non_substitution_boundary": "当前截面和长期路径不能互代",
            "source_refs": ["V82-P0883", "V82-P0884", "V82-P0885", "V82-P0886"],
        },
        {
            "axis_id": "O",
            "canonical_zh": "组织层级",
            "state_field_core": "组织图、版本、节点、包含边、接口、重叠",
            "expands_computational_witness": "同版组织 DAG 中目标节点覆盖源节点祖先闭包",
            "non_substitution_boundary": "组织上位不等于 J 扩大",
            "source_refs": ["V82-P0887", "V82-P0888", "V82-P0889", "V82-P0890"],
        },
        {
            "axis_id": "C",
            "canonical_zh": "因果层次",
            "state_field_core": "因果模型、变量、边、干预语义、抽象映射",
            "expands_computational_witness": "目标模型经语义保持映射覆盖源模型并增加可区分层面",
            "non_substitution_boundary": "层级标签、时序和相关不能代替因果桥",
            "source_refs": ["V82-P0891", "V82-P0892", "V82-P0893", "V82-P0894"],
        },
        {
            "axis_id": "R",
            "canonical_zh": "观察分辨率",
            "state_field_core": "测量协议、可区分类、参数、误差、保护性省略",
            "expands_computational_witness": "目标协议保留源协议全部区分并至少细分一类",
            "non_substitution_boundary": "高分辨率不等于完整或有权行动",
            "source_refs": ["V82-P0895", "V82-P0896", "V82-P0897", "V82-P0898"],
        },
        {
            "axis_id": "I",
            "canonical_zh": "影响范围",
            "state_field_core": "结果、阈值、窗口、受影响位置、效应阶次",
            "expands_computational_witness": "对齐后目标受影响位置集真包含源集合",
            "non_substitution_boundary": "影响和观察均不等于授权",
            "source_refs": ["V82-P0899", "V82-P0900", "V82-P0901", "V82-P0902"],
        },
        {
            "axis_id": "N",
            "canonical_zh": "网络拓扑范围",
            "state_field_core": "图与版本、节点、边、语义、采样边界",
            "expands_computational_witness": "存在语义保持图嵌入且目标覆盖源图",
            "non_substitution_boundary": "网络中心不等于责任中心",
            "source_refs": ["V82-P0903", "V82-P0904", "V82-P0905", "V82-P0906"],
        },
        {
            "axis_id": "J",
            "canonical_zh": "管辖与授权范围",
            "state_field_core": "原子授权元组集合；每个元组固定来源、主体、单一对象、单一动作、地域、期限、撤回、有效性和证据",
            "expands_computational_witness": "目标有效原子元组规范化集合真包含，且每个新增元组有独立有效性见证",
            "non_substitution_boundary": "任何其他轴均不能替代 J；禁止对象集与动作集做笛卡尔积",
            "source_refs": ["V82-P0907", "V82-P0908", "V82-P0909", "V82-P0910"],
        },
    ]
    assert requirement["axis_relations"] == [
        "equal",
        "expands",
        "contracts",
        "incomparable",
        "unknown",
    ]
    assert requirement["transformation_classes"] == [
        "horizontal_or_incomparable",
        "mixed",
        "unresolved",
        "all_equal",
        "elevation",
        "reduction",
    ]
    assert requirement["axis_difference_required_fields"] == [
        "axis_id",
        "source_state",
        "target_state",
        "relation",
        "order_witness",
        "information_loss",
        "uncertainty",
    ]
    assert requirement["order_witness_required_fields"] == [
        "comparator_id",
        "comparator_version",
        "verifier_id",
        "evidence_refs",
        "comparison_payload",
        "comparator_result_ref",
        "verification_artifact_ref",
        "verification_hash",
        "validation_status",
    ]
    assert requirement["order_witness_invariants"] == [
        "non_unknown_requires_closed_valid_witness",
        "unresolvable_witness_forces_unknown",
        "nontrivial_relation_requires_registered_comparator_result",
        "identical_states_may_use_builtin_deep_equality_for_equal",
        "identical_states_cannot_expand_or_contract",
    ]
    serialized = json.dumps(requirement, ensure_ascii=False).casefold()
    for invented_axis in (
        "spatial",
        "temporal",
        "organizational",
        "institutional",
        "informational",
        "relational",
        "risk",
    ):
        assert invented_axis not in serialized

    assert requirement["order_witness_registry_resolution"] == {
        "registry": "axis_comparator_results",
        "match_fields": [
            "axis_id",
            "comparator_id",
            "comparator_version",
            "source_state_sha256",
            "target_state_sha256",
            "relation",
            "verification_hash",
            "validation_status",
        ],
        "unresolvable_relation": "unknown",
        "nontrivial_relation_requires_resolved_result": True,
        "builtin_deep_equality_scope": "identical_states_equal_only",
    }
    assert requirement["partial_order_invariants"] == [
        "normalized_states_are_reflexive",
        "bidirectional_order_implies_same_normalized_equivalence_class",
        "transitivity_requires_composable_intermediate_state_version_and_witness",
        "arbitrary_pairwise_distance_tolerance_cannot_define_equality",
        "expands_requires_composable_semantics_preserving_auxiliary_mappings",
        "auxiliary_mapping_conflict_forces_incomparable_or_unknown",
    ]
    assert requirement["classification_precedence"] == [
        {"condition": "any_incomparable", "classification": "horizontal_or_incomparable"},
        {"condition": "has_expands_and_contracts", "classification": "mixed"},
        {"condition": "any_unknown", "classification": "unresolved"},
        {"condition": "all_equal", "classification": "all_equal"},
        {"condition": "equal_or_expands_with_at_least_one_expands", "classification": "elevation"},
        {"condition": "equal_or_contracts_with_at_least_one_contracts", "classification": "reduction"},
    ]
    assert requirement["j_authorization_tuple_required_fields"] == [
        "source_ref",
        "decision_subject_ref",
        "object_ref",
        "action_ref",
        "jurisdiction",
        "validity_period",
        "revocation_conditions",
        "evidence_refs",
        "independent_review_ref",
    ]
    assert requirement["j_expansion_invariants"] == [
        "only_valid_normalized_atomic_tuples_enter_set_comparison",
        "comparison_payload_lists_complete_new_target_tuples_and_validity_evidence",
        "comparison_payload_aligns_with_j_authorization",
        "multiple_objects_or_actions_require_separate_tuples",
        "strings_ids_claims_control_coverage_or_other_axes_cannot_make_j_expand",
    ]


def test_rcc_and_rac_contracts_are_closed_and_source_faithful() -> None:
    requirements = machine_requirements()
    rcc = requirements["V82-REQ-RCC-RELATION"]
    rac = requirements["V82-REQ-RAC-MEMBERSHIP"]

    assert rcc["requirement_type"] == "rcc_relation"
    assert rcc["source_refs"] == [
        "V82-P1766",
        "V82-P1796",
        "V82-P1797",
        "V82-P1798",
        "V82-P1799",
        "V82-P1800",
        "V82-P1801",
        "V82-P1802",
        "V82-P1803",
        "V82-P1804",
        "V82-P1805",
        "V82-P1806",
        "V82-P1807",
        "V82-P1808",
        "V82-P1813",
        "V82-P1814",
        "V82-P1815",
        "V82-P1816",
        "V82-P1817",
        "V82-P1818",
        "V82-P1819",
        "V82-P1820",
        "V82-P1821",
        "V82-P1822",
        "V82-P1823",
        "V82-P1824",
        "V82-P1825",
        "V82-P1826",
        "V82-P1827",
        "V82-P1828",
        "V82-P1829",
        "V82-P1830",
        "V82-P1831",
        "V82-P1832",
        "V82-P1833",
        "V82-P1834",
        "V82-P1835",
        "V82-P1836",
        "V82-P1837",
        "V82-P1839",
        "V82-P1840",
        "V82-P1841",
    ]
    assert rcc["relation_types"] == ["平行", "嵌套", "重叠", "桥接", "竞争", "临时"]
    assert rcc["relation_definitions"] == [
        {
            "relation_type": "平行",
            "definition": "当前无包含关系",
            "criteria": "共享环境与间接耦合",
            "failure_or_transition": "出现包含、重叠或桥接",
            "source_refs": ["V82-P1813", "V82-P1814", "V82-P1815", "V82-P1816"],
        },
        {
            "relation_type": "嵌套",
            "definition": "明确的成员/合同/管辖/空间包含",
            "criteria": "下行约束与上行聚合损失",
            "failure_or_transition": "K 改变、退出或管辖重构",
            "source_refs": ["V82-P1817", "V82-P1818", "V82-P1819", "V82-P1820"],
        },
        {
            "relation_type": "重叠",
            "definition": "共享部分成员、角色、资源或接口",
            "criteria": "角色冲突和双重计算",
            "failure_or_transition": "共享项消失或转为包含",
            "source_refs": ["V82-P1821", "V82-P1822", "V82-P1823", "V82-P1824"],
        },
        {
            "relation_type": "桥接",
            "definition": "可识别的跨圈层传导接口",
            "criteria": "翻译、过滤、过载和代表权",
            "failure_or_transition": "通道关闭、替代或制度化",
            "source_refs": ["V82-P1825", "V82-P1826", "V82-P1827", "V82-P1828"],
        },
        {
            "relation_type": "竞争",
            "definition": "对可用集合形成排他约束",
            "criteria": "稀缺项、时间窗、合作通道",
            "failure_or_transition": "资源扩张、规则协调或退出",
            "source_refs": ["V82-P1829", "V82-P1830", "V82-P1831", "V82-P1832"],
        },
        {
            "relation_type": "临时",
            "definition": "围绕有限事件或任务形成",
            "criteria": "结束、留痕和责任承接",
            "failure_or_transition": "解体、制度化或转为其他关系",
            "source_refs": ["V82-P1833", "V82-P1834", "V82-P1835", "V82-P1836"],
        },
    ]
    assert rcc["required_fields"] == [
        "source_circle_ref",
        "target_circle_ref",
        "direction",
        "relation_type",
        "shared_members_or_interfaces",
        "channel",
        "strength_or_scope",
        "time_window",
        "delay",
        "threshold",
        "evidence_refs",
        "counterexample_refs",
        "failure_conditions",
    ]
    assert rcc["invariants"] == [
        "one_declared_relation_per_edge",
        "same_pair_may_have_multiple_typed_edges_with_separate_channels_and_time_windows",
        "directed_multigraph_with_local_containment",
        "multiple_local_parents_are_allowed",
        "higher_does_not_imply_more_important_real_or_authorized",
        "shared_environment_is_not_a_direct_relation",
        "member_overlap_is_not_nesting",
        "information_contact_is_not_feedback",
        "transformation_is_not_a_seventh_relation_type",
    ]
    assert rcc["validation_contract"] == {
        "record_fields": "closed_exactly_required_fields",
        "relation_type": "closed_to_relation_types",
        "evidence_refs": "runtime_evidence_ids",
        "counterexample_refs": "runtime_counterexample_ids",
        "authority_source_refs": "separate_v82_anchors",
    }

    assert rac["requirement_type"] == "rac_membership"
    assert rac["source_refs"] == [
        "V82-P1766",
        "V82-P1780",
        "V82-P1781",
        "V82-P1843",
        "V82-P1862",
        "V82-P1915",
        "V82-P1916",
    ]
    assert rac["required_fields"] == [
        "actor_ref",
        "circle_ref",
        "membership_basis",
        "start_time",
        "end_time",
        "roles",
        "commitment_strength",
        "actual_participation",
        "exit_ability",
        "dispute_status",
        "evidence_status",
        "source_refs",
    ]
    assert rac["invariants"] == [
        "membership_is_not_binary_or_permanent",
        "multiple_circle_memberships_are_allowed",
        "role_conflicts_and_exit_differences_are_preserved",
        "formal_membership_does_not_imply_action_capacity",
        "representation_does_not_imply_authorization",
        "bridge_requires_an_actual_channel_and_state_or_information_change",
        "representation_capacity_and_responsibility_remain_separate",
    ]
    assert rac["validation_contract"] == {
        "record_fields": "closed_exactly_required_fields",
        "example_values": "non_normative_and_not_enumerated",
        "source_refs": "runtime_evidence_or_source_ids",
        "authority_source_refs": "separate_v82_anchors",
    }

    contract_schema = load_json(ULTRA / "schemas" / "ultra-contract-map.schema.json")
    Draft202012Validator.check_schema(contract_schema)
    assert contract_schema["$defs"]["rccRequirement"]["properties"][
        "relation_types"
    ]["const"] == ["平行", "嵌套", "重叠", "桥接", "竞争", "临时"]
    for forbidden_runtime_api in (
        "rccRecord",
        "racRecord",
        "m02ExecutionRecord",
        "governanceChangeRecord",
        "axisDifferenceRecord",
    ):
        assert forbidden_runtime_api not in contract_schema["$defs"]


def test_m02_descriptor_freezes_branch_registration_and_registry_resolution() -> None:
    requirement = machine_requirements()["V82-REQ-M02-EXECUTION"]
    assert requirement["requirement_type"] == "m02_execution"
    assert requirement["source_refs"] == [
        "V82-P0661",
        "V82-P0662",
        "V82-P0663",
        "V82-P0926",
        "V82-P0928",
        "V82-P0929",
        "V82-P0930",
        "V82-P0931",
        "V82-P0932",
        "V82-P0938",
        "V82-P0939",
        "V82-P0940",
        "V82-P0941",
        "V82-P0942",
        "V82-P1006",
        "V82-P1016",
    ]
    assert requirement["concept_id"] == "V82-M02"
    assert requirement["operator_id"] == "scale_operator:M02"
    assert requirement["branches"] == [
        {
            "branch_id": "descriptive_nesting",
            "claim_mode": "descriptive_mapping",
            "requires_root_instance": False,
            "allowed_root_subtypes": [],
            "required_evidence_fields": [
                "boundary_refs",
                "member_refs",
                "overlap_refs",
                "exit_refs",
                "interface_mapping_refs",
            ],
        },
        {
            "branch_id": "cross_layer_causal",
            "claim_mode": "causal",
            "requires_root_instance": True,
            "allowed_root_subtypes": ["G4a", "G4b"],
            "required_evidence_fields": [
                "root_instance_ids",
                "success_criterion_id",
                "causal_bridge_refs",
                "causal_gate_ref",
                "positive_decision_rule_ref",
                "null_decision_rule_ref",
            ],
        },
        {
            "branch_id": "object_conversion",
            "claim_mode": "object_conversion",
            "requires_root_instance": True,
            "allowed_root_subtypes": ["G4b"],
            "required_evidence_fields": [
                "root_instance_ids",
                "success_criterion_id",
                "causal_bridge_refs",
                "positive_decision_rule_ref",
                "null_decision_rule_ref",
            ],
        },
        {
            "branch_id": "intervention_conversion",
            "claim_mode": "intervention_conversion",
            "requires_root_instance": True,
            "allowed_root_subtypes": ["G4b"],
            "required_evidence_fields": [
                "root_instance_ids",
                "success_criterion_id",
                "causal_bridge_refs",
                "positive_decision_rule_ref",
                "null_decision_rule_ref",
            ],
        },
    ]
    assert requirement["success_criteria_by_root_subtype"] == {
        "G4a": [
            "conditional_information_gain",
            "conditional_predictive_gain",
            "conditional_intervention_gain",
        ],
        "G4b": [
            "object_dynamics_non_commutation",
            "intervention_non_commutation",
            "identity_criterion_violation",
            "effective_relation_change",
            "intervention_response_change",
        ],
    }
    assert requirement["success_criterion_selection_cardinality"] == 1
    assert requirement["pre_result_registration_required_fields"] == [
        "pre_result_registration_ref",
        "pre_result_registration_hash",
    ]
    assert requirement["pre_result_registration_match_fields"] == [
        *M02_FROZEN_REGISTRATION_MATCH_FIELDS,
    ]
    assert requirement["positive_support_requires"] == [
        "positive_decision_rule_ref",
        "positive_threshold",
    ]
    assert requirement["runtime_registry_resolution_contract"] == [
        "pre_result_registration_ref_and_hash_must_resolve",
        "all_match_fields_must_equal_same_hash_verified_pre_result_registration",
        "branch_and_mode_must_match_frozen_registration",
        "non_descriptive_root_instance_ids_must_resolve",
        "causal_object_and_intervention_require_nonempty_causal_bridge",
        "object_and_intervention_roots_require_g4b",
        "cross_layer_causal_roots_allow_g4a_or_g4b",
        "success_criterion_must_match_exactly_one_subtype_enum_value",
        "registered_positive_rule_and_threshold_must_both_pass_for_supported",
        "registered_null_rule_and_all_three_null_gates_must_pass_for_null_supported",
        "not_evaluated_means_selected_branch_did_not_run",
        "descriptive_supported_does_not_require_g_fields",
    ]
    assert requirement["result_states"] == [
        "supported",
        "unsupported_or_undecided",
        "null_supported",
        "not_evaluated",
    ]
    assert requirement["null_support_requires"] == [
        "null_decision_rule_ref",
        "equivalence_or_sufficiency_test_ref",
        "power_or_sensitivity_ref",
        "tolerance_ref",
    ]
    assert requirement["result_state_semantics"] == {
        "supported": (
            "selected_branch_ran_and_registered_positive_rule_and_threshold_passed"
        ),
        "unsupported_or_undecided": "selected_branch_ran_without_positive_or_null_support",
        "null_supported": (
            "selected_branch_ran_and_registered_null_rule_and_all_three_null_gates_passed"
        ),
        "not_evaluated": "selected_branch_did_not_run",
    }
    assert requirement["forbidden_substitutions"] == [
        "不得用描述性嵌套的边界材料支持后面三支",
        "描述性嵌套不生成上位优先、下位义务或 J 轴扩展",
    ]
    assert requirement["action_ceiling"] == (
        "描述性嵌套不生成上位优先、下位义务或 J 轴扩展。"
    )


def test_p2781_governance_invariants_are_machine_checkable() -> None:
    requirement = machine_requirements()["V82-REQ-GOVERNANCE-MACHINE"]
    assert requirement == {
        "requirement_id": "V82-REQ-GOVERNANCE-MACHINE",
        "requirement_type": "governance_invariants",
        "source_refs": ["V82-P2780", "V82-P2781", "V82-P2890"],
        "framework_self_proof_allowed": False,
        "governance_record_generates_real_world_authorization": False,
        "terminal_to_active_forbidden": ["replaced", "retired"],
        "applied_change_requires": "resolvable_external_approval",
        "invalid_approval_evidence": [
            "alias",
            "self_reported_independent_true",
            "self_issued_authorization",
        ],
        "contrary_permission_text_overrides": False,
        "machine_invariants": [
            "framework_self_proof_forbidden",
            "governance_record_authorization_generation_forbidden",
            "replaced_to_active_forbidden",
            "retired_to_active_forbidden",
            "applied_requires_resolvable_external_approval",
            "alias_approval_invalid",
            "self_reported_independence_invalid",
            "self_issued_authorization_invalid",
            "contrary_permission_text_cannot_override_structured_constraints",
        ],
        "external_approval_required_bindings": [
            "governance_record_ref",
            "subject_ref",
            "target_version",
            "transition",
            "objection_refs",
            "decision_ref",
        ],
        "runtime_registry_resolution_fields": [
            "reviewer_refs",
            "decision_member_refs",
            "decision_body_ref",
            "issuer_ref",
            "authorization_scope",
            "subject_ref",
            "target_version",
            "validity_window",
            "conflict_refs",
        ],
        "external_approval_resolution_invariants": [
            "externality_cannot_be_self_reported",
            "decision_must_resolve_to_approved",
            "alias_resolved_identity_must_be_external",
            "internal_signature_is_rejected",
            "self_issued_authorization_is_rejected",
        ],
    }


def test_machine_requirement_ids_owners_and_anchor_backlinks_are_closed() -> None:
    expected_owners = {
        "V82-REQ-SP-AXES": "V82-CONTRACT-TRANSFORMATION",
        "V82-REQ-M02-EXECUTION": "V82-CONTRACT-TRANSFORMATION",
        "V82-REQ-RCC-RELATION": "V82-CONTRACT-WORLD-VOLUME",
        "V82-REQ-RAC-MEMBERSHIP": "V82-CONTRACT-WORLD-VOLUME",
        "V82-REQ-GOVERNANCE-MACHINE": "V82-CONTRACT-JUDGMENT-GOVERNANCE",
    }
    contract_map = load_json(CONTRACT_ROOT / "v8.2-contract-map.json")
    map_entries = {
        entry["contract_id"]: entry for entry in contract_map["contracts"]
    }
    observed_owners: dict[str, str] = {}
    schema = load_json(ULTRA / "schemas" / "ultra-contract-map.schema.json")
    Draft202012Validator.check_schema(schema)
    document_validator = Draft202012Validator(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$defs": schema["$defs"],
            "$ref": "#/$defs/contractDocument",
        }
    )

    for entry in contract_map["contracts"]:
        document = load_json(CONTRACT_ROOT / entry["file"])
        assert not list(document_validator.iter_errors(document))
        assert entry["source_anchors"] == document["source_anchors"]
        document_anchors = set(document["source_anchors"])
        for requirement in document["machine_requirements"]:
            requirement_id = requirement["requirement_id"]
            assert requirement_id not in observed_owners
            observed_owners[requirement_id] = document["contract_id"]
            assert set(requirement["source_refs"]) <= document_anchors

    assert observed_owners == expected_owners
    assert set(map_entries) == {
        "V82-CONTRACT-CORE-KERNEL",
        "V82-CONTRACT-TRANSFORMATION",
        "V82-CONTRACT-WORLD-VOLUME",
        "V82-CONTRACT-RECURSIVE-INFERENCE",
        "V82-CONTRACT-JUDGMENT-GOVERNANCE",
    }


def test_route_map_covers_requirements_and_their_owning_contracts() -> None:
    owners = {
        "V82-REQ-SP-AXES": "V82-CONTRACT-TRANSFORMATION",
        "V82-REQ-M02-EXECUTION": "V82-CONTRACT-TRANSFORMATION",
        "V82-REQ-RCC-RELATION": "V82-CONTRACT-WORLD-VOLUME",
        "V82-REQ-RAC-MEMBERSHIP": "V82-CONTRACT-WORLD-VOLUME",
        "V82-REQ-GOVERNANCE-MACHINE": "V82-CONTRACT-JUDGMENT-GOVERNANCE",
    }
    route_map = load_json(ULTRA / "references" / "v8.2-route-map.json")
    covered: set[str] = set()
    for route in route_map["routes"]:
        assert set(route) == {
            "route_id",
            "task",
            "source_anchors",
            "concept_ids",
            "contract_ids",
            "requirement_ids",
        }
        for requirement_id in route["requirement_ids"]:
            assert requirement_id in owners
            assert owners[requirement_id] in route["contract_ids"]
            covered.add(requirement_id)
    assert covered == set(owners)


def test_requirement_source_support_rejects_field_mutation_and_padding() -> None:
    checker = load_checker()
    source_checker = checker._load_source_checker(ROOT)
    errors: list[str] = []
    _, source_records = checker._validated_source_snapshot(
        source_checker,
        ROOT,
        errors,
    )
    assert errors == []

    mutated = copy.deepcopy(machine_requirements()["V82-REQ-SP-AXES"])
    mutated["axes"][0]["state_field_core"] = "invented state field"
    checker._validate_requirement_source_support(mutated, source_records, errors)
    assert any(
        "does not contain required marker" in error
        or "field value is not supported" in error
        for error in errors
    )

    errors.clear()
    padded = copy.deepcopy(machine_requirements()["V82-REQ-RAC-MEMBERSHIP"])
    padded["source_refs"].append("V82-P0001")
    checker._validate_requirement_source_support(padded, source_records, errors)
    assert any("unsupported padding" in error for error in errors)


@pytest.mark.parametrize("field", M02_FROZEN_REGISTRATION_MATCH_FIELDS)
def test_m02_source_support_rejects_each_post_result_registration_substitution(
    field: str,
) -> None:
    checker = load_checker()
    source_checker = checker._load_source_checker(ROOT)
    source_errors: list[str] = []
    _, source_records = checker._validated_source_snapshot(
        source_checker,
        ROOT,
        source_errors,
    )
    assert source_errors == []

    mutated = copy.deepcopy(machine_requirements()["V82-REQ-M02-EXECUTION"])
    match_fields = mutated["pre_result_registration_match_fields"]
    assert isinstance(match_fields, list)
    assert field in match_fields, f"{field} is not bound to the pre-result registration"
    match_fields[match_fields.index(field)] = f"post_result_{field}"

    errors: list[str] = []
    checker._validate_requirement_source_support(mutated, source_records, errors)
    assert any(
        "pre_result_registration_match_fields" in error
        and "required canonical values" in error
        for error in errors
    ), (field, errors)


@pytest.mark.parametrize("field", M02_FROZEN_REGISTRATION_MATCH_FIELDS)
def test_m02_contract_schema_rejects_each_post_result_registration_substitution(
    field: str,
) -> None:
    schema = load_json(ULTRA / "schemas" / "ultra-contract-map.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$defs": schema["$defs"],
            "$ref": "#/$defs/contractDocument",
        }
    )
    document = load_json(CONTRACT_ROOT / "transformation-contracts.json")
    requirement = next(
        requirement
        for requirement in document["machine_requirements"]
        if requirement["requirement_id"] == "V82-REQ-M02-EXECUTION"
    )
    match_fields = requirement["pre_result_registration_match_fields"]
    assert isinstance(match_fields, list)
    assert field in match_fields, f"{field} is not bound to the pre-result registration"
    match_fields[match_fields.index(field)] = f"post_result_{field}"

    errors = list(validator.iter_errors(document))
    assert errors, field


def test_requirement_owner_closure_rejects_deletion_and_wrong_contract() -> None:
    checker = load_checker()
    requirements: dict[str, tuple[str, dict[str, object], set[str]]] = {}
    contract_map = load_json(CONTRACT_ROOT / "v8.2-contract-map.json")
    for entry in contract_map["contracts"]:
        assert isinstance(entry, dict)
        document = load_json(CONTRACT_ROOT / str(entry["file"]))
        owner = str(document["contract_id"])
        anchors = set(document["source_anchors"])
        for requirement in document["machine_requirements"]:
            requirements[str(requirement["requirement_id"])] = (
                owner,
                requirement,
                anchors,
            )
    source_checker = checker._load_source_checker(ROOT)
    source_errors: list[str] = []
    _, source_records = checker._validated_source_snapshot(
        source_checker,
        ROOT,
        source_errors,
    )
    assert source_errors == []

    deleted = dict(requirements)
    deleted.pop("V82-REQ-RAC-MEMBERSHIP")
    errors: list[str] = []
    checker._validate_machine_requirement_closure(deleted, source_records, errors)
    assert any("closure mismatch" in error for error in errors)

    moved = dict(requirements)
    requirement_id, (_, requirement, anchors) = next(
        (key, value)
        for key, value in moved.items()
        if key == "V82-REQ-RAC-MEMBERSHIP"
    )
    moved[requirement_id] = ("V82-CONTRACT-TRANSFORMATION", requirement, anchors)
    errors.clear()
    checker._validate_machine_requirement_closure(moved, source_records, errors)
    assert any("owner mismatch" in error for error in errors)
