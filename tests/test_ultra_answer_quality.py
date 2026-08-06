from __future__ import annotations

import importlib
from pathlib import Path
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
if str(RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPTS))


EXPECTED_DIMENSIONS = (
    "direct-answer",
    "evidence-boundary",
    "mechanism-competition",
    "recursive-expansion",
    "reversal-conditions",
    "action-comparison",
    "reader-independence",
)


def _runtime():
    return importlib.import_module("ultra_runtime.article")


def _quality_contract() -> dict[str, object]:
    anchors = {
        "direct-answer": [["当前判断", "就业"]],
        "evidence-boundary": [["证据边界", "尚无"]],
        "mechanism-competition": [["机制一", "机制二"]],
        "recursive-expansion": [["一阶", "二阶", "三阶"]],
        "reversal-conditions": [["反转条件", "如果"]],
        "action-comparison": [["全民基本收入", "公共资本", "劳动者共治"]],
        "reader-independence": [["结论", "读者"]],
    }
    return {
        "dimensions": [
            {
                "dimension_id": dimension,
                "required_anchor_groups": anchors[dimension],
                "minimum_span_characters": 24,
            }
            for dimension in EXPECTED_DIMENSIONS
        ],
        "simulated_values": ["30%"],
        "simulation_qualifiers": ["模拟", "情景", "假设", "压力测试"],
    }


def _substantive_article() -> str:
    return "\n\n".join(
        (
            "当前判断是，AI 会重组就业而非自动消灭全部就业，制度选择决定成本如何分配。",
            "证据边界必须写清：现有材料显示岗位任务变化，但尚无证据证明长期净就业必然下降。",
            "机制一是企业用自动化压低议价成本；机制二是新任务与新需求扩张，两者会竞争并混合。",
            "一阶是岗位替代，二阶是收入与需求反馈，三阶是所有权和谈判制度被重新塑造。",
            "反转条件是如果新岗位增速、工资份额和工时改善持续出现，就应下调危机判断。",
            "行动比较不能只列名：全民基本收入托底需求，公共资本分享收益，劳动者共治改变决策权。",
            "这份结论让普通读者仅凭正文即可理解判断、证据限制、政策差异和下一步选择。",
            "模拟情景中的30%只是压力测试参数，不是已经发生的现实观测。",
        )
    )


def test_repeated_markers_cannot_satisfy_answer_quality() -> None:
    runtime = _runtime()
    evaluate = getattr(runtime, "evaluate_answer_quality", None)
    assert callable(evaluate)
    hollow = "\n".join(EXPECTED_DIMENSIONS * 8)

    result = evaluate(hollow, _quality_contract())

    assert result["overall_status"] == "fail"
    assert "fail" in result["dimensions"].values()


def test_ai_employment_fixture_requires_substantive_comparison_and_boundaries() -> None:
    runtime = _runtime()
    evaluate = getattr(runtime, "evaluate_answer_quality", None)
    assert callable(evaluate)

    result = evaluate(_substantive_article(), _quality_contract())

    assert runtime.QUALITY_DIMENSIONS == EXPECTED_DIMENSIONS
    assert set(result["dimensions"]) == set(EXPECTED_DIMENSIONS)
    assert set(result["dimensions"].values()) == {"pass"}
    assert result["simulated_as_fact"] == "pass"
    assert result["overall_status"] == "pass"


def test_unqualified_simulated_number_fails_answer_quality() -> None:
    runtime = _runtime()
    evaluate = getattr(runtime, "evaluate_answer_quality", None)
    assert callable(evaluate)
    article = _substantive_article().replace(
        "模拟情景中的30%只是压力测试参数，不是已经发生的现实观测。",
        "现实已经证明就业会永久下降30%。",
    )

    result = evaluate(article, _quality_contract())

    assert result["simulated_as_fact"] == "fail"
    assert result["overall_status"] == "fail"
