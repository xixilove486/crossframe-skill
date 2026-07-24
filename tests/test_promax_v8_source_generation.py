from __future__ import annotations

from dataclasses import replace
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_XML = ROOT / "tests/fixtures/promax-v8-source/document.xml"
DOCUMENT_ORDER_XML = ROOT / "tests/fixtures/promax-v8-source/document-order.xml"
NESTED_TABLE_XML = ROOT / "tests/fixtures/promax-v8-source/nested-table.xml"
GENERATOR_PATH = (
    ROOT
    / "skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py"
)
REAL_SOURCE = Path(r"E:\世界模型\跨尺度多圈层结构推演框架_v8.0.docx")
EXPECTED_SECTION_START_IDS = (
    "V8-P0334",
    "V8-P0408",
    "V8-P0486",
    "V8-P0544",
    "V8-P0807",
    "V8-P0996",
    "V8-P1073",
    "V8-P2244",
    "V8-P2527",
    "V8-P2716",
    "V8-P2907",
    "V8-P3096",
    "V8-P3307",
    "V8-P3559",
    "V8-P3626",
    "V8-P3735",
)

if not GENERATOR_PATH.is_file():
    raise ModuleNotFoundError(
        "CrossFrame ProMax v8 source generator has not been implemented"
    )
spec = importlib.util.spec_from_file_location("promax_v8_source_generator", GENERATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load generator module: {GENERATOR_PATH}")
generator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = generator
spec.loader.exec_module(generator)


def write_fixture_docx(path: Path, xml_bytes: bytes | None = None) -> None:
    payload = FIXTURE_XML.read_bytes() if xml_bytes is None else xml_bytes
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", payload)


def fixture_root() -> ET.Element:
    return ET.fromstring(FIXTURE_XML.read_bytes())


def non_whitespace(text: str) -> int:
    return sum(not character.isspace() for character in text)


def valid_release_snapshot():
    paragraphs = [
        generator.V8Paragraph(f"V8-P{index:04d}", "", "x")
        for index in range(1, generator.EXPECTED_PARAGRAPHS + 1)
    ]
    heading_indexes = [
        int(paragraph_id.removeprefix("V8-P")) - 1
        for paragraph_id in EXPECTED_SECTION_START_IDS
    ]
    for heading_index, title in zip(
        heading_indexes, generator.CANONICAL_TITLES, strict=True
    ):
        paragraphs[heading_index] = replace(
            paragraphs[heading_index], style="1", text=title
        )

    for index, text in zip(range(2000, 2004), ("a", "b", "c", "d"), strict=True):
        paragraphs[index] = replace(paragraphs[index], text=text)

    current_non_ws = sum(non_whitespace(paragraph.text) for paragraph in paragraphs)
    padding = generator.EXPECTED_NON_WHITESPACE_CHARS - current_non_ws
    if padding < 0:
        raise AssertionError("synthetic snapshot unexpectedly exceeds release character count")
    paragraphs[-1] = replace(paragraphs[-1], text="x" * (padding + 1))
    paragraph_tuple = tuple(paragraphs)

    tables = [
        generator.V8Table(
            tid="V8-T001",
            paragraph_ids=("V8-P2001", "V8-P2002", "V8-P2003", "V8-P2004"),
            rows=(("a", "b"), ("c", "d")),
            cell_paragraph_ids=(
                (("V8-P2001",), ("V8-P2002",)),
                (("V8-P2003",), ("V8-P2004",)),
            ),
        )
    ]
    for table_index in range(2, generator.EXPECTED_TABLES + 1):
        paragraph_id = f"V8-P{2100 + table_index:04d}"
        tables.append(
            generator.V8Table(
                tid=f"V8-T{table_index:03d}",
                paragraph_ids=(paragraph_id,),
                rows=(("x",),),
                cell_paragraph_ids=(((paragraph_id,),),),
            )
        )
    table_tuple = tuple(tables)
    sections = generator.split_v8_sections(paragraph_tuple, table_tuple)
    return generator.V8Snapshot(
        source_sha256=generator.EXPECTED_SOURCE_SHA256,
        paragraphs=paragraph_tuple,
        tables=table_tuple,
        sections=sections,
        non_whitespace_chars=generator.EXPECTED_NON_WHITESPACE_CHARS,
    )


class V8XmlExtractionTests(unittest.TestCase):
    def test_read_document_xml_reads_the_ooxml_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "fixture.docx"
            write_fixture_docx(source)
            root = generator.read_document_xml(source)
        self.assertTrue(root.tag.endswith("}document"))

    def test_read_document_xml_bytes_reads_the_same_ooxml_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "fixture.docx"
            write_fixture_docx(source)
            root = generator.read_document_xml_bytes(source.read_bytes())
        self.assertTrue(root.tag.endswith("}document"))

    def test_extract_paragraphs_walks_table_cells_in_document_order(self) -> None:
        paragraphs = generator.extract_v8_paragraphs(fixture_root())
        self.assertEqual(
            [paragraph.text for paragraph in paragraphs[:10]],
            [
                "封面",
                "第一部分　导读",
                "第一部分　导读",
                "导读正文",
                "A1",
                "A2",
                "B1",
                "B2",
                "第二部分　边界与方法",
                "第二部分正文",
            ],
        )
        self.assertEqual(
            [paragraph.pid for paragraph in paragraphs],
            [f"V8-P{index:04d}" for index in range(1, len(paragraphs) + 1)],
        )

    def test_extract_paragraph_text_preserves_ooxml_tabs_and_breaks(self) -> None:
        root = ET.fromstring(DOCUMENT_ORDER_XML.read_bytes())
        paragraphs = generator.extract_v8_paragraphs(root)
        self.assertEqual([paragraph.text for paragraph in paragraphs], ["左\t中\n下\n底"])
        self.assertEqual(non_whitespace(paragraphs[0].text), 4)

    def test_production_paragraph_index_drives_table_bindings(self) -> None:
        document_root = fixture_root()
        paragraphs = generator.extract_v8_paragraphs(document_root)
        paragraph_index = generator.index_v8_paragraph_elements(document_root)
        tables = generator.extract_v8_tables(document_root, paragraph_index)
        self.assertEqual(
            tuple(paragraph_index.values()),
            tuple(paragraph.pid for paragraph in paragraphs),
        )
        self.assertEqual(tables[0].paragraph_ids, tuple(f"V8-P{i:04d}" for i in range(5, 9)))

    def test_extract_tables_preserves_rows_cells_and_source_bindings(self) -> None:
        document_root = fixture_root()
        tables = generator.extract_v8_tables(
            document_root, generator.index_v8_paragraph_elements(document_root)
        )
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].tid, "V8-T001")
        self.assertEqual(tables[0].paragraph_ids, tuple(f"V8-P{i:04d}" for i in range(5, 9)))
        self.assertEqual(tables[0].rows, (("A1", "A2"), ("B1", "B2")))
        self.assertEqual(
            tables[0].cell_paragraph_ids,
            (
                (("V8-P0005",), ("V8-P0006",)),
                (("V8-P0007",), ("V8-P0008",)),
            ),
        )

    def test_extract_tables_requires_the_explicit_paragraph_element_index(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(generator.extract_v8_tables).parameters),
            ("document_root", "pid_by_element"),
        )

    def test_nested_tables_use_depth_first_descendant_cell_bindings(self) -> None:
        document_root = ET.fromstring(NESTED_TABLE_XML.read_bytes())
        paragraphs = generator.extract_v8_paragraphs(document_root)
        tables = generator.extract_v8_tables(
            document_root, generator.index_v8_paragraph_elements(document_root)
        )
        self.assertEqual(
            tuple(paragraph.text for paragraph in paragraphs),
            ("outer-before", "inner", "outer-after"),
        )
        self.assertEqual(len(tables), 2)
        self.assertEqual(
            tables[0].rows,
            (("outer-before\ninner\nouter-after",),),
        )
        self.assertEqual(
            tables[0].cell_paragraph_ids,
            ((("V8-P0001", "V8-P0002", "V8-P0003"),),),
        )
        self.assertEqual(tables[0].paragraph_ids, ("V8-P0001", "V8-P0002", "V8-P0003"))
        self.assertEqual(tables[1].rows, (("inner",),))
        self.assertEqual(tables[1].cell_paragraph_ids, ((("V8-P0002",),),))

    def test_split_sections_ignores_same_named_toc1_and_uses_exact_style1(self) -> None:
        document_root = fixture_root()
        paragraphs = generator.extract_v8_paragraphs(document_root)
        tables = generator.extract_v8_tables(
            document_root, generator.index_v8_paragraph_elements(document_root)
        )
        sections = generator.split_v8_sections(paragraphs, tables)
        self.assertEqual(len(sections), 16)
        self.assertEqual(sections[0].start_heading_id, "V8-P0003")
        self.assertEqual(sections[0].paragraph_ids, tuple(f"V8-P{i:04d}" for i in range(3, 9)))
        self.assertEqual(sections[0].table_ids, ("V8-T001",))
        self.assertEqual(sections[1].start_heading_id, "V8-P0009")

    def test_split_sections_rejects_missing_duplicate_and_reordered_titles(self) -> None:
        document_root = fixture_root()
        paragraphs = list(generator.extract_v8_paragraphs(document_root))
        tables = generator.extract_v8_tables(
            document_root, generator.index_v8_paragraph_elements(document_root)
        )
        title_positions = [
            index
            for index, paragraph in enumerate(paragraphs)
            if paragraph.style == "1" and paragraph.text in generator.CANONICAL_TITLES
        ]

        cases = {}
        missing = paragraphs.copy()
        missing[title_positions[-1]] = replace(missing[title_positions[-1]], style="")
        cases["missing"] = missing
        duplicate = paragraphs.copy()
        duplicate[title_positions[-1]] = replace(
            duplicate[title_positions[-1]], text=generator.CANONICAL_TITLES[0]
        )
        cases["duplicate"] = duplicate
        reordered = paragraphs.copy()
        first, second = title_positions[:2]
        reordered[first] = replace(reordered[first], text=generator.CANONICAL_TITLES[1])
        reordered[second] = replace(reordered[second], text=generator.CANONICAL_TITLES[0])
        cases["order"] = reordered
        ascii_space = paragraphs.copy()
        ascii_space[first] = replace(
            ascii_space[first], text=generator.CANONICAL_TITLES[0].replace("　", " ")
        )
        cases["exact"] = ascii_space

        for label, candidate in cases.items():
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, label):
                generator.split_v8_sections(tuple(candidate), tables)


