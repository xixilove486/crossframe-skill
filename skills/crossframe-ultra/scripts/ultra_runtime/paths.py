from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import os
from pathlib import Path
import re
import stat


PRODUCTION_ROOT = Path(r"E:\世界模型\output\crossframe-ultra")
TEST_ROOT = Path(r"E:\世界模型\output\crossframe-ultra-tests")

MAX_COMPONENT_LENGTH = 240
MAX_PATH_LENGTH = 240
ARTIFACT_SUBDIRECTORIES = (
    "U00-U03-evidence",
    "U04-U05-world-volume",
    "U06-U08-inference",
    "U09-U10-verdict",
)

_RUN_ID_PATTERN = re.compile(r"\A\d{8}T\d{6}Z-[0-9a-f]{12}\Z")
_CANONICAL_UTC_PATTERN = re.compile(
    r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{6})?Z\Z",
    re.ASCII,
)
_WINDOWS_RESERVED_BASE_NAMES = frozenset(
    {
        "CON",
        "CONIN$",
        "CONOUT$",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
        *(f"COM{number}" for number in "¹²³"),
        *(f"LPT{number}" for number in "¹²³"),
    }
)
_WINDOWS_ILLEGAL_CHARACTERS = frozenset('<>:"/\\|?*')


try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)


class RunMode(StrEnum):
    PRODUCTION = "production"
    TEST = "test"


@dataclass(frozen=True, slots=True)
class RootPolicy:
    production_root: Path
    test_root: Path


@dataclass(frozen=True, slots=True)
class RunLayout:
    root: Path
    root_staging_dir: Path
    run_dir: Path
    input_dir: Path
    authoring_dir: Path
    artifacts_dir: Path
    delivery_dir: Path
    validation_dir: Path
    validation_current_dir: Path
    validation_attempts_dir: Path
    recovery_dir: Path
    logs_dir: Path


def default_root_policy() -> RootPolicy:
    return RootPolicy(PRODUCTION_ROOT, TEST_ROOT)


