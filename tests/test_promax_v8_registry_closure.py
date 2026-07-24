from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/crossframe-promax"
REFERENCES = SKILL / "references"
REGISTRY_PATH = REFERENCES / "concept-registry/v8-concept-registry.json"
CONTRACT_MAP_PATH = REFERENCES / "concept-contracts/v8-contract-map.json"
ROUTE_MAP_PATH = REFERENCES / "v8-route-map.json"
CHECKER_PATH = SKILL / "scripts/check_crossframe_promax_v8_knowledge.py"
LAUNCHER_PATH = ROOT / "scripts/check_crossframe_promax_v8_knowledge.py"
SCHEMAS = {
    "source": SKILL / "schemas/v8-source-manifest.schema.json",
    "registry": SKILL / "schemas/v8-concept-registry.schema.json",
    "contracts": SKILL / "schemas/v8-contract-map.schema.json",
    "routes": SKILL / "schemas/v8-route-map.schema.json",
}
CONTRACTS = {
    "v8_actor_state_contracts": (
        "actor-state-contracts.json",
        "11bbd5a920732b2ff9cf7969ac0af70eeb6056f2bdeef51f3f43a4f68cfbfb6d",
    ),
    "v8_multicircle_contracts": (
        "multicircle-contracts.json",
        "dd2bf24cef5584839ab26a72878fb2102ab498c56d59297479de449921649964",
    ),
    "v8_simulation_forecast_contracts": (
        "simulation-forecast-contracts.json",
        "c0d652560bb1ac25714f806020888ce89ac502a51185885a6e997e7901d08c1d",
    ),
}
SNAPSHOT_SHA256 = "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
EXPECTED_CANONICAL_CONCEPT_COUNT = 709
EXPECTED_CANONICAL_INVENTORY_SHA256 = "e30de5dc667c0a4075c205f61f00aab729a7683ba6c70abb4c137a612d6b5635"
EXPECTED_REGISTRY_FILE_SHA256 = "a9f2e57c3fb7147aaab8a291f5ebaf130ada5abb84ae58c0ca1797bb7a3d5b6f"
EXPECTED_CONTRACT_MAP_FILE_SHA256 = "601a739c5ce8f994e4832e1e1d57973be52c2522d2c2f464ee403a73cae65c8e"
EXPECTED_ROUTE_MAP_FILE_SHA256 = "ef084b0cd98fd6de01dd40f2701b4b010f3041e83f5e38c68556e9288f2c2fd0"
EXPECTED_BINDING_INVENTORY_SHA256 = "f68a403aac09143c4057fac030070b4866106db1dd750d022d5f321427ab2d48"
EXPECTED_SEMANTIC_COVERAGE_SHA256 = "54d3910dac39c71b64adae363907f9442f9d7ffcbbd23939ee4b0d9f2b48a92c"
EXPECTED_CONCEPT_SEMANTIC_SHA256 = "c306710628498553cb53709ea51a40ab969021580713310637be37403b1a42ce"
EXPECTED_ROUTE_SEMANTIC_SHA256 = "eb52863b417fb5566a23e2aab00aedab229d728b699d83543e341778a117a510"
EXPECTED_SCHEMA_FILE_SHA256 = {
    "source": "74f24b3da3186525a79b4eddec8c1e9ddb2f7755211bb89fc32bf81ccc5b0ff6",
    "registry": "9f77a096eba132a02f57883b7a662df34e59285e2b186711eaffce4914a33b4d",
    "contracts": "3c0bf440900cf92067f02567078655994992c5c1efb2d8144889dae0497a8037",
    "routes": "c44ac7d75d942a25c8960942f3e2fe97a71cbb0f03847696b101b9f81d4e5557",
}
EXPECTED_SEMANTIC_LEAF_COUNTS = {
    "v8_actor_state_contracts": 97,
    "v8_multicircle_contracts": 110,
    "v8_simulation_forecast_contracts": 150,
}
EXPECTED_SEMANTIC_POINTER_COUNTS = {
    "v8_actor_state_contracts": 114,
    "v8_multicircle_contracts": 125,
    "v8_simulation_forecast_contracts": 168,
}
EXPECTED_ROUTE_SOURCES = {
    "V8-ROUTE-01-GUIDE": "01-guide.md",
    "V8-ROUTE-02-BOUNDARY": "02-boundary-method.md",
    "V8-ROUTE-03-GRAMMAR": "03-universal-grammar.md",
    "V8-ROUTE-04-ROOT": "04-root-assumptions.md",
    "V8-ROUTE-05-SCALE": "05-scale-transformation.md",
    "V8-ROUTE-06-OPERATION": "06-operation-evolution.md",
    "V8-ROUTE-07-HUMAN": "07-human-world.md",
    "V8-ROUTE-08-PROTOTYPE": "08-human-state-prototype.md",
    "V8-ROUTE-09-ACTOR": "09-actor-state-personality.md",
    "V8-ROUTE-10-MULTICIRCLE": "10-multicircle-joint-state.md",
    "V8-ROUTE-11-SIMULATION": "11-event-dynamic-deduction.md",
    "V8-ROUTE-12-FORECAST": "12-conditional-forecast-choice.md",
    "V8-ROUTE-13-TOOLS": "13-interface-tools.md",
    "V8-ROUTE-14-NORMATIVE": "14-normative-selection.md",
    "V8-ROUTE-15-INTERVENTION": "15-intervention-applications.md",
    "V8-ROUTE-16-GOVERNANCE": "16-governance.md",
}
EXPECTED_ROUTE_SIGNAL_SEMANTICS = "task_signals 与 object_signals 是人工固化的 v8 运行路由词，不是 v8 canonical definitions，也不得据此创造或改写 canonical concepts。"
EXPECTED_ROUTE_SIGNALS = {
    "V8-ROUTE-01-GUIDE": (["框架入口", "输出责任", "强判断"], ["分析输出", "判断对象"]),
    "V8-ROUTE-02-BOUNDARY": (["对象准入", "证据与来源审计", "方法边界"], ["候选对象", "材料与命题"]),
    "V8-ROUTE-03-GRAMMAR": (["结构描述", "原语闭合", "尺度声明"], ["广义结构对象", "状态与接口"]),
    "V8-ROUTE-04-ROOT": (["根实例检验", "认识论约束", "推论合同"], ["经验实例", "竞争零模型"]),
    "V8-ROUTE-05-SCALE": (["尺度比较", "算子变换", "跨圈层迁移"], ["尺度剖面", "源目标对象"]),
    "V8-ROUTE-06-OPERATION": (["运转机制", "反馈学习", "相位与筛选"], ["运行对象", "异步机制"]),
    "V8-ROUTE-07-HUMAN": (["人类条款", "责任分型", "人类变量接口"], ["人类结构对象", "受影响位置"]),
    "V8-ROUTE-08-PROTOTYPE": (["状态原型", "非线性路径", "有序退场"], ["人类联合状态", "调节与承接"]),
    "V8-ROUTE-09-ACTOR": (["行动者状态", "人格假设", "角色激活"], ["行动者", "慢中快变量"]),
    "V8-ROUTE-10-MULTICIRCLE": (["圈层准入", "联合状态", "多时钟"], ["候选圈层", "多重成员关系"]),
    "V8-ROUTE-11-SIMULATION": (["事件驱动推演", "路径分叉", "变量候选"], ["事件", "联合状态更新"]),
    "V8-ROUTE-12-FORECAST": (["条件前瞻", "方案比较", "结果回写"], ["预测目标", "有限选择"]),
    "V8-ROUTE-13-TOOLS": (["接口转换", "诊断闸门", "动态运行"], ["工具调用", "审计记录"]),
    "V8-ROUTE-14-NORMATIVE": (["规范选择", "保护底板", "有限授权"], ["受影响主体", "现实方案"]),
    "V8-ROUTE-15-INTERVENTION": (["干涉分级", "应用模块", "承接与退出"], ["应用场景", "有限执行"]),
    "V8-ROUTE-16-GOVERNANCE": (["框架治理", "恶意合规审计", "退役替代"], ["框架与版本", "治理风险"]),
}
EXPECTED_CJK_NAMES = {
    "V8-CANON-CM-MAINTENANCE-CURRENT": "CM-MAINTENANCE 维护即时分支",
    "V8-CANON-CM-MAINTENANCE-CUMULATIVE": "CM-MAINTENANCE 维护累积分支",
    "V8-CANON-CM-LOAD-INSTANT": "CM-LOAD 瞬时负荷分支",
    "V8-CANON-CM-LOAD-CUMULATIVE": "CM-LOAD 累积负荷分支",
    "V8-CANON-CM-PHASE-PATTERN": "CM-PHASE 相位模式",
    "V8-CANON-CM-PHASE-CAUSAL-TRIGGER": "CM-PHASE 相位因果触发",
    "V8-CANON-CM-PHASE-HYSTERETIC": "CM-PHASE 相位迟滞分支",
    "V8-CANON-CM-SELECTION-PATTERN": "CM-SELECTION 筛选模式",
    "V8-CANON-CM-SELECTION-CARRIER": "CM-SELECTION 筛选具体机制",
    "V8-CANON-CM-SELECTION-HISTORY": "CM-SELECTION 筛选跨轮路径",
    "V8-CANON-NSP-LEAST-HARM": "NSP-LEAST-HARM 最小伤害原则",
    "V8-CANON-NSP-PROPORTIONALITY": "NSP-PROPORTIONALITY 比例原则",
    "V8-CANON-SEL-SYS": "SEL-SYS 系统筛选",
    "V8-CANON-SEL-AGT": "SEL-AGT 行动主体选择",
    "V8-CANON-SEL-GOV": "SEL-GOV 集体治理选择",
}
OPTIONAL_SEMANTIC_FIELDS = (
    "prerequisites",
    "forbidden_substitutions_or_generalizations",
    "common_misuses",
    "conflicts_disambiguation",
    "evidence_requirements",
    "counterexamples",
    "withdrawal_conditions",
    "deduction_interfaces",
    "action_ceiling",
)
HV_SOURCE_CARD_SCHEMA_ID = "crossframe-promax-v8-human-variable-source-card/1.0.0"
HV_P1129_FIELDS = (
    "id", "qualified_id", "name", "proposition", "scope", "claim_type",
    "contract_role", "pause_condition", "allowed_inference", "prohibited_leap",
    "inferential_requires", "protocol_requires", "specializes", "applies_to",
    "conditional_support_routes", "scale_profile", "effective_object", "state",
    "observables", "evidence", "input_dependencies", "output_effects", "carrier",
    "responsible_subject", "time_window_and_lag", "uncertainty",
    "local_exclusion_zone", "affected_positions", "normative_status",
    "scale_invariants", "required_scale_additions", "changing_semantics",
    "non_applicable_objects", "forbidden_elevation", "judgment_ceiling",
    "action_ceiling", "counterexamples", "appeal", "rollback",
)
HV_SOURCE_FIELD_OFFSETS = {
    "id": (4, 5), "qualified_id": (6, 7), "name": (8, 9),
    "proposition": (14, 15), "scope": (16, 17), "claim_type": (10, 11),
    "contract_role": (12, 13), "pause_condition": (18, 19),
    "allowed_inference": (33, 34), "prohibited_leap": (35, 36),
    "inferential_requires": (23, 24), "protocol_requires": (25, 26),
    "specializes": (27, 28), "applies_to": (29, 30),
    "conditional_support_routes": (31, 32), "scale_profile": (40, 41),
    "effective_object": (42, 43), "state": (57, 58),
    "observables": (59, 60), "evidence": (61, 62),
    "input_dependencies": (63, 64), "output_effects": (65, 66),
    "carrier": (78, 79), "responsible_subject": (80, 81),
    "time_window_and_lag": (67, 68), "uncertainty": (69, 70),
    "local_exclusion_zone": (71, 72), "affected_positions": (73, 74),
    "normative_status": (82, 83), "scale_invariants": (44, 45),
    "required_scale_additions": (46, 47), "changing_semantics": (48, 49),
    "non_applicable_objects": (50, 51), "forbidden_elevation": (52, 53),
    "judgment_ceiling": (84, 85), "action_ceiling": (86, 87),
    "counterexamples": (88, 89), "appeal": (90, 91), "rollback": (92, 93),
}
HV_SOURCE_CARD_SHA256 = {
    "V8-CANON-HV01": "05a4321aa97e897ed2175b612c754642f4fbed6d12273c15b187d59fa3d261d3",
    "V8-CANON-HV02": "fe7cd8269a5dd2ae1971f40ef5cdddd8a99ad2b8d3af2e5bc8b05cd27c0d24c6",
    "V8-CANON-HV03": "4ca87e904c9b79f209ba6086d5eaeee572179fdf149331f10c4851206d8562dd",
    "V8-CANON-HV04": "cbc3811171dd029c9674f22bbebedffebbd1391f88351905c525950ff562ef94",
    "V8-CANON-HV05": "dfc1dc9682e4f737ac2cbfe020ed466bd0242a02c8426d4b84eacc798565d287",
    "V8-CANON-HV06": "3c3f1e6bbbf5ecf41ff723c144a733f6567561b2b9a462456b0a578daad1e481",
    "V8-CANON-HV07": "28de39579e664462f9e8c4b3e2f9659fa917a590b5ed74782878784cd001582f",
    "V8-CANON-HV08": "2f26ceff316c36d6a7117fee5e301dc7fd38400aa88bb776c59d2c497ea8f67b",
    "V8-CANON-HV09": "5f03d8e5624ecc9e6a2072d3223eccf17e417dccaddc998ed4c5af2a23cc4ede",
    "V8-CANON-HV10": "d22ff0b2a70c1472b73be3ef4b334da2ac7b89a11b7fd2b2b2f16ae46a61e848",
    "V8-CANON-HV11": "e07fe90611974917bfce08072c44b0e89014d57c8f74bf67ebe57fe1048cfb94",
}
EXPECTED_HV_ROUTE_REQUIRED_IDS = {
    "HV01-R0-candidate-object": {"V8-CANON-D0", "V8-CANON-G1", "V8-CANON-VOCAB-ROOT-INSTANCE-RESULT-SUPPORTED"},
    "HV01-R1-effective-domain": {"V8-CANON-D0-K", "V8-CANON-E4", "V8-CANON-G1", "V8-CANON-VOCAB-ROOT-INSTANCE-RESULT-SUPPORTED"},
    "HV02-R0-boundary-inventory": set(),
    "HV02-R1-selective-effect": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2"},
    "HV03-R0-candidate-anchor": {"V8-CANON-H1"},
    "HV03-R1-effective-anchor": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-H1", "V8-CANON-VOCAB-ROOT-INSTANCE-RESULT-SUPPORTED"},
    "HV04-R0-generation-typing": {"V8-CANON-GC", "V8-CANON-GE", "V8-CANON-GS"},
    "HV04-R1-generation-mechanism": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2", "V8-CANON-GC", "V8-CANON-GE", "V8-CANON-GS"},
    "HV05-R0-carrier-responsibility-split": {"V8-CANON-CV", "V8-CANON-H2", "V8-CANON-RS"},
    "HV05-R1-functional-carrier-effect": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2"},
    "HV05-R2-intertemporal-reproduction": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2", "V8-CANON-G3"},
    "HV05-R3-historical-carrier-trace": {"V8-CANON-E4", "V8-CANON-H5", "V8-CANON-VOCAB-ROOT-INSTANCE-RESULT-SUPPORTED"},
    "HV06-R0-segment-map": set(),
    "HV06-R1-complete-chain-composition": {"V8-CANON-HV03", "V8-CANON-HV04", "V8-CANON-HV05"},
    "HV06-R2-effective-channel": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2", "V8-CANON-HV03", "V8-CANON-HV04", "V8-CANON-HV05"},
    "HV07-R0-writeback-classification": set(),
    "HV07-R1-causal-feedback": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2"},
    "HV07-R2-feedback-mediated-learning": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2", "V8-CANON-G3"},
    "HV08-R0-condition-inventory": {"V8-CANON-H4"},
    "HV08-R1-position-or-mediation-effect": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-H4", "V8-CANON-VOCAB-ROOT-INSTANCE-RESULT-SUPPORTED"},
    "HV08-R2-reflexive-response": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E3", "V8-CANON-E4", "V8-CANON-H4", "V8-CANON-VOCAB-ROOT-INSTANCE-RESULT-SUPPORTED"},
    "HV09-R0-instant-task-capacity": set(),
    "HV09-R1-overload-mechanism": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-CM-LOAD", "V8-CANON-E4", "V8-CANON-G2"},
    "HV09-R2-cumulative-overload": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-CM-LOAD", "V8-CANON-E4", "V8-CANON-G2", "V8-CANON-G3"},
    "HV10-R0-component-applicability": {"V8-CANON-HV03", "V8-CANON-HV04", "V8-CANON-HV05", "V8-CANON-HV07"},
    "HV10-R1-pattern-phase-match": {"V8-CANON-CM-PHASE", "V8-CANON-E4"},
    "HV10-R2-causal-transition": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-CM-PHASE", "V8-CANON-E4", "V8-CANON-G2"},
    "HV10-R3-path-dependent-phase": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-CM-PHASE", "V8-CANON-E4", "V8-CANON-G3"},
    "HV11-R0-action-cost-record": set(),
    "HV11-R1-voluntary-limited-action": set(),
    "HV11-R2-structural-consequence": {"V8-CANON-CAUSAL-CONTRACT", "V8-CANON-E4", "V8-CANON-G2"},
}

REQUIRED_CONCEPT_IDS = {
    *(f"V8-CANON-D{i}" for i in range(4)),
    *(f"V8-CANON-U{i:02d}" for i in range(1, 12)),
    *(f"V8-CANON-G{i}" for i in range(1, 5)),
    *(f"V8-CANON-G{i}{suffix}" for i in range(1, 5) for suffix in ("A", "B")),
    *(f"V8-CANON-E{i}" for i in range(1, 6)),
    *(f"V8-CANON-C{i}" for i in range(1, 13)),
    *(f"V8-CANON-M{i:02d}" for i in range(1, 10)),
    *(f"V8-CANON-H{i}" for i in range(1, 7)),
    *(f"V8-CANON-HV{i:02d}" for i in range(1, 12)),
    *(f"V8-CANON-S{i}" for i in range(7)),
    "V8-CANON-X0",
    "V8-CANON-CM-FEEDBACK",
    "V8-CANON-CM-LEARNING",
    "V8-CANON-CM-MAINTENANCE",
    "V8-CANON-CM-LOAD",
    "V8-CANON-CM-PHASE",
    "V8-CANON-CM-SELECTION",
    *(f"V8-CANON-SCALE-AXIS-{axis}" for axis in ("A", "X", "T", "O", "C", "R", "I", "N", "J")),
    *(f"V8-CANON-H{i}" for i in range(1, 7)),
    *(f"V8-CANON-N{i}" for i in range(1, 6)),
    *(f"V8-CANON-PF-{i}" for i in range(1, 11)),
    *(f"V8-CANON-T{i}" for i in range(5)),
    *(f"V8-CANON-GOV-{i:02d}" for i in range(1, 25)),
    *(f"V8-CANON-APP-{code}" for code in ("REL", "FAM", "ORG", "PLT", "INS", "OPI", "SPC", "EMG", "ULS")),
    "V8-CANON-ACTOR-STATE",
    "V8-CANON-MULTICIRCLE-JOINT-OBJECT",
}

REQUIRED_VOCABULARY_IDS = {
    *(f"V8-CANON-VOCAB-CLAIM-{item}" for item in ("D", "G", "E", "H", "N", "O")),
    *(f"V8-CANON-VOCAB-DEPENDENCY-{item}" for item in ("INFERENTIAL", "PROTOCOL", "SPECIALIZES", "APPLIES-TO")),
    *(f"V8-CANON-VOCAB-INFO-{item}" for item in ("UNKNOWN", "NOT-APPLICABLE", "NOT-OBSERVABLE", "WITHHELD-FOR-PROTECTION")),
    *(f"V8-CANON-VOCAB-AXIS-RELATION-{item}" for item in ("EQUAL", "EXPANDS", "CONTRACTS", "INCOMPARABLE", "UNKNOWN")),
    *(f"V8-CANON-VOCAB-TRANSFORM-{item}" for item in ("HORIZONTAL-OR-INCOMPARABLE", "MIXED", "UNRESOLVED", "ALL-EQUAL", "ELEVATION", "REDUCTION")),
    *(f"V8-CANON-VOCAB-OPERATOR-{item}" for item in ("SUPPORTED", "UNSUPPORTED-OR-UNDECIDED", "NULL-SUPPORTED", "NOT-EVALUATED")),
    *(f"V8-CANON-VOCAB-ACTOR-BAND-{item}" for item in ("SLOW", "MEDIUM", "FAST")),
    *(f"V8-CANON-VOCAB-ACTOR-STATE-{item}" for item in ("UNKNOWN", "CANDIDATE", "SUPPORTED-HYPOTHESIS", "OBSERVED", "CONTESTED", "RETIRED")),
    *(f"V8-CANON-VOCAB-PRIVACY-{item}" for item in ("PUBLIC", "CONTEXT-LIMITED", "SENSITIVE", "HIGHLY-SENSITIVE", "WITHHELD")),
    *(f"V8-CANON-VOCAB-CIRCLE-RELATION-{item}" for item in ("PARALLEL", "NESTED", "OVERLAPPING", "BRIDGING", "COMPETITIVE", "TEMPORARY")),
    *(f"V8-CANON-VOCAB-CIRCLE-TRANSITION-{item}" for item in ("UNCHANGED", "STRENGTHENED", "WEAKENED", "REORIENTED", "TRANSFORMED", "DISSOLVED", "UNKNOWN")),
    *(f"V8-CANON-VOCAB-CONDITION-CHANNEL-{item}" for item in ("MATERIAL", "EXPERIENTIAL-MEANING")),
    *(f"V8-CANON-VOCAB-CLOCK-{item}" for item in ("IMMEDIATE", "INTERACTION", "ORGANIZATIONAL", "INSTITUTIONAL", "LONG-TERM")),
    *(f"V8-CANON-VOCAB-EVENT-{item}" for item in ("OBSERVED", "REPORTED", "PLANNED", "HYPOTHETICAL", "SIMULATED")),
    *(f"V8-CANON-VOCAB-BRANCH-{item}" for item in ("FACT", "MECHANISM", "CHOICE", "EXOGENOUS-DISTURBANCE")),
    *(f"V8-CANON-VOCAB-LEDGER-{item}" for item in ("PROPOSED", "UNDER-TEST", "SUPPORTED-CANDIDATE", "REJECTED", "RETIRED")),
    *(f"V8-CANON-VOCAB-OUTPUT-{item}" for item in ("EXPLANATION", "SIMULATION", "CONDITIONAL-FORECAST", "LIMITED-CHOICE")),
    *(f"V8-CANON-VOCAB-FORECAST-LEVEL-{item}" for item in ("PROBABILITY-OR-RANGE", "RANK-OR-SUPPORT", "CONDITIONAL-DIRECTION", "NO-FORECAST")),
    *(f"V8-CANON-VOCAB-FORECAST-RESULT-{item}" for item in ("SUPPORTED", "UNSUPPORTED", "UNDECIDED", "TARGET-INVALID", "UNASSESSABLE")),
    *(f"V8-CANON-VOCAB-OPTION-{item}" for item in ("MAINTAIN-STATUS-QUO", "ACTIVE-ACTION", "DELAYED-ACTION", "PROBE-ACTION", "EXIT-OR-TRANSFER", "NO-ACTION")),
    *(f"V8-CANON-VOCAB-SELECTION-STATE-{item}" for item in ("DRAFT", "UNDER-REVIEW", "AUTHORIZED", "PAUSED", "STOPPED", "ROLLED-BACK", "CLOSED")),
}