class V8SnapshotValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = valid_release_snapshot()

    def test_release_constants_and_valid_snapshot_are_exact(self) -> None:
        self.assertEqual(
            generator.EXPECTED_SOURCE_SHA256,
            "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c",
        )
        self.assertEqual(generator.EXPECTED_PARAGRAPHS, 3863)
        self.assertEqual(generator.EXPECTED_NON_WHITESPACE_CHARS, 155721)
        self.assertEqual(generator.EXPECTED_TABLES, 117)
        self.assertEqual(generator.EXPECTED_SECTIONS, 16)
        self.assertEqual(generator.EXPECTED_SECTION_START_IDS, EXPECTED_SECTION_START_IDS)
        self.assertEqual(generator.EXPECTED_ENVELOPE_RANGE, ("V8-P0001", "V8-P0333"))
        self.assertEqual(
            tuple(section.start_heading_id for section in self.snapshot.sections),
            EXPECTED_SECTION_START_IDS,
        )
        self.assertEqual(self.snapshot.sections[-1].paragraph_ids[-1], "V8-P3863")
        self.assertEqual(generator.validate_v8_snapshot(self.snapshot), [])

    def test_validate_snapshot_rejects_wrong_sha(self) -> None:
        errors = generator.validate_v8_snapshot(
            replace(self.snapshot, source_sha256="0" * 64)
        )
        self.assertTrue(any("SHA256" in error for error in errors), errors)

    def test_validate_snapshot_rejects_deleted_and_duplicate_paragraph_anchors(self) -> None:
        for label, replacement_id in (
            ("deleted", "V8-P9999"),
            ("duplicate", self.snapshot.paragraphs[0].pid),
        ):
            paragraphs = list(self.snapshot.paragraphs)
            paragraphs[1] = replace(paragraphs[1], pid=replacement_id)
            candidate = replace(self.snapshot, paragraphs=tuple(paragraphs))
            with self.subTest(label=label):
                errors = generator.validate_v8_snapshot(candidate)
                self.assertTrue(any("anchor" in error for error in errors), errors)

    def test_validate_snapshot_rejects_first_heading_at_p0001(self) -> None:
        paragraphs = list(self.snapshot.paragraphs)
        first_heading_index = int(EXPECTED_SECTION_START_IDS[0][4:]) - 1
        paragraphs[0], paragraphs[first_heading_index] = (
            replace(
                paragraphs[0],
                style=paragraphs[first_heading_index].style,
                text=paragraphs[first_heading_index].text,
            ),
            replace(
                paragraphs[first_heading_index],
                style=self.snapshot.paragraphs[0].style,
                text=self.snapshot.paragraphs[0].text,
            ),
        )
        paragraph_tuple = tuple(paragraphs)
        sections = generator.split_v8_sections(paragraph_tuple, self.snapshot.tables)
        candidate = replace(
            self.snapshot,
            paragraphs=paragraph_tuple,
            sections=sections,
        )
        errors = generator.validate_v8_snapshot(candidate)
        self.assertTrue(any("section start anchor" in error for error in errors), errors)
        self.assertTrue(any("source envelope" in error for error in errors), errors)

    def test_validate_snapshot_rejects_any_shifted_section_start(self) -> None:
        paragraphs = list(self.snapshot.paragraphs)
        second_heading_index = int(EXPECTED_SECTION_START_IDS[1][4:]) - 1
        paragraphs[second_heading_index], paragraphs[second_heading_index + 1] = (
            replace(
                paragraphs[second_heading_index],
                style=paragraphs[second_heading_index + 1].style,
                text=paragraphs[second_heading_index + 1].text,
            ),
            replace(
                paragraphs[second_heading_index + 1],
                style=self.snapshot.paragraphs[second_heading_index].style,
                text=self.snapshot.paragraphs[second_heading_index].text,
            ),
        )
        paragraph_tuple = tuple(paragraphs)
        sections = generator.split_v8_sections(paragraph_tuple, self.snapshot.tables)
        candidate = replace(
            self.snapshot,
            paragraphs=paragraph_tuple,
            sections=sections,
        )
        errors = generator.validate_v8_snapshot(candidate)
        self.assertTrue(any("section start anchor" in error for error in errors), errors)


