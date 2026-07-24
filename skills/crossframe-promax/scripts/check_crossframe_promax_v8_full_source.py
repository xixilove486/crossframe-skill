from __future__ import annotations

import argparse
from io import BytesIO
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
EXPECTED_SOURCE_SHA256 = (
    "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
)
EXPECTED_PARAGRAPHS = 3863
EXPECTED_NON_WHITESPACE_CHARS = 155721
EXPECTED_TABLES = 117
EXPECTED_SECTIONS = 16
GENERATOR_VERSION = "1.0.0"
EXPECTED_TREE_MERKLE_ROOT = (
    "9b804bd8d4de67b0e0cc0ce3fd106aafe5dd7a40e04a11023af627c9fab4ed6b"
)
TREE_MERKLE_DOMAIN = b"crossframe.promax.v8.source-tree-merkle.v1"

CANONICAL_PARTS = (
    ("01-guide.md", "第一部分　导读"),
    ("02-boundary-method.md", "第二部分　边界与方法"),
    ("03-universal-grammar.md", "第三部分　通用结构语法"),
    ("04-root-assumptions.md", "第四部分　根假设与推论"),
    ("05-scale-transformation.md", "第五部分　跨尺度与跨圈层变换"),
    ("06-operation-evolution.md", "第六部分　运转与演化"),
    ("07-human-world.md", "第七部分　人类结构化世界"),
    ("08-human-state-prototype.md", "第八部分　人类状态原型"),
    ("09-actor-state-personality.md", "第九部分　行动者状态与人格假设"),
    ("10-multicircle-joint-state.md", "第十部分　多圈层对象与联合状态"),
    ("11-event-dynamic-deduction.md", "第十一部分　事件驱动的动态推演"),
    ("12-conditional-forecast-choice.md", "第十二部分　条件前瞻与有限选择"),
    ("13-interface-tools.md", "第十三部分　接口与工具"),
    ("14-normative-selection.md", "第十四部分　规范选择"),
    ("15-intervention-applications.md", "第十五部分　干涉与应用"),
    ("16-governance.md", "第十六部分　治理"),
)

