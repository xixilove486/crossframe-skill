from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = ROOT / "skills/crossframe-ultra"
RUNTIME_SCRIPTS = ULTRA_ROOT / "scripts"
SCHEMA_ROOT = ULTRA_ROOT / "schemas"
MATRIX_PATH = ULTRA_ROOT / "references/compatibility-matrix.json"


def load_module(name: str):
    scripts = str(RUNTIME_SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module(name)


def clear_legacy_cache(function: object) -> None:
    cache_clear = getattr(function, "cache_clear", None)
    if cache_clear is not None:
        cache_clear()


@pytest.mark.parametrize(
    "raw",
    (
        b'{"field":1,"field":2}',
        b'{"field":NaN}',
        b'{"field":Infinity}',
        b'{"field":-Infinity}',
    ),
    ids=("duplicate-key", "nan", "infinity", "negative-infinity"),
)
def test_load_json_object_rejects_non_strict_json(tmp_path: Path, raw: bytes) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    path = tmp_path / "document.json"
    path.write_bytes(raw)

    with pytest.raises(ValueError):
        jsonio.load_json_object(path)


@pytest.mark.parametrize(
    "raw",
    (
        b'\xef\xbb\xbf{"field":1}',
        b'{"field":"\xff"}',
    ),
    ids=("utf8-bom", "invalid-utf8"),
)
def test_load_json_object_rejects_noncanonical_utf8(
    tmp_path: Path,
    raw: bytes,
) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    path = tmp_path / "document.json"
    path.write_bytes(raw)

    with pytest.raises(ValueError):
        jsonio.load_json_object(path)


def test_load_json_object_enforces_explicit_byte_limit(tmp_path: Path) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    path = tmp_path / "document.json"
    path.write_bytes(b'{"field":"oversized"}')

    with pytest.raises(ValueError, match="byte"):
        jsonio.load_json_object(path, max_bytes=8)


@pytest.mark.parametrize(
    "raw",
    (
        b'{"items":[0,0,0,0]}',
        b'{"first":0,"second":0,"third":0}',
    ),
    ids=("wide-list", "wide-object"),
)
def test_load_json_object_enforces_explicit_container_member_limit(raw: bytes) -> None:
    jsonio = load_module("ultra_runtime.jsonio")

    with pytest.raises(ValueError, match="container"):
        jsonio.load_json_object_bytes(
            raw,
            source="wide-container.json",
            max_container_items=2,
        )


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (b'{"items":[0]}', {"items": [0]}),
        (b'{"left":0,"right":0}', {"left": 0, "right": 0}),
    ),
    ids=("narrow-list", "narrow-object"),
)
def test_load_json_object_accepts_container_member_limit_boundary(
    raw: bytes,
    expected: dict[str, object],
) -> None:
    jsonio = load_module("ultra_runtime.jsonio")

    assert jsonio.load_json_object_bytes(
        raw,
        source="narrow-container.json",
        max_container_items=2,
    ) == expected


def test_load_json_object_enforces_explicit_depth_limit(tmp_path: Path) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    path = tmp_path / "document.json"
    path.write_text('{"items":[[[0]]]}', encoding="utf-8")

    with pytest.raises(ValueError, match="depth"):
        jsonio.load_json_object(path, max_depth=2)


def test_load_json_object_normalizes_deep_parser_recursion(tmp_path: Path) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    path = tmp_path / "document.json"
    depth = 4_000
    path.write_text('{"items":' + "[" * depth + "0" + "]" * depth + "}", encoding="utf-8")

    with pytest.raises(ValueError, match="resource|depth|limit"):
        jsonio.load_json_object(path)


def test_load_json_object_normalizes_memory_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    path = tmp_path / "document.json"
    path.write_text("{}", encoding="utf-8")

    def fail_read_bytes(self: Path) -> bytes:
        raise MemoryError("simulated allocation failure")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)
    with pytest.raises(ValueError, match="resource|memory|limit"):
        jsonio.load_json_object(path)


@pytest.mark.parametrize(
    "error_type",
    (MemoryError, RecursionError),
    ids=("memory-error", "recursion-error"),
)
@pytest.mark.parametrize(
    "failure_stage",
    ("length", "bom", "decode"),
)
def test_load_json_object_bytes_normalizes_preprocessing_resource_errors(
    error_type: type[BaseException],
    failure_stage: str,
) -> None:
    jsonio = load_module("ultra_runtime.jsonio")
    original_error = error_type(f"simulated {failure_stage} failure")

    if failure_stage == "length":
        class PreprocessingFailure(bytes):
            def __len__(self) -> int:
                raise original_error
    elif failure_stage == "bom":
        class PreprocessingFailure(bytes):
            def startswith(self, prefix: object, *args: object) -> bool:
                raise original_error
    else:
        class PreprocessingFailure(bytes):
            def decode(self, encoding: str = "utf-8", errors: str = "strict") -> str:
                raise original_error

    with pytest.raises(ValueError, match="resource|depth|memory|limit") as caught:
        jsonio.load_json_object_bytes(
            PreprocessingFailure(b"{}"),
            source="preprocessing-failure.json",
        )

    assert caught.value.__cause__ is original_error


def test_schema_loader_rechecks_strict_json_after_disk_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schemas = load_module("ultra_runtime.schemas")
    path = tmp_path / "ultra-common.schema.json"
    path.write_bytes((SCHEMA_ROOT / path.name).read_bytes())
    monkeypatch.setattr(schemas, "schema_root", lambda: tmp_path)
    clear_legacy_cache(schemas._load_schema_cached)

    schemas.load_schema(path.name)
    path.write_bytes(
        path.read_bytes().replace(
            b"{",
            b'{"$schema":"duplicate","$schema":"duplicate",',
            1,
        )
    )

    with pytest.raises(schemas.UltraSchemaError):
        schemas.load_schema(path.name)


def test_compatibility_loader_rechecks_strict_json_after_disk_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schemas = load_module("ultra_runtime.schemas")
    path = tmp_path / "compatibility-matrix.json"
    path.write_bytes(MATRIX_PATH.read_bytes())
    monkeypatch.setattr(schemas, "_compatibility_matrix_path", lambda: path)
    clear_legacy_cache(schemas._load_compatibility_matrix_cached)

    schemas.load_compatibility_matrix()
    document = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        '{"schema_id":"duplicate",' + json.dumps(document, ensure_ascii=False)[1:],
        encoding="utf-8",
    )

    with pytest.raises(schemas.UltraCompatibilityError):
        schemas.load_compatibility_matrix()
