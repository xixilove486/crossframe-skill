from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import fields, replace
from hashlib import sha256
from io import BytesIO
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import get_type_hints
from unittest import mock
import warnings
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile
import xml.etree.ElementTree as ET

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests/fixtures/ultra-v82-source"
DOCUMENT_XML = FIXTURE_ROOT / "document.xml"
NESTED_TABLE_XML = FIXTURE_ROOT / "nested-table.xml"
DOCUMENT_ORDER_XML = FIXTURE_ROOT / "document-order.xml"
GENERATOR_PATH = (
    ROOT / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py"
)
ROOT_WRAPPER = ROOT / "scripts/generate_crossframe_ultra_v82_source.py"
REAL_SOURCE = Path(r"E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"

EXPECTED_DIVISIONS = (
    ("01-guide", "第一部分　导读", 350, 423, (2, 3)),
    ("02-boundary-method", "第二部分　边界与方法", 424, 522, (4, 5)),
    ("03-universal-grammar", "第三部分　通用结构语法", 523, 584, ()),
    ("04-root-assumptions", "第四部分　根假设与推论", 585, 862, tuple(range(6, 12))),
    (
        "05-scale-circle-transformation",
        "第五部分　跨尺度与跨圈层变换",
        863,
        1082,
        tuple(range(12, 17)),
    ),
    ("06-operation-evolution", "第六部分　运转与演化", 1083, 1159, (17,)),
    (
        "07-human-structured-world",
        "第七部分　人类结构化世界",
        1160,
        1267,
        (18, 19),
    ),
    (
        "08-human-state-prototypes",
        "第八部分　人类状态原型",
        1268,
        1550,
        tuple(range(20, 30)),
    ),
    (
        "09-actor-state-personality",
        "第九部分　行动者状态与人格假设",
        1551,
        1739,
        tuple(range(30, 36)),
    ),
    (
        "10-multicircle-joint-state",
        "第十部分　多圈层对象与联合状态",
        1740,
        1930,
        tuple(range(36, 42)),
    ),
    (
        "11-event-dynamic-inference",
        "第十一部分　事件驱动的动态推演",
        1931,
        2131,
        tuple(range(42, 48)),
    ),
    (
        "12-conditional-forecast-choice",
        "第十二部分　条件前瞻与有限选择",
        2132,
        2348,
        tuple(range(48, 56)),
    ),
    (
        "13-interfaces-tools",
        "第十三部分　接口与工具",
        2349,
        2600,
        tuple(range(56, 64)),
    ),
    ("14-normative-selection", "第十四部分　规范选择", 2601, 2667, ()),
    ("15-intervention-applications", "第十五部分　干涉与应用", 2668, 2776, ()),
    ("16-governance", "第十六部分　治理", 2777, 2905, ()),
    (
        "17-appendix-a-human-variable-cards",
        "附录A　人类变量接口卡册",
        2906,
        4477,
        tuple(range(64, 120)),
    ),
    (
        "18-appendix-b-numbering-terms",
        "附录B　编号体系与术语总表",
        4478,
        4572,
        (120,),
    ),
    (
        "19-appendix-c-revisions",
        "附录C　版本修订记录",
        4573,
        4586,
        (121,),
    ),
    (
        "20-appendix-d-common-kernel-mapping",
        "附录D　双文本共同内核与映射",
        4587,
        4631,
        (122,),
    ),
)

if not GENERATOR_PATH.is_file():
    raise ModuleNotFoundError(
        "CrossFrame Ultra v8.2 source generator has not been implemented: "
        f"{GENERATOR_PATH}"
    )
spec = importlib.util.spec_from_file_location("ultra_v82_source_generator", GENERATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load generator module: {GENERATOR_PATH}")
generator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = generator
spec.loader.exec_module(generator)


def paragraph_text(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        if node.tag == f"{W}t":
            parts.append(node.text or "")
        elif node.tag == f"{W}tab":
            parts.append("\t")
        elif node.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
    return "".join(parts)


def ordinal_by_element(root: ET.Element) -> dict[int, int]:
    elements = [
        element
        for element in root.iter(f"{W}p")
        if paragraph_text(element).strip()
    ]
    return {id(element): ordinal for ordinal, element in enumerate(elements, start=1)}


def fixture_root(path: Path = DOCUMENT_XML) -> ET.Element:
    return ET.fromstring(path.read_bytes())


def docx_bytes(
    document_xml: bytes,
    *,
    comment: bytes,
    compression: int = ZIP_DEFLATED,
) -> bytes:
    stream = BytesIO()
    with ZipFile(stream, "w", compression=compression) as archive:
        archive.comment = comment
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("docProps/core.xml", b"<metadata/>" + comment)
    return stream.getvalue()


def zip_bytes(entries: Sequence[tuple[str, bytes]]) -> bytes:
    stream = BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            for name, payload in entries:
                archive.writestr(name, payload)
    return stream.getvalue()


def mark_first_zip_member_encrypted(source_bytes: bytes) -> bytes:
    payload = bytearray(source_bytes)
    local = payload.find(b"PK\x03\x04")
    central = payload.find(b"PK\x01\x02")
    assert local >= 0 and central >= 0
    for offset in (local + 6, central + 8):
        flags = int.from_bytes(payload[offset : offset + 2], "little") | 0x1
        payload[offset : offset + 2] = flags.to_bytes(2, "little")
    return bytes(payload)


def make_directory_reparse(link: Path, target: Path) -> None:
    if os.name == "nt":
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"cannot create junction {link} -> {target}: "
                f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
    else:
        link.symlink_to(target, target_is_directory=True)


def remove_directory_reparse(link: Path) -> None:
    if os.path.lexists(link):
        os.rmdir(link)


def write_docx(path: Path, document_xml: bytes = DOCUMENT_XML.read_bytes()) -> None:
    path.write_bytes(docx_bytes(document_xml, comment=b"fixture"))


def snapshot_from_source_bytes(source_bytes: bytes):
    root = generator.read_document_xml_bytes(source_bytes)
    paragraphs = generator.extract_v82_paragraphs(root)
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    divisions = generator.split_v82_divisions(paragraphs, tables)
    semantic = generator.semantic_snapshot_bytes(paragraphs, tables)
    return generator.V82Snapshot(
        raw_sha256=sha256(source_bytes).hexdigest(),
        semantic_sha256=sha256(semantic).hexdigest(),
        paragraphs=paragraphs,
        tables=tables,
        divisions=divisions,
        non_whitespace_chars=sum(
            not character.isspace()
            for paragraph in paragraphs
            for character in paragraph.text
        ),
    )


def refresh_tree_hash(source_tree: Path) -> None:
    (source_tree / "source-tree.sha256").write_text(
        generator.compute_v82_tree_sha256(source_tree) + "\n",
        encoding="ascii",
        newline="\n",
    )


@pytest.fixture(scope="session")
def real_source_bytes() -> bytes:
    if not REAL_SOURCE.is_file():
        pytest.skip(f"external v8.2 source is unavailable: {REAL_SOURCE}")
    return REAL_SOURCE.read_bytes()


@pytest.fixture(scope="session")
def real_snapshot(real_source_bytes: bytes):
    return snapshot_from_source_bytes(real_source_bytes)


def test_frozen_release_constants_are_exact() -> None:
    assert generator.SOURCE_DOCX == REAL_SOURCE
    assert generator.RAW_SHA256 == "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
    assert generator.SEMANTIC_NORMALIZATION_VERSION == 1
    assert generator.SEMANTIC_SHA256 == "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
    assert generator.EXPECTED_PARAGRAPHS == 4631
    assert generator.EXPECTED_NON_WHITESPACE_CHARS == 165690
    assert generator.EXPECTED_TABLES == 122
    assert generator.EXPECTED_DIVISIONS == 20


def test_public_dataclasses_are_frozen_slotted_and_have_exact_fields() -> None:
    expected = {
        "V82Paragraph": ("ordinal", "anchor", "style", "text"),
        "V82Table": (
            "ordinal",
            "anchor",
            "paragraph_ordinals",
            "rows",
            "cell_paragraph_ordinals",
        ),
        "V82Division": (
            "slug",
            "title",
            "start_ordinal",
            "end_ordinal",
            "table_ordinals",
        ),
        "V82Snapshot": (
            "raw_sha256",
            "semantic_sha256",
            "paragraphs",
            "tables",
            "divisions",
            "non_whitespace_chars",
        ),
    }
    for class_name, field_names in expected.items():
        cls = getattr(generator, class_name)
        assert tuple(field.name for field in fields(cls)) == field_names
        assert cls.__dataclass_params__.frozen is True
        assert tuple(cls.__slots__) == field_names


def test_public_function_signatures_are_exact() -> None:
    expected_parameters = {
        "read_document_xml_bytes": ("source_bytes",),
        "extract_v82_paragraphs": ("root",),
        "extract_v82_tables": ("root", "ordinal_by_element"),
        "split_v82_divisions": ("paragraphs", "tables"),
        "semantic_snapshot_bytes": ("paragraphs", "tables"),
        "validate_v82_snapshot": ("snapshot",),
        "render_v82_source_tree": ("snapshot", "stage_dir"),
    }
    for function_name, parameter_names in expected_parameters.items():
        function = getattr(generator, function_name)
        assert tuple(inspect.signature(function).parameters) == parameter_names

    hints = get_type_hints(generator.extract_v82_tables)
    assert hints["root"] is ET.Element
    assert hints["ordinal_by_element"] == Mapping[int, int]
    assert hints["return"] == tuple[generator.V82Table, ...]
    assert get_type_hints(generator.split_v82_divisions)["paragraphs"] == Sequence[
        generator.V82Paragraph
    ]


def test_repacked_docx_has_stable_semantic_hash_despite_different_raw_bytes() -> None:
    xml_bytes = DOCUMENT_XML.read_bytes()
    first = docx_bytes(xml_bytes, comment=b"first", compression=ZIP_DEFLATED)
    second = docx_bytes(xml_bytes, comment=b"second", compression=ZIP_STORED)
    assert sha256(first).hexdigest() != sha256(second).hexdigest()

    first_root = generator.read_document_xml_bytes(first)
    second_root = generator.read_document_xml_bytes(second)
    first_paragraphs = generator.extract_v82_paragraphs(first_root)
    second_paragraphs = generator.extract_v82_paragraphs(second_root)
    first_tables = generator.extract_v82_tables(first_root, ordinal_by_element(first_root))
    second_tables = generator.extract_v82_tables(second_root, ordinal_by_element(second_root))

    first_semantic = generator.semantic_snapshot_bytes(first_paragraphs, first_tables)
    second_semantic = generator.semantic_snapshot_bytes(second_paragraphs, second_tables)
    assert first_semantic == second_semantic
    assert sha256(first_semantic).hexdigest() == sha256(second_semantic).hexdigest()


def test_source_security_limits_are_frozen_and_fit_the_real_docx(
    real_source_bytes: bytes,
) -> None:
    assert generator.MAX_SOURCE_DOCX_BYTES == 8 * 1024 * 1024
    assert generator.MAX_DOCUMENT_XML_BYTES == 16 * 1024 * 1024
    assert generator.MAX_DOCUMENT_XML_COMPRESSION_RATIO == 100
    assert generator.MAX_ZIP_MEMBERS == 512
    assert len(real_source_bytes) < generator.MAX_SOURCE_DOCX_BYTES
    with ZipFile(BytesIO(real_source_bytes)) as archive:
        document = [
            info for info in archive.infolist() if info.filename == "word/document.xml"
        ]
    assert len(document) == 1
    assert document[0].file_size < generator.MAX_DOCUMENT_XML_BYTES
    assert (
        document[0].file_size / document[0].compress_size
        < generator.MAX_DOCUMENT_XML_COMPRESSION_RATIO
    )


def test_low_level_reader_rejects_oversized_source_bytes() -> None:
    with pytest.raises(ValueError, match="source archive size"):
        generator.read_document_xml_bytes(
            b"x" * (generator.MAX_SOURCE_DOCX_BYTES + 1)
        )


def test_raw_mismatch_uses_single_bounded_read_without_read_bytes_or_opening_zip(
    tmp_path: Path,
) -> None:
    source = tmp_path / "wrong.docx"
    source.write_bytes(b"not-the-frozen-source")
    with mock.patch.object(
        Path,
        "read_bytes",
        side_effect=AssertionError("unbounded read_bytes called"),
    ), mock.patch.object(
        generator,
        "ZipFile",
        side_effect=AssertionError("ZIP opened before raw hash matched"),
    ):
        with pytest.raises(ValueError, match="raw SHA256 mismatch"):
            generator.generate(tmp_path / "repo", source)


def test_generate_hashes_and_parses_the_same_single_source_read(
    tmp_path: Path,
    real_source_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.docx"
    replacement = tmp_path / "replacement.docx"
    source.write_bytes(real_source_bytes)
    replacement_bytes = docx_bytes(DOCUMENT_XML.read_bytes(), comment=b"replacement")
    replacement.write_bytes(replacement_bytes)
    real_path_open = Path.open
    source_open_count = 0

    class ReplaceSourceOnClose:
        def __init__(self, handle) -> None:
            self._handle = handle
            self._closed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> bool:
            self.close()
            return False

        def close(self) -> None:
            if self._closed:
                return
            self._closed = True
            self._handle.close()
            os.replace(replacement, source)

        def __getattr__(self, name: str):
            return getattr(self._handle, name)

    def open_and_replace_after_first_read(
        path: Path,
        mode: str = "r",
        *args,
        **kwargs,
    ):
        nonlocal source_open_count
        handle = real_path_open(path, mode, *args, **kwargs)
        if Path(path) == source and mode == "rb":
            source_open_count += 1
            if source_open_count == 1:
                return ReplaceSourceOnClose(handle)
        return handle

    class SnapshotProbe(Exception):
        pass

    parsed_payloads: list[bytes] = []

    def capture_snapshot_payload(payload: bytes):
        parsed_payloads.append(payload)
        raise SnapshotProbe

    monkeypatch.setattr(Path, "open", open_and_replace_after_first_read)
    monkeypatch.setattr(generator, "build_v82_snapshot", capture_snapshot_payload)

    with pytest.raises(SnapshotProbe):
        generator.generate(tmp_path / "repo", source)

    assert source_open_count == 1
    assert parsed_payloads == [real_source_bytes]
    assert sha256(parsed_payloads[0]).hexdigest() == generator.RAW_SHA256


def test_oversized_source_path_is_rejected_before_opening_file(tmp_path: Path) -> None:
    source = tmp_path / "oversized.docx"
    with source.open("wb") as handle:
        handle.truncate(8 * 1024 * 1024 + 1)
    with mock.patch.object(
        Path,
        "open",
        side_effect=AssertionError("oversized source was opened"),
    ):
        with pytest.raises(ValueError, match="source file size"):
            generator.generate(tmp_path / "repo", source)


def test_bounded_read_rejects_a_source_that_grows_past_the_size_limit(
    tmp_path: Path,
) -> None:
    source = tmp_path / "grew-after-stat.docx"
    with source.open("wb") as handle:
        handle.truncate(generator.MAX_SOURCE_DOCX_BYTES + 1)
    with pytest.raises(ValueError, match="source file size.*read"):
        generator._read_bounded_source_file(source)


@pytest.mark.parametrize(
    ("payload", "diagnostic"),
    (
        (b"not-a-zip", "invalid DOCX ZIP"),
        (zip_bytes((("other.xml", b"<x/>"),)), "exactly one word/document.xml"),
        (
            zip_bytes(
                (
                    ("word/document.xml", DOCUMENT_XML.read_bytes()),
                    ("word/document.xml", DOCUMENT_XML.read_bytes()),
                )
            ),
            "exactly one word/document.xml",
        ),
        (
            mark_first_zip_member_encrypted(
                zip_bytes((("word/document.xml", DOCUMENT_XML.read_bytes()),))
            ),
            "encrypted",
        ),
    ),
    ids=("bad-zip", "missing-document", "duplicate-document", "encrypted-document"),
)
def test_low_level_reader_rejects_invalid_document_members(
    payload: bytes,
    diagnostic: str,
) -> None:
    with pytest.raises(ValueError, match=diagnostic):
        generator.read_document_xml_bytes(payload)


def test_low_level_reader_rejects_oversized_document_xml_member() -> None:
    payload = zip_bytes(
        (("word/document.xml", b"x" * (16 * 1024 * 1024 + 1)),)
    )
    with pytest.raises(ValueError, match="uncompressed size"):
        generator.read_document_xml_bytes(payload)


def test_low_level_reader_rejects_extreme_document_xml_compression_ratio() -> None:
    payload = zip_bytes((("word/document.xml", b"x" * (1024 * 1024)),))
    with pytest.raises(ValueError, match="compression ratio"):
        generator.read_document_xml_bytes(payload)


def test_low_level_reader_rejects_doctype_and_entity_declarations() -> None:
    malicious_xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<!DOCTYPE w:document [<!ENTITY payload "expanded">]>\n'
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/'
        b'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
        b'&payload;</w:t></w:r></w:p></w:body></w:document>'
    )
    payload = zip_bytes((("word/document.xml", malicious_xml),))
    with pytest.raises(ValueError, match="DOCTYPE|ENTITY"):
        generator.read_document_xml_bytes(payload)


@pytest.mark.parametrize(
    ("codec", "xml_encoding"),
    (("utf-16", "UTF-16"), ("utf-32", "UTF-32")),
)
def test_low_level_reader_rejects_unicode_encoded_doctype_and_entity(
    codec: str,
    xml_encoding: str,
) -> None:
    malicious_text = (
        f'<?xml version="1.0" encoding="{xml_encoding}"?>\n'
        '<!DOCTYPE w:document [<!ENTITY payload "expanded">]>\n'
        f'<w:document xmlns:w="{W_NS}"><w:body><w:p><w:r><w:t>'
        '&payload;</w:t></w:r></w:p></w:body></w:document>'
    )
    payload = zip_bytes(
        (("word/document.xml", malicious_text.encode(codec)),)
    )

    with pytest.raises(ValueError, match="UTF-8|DOCTYPE|ENTITY|encoding"):
        generator.read_document_xml_bytes(payload)


def test_semantic_normalization_is_exact_canonical_json_with_one_lf() -> None:
    root = fixture_root(DOCUMENT_ORDER_XML)
    paragraphs = generator.extract_v82_paragraphs(root)
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    payload = {
        "normalization_version": 1,
        "paragraphs": [
            {
                "ordinal": paragraph.ordinal,
                "style": paragraph.style,
                "text": paragraph.text,
            }
            for paragraph in paragraphs
        ],
        "tables": [
            {
                "ordinal": table.ordinal,
                "paragraph_ordinals": list(table.paragraph_ordinals),
                "rows": [list(row) for row in table.rows],
                "cell_paragraph_ordinals": [
                    [list(cell) for cell in row]
                    for row in table.cell_paragraph_ordinals
                ],
            }
            for table in tables
        ],
    }
    expected = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    actual = generator.semantic_snapshot_bytes(paragraphs, tables)
    assert actual == expected
    assert actual.endswith(b"\n")
    assert not actual.endswith(b"\n\n")


def test_text_and_record_count_mutations_change_semantic_hash() -> None:
    root = fixture_root(DOCUMENT_ORDER_XML)
    paragraphs = generator.extract_v82_paragraphs(root)
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    baseline = sha256(generator.semantic_snapshot_bytes(paragraphs, tables)).hexdigest()

    changed_text = (replace(paragraphs[0], text=paragraphs[0].text + "变"), *paragraphs[1:])
    fewer_paragraphs = paragraphs[:-1]
    changed_rows = (
        replace(tables[0], rows=(("changed", "cell-two"),)),
        *tables[1:],
    )
    candidates = (
        generator.semantic_snapshot_bytes(changed_text, tables),
        generator.semantic_snapshot_bytes(fewer_paragraphs, tables),
        generator.semantic_snapshot_bytes(paragraphs, changed_rows),
    )
    assert all(sha256(candidate).hexdigest() != baseline for candidate in candidates)


def test_body_and_cell_paragraphs_follow_depth_first_document_order() -> None:
    root = fixture_root(DOCUMENT_ORDER_XML)
    paragraphs = generator.extract_v82_paragraphs(root)
    assert tuple(paragraph.text for paragraph in paragraphs) == (
        "左\t中\n下\n底",
        "cell-one",
        "cell-two",
        "tail",
    )
    assert tuple(paragraph.ordinal for paragraph in paragraphs) == (1, 2, 3, 4)
    assert tuple(paragraph.anchor for paragraph in paragraphs) == (
        "V82-P0001",
        "V82-P0002",
        "V82-P0003",
        "V82-P0004",
    )


def test_table_bindings_and_rows_are_exact_and_stable() -> None:
    root = fixture_root(DOCUMENT_XML)
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    assert tables == (
        generator.V82Table(
            ordinal=1,
            anchor="V82-T001",
            paragraph_ordinals=(5, 6, 7, 8),
            rows=(("A1", "A2"), ("B1", "B2")),
            cell_paragraph_ordinals=(((5,), (6,)), ((7,), (8,))),
        ),
    )


def test_nested_tables_do_not_duplicate_or_omit_global_paragraphs() -> None:
    root = fixture_root(NESTED_TABLE_XML)
    paragraphs = generator.extract_v82_paragraphs(root)
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    assert tuple(paragraph.text for paragraph in paragraphs) == (
        "document-before",
        "outer-before",
        "inner",
        "outer-after",
        "document-after",
    )
    assert tuple(paragraph.ordinal for paragraph in paragraphs) == (1, 2, 3, 4, 5)
    assert len({paragraph.anchor for paragraph in paragraphs}) == 5
    assert tables[0].paragraph_ordinals == (2, 3, 4)
    assert tables[0].rows == (("outer-before\ninner\nouter-after",),)
    assert tables[0].cell_paragraph_ordinals == (((2, 3, 4),),)
    assert tables[1].paragraph_ordinals == (3,)
    assert tables[1].rows == (("inner",),)
    assert tables[1].cell_paragraph_ordinals == (((3,),),)


def test_only_parttitle_identifies_top_level_divisions_and_toc1_is_ignored() -> None:
    root = fixture_root(DOCUMENT_XML)
    paragraphs = generator.extract_v82_paragraphs(root)
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    divisions = generator.split_v82_divisions(paragraphs, tables)
    assert len(divisions) == 20
    assert divisions[0] == generator.V82Division(
        slug="01-guide",
        title="第一部分　导读",
        start_ordinal=3,
        end_ordinal=8,
        table_ordinals=(1,),
    )
    assert paragraphs[1].style == "TOC1"
    assert paragraphs[2].style == "PartTitle"


@pytest.mark.parametrize("case", ("missing", "duplicate", "reordered"))
def test_split_divisions_rejects_invalid_top_level_titles(case: str) -> None:
    root = fixture_root(DOCUMENT_XML)
    paragraphs = list(generator.extract_v82_paragraphs(root))
    tables = generator.extract_v82_tables(root, ordinal_by_element(root))
    title_indexes = [
        index for index, paragraph in enumerate(paragraphs) if paragraph.style == "PartTitle"
    ]
    if case == "missing":
        index = title_indexes[0]
        paragraphs[index] = replace(paragraphs[index], style="BodyText")
    elif case == "duplicate":
        index = title_indexes[1]
        paragraphs[index] = replace(paragraphs[index], text=paragraphs[title_indexes[0]].text)
    else:
        first, second = title_indexes[:2]
        paragraphs[first], paragraphs[second] = (
            replace(paragraphs[first], text=paragraphs[second].text),
            replace(paragraphs[second], text=paragraphs[first].text),
        )
    with pytest.raises(ValueError, match=case):
        generator.split_v82_divisions(tuple(paragraphs), tables)


def test_real_docx_full_snapshot_matches_all_frozen_counts_hashes_and_ranges(
    real_source_bytes: bytes,
    real_snapshot,
) -> None:
    assert sha256(real_source_bytes).hexdigest() == generator.RAW_SHA256
    assert real_snapshot.raw_sha256 == generator.RAW_SHA256
    assert real_snapshot.semantic_sha256 == generator.SEMANTIC_SHA256
    assert len(real_snapshot.paragraphs) == generator.EXPECTED_PARAGRAPHS
    assert real_snapshot.non_whitespace_chars == generator.EXPECTED_NON_WHITESPACE_CHARS
    assert len(real_snapshot.tables) == generator.EXPECTED_TABLES
    assert len(real_snapshot.divisions) == generator.EXPECTED_DIVISIONS
    assert tuple(
        (
            division.slug,
            division.title,
            division.start_ordinal,
            division.end_ordinal,
            division.table_ordinals,
        )
        for division in real_snapshot.divisions
    ) == EXPECTED_DIVISIONS
    assert real_snapshot.paragraphs[0].anchor == "V82-P0001"
    assert real_snapshot.paragraphs[-1].anchor == "V82-P4631"
    assert real_snapshot.tables[0].anchor == "V82-T001"
    assert real_snapshot.tables[-1].anchor == "V82-T122"
    assert generator.validate_v82_snapshot(real_snapshot) == []


def test_validation_reports_hash_count_anchor_range_and_table_ownership_errors(
    real_snapshot,
) -> None:
    wrong_raw = generator.validate_v82_snapshot(
        replace(real_snapshot, raw_sha256="0" * 64)
    )
    assert any("raw SHA256" in error for error in wrong_raw), wrong_raw

    wrong_semantic = generator.validate_v82_snapshot(
        replace(real_snapshot, semantic_sha256="0" * 64)
    )
    assert any("semantic SHA256" in error for error in wrong_semantic), wrong_semantic

    paragraphs = list(real_snapshot.paragraphs)
    paragraphs[1] = replace(paragraphs[1], anchor=paragraphs[0].anchor)
    wrong_paragraphs = generator.validate_v82_snapshot(
        replace(real_snapshot, paragraphs=tuple(paragraphs[:-1]))
    )
    assert any("paragraph count" in error for error in wrong_paragraphs), wrong_paragraphs
    assert any("paragraph anchor" in error for error in wrong_paragraphs), wrong_paragraphs

    divisions = list(real_snapshot.divisions)
    divisions[0] = replace(
        divisions[0],
        end_ordinal=divisions[0].end_ordinal - 1,
        table_ordinals=(3,),
    )
    wrong_divisions = generator.validate_v82_snapshot(
        replace(real_snapshot, divisions=tuple(divisions))
    )
    assert any("division range" in error for error in wrong_divisions), wrong_divisions
    assert any("table ownership" in error for error in wrong_divisions), wrong_divisions

    wrong_tables = generator.validate_v82_snapshot(
        replace(real_snapshot, tables=real_snapshot.tables[:-1])
    )
    assert any("table count" in error for error in wrong_tables), wrong_tables


@pytest.mark.parametrize("case", ("missing", "duplicate", "reordered"))
def test_validation_reports_invalid_top_level_titles(real_snapshot, case: str) -> None:
    paragraphs = list(real_snapshot.paragraphs)
    indexes = [
        index for index, paragraph in enumerate(paragraphs) if paragraph.style == "PartTitle"
    ]
    if case == "missing":
        paragraphs[indexes[0]] = replace(paragraphs[indexes[0]], style="BodyText")
    elif case == "duplicate":
        paragraphs[indexes[1]] = replace(
            paragraphs[indexes[1]], text=paragraphs[indexes[0]].text
        )
    else:
        first, second = indexes[:2]
        paragraphs[first], paragraphs[second] = (
            replace(paragraphs[first], text=paragraphs[second].text),
            replace(paragraphs[second], text=paragraphs[first].text),
        )
    errors = generator.validate_v82_snapshot(
        replace(real_snapshot, paragraphs=tuple(paragraphs))
    )
    assert any(case in error for error in errors), errors


def test_rendered_tree_is_reread_semantically_and_tree_hash_verified(
    tmp_path: Path,
    real_snapshot,
) -> None:
    stage = tmp_path / "v8.2-source"
    generator.render_v82_source_tree(real_snapshot, stage)
    assert generator.validate_rendered_v82_source_tree(stage, real_snapshot) == []
    expected_markdown = {"00-source-envelope.md"}
    expected_markdown.update(f"{division.slug}.md" for division in real_snapshot.divisions)
    assert expected_markdown.issubset(
        {path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file()}
    )
    assert (stage / "semantic-snapshot.json").read_bytes() == generator.semantic_snapshot_bytes(
        real_snapshot.paragraphs, real_snapshot.tables
    )

    semantic_path = stage / "semantic-snapshot.json"
    semantic_path.write_bytes(semantic_path.read_bytes().replace(b'"ordinal":1', b'"ordinal":9', 1))
    errors = generator.validate_rendered_v82_source_tree(stage, real_snapshot)
    assert any("semantic snapshot" in error for error in errors), errors
    assert any("tree hash" in error for error in errors), errors


def test_render_is_exactly_the_pure_snapshot_derived_file_mapping(
    tmp_path: Path,
    real_snapshot,
) -> None:
    expected_files = generator._rendered_v82_files(real_snapshot)
    assert all(isinstance(path, str) for path in expected_files)
    assert all(isinstance(content, bytes) for content in expected_files.values())

    stage = tmp_path / "v8.2-source"
    generator.render_v82_source_tree(real_snapshot, stage)
    actual_files = {
        path.relative_to(stage).as_posix(): path.read_bytes()
        for path in stage.rglob("*")
        if path.is_file()
    }
    assert actual_files == expected_files


def test_render_rejects_a_junction_stage_root_before_writing(
    tmp_path: Path,
    real_snapshot,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    stage = tmp_path / "stage"
    make_directory_reparse(stage, outside)
    try:
        with pytest.raises(ValueError, match="symlink|reparse"):
            generator.render_v82_source_tree(real_snapshot, stage)
    finally:
        remove_directory_reparse(stage)

    assert list(outside.iterdir()) == []


def test_render_blocks_stage_replacement_after_the_initial_check(
    tmp_path: Path,
    real_snapshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage = tmp_path / "stage"
    displaced = tmp_path / "displaced-stage"
    outside = tmp_path / "outside"
    stage.mkdir()
    outside.mkdir()
    real_rendered_files = generator._rendered_v82_files
    replacement_errors: list[OSError] = []
    replacement_attempted = False

    def replace_stage_before_first_write(snapshot):
        nonlocal replacement_attempted
        files = real_rendered_files(snapshot)
        replacement_attempted = True
        try:
            stage.rename(displaced)
            make_directory_reparse(stage, outside)
        except OSError as error:
            replacement_errors.append(error)
        return files

    monkeypatch.setattr(
        generator,
        "_rendered_v82_files",
        replace_stage_before_first_write,
    )
    rejection: ValueError | None = None
    try:
        try:
            generator.render_v82_source_tree(real_snapshot, stage)
        except ValueError as error:
            rejection = error
    finally:
        if os.path.lexists(stage) and generator._is_link_or_reparse(stage):
            remove_directory_reparse(stage)

    assert replacement_attempted
    assert replacement_errors or rejection is not None
    assert list(outside.iterdir()) == []


def test_render_pins_stage_against_a_concurrent_replacement(
    tmp_path: Path,
    real_snapshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage = tmp_path / "stage"
    displaced = tmp_path / "displaced-stage"
    outside = tmp_path / "outside"
    stage.mkdir()
    outside.mkdir()
    first_write_ready = threading.Event()
    replacement_finished = threading.Event()
    replacement_errors: list[OSError] = []
    replacement_succeeded = False
    real_write_bytes = generator._write_bytes

    def pause_before_first_write(path: Path, payload: bytes) -> None:
        if not first_write_ready.is_set():
            first_write_ready.set()
            assert replacement_finished.wait(timeout=5)
        real_write_bytes(path, payload)

    def replace_stage() -> None:
        nonlocal replacement_succeeded
        assert first_write_ready.wait(timeout=5)
        try:
            stage.rename(displaced)
            make_directory_reparse(stage, outside)
            replacement_succeeded = True
        except OSError as error:
            replacement_errors.append(error)
        finally:
            replacement_finished.set()

    monkeypatch.setattr(generator, "_write_bytes", pause_before_first_write)
    attacker = threading.Thread(target=replace_stage, daemon=True)
    attacker.start()
    rejection: OSError | ValueError | None = None
    try:
        try:
            generator.render_v82_source_tree(real_snapshot, stage)
        except (OSError, ValueError) as error:
            rejection = error
    finally:
        attacker.join(timeout=5)
        if os.path.lexists(stage) and generator._is_link_or_reparse(stage):
            remove_directory_reparse(stage)

    assert not attacker.is_alive()
    assert replacement_errors or (replacement_succeeded and rejection is not None)
    assert list(outside.iterdir()) == []


def test_generate_creates_and_renders_stage_while_promotion_lock_is_held(
    tmp_path: Path,
    real_source_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source.docx"
    source.write_bytes(real_source_bytes)
    lock_held = False
    lock_entries = 0
    rendered_stages: list[Path] = []

    @contextmanager
    def tracked_promotion_lock(_live_dir: Path):
        nonlocal lock_held, lock_entries
        assert not lock_held
        lock_held = True
        lock_entries += 1
        try:
            yield
        finally:
            lock_held = False

    class RenderProbe(Exception):
        pass

    def observe_render(_snapshot, stage_dir: Path) -> None:
        assert lock_held, "stage rendering happened outside the promotion lock"
        rendered_stages.append(Path(stage_dir))
        raise RenderProbe

    monkeypatch.setattr(generator, "_promotion_lock", tracked_promotion_lock)
    monkeypatch.setattr(generator, "render_v82_source_tree", observe_render)

    with pytest.raises(RenderProbe):
        generator.generate(repo, source)

    assert lock_entries == 1
    assert len(rendered_stages) == 1
    assert rendered_stages[0].name.startswith(".v8.2-source.stage-")
    assert list(rendered_stages[0].parent.glob(".v8.2-source.stage-*")) == []


@pytest.mark.parametrize("surface", ("title", "metadata", "body"))
def test_rerendered_tree_hash_cannot_hide_visible_source_tampering(
    tmp_path: Path,
    real_snapshot,
    surface: str,
) -> None:
    stage = tmp_path / "v8.2-source"
    generator.render_v82_source_tree(real_snapshot, stage)
    source_file = stage / "01-guide.md"
    original = source_file.read_text(encoding="utf-8")
    if surface == "title":
        changed = original.replace("# 第一部分　导读", "# 篡改标题", 1)
    elif surface == "metadata":
        changed = original.replace(
            "Paragraph range: `V82-P0350`-`V82-P0423`",
            "Paragraph range: `V82-P0350`-`V82-P9999`",
            1,
        )
    else:
        paragraph = real_snapshot.paragraphs[350]
        visible_record = (
            f"<!-- source-paragraph:{paragraph.anchor} style={paragraph.style} -->\n"
            f"{paragraph.text}\n"
        )
        changed = original.replace(
            visible_record,
            visible_record.replace(paragraph.text, "篡改正文", 1),
            1,
        )
    assert changed != original
    source_file.write_text(changed, encoding="utf-8", newline="\n")
    refresh_tree_hash(stage)

    errors = generator.validate_rendered_v82_source_tree(stage, real_snapshot)
    assert any("file bytes mismatch" in error for error in errors), errors


def test_rendered_tree_rejects_missing_and_unexpected_files(
    tmp_path: Path,
    real_snapshot,
) -> None:
    missing_stage = tmp_path / "missing"
    generator.render_v82_source_tree(real_snapshot, missing_stage)
    (missing_stage / "01-guide.md").unlink()
    refresh_tree_hash(missing_stage)
    missing_errors = generator.validate_rendered_v82_source_tree(
        missing_stage, real_snapshot
    )
    assert any("missing files" in error for error in missing_errors), missing_errors

    unexpected_stage = tmp_path / "unexpected"
    generator.render_v82_source_tree(real_snapshot, unexpected_stage)
    (unexpected_stage / "extra.txt").write_text("extra", encoding="utf-8")
    refresh_tree_hash(unexpected_stage)
    unexpected_errors = generator.validate_rendered_v82_source_tree(
        unexpected_stage, real_snapshot
    )
    assert any("unexpected files" in error for error in unexpected_errors), unexpected_errors


def test_rendered_tree_rejects_expected_file_replaced_by_symlink(
    tmp_path: Path,
    real_snapshot,
) -> None:
    stage = tmp_path / "v8.2-source"
    generator.render_v82_source_tree(real_snapshot, stage)
    expected_file = stage / "01-guide.md"
    external_copy = tmp_path / "external-guide.md"
    external_copy.write_bytes(expected_file.read_bytes())
    expected_file.unlink()
    try:
        expected_file.symlink_to(external_copy)
    except OSError:
        external_directory = tmp_path / "external-guide"
        external_directory.mkdir()
        make_directory_reparse(expected_file, external_directory)
    try:
        errors = generator.validate_rendered_v82_source_tree(stage, real_snapshot)
        assert any("symlink" in error or "reparse" in error for error in errors), errors
    finally:
        if os.path.lexists(expected_file):
            if expected_file.is_symlink():
                expected_file.unlink()
            elif generator._is_link_or_reparse(expected_file):
                remove_directory_reparse(expected_file)


def test_rendered_tree_rejects_junction_inside_tree(
    tmp_path: Path,
    real_snapshot,
) -> None:
    stage = tmp_path / "v8.2-source"
    external = tmp_path / "external"
    external.mkdir()
    (external / "outside.txt").write_text("outside", encoding="utf-8")
    generator.render_v82_source_tree(real_snapshot, stage)
    junction = stage / "linked-outside"
    make_directory_reparse(junction, external)
    try:
        errors = generator.validate_rendered_v82_source_tree(stage, real_snapshot)
        assert any("symlink" in error or "reparse" in error for error in errors), errors
    finally:
        remove_directory_reparse(junction)


def test_prevalidation_finishes_before_staging_and_preserves_live_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    live = repo / "skills/crossframe-ultra/references/v8.2-source"
    live.mkdir(parents=True)
    sentinel = live / "sentinel.txt"
    sentinel.write_text("old", encoding="utf-8")
    source = tmp_path / "fixture.docx"
    write_docx(source)
    monkeypatch.setattr(generator, "RAW_SHA256", sha256(source.read_bytes()).hexdigest())

    with pytest.raises(ValueError, match="paragraph count"):
        generator.generate(repo, source)

    assert sentinel.read_text(encoding="utf-8") == "old"
    assert list(live.parent.glob(".v8.2-source.stage-*")) == []


def test_render_failure_preserves_existing_live_tree(
    tmp_path: Path,
    real_source_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    live = repo / "skills/crossframe-ultra/references/v8.2-source"
    live.mkdir(parents=True)
    sentinel = live / "sentinel.txt"
    sentinel.write_text("old", encoding="utf-8")
    source = tmp_path / "source.docx"
    source.write_bytes(real_source_bytes)
    monkeypatch.setattr(
        generator,
        "render_v82_source_tree",
        mock.Mock(side_effect=OSError("injected render failure")),
    )

    with pytest.raises(OSError, match="injected render failure"):
        generator.generate(repo, source)

    assert sentinel.read_text(encoding="utf-8") == "old"
    assert list(live.parent.glob(".v8.2-source.stage-*")) == []


def test_atomic_promotion_failure_restores_existing_live_tree(tmp_path: Path) -> None:
    live = tmp_path / "v8.2-source"
    stage = tmp_path / ".v8.2-source.stage-test"
    live.mkdir()
    stage.mkdir()
    (live / "sentinel.txt").write_text("old", encoding="utf-8")
    (stage / "new.txt").write_text("new", encoding="utf-8")
    real_rename = generator._rename_guarded_directory
    calls = 0

    def fail_second_rename(source_guard, target, parent_guard, *, label):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected promotion failure")
        return real_rename(
            source_guard,
            target,
            parent_guard,
            label=label,
        )

    with mock.patch.object(
        generator,
        "_rename_guarded_directory",
        side_effect=fail_second_rename,
    ):
        with pytest.raises(OSError, match="injected promotion failure"):
            generator.atomic_replace_tree(stage, live)

    assert (live / "sentinel.txt").read_text(encoding="utf-8") == "old"
    assert not stage.exists()
    assert list(tmp_path.glob(".v8.2-source.backup-*")) == []


def test_failed_publisher_cannot_delete_a_concurrent_successful_publication(
    tmp_path: Path,
) -> None:
    live = tmp_path / "v8.2-source"
    stage_a = tmp_path / ".v8.2-source.stage-a"
    stage_b = tmp_path / ".v8.2-source.stage-b"
    live.mkdir()
    stage_a.mkdir()
    stage_b.mkdir()
    (live / "version.txt").write_text("old", encoding="utf-8")
    (stage_a / "version.txt").write_text("publisher-a", encoding="utf-8")
    (stage_b / "version.txt").write_text("publisher-b", encoding="utf-8")

    a_publish_attempted = threading.Event()
    b_lock_attempted = threading.Event()
    b_lock_acquired = threading.Event()
    b_errors: list[BaseException] = []
    event_order: list[str] = []
    event_order_guard = threading.Lock()
    real_rename = generator._rename_guarded_directory
    real_promotion_lock = generator._promotion_lock

    def record_event(name: str) -> None:
        with event_order_guard:
            event_order.append(name)

    @contextmanager
    def observed_promotion_lock(lock_live: Path):
        is_publisher_b = threading.current_thread().name == "publisher-b"
        if is_publisher_b:
            record_event("b-lock-attempted")
            b_lock_attempted.set()
        with real_promotion_lock(lock_live):
            if is_publisher_b:
                record_event("b-lock-acquired")
                b_lock_acquired.set()
            yield

    def interleaved_rename(source_guard, target, parent_guard, *, label):
        if source_guard.path == stage_a and Path(target) == live:
            a_publish_attempted.set()
            assert b_lock_attempted.wait(timeout=2), (
                "publisher B did not attempt the promotion lock while A held it"
            )
            assert not b_lock_acquired.is_set(), (
                "publisher B acquired the promotion lock before publisher A failed"
            )
            record_event("a-publish-failed")
            raise OSError("injected publisher-a failure")
        return real_rename(
            source_guard,
            target,
            parent_guard,
            label=label,
        )

    def publish_b() -> None:
        assert a_publish_attempted.wait(timeout=2)
        try:
            generator.atomic_replace_tree(stage_b, live)
        except BaseException as error:
            b_errors.append(error)

    contender = threading.Thread(target=publish_b, name="publisher-b", daemon=True)
    contender.start()
    with mock.patch.object(generator, "_promotion_lock", observed_promotion_lock), (
        mock.patch.object(
            generator,
            "_rename_guarded_directory",
            side_effect=interleaved_rename,
        )
    ):
        with pytest.raises(OSError, match="publisher-a failure"):
            generator.atomic_replace_tree(stage_a, live)
    contender.join(timeout=3)

    assert not contender.is_alive()
    assert b_errors == []
    assert b_lock_acquired.is_set()
    assert event_order.index("b-lock-attempted") < event_order.index(
        "a-publish-failed"
    ) < event_order.index("b-lock-acquired")
    assert (live / "version.txt").read_text(encoding="utf-8") == "publisher-b"
    assert list(tmp_path.glob(".v8.2-source.backup-*")) == []


def test_promotion_lock_blocks_an_independent_process(tmp_path: Path) -> None:
    live = tmp_path / "v8.2-source"
    live.mkdir()
    acquired_marker = tmp_path / "child-acquired.txt"
    child_code = "\n".join(
        (
            "import importlib.util",
            "from pathlib import Path",
            "import sys",
            "module_path = Path(sys.argv[1])",
            "spec = importlib.util.spec_from_file_location('ultra_lock_probe', module_path)",
            "module = importlib.util.module_from_spec(spec)",
            "sys.modules[spec.name] = module",
            "spec.loader.exec_module(module)",
            "print('ready', flush=True)",
            "with module._promotion_lock(Path(sys.argv[2])):",
            "    Path(sys.argv[3]).write_text('acquired', encoding='utf-8')",
        )
    )

    with generator._promotion_lock(live):
        child = subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-c",
                child_code,
                str(GENERATOR_PATH),
                str(live),
                str(acquired_marker),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "ready"
        deadline = time.monotonic() + 0.25
        while time.monotonic() < deadline and not acquired_marker.exists():
            time.sleep(0.01)
        assert not acquired_marker.exists()
        assert child.poll() is None

    stdout, stderr = child.communicate(timeout=5)
    assert child.returncode == 0, (stdout, stderr)
    assert acquired_marker.read_text(encoding="utf-8") == "acquired"


def test_committed_live_survives_nonfatal_backup_cleanup_failure(
    tmp_path: Path,
) -> None:
    live = tmp_path / "v8.2-source"
    stage = tmp_path / ".v8.2-source.stage-new"
    live.mkdir()
    stage.mkdir()
    (live / "version.txt").write_text("old", encoding="utf-8")
    (stage / "version.txt").write_text("new", encoding="utf-8")
    real_remove = generator._remove_path_with_identity

    def fail_backup_cleanup(path: Path, expected_identity) -> None:
        if ".backup-" in path.name:
            raise OSError("injected backup cleanup failure")
        real_remove(path, expected_identity)

    with mock.patch.object(
        generator,
        "_remove_path_with_identity",
        side_effect=fail_backup_cleanup,
    ):
        with pytest.warns(RuntimeWarning, match="backup cleanup failed"):
            generator.atomic_replace_tree(stage, live)

    assert (live / "version.txt").read_text(encoding="utf-8") == "new"
    assert len(list(tmp_path.glob(".v8.2-source.backup-*"))) == 1


@pytest.mark.parametrize("link_repo_root", (False, True), ids=("references", "repo-root"))
def test_generate_rejects_repo_or_reference_junction_escape(
    tmp_path: Path,
    link_repo_root: bool,
    real_source_bytes: bytes,
) -> None:
    source = tmp_path / "source.docx"
    source.write_bytes(real_source_bytes)
    outside = tmp_path / "outside"
    outside.mkdir()
    if link_repo_root:
        real_repo = tmp_path / "real-repo"
        real_repo.mkdir()
        repo = tmp_path / "repo-link"
        make_directory_reparse(repo, real_repo)
        junction = repo
    else:
        repo = tmp_path / "repo"
        ultra = repo / "skills/crossframe-ultra"
        ultra.mkdir(parents=True)
        junction = ultra / "references"
        make_directory_reparse(junction, outside)
    try:
        with mock.patch.object(
            generator,
            "render_v82_source_tree",
            side_effect=AssertionError("unsafe render path reached"),
        ):
            with pytest.raises(ValueError, match="symlink|reparse|outside repo"):
                generator.generate(repo, source)
    finally:
        remove_directory_reparse(junction)
    assert list(outside.iterdir()) == []


def test_atomic_promotion_rejects_reparse_parent_even_when_resolved_parents_match(
    tmp_path: Path,
) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    parent_link = tmp_path / "parent-link"
    make_directory_reparse(parent_link, real_parent)
    stage = parent_link / ".v8.2-source.stage-new"
    live = parent_link / "v8.2-source"
    stage.mkdir()
    live.mkdir()
    (stage / "version.txt").write_text("new", encoding="utf-8")
    (live / "version.txt").write_text("old", encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="symlink|reparse"):
            generator.atomic_replace_tree(stage, live)
    finally:
        remove_directory_reparse(parent_link)


def test_atomic_promotion_revalidates_live_after_lock_acquisition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage = tmp_path / ".v8.2-source.stage-new"
    live = tmp_path / "v8.2-source"
    external = tmp_path / "external-live"
    stage.mkdir()
    live.mkdir()
    external.mkdir()
    (stage / "version.txt").write_text("new", encoding="utf-8")
    (external / "outside.txt").write_text("outside", encoding="utf-8")

    @contextmanager
    def swap_live_while_entering_lock(_live_dir: Path):
        live.rmdir()
        make_directory_reparse(live, external)
        try:
            yield
        finally:
            if os.path.lexists(live) and generator._is_link_or_reparse(live):
                remove_directory_reparse(live)

    monkeypatch.setattr(generator, "_promotion_lock", swap_live_while_entering_lock)
    with pytest.raises(ValueError, match="symlink|reparse"):
        generator.atomic_replace_tree(stage, live)
    assert (external / "outside.txt").read_text(encoding="utf-8") == "outside"


def test_root_wrapper_is_a_thin_runpy_adapter() -> None:
    text = ROOT_WRAPPER.read_text(encoding="utf-8")
    assert "runpy.run_path" in text
    assert "generate_crossframe_ultra_v82_source.py" in text
    assert "ZipFile" not in text
    assert "ElementTree" not in text
    assert "def extract_" not in text
    assert len(text.splitlines()) <= 20
