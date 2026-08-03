from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import current_version_binding
from .jsonio import canonical_json_bytes, load_json_object, sha256_bytes
from .paths import RunLayout, _require_utc, _validate_run_id, assert_safe_descendant
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


MANIFEST_FILENAME = "ultra-artifact-manifest.json"
PARTIAL_ARTICLE_PATH = "work/authoring/article.partial.md"
READ_EVENTS_PATH = "artifacts/U00-U03-evidence/ultra-read-events.jsonl"
OFFICIAL_DELIVERY_PATHS = (
    "delivery/CrossFrame-Ultra-完整文章.md",
    "delivery/完整推演档案.md",
    "delivery/工件索引.md",
)


class ArtifactManifestError(ValueError):
    def __init__(self, error_code: str, message: str, *, artifact: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.artifact = artifact


def _fail(error_code: str, message: str, artifact: str) -> ArtifactManifestError:
    return ArtifactManifestError(error_code, message, artifact=artifact)


def _validate_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    _validate_run_id(layout.run_dir.name)
    expected = (
        layout.root
        / "runs"
        / layout.run_dir.name[:4]
        / layout.run_dir.name[4:6]
        / layout.run_dir.name
    )
    if layout.run_dir != expected:
        raise ValueError("run layout does not match its fixed root and run_id")
    for candidate in (
        layout.run_dir,
        layout.artifacts_dir,
        layout.authoring_dir,
        layout.delivery_dir,
        layout.artifacts_dir / MANIFEST_FILENAME,
    ):
        assert_safe_descendant(layout.root, candidate)


def _iso_utc(value: datetime) -> str:
    _require_utc(value, "generated_at")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _relative_run_path(layout: RunLayout, path: Path) -> str:
    assert_safe_descendant(layout.root, path)
    try:
        relative = path.relative_to(layout.run_dir)
    except (ValueError, OSError) as error:
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            f"artifact path is outside the selected run: {path}",
            str(path),
        ) from error
    return relative.as_posix()


def _media_type(path: Path) -> str:
    if path.suffix == ".json":
        return "application/json"
    if path.suffix == ".jsonl":
        return "application/x-ndjson"
    if path.suffix == ".md":
        return "text/markdown"
    return "application/octet-stream"


def _metadata_for_file(layout: RunLayout, path: Path) -> tuple[str, str]:
    relative = _relative_run_path(layout, path)
    if relative == READ_EVENTS_PATH:
        return "crossframe.ultra.v82.read-event", "U1"
    if path.suffix == ".json":
        try:
            value = load_json_object(path)
        except (OSError, TypeError, ValueError) as error:
            raise _fail(
                "ULTRA-MANIFEST-INVALID",
                f"cannot inventory JSON artifact {relative}: {error}",
                relative,
            ) from error
        schema_id = value.get("schema_id")
        phase_id = value.get("phase_id")
        if not isinstance(schema_id, str) or not schema_id.startswith(
            "crossframe.ultra.v82."
        ):
            raise _fail(
                "ULTRA-MANIFEST-INVALID",
                f"JSON artifact has no Ultra schema authority: {relative}",
                relative,
            )
        if not isinstance(phase_id, str):
            raise _fail(
                "ULTRA-MANIFEST-INVALID",
                f"JSON artifact has no phase authority: {relative}",
                relative,
            )
        return schema_id, phase_id
    if relative == PARTIAL_ARTICLE_PATH:
        return "crossframe.ultra.v82.article-partial", "U11"
    if relative.startswith("work/authoring/"):
        return "crossframe.ultra.v82.authoring-document", "U11"
    raise _fail(
        "ULTRA-MANIFEST-INVALID",
        f"unrecognized artifact type in validation inventory: {relative}",
        relative,
    )


def _inventory_files(layout: RunLayout) -> tuple[Path, ...]:
    files: list[Path] = []
    manifest_path = layout.artifacts_dir / MANIFEST_FILENAME
    for directory in (layout.artifacts_dir, layout.authoring_dir):
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path == manifest_path:
                continue
            _relative_run_path(layout, path)
            files.append(path)
    return tuple(sorted(files, key=lambda item: _relative_run_path(layout, item)))


