from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests" / "evals" / "ultra-vs-promax"
SCENARIOS_PATH = EVAL_ROOT / "scenarios.json"
PAIRING_PATH = EVAL_ROOT / "pairing-manifest.json"

CATEGORY_ORDER = (
    "public",
    "organization",
    "business-tech",
    "personal",
    "history",
    "closed-material",
)

EXPECTED_CASES = (
    (
        "P01",
        "public",
        "某市计划把公共服务资格初筛交给统一 AI 系统。当前最可能改善什么、伤害什么，三阶会走向哪里？",
        "jurisdiction, low-visibility positions",
    ),
    (
        "P02",
        "public",
        "平台把“自愿认证”改成默认认证但允许退出。这是否仍是自愿，最可能如何演化？",
        "authorization, exit cost",
    ),
    (
        "P03",
        "public",
        "所有媒体都报道同一政策成功，所以独立证据已经很多。这个结论对吗？",
        "shared-source pollution",
    ),
    (
        "P04",
        "public",
        "危机舆情两天转向、组织季度调整、法规一年后生效。现在该怎么判断？",
        "asynchronous clocks",
    ),
    (
        "O01",
        "organization",
        "一名员工公开离职，公司短期声誉回升。请推演一阶、二阶和三阶。",
        "order-2 reversal, lock-in",
    ),
    (
        "O02",
        "organization",
        "项目延期，管理层认为原因只是执行力不足。当前最可能机制是什么？",
        "false premise, rival mechanism",
    ),
    (
        "O03",
        "organization",
        "某领导在一次冲突中强硬，因此人格一定专断。这个判断成立吗？",
        "actor-role/personality separation",
    ),
    (
        "O04",
        "organization",
        "重组让同一人同时属于产品线、地区线与专业委员会。责任如何判断？",
        "multi-parent nesting",
    ),
    (
        "B01",
        "business-tech",
        "企业引入生成式 AI 后单项效率提升。整体产能是否必然提升？",
        "local gain vs system bottleneck",
    ),
    (
        "B02",
        "business-tech",
        "新协议技术更优但生态采用缓慢。最可能的三阶路径是什么？",
        "network/institution clocks",
    ),
    (
        "B03",
        "business-tech",
        "竞争者降价，我们是否应立即跟进？",
        "action set, no-action comparison",
    ),
    (
        "B04",
        "business-tech",
        "数据泄露尚未证实影响用户，但内部日志异常。现在最合理判断和行动是什么？",
        "sparse evidence, responsibility",
    ),
    (
        "L01",
        "personal",
        "我想换工作，但只有收入、照护责任和行业机会三类有限信息。请明确建议。",
        "low-confidence hard judgment",
    ),
    (
        "L02",
        "personal",
        "伴侣一次失约是否证明关系不值得继续？",
        "event vs stable trait",
    ),
    (
        "L03",
        "personal",
        "搬家对职业有利、对照护不利、对伴侣中性。怎样排序？",
        "cross-circle distribution",
    ),
    (
        "L04",
        "personal",
        "家庭照护中“大家都同意”但无法退出者没有表达。授权成立吗？",
        "low-power authorization",
    ),
    (
        "H01",
        "history",
        "只使用冻结到改革发生前的材料，判断改革最可能成功还是失败。",
        "historical time box",
    ),
    (
        "H02",
        "history",
        "如果关键中介机构不存在，原事件最可能怎样变化？",
        "counterfactual and channel",
    ),
    (
        "H03",
        "history",
        "三份史料实际都转述同一档案，能否算三份独立支持？",
        "lineage deduplication",
    ),
    (
        "H04",
        "history",
        "一项临时制度为何可能在第三阶永久化？",
        "institutional lock-in",
    ),
    (
        "C01",
        "closed-material",
        "两份备忘录互相矛盾；只用材料内证据给出当前最可能解释。",
        "closed evidence court",
    ),
    (
        "C02",
        "closed-material",
        "对象同时被成员、合同和资源会计三种关系包含，请建立非树结构。",
        "multi-basis containment",
    ),
    (
        "C03",
        "closed-material",
        "外部事件与目标共享环境，但材料没有作用通道。目标状态能否更新？",
        "no-channel no-update",
    ),
    (
        "C04",
        "closed-material",
        "“这个方案更好”没有比较对象和评价标准。请判断该命题。",
        "proposition non-decidability",
    ),
)

DECISIVE_CASE_IDS = {
    "P04",
    "O01",
    "O04",
    "B02",
    "L03",
    "H04",
    "C02",
    "C03",
}

REQUIRED_ADVERSARIAL_TARGETS = {
    "false-user-premise",
    "sparse-evidence-ranking",
    "multi-parent-nesting",
    "no-channel-no-update",
    "asynchronous-clocks",
    "order-two-reversal",
    "order-three-lock-in",
    "simulation-identity",
    "value-authorization-separation",
    "sensitive-outbound",
}

SCENARIO_FIELDS = {
    "id",
    "category",
    "question",
    "decisive_pressure",
    "v82_decisive",
    "adversarial_targets",
    "execution_readiness",
    "case_dir",
    "prompt_path",
    "evidence_cutoff_path",
    "materials_dir",
    "expected_pressure_path",
    "privacy_policy_path",
}


