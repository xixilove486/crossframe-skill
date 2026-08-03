"""Read-only integrity checker for the v8.2 authority tree.

The parser and semantic normalizer deliberately live in Task 2's compiler.  This
module only audits the authority representation produced from that snapshot; it
never treats markdown file names or manifest counts as source authority.
"""

from __future__ import annotations

# Isolation must be established at interpreter startup.  A non-isolated process
# may already have executed PYTHONPATH sitecustomize code, so it must fail closed
# before importing any ordinary module rather than attempting an in-process
# restart.
import sys as _bootstrap_sys

_ISOLATION_ERROR = (
    "trusted source validation requires direct Python startup flags -I -S -B"
)
if __name__ == "__main__" and not (
    _bootstrap_sys.flags.isolated
    and _bootstrap_sys.flags.no_site
    and _bootstrap_sys.flags.dont_write_bytecode
):
    if "--json" in _bootstrap_sys.argv[1:]:
        _bootstrap_sys.stdout.write(
            '{"errors":["trusted source validation requires direct Python '
            'startup flags -I -S -B"],"ok":false}\n'
        )
    else:
        _bootstrap_sys.stderr.write(f"error: {_ISOLATION_ERROR}\n")
    raise SystemExit(2)

import argparse
import base64
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import threading
from types import MappingProxyType


RAW_SHA256 = "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
SEMANTIC_SHA256 = "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
SEMANTIC_NORMALIZATION_VERSION = 1
EXPECTED_PARAGRAPHS = 4631
EXPECTED_NON_WHITESPACE_CHARS = 165690
EXPECTED_TABLES = 122
EXPECTED_DIVISIONS = 20
MAX_SOURCE_DOCX_BYTES = 8 * 1024 * 1024
MAX_SOURCE_TREE_FILE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_TREE_BYTES = 8 * 1024 * 1024
MAX_SOURCE_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_SOURCE_COMPILER_BYTES = 1 * 1024 * 1024
MAX_CAPTURED_AUTHORITY_BYTES = 12 * 1024 * 1024
MAX_SOURCE_TREE_ENTRIES = 256
MAX_SOURCE_TREE_DEPTH = 2
MAX_ISOLATED_REQUEST_BYTES = 16 * 1024 * 1024
MAX_ISOLATED_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_ISOLATED_STDERR_BYTES = 64 * 1024
ISOLATED_COMPILER_TIMEOUT_SECONDS = 30
COMPILER_VERSION = "1.0.0"
EXPECTED_COMPILER_SHA256 = "ead8862515fe71e11dd3ecb28cdabeccdf064bf8c67ce2c2763ae83954a9d2ad"
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

@dataclass(frozen=True)
class CommittedSourceSnapshot:
    """One immutable view of every byte used by committed-source validation."""

    errors: tuple[str, ...]
    manifest_bytes: bytes | None
    manifest: Mapping[str, object] | None
    files: Mapping[str, bytes]
    compiler_bytes: bytes | None
    paragraphs: tuple[Mapping[str, object], ...]
    tables: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class _CapturedParagraph:
    ordinal: int
    anchor: str
    style: str
    text: str


@dataclass(frozen=True, slots=True)
class _CapturedTable:
    ordinal: int
    anchor: str
    paragraph_ordinals: tuple[int, ...]
    rows: tuple[tuple[str, ...], ...]
    cell_paragraph_ordinals: tuple[tuple[tuple[int, ...], ...], ...]


@dataclass(frozen=True, slots=True)
class _CapturedSnapshot:
    raw_sha256: str
    semantic_sha256: str
    non_whitespace_chars: int
    paragraphs: tuple[_CapturedParagraph, ...]
    tables: tuple[_CapturedTable, ...]
    errors: tuple[str, ...]


@dataclass
class _AnchoredRegularFile:
    final_path: Path
    identity: tuple[int, ...]
    size: int
    _read_and_verify: Callable[[], bytes]
    _payload: bytes | None = None

    def read_all(self) -> bytes:
        if self._payload is None:
            self._payload = self._read_and_verify()
        return self._payload


@dataclass(frozen=True)
class _AnchoredDirectory:
    final_path: Path
    identity: tuple[int, ...]
    _scan_target: object

    def scandir(self) -> Iterator[os.DirEntry[str]]:
        return os.scandir(self._scan_target)


if os.name == "nt":
    from ctypes import wintypes

    _WIN_GENERIC_READ = 0x80000000
    _WIN_FILE_READ_ATTRIBUTES = 0x0080
    _WIN_FILE_SHARE_READ = 0x00000001
    _WIN_FILE_SHARE_WRITE = 0x00000002
    _WIN_OPEN_EXISTING = 3
    _WIN_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _WIN_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _WIN_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _WIN_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _WIN_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class _WinByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _KERNEL32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    _KERNEL32.CreateFileW.restype = wintypes.HANDLE
    _KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _KERNEL32.CloseHandle.restype = wintypes.BOOL
    _KERNEL32.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_WinByHandleFileInformation),
    )
    _KERNEL32.GetFileInformationByHandle.restype = wintypes.BOOL
    _KERNEL32.GetFinalPathNameByHandleW.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    _KERNEL32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    _KERNEL32.ReadFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    _KERNEL32.ReadFile.restype = wintypes.BOOL
    _KERNEL32.SetFilePointerEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_longlong,
        ctypes.POINTER(ctypes.c_longlong),
        wintypes.DWORD,
    )
    _KERNEL32.SetFilePointerEx.restype = wintypes.BOOL


