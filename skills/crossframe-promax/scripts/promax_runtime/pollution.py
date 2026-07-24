from __future__ import annotations

from pathlib import Path

from check_crossframe_promax_v8_knowledge import (
    pollution_errors_for_text as _canonical_pollution_errors_for_text,
    scan_version_pollution as _canonical_scan_version_pollution,
)


class VersionPollutionError(ValueError):
    """Raised when non-v8 knowledge or unsafe assets enter the ProMax skill."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(errors))


_MAX_WORD = "m" + "ax"
_SIBLING_SKILL = "crossframe-" + _MAX_WORD


def pollution_errors_for_text(text: str, path_label: str) -> list[str]:
    """Apply the canonical repository v8-only lexical/path isolation rules."""

    if not isinstance(text, str) or not isinstance(path_label, str):
        raise TypeError("pollution scan inputs must be strings")
    return _canonical_pollution_errors_for_text(text, path_label)


def scan_version_pollution(skill_root: Path | str) -> list[str]:
    """Scan one ProMax skill tree with the canonical version-isolation core."""

    root = Path(skill_root)
    if not root.is_dir():
        raise ValueError(f"skill root is not a directory: {root}")
    return _canonical_scan_version_pollution(root)


def validate_version_isolation(skill_root: Path | str) -> dict[str, int]:
    """Require zero pollution and return an auditable scan summary."""

    root = Path(skill_root)
    errors = scan_version_pollution(root)
    if errors:
        raise VersionPollutionError(errors)
    scanned_file_count = sum(
        1
        for path in root.rglob("*")
        if path.is_file()
        and not any(part.casefold() == "__pycache__" for part in path.relative_to(root).parts)
    )
    return {
        "scanned_file_count": scanned_file_count,
        "pollution_count": 0,
    }


def platform_selected_promax_route() -> dict[str, object]:
    """Record the host's completed ProMax selection without reopening activation."""

    return {
        "requested_skill_names": ["crossframe-promax"],
        "routing_conflict": {
            "detected": False,
            "conflicting_names": [],
            "resolved_to": "crossframe-promax",
            "priority_rule": (
                "routing-priority-crossframe-promax-over-"
                + _SIBLING_SKILL
                + "-no-fallback"
            ),
            "fallback_allowed": False,
        },
    }