def load_json(path: Path) -> object:
    assert path.is_file(), f"missing deterministic Task 16 asset: {path.as_posix()}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_twenty_four_cases_are_frozen_exactly_and_evenly() -> None:
    raw = load_json(SCENARIOS_PATH)
    assert isinstance(raw, list)
    assert len(raw) == 24
    assert [
        (
            case["id"],
            case["category"],
            case["question"],
            case["decisive_pressure"],
        )
        for case in raw
    ] == list(EXPECTED_CASES)
    assert all(set(case) == SCENARIO_FIELDS for case in raw)
    assert Counter(case["category"] for case in raw) == {
        category: 4 for category in CATEGORY_ORDER
    }
    assert len({case["id"] for case in raw}) == 24


def test_exactly_eight_cases_are_declared_v82_decisive() -> None:
    cases = load_json(SCENARIOS_PATH)
    assert isinstance(cases, list)
    assert {
        case["id"] for case in cases if case["v82_decisive"] is True
    } == DECISIVE_CASE_IDS
    assert all(type(case["v82_decisive"]) is bool for case in cases)


def test_case_directories_bind_prompts_cutoffs_materials_pressure_and_privacy() -> None:
    cases = load_json(SCENARIOS_PATH)
    assert isinstance(cases, list)
    for case in cases:
        case_id = case["id"]
        expected_dir = f"tests/evals/ultra-vs-promax/cases/{case_id}"
        assert case["case_dir"] == expected_dir
        assert case["prompt_path"] == f"{expected_dir}/prompt.md"
        assert case["evidence_cutoff_path"] == (
            f"{expected_dir}/evidence-cutoff.json"
        )
        assert case["materials_dir"] == f"{expected_dir}/materials"
        assert case["expected_pressure_path"] == (
            f"{expected_dir}/expected-pressure.json"
        )
        assert case["privacy_policy_path"] == (
            f"{expected_dir}/privacy-policy.json"
        )
        assert (ROOT / case["prompt_path"]).read_bytes() == (
            case["question"] + "\n"
        ).encode("utf-8")

        cutoff = load_json(ROOT / case["evidence_cutoff_path"])
        assert isinstance(cutoff, dict)
        assert cutoff["schema_id"] == "crossframe.ultra.benchmark-evidence-cutoff"
        assert cutoff["schema_version"] == 1
        assert cutoff["case_id"] == case_id
        assert cutoff["benchmark_cutoff"] == "2026-08-02T00:00:00Z"
        assert cutoff["evidence_state"] == "awaiting-frozen-bundle"
        if case["category"] == "history":
            assert cutoff["temporal_rule"] == "strictly-before-target-event"
        else:
            assert cutoff["temporal_rule"] == "not-after-benchmark-cutoff"

        materials = load_json(ROOT / case["materials_dir"] / "manifest.json")
        assert isinstance(materials, dict)
        assert materials["case_id"] == case_id
        assert materials["bundle_status"] == "pending"
        assert materials["source_files"] == []
        assert materials["source_count"] == 0
        expected_retrieval = (
            "prohibited"
            if case["category"] == "closed-material"
            else "frozen-bundle-only"
        )
        assert materials["retrieval_mode"] == expected_retrieval
        assert materials["outcome_leakage_review"] == "pending"
        assert materials["privacy_review"] == "pending"
        assert materials["license_review"] == "pending"

        pressure = load_json(ROOT / case["expected_pressure_path"])
        assert isinstance(pressure, dict)
        assert pressure["case_id"] == case_id
        assert pressure["decisive_pressure"] == case["decisive_pressure"]
        assert pressure["v82_decisive"] is case["v82_decisive"]
        assert pressure["adversarial_targets"] == case["adversarial_targets"]
        assert pressure["visibility"] == {"product": False, "grader": False}
        forbidden_keys = {
            "expected_winner",
            "winner",
            "score",
            "model_output",
            "grade",
        }
        assert forbidden_keys.isdisjoint(pressure)

        privacy = load_json(ROOT / case["privacy_policy_path"])
        assert isinstance(privacy, dict)
        assert privacy["case_id"] == case_id
        assert privacy["live_retrieval_allowed"] is False
        assert privacy["private_source_text_outbound_allowed"] is False
        assert case["expected_pressure_path"] in privacy["forbidden_visible_paths"]
        assert case["privacy_policy_path"] in privacy["product_visible_paths"]


def test_adversarial_targets_cover_the_frozen_red_failures_without_outcome_leakage() -> None:
    cases = load_json(SCENARIOS_PATH)
    assert isinstance(cases, list)
    observed = {
        target
        for case in cases
        for target in case["adversarial_targets"]
    }
    assert REQUIRED_ADVERSARIAL_TARGETS.issubset(observed)
    for case in cases:
        assert case["execution_readiness"] == "awaiting-evidence-bundle"
        assert case["adversarial_targets"]
        assert len(case["adversarial_targets"]) == len(
            set(case["adversarial_targets"])
        )


def test_pairing_contract_is_failure_closed_and_never_falls_back() -> None:
    manifest = load_json(PAIRING_PATH)
    assert isinstance(manifest, dict)
    assert manifest["status"] == "scaffold"
    assert manifest["fallback_allowed"] is False
    assert manifest["tool_profiles"]["frozen-offline"]["network"] is False
    assert manifest["tool_profiles"]["frozen-offline"]["retrieval"] is False
    for pair in manifest["pairs"]:
        assert pair["status"] == "pending"
        assert pair["products"]["promax"]["runtime_name"] == (
            "crossframe-promax"
        )
        assert pair["products"]["ultra"]["runtime_name"] == (
            "crossframe-ultra"
        )
        assert pair["products"]["promax"]["fallback_allowed"] is False
        assert pair["products"]["ultra"]["fallback_allowed"] is False