_ISOLATED_COMPILER_RUNNER = r'''
import base64
from hashlib import sha256
import json
import sys
import types

MAX_INPUT = 16 * 1024 * 1024
MAX_OUTPUT = 16 * 1024 * 1024


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + str(key))
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-finite JSON number: " + value)


def _loads(text):
    if text.startswith("\\ufeff"):
        raise ValueError("UTF-8 BOM is forbidden")
    return json.loads(
        text,
        object_pairs_hook=_pairs,
        parse_constant=_constant,
    )


def _paragraph_record(item):
    return {
        "ordinal": item.ordinal,
        "anchor": item.anchor,
        "style": item.style,
        "text": item.text,
    }


def _table_record(item):
    return {
        "ordinal": item.ordinal,
        "anchor": item.anchor,
        "paragraph_ordinals": list(item.paragraph_ordinals),
        "rows": [list(row) for row in item.rows],
        "cell_paragraph_ordinals": [
            [list(cell) for cell in row] for row in item.cell_paragraph_ordinals
        ],
    }


def _records(namespace, paragraphs, tables):
    paragraph_type = namespace["V82Paragraph"]
    table_type = namespace["V82Table"]
    paragraph_objects = tuple(
        paragraph_type(
            ordinal=item["ordinal"],
            anchor=item["anchor"],
            style=item["style"],
            text=item["text"],
        )
        for item in paragraphs
    )
    table_objects = tuple(
        table_type(
            ordinal=item["ordinal"],
            anchor=item["anchor"],
            paragraph_ordinals=tuple(item["paragraph_ordinals"]),
            rows=tuple(tuple(row) for row in item["rows"]),
            cell_paragraph_ordinals=tuple(
                tuple(tuple(cell) for cell in row)
                for row in item["cell_paragraph_ordinals"]
            ),
        )
        for item in tables
    )
    return paragraph_objects, table_objects


def _main():
    try:
        request_bytes = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(request_bytes) > MAX_INPUT:
            raise ValueError("isolated compiler request exceeds safety limit")
        request = _loads(request_bytes.decode("utf-8"))
        if type(request) is not dict or set(request) != {"compiler", "operation", "payload"}:
            raise ValueError("isolated compiler request fields are not closed")
        compiler_b64 = request["compiler"]
        operation = request["operation"]
        payload = request["payload"]
        if type(compiler_b64) is not str or type(operation) is not str or type(payload) is not dict:
            raise ValueError("isolated compiler request types are invalid")
        compiler_bytes = base64.b64decode(compiler_b64.encode("ascii"), validate=True)
        source = compiler_bytes.decode("utf-8")
        module_name = "_captured_crossframe_ultra_v82_compiler"
        module = types.ModuleType(module_name)
        module.__file__ = "<captured-crossframe-ultra-v82-compiler>"
        module.__package__ = ""
        sys.modules[module_name] = module
        namespace = module.__dict__
        try:
            exec(compile(source, module.__file__, "exec"), namespace, namespace)
        finally:
            sys.modules.pop(module_name, None)
        if operation == "semantic_records":
            paragraphs, tables = _records(
                namespace,
                payload["paragraphs"],
                payload["tables"],
            )
            digest = sha256(namespace["semantic_snapshot_bytes"](paragraphs, tables)).hexdigest()
            response = {"ok": True, "semantic_sha256": digest}
        elif operation == "source_snapshot":
            source_bytes = base64.b64decode(payload["source"].encode("ascii"), validate=True)
            snapshot = namespace["build_v82_snapshot"](source_bytes)
            snapshot_errors = namespace["validate_v82_snapshot"](snapshot)
            response = {
                "ok": True,
                "raw_sha256": snapshot.raw_sha256,
                "semantic_sha256": snapshot.semantic_sha256,
                "non_whitespace_chars": snapshot.non_whitespace_chars,
                "paragraphs": [_paragraph_record(item) for item in snapshot.paragraphs],
                "tables": [_table_record(item) for item in snapshot.tables],
                "errors": [str(item) for item in snapshot_errors],
            }
        else:
            raise ValueError("unknown isolated compiler operation")
    except BaseException as error:
        response = {"ok": False, "error": type(error).__name__ + ": " + str(error)}
    output = json.dumps(
        response,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    if len(output) > MAX_OUTPUT:
        output = b'{"error":"isolated compiler response exceeds safety limit","ok":false}'
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    _main()
'''


def _bounded_pipe_reader(pipe: object, limit: int, result: dict[str, object], key: str) -> None:
    chunks: list[bytes] = []
    total = 0
    try:
        while True:
            amount = min(64 * 1024, limit + 1 - total)
            if amount <= 0:
                result[f"{key}_overflow"] = True
                break
            chunk = pipe.read(amount)  # type: ignore[attr-defined]
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                result[f"{key}_overflow"] = True
                break
    except (OSError, ValueError) as error:
        result[f"{key}_error"] = str(error)
    finally:
        result[key] = b"".join(chunks)
        try:
            pipe.close()  # type: ignore[attr-defined]
        except OSError:
            pass


