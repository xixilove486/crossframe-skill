from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .errors import CanonicalJSONError, JSONDocumentError


def _reject_non_string_keys(value: object, pointer: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise CanonicalJSONError(
                    f"canonical JSON object key at {pointer} must be a string"
                )
            _reject_non_string_keys(child, f"{pointer}/{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_non_string_keys(child, f"{pointer}/{index}")


def canonical_json_bytes(value: object) -> bytes:
    """Return one deterministic UTF-8 JSON representation without a newline."""

    _reject_non_string_keys(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, OverflowError) as error:
        raise CanonicalJSONError(f"value is not canonical JSON: {error}") from error
    try:
        return text.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise CanonicalJSONError(
            f"value contains text that is not valid strict UTF-8: {error}"
        ) from error


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _require_strict_utf8_text(value: str, *, pointer: str) -> None:
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ValueError(f"text at {pointer} is not strict UTF-8") from error


def _validate_loaded_json(value: object, *, pointer: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require_strict_utf8_text(key, pointer=f"{pointer}/<key>")
            _validate_loaded_json(child, pointer=f"{pointer}/{key!r}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_loaded_json(child, pointer=f"{pointer}/{index}")
    elif isinstance(value, str):
        _require_strict_utf8_text(value, pointer=pointer)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {pointer} is forbidden")


def _parse_json_text(text: str, *, source: str) -> object:
    try:
        value = json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
        _validate_loaded_json(value)
        return value
    except (json.JSONDecodeError, ValueError) as error:
        raise JSONDocumentError(f"invalid JSON in {source}: {error}") from error


def _read_utf8(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise JSONDocumentError(f"cannot read strict UTF-8 JSON from {path}: {error}") from error


def load_json_bytes(raw: bytes, *, source: str) -> object:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise JSONDocumentError(f"cannot decode strict UTF-8 JSON from {source}: {error}") from error
    return _parse_json_text(text, source=source)


def load_json(path: Path | str) -> object:
    source_path = Path(path)
    return _parse_json_text(_read_utf8(source_path), source=str(source_path))


def load_jsonl(path: Path | str) -> list[dict[str, object]]:
    source_path = Path(path)
    try:
        raw = source_path.read_bytes()
    except OSError as error:
        raise JSONDocumentError(f"cannot read JSONL from {source_path}: {error}") from error
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise JSONDocumentError(f"JSONL document must end with a newline: {source_path}")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise JSONDocumentError(f"JSONL document is not strict UTF-8: {source_path}") from error

    records: list[dict[str, object]] = []
    for line_number, line in enumerate(text[:-1].split("\n"), start=1):
        if not line.strip():
            raise JSONDocumentError(
                f"blank JSONL record at {source_path}:{line_number}"
            )
        value = _parse_json_text(
            line,
            source=f"{source_path}:{line_number}",
        )
        if not isinstance(value, dict):
            raise JSONDocumentError(
                f"JSONL record must be an object at {source_path}:{line_number}"
            )
        records.append(value)
    return records
