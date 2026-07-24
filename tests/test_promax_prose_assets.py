from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "crossframe-promax"
REFERENCES = SKILL_ROOT / "references"
TECHNIQUES = REFERENCES / "prose-techniques"
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from promax_runtime.prose import (  # noqa: E402
    PROSE_TECHNIQUE_IDS,
    PROSE_TECHNIQUE_ROUTES,
)

EXPECTED_TECHNIQUE_IDS = {
    "analogical-reasoning",
    "ancient-modern-global",
    "clouds-moon",
    "coincidence-structure",
    "direct-emotion",
    "double-bridge",
    "event-association",
    "feint-attack",
    "final-reveal",
    "fine-carving",
    "finishing-touch",
    "fixed-point-changing-scenes",
    "form-by-object",
    "guest-host-contrast",
    "hide-before-reveal",
    "language-momentum",
    "layered-argument",
    "less-is-more",
    "life-from-dead",
    "meaning-beyond-words",
    "motion-for-stillness",
    "moving-viewpoint",
    "multi-edge-extension",
    "narration-commentary",
    "object-reason",
    "one-stone-many-birds",
    "one-word-spine",
    "personified-object",
    "point-spirit",
    "point-surface",
    "positive-negative-contrast",
    "praise-blame-interlace",
    "raise-high-drop-heavy",
    "release-to-capture",
    "remove-foundation",
    "retreat-to-advance",
    "same-different",
    "scene-emotion",
    "small-water-waves",
    "sparse-outline",
    "split-wood-reasoning",
    "stars-moon",
    "stream-consciousness",
    "surprise-victory",
    "suspense",
    "symbolic-meaning",
    "thread-beads",
    "vertical-narration",
    "virtual-to-real",
    "winding-path",
}
GENRE_IDS = {
    "reply",
    "public-commentary",
    "concept-explanation",
    "organization-review",
    "case-analysis",
    "debate-refutation",
    "reading-synthesis",
    "trend-deduction",
    "neutral-analysis",
}
REQUIRED_SECTIONS = (
    "定义",
    "适用体裁",
    "解决问题",
    "操作步骤",
    "段落动作",
    "好句类型",
    "段落前后关系",
    "失败形态",
    "误用风险",
    "输出自检",
)
P8_BOUNDARY = "只影响表达，不改变 P8 锁定的事实、命题、证据、判断与授权"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_route_blocks(text: str) -> list[tuple[str, str, list[str], list[str]]]:
    blocks = re.split(r"(?m)^## 路由：", text)[1:]
    parsed: list[tuple[str, str, list[str], list[str]]] = []
    for block in blocks:
        lines = block.splitlines()
        route_id = lines[0].strip()

        def value(label: str) -> str:
            match = re.search(rf"(?m)^- {re.escape(label)}：(.+)$", block)
            if match is None:
                raise AssertionError(f"route {route_id!r} missing {label}")
            return match.group(1).strip()

        def ids(label: str) -> list[str]:
            raw = value(label)
            if raw == "无":
                return []
            return re.findall(r"`([a-z0-9-]+)`", raw)

        genre_match = re.fullmatch(r"`([a-z0-9-]+)`", value("genre_id"))
        if genre_match is None:
            raise AssertionError(f"route {route_id!r} has malformed genre_id")
        parsed.append(
            (
                route_id,
                genre_match.group(1),
                ids("core"),
                ids("auxiliary_candidates"),
            )
        )
    return parsed