BASE_ADDITIONAL_IDS = {
    "V8-CANON-ANALOGY-CONTRACT", "V8-CANON-CAUSAL-CONTRACT",
    "V8-CANON-CIRCLE-CANDIDATE", "V8-CANON-EVIDENCE-CONTRACT",
    "V8-CANON-H-WORLD", "V8-CANON-HUMAN-EMPIRICAL-CONTRACT",
    "V8-CANON-N0", "V8-CANON-NSP-LEAST-HARM",
    "V8-CANON-NSP-PROPORTIONALITY", "V8-CANON-OMEGA-F-UPDATE",
    "V8-CANON-ROOT-INSTANCE-CONTRACT", "V8-CANON-SOURCE-CONTRACT",
    "V8-CANON-CV", "V8-CANON-GC", "V8-CANON-GE", "V8-CANON-GS",
    "V8-CANON-IB", "V8-CANON-IM", "V8-CANON-IS", "V8-CANON-RS",
    "V8-CANON-SEL-AGT", "V8-CANON-SEL-GOV", "V8-CANON-SEL-SYS",
    *(f"V8-CANON-O{index}" for index in range(1, 5)),
    *(f"V8-CANON-IT{index}" for index in range(1, 5)),
    *(f"V8-CANON-IG{index}" for index in range(1, 8)),
    *(f"V8-CANON-FG{index}" for index in range(1, 6)),
    *(f"V8-CANON-DS{index:02d}" for index in range(1, 14)),
    *(f"V8-CANON-SJ{index}" for index in range(1, 9)),
    *(f"V8-CANON-L{index}" for index in range(1, 4)),
    *(f"V8-CANON-DF{index}" for index in range(1, 10)),
    *(f"V8-CANON-CM-{item}" for item in (
        "MAINTENANCE-CURRENT", "MAINTENANCE-CUMULATIVE", "LOAD-INSTANT",
        "LOAD-CUMULATIVE", "PHASE-PATTERN", "PHASE-CAUSAL-TRIGGER",
        "PHASE-HYSTERETIC", "SELECTION-PATTERN", "SELECTION-CARRIER",
        "SELECTION-HISTORY",
    )),
    *(f"V8-CANON-TOOL-{item}" for item in (
        "EVIDENCE-LEDGER", "OPEN-ASSERTION", "CLAIM-VALIDATION",
        "FORECAST-REGISTRY", "STRESS-TEST", "AI-BOUNDARY",
    )),
}
if len(BASE_ADDITIONAL_IDS) != 92:
    raise RuntimeError(f"base additional ID oracle drifted: {len(BASE_ADDITIONAL_IDS)}")

AUDITED_EXPANSION_IDS: set[str] = set()
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-S{state}-{suffix}"
    for state in range(7)
    for suffix in ("E1", "E2", "X1", "X2", "O1", "O2", "O3", "O4")
)
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-{code}"
    for code in (
        "COUNTEREXAMPLE-REGISTRY", "CASE-REGISTRY", "CLAIM-REGISTRY",
        "FORECAST-REGISTRY", "VERSION-LOG", "WEAK-SIGNAL-PROTECTION",
        "WS1", "WS2", "WS3", "WS4", "WS5", "WS6",
        "NO-INFRASTRUCTURE-PATH", "INABILITY-TO-EXIT-PROTECTION",
        "TRAUMA-NO-HEALTHY-BASELINE",
    )
)
AUDITED_EXPANSION_IDS.update(f"V8-CANON-D0-{code}" for code in ("B", "X", "R", "I", "T", "SP", "K"))
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-D1-{code}"
    for code in ("CHANGE", "OPERATION", "PERSISTENCE", "EVOLUTION", "DISSOLUTION", "REPAIR")
)
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-{code}"
    for code in (
        "U03-STATE", "U03-OBSERVABLE", "U04-COMPONENT", "U04-CARRIER", "U04-SUBSTRATE",
        "U05-RELATION", "U05-CONSTRAINT", "U06-FLOW", "U06-CHANNEL", "U06-CONDUCTION",
        "U07-STATE-UPDATE", "U08-CONDITION", "U08-ENVIRONMENT", "U09-LOAD", "U09-CAPACITY",
        "U09-RECOVERY-MARGIN", "U10-TRACE", "U10-MEMORY", "U10-PATH-DIFFERENCE",
        "U11-PHASE", "U11-TRANSITION",
    )
)
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-{code}"
    for code in (
        "C3-FEEDBACK", "C3-LEARNING", "C5-INSTANT", "C5-CUMULATIVE",
        "C8-PATTERN", "C8-MECHANISM", "C9-RESPONSE", "C9-PERSISTENT",
        "C10-CURRENT", "C10-INTERTEMPORAL", "C10-HISTORICAL-CARRIER",
        "C8-V", "C8-D", "C8-R",
    )
)
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-TASK-{code}"
    for code in ("EXPLANATION", "DIAGNOSIS", "NORMATIVE-SELECTION", "INTERVENTION")
)
AUDITED_EXPANSION_IDS.update(
    f"V8-CANON-{code}"
    for code in (
        "ONTOLOGY-GENERAL-EMPIRICAL-STRUCTURAL-WORLD", "CORE-TERM-COST",
        "CORE-TERM-EXTERNALITY", "CORE-TERM-SELECTION", "CORE-TERM-RESPONSIBILITY",
        "CORE-TERM-AUTHORIZATION",
    )
)
for prefix, values in (
    ("VOCAB-GOV-ROOT-HYPOTHESIS-", ("NORMAL-USE", "BOUNDARY-RESTRICTED", "SUSPENDED", "REPLACEMENT-COMPETITION", "RETIRED-FROM-CORE")),
    ("VOCAB-GOV-PUBLIC-CLAIM-", ("INTERNAL-DRAFT", "OPEN-ASSERTION", "PUBLISHABLE", "DOWNGRADED", "SUSPENDED", "PUBLICATION-BLOCKED", "WITHDRAWN", "REPLACED")),
    ("VOCAB-GOV-FRAMEWORK-", ("ACTIVE", "BOUNDARY-RESTRICTED", "SUSPENDED", "REPLACEMENT-COMPETITION", "REPLACED", "RETIRED")),
    ("VOCAB-GOV-PRECONCEPT-", ("EXPRESSIVE", "EXPLORATORY", "DIAGNOSTIC", "STRONG-JUDGMENT", "DISPOSITION")),
    ("VOCAB-GOV-OPACITY-", ("PROTECTED", "FUNCTIONAL", "SUPPRESSIVE")),
    ("VOCAB-GOV-REPLACEMENT-", ("RESTRICT", "SUSPEND", "COMPETE", "REPLACE", "RETIRE", "HANDOFF")),
    ("VOCAB-GOV-TRAUMA-", ("DEVIATED-FROM-HEALTHIER", "HOLLOW-NOMINAL-ANCHOR", "INITIAL-NO-HEALTHY-ANCHOR", "TRAUMA-BUILT")),
):
    AUDITED_EXPANSION_IDS.update(f"V8-CANON-{prefix}{value}" for value in values)
for prefix, values in (
    ("VOCAB-CLAIM-MODE-", ("DESCRIPTIVE-MAPPING", "ROOT-HYPOTHESIS", "CAUSAL", "OBJECT-CONVERSION", "INTERVENTION-CONVERSION")),
    ("VOCAB-M02-BRANCH-", ("DESCRIPTIVE-NESTING", "CROSS-LAYER-CAUSAL", "OBJECT-CONVERSION", "INTERVENTION-CONVERSION")),
    ("VOCAB-M05-BRANCH-", ("INSTITUTIONAL-FACT", "INSTITUTIONAL-CAUSAL-EFFECT", "INSTITUTIONAL-OBJECT-CONVERSION", "INSTITUTIONAL-INTERVENTION-CONVERSION")),
    ("VOCAB-M07-BRANCH-", ("REPRESENTATION-CLAIM", "ACTUAL-ACTS", "DELEGATION-VALIDITY", "J-TRANSFER")),
    ("VOCAB-IDENTITY-PREDICATE-RESULT-", ("PASSED", "FAILED", "UNDETERMINED")),
    ("VOCAB-K-MAPPING-CLASS-", ("SAME-OBJECT", "CONVERTED-OBJECT", "INCOMPARABLE", "UNDETERMINED")),
):
    AUDITED_EXPANSION_IDS.update(f"V8-CANON-{prefix}{value}" for value in values)
for prefix, values in (
    ("VOCAB-HSP-CLASSIFICATION-MODE-", ("SINGLE-DOMINANT", "MIXED", "PARALLEL", "UNKNOWN")),
    ("VOCAB-HSP-MISSING-STATUS-", ("NOT-COLLECTED", "NOT-OBSERVABLE", "NOT-APPLICABLE", "CONFLICTED", "UNKNOWN")),
    ("VOCAB-HSP-PATH-", ("MIXED", "PARALLEL", "JUMP", "REGRESSION", "SPLIT", "MERGE", "DORMANCY", "TAKEOVER", "FUNCTIONAL-TRANSFER", "PARADIGM-REPLACEMENT", "TRAUMA-BUILT-DEVELOPMENT", "PSEUDO-STEADY", "FORCED-REWRITE", "EXTERNAL-CARRIER-MIGRATION", "COLLAPSE")),
    ("VOCAB-X0-RESULT-", ("CANDIDATE", "IN-PROGRESS", "PARTIALLY-COMPLETED", "COMPLETED", "UNKNOWN")),
):
    AUDITED_EXPANSION_IDS.update(f"V8-CANON-{prefix}{value}" for value in values)
AUDITED_EXPANSION_IDS.add("V8-CANON-VOCAB-X0-ORIGIN-POLICY-ANY-REGISTERED-ORIGIN")
for prefix, values in (
    ("VOCAB-TOOL-OUTPUT-", ("COMPARATIVE-JUDGMENT", "STRONG-JUDGMENT", "ACTION-REQUIREMENTS")),
    ("VOCAB-TOOL-OUTPUT-CEILING-", ("DESCRIPTION-ONLY", "DIAGNOSTIC-ONLY", "REQUIREMENTS-ONLY")),
    ("VOCAB-TOOL-RECORD-GATE-", ("PASSED", "FAILED", "NOT-RUN")),
    ("VOCAB-SELECTION-OPTION-KIND-", ("SYSTEM-VARIANT", "EXTERNAL-ACTION")),
    ("VOCAB-DISSENT-STATUS-", ("OPEN", "PROTECTED-AND-PENDING", "UNRESOLVED-ACTION-PAUSED")),
    ("VOCAB-PF-BINDING-STATUS-", ("ACTIVE", "PENDING", "FAILED", "NOT-APPLICABLE")),
    ("VOCAB-EXECUTION-STATE-", ("DRAFT", "ACTIVE", "ROLLED-BACK", "COMPLETED", "EXPIRED", "WITHDRAWN")),
):
    AUDITED_EXPANSION_IDS.update(f"V8-CANON-{prefix}{value}" for value in values)
for prefix, values in (
    ("VOCAB-ROOT-PREREGISTRATION-STATUS-", ("DRAFT", "FROZEN-BEFORE-EVIDENCE", "COMPLETED-FROM-FROZEN", "DEVIATED-AFTER-EVIDENCE")),
    ("VOCAB-ROOT-EVIDENCE-MODE-", ("CONFIRMATORY", "REPLICATION", "FALSIFICATION", "EXPLORATORY")),
    ("VOCAB-ROOT-INSTANCE-RESULT-", ("SUPPORTED", "UNSUPPORTED-OR-UNDECIDED", "NULL-SUPPORTED", "NOT-EVALUATED")),
    ("VOCAB-G1-SUCCESS-CRITERION-", ("OUT-OF-SAMPLE-PREDICTIVE-GAIN", "OUT-OF-SAMPLE-INTERVENTION-GAIN")),
    ("VOCAB-G2-SUCCESS-CRITERION-", ("CONTROLLED-PERTURBATION-EFFECT", "CONTROLLED-INTERVENTION-EFFECT", "IDENTIFIED-NATURAL-VARIATION-CHANNEL-EFFECT")),
    ("VOCAB-G3-SUCCESS-CRITERION-", ("HISTORICAL-CONDITIONAL-PREDICTIVE-GAIN", "HISTORY-ERASURE-EFFECT", "HISTORY-RESTORATION-EFFECT", "EQUIVALENT-INTERVENTION-EFFECT")),
    ("VOCAB-G4-SUCCESS-CRITERION-", ("CONDITIONAL-INFORMATION-GAIN", "CONDITIONAL-PREDICTIVE-GAIN", "CONDITIONAL-INTERVENTION-GAIN", "OBJECT-DYNAMICS-NON-COMMUTATION", "INTERVENTION-NON-COMMUTATION", "IDENTITY-CRITERION-VIOLATION", "EFFECTIVE-RELATION-CHANGE", "INTERVENTION-RESPONSE-CHANGE")),
    ("VOCAB-H1-SELECTED-FAMILY-", ("RESOURCE-ALLOCATION-OUTCOME", "ACTION-CHOICE-OUTCOME", "COORDINATION-OUTCOME")),
    ("VOCAB-H1-SUCCESS-CRITERION-", ("MEANING-ARRANGEMENT-RESOURCE-ALLOCATION-EFFECT", "MEANING-ARRANGEMENT-ACTION-CHOICE-EFFECT", "MEANING-ARRANGEMENT-COORDINATION-OUTCOME-EFFECT")),
    ("VOCAB-H4-SELECTED-FAMILY-", ("EVIDENCE-COVERAGE", "EXPRESSION-SAFETY", "OBJECT-BEHAVIOR", "REFLEXIVE-RESPONSE")),
    ("VOCAB-H4-SUCCESS-CRITERION-", ("POSITION-OR-MEDIATION-EVIDENCE-COVERAGE-EFFECT", "POSITION-OR-MEDIATION-EXPRESSION-SAFETY-EFFECT", "MEDIATION-OR-PUBLICITY-BEHAVIORAL-RESPONSE-EFFECT", "OBSERVATION-OR-PUBLICATION-REFLEXIVE-RESPONSE-EFFECT")),
    ("VOCAB-H5-SELECTED-FAMILY-", ("INSTITUTIONAL-OR-TEXTUAL-RECORD", "ROLE-OR-ORGANIZATIONAL-ARRANGEMENT", "HABIT-OR-PRACTICE", "TRAUMA-RECORD", "COLLECTIVE-MEMORY-CARRIER")),
    ("VOCAB-H5-SUCCESS-CRITERION-", ("THRESHOLD-PERSISTENCE-OVER-PREREGISTERED-WINDOW", "REPEAT-DETECTION-ACROSS-PREREGISTERED-WINDOWS", "PERSISTENCE-AFTER-EVENT-OR-EXPOSURE-END")),
):
    AUDITED_EXPANSION_IDS.update(f"V8-CANON-{prefix}{value}" for value in values)
