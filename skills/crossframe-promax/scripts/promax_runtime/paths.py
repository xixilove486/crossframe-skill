from __future__ import annotations

from pathlib import PurePosixPath
import unicodedata


_WINDOWS_RESERVED_STEMS = {
    "aux",
    "clock$",
    "con",
    "conin$",
    "conout$",
    "nul",
    "prn",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
_PRIVATE_REASONING_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "chain of thought",
    "hidden-reasoning",
    "hidden_reasoning",
    "hidden reasoning",
    "hidden-thought",
    "hidden_thought",
    "hidden thought",
    "internal-monologue",
    "internal_monologue",
    "internal monologue",
    "scratchpad",
)
_FORBIDDEN_UNICODE_CATEGORIES = {"Cc", "Cf", "Cs", "Zl", "Zp"}


def relative_artifact_path_error(value: object) -> str | None:
    if not isinstance(value, str) or not value or not value.strip():
        return "artifact path must be non-empty non-whitespace text"
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        return "artifact path must be strict UTF-8 text"
    if unicodedata.normalize("NFC", value) != value:
        return "artifact path must use NFC normalization"
    if any(character in value for character in '\\:<>"|?*'):
        return "artifact path must be normalized POSIX text without alternate streams"
    if any(
        unicodedata.category(character) in _FORBIDDEN_UNICODE_CATEGORIES
        for character in value
    ):
        return "artifact path contains a forbidden control or format character"

    parts = value.split("/")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or pure.as_posix() != value
        or value.endswith("/")
        or any(part in {"", ".", ".."} for part in parts)
        or any(part.endswith((".", " ")) for part in parts)
    ):
        return "artifact path must have one canonical relative POSIX spelling"
    for part in parts:
        stem = part.split(".", 1)[0].casefold()
        if stem in _WINDOWS_RESERVED_STEMS:
            return "artifact path contains a reserved Windows device name"
    lowered = value.casefold()
    if any(marker in lowered for marker in _PRIVATE_REASONING_MARKERS):
        return "artifact path may not request or emit hidden private reasoning"
    return None


def is_valid_relative_artifact_path(value: object) -> bool:
    return relative_artifact_path_error(value) is None


def validate_relative_artifact_path(value: object) -> str:
    error = relative_artifact_path_error(value)
    if error is not None:
        raise ValueError(error)
    assert isinstance(value, str)
    return value
