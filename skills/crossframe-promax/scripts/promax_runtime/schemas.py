from __future__ import annotations

import json
import re
from datetime import date as calendar_date
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .paths import is_valid_relative_artifact_path


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
SCHEMA_SUFFIX = ".schema.json"
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_RFC3339_RE = re.compile(
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"[Tt](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.[0-9]+)?"
    r"(?P<zone>[Zz]|(?P<sign>[+-])(?P<offset_hour>[0-9]{2}):(?P<offset_minute>[0-9]{2}))"
)
_URI_SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*")
FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("promax-relative-path")
def _is_promax_relative_artifact_path(value: object) -> bool:
    if not isinstance(value, str):
        return True
    return is_valid_relative_artifact_path(value)


@FORMAT_CHECKER.checks("date")
def _is_rfc3339_full_date(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if _DATE_RE.fullmatch(value) is None:
        return False
    try:
        calendar_date.fromisoformat(value)
    except ValueError:
        return False
    return True


@FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_date_time(value: object) -> bool:
    if not isinstance(value, str):
        return True
    match = _RFC3339_RE.fullmatch(value)
    if match is None:
        return False
    try:
        calendar_date.fromisoformat(match.group("date"))
    except ValueError:
        return False
    if int(match.group("hour")) > 23 or int(match.group("minute")) > 59:
        return False
    if int(match.group("second")) > 60:
        return False
    if match.group("zone").casefold() != "z":
        if int(match.group("offset_hour")) > 23:
            return False
        if int(match.group("offset_minute")) > 59:
            return False
    return True


@FORMAT_CHECKER.checks("uri")
def _is_absolute_network_uri(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if not value or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if _URI_SCHEME_RE.fullmatch(parsed.scheme) is None:
        return False
    if not parsed.netloc or parsed.hostname is None:
        return False
    if port is not None and not 0 <= port <= 65535:
        return False
    return True


@lru_cache(maxsize=1)
def available_schema_names() -> tuple[str, ...]:
    return tuple(sorted(path.name for path in SCHEMA_DIR.glob(f"*{SCHEMA_SUFFIX}") if path.is_file()))


def _checked_schema_name(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise ValueError("schema name must be a non-empty string")
    if Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"schema name must not contain a path: {name!r}")
    if name not in available_schema_names():
        raise KeyError(f"unknown schema: {name}")
    return name


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    checked = _checked_schema_name(name)
    with (SCHEMA_DIR / checked).open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict):
        raise ValueError(f"schema root must be an object: {checked}")
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=1)
def build_registry() -> Registry[Any]:
    resources: list[tuple[str, Resource[Any]]] = []
    for name in available_schema_names():
        schema = load_schema(name)
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError(f"schema has no usable $id: {name}")
        resources.append((schema_id, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


@lru_cache(maxsize=None)
def validator_for(name: str) -> Draft202012Validator:
    schema = load_schema(name)
    return Draft202012Validator(
        schema,
        registry=build_registry(),
        format_checker=FORMAT_CHECKER,
    )


def validate_instance(name: str, instance: Any) -> None:
    validator_for(name).validate(instance)