def _run_isolated_compiler(
    compiler_bytes: bytes,
    operation: str,
    payload: Mapping[str, object],
) -> object:
    """Run only frozen compiler bytes in a bounded, isolated child process."""
    if _sha256_bytes(compiler_bytes) != EXPECTED_COMPILER_SHA256:
        raise ValueError("captured compiler SHA256 is not the frozen authority")
    request = _canonical_json(
        {
            "compiler": base64.b64encode(compiler_bytes).decode("ascii"),
            "operation": operation,
            "payload": payload,
        }
    )
    if len(request) > MAX_ISOLATED_REQUEST_BYTES:
        raise ValueError("isolated compiler request exceeds safety limit")
    process = subprocess.Popen(
        [sys.executable, "-I", "-S", "-B", "-c", _ISOLATED_COMPILER_RUNNER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(sys.executable).resolve().parent,
        close_fds=True,
    )
    captured: dict[str, object] = {}
    stdout_thread = threading.Thread(
        target=_bounded_pipe_reader,
        args=(process.stdout, MAX_ISOLATED_RESPONSE_BYTES, captured, "stdout"),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_bounded_pipe_reader,
        args=(process.stderr, MAX_ISOLATED_STDERR_BYTES, captured, "stderr"),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    timed_out = False
    write_failed: BaseException | None = None
    try:
        assert process.stdin is not None
        try:
            process.stdin.write(request)
            process.stdin.close()
        except (BrokenPipeError, OSError) as error:
            write_failed = error
            try:
                process.kill()
            except OSError:
                pass
            process.wait(timeout=5)
        if write_failed is None:
            try:
                process.wait(timeout=ISOLATED_COMPILER_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                process.wait(timeout=5)
    finally:
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
    if timed_out:
        raise ValueError("isolated compiler timed out")
    if write_failed is not None:
        raise ValueError(f"isolated compiler closed its input: {write_failed}")
    if captured.get("stdout_overflow"):
        raise ValueError("isolated compiler response exceeds safety limit")
    if captured.get("stderr_overflow"):
        raise ValueError("isolated compiler diagnostics exceed safety limit")
    if captured.get("stdout_error") or captured.get("stderr_error"):
        raise ValueError(
            "isolated compiler pipe failure: "
            + str(captured.get("stdout_error") or captured.get("stderr_error"))
        )
    returncode = process.returncode
    if returncode != 0:
        diagnostics = bytes(captured.get("stderr", b"")).decode("utf-8", "replace")
        raise ValueError(f"isolated compiler returned {returncode}: {diagnostics[:512]}")
    output = bytes(captured.get("stdout", b""))
    diagnostics = bytes(captured.get("stderr", b""))
    if diagnostics:
        raise ValueError(
            "isolated compiler emitted diagnostics: "
            + diagnostics.decode("utf-8", "replace")[:512]
        )
    try:
        text = output.decode("utf-8")
        return _strict_json_loads(text)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"isolated compiler returned invalid JSON: {error}") from error


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


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


def _absolute_anchored_paths(path: Path, anchor: Path) -> tuple[Path, Path]:
    path = Path(os.path.abspath(path))
    anchor = Path(os.path.abspath(anchor))
    try:
        common = os.path.commonpath((str(path), str(anchor)))
    except ValueError as error:
        raise ValueError(f"path escapes anchor: {path}") from error
    if os.path.normcase(os.path.normpath(common)) != os.path.normcase(
        os.path.normpath(str(anchor))
    ):
        raise ValueError(f"path escapes anchor: {path}")
    return path, anchor


def _windows_extended_path(path: Path) -> str:
    value = str(path)
    if value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def _windows_normalized_final_path(value: str) -> Path:
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(os.path.abspath(value))


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.normpath(str(left))) == os.path.normcase(
        os.path.normpath(str(right))
    )


def _windows_final_path(handle: int) -> Path:
    capacity = 512
    while True:
        buffer = ctypes.create_unicode_buffer(capacity)
        result = _KERNEL32.GetFinalPathNameByHandleW(handle, buffer, capacity, 0)
        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        if result < capacity:
            return _windows_normalized_final_path(buffer.value)
        capacity = result + 1


def _windows_handle_info(handle: int) -> tuple[int, tuple[int, ...], int, tuple[int, ...]]:
    information = _WinByHandleFileInformation()
    if not _KERNEL32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        raise ctypes.WinError(ctypes.get_last_error())
    identity = (
        int(information.dwVolumeSerialNumber),
        (int(information.nFileIndexHigh) << 32) | int(information.nFileIndexLow),
    )
    size = (int(information.nFileSizeHigh) << 32) | int(information.nFileSizeLow)
    write_time = (
        int(information.ftLastWriteTime.dwHighDateTime) << 32
    ) | int(information.ftLastWriteTime.dwLowDateTime)
    signature = (*identity, size, write_time)
    return int(information.dwFileAttributes), identity, size, signature


def _windows_open_handle(path: Path, *, directory: bool) -> tuple[int, tuple[int, ...], int, tuple[int, ...]]:
    desired_access = _WIN_FILE_READ_ATTRIBUTES if directory else (
        _WIN_GENERIC_READ | _WIN_FILE_READ_ATTRIBUTES
    )
    share_mode = (
        _WIN_FILE_SHARE_READ | _WIN_FILE_SHARE_WRITE
        if directory
        else _WIN_FILE_SHARE_READ
    )
    flags = _WIN_FILE_FLAG_OPEN_REPARSE_POINT
    if directory:
        flags |= _WIN_FILE_FLAG_BACKUP_SEMANTICS
    handle = _KERNEL32.CreateFileW(
        _windows_extended_path(path),
        desired_access,
        share_mode,
        None,
        _WIN_OPEN_EXISTING,
        flags,
        None,
    )
    if handle == _WIN_INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes, identity, size, signature = _windows_handle_info(handle)
        if attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"path contains symlink, junction, or reparse point: {path}")
        is_directory = bool(attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY)
        if is_directory != directory:
            kind = "directory" if directory else "regular file"
            raise ValueError(f"path is not a {kind}: {path}")
        final_path = _windows_final_path(handle)
        if not _same_path(final_path, path):
            raise ValueError(
                f"handle final path escaped through a reparse point: {path} -> {final_path}"
            )
        return int(handle), identity, size, signature
    except Exception:
        _KERNEL32.CloseHandle(handle)
        raise


def _windows_directory_prefixes(path: Path) -> tuple[Path, ...]:
    parts = path.parts
    if not parts:
        raise ValueError(f"directory path has no root: {path}")
    current = Path(parts[0])
    prefixes = [current]
    for part in parts[1:]:
        current = current / part
        prefixes.append(current)
    return tuple(prefixes)


def _close_windows_handles(handles: Iterable[int]) -> None:
    for handle in reversed(tuple(handles)):
        _KERNEL32.CloseHandle(handle)


def _read_bounded_chunks(
    read: Callable[[int], bytes],
    *,
    initial_size: int,
    max_bytes: int,
) -> bytes:
    """Read at most initial_size + 1 bytes, with a hard authority limit."""
    if type(initial_size) is not int or type(max_bytes) is not int:
        raise TypeError("bounded reader sizes must be integers")
    if initial_size < 0 or max_bytes < 0:
        raise ValueError("bounded reader sizes cannot be negative")
    if initial_size > max_bytes:
        raise ValueError(
            f"initial size exceeds safety limit: {initial_size} > {max_bytes}"
        )
    limit = initial_size + 1
    chunks: list[bytes] = []
    total = 0
    while total < limit:
        amount = min(1024 * 1024, limit - total)
        chunk = read(amount)
        if not isinstance(chunk, bytes):
            raise TypeError("bounded reader callback must return bytes")
        if len(chunk) > amount:
            raise ValueError("bounded reader callback exceeded requested amount")
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    return b"".join(chunks)


