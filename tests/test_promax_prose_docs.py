from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "crossframe-promax"


def read(relative: str) -> str:
    return (SKILL / relative).read_text(encoding="utf-8")


class ProMaxProseDocumentationTests(unittest.TestCase):
    def test_skill_loads_self_contained_prose_contract(self) -> None:
        text = read("SKILL.md")
        for required_path in (
            "protocols/promax-prose-protocol.md",
            "references/promax-house-voice.md",
            "references/prose-routing-map.md",
            "references/prose-techniques/index.md",
        ):
            self.assertIn(required_path, text)
        self.assertIn("六个角色", text)
        self.assertIn("prose_fidelity_auditor", text)
        self.assertIn("promax-prose-review.json", text)

    def test_essay_contract_is_reader_facing_not_audit_dump(self) -> None:
        text = read("templates/promax-essay-output.md")
        for forbidden in (
            "v8 概念逐项解释",
            "同一自然段必须逐字携带",
            "首选 OPTION-*",
            "逐字携带十九字段",
        ):
            self.assertNotIn(forbidden, text)
        for required in (
            "现实入口",
            "中心命题",
            "机制递进",
            "同维正反比较",
            "最强反方",
            "撤回条件",
            "行动边界",
            "余味结尾",
            "不设总字数上限",
            "先说现实关系",
        ):
            self.assertIn(required, text)

    def test_dossier_and_atlas_own_audit_completeness(self) -> None:
        dossier = read("templates/promax-dossier-output.md")
        atlas = read("templates/promax-concept-atlas-output.md")
        self.assertIn("读者投影", dossier)
        self.assertIn("写作技法", dossier)
        self.assertIn("全部 applied", atlas)
        self.assertIn("权威定义", atlas)

    def test_runtime_routes_reader_projection_and_prose_review(self) -> None:
        runtime = read("protocols/promax-runtime-protocol.md")
        routing = read("references/runtime-routing-map.md")
        repair = read("protocols/promax-repair-loop-protocol.md")
        for text in (runtime, routing):
            self.assertIn("reader_projection", text)
            self.assertIn("promax-prose-review.json", text)
            self.assertIn("prose_fidelity_auditor", text)
            self.assertIn("自动选择", text)
        self.assertIn("正文表达或声口失败", repair)
        self.assertIn("P10", repair)
        self.assertIn("体裁、读者节拍或技法映射失败", repair)
        self.assertIn("P9", repair)

    def test_manifest_contract_records_sixth_role_and_internal_review(self) -> None:
        text = read("templates/promax-artifact-manifest-output.md")
        self.assertIn("promax-prose-review.json", text)
        self.assertIn("六角色记录", text)
        self.assertIn("prose_fidelity_auditor", text)
        self.assertIn("不作为公开交付链接", text)


if __name__ == "__main__":
    unittest.main()