SOURCE_RANGES = (
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

MANIFEST_KEYS = {
    "schema_id",
    "schema_version",
    "framework_version",
    "snapshot_sha256",
    "paragraph_count",
    "non_whitespace_chars",
    "table_count",
    "section_count",
    "generator",
    "source_ranges",
    "files",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
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


def _paragraph_number(paragraph_id: str) -> int:
    return int(paragraph_id.rsplit("P", 1)[1])


def _table_number(table_id: str) -> int:
    return int(table_id.rsplit("T", 1)[1])


def _ids_between(start: str, end: str, kind: str) -> list[str]:
    if kind == "paragraph":
        return [
            f"V8-P{number:04d}"
            for number in range(_paragraph_number(start), _paragraph_number(end) + 1)
        ]
    return [
        f"V8-T{number:03d}"
        for number in range(_table_number(start), _table_number(end) + 1)
    ]


def _expected_source_ranges() -> list[dict[str, object]]:
    return [
        {
            "file": filename,
            "paragraph_start": paragraph_start,
            "paragraph_end": paragraph_end,
            "table_start": table_start,
            "table_end": table_end,
        }
        for filename, paragraph_start, paragraph_end, table_start, table_end in SOURCE_RANGES
    ]


def _expected_tree_files() -> set[str]:
    files = {
        "00-heading-index.md",
        "00-index.md",
        "00-table-index.md",
        "00-term-index.md",
    }
    files.update(source_range[0] for source_range in SOURCE_RANGES)
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


def _source_file_for_pid(paragraph_id: str) -> str | None:
    try:
        number = _paragraph_number(paragraph_id)
    except (ValueError, IndexError):
        return None
    for filename, start, end, _table_start, _table_end in SOURCE_RANGES:
        if _paragraph_number(start) <= number <= _paragraph_number(end):
            return filename
    return None


def _read_text(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read {label}: {error}")
        return None


def _read_json(path: Path, label: str, errors: list[str]) -> object | None:
    content = _read_text(path, label, errors)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        errors.append(f"invalid JSON in {label}: {error}")
        return None


def _canonical_json(content: str, label: str, errors: list[str]) -> object | None:
    marker = "## Canonical Structure\n\n```json\n"
    if content.count(marker) != 1:
        errors.append(f"canonical JSON block mismatch: {label}")
        return None
    payload_text = content.split(marker, 1)[1]
    payload_text, fence, _after = payload_text.partition("\n```")
    if not fence:
        errors.append(f"canonical JSON fence missing: {label}")
        return None
    try:
        return json.loads(payload_text)
    except json.JSONDecodeError as error:
        errors.append(f"canonical JSON invalid: {label}: {error}")
        return None


def _source_sha_line(content: str, label: str, errors: list[str]) -> None:
    expected = f"Source SHA256: `{EXPECTED_SOURCE_SHA256}`"
    if content.count(expected) != 1:
        errors.append(f"source SHA256 backlink mismatch: {label}")


def _parse_source_file(
    source_tree: Path,
    source_range: tuple[str, str, str, str | None, str | None],
    expected_title: str | None,
    errors: list[str],
) -> list[dict[str, str]]:
    filename, paragraph_start, paragraph_end, _table_start, _table_end = source_range
    path = source_tree / filename
    if not path.is_file():
        return []
    content = _read_text(path, filename, errors)
    if content is None:
        return []
    _source_sha_line(content, filename, errors)
    range_line = f"Paragraph range: `{paragraph_start}`-`{paragraph_end}`"
    if content.count(range_line) != 1:
        errors.append(f"section paragraph range metadata mismatch: {filename}")
    payload = _canonical_json(content, filename, errors)
    if not isinstance(payload, list):
        if payload is not None:
            errors.append(f"canonical paragraph JSON shape mismatch: {filename}")
        return []
    records: list[dict[str, str]] = []
    for record in payload:
        if not (
            isinstance(record, dict)
            and set(record) == {"pid", "style", "text"}
            and all(isinstance(record.get(key), str) for key in ("pid", "style", "text"))
        ):
            errors.append(f"canonical paragraph JSON shape mismatch: {filename}")
            return []
        records.append(record)
    expected_ids = _ids_between(paragraph_start, paragraph_end, "paragraph")
    json_ids = [record["pid"] for record in records]
    if json_ids != expected_ids:
        errors.append(f"section paragraph anchor range mismatch: {filename}")
    if expected_title is not None:
        if not records or records[0]["style"] != "1" or records[0]["text"] != expected_title:
            errors.append(f"section H1 mismatch: {filename}")

    prose_header = "## Source Paragraphs\n\n"
    canonical_header = "## Canonical Structure\n\n```json\n"
    if content.count(prose_header) != 1 or canonical_header not in content:
        errors.append(f"source prose structure mismatch: {filename}")
        return records
    prose = content.split(prose_header, 1)[1].split(canonical_header, 1)[0]
    marker_ids = re.findall(
        r"^<!-- source_paragraph:(V8-P\d{4}) style=.* -->$",
        prose,
        flags=re.MULTILINE,
    )
    if marker_ids != json_ids or len(marker_ids) != len(set(marker_ids)):
        errors.append(f"source paragraph anchor order/uniqueness mismatch: {filename}")
    expected_prose = "".join(
        f"<!-- source_paragraph:{record['pid']} style={record['style']} -->\n"
        f"{record['text']}\n\n"
        for record in records
    )
    if prose != expected_prose:
        errors.append(f"source prose/JSON mismatch: {filename}")
    return records


def _markdown_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>").strip()


def _validate_table_prose(
    content: str, label: str, payload: dict[str, object], errors: list[str]
) -> None:
    rows = payload.get("rows")
    cell_ids = payload.get("cell_paragraph_ids")
    if not isinstance(rows, list) or not isinstance(cell_ids, list):
        return
    if any(
        not isinstance(row, list) or any(not isinstance(cell, str) for cell in row)
        for row in rows
    ):
        return
    columns = max((len(row) for row in rows), default=0)
    row_lines: list[str] = []
    if columns:
        row_lines.append(
            "| " + " | ".join(f"column {index}" for index in range(1, columns + 1)) + " |"
        )
        row_lines.append("| " + " | ".join("---" for _ in range(columns)) + " |")
        for row in rows:
            padded = row + [""] * (columns - len(row))
            row_lines.append("| " + " | ".join(_markdown_cell(cell) for cell in padded) + " |")
    expected_rows = "\n".join(row_lines) + ("\n" if row_lines else "")

    cell_lines: list[str] = []
    for row_index, row in enumerate(cell_ids, start=1):
        if not isinstance(row, list):
            return
        for column_index, cell in enumerate(row, start=1):
            if not isinstance(cell, list) or any(not isinstance(pid, str) for pid in cell):
                return
            anchors = ", ".join(f"`{pid}`" for pid in cell) or "`EMPTY`"
            cell_lines.append(f"- R{row_index}C{column_index}: {anchors}")
    expected_cells = "\n".join(cell_lines) + ("\n" if cell_lines else "")
    rows_header = "## Rows\n\n"
    cells_header = "## Cell Paragraph IDs\n\n"
    if rows_header not in content or cells_header not in content:
        errors.append(f"table prose structure mismatch: {label}")
        return
    actual_rows = content.split(rows_header, 1)[1].split("\n## Cell Paragraph IDs", 1)[0]
    actual_cells = content.split(cells_header, 1)[1].split(
        "\n## Canonical Structure", 1
    )[0]
    if actual_rows != expected_rows or actual_cells != expected_cells:
        errors.append(f"table prose/JSON disagreement: {label}")


def _parse_table_file(
    source_tree: Path,
    table_id: str,
    paragraph_text_by_id: dict[str, str],
    errors: list[str],
) -> dict[str, object] | None:
    relative_path = f"tables/{table_id}.md"
    path = source_tree / relative_path
    if not path.is_file():
        return None
    content = _read_text(path, relative_path, errors)
    if content is None:
        return None
    _source_sha_line(content, relative_path, errors)
    payload = _canonical_json(content, relative_path, errors)
    required_keys = {"tid", "paragraph_ids", "rows", "cell_paragraph_ids"}
    if not isinstance(payload, dict) or set(payload) != required_keys:
        if payload is not None:
            errors.append(f"canonical table JSON shape mismatch: {table_id}")
        return None
    if payload.get("tid") != table_id:
        errors.append(f"table ID mismatch: {relative_path}")
    paragraph_ids = payload.get("paragraph_ids")
    rows = payload.get("rows")
    cell_ids = payload.get("cell_paragraph_ids")
    if not isinstance(paragraph_ids, list) or any(not isinstance(pid, str) for pid in paragraph_ids):
        errors.append(f"table paragraph IDs shape mismatch: {table_id}")
        return payload
    if not isinstance(rows, list) or not isinstance(cell_ids, list) or len(rows) != len(cell_ids):
        errors.append(f"table row/cell shape mismatch: {table_id}")
        return payload
    flattened: list[str] = []
    for row_index, (row, anchor_row) in enumerate(zip(rows, cell_ids, strict=True), start=1):
        if not isinstance(row, list) or not isinstance(anchor_row, list) or len(row) != len(anchor_row):
            errors.append(f"table row/cell shape mismatch: {table_id} R{row_index}")
            continue
        for column_index, (cell_text, anchors) in enumerate(
            zip(row, anchor_row, strict=True), start=1
        ):
            if not isinstance(cell_text, str) or not isinstance(anchors, list) or any(
                not isinstance(pid, str) for pid in anchors
            ):
                errors.append(
                    f"table row/cell shape mismatch: {table_id} R{row_index}C{column_index}"
                )
                continue
            flattened.extend(anchors)
            if any(pid not in paragraph_text_by_id for pid in anchors):
                errors.append(
                    f"cell anchor unknown: {table_id} R{row_index}C{column_index}"
                )
                continue
            expected_text = "\n".join(paragraph_text_by_id[pid] for pid in anchors)
            if cell_text != expected_text:
                errors.append(
                    f"cell text mismatch: {table_id} R{row_index}C{column_index}"
                )
    if flattened != paragraph_ids:
        errors.append(f"cell anchor binding mismatch: {table_id}")
    _validate_table_prose(content, relative_path, payload, errors)
    return payload


def _validate_manifest(
    repo: Path, references: Path, source_tree: Path, errors: list[str]
) -> dict[str, object] | None:
    manifest_path = references / "source_manifest.json"
    if not manifest_path.is_file():
        errors.append("source manifest missing: source_manifest.json")
        return None
    manifest = _read_json(manifest_path, "source_manifest.json", errors)
    if not isinstance(manifest, dict):
        return None
    if set(manifest) != MANIFEST_KEYS:
        errors.append("source manifest top-level fields are not closed")
    expected_constants = {
        "schema_id": "crossframe.promax.v8.source-manifest",
        "schema_version": 1,
        "framework_version": "v8.0",
        "snapshot_sha256": EXPECTED_SOURCE_SHA256,
        "paragraph_count": EXPECTED_PARAGRAPHS,
        "non_whitespace_chars": EXPECTED_NON_WHITESPACE_CHARS,
        "table_count": EXPECTED_TABLES,
        "section_count": EXPECTED_SECTIONS,
    }
    for key, expected in expected_constants.items():
        if manifest.get(key) != expected:
            errors.append(f"source manifest constant mismatch: {key}")
    if manifest.get("source_ranges") != _expected_source_ranges():
        errors.append("source manifest range mismatch")

    generator = manifest.get("generator")
    generator_path = (
        repo
        / "skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py"
    )
    if not isinstance(generator, dict) or set(generator) != {"version", "sha256"}:
        errors.append("source manifest generator fields are not closed")
    else:
        if generator.get("version") != GENERATOR_VERSION:
            errors.append("source manifest generator version mismatch")
        if generator_path.is_file():
            try:
                expected_generator_sha = _normalized_text_hash_and_size(
                    generator_path
                )[0]
            except (OSError, UnicodeError, ValueError) as error:
                errors.append(f"cannot hash generator: {error}")
            else:
                if generator.get("sha256") != expected_generator_sha:
                    errors.append("source manifest generator hash mismatch")
        else:
            errors.append("canonical generator missing")

    entries = manifest.get("files")
    if not isinstance(entries, list):
        errors.append("source manifest files must be a list")
        return manifest
    paths: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size"}:
            errors.append("source manifest file entry fields are not closed")
            continue
        relative_path = entry.get("path")
        if not isinstance(relative_path, str):
            errors.append("source manifest file path must be a string")
            continue
        paths.append(relative_path)
        if not relative_path.startswith("v8-full-source/"):
            errors.append(f"source manifest file path is outside tree: {relative_path}")
            continue
        path = references / relative_path
        if not path.is_file():
            continue
        try:
            actual_hash, actual_size = _normalized_text_hash_and_size(path)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"cannot inspect manifest file {relative_path}: {error}")
            continue
        if entry.get("sha256") != actual_hash:
            errors.append(f"manifest hash mismatch: {relative_path}")
        if entry.get("size") != actual_size:
            errors.append(f"manifest size mismatch: {relative_path}")
    expected_manifest_paths = sorted(
        f"v8-full-source/{relative_path}" for relative_path in _expected_tree_files()
    )
    if paths != sorted(paths):
        errors.append("source manifest file entries are not sorted")
    if paths != expected_manifest_paths:
        errors.append("source manifest file inventory mismatch")
    return manifest


def _validate_indexes(
    source_tree: Path,
    records: list[dict[str, str]],
    errors: list[str],
) -> None:
    contents: dict[str, str] = {}
    for filename in (
        "00-heading-index.md",
        "00-index.md",
        "00-table-index.md",
        "00-term-index.md",
    ):
        path = source_tree / filename
        if not path.is_file():
            continue
        content = _read_text(path, filename, errors)
        if content is not None:
            contents[filename] = content
            _source_sha_line(content, filename, errors)
    index = contents.get("00-index.md", "")
    for filename, _start, _end, _table_start, _table_end in SOURCE_RANGES:
        if f"]({filename})" not in index:
            errors.append(f"index backlink missing: {filename}")
    envelope_line = next(
        (line for line in index.splitlines() if "](00-source-envelope.md)" in line),
        "",
    )
    if "V8-T001" not in envelope_line:
        errors.append("index backlink missing: envelope table V8-T001")

    table_index = contents.get("00-table-index.md", "")
    for number in range(1, 118):
        relative_path = f"tables/V8-T{number:03d}.md"
        if f"]({relative_path})" not in table_index:
            errors.append(f"index backlink missing: {relative_path}")

    heading_index = contents.get("00-heading-index.md", "")
    for record in records:
        if not record["style"]:
            continue
        source_file = _source_file_for_pid(record["pid"])
        if source_file is None or f"[{record['pid']}]({source_file})" not in heading_index:
            errors.append(f"index backlink missing: heading {record['pid']}")

    term_index = contents.get("00-term-index.md", "")
    if "## Exact Source Form Locator" not in term_index:
        errors.append("term index locator is missing")
    for filename, title in CANONICAL_PARTS:
        matching = [record for record in records if record["style"] == "1" and record["text"] == title]
        if not matching or f"[{matching[0]['pid']}]({filename})" not in term_index:
            errors.append(f"index backlink missing: term locator {filename}")


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


def _source_snapshot(source_bytes: bytes) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    with ZipFile(BytesIO(source_bytes)) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    elements: list[ET.Element] = []
    records: list[dict[str, str]] = []
    for element in root.iter(f"{W}p"):
        text = _paragraph_text(element)
        if not text.strip():
            continue
        elements.append(element)
        records.append(
            {
                "pid": f"V8-P{len(records) + 1:04d}",
                "style": _paragraph_style(element),
                "text": text,
            }
        )
    pid_by_element = {
        id(element): record["pid"] for element, record in zip(elements, records, strict=True)
    }
    tables: list[dict[str, object]] = []
    for table_number, table_element in enumerate(root.iter(f"{W}tbl"), start=1):
        rows: list[list[str]] = []
        cell_paragraph_ids: list[list[list[str]]] = []
        paragraph_ids: list[str] = []
        for row_element in table_element.findall(f"{W}tr"):
            row: list[str] = []
            anchor_row: list[list[str]] = []
            for cell_element in row_element.findall(f"{W}tc"):
                texts: list[str] = []
                anchors: list[str] = []
                for paragraph in cell_element.iter(f"{W}p"):
                    text = _paragraph_text(paragraph)
                    if not text.strip():
                        continue
                    pid = pid_by_element[id(paragraph)]
                    texts.append(text)
                    anchors.append(pid)
                    paragraph_ids.append(pid)
                row.append("\n".join(texts))
                anchor_row.append(anchors)
            rows.append(row)
            cell_paragraph_ids.append(anchor_row)
        tables.append(
            {
                "tid": f"V8-T{table_number:03d}",
                "paragraph_ids": paragraph_ids,
                "rows": rows,
                "cell_paragraph_ids": cell_paragraph_ids,
            }
        )
    return records, tables


def _compare_source_docx(
    source_docx: Path,
    committed_records: list[dict[str, str]],
    committed_tables: list[dict[str, object]],
    errors: list[str],
) -> None:
    try:
        source_bytes = Path(source_docx).read_bytes()
    except OSError as error:
        errors.append(f"cannot read source DOCX: {error}")
        return
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        errors.append(
            "source SHA256 mismatch: "
            f"expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}"
        )
        return
    try:
        source_records, source_tables = _source_snapshot(source_bytes)
    except (BadZipFile, KeyError, ET.ParseError, OSError) as error:
        errors.append(f"cannot parse source DOCX: {error}")
        return
    if source_records != committed_records:
        mismatch = next(
            (
                record.get("pid", "unknown")
                for record, committed in zip(source_records, committed_records)
                if record != committed
            ),
            "count",
        )
        errors.append(f"source paragraph mismatch: {mismatch}")
    if source_tables != committed_tables:
        mismatch = next(
            (
                table.get("tid", "unknown")
                for table, committed in zip(source_tables, committed_tables)
                if table != committed
            ),
            "count",
        )
        errors.append(f"source table mismatch: {mismatch}")
    measured_non_whitespace = sum(
        not character.isspace()
        for record in source_records
        for character in record["text"]
    )
    if len(source_records) != EXPECTED_PARAGRAPHS:
        errors.append("source paragraph count mismatch")
    if measured_non_whitespace != EXPECTED_NON_WHITESPACE_CHARS:
        errors.append("source non-whitespace character count mismatch")
    if len(source_tables) != EXPECTED_TABLES:
        errors.append("source table count mismatch")


def _check_repository_unlocked(
    repo: Path, source_docx: Path | None = None
) -> list[str]:
    repo = Path(repo).resolve()
    references = repo / "skills/crossframe-promax/references"
    source_tree = references / "v8-full-source"
    errors: list[str] = []
    if not source_tree.is_dir():
        return [f"source tree does not exist: {source_tree}"]

    expected_files = _expected_tree_files()
    actual_files = {
        path.relative_to(source_tree).as_posix()
        for path in source_tree.rglob("*")
        if path.is_file()
    }
    for relative_path in sorted(expected_files - actual_files):
        errors.append(f"missing file: {relative_path}")
    for relative_path in sorted(actual_files - expected_files):
        errors.append(f"unexpected file: {relative_path}")
    if actual_files == expected_files:
        try:
            actual_merkle_root = compute_tree_merkle_root(source_tree)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"frozen tree Merkle root cannot be computed: {error}")
        else:
            if actual_merkle_root != EXPECTED_TREE_MERKLE_ROOT:
                errors.append(
                    "frozen tree Merkle root mismatch: "
                    f"expected {EXPECTED_TREE_MERKLE_ROOT}, "
                    f"got {actual_merkle_root}"
                )
    _validate_manifest(repo, references, source_tree, errors)

    titles_by_file = dict(CANONICAL_PARTS)
    committed_records: list[dict[str, str]] = []
    records_by_file: dict[str, list[dict[str, str]]] = {}
    for source_range in SOURCE_RANGES:
        filename = source_range[0]
        records = _parse_source_file(
            source_tree,
            source_range,
            titles_by_file.get(filename),
            errors,
        )
        records_by_file[filename] = records
        committed_records.extend(records)
    expected_paragraph_ids = [f"V8-P{number:04d}" for number in range(1, 3864)]
    committed_ids = [record["pid"] for record in committed_records]
    if committed_ids != expected_paragraph_ids or len(committed_ids) != len(set(committed_ids)):
        errors.append("global paragraph anchor coverage mismatch")
    paragraph_text_by_id = {
        record["pid"]: record["text"] for record in committed_records
    }
    measured_non_whitespace = sum(
        not character.isspace()
        for record in committed_records
        for character in record["text"]
    )
    if measured_non_whitespace != EXPECTED_NON_WHITESPACE_CHARS:
        errors.append("committed non-whitespace character count mismatch")

    committed_tables: list[dict[str, object]] = []
    table_by_id: dict[str, dict[str, object]] = {}
    for number in range(1, 118):
        table_id = f"V8-T{number:03d}"
        table = _parse_table_file(source_tree, table_id, paragraph_text_by_id, errors)
        if table is not None:
            committed_tables.append(table)
            table_by_id[table_id] = table
    if [table.get("tid") for table in committed_tables] != [
        f"V8-T{number:03d}" for number in range(1, 118)
    ]:
        errors.append("global table ID coverage mismatch")
    for filename, start, end, table_start, table_end in SOURCE_RANGES:
        expected_table_ids = (
            []
            if table_start is None or table_end is None
            else _ids_between(table_start, table_end, "table")
        )
        actual_table_ids = []
        for table_id, table in table_by_id.items():
            paragraph_ids = table.get("paragraph_ids")
            if not isinstance(paragraph_ids, list) or not paragraph_ids:
                continue
            try:
                first_number = _paragraph_number(paragraph_ids[0])
            except (ValueError, IndexError):
                continue
            if _paragraph_number(start) <= first_number <= _paragraph_number(end):
                actual_table_ids.append(table_id)
        if actual_table_ids != expected_table_ids:
            errors.append(f"table range mismatch: {filename}")

    for relative_path in sorted(expected_files & actual_files):
        content = _read_text(source_tree / relative_path, relative_path, errors)
        if content is not None:
            _source_sha_line(content, relative_path, errors)
    _validate_indexes(source_tree, committed_records, errors)
    if source_docx is not None:
        _compare_source_docx(
            Path(source_docx), committed_records, committed_tables, errors
        )
    return list(dict.fromkeys(errors))


def _load_release_support(repo: Path):
    generator_path = (
        Path(repo)
        / "skills/crossframe-promax/scripts/"
        "generate_crossframe_promax_v8_full_source.py"
    )
    if not generator_path.is_file():
        raise RuntimeError(f"canonical generator missing: {generator_path}")
    module_name = "promax_v8_release_support_" + hashlib.sha256(
        str(generator_path).encode("utf-8")
    ).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(module_name, generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical generator: {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def check_repository(
    repo: Path, source_docx: Path | None = None
) -> list[str]:
    repo = Path(repo).resolve()
    references = repo / "skills/crossframe-promax/references"
    references.mkdir(parents=True, exist_ok=True)
    try:
        release_support = _load_release_support(repo)
    except (OSError, RuntimeError) as error:
        return [str(error)]
    lock_path = references / ".v8-full-source.lock"
    try:
        generation_lock = release_support._acquire_generation_lock(lock_path)
    except release_support.GenerationLockBusy:
        return [f"source generation busy: {lock_path}"]
    except RuntimeError as error:
        return [f"source generation coordination failed: {error}"]
    try:
        try:
            release_support.recover_release_transaction(references)
        except (OSError, RuntimeError, ValueError) as error:
            return [f"source release recovery failed: {error}"]
        return _check_repository_unlocked(repo, source_docx)
    finally:
        release_support._release_generation_lock(generation_lock)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the committed CrossFrame ProMax v8 source snapshot."
    )
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--source-docx", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = check_repository(args.repo, args.source_docx)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("CrossFrame ProMax v8 source snapshot: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
