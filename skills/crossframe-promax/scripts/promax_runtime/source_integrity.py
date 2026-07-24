from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping, Sequence

from jsonschema import ValidationError

from .jsonio import load_json_bytes, sha256_json
from .safe_files import read_stable_regular_file
from .schemas import validate_instance


V8_SOURCE_SNAPSHOT_SHA256 = (
    "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
)
V8_PARAGRAPH_COUNT = 3863
V8_NON_WHITESPACE_CHARS = 155721
V8_TABLE_COUNT = 117
V8_SECTION_COUNT = 16
V8_CONCEPT_COUNT = 709
V8_CONTROL_ASSET_SHA256 = {
    "source_manifest": "ab267fa7e683c411d6397a5e1addc80013a47897dd0d92543be61ba4493d05d7",
    "concept_registry": "a9f2e57c3fb7147aaab8a291f5ebaf130ada5abb84ae58c0ca1797bb7a3d5b6f",
    "contract_map": "601a739c5ce8f994e4832e1e1d57973be52c2522d2c2f464ee403a73cae65c8e",
    "route_map": "ef084b0cd98fd6de01dd40f2701b4b010f3041e83f5e38c68556e9288f2c2fd0",
}
_CANONICAL_STRUCTURE_MARKER = b"\n## Canonical Structure\n\n```json\n"
_CANONICAL_STRUCTURE_END = b"\n```\n"


class SourceIntegrityError(ValueError):
    """Raised when the v8 source or its read-event proof is not exact."""


def sha256_file(path: Path | str) -> str:
    source = Path(path)
    raw = read_stable_regular_file(source, within_root=source.parent)
    return hashlib.sha256(raw).hexdigest()


def _load_object_and_hash(path: Path, *, root: Path) -> tuple[dict[str, object], str]:
    raw = read_stable_regular_file(path, within_root=root)
    value = load_json_bytes(raw, source=str(path))
    if not isinstance(value, dict):
        raise ValueError(f"canonical v8 asset must be a JSON object: {path}")
    return value, hashlib.sha256(raw).hexdigest()


def _require_exact(
    document: Mapping[str, object],
    expected: Mapping[str, object],
    *,
    source: Path,
) -> None:
    for field, expected_value in expected.items():
        actual = document.get(field)
        if actual != expected_value:
            raise ValueError(
                f"canonical v8 asset {source} has {field}={actual!r}; "
                f"expected {expected_value!r}"
            )


def _control_asset_paths(references: Path) -> dict[str, Path]:
    return {
        "source_manifest": references / "source_manifest.json",
        "concept_registry": references
        / "concept-registry"
        / "v8-concept-registry.json",
        "contract_map": references
        / "concept-contracts"
        / "v8-contract-map.json",
        "route_map": references / "v8-route-map.json",
    }


def _load_control_assets(
    references: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, str], dict[str, Path]]:
    paths = _control_asset_paths(references)
    loaded = {
        name: _load_object_and_hash(path, root=references)
        for name, path in paths.items()
    }
    documents = {name: document for name, (document, _) in loaded.items()}
    hashes = {name: digest for name, (_, digest) in loaded.items()}
    for name, expected_digest in V8_CONTROL_ASSET_SHA256.items():
        if hashes.get(name) != expected_digest:
            raise SourceIntegrityError(
                f"canonical v8 control asset hash mismatch: {paths[name]}"
            )
    return documents, hashes, paths


def _load_canonical_structure(
    path: Path,
    *,
    root: Path,
    verified_raw: bytes | None = None,
) -> object:
    raw = (
        read_stable_regular_file(path, within_root=root)
        if verified_raw is None
        else verified_raw
    )
    if raw.count(_CANONICAL_STRUCTURE_MARKER) != 1:
        raise SourceIntegrityError(
            f"source file must contain exactly one canonical JSON structure: {path}"
        )
    _, payload_and_tail = raw.split(_CANONICAL_STRUCTURE_MARKER, 1)
    if _CANONICAL_STRUCTURE_END not in payload_and_tail:
        raise SourceIntegrityError(f"canonical JSON structure is not closed: {path}")
    payload, _ = payload_and_tail.split(_CANONICAL_STRUCTURE_END, 1)
    try:
        return load_json_bytes(payload, source=f"{path} canonical structure")
    except ValueError as error:
        raise SourceIntegrityError(
            f"cannot load canonical JSON structure from {path}: {error}"
        ) from error