class V8GeneratedTreeValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = valid_release_snapshot()

    def render(self, root: Path) -> Path:
        stage = root / "v8-full-source"
        generator.render_v8_source_tree(self.snapshot, stage)
        self.assertEqual(generator.validate_generated_v8_tree(stage, self.snapshot), [])
        return stage

    def test_source_files_embed_canonical_paragraph_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = self.render(Path(directory))
            content = (stage / "00-source-envelope.md").read_text(encoding="utf-8")
        canonical = content.split("## Canonical Structure\n\n```json\n", 1)[1]
        payload = json.loads(canonical.split("\n```", 1)[0])
        self.assertEqual(payload[0], {"pid": "V8-P0001", "style": "", "text": "x"})
        self.assertEqual(payload[-1]["pid"], "V8-P0333")

    def test_validator_does_not_invoke_the_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = self.render(Path(directory))
            with mock.patch.object(
                generator,
                "render_v8_source_tree",
                side_effect=AssertionError("validator called renderer"),
            ):
                errors = generator.validate_generated_v8_tree(stage, self.snapshot)
        self.assertEqual(errors, [])

    def test_systematic_source_renderer_corruption_is_rejected(self) -> None:
        real_source_file_lines = generator._source_file_lines

        def corrupt_source_file_lines(*args, **kwargs):
            lines = real_source_file_lines(*args, **kwargs)
            return [
                "y" if line == "x" else line.replace('"text": "x"', '"text": "y"')
                for line in lines
            ]

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            generator,
            "_source_file_lines",
            side_effect=corrupt_source_file_lines,
        ):
            stage = Path(directory) / "v8-full-source"
            generator.render_v8_source_tree(self.snapshot, stage)
            errors = generator.validate_generated_v8_tree(stage, self.snapshot)
        self.assertTrue(any("canonical paragraph" in error for error in errors), errors)

    def test_systematic_table_renderer_corruption_is_rejected(self) -> None:
        real_render_table = generator._render_table

        def corrupt_render_table(table, source_sha256, output_path):
            real_render_table(table, source_sha256, output_path)
            content = output_path.read_text(encoding="utf-8")
            output_path.write_text(
                content.replace("x", "y"),
                encoding="utf-8",
                newline="\n",
            )

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            generator,
            "_render_table",
            side_effect=corrupt_render_table,
        ):
            stage = Path(directory) / "v8-full-source"
            generator.render_v8_source_tree(self.snapshot, stage)
            errors = generator.validate_generated_v8_tree(stage, self.snapshot)
        self.assertTrue(any("canonical table" in error for error in errors), errors)

    def test_prose_and_canonical_json_disagreement_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = self.render(Path(directory))
            source_file = stage / "16-governance.md"
            original = source_file.read_text(encoding="utf-8")
            marker = "<!-- source_paragraph:V8-P3736 style= -->"
            changed = original.replace(f"{marker}\nx\n", f"{marker}\ny\n", 1)
            self.assertNotEqual(changed, original)
            source_file.write_text(changed, encoding="utf-8", newline="\n")
            errors = generator.validate_generated_v8_tree(stage, self.snapshot)
        self.assertTrue(any("prose/JSON" in error for error in errors), errors)

    def test_changed_character_with_same_count_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = self.render(Path(directory))
            source_file = stage / "16-governance.md"
            original = source_file.read_text(encoding="utf-8")
            changed = original.replace("\nx\n\n", "\ny\n\n", 1)
            self.assertNotEqual(changed, original)
            source_file.write_text(changed, encoding="utf-8", newline="\n")
            errors = generator.validate_generated_v8_tree(stage, self.snapshot)
        self.assertTrue(any("content mismatch" in error for error in errors), errors)

    def test_deleted_and_duplicate_generated_anchors_are_rejected(self) -> None:
        marker = "<!-- source_paragraph:V8-P3736 style= -->"
        for label, replacement in (("deleted", ""), ("duplicate", f"{marker}\n{marker}")):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                stage = self.render(Path(directory))
                source_file = stage / "16-governance.md"
                original = source_file.read_text(encoding="utf-8")
                self.assertIn(marker, original)
                source_file.write_text(
                    original.replace(marker, replacement, 1),
                    encoding="utf-8",
                    newline="\n",
                )
                errors = generator.validate_generated_v8_tree(stage, self.snapshot)
                self.assertTrue(any("content mismatch" in error for error in errors), errors)

    def test_table_cell_mutation_and_row_exchange_are_rejected(self) -> None:
        mutations = (
            ("cell", "| a | b |", "| z | b |"),
            ("rows", "| a | b |\n| c | d |", "| c | d |\n| a | b |"),
        )
        for label, old, new in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                stage = self.render(Path(directory))
                table_file = stage / "tables/V8-T001.md"
                original = table_file.read_text(encoding="utf-8")
                self.assertIn(old, original)
                table_file.write_text(
                    original.replace(old, new, 1),
                    encoding="utf-8",
                    newline="\n",
                )
                errors = generator.validate_generated_v8_tree(stage, self.snapshot)
                self.assertTrue(any("content mismatch" in error for error in errors), errors)