def _delivery_inventory(layout: RunLayout) -> tuple[dict[str, str], ...]:
    records: list[dict[str, str]] = []
    existing: list[str] = []
    for relative in OFFICIAL_DELIVERY_PATHS:
        path = layout.run_dir / Path(relative)
        assert_safe_descendant(layout.root, path)
        if not path.exists():
            continue
        if not path.is_file():
            raise _fail(
                "ULTRA-PREMATURE-PUBLISH",
                f"official delivery path is not a regular file: {relative}",
                relative,
            )
        existing.append(relative)
        records.append(
            {
                "path": relative,
                "sha256": sha256_bytes(path.read_bytes()),
                "media_type": "text/markdown",
            }
        )
    if existing and len(existing) != len(OFFICIAL_DELIVERY_PATHS):
        raise _fail(
            "ULTRA-PREMATURE-PUBLISH",
            "official delivery is only partially published",
            "delivery",
        )
    return tuple(records)


def build_artifact_manifest(
    layout: RunLayout,
    *,
    phase_chain_head_sha256: str,
    validator_set_sha256: str,
    generated_at: datetime,
) -> dict[str, object]:
    _validate_layout(layout)
    if not isinstance(phase_chain_head_sha256, str) or len(phase_chain_head_sha256) != 64:
        raise ValueError("phase_chain_head_sha256 must be a SHA-256 digest")
    if not isinstance(validator_set_sha256, str) or len(validator_set_sha256) != 64:
        raise ValueError("validator_set_sha256 must be a SHA-256 digest")
    artifacts: list[dict[str, str]] = []
    for path in _inventory_files(layout):
        schema_id, phase_id = _metadata_for_file(layout, path)
        artifacts.append(
            {
                "path": _relative_run_path(layout, path),
                "sha256": sha256_bytes(path.read_bytes()),
                "schema_id": schema_id,
                "phase_id": phase_id,
                "media_type": _media_type(path),
            }
        )
    if not artifacts:
        raise ValueError("artifact manifest cannot be empty")
    delivery = list(_delivery_inventory(layout))
    value: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.artifact-manifest",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": _iso_utc(generated_at),
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "phase_chain_head_sha256": phase_chain_head_sha256,
        "validator_set_sha256": validator_set_sha256,
        "artifacts": artifacts,
        "delivery_artifacts": delivery,
        "official_delivery_published": bool(delivery),
    }
    value["content_sha256"] = compute_artifact_content_sha256(value)
    validate_phase_artifact(
        "ultra-artifact-manifest.schema.json",
        value,
        expected_schema_id="crossframe.ultra.v82.artifact-manifest",
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    return value


def _safe_manifest_artifact_path(layout: RunLayout, relative: object) -> Path:
    if not isinstance(relative, str) or not relative:
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            "manifest artifact path must be a non-empty relative path",
            "artifacts/ultra-artifact-manifest.json",
        )
    if "\\" in relative or relative.startswith("/"):
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            f"manifest artifact path is not canonical: {relative!r}",
            relative,
        )
    parts = Path(relative).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            f"manifest artifact path escapes its run: {relative!r}",
            relative,
        )
    if not (
        relative.startswith("artifacts/") or relative.startswith("work/authoring/")
    ):
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            f"manifest artifact is outside an owned inventory slot: {relative!r}",
            relative,
        )
    candidate = layout.run_dir / Path(relative)
    try:
        assert_safe_descendant(layout.root, candidate)
        candidate.relative_to(layout.run_dir)
    except (TypeError, ValueError, OSError) as error:
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            f"manifest artifact resolves outside the run: {relative!r}",
            relative,
        ) from error
    return candidate


def _validate_embedded_authority(
    layout: RunLayout, path: Path, record: Mapping[str, Any]
) -> None:
    relative = str(record["path"])
    if path.suffix != ".json":
        return
    try:
        raw = path.read_bytes()
        value = load_json_object(path)
    except (OSError, TypeError, ValueError) as error:
        raise _fail(
            "ULTRA-ARTIFACT-HASH",
            f"cannot load inventoried JSON artifact {relative}: {error}",
            relative,
        ) from error
    if raw != canonical_json_bytes(value):
        raise _fail(
            "ULTRA-ARTIFACT-HASH",
            f"JSON artifact is not stored as canonical bytes: {relative}",
            relative,
        )
    if value.get("schema_id") != record.get("schema_id"):
        raise _fail(
            "ULTRA-ARTIFACT-HASH",
            f"manifest schema authority differs from disk artifact: {relative}",
            relative,
        )
    if value.get("phase_id") != record.get("phase_id"):
        raise _fail(
            "ULTRA-ARTIFACT-HASH",
            f"manifest phase authority differs from disk artifact: {relative}",
            relative,
        )
    if value.get("run_id") != layout.run_dir.name:
        raise _fail(
            "ULTRA-CROSS-RUN-MANIFEST",
            f"artifact belongs to another run: {relative}",
            relative,
        )
    if value.get("version_binding") != current_version_binding():
        raise _fail(
            "ULTRA-ARTIFACT-HASH",
            f"artifact version binding is not current: {relative}",
            relative,
        )
    if value.get("content_sha256") != compute_artifact_content_sha256(value):
        raise _fail(
            "ULTRA-ARTIFACT-HASH",
            f"artifact content hash differs from its payload: {relative}",
            relative,
        )