def _windows_read_handle(
    handle: int,
    *,
    path: Path,
    expected_final_path: Path,
    expected_signature: tuple[int, ...],
    expected_size: int,
) -> bytes:
    new_position = ctypes.c_longlong()
    if not _KERNEL32.SetFilePointerEx(handle, 0, ctypes.byref(new_position), 0):
        raise ctypes.WinError(ctypes.get_last_error())
    def read_chunk(amount: int) -> bytes:
        buffer = ctypes.create_string_buffer(amount)
        read = wintypes.DWORD()
        if not _KERNEL32.ReadFile(handle, buffer, amount, ctypes.byref(read), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.raw[: read.value]

    payload = _read_bounded_chunks(
        read_chunk,
        initial_size=expected_size,
        max_bytes=expected_size,
    )
    _attributes, _identity, size_after, signature_after = _windows_handle_info(handle)
    final_after = _windows_final_path(handle)
    if signature_after != expected_signature or size_after != expected_size:
        raise ValueError(f"file changed while being read: {path}")
    if not _same_path(final_after, expected_final_path):
        raise ValueError(f"file handle final path changed while being read: {path}")
    if len(payload) != expected_size:
        raise ValueError(f"file size/read length mismatch: {path}")
    return payload


def _posix_directory_chain(path: Path) -> list[int]:
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    handles = [os.open(os.sep, directory_flags)]
    try:
        for part in path.parts[1:]:
            handle = os.open(
                part,
                directory_flags | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=handles[-1],
            )
            metadata = os.fstat(handle)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(handle)
                raise ValueError(f"path is not a directory: {path}")
            handles.append(handle)
    except Exception:
        for handle in reversed(handles):
            os.close(handle)
        raise
    return handles


@contextmanager
def _open_anchored_directory(path: Path, *, anchor: Path) -> Iterator[_AnchoredDirectory]:
    path, _anchor = _absolute_anchored_paths(path, anchor)
    if os.name == "nt":
        handles: list[int] = []
        try:
            identity: tuple[int, ...] = ()
            for prefix in _windows_directory_prefixes(path):
                handle, identity, _size, _signature = _windows_open_handle(
                    prefix, directory=True
                )
                handles.append(handle)
            yield _AnchoredDirectory(path, identity, path)
        finally:
            _close_windows_handles(handles)
        return
    handles = _posix_directory_chain(path)
    try:
        metadata = os.fstat(handles[-1])
        yield _AnchoredDirectory(path, (metadata.st_dev, metadata.st_ino), handles[-1])
    finally:
        for handle in reversed(handles):
            os.close(handle)


@contextmanager
def _open_anchored_regular_file(
    path: Path,
    *,
    anchor: Path,
) -> Iterator[_AnchoredRegularFile]:
    path, _anchor = _absolute_anchored_paths(path, anchor)
    if path == _anchor:
        raise ValueError(f"regular file path cannot equal its directory anchor: {path}")
    if os.name == "nt":
        directory_handles: list[int] = []
        file_handle: int | None = None
        try:
            for prefix in _windows_directory_prefixes(path.parent):
                handle, _identity, _size, _signature = _windows_open_handle(
                    prefix, directory=True
                )
                directory_handles.append(handle)
            file_handle, identity, size, signature = _windows_open_handle(
                path, directory=False
            )
            final_path = _windows_final_path(file_handle)
            yield _AnchoredRegularFile(
                final_path=final_path,
                identity=identity,
                size=size,
                _read_and_verify=lambda: _windows_read_handle(
                    file_handle,
                    path=path,
                    expected_final_path=final_path,
                    expected_signature=signature,
                    expected_size=size,
                ),
            )
        finally:
            if file_handle is not None:
                _KERNEL32.CloseHandle(file_handle)
            _close_windows_handles(directory_handles)
        return
    directory_handles = _posix_directory_chain(path.parent)
    file_handle: int | None = None
    try:
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        file_handle = os.open(path.name, file_flags, dir_fd=directory_handles[-1])
        before = os.fstat(file_handle)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"file is not regular: {path}")
        identity = (before.st_dev, before.st_ino)
        signature = (
            *identity,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )

        def read_and_verify() -> bytes:
            os.lseek(file_handle, 0, os.SEEK_SET)

            payload = _read_bounded_chunks(
                lambda amount: os.read(file_handle, amount),
                initial_size=before.st_size,
                max_bytes=before.st_size,
            )
            after = os.fstat(file_handle)
            after_signature = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if after_signature != signature or len(payload) != before.st_size:
                raise ValueError(f"file changed while being read: {path}")
            return payload

        yield _AnchoredRegularFile(path, identity, before.st_size, read_and_verify)
    finally:
        if file_handle is not None:
            os.close(file_handle)
        for handle in reversed(directory_handles):
            os.close(handle)


def _assert_no_link_ancestors(path: Path, stop: Path) -> None:
    """Reject links in existing ancestors; byte reads use anchored handles."""
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
    try:
        with _open_anchored_directory(repo, anchor=repo):
            pass
    except (OSError, ValueError) as error:
        raise ValueError(f"repository root cannot be opened safely: {repo}: {error}") from error
    return repo


def _read_regular_file(
    path: Path,
    *,
    anchor: Path | None = None,
    max_bytes: int | None = None,
    label: str = "authority file",
) -> bytes:
    path = Path(os.path.abspath(path))
    anchor = Path(os.path.abspath(anchor or path.parent))
    if max_bytes is None:
        max_bytes = MAX_SOURCE_TREE_FILE_BYTES
    with _open_anchored_regular_file(path, anchor=anchor) as opened:
        if max_bytes is not None:
            if type(max_bytes) is not int or max_bytes < 0:
                raise ValueError(f"{label} limit is invalid")
            # The handle's initial size is authoritative for the pre-read
            # check.  This prevents a large file from ever reaching read_all.
            if opened.size > max_bytes:
                raise ValueError(
                    f"{label} exceeds safety limit before read: "
                    f"{opened.size} > {max_bytes}"
                )
        payload = opened.read_all()
        if max_bytes is not None and len(payload) > max_bytes:
            raise ValueError(
                f"{label} exceeds safety limit after read: "
                f"{len(payload)} > {max_bytes}"
            )
        if len(payload) != opened.size:
            raise ValueError(f"{label} size changed while being read")
        return payload


def _read_bounded_source_docx(path: Path) -> bytes:
    return _read_regular_file(
        path,
        anchor=path.parent,
        max_bytes=MAX_SOURCE_DOCX_BYTES,
        label="source DOCX",
    )