class ProMaxProseAssetTests(unittest.TestCase):
    def test_library_has_exactly_the_fifty_required_independent_cards(self) -> None:
        cards = sorted(
            path for path in TECHNIQUES.glob("*.md") if path.name != "index.md"
        )
        self.assertEqual(EXPECTED_TECHNIQUE_IDS, {card.stem for card in cards})
        self.assertEqual(50, len(cards))

    def test_index_maps_every_technique_id_to_one_existing_relative_card_path(
        self,
    ) -> None:
        text = read(TECHNIQUES / "index.md")
        rows = re.findall(
            r"(?m)^\|\s*`([a-z0-9-]+)`\s*\|\s*`([^`]+\.md)`\s*\|$",
            text,
        )
        self.assertEqual(50, len(rows))
        self.assertEqual(50, len({technique_id for technique_id, _ in rows}))
        self.assertEqual(50, len({relative_path for _, relative_path in rows}))
        self.assertEqual(
            {
                technique_id: f"{technique_id}.md"
                for technique_id in EXPECTED_TECHNIQUE_IDS
            },
            dict(rows),
        )
        for technique_id, relative_path in rows:
            with self.subTest(technique_id=technique_id):
                path = Path(relative_path)
                self.assertFalse(path.is_absolute())
                self.assertEqual(path.name, relative_path)
                self.assertTrue((TECHNIQUES / path).is_file())

    def test_every_referenced_prose_asset_path_exists(self) -> None:
        referenced: set[str] = set()
        for source in (
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "protocols/promax-prose-protocol.md",
        ):
            referenced.update(
                re.findall(
                    r"`((?:protocols|references)/[^`]*(?:prose|house-voice)[^`]*\.md)`",
                    read(source),
                )
            )
        self.assertTrue(
            {
                "protocols/promax-prose-protocol.md",
                "references/promax-house-voice.md",
                "references/prose-routing-map.md",
                "references/prose-techniques/index.md",
            }
            <= referenced
        )
        for relative_path in sorted(referenced):
            with self.subTest(relative_path=relative_path):
                self.assertTrue((SKILL_ROOT / relative_path).is_file())

    def test_every_card_has_complete_actionable_contract_and_p8_boundary(self) -> None:
        for technique_id in sorted(EXPECTED_TECHNIQUE_IDS):
            with self.subTest(technique_id=technique_id):
                text = read(TECHNIQUES / f"{technique_id}.md")
                headings = set(re.findall(r"(?m)^## (.+)$", text))
                self.assertTrue(set(REQUIRED_SECTIONS).issubset(headings))
                self.assertIn(P8_BOUNDARY, text)
                self.assertGreaterEqual(len(text), 650)

    def test_cards_are_independently_authored_instead_of_one_repeated_shell(self) -> None:
        definitions: set[str] = set()
        paragraph_actions: set[str] = set()
        problems: set[str] = set()
        operation_cores: set[str] = set()
        misuse_risks: set[str] = set()
        for technique_id in sorted(EXPECTED_TECHNIQUE_IDS):
            text = read(TECHNIQUES / f"{technique_id}.md")
            definition = re.search(
                r"(?ms)^## 定义\s+(.+?)(?=^## )", text
            )
            paragraph_action = re.search(
                r"(?ms)^## 段落动作\s+(.+?)(?=^## )", text
            )
            self.assertIsNotNone(definition)
            self.assertIsNotNone(paragraph_action)
            definitions.add(definition.group(1).strip())
            paragraph_actions.add(paragraph_action.group(1).strip())
            for heading, destination in (
                ("解决问题", problems),
                ("操作步骤", operation_cores),
                ("误用风险", misuse_risks),
            ):
                section = re.search(
                    rf"(?ms)^## {heading}\s+(.+?)(?=^## )",
                    text,
                )
                self.assertIsNotNone(section)
                destination.add(section.group(1).strip())
        self.assertEqual(50, len(definitions))
        self.assertGreaterEqual(len(paragraph_actions), 45)
        self.assertEqual(50, len(problems))
        self.assertEqual(50, len(operation_cores))
        self.assertEqual(50, len(misuse_risks))

    def test_routing_uses_nine_genres_and_small_bounded_route_sets(self) -> None:
        text = read(REFERENCES / "prose-routing-map.md")
        routes = parse_route_blocks(text)
        self.assertEqual(9, len(routes))
        self.assertEqual(len(routes), len({route_id for route_id, *_ in routes}))
        self.assertEqual(GENRE_IDS, {genre for _, genre, _, _ in routes})
        self.assertIn("单次 P9 选择", text)
        self.assertIn("auxiliary 只能选 0–2 张", text)
        self.assertIn("core 与 auxiliary 合计不得超过 5 张", text)

        routed: set[str] = set()
        parsed_routes: dict[str, dict[str, object]] = {}
        for route_id, genre, core, candidates in routes:
            with self.subTest(route_id=route_id, genre=genre):
                self.assertEqual(3, len(core))
                self.assertEqual(len(core), len(set(core)))
                self.assertEqual(len(candidates), len(set(candidates)))
                self.assertFalse(set(core) & set(candidates))
                self.assertTrue(set(core + candidates) <= EXPECTED_TECHNIQUE_IDS)
                routed.update(core)
                routed.update(candidates)
                parsed_routes[genre] = {
                    "core": tuple(core),
                    "auxiliary": frozenset(candidates),
                }
        self.assertEqual(EXPECTED_TECHNIQUE_IDS, routed)
        self.assertEqual(EXPECTED_TECHNIQUE_IDS, set(PROSE_TECHNIQUE_IDS))
        self.assertEqual(parsed_routes, PROSE_TECHNIQUE_ROUTES)

    def test_mandatory_routes_never_require_p9_to_revise_p8(self) -> None:
        routed_core_ids = {
            technique_id
            for route in PROSE_TECHNIQUE_ROUTES.values()
            for technique_id in route["core"]
        }
        self.assertNotIn("retreat-to-advance", routed_core_ids)
        self.assertNotIn("remove-foundation", routed_core_ids)
        self.assertIn(
            "不得在 P9 新增撤回、缩小命题或改写判断强度",
            read(TECHNIQUES / "retreat-to-advance.md"),
        )
        self.assertIn(
            "不得在 P9 据此调整强度",
            read(TECHNIQUES / "remove-foundation.md"),
        )

    def test_output_plan_schema_freezes_the_same_fifty_card_inventory(self) -> None:
        schema = json.loads(
            read(SKILL_ROOT / "schemas/promax-output-plan.schema.json")
        )
        self.assertEqual(
            EXPECTED_TECHNIQUE_IDS,
            set(schema["$defs"]["techniqueId"]["enum"]),
        )

    def test_house_voice_defines_reader_facing_judgment_and_safety_boundaries(self) -> None:
        text = read(REFERENCES / "promax-house-voice.md")
        for required in (
            "现实入口",
            "第一段不用术语",
            "明确判断",
            "机制",
            "成本承担者",
            "最强反方",
            "撤回条件",
            "行动边界",
            "不自动迎合",
            "不自动反对",
            "模型套话",
            "审计泄漏",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertIn(P8_BOUNDARY, text)

    def test_house_voice_is_independent_from_host_model_flavor(self) -> None:
        text = read(REFERENCES / "promax-house-voice.md")
        for required in (
            "## 宿主模型风味独立性",
            "宿主默认",
            "先赞同",
            "先反对",
            "清单化",
            "客服式缓和",
            "反驳表演",
            "模型惯用节奏",
            "判断只服从 P8 锁",
            "表达只服从 ProMax house voice",
            "不能仅靠禁止模型套话",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_new_prose_assets_are_self_contained_and_version_clean(self) -> None:
        asset_paths = sorted(TECHNIQUES.glob("*.md")) + [
            REFERENCES / "prose-routing-map.md",
            REFERENCES / "promax-house-voice.md",
        ]
        forbidden_literals = (
            "crossframe-essay",
            "crossframe-max",
            "crossframe-suite",
            "crossframe-review",
            ".codex/skills",
            ".claude/skills",
        )
        for path in asset_paths:
            text = read(path)
            with self.subTest(path=path.name):
                self.assertIsNone(re.search(r"(?<![\w-])v5(?![\w-])", text, re.I))
                for literal in forbidden_literals:
                    self.assertNotIn(literal, text.lower())
                self.assertNotRegex(text, r"(?i)[a-z]:\\|/home/|/users/")


if __name__ == "__main__":
    unittest.main()