def validate_artifact_manifest(
    layout: RunLayout,
    manifest_path: Path,
) -> dict[str, object]:
    _validate_layout(layout)
    expected_path = layout.artifacts_dir / MANIFEST_FILENAME
    if manifest_path != expected_path:
        raise _fail(
            "ULTRA-PATH-ESCAPE",
            "artifact manifest must occupy its fixed run path",
            str(manifest_path),
        )
    assert_safe_descendant(layout.root, manifest_path)
    try:
        raw = manifest_path.read_bytes()
        value = load_json_object(manifest_path)
    except (OSError, TypeError, ValueError) as error:
        raise _fail(
            "ULTRA-MANIFEST-INVALID",
            f"cannot load artifact manifest: {error}",
            "artifacts/ultra-artifact-manifest.json",
        ) from error
    if value.get("run_id") != layout.run_dir.name:
        raise _fail(
            "ULTRA-CROSS-RUN-MANIFEST",
            "artifact manifest belongs to another run",
            "artifacts/ultra-artifact-manifest.json",
        )
    records = value.get("artifacts")
    if isinstance(records, list):
        for record in records:
            if isinstance(record, Mapping):
                _safe_manifest_artifact_path(layout, record.get("path"))
    try:
        snapshot = validate_phase_artifact(
            "ultra-artifact-manifest.schema.json",
            value,
            expected_schema_id="crossframe.ultra.v82.artifact-manifest",
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_phase_id="U12",
        )
    except Exception as error:
        raise _fail(
            "ULTRA-MANIFEST-INVALID",
            f"artifact manifest violates its closed authority: {error}",
            "artifacts/ultra-artifact-manifest.json",
        ) from error
    if raw != canonical_json_bytes(snapshot):
        raise _fail(
            "ULTRA-MANIFEST-INVALID",
            "artifact manifest is not stored as canonical bytes",
            "artifacts/ultra-artifact-manifest.json",
        )

    seen: set[str] = set()
    for record in snapshot["artifacts"]:
        relative = str(record["path"])
        if relative in seen:
            raise _fail(
                "ULTRA-MANIFEST-INVALID",
                f"duplicate artifact manifest path: {relative}",
                relative,
            )
        seen.add(relative)
        path = _safe_manifest_artifact_path(layout, relative)
        if not path.is_file():
            raise _fail(
                "ULTRA-ARTIFACT-HASH",
                f"manifest artifact is missing or not regular: {relative}",
                relative,
            )
        if sha256_bytes(path.read_bytes()) != record["sha256"]:
            raise _fail(
                "ULTRA-ARTIFACT-HASH",
                f"manifest artifact hash differs from disk: {relative}",
                relative,
            )
        _validate_embedded_authority(layout, path, record)

    actual = {
        _relative_run_path(layout, path) for path in _inventory_files(layout)
    }
    if actual != seen:
        raise _fail(
            "ULTRA-MANIFEST-INVALID",
            "manifest inventory differs from the disk artifact inventory",
            "artifacts/ultra-artifact-manifest.json",
        )

    actual_delivery = _delivery_inventory(layout)
    declared_delivery = tuple(snapshot["delivery_artifacts"])
    if snapshot["official_delivery_published"]:
        if len(actual_delivery) != len(OFFICIAL_DELIVERY_PATHS):
            raise _fail(
                "ULTRA-PREMATURE-PUBLISH",
                "published manifest lacks all official delivery files",
                "delivery",
            )
        if tuple(actual_delivery) != declared_delivery:
            raise _fail(
                "ULTRA-ARTIFACT-HASH",
                "official delivery hashes differ from the manifest",
                "delivery",
            )
    elif actual_delivery or declared_delivery:
        raise _fail(
            "ULTRA-PREMATURE-PUBLISH",
            "official delivery appeared before a published validation generation",
            "delivery",
        )
    return snapshot
