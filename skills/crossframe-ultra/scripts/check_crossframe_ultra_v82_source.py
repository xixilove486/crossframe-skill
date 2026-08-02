"""Read-only integrity checker and staging helper for the v8.2 authority tree.

The parser and semantic normalizer deliberately live in Task 2's compiler.  This
module only materializes and audits the authority representation produced from
that snapshot; it never treats markdown file names or manifest counts as source
authority.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
from uuid import uuid4


RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
SEMANTIC_NORMALIZATION_VERSION = 1
EXPECTED_PARAGRAPHS = 4631
EXPECTED_NON_WHITESPACE_CHARS = 165690
EXPECTED_TABLES = 122
EXPECTED_DIVISIONS = 20
MAX_SOURCE_DOCX_BYTES = 8 * 1024 * 1024
COMPILER_VERSION = "1.0.0"
TREE_MERKLE_VERSION = 1
TREE_MERKLE_DOMAIN = b"crossframe.ultra.v82.authority-tree-merkle.v1"
# Frozen after the exact v8.2 tree was rendered.  The manifest repeats this
# value for discoverability, but the checker never treats the manifest as the
# only authority for the tree root.
EXPECTED_TREE_MERKLE_ROOT = "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
OLD_ANCHOR_RE = re.compile(r"\bV8-[PT]\d{4}\b")
PARAGRAPH_MARKER_RE = re.compile(
    r"^<!-- source-paragraph:(V82-P\d{4}) style=([^>]*) -->$", re.MULTILINE
)
CANONICAL_BLOCK_RE = re.compile(
    r"<!-- canonical-records:start -->\n```json\n(.*?)\n```\n<!-- canonical-records:end -->",
    re.DOTALL,
)
TABLE_ROWS_BLOCK_RE = re.compile(
    r"<!-- table-rows:start -->\n```json\n(.*?)\n```\n<!-- table-rows:end -->",
    re.DOTALL,
)
TABLE_CELLS_BLOCK_RE = re.compile(
    r"<!-- cell-paragraph-anchors:start -->\n```json\n(.*?)\n```\n<!-- cell-paragraph-anchors:end -->",
    re.DOTALL,
)

ROOT_RELATIVE = Path("skills/crossframe-ultra")
REFERENCES_RELATIVE = ROOT_RELATIVE / "references"
SOURCE_TREE_RELATIVE = REFERENCES_RELATIVE / "v8.2-full-source"
MANIFEST_RELATIVE = REFERENCES_RELATIVE / "source-manifest.json"
LEGACY_TREE_RELATIVE = REFERENCES_RELATIVE / "v8.2-source"

# The envelope is intentionally separate from the twenty top-level divisions.
# Keeping this table here makes the checker independent of mutable manifest
# counts while still using Task 2 for paragraph/table extraction.
SOURCE_RANGES: tuple[dict[str, object], ...] = (
    {
        "file": "00-source-envelope.md",
        "title": "Front matter",
        "paragraph_start": "V82-P0001",
        "paragraph_end": "V82-P0349",
        "table_start": "V82-T001",
        "table_end": "V82-T001",
        "role": "source-envelope",
    },
    {
        "file": "01-guide.md",
        "title": "第一部分　导读",
        "paragraph_start": "V82-P0350",
        "paragraph_end": "V82-P0423",
        "table_start": "V82-T002",
        "table_end": "V82-T003",
        "role": "division",
    },
    {
        "file": "02-boundary-method.md",
        "title": "第二部分　边界与方法",
        "paragraph_start": "V82-P0424",
        "paragraph_end": "V82-P0522",
        "table_start": "V82-T004",
        "table_end": "V82-T005",
        "role": "division",
    },
    {
        "file": "03-universal-grammar.md",
        "title": "第三部分　通用结构语法",
        "paragraph_start": "V82-P0523",
        "paragraph_end": "V82-P0584",
        "table_start": None,
        "table_end": None,
        "role": "division",
    },
    {
        "file": "04-root-assumptions.md",
        "title": "第四部分　根假设与推论",
        "paragraph_start": "V82-P0585",
        "paragraph_end": "V82-P0862",
        "table_start": "V82-T006",
        "table_end": "V82-T011",
        "role": "division",
    },
    {
        "file": "05-scale-circle-transformation.md",
        "title": "第五部分　跨尺度与跨圈层变换",
        "paragraph_start": "V82-P0863",
        "paragraph_end": "V82-P1082",
        "table_start": "V82-T012",
        "table_end": "V82-T016",
        "role": "division",
    },
    {
        "file": "06-operation-evolution.md",
        "title": "第六部分　运转与演化",
        "paragraph_start": "V82-P1083",
        "paragraph_end": "V82-P1159",
        "table_start": "V82-T017",
        "table_end": "V82-T017",
        "role": "division",
    },
    {
        "file": "07-human-structured-world.md",
        "title": "第七部分　人类结构化世界",
        "paragraph_start": "V82-P1160",
        "paragraph_end": "V82-P1267",
        "table_start": "V82-T018",
        "table_end": "V82-T019",
        "role": "division",
    },
    {
        "file": "08-human-state-prototypes.md",
        "title": "第八部分　人类状态原型",
        "paragraph_start": "V82-P1268",
        "paragraph_end": "V82-P1550",
        "table_start": "V82-T020",
        "table_end": "V82-T029",
        "role": "division",
    },
    {
        "file": "09-actor-state-personality.md",
        "title": "第九部分　行动者状态与人格假设",
        "paragraph_start": "V82-P1551",
        "paragraph_end": "V82-P1739",
        "table_start": "V82-T030",
        "table_end": "V82-T035",
        "role": "division",
    },
    {
        "file": "10-multicircle-joint-state.md",
        "title": "第十部分　多圈层对象与联合状态",
        "paragraph_start": "V82-P1740",
        "paragraph_end": "V82-P1930",
        "table_start": "V82-T036",
        "table_end": "V82-T041",
        "role": "division",
    },
    {
        "file": "11-event-dynamic-inference.md",
        "title": "第十一部分　事件驱动的动态推演",
        "paragraph_start": "V82-P1931",
        "paragraph_end": "V82-P2131",
        "table_start": "V82-T042",
        "table_end": "V82-T047",
        "role": "division",
    },
    {
        "file": "12-conditional-forecast-choice.md",
        "title": "第十二部分　条件前瞻与有限选择",
        "paragraph_start": "V82-P2132",
        "paragraph_end": "V82-P2348",
        "table_start": "V82-T048",
        "table_end": "V82-T055",
        "role": "division",
    },
    {
        "file": "13-interfaces-tools.md",
        "title": "第十三部分　接口与工具",
        "paragraph_start": "V82-P2349",
        "paragraph_end": "V82-P2600",
        "table_start": "V82-T056",
        "table_end": "V82-T063",
        "role": "division",
    },
    {
        "file": "14-normative-selection.md",
        "title": "第十四部分　规范选择",
        "paragraph_start": "V82-P2601",
        "paragraph_end": "V82-P2667",
        "table_start": None,
        "table_end": None,
        "role": "division",
    },
    {
        "file": "15-intervention-applications.md",
        "title": "第十五部分　干涉与应用",
        "paragraph_start": "V82-P2668",
        "paragraph_end": "V82-P2776",
        "table_start": None,
        "table_end": None,
        "role": "division",
    },
    {
        "file": "16-governance.md",
        "title": "第十六部分　治理",
        "paragraph_start": "V82-P2777",
        "paragraph_end": "V82-P2905",
        "table_start": None,
        "table_end": None,
        "role": "division",
    },
    {
        "file": "17-appendix-a-human-variable-cards.md",
        "title": "附录A　人类变量接口卡册",
        "paragraph_start": "V82-P2906",
        "paragraph_end": "V82-P4477",
        "table_start": "V82-T064",
        "table_end": "V82-T119",
        "role": "division",
    },
    {
        "file": "18-appendix-b-numbering-terms.md",
        "title": "附录B　编号体系与术语总表",
        "paragraph_start": "V82-P4478",
        "paragraph_end": "V82-P4572",
        "table_start": "V82-T120",
        "table_end": "V82-T120",
        "role": "division",
    },
    {
        "file": "19-appendix-c-revisions.md",
        "title": "附录C　版本修订记录",
        "paragraph_start": "V82-P4573",
        "paragraph_end": "V82-P4586",
        "table_start": "V82-T121",
        "table_end": "V82-T121",
        "role": "division",
    },
    {
        "file": "20-appendix-d-common-kernel-mapping.md",
        "title": "附录D　双文本共同内核与映射",
        "paragraph_start": "V82-P4587",
        "paragraph_end": "V82-P4631",
        "table_start": "V82-T122",
        "table_end": "V82-T122",
        "role": "division",
    },
)

DIVISION_RANGES = SOURCE_RANGES[1:]
INDEX_FILES = (
    "00-index.md",
    "00-heading-index.md",
    "00-term-index.md",
    "00-table-index.md",
)
SECTION_FILES = tuple(item["file"] for item in SOURCE_RANGES)
EXPECTED_TREE_FILES = frozenset(
    INDEX_FILES
    + SECTION_FILES
    + tuple(f"tables/V82-T{number:03d}.md" for number in range(1, EXPECTED_TABLES + 1))
)
HEADING_STYLES = frozenset(
    {
        "CoverTitle",
        "CoverVer",
        "CoverSub",
        "CoverDate",
        "FrontHeading",
        "PartTitle",
        "SecH2",
        "SecH3",
    }
)
CONCEPT_STYLES = HEADING_STYLES | {"CardLabel"}

_TASK2_COMPILER = None


def _load_task2_compiler():
    global _TASK2_COMPILER
    if _TASK2_COMPILER is not None:
        return _TASK2_COMPILER
    path = Path(__file__).resolve().with_name("generate_crossframe_ultra_v82_source.py")
    spec = importlib.util.spec_from_file_location("ultra_v82_task2_compiler", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load Task2 compiler: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _TASK2_COMPILER = module
    return module


def _compiler_path() -> Path:
    return Path(__file__).resolve().with_name("generate_crossframe_ultra_v82_source.py")


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _pretty_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)


def _sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(_read_regular_file(path))


def _is_reparse_or_link(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _assert_no_link_ancestors(path: Path, stop: Path) -> None:
    """Reject links in every existing ancestor without resolving user paths."""
    path = Path(os.path.abspath(path))
    stop = Path(os.path.abspath(stop))
    try:
        path.relative_to(stop)
    except ValueError as error:
        raise ValueError(f"path escapes repository: {path}") from error
    current = path
    ancestors: list[Path] = []
    while True:
        ancestors.append(current)
        if current == stop:
            break
        parent = current.parent
        if parent == current:
            raise ValueError(f"repository ancestor not reached: {stop}")
        current = parent
    for item in reversed(ancestors):
        if item.exists() and _is_reparse_or_link(item):
            raise ValueError(f"path contains symlink or reparse point: {item}")


def _safe_repo(repo: Path) -> Path:
    repo = Path(os.path.abspath(repo))
    if _is_reparse_or_link(repo):
        raise ValueError(f"repository root is a symlink or reparse point: {repo}")
    if not repo.is_dir():
        raise ValueError(f"repository root is not a directory: {repo}")
    return repo


def _read_regular_file(path: Path) -> bytes:
    path = Path(path)
    if _is_reparse_or_link(path):
        raise ValueError(f"file is a symlink or reparse point: {path}")
    metadata_before = os.lstat(path)
    if not stat.S_ISREG(metadata_before.st_mode):
        raise ValueError(f"file is not regular: {path}")
    with path.open("rb") as handle:
        payload = handle.read()
    metadata_after = os.lstat(path)
    if (
        metadata_before.st_dev,
        metadata_before.st_ino,
        metadata_before.st_size,
    ) != (
        metadata_after.st_dev,
        metadata_after.st_ino,
        metadata_after.st_size,
    ):
        raise ValueError(f"file changed while being read: {path}")
    return payload


def _read_bounded_source_docx(path: Path) -> bytes:
    metadata = os.lstat(path)
    if metadata.st_size > MAX_SOURCE_DOCX_BYTES:
        raise ValueError(
            f"source DOCX exceeds safety limit: {metadata.st_size} > {MAX_SOURCE_DOCX_BYTES}"
        )
    payload = _read_regular_file(path)
    if len(payload) > MAX_SOURCE_DOCX_BYTES:
        raise ValueError("source DOCX grew beyond safety limit while being read")
    return payload


def _walk_regular_tree(root: Path) -> tuple[dict[str, bytes], list[str]]:
    root = Path(root)
    errors: list[str] = []
    files: dict[str, bytes] = {}
    if not root.exists():
        return files, [f"source tree does not exist: {root}"]
    if _is_reparse_or_link(root):
        return files, [f"source tree root is a symlink or reparse point: {root}"]
    if not root.is_dir():
        return files, [f"source tree is not a directory: {root}"]
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as error:
            errors.append(f"cannot scan source tree {directory}: {error}")
            continue
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                if _is_reparse_or_link(path):
                    errors.append(f"source tree contains symlink or reparse point: {relative}")
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files[relative] = _read_regular_file(path)
                else:
                    errors.append(f"source tree contains non-regular entry: {relative}")
            except (OSError, ValueError) as error:
                errors.append(f"cannot inspect source tree entry {relative}: {error}")
    return files, list(dict.fromkeys(errors))


def _anchor_number(anchor: str, kind: str) -> int:
    prefix = "V82-P" if kind == "paragraph" else "V82-T"
    pattern = rf"^{prefix}(\d+)$"
    match = re.fullmatch(pattern, anchor)
    if not match:
        raise ValueError(f"invalid {kind} anchor: {anchor!r}")
    return int(match.group(1))


def _anchors_between(start: str | None, end: str | None, kind: str) -> tuple[str, ...]:
    if start is None or end is None:
        return ()
    return tuple(
        f"V82-P{number:04d}" if kind == "paragraph" else f"V82-T{number:03d}"
        for number in range(_anchor_number(start, kind), _anchor_number(end, kind) + 1)
    )


def _expected_manifest_paths() -> tuple[str, ...]:
    return tuple(sorted(f"v8.2-full-source/{path}" for path in EXPECTED_TREE_FILES))


def _tree_merkle_root(files: Mapping[str, bytes]) -> str:
    """Compute a deterministic, domain-separated binary Merkle root."""
    paths = sorted(files)
    if not paths:
        raise ValueError("source tree Merkle root cannot cover an empty tree")

    def digest(*parts: bytes) -> bytes:
        value = sha256()
        for part in parts:
            value.update(part)
        return value.digest()

    level = []
    for relative in paths:
        path_bytes = relative.encode("utf-8")
        content = files[relative]
        level.append(
            digest(
                TREE_MERKLE_DOMAIN,
                b"\x00leaf\x00",
                len(path_bytes).to_bytes(4, "big"),
                path_bytes,
                len(content).to_bytes(8, "big"),
                content,
            )
        )
    leaf_count = len(level)
    while len(level) > 1:
        next_level: list[bytes] = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                next_level.append(digest(TREE_MERKLE_DOMAIN, b"\x00odd\x00", level[index]))
            else:
                next_level.append(
                    digest(TREE_MERKLE_DOMAIN, b"\x00node\x00", level[index], level[index + 1])
                )
        level = next_level
    return digest(
        TREE_MERKLE_DOMAIN,
        b"\x00root\x00",
        leaf_count.to_bytes(4, "big"),
        level[0],
    ).hex()


def compute_source_tree_merkle_root(source_tree: Path) -> str:
    files, errors = _walk_regular_tree(Path(source_tree))
    if errors:
        raise ValueError("; ".join(errors))
    return _tree_merkle_root(files)


def _paragraph_dict(paragraph: object) -> dict[str, object]:
    return {
        "ordinal": int(paragraph.ordinal),
        "anchor": str(paragraph.anchor),
        "style": str(paragraph.style),
        "text": str(paragraph.text),
    }


def _table_dict(table: object) -> dict[str, object]:
    return {
        "ordinal": int(table.ordinal),
        "anchor": str(table.anchor),
        "paragraph_ordinals": list(table.paragraph_ordinals),
        "rows": [list(row) for row in table.rows],
        "cell_paragraph_ordinals": [
            [list(cell) for cell in row] for row in table.cell_paragraph_ordinals
        ],
    }


def _snapshot_records(snapshot: object) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    return (
        [_paragraph_dict(item) for item in snapshot.paragraphs],
        [_table_dict(item) for item in snapshot.tables],
    )


def _unit_hash(kind: str, record: Mapping[str, object]) -> str:
    return _sha256_bytes(_canonical_json({"kind": kind, **record}))


def _source_unit_entries(
    paragraphs: Sequence[Mapping[str, object]], tables: Sequence[Mapping[str, object]]
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for record in paragraphs:
        entries.append(
            {
                "unit_id": record["anchor"],
                "kind": "paragraph",
                "ordinal": record["ordinal"],
                "sha256": _unit_hash("paragraph", record),
            }
        )
    for record in tables:
        entries.append(
            {
                "unit_id": record["anchor"],
                "kind": "table",
                "ordinal": record["ordinal"],
                "sha256": _unit_hash("table", record),
            }
        )
    return entries


def _heading_records(paragraphs: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    return [record for record in paragraphs if record["style"] in HEADING_STYLES]


def _concept_records(paragraphs: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    found: dict[tuple[str, str], Mapping[str, object]] = {}
    for record in paragraphs:
        if record["style"] in CONCEPT_STYLES:
            found.setdefault((str(record["style"]), str(record["text"])), record)
    return [found[key] for key in sorted(found)]


def _contract_count(paragraphs: Sequence[Mapping[str, object]]) -> int:
    return sum(
        1
        for record in paragraphs
        if record["style"] in HEADING_STYLES and "合同" in str(record["text"])
    )


def _range_to_json(item: Mapping[str, object]) -> dict[str, object]:
    return {key: item[key] for key in item}


def _expected_file_entries(files: Mapping[str, bytes]) -> list[dict[str, object]]:
    return [
        {
            "path": f"v8.2-full-source/{relative}",
            "sha256": _sha256_bytes(files[relative]),
            "size": len(files[relative]),
        }
        for relative in sorted(files)
    ]


def _manifest_payload(
    snapshot: object,
    files: Mapping[str, bytes],
    *,
    compiler_sha256: str,
) -> dict[str, object]:
    paragraphs, tables = _snapshot_records(snapshot)
    concepts = _concept_records(paragraphs)
    headings = _heading_records(paragraphs)
    source_units = _source_unit_entries(paragraphs, tables)
    divisions = [_range_to_json(item) for item in DIVISION_RANGES]
    ranges = [_range_to_json(item) for item in SOURCE_RANGES]
    division_records = []
    for item in DIVISION_RANGES:
        table_start = item.get("table_start")
        table_end = item.get("table_end")
        division_records.append(
            {
                "slug": str(item["file"]).removesuffix(".md"),
                "title": item["title"],
                "start_ordinal": _anchor_number(str(item["paragraph_start"]), "paragraph"),
                "end_ordinal": _anchor_number(str(item["paragraph_end"]), "paragraph"),
                "table_ordinals": [
                    _anchor_number(anchor, "table")
                    for anchor in _anchors_between(
                        str(table_start) if table_start is not None else None,
                        str(table_end) if table_end is not None else None,
                        "table",
                    )
                ],
            }
        )
    return {
        "schema_id": "crossframe.ultra.v8.2.source-manifest",
        "schema_version": 1,
        "framework_version": "v8.2",
        "framework_revision": "v8.2",
        "raw_sha256": snapshot.raw_sha256,
        "semantic_sha256": snapshot.semantic_sha256,
        "semantic_normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "paragraph_count": len(paragraphs),
        "heading_count": len(headings),
        "table_count": len(tables),
        "concept_count": len(concepts),
        "contract_count": _contract_count(paragraphs),
        "source_unit_count": len(source_units),
        "non_whitespace_chars": snapshot.non_whitespace_chars,
        "compiler_version": COMPILER_VERSION,
        "compiler": {
            "version": COMPILER_VERSION,
            "path": "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py",
            "sha256": compiler_sha256,
        },
        "source_ranges": ranges,
        "division_ranges": divisions,
        "divisions": division_records,
        "source_units": source_units,
        "files": _expected_file_entries(files),
        "source_tree_merkle_root": _tree_merkle_root(files),
        "source_tree_merkle_version": TREE_MERKLE_VERSION,
    }


def _table_for_ordinal(snapshot: object) -> dict[int, dict[str, object]]:
    return {record["ordinal"]: record for record in _snapshot_records(snapshot)[1]}


def _range_records(
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
    item: Mapping[str, object],
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    p_start = _anchor_number(str(item["paragraph_start"]), "paragraph")
    p_end = _anchor_number(str(item["paragraph_end"]), "paragraph")
    p_records = [
        record
        for record in paragraphs
        if p_start <= int(record["ordinal"]) <= p_end
    ]
    t_start = item.get("table_start")
    t_end = item.get("table_end")
    if t_start is None or t_end is None:
        return p_records, []
    low = _anchor_number(str(t_start), "table")
    high = _anchor_number(str(t_end), "table")
    return p_records, [record for record in tables if low <= int(record["ordinal"]) <= high]


def _escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _render_source_file(
    snapshot: object,
    item: Mapping[str, object],
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
) -> bytes:
    p_start = paragraphs[0]["anchor"] if paragraphs else "EMPTY"
    p_end = paragraphs[-1]["anchor"] if paragraphs else "EMPTY"
    title = "CrossFrame Ultra v8.2 Source Envelope" if item["role"] == "source-envelope" else f"CrossFrame Ultra v8.2 {item['title']}"
    table_ids = [str(record["anchor"]) for record in tables]
    lines = [
        f"# {title}",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"Source role: `{item['role']}`",
        f"Paragraph range: `{p_start}`-`{p_end}`",
        f"Paragraph count: `{len(paragraphs)}`",
        f"Tables: `{', '.join(table_ids) if table_ids else 'none'}`",
        "",
        "## Source Paragraphs",
        "",
    ]
    for record in paragraphs:
        lines.append(
            f"<!-- source-paragraph:{record['anchor']} style={record['style']} -->"
        )
        lines.append(str(record["text"]))
        lines.append("")
    payload = {"paragraphs": list(paragraphs), "tables": list(tables)}
    lines.extend(
        [
            "## Canonical Records",
            "",
            "<!-- canonical-records:start -->",
            "```json",
            _pretty_json(payload),
            "```",
            "<!-- canonical-records:end -->",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _render_table_file(snapshot: object, table: Mapping[str, object]) -> bytes:
    rows = table["rows"]
    cells = table["cell_paragraph_ordinals"]
    lines = [
        f"# CrossFrame Ultra v8.2 Table {table['anchor']}",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"Table ID: `{table['anchor']}`",
        "Source paragraph anchors: "
        + (", ".join(f"`V82-P{n:04d}`" for n in table["paragraph_ordinals"]) or "none"),
        f"Row count: `{len(rows)}`",
        f"Column count: `{max((len(row) for row in rows), default=0)}`",
        "",
        "## Rows",
        "",
    ]
    if rows:
        width = max(len(row) for row in rows)
        lines.append("| " + " | ".join(f"column {i + 1}" for i in range(width)) + " |")
        lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
        for row in rows:
            padded = list(row) + [""] * (width - len(row))
            lines.append("| " + " | ".join(_escape_markdown_cell(str(value)) for value in padded) + " |")
    lines.extend(
        [
            "",
            "<!-- table-rows:start -->",
            "```json",
            _pretty_json(rows),
            "```",
            "<!-- table-rows:end -->",
            "",
            "## Cell Paragraph Anchors",
            "",
            "<!-- cell-paragraph-anchors:start -->",
            "```json",
            _pretty_json(cells),
            "```",
            "<!-- cell-paragraph-anchors:end -->",
            "",
            "## Canonical Structure",
            "",
            "<!-- canonical-records:start -->",
            "```json",
            _pretty_json(table),
            "```",
            "<!-- canonical-records:end -->",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _source_file_for_paragraph(ordinal: int) -> str:
    for item in SOURCE_RANGES:
        if _anchor_number(str(item["paragraph_start"]), "paragraph") <= ordinal <= _anchor_number(str(item["paragraph_end"]), "paragraph"):
            return str(item["file"])
    raise ValueError(f"paragraph ordinal outside fixed ranges: {ordinal}")


def _render_index_files(snapshot: object, paragraphs: list[dict[str, object]], tables: list[dict[str, object]]) -> dict[str, bytes]:
    lines = [
        "# CrossFrame Ultra v8.2 Full Source Index",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"Semantic normalization version: `{SEMANTIC_NORMALIZATION_VERSION}`",
        f"Paragraph count: `{len(paragraphs)}`",
        f"Heading count: `{len(_heading_records(paragraphs))}`",
        f"Table count: `{len(tables)}`",
        f"Concept count: `{len(_concept_records(paragraphs))}`",
        f"Contract count: `{_contract_count(paragraphs)}`",
        f"Source-unit count: `{len(paragraphs) + len(tables)}`",
        "",
        "| file | title | paragraph range | paragraph count | tables |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for item in SOURCE_RANGES:
        p_start = str(item["paragraph_start"])
        p_end = str(item["paragraph_end"])
        p_count = _anchor_number(p_end, "paragraph") - _anchor_number(p_start, "paragraph") + 1
        t_start, t_end = item.get("table_start"), item.get("table_end")
        table_text = ""
        if t_start is not None and t_end is not None:
            table_text = ", ".join(_anchors_between(str(t_start), str(t_end), "table"))
        lines.append(
            f"| [{item['file']}]({item['file']}) | {item['title']} | `{p_start}-{p_end}` | `{p_count}` | {table_text} |"
        )
    index = "\n".join(lines) + "\n"

    heading_lines = [
        "# CrossFrame Ultra v8.2 Heading Index",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        "",
        "| paragraph id | style | text | source file |",
        "| --- | --- | --- | --- |",
    ]
    for record in _heading_records(paragraphs):
        anchor = str(record["anchor"])
        source_file = _source_file_for_paragraph(int(record["ordinal"]))
        text = str(record["text"]).replace("|", "\\|").replace("\n", "<br>")
        heading_lines.append(
            f"| [{anchor}]({source_file}) | `{record['style']}` | {text} | [{source_file}]({source_file}) |"
        )
    heading_index = "\n".join(heading_lines) + "\n"

    concept_lines = [
        "# CrossFrame Ultra v8.2 Exact Source Form Locator",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        "",
        "## Exact Source Form Locator",
        "",
        "This index groups exact styled source forms without adding definitions.",
        "",
        "| exact source form | style | source anchors |",
        "| --- | --- | --- |",
    ]
    for record in _concept_records(paragraphs):
        text = str(record["text"]).replace("|", "\\|").replace("\n", "<br>")
        same = [
            item
            for item in paragraphs
            if item["style"] == record["style"] and item["text"] == record["text"]
        ]
        links = ", ".join(
            f"[{item['anchor']}]({_source_file_for_paragraph(int(item['ordinal']))})"
            for item in same
        )
        concept_lines.append(f"| {text} | `{record['style']}` | {links} |")
    term_index = "\n".join(concept_lines) + "\n"

    table_lines = [
        "# CrossFrame Ultra v8.2 Table Index",
        "",
        f"Raw SHA256: `{snapshot.raw_sha256}`",
        f"Semantic SHA256: `{snapshot.semantic_sha256}`",
        f"Table count: `{len(tables)}`",
        "",
        "| table | paragraph anchors | rows | columns | file |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for table in tables:
        table_lines.append(
            f"| `{table['anchor']}` | `{len(table['paragraph_ordinals'])}` | `{len(table['rows'])}` | `{max((len(row) for row in table['rows']), default=0)}` | [{table['anchor']}](tables/{table['anchor']}.md) |"
        )
    table_index = "\n".join(table_lines) + "\n"
    return {
        "00-index.md": index.encode("utf-8"),
        "00-heading-index.md": heading_index.encode("utf-8"),
        "00-term-index.md": term_index.encode("utf-8"),
        "00-table-index.md": table_index.encode("utf-8"),
    }


def _render_authority_files(snapshot: object) -> dict[str, bytes]:
    paragraphs, tables = _snapshot_records(snapshot)
    files = _render_index_files(snapshot, paragraphs, tables)
    table_map = {int(record["ordinal"]): record for record in tables}
    for item in SOURCE_RANGES:
        p_records, t_records = _range_records(paragraphs, tables, item)
        files[str(item["file"])] = _render_source_file(snapshot, item, p_records, t_records)
    for ordinal, table in sorted(table_map.items()):
        files[f"tables/V82-T{ordinal:03d}.md"] = _render_table_file(snapshot, table)
    if set(files) != set(EXPECTED_TREE_FILES):
        raise ValueError("authority renderer produced an unexpected file inventory")
    return files


def _write_tree_files(stage: Path, files: Mapping[str, bytes]) -> None:
    stage.mkdir(parents=True, exist_ok=False)
    for relative, content in sorted(files.items()):
        target = stage / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if _is_reparse_or_link(target.parent):
            raise ValueError(f"staging parent is a symlink or reparse point: {target.parent}")
        target.write_bytes(content)


def generate_authority_tree(repo: Path, source_docx: Path) -> Path:
    """Compile and atomically promote a full v8.2 tree.

    This helper is intentionally separate from the read-only CLI.  It uses
    Task 2's snapshot compiler and is useful for the one-time source promotion.
    """
    repo = _safe_repo(Path(repo))
    source_docx = Path(os.path.abspath(source_docx))
    _assert_no_link_ancestors(source_docx, source_docx.anchor and Path(source_docx.anchor) or source_docx.parent)
    source_bytes = _read_bounded_source_docx(source_docx)
    if _sha256_bytes(source_bytes) != RAW_SHA256:
        raise ValueError(f"raw SHA256 mismatch: expected {RAW_SHA256}, got {_sha256_bytes(source_bytes)}")
    compiler = _load_task2_compiler()
    snapshot = compiler.build_v82_snapshot(source_bytes)
    snapshot_errors = compiler.validate_v82_snapshot(snapshot)
    if snapshot_errors:
        raise ValueError("invalid v8.2 snapshot: " + "; ".join(snapshot_errors))
    refs = repo / REFERENCES_RELATIVE
    _assert_no_link_ancestors(refs, repo)
    refs.mkdir(parents=True, exist_ok=True)
    live = repo / SOURCE_TREE_RELATIVE
    manifest_path = repo / MANIFEST_RELATIVE
    for path in (refs, live.parent, manifest_path.parent):
        _assert_no_link_ancestors(path, repo)
    stage = refs / f".v8.2-full-source.stage-{uuid4().hex}"
    files = _render_authority_files(snapshot)
    _write_tree_files(stage, files)
    compiler_sha = _sha256_path(_compiler_path())
    manifest = _manifest_payload(snapshot, files, compiler_sha256=compiler_sha)
    manifest_stage = refs / f".source-manifest.stage-{uuid4().hex}.json"
    manifest_stage.write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    backup = refs / f".v8.2-full-source.backup-{uuid4().hex}"
    old_manifest = refs / f".source-manifest.backup-{uuid4().hex}.json"
    try:
        if live.exists():
            os.replace(live, backup)
        os.replace(stage, live)
        if manifest_path.exists():
            os.replace(manifest_path, old_manifest)
        os.replace(manifest_stage, manifest_path)
    except Exception:
        if live.exists() and not stage.exists():
            try:
                os.replace(live, stage)
            except OSError:
                pass
        if backup.exists() and not live.exists():
            os.replace(backup, live)
        if old_manifest.exists() and not manifest_path.exists():
            os.replace(old_manifest, manifest_path)
        raise
    finally:
        for leftover in (stage, manifest_stage, backup, old_manifest):
            if leftover.exists():
                if leftover.is_dir():
                    shutil.rmtree(leftover)
                else:
                    leftover.unlink()
    return live


def _read_json_bytes(payload: bytes, label: str, errors: list[str]) -> object | None:
    try:
        text = payload.decode("utf-8")
        if text.startswith("\ufeff"):
            raise ValueError("UTF-8 BOM is forbidden")
        return json.loads(text)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        errors.append(f"{label}: invalid JSON: {error}")
        return None


def _canonical_block(content: str, label: str, errors: list[str]) -> object | None:
    matches = list(CANONICAL_BLOCK_RE.finditer(content))
    if len(matches) != 1:
        errors.append(f"{label}: canonical record block count is not one")
        return None
    try:
        return json.loads(matches[0].group(1))
    except json.JSONDecodeError as error:
        errors.append(f"{label}: canonical records JSON is invalid: {error}")
        return None


def _parse_visible_paragraphs(content: str, label: str, errors: list[str]) -> list[dict[str, str]]:
    matches = list(PARAGRAPH_MARKER_RE.finditer(content))
    records: list[dict[str, str]] = []
    canonical_start = content.find("## Canonical Records")
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else (canonical_start if canonical_start >= 0 else len(content))
        text = content[match.end() : end]
        if text.startswith("\n"):
            text = text[1:]
        text = text.rstrip("\n")
        records.append({"anchor": match.group(1), "style": match.group(2), "text": text})
    if not matches:
        errors.append(f"{label}: source paragraph anchors are missing")
    return records


def _validate_section_file(
    content: str,
    item: Mapping[str, object],
    expected_paragraphs: Sequence[Mapping[str, object]],
    expected_tables: Sequence[Mapping[str, object]],
    raw_sha: str,
    semantic_sha: str,
    errors: list[str],
) -> dict[str, object] | None:
    label = str(item["file"])
    if f"Raw SHA256: `{raw_sha}`" not in content:
        errors.append(f"{label}: raw SHA256 backlink mismatch")
    if f"Semantic SHA256: `{semantic_sha}`" not in content:
        errors.append(f"{label}: semantic SHA256 backlink mismatch")
    payload = _canonical_block(content, label, errors)
    if not isinstance(payload, dict):
        return None
    if set(payload) != {"paragraphs", "tables"}:
        errors.append(f"{label}: canonical record fields are not closed")
        return None
    actual_paragraphs = payload.get("paragraphs")
    actual_tables = payload.get("tables")
    if actual_paragraphs != list(expected_paragraphs):
        errors.append(f"{label}: canonical paragraph records mismatch")
    if actual_tables != list(expected_tables):
        errors.append(f"{label}: canonical table records mismatch")
    visible = _parse_visible_paragraphs(content, label, errors)
    expected_visible = [
        {"anchor": record["anchor"], "style": record["style"], "text": record["text"]}
        for record in expected_paragraphs
    ]
    if visible != expected_visible:
        errors.append(f"{label}: visible source paragraph records mismatch")
    if item["role"] == "division":
        if not expected_paragraphs or expected_paragraphs[0]["style"] != "PartTitle":
            errors.append(f"{label}: division does not start with a PartTitle paragraph")
        elif expected_paragraphs[0]["text"] != item["title"]:
            errors.append(f"{label}: PartTitle text mismatch")
    return payload


def _parse_markdown_rows(content: str) -> list[list[str]]:
    start = content.find("## Rows\n")
    end = content.find("<!-- table-rows:start -->")
    if start < 0 or end < 0 or end <= start:
        return []
    lines = content[start:end].splitlines()[2:]
    table_lines = [line for line in lines if line.startswith("|")]
    if len(table_lines) < 2:
        return []
    values: list[list[str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        values.append([cell.replace("\\|", "|").replace("<br>", "\n") for cell in cells])
    return values


def _validate_table_file(
    content: str,
    expected: Mapping[str, object],
    raw_sha: str,
    semantic_sha: str,
    errors: list[str],
) -> None:
    label = str(expected["anchor"])
    if f"Raw SHA256: `{raw_sha}`" not in content:
        errors.append(f"{label}: raw SHA256 backlink mismatch")
    if f"Semantic SHA256: `{semantic_sha}`" not in content:
        errors.append(f"{label}: semantic SHA256 backlink mismatch")
    payload = _canonical_block(content, label, errors)
    if payload != dict(expected):
        errors.append(f"{label}: canonical table structure mismatch")
    row_block = list(TABLE_ROWS_BLOCK_RE.finditer(content))
    cell_block = list(TABLE_CELLS_BLOCK_RE.finditer(content))
    if len(row_block) != 1 or len(cell_block) != 1:
        errors.append(f"{label}: table display blocks are missing or duplicated")
        return
    try:
        display_rows = json.loads(row_block[0].group(1))
        display_cells = json.loads(cell_block[0].group(1))
    except json.JSONDecodeError as error:
        errors.append(f"{label}: table display JSON is invalid: {error}")
        return
    if display_rows != expected["rows"]:
        errors.append(f"{label}: displayed table cell order/content mismatch")
    if display_cells != expected["cell_paragraph_ordinals"]:
        errors.append(f"{label}: displayed cell-paragraph binding mismatch")
    if _parse_markdown_rows(content) != [list(row) for row in expected["rows"]]:
        errors.append(f"{label}: markdown rows mismatch")


def _manifest_from_tree(repo: Path, files: Mapping[str, bytes], errors: list[str]) -> dict[str, object] | None:
    manifest_path = repo / MANIFEST_RELATIVE
    try:
        payload = _read_regular_file(manifest_path)
    except (OSError, ValueError) as error:
        errors.append(f"source manifest cannot be read: {error}")
        return None
    value = _read_json_bytes(payload, "source-manifest.json", errors)
    if not isinstance(value, dict):
        errors.append("source-manifest.json root must be an object")
        return None
    return value


def _validate_manifest(
    repo: Path,
    manifest: Mapping[str, object],
    files: Mapping[str, bytes],
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
    errors: list[str],
) -> None:
    required = {
        "schema_id",
        "schema_version",
        "framework_version",
        "framework_revision",
        "raw_sha256",
        "semantic_sha256",
        "semantic_normalization_version",
        "normalization_version",
        "paragraph_count",
        "heading_count",
        "table_count",
        "concept_count",
        "contract_count",
        "source_unit_count",
        "non_whitespace_chars",
        "compiler_version",
        "compiler",
        "source_ranges",
        "division_ranges",
        "divisions",
        "source_units",
        "files",
        "source_tree_merkle_root",
        "source_tree_merkle_version",
    }
    if set(manifest) != required:
        errors.append("source manifest top-level fields are not closed")
    expected_constants = {
        "schema_id": "crossframe.ultra.v8.2.source-manifest",
        "schema_version": 1,
        "framework_version": "v8.2",
        "framework_revision": "v8.2",
        "raw_sha256": RAW_SHA256,
        "semantic_sha256": SEMANTIC_SHA256,
        "semantic_normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "normalization_version": SEMANTIC_NORMALIZATION_VERSION,
        "paragraph_count": len(paragraphs),
        "heading_count": len(_heading_records(paragraphs)),
        "table_count": len(tables),
        "concept_count": len(_concept_records(paragraphs)),
        "contract_count": _contract_count(paragraphs),
        "source_unit_count": len(paragraphs) + len(tables),
        "non_whitespace_chars": sum(
            not character.isspace() for record in paragraphs for character in str(record["text"])
        ),
        "compiler_version": COMPILER_VERSION,
        "source_tree_merkle_version": TREE_MERKLE_VERSION,
    }
    for key, expected in expected_constants.items():
        if manifest.get(key) != expected:
            errors.append(f"source manifest constant mismatch: {key}")
    if manifest.get("source_ranges") != [_range_to_json(item) for item in SOURCE_RANGES]:
        errors.append("source manifest source_ranges mismatch")
    if manifest.get("division_ranges") != [_range_to_json(item) for item in DIVISION_RANGES]:
        errors.append("source manifest division_ranges mismatch")
    expected_divisions = []
    for item in DIVISION_RANGES:
        expected_divisions.append(
            {
                "slug": str(item["file"]).removesuffix(".md"),
                "title": item["title"],
                "start_ordinal": _anchor_number(str(item["paragraph_start"]), "paragraph"),
                "end_ordinal": _anchor_number(str(item["paragraph_end"]), "paragraph"),
                "table_ordinals": [
                    _anchor_number(anchor, "table")
                    for anchor in _anchors_between(
                        str(item["table_start"]) if item.get("table_start") is not None else None,
                        str(item["table_end"]) if item.get("table_end") is not None else None,
                        "table",
                    )
                ],
            }
        )
    if manifest.get("divisions") != expected_divisions:
        errors.append("source manifest divisions mismatch")
    compiler = manifest.get("compiler")
    if not isinstance(compiler, dict) or set(compiler) != {"version", "path", "sha256"}:
        errors.append("source manifest compiler fields are not closed")
    else:
        if compiler.get("version") != COMPILER_VERSION:
            errors.append("source manifest compiler version mismatch")
        if compiler.get("path") != "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py":
            errors.append("source manifest compiler path mismatch")
        try:
            compiler_path = repo / str(compiler["path"])
            _assert_no_link_ancestors(compiler_path, repo)
            compiler_hash = _sha256_path(compiler_path)
            if compiler.get("sha256") != compiler_hash:
                errors.append("source manifest compiler hash mismatch")
        except (OSError, ValueError) as error:
            errors.append(f"cannot verify compiler hash: {error}")
    entries = manifest.get("files")
    expected_entries = _expected_file_entries(files)
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            relative_path = entry.get("path")
            if not isinstance(relative_path, str):
                continue
            pure = PurePosixPath(relative_path)
            if (
                pure.is_absolute()
                or "\\" in relative_path
                or ".." in pure.parts
                or not relative_path.startswith("v8.2-full-source/")
            ):
                errors.append(f"manifest path escapes source tree: {relative_path}")
    if entries != expected_entries:
        errors.append("source manifest file inventory or byte hash mismatch")
    source_units = manifest.get("source_units")
    expected_units = _source_unit_entries(paragraphs, tables)
    if source_units != expected_units:
        errors.append("source manifest source-unit hashes mismatch")
    try:
        root = _tree_merkle_root(files)
        if manifest.get("source_tree_merkle_root") != root:
            errors.append("source tree Merkle root mismatch")
    except ValueError as error:
        errors.append(f"cannot compute source tree Merkle root: {error}")


def _validate_old_anchor_free(payloads: Iterable[tuple[str, bytes]], errors: list[str]) -> None:
    for label, content in payloads:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue
        match = OLD_ANCHOR_RE.search(text)
        if match:
            errors.append(f"old V8-P/V8-T anchor injected: {label}: {match.group(0)}")


def _validate_indexes(
    files: Mapping[str, bytes],
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
    raw_sha: str,
    semantic_sha: str,
    errors: list[str],
) -> None:
    texts: dict[str, str] = {}
    for name in INDEX_FILES:
        try:
            text = files[name].decode("utf-8")
        except (KeyError, UnicodeDecodeError) as error:
            errors.append(f"index {name} cannot be read: {error}")
            continue
        texts[name] = text
        if f"Raw SHA256: `{raw_sha}`" not in text or f"Semantic SHA256: `{semantic_sha}`" not in text:
            errors.append(f"index {name}: source hash backlink mismatch")
    index = texts.get("00-index.md", "")
    for item in SOURCE_RANGES:
        link = f"]({item['file']})"
        if link not in index:
            errors.append(f"index backlink missing: {item['file']}")
    heading = texts.get("00-heading-index.md", "")
    for record in _heading_records(paragraphs):
        anchor = str(record["anchor"])
        source_file = _source_file_for_paragraph(int(record["ordinal"]))
        if f"[{anchor}]({source_file})" not in heading:
            errors.append(f"heading index backlink missing: {anchor}")
    # TOC entries are navigation metadata, not structural headings.
    if re.search(r"\| \[V82-P\d{4}\].*`TOC[123]`", heading):
        errors.append("heading index incorrectly promotes TOC anchors")
    table_index = texts.get("00-table-index.md", "")
    for number in range(1, EXPECTED_TABLES + 1):
        if f"[V82-T{number:03d}](tables/V82-T{number:03d}.md)" not in table_index:
            errors.append(f"table index backlink missing: V82-T{number:03d}")
    term = texts.get("00-term-index.md", "")
    if "## Exact Source Form Locator" not in term:
        errors.append("term index locator is missing")
    for record in _concept_records(paragraphs):
        anchor = str(record["anchor"])
        source_file = _source_file_for_paragraph(int(record["ordinal"]))
        if f"[{anchor}]({source_file})" not in term:
            errors.append(f"term index backlink missing: {anchor}")


def _parse_committed_records(
    repo: Path,
    files: Mapping[str, bytes],
    errors: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    all_paragraphs: list[dict[str, object]] = []
    all_tables: list[dict[str, object]] = []
    for item in SOURCE_RANGES:
        label = str(item["file"])
        content_bytes = files.get(label)
        if content_bytes is None:
            errors.append(f"missing source file: {label}")
            continue
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            errors.append(f"{label}: invalid UTF-8: {error}")
            continue
        p_start = _anchor_number(str(item["paragraph_start"]), "paragraph")
        p_end = _anchor_number(str(item["paragraph_end"]), "paragraph")
        t_start = item.get("table_start")
        t_end = item.get("table_end")
        expected_p = [
            {
                "ordinal": number,
                "anchor": f"V82-P{number:04d}",
                "style": "__UNKNOWN__",
                "text": "__UNKNOWN__",
            }
            for number in range(p_start, p_end + 1)
        ]
        # Section files are parsed independently first.  The style/text values
        # are taken from their canonical records; cross-file sequence checks
        # below then reject duplicate, missing, or reordered anchors.
        payload = _canonical_block(content, label, errors)
        if isinstance(payload, dict) and isinstance(payload.get("paragraphs"), list):
            actual_p = payload["paragraphs"]
        else:
            actual_p = []
        if isinstance(payload, dict) and isinstance(payload.get("tables"), list):
            actual_t = payload["tables"]
        else:
            actual_t = []
        expected_t = []
        if t_start is not None and t_end is not None:
            for number in range(_anchor_number(str(t_start), "table"), _anchor_number(str(t_end), "table") + 1):
                expected_t.append({"ordinal": number, "anchor": f"V82-T{number:03d}"})
        # The full structural comparison is performed against source snapshot
        # when available; here retain only well-shaped records for diagnostics.
        if isinstance(actual_p, list):
            all_paragraphs.extend(record for record in actual_p if isinstance(record, dict))
        if isinstance(actual_t, list):
            all_tables.extend(record for record in actual_t if isinstance(record, dict))
        # Run metadata/marker checks that do not require source text.
        _ = expected_p, expected_t
    return all_paragraphs, all_tables


def _validate_record_structure(
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
    errors: list[str],
) -> None:
    """Recompute source invariants from records, independent of manifest data."""
    expected_paragraphs = [f"V82-P{number:04d}" for number in range(1, EXPECTED_PARAGRAPHS + 1)]
    actual_paragraphs = [str(record.get("anchor")) for record in paragraphs]
    if actual_paragraphs != expected_paragraphs:
        errors.append("paragraph anchors are not a complete continuous V82-P0001-V82-P4631 sequence")
    if len(actual_paragraphs) != len(set(actual_paragraphs)):
        errors.append("duplicate paragraph anchor detected")
    expected_tables = [f"V82-T{number:03d}" for number in range(1, EXPECTED_TABLES + 1)]
    actual_tables = [str(record.get("anchor")) for record in tables]
    if actual_tables != expected_tables:
        errors.append("table anchors are not a complete continuous V82-T001-V82-T122 sequence")
    if len(actual_tables) != len(set(actual_tables)):
        errors.append("duplicate table anchor detected")
    text_by_ordinal: dict[int, str] = {}
    for record in paragraphs:
        try:
            ordinal = int(record["ordinal"])
            text = str(record["text"])
        except (KeyError, TypeError, ValueError):
            errors.append("paragraph record has invalid fields")
            continue
        text_by_ordinal[ordinal] = text
        if record.get("anchor") != f"V82-P{ordinal:04d}":
            errors.append(f"paragraph anchor/ordinal binding mismatch: {record.get('anchor')}")
        if not isinstance(record.get("text"), str) or not isinstance(record.get("style"), str):
            errors.append(f"paragraph {ordinal}: text/style must be strings")
    for table in tables:
        label = str(table.get("anchor", "unknown-table"))
        try:
            ordinal = int(table["ordinal"])
            paragraph_ordinals = tuple(int(value) for value in table["paragraph_ordinals"])
            rows = table["rows"]
            cell_bindings = table["cell_paragraph_ordinals"]
        except (KeyError, TypeError, ValueError):
            errors.append(f"{label}: table record has invalid fields")
            continue
        if table.get("anchor") != f"V82-T{ordinal:03d}":
            errors.append(f"{label}: table anchor/ordinal binding mismatch")
        try:
            flattened = tuple(
                value
                for row in cell_bindings
                for cell in row
                for value in cell
            )
        except TypeError:
            errors.append(f"{label}: cell paragraph binding shape is invalid")
            continue
        if flattened != paragraph_ordinals:
            errors.append(f"{label}: table paragraph anchor binding mismatch")
        if not isinstance(rows, list) or not isinstance(cell_bindings, list) or len(rows) != len(cell_bindings):
            errors.append(f"{label}: row and cell-binding shape mismatch")
            continue
        for row_number, (row, binding_row) in enumerate(zip(rows, cell_bindings, strict=True), start=1):
            if not isinstance(row, list) or not isinstance(binding_row, list) or len(row) != len(binding_row):
                errors.append(f"{label}: row {row_number} and cell-binding shape mismatch")
                continue
            for column_number, (cell_text, binding) in enumerate(zip(row, binding_row, strict=True), start=1):
                try:
                    ids = tuple(int(value) for value in binding)
                except (TypeError, ValueError):
                    errors.append(f"{label}: R{row_number}C{column_number} has invalid paragraph binding")
                    continue
                if any(value not in text_by_ordinal for value in ids):
                    errors.append(f"{label}: R{row_number}C{column_number} references an unknown paragraph ordinal")
                    continue
                expected_text = "\n".join(text_by_ordinal[value] for value in ids)
                if cell_text != expected_text:
                    errors.append(f"{label}: R{row_number}C{column_number} text does not match bound paragraphs")
    # Verify table ownership from fixed source ranges, rather than trusting the
    # division list in the manifest.
    for item in SOURCE_RANGES:
        expected_ids = _anchors_between(item.get("table_start"), item.get("table_end"), "table")
        p_start = _anchor_number(str(item["paragraph_start"]), "paragraph")
        p_end = _anchor_number(str(item["paragraph_end"]), "paragraph")
        actual_ids = []
        for table in tables:
            paragraph_ordinals = table.get("paragraph_ordinals", ())
            if paragraph_ordinals and p_start <= int(paragraph_ordinals[0]) <= p_end:
                actual_ids.append(str(table.get("anchor")))
        if tuple(actual_ids) != expected_ids:
            errors.append(f"table ownership mismatch for {item['file']}")


def _semantic_hash_from_records(
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
) -> str | None:
    try:
        compiler = _load_task2_compiler()
        paragraph_objects = tuple(
            compiler.V82Paragraph(
                ordinal=int(record["ordinal"]),
                anchor=str(record["anchor"]),
                style=str(record["style"]),
                text=str(record["text"]),
            )
            for record in paragraphs
        )
        table_objects = tuple(
            compiler.V82Table(
                ordinal=int(record["ordinal"]),
                anchor=str(record["anchor"]),
                paragraph_ordinals=tuple(int(value) for value in record["paragraph_ordinals"]),
                rows=tuple(tuple(str(value) for value in row) for row in record["rows"]),
                cell_paragraph_ordinals=tuple(
                    tuple(tuple(int(value) for value in cell) for cell in row)
                    for row in record["cell_paragraph_ordinals"]
                ),
            )
            for record in tables
        )
        return _sha256_bytes(compiler.semantic_snapshot_bytes(paragraph_objects, table_objects))
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def _self_integrity(repo: Path) -> tuple[list[str], dict[str, bytes], dict[str, object] | None, list[dict[str, object]], list[dict[str, object]]]:
    errors: list[str] = []
    try:
        repo = _safe_repo(repo)
        _assert_no_link_ancestors(repo / ROOT_RELATIVE, repo)
        source_tree = repo / SOURCE_TREE_RELATIVE
        _assert_no_link_ancestors(source_tree, repo)
    except ValueError as error:
        return [str(error)], {}, None, [], []
    references = repo / REFERENCES_RELATIVE
    if references.is_dir() and not _is_reparse_or_link(references):
        try:
            for entry in os.scandir(references):
                entry_path = Path(entry.path)
                if entry.name.startswith(
                    (
                        ".v8.2-full-source.stage-",
                        ".v8.2-full-source.backup-",
                        ".source-manifest.stage-",
                        ".source-manifest.backup-",
                    )
                ):
                    errors.append(f"incomplete source promotion residue: {entry.name}")
                if _is_reparse_or_link(entry_path):
                    errors.append(f"references contains symlink or reparse point: {entry.name}")
        except OSError as error:
            errors.append(f"cannot inspect references directory: {error}")
    if (repo / LEGACY_TREE_RELATIVE).exists():
        errors.append("legacy v8.2-source tree must not be present")
    files, walk_errors = _walk_regular_tree(source_tree)
    errors.extend(walk_errors)
    actual_paths = set(files)
    missing = sorted(EXPECTED_TREE_FILES - actual_paths)
    extra = sorted(actual_paths - EXPECTED_TREE_FILES)
    errors.extend(f"missing generated file: {path}" for path in missing)
    errors.extend(f"unexpected generated file: {path}" for path in extra)
    if not missing and not extra and not walk_errors:
        try:
            actual_root = _tree_merkle_root(files)
        except ValueError as error:
            errors.append(f"cannot compute frozen source tree Merkle root: {error}")
        else:
            if actual_root != EXPECTED_TREE_MERKLE_ROOT:
                errors.append(
                    "frozen source tree Merkle root mismatch: "
                    f"expected {EXPECTED_TREE_MERKLE_ROOT}, got {actual_root}"
                )
    manifest = _manifest_from_tree(repo, files, errors)
    if manifest is None:
        return list(dict.fromkeys(errors)), files, None, [], []
    # Parse canonical payloads and collect records before validating indexes.
    paragraphs, tables = _parse_committed_records(repo, files, errors)
    _validate_record_structure(paragraphs, tables, errors)
    semantic_from_records = _semantic_hash_from_records(paragraphs, tables)
    if semantic_from_records != SEMANTIC_SHA256:
        errors.append(
            "committed semantic SHA256 mismatch: "
            f"expected {SEMANTIC_SHA256}, got {semantic_from_records}"
        )
    # Every expected paragraph/table must occur once, in source order.  The
    # manifest cannot enlarge or shrink this authoritative expected range.
    expected_p_ids = [f"V82-P{number:04d}" for number in range(1, EXPECTED_PARAGRAPHS + 1)]
    actual_p_ids = [str(record.get("anchor")) for record in paragraphs]
    if actual_p_ids != expected_p_ids:
        errors.append("paragraph anchors are not a complete continuous V82-P0001-V82-P4631 sequence")
    if len(actual_p_ids) != len(set(actual_p_ids)):
        errors.append("duplicate paragraph anchor detected")
    expected_t_ids = [f"V82-T{number:03d}" for number in range(1, EXPECTED_TABLES + 1)]
    actual_t_ids = [str(record.get("anchor")) for record in tables]
    if actual_t_ids != expected_t_ids:
        errors.append("table anchors are not a complete continuous V82-T001-V82-T122 sequence")
    if len(actual_t_ids) != len(set(actual_t_ids)):
        errors.append("duplicate table anchor detected")
    # Validate each section against fixed range anchors and machine-readable
    # records; this does not use manifest counts.
    p_by_id = {str(record.get("anchor")): record for record in paragraphs}
    t_by_id = {str(record.get("anchor")): record for record in tables}
    for item in SOURCE_RANGES:
        expected_p = [p_by_id[anchor] for anchor in _anchors_between(str(item["paragraph_start"]), str(item["paragraph_end"]), "paragraph") if anchor in p_by_id]
        expected_t = [t_by_id[anchor] for anchor in _anchors_between(item.get("table_start"), item.get("table_end"), "table") if anchor in t_by_id]
        content_bytes = files.get(str(item["file"]))
        if content_bytes is None:
            continue
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            continue
        _validate_section_file(content, item, expected_p, expected_t, RAW_SHA256, SEMANTIC_SHA256, errors)
    for number in range(1, EXPECTED_TABLES + 1):
        record = t_by_id.get(f"V82-T{number:03d}")
        content = files.get(f"tables/V82-T{number:03d}.md")
        if record is not None and content is not None:
            try:
                _validate_table_file(content.decode("utf-8"), record, RAW_SHA256, SEMANTIC_SHA256, errors)
            except (UnicodeDecodeError, KeyError, TypeError, ValueError, IndexError) as error:
                errors.append(f"V82-T{number:03d}: malformed table record: {error}")
    _validate_indexes(files, paragraphs, tables, RAW_SHA256, SEMANTIC_SHA256, errors)
    _validate_old_anchor_free(((name, payload) for name, payload in files.items()), errors)
    try:
        _validate_old_anchor_free(
            (("source-manifest.json", _read_regular_file(repo / MANIFEST_RELATIVE)),),
            errors,
        )
    except (OSError, ValueError):
        pass
    _validate_manifest(repo, manifest, files, paragraphs, tables, errors)
    return list(dict.fromkeys(errors)), files, manifest, paragraphs, tables


def validate_committed_source_tree(repo: Path) -> list[str]:
    """Validate the committed authority tree without reading the DOCX."""
    try:
        errors, _files, _manifest, _paragraphs, _tables = _self_integrity(Path(repo))
    except Exception as error:
        return [f"source-tree validation failure: {error}"]
    return errors


def _snapshot_from_source_bytes(source_bytes: bytes) -> object:
    compiler = _load_task2_compiler()
    return compiler.build_v82_snapshot(source_bytes)


def validate_against_docx(repo: Path, source_docx: Path) -> list[str]:
    """Validate self-integrity and exact raw/semantic/source-unit identity."""
    try:
        errors, _files, _manifest, committed_paragraphs, committed_tables = _self_integrity(Path(repo))
    except Exception as error:
        return [f"source-tree validation failure: {error}"]
    source_docx = Path(os.path.abspath(source_docx))
    try:
        _assert_no_link_ancestors(source_docx, source_docx.parent)
        source_bytes = _read_bounded_source_docx(source_docx)
    except (OSError, ValueError) as error:
        errors.append(f"source DOCX cannot be read safely: {error}")
        return list(dict.fromkeys(errors))
    raw = _sha256_bytes(source_bytes)
    if raw != RAW_SHA256:
        errors.append(f"raw SHA256 mismatch: expected {RAW_SHA256}, got {raw}")
        return list(dict.fromkeys(errors))
    try:
        snapshot = _snapshot_from_source_bytes(source_bytes)
    except Exception as error:  # compiler owns detailed source parsing errors
        errors.append(f"cannot parse source DOCX: {error}")
        return list(dict.fromkeys(errors))
    compiler = _load_task2_compiler()
    snapshot_errors = compiler.validate_v82_snapshot(snapshot)
    errors.extend(f"source snapshot: {error}" for error in snapshot_errors)
    if snapshot.semantic_sha256 != SEMANTIC_SHA256:
        errors.append(f"semantic SHA256 mismatch: expected {SEMANTIC_SHA256}, got {snapshot.semantic_sha256}")
    source_paragraphs, source_tables = _snapshot_records(snapshot)
    if committed_paragraphs != source_paragraphs:
        mismatch = next(
            (
                str(source.get("anchor"))
                for source, committed in zip(source_paragraphs, committed_paragraphs)
                if source != committed
            ),
            "count",
        )
        errors.append(f"source paragraph mismatch: {mismatch}")
    if committed_tables != source_tables:
        mismatch = next(
            (
                str(source.get("anchor"))
                for source, committed in zip(source_tables, committed_tables)
                if source != committed
            ),
            "count",
        )
        errors.append(f"source table mismatch: {mismatch}")
    expected_semantic = _sha256_bytes(compiler.semantic_snapshot_bytes(snapshot.paragraphs, snapshot.tables))
    if expected_semantic != SEMANTIC_SHA256:
        errors.append(f"source semantic snapshot mismatch: expected {SEMANTIC_SHA256}, got {expected_semantic}")
    expected_units = _source_unit_entries(source_paragraphs, source_tables)
    # Re-read manifest to compare source units even if committed records were
    # malformed enough that the self-integrity pass could not do so.
    manifest_path = Path(repo) / MANIFEST_RELATIVE
    try:
        manifest = _read_json_bytes(_read_regular_file(manifest_path), "source-manifest.json", errors)
    except (OSError, ValueError):
        manifest = None
    if isinstance(manifest, dict) and manifest.get("source_units") != expected_units:
        errors.append("source-unit hashes do not match the exact DOCX")
    return list(dict.fromkeys(errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the CrossFrame Ultra v8.2 authority source tree.")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--source-docx", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        errors = (
            validate_against_docx(args.repo, args.source_docx)
            if args.source_docx is not None
            else validate_committed_source_tree(args.repo)
        )
    except Exception as error:
        errors = [f"checker failure: {error}"]
    result = {"ok": not errors, "errors": errors}
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif errors:
        print("CrossFrame Ultra v8.2 source tree: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("CrossFrame Ultra v8.2 source tree: OK")
        if args.source_docx is not None:
            print(f"raw SHA256: {RAW_SHA256}")
            print(f"semantic SHA256: {SEMANTIC_SHA256}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