def _anchor_number(anchor: object, *, prefix: str, width: int) -> int:
    if not isinstance(anchor, str):
        raise SourceIntegrityError(f"source anchor must be text: {anchor!r}")
    expected_length = len(prefix) + width
    if (
        len(anchor) != expected_length
        or not anchor.startswith(prefix)
        or not anchor[len(prefix) :].isdigit()
    ):
        raise SourceIntegrityError(f"invalid source anchor: {anchor!r}")
    return int(anchor[len(prefix) :])


def _verify_manifest_files(
    manifest: Mapping[str, object],
    *,
    references: Path,
) -> dict[str, bytes]:
    raw_records = manifest.get("files")
    if not isinstance(raw_records, list) or len(raw_records) != 138:
        raise SourceIntegrityError("v8 source manifest must bind exactly 138 files")
    verified: dict[str, bytes] = {}
    for index, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, Mapping) or set(raw_record) != {
            "path",
            "sha256",
            "size",
        }:
            raise SourceIntegrityError(f"invalid source manifest file record at {index}")
        relative = raw_record.get("path")
        digest = raw_record.get("sha256")
        size = raw_record.get("size")
        if (
            not isinstance(relative, str)
            or not relative.startswith("v8-full-source/")
            or relative.startswith("/")
            or "\\" in relative
            or ":" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
            or relative in verified
        ):
            raise SourceIntegrityError(
                f"invalid or duplicate source manifest path: {relative!r}"
            )
        if not isinstance(digest, str) or len(digest) != 64:
            raise SourceIntegrityError(f"invalid manifest hash for {relative}")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise SourceIntegrityError(f"invalid manifest size for {relative}")
        path = references.joinpath(*relative.split("/"))
        raw = read_stable_regular_file(path, within_root=references)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise SourceIntegrityError(
                f"v8 source file differs from the exact manifest content: {relative}"
            )
        verified[relative] = raw
    return verified


def load_canonical_read_targets(
    repo: Path | str,
) -> tuple[dict[str, object], ...]:
    """Return the exact 3,863 paragraph and 117 table read targets.

    Content digests bind canonical JSON records, including their anchor IDs;
    visible Markdown marker counts are never accepted as read evidence.
    """

    repo_root = Path(repo).resolve()
    references = repo_root / "skills" / "crossframe-promax" / "references"
    documents, _, paths = _load_control_assets(references)
    manifest = documents["source_manifest"]
    _require_exact(
        manifest,
        {
            "schema_id": "crossframe.promax.v8.source-manifest",
            "schema_version": 1,
            "framework_version": "v8.0",
            "snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "paragraph_count": V8_PARAGRAPH_COUNT,
            "non_whitespace_chars": V8_NON_WHITESPACE_CHARS,
            "table_count": V8_TABLE_COUNT,
            "section_count": V8_SECTION_COUNT,
        },
        source=paths["source_manifest"],
    )
    verified_files = _verify_manifest_files(manifest, references=references)

    raw_ranges = manifest.get("source_ranges")
    if not isinstance(raw_ranges, list) or len(raw_ranges) != 17:
        raise SourceIntegrityError(
            "v8 source manifest must bind the envelope plus 16 source sections"
        )

    targets: list[dict[str, object]] = []
    expected_paragraph_number = 1
    for raw_range in raw_ranges:
        if not isinstance(raw_range, Mapping):
            raise SourceIntegrityError("source range must be a structured object")
        filename = raw_range.get("file")
        if not isinstance(filename, str):
            raise SourceIntegrityError("source range file must be text")
        relative = f"v8-full-source/{filename}"
        if relative not in verified_files:
            raise SourceIntegrityError(f"source range is absent from manifest: {filename}")
        structure = _load_canonical_structure(
            references / relative,
            root=references,
            verified_raw=verified_files[relative],
        )
        if not isinstance(structure, list):
            raise SourceIntegrityError(
                f"canonical paragraph structure must be an array: {filename}"
            )
        start = _anchor_number(
            raw_range.get("paragraph_start"), prefix="V8-P", width=4
        )
        end = _anchor_number(
            raw_range.get("paragraph_end"), prefix="V8-P", width=4
        )
        if start != expected_paragraph_number or len(structure) != end - start + 1:
            raise SourceIntegrityError(
                f"paragraph range/count mismatch in canonical source: {filename}"
            )
        for number, raw_paragraph in zip(range(start, end + 1), structure):
            if not isinstance(raw_paragraph, Mapping) or set(raw_paragraph) != {
                "pid",
                "style",
                "text",
            }:
                raise SourceIntegrityError(
                    f"invalid canonical paragraph record in {filename}"
                )
            anchor = f"V8-P{number:04d}"
            if raw_paragraph.get("pid") != anchor:
                raise SourceIntegrityError(
                    f"paragraph anchor order mismatch in {filename}: {anchor}"
                )
            if not isinstance(raw_paragraph.get("style"), str) or not isinstance(
                raw_paragraph.get("text"), str
            ):
                raise SourceIntegrityError(
                    f"paragraph content must be exact text in {filename}: {anchor}"
                )
            targets.append(
                {
                    "source_kind": "paragraph",
                    "source_anchor": anchor,
                    "source_file": filename,
                    "content_sha256": sha256_json(dict(raw_paragraph)),
                }
            )
        expected_paragraph_number = end + 1
    if expected_paragraph_number != V8_PARAGRAPH_COUNT + 1:
        raise SourceIntegrityError("canonical paragraph coverage does not end at V8-P3863")

    for number in range(1, V8_TABLE_COUNT + 1):
        anchor = f"V8-T{number:03d}"
        relative = f"v8-full-source/tables/{anchor}.md"
        if relative not in verified_files:
            raise SourceIntegrityError(f"table is absent from source manifest: {anchor}")
        structure = _load_canonical_structure(
            references / relative,
            root=references,
            verified_raw=verified_files[relative],
        )
        if not isinstance(structure, Mapping) or structure.get("tid") != anchor:
            raise SourceIntegrityError(f"canonical table identity mismatch: {anchor}")
        if set(structure) != {"tid", "paragraph_ids", "rows", "cell_paragraph_ids"}:
            raise SourceIntegrityError(f"canonical table shape mismatch: {anchor}")
        targets.append(
            {
                "source_kind": "table",
                "source_anchor": anchor,
                "source_file": f"tables/{anchor}.md",
                "content_sha256": sha256_json(dict(structure)),
            }
        )

    if len(targets) != V8_PARAGRAPH_COUNT + V8_TABLE_COUNT:
        raise SourceIntegrityError("canonical read target inventory is incomplete")
    return tuple(targets)


