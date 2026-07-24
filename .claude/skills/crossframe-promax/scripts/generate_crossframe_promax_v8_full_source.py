from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import BinaryIO
import warnings
from uuid import uuid4
from zipfile import ZipFile
import xml.etree.ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"

CANONICAL_SOURCE_SHA256 = (
    "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
)
EXPECTED_SOURCE_SHA256 = CANONICAL_SOURCE_SHA256
EXPECTED_PARAGRAPHS = 3863
EXPECTED_NON_WHITESPACE_CHARS = 155721
EXPECTED_TABLES = 117
EXPECTED_SECTIONS = 16
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
EXPECTED_SECTION_END_IDS = (
    "V8-P0407",
    "V8-P0485",
    "V8-P0543",
    "V8-P0806",
    "V8-P0995",
    "V8-P1072",
    "V8-P2243",
    "V8-P2526",
    "V8-P2715",
    "V8-P2906",
    "V8-P3095",
    "V8-P3306",
    "V8-P3558",
    "V8-P3625",
    "V8-P3734",
    "V8-P3863",
)
EXPECTED_ENVELOPE_RANGE = ("V8-P0001", "V8-P0333")
GENERATOR_VERSION = "1.0.0"
EXPECTED_TREE_MERKLE_ROOT = (
    "9b804bd8d4de67b0e0cc0ce3fd106aafe5dd7a40e04a11023af627c9fab4ed6b"
)
TREE_MERKLE_DOMAIN = b"crossframe.promax.v8.source-tree-merkle.v1"
TRANSACTION_JOURNAL_NAME = ".v8-full-source.transaction.json"

CANONICAL_PARTS = (
    ("01-guide", "第一部分　导读"),
    ("02-boundary-method", "第二部分　边界与方法"),
    ("03-universal-grammar", "第三部分　通用结构语法"),
    ("04-root-assumptions", "第四部分　根假设与推论"),
    ("05-scale-transformation", "第五部分　跨尺度与跨圈层变换"),
    ("06-operation-evolution", "第六部分　运转与演化"),
    ("07-human-world", "第七部分　人类结构化世界"),
    ("08-human-state-prototype", "第八部分　人类状态原型"),
    ("09-actor-state-personality", "第九部分　行动者状态与人格假设"),
    ("10-multicircle-joint-state", "第十部分　多圈层对象与联合状态"),
    ("11-event-dynamic-deduction", "第十一部分　事件驱动的动态推演"),
    ("12-conditional-forecast-choice", "第十二部分　条件前瞻与有限选择"),
    ("13-interface-tools", "第十三部分　接口与工具"),
    ("14-normative-selection", "第十四部分　规范选择"),
    ("15-intervention-applications", "第十五部分　干涉与应用"),
    ("16-governance", "第十六部分　治理"),
)
CANONICAL_TITLES = tuple(title for _slug, title in CANONICAL_PARTS)

EXPECTED_SOURCE_RANGES = (
    ("00-source-envelope.md", "V8-P0001", "V8-P0333", "V8-T001", "V8-T001"),
    ("01-guide.md", "V8-P0334", "V8-P0407", "V8-T002", "V8-T003"),
    ("02-boundary-method.md", "V8-P0408", "V8-P0485", "V8-T004", "V8-T004"),
    ("03-universal-grammar.md", "V8-P0486", "V8-P0543", None, None),
    ("04-root-assumptions.md", "V8-P0544", "V8-P0806", "V8-T005", "V8-T010"),
    ("05-scale-transformation.md", "V8-P0807", "V8-P0995", "V8-T011", "V8-T014"),
    ("06-operation-evolution.md", "V8-P0996", "V8-P1072", "V8-T015", "V8-T015"),
    ("07-human-world.md", "V8-P1073", "V8-P2243", "V8-T016", "V8-T073"),
    ("08-human-state-prototype.md", "V8-P2244", "V8-P2526", "V8-T074", "V8-T083"),
    ("09-actor-state-personality.md", "V8-P2527", "V8-P2715", "V8-T084", "V8-T089"),
    ("10-multicircle-joint-state.md", "V8-P2716", "V8-P2906", "V8-T090", "V8-T095"),
    ("11-event-dynamic-deduction.md", "V8-P2907", "V8-P3095", "V8-T096", "V8-T101"),
    ("12-conditional-forecast-choice.md", "V8-P3096", "V8-P3306", "V8-T102", "V8-T109"),
    ("13-interface-tools.md", "V8-P3307", "V8-P3558", "V8-T110", "V8-T117"),
    ("14-normative-selection.md", "V8-P3559", "V8-P3625", None, None),
    ("15-intervention-applications.md", "V8-P3626", "V8-P3734", None, None),
    ("16-governance.md", "V8-P3735", "V8-P3863", None, None),
)


@dataclass(frozen=True)
class V8Paragraph:
    pid: str
    style: str
    text: str


@dataclass(frozen=True)
class V8Table:
    tid: str
    paragraph_ids: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    cell_paragraph_ids: tuple[tuple[tuple[str, ...], ...], ...]


@dataclass(frozen=True)
class V8Section:
    slug: str
    title: str
    start_heading_id: str
    paragraph_ids: tuple[str, ...]
    table_ids: tuple[str, ...]


@dataclass(frozen=True)
class V8Snapshot:
    source_sha256: str
    paragraphs: tuple[V8Paragraph, ...]
    tables: tuple[V8Table, ...]
    sections: tuple[V8Section, ...]
    non_whitespace_chars: int


@dataclass
class GenerationLock:
    path: Path
    handle: BinaryIO
    released: bool = False


