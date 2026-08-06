from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ultra_runtime.constants import current_version_binding
from ultra_runtime.jsonio import atomic_write_json, canonical_json_bytes
from ultra_runtime.schemas import (
    compute_artifact_content_sha256,
    validate_instance,
)
from ultra_runtime.source_integrity import canonical_skill_tree_hashes


SKILL_RELATIVE = Path("skills/crossframe-ultra")
SOURCE_MANIFEST_RELATIVE = Path("references/source-manifest.json")
RELEASE_MANIFEST_RELATIVE = Path("references/release-manifest.json")
RELEASE_STAMP = "2026-08-02T00:00:00Z"


class ReleaseManifestBuildError(ValueError):
    """Raised when the canonical release authority cannot be built safely."""


def _source_manifest(skill_root: Path) -> dict[str, object]:
    path = skill_root / SOURCE_MANIFEST_RELATIVE
    try:
        text = path.read_text(encoding="utf-8")
        if text.startswith("\ufeff"):
            raise ValueError("UTF-8 BOM is forbidden")
        value = json.loads(text)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise ReleaseManifestBuildError(
            "cannot read the promoted source manifest"
        ) from error
    if not isinstance(value, dict):
        raise ReleaseManifestBuildError("source manifest must be a JSON object")
    return value


def _required_value(
    source: Mapping[str, object],
    field: str,
    expected_type: type,
) -> object:
    value = source.get(field)
    if type(value) is not expected_type:
        raise ReleaseManifestBuildError(
            f"source manifest field {field!r} has the wrong type"
        )
    return value


def build_release_manifest(repo: Path) -> dict[str, object]:
    """Build the deterministic public release manifest for the canonical tree."""
    if not isinstance(repo, Path):
        raise TypeError("repo must be a pathlib.Path")
    repo = repo.resolve()
    skill_root = repo / SKILL_RELATIVE

    # This shared authority owns the fixed exclusions and rejects symlinks and
    # reparse points. Do not duplicate its hashing or traversal policy here.
    tree_hashes = canonical_skill_tree_hashes(skill_root)
    source = _source_manifest(skill_root)

    release_artifacts = [
        {
            "path": relative,
            "sha256": digest,
            "media_type": "application/octet-stream",
        }
        for relative, digest in tree_hashes.items()
    ]
    document: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.release-manifest",
        "schema_version": 1,
        "run_id": "ultra-release-v8.2-r1",
        "version_binding": current_version_binding(),
        "generated_at": RELEASE_STAMP,
        "release_id": "ultra-v8.2-r1-runtime-1.1.0",
        "release_state": "stable",
        "stable_pointer": SOURCE_MANIFEST_RELATIVE.as_posix(),
        "framework_source": {
            "path": SOURCE_MANIFEST_RELATIVE.as_posix(),
            "raw_sha256": _required_value(source, "raw_sha256", str),
            "semantic_sha256": _required_value(source, "semantic_sha256", str),
            "alternate_raw_packages": [],
        },
        "compiler": {
            "normalization_algorithm": "ultra-semantic-normalization",
            "normalization_version": "1.0.0",
        },
        "source_counts": {
            "paragraphs": _required_value(source, "paragraph_count", int),
            "headings": _required_value(source, "heading_count", int),
            "tables": _required_value(source, "table_count", int),
            "concepts": _required_value(source, "concept_count", int),
            "contracts": _required_value(source, "contract_count", int),
            "source_units": _required_value(source, "source_unit_count", int),
        },
        "release_artifacts": release_artifacts,
        "built_at": RELEASE_STAMP,
        "validated_at": RELEASE_STAMP,
    }
    document["content_sha256"] = compute_artifact_content_sha256(document)
    validate_instance("ultra-release-manifest.schema.json", document)
    return document


def write_release_manifest(repo: Path) -> Path:
    repo = repo.resolve()
    target = repo / SKILL_RELATIVE / RELEASE_MANIFEST_RELATIVE
    atomic_write_json(target, build_release_manifest(repo))
    return target


def check_release_manifest(repo: Path) -> bool:
    repo = repo.resolve()
    target = repo / SKILL_RELATIVE / RELEASE_MANIFEST_RELATIVE
    try:
        committed = target.read_bytes()
    except OSError:
        return False
    return committed == canonical_json_bytes(build_release_manifest(repo))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build or check the deterministic CrossFrame Ultra release manifest."
    )
    parser.add_argument("--repo", required=True, type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            target = write_release_manifest(args.repo)
            print(f"CrossFrame Ultra release manifest written: {target}")
            return 0
        if check_release_manifest(args.repo):
            print("CrossFrame Ultra release manifest: current")
            return 0
        print("CrossFrame Ultra release manifest: stale", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