def _walk_regular_tree(
    root: Path,
    *,
    anchor: Path | None = None,
    max_file_bytes: int | None = None,
    max_total_bytes: int | None = None,
    max_entries: int | None = None,
    max_depth: int | None = None,
    expected_files: Iterable[str] | None = None,
) -> tuple[dict[str, bytes], list[str]]:
    root = Path(os.path.abspath(root))
    anchor = Path(os.path.abspath(anchor or root))
    max_file_bytes = MAX_SOURCE_TREE_FILE_BYTES if max_file_bytes is None else max_file_bytes
    max_total_bytes = MAX_SOURCE_TREE_BYTES if max_total_bytes is None else max_total_bytes
    max_entries = MAX_SOURCE_TREE_ENTRIES if max_entries is None else max_entries
    max_depth = MAX_SOURCE_TREE_DEPTH if max_depth is None else max_depth
    if any(type(value) is not int or value < 0 for value in (max_file_bytes, max_total_bytes, max_entries, max_depth)):
        raise ValueError("source tree safety limits are invalid")
    expected = None if expected_files is None else frozenset(str(item) for item in expected_files)
    if expected is not None:
        if len(expected) > max_entries:
            return {}, [
                "frozen authority file list exceeds entry safety limit "
                f"({max_entries})"
            ]
        invalid_expected = [
            relative
            for relative in expected
            if (
                not relative
                or PurePosixPath(relative).is_absolute()
                or "\\" in relative
                or ".." in PurePosixPath(relative).parts
                or len(PurePosixPath(relative).parts) > max_depth
            )
        ]
        if invalid_expected:
            return {}, [
                "frozen authority file list contains invalid depth/path "
                f"(max depth {max_depth}): "
                + ", ".join(sorted(invalid_expected)[:4])
            ]
    allowed_directories = (
        None
        if expected is None
        else frozenset(
            prefix.as_posix()
            for relative in expected
            for prefix in tuple(
                PurePosixPath(relative).parents
            )[:-1]
            if prefix != PurePosixPath(".")
        )
    )
    errors: list[str] = []
    files: dict[str, bytes] = {}
    pending = [root]
    total_bytes = 0
    entry_count = 0
    entry_limit_hit = False
    while pending:
        directory = pending.pop()
        try:
            with _open_anchored_directory(directory, anchor=anchor) as opened:
                with opened.scandir() as iterator:
                    entries = []
                    for entry in iterator:
                        entry_count += 1
                        if entry_count > max_entries:
                            errors.append(
                                "source tree entry count exceeds safety limit "
                                f"({max_entries})"
                            )
                            entry_limit_hit = True
                            break
                        entries.append(entry)
                    entries.sort(key=lambda entry: entry.name)
        except (OSError, ValueError) as error:
            errors.append(f"cannot scan source tree {directory}: {error}")
            continue
        for entry in entries:
            path = directory / entry.name
            relative = path.relative_to(root).as_posix()
            depth = len(PurePosixPath(relative).parts)
            try:
                metadata = entry.stat(follow_symlinks=False)
                attributes = getattr(metadata, "st_file_attributes", 0)
                reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                if stat.S_ISLNK(metadata.st_mode) or attributes & reparse_flag:
                    errors.append(f"source tree contains symlink or reparse point: {relative}")
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if depth > max_depth:
                        errors.append(f"source tree depth exceeds safety limit ({max_depth}): {relative}")
                        continue
                    if allowed_directories is not None and relative not in allowed_directories:
                        errors.append(f"source tree contains unknown directory: {relative}")
                        continue
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    if depth > max_depth:
                        errors.append(f"source tree depth exceeds safety limit ({max_depth}): {relative}")
                        continue
                    if expected is not None and relative not in expected:
                        errors.append(f"unexpected generated file: {relative}")
                        continue
                    remaining = max_total_bytes - total_bytes
                    if remaining <= 0:
                        errors.append(
                            f"source tree total byte limit exceeded before reading {relative}"
                        )
                        continue
                    file_limit = min(max_file_bytes, remaining)
                    try:
                        payload = _read_regular_file(
                            path,
                            anchor=anchor,
                            max_bytes=file_limit,
                            label=f"source tree file {relative}",
                        )
                    except (OSError, ValueError) as error:
                        message = str(error)
                        if file_limit == remaining and (
                            "exceeds safety limit" in message or "limit" in message
                        ):
                            message = (
                                f"source tree total byte limit exceeded for {relative}: "
                                + message
                            )
                        errors.append(message)
                        continue
                    if len(payload) > max_file_bytes:
                        errors.append(
                            f"source tree file exceeds safety limit ({max_file_bytes}): {relative}"
                        )
                        continue
                    if total_bytes + len(payload) > max_total_bytes:
                        errors.append(
                            f"source tree total byte limit exceeded: {relative}"
                        )
                        continue
                    files[relative] = payload
                    total_bytes += len(payload)
                else:
                    errors.append(f"source tree contains non-regular entry: {relative}")
            except (OSError, ValueError) as error:
                errors.append(f"cannot inspect source tree entry {relative}: {error}")
        if entry_limit_hit:
            pending.clear()
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
    files, errors = _walk_regular_tree(Path(source_tree), anchor=Path(source_tree))
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


def _source_file_for_paragraph(ordinal: int) -> str:
    for item in SOURCE_RANGES:
        if _anchor_number(str(item["paragraph_start"]), "paragraph") <= ordinal <= _anchor_number(str(item["paragraph_end"]), "paragraph"):
            return str(item["file"])
    raise ValueError(f"paragraph ordinal outside fixed ranges: {ordinal}")


def _strict_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _strict_json_loads(text: str) -> object:
    if text.startswith("\ufeff"):
        raise ValueError("UTF-8 BOM is forbidden")
    return json.loads(
        text,
        object_pairs_hook=_strict_json_pairs,
        parse_constant=_strict_json_constant,
    )