def _require_utc(value: datetime, label: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be timezone-aware UTC")


def _parse_canonical_utc(value: object, label: str) -> datetime:
    if not isinstance(value, str) or _CANONICAL_UTC_PATTERN.fullmatch(value) is None:
        raise ValueError(
            f"{label} must be a canonical UTC timestamp ending in Z"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{label} is not a valid UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be UTC-aware")
    canonical = parsed.isoformat(
        timespec="microseconds" if parsed.microsecond else "seconds"
    ).replace("+00:00", "Z")
    if canonical != value:
        raise ValueError(f"{label} must use canonical UTC timestamp spelling")
    return parsed


def create_run_id(now_utc: datetime, entropy: bytes) -> str:
    _require_utc(now_utc, "now_utc")
    if not isinstance(entropy, bytes):
        raise TypeError("entropy must be bytes")
    digest = hashlib.sha256(entropy).hexdigest()[:12]
    return f"{now_utc:%Y%m%dT%H%M%SZ}-{digest}"


def _validate_run_id(run_id: str) -> None:
    if not isinstance(run_id, str):
        raise TypeError("run_id must be a string")
    if _RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise ValueError("run_id must match YYYYMMDDTHHMMSSZ-<12 lowercase hex>")
    try:
        datetime.strptime(run_id[:16], "%Y%m%dT%H%M%SZ")
    except ValueError as error:
        raise ValueError(f"run_id contains an invalid UTC timestamp: {run_id}") from error


def _validate_component(component: str) -> None:
    if component in {"", ".", ".."}:
        raise ValueError(f"unsafe empty or relative path component: {component!r}")
    if len(component) > MAX_COMPONENT_LENGTH:
        raise ValueError(f"path component exceeds {MAX_COMPONENT_LENGTH} characters")
    if component.endswith((" ", ".")):
        raise ValueError(f"Windows path component has a trailing space or dot: {component!r}")
    if any(ord(character) < 32 for character in component):
        raise ValueError("path component contains a control character")
    if any(character in _WINDOWS_ILLEGAL_CHARACTERS for character in component):
        raise ValueError(f"path component contains an illegal Windows character: {component!r}")
    if _is_windows_reserved_name(component):
        raise ValueError(f"path component uses a reserved Windows name: {component!r}")


def _is_windows_reserved_name(component: str) -> bool:
    base_name = component.split(".", 1)[0].upper()
    return base_name in _WINDOWS_RESERVED_BASE_NAMES


def _is_reparse_point(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _ancestor_chain(path: Path) -> tuple[Path, ...]:
    chain: list[Path] = []
    current = path
    while True:
        chain.append(current)
        if current.parent == current:
            break
        current = current.parent
    chain.reverse()
    return tuple(chain)


def _reject_reparse_ancestors(path: Path) -> None:
    for ancestor in _ancestor_chain(path):
        if _is_reparse_point(ancestor):
            raise ValueError(
                f"path crosses a Windows reparse point, symlink, or junction: {ancestor}"
            )


def _normalize_resolved_windows_prefix(path: Path) -> Path:
    text = str(path)
    extended_prefix = "\\\\?\\"
    if not text.startswith(extended_prefix):
        return path
    remainder = text[len(extended_prefix) :]
    if remainder.upper().startswith("UNC\\"):
        return Path("\\\\" + remainder[4:])
    return Path(remainder)


def _validate_root(root: Path) -> None:
    if not isinstance(root, Path):
        raise TypeError("root must be a pathlib.Path")
    if not root.is_absolute():
        raise ValueError("root must be absolute")
    if root.drive.startswith("\\\\") or root.anchor.startswith("\\\\"):
        raise ValueError("UNC and Windows device roots are not allowed")
    if any(part == ".." for part in root.parts):
        raise ValueError("root cannot contain '..'")
    anchor = Path(root.anchor)
    for component in root.relative_to(anchor).parts:
        _validate_component(component)
    if len(str(root)) > MAX_PATH_LENGTH:
        raise ValueError(f"root path exceeds {MAX_PATH_LENGTH} characters")


def assert_safe_descendant(root: Path, candidate: Path) -> Path:
    _validate_root(root)
    if not isinstance(candidate, Path):
        raise TypeError("candidate must be a pathlib.Path")
    if any(part == ".." for part in candidate.parts):
        raise ValueError("candidate cannot contain '..'")
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        relative = candidate.relative_to(root)
    except (ValueError, OSError) as error:
        raise ValueError(f"candidate is outside the selected root: {candidate}") from error
    if not relative.parts:
        raise ValueError("candidate must be a strict descendant of the selected root")
    for component in relative.parts:
        _validate_component(component)
    if len(str(candidate)) > MAX_PATH_LENGTH:
        raise ValueError(f"candidate path exceeds {MAX_PATH_LENGTH} characters")

    _reject_reparse_ancestors(root)
    _reject_reparse_ancestors(candidate)
    resolved_root = _normalize_resolved_windows_prefix(root.resolve(strict=False))
    resolved_candidate = _normalize_resolved_windows_prefix(
        candidate.resolve(strict=False)
    )
    try:
        resolved_relative = resolved_candidate.relative_to(resolved_root)
    except (ValueError, OSError) as error:
        raise ValueError(
            f"resolved candidate escapes the selected root: {resolved_candidate}"
        ) from error
    if not resolved_relative.parts:
        raise ValueError("resolved candidate must remain a strict descendant")
    return candidate


def _validate_policy(policy: RootPolicy) -> None:
    if not isinstance(policy, RootPolicy):
        raise TypeError("policy must be a RootPolicy")
    _validate_root(policy.production_root)
    _validate_root(policy.test_root)
    if policy.production_root == policy.test_root:
        raise ValueError("production and test roots must be distinct")
    if policy.production_root == TEST_ROOT:
        raise ValueError("the fixed test root cannot occupy the production root slot")
    if policy.test_root == PRODUCTION_ROOT:
        raise ValueError("the fixed production root cannot occupy the test root slot")
    for first, second in (
        (policy.production_root, policy.test_root),
        (policy.test_root, policy.production_root),
    ):
        try:
            second.relative_to(first)
        except ValueError:
            continue
        raise ValueError("production and test roots cannot contain one another")


def build_run_layout(mode: RunMode, run_id: str, policy: RootPolicy) -> RunLayout:
    if not isinstance(mode, RunMode):
        raise TypeError("mode must be a RunMode")
    _validate_run_id(run_id)
    _validate_policy(policy)
    root = policy.production_root if mode is RunMode.PRODUCTION else policy.test_root
    run_dir = root / "runs" / run_id[:4] / run_id[4:6] / run_id
    paths = {
        "root_staging_dir": root / ".staging",
        "run_dir": run_dir,
        "input_dir": run_dir / "input",
        "authoring_dir": run_dir / "work" / "authoring",
        "artifacts_dir": run_dir / "artifacts",
        "delivery_dir": run_dir / "delivery",
        "validation_dir": run_dir / "validation",
        "validation_current_dir": run_dir / "validation" / "current",
        "validation_attempts_dir": run_dir / "validation" / "attempts",
        "recovery_dir": run_dir / "recovery",
        "logs_dir": run_dir / "logs",
    }
    for candidate in paths.values():
        assert_safe_descendant(root, candidate)
    return RunLayout(root=root, **paths)