def build_read_events(
    repo: Path | str,
    *,
    run_id: str,
    read_at: str,
) -> list[dict[str, object]]:
    """Materialize the deterministic P1 proof for every canonical v8 target.

    This function only records the bytes that the runtime actually traverses.
    It does not generate analysis, concept decisions, or any other model-owned
    semantics.
    """

    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be non-empty text")
    if not isinstance(read_at, str) or not read_at.strip():
        raise ValueError("read_at must be a non-empty timestamp")
    return [
        {
            "schema_id": "crossframe.promax.v8.read-event",
            "schema_version": 1,
            "event_id": f"read-event-{sequence:06d}",
            "run_id": run_id,
            "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "sequence": sequence,
            "source_kind": target["source_kind"],
            "source_anchor": target["source_anchor"],
            "source_file": target["source_file"],
            "content_sha256": target["content_sha256"],
            "read_at": read_at.strip(),
        }
        for sequence, target in enumerate(load_canonical_read_targets(repo), start=1)
    ]


def validate_read_event_coverage(
    events: Sequence[Mapping[str, object]],
    *,
    repo: Path | str,
    expected_run_id: str,
    expected_source_snapshot_sha256: str,
) -> dict[str, object]:
    """Validate exact ordered read proof for every canonical paragraph/table."""

    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise SourceIntegrityError("read events must be an ordered sequence")
    if expected_source_snapshot_sha256 != V8_SOURCE_SNAPSHOT_SHA256:
        raise SourceIntegrityError("read coverage must bind the exact v8 source snapshot")
    targets = load_canonical_read_targets(repo)
    if len(events) != len(targets):
        raise SourceIntegrityError(
            f"read-event coverage must contain exactly {len(targets)} records"
        )
    seen_event_ids: set[str] = set()
    seen_anchors: set[str] = set()
    for sequence, (raw_event, target) in enumerate(zip(events, targets), start=1):
        if not isinstance(raw_event, Mapping):
            raise SourceIntegrityError(f"read event {sequence} must be an object")
        event = dict(raw_event)
        try:
            validate_instance("promax-read-event.schema.json", event)
        except ValidationError as error:
            raise SourceIntegrityError(
                f"read event {sequence} violates its schema: {error.message}"
            ) from error
        if event.get("run_id") != expected_run_id:
            raise SourceIntegrityError(f"read event {sequence} is bound to another run")
        if event.get("source_snapshot_sha256") != expected_source_snapshot_sha256:
            raise SourceIntegrityError(
                f"read event {sequence} is bound to another source snapshot"
            )
        event_id = event.get("event_id")
        anchor = event.get("source_anchor")
        if not isinstance(event_id, str) or event_id in seen_event_ids:
            raise SourceIntegrityError(f"duplicate read event identity: {event_id!r}")
        if not isinstance(anchor, str) or anchor in seen_anchors:
            raise SourceIntegrityError(f"duplicate read source anchor: {anchor!r}")
        seen_event_ids.add(event_id)
        seen_anchors.add(anchor)
        if event.get("sequence") != sequence:
            raise SourceIntegrityError(
                f"read event sequence is not contiguous at record {sequence}"
            )
        for field in (
            "source_kind",
            "source_anchor",
            "source_file",
            "content_sha256",
        ):
            if event.get(field) != target[field]:
                raise SourceIntegrityError(
                    f"read event {sequence} does not bind canonical {field}"
                )
    return {
        "source_snapshot_sha256": expected_source_snapshot_sha256,
        "paragraph_count": V8_PARAGRAPH_COUNT,
        "table_count": V8_TABLE_COUNT,
        "event_count": len(targets),
    }