def _json_exact_equal(left: object, right: object) -> bool:
    """Compare decoded JSON recursively without Python numeric coercion."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if set(left) != set(right):  # type: ignore[arg-type]
            return False
        return all(
            _json_exact_equal(left[key], right[key])  # type: ignore[index]
            for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(  # type: ignore[arg-type]
            _json_exact_equal(item, expected)
            for item, expected in zip(left, right, strict=True)  # type: ignore[arg-type]
        )
    return left == right


def _read_json_bytes(payload: bytes, label: str, errors: list[str]) -> object | None:
    try:
        text = payload.decode("utf-8")
        return _strict_json_loads(text)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        errors.append(f"{label}: invalid JSON: {error}")
        return None


def _canonical_block(content: str, label: str, errors: list[str]) -> object | None:
    matches = list(CANONICAL_BLOCK_RE.finditer(content))
    if len(matches) != 1:
        errors.append(f"{label}: canonical record block count is not one")
        return None
    try:
        return _strict_json_loads(matches[0].group(1))
    except (json.JSONDecodeError, ValueError) as error:
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
        display_rows = _strict_json_loads(row_block[0].group(1))
        display_cells = _strict_json_loads(cell_block[0].group(1))
    except (json.JSONDecodeError, ValueError) as error:
        errors.append(f"{label}: table display JSON is invalid: {error}")
        return
    if display_rows != expected["rows"]:
        errors.append(f"{label}: displayed table cell order/content mismatch")
    if display_cells != expected["cell_paragraph_ordinals"]:
        errors.append(f"{label}: displayed cell-paragraph binding mismatch")
    if _parse_markdown_rows(content) != [list(row) for row in expected["rows"]]:
        errors.append(f"{label}: markdown rows mismatch")


def _manifest_from_tree(
    repo: Path,
    files: Mapping[str, bytes],
    errors: list[str],
    *,
    max_bytes: int | None = None,
    label: str = "source manifest",
) -> tuple[bytes | None, dict[str, object] | None]:
    manifest_path = repo / MANIFEST_RELATIVE
    if max_bytes is None:
        max_bytes = MAX_SOURCE_MANIFEST_BYTES
    try:
        payload = _read_regular_file(
            manifest_path,
            anchor=repo,
            max_bytes=max_bytes,
            label=label,
        )
    except (OSError, ValueError) as error:
        errors.append(f"source manifest cannot be read: {error}")
        return None, None
    value = _read_json_bytes(payload, "source-manifest.json", errors)
    if not isinstance(value, dict):
        errors.append("source-manifest.json root must be an object")
        return payload, None
    return payload, value


def _validate_manifest(
    manifest: Mapping[str, object],
    files: Mapping[str, bytes],
    compiler_bytes: bytes | None,
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
        if not _json_exact_equal(manifest.get(key), expected):
            errors.append(f"source manifest constant mismatch: {key}")
    if not _json_exact_equal(
        manifest.get("source_ranges"), [_range_to_json(item) for item in SOURCE_RANGES]
    ):
        errors.append("source manifest source_ranges mismatch")
    if not _json_exact_equal(
        manifest.get("division_ranges"), [_range_to_json(item) for item in DIVISION_RANGES]
    ):
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
    if not _json_exact_equal(manifest.get("divisions"), expected_divisions):
        errors.append("source manifest divisions mismatch")
    compiler = manifest.get("compiler")
    if type(compiler) is not dict or set(compiler) != {"version", "path", "sha256"}:
        errors.append("source manifest compiler fields are not closed")
    else:
        if type(compiler.get("version")) is not str or compiler.get("version") != COMPILER_VERSION:
            errors.append("source manifest compiler version mismatch")
        if type(compiler.get("path")) is not str or compiler.get("path") != "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py":
            errors.append("source manifest compiler path mismatch")
        if compiler_bytes is None:
            errors.append("cannot verify compiler hash: compiler snapshot is unavailable")
        else:
            compiler_hash = _sha256_bytes(compiler_bytes)
            if compiler_hash != EXPECTED_COMPILER_SHA256:
                errors.append(
                    "frozen compiler SHA256 mismatch: "
                    f"expected {EXPECTED_COMPILER_SHA256}, got {compiler_hash}"
                )
            if type(compiler.get("sha256")) is not str or compiler.get("sha256") != compiler_hash:
                errors.append("source manifest compiler hash mismatch")
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
    if not _json_exact_equal(entries, expected_entries):
        errors.append("source manifest file inventory or byte hash mismatch")
    source_units = manifest.get("source_units")
    expected_units = _source_unit_entries(paragraphs, tables)
    if not _json_exact_equal(source_units, expected_units):
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
        if (
            type(record.get("ordinal")) is not int
            or type(record.get("anchor")) is not str
            or type(record.get("text")) is not str
            or type(record.get("style")) is not str
        ):
            errors.append("paragraph record has invalid fields")
            continue
        ordinal = record["ordinal"]
        text = record["text"]
        text_by_ordinal[ordinal] = text
        if record.get("anchor") != f"V82-P{ordinal:04d}":
            errors.append(f"paragraph anchor/ordinal binding mismatch: {record.get('anchor')}")
    for table in tables:
        label = str(table.get("anchor", "unknown-table"))
        if (
            type(table.get("ordinal")) is not int
            or type(table.get("anchor")) is not str
            or type(table.get("paragraph_ordinals")) is not list
            or any(type(value) is not int for value in table.get("paragraph_ordinals", []))
            or type(table.get("rows")) is not list
            or any(
                type(row) is not list or any(type(value) is not str for value in row)
                for row in table.get("rows", [])
            )
            or type(table.get("cell_paragraph_ordinals")) is not list
            or any(
                type(row) is not list
                or any(
                    type(cell) is not list
                    or any(type(value) is not int for value in cell)
                    for cell in row
                )
                for row in table.get("cell_paragraph_ordinals", [])
            )
        ):
            errors.append(f"{label}: table record has invalid fields")
            continue
        ordinal = table["ordinal"]
        paragraph_ordinals = tuple(table["paragraph_ordinals"])
        rows = table["rows"]
        cell_bindings = table["cell_paragraph_ordinals"]
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
    compiler_bytes: bytes,
) -> str | None:
    try:
        response = _run_isolated_compiler(
            compiler_bytes,
            "semantic_records",
            {
                "paragraphs": [_thaw_authority_value(record) for record in paragraphs],
                "tables": [_thaw_authority_value(record) for record in tables],
            },
        )
        if (
            type(response) is not dict
            or set(response) != {"ok", "semantic_sha256"}
            or response.get("ok") is not True
            or type(response.get("semantic_sha256")) is not str
        ):
            return None
        return str(response["semantic_sha256"])
    except (KeyError, TypeError, ValueError, AttributeError, OSError):
        return None


def _captured_snapshot_from_response(response: object) -> _CapturedSnapshot:
    if type(response) is not dict:
        raise ValueError("isolated compiler response root must be an object")
    if response.get("ok") is not True:
        if set(response) != {"ok", "error"} or type(response.get("error")) is not str:
            raise ValueError("isolated compiler error response is not closed")
        raise ValueError(str(response["error"]))
    required = {
        "ok",
        "raw_sha256",
        "semantic_sha256",
        "non_whitespace_chars",
        "paragraphs",
        "tables",
        "errors",
    }
    if set(response) != required:
        raise ValueError("isolated compiler snapshot response fields are not closed")
    if (
        type(response["raw_sha256"]) is not str
        or type(response["semantic_sha256"]) is not str
        or type(response["non_whitespace_chars"]) is not int
        or type(response["paragraphs"]) is not list
        or type(response["tables"]) is not list
        or type(response["errors"]) is not list
        or any(type(item) is not str for item in response["errors"])
    ):
        raise ValueError("isolated compiler snapshot response types are invalid")
    captured_paragraphs: list[_CapturedParagraph] = []
    for item in response["paragraphs"]:
        if type(item) is not dict or set(item) != {"ordinal", "anchor", "style", "text"}:
            raise ValueError("isolated paragraph response fields are not closed")
        if (
            type(item["ordinal"]) is not int
            or type(item["anchor"]) is not str
            or type(item["style"]) is not str
            or type(item["text"]) is not str
        ):
            raise ValueError("isolated paragraph response types are invalid")
        captured_paragraphs.append(
            _CapturedParagraph(item["ordinal"], item["anchor"], item["style"], item["text"])
        )
    captured_tables: list[_CapturedTable] = []
    for item in response["tables"]:
        if type(item) is not dict or set(item) != {
            "ordinal",
            "anchor",
            "paragraph_ordinals",
            "rows",
            "cell_paragraph_ordinals",
        }:
            raise ValueError("isolated table response fields are not closed")
        if (
            type(item["ordinal"]) is not int
            or type(item["anchor"]) is not str
            or type(item["paragraph_ordinals"]) is not list
            or any(type(value) is not int for value in item["paragraph_ordinals"])
            or type(item["rows"]) is not list
            or any(
                type(row) is not list or any(type(value) is not str for value in row)
                for row in item["rows"]
            )
            or type(item["cell_paragraph_ordinals"]) is not list
            or any(
                type(row) is not list
                or any(
                    type(cell) is not list
                    or any(type(value) is not int for value in cell)
                    for cell in row
                )
                for row in item["cell_paragraph_ordinals"]
            )
        ):
            raise ValueError("isolated table response types are invalid")
        captured_tables.append(
            _CapturedTable(
                item["ordinal"],
                item["anchor"],
                tuple(item["paragraph_ordinals"]),
                tuple(tuple(row) for row in item["rows"]),
                tuple(
                    tuple(tuple(cell) for cell in row)
                    for row in item["cell_paragraph_ordinals"]
                ),
            )
        )
    return _CapturedSnapshot(
        raw_sha256=response["raw_sha256"],
        semantic_sha256=response["semantic_sha256"],
        non_whitespace_chars=response["non_whitespace_chars"],
        paragraphs=tuple(captured_paragraphs),
        tables=tuple(captured_tables),
        errors=tuple(response["errors"]),
    )


def _freeze_authority_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_authority_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_authority_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_authority_value(item) for item in value)
    return value


def _thaw_authority_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_authority_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_authority_value(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw_authority_value(item) for item in value}
    return value


def _committed_snapshot(
    errors: Sequence[str],
    manifest_bytes: bytes | None,
    manifest: Mapping[str, object] | None,
    files: Mapping[str, bytes],
    compiler_bytes: bytes | None,
    paragraphs: Sequence[Mapping[str, object]],
    tables: Sequence[Mapping[str, object]],
) -> CommittedSourceSnapshot:
    frozen_manifest = _freeze_authority_value(manifest) if manifest is not None else None
    if frozen_manifest is not None and not isinstance(frozen_manifest, Mapping):
        raise TypeError("frozen manifest must remain a mapping")
    return CommittedSourceSnapshot(
        errors=tuple(dict.fromkeys(errors)),
        manifest_bytes=manifest_bytes,
        manifest=frozen_manifest,
        files=MappingProxyType(dict(files)),
        compiler_bytes=compiler_bytes,
        paragraphs=tuple(
            _freeze_authority_value(record) for record in paragraphs
        ),
        tables=tuple(_freeze_authority_value(record) for record in tables),
    )


def _self_integrity(repo: Path) -> CommittedSourceSnapshot:
    errors: list[str] = []
    manifest_bytes: bytes | None = None
    manifest: dict[str, object] | None = None
    compiler_bytes: bytes | None = None
    files: dict[str, bytes] = {}
    paragraphs: list[dict[str, object]] = []
    tables: list[dict[str, object]] = []
    try:
        repo = _safe_repo(repo)
        source_tree = repo / SOURCE_TREE_RELATIVE
    except (OSError, ValueError) as error:
        return _committed_snapshot(
            [str(error)], None, None, {}, None, (), ()
        )
    references = repo / REFERENCES_RELATIVE
    try:
        with _open_anchored_directory(references, anchor=repo) as opened:
            with opened.scandir() as iterator:
                for entry in iterator:
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        errors.append(
                            f"cannot inspect references entry {entry.name}: {error}"
                        )
                        continue
                    if entry.name.startswith(
                        (
                            ".v8.2-full-source.stage-",
                            ".v8.2-full-source.backup-",
                            ".source-manifest.stage-",
                            ".source-manifest.backup-",
                        )
                    ):
                        errors.append(f"incomplete source promotion residue: {entry.name}")
                    attributes = getattr(metadata, "st_file_attributes", 0)
                    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                    if stat.S_ISLNK(metadata.st_mode) or attributes & reparse_flag:
                        errors.append(
                            f"references contains symlink or reparse point: {entry.name}"
                        )
                    if entry.name == LEGACY_TREE_RELATIVE.name:
                        errors.append("legacy v8.2-source tree must not be present")
    except (OSError, ValueError) as error:
        errors.append(f"cannot inspect references directory safely: {error}")
    files, walk_errors = _walk_regular_tree(
        source_tree,
        anchor=repo,
        expected_files=EXPECTED_TREE_FILES,
        max_file_bytes=min(MAX_SOURCE_TREE_FILE_BYTES, MAX_CAPTURED_AUTHORITY_BYTES),
        max_total_bytes=min(MAX_SOURCE_TREE_BYTES, MAX_CAPTURED_AUTHORITY_BYTES),
    )
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
    captured_total = sum(len(payload) for payload in files.values())
    if captured_total > MAX_CAPTURED_AUTHORITY_BYTES:
        errors.append(
            "captured authority byte limit exceeded by source tree: "
            f"{captured_total} > {MAX_CAPTURED_AUTHORITY_BYTES}"
        )
    manifest_remaining = max(0, MAX_CAPTURED_AUTHORITY_BYTES - captured_total)
    manifest_limit = min(MAX_SOURCE_MANIFEST_BYTES, manifest_remaining)
    manifest_label = "source manifest"
    if manifest_limit < MAX_SOURCE_MANIFEST_BYTES:
        manifest_label = "source manifest (captured authority total)"
    manifest_bytes, manifest = _manifest_from_tree(
        repo,
        files,
        errors,
        max_bytes=manifest_limit,
        label=manifest_label,
    )
    if manifest_bytes is not None:
        captured_total += len(manifest_bytes)
    compiler_path = repo / ROOT_RELATIVE / "scripts/generate_crossframe_ultra_v82_source.py"
    compiler_hash: str | None = None
    compiler_limit = min(
        MAX_SOURCE_COMPILER_BYTES,
        max(0, MAX_CAPTURED_AUTHORITY_BYTES - captured_total),
    )
    compiler_label = "source compiler"
    if compiler_limit < MAX_SOURCE_COMPILER_BYTES:
        compiler_label = "source compiler (captured authority total)"
    try:
        compiler_bytes = _read_regular_file(
            compiler_path,
            anchor=repo,
            max_bytes=compiler_limit,
            label=compiler_label,
        )
    except (OSError, ValueError) as error:
        errors.append(f"source compiler cannot be read safely: {error}")
    if compiler_bytes is not None:
        compiler_hash = _sha256_bytes(compiler_bytes)
        if compiler_hash != EXPECTED_COMPILER_SHA256:
            errors.append(
                "frozen compiler SHA256 mismatch: "
                f"expected {EXPECTED_COMPILER_SHA256}, got {compiler_hash}"
            )
        captured_total += len(compiler_bytes)
        if captured_total > MAX_CAPTURED_AUTHORITY_BYTES:
            errors.append(
                "captured authority byte limit exceeded: "
                f"{captured_total} > {MAX_CAPTURED_AUTHORITY_BYTES}"
            )
    if manifest is None:
        return _committed_snapshot(
            errors, manifest_bytes, None, files, compiler_bytes, (), ()
        )
    # Parse canonical payloads and collect records before validating indexes.
    paragraphs, tables = _parse_committed_records(repo, files, errors)
    _validate_record_structure(paragraphs, tables, errors)
    semantic_from_records = (
        _semantic_hash_from_records(paragraphs, tables, compiler_bytes)
        if compiler_bytes is not None and compiler_hash == EXPECTED_COMPILER_SHA256
        else None
    )
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
    if manifest_bytes is not None:
        _validate_old_anchor_free(
            (("source-manifest.json", manifest_bytes),),
            errors,
        )
    _validate_manifest(
        manifest, files, compiler_bytes, paragraphs, tables, errors
    )
    return _committed_snapshot(
        errors,
        manifest_bytes,
        manifest,
        files,
        compiler_bytes,
        paragraphs,
        tables,
    )


def validate_committed_source_snapshot(repo: Path) -> CommittedSourceSnapshot:
    """Return the exact captured bytes and records consumed by validation."""
    try:
        return _self_integrity(Path(repo))
    except Exception as error:
        return _committed_snapshot(
            [f"source-tree validation failure: {error}"],
            None,
            None,
            {},
            None,
            (),
            (),
        )


def validate_committed_source_tree(repo: Path) -> list[str]:
    """Validate the committed authority tree without reading the DOCX."""
    return list(validate_committed_source_snapshot(repo).errors)


def validate_against_docx(repo: Path, source_docx: Path) -> list[str]:
    """Validate self-integrity and exact raw/semantic/source-unit identity."""
    committed = validate_committed_source_snapshot(repo)
    errors = list(committed.errors)
    committed_paragraphs = [
        _thaw_authority_value(record) for record in committed.paragraphs
    ]
    committed_tables = [_thaw_authority_value(record) for record in committed.tables]
    source_docx = Path(os.path.abspath(source_docx))
    try:
        source_bytes = _read_bounded_source_docx(source_docx)
    except (OSError, ValueError) as error:
        errors.append(f"source DOCX cannot be read safely: {error}")
        return list(dict.fromkeys(errors))
    raw = _sha256_bytes(source_bytes)
    if raw != RAW_SHA256:
        errors.append(f"raw SHA256 mismatch: expected {RAW_SHA256}, got {raw}")
        return list(dict.fromkeys(errors))
    if committed.compiler_bytes is None:
        errors.append("cannot validate source DOCX without the captured source compiler")
        return list(dict.fromkeys(errors))
    compiler_hash = _sha256_bytes(committed.compiler_bytes)
    if compiler_hash != EXPECTED_COMPILER_SHA256:
        errors.append(
            "cannot execute untrusted captured source compiler: "
            f"expected {EXPECTED_COMPILER_SHA256}, got {compiler_hash}"
        )
        return list(dict.fromkeys(errors))
    try:
        snapshot = _captured_snapshot_from_response(
            _run_isolated_compiler(
                committed.compiler_bytes,
                "source_snapshot",
                {"source": base64.b64encode(source_bytes).decode("ascii")},
            )
        )
    except Exception as error:  # compiler owns detailed source parsing errors
        errors.append(f"cannot parse source DOCX: {error}")
        return list(dict.fromkeys(errors))
    errors.extend(f"source snapshot: {error}" for error in snapshot.errors)
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
    expected_semantic = _semantic_hash_from_records(
        source_paragraphs,
        source_tables,
        committed.compiler_bytes,
    )
    if expected_semantic != SEMANTIC_SHA256:
        errors.append(f"source semantic snapshot mismatch: expected {SEMANTIC_SHA256}, got {expected_semantic}")
    expected_units = _source_unit_entries(source_paragraphs, source_tables)
    manifest = _thaw_authority_value(committed.manifest)
    if isinstance(manifest, dict) and not _json_exact_equal(
        manifest.get("source_units"), expected_units
    ):
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
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
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