class GenerationLockBusy(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_protected_text_bytes(raw: bytes) -> bytes:
    raw.decode("utf-8", errors="strict")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise ValueError("bare CR is forbidden")
    return normalized


def _normalized_text_hash_and_size(path: Path) -> tuple[str, int]:
    normalized = _normalize_protected_text_bytes(Path(path).read_bytes())
    return hashlib.sha256(normalized).hexdigest(), len(normalized)


def _expected_tree_files() -> set[str]:
    files = {
        "00-heading-index.md",
        "00-index.md",
        "00-source-envelope.md",
        "00-table-index.md",
        "00-term-index.md",
    }
    files.update(f"{slug}.md" for slug, _title in CANONICAL_PARTS)
    files.update(f"tables/V8-T{number:03d}.md" for number in range(1, 118))
    return files


def compute_tree_merkle_root(source_tree: Path) -> str:
    source_tree = Path(source_tree)

    def digest(*parts: bytes) -> bytes:
        hasher = hashlib.sha256()
        for part in parts:
            hasher.update(part)
        return hasher.digest()

    leaves: list[bytes] = []
    relative_paths = sorted(_expected_tree_files())
    for relative_path in relative_paths:
        path_bytes = relative_path.encode("utf-8")
        content = _normalize_protected_text_bytes(
            (source_tree / relative_path).read_bytes()
        )
        leaves.append(
            digest(
                TREE_MERKLE_DOMAIN,
                b"\x00leaf\x00",
                len(path_bytes).to_bytes(4, "big", signed=False),
                path_bytes,
                len(content).to_bytes(8, "big", signed=False),
                content,
            )
        )
    if not leaves:
        raise ValueError("source tree Merkle root cannot cover an empty tree")
    leaf_count = len(leaves)
    level = leaves
    while len(level) > 1:
        next_level: list[bytes] = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                next_level.append(
                    digest(TREE_MERKLE_DOMAIN, b"\x00odd\x00", level[index])
                )
            else:
                next_level.append(
                    digest(
                        TREE_MERKLE_DOMAIN,
                        b"\x00node\x00",
                        level[index],
                        level[index + 1],
                    )
                )
        level = next_level
    return digest(
        TREE_MERKLE_DOMAIN,
        b"\x00root\x00",
        leaf_count.to_bytes(4, "big", signed=False),
        level[0],
    ).hex()


def read_document_xml(source_docx: Path) -> ET.Element:
    return read_document_xml_bytes(Path(source_docx).read_bytes())


def read_document_xml_bytes(source_bytes: bytes) -> ET.Element:
    with ZipFile(BytesIO(source_bytes)) as archive:
        return ET.fromstring(archive.read("word/document.xml"))


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


def _paragraph_elements(
    document_root: ET.Element,
) -> tuple[tuple[ET.Element, str, str], ...]:
    found: list[tuple[ET.Element, str, str]] = []
    for element in document_root.iter(f"{W}p"):
        text = _paragraph_text(element)
        if text.strip():
            found.append((element, _paragraph_style(element), text))
    return tuple(found)


def extract_v8_paragraphs(document_root: ET.Element) -> tuple[V8Paragraph, ...]:
    return tuple(
        V8Paragraph(f"V8-P{index:04d}", style, text)
        for index, (_element, style, text) in enumerate(
            _paragraph_elements(document_root), start=1
        )
    )


def index_v8_paragraph_elements(document_root: ET.Element) -> dict[int, str]:
    return {
        id(element): f"V8-P{index:04d}"
        for index, (element, _style, _text) in enumerate(
            _paragraph_elements(document_root), start=1
        )
    }


def extract_v8_tables(
    document_root: ET.Element,
    pid_by_element: dict[int, str],
) -> tuple[V8Table, ...]:
    """Bind tables to global paragraph IDs using depth-first descendant order.

    An outer cell includes paragraphs from nested tables, while each nested table
    also records those paragraphs in its own table-local structure.
    """
    tables: list[V8Table] = []
    for table_index, table_element in enumerate(
        document_root.iter(f"{W}tbl"), start=1
    ):
        rows: list[tuple[str, ...]] = []
        row_cell_ids: list[tuple[tuple[str, ...], ...]] = []
        table_paragraph_ids: list[str] = []
        for row_element in table_element.findall(f"{W}tr"):
            cells: list[str] = []
            cell_ids_for_row: list[tuple[str, ...]] = []
            for cell_element in row_element.findall(f"{W}tc"):
                cell_texts: list[str] = []
                cell_ids: list[str] = []
                for paragraph in cell_element.iter(f"{W}p"):
                    text = _paragraph_text(paragraph)
                    if not text.strip():
                        continue
                    paragraph_id = pid_by_element[id(paragraph)]
                    cell_texts.append(text)
                    cell_ids.append(paragraph_id)
                    table_paragraph_ids.append(paragraph_id)
                cells.append("\n".join(cell_texts))
                cell_ids_for_row.append(tuple(cell_ids))
            rows.append(tuple(cells))
            row_cell_ids.append(tuple(cell_ids_for_row))
        tables.append(
            V8Table(
                tid=f"V8-T{table_index:03d}",
                paragraph_ids=tuple(table_paragraph_ids),
                rows=tuple(rows),
                cell_paragraph_ids=tuple(row_cell_ids),
            )
        )
    return tuple(tables)


def _anchor_number(anchor: str) -> int:
    return int(anchor.rsplit("P", 1)[1])


def _source_file_for_paragraph_id(paragraph_id: str) -> str:
    number = _anchor_number(paragraph_id)
    for filename, start, end, _table_start, _table_end in EXPECTED_SOURCE_RANGES:
        if _anchor_number(start) <= number <= _anchor_number(end):
            return filename
    raise ValueError(f"paragraph is outside fixed v8 source ranges: {paragraph_id}")


def _table_ids_in_range(
    table_start: str | None, table_end: str | None
) -> tuple[str, ...]:
    if table_start is None or table_end is None:
        return ()
    start = int(table_start.rsplit("T", 1)[1])
    end = int(table_end.rsplit("T", 1)[1])
    return tuple(f"V8-T{number:03d}" for number in range(start, end + 1))


def split_v8_sections(
    paragraphs: tuple[V8Paragraph, ...],
    tables: tuple[V8Table, ...],
) -> tuple[V8Section, ...]:
    heading_positions: list[int] = []
    duplicate_titles: list[str] = []
    missing_titles: list[str] = []
    for title in CANONICAL_TITLES:
        matches = [
            index
            for index, paragraph in enumerate(paragraphs)
            if paragraph.style == "1" and paragraph.text == title
        ]
        if len(matches) > 1:
            duplicate_titles.append(title)
        elif not matches:
            missing_titles.append(title)
        else:
            heading_positions.append(matches[0])
    if duplicate_titles:
        raise ValueError(
            "duplicate exact canonical heading: " + ", ".join(duplicate_titles)
        )
    if missing_titles:
        raise ValueError(
            "missing exact canonical heading: " + ", ".join(missing_titles)
        )
    if heading_positions != sorted(heading_positions):
        raise ValueError("canonical heading order does not match the fixed sixteen parts")

    boundaries = heading_positions + [len(paragraphs)]
    sections: list[V8Section] = []
    for part_index, ((slug, title), start) in enumerate(
        zip(CANONICAL_PARTS, heading_positions, strict=True)
    ):
        end = boundaries[part_index + 1]
        section_paragraphs = paragraphs[start:end]
        start_number = _anchor_number(section_paragraphs[0].pid)
        end_number = _anchor_number(section_paragraphs[-1].pid)
        section_table_ids = tuple(
            table.tid
            for table in tables
            if table.paragraph_ids
            and start_number <= _anchor_number(table.paragraph_ids[0]) <= end_number
        )
        sections.append(
            V8Section(
                slug=slug,
                title=title,
                start_heading_id=section_paragraphs[0].pid,
                paragraph_ids=tuple(
                    paragraph.pid for paragraph in section_paragraphs
                ),
                table_ids=section_table_ids,
            )
        )
    return tuple(sections)


def _non_whitespace_count(paragraphs: tuple[V8Paragraph, ...]) -> int:
    return sum(
        not character.isspace()
        for paragraph in paragraphs
        for character in paragraph.text
    )


def validate_v8_snapshot(snapshot: V8Snapshot) -> list[str]:
    errors: list[str] = []
    if snapshot.source_sha256.lower() != EXPECTED_SOURCE_SHA256:
        errors.append(
            "source SHA256 mismatch: "
            f"expected {EXPECTED_SOURCE_SHA256}, got {snapshot.source_sha256}"
        )
    if len(snapshot.paragraphs) != EXPECTED_PARAGRAPHS:
        errors.append(
            f"paragraph count mismatch: expected {EXPECTED_PARAGRAPHS}, "
            f"got {len(snapshot.paragraphs)}"
        )
    expected_paragraph_ids = tuple(
        f"V8-P{index:04d}" for index in range(1, len(snapshot.paragraphs) + 1)
    )
    actual_paragraph_ids = tuple(
        paragraph.pid for paragraph in snapshot.paragraphs
    )
    if actual_paragraph_ids != expected_paragraph_ids:
        errors.append("paragraph anchor sequence is not continuous and unique")

    measured_non_whitespace = _non_whitespace_count(snapshot.paragraphs)
    if snapshot.non_whitespace_chars != measured_non_whitespace:
        errors.append(
            "snapshot non-whitespace character metric does not match paragraph content"
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
    expected_table_ids = tuple(
        f"V8-T{index:03d}" for index in range(1, len(snapshot.tables) + 1)
    )
    actual_table_ids = tuple(table.tid for table in snapshot.tables)
    if actual_table_ids != expected_table_ids:
        errors.append("table anchor sequence is not continuous and unique")

    paragraph_text_by_id = {
        paragraph.pid: paragraph.text for paragraph in snapshot.paragraphs
    }
    for table in snapshot.tables:
        flattened_ids = tuple(
            paragraph_id
            for row in table.cell_paragraph_ids
            for cell in row
            for paragraph_id in cell
        )
        if flattened_ids != table.paragraph_ids:
            errors.append(f"{table.tid}: table paragraph anchor binding mismatch")
        if len(table.rows) != len(table.cell_paragraph_ids):
            errors.append(f"{table.tid}: row and cell-anchor shape mismatch")
            continue
        for row_index, (row, cell_ids) in enumerate(
            zip(table.rows, table.cell_paragraph_ids, strict=True), start=1
        ):
            if len(row) != len(cell_ids):
                errors.append(
                    f"{table.tid}: row {row_index} and cell-anchor shape mismatch"
                )
                continue
            for column_index, (cell_text, ids) in enumerate(
                zip(row, cell_ids, strict=True), start=1
            ):
                if any(paragraph_id not in paragraph_text_by_id for paragraph_id in ids):
                    errors.append(
                        f"{table.tid}: R{row_index}C{column_index} has unknown paragraph anchor"
                    )
                    continue
                expected_text = "\n".join(
                    paragraph_text_by_id[paragraph_id] for paragraph_id in ids
                )
                if cell_text != expected_text:
                    errors.append(
                        f"{table.tid}: R{row_index}C{column_index} text does not match bound paragraphs"
                    )

    if len(snapshot.sections) != EXPECTED_SECTIONS:
        errors.append(
            f"section count mismatch: expected {EXPECTED_SECTIONS}, "
            f"got {len(snapshot.sections)}"
        )
    actual_section_starts = tuple(
        section.start_heading_id for section in snapshot.sections
    )
    if actual_section_starts != EXPECTED_SECTION_START_IDS:
        errors.append(
            "section start anchor mismatch: "
            f"expected {EXPECTED_SECTION_START_IDS}, got {actual_section_starts}"
        )
    actual_section_ranges = tuple(
        (
            section.paragraph_ids[0] if section.paragraph_ids else "EMPTY",
            section.paragraph_ids[-1] if section.paragraph_ids else "EMPTY",
        )
        for section in snapshot.sections
    )
    expected_section_ranges = tuple(
        zip(EXPECTED_SECTION_START_IDS, EXPECTED_SECTION_END_IDS, strict=True)
    )
    if actual_section_ranges != expected_section_ranges:
        errors.append(
            "section paragraph ranges do not match the fixed continuous v8 boundaries"
        )
    if snapshot.paragraphs and actual_section_starts:
        first_section_number = _anchor_number(actual_section_starts[0])
        actual_envelope_range = (
            snapshot.paragraphs[0].pid,
            f"V8-P{first_section_number - 1:04d}",
        )
        if actual_envelope_range != EXPECTED_ENVELOPE_RANGE:
            errors.append(
                "source envelope range mismatch: "
                f"expected {EXPECTED_ENVELOPE_RANGE}, got {actual_envelope_range}"
            )
    try:
        expected_sections = split_v8_sections(snapshot.paragraphs, snapshot.tables)
    except ValueError as error:
        errors.append(str(error))
    else:
        if snapshot.sections != expected_sections:
            errors.append("section boundaries or table bindings do not match source anchors")
    return list(dict.fromkeys(errors))


def _source_file_lines(
    title: str,
    role: str,
    paragraphs: tuple[V8Paragraph, ...],
    source_sha256: str,
) -> list[str]:
    start = paragraphs[0].pid if paragraphs else "EMPTY"
    end = paragraphs[-1].pid if paragraphs else "EMPTY"
    lines = [
        f"# {title}",
        "",
        f"Source SHA256: `{source_sha256}`",
        f"Source role: `{role}`",
        f"Paragraph range: `{start}`-`{end}`",
        f"Paragraph count: `{len(paragraphs)}`",
        "",
        "## Source Paragraphs",
        "",
    ]
    for paragraph in paragraphs:
        lines.extend(
            [
                f"<!-- source_paragraph:{paragraph.pid} style={paragraph.style} -->",
                paragraph.text,
                "",
            ]
        )
    lines.extend(
        [
            "## Canonical Structure",
            "",
            "```json",
            json.dumps(
                [
                    {
                        "pid": paragraph.pid,
                        "style": paragraph.style,
                        "text": paragraph.text,
                    }
                    for paragraph in paragraphs
                ],
                ensure_ascii=False,
                indent=2,
            ),
            "```",
        ]
    )
    return lines


def _markdown_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>").strip()


def _write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def _render_table(
    table: V8Table, source_sha256: str, output_path: Path
) -> None:
    columns = max((len(row) for row in table.rows), default=0)
    lines = [
        f"# CrossFrame ProMax v8 Table {table.tid}",
        "",
        f"Source SHA256: `{source_sha256}`",
        f"Table ID: `{table.tid}`",
        "Source paragraph IDs: "
        + (", ".join(f"`{pid}`" for pid in table.paragraph_ids) or "`EMPTY`"),
        f"Row count: `{len(table.rows)}`",
        f"Column count: `{columns}`",
        "",
        "## Rows",
        "",
    ]
    if columns:
        lines.append("| " + " | ".join(f"column {index}" for index in range(1, columns + 1)) + " |")
        lines.append("| " + " | ".join("---" for _ in range(columns)) + " |")
        for row in table.rows:
            padded = row + ("",) * (columns - len(row))
            lines.append("| " + " | ".join(_markdown_cell(cell) for cell in padded) + " |")
    lines.extend(["", "## Cell Paragraph IDs", ""])
    for row_index, row in enumerate(table.cell_paragraph_ids, start=1):
        for column_index, cell_ids in enumerate(row, start=1):
            value = ", ".join(f"`{pid}`" for pid in cell_ids) or "`EMPTY`"
            lines.append(f"- R{row_index}C{column_index}: {value}")
    lines.extend(
        [
            "",
            "## Canonical Structure",
            "",
            "```json",
            json.dumps(
                {
                    "tid": table.tid,
                    "paragraph_ids": table.paragraph_ids,
                    "rows": table.rows,
                    "cell_paragraph_ids": table.cell_paragraph_ids,
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
        ]
    )
    _write_text(output_path, lines)


def render_v8_source_tree(snapshot: V8Snapshot, output_dir: Path) -> None:
    errors = validate_v8_snapshot(snapshot)
    if errors:
        raise ValueError("invalid v8 snapshot: " + "; ".join(errors))
    output_dir = Path(output_dir)
    if output_dir.exists():
        if not output_dir.is_dir() or any(output_dir.iterdir()):
            raise ValueError(f"render target must be an empty directory: {output_dir}")
    else:
        output_dir.mkdir(parents=True)
    paragraph_by_id = {
        paragraph.pid: paragraph for paragraph in snapshot.paragraphs
    }
    first_section_start = _anchor_number(snapshot.sections[0].start_heading_id)
    envelope = snapshot.paragraphs[: first_section_start - 1]
    _write_text(
        output_dir / "00-source-envelope.md",
        _source_file_lines(
            "CrossFrame ProMax v8 Source Envelope",
            "source-envelope",
            envelope,
            snapshot.source_sha256,
        ),
    )
    for section in snapshot.sections:
        section_paragraphs = tuple(
            paragraph_by_id[paragraph_id] for paragraph_id in section.paragraph_ids
        )
        _write_text(
            output_dir / f"{section.slug}.md",
            _source_file_lines(
                section.title,
                section.slug,
                section_paragraphs,
                snapshot.source_sha256,
            ),
        )

    index_lines = [
        "# CrossFrame ProMax v8 Full Source Index",
        "",
        f"Source SHA256: `{snapshot.source_sha256}`",
        f"Paragraph count: `{len(snapshot.paragraphs)}`",
        f"Non-whitespace characters: `{snapshot.non_whitespace_chars}`",
        f"Table count: `{len(snapshot.tables)}`",
        f"Section count: `{len(snapshot.sections)}`",
        "",
        "| file | title | paragraph range | paragraph count | tables |",
        "| --- | --- | --- | --- | --- |",
    ]
    envelope_range = (
        f"{envelope[0].pid}-{envelope[-1].pid}" if envelope else "EMPTY"
    )
    index_lines.append(
        f"| [00-source-envelope.md](00-source-envelope.md) | Source envelope | "
        f"`{envelope_range}` | `{len(envelope)}` | V8-T001 |"
    )
    for section in snapshot.sections:
        table_ids = ", ".join(section.table_ids)
        index_lines.append(
            f"| [{section.slug}.md]({section.slug}.md) | {section.title} | "
            f"`{section.paragraph_ids[0]}-{section.paragraph_ids[-1]}` | "
            f"`{len(section.paragraph_ids)}` | {table_ids} |"
        )
    _write_text(output_dir / "00-index.md", index_lines)

    heading_lines = [
        "# CrossFrame ProMax v8 Heading Index",
        "",
        f"Source SHA256: `{snapshot.source_sha256}`",
        "",
        "| paragraph id | style | text | source file |",
        "| --- | --- | --- | --- |",
    ]
    for paragraph in snapshot.paragraphs:
        if paragraph.style:
            source_file = _source_file_for_paragraph_id(paragraph.pid)
            heading_lines.append(
                f"| [{paragraph.pid}]({source_file}) | `{paragraph.style}` | "
                f"{_markdown_cell(paragraph.text)} | [{source_file}]({source_file}) |"
            )
    _write_text(output_dir / "00-heading-index.md", heading_lines)

    forms: dict[str, list[V8Paragraph]] = {}
    for paragraph in snapshot.paragraphs:
        if paragraph.style:
            forms.setdefault(paragraph.text, []).append(paragraph)
    term_lines = [
        "# CrossFrame ProMax v8 Exact Source Form Locator",
        "",
        f"Source SHA256: `{snapshot.source_sha256}`",
        "",
        "## Exact Source Form Locator",
        "",
        "This locator groups exact styled source forms without adding definitions.",
        "",
        "| exact source form | styles | source anchors |",
        "| --- | --- | --- |",
    ]
    for source_form in sorted(forms):
        paragraphs_for_form = forms[source_form]
        styles = ", ".join(
            sorted({paragraph.style for paragraph in paragraphs_for_form})
        )
        anchors = ", ".join(
            f"[{paragraph.pid}]({_source_file_for_paragraph_id(paragraph.pid)})"
            for paragraph in paragraphs_for_form
        )
        term_lines.append(
            f"| {_markdown_cell(source_form)} | `{styles}` | {anchors} |"
        )
    _write_text(
        output_dir / "00-term-index.md",
        term_lines,
    )

    table_index_lines = [
        "# CrossFrame ProMax v8 Table Index",
        "",
        f"Source SHA256: `{snapshot.source_sha256}`",
        f"Table count: `{len(snapshot.tables)}`",
        "",
        "| table | paragraph ids | rows | columns | file |",
        "| --- | --- | --- | --- | --- |",
    ]
    for table in snapshot.tables:
        columns = max((len(row) for row in table.rows), default=0)
        table_index_lines.append(
            f"| `{table.tid}` | `{len(table.paragraph_ids)}` | "
            f"`{len(table.rows)}` | `{columns}` | "
            f"[{table.tid}.md](tables/{table.tid}.md) |"
        )
        _render_table(
            table,
            snapshot.source_sha256,
            output_dir / "tables" / f"{table.tid}.md",
        )
    _write_text(output_dir / "00-table-index.md", table_index_lines)


def _expected_generated_paths(snapshot: V8Snapshot) -> set[str]:
    paths = {
        "00-heading-index.md",
        "00-index.md",
        "00-source-envelope.md",
        "00-table-index.md",
        "00-term-index.md",
    }
    paths.update(f"{section.slug}.md" for section in snapshot.sections)
    paths.update(f"tables/{table.tid}.md" for table in snapshot.tables)
    return paths


def _read_generated_text(path: Path, relative_path: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read generated file {relative_path}: {error}")
        return None


def _parse_canonical_json(
    content: str, relative_path: str, errors: list[str]
) -> object | None:
    marker = "## Canonical Structure\n\n```json\n"
    if content.count(marker) != 1:
        errors.append(
            f"content mismatch: {relative_path} canonical JSON block count"
        )
        return None
    payload_text = content.split(marker, 1)[1]
    payload_text, fence, _trailing = payload_text.partition("\n```")
    if not fence:
        errors.append(f"content mismatch: {relative_path} canonical JSON fence")
        return None
    try:
        return json.loads(payload_text)
    except json.JSONDecodeError as error:
        errors.append(f"content mismatch: {relative_path} canonical JSON: {error}")
        return None


def _validate_source_sha(
    content: str,
    relative_path: str,
    source_sha256: str,
    errors: list[str],
) -> None:
    expected = f"Source SHA256: `{source_sha256}`"
    if content.count(expected) != 1:
        errors.append(f"source SHA256 mismatch: {relative_path}")


def _paragraph_records(
    paragraphs: tuple[V8Paragraph, ...],
) -> list[dict[str, str]]:
    return [
        {
            "pid": paragraph.pid,
            "style": paragraph.style,
            "text": paragraph.text,
        }
        for paragraph in paragraphs
    ]


def _validate_source_artifact(
    content: str,
    relative_path: str,
    expected_paragraphs: tuple[V8Paragraph, ...],
    source_sha256: str,
    errors: list[str],
) -> tuple[list[str], list[str]]:
    _validate_source_sha(content, relative_path, source_sha256, errors)
    payload = _parse_canonical_json(content, relative_path, errors)
    expected_records = _paragraph_records(expected_paragraphs)
    records: list[dict[str, str]] | None = None
    if isinstance(payload, list) and all(
        isinstance(record, dict)
        and set(record) == {"pid", "style", "text"}
        and all(isinstance(record[key], str) for key in ("pid", "style", "text"))
        for record in payload
    ):
        records = payload
        if records != expected_records:
            errors.append(
                f"content mismatch: {relative_path} canonical paragraph JSON"
            )
    elif payload is not None:
        errors.append(
            f"content mismatch: {relative_path} canonical paragraph JSON shape"
        )

    prose_header = "## Source Paragraphs\n\n"
    canonical_header = "## Canonical Structure\n\n```json\n"
    prose_region = ""
    if content.count(prose_header) != 1 or canonical_header not in content:
        errors.append(f"content mismatch: {relative_path} source prose structure")
    else:
        prose_region = content.split(prose_header, 1)[1].split(
            canonical_header, 1
        )[0]
    marker_ids = re.findall(
        r"^<!-- source_paragraph:(V8-P\d{4}) style=.* -->$",
        prose_region,
        flags=re.MULTILINE,
    )
    if len(marker_ids) != len(set(marker_ids)):
        errors.append(f"anchor coverage mismatch: {relative_path} duplicate prose marker")

    json_ids: list[str] = []
    if records is not None:
        json_ids = [record["pid"] for record in records]
        expected_prose = "".join(
            f"<!-- source_paragraph:{record['pid']} style={record['style']} -->\n"
            f"{record['text']}\n\n"
            for record in records
        )
        if marker_ids != json_ids or prose_region != expected_prose:
            errors.append(f"content mismatch: {relative_path} prose/JSON disagreement")
    return marker_ids, json_ids


def _table_payload(table: V8Table) -> dict[str, object]:
    return {
        "tid": table.tid,
        "paragraph_ids": list(table.paragraph_ids),
        "rows": [list(row) for row in table.rows],
        "cell_paragraph_ids": [
            [list(cell) for cell in row] for row in table.cell_paragraph_ids
        ],
    }


def _validate_table_prose(
    content: str,
    relative_path: str,
    payload: dict[str, object],
    errors: list[str],
) -> None:
    rows = payload["rows"]
    cell_paragraph_ids = payload["cell_paragraph_ids"]
    if not isinstance(rows, list) or not isinstance(cell_paragraph_ids, list):
        return
    columns = max(
        (len(row) for row in rows if isinstance(row, list)),
        default=0,
    )
    row_lines: list[str] = []
    if columns:
        row_lines.append(
            "| "
            + " | ".join(f"column {index}" for index in range(1, columns + 1))
            + " |"
        )
        row_lines.append("| " + " | ".join("---" for _ in range(columns)) + " |")
        for row in rows:
            if not isinstance(row, list) or any(not isinstance(cell, str) for cell in row):
                return
            padded = row + [""] * (columns - len(row))
            cells = [
                cell.replace("|", "\\|").replace("\n", "<br>").strip()
                for cell in padded
            ]
            row_lines.append("| " + " | ".join(cells) + " |")
    expected_rows = "\n".join(row_lines) + ("\n" if row_lines else "")

    cell_lines: list[str] = []
    for row_index, row in enumerate(cell_paragraph_ids, start=1):
        if not isinstance(row, list):
            return
        for column_index, cell in enumerate(row, start=1):
            if not isinstance(cell, list) or any(not isinstance(pid, str) for pid in cell):
                return
            value = ", ".join(f"`{pid}`" for pid in cell) or "`EMPTY`"
            cell_lines.append(f"- R{row_index}C{column_index}: {value}")
    expected_cells = "\n".join(cell_lines) + ("\n" if cell_lines else "")

    rows_header = "## Rows\n\n"
    cells_header = "## Cell Paragraph IDs\n\n"
    canonical_header = "## Canonical Structure\n\n```json\n"
    if (
        content.count(rows_header) != 1
        or content.count(cells_header) != 1
        or canonical_header not in content
    ):
        errors.append(f"content mismatch: {relative_path} table prose structure")
        return
    actual_rows = content.split(rows_header, 1)[1].split("\n## Cell Paragraph IDs", 1)[0]
    actual_cells = content.split(cells_header, 1)[1].split(
        "\n## Canonical Structure", 1
    )[0]
    if actual_rows != expected_rows or actual_cells != expected_cells:
        errors.append(f"content mismatch: {relative_path} table prose/JSON disagreement")


def _validate_table_artifact(
    content: str,
    relative_path: str,
    table: V8Table,
    source_sha256: str,
    errors: list[str],
) -> None:
    _validate_source_sha(content, relative_path, source_sha256, errors)
    payload = _parse_canonical_json(content, relative_path, errors)
    if not isinstance(payload, dict):
        if payload is not None:
            errors.append(f"content mismatch: {relative_path} canonical table JSON shape")
        return
    expected = _table_payload(table)
    if payload != expected:
        errors.append(f"content mismatch: {relative_path} canonical table JSON")
    required_keys = {"tid", "paragraph_ids", "rows", "cell_paragraph_ids"}
    if set(payload) != required_keys:
        errors.append(f"content mismatch: {relative_path} canonical table JSON shape")
        return
    _validate_table_prose(content, relative_path, payload, errors)


def _validate_control_artifacts(
    generated_dir: Path, snapshot: V8Snapshot, errors: list[str]
) -> None:
    for relative_path in (
        "00-heading-index.md",
        "00-index.md",
        "00-table-index.md",
        "00-term-index.md",
    ):
        path = generated_dir / relative_path
        if not path.is_file():
            continue
        content = _read_generated_text(path, relative_path, errors)
        if content is not None:
            _validate_source_sha(
                content, relative_path, snapshot.source_sha256, errors
            )

    index_path = generated_dir / "00-index.md"
    if index_path.is_file():
        content = _read_generated_text(index_path, "00-index.md", errors)
        if content is not None:
            expected_metrics = (
                f"Paragraph count: `{len(snapshot.paragraphs)}`",
                f"Non-whitespace characters: `{snapshot.non_whitespace_chars}`",
                f"Table count: `{len(snapshot.tables)}`",
                f"Section count: `{len(snapshot.sections)}`",
            )
            if any(content.count(metric) != 1 for metric in expected_metrics):
                errors.append("content mismatch: 00-index.md release metrics")

    heading_path = generated_dir / "00-heading-index.md"
    if heading_path.is_file():
        content = _read_generated_text(heading_path, "00-heading-index.md", errors)
        if content is not None:
            expected_rows: list[str] = []
            for paragraph in snapshot.paragraphs:
                if not paragraph.style:
                    continue
                escaped_text = (
                    paragraph.text.replace("|", "\\|")
                    .replace("\n", "<br>")
                    .strip()
                )
                source_file = _source_file_for_paragraph_id(paragraph.pid)
                expected_rows.append(
                    f"| [{paragraph.pid}]({source_file}) | `{paragraph.style}` | "
                    f"{escaped_text} | [{source_file}]({source_file}) |"
                )
            header = "| --- | --- | --- | --- |\n"
            actual_rows = content.split(header, 1)[1].splitlines() if header in content else []
            if actual_rows != expected_rows:
                errors.append("content mismatch: 00-heading-index.md")


def validate_generated_v8_tree(
    generated_dir: Path, snapshot: V8Snapshot
) -> list[str]:
    snapshot_errors = validate_v8_snapshot(snapshot)
    if snapshot_errors:
        return [f"snapshot: {error}" for error in snapshot_errors]
    generated_dir = Path(generated_dir)
    if not generated_dir.is_dir():
        return [f"generated source tree does not exist: {generated_dir}"]
    errors: list[str] = []
    expected_paths = _expected_generated_paths(snapshot)
    actual_paths = {
        path.relative_to(generated_dir).as_posix()
        for path in generated_dir.rglob("*")
        if path.is_file()
    }
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    if missing:
        errors.append("missing generated files: " + ", ".join(missing))
    if extra:
        errors.append("unexpected generated files: " + ", ".join(extra))

    paragraph_by_id = {
        paragraph.pid: paragraph for paragraph in snapshot.paragraphs
    }
    first_section_start = _anchor_number(snapshot.sections[0].start_heading_id)
    source_artifacts = [
        ("00-source-envelope.md", snapshot.paragraphs[: first_section_start - 1])
    ]
    source_artifacts.extend(
        (
            f"{section.slug}.md",
            tuple(paragraph_by_id[pid] for pid in section.paragraph_ids),
        )
        for section in snapshot.sections
    )
    all_prose_ids: list[str] = []
    all_json_ids: list[str] = []
    for relative_path, paragraphs in source_artifacts:
        path = generated_dir / relative_path
        if not path.is_file():
            continue
        content = _read_generated_text(path, relative_path, errors)
        if content is None:
            continue
        prose_ids, json_ids = _validate_source_artifact(
            content,
            relative_path,
            paragraphs,
            snapshot.source_sha256,
            errors,
        )
        all_prose_ids.extend(prose_ids)
        all_json_ids.extend(json_ids)

    expected_ids = [paragraph.pid for paragraph in snapshot.paragraphs]
    if all_prose_ids != expected_ids:
        errors.append("anchor coverage mismatch: source prose paragraphs")
    if all_json_ids != expected_ids:
        errors.append("anchor coverage mismatch: canonical paragraph JSON")

    for table in snapshot.tables:
        relative_path = f"tables/{table.tid}.md"
        path = generated_dir / relative_path
        if not path.is_file():
            continue
        content = _read_generated_text(path, relative_path, errors)
        if content is not None:
            _validate_table_artifact(
                content,
                relative_path,
                table,
                snapshot.source_sha256,
                errors,
            )

    _validate_control_artifacts(generated_dir, snapshot, errors)
    return list(dict.fromkeys(errors))


def _remove_tree(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _warn_nonfatal(message: str) -> None:
    try:
        warnings.warn(message, RuntimeWarning, stacklevel=2)
    except Exception:
        pass


def _cleanup_committed_backup(path: Path) -> bool:
    try:
        _remove_tree(path)
    except OSError as error:
        _warn_nonfatal(
            "release committed but backup cleanup failed; "
            f"backup retained at {path}: {error}"
        )
        return False
    return True


def atomic_replace_tree(stage_dir: Path, live_dir: Path) -> None:
    stage_dir = Path(stage_dir)
    live_dir = Path(live_dir)
    if stage_dir.resolve() == live_dir.resolve():
        raise ValueError("stage and live must be different directories")
    if not stage_dir.is_dir():
        raise ValueError(f"stage directory does not exist: {stage_dir}")
    if stage_dir.parent.resolve() != live_dir.parent.resolve():
        raise ValueError("stage and live directories must have the same parent")
    backup = live_dir.parent / f".{live_dir.name}.backup-{uuid4().hex}"
    backup_created = False
    live_moved = False
    try:
        if live_dir.exists():
            os.replace(live_dir, backup)
            backup_created = True
            live_moved = True
        os.replace(stage_dir, live_dir)
    except BaseException:
        try:
            if live_moved:
                if live_dir.exists():
                    _remove_tree(live_dir)
                if backup_created and backup.exists():
                    os.replace(backup, live_dir)
                    backup_created = False
                    live_moved = False
        finally:
            if stage_dir.exists():
                _remove_tree(stage_dir)
        raise
    if backup_created and backup.exists():
        _cleanup_committed_backup(backup)


def _fingerprint_release_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _fingerprint_release_tree(path: Path) -> str:
    path = Path(path)
    hasher = hashlib.sha256()
    hasher.update(b"crossframe.promax.v8.release-tree.v1\x00")
    for artifact in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = artifact.relative_to(path).as_posix().encode("utf-8")
        content = artifact.read_bytes()
        hasher.update(len(relative).to_bytes(4, "big", signed=False))
        hasher.update(relative)
        hasher.update(len(content).to_bytes(8, "big", signed=False))
        hasher.update(content)
    return hasher.hexdigest()


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_json_durable(path: Path, payload: dict[str, object]) -> None:
    path = Path(path)
    encoded = (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    temporary = path.parent / f".{path.name}.tmp-{uuid4().hex}"
    descriptor = os.open(
        temporary,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        if temporary.exists():
            _remove_tree(temporary)
        raise


def _valid_release_digest(value: object, *, optional: bool) -> bool:
    if value is None:
        return optional
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _read_transaction_journal(release_parent: Path) -> dict[str, object] | None:
    journal_path = Path(release_parent) / TRANSACTION_JOURNAL_NAME
    if not journal_path.exists():
        return None
    try:
        payload = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid release transaction journal: {error}") from error
    expected_keys = {
        "schema_version",
        "transaction_id",
        "state",
        "stage_tree_name",
        "stage_manifest_name",
        "old_tree_sha256",
        "old_manifest_sha256",
        "new_tree_sha256",
        "new_manifest_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise RuntimeError("release transaction journal fields are not closed")
    transaction_id = payload.get("transaction_id")
    if not isinstance(transaction_id, str) or re.fullmatch(
        r"[0-9a-f]{32}", transaction_id
    ) is None:
        raise RuntimeError("release transaction journal id is invalid")
    if payload.get("schema_version") != 1:
        raise RuntimeError("release transaction journal schema is invalid")
    if payload.get("state") not in {"prepared", "committed"}:
        raise RuntimeError("release transaction journal state is invalid")
    for key, prefix in (
        ("stage_tree_name", ".v8-full-source.stage-"),
        ("stage_manifest_name", ".source_manifest.json.stage-"),
    ):
        value = payload.get(key)
        if (
            not isinstance(value, str)
            or Path(value).name != value
            or not value.startswith(prefix)
        ):
            raise RuntimeError(f"release transaction journal {key} is invalid")
    for key in ("old_tree_sha256", "old_manifest_sha256"):
        if not _valid_release_digest(payload.get(key), optional=True):
            raise RuntimeError(f"release transaction journal {key} is invalid")
    for key in ("new_tree_sha256", "new_manifest_sha256"):
        if not _valid_release_digest(payload.get(key), optional=False):
            raise RuntimeError(f"release transaction journal {key} is invalid")
    return payload


def _matches_release_tree(path: Path, expected: object) -> bool:
    return (
        isinstance(expected, str)
        and Path(path).is_dir()
        and _fingerprint_release_tree(path) == expected
    )


def _matches_release_file(path: Path, expected: object) -> bool:
    return (
        isinstance(expected, str)
        and Path(path).is_file()
        and _fingerprint_release_file(path) == expected
    )


def _cleanup_committed_artifact(path: Path) -> bool:
    if not Path(path).exists():
        return True
    return _cleanup_committed_backup(Path(path))


def recover_release_transaction(release_parent: Path) -> str:
    release_parent = Path(release_parent).resolve()
    journal_temporaries = sorted(
        release_parent.glob(f".{TRANSACTION_JOURNAL_NAME}.tmp-*")
    )
    payload = _read_transaction_journal(release_parent)
    if payload is None:
        for temporary in journal_temporaries:
            _cleanup_committed_artifact(temporary)
        return "none"

    transaction_id = str(payload["transaction_id"])
    journal_path = release_parent / TRANSACTION_JOURNAL_NAME
    live_tree = release_parent / "v8-full-source"
    live_manifest = release_parent / "source_manifest.json"
    stage_tree = release_parent / str(payload["stage_tree_name"])
    stage_manifest = release_parent / str(payload["stage_manifest_name"])
    tree_backup = release_parent / (
        f".{live_tree.name}.backup-{transaction_id}"
    )
    manifest_backup = release_parent / (
        f".{live_manifest.name}.backup-{transaction_id}"
    )

    new_pair_is_live = _matches_release_tree(
        live_tree, payload["new_tree_sha256"]
    ) and _matches_release_file(live_manifest, payload["new_manifest_sha256"])
    if new_pair_is_live:
        cleanup_succeeded = True
        for residue in (
            tree_backup,
            manifest_backup,
            stage_tree,
            stage_manifest,
            *journal_temporaries,
        ):
            cleanup_succeeded = (
                _cleanup_committed_artifact(residue) and cleanup_succeeded
            )
        if cleanup_succeeded:
            try:
                _remove_tree(journal_path)
                _fsync_directory(release_parent)
            except OSError as error:
                _warn_nonfatal(
                    "release committed but transaction journal cleanup failed; "
                    f"journal retained at {journal_path}: {error}"
                )
        return "committed"

    if payload["state"] == "committed":
        raise RuntimeError("committed release fingerprints do not match the journal")

    old_tree_sha = payload["old_tree_sha256"]
    if old_tree_sha is None:
        if tree_backup.exists():
            raise RuntimeError("unexpected tree backup for an initially absent tree")
        if live_tree.exists():
            _remove_tree(live_tree)
    elif tree_backup.exists():
        if not _matches_release_tree(tree_backup, old_tree_sha):
            raise RuntimeError("old tree backup fingerprint mismatch")
        if live_tree.exists():
            _remove_tree(live_tree)
        os.replace(tree_backup, live_tree)
    elif not _matches_release_tree(live_tree, old_tree_sha):
        raise RuntimeError("old live tree cannot be recovered")

    old_manifest_sha = payload["old_manifest_sha256"]
    if old_manifest_sha is None:
        if manifest_backup.exists():
            raise RuntimeError(
                "unexpected manifest backup for an initially absent manifest"
            )
        if live_manifest.exists():
            _remove_tree(live_manifest)
    elif manifest_backup.exists():
        if not _matches_release_file(manifest_backup, old_manifest_sha):
            raise RuntimeError("old manifest backup fingerprint mismatch")
        if live_manifest.exists():
            _remove_tree(live_manifest)
        os.replace(manifest_backup, live_manifest)
    elif not _matches_release_file(live_manifest, old_manifest_sha):
        raise RuntimeError("old live manifest cannot be recovered")

    for stage in (stage_tree, stage_manifest, *journal_temporaries):
        if stage.exists():
            _remove_tree(stage)
    if old_tree_sha is not None and not _matches_release_tree(live_tree, old_tree_sha):
        raise RuntimeError("restored live tree fingerprint mismatch")
    if old_manifest_sha is not None and not _matches_release_file(
        live_manifest, old_manifest_sha
    ):
        raise RuntimeError("restored live manifest fingerprint mismatch")
    _remove_tree(journal_path)
    _fsync_directory(release_parent)
    return "rolled-back"


def atomic_replace_release(
    stage_tree: Path,
    live_tree: Path,
    stage_manifest: Path,
    live_manifest: Path,
    transaction_id: str | None = None,
) -> None:
    stage_tree = Path(stage_tree)
    live_tree = Path(live_tree)
    stage_manifest = Path(stage_manifest)
    live_manifest = Path(live_manifest)
    resolved_paths = {
        path.resolve()
        for path in (stage_tree, live_tree, stage_manifest, live_manifest)
    }
    if len(resolved_paths) != 4:
        raise ValueError("release stage and live paths must all be different")
    if not stage_tree.is_dir():
        raise ValueError(f"stage tree does not exist: {stage_tree}")
    if not stage_manifest.is_file():
        raise ValueError(f"stage manifest does not exist: {stage_manifest}")
    release_parent = live_tree.parent.resolve()
    if any(
        path.parent.resolve() != release_parent
        for path in (stage_tree, stage_manifest, live_manifest)
    ):
        raise ValueError("release stage and live paths must have the same parent")
    recover_release_transaction(release_parent)

    if transaction_id is None:
        transaction_id = uuid4().hex
    if not re.fullmatch(r"[0-9a-f]{32}", transaction_id):
        raise ValueError("transaction id must be 32 lowercase hexadecimal characters")
    tree_backup = release_parent / f".{live_tree.name}.backup-{transaction_id}"
    manifest_backup = release_parent / (
        f".{live_manifest.name}.backup-{transaction_id}"
    )
    if tree_backup.exists() or manifest_backup.exists():
        raise RuntimeError("release transaction backup path already exists")

    journal_path = release_parent / TRANSACTION_JOURNAL_NAME
    payload: dict[str, object] = {
        "schema_version": 1,
        "transaction_id": transaction_id,
        "state": "prepared",
        "stage_tree_name": stage_tree.name,
        "stage_manifest_name": stage_manifest.name,
        "old_tree_sha256": (
            _fingerprint_release_tree(live_tree) if live_tree.exists() else None
        ),
        "old_manifest_sha256": (
            _fingerprint_release_file(live_manifest)
            if live_manifest.exists()
            else None
        ),
        "new_tree_sha256": _fingerprint_release_tree(stage_tree),
        "new_manifest_sha256": _fingerprint_release_file(stage_manifest),
    }
    _write_json_durable(journal_path, payload)
    try:
        if live_tree.exists():
            os.replace(live_tree, tree_backup)
        if live_manifest.exists():
            os.replace(live_manifest, manifest_backup)
        os.replace(stage_tree, live_tree)
        os.replace(stage_manifest, live_manifest)
        payload["state"] = "committed"
        _write_json_durable(journal_path, payload)
    except BaseException as install_error:
        try:
            recovery_outcome = recover_release_transaction(release_parent)
        except BaseException as recovery_error:
            raise RuntimeError(
                "release recovery failed after "
                f"{install_error}: {recovery_error}"
            ) from install_error
        if recovery_outcome == "committed":
            return
        raise
    recover_release_transaction(release_parent)


def _lock_generation_file(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_generation_lock_file(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _acquire_generation_lock(lock_path: Path) -> GenerationLock:
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = lock_path.open("a+b", buffering=0)
    except OSError as error:
        raise RuntimeError(f"cannot open generation lock: {lock_path}") from error
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\x00")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        try:
            handle.close()
        except OSError:
            pass
        raise RuntimeError(f"cannot initialize generation lock: {lock_path}") from error
    try:
        _lock_generation_file(handle)
    except OSError as error:
        try:
            handle.close()
        except OSError:
            pass
        raise GenerationLockBusy(f"generation lock exists: {lock_path}") from error
    return GenerationLock(path=lock_path, handle=handle)


def _release_generation_lock(generation_lock: GenerationLock) -> None:
    if generation_lock.released:
        return
    descriptor = generation_lock.handle.fileno()
    try:
        try:
            _unlock_generation_lock_file(generation_lock.handle)
        except OSError as error:
            _warn_nonfatal(
                "generation lock explicit unlock failed; "
                f"file close will release it: {error}"
            )
    finally:
        try:
            generation_lock.handle.close()
        except OSError as error:
            _warn_nonfatal(f"generation lock close failed: {error}")
            try:
                os.close(descriptor)
            except OSError as fallback_error:
                _warn_nonfatal(
                    "generation lock descriptor close failed: "
                    f"{fallback_error}"
                )
        generation_lock.released = True


def build_source_manifest(
    snapshot: V8Snapshot, source_tree: Path
) -> dict[str, object]:
    source_tree = Path(source_tree)
    file_entries = _source_tree_file_entries(source_tree)
    source_ranges = [
        {
            "file": filename,
            "paragraph_start": paragraph_start,
            "paragraph_end": paragraph_end,
            "table_start": table_start,
            "table_end": table_end,
        }
        for (
            filename,
            paragraph_start,
            paragraph_end,
            table_start,
            table_end,
        ) in EXPECTED_SOURCE_RANGES
    ]
    return {
        "schema_id": "crossframe.promax.v8.source-manifest",
        "schema_version": 1,
        "framework_version": "v8.0",
        "snapshot_sha256": snapshot.source_sha256,
        "paragraph_count": len(snapshot.paragraphs),
        "non_whitespace_chars": snapshot.non_whitespace_chars,
        "table_count": len(snapshot.tables),
        "section_count": len(snapshot.sections),
        "generator": {
            "version": GENERATOR_VERSION,
            "sha256": _normalized_text_hash_and_size(Path(__file__).resolve())[0],
        },
        "source_ranges": source_ranges,
        "files": file_entries,
    }


def _source_tree_file_entries(source_tree: Path) -> list[dict[str, object]]:
    source_tree = Path(source_tree)
    file_entries: list[dict[str, object]] = []
    for path in sorted(source_tree.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(source_tree).as_posix()
        normalized_hash, normalized_size = _normalized_text_hash_and_size(path)
        file_entries.append(
            {
                "path": f"v8-full-source/{relative_path}",
                "sha256": normalized_hash,
                "size": normalized_size,
            }
        )
    return file_entries


def write_source_manifest_stage(
    stage_path: Path, manifest: dict[str, object]
) -> None:
    stage_path = Path(stage_path)
    if stage_path.exists():
        raise ValueError(f"manifest stage already exists: {stage_path}")
    stage_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_staged_source_manifest(
    stage_path: Path,
    source_tree: Path,
    expected_manifest: dict[str, object],
) -> list[str]:
    stage_path = Path(stage_path)
    source_tree = Path(source_tree)
    errors: list[str] = []
    try:
        stage_bytes = stage_path.read_bytes()
    except OSError as error:
        return [f"cannot read staged source manifest: {error}"]
    expected_bytes = (
        json.dumps(expected_manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    if stage_bytes != expected_bytes:
        errors.append("staged source manifest bytes mismatch")
    try:
        staged_manifest = json.loads(stage_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"invalid staged source manifest JSON: {error}")
        return errors
    if not isinstance(staged_manifest, dict):
        errors.append("staged source manifest root must be an object")
        return errors
    if staged_manifest != expected_manifest:
        errors.append("staged source manifest payload mismatch")
    if staged_manifest.get("files") != _source_tree_file_entries(source_tree):
        errors.append("staged source manifest tree inventory mismatch")
    return list(dict.fromkeys(errors))


def generate(repo: Path, source_docx: Path) -> Path:
    repo = Path(repo).resolve()
    source_docx = Path(source_docx).resolve()
    source_bytes = source_docx.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            "source SHA256 mismatch: "
            f"expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}"
        )
    document_root = read_document_xml_bytes(source_bytes)
    paragraphs = extract_v8_paragraphs(document_root)
    pid_by_element = index_v8_paragraph_elements(document_root)
    tables = extract_v8_tables(document_root, pid_by_element)
    sections = split_v8_sections(paragraphs, tables)
    snapshot = V8Snapshot(
        source_sha256=source_sha256,
        paragraphs=paragraphs,
        tables=tables,
        sections=sections,
        non_whitespace_chars=_non_whitespace_count(paragraphs),
    )
    snapshot_errors = validate_v8_snapshot(snapshot)
    if snapshot_errors:
        raise ValueError("invalid v8 source snapshot: " + "; ".join(snapshot_errors))

    live_dir = repo / "skills/crossframe-promax/references/v8-full-source"
    live_dir.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = live_dir.parent / "source_manifest.json"
    lock_path = live_dir.parent / f".{live_dir.name}.lock"
    generation_lock = _acquire_generation_lock(lock_path)
    transaction_id = uuid4().hex
    stage_dir = live_dir.parent / f".{live_dir.name}.stage-{transaction_id}"
    manifest_stage = live_dir.parent / (
        f".{manifest_path.name}.stage-{transaction_id}"
    )
    try:
        stage_dir.mkdir()
        try:
            render_v8_source_tree(snapshot, stage_dir)
            generated_errors = validate_generated_v8_tree(stage_dir, snapshot)
            if generated_errors:
                raise ValueError(
                    "generated v8 source validation failed: "
                    + "; ".join(generated_errors)
                )
            if snapshot.source_sha256 == CANONICAL_SOURCE_SHA256:
                try:
                    stage_merkle_root = compute_tree_merkle_root(stage_dir)
                except (OSError, UnicodeError, ValueError) as error:
                    raise ValueError(
                        f"generated frozen tree Merkle root failed: {error}"
                    ) from error
                if stage_merkle_root != EXPECTED_TREE_MERKLE_ROOT:
                    raise ValueError(
                        "generated frozen tree Merkle root mismatch: "
                        f"expected {EXPECTED_TREE_MERKLE_ROOT}, "
                        f"got {stage_merkle_root}"
                    )
            manifest = build_source_manifest(snapshot, stage_dir)
            write_source_manifest_stage(manifest_stage, manifest)
            manifest_errors = validate_staged_source_manifest(
                manifest_stage,
                stage_dir,
                manifest,
            )
            if manifest_errors:
                raise ValueError(
                    "generated source manifest validation failed: "
                    + "; ".join(manifest_errors)
                )
            atomic_replace_release(
                stage_dir,
                live_dir,
                manifest_stage,
                manifest_path,
                transaction_id,
            )
        finally:
            if manifest_stage.exists():
                _remove_tree(manifest_stage)
            if stage_dir.exists():
                _remove_tree(stage_dir)
    finally:
        _release_generation_lock(generation_lock)
    return live_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the CrossFrame ProMax v8 full-source tree safely."
    )
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--source-docx", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output = generate(args.repo, args.source_docx)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"generated v8 full source: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
