from __future__ import annotations

import argparse
import codecs
from collections.abc import Mapping, Sequence
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import threading
from uuid import uuid4
import warnings
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


SOURCE_DOCX = Path(r"E:\世界模型\跨尺度多圈层结构推演框架v8.2.docx")
RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_NORMALIZATION_VERSION = 1
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
EXPECTED_PARAGRAPHS = 4631
EXPECTED_NON_WHITESPACE_CHARS = 165690
EXPECTED_TABLES = 122
EXPECTED_DIVISIONS = 20
MAX_SOURCE_DOCX_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_XML_BYTES = 16 * 1024 * 1024
MAX_DOCUMENT_XML_COMPRESSION_RATIO = 100
MAX_ZIP_MEMBERS = 512

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
TREE_HASH_DOMAIN = b"crossframe.ultra.v82.source-tree.v1\x00"
LIVE_TREE_RELATIVE_PATH = Path(
    "skills/crossframe-ultra/references/v8.2-source"
)

DIVISION_SPECS = (
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
CANONICAL_TITLES = tuple(spec[1] for spec in DIVISION_SPECS)
_PROMOTION_THREAD_LOCKS_GUARD = threading.Lock()
_PROMOTION_THREAD_LOCKS: dict[str, threading.Lock] = {}
_RENDER_GUARD_LOCAL = threading.local()


@dataclass(frozen=True, slots=True)
class V82Paragraph:
    ordinal: int
    anchor: str
    style: str
    text: str


@dataclass(frozen=True, slots=True)
class V82Table:
    ordinal: int
    anchor: str
    paragraph_ordinals: tuple[int, ...]
    rows: tuple[tuple[str, ...], ...]
    cell_paragraph_ordinals: tuple[tuple[tuple[int, ...], ...], ...]


@dataclass(frozen=True, slots=True)
class V82Division:
    slug: str
    title: str
    start_ordinal: int
    end_ordinal: int
    table_ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class V82Snapshot:
    raw_sha256: str
    semantic_sha256: str
    paragraphs: tuple[V82Paragraph, ...]
    tables: tuple[V82Table, ...]
    divisions: tuple[V82Division, ...]
    non_whitespace_chars: int


def read_document_xml_bytes(source_bytes: bytes) -> ET.Element:
    if len(source_bytes) > MAX_SOURCE_DOCX_BYTES:
        raise ValueError(
            "source archive size exceeds limit: "
            f"{len(source_bytes)} > {MAX_SOURCE_DOCX_BYTES} bytes"
        )
    try:
        with ZipFile(BytesIO(source_bytes)) as archive:
            members = archive.infolist()
            if len(members) > MAX_ZIP_MEMBERS:
                raise ValueError(
                    "DOCX ZIP member count exceeds limit: "
                    f"{len(members)} > {MAX_ZIP_MEMBERS}"
                )
            document_members = [
                member
                for member in members
                if member.filename == "word/document.xml"
            ]
            if len(document_members) != 1:
                raise ValueError(
                    "DOCX ZIP must contain exactly one word/document.xml; "
                    f"found {len(document_members)}"
                )
            document_member = document_members[0]
            if document_member.flag_bits & (0x1 | 0x40):
                raise ValueError("word/document.xml must not be encrypted")
            if document_member.file_size > MAX_DOCUMENT_XML_BYTES:
                raise ValueError(
                    "word/document.xml uncompressed size exceeds limit: "
                    f"{document_member.file_size} > {MAX_DOCUMENT_XML_BYTES} bytes"
                )
            if document_member.file_size and document_member.compress_size <= 0:
                raise ValueError(
                    "word/document.xml compression ratio is invalid: "
                    "non-empty member has zero compressed size"
                )
            compression_ratio = document_member.file_size / max(
                document_member.compress_size, 1
            )
            if compression_ratio > MAX_DOCUMENT_XML_COMPRESSION_RATIO:
                raise ValueError(
                    "word/document.xml compression ratio exceeds limit: "
                    f"{compression_ratio:.2f} > "
                    f"{MAX_DOCUMENT_XML_COMPRESSION_RATIO}"
                )
            with archive.open(document_member) as document_stream:
                document_xml = document_stream.read(MAX_DOCUMENT_XML_BYTES + 1)
    except BadZipFile as error:
        raise ValueError(f"invalid DOCX ZIP: {error}") from error
    except RuntimeError as error:
        if "encrypt" in str(error).lower() or "password" in str(error).lower():
            raise ValueError(
                f"word/document.xml must not be encrypted: {error}"
            ) from error
        raise ValueError(f"cannot read word/document.xml: {error}") from error
    if len(document_xml) > MAX_DOCUMENT_XML_BYTES:
        raise ValueError(
            "word/document.xml uncompressed size exceeds limit while reading"
        )
    forbidden_boms = (
        codecs.BOM_UTF16_LE,
        codecs.BOM_UTF16_BE,
        codecs.BOM_UTF32_LE,
        codecs.BOM_UTF32_BE,
    )
    if document_xml.startswith(forbidden_boms):
        raise ValueError(
            "word/document.xml must use UTF-8 or UTF-8-SIG; "
            "UTF-16/UTF-32 encodings are forbidden"
        )
    try:
        document_text = document_xml.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(
            "word/document.xml must use valid UTF-8 or UTF-8-SIG encoding"
        ) from error
    if "\x00" in document_text:
        raise ValueError(
            "word/document.xml must use UTF-8 or UTF-8-SIG; "
            "NUL-delimited encodings are forbidden"
        )
    declaration = re.match(
        r"\A\s*<\?xml\b(?P<attributes>.*?)\?>",
        document_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if declaration is not None:
        encoding = re.search(
            r"\bencoding\s*=\s*(['\"])(?P<value>[^'\"]+)\1",
            declaration.group("attributes"),
            flags=re.IGNORECASE,
        )
        if encoding is not None and encoding.group("value").casefold() not in {
            "utf-8",
            "utf8",
        }:
            raise ValueError(
                "word/document.xml encoding declaration must be UTF-8"
            )
    if re.search(
        r"<!\s*(?:doctype|entity)\b",
        document_text,
        flags=re.IGNORECASE,
    ):
        raise ValueError("word/document.xml contains a forbidden DOCTYPE or ENTITY")
    try:
        return ET.fromstring(document_text)
    except (ET.ParseError, ValueError) as error:
        raise ValueError(f"invalid word/document.xml: {error}") from error


def _paragraph_text(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        if node.tag == f"{W}t":
            parts.append(node.text or "")
        elif node.tag == f"{W}tab":
            parts.append("\t")
        elif node.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
    return "".join(parts)


def _paragraph_style(element: ET.Element) -> str:
    properties = element.find(f"{W}pPr")
    style = None if properties is None else properties.find(f"{W}pStyle")
    return "" if style is None else style.attrib.get(f"{W}val", "")


def _paragraph_elements(root: ET.Element) -> tuple[ET.Element, ...]:
    return tuple(
        element
        for element in root.iter(f"{W}p")
        if _paragraph_text(element).strip()
    )


def _index_v82_paragraph_elements(root: ET.Element) -> dict[int, int]:
    return {
        id(element): ordinal
        for ordinal, element in enumerate(_paragraph_elements(root), start=1)
    }


def extract_v82_paragraphs(root: ET.Element) -> tuple[V82Paragraph, ...]:
    return tuple(
        V82Paragraph(
            ordinal=ordinal,
            anchor=f"V82-P{ordinal:04d}",
            style=_paragraph_style(element),
            text=_paragraph_text(element),
        )
        for ordinal, element in enumerate(_paragraph_elements(root), start=1)
    )


def extract_v82_tables(
    root: ET.Element,
    ordinal_by_element: Mapping[int, int],
) -> tuple[V82Table, ...]:
    tables: list[V82Table] = []
    for table_ordinal, table_element in enumerate(
        root.iter(f"{W}tbl"), start=1
    ):
        rows: list[tuple[str, ...]] = []
        cell_ordinal_rows: list[tuple[tuple[int, ...], ...]] = []
        table_paragraph_ordinals: list[int] = []
        for row_element in table_element.findall(f"{W}tr"):
            cells: list[str] = []
            cell_ordinals_for_row: list[tuple[int, ...]] = []
            for cell_element in row_element.findall(f"{W}tc"):
                cell_texts: list[str] = []
                cell_ordinals: list[int] = []
                for paragraph in cell_element.iter(f"{W}p"):
                    text = _paragraph_text(paragraph)
                    if not text.strip():
                        continue
                    ordinal = ordinal_by_element[id(paragraph)]
                    cell_texts.append(text)
                    cell_ordinals.append(ordinal)
                    table_paragraph_ordinals.append(ordinal)
                cells.append("\n".join(cell_texts))
                cell_ordinals_for_row.append(tuple(cell_ordinals))
            rows.append(tuple(cells))
            cell_ordinal_rows.append(tuple(cell_ordinals_for_row))
        tables.append(
            V82Table(
                ordinal=table_ordinal,
                anchor=f"V82-T{table_ordinal:03d}",
                paragraph_ordinals=tuple(table_paragraph_ordinals),
                rows=tuple(rows),
                cell_paragraph_ordinals=tuple(cell_ordinal_rows),
            )
        )
    return tuple(tables)


def split_v82_divisions(
    paragraphs: Sequence[V82Paragraph],
    tables: Sequence[V82Table],
) -> tuple[V82Division, ...]:
    part_titles = [
        (index, paragraph.text)
        for index, paragraph in enumerate(paragraphs)
        if paragraph.style == "PartTitle"
    ]
    positions: list[int] = []
    errors: list[str] = []
    for title in CANONICAL_TITLES:
        matches = [index for index, found_title in part_titles if found_title == title]
        if not matches:
            errors.append(f"missing top-level PartTitle: {title}")
        elif len(matches) > 1:
            errors.append(f"duplicate top-level PartTitle: {title}")
        else:
            positions.append(matches[0])
    unexpected = [title for _index, title in part_titles if title not in CANONICAL_TITLES]
    if unexpected:
        errors.append("unexpected top-level PartTitle: " + ", ".join(unexpected))
    if errors:
        raise ValueError("; ".join(errors))
    if positions != sorted(positions):
        raise ValueError("reordered top-level PartTitle sequence")

    boundaries = positions[1:] + [len(paragraphs)]
    divisions: list[V82Division] = []
    for spec, start_index, end_index in zip(
        DIVISION_SPECS, positions, boundaries, strict=True
    ):
        slug, title, _expected_start, _expected_end, _expected_tables = spec
        selected = paragraphs[start_index:end_index]
        if not selected:
            raise ValueError(f"empty top-level division: {title}")
        start_ordinal = selected[0].ordinal
        end_ordinal = selected[-1].ordinal
        table_ordinals = tuple(
            table.ordinal
            for table in tables
            if table.paragraph_ordinals
            and start_ordinal <= table.paragraph_ordinals[0] <= end_ordinal
        )
        divisions.append(
            V82Division(
                slug=slug,
                title=title,
                start_ordinal=start_ordinal,
                end_ordinal=end_ordinal,
                table_ordinals=table_ordinals,
            )
        )
    return tuple(divisions)


def semantic_snapshot_bytes(
    paragraphs: Sequence[V82Paragraph],
    tables: Sequence[V82Table],
) -> bytes:
    payload = {
        "normalization_version": SEMANTIC_NORMALIZATION_VERSION,
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
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _non_whitespace_count(paragraphs: Sequence[V82Paragraph]) -> int:
    return sum(
        not character.isspace()
        for paragraph in paragraphs
        for character in paragraph.text
    )


def _append_once(errors: list[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def validate_v82_snapshot(snapshot: V82Snapshot) -> list[str]:
    errors: list[str] = []
    if snapshot.raw_sha256 != RAW_SHA256:
        errors.append(
            f"raw SHA256 mismatch: expected {RAW_SHA256}, got {snapshot.raw_sha256}"
        )

    calculated_semantic_sha256 = sha256(
        semantic_snapshot_bytes(snapshot.paragraphs, snapshot.tables)
    ).hexdigest()
    if snapshot.semantic_sha256 != calculated_semantic_sha256:
        errors.append(
            "semantic SHA256 does not match snapshot content: "
            f"declared {snapshot.semantic_sha256}, calculated {calculated_semantic_sha256}"
        )
    if calculated_semantic_sha256 != SEMANTIC_SHA256:
        errors.append(
            "semantic SHA256 mismatch: "
            f"expected {SEMANTIC_SHA256}, got {calculated_semantic_sha256}"
        )

    if len(snapshot.paragraphs) != EXPECTED_PARAGRAPHS:
        errors.append(
            f"paragraph count mismatch: expected {EXPECTED_PARAGRAPHS}, "
            f"got {len(snapshot.paragraphs)}"
        )
    expected_paragraph_ordinals = tuple(range(1, EXPECTED_PARAGRAPHS + 1))
    actual_paragraph_ordinals = tuple(
        paragraph.ordinal for paragraph in snapshot.paragraphs
    )
    if actual_paragraph_ordinals != expected_paragraph_ordinals:
        errors.append("paragraph ordinal sequence is not continuous and unique")
    expected_paragraph_anchors = tuple(
        f"V82-P{ordinal:04d}" for ordinal in expected_paragraph_ordinals
    )
    actual_paragraph_anchors = tuple(
        paragraph.anchor for paragraph in snapshot.paragraphs
    )
    if actual_paragraph_anchors != expected_paragraph_anchors:
        errors.append("paragraph anchor sequence is not continuous and unique")

    measured_non_whitespace = _non_whitespace_count(snapshot.paragraphs)
    if snapshot.non_whitespace_chars != measured_non_whitespace:
        errors.append(
            "snapshot non-whitespace character count does not match paragraph content"
        )
    if measured_non_whitespace != EXPECTED_NON_WHITESPACE_CHARS:
        errors.append(
            "non-whitespace character count mismatch: "
            f"expected {EXPECTED_NON_WHITESPACE_CHARS}, got {measured_non_whitespace}"
        )

    if len(snapshot.tables) != EXPECTED_TABLES:
        errors.append(
            f"table count mismatch: expected {EXPECTED_TABLES}, got {len(snapshot.tables)}"
        )
    expected_table_ordinals = tuple(range(1, EXPECTED_TABLES + 1))
    actual_table_ordinals = tuple(table.ordinal for table in snapshot.tables)
    if actual_table_ordinals != expected_table_ordinals:
        errors.append("table ordinal sequence is not continuous and unique")
    expected_table_anchors = tuple(
        f"V82-T{ordinal:03d}" for ordinal in expected_table_ordinals
    )
    actual_table_anchors = tuple(table.anchor for table in snapshot.tables)
    if actual_table_anchors != expected_table_anchors:
        errors.append("table anchor sequence is not continuous and unique")

    paragraph_text_by_ordinal = {
        paragraph.ordinal: paragraph.text for paragraph in snapshot.paragraphs
    }
    for table in snapshot.tables:
        flattened = tuple(
            ordinal
            for row in table.cell_paragraph_ordinals
            for cell in row
            for ordinal in cell
        )
        if flattened != table.paragraph_ordinals:
            errors.append(
                f"{table.anchor}: table paragraph ordinal binding mismatch"
            )
        if len(table.rows) != len(table.cell_paragraph_ordinals):
            errors.append(f"{table.anchor}: row and cell binding shape mismatch")
            continue
        for row_number, (row, cell_bindings) in enumerate(
            zip(table.rows, table.cell_paragraph_ordinals, strict=True), start=1
        ):
            if len(row) != len(cell_bindings):
                errors.append(
                    f"{table.anchor}: row {row_number} and cell binding shape mismatch"
                )
                continue
            for column_number, (cell_text, ordinals) in enumerate(
                zip(row, cell_bindings, strict=True), start=1
            ):
                if any(
                    ordinal not in paragraph_text_by_ordinal for ordinal in ordinals
                ):
                    errors.append(
                        f"{table.anchor}: R{row_number}C{column_number} references "
                        "an unknown paragraph ordinal"
                    )
                    continue
                expected_text = "\n".join(
                    paragraph_text_by_ordinal[ordinal] for ordinal in ordinals
                )
                if cell_text != expected_text:
                    errors.append(
                        f"{table.anchor}: R{row_number}C{column_number} text does not "
                        "match bound paragraphs"
                    )

    if len(snapshot.divisions) != EXPECTED_DIVISIONS:
        errors.append(
            f"division count mismatch: expected {EXPECTED_DIVISIONS}, "
            f"got {len(snapshot.divisions)}"
        )
    try:
        rebuilt_divisions = split_v82_divisions(
            snapshot.paragraphs, snapshot.tables
        )
    except ValueError as error:
        errors.append(str(error))
        rebuilt_divisions = ()
    if rebuilt_divisions and snapshot.divisions != rebuilt_divisions:
        errors.append("division boundaries or table ownership do not match source records")

    for index, spec in enumerate(DIVISION_SPECS):
        if index >= len(snapshot.divisions):
            break
        slug, title, start, end, table_ordinals = spec
        division = snapshot.divisions[index]
        if (division.slug, division.title) != (slug, title):
            errors.append(
                f"division identity mismatch at position {index + 1}: "
                f"expected {slug} / {title}"
            )
        if (division.start_ordinal, division.end_ordinal) != (start, end):
            errors.append(
                f"division range mismatch for {slug}: expected P{start:04d}-P{end:04d}, "
                f"got P{division.start_ordinal:04d}-P{division.end_ordinal:04d}"
            )
        if division.table_ordinals != table_ordinals:
            errors.append(
                f"table ownership mismatch for {slug}: expected {table_ordinals}, "
                f"got {division.table_ordinals}"
            )

    envelope_tables = tuple(
        table.ordinal
        for table in snapshot.tables
        if table.paragraph_ordinals
        and 1 <= table.paragraph_ordinals[0] <= 349
    )
    if envelope_tables != (1,):
        errors.append(
            f"table ownership mismatch for 00-source-envelope: expected (1,), "
            f"got {envelope_tables}"
        )
    return list(dict.fromkeys(errors))


def build_v82_snapshot(source_bytes: bytes) -> V82Snapshot:
    root = read_document_xml_bytes(source_bytes)
    paragraphs = extract_v82_paragraphs(root)
    ordinal_index = _index_v82_paragraph_elements(root)
    tables = extract_v82_tables(root, ordinal_index)
    divisions = split_v82_divisions(paragraphs, tables)
    semantic_bytes = semantic_snapshot_bytes(paragraphs, tables)
    return V82Snapshot(
        raw_sha256=sha256(source_bytes).hexdigest(),
        semantic_sha256=sha256(semantic_bytes).hexdigest(),
        paragraphs=paragraphs,
        tables=tables,
        divisions=divisions,
        non_whitespace_chars=_non_whitespace_count(paragraphs),
    )


def _paragraph_record(paragraph: V82Paragraph) -> dict[str, object]:
    return {
        "ordinal": paragraph.ordinal,
        "anchor": paragraph.anchor,
        "style": paragraph.style,
        "text": paragraph.text,
    }


def _table_record(table: V82Table) -> dict[str, object]:
    return {
        "ordinal": table.ordinal,
        "anchor": table.anchor,
        "paragraph_ordinals": list(table.paragraph_ordinals),
        "rows": [list(row) for row in table.rows],
        "cell_paragraph_ordinals": [
            [list(cell) for cell in row]
            for row in table.cell_paragraph_ordinals
        ],
    }


def _record_payload(
    paragraphs: Sequence[V82Paragraph],
    tables: Sequence[V82Table],
) -> dict[str, object]:
    return {
        "paragraphs": [_paragraph_record(paragraph) for paragraph in paragraphs],
        "tables": [_table_record(table) for table in tables],
    }


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_descriptor_payload(descriptor: int, payload: bytes, *, label: str) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError(f"short write while rendering {label}")
        view = view[written:]
    os.fsync(descriptor)


def _write_bytes(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        _write_descriptor_payload(descriptor, payload, label=str(path))
    finally:
        os.close(descriptor)


def _tables_by_ordinal(snapshot: V82Snapshot) -> dict[int, V82Table]:
    return {table.ordinal: table for table in snapshot.tables}


def _source_record_specs(
    snapshot: V82Snapshot,
) -> tuple[tuple[str, str, tuple[V82Paragraph, ...], tuple[V82Table, ...]], ...]:
    table_by_ordinal = _tables_by_ordinal(snapshot)
    specs: list[
        tuple[str, str, tuple[V82Paragraph, ...], tuple[V82Table, ...]]
    ] = []
    envelope_paragraphs = tuple(
        paragraph for paragraph in snapshot.paragraphs if 1 <= paragraph.ordinal <= 349
    )
    envelope_tables = tuple(
        table_by_ordinal[ordinal]
        for ordinal in (1,)
        if ordinal in table_by_ordinal
    )
    specs.append(
        (
            "00-source-envelope.md",
            "Front matter",
            envelope_paragraphs,
            envelope_tables,
        )
    )
    for division in snapshot.divisions:
        paragraphs = tuple(
            paragraph
            for paragraph in snapshot.paragraphs
            if division.start_ordinal <= paragraph.ordinal <= division.end_ordinal
        )
        tables = tuple(
            table_by_ordinal[ordinal]
            for ordinal in division.table_ordinals
            if ordinal in table_by_ordinal
        )
        specs.append((f"{division.slug}.md", division.title, paragraphs, tables))
    return tuple(specs)


def _render_record_bytes(
    title: str,
    snapshot: V82Snapshot,
    paragraphs: Sequence[V82Paragraph],
    tables: Sequence[V82Table],
) -> bytes:
    start = paragraphs[0].anchor if paragraphs else "EMPTY"
    end = paragraphs[-1].anchor if paragraphs else "EMPTY"
    table_anchors = ", ".join(table.anchor for table in tables) or "none"
    lines = [
        f"# {title}",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"Paragraph range: `{start}`-`{end}`",
        f"Tables: `{table_anchors}`",
        "",
        "## Source Paragraphs",
        "",
    ]
    for paragraph in paragraphs:
        lines.extend(
            [
                f"<!-- source-paragraph:{paragraph.anchor} style={paragraph.style} -->",
                paragraph.text,
                "",
            ]
        )
    payload = _record_payload(paragraphs, tables)
    lines.extend(
        [
            "## Canonical Records",
            "",
            "<!-- canonical-records:start -->",
            "```json",
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "```",
            "<!-- canonical-records:end -->",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _source_manifest(snapshot: V82Snapshot) -> dict[str, object]:
    record_files = [spec[0] for spec in _source_record_specs(snapshot)]
    return {
        "normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "raw_sha256": snapshot.raw_sha256,
        "semantic_sha256": snapshot.semantic_sha256,
        "paragraph_count": len(snapshot.paragraphs),
        "non_whitespace_chars": snapshot.non_whitespace_chars,
        "table_count": len(snapshot.tables),
        "division_count": len(snapshot.divisions),
        "record_files": record_files,
        "divisions": [
            {
                "slug": division.slug,
                "title": division.title,
                "start_ordinal": division.start_ordinal,
                "end_ordinal": division.end_ordinal,
                "table_ordinals": list(division.table_ordinals),
            }
            for division in snapshot.divisions
        ],
    }


def _tree_hash_from_files(files: Mapping[str, bytes]) -> str:
    digest = sha256()
    digest.update(TREE_HASH_DOMAIN)
    for relative_path in sorted(files):
        if relative_path == "source-tree.sha256":
            continue
        relative = relative_path.encode("utf-8")
        content = files[relative_path]
        digest.update(len(relative).to_bytes(4, "big", signed=False))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big", signed=False))
        digest.update(content)
    return digest.hexdigest()


def _rendered_v82_files(snapshot: V82Snapshot) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for filename, title, paragraphs, tables in _source_record_specs(snapshot):
        files[filename] = _render_record_bytes(
            title,
            snapshot,
            paragraphs,
            tables,
        )
    files["semantic-snapshot.json"] = semantic_snapshot_bytes(
        snapshot.paragraphs, snapshot.tables
    )
    files["source-manifest.json"] = _canonical_json_bytes(
        _source_manifest(snapshot)
    )
    files["source-tree.sha256"] = (
        _tree_hash_from_files(files) + "\n"
    ).encode("ascii")
    return files


def _is_link_or_reparse(path: Path) -> bool:
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


@dataclass(frozen=True, slots=True)
class _DirectoryIdentity:
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class _DirectoryGuard:
    path: Path
    identity: _DirectoryIdentity
    native_handle: int | None = None
    descriptor: int | None = None


def _open_windows_directory_handle(
    path: Path,
    *,
    rename_capable: bool,
    deny_delete_sharing: bool,
) -> tuple[int, _DirectoryIdentity]:
    import ctypes
    from ctypes import wintypes

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = (
            ("file_attributes", wintypes.DWORD),
            ("creation_time", wintypes.FILETIME),
            ("last_access_time", wintypes.FILETIME),
            ("last_write_time", wintypes.FILETIME),
            ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD),
            ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        )

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ByHandleFileInformation),
    )
    get_information.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL

    delete_access = 0x00010000
    file_read_attributes = 0x00000080
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    file_share_delete = 0x00000004
    open_existing = 3
    file_flag_backup_semantics = 0x02000000
    file_flag_open_reparse_point = 0x00200000
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400

    desired_access = file_read_attributes
    if rename_capable:
        desired_access |= delete_access
    share_mode = file_share_read | file_share_write
    if not deny_delete_sharing:
        share_mode |= file_share_delete
    handle = create_file(
        str(_lexical_absolute(path)),
        desired_access,
        share_mode,
        None,
        open_existing,
        file_flag_backup_semantics | file_flag_open_reparse_point,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    information = ByHandleFileInformation()
    if not get_information(handle, ctypes.byref(information)):
        error = ctypes.get_last_error()
        close_handle(handle)
        raise ctypes.WinError(error)
    if information.file_attributes & file_attribute_reparse_point:
        close_handle(handle)
        raise ValueError(f"directory is a symlink or reparse point: {path}")
    if not information.file_attributes & file_attribute_directory:
        close_handle(handle)
        raise ValueError(f"path is not a directory: {path}")
    identity = _DirectoryIdentity(
        device=int(information.volume_serial_number),
        inode=(
            int(information.file_index_high) << 32
            | int(information.file_index_low)
        ),
    )
    return int(handle), identity


def _close_windows_handle(handle: int) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    if not close_handle(handle):
        raise ctypes.WinError(ctypes.get_last_error())


@contextmanager
def _guard_directory(
    path: Path,
    *,
    rename_capable: bool = False,
    deny_delete_sharing: bool = True,
):
    path = _lexical_absolute(Path(path))
    if os.name == "nt":
        handle, identity = _open_windows_directory_handle(
            path,
            rename_capable=rename_capable,
            deny_delete_sharing=deny_delete_sharing,
        )
        try:
            yield _DirectoryGuard(
                path=path,
                identity=identity,
                native_handle=handle,
            )
        finally:
            _close_windows_handle(handle)
        return

    flags = os.O_RDONLY
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        if _path_exists_without_following(path) and _is_link_or_reparse(path):
            raise ValueError(
                f"directory is a symlink or reparse point: {path}"
            ) from error
        raise
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"path is not a directory: {path}")
        yield _DirectoryGuard(
            path=path,
            identity=_DirectoryIdentity(metadata.st_dev, metadata.st_ino),
            descriptor=descriptor,
        )
    finally:
        os.close(descriptor)


def _directory_identity_at_path(path: Path) -> _DirectoryIdentity:
    with _guard_directory(
        path,
        deny_delete_sharing=False,
    ) as guard:
        return guard.identity


def _assert_directory_identity(
    path: Path,
    expected: _DirectoryIdentity,
    *,
    label: str,
) -> None:
    try:
        actual = _directory_identity_at_path(path)
    except (OSError, ValueError) as error:
        raise ValueError(f"{label} identity is no longer safe: {path}: {error}") from error
    if actual != expected:
        raise ValueError(
            f"{label} identity changed: expected {expected}, got {actual}: {path}"
        )


def _windows_rename_directory_handle(handle: int, target: Path) -> None:
    import ctypes
    from ctypes import wintypes

    class FileRenameInformation(ctypes.Structure):
        _fields_ = (
            ("replace_if_exists", wintypes.BOOLEAN),
            ("root_directory", wintypes.HANDLE),
            ("file_name_length", wintypes.DWORD),
            ("file_name", wintypes.WCHAR * 1),
        )

    target_bytes = str(_lexical_absolute(target)).encode("utf-16-le")
    buffer_size = (
        FileRenameInformation.file_name.offset
        + len(target_bytes)
        + ctypes.sizeof(wintypes.WCHAR)
    )
    buffer = ctypes.create_string_buffer(buffer_size)
    information = FileRenameInformation.from_buffer(buffer)
    information.replace_if_exists = False
    information.root_directory = None
    information.file_name_length = len(target_bytes)
    ctypes.memmove(
        ctypes.addressof(buffer) + FileRenameInformation.file_name.offset,
        target_bytes,
        len(target_bytes),
    )
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    set_information = kernel32.SetFileInformationByHandle
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    set_information.restype = wintypes.BOOL
    file_rename_info = 3
    if not set_information(
        handle,
        file_rename_info,
        buffer,
        buffer_size,
    ):
        raise ctypes.WinError(ctypes.get_last_error())


def _rename_guarded_directory(
    source_guard: _DirectoryGuard,
    target: Path,
    parent_guard: _DirectoryGuard,
    *,
    label: str,
) -> _DirectoryGuard:
    target = _lexical_absolute(Path(target))
    if source_guard.path.parent != parent_guard.path:
        raise ValueError(f"{label} source is not below the guarded promotion parent")
    if target.parent != parent_guard.path:
        raise ValueError(f"{label} target is not below the guarded promotion parent")
    _assert_directory_identity(
        parent_guard.path,
        parent_guard.identity,
        label="promotion parent",
    )
    _assert_directory_identity(
        source_guard.path,
        source_guard.identity,
        label=label,
    )
    if _path_exists_without_following(target):
        raise ValueError(f"{label} target already exists: {target}")
    if os.name == "nt":
        if source_guard.native_handle is None:
            raise ValueError(f"{label} has no pinned Windows directory handle")
        _windows_rename_directory_handle(source_guard.native_handle, target)
    else:
        if parent_guard.descriptor is None:
            raise ValueError(f"{label} has no anchored parent descriptor")
        os.rename(
            source_guard.path.name,
            target.name,
            src_dir_fd=parent_guard.descriptor,
            dst_dir_fd=parent_guard.descriptor,
        )
    moved_guard = _DirectoryGuard(
        path=target,
        identity=source_guard.identity,
        native_handle=source_guard.native_handle,
        descriptor=source_guard.descriptor,
    )
    _assert_directory_identity(
        moved_guard.path,
        moved_guard.identity,
        label=label,
    )
    _assert_directory_identity(
        parent_guard.path,
        parent_guard.identity,
        label="promotion parent",
    )
    return moved_guard


def _windows_mark_directory_for_deletion(handle: int) -> None:
    import ctypes
    from ctypes import wintypes

    class FileDispositionInformation(ctypes.Structure):
        _fields_ = (("delete_file", wintypes.BOOLEAN),)

    information = FileDispositionInformation(True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    set_information = kernel32.SetFileInformationByHandle
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    set_information.restype = wintypes.BOOL
    file_disposition_info = 4
    if not set_information(
        handle,
        file_disposition_info,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        raise ctypes.WinError(ctypes.get_last_error())


def _path_exists_without_following(path: Path) -> bool:
    return os.path.lexists(path)


def _reject_link_or_reparse(path: Path, *, label: str) -> None:
    if _path_exists_without_following(path) and _is_link_or_reparse(path):
        raise ValueError(f"{label} is a symlink or reparse point: {path}")


def _validate_repo_release_parent(repo_root: Path, release_parent: Path) -> None:
    repo_root = _lexical_absolute(repo_root)
    release_parent = _lexical_absolute(release_parent)
    try:
        relative = release_parent.relative_to(repo_root)
    except ValueError as error:
        raise ValueError(
            f"release parent is outside repo: {release_parent}"
        ) from error

    candidate = repo_root
    _reject_link_or_reparse(candidate, label="repo root")
    for part in relative.parts:
        candidate = candidate / part
        _reject_link_or_reparse(candidate, label="repo release ancestor")

    resolved_repo = repo_root.resolve(strict=False)
    resolved_parent = release_parent.resolve(strict=False)
    try:
        resolved_parent.relative_to(resolved_repo)
    except ValueError as error:
        raise ValueError(
            "resolved release parent is outside repo: "
            f"{resolved_parent} is not below {resolved_repo}"
        ) from error


@contextmanager
def _guard_repo_release_parent(repo_root: Path, release_parent: Path):
    repo_root = _lexical_absolute(repo_root)
    release_parent = _lexical_absolute(release_parent)
    _validate_repo_release_parent(repo_root, release_parent)
    relative = release_parent.relative_to(repo_root)
    paths = [repo_root]
    candidate = repo_root
    for part in relative.parts:
        candidate = candidate / part
        paths.append(candidate)
    with ExitStack() as stack:
        guards = [
            stack.enter_context(
                _guard_directory(path, rename_capable=True)
            )
            for path in paths
        ]
        for guard in guards:
            _assert_directory_identity(
                guard.path,
                guard.identity,
                label="repo release ancestor",
            )
        yield guards[-1]


def _validate_promotion_paths(
    stage_dir: Path,
    live_dir: Path,
    *,
    repo_root: Path | None = None,
    backup: Path | None = None,
) -> None:
    stage_dir = _lexical_absolute(stage_dir)
    live_dir = _lexical_absolute(live_dir)
    if stage_dir == live_dir:
        raise ValueError("stage and live must be different directories")
    if stage_dir.parent != live_dir.parent:
        raise ValueError("stage and live directories must have the same parent")

    parent = stage_dir.parent
    _reject_link_or_reparse(parent, label="promotion parent")
    lock_path = parent / f".{live_dir.name}.promotion.lock"
    for label, path in (
        ("stage directory", stage_dir),
        ("live directory", live_dir),
        ("promotion lock", lock_path),
    ):
        _reject_link_or_reparse(path, label=label)
    if backup is not None:
        backup = _lexical_absolute(backup)
        if backup.parent != parent:
            raise ValueError("backup must use the same safe promotion parent")
        _reject_link_or_reparse(backup, label="backup directory")

    resolved_parent = parent.resolve(strict=False)
    resolved_paths = [
        ("stage directory", stage_dir),
        ("live directory", live_dir),
        ("promotion lock", lock_path),
    ]
    if backup is not None:
        resolved_paths.append(("backup directory", backup))
    for label, path in resolved_paths:
        if path.resolve(strict=False).parent != resolved_parent:
            raise ValueError(f"{label} resolves outside the safe promotion parent")
    if repo_root is not None:
        _validate_repo_release_parent(repo_root, parent)


def _read_regular_tree_files(source_tree: Path) -> dict[str, bytes]:
    source_tree = Path(source_tree)
    if _is_link_or_reparse(source_tree):
        raise ValueError(f"source tree root is a symlink or reparse point: {source_tree}")
    files: dict[str, bytes] = {}
    pending = [source_tree]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(source_tree).as_posix()
                if _is_link_or_reparse(path):
                    raise ValueError(
                        f"rendered source tree contains a symlink or reparse point: {relative}"
                    )
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files[relative] = path.read_bytes()
                else:
                    raise ValueError(
                        f"rendered source tree contains a non-regular entry: {relative}"
                    )
    return files


def compute_v82_tree_sha256(source_tree: Path) -> str:
    return _tree_hash_from_files(_read_regular_tree_files(Path(source_tree)))


def _write_guarded_stage_file(
    stage_guard: _DirectoryGuard,
    relative_path: str,
    content: bytes,
) -> None:
    if (
        not relative_path
        or relative_path in {".", ".."}
        or "/" in relative_path
        or "\\" in relative_path
    ):
        raise ValueError(
            f"rendered source paths must be flat safe filenames: {relative_path!r}"
        )
    _assert_directory_identity(
        stage_guard.path,
        stage_guard.identity,
        label="render stage",
    )
    if os.name == "nt":
        _write_bytes(stage_guard.path / relative_path, content)
    else:
        if stage_guard.descriptor is None:
            raise ValueError("render stage has no anchored directory descriptor")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(
            relative_path,
            flags,
            0o600,
            dir_fd=stage_guard.descriptor,
        )
        try:
            _write_descriptor_payload(
                descriptor,
                content,
                label=relative_path,
            )
        finally:
            os.close(descriptor)
    _assert_directory_identity(
        stage_guard.path,
        stage_guard.identity,
        label="render stage",
    )


def _render_v82_source_tree_with_guard(
    snapshot: V82Snapshot,
    stage_guard: _DirectoryGuard,
) -> None:
    _assert_directory_identity(
        stage_guard.path,
        stage_guard.identity,
        label="render stage",
    )
    with os.scandir(stage_guard.path) as entries:
        if next(entries, None) is not None:
            raise ValueError(
                f"render target must be an empty directory: {stage_guard.path}"
            )
    rendered_files = _rendered_v82_files(snapshot)
    for relative_path, content in rendered_files.items():
        _write_guarded_stage_file(stage_guard, relative_path, content)


@contextmanager
def _activate_render_guard(stage_guard: _DirectoryGuard):
    previous = getattr(_RENDER_GUARD_LOCAL, "stage_guard", None)
    _RENDER_GUARD_LOCAL.stage_guard = stage_guard
    try:
        yield
    finally:
        if previous is None:
            delattr(_RENDER_GUARD_LOCAL, "stage_guard")
        else:
            _RENDER_GUARD_LOCAL.stage_guard = previous


def render_v82_source_tree(snapshot: V82Snapshot, stage_dir: Path) -> None:
    errors = validate_v82_snapshot(snapshot)
    if errors:
        raise ValueError("invalid v8.2 snapshot: " + "; ".join(errors))
    stage_dir = _lexical_absolute(Path(stage_dir))
    active_guard = getattr(_RENDER_GUARD_LOCAL, "stage_guard", None)
    if active_guard is not None:
        if active_guard.path != stage_dir:
            raise ValueError(
                "active render guard does not match requested stage: "
                f"{active_guard.path} != {stage_dir}"
            )
        _render_v82_source_tree_with_guard(snapshot, active_guard)
        return
    stage_parent = stage_dir.parent
    if not _path_exists_without_following(stage_parent):
        raise ValueError(f"render target parent does not exist: {stage_parent}")
    with _guard_directory(stage_parent, rename_capable=True) as parent_guard:
        _assert_directory_identity(
            stage_parent,
            parent_guard.identity,
            label="render stage parent",
        )
        if not _path_exists_without_following(stage_dir):
            os.mkdir(stage_dir, 0o700)
            _assert_directory_identity(
                stage_parent,
                parent_guard.identity,
                label="render stage parent",
            )
        with _guard_directory(stage_dir, rename_capable=True) as stage_guard:
            _render_v82_source_tree_with_guard(snapshot, stage_guard)


def _read_record_payload(content: bytes) -> dict[str, object]:
    text = content.decode("utf-8")
    start_marker = "<!-- canonical-records:start -->\n```json\n"
    end_marker = "\n```\n<!-- canonical-records:end -->"
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError("canonical record markers are missing or duplicated")
    raw_payload = text.split(start_marker, 1)[1].split(end_marker, 1)[0]
    payload = json.loads(raw_payload)
    if not isinstance(payload, dict):
        raise ValueError("canonical record payload must be an object")
    return payload


def validate_rendered_v82_source_tree(
    stage_dir: Path,
    snapshot: V82Snapshot,
) -> list[str]:
    stage_dir = Path(stage_dir)
    errors: list[str] = []
    if not stage_dir.is_dir():
        return [f"rendered source tree is missing: {stage_dir}"]

    expected_files = _rendered_v82_files(snapshot)
    expected_paths = set(expected_files)
    try:
        actual_files = _read_regular_tree_files(stage_dir)
    except (OSError, ValueError) as error:
        return [str(error)]
    actual_paths = set(actual_files)
    missing = sorted(expected_paths - actual_paths)
    unexpected = sorted(actual_paths - expected_paths)
    if missing:
        errors.append("rendered source tree missing files: " + ", ".join(missing))
    if unexpected:
        errors.append(
            "rendered source tree has unexpected files: " + ", ".join(unexpected)
        )

    for relative_path in sorted(expected_paths & actual_paths):
        if actual_files[relative_path] != expected_files[relative_path]:
            errors.append(f"{relative_path}: file bytes mismatch")

    for filename, _title, paragraphs, tables in _source_record_specs(snapshot):
        if filename not in actual_files:
            continue
        try:
            payload = _read_record_payload(actual_files[filename])
        except (UnicodeError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{filename}: cannot reread canonical records: {error}")
            continue
        expected_payload = _record_payload(paragraphs, tables)
        if payload != expected_payload:
            errors.append(f"{filename}: canonical rendered records mismatch")

    rendered_semantic = actual_files.get("semantic-snapshot.json")
    if rendered_semantic is not None:
        expected_semantic = semantic_snapshot_bytes(
            snapshot.paragraphs, snapshot.tables
        )
        if rendered_semantic != expected_semantic:
            errors.append("semantic snapshot bytes mismatch")
        else:
            rendered_semantic_hash = sha256(rendered_semantic).hexdigest()
            if rendered_semantic_hash != snapshot.semantic_sha256:
                errors.append(
                    "semantic snapshot hash does not match declared semantic SHA256"
                )

    rendered_manifest = actual_files.get("source-manifest.json")
    if rendered_manifest is not None:
        expected_manifest = _canonical_json_bytes(_source_manifest(snapshot))
        if rendered_manifest != expected_manifest:
            errors.append("source manifest bytes mismatch")

    rendered_tree_hash = actual_files.get("source-tree.sha256")
    if rendered_tree_hash is not None:
        try:
            declared_tree_hash = rendered_tree_hash.decode("ascii").strip()
            calculated_tree_hash = _tree_hash_from_files(actual_files)
        except (UnicodeError, ValueError) as error:
            errors.append(f"cannot verify tree hash: {error}")
        else:
            if declared_tree_hash != calculated_tree_hash:
                errors.append(
                    "tree hash mismatch: "
                    f"declared {declared_tree_hash}, calculated {calculated_tree_hash}"
                )
    return list(dict.fromkeys(errors))


def _delete_guarded_flat_directory(guard: _DirectoryGuard) -> None:
    path = guard.path
    with os.scandir(path) as entries:
        children = list(entries)
    for entry in children:
        child = Path(entry.path)
        if _is_link_or_reparse(child):
            raise ValueError(
                "refusing to remove a tree containing a symlink or "
                f"reparse point: {child}"
            )
        if not entry.is_file(follow_symlinks=False):
            raise ValueError(
                f"refusing to remove a non-flat generated tree: {child}"
            )
        os.unlink(child)
    _assert_directory_identity(
        path,
        guard.identity,
        label="removal target",
    )
    if os.name == "nt":
        if guard.native_handle is None:
            raise ValueError("removal target has no pinned Windows handle")
        _windows_mark_directory_for_deletion(guard.native_handle)
    else:
        os.rmdir(path)


def _remove_path_with_identity(
    path: Path,
    expected_identity: _DirectoryIdentity | None,
) -> None:
    path = _lexical_absolute(Path(path))
    if not _path_exists_without_following(path):
        return
    if _is_link_or_reparse(path):
        raise ValueError(f"refusing to remove a symlink or reparse point: {path}")
    metadata = os.lstat(path)
    if not stat.S_ISDIR(metadata.st_mode):
        if expected_identity is not None:
            raise ValueError(f"removal target identity changed to a file: {path}")
        os.unlink(path)
        return
    with _guard_directory(path, rename_capable=True) as guard:
        if expected_identity is not None and guard.identity != expected_identity:
            raise ValueError(
                "removal target identity changed: "
                f"expected {expected_identity}, got {guard.identity}: {path}"
            )
        _delete_guarded_flat_directory(guard)


def _remove_path(path: Path) -> None:
    _remove_path_with_identity(path, None)


def _promotion_thread_lock(lock_path: Path) -> threading.Lock:
    key = str(lock_path.resolve()).casefold() if os.name == "nt" else str(lock_path.resolve())
    with _PROMOTION_THREAD_LOCKS_GUARD:
        return _PROMOTION_THREAD_LOCKS.setdefault(key, threading.Lock())


@contextmanager
def _cross_process_file_lock(lock_path: Path):
    lock_path = Path(lock_path)
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _promotion_lock(live_dir: Path):
    lock_path = live_dir.parent / f".{live_dir.name}.promotion.lock"
    thread_lock = _promotion_thread_lock(lock_path)
    with thread_lock:
        with _cross_process_file_lock(lock_path):
            yield


def _atomic_replace_tree_locked(
    stage_guard: _DirectoryGuard,
    live_dir: Path,
    parent_guard: _DirectoryGuard,
    *,
    repo_root: Path | None = None,
) -> None:
    live_dir = _lexical_absolute(Path(live_dir))
    _validate_promotion_paths(
        stage_guard.path,
        live_dir,
        repo_root=repo_root,
    )
    _assert_directory_identity(
        stage_guard.path,
        stage_guard.identity,
        label="promotion stage",
    )
    _assert_directory_identity(
        parent_guard.path,
        parent_guard.identity,
        label="promotion parent",
    )
    backup = live_dir.parent / f".{live_dir.name}.backup-{uuid4().hex}"
    _validate_promotion_paths(
        stage_guard.path,
        live_dir,
        repo_root=repo_root,
        backup=backup,
    )
    backup_context = None
    backup_guard: _DirectoryGuard | None = None
    backup_created = False
    published = False
    try:
        if _path_exists_without_following(live_dir):
            backup_context = _guard_directory(live_dir, rename_capable=True)
            live_guard = backup_context.__enter__()
            backup_guard = _rename_guarded_directory(
                live_guard,
                backup,
                parent_guard,
                label="live tree backup",
            )
            backup_created = True
        _rename_guarded_directory(
            stage_guard,
            live_dir,
            parent_guard,
            label="staged tree publication",
        )
        published = True
    except BaseException:
        try:
            if (
                backup_created
                and not published
                and backup_guard is not None
                and not _path_exists_without_following(live_dir)
            ):
                _rename_guarded_directory(
                    backup_guard,
                    live_dir,
                    parent_guard,
                    label="live tree rollback",
                )
                backup_created = False
        finally:
            if backup_context is not None:
                backup_context.__exit__(None, None, None)
        raise
    if backup_context is not None:
        backup_context.__exit__(None, None, None)
    if published and backup_created and _path_exists_without_following(backup):
        try:
            if backup_guard is None:
                raise ValueError("published backup identity is unavailable")
            _remove_path_with_identity(backup, backup_guard.identity)
        except (OSError, ValueError) as error:
            warnings.warn(
                "source tree published but backup cleanup failed; "
                f"backup retained at {backup}: {error}",
                RuntimeWarning,
                stacklevel=2,
            )


def atomic_replace_tree(
    stage_dir: Path,
    live_dir: Path,
    *,
    repo_root: Path | None = None,
) -> None:
    stage_dir = _lexical_absolute(Path(stage_dir))
    live_dir = _lexical_absolute(Path(live_dir))
    _validate_promotion_paths(stage_dir, live_dir, repo_root=repo_root)
    if not stage_dir.is_dir():
        raise ValueError(f"stage directory does not exist: {stage_dir}")
    stage_identity: _DirectoryIdentity | None = None
    try:
        with _promotion_lock(live_dir):
            with _guard_directory(
                live_dir.parent,
                rename_capable=True,
            ) as parent_guard:
                _validate_promotion_paths(
                    stage_dir,
                    live_dir,
                    repo_root=repo_root,
                )
                with _guard_directory(
                    stage_dir,
                    rename_capable=True,
                ) as stage_guard:
                    stage_identity = stage_guard.identity
                    _atomic_replace_tree_locked(
                        stage_guard,
                        live_dir,
                        parent_guard,
                        repo_root=repo_root,
                    )
    except BaseException:
        if (
            stage_identity is not None
            and _path_exists_without_following(stage_dir)
        ):
            try:
                _remove_path_with_identity(stage_dir, stage_identity)
            except (OSError, ValueError):
                pass
        raise


def _validate_source_file_size(source_docx: Path) -> int:
    source_size = source_docx.stat().st_size
    if source_size > MAX_SOURCE_DOCX_BYTES:
        raise ValueError(
            "source file size exceeds limit: "
            f"{source_size} > {MAX_SOURCE_DOCX_BYTES} bytes"
        )
    return source_size


def _read_bounded_source_file(path: Path) -> bytes:
    with path.open("rb") as handle:
        source_bytes = handle.read(MAX_SOURCE_DOCX_BYTES + 1)
    if len(source_bytes) > MAX_SOURCE_DOCX_BYTES:
        raise ValueError(
            "source file size exceeds limit while reading: "
            f"more than {MAX_SOURCE_DOCX_BYTES} bytes"
        )
    return source_bytes


def generate(repo: Path, source_docx: Path = SOURCE_DOCX) -> Path:
    repo = _lexical_absolute(Path(repo))
    source_docx = Path(source_docx).resolve()
    _validate_source_file_size(source_docx)
    source_bytes = _read_bounded_source_file(source_docx)
    source_sha256 = sha256(source_bytes).hexdigest()
    if source_sha256 != RAW_SHA256:
        raise ValueError(
            f"raw SHA256 mismatch: expected {RAW_SHA256}, got {source_sha256}"
        )
    snapshot = build_v82_snapshot(source_bytes)
    snapshot_errors = validate_v82_snapshot(snapshot)
    if snapshot_errors:
        raise ValueError(
            "invalid v8.2 source snapshot: " + "; ".join(snapshot_errors)
        )

    live_dir = repo / LIVE_TREE_RELATIVE_PATH
    _validate_repo_release_parent(repo, live_dir.parent)
    live_dir.parent.mkdir(parents=True, exist_ok=True)
    _validate_repo_release_parent(repo, live_dir.parent)
    with _promotion_lock(live_dir):
        with _guard_repo_release_parent(repo, live_dir.parent) as parent_guard:
            _validate_repo_release_parent(repo, live_dir.parent)
            _assert_directory_identity(
                live_dir.parent,
                parent_guard.identity,
                label="promotion parent",
            )
            stage_dir = (
                live_dir.parent / f".{live_dir.name}.stage-{uuid4().hex}"
            )
            _validate_promotion_paths(stage_dir, live_dir, repo_root=repo)
            os.mkdir(stage_dir, 0o700)
            _assert_directory_identity(
                live_dir.parent,
                parent_guard.identity,
                label="promotion parent",
            )
            stage_identity: _DirectoryIdentity | None = None
            try:
                with _guard_directory(
                    stage_dir,
                    rename_capable=True,
                ) as stage_guard:
                    stage_identity = stage_guard.identity
                    with _activate_render_guard(stage_guard):
                        render_v82_source_tree(snapshot, stage_dir)
                    _assert_directory_identity(
                        stage_dir,
                        stage_guard.identity,
                        label="render stage",
                    )
                    rendered_errors = validate_rendered_v82_source_tree(
                        stage_dir,
                        snapshot,
                    )
                    if rendered_errors:
                        raise ValueError(
                            "rendered v8.2 source validation failed: "
                            + "; ".join(rendered_errors)
                        )
                    audited_hash = (
                        stage_dir / "source-tree.sha256"
                    ).read_text(encoding="ascii").strip()
                    if audited_hash != compute_v82_tree_sha256(stage_dir):
                        raise ValueError(
                            "tree hash changed after rendered record audit"
                        )
                    _atomic_replace_tree_locked(
                        stage_guard,
                        live_dir,
                        parent_guard,
                        repo_root=repo,
                    )
            finally:
                if (
                    stage_identity is not None
                    and _path_exists_without_following(stage_dir)
                ):
                    _remove_path_with_identity(stage_dir, stage_identity)
    return live_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile and atomically promote the CrossFrame Ultra v8.2 source tree."
    )
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--source-docx", type=Path, default=SOURCE_DOCX)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        live_dir = generate(args.repo, args.source_docx)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"generated CrossFrame Ultra v8.2 source tree: {live_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
