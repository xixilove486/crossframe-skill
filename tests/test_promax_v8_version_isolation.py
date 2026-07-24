from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/crossframe-promax"
CHECKER_PATH = SKILL / "scripts/check_crossframe_promax_v8_knowledge.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(CHECKER_PATH.is_file(), "v8 knowledge checker not implemented")
class ProMaxV8VersionIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_module("promax_v8_isolation_checker", CHECKER_PATH)

    def assert_polluted(self, errors: list[str], fragment: str) -> None:
        self.assertTrue(any(fragment.lower() in item.lower() for item in errors), errors)

    def test_committed_skill_has_zero_version_pollution(self) -> None:
        self.assertEqual(self.checker.scan_version_pollution(SKILL), [])

    def test_hv_codes_and_v8_identifiers_are_not_false_positives(self) -> None:
        samples = (
            "HV01 结构域；HV02 边界与接口；HV10 资源与脆弱性；HV11 方向与规范条件",
            "V8-P0001 V8-T117 V8-CANON-HV01 v8.0",
            "第六部分、第七部分与第八部分是章节，不是旧版本。",
            "P0-P11 是路径序列；HV06 是人类变量卡；schema version 1.0.0。",
            "v7ish 只是包含相邻字符的普通 token，不是版本标记。",
            "GOV-01、M06、M07、S6、max_inference、maximum、Maxwell 都是合法标识。",
            "continuation lineage and inherited state describe runtime continuity only.",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertEqual(self.checker.pollution_errors_for_text(sample, "sample.md"), [])

    def test_explicit_pre_v8_markers_old_paths_and_lineage_are_rejected(self) -> None:
        cases = (
            ("来源 v7.0", "pre-v8"),
            ("framework-version: V6", "pre-v8"),
            ("复制自 v5/knowledge/contracts.json", "pre-v8"),
            ("knowledge.v7.json", "pre-v8"),
            ("contracts.v6/actor.json", "pre-v8"),
            ("framework.v5", "pre-v8"),
            ("contracts/inherited/actor.json", "inherited"),
            ("knowledge/lineage/v7-to-v8.json", "lineage"),
            ("work/v8/lineage/map.json", "lineage"),
            ("跨尺度结构解释框架_v6.0.docx", "pre-v8"),
        )
        for text, fragment in cases:
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "injected.md"), fragment
                )

    def test_explicit_non_v8_framework_versions_are_rejected(self) -> None:
        cases = (
            "来源 v9.0",
            "framework-version: V10",
            "knowledge.v9.json",
            "跨尺度框架_v9.0.docx",
            "来源 v8.1",
            "framework-version: v8.0.1",
            "framework version 7.0",
            "framework-version: 7",
            "knowledge version 7.0",
            "contracts version 5",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "injected.md"),
                    "non-v8",
                )

        allowed = (
            "来源 v8",
            "framework-version: V8.0",
            "knowledge.v8.json",
            "framework version 8.0",
            "schema version 1.0.0",
        )
        for text in allowed:
            with self.subTest(allowed=text):
                self.assertEqual(
                    self.checker.pollution_errors_for_text(text, "injected.md"),
                    [],
                )

    def test_unprefixed_numeric_framework_versions_are_context_checked(self) -> None:
        forbidden = (
            "采用 7.0 版本的框架",
            "采用 6.0 版框架知识",
            "旧版 6.0 的概念定义",
            "框架采用 7.0 版本",
            "知识来源版本为 5.0",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(
                        text, "references/protocol.md"
                    ),
                    "non-v8",
                )

        allowed = (
            "采用 8.0 版本的框架",
            "采用 8.0 版框架知识",
            "当前版 8.0 的概念定义",
            "framework version 8.0",
            "schema version 1.0.0",
            "Python 3.10",
        )
        for text in allowed:
            with self.subTest(allowed=text):
                self.assertEqual(
                    self.checker.pollution_errors_for_text(
                        text, "references/protocol.md"
                    ),
                    [],
                )

    def test_other_crossframe_skills_cannot_be_knowledge_sources(self) -> None:
        for text in (
            "知识来源：skills/crossframe-max/references/knowledge.md",
            "从 crossframe-suite 的知识库继承概念定义",
            "读取 crossframe-review 作为理论来源",
            "知识来源：skills/crossframe/references/knowledge.md",
            "读取 crossframe 作为理论来源",
            "知识来源：.claude/skills/crossframe/references/knowledge.md",
            "知识来源：.claude/skills/crossframe-promax/references/knowledge.md",
        ):
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "injected.md"),
                    "knowledge source",
                )

    def test_crossframe_base_and_mirror_paths_cannot_bypass_isolation(self) -> None:
        cases = (
            ("v8-only clean content", "skills/crossframe/references/knowledge.md"),
            ("v8-only clean content", ".claude/skills/crossframe/references/knowledge.md"),
            ("v8-only clean content", ".claude/skills/crossframe-max/references/knowledge.md"),
            ("v8-only clean content", ".claude/skills/crossframe-promax/references/knowledge.md"),
        )
        for text, path in cases:
            with self.subTest(path=path):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, path),
                    "knowledge source",
                )

        for text in (
            "CrossFrame ProMax is a standalone v8-only structural reasoning skill.",
            "CrossFrame ProMax 使用自身打包的 v8-only 知识资产。",
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    self.checker.pollution_errors_for_text(text, "design.md"),
                    [],
                )

    def test_max_is_allowed_only_in_explicit_routing_priority_language(self) -> None:
        allowed = (
            "Routing priority: when CrossFrame ProMax and CrossFrame Max are both named, ProMax wins.",
            "路由优先级：同时点名 ProMax 与 Max 时，ProMax 优先，禁止回退到 Max。",
            "PROMAX-PRIORITY-OVER-MAX PROMAX-NO-FALLBACK-TO-MAX",
        )
        for text in allowed:
            with self.subTest(text=text):
                self.assertEqual(self.checker.pollution_errors_for_text(text, "routing.md"), [])
        for text in allowed:
            with self.subTest(reference_surface=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(
                        text, "references/concept-registry/knowledge.md"
                    ),
                    "knowledge source",
                )
        forbidden = (
            "采用 Max 的概念定义补充 ProMax",
            "Max 是本知识注册表的来源",
            "max is the knowledge source",
            "mAx 是知识来源",
            "缺材料时读取 crossframe-max",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "knowledge.md"),
                    "knowledge source",
                )
        mixed = (
            "Routing priority: ProMax wins over Max; then use Max as the knowledge source.",
            "路由优先：ProMax 优先；同时采用 Max 的概念定义补充知识。",
        )
        for text in mixed:
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "routing.md"),
                    "knowledge source",
                )

        self.assert_polluted(
            self.checker.pollution_errors_for_text(
                allowed[0], "notes/route-knowledge.md"
            ),
            "knowledge source",
        )
        self.assertEqual(
            self.checker.pollution_errors_for_text(
                "PROMAX-PRIORITY-OVER-MAX PROMAX-NO-FALLBACK-TO-MAX",
                "schemas/promax-run-contract.schema.json",
            ),
            [],
        )
        self.assertEqual(
            self.checker.pollution_errors_for_text(
                '      "const": "crossframe-max"',
                "schemas/promax-run-contract.schema.json",
            ),
            [],
        )
        self.assert_polluted(
            self.checker.pollution_errors_for_text(
                '      "description": "crossframe-max is the knowledge source"',
                "schemas/promax-run-contract.schema.json",
            ),
            "knowledge source",
        )

    def test_max_skill_spelling_variants_cannot_bypass_isolation(self) -> None:
        variants = (
            "crossframe-max",
            "crossframe_max",
            "crossframe max",
            "crossframemax",
            "CrOsSfRaMe-MaX",
            "CROSSFRAME_MAX",
            "CrossFrame Max",
            "CrossFrameMax",
        )
        for variant in variants:
            priority = (
                f"Routing priority: CrossFrame ProMax wins when {variant} is also named; "
                "ProMax has no fallback."
            )
            with self.subTest(variant=variant, surface="control"):
                self.assertEqual(
                    self.checker.pollution_errors_for_text(priority, "routing.md"),
                    [],
                )
            with self.subTest(variant=variant, surface="knowledge"):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(
                        f"知识来源：{variant}",
                        "references/concept-registry/knowledge.md",
                    ),
                    "knowledge source",
                )
            with self.subTest(variant=variant, surface="priority-in-knowledge"):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(
                        priority,
                        "references/concept-registry/knowledge.md",
                    ),
                    "knowledge source",
                )

    def test_compact_sibling_aliases_are_rejected_without_lexical_false_positives(self) -> None:
        forbidden = (
            "CrossFrameSuite 是知识来源",
            "读取 CrossFrameReview 作为概念定义",
            "CrossFrameCritical",
            "CROSSFRAMESUITE",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "injected.md"),
                    "knowledge source",
                )

        allowed = (
            "CrossFrame ProMax 是当前独立技能",
            "CrossFrameProMax",
            "CrossFramePromaxRuntime",
            "CrossFrameProMax-v8",
            "crossframed response",
            "crossframework theory",
        )
        for text in allowed:
            with self.subTest(allowed=text):
                self.assertEqual(
                    self.checker.pollution_errors_for_text(text, "design.md"),
                    [],
                )

    def test_separator_json_path_and_nfkc_bypasses_are_rejected(self) -> None:
        cases = (
            (
                "知识来源：crossframe__max",
                "references/knowledge.md",
                "knowledge source",
            ),
            (
                "知识来源：crossframe---max",
                "references/knowledge.md",
                "knowledge source",
            ),
            (
                r'{"source":"crossframe\u002dmax","version":"v\u0037"}',
                "references/escaped.json",
                "knowledge source",
            ),
            (
                r'{"source":"crossframe\u002dmax","version":"v\u0037"}',
                "references/escaped.json",
                "pre-v8",
            ),
            (
                "v8-only clean content",
                "references/crossframe-max/knowledge.json",
                "knowledge source",
            ),
            (
                "知识来源：ＣｒｏｓｓＦｒａｍｅ Ｍａｘ",
                "references/fullwidth.md",
                "knowledge source",
            ),
            (
                "v8-only clean content",
                "ｒｅｆｅｒｅｎｃｅｓ/ＣｒｏｓｓＦｒａｍｅ＿Ｍａｘ/knowledge.json",
                "knowledge source",
            ),
        )
        for text, path, fragment in cases:
            with self.subTest(path=path, fragment=fragment):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, path),
                    fragment,
                )

        priority = (
            "Routing priority: CrossFrame ProMax wins when crossframe__max is also "
            "named; ProMax has no fallback."
        )
        self.assertEqual(
            self.checker.pollution_errors_for_text(priority, "routing.md"),
            [],
        )
        self.assertEqual(
            self.checker.pollution_errors_for_text(
                r"literal escape spelling crossframe\u002dmax and v\u0037",
                "notes.md",
            ),
            [],
        )

    def test_bounded_loader_and_identifier_normalization_bypasses_are_rejected(self) -> None:
        cases = (
            (
                r'source: "skills/crossframe\u002freferences/knowledge.md"',
                "references/encoded.yaml",
                "knowledge source",
            ),
            (
                r'source: "crossframe\x2dmax"',
                "references/encoded.yml",
                "knowledge source",
            ),
            (
                r'version: "v\u0037.0"',
                "references/encoded.yaml",
                "pre-v8",
            ),
            (
                r'source: "skills/\U00000063rossframe/references/knowledge.md"',
                "references/encoded.yaml",
                "knowledge source",
            ),
            (
                r'source: "crossframe-\U0000006dax"',
                "references/encoded.yml",
                "knowledge source",
            ),
            (
                r'version: "v\U00000037.0"',
                "references/encoded.yaml",
                "pre-v8",
            ),
            (
                "[x](skills/%63rossframe/references/knowledge.md)",
                "references/encoded.md",
                "knowledge source",
            ),
            (
                "skills/crossframe-%6dax/references/knowledge.md",
                "references/encoded.md",
                "knowledge source",
            ),
            (
                '<a href="skills/&#99;rossframe/references/knowledge.md">x</a>',
                "references/encoded.html",
                "knowledge source",
            ),
            (
                "crossframe-&#109;ax 是知识来源",
                "references/encoded.html",
                "knowledge source",
            ),
            (
                "skills/cross\u2060frame/references/knowledge.md",
                "references/encoded.md",
                "knowledge source",
            ),
        )
        for text, path, fragment in cases:
            with self.subTest(path=path, text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, path),
                    fragment,
                )

        clean_controls = (
            (
                r"literal crossframe\u002dmax outside a YAML quoted scalar",
                "notes.md",
            ),
            (
                r"source: 'crossframe\u002dmax'",
                "references/literal.yaml",
            ),
            (
                "[x](skills/%2563rossframe/references/knowledge.md)",
                "notes.md",
            ),
            (
                "&amp;#99;rossframe is a literal entity example",
                "notes.md",
            ),
            (
                "中文\u2060分隔符不构成 ASCII 标识符",
                "notes.md",
            ),
        )
        for text, path in clean_controls:
            with self.subTest(clean_path=path, clean_text=text):
                self.assertEqual(
                    self.checker.pollution_errors_for_text(text, path),
                    [],
                )

    def test_unprefixed_source_anchors_are_rejected(self) -> None:
        for text in ("source paragraph P0488", "table anchor T117", "锚点 P3863"):
            with self.subTest(text=text):
                self.assert_polluted(
                    self.checker.pollution_errors_for_text(text, "injected.json"),
                    "unprefixed",
                )

    def test_filesystem_scanner_reports_injected_pollution_but_skips_pycache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "crossframe-promax"
            shutil.copytree(SKILL, root)
            injected = root / "references/forbidden.md"
            injected.write_text("contracts/inherited and lineage from v7", encoding="utf-8")
            cache = root / "scripts/__pycache__/ignored.pyc"
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(b"v6 contracts/inherited lineage")
            errors = self.checker.scan_version_pollution(root)
        self.assert_polluted(errors, "forbidden.md")
        self.assertFalse(any("__pycache__" in item for item in errors), errors)

    def test_filesystem_scanner_cannot_be_bypassed_by_filename_or_text_extension(self) -> None:
        extensions = ("json", "yaml", "py", "txt", "rst", "toml", "")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "crossframe-promax"
            shutil.copytree(SKILL, root)
            for extension in extensions:
                path = root / (f"routing.{extension}" if extension else "routing")
                path.write_text("Max 是本知识注册表的来源", encoding="utf-8")
            errors = self.checker.scan_version_pollution(root)
        for extension in extensions:
            with self.subTest(extension=extension):
                self.assert_polluted(errors, f"routing.{extension}" if extension else "routing")

    def test_filesystem_scanner_rejects_polluted_path_segments(self) -> None:
        rejected = (
            "contracts/inherited/actor.json",
            "references/lineage/bridge.json",
            "references/concept-registry/lineage.json",
            "references/v7/knowledge.json",
            "references/knowledge.v7.json",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "crossframe-promax"
            root.mkdir()
            for relative in rejected:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("v8-only clean content", encoding="utf-8")
            allowed = root / "runtime/continuation-lineage.json"
            allowed.parent.mkdir(parents=True, exist_ok=True)
            allowed.write_text("runtime continuation only", encoding="utf-8")
            errors = self.checker.scan_version_pollution(root)
        for relative in rejected:
            with self.subTest(relative=relative):
                self.assert_polluted(errors, relative)
        self.assertFalse(any("continuation-lineage" in item for item in errors), errors)

    def test_nul_and_non_utf8_files_cannot_silently_bypass_scanning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "crossframe-promax"
            root.mkdir()
            (root / "nul.txt").write_bytes(
                b"\x00v7 knowledge source: CrossFrame Max"
            )
            (root / "opaque.txt").write_bytes(b"\xff\xfe\x80")
            errors = self.checker.scan_version_pollution(root)
        self.assert_polluted(errors, "nul.txt")
        self.assert_polluted(errors, "pre-v8")
        self.assert_polluted(errors, "knowledge source")
        self.assert_polluted(errors, "unscannable")

    def test_binary_assets_are_prohibited_in_the_v8_only_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "crossframe-promax"
            root.mkdir()
            (root / "clean.md").write_text(
                "v8-only canonical source snapshot",
                encoding="utf-8",
            )
            references = root / "references"
            references.mkdir()
            (references / ".v8-full-source.lock").write_bytes(b"\x00")
            (root / "innocent.pdf").write_bytes(
                b"knowledge source: crossframe-max v7"
            )
            errors = self.checker.scan_version_pollution(root)
        self.assert_polluted(errors, "binary asset prohibited")
        self.assert_polluted(errors, "innocent.pdf")
        self.assertFalse(any("clean.md" in item for item in errors), errors)
        self.assertFalse(any(".v8-full-source.lock" in item for item in errors), errors)

    def test_symbolic_links_are_rejected_before_target_content_is_trusted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "crossframe-promax"
            root.mkdir()
            target = Path(directory) / "outside-clean.txt"
            target.write_text("v8-only clean content", encoding="utf-8")
            link = root / "references-link.txt"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links unavailable on this host: {exc}")
            errors = self.checker.scan_version_pollution(root)
        self.assert_polluted(errors, "symbolic link")
        self.assert_polluted(errors, "references-link.txt")


if __name__ == "__main__":
    unittest.main()