AUDITED_EXPANSION_IDS.update(f"V8-CANON-RESPONSIBILITY-LAYER-{code}" for code in ("U", "S", "H", "A", "MC", "P", "I", "N"))
AUDITED_EXPANSION_IDS.update({"V8-CANON-STRONG-JUDGMENT-TEN-QUESTIONS", "V8-CANON-PROTECTION-FLOOR"})
AUDITED_EXPANSION_IDS.update({"V8-CANON-PERSONALITY-HYPOTHESIS", "V8-CANON-ROLE-ACTIVATION"})
AUDITED_EXPANSION_IDS.update(f"V8-CANON-UPDATE-PROVENANCE-{code}" for code in ("DIRECT-OBSERVATION", "MECHANISM-INFERENCE", "SCENARIO-VALUE", "UNEXPLAINED-RESIDUAL"))
AUDITED_EXPANSION_IDS.update({"V8-CANON-CROSS-CIRCLE-CASCADE", "V8-CANON-BRANCHING-PATH-GRAPH", "V8-CANON-VARIABLE-CANDIDATE-LEDGER"})
AUDITED_EXPANSION_IDS.update(f"V8-CANON-CROSS-CIRCLE-CASCADE-{code}" for code in ("MEMBERSHIP", "RESOURCE", "MEANING", "INSTITUTIONAL", "PLATFORM"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-INFERENCE-MODE-{code}" for code in ("SCENARIO", "COUNTERFACTUAL", "SIMULATION"))
AUDITED_EXPANSION_IDS.update({"V8-CANON-SIMPLE-FORECAST-BASELINE", "V8-CANON-FORECAST-ACTION-CEILING", "V8-CANON-INFORMATIONAL-EXPERIMENT"})
AUDITED_EXPANSION_IDS.update(f"V8-CANON-FORECAST-EVALUATION-{code}" for code in ("CALIBRATION", "RESOLUTION", "COVERAGE", "BASELINE-GAIN", "STABILITY", "DISTRIBUTIONAL-ERROR"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-FORECAST-SIGNAL-{code}" for code in ("EARLY", "REVERSE", "TRIGGER"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-FORECAST-PUBLICATION-STATUS-{code}" for code in ("EXPLANATION-ONLY", "SIMULATION-ONLY", "REGISTERED-FORECAST", "NORMATIVE-NOT-PASSED", "EXTERNALLY-AUTHORIZED"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-GOVERNANCE-DEBT-{code}" for code in ("OBJECT", "VARIABLE", "COMPLEXITY", "CALIBRATION", "POWER"))
AUDITED_EXPANSION_IDS.add("V8-CANON-AUTONOMOUS-REFINEMENT-VARIABLE-CEILING")
AUDITED_EXPANSION_IDS.update(f"V8-CANON-ACTOR-CIRCLE-DIRECTION-{code}" for code in ("CIRCLE-TO-ACTOR", "ACTOR-TO-CIRCLE", "BIDIRECTIONAL-FEEDBACK"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-CROSS-CHANNEL-BRIDGE-{code}" for code in ("M-TO-PSI", "PSI-TO-M", "M-PSI-CLOSED-LOOP"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-CANDIDATE-SOURCE-{code}" for code in ("SYSTEM-RESIDUAL", "PARTICIPANT-NARRATIVE", "CROSS-CASE-REPETITION", "MODEL-SEARCH", "AI-SUGGESTION"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-SELF-DIAGNOSIS-OBJECT-{code}" for code in ("DOCUMENT", "CONCEPT", "PRACTICE", "COMMUNITY"))
AUDITED_EXPANSION_IDS.update(f"V8-CANON-CONSENSUS-COMPONENT-{code}" for code in ("ISSUE-REGISTRATION", "MATERIAL-DISCLOSURE", "AFFECTED-OBJECT-IDENTIFICATION", "DISSENT-ENTRY", "DECISION-GRADING", "MINORITY-OPINION-RETENTION"))
if len(AUDITED_EXPANSION_IDS) != 366:
    raise RuntimeError(f"audited expansion ID oracle drifted: {len(AUDITED_EXPANSION_IDS)}")

EXPECTED_CANONICAL_IDS = (
    REQUIRED_CONCEPT_IDS
    | REQUIRED_VOCABULARY_IDS
    | BASE_ADDITIONAL_IDS
    | AUDITED_EXPANSION_IDS
)
if len(EXPECTED_CANONICAL_IDS) != EXPECTED_CANONICAL_CONCEPT_COUNT:
    raise RuntimeError(f"canonical ID oracle drifted: {len(EXPECTED_CANONICAL_IDS)}")
if hashlib.sha256(("\n".join(sorted(EXPECTED_CANONICAL_IDS)) + "\n").encode("utf-8")).hexdigest() != EXPECTED_CANONICAL_INVENTORY_SHA256:
    raise RuntimeError("canonical ID oracle digest drifted")

ACTOR_STATE_FAMILY = {
    f"V8-CANON-VOCAB-ACTOR-STATE-{item}"
    for item in ("UNKNOWN", "CANDIDATE", "SUPPORTED-HYPOTHESIS", "OBSERVED", "CONTESTED", "RETIRED")
}
ACTOR_BAND_FAMILY = {
    f"V8-CANON-VOCAB-ACTOR-BAND-{item}" for item in ("SLOW", "MEDIUM", "FAST")
}
PRIVACY_FAMILY = {
    f"V8-CANON-VOCAB-PRIVACY-{item}"
    for item in ("PUBLIC", "CONTEXT-LIMITED", "SENSITIVE", "HIGHLY-SENSITIVE", "WITHHELD")
}
RELATION_FAMILY = {
    f"V8-CANON-VOCAB-CIRCLE-RELATION-{item}"
    for item in ("PARALLEL", "NESTED", "OVERLAPPING", "BRIDGING", "COMPETITIVE", "TEMPORARY")
}
TRANSITION_FAMILY = {
    f"V8-CANON-VOCAB-CIRCLE-TRANSITION-{item}"
    for item in ("UNCHANGED", "STRENGTHENED", "WEAKENED", "REORIENTED", "TRANSFORMED", "DISSOLVED", "UNKNOWN")
}
CHANNEL_FAMILY = {
    "V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL",
    "V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING",
}
CLOCK_FAMILY = {
    f"V8-CANON-VOCAB-CLOCK-{item}"
    for item in ("IMMEDIATE", "INTERACTION", "ORGANIZATIONAL", "INSTITUTIONAL", "LONG-TERM")
}
EVENT_FAMILY = {
    f"V8-CANON-VOCAB-EVENT-{item}"
    for item in ("OBSERVED", "REPORTED", "PLANNED", "HYPOTHETICAL", "SIMULATED")
}
BRANCH_FAMILY = {
    f"V8-CANON-VOCAB-BRANCH-{item}"
    for item in ("FACT", "MECHANISM", "CHOICE", "EXOGENOUS-DISTURBANCE")
}
LEDGER_FAMILY = {
    f"V8-CANON-VOCAB-LEDGER-{item}"
    for item in ("PROPOSED", "UNDER-TEST", "SUPPORTED-CANDIDATE", "REJECTED", "RETIRED")
}
OPTION_FAMILY = {
    f"V8-CANON-VOCAB-OPTION-{item}"
    for item in ("MAINTAIN-STATUS-QUO", "ACTIVE-ACTION", "DELAYED-ACTION", "PROBE-ACTION", "EXIT-OR-TRANSFER", "NO-ACTION")
}
FORECAST_RESULT_FAMILY = {
    f"V8-CANON-VOCAB-FORECAST-RESULT-{item}"
    for item in ("SUPPORTED", "UNSUPPORTED", "UNDECIDED", "TARGET-INVALID", "UNASSESSABLE")
}

EXPECTED_BOUND_CONCEPT_IDS: dict[str, dict[str, list[str]]] = {'v8_actor_state_contracts': {'/actor_record_schema': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/0': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/1': ['V8-CANON-D0-T'],
                              '/actor_record_schema/required_fields/2': ['V8-CANON-D0-SP'],
                              '/actor_record_schema/required_fields/3': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/actor_record_schema/required_fields/4': ['V8-CANON-ROLE-ACTIVATION'],
                              '/actor_record_schema/required_fields/5': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/6': ['V8-CANON-ACTOR-STATE'],
                              '/actor_record_schema/required_fields/7': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                                                         'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                                                         'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                                                         'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                                                         'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/actor_record_schema/required_fields/8': ['V8-CANON-ACTOR-STATE'],
                              '/guards': ['V8-CANON-ACTOR-STATE'],
                              '/guards/0': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/guards/1': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                            'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                            'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS'],
                              '/guards/2': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/guards/3': ['V8-CANON-ROLE-ACTIVATION'],
                              '/guards/4': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                            'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                            'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                            'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                            'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/guards/5': ['V8-CANON-CORE-TERM-AUTHORIZATION'],
                              '/guards/6': ['V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/personality_hypothesis_contract': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/0': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/1': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/2': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/3': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/forbidden_outputs/4': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/1': ['V8-CANON-ACTOR-STATE'],
                              '/personality_hypothesis_contract/required_fields/10': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                                                      'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/personality_hypothesis_contract/required_fields/11': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/12': ['V8-CANON-D0-T'],
                              '/personality_hypothesis_contract/required_fields/2': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/3': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/4': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/5': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/personality_hypothesis_contract/required_fields/6': ['V8-CANON-D0-T'],
                              '/personality_hypothesis_contract/required_fields/7': ['V8-CANON-SOURCE-CONTRACT'],
                              '/personality_hypothesis_contract/required_fields/8': ['V8-CANON-E4'],
                              '/personality_hypothesis_contract/required_fields/9': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/personality_hypothesis_contract/status': ['V8-CANON-PERSONALITY-HYPOTHESIS'],
                              '/privacy_levels': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                                  'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                                  'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                                  'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                                  'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/privacy_levels/0': ['V8-CANON-VOCAB-PRIVACY-PUBLIC'],
                              '/privacy_levels/1': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED'],
                              '/privacy_levels/2': ['V8-CANON-VOCAB-PRIVACY-SENSITIVE'],
                              '/privacy_levels/3': ['V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE'],
                              '/privacy_levels/4': ['V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/scope': ['V8-CANON-ACTOR-STATE'],
                              '/timescale_bands': ['V8-CANON-VOCAB-ACTOR-BAND-FAST',
                                                   'V8-CANON-VOCAB-ACTOR-BAND-MEDIUM',
                                                   'V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/definition': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/0': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/1': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/2': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/3': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/examples/4': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/id': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/minimum_evidence': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/0/name': ['V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/timescale_bands/1': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/definition': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/0': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/1': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/2': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/3': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/examples/4': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/id': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/minimum_evidence': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/1/name': ['V8-CANON-VOCAB-ACTOR-BAND-MEDIUM'],
                              '/timescale_bands/2': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/definition': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/0': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/1': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/2': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/3': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/examples/4': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/id': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/minimum_evidence': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/timescale_bands/2/name': ['V8-CANON-VOCAB-ACTOR-BAND-FAST'],
                              '/variable_record_schema': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/1': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/10': ['V8-CANON-E4'],
                              '/variable_record_schema/required_fields/11': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/variable_record_schema/required_fields/12': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_record_schema/required_fields/13': ['V8-CANON-VOCAB-PRIVACY-CONTEXT-LIMITED',
                                                                             'V8-CANON-VOCAB-PRIVACY-HIGHLY-SENSITIVE',
                                                                             'V8-CANON-VOCAB-PRIVACY-PUBLIC',
                                                                             'V8-CANON-VOCAB-PRIVACY-SENSITIVE',
                                                                             'V8-CANON-VOCAB-PRIVACY-WITHHELD'],
                              '/variable_record_schema/required_fields/14': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/15': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/3': ['V8-CANON-VOCAB-ACTOR-BAND-FAST',
                                                                            'V8-CANON-VOCAB-ACTOR-BAND-MEDIUM',
                                                                            'V8-CANON-VOCAB-ACTOR-BAND-SLOW'],
                              '/variable_record_schema/required_fields/4': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                                            'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_record_schema/required_fields/5': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/6': ['V8-CANON-D0-T'],
                              '/variable_record_schema/required_fields/7': ['V8-CANON-SOURCE-CONTRACT'],
                              '/variable_record_schema/required_fields/8': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/required_fields/9': ['V8-CANON-ACTOR-STATE'],
                              '/variable_record_schema/state_upgrade_rule': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                                             'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS'],
                              '/variable_record_schema/unknown_rule': ['V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_states': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-CONTESTED',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-OBSERVED',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-RETIRED',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS',
                                                   'V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_states/0': ['V8-CANON-VOCAB-ACTOR-STATE-OBSERVED'],
                              '/variable_states/1': ['V8-CANON-VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS'],
                              '/variable_states/2': ['V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE'],
                              '/variable_states/3': ['V8-CANON-VOCAB-ACTOR-STATE-CONTESTED'],
                              '/variable_states/4': ['V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN'],
                              '/variable_states/5': ['V8-CANON-VOCAB-ACTOR-STATE-RETIRED']},
 'v8_multicircle_contracts': {'/circle_record_schema': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/object_rule': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/0': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/10': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING'],
                              '/circle_record_schema/required_fields/11': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/12': ['V8-CANON-D0-T'],
                              '/circle_record_schema/required_fields/13': ['V8-CANON-D0-SP'],
                              '/circle_record_schema/required_fields/14': ['V8-CANON-D0-K'],
                              '/circle_record_schema/required_fields/15': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/circle_record_schema/required_fields/16': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/circle_record_schema/required_fields/17': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/2': ['V8-CANON-D0-B'],
                              '/circle_record_schema/required_fields/3': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/4': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/5': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/6': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/7': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/8': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/circle_record_schema/required_fields/9': ['V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/clock_kinds': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                               'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                               'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                               'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                               'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/clock_kinds/0': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE'],
                              '/clock_kinds/1': ['V8-CANON-VOCAB-CLOCK-INTERACTION'],
                              '/clock_kinds/2': ['V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/clock_kinds/3': ['V8-CANON-VOCAB-CLOCK-INSTITUTIONAL'],
                              '/clock_kinds/4': ['V8-CANON-VOCAB-CLOCK-LONG-TERM'],
                              '/condition_channels': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                      'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/condition_channels/0': ['V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/condition_channels/1': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING'],
                              '/event_touch_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/asynchronous_rule': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/1': ['V8-CANON-ACTOR-STATE'],
                              '/event_touch_schema/required_fields/2': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/event_touch_schema/required_fields/3': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/4': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                        'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/event_touch_schema/required_fields/5': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                                                        'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                                                        'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                                                        'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                                                        'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/event_touch_schema/required_fields/6': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/7': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/8': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/event_touch_schema/required_fields/9': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/guards': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/guards/0': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/guards/1': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-NESTED',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL',
                                            'V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/guards/2': ['V8-CANON-CROSS-CHANNEL-BRIDGE-M-PSI-CLOSED-LOOP',
                                            'V8-CANON-CROSS-CHANNEL-BRIDGE-M-TO-PSI',
                                            'V8-CANON-CROSS-CHANNEL-BRIDGE-PSI-TO-M',
                                            'V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                            'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/guards/3': ['V8-CANON-ACTOR-CIRCLE-DIRECTION-ACTOR-TO-CIRCLE',
                                            'V8-CANON-ACTOR-CIRCLE-DIRECTION-BIDIRECTIONAL-FEEDBACK',
                                            'V8-CANON-ACTOR-CIRCLE-DIRECTION-CIRCLE-TO-ACTOR'],
                              '/guards/4': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/guards/5': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/1': ['V8-CANON-D0-T'],
                              '/joint_state_schema/required_fields/10': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                                                         'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                                                         'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                                                         'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                                                         'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                              '/joint_state_schema/required_fields/11': ['V8-CANON-D0-SP'],
                              '/joint_state_schema/required_fields/12': ['V8-CANON-D0-T'],
                              '/joint_state_schema/required_fields/13': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/14': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/15': ['V8-CANON-D0-K'],
                              '/joint_state_schema/required_fields/16': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/2': ['V8-CANON-ACTOR-STATE'],
                              '/joint_state_schema/required_fields/3': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/joint_state_schema/required_fields/4': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/5': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/joint_state_schema/required_fields/6': ['V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/joint_state_schema/required_fields/7': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING'],
                              '/joint_state_schema/required_fields/8': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                        'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/joint_state_schema/required_fields/9': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/1': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/10': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/2': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/membership_record_schema/required_fields/3': ['V8-CANON-ROLE-ACTIVATION'],
                              '/membership_record_schema/required_fields/4': ['V8-CANON-D0-T'],
                              '/membership_record_schema/required_fields/5': ['V8-CANON-D0-T'],
                              '/membership_record_schema/required_fields/6': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/7': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/8': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/membership_record_schema/required_fields/9': ['V8-CANON-SOURCE-CONTRACT'],
                              '/relation_kinds': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-NESTED',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL',
                                                  'V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/relation_kinds/0': ['V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL'],
                              '/relation_kinds/1': ['V8-CANON-VOCAB-CIRCLE-RELATION-NESTED'],
                              '/relation_kinds/2': ['V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING'],
                              '/relation_kinds/3': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING'],
                              '/relation_kinds/4': ['V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE'],
                              '/relation_kinds/5': ['V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/relation_record_schema': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/nested_rule': ['V8-CANON-VOCAB-CIRCLE-RELATION-NESTED'],
                              '/relation_record_schema/parallel_rule': ['V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL'],
                              '/relation_record_schema/required_fields': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/1': ['V8-CANON-VOCAB-CIRCLE-RELATION-BRIDGING',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-COMPETITIVE',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-NESTED',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-OVERLAPPING',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-PARALLEL',
                                                                            'V8-CANON-VOCAB-CIRCLE-RELATION-TEMPORARY'],
                              '/relation_record_schema/required_fields/10': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/11': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/relation_record_schema/required_fields/12': ['V8-CANON-EVIDENCE-CONTRACT'],
                              '/relation_record_schema/required_fields/13': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/14': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-DISSOLVED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-REORIENTED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-STRENGTHENED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNCHANGED',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN',
                                                                             'V8-CANON-VOCAB-CIRCLE-TRANSITION-WEAKENED'],
                              '/relation_record_schema/required_fields/2': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/relation_record_schema/required_fields/3': ['V8-CANON-CIRCLE-CANDIDATE'],
                              '/relation_record_schema/required_fields/4': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/5': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/6': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                            'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                              '/relation_record_schema/required_fields/7': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                              '/relation_record_schema/required_fields/8': ['V8-CANON-D0-T'],
                              '/relation_record_schema/required_fields/9': ['V8-CANON-D0-T'],
                              '/relation_record_schema/transformation_rule': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED'],
                              '/relation_transition_results': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-DISSOLVED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-REORIENTED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-STRENGTHENED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNCHANGED',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN',
                                                               'V8-CANON-VOCAB-CIRCLE-TRANSITION-WEAKENED'],
                              '/relation_transition_results/0': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-UNCHANGED'],
                              '/relation_transition_results/1': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-STRENGTHENED'],
                              '/relation_transition_results/2': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-WEAKENED'],
                              '/relation_transition_results/3': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-REORIENTED'],
                              '/relation_transition_results/4': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-TRANSFORMED'],
                              '/relation_transition_results/5': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-DISSOLVED'],
                              '/relation_transition_results/6': ['V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN'],
                              '/scope': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT']},
 'v8_simulation_forecast_contracts': {'/authorization_policy': ['V8-CANON-FORECAST-ACTION-CEILING',
                                                                'V8-CANON-O3',
                                                                'V8-CANON-SCALE-AXIS-J'],
                                      '/baseline_policy': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/event_kinds': ['V8-CANON-VOCAB-EVENT-HYPOTHETICAL',
                                                       'V8-CANON-VOCAB-EVENT-OBSERVED',
                                                       'V8-CANON-VOCAB-EVENT-PLANNED',
                                                       'V8-CANON-VOCAB-EVENT-REPORTED',
                                                       'V8-CANON-VOCAB-EVENT-SIMULATED'],
                                      '/event_kinds/0': ['V8-CANON-VOCAB-EVENT-OBSERVED'],
                                      '/event_kinds/1': ['V8-CANON-VOCAB-EVENT-REPORTED'],
                                      '/event_kinds/2': ['V8-CANON-VOCAB-EVENT-PLANNED'],
                                      '/event_kinds/3': ['V8-CANON-VOCAB-EVENT-HYPOTHETICAL'],
                                      '/event_kinds/4': ['V8-CANON-VOCAB-EVENT-SIMULATED'],
                                      '/event_record_schema/required_fields/1': ['V8-CANON-VOCAB-EVENT-HYPOTHETICAL',
                                                                                 'V8-CANON-VOCAB-EVENT-OBSERVED',
                                                                                 'V8-CANON-VOCAB-EVENT-PLANNED',
                                                                                 'V8-CANON-VOCAB-EVENT-REPORTED',
                                                                                 'V8-CANON-VOCAB-EVENT-SIMULATED'],
                                      '/event_record_schema/required_fields/11': ['V8-CANON-E4'],
                                      '/event_record_schema/required_fields/13': ['V8-CANON-D0-T'],
                                      '/event_record_schema/required_fields/14': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/event_record_schema/required_fields/2': ['V8-CANON-D0-T'],
                                      '/event_record_schema/required_fields/3': ['V8-CANON-D0-T'],
                                      '/event_record_schema/required_fields/4': ['V8-CANON-SOURCE-CONTRACT'],
                                      '/event_record_schema/required_fields/5': ['V8-CANON-ACTOR-STATE'],
                                      '/event_record_schema/required_fields/6': ['V8-CANON-CIRCLE-CANDIDATE'],
                                      '/event_record_schema/required_fields/7': ['V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING',
                                                                                 'V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL'],
                                      '/event_record_schema/required_fields/9': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/forecast_record_schema': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/comparison_rule': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/forecast_record_schema/metric_rule': ['V8-CANON-FORECAST-EVALUATION-CALIBRATION',
                                                                              'V8-CANON-FORECAST-EVALUATION-COVERAGE'],
                                      '/forecast_record_schema/required_fields': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/0': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/1': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/10': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/forecast_record_schema/required_fields/11': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/12': ['V8-CANON-FORECAST-EVALUATION-CALIBRATION'],
                                      '/forecast_record_schema/required_fields/13': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/14': ['V8-CANON-FORECAST-SIGNAL-EARLY'],
                                      '/forecast_record_schema/required_fields/15': ['V8-CANON-FORECAST-SIGNAL-REVERSE'],
                                      '/forecast_record_schema/required_fields/16': ['V8-CANON-FORECAST-SIGNAL-TRIGGER'],
                                      '/forecast_record_schema/required_fields/17': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/18': ['V8-CANON-DF9'],
                                      '/forecast_record_schema/required_fields/19': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/2': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/20': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/forecast_record_schema/required_fields/3': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/4': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/5': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/forecast_record_schema/required_fields/6': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/7': ['V8-CANON-D0-T'],
                                      '/forecast_record_schema/required_fields/8': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/forecast_record_schema/required_fields/9': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/guards': ['V8-CANON-DF9',
                                                  'V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST',
                                                  'V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE',
                                                  'V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/guards/0': ['V8-CANON-BRANCHING-PATH-GRAPH',
                                                    'V8-CANON-FORECAST-SIGNAL-REVERSE'],
                                      '/guards/1': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/guards/2': ['V8-CANON-DF9',
                                                    'V8-CANON-FORECAST-EVALUATION-CALIBRATION',
                                                    'V8-CANON-FORECAST-REGISTRY',
                                                    'V8-CANON-FORECAST-SIGNAL-TRIGGER',
                                                    'V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/guards/3': ['V8-CANON-FORECAST-ACTION-CEILING',
                                                    'V8-CANON-O3',
                                                    'V8-CANON-SCALE-AXIS-J'],
                                      '/guards/4': ['V8-CANON-VOCAB-OPTION-NO-ACTION',
                                                    'V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/guards/5': ['V8-CANON-DF9'],
                                      '/guards/6': ['V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/option_record_schema': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/1': ['V8-CANON-VOCAB-OPTION-ACTIVE-ACTION',
                                                                                  'V8-CANON-VOCAB-OPTION-DELAYED-ACTION',
                                                                                  'V8-CANON-VOCAB-OPTION-EXIT-OR-TRANSFER',
                                                                                  'V8-CANON-VOCAB-OPTION-MAINTAIN-STATUS-QUO',
                                                                                  'V8-CANON-VOCAB-OPTION-NO-ACTION',
                                                                                  'V8-CANON-VOCAB-OPTION-PROBE-ACTION'],
                                      '/option_record_schema/required_fields/10': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/11': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/12': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/13': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/14': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/15': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/16': ['V8-CANON-SCALE-AXIS-J'],
                                      '/option_record_schema/required_fields/17': ['V8-CANON-DF8'],
                                      '/option_record_schema/required_fields/18': ['V8-CANON-DF8'],
                                      '/option_record_schema/required_fields/2': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/3': ['V8-CANON-FORECAST-REGISTRY'],
                                      '/option_record_schema/required_fields/4': ['V8-CANON-N1',
                                                                                  'V8-CANON-N2',
                                                                                  'V8-CANON-N3',
                                                                                  'V8-CANON-N4',
                                                                                  'V8-CANON-N5'],
                                      '/option_record_schema/required_fields/5': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/6': ['V8-CANON-PF-1',
                                                                                  'V8-CANON-PF-10',
                                                                                  'V8-CANON-PF-2',
                                                                                  'V8-CANON-PF-3',
                                                                                  'V8-CANON-PF-4',
                                                                                  'V8-CANON-PF-5',
                                                                                  'V8-CANON-PF-6',
                                                                                  'V8-CANON-PF-7',
                                                                                  'V8-CANON-PF-8',
                                                                                  'V8-CANON-PF-9'],
                                      '/option_record_schema/required_fields/7': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/option_record_schema/required_fields/8': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/option_record_schema/required_fields/9': ['V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE'],
                                      '/outcome_writeback_schema': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/1': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/10': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/11': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/12': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/13': ['V8-CANON-D0-T'],
                                      '/outcome_writeback_schema/required_fields/2': ['V8-CANON-D0-T'],
                                      '/outcome_writeback_schema/required_fields/3': ['V8-CANON-SOURCE-CONTRACT'],
                                      '/outcome_writeback_schema/required_fields/4': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/5': ['V8-CANON-VOCAB-FORECAST-RESULT-SUPPORTED',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-TARGET-INVALID',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-UNASSESSABLE',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-UNDECIDED',
                                                                                      'V8-CANON-VOCAB-FORECAST-RESULT-UNSUPPORTED'],
                                      '/outcome_writeback_schema/required_fields/6': ['V8-CANON-FORECAST-EVALUATION-CALIBRATION'],
                                      '/outcome_writeback_schema/required_fields/7': ['V8-CANON-FORECAST-EVALUATION-BASELINE-GAIN',
                                                                                      'V8-CANON-SIMPLE-FORECAST-BASELINE'],
                                      '/outcome_writeback_schema/required_fields/8': ['V8-CANON-DF9'],
                                      '/outcome_writeback_schema/required_fields/9': ['V8-CANON-FORECAST-EVALUATION-DISTRIBUTIONAL-ERROR'],
                                      '/path_node_schema': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/dag_rule': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/10': ['V8-CANON-FORECAST-SIGNAL-REVERSE'],
                                      '/path_node_schema/required_fields/11': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/12': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/2': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/3': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/4': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/5': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/6': ['V8-CANON-VOCAB-CLOCK-IMMEDIATE',
                                                                              'V8-CANON-VOCAB-CLOCK-INSTITUTIONAL',
                                                                              'V8-CANON-VOCAB-CLOCK-INTERACTION',
                                                                              'V8-CANON-VOCAB-CLOCK-LONG-TERM',
                                                                              'V8-CANON-VOCAB-CLOCK-ORGANIZATIONAL'],
                                      '/path_node_schema/required_fields/7': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/8': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/path_node_schema/required_fields/9': ['V8-CANON-FORECAST-SIGNAL-EARLY'],
                                      '/required_option_kinds': ['V8-CANON-VOCAB-OPTION-ACTIVE-ACTION',
                                                                 'V8-CANON-VOCAB-OPTION-DELAYED-ACTION',
                                                                 'V8-CANON-VOCAB-OPTION-EXIT-OR-TRANSFER',
                                                                 'V8-CANON-VOCAB-OPTION-MAINTAIN-STATUS-QUO',
                                                                 'V8-CANON-VOCAB-OPTION-NO-ACTION',
                                                                 'V8-CANON-VOCAB-OPTION-PROBE-ACTION'],
                                      '/required_option_kinds/0': ['V8-CANON-VOCAB-OPTION-MAINTAIN-STATUS-QUO'],
                                      '/required_option_kinds/1': ['V8-CANON-VOCAB-OPTION-ACTIVE-ACTION'],
                                      '/required_option_kinds/2': ['V8-CANON-VOCAB-OPTION-DELAYED-ACTION'],
                                      '/required_option_kinds/3': ['V8-CANON-VOCAB-OPTION-PROBE-ACTION'],
                                      '/required_option_kinds/4': ['V8-CANON-VOCAB-OPTION-EXIT-OR-TRANSFER'],
                                      '/required_option_kinds/5': ['V8-CANON-VOCAB-OPTION-NO-ACTION'],
                                      '/scope': ['V8-CANON-DF9',
                                                 'V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST',
                                                 'V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE',
                                                 'V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/1': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/10': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/11': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/12': ['V8-CANON-BRANCHING-PATH-GRAPH'],
                                      '/simulation_run_schema/required_fields/13': ['V8-CANON-FORECAST-SIGNAL-TRIGGER'],
                                      '/simulation_run_schema/required_fields/2': ['V8-CANON-MULTICIRCLE-JOINT-OBJECT'],
                                      '/simulation_run_schema/required_fields/3': ['V8-CANON-D0-T'],
                                      '/simulation_run_schema/required_fields/4': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/5': ['V8-CANON-SCALE-AXIS-J'],
                                      '/simulation_run_schema/required_fields/6': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/7': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/simulation_run_schema/required_fields/8': ['V8-CANON-VOCAB-OUTPUT-SIMULATION'],
                                      '/variable_candidate_ledger_schema': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/allowed_states': ['V8-CANON-VOCAB-LEDGER-PROPOSED',
                                                                                           'V8-CANON-VOCAB-LEDGER-REJECTED',
                                                                                           'V8-CANON-VOCAB-LEDGER-RETIRED',
                                                                                           'V8-CANON-VOCAB-LEDGER-SUPPORTED-CANDIDATE',
                                                                                           'V8-CANON-VOCAB-LEDGER-UNDER-TEST'],
                                      '/variable_candidate_ledger_schema/allowed_states/0': ['V8-CANON-VOCAB-LEDGER-PROPOSED'],
                                      '/variable_candidate_ledger_schema/allowed_states/1': ['V8-CANON-VOCAB-LEDGER-UNDER-TEST'],
                                      '/variable_candidate_ledger_schema/allowed_states/2': ['V8-CANON-VOCAB-LEDGER-SUPPORTED-CANDIDATE'],
                                      '/variable_candidate_ledger_schema/allowed_states/3': ['V8-CANON-VOCAB-LEDGER-REJECTED'],
                                      '/variable_candidate_ledger_schema/allowed_states/4': ['V8-CANON-VOCAB-LEDGER-RETIRED'],
                                      '/variable_candidate_ledger_schema/required_fields': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/1': ['V8-CANON-CANDIDATE-SOURCE-SYSTEM-RESIDUAL'],
                                      '/variable_candidate_ledger_schema/required_fields/10': ['V8-CANON-EVIDENCE-CONTRACT'],
                                      '/variable_candidate_ledger_schema/required_fields/11': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/12': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/2': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/3': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/4': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/5': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/6': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/7': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/8': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/variable_candidate_ledger_schema/required_fields/9': ['V8-CANON-VOCAB-LEDGER-PROPOSED',
                                                                                              'V8-CANON-VOCAB-LEDGER-REJECTED',
                                                                                              'V8-CANON-VOCAB-LEDGER-RETIRED',
                                                                                              'V8-CANON-VOCAB-LEDGER-SUPPORTED-CANDIDATE',
                                                                                              'V8-CANON-VOCAB-LEDGER-UNDER-TEST'],
                                      '/variable_candidate_ledger_schema/truth_rule': ['V8-CANON-VARIABLE-CANDIDATE-LEDGER'],
                                      '/writeback_policy': ['V8-CANON-DF9']}}

EXPECTED_UNBOUND_POINTERS: dict[str, set[str]] = {'v8_actor_state_contracts': {'/actor_record_schema/additional_fields',
                              '/actor_record_schema/required_fields/10',
                              '/actor_record_schema/required_fields/9',
                              '/closed',
                              '/personality_hypothesis_contract/required_fields/0',
                              '/variable_record_schema/additional_fields',
                              '/variable_record_schema/required_fields/0',
                              '/variable_record_schema/required_fields/2'},
 'v8_multicircle_contracts': {'/circle_record_schema/additional_fields',
                              '/circle_record_schema/required_fields/1',
                              '/closed',
                              '/event_touch_schema/additional_fields',
                              '/event_touch_schema/required_fields/0',
                              '/joint_state_schema/additional_fields',
                              '/joint_state_schema/required_fields/0',
                              '/joint_state_schema/schema_id',
                              '/membership_record_schema/additional_fields',
                              '/membership_record_schema/required_fields/0',
                              '/relation_record_schema/additional_fields',
                              '/relation_record_schema/required_fields/0'},
 'v8_simulation_forecast_contracts': {'/closed',
                                      '/event_record_schema',
                                      '/event_record_schema/additional_fields',
                                      '/event_record_schema/required_fields',
                                      '/event_record_schema/required_fields/0',
                                      '/event_record_schema/required_fields/10',
                                      '/event_record_schema/required_fields/12',
                                      '/event_record_schema/required_fields/8',
                                      '/forecast_record_schema/additional_fields',
                                      '/option_record_schema/additional_fields',
                                      '/option_record_schema/required_fields/0',
                                      '/outcome_writeback_schema/additional_fields',
                                      '/outcome_writeback_schema/required_fields/0',
                                      '/path_node_schema/additional_fields',
                                      '/path_node_schema/required_fields/0',
                                      '/path_node_schema/required_fields/1',
                                      '/simulation_run_schema/additional_fields',
                                      '/simulation_run_schema/propagation_rule',
                                      '/simulation_run_schema/required_fields/0',
                                      '/simulation_run_schema/required_fields/14',
                                      '/simulation_run_schema/required_fields/9',
                                      '/variable_candidate_ledger_schema/additional_fields',
                                      '/variable_candidate_ledger_schema/required_fields/0'}}

EXPECTED_OWNER_ORACLE_SHA256 = "5f049ab85f0da320e40a7c12d2fae4663e2fca634c664f134e3f81f5f1035be8"


def owner_oracle_sha256(owner_map: dict[str, dict[str, object]]) -> str:
    rows = [
        [contract_id, pointer, sorted(owners)]
        for contract_id, pointer_map in owner_map.items()
        for pointer, owners in pointer_map.items()
    ]
    encoded = json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":")) + "\n"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_pointer(value, pointer: str):
    current = value
    if pointer == "":
        return current
    for token in pointer.removeprefix("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def sentence_parts_for_test(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。；！？])", text) if item.strip()]


def canonical_json_sha256(value) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_hv_route_source_for_test(raw_text: str) -> list[dict[str, str]]:
    field_names = (
        "claim_level", "when", "additional_inferential_requires",
        "additional_protocol_requires", "allowed_conclusion", "result_ceiling",
    )
    starts = list(re.finditer(r"(?:^|(?<=。))\d+\. route_id=([^；]+)；", raw_text))
    routes: list[dict[str, str]] = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(raw_text)
        fragment = raw_text[match.start():end].strip()
        route = {"route_id": match.group(1), "source_text": fragment}
        for field_index, field in enumerate(field_names):
            marker = f"{field}="
            start = fragment.index(marker) + len(marker)
            if field_index + 1 < len(field_names):
                stop = fragment.index(f"；{field_names[field_index + 1]}=", start)
                route[field] = fragment[start:stop].strip()
            else:
                route[field] = fragment[start:].strip()
        routes.append(route)
    return routes


def semantic_pointer_inventory(payload) -> tuple[list[str], list[str]]:
    pointers: list[str] = []
    leaves: list[str] = []

    def walk(node, pointer: str) -> None:
        pointers.append(pointer)
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{pointer}/{pointer_escape(key)}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{pointer}/{index}")
        else:
            leaves.append(pointer)

    for key, value in payload.items():
        if key not in {"schema_id", "schema_version"}:
            walk(value, f"/{pointer_escape(key)}")
    return pointers, leaves


SCALAR_ENUM_PARENTS = {
    "/variable_states",
    "/privacy_levels",
    "/relation_kinds",
    "/relation_transition_results",
    "/condition_channels",
    "/clock_kinds",
    "/event_kinds",
    "/variable_candidate_ledger_schema/allowed_states",
    "/required_option_kinds",
}


def expected_binding_role_for_test(pointer: str) -> str:
    tail = pointer.rsplit("/", 1)[-1]
    if pointer == "/scope":
        return "domain"
    if (
        pointer == "/guards"
        or pointer.startswith("/guards/")
        or pointer == "/personality_hypothesis_contract/forbidden_outputs"
        or pointer.startswith("/personality_hypothesis_contract/forbidden_outputs/")
    ):
        return "forbidden"
    if pointer == "/authorization_policy":
        return "action_ceiling"
    if pointer in SCALAR_ENUM_PARENTS:
        return "enum_set"
    if pointer == "/timescale_bands" or re.fullmatch(
        r"/timescale_bands/(?:0|[1-9][0-9]*)", pointer
    ):
        return "record_schema"
    if tail == "examples" or "/examples/" in pointer:
        return "example"
    if pointer.rsplit("/", 1)[0] in SCALAR_ENUM_PARENTS:
        return "enum_value"
    if tail == "required_fields":
        return "constraint"
    if "/required_fields/" in pointer:
        return "required_field"
    if tail.endswith("_schema") or tail.endswith("_contract"):
        return "record_schema"
    if tail in {"name", "definition"}:
        return "definition"
    return "constraint"


def binding_inventory_sha256(contract_map) -> str:
    rows = []
    for contract in contract_map["contracts"]:
        for binding in contract["bindings"]:
            rows.append([
                contract["contract_id"],
                binding["json_pointer"],
                binding["concept_id"],
                binding["binding_role"],
                [
                    [anchor["anchor_id"], anchor["source_file"]]
                    for anchor in binding["source_anchors"]
                ],
            ])
    encoded = json.dumps(
        sorted(rows), ensure_ascii=False, separators=(",", ":")
    ) + "\n"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def semantic_coverage_sha256(contract_map) -> str:
    rows = []
    for contract in contract_map["contracts"]:
        for binding in contract["bindings"]:
            rows.append([
                "bound",
                contract["contract_id"],
                binding["json_pointer"],
                binding["concept_id"],
                binding["binding_role"],
                [
                    [anchor["anchor_id"], anchor["source_file"]]
                    for anchor in binding["source_anchors"]
                ],
            ])
        for unbound in contract["unbound_semantic_pointers"]:
            rows.append([
                "unbound",
                contract["contract_id"],
                unbound["json_pointer"],
                unbound["reason_code"],
                unbound["runtime_requirement"],
            ])
    encoded = json.dumps(
        sorted(rows), ensure_ascii=False, separators=(",", ":")
    ) + "\n"
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_object_schemas_closed(test: unittest.TestCase, node, location: str = "$") -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            test.assertIs(
                node.get("additionalProperties"),
                False,
                f"open object schema at {location}",
            )
        for key, value in node.items():
            assert_object_schemas_closed(test, value, f"{location}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            assert_object_schemas_closed(test, value, f"{location}[{index}]")


def paragraph_index(source_root: Path) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    marker = "<!-- source_paragraph:"
    for path in sorted(source_root.glob("*.md")):
        if path.name.startswith("00-") and path.name != "00-source-envelope.md":
            continue
        text = path.read_text(encoding="utf-8")
        chunks = text.split(marker)
        for chunk in chunks[1:]:
            header, body = chunk.split(" -->", 1)
            anchor = header.split(maxsplit=1)[0]
            prose = body.split(marker, 1)[0].strip()
            result[anchor] = (path.name, prose)
    return result


class ProMaxV8KnowledgePresenceTests(unittest.TestCase):
    def test_required_assets_and_checker_exist(self) -> None:
        for path in (
            REGISTRY_PATH,
            REFERENCES / "concept-registry/index.md",
            CONTRACT_MAP_PATH,
            ROUTE_MAP_PATH,
            CHECKER_PATH,
            LAUNCHER_PATH,
            *SCHEMAS.values(),
        ):
            self.assertTrue(path.is_file(), f"missing: {path.relative_to(ROOT)}")
        for _contract_id, (name, _digest) in CONTRACTS.items():
            self.assertTrue((REFERENCES / "concept-contracts" / name).is_file())

    @unittest.skipUnless(CHECKER_PATH.is_file(), "v8 knowledge checker not implemented")
    def test_checker_passes_api_and_cli(self) -> None:
        checker = load_module("promax_v8_knowledge_checker", CHECKER_PATH)
        self.assertEqual(checker.check_repository(ROOT), [])
        completed = subprocess.run(
            [sys.executable, str(LAUNCHER_PATH), "--repo", str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


@unittest.skipUnless(
    REGISTRY_PATH.is_file()
    and CONTRACT_MAP_PATH.is_file()
    and ROUTE_MAP_PATH.is_file()
    and all(path.is_file() for path in SCHEMAS.values()),
    "v8 knowledge assets not implemented",
)
class ProMaxV8SchemaAndShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(REGISTRY_PATH)
        cls.contract_map = load_json(CONTRACT_MAP_PATH)
        cls.route_map = load_json(ROUTE_MAP_PATH)

    def test_all_four_schemas_are_valid_and_closed(self) -> None:
        for name, path in SCHEMAS.items():
            with self.subTest(schema=name):
                schema = load_json(path)
                Draft202012Validator.check_schema(schema)
                assert_object_schemas_closed(self, schema)

    def test_assets_validate_against_their_schemas(self) -> None:
        instances = {
            "source": load_json(REFERENCES / "source_manifest.json"),
            "registry": self.registry,
            "contracts": self.contract_map,
            "routes": self.route_map,
        }
        for name, instance in instances.items():
            with self.subTest(asset=name):
                Draft202012Validator(load_json(SCHEMAS[name])).validate(instance)

    def test_registry_has_exhaustive_named_core_and_no_namespace_collision(self) -> None:
        self.assertEqual(self.registry["framework_version"], "v8.0")
        self.assertEqual(self.registry["snapshot_sha256"], SNAPSHOT_SHA256)
        self.assertEqual(self.registry["canonical_namespace"], "V8-CANON-")
        self.assertEqual(self.registry["provisional_namespace"], "PROMAX-PROV-")
        concepts = self.registry["concepts"]
        self.assertEqual(len(concepts), EXPECTED_CANONICAL_CONCEPT_COUNT)
        self.assertEqual(self.registry["concept_count"], EXPECTED_CANONICAL_CONCEPT_COUNT)
        ids = [item["concept_id"] for item in concepts]
        names = [item["authoritative_name_zh"] for item in concepts]
        self.assertEqual(len(ids), len(set(ids)), "duplicate concept ID")
        self.assertEqual(len(names), len(set(names)), "duplicate canonical Chinese name")
        self.assertTrue(
            all(any("\u4e00" <= char <= "\u9fff" for char in name) for name in names),
            "every authoritative_name_zh must contain Chinese text",
        )
        by_id = {item["concept_id"]: item for item in concepts}
        self.assertEqual(
            {concept_id: by_id[concept_id]["authoritative_name_zh"] for concept_id in EXPECTED_CJK_NAMES},
            EXPECTED_CJK_NAMES,
        )
        self.assertTrue(all(item.startswith("V8-CANON-") for item in ids))
        self.assertFalse(any(item.startswith("PROMAX-PROV-") for item in ids))
        self.assertEqual(set(ids), EXPECTED_CANONICAL_IDS)
        self.assertEqual(len(REQUIRED_VOCABULARY_IDS), 103)
        recomputed_inventory = hashlib.sha256(
            ("\n".join(sorted(ids)) + "\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(recomputed_inventory, EXPECTED_CANONICAL_INVENTORY_SHA256)
        self.assertEqual(self.registry["concept_inventory_sha256"], recomputed_inventory)
        self.assertIn("343 项基础清单", self.registry["curation_basis"])
        self.assertIn("366 项经逐条来源审计", self.registry["curation_basis"])
        self.assertIn("精确 709 项", self.registry["curation_basis"])

    def test_derived_authoritative_assets_are_independently_pinned(self) -> None:
        self.assertEqual(sha256_file(REGISTRY_PATH), EXPECTED_REGISTRY_FILE_SHA256)
        self.assertEqual(sha256_file(CONTRACT_MAP_PATH), EXPECTED_CONTRACT_MAP_FILE_SHA256)
        self.assertEqual(sha256_file(ROUTE_MAP_PATH), EXPECTED_ROUTE_MAP_FILE_SHA256)
        self.assertEqual(
            binding_inventory_sha256(self.contract_map),
            EXPECTED_BINDING_INVENTORY_SHA256,
        )
        self.assertEqual(
            semantic_coverage_sha256(self.contract_map),
            EXPECTED_SEMANTIC_COVERAGE_SHA256,
        )
        self.assertEqual(
            self.contract_map["semantic_coverage_sha256"],
            EXPECTED_SEMANTIC_COVERAGE_SHA256,
        )
        self.assertEqual(
            canonical_json_sha256(self.registry["concepts"]),
            EXPECTED_CONCEPT_SEMANTIC_SHA256,
        )
        self.assertEqual(
            canonical_json_sha256(self.route_map["routes"]),
            EXPECTED_ROUTE_SEMANTIC_SHA256,
        )
        for label, schema_path in SCHEMAS.items():
            self.assertEqual(
                sha256_file(schema_path),
                EXPECTED_SCHEMA_FILE_SHA256[label],
            )

    def test_same_spelling_in_distinct_contract_namespaces_is_not_collapsed(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        namespace_pairs = (
            ("VOCAB-ACTOR-STATE-OBSERVED", "VOCAB-EVENT-OBSERVED"),
            ("VOCAB-ACTOR-STATE-CANDIDATE", "VOCAB-LEDGER-PROPOSED"),
            ("VOCAB-ACTOR-STATE-RETIRED", "VOCAB-LEDGER-RETIRED"),
            ("VOCAB-ACTOR-STATE-SUPPORTED-HYPOTHESIS", "VOCAB-LEDGER-SUPPORTED-CANDIDATE"),
            ("VOCAB-PRIVACY-WITHHELD", "VOCAB-INFO-WITHHELD-FOR-PROTECTION"),
        )
        for left, right in namespace_pairs:
            left_record = concepts[f"V8-CANON-{left}"]
            right_record = concepts[f"V8-CANON-{right}"]
            with self.subTest(left=left, right=right):
                self.assertNotEqual(
                    left_record["authoritative_name_zh"],
                    right_record["authoritative_name_zh"],
                )

    def test_closed_vocabulary_definitions_are_value_specific_within_each_namespace(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        expected = {
            **{f"V8-CANON-VOCAB-AXIS-RELATION-{key}": value for key, value in {
                "EQUAL": "equal", "EXPANDS": "expands", "CONTRACTS": "contracts",
                "INCOMPARABLE": "incomparable", "UNKNOWN": "unknown",
            }.items()},
            **{f"V8-CANON-VOCAB-PRIVACY-{key}": value for key, value in {
                "PUBLIC": "公开", "CONTEXT-LIMITED": "情境限定", "SENSITIVE": "敏感",
                "HIGHLY-SENSITIVE": "高度敏感", "WITHHELD": "拒绝披露",
            }.items()},
            **{f"V8-CANON-VOCAB-CIRCLE-TRANSITION-{key}": value for key, value in {
                "UNCHANGED": "维持", "STRENGTHENED": "增强", "WEAKENED": "减弱",
                "REORIENTED": "改向", "TRANSFORMED": "转化", "DISSOLVED": "解体",
            }.items()},
            "V8-CANON-VOCAB-CONDITION-CHANNEL-MATERIAL": "M 包括身体、时间、空间、资金、能源、设备、基础设施、产权、供应、照护和实际行动能力",
            "V8-CANON-VOCAB-CONDITION-CHANNEL-EXPERIENTIAL-MEANING": "Ψ 包括感受、期待、记忆、身份、信任、羞耻、希望、恐惧、承诺、价值冲突和合法性感知",
            **{f"V8-CANON-VOCAB-BRANCH-{key}": value for key, value in {
                "FACT": "事实不确定", "MECHANISM": "机制不确定",
                "CHOICE": "行动者选择", "EXOGENOUS-DISTURBANCE": "外生扰动",
            }.items()},
            **{f"V8-CANON-VOCAB-FORECAST-RESULT-{key}": value for key, value in {
                "SUPPORTED": "支持", "UNSUPPORTED": "未支持", "UNDECIDED": "未决",
                "TARGET-INVALID": "目标失效", "UNASSESSABLE": "无法评价",
            }.items()},
            **{f"V8-CANON-VOCAB-SELECTION-STATE-{key}": value for key, value in {
                "DRAFT": "draft", "UNDER-REVIEW": "under_review", "AUTHORIZED": "authorized",
                "PAUSED": "paused", "STOPPED": "stopped", "ROLLED-BACK": "rolled_back",
                "CLOSED": "closed",
            }.items()},
        }
        for concept_id, definition in expected.items():
            with self.subTest(concept=concept_id):
                self.assertEqual(concepts[concept_id]["definition"], definition)

        namespaces = (
            "V8-CANON-VOCAB-AXIS-RELATION-",
            "V8-CANON-VOCAB-PRIVACY-",
            "V8-CANON-VOCAB-CIRCLE-TRANSITION-",
            "V8-CANON-VOCAB-CONDITION-CHANNEL-",
            "V8-CANON-VOCAB-BRANCH-",
            "V8-CANON-VOCAB-FORECAST-RESULT-",
            "V8-CANON-VOCAB-SELECTION-STATE-",
        )
        for prefix in namespaces:
            definitions = [
                concept["definition"]
                for concept_id, concept in concepts.items()
                if concept_id.startswith(prefix)
            ]
            with self.subTest(namespace=prefix):
                self.assertEqual(len(definitions), len(set(definitions)))

    def test_every_concept_has_all_semantic_contract_fields(self) -> None:
        required = {
            "concept_id",
            "authoritative_name_zh",
            "concept_type",
            "responsibility_layer",
            "definition",
            "authoritative_wire_tokens",
            "primary_source_anchor_id",
            "source_anchors",
            "prerequisites",
            "allowed_inferences",
            "forbidden_substitutions_or_generalizations",
            "common_misuses",
            "required_neighbor_ids",
            "conflicts_disambiguation",
            "evidence_requirements",
            "counterexamples",
            "withdrawal_conditions",
            "deduction_interfaces",
            "action_ceiling",
            "conditional_support_routes",
            "source_undefined_fields",
            "contract_ids",
            "contract_bindings",
            "route_ids",
        }
        for concept in self.registry["concepts"]:
            with self.subTest(concept=concept["concept_id"]):
                expected_fields = set(required)
                if concept["concept_type"] == "human_variable_interface":
                    expected_fields.add("source_card")
                self.assertEqual(set(concept), expected_fields)
                for field in (
                    "source_anchors",
                    "allowed_inferences",
                    "required_neighbor_ids",
                    "route_ids",
                ):
                    self.assertTrue(concept[field], f"{concept['concept_id']} empty {field}")

    def test_source_undefined_fields_are_an_exact_honest_closure(self) -> None:
        anchors = paragraph_index(REFERENCES / "v8-full-source")
        forbidden_fallback_fragments = (
            "源锚点声明的对象、窗口与适用条件",
            "泛化到源锚点未覆盖",
            "字段完整误当作经验成立",
            "构成反例或不适用例",
            "源锚点的必要条件、对象同一性或证据门失效",
            "must-read-neighbor",
            "不因相邻或同路线而互换",
        )
        serialized = json.dumps(self.registry, ensure_ascii=False)
        for fragment in forbidden_fallback_fragments:
            self.assertNotIn(fragment, serialized)

        for concept in self.registry["concepts"]:
            if concept["concept_type"] == "human_variable_interface":
                expected_undefined = [
                    "common_misuses",
                    "conflicts_disambiguation",
                    "withdrawal_conditions",
                    "deduction_interfaces",
                ]
            else:
                expected_undefined = [
                    field for field in OPTIONAL_SEMANTIC_FIELDS
                    if concept[field] in ([], None)
                ]
            with self.subTest(concept=concept["concept_id"]):
                self.assertEqual(concept["source_undefined_fields"], expected_undefined)
                anchor_texts = [
                    anchors[item["anchor_id"]][1] for item in concept["source_anchors"]
                ]
                for field in (
                    "prerequisites",
                    "forbidden_substitutions_or_generalizations",
                    "common_misuses",
                    "evidence_requirements",
                    "counterexamples",
                    "withdrawal_conditions",
                ):
                    for excerpt in concept[field]:
                        self.assertTrue(
                            any(excerpt in text for text in anchor_texts),
                            f"{concept['concept_id']} fabricated or cross-anchor {field}: {excerpt}",
                        )
                if concept["action_ceiling"] is not None:
                    self.assertTrue(any(concept["action_ceiling"] in text for text in anchor_texts))
                for conflict in concept["conflicts_disambiguation"]:
                    self.assertTrue(any(conflict["disambiguation"] in text for text in anchor_texts))
                for interface in concept["deduction_interfaces"]:
                    self.assertTrue(any(interface["relation"] in text for text in anchor_texts))
                    self.assertTrue(any(interface["output_ceiling"] in text for text in anchor_texts))

        global_ceiling = self.registry["global_action_ceiling"]
        global_support = {
            item["anchor_id"]: anchors[item["anchor_id"]][1]
            for item in global_ceiling["source_anchors"]
        }
        self.assertEqual(
            global_ceiling["clauses"],
            [global_support["V8-P0791"], global_support["V8-P0854"], global_support["V8-P3564"]],
        )

    def test_hv_source_cards_are_lossless_closed_and_exactly_projected(self) -> None:
        anchors = paragraph_index(REFERENCES / "v8-full-source")
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        hv_ids = {
            concept_id
            for concept_id, concept in concepts.items()
            if concept["concept_type"] == "human_variable_interface"
        }
        self.assertEqual(hv_ids, set(HV_SOURCE_CARD_SHA256))
        self.assertEqual(
            {concept_id for concept_id, concept in concepts.items() if "source_card" in concept},
            hv_ids,
        )

        actual_routes: dict[str, set[str]] = {}
        expected_route_counts = (2, 2, 2, 2, 4, 3, 3, 3, 3, 4, 3)
        for index in range(1, 12):
            concept_id = f"V8-CANON-HV{index:02d}"
            concept = concepts[concept_id]
            card_start = 1133 + (index - 1) * 94
            summary_anchor = 2195 + (index - 1) * 2
            card = concept["source_card"]
            with self.subTest(concept=concept_id):
                self.assertEqual(card["schema_id"], HV_SOURCE_CARD_SCHEMA_ID)
                self.assertEqual(card["field_count"], 39)
                self.assertEqual(card["card_anchor"], {
                    "anchor_id": f"V8-P{card_start:04d}",
                    "source_file": "07-human-world.md",
                })
                heading_file, heading_prose = anchors[card["card_anchor"]["anchor_id"]]
                self.assertEqual(heading_file, card["card_anchor"]["source_file"])
                self.assertEqual(
                    heading_prose,
                    f"{concept['authoritative_name_zh']}（完整接口卡）",
                )
                self.assertEqual(tuple(card["fields"]), HV_P1129_FIELDS)
                digest_payload = {
                    key: value for key, value in card.items() if key != "content_sha256"
                }
                self.assertEqual(
                    card["content_sha256"], HV_SOURCE_CARD_SHA256[concept_id]
                )
                self.assertEqual(
                    canonical_json_sha256(digest_payload), HV_SOURCE_CARD_SHA256[concept_id]
                )

                expected_anchor_ids = {
                    f"V8-P{summary_anchor:04d}",
                    f"V8-P{card_start:04d}",
                }
                for field_name in HV_P1129_FIELDS:
                    label_offset, value_offset = HV_SOURCE_FIELD_OFFSETS[field_name]
                    field = card["fields"][field_name]
                    label_id = f"V8-P{card_start + label_offset:04d}"
                    value_id = f"V8-P{card_start + value_offset:04d}"
                    expected_anchor_ids.update((label_id, value_id))
                    self.assertEqual(field["label_anchor"], {
                        "anchor_id": label_id,
                        "source_file": "07-human-world.md",
                    })
                    self.assertEqual(field["value_anchor"], {
                        "anchor_id": value_id,
                        "source_file": "07-human-world.md",
                    })
                    self.assertEqual(field["label_text"], anchors[label_id][1])
                    self.assertEqual(field["raw_value_text"], anchors[value_id][1])
                self.assertEqual(
                    {item["anchor_id"] for item in concept["source_anchors"]},
                    expected_anchor_ids,
                )

                raw = {
                    key: card["fields"][key]["raw_value_text"]
                    for key in HV_P1129_FIELDS
                }
                project = lambda value: [] if value == "无（空集合）" else [value]
                self.assertEqual(concept["definition"], raw["proposition"])
                self.assertEqual(concept["allowed_inferences"], [raw["allowed_inference"]])
                self.assertEqual(concept["prerequisites"], project(raw["inferential_requires"]))
                self.assertEqual(
                    concept["forbidden_substitutions_or_generalizations"],
                    [*project(raw["prohibited_leap"]), *project(raw["forbidden_elevation"])],
                )
                self.assertEqual(concept["evidence_requirements"], project(raw["evidence"]))
                self.assertEqual(concept["counterexamples"], project(raw["counterexamples"]))
                self.assertEqual(concept["withdrawal_conditions"], [])
                self.assertEqual(
                    concept["action_ceiling"],
                    None if raw["action_ceiling"] == "无（空集合）" else raw["action_ceiling"],
                )
                self.assertEqual(
                    concept["source_undefined_fields"],
                    ["common_misuses", "conflicts_disambiguation", "withdrawal_conditions", "deduction_interfaces"],
                )
                self.assertNotIn("prerequisites", concept["source_undefined_fields"])

                parsed_routes = parse_hv_route_source_for_test(
                    raw["conditional_support_routes"]
                )
                structured_routes = concept["conditional_support_routes"]
                self.assertEqual(len(structured_routes), expected_route_counts[index - 1])
                self.assertEqual(
                    [route["route_id"] for route in structured_routes],
                    [route["route_id"] for route in parsed_routes],
                )
                for structured, parsed in zip(structured_routes, parsed_routes):
                    for field in (
                        "route_id", "claim_level", "when",
                        "additional_inferential_requires",
                        "additional_protocol_requires", "allowed_conclusion",
                        "result_ceiling", "source_text",
                    ):
                        self.assertEqual(structured[field], parsed[field])
                    self.assertEqual(structured["source_anchor"], card["fields"]["conditional_support_routes"]["value_anchor"])
                    actual_routes[structured["route_id"]] = set(
                        structured["required_concept_ids"]
                    )
                    self.assertTrue(
                        set(structured["required_concept_ids"]).issubset(
                            concept["required_neighbor_ids"]
                        )
                    )

        self.assertEqual(actual_routes, EXPECTED_HV_ROUTE_REQUIRED_IDS)
        self.assertEqual(len(actual_routes), 31)
        for concept_id, concept in concepts.items():
            if concept_id not in hv_ids:
                self.assertEqual(concept["conditional_support_routes"], [])

    def test_optional_semantics_are_explicitly_curated_without_generic_role_fillers(self) -> None:
        optional_labels = {
            "机制链为：", "允许登记", "禁止越界", "必须保留", "必须附加的限制",
            "字段", "回答的问题", "最低记录要求", "不能推出",
        }
        curated_ids = {
            *(f"V8-CANON-C{index}" for index in range(1, 13)),
            *(f"V8-CANON-H{index}" for index in range(1, 7)),
            *(f"V8-CANON-VOCAB-ACTOR-STATE-{item}" for item in ("UNKNOWN", "CANDIDATE", "SUPPORTED-HYPOTHESIS", "OBSERVED", "CONTESTED", "RETIRED")),
            *(f"V8-CANON-VOCAB-EVENT-{item}" for item in ("OBSERVED", "REPORTED", "PLANNED", "HYPOTHETICAL", "SIMULATED")),
            *(f"V8-CANON-VOCAB-FORECAST-LEVEL-{item}" for item in ("PROBABILITY-OR-RANGE", "RANK-OR-SUPPORT", "CONDITIONAL-DIRECTION", "NO-FORECAST")),
            *(f"V8-CANON-VOCAB-LEDGER-{item}" for item in ("PROPOSED", "UNDER-TEST", "SUPPORTED-CANDIDATE", "REJECTED", "RETIRED")),
            "V8-CANON-CM-FEEDBACK", "V8-CANON-CM-LEARNING",
            "V8-CANON-CM-MAINTENANCE", "V8-CANON-CM-LOAD",
            "V8-CANON-CM-PHASE", "V8-CANON-CM-SELECTION",
            *(f"V8-CANON-CM-MAINTENANCE-{item}" for item in ("CURRENT", "CUMULATIVE")),
            *(f"V8-CANON-CM-LOAD-{item}" for item in ("INSTANT", "CUMULATIVE")),
            *(f"V8-CANON-CM-PHASE-{item}" for item in ("PATTERN", "CAUSAL-TRIGGER", "HYSTERETIC")),
            *(f"V8-CANON-CM-SELECTION-{item}" for item in ("PATTERN", "CARRIER", "HISTORY")),
            "V8-CANON-OMEGA-F-UPDATE", "V8-CANON-ACTOR-STATE",
        }
        semantic_fields = tuple(
            field for field in OPTIONAL_SEMANTIC_FIELDS if field != "deduction_interfaces"
        )
        for concept in self.registry["concepts"]:
            populated = any(concept[field] not in ([], None) for field in semantic_fields)
            if populated:
                self.assertIn(concept["concept_id"], EXPECTED_CANONICAL_IDS)
            for field in semantic_fields:
                values = [concept[field]] if field == "action_ceiling" else concept[field]
                for value in values or []:
                    if isinstance(value, str):
                        self.assertNotIn(value, optional_labels)

        overlap_rows = set()
        list_fields = (
            "prerequisites", "forbidden_substitutions_or_generalizations", "common_misuses",
            "evidence_requirements", "counterexamples", "withdrawal_conditions",
        )
        for concept in self.registry["concepts"]:
            for left_index, left in enumerate(list_fields):
                for right in list_fields[left_index + 1:]:
                    for excerpt in set(concept[left]) & set(concept[right]):
                        overlap_rows.add((concept["concept_id"], left, right, excerpt))
        expected_overlap_rows = {
            (
                "V8-CANON-ACTOR-STATE",
                "forbidden_substitutions_or_generalizations",
                "common_misuses",
                "任何无法观察、没有来源、当事人拒绝披露或彼此冲突的信息都要保留为不同类型的未知，而不是由模型以“常识”补齐。",
            ),
            (
                "V8-CANON-CM-FEEDBACK",
                "counterexamples",
                "withdrawal_conditions",
                "信号到达但后续转移不变，变化由独立共同输入解释，或切断返回通道后差异仍保持不变时，不登记有效反馈。",
            ),
            *{
                (
                    f"V8-CANON-VOCAB-ACTOR-STATE-{code}",
                    "prerequisites",
                    "evidence_requirements",
                    excerpt,
                )
                for code, excerpt in (
                    ("UNKNOWN", "合法且合适的新观察"),
                    ("CANDIDATE", "预先声明的指标、时间窗与反例门"),
                    ("SUPPORTED-HYPOTHESIS", "样本外复核、跨情境检验或独立来源"),
                    ("OBSERVED", "来源完整性与观察合同"),
                    ("CONTESTED", "独立复核或新的区分性证据"),
                    ("RETIRED", "新版本只能追加退役理由"),
                )
            },
            (
                "V8-CANON-VOCAB-EVENT-SIMULATED",
                "forbidden_substitutions_or_generalizations",
                "evidence_requirements",
                "模型版本、参数和禁止外推",
            ),
        }
        self.assertEqual(overlap_rows, expected_overlap_rows)

    def test_definition_and_allowed_inferences_are_exactly_supported_by_anchors(self) -> None:
        anchors = paragraph_index(REFERENCES / "v8-full-source")
        for concept in self.registry["concepts"]:
            support_parts: list[str] = []
            for source_anchor in concept["source_anchors"]:
                anchor_id = source_anchor["anchor_id"]
                self.assertIn(anchor_id, anchors, concept["concept_id"])
                source_file, prose = anchors[anchor_id]
                self.assertEqual(source_anchor["source_file"], source_file)
                support_parts.append(prose)
            with self.subTest(concept=concept["concept_id"]):
                if concept["concept_id"] == "V8-CANON-OMEGA-F-UPDATE":
                    self.assertEqual(
                        concept["definition"],
                        "\n".join(anchors[f"V8-P{value:04d}"][1] for value in range(2958, 2963)),
                    )
                else:
                    self.assertTrue(
                        any(concept["definition"] in prose for prose in support_parts),
                        f"cross-anchor or unsupported definition: {concept['concept_id']}",
                    )
                for inference in concept["allowed_inferences"]:
                    self.assertTrue(
                        any(inference in prose for prose in support_parts),
                        f"cross-anchor or unsupported inference: {concept['concept_id']}",
                    )

    def test_deduction_interfaces_have_complete_positive_dependency_targets(self) -> None:
        expected = {
            "V8-CANON-C1": {"V8-CANON-D0", "V8-CANON-G1"},
            "V8-CANON-C2": {"V8-CANON-D0", "V8-CANON-G2"},
            "V8-CANON-C3": {"V8-CANON-D2", "V8-CANON-G2"},
            "V8-CANON-C4": {"V8-CANON-D1", "V8-CANON-G3"},
            "V8-CANON-C5": {"V8-CANON-D0", "V8-CANON-G2"},
            "V8-CANON-C6": {"V8-CANON-D3", "V8-CANON-G4"},
            "V8-CANON-C7": {"V8-CANON-G2", "V8-CANON-G4"},
            "V8-CANON-C8": {"V8-CANON-D1"},
            "V8-CANON-C9": {"V8-CANON-G2"},
            "V8-CANON-C10": {"V8-CANON-G2"},
            "V8-CANON-C11": {"V8-CANON-D2", "V8-CANON-G2"},
            "V8-CANON-C12": {"V8-CANON-N1", "V8-CANON-O1", "V8-CANON-O2", "V8-CANON-O3", "V8-CANON-O4"},
            "V8-CANON-C3-FEEDBACK": {"V8-CANON-C3"},
            "V8-CANON-C3-LEARNING": {"V8-CANON-C3", "V8-CANON-G3"},
            "V8-CANON-C5-INSTANT": {"V8-CANON-C5"},
            "V8-CANON-C5-CUMULATIVE": {"V8-CANON-C5", "V8-CANON-G3"},
            "V8-CANON-C8-PATTERN": {"V8-CANON-C8"},
            "V8-CANON-C8-MECHANISM": {"V8-CANON-C8", "V8-CANON-G2"},
            "V8-CANON-C9-RESPONSE": {"V8-CANON-C9"},
            "V8-CANON-C9-PERSISTENT": {"V8-CANON-C9", "V8-CANON-G3"},
            "V8-CANON-C10-CURRENT": {"V8-CANON-C10", "V8-CANON-G2", "V8-CANON-H2"},
            "V8-CANON-C10-INTERTEMPORAL": {"V8-CANON-C10", "V8-CANON-G3"},
            "V8-CANON-C10-HISTORICAL-CARRIER": {"V8-CANON-C10", "V8-CANON-G3", "V8-CANON-H5"},
            "V8-CANON-S0": {f"V8-CANON-{item}" for item in ("C1", "C10", "C12", "C2", "C4", "C5", "G1", "G2", "G3", "H1", "H2", "H5", "U01", "U02", "U03", "U08", "U09", "U11")},
            "V8-CANON-S1": {f"V8-CANON-{item}" for item in ("C1", "C10", "C11", "C12", "C2", "C3", "C5", "C9", "G1", "G2", "G3", "H1", "H2", "H3", "H4", "U01", "U02", "U03", "U04", "U06", "U07", "U09", "U11")},
            "V8-CANON-S2": {f"V8-CANON-{item}" for item in ("C1", "C10", "C11", "C12", "C2", "C3", "C4", "C5", "C6", "C7", "C9", "G1", "G2", "G3", "G4", "H1", "H2", "H3", "H4", "H5", "U01", "U02", "U03", "U04", "U06", "U07", "U08", "U09", "U11")},
            "V8-CANON-S3": {f"V8-CANON-{item}" for item in ("C10", "C11", "C12", "C2", "C3", "C4", "C5", "C6", "C7", "C9", "G2", "G3", "G4", "H1", "H2", "H3", "H4", "H5", "U02", "U03", "U05", "U06", "U07", "U08", "U09", "U10", "U11")},
            "V8-CANON-S4": {f"V8-CANON-{item}" for item in ("C10", "C11", "C12", "C2", "C3", "C4", "C5", "C6", "C7", "C9", "G2", "G3", "G4", "H1", "H2", "H3", "H4", "H5", "U03", "U05", "U06", "U07", "U09", "U10", "U11")},
            "V8-CANON-S5": {f"V8-CANON-{item}" for item in ("C1", "C12", "G1", "G2", "G3", "G4", "H1", "H2", "H3", "H4", "H5", "U01", "U11")},
            "V8-CANON-S6": {f"V8-CANON-{item}" for item in ("C1", "C12", "G1", "G2", "G3", "G4", "H1", "H2", "H3", "H4", "H5", "U01", "U11")},
            "V8-CANON-CM-FEEDBACK": {"V8-CANON-D2", "V8-CANON-G2", "V8-CANON-E4", "V8-CANON-CAUSAL-CONTRACT", "V8-CANON-EVIDENCE-CONTRACT"},
            "V8-CANON-CM-LEARNING": {"V8-CANON-CM-FEEDBACK", "V8-CANON-G3", "V8-CANON-E4", "V8-CANON-CAUSAL-CONTRACT", "V8-CANON-EVIDENCE-CONTRACT"},
            "V8-CANON-CM-MAINTENANCE": {"V8-CANON-D0", "V8-CANON-D1", "V8-CANON-G2", "V8-CANON-E4", "V8-CANON-CAUSAL-CONTRACT", "V8-CANON-EVIDENCE-CONTRACT"},
            "V8-CANON-CM-LOAD": {"V8-CANON-D0", "V8-CANON-G2", "V8-CANON-E4", "V8-CANON-CAUSAL-CONTRACT", "V8-CANON-EVIDENCE-CONTRACT"},
            "V8-CANON-CM-PHASE": {"V8-CANON-D0", "V8-CANON-D1", "V8-CANON-E4", "V8-CANON-CAUSAL-CONTRACT", "V8-CANON-EVIDENCE-CONTRACT"},
            "V8-CANON-CM-SELECTION": {"V8-CANON-D1", "V8-CANON-E4", "V8-CANON-CAUSAL-CONTRACT", "V8-CANON-EVIDENCE-CONTRACT"},
            "V8-CANON-CM-MAINTENANCE-CURRENT": {"V8-CANON-CM-MAINTENANCE"},
            "V8-CANON-CM-MAINTENANCE-CUMULATIVE": {"V8-CANON-CM-MAINTENANCE", "V8-CANON-G3"},
            "V8-CANON-CM-LOAD-INSTANT": {"V8-CANON-CM-LOAD"},
            "V8-CANON-CM-LOAD-CUMULATIVE": {"V8-CANON-CM-LOAD", "V8-CANON-G3"},
            "V8-CANON-CM-PHASE-PATTERN": {"V8-CANON-CM-PHASE"},
            "V8-CANON-CM-PHASE-CAUSAL-TRIGGER": {"V8-CANON-CM-PHASE", "V8-CANON-G2", "V8-CANON-CAUSAL-CONTRACT"},
            "V8-CANON-CM-PHASE-HYSTERETIC": {"V8-CANON-CM-PHASE", "V8-CANON-G3", "V8-CANON-CAUSAL-CONTRACT"},
            "V8-CANON-CM-SELECTION-PATTERN": {"V8-CANON-CM-SELECTION"},
            "V8-CANON-CM-SELECTION-CARRIER": {"V8-CANON-CM-SELECTION", "V8-CANON-G2"},
            "V8-CANON-CM-SELECTION-HISTORY": {"V8-CANON-CM-SELECTION", "V8-CANON-G3"},
            **{f"V8-CANON-G{family}{suffix}": {f"V8-CANON-G{family}"} for family in range(1, 5) for suffix in ("A", "B")},
        }
        actual = {
            concept["concept_id"]: {
                interface["target_concept_id"] for interface in concept["deduction_interfaces"]
            }
            for concept in self.registry["concepts"]
            if concept["deduction_interfaces"]
        }
        self.assertEqual(actual, expected)
        self.assertNotIn("V8-CANON-G3", actual["V8-CANON-CM-FEEDBACK"])
        self.assertNotIn("V8-CANON-G3", actual["V8-CANON-CM-PHASE"])
        excluded = {
            "V8-CANON-CM-MAINTENANCE-CURRENT": {"V8-CANON-G3"},
            "V8-CANON-CM-LOAD-INSTANT": {"V8-CANON-G3"},
            "V8-CANON-CM-PHASE-PATTERN": {"V8-CANON-G2", "V8-CANON-G3", "V8-CANON-CAUSAL-CONTRACT"},
            "V8-CANON-CM-PHASE-CAUSAL-TRIGGER": {"V8-CANON-G3"},
            "V8-CANON-CM-PHASE-HYSTERETIC": {"V8-CANON-G2"},
        }
        for concept_id, excluded_ids in excluded.items():
            self.assertFalse(actual[concept_id] & excluded_ids, concept_id)

        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        for concept_id in {
            "V8-CANON-CM-MAINTENANCE-CURRENT", "V8-CANON-CM-MAINTENANCE-CUMULATIVE",
            "V8-CANON-CM-LOAD-INSTANT", "V8-CANON-CM-LOAD-CUMULATIVE",
            "V8-CANON-CM-PHASE-PATTERN", "V8-CANON-CM-PHASE-CAUSAL-TRIGGER",
            "V8-CANON-CM-PHASE-HYSTERETIC", "V8-CANON-CM-SELECTION-PATTERN",
            "V8-CANON-CM-SELECTION-CARRIER", "V8-CANON-CM-SELECTION-HISTORY",
        }:
            relation_values = {item["relation"] for item in concepts[concept_id]["deduction_interfaces"]}
            output_values = {item["output_ceiling"] for item in concepts[concept_id]["deduction_interfaces"]}
            self.assertEqual(relation_values, set(concepts[concept_id]["allowed_inferences"]))
            self.assertEqual(output_values, set(concepts[concept_id]["allowed_inferences"]))

    def test_cm_branch_conditions_and_conflict_disambiguations_are_explicit(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        expected_prerequisites = {
            "V8-CANON-CM-MAINTENANCE-CURRENT": ["条件为“维护输入即时改变K/F保持”"],
            "V8-CANON-CM-MAINTENANCE-CUMULATIVE": ["条件为“磨损历史项提供条件增量、累积或迟恢复”"],
            "V8-CANON-CM-LOAD-INSTANT": ["只要求同型需求—容量和同窗即时缺口"],
            "V8-CANON-CM-LOAD-CUMULATIVE": ["只有历史项改变后续容量或恢复，并由 G3-instance 支持时"],
            "V8-CANON-CM-PHASE-PATTERN": ["条件为“同一K、两个可复核区间、预定阈值模式”"],
            "V8-CANON-CM-PHASE-CAUSAL-TRIGGER": ["条件为“指定触发通道、通道干预或可识别自然变异”"],
            "V8-CANON-CM-PHASE-HYSTERETIC": ["只有主张迟滞、路径或迟恢复时才追加 G3-instance"],
            "V8-CANON-CM-SELECTION-PATTERN": ["条件为“V、D、R、下一轮、重复轮次、漂变竞争”"],
            "V8-CANON-CM-SELECTION-CARRIER": ["条件为“指定保留或再生产通道、通道扰动或可识别自然变异”"],
            "V8-CANON-CM-SELECTION-HISTORY": ["条件为“跨轮历史项条件增量、当前状态控制”"],
        }
        for concept_id, prerequisites in expected_prerequisites.items():
            self.assertEqual(concepts[concept_id]["prerequisites"], prerequisites)

        expected_conflicts = {
            "V8-CANON-CM-FEEDBACK": {"V8-CANON-CM-LEARNING"},
            "V8-CANON-CM-LEARNING": {"V8-CANON-CM-FEEDBACK"},
            "V8-CANON-CM-MAINTENANCE-CURRENT": {"V8-CANON-CM-MAINTENANCE-CUMULATIVE"},
            "V8-CANON-CM-MAINTENANCE-CUMULATIVE": {"V8-CANON-CM-MAINTENANCE-CURRENT"},
            "V8-CANON-CM-LOAD-INSTANT": {"V8-CANON-CM-LOAD-CUMULATIVE"},
            "V8-CANON-CM-LOAD-CUMULATIVE": {"V8-CANON-CM-LOAD-INSTANT"},
            "V8-CANON-CM-PHASE-PATTERN": {"V8-CANON-CM-PHASE-CAUSAL-TRIGGER", "V8-CANON-CM-PHASE-HYSTERETIC"},
            "V8-CANON-CM-PHASE-CAUSAL-TRIGGER": {"V8-CANON-CM-PHASE-PATTERN", "V8-CANON-CM-PHASE-HYSTERETIC"},
            "V8-CANON-CM-PHASE-HYSTERETIC": {"V8-CANON-CM-PHASE-PATTERN", "V8-CANON-CM-PHASE-CAUSAL-TRIGGER"},
            "V8-CANON-CM-SELECTION-PATTERN": {"V8-CANON-CM-SELECTION-CARRIER", "V8-CANON-CM-SELECTION-HISTORY"},
            "V8-CANON-CM-SELECTION-CARRIER": {"V8-CANON-CM-SELECTION-PATTERN", "V8-CANON-CM-SELECTION-HISTORY"},
            "V8-CANON-CM-SELECTION-HISTORY": {"V8-CANON-CM-SELECTION-PATTERN", "V8-CANON-CM-SELECTION-CARRIER"},
        }
        actual_conflicts = {
            concept_id: {item["concept_id"] for item in concept["conflicts_disambiguation"]}
            for concept_id, concept in concepts.items()
            if concept["conflicts_disambiguation"]
        }
        for concept_id, target_ids in expected_conflicts.items():
            self.assertTrue(
                target_ids.issubset(actual_conflicts[concept_id]), concept_id
            )
            self.assertTrue(target_ids.issubset(concepts[concept_id]["required_neighbor_ids"]))

    def test_wire_tokens_and_manual_semantic_collisions_form_symmetric_cliques(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        anchors = paragraph_index(REFERENCES / "v8-full-source")
        token_members: dict[str, set[str]] = {}
        for concept_id, concept in concepts.items():
            support = "\n".join(
                anchors[anchor["anchor_id"]][1]
                for anchor in concept["source_anchors"]
            )
            for token in concept["authoritative_wire_tokens"]:
                self.assertIn(token, support)
                token_members.setdefault(token, set()).add(concept_id)

        manual_clusters = (
            {"V8-CANON-SIMPLE-FORECAST-BASELINE", "V8-CANON-N0"},
            {"V8-CANON-INFERENCE-MODE-SIMULATION", "V8-CANON-VOCAB-EVENT-SIMULATED", "V8-CANON-VOCAB-OUTPUT-SIMULATION"},
            {"V8-CANON-UPDATE-PROVENANCE-DIRECT-OBSERVATION", "V8-CANON-VOCAB-EVENT-OBSERVED", "V8-CANON-VOCAB-ACTOR-STATE-OBSERVED"},
            {"V8-CANON-FORECAST-PUBLICATION-STATUS-EXPLANATION-ONLY", "V8-CANON-VOCAB-OUTPUT-EXPLANATION"},
            {"V8-CANON-FORECAST-PUBLICATION-STATUS-SIMULATION-ONLY", "V8-CANON-VOCAB-OUTPUT-SIMULATION"},
            {"V8-CANON-FORECAST-PUBLICATION-STATUS-REGISTERED-FORECAST", "V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST"},
            {"V8-CANON-FORECAST-REGISTRY", "V8-CANON-TOOL-FORECAST-REGISTRY"},
            {
                "V8-CANON-VOCAB-AXIS-RELATION-UNKNOWN",
                "V8-CANON-VOCAB-HSP-CLASSIFICATION-MODE-UNKNOWN",
                "V8-CANON-VOCAB-HSP-MISSING-STATUS-UNKNOWN",
                "V8-CANON-VOCAB-X0-RESULT-UNKNOWN",
                "V8-CANON-VOCAB-ACTOR-STATE-UNKNOWN",
                "V8-CANON-VOCAB-CIRCLE-TRANSITION-UNKNOWN",
                "V8-CANON-VOCAB-INFO-UNKNOWN",
            },
            {"V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE", "V8-CANON-VOCAB-X0-RESULT-CANDIDATE"},
            {"V8-CANON-VOCAB-GOV-FRAMEWORK-RETIRED", "V8-CANON-VOCAB-ACTOR-STATE-RETIRED", "V8-CANON-VOCAB-LEDGER-RETIRED"},
        )
        clusters = [members for members in token_members.values() if len(members) > 1]
        clusters.extend(manual_clusters)
        for cluster in clusters:
            for source_id in cluster:
                conflicts = {
                    item["concept_id"]: item["disambiguation"]
                    for item in concepts[source_id]["conflicts_disambiguation"]
                }
                with self.subTest(source=source_id, cluster=sorted(cluster)):
                    self.assertTrue((cluster - {source_id}).issubset(conflicts))
                    for target_id in cluster - {source_id}:
                        self.assertEqual(conflicts[target_id], concepts[source_id]["definition"])
                        self.assertIn(target_id, concepts[source_id]["required_neighbor_ids"])
                        self.assertIn(source_id, concepts[target_id]["required_neighbor_ids"])

    def test_shared_table_headers_do_not_change_source_row_neighbor_order(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        sequences = (
            [f"V8-CANON-H{index}" for index in range(1, 7)],
            [f"V8-CANON-VOCAB-ACTOR-STATE-{item}" for item in ("UNKNOWN", "CANDIDATE", "SUPPORTED-HYPOTHESIS", "OBSERVED", "CONTESTED", "RETIRED")],
            [f"V8-CANON-VOCAB-EVENT-{item}" for item in ("OBSERVED", "REPORTED", "PLANNED", "HYPOTHETICAL", "SIMULATED")],
        )
        for sequence in sequences:
            for left, right in zip(sequence, sequence[1:]):
                with self.subTest(left=left, right=right):
                    self.assertIn(right, concepts[left]["required_neighbor_ids"])
                    self.assertIn(left, concepts[right]["required_neighbor_ids"])

    def test_expansion_parent_families_have_exact_membership_and_symmetric_cliques(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        families = {
            "V8-CANON-ROLE-ACTIVATION": {
                f"V8-CANON-ACTOR-CIRCLE-DIRECTION-{code}"
                for code in ("CIRCLE-TO-ACTOR", "ACTOR-TO-CIRCLE", "BIDIRECTIONAL-FEEDBACK")
            },
            "V8-CANON-MULTICIRCLE-JOINT-OBJECT": {
                f"V8-CANON-CROSS-CHANNEL-BRIDGE-{code}"
                for code in ("M-TO-PSI", "PSI-TO-M", "M-PSI-CLOSED-LOOP")
            },
            "V8-CANON-OMEGA-F-UPDATE": {
                f"V8-CANON-UPDATE-PROVENANCE-{code}"
                for code in ("DIRECT-OBSERVATION", "MECHANISM-INFERENCE", "SCENARIO-VALUE", "UNEXPLAINED-RESIDUAL")
            },
            "V8-CANON-CROSS-CIRCLE-CASCADE": {
                f"V8-CANON-CROSS-CIRCLE-CASCADE-{code}"
                for code in ("MEMBERSHIP", "RESOURCE", "MEANING", "INSTITUTIONAL", "PLATFORM")
            },
            "V8-CANON-VARIABLE-CANDIDATE-LEDGER": {
                f"V8-CANON-CANDIDATE-SOURCE-{code}"
                for code in ("SYSTEM-RESIDUAL", "PARTICIPANT-NARRATIVE", "CROSS-CASE-REPETITION", "MODEL-SEARCH", "AI-SUGGESTION")
            },
            "V8-CANON-BRANCHING-PATH-GRAPH": {
                *(f"V8-CANON-INFERENCE-MODE-{code}" for code in ("SCENARIO", "COUNTERFACTUAL", "SIMULATION")),
                *(f"V8-CANON-FORECAST-SIGNAL-{code}" for code in ("EARLY", "REVERSE", "TRIGGER")),
            },
            "V8-CANON-SIMPLE-FORECAST-BASELINE": {
                f"V8-CANON-FORECAST-EVALUATION-{code}"
                for code in ("CALIBRATION", "RESOLUTION", "COVERAGE", "BASELINE-GAIN", "DISTRIBUTIONAL-ERROR", "STABILITY")
            },
            "V8-CANON-VOCAB-OUTPUT-CONDITIONAL-FORECAST": {
                f"V8-CANON-FORECAST-PUBLICATION-STATUS-{code}"
                for code in ("EXPLANATION-ONLY", "SIMULATION-ONLY", "REGISTERED-FORECAST", "NORMATIVE-NOT-PASSED", "EXTERNALLY-AUTHORIZED")
            },
            "V8-CANON-GOV-22": {
                f"V8-CANON-GOVERNANCE-DEBT-{code}"
                for code in ("OBJECT", "VARIABLE", "COMPLEXITY", "CALIBRATION", "POWER")
            },
            "V8-CANON-GOV-01": {
                f"V8-CANON-SELF-DIAGNOSIS-OBJECT-{code}"
                for code in ("DOCUMENT", "CONCEPT", "PRACTICE", "COMMUNITY")
            },
            "V8-CANON-GOV-02": {
                f"V8-CANON-CONSENSUS-COMPONENT-{code}"
                for code in ("ISSUE-REGISTRATION", "MATERIAL-DISCLOSURE", "AFFECTED-OBJECT-IDENTIFICATION", "DISSENT-ENTRY", "DECISION-GRADING", "MINORITY-OPINION-RETENTION")
            },
        }
        for parent_id, child_ids in families.items():
            family = {parent_id, *child_ids}
            self.assertTrue(family.issubset(concepts))
            for source_id in family:
                with self.subTest(parent=parent_id, source=source_id):
                    self.assertTrue(
                        (family - {source_id}).issubset(
                            concepts[source_id]["required_neighbor_ids"]
                        )
                    )

    def test_publication_status_gov19_and_sj3_rows_keep_exact_roles(self) -> None:
        anchors = paragraph_index(REFERENCES / "v8-full-source")
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        for code, anchor_number in (
            ("EXPLANATION-ONLY", 3293),
            ("SIMULATION-ONLY", 3296),
            ("REGISTERED-FORECAST", 3299),
            ("NORMATIVE-NOT-PASSED", 3302),
            ("EXTERNALLY-AUTHORIZED", 3305),
        ):
            concept = concepts[f"V8-CANON-FORECAST-PUBLICATION-STATUS-{code}"]
            self.assertEqual(
                concept["forbidden_substitutions_or_generalizations"],
                [anchors[f"V8-P{anchor_number:04d}"][1]],
            )

        gov19 = concepts["V8-CANON-GOV-19"]
        self.assertIn(
            {"anchor_id": "V8-P3755", "source_file": "16-governance.md"},
            gov19["source_anchors"],
        )
        self.assertIn(anchors["V8-P3755"][1], gov19["prerequisites"])
        self.assertIn("V8-CANON-VERSION-LOG", gov19["required_neighbor_ids"])
        self.assertIn("V8-CANON-GOV-19", concepts["V8-CANON-VERSION-LOG"]["required_neighbor_ids"])

        sj3 = concepts["V8-CANON-SJ3"]
        self.assertEqual(sj3["evidence_requirements"], [anchors["V8-P3457"][1]])

        contract_owner_anchors = {
            "V8-CANON-ACTOR-STATE": ("V8-P2565",),
            "V8-CANON-PERSONALITY-HYPOTHESIS": (
                "V8-P2613", "V8-P2614", "V8-P2615",
            ),
            "V8-CANON-MULTICIRCLE-JOINT-OBJECT": (
                "V8-P2772", "V8-P2782", "V8-P2889", "V8-P2891",
            ),
            "V8-CANON-VOCAB-OUTPUT-SIMULATION": ("V8-P2911", "V8-P2966"),
            "V8-CANON-FORECAST-REGISTRY": ("V8-P3122",),
            "V8-CANON-VOCAB-OUTPUT-LIMITED-CHOICE": ("V8-P3228",),
            "V8-CANON-DF9": ("V8-P3273",),
        }
        for concept_id, anchor_ids in contract_owner_anchors.items():
            for anchor_id in anchor_ids:
                self.assertIn(
                    {"anchor_id": anchor_id, "source_file": anchors[anchor_id][0]},
                    concepts[concept_id]["source_anchors"],
                )

    def test_high_risk_cards_keep_their_role_specific_rows(self) -> None:
        anchors = paragraph_index(REFERENCES / "v8-full-source")
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}

        h_fragments = {
            1: (["预先指定的候选意义安排相对比较条件"], ["资源、行动或协调结果出现超过阈值的差异"]),
            2: ([], []),
            3: (["申诉、审计或反馈改变记录、规则、资源、角色、责任、记忆或停止条件"], ["有实际执行记录"]),
            4: (["位置、中介、公开条件、结果量、比较条件和阈值均预先指定"], ["被证据支持的遮蔽、放大或反身通道"]),
            5: (["历史事件、候选载体、基线、留痕量、阈值与持久窗口均预先指定"], ["出现超过阈值的持久差异"]),
            6: ([], []),
        }
        for index, value in enumerate((1083, 1087, 1091, 1095, 1099, 1103), 1):
            concept = concepts[f"V8-CANON-H{index}"]
            with self.subTest(card=f"H{index}"):
                self.assertEqual(
                    {item["anchor_id"] for item in concept["source_anchors"]},
                    {*(f"V8-P{item:04d}" for item in range(1079, 1083)), *(f"V8-P{item:04d}" for item in range(value, value + 4))},
                )
                self.assertEqual(concept["definition"], anchors[f"V8-P{value + 2:04d}"][1])
                self.assertEqual(concept["allowed_inferences"], [anchors[f"V8-P{value + 2:04d}"][1]])
                self.assertEqual(concept["prerequisites"], h_fragments[index][0])
                self.assertEqual(concept["evidence_requirements"], h_fragments[index][1])
                self.assertEqual(concept["forbidden_substitutions_or_generalizations"], [anchors[f"V8-P{value + 3:04d}"][1]])
                self.assertEqual(concept["common_misuses"], [])
                self.assertEqual(concept["counterexamples"], [])
                self.assertEqual(concept["withdrawal_conditions"], [])
                self.assertEqual(concept["action_ceiling"], anchors[f"V8-P{value + 3:04d}"][1])

        actor_cards = (("UNKNOWN", 2651), ("CANDIDATE", 2655), ("SUPPORTED-HYPOTHESIS", 2659), ("OBSERVED", 2663), ("CONTESTED", 2667), ("RETIRED", 2671))
        for code, value in actor_cards:
            concept = concepts[f"V8-CANON-VOCAB-ACTOR-STATE-{code}"]
            retained = anchors[f"V8-P{value + 3:04d}"][1]
            upgrade = anchors[f"V8-P{value + 2:04d}"][1]
            with self.subTest(card=f"ACTOR-STATE-{code}"):
                self.assertEqual(
                    {item["anchor_id"] for item in concept["source_anchors"]},
                    {*(f"V8-P{item:04d}" for item in range(2647, 2651)), *(f"V8-P{item:04d}" for item in range(value, value + 4))},
                )
                self.assertEqual(concept["definition"], anchors[f"V8-P{value:04d}"][1])
                self.assertEqual(concept["allowed_inferences"], [anchors[f"V8-P{value + 1:04d}"][1]])
                self.assertEqual(concept["prerequisites"], [upgrade])
                self.assertEqual(concept["evidence_requirements"], [upgrade, *([] if code == "OBSERVED" else [retained])])
                self.assertEqual(concept["forbidden_substitutions_or_generalizations"], [retained] if code == "OBSERVED" else [])
                self.assertEqual(concept["common_misuses"], [])
                self.assertEqual(concept["counterexamples"], [])
                self.assertEqual(concept["withdrawal_conditions"], [])
                self.assertEqual(concept["action_ceiling"], retained if code == "OBSERVED" else None)

        event_cards = (("OBSERVED", 2937), ("REPORTED", 2941), ("PLANNED", 2945), ("HYPOTHETICAL", 2949), ("SIMULATED", 2953))
        for code, value in event_cards:
            concept = concepts[f"V8-CANON-VOCAB-EVENT-{code}"]
            fact_status = anchors[f"V8-P{value + 2:04d}"][1]
            required_limit = anchors[f"V8-P{value + 3:04d}"][1]
            explicit_forbidden = [item for item in (fact_status, required_limit) if "不等于" in item or "禁止" in item]
            with self.subTest(card=f"EVENT-{code}"):
                self.assertEqual(
                    {item["anchor_id"] for item in concept["source_anchors"]},
                    {*(f"V8-P{item:04d}" for item in range(2933, 2937)), *(f"V8-P{item:04d}" for item in range(value, value + 4))},
                )
                self.assertEqual(concept["definition"], anchors[f"V8-P{value:04d}"][1])
                self.assertEqual(concept["allowed_inferences"], [anchors[f"V8-P{value + 1:04d}"][1], fact_status])
                self.assertEqual(concept["prerequisites"], [])
                self.assertEqual(concept["evidence_requirements"], [required_limit])
                self.assertEqual(concept["forbidden_substitutions_or_generalizations"], explicit_forbidden)
                self.assertEqual(concept["common_misuses"], [])
                self.assertEqual(concept["counterexamples"], [])
                self.assertEqual(concept["withdrawal_conditions"], [])
                self.assertEqual(concept["action_ceiling"], required_limit if code == "SIMULATED" else None)

        c_anchors = (647, 654, 661, 686, 693, 701, 708, 736, 744, 752, 760, 788)
        for index, value in enumerate(c_anchors, 1):
            concept = concepts[f"V8-CANON-C{index}"]
            with self.subTest(card=f"C{index}"):
                self.assertEqual(concept["definition"], anchors[f"V8-P{value + 3:04d}"][1])
                self.assertEqual(concept["allowed_inferences"], [anchors[f"V8-P{value + 3:04d}"][1]])
                self.assertEqual(concept["prerequisites"], [anchors[f"V8-P{value + 2:04d}"][1]])
                self.assertEqual(concept["evidence_requirements"], [anchors[f"V8-P{value + 5:04d}"][1]])
                self.assertEqual(concept["forbidden_substitutions_or_generalizations"], [anchors[f"V8-P{value + 4:04d}"][1]])
                self.assertEqual(concept["common_misuses"], [])
                self.assertEqual(concept["counterexamples"], [])
                self.assertEqual(concept["withdrawal_conditions"], [])

        for code, value in (("CM-FEEDBACK", 1000), ("CM-LEARNING", 1005)):
            concept = concepts[f"V8-CANON-{code}"]
            with self.subTest(card=code):
                self.assertEqual(concept["definition"], anchors[f"V8-P{value + 2:04d}"][1])
                self.assertEqual(concept["allowed_inferences"], [anchors[f"V8-P{value + 2:04d}"][1]])
                if code == "CM-FEEDBACK":
                    feedback = sentence_parts_for_test(anchors["V8-P1004"][1])
                    self.assertEqual(concept["prerequisites"], [anchors["V8-P1002"][1]])
                    self.assertEqual(concept["evidence_requirements"], [feedback[0]])
                    self.assertEqual(concept["counterexamples"], [feedback[1]])
                    self.assertEqual(concept["withdrawal_conditions"], [feedback[1]])
                    self.assertEqual(concept["forbidden_substitutions_or_generalizations"], ["".join(feedback[2:])])
                else:
                    enabling = sentence_parts_for_test(anchors["V8-P1007"][1])
                    learning = sentence_parts_for_test(anchors["V8-P1009"][1])
                    self.assertEqual(concept["prerequisites"], enabling[:2])
                    self.assertEqual(concept["evidence_requirements"], enabling[2:4])
                    self.assertEqual(concept["counterexamples"], [learning[0]])
                    self.assertEqual(concept["withdrawal_conditions"], [learning[1]])
                    self.assertEqual(concept["forbidden_substitutions_or_generalizations"], [learning[2]])
                self.assertEqual(concept["common_misuses"], [])

        maintenance = concepts["V8-CANON-CM-MAINTENANCE"]
        maintenance_requirements = sentence_parts_for_test(anchors["V8-P1018"][1])
        maintenance_failures = sentence_parts_for_test(anchors["V8-P1021"][1])
        maintenance_boundaries = sentence_parts_for_test(anchors["V8-P1022"][1])
        self.assertEqual(maintenance["allowed_inferences"], maintenance_failures[:2])
        self.assertEqual(maintenance["prerequisites"], [maintenance_requirements[2]])
        self.assertEqual(maintenance["evidence_requirements"], maintenance_requirements[3:5])
        self.assertEqual(maintenance["counterexamples"], [
            "对象在目标窗口内无需持续维护仍保持 K/F",
            "维护输入变化不改变 K/F",
            "所谓磨损由独立冲击解释",
            "对象 K 已改变却继续沿用旧维护判据",
        ])
        self.assertEqual(maintenance["withdrawal_conditions"], maintenance_failures[2:4])
        self.assertEqual(maintenance["forbidden_substitutions_or_generalizations"], [maintenance_boundaries[0]])
        self.assertEqual(maintenance["action_ceiling"], maintenance_boundaries[0])

        load = concepts["V8-CANON-CM-LOAD"]
        load_requirements = sentence_parts_for_test(anchors["V8-P1024"][1])
        load_counterexamples = sentence_parts_for_test(anchors["V8-P1027"][1])
        load_boundaries = sentence_parts_for_test(anchors["V8-P1028"][1])
        self.assertEqual(load["allowed_inferences"], load_counterexamples[:2])
        self.assertEqual(load["prerequisites"], [load_requirements[2]])
        self.assertEqual(load["evidence_requirements"], [*load_requirements[3:5], *load_boundaries[:3]])
        self.assertEqual(load["counterexamples"], load_counterexamples[2:4])
        self.assertEqual(load["withdrawal_conditions"], [])
        self.assertEqual(load["forbidden_substitutions_or_generalizations"], [load_counterexamples[4], load_boundaries[3]])
        self.assertEqual(load["action_ceiling"], load_boundaries[3])

        phase = concepts["V8-CANON-CM-PHASE"]
        phase_failures = sentence_parts_for_test(anchors["V8-P1035"][1])
        self.assertEqual(phase["allowed_inferences"], [anchors[f"V8-P{value:04d}"][1] for value in (1032, 1033, 1034)])
        self.assertEqual(phase["prerequisites"], ["同一候选对象合同和 K 下，只要预先登记状态变量、候选参数或触发条件、阈值，以及噪声和分箱稳健性"])
        self.assertEqual(phase["evidence_requirements"], ["至少两个可重复区分的运转区间"])
        self.assertEqual(phase["counterexamples"], [
            "连续趋势若在同一状态分布内充分解释变化",
            "阈值随分箱任意移动",
            "转移前 K 已失效",
        ])
        self.assertEqual(phase["withdrawal_conditions"], [phase_failures[0]])
        self.assertEqual(phase["forbidden_substitutions_or_generalizations"], phase_failures[1:4])
        self.assertEqual(phase["action_ceiling"], phase_failures[3])

        selection = concepts["V8-CANON-CM-SELECTION"]
        selection_dependency = sentence_parts_for_test(anchors["V8-P1037"][1])
        selection_failures = sentence_parts_for_test(anchors["V8-P1042"][1])
        self.assertEqual(selection["allowed_inferences"], [anchors[f"V8-P{value:04d}"][1] for value in (1039, 1040, 1041)])
        self.assertEqual(selection["prerequisites"], ["条件为“V、D、R、下一轮、重复轮次、漂变竞争”"])
        self.assertEqual(selection["evidence_requirements"], [anchors["V8-P1039"][1]])
        self.assertEqual(selection["counterexamples"], [
            selection_failures[0],
            selection_failures[1],
            "漂变模型已经充分",
            "候选再生产通道被扰动而保留不变",
        ])
        self.assertEqual(selection["withdrawal_conditions"], selection_failures[2:4])
        self.assertEqual(selection["forbidden_substitutions_or_generalizations"], [selection_dependency[2], *selection_failures[4:6]])
        self.assertEqual(selection["action_ceiling"], selection_failures[5])

        self.assertEqual(concepts["V8-CANON-N0"]["definition"], anchors["V8-P0415"][1])
        self.assertEqual(
            concepts["V8-CANON-N0"]["allowed_inferences"],
            ["".join(sentence_parts_for_test(anchors["V8-P0416"][1])[:3])],
        )
        omega_definition = "\n".join(anchors[f"V8-P{value:04d}"][1] for value in range(2958, 2963))
        self.assertEqual(concepts["V8-CANON-OMEGA-F-UPDATE"]["definition"], omega_definition)
        self.assertEqual(concepts["V8-CANON-OMEGA-F-UPDATE"]["allowed_inferences"], [anchors["V8-P2963"][1]])
        self.assertEqual(concepts["V8-CANON-OMEGA-F-UPDATE"]["prerequisites"], [])
        self.assertEqual(concepts["V8-CANON-OMEGA-F-UPDATE"]["evidence_requirements"], [])
        self.assertEqual(concepts["V8-CANON-OMEGA-F-UPDATE"]["common_misuses"], [])
        self.assertEqual(concepts["V8-CANON-OMEGA-F-UPDATE"]["counterexamples"], [])
        self.assertIn(
            "这个式子只规定记录责任，不宣称存在唯一真实的 F，也不允许用函数符号替代具体机制。",
            concepts["V8-CANON-OMEGA-F-UPDATE"]["forbidden_substitutions_or_generalizations"],
        )

        actor = concepts["V8-CANON-ACTOR-STATE"]
        actor_boundary = sentence_parts_for_test(anchors["V8-P2532"][1])
        self.assertEqual(actor["allowed_inferences"], [actor_boundary[0]])
        self.assertEqual(actor["prerequisites"], [])
        self.assertEqual(actor["evidence_requirements"], [])
        self.assertEqual(actor["forbidden_substitutions_or_generalizations"], actor_boundary[1:])
        self.assertEqual(actor["common_misuses"], [actor_boundary[2]])
        self.assertEqual(actor["counterexamples"], [])
        self.assertEqual(actor["withdrawal_conditions"], [])
        self.assertEqual(actor["action_ceiling"], actor_boundary[2])

        ledger_tokens = {
            "PROPOSED": "提出",
            "UNDER-TEST": "检验中",
            "SUPPORTED-CANDIDATE": "得到支持的候选",
            "REJECTED": "拒绝",
            "RETIRED": "退役",
        }
        ledger_evidence = sentence_parts_for_test(anchors["V8-P3061"][1])[2]
        for code, token in ledger_tokens.items():
            concept = concepts[f"V8-CANON-VOCAB-LEDGER-{code}"]
            with self.subTest(card=f"LEDGER-{code}"):
                self.assertEqual(concept["definition"], token)
                self.assertEqual(
                    {item["anchor_id"] for item in concept["source_anchors"]},
                    {"V8-P3061", "V8-P3062"},
                )
                self.assertEqual(concept["prerequisites"], [])
                self.assertEqual(concept["evidence_requirements"], [ledger_evidence])
                self.assertEqual(concept["common_misuses"], [])
                self.assertEqual(concept["counterexamples"], [])
                self.assertEqual(concept["withdrawal_conditions"], [])
                self.assertIsNone(concept["action_ceiling"])

        for code, value in (("PROBABILITY-OR-RANGE", 3158), ("RANK-OR-SUPPORT", 3161), ("CONDITIONAL-DIRECTION", 3164), ("NO-FORECAST", 3167)):
            concept = concepts[f"V8-CANON-VOCAB-FORECAST-LEVEL-{code}"]
            with self.subTest(card=f"FORECAST-{code}"):
                self.assertEqual(concept["prerequisites"], [anchors[f"V8-P{value - 1:04d}"][1]])
                self.assertEqual(concept["definition"], anchors[f"V8-P{value:04d}"][1])
                self.assertEqual(concept["evidence_requirements"], [anchors[f"V8-P{value + 1:04d}"][1]])


@unittest.skipUnless(
    REGISTRY_PATH.is_file() and CONTRACT_MAP_PATH.is_file() and ROUTE_MAP_PATH.is_file(),
    "v8 knowledge graph not implemented",
)
class ProMaxV8ClosedGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(REGISTRY_PATH)
        cls.contract_map = load_json(CONTRACT_MAP_PATH)
        cls.route_map = load_json(ROUTE_MAP_PATH)

    def test_contract_files_are_byte_exact_and_pinned(self) -> None:
        entries = {item["contract_id"]: item for item in self.contract_map["contracts"]}
        self.assertEqual(set(entries), set(CONTRACTS))
        for contract_id, (name, expected_sha) in CONTRACTS.items():
            path = REFERENCES / "concept-contracts" / name
            entry = entries[contract_id]
            with self.subTest(contract=contract_id):
                self.assertEqual(entry["path"], f"concept-contracts/{name}")
                self.assertEqual(entry["sha256"], expected_sha)
                self.assertEqual(sha256_file(path), expected_sha)
                payload = load_json(path)
                self.assertEqual(payload["schema_id"], contract_id)

    def test_registry_contract_route_graph_is_bidirectionally_closed(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        contract_rows = self.contract_map["contracts"]
        route_rows = self.route_map["routes"]
        self.assertEqual(self.contract_map["snapshot_sha256"], SNAPSHOT_SHA256)
        self.assertEqual(self.route_map["snapshot_sha256"], SNAPSHOT_SHA256)
        self.assertEqual(len(contract_rows), len({item["contract_id"] for item in contract_rows}))
        self.assertEqual(len(route_rows), 16)
        self.assertEqual(self.route_map["route_count"], 16)
        self.assertEqual(self.route_map["signal_semantics"], EXPECTED_ROUTE_SIGNAL_SEMANTICS)
        self.assertEqual(len(route_rows), len({item["route_id"] for item in route_rows}))
        self.assertEqual(len(route_rows), len({item["source_section"] for item in route_rows}))
        self.assertEqual(
            {item["route_id"]: item["source_section"] for item in route_rows},
            EXPECTED_ROUTE_SOURCES,
        )
        contracts = {item["contract_id"]: item for item in contract_rows}
        routes = {item["route_id"]: item for item in route_rows}
        routed_ids: set[str] = set()
        for concept_id, concept in concepts.items():
            self.assertNotIn(concept_id, concept["required_neighbor_ids"])
            for neighbor_id in concept["required_neighbor_ids"]:
                self.assertIn(neighbor_id, concepts)
                self.assertIn(concept_id, concepts[neighbor_id]["required_neighbor_ids"])
            self.assertEqual(
                len(concept["conflicts_disambiguation"]),
                len({item["concept_id"] for item in concept["conflicts_disambiguation"]}),
            )
            for conflict in concept["conflicts_disambiguation"]:
                self.assertIn(conflict["concept_id"], concepts)
            for interface in concept["deduction_interfaces"]:
                self.assertIn(interface["target_concept_id"], concepts)
            for contract_id in concept["contract_ids"]:
                self.assertIn(contract_id, contracts)
                self.assertIn(concept_id, contracts[contract_id]["concept_ids"])
            self.assertEqual(
                set(concept["contract_ids"]),
                {item["contract_id"] for item in concept["contract_bindings"]},
            )
            for route_id in concept["route_ids"]:
                self.assertIn(route_id, routes)
                route_refs = set(routes[route_id]["required_concept_ids"])
                route_refs.update(routes[route_id]["neighbor_closure_ids"])
                self.assertIn(concept_id, route_refs)
            source_files = {item["source_file"] for item in concept["source_anchors"]}
            self.assertTrue(
                any(routes[route_id]["source_section"] in source_files for route_id in concept["route_ids"]),
                f"no source route backlink for {concept_id}",
            )
        for contract_id, contract in contracts.items():
            bound_ids = {item["concept_id"] for item in contract["bindings"]}
            self.assertEqual(set(contract["concept_ids"]), bound_ids)
            for concept_id in contract["concept_ids"]:
                self.assertIn(concept_id, concepts)
                self.assertIn(contract_id, concepts[concept_id]["contract_ids"])
        for route_id, route in routes.items():
            required = set(route["required_concept_ids"])
            closure = set(route["neighbor_closure_ids"])
            self.assertFalse(required & closure)
            refs = required | closure
            self.assertEqual(
                (route["task_signals"], route["object_signals"]),
                EXPECTED_ROUTE_SIGNALS[route_id],
            )
            expected_primary_ids = {
                concept_id
                for concept_id, concept in concepts.items()
                if next(
                    anchor["source_file"]
                    for anchor in concept["source_anchors"]
                    if anchor["anchor_id"] == concept["primary_source_anchor_id"]
                ) == route["source_section"]
            }
            self.assertEqual(
                required,
                expected_primary_ids,
                f"route seeds must exhaust explicit primary-anchor ownership: {route_id}",
            )
            reached = set(required)
            frontier = list(required)
            while frontier:
                current = frontier.pop()
                for neighbor_id in concepts[current]["required_neighbor_ids"]:
                    if neighbor_id not in reached:
                        reached.add(neighbor_id)
                        frontier.append(neighbor_id)
            self.assertEqual(closure, reached - required, f"incorrect fixed-point closure: {route_id}")
            for concept_id in refs:
                self.assertIn(concept_id, concepts)
                self.assertIn(route_id, concepts[concept_id]["route_ids"])
            routed_ids.update(refs)
        self.assertEqual(routed_ids, set(concepts), "every canonical concept must be routed")

    def test_primary_route_ownership_does_not_depend_on_support_anchor_order(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        routes = {item["source_section"]: set(item["required_concept_ids"]) for item in self.route_map["routes"]}
        for concept_id, concept in concepts.items():
            primary_id = concept["primary_source_anchor_id"]
            primary_file = next(
                anchor["source_file"]
                for anchor in concept["source_anchors"]
                if anchor["anchor_id"] == primary_id
            )
            reordered = list(reversed(concept["source_anchors"]))
            reordered_primary_file = next(
                anchor["source_file"] for anchor in reordered if anchor["anchor_id"] == primary_id
            )
            with self.subTest(concept=concept_id):
                self.assertEqual(reordered_primary_file, primary_file)
                self.assertIn(concept_id, routes[primary_file])

    def test_json_pointer_contract_bindings_are_exactly_bidirectional(self) -> None:
        concepts = {item["concept_id"]: item for item in self.registry["concepts"]}
        map_bindings = {
            (contract["contract_id"], binding["json_pointer"], binding["concept_id"], binding["binding_role"])
            for contract in self.contract_map["contracts"]
            for binding in contract["bindings"]
        }
        registry_bindings = {
            (binding["contract_id"], binding["json_pointer"], concept_id, binding["binding_role"])
            for concept_id, concept in concepts.items()
            for binding in concept["contract_bindings"]
        }
        self.assertEqual(map_bindings, registry_bindings)
        actual_binding_concepts: dict[tuple[str, str], set[str]] = {}
        for contract in self.contract_map["contracts"]:
            payload = load_json(REFERENCES / contract["path"])
            self.assertEqual(contract["scope"], payload["scope"])
            expected_pointers, leaf_pointers = semantic_pointer_inventory(payload)
            self.assertEqual(
                len(leaf_pointers),
                EXPECTED_SEMANTIC_LEAF_COUNTS[contract["contract_id"]],
            )
            self.assertEqual(
                len(expected_pointers),
                EXPECTED_SEMANTIC_POINTER_COUNTS[contract["contract_id"]],
            )
            pointers = {binding["json_pointer"] for binding in contract["bindings"]}
            unbound_pointers = {
                item["json_pointer"] for item in contract["unbound_semantic_pointers"]
            }
            self.assertEqual(
                unbound_pointers,
                EXPECTED_UNBOUND_POINTERS[contract["contract_id"]],
            )
            self.assertFalse(pointers & unbound_pointers)
            self.assertEqual(pointers | unbound_pointers, set(expected_pointers))
            for pointer in pointers | unbound_pointers:
                self.assertIsNotNone(resolve_pointer(payload, pointer))
            self.assertEqual(contract["required_semantic_pointers"], expected_pointers)
            for unbound in contract["unbound_semantic_pointers"]:
                self.assertEqual(
                    unbound,
                    {
                        "json_pointer": unbound["json_pointer"],
                        "reason_code": "no_distinct_v8_canonical_concept",
                        "runtime_requirement": "read_authored_contract_pointer_directly",
                    },
                )
            for binding in contract["bindings"]:
                actual_binding_concepts.setdefault(
                    (contract["contract_id"], binding["json_pointer"]), set()
                ).add(binding["concept_id"])
                self.assertEqual(
                    binding["source_anchors"],
                    concepts[binding["concept_id"]]["source_anchors"],
                )
                pointer = binding["json_pointer"]
                self.assertEqual(
                    binding["binding_role"],
                    expected_binding_role_for_test(pointer),
                    f"wrong exact role for {contract['contract_id']}:{pointer}",
                )

        expected_flat = {
            (contract_id, pointer): set(concept_ids)
            for contract_id, pointer_map in EXPECTED_BOUND_CONCEPT_IDS.items()
            for pointer, concept_ids in pointer_map.items()
        }
        self.assertEqual(actual_binding_concepts, expected_flat)
        actual_owner_map = {
            contract_id: {
                pointer: sorted(actual_binding_concepts[(contract_id, pointer)])
                for pointer in pointer_map
            }
            for contract_id, pointer_map in EXPECTED_BOUND_CONCEPT_IDS.items()
        }
        self.assertEqual(
            owner_oracle_sha256(EXPECTED_BOUND_CONCEPT_IDS),
            EXPECTED_OWNER_ORACLE_SHA256,
        )
        self.assertEqual(
            owner_oracle_sha256(actual_owner_map),
            EXPECTED_OWNER_ORACLE_SHA256,
        )

    def test_strict_contract_owner_oracle_counts_and_narrow_ownership(self) -> None:
        expected_counts = {
            "v8_actor_state_contracts": (106, 8, 150, 24),
            "v8_multicircle_contracts": (113, 12, 162, 36),
            "v8_simulation_forecast_contracts": (145, 23, 211, 70),
        }
        for contract in self.contract_map["contracts"]:
            contract_id = contract["contract_id"]
            actual = (
                len({item["json_pointer"] for item in contract["bindings"]}),
                len(contract["unbound_semantic_pointers"]),
                len(contract["bindings"]),
                len(contract["concept_ids"]),
            )
            self.assertEqual(actual, expected_counts[contract_id])

        simulation = EXPECTED_BOUND_CONCEPT_IDS["v8_simulation_forecast_contracts"]
        for pointer in (
            "/forecast_record_schema/comparison_rule",
            "/baseline_policy",
            "/guards/6",
        ):
            self.assertEqual(
                simulation[pointer],
                ["V8-CANON-SIMPLE-FORECAST-BASELINE"],
            )
        self.assertIn(
            "/simulation_run_schema/propagation_rule",
            EXPECTED_UNBOUND_POINTERS["v8_simulation_forecast_contracts"],
        )


@unittest.skipUnless(CHECKER_PATH.is_file(), "v8 knowledge checker not implemented")
class ProMaxV8KnowledgeTamperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_module("promax_v8_knowledge_checker_tamper", CHECKER_PATH)

    def copied_repo(self):
        return _CopiedKnowledgeRepository()

    def rebound_asset_hashes(self, repo: Path):
        return _CheckerAssetHashOverride(self.checker, repo)

    def assert_error(self, errors: list[str], fragment: str) -> None:
        self.assertTrue(any(fragment.lower() in item.lower() for item in errors), errors)

    def test_checker_uses_strict_rfc6901_pointer_resolution(self) -> None:
        payload = {"a/b": {"~key": ["zero", "one"]}}
        self.assertEqual(self.checker.resolve_pointer(payload, "/a~1b/~0key/1"), "one")
        for pointer in ("", "a", "/a~2b", "/a~1b/~0key/00", "/a~1b/~0key/-"):
            with self.subTest(pointer=pointer):
                with self.assertRaises((ValueError, KeyError, IndexError, TypeError)):
                    self.checker.resolve_pointer(payload, pointer)

    def test_checker_rejects_each_publication_status_forbidden_row_tamper(self) -> None:
        registry = load_json(REGISTRY_PATH)
        anchors = self.checker.paragraph_index(REFERENCES / "v8-full-source")
        publication_ids = [
            f"V8-CANON-FORECAST-PUBLICATION-STATUS-{code}"
            for code in (
                "EXPLANATION-ONLY", "SIMULATION-ONLY", "REGISTERED-FORECAST",
                "NORMATIVE-NOT-PASSED", "EXTERNALLY-AUTHORIZED",
            )
        ]
        for concept_id in publication_ids:
            with self.subTest(concept=concept_id):
                concepts = {
                    item["concept_id"]: json.loads(json.dumps(item, ensure_ascii=False))
                    for item in registry["concepts"]
                }
                concepts[concept_id]["forbidden_substitutions_or_generalizations"] = []
                errors: list[str] = []
                self.checker.validate_fixed_high_risk_rows(concepts, anchors, errors)
                self.assert_error(errors, "publication")

    def test_missing_anchor_and_unsupported_definition_are_rejected(self) -> None:
        for label, mutate, fragment in (
            (
                "anchor",
                lambda item: item["source_anchors"][0].update(anchor_id="V8-P9999"),
                "anchor",
            ),
            (
                "definition",
                lambda item: item.update(definition="没有任何 v8 锚点支持的杜撰定义"),
                "definition",
            ),
            (
                "inference",
                lambda item: item["allowed_inferences"].append("没有锚点支持的推论"),
                "inference",
            ),
        ):
            with self.subTest(label=label), self.copied_repo() as repo:
                path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                value = load_json(path)
                mutate(value["concepts"][0])
                dump_json(path, value)
                self.assert_error(self.checker.check_repository(repo), fragment)

    def test_conflict_disambiguation_must_be_supported_by_own_source_anchors(self) -> None:
        with self.copied_repo() as repo:
            path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
            registry = load_json(path)
            concept = next(
                item
                for item in registry["concepts"]
                if item["concept_id"] == "V8-CANON-CM-FEEDBACK"
            )
            concept["conflicts_disambiguation"][0]["disambiguation"] = (
                "这是一条未由该概念任何 v8 源锚点支持的伪造消歧。"
            )
            dump_json(path, registry)
            with self.rebound_asset_hashes(repo):
                self.assert_error(
                    self.checker.check_repository(repo),
                    "conflict disambiguation is unsupported",
                )

    def test_short_true_substrings_cannot_replace_curated_definition_or_inference(self) -> None:
        for label, mutate, fragment in (
            (
                "definition",
                lambda item: item.update(definition="允许结论"),
                "definition",
            ),
            (
                "inference",
                lambda item: item.update(allowed_inferences=["允许结论"]),
                "inference",
            ),
        ):
            with self.subTest(label=label), self.copied_repo() as repo:
                path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                value = load_json(path)
                item = next(concept for concept in value["concepts"] if concept["concept_id"] == "V8-CANON-C1")
                mutate(item)
                dump_json(path, value)
                with self.rebound_asset_hashes(repo):
                    self.assert_error(self.checker.check_repository(repo), fragment)

    def test_hv_source_card_and_route_tampering_survives_asset_hash_rebinding(self) -> None:
        def cross_card_anchor(registry) -> None:
            hv01 = next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")
            hv02 = next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV02")
            hv01["source_card"]["fields"]["evidence"].update(
                hv02["source_card"]["fields"]["evidence"]
            )

        cases = (
            (
                "delete field",
                lambda registry: next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")["source_card"]["fields"].pop("rollback"),
                "schema validation",
            ),
            (
                "wrong label",
                lambda registry: next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")["source_card"]["fields"]["evidence"].update(label_text="伪造标签"),
                "source_card",
            ),
            (
                "wrong digest",
                lambda registry: next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")["source_card"].update(content_sha256="0" * 64),
                "source_card",
            ),
            (
                "wrong card heading",
                lambda registry: next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")["source_card"].update(
                    card_anchor={
                        "anchor_id": "V8-P2195",
                        "source_file": "07-human-world.md",
                    }
                ),
                "heading",
            ),
            ("cross-card anchor", cross_card_anchor, "source_card"),
            (
                "route drift",
                lambda registry: next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV10")["conditional_support_routes"][0].update(allowed_conclusion="伪造结论"),
                "route",
            ),
            (
                "non-HV injection",
                lambda registry: next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-C1").update(
                    source_card=next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")["source_card"]
                ),
                "schema validation",
            ),
        )
        for label, mutate, fragment in cases:
            with self.subTest(label=label), self.copied_repo() as repo:
                path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                registry = load_json(path)
                mutate(registry)
                if label in {"wrong label", "wrong card heading", "cross-card anchor"}:
                    card = next(c for c in registry["concepts"] if c["concept_id"] == "V8-CANON-HV01")["source_card"]
                    card["content_sha256"] = canonical_json_sha256(
                        {key: value for key, value in card.items() if key != "content_sha256"}
                    )
                dump_json(path, registry)
                with self.rebound_asset_hashes(repo):
                    self.assert_error(self.checker.check_repository(repo), fragment)

    def test_collision_family_publication_and_global_ceiling_tampering_is_rejected_after_rehash(self) -> None:
        cases = (
            (
                "wrong optional role",
                lambda concepts, registry: next(c for c in concepts if c["concept_id"] == "V8-CANON-C1").update(
                    evidence_requirements=list(next(c for c in concepts if c["concept_id"] == "V8-CANON-C1")["prerequisites"])
                ),
                "semantic-role",
            ),
            (
                "collision",
                lambda concepts, registry: next(c for c in concepts if c["concept_id"] == "V8-CANON-VOCAB-ACTOR-STATE-CANDIDATE").update(conflicts_disambiguation=[]),
                "collision",
            ),
            (
                "family",
                lambda concepts, registry: next(c for c in concepts if c["concept_id"] == "V8-CANON-ROLE-ACTIVATION")["required_neighbor_ids"].remove("V8-CANON-ACTOR-CIRCLE-DIRECTION-CIRCLE-TO-ACTOR"),
                "family",
            ),
            (
                "publication",
                lambda concepts, registry: next(c for c in concepts if c["concept_id"] == "V8-CANON-FORECAST-PUBLICATION-STATUS-EXTERNALLY-AUTHORIZED").update(forbidden_substitutions_or_generalizations=[]),
                "publication",
            ),
            (
                "global ceiling",
                lambda concepts, registry: registry["global_action_ceiling"]["clauses"].append("伪造行动授权"),
                "global action ceiling",
            ),
        )
        for label, mutate, fragment in cases:
            with self.subTest(label=label), self.copied_repo() as repo:
                path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                registry = load_json(path)
                mutate(registry["concepts"], registry)
                dump_json(path, registry)
                with self.rebound_asset_hashes(repo):
                    self.assert_error(self.checker.check_repository(repo), fragment)

    def test_duplicate_name_namespace_collision_and_open_schema_are_rejected(self) -> None:
        cases = (
            (
                "duplicate name",
                "concept-registry/v8-concept-registry.json",
                lambda value: value["concepts"][1].update(
                    authoritative_name_zh=value["concepts"][0]["authoritative_name_zh"]
                ),
                "duplicate",
            ),
            (
                "provisional namespace injection",
                "concept-registry/v8-concept-registry.json",
                lambda value: value["concepts"][0].update(concept_id="PROMAX-PROV-FAKE"),
                "schema validation",
            ),
            (
                "open schema",
                "../schemas/v8-concept-registry.schema.json",
                lambda value: value.update(additionalProperties=True),
                "closed",
            ),
        )
        for label, relative, mutate, fragment in cases:
            with self.subTest(label=label), self.copied_repo() as repo:
                path = repo / "skills/crossframe-promax/references" / relative
                value = load_json(path)
                mutate(value)
                dump_json(path, value)
                self.assert_error(self.checker.check_repository(repo), fragment)

    def test_dangling_and_missing_backlinks_are_rejected(self) -> None:
        for label, mutate, fragment in (
            (
                "dangling neighbor",
                lambda registry, contracts, routes: registry["concepts"][0][
                    "required_neighbor_ids"
                ].append("V8-CANON-NOT-REAL"),
                "dangling",
            ),
            (
                "missing contract backlink",
                lambda registry, contracts, routes: contracts["contracts"][0][
                    "concept_ids"
                ].remove(registry["concepts"][next(
                    index
                    for index, item in enumerate(registry["concepts"])
                    if contracts["contracts"][0]["contract_id"] in item["contract_ids"]
                )]["concept_id"]),
                "backlink",
            ),
            (
                "missing route backlink",
                lambda registry, contracts, routes: next(
                    item
                    for item in registry["concepts"]
                    if len(item["route_ids"]) > 1
                )["route_ids"].pop(),
                "backlink",
            ),
        ):
            with self.subTest(label=label), self.copied_repo() as repo:
                registry_path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                contract_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
                route_path = repo / "skills/crossframe-promax/references/v8-route-map.json"
                registry, contracts, routes = map(load_json, (registry_path, contract_path, route_path))
                mutate(registry, contracts, routes)
                dump_json(registry_path, registry)
                dump_json(contract_path, contracts)
                dump_json(route_path, routes)
                self.assert_error(self.checker.check_repository(repo), fragment)

    def test_contract_mutation_is_rejected_even_when_map_hash_is_cooperatively_changed(self) -> None:
        with self.copied_repo() as repo:
            contract_path = repo / "skills/crossframe-promax/references/concept-contracts/actor-state-contracts.json"
            value = load_json(contract_path)
            value["scope"] += "（被协同篡改）"
            dump_json(contract_path, value)
            map_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
            contract_map = load_json(map_path)
            contract_map["contracts"][0]["sha256"] = sha256_file(contract_path)
            dump_json(map_path, contract_map)
            errors = self.checker.check_repository(repo)
        self.assert_error(errors, "authored contract")

    def test_contract_map_scope_cannot_diverge_from_authored_contract(self) -> None:
        with self.copied_repo() as repo:
            map_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
            contract_map = load_json(map_path)
            contract_map["contracts"][0]["scope"] += "（伪造范围）"
            dump_json(map_path, contract_map)
            errors = self.checker.check_repository(repo)
        self.assert_error(errors, "scope")

    def test_source_markdown_tamper_is_rejected_even_when_registered_excerpts_remain(self) -> None:
        with self.copied_repo() as repo:
            source_path = repo / "skills/crossframe-promax/references/v8-full-source/01-guide.md"
            original = source_path.read_text(encoding="utf-8")
            source_path.write_text(
                original + "\n<!-- unrelated-but-unauthorized-source-change -->\n",
                encoding="utf-8",
                newline="\n",
            )
            errors = self.checker.check_repository(repo)
        self.assert_error(errors, "source integrity")

    def test_contract_binding_pointer_and_backlink_tampering_are_rejected(self) -> None:
        cases = (
            ("wrong pointer", "pointer"),
            ("wrong backlink", "backlink"),
            ("missing enum", "semantic coverage"),
            ("missing guard", "semantic coverage"),
            ("wrong guard role", "guard"),
        )
        for label, fragment in cases:
            with self.subTest(label=label), self.copied_repo() as repo:
                registry_path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                contract_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
                registry = load_json(registry_path)
                contract_map = load_json(contract_path)
                actor = next(
                    item
                    for item in contract_map["contracts"]
                    if item["contract_id"] == "v8_actor_state_contracts"
                )

                if label == "wrong pointer":
                    binding = actor["bindings"][0]
                    old_pointer = binding["json_pointer"]
                    binding["json_pointer"] = "/not_a_real_contract_pointer"
                    actor["required_semantic_pointers"] = [
                        binding["json_pointer"] if item == old_pointer else item
                        for item in actor["required_semantic_pointers"]
                    ]
                    concept = next(
                        item for item in registry["concepts"]
                        if item["concept_id"] == binding["concept_id"]
                    )
                    next(
                        item for item in concept["contract_bindings"]
                        if item["contract_id"] == actor["contract_id"]
                        and item["json_pointer"] == old_pointer
                    )["json_pointer"] = binding["json_pointer"]
                elif label == "wrong backlink":
                    binding = actor["bindings"][0]
                    binding["concept_id"] = next(
                        item["concept_id"]
                        for item in registry["concepts"]
                        if item["concept_id"] != binding["concept_id"]
                    )
                    binding["source_anchors"] = next(
                        item["source_anchors"]
                        for item in registry["concepts"]
                        if item["concept_id"] == binding["concept_id"]
                    )
                else:
                    target_pointer = "/variable_states/0" if label == "missing enum" else "/guards/0"
                    binding = next(
                        item for item in actor["bindings"]
                        if item["json_pointer"] == target_pointer
                    )
                    concept = next(
                        item for item in registry["concepts"]
                        if item["concept_id"] == binding["concept_id"]
                    )
                    registry_binding = next(
                        item for item in concept["contract_bindings"]
                        if item["contract_id"] == actor["contract_id"]
                        and item["json_pointer"] == target_pointer
                    )
                    if label == "wrong guard role":
                        binding["binding_role"] = "definition"
                        registry_binding["binding_role"] = "definition"
                    else:
                        actor["bindings"].remove(binding)
                        actor["required_semantic_pointers"].remove(target_pointer)
                        concept["contract_bindings"].remove(registry_binding)

                dump_json(registry_path, registry)
                dump_json(contract_path, contract_map)
                self.assert_error(self.checker.check_repository(repo), fragment)

    def test_strict_bound_unbound_status_tampering_is_rejected(self) -> None:
        contract_id = "v8_simulation_forecast_contracts"
        unbound_pointer = "/event_record_schema"
        bound_pointer = "/event_kinds/0"
        nearby_concept_id = "V8-CANON-VOCAB-EVENT-OBSERVED"

        def add_binding(contract, registry, pointer: str) -> None:
            concept = next(
                item for item in registry["concepts"]
                if item["concept_id"] == nearby_concept_id
            )
            contract["bindings"].append({
                "json_pointer": pointer,
                "concept_id": nearby_concept_id,
                "binding_role": expected_binding_role_for_test(pointer),
                "source_anchors": concept["source_anchors"],
            })
            concept["contract_bindings"].append({
                "contract_id": contract_id,
                "json_pointer": pointer,
                "binding_role": expected_binding_role_for_test(pointer),
            })
            concept["contract_ids"] = sorted({
                *concept["contract_ids"],
                contract_id,
            })
            contract["concept_ids"] = sorted({
                item["concept_id"] for item in contract["bindings"]
            })

        def remove_binding(contract, registry, pointer: str) -> None:
            removed = [item for item in contract["bindings"] if item["json_pointer"] == pointer]
            self.assertTrue(removed)
            contract["bindings"] = [
                item for item in contract["bindings"] if item["json_pointer"] != pointer
            ]
            for concept in registry["concepts"]:
                concept["contract_bindings"] = [
                    item
                    for item in concept["contract_bindings"]
                    if not (
                        item["contract_id"] == contract_id
                        and item["json_pointer"] == pointer
                    )
                ]
                concept["contract_ids"] = sorted({
                    item["contract_id"] for item in concept["contract_bindings"]
                })
            contract["concept_ids"] = sorted({
                item["concept_id"] for item in contract["bindings"]
            })

        cases = (
            ("delete status", "coverage partition"),
            ("both statuses", "both bound and unbound"),
            ("fake reason", "schema validation"),
            ("unbound to nearby concept", "strict contract owner"),
            ("bound to unbound", "strict unbound"),
        )
        for label, fragment in cases:
            with self.subTest(label=label), self.copied_repo() as repo:
                registry_path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                map_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
                registry = load_json(registry_path)
                contract_map = load_json(map_path)
                contract = next(
                    item for item in contract_map["contracts"]
                    if item["contract_id"] == contract_id
                )
                unbound = next(
                    item for item in contract["unbound_semantic_pointers"]
                    if item["json_pointer"] == unbound_pointer
                )
                if label == "delete status":
                    contract["unbound_semantic_pointers"].remove(unbound)
                elif label == "both statuses":
                    add_binding(contract, registry, unbound_pointer)
                elif label == "fake reason":
                    unbound["reason_code"] = "nearby_concept_is_good_enough"
                elif label == "unbound to nearby concept":
                    contract["unbound_semantic_pointers"].remove(unbound)
                    add_binding(contract, registry, unbound_pointer)
                else:
                    remove_binding(contract, registry, bound_pointer)
                    contract["unbound_semantic_pointers"].append({
                        "json_pointer": bound_pointer,
                        "reason_code": "no_distinct_v8_canonical_concept",
                        "runtime_requirement": "read_authored_contract_pointer_directly",
                    })
                dump_json(registry_path, registry)
                dump_json(map_path, contract_map)
                with self.rebound_asset_hashes(repo):
                    self.assert_error(self.checker.check_repository(repo), fragment)

    def test_malformed_contract_map_types_are_rejected_before_semantic_checks(self) -> None:
        cases = (
            ("bindings object", lambda contract: contract.update(bindings={})),
            (
                "unbound pointer number",
                lambda contract: contract["unbound_semantic_pointers"][0].update(
                    json_pointer=7
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label), self.copied_repo() as repo:
                map_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
                contract_map = load_json(map_path)
                mutate(contract_map["contracts"][0])
                dump_json(map_path, contract_map)
                with self.rebound_asset_hashes(repo):
                    self.assert_error(
                        self.checker.check_repository(repo),
                        "schema validation",
                    )

    def test_semantic_pointer_deletion_is_rejected_for_each_authored_contract(self) -> None:
        targets = (
            ("v8_actor_state_contracts", "/actor_record_schema/required_fields/0"),
            ("v8_multicircle_contracts", "/circle_record_schema/required_fields/0"),
            ("v8_simulation_forecast_contracts", "/event_record_schema/required_fields/0"),
            ("v8_actor_state_contracts", "/closed"),
            ("v8_multicircle_contracts", "/closed"),
            ("v8_simulation_forecast_contracts", "/closed"),
        )
        for contract_id, pointer in targets:
            with self.subTest(contract=contract_id, pointer=pointer), self.copied_repo() as repo:
                registry_path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
                map_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
                registry = load_json(registry_path)
                contract_map = load_json(map_path)
                contract = next(item for item in contract_map["contracts"] if item["contract_id"] == contract_id)
                removed = [item for item in contract["bindings"] if item["json_pointer"] == pointer]
                removed_unbound = [
                    item
                    for item in contract["unbound_semantic_pointers"]
                    if item["json_pointer"] == pointer
                ]
                self.assertNotEqual(bool(removed), bool(removed_unbound))
                contract["bindings"] = [item for item in contract["bindings"] if item["json_pointer"] != pointer]
                contract["unbound_semantic_pointers"] = [
                    item
                    for item in contract["unbound_semantic_pointers"]
                    if item["json_pointer"] != pointer
                ]
                contract["required_semantic_pointers"].remove(pointer)
                for concept in registry["concepts"]:
                    concept["contract_bindings"] = [
                        item for item in concept["contract_bindings"]
                        if not (item["contract_id"] == contract_id and item["json_pointer"] == pointer)
                    ]
                    concept["contract_ids"] = sorted({item["contract_id"] for item in concept["contract_bindings"]})
                contract["concept_ids"] = sorted({item["concept_id"] for item in contract["bindings"]})
                dump_json(registry_path, registry)
                dump_json(map_path, contract_map)
                with self.rebound_asset_hashes(repo):
                    self.assert_error(
                        self.checker.check_repository(repo),
                        "semantic coverage",
                    )

    def test_coordinated_id_replacement_and_self_reported_digest_are_rejected(self) -> None:
        with self.copied_repo() as repo:
            registry_path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
            contract_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
            route_path = repo / "skills/crossframe-promax/references/v8-route-map.json"
            registry = load_json(registry_path)
            contracts = load_json(contract_path)
            routes = load_json(route_path)
            old_id = "V8-CANON-C1"
            new_id = "V8-CANON-COORDINATED-REPLACEMENT"

            def replace_ids(node):
                if isinstance(node, dict):
                    return {key: replace_ids(value) for key, value in node.items()}
                if isinstance(node, list):
                    return [replace_ids(value) for value in node]
                return new_id if node == old_id else node

            registry = replace_ids(registry)
            contracts = replace_ids(contracts)
            routes = replace_ids(routes)
            ids = sorted(item["concept_id"] for item in registry["concepts"])
            registry["concept_inventory_sha256"] = hashlib.sha256(
                ("\n".join(ids) + "\n").encode("utf-8")
            ).hexdigest()
            dump_json(registry_path, registry)
            dump_json(contract_path, contracts)
            dump_json(route_path, routes)
            errors = self.checker.check_repository(repo)
        self.assert_error(errors, "canonical inventory")

    def test_coordinated_concept_deletion_across_all_three_assets_is_rejected(self) -> None:
        with self.copied_repo() as repo:
            registry_path = repo / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
            contract_path = repo / "skills/crossframe-promax/references/concept-contracts/v8-contract-map.json"
            route_path = repo / "skills/crossframe-promax/references/v8-route-map.json"
            registry = load_json(registry_path)
            contracts = load_json(contract_path)
            routes = load_json(route_path)
            victim = registry["concepts"].pop()["concept_id"]
            for concept in registry["concepts"]:
                concept["required_neighbor_ids"] = [x for x in concept["required_neighbor_ids"] if x != victim]
                concept["conflicts_disambiguation"] = [
                    x for x in concept["conflicts_disambiguation"] if x["concept_id"] != victim
                ]
                concept["deduction_interfaces"] = [
                    x for x in concept["deduction_interfaces"] if x["target_concept_id"] != victim
                ]
            for contract in contracts["contracts"]:
                contract["concept_ids"] = [x for x in contract["concept_ids"] if x != victim]
            for route in routes["routes"]:
                route["required_concept_ids"] = [x for x in route["required_concept_ids"] if x != victim]
                route["neighbor_closure_ids"] = [x for x in route["neighbor_closure_ids"] if x != victim]
            dump_json(registry_path, registry)
            dump_json(contract_path, contracts)
            dump_json(route_path, routes)
            errors = self.checker.check_repository(repo)
        self.assert_error(errors, "schema validation")


class _CopiedKnowledgeRepository:
    def __enter__(self) -> Path:
        self._temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self._temporary.name) / "repo"
        target = self.repo / "skills/crossframe-promax"
        shutil.copytree(SKILL, target)
        return self.repo

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._temporary.cleanup()


class _CheckerAssetHashOverride:
    def __init__(self, checker, repo: Path) -> None:
        self.checker = checker
        self.repo = repo

    def __enter__(self):
        self.original = {
            "REGISTRY_FILE_SHA256": self.checker.REGISTRY_FILE_SHA256,
            "CONTRACT_MAP_FILE_SHA256": self.checker.CONTRACT_MAP_FILE_SHA256,
            "ROUTE_MAP_FILE_SHA256": self.checker.ROUTE_MAP_FILE_SHA256,
            "SCHEMA_FILE_SHA256": dict(self.checker.SCHEMA_FILE_SHA256),
        }
        skill = self.repo / "skills/crossframe-promax"
        self.checker.REGISTRY_FILE_SHA256 = sha256_file(
            skill / "references/concept-registry/v8-concept-registry.json"
        )
        self.checker.CONTRACT_MAP_FILE_SHA256 = sha256_file(
            skill / "references/concept-contracts/v8-contract-map.json"
        )
        self.checker.ROUTE_MAP_FILE_SHA256 = sha256_file(
            skill / "references/v8-route-map.json"
        )
        self.checker.SCHEMA_FILE_SHA256 = {
            name: sha256_file(path)
            for name, path in {
                "source": skill / "schemas/v8-source-manifest.schema.json",
                "registry": skill / "schemas/v8-concept-registry.schema.json",
                "contracts": skill / "schemas/v8-contract-map.schema.json",
                "routes": skill / "schemas/v8-route-map.schema.json",
            }.items()
        }
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.checker.REGISTRY_FILE_SHA256 = self.original["REGISTRY_FILE_SHA256"]
        self.checker.CONTRACT_MAP_FILE_SHA256 = self.original["CONTRACT_MAP_FILE_SHA256"]
        self.checker.ROUTE_MAP_FILE_SHA256 = self.original["ROUTE_MAP_FILE_SHA256"]
        self.checker.SCHEMA_FILE_SHA256 = self.original["SCHEMA_FILE_SHA256"]


if __name__ == "__main__":
    unittest.main()