class V8GenerationSafetyTests(unittest.TestCase):
    def test_real_source_sha_matches_frozen_constant_when_source_is_available(self) -> None:
        if not REAL_SOURCE.is_file():
            self.skipTest(f"real v8 source is unavailable: {REAL_SOURCE}")
        self.assertEqual(generator.sha256_file(REAL_SOURCE), generator.EXPECTED_SOURCE_SHA256)

    def test_prevalidation_failure_preserves_existing_live_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            live = repo / "skills/crossframe-promax/references/v8-full-source"
            live.mkdir(parents=True)
            sentinel = live / "sentinel.txt"
            sentinel.write_text("keep-me", encoding="utf-8")
            source = root / "fixture.docx"
            write_fixture_docx(source)
            fixture_sha = generator.sha256_file(source)
            with mock.patch.object(generator, "EXPECTED_SOURCE_SHA256", fixture_sha):
                with self.assertRaisesRegex(ValueError, "paragraph count"):
                    generator.generate(repo, source)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep-me")
            self.assertEqual(
                list(live.parent.glob(f".{live.name}.stage-*")),
                [],
            )

    def test_wrong_sha_fails_before_touching_live_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            live = repo / "skills/crossframe-promax/references/v8-full-source"
            live.mkdir(parents=True)
            sentinel = live / "sentinel.txt"
            sentinel.write_text("keep-me", encoding="utf-8")
            source = root / "fixture.docx"
            write_fixture_docx(source)
            with self.assertRaisesRegex(ValueError, "SHA256"):
                generator.generate(repo, source)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep-me")

    def test_atomic_replace_restores_live_tree_and_cleans_stage_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            live = parent / "v8-full-source"
            stage = parent / ".v8-full-source.stage-test"
            live.mkdir()
            stage.mkdir()
            (live / "sentinel.txt").write_text("old", encoding="utf-8")
            (stage / "new.txt").write_text("new", encoding="utf-8")
            real_replace = os.replace
            calls = 0

            def fail_install(source: os.PathLike[str], target: os.PathLike[str]) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected install failure")
                real_replace(source, target)

            with mock.patch.object(generator.os, "replace", side_effect=fail_install):
                with self.assertRaisesRegex(OSError, "injected install failure"):
                    generator.atomic_replace_tree(stage, live)
            self.assertEqual((live / "sentinel.txt").read_text(encoding="utf-8"), "old")
            self.assertFalse(stage.exists())
            self.assertEqual(list(parent.glob(".v8-full-source.backup-*")), [])

    def test_atomic_replace_first_move_failure_never_deletes_live_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            live = parent / "v8-full-source"
            stage = parent / ".v8-full-source.stage-test"
            live.mkdir()
            stage.mkdir()
            sentinel = live / "sentinel.txt"
            sentinel.write_text("old", encoding="utf-8")
            (stage / "new.txt").write_text("new", encoding="utf-8")

            with mock.patch.object(
                generator.os,
                "replace",
                side_effect=OSError("injected first move failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected first move failure"):
                    generator.atomic_replace_tree(stage, live)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "old")
            self.assertFalse(stage.exists())
            self.assertEqual(list(parent.glob(".v8-full-source.backup-*")), [])

    def test_atomic_replace_rejects_the_same_resolved_stage_and_live_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            live = Path(directory) / "v8-full-source"
            live.mkdir()
            sentinel = live / "sentinel.txt"
            sentinel.write_text("old", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "different directories"):
                generator.atomic_replace_tree(live, live)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "old")

    def test_preexisting_generation_lock_fails_without_touching_live_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            live = repo / "skills/crossframe-promax/references/v8-full-source"
            live.mkdir(parents=True)
            sentinel = live / "sentinel.txt"
            sentinel.write_text("keep-me", encoding="utf-8")
            lock = live.parent / ".v8-full-source.lock"
            generation_lock = generator._acquire_generation_lock(lock)
            source = root / "fixture.docx"
            write_fixture_docx(source)
            fixture_sha = generator.sha256_file(source)
            try:
                with mock.patch.object(
                    generator, "EXPECTED_SOURCE_SHA256", fixture_sha
                ), mock.patch.object(
                    generator,
                    "validate_v8_snapshot",
                    return_value=[],
                ):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "generation lock exists",
                    ):
                        generator.generate(repo, source)
            finally:
                generator._release_generation_lock(generation_lock)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep-me")
            self.assertTrue(lock.is_file())
            self.assertEqual(list(live.parent.glob(".v8-full-source.stage-*")), [])

    def test_competing_generation_fails_while_first_generation_holds_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            source = root / "fixture.docx"
            write_fixture_docx(source)
            fixture_sha = generator.sha256_file(source)
            live = repo / "skills/crossframe-promax/references/v8-full-source"
            lock = live.parent / ".v8-full-source.lock"
            real_render = generator.render_v8_source_tree
            contender_attempted = False
            contender_failed = False

            def render_with_contender(snapshot, output_dir):
                nonlocal contender_attempted, contender_failed
                if contender_attempted:
                    real_render(snapshot, output_dir)
                    return
                contender_attempted = True
                self.assertTrue(lock.is_file())
                with self.assertRaisesRegex(RuntimeError, "generation lock exists"):
                    generator.generate(repo, source)
                contender_failed = True
                real_render(snapshot, output_dir)

            with mock.patch.object(
                generator, "EXPECTED_SOURCE_SHA256", fixture_sha
            ), mock.patch.object(
                generator, "validate_v8_snapshot", return_value=[]
            ), mock.patch.object(
                generator,
                "render_v8_source_tree",
                side_effect=render_with_contender,
            ):
                result = generator.generate(repo, source)
            self.assertTrue(contender_failed)
            self.assertEqual(result, live)
            self.assertTrue((live / "00-index.md").is_file())
            released_lock = generator._acquire_generation_lock(lock)
            generator._release_generation_lock(released_lock)

    def test_generate_reads_source_bytes_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            source = root / "fixture.docx"
            write_fixture_docx(source)
            fixture_sha = generator.sha256_file(source)
            real_read_bytes = Path.read_bytes
            source_reads = 0

            def counted_read_bytes(path):
                nonlocal source_reads
                if Path(path) == source:
                    source_reads += 1
                    if source_reads > 1:
                        return b"replacement bytes are not a docx"
                return real_read_bytes(path)

            with mock.patch.object(
                generator, "EXPECTED_SOURCE_SHA256", fixture_sha
            ), mock.patch.object(
                generator, "validate_v8_snapshot", return_value=[]
            ), mock.patch.object(
                Path,
                "read_bytes",
                autospec=True,
                side_effect=counted_read_bytes,
            ):
                generator.generate(repo, source)
            self.assertEqual(source_reads, 1)


if __name__ == "__main__":
    unittest.main()