def build_source_snapshot(
    repo: Path | str,
    *,
    verified_at: str,
) -> dict[str, object]:
    """Freeze the four canonical v8 control assets into one runtime snapshot.

    Full paragraph/table byte validation remains the P1 validator's job.  This
    helper binds a run to the committed manifest and knowledge graph files so a
    later report cannot silently substitute another set of control assets.
    """

    repo_root = Path(repo).resolve()
    references = repo_root / "skills" / "crossframe-promax" / "references"
    documents, hashes, paths = _load_control_assets(references)

    _require_exact(
        documents["source_manifest"],
        {
            "schema_id": "crossframe.promax.v8.source-manifest",
            "schema_version": 1,
            "framework_version": "v8.0",
            "snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "paragraph_count": V8_PARAGRAPH_COUNT,
            "non_whitespace_chars": V8_NON_WHITESPACE_CHARS,
            "table_count": V8_TABLE_COUNT,
            "section_count": V8_SECTION_COUNT,
        },
        source=paths["source_manifest"],
    )
    _require_exact(
        documents["concept_registry"],
        {
            "schema_id": "crossframe.promax.v8.concept-registry",
            "schema_version": 1,
            "framework_version": "v8.0",
            "snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "concept_count": V8_CONCEPT_COUNT,
        },
        source=paths["concept_registry"],
    )
    _require_exact(
        documents["contract_map"],
        {
            "schema_id": "crossframe.promax.v8.contract-map",
            "schema_version": 1,
            "framework_version": "v8.0",
            "snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "contract_count": 3,
        },
        source=paths["contract_map"],
    )
    _require_exact(
        documents["route_map"],
        {
            "schema_id": "crossframe.promax.v8.route-map",
            "schema_version": 1,
            "framework_version": "v8.0",
            "snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
            "route_count": 16,
        },
        source=paths["route_map"],
    )
    for name, path in paths.items():
        if sha256_file(path) != hashes[name]:
            raise ValueError(
                f"canonical v8 asset changed during snapshot verification: {path}"
            )
    if not isinstance(verified_at, str) or not verified_at.strip():
        raise ValueError("verified_at must be a non-empty timestamp")

    snapshot: dict[str, object] = {
        "schema_id": "crossframe.promax.v8.source-snapshot",
        "schema_version": 1,
        "framework_version": "v8.0",
        "snapshot_id": "crossframe-promax-v8-source-3186805a",
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "source_manifest_sha256": hashes["source_manifest"],
        "concept_registry_sha256": hashes["concept_registry"],
        "contract_map_sha256": hashes["contract_map"],
        "route_map_sha256": hashes["route_map"],
        "paragraph_count": V8_PARAGRAPH_COUNT,
        "non_whitespace_chars": V8_NON_WHITESPACE_CHARS,
        "table_count": V8_TABLE_COUNT,
        "section_count": V8_SECTION_COUNT,
        "verified_at": verified_at.strip(),
    }
    validate_instance("promax-source-snapshot.schema.json", snapshot)
    return snapshot
