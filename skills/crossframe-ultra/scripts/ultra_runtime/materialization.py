from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from .constants import PHASES, current_version_binding
from .jsonio import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    sha256_bytes,
)
from .paths import (
    RootPolicy,
    RunLayout,
    RunMode,
    _require_utc,
    assert_safe_descendant,
    build_run_layout,
    create_run_id,
)
from .schemas import compute_artifact_content_sha256, validate_phase_artifact


AUTHORING_SLOT_RELATIVE_PATHS = (
    "U01-read-events.jsonl",
    "U02-retrieval-ledger.json",
    "U03-evidence-ledger.json",
    "U04-world-volume.json",
    "U05-transformation-ledger.json",
    "U05-concept-disposition.json",
    "U06-claim-mechanism-graph.json",
    "U07-recursive-states/<node-id>.json",
    "U07-recursive-lineage.json",
    "U08-order-evaluation.json",
    "U08-red-team-report.json",
    "U09-verdict.json",
    "U09-action-ranking.json",
    "U09-forecast-ledger.json",
    "U10-framework-gap-ledger.json",
    "U10-output-plan.json",
    "U11-semantic-coverage.json",
    "article/packets/<packet-id>.md",
    "U11-article-review.json",
    "完整推演档案.md",
)

MATERIALIZATION_CONTROL_FILENAME = "ultra-materialization-control.json"
PARTIAL_ARTICLE_RELATIVE_PATH = "article.partial.md"


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    relative_path: str
    phase_id: str
    schema_name: str
    schema_id: str
    artifact_relative_path: str


_STATIC_ARTIFACT_SPECS = (
    ArtifactSpec(
        "U02-retrieval-ledger.json",
        "U2",
        "ultra-retrieval-ledger.schema.json",
        "crossframe.ultra.v82.retrieval-ledger",
        "U00-U03-evidence/U02-retrieval-ledger.json",
    ),
    ArtifactSpec(
        "U03-evidence-ledger.json",
        "U3",
        "ultra-evidence-ledger.schema.json",
        "crossframe.ultra.v82.evidence-ledger",
        "U00-U03-evidence/U03-evidence-ledger.json",
    ),
    ArtifactSpec(
        "U04-world-volume.json",
        "U4",
        "ultra-world-volume.schema.json",
        "crossframe.ultra.v82.world-volume",
        "U04-U05-world-volume/U04-world-volume.json",
    ),
    ArtifactSpec(
        "U05-transformation-ledger.json",
        "U5",
        "ultra-transformation-ledger.schema.json",
        "crossframe.ultra.v82.transformation-ledger",
        "U04-U05-world-volume/U05-transformation-ledger.json",
    ),
    ArtifactSpec(
        "U05-concept-disposition.json",
        "U5",
        "ultra-concept-disposition.schema.json",
        "crossframe.ultra.v82.concept-disposition",
        "U04-U05-world-volume/U05-concept-disposition.json",
    ),
    ArtifactSpec(
        "U06-claim-mechanism-graph.json",
        "U6",
        "ultra-claim-mechanism-graph.schema.json",
        "crossframe.ultra.v82.claim-mechanism-graph",
        "U06-U08-inference/U06-claim-mechanism-graph.json",
    ),
    ArtifactSpec(
        "U07-recursive-lineage.json",
        "U7",
        "ultra-recursive-lineage.schema.json",
        "crossframe.ultra.v82.recursive-lineage",
        "U06-U08-inference/U07-recursive-lineage.json",
    ),
    ArtifactSpec(
        "U08-order-evaluation.json",
        "U8",
        "ultra-order-evaluation.schema.json",
        "crossframe.ultra.v82.order-evaluation",
        "U06-U08-inference/U08-order-evaluation.json",
    ),
    ArtifactSpec(
        "U08-red-team-report.json",
        "U8",
        "ultra-red-team-report.schema.json",
        "crossframe.ultra.v82.red-team-report",
        "U06-U08-inference/U08-red-team-report.json",
    ),
    ArtifactSpec(
        "U09-verdict.json",
        "U9",
        "ultra-verdict.schema.json",
        "crossframe.ultra.v82.verdict",
        "U09-U10-verdict/U09-verdict.json",
    ),
    ArtifactSpec(
        "U09-action-ranking.json",
        "U9",
        "ultra-action-ranking.schema.json",
        "crossframe.ultra.v82.action-ranking",
        "U09-U10-verdict/U09-action-ranking.json",
    ),
    ArtifactSpec(
        "U09-forecast-ledger.json",
        "U9",
        "ultra-forecast-ledger.schema.json",
        "crossframe.ultra.v82.forecast-ledger",
        "U09-U10-verdict/U09-forecast-ledger.json",
    ),
    ArtifactSpec(
        "U10-framework-gap-ledger.json",
        "U10",
        "ultra-framework-gap-ledger.schema.json",
        "crossframe.ultra.v82.framework-gap-ledger",
        "U09-U10-verdict/U10-framework-gap-ledger.json",
    ),
    ArtifactSpec(
        "U10-output-plan.json",
        "U10",
        "ultra-output-plan.schema.json",
        "crossframe.ultra.v82.output-plan",
        "U09-U10-verdict/U10-output-plan.json",
    ),
    ArtifactSpec(
        "U11-semantic-coverage.json",
        "U11",
        "ultra-semantic-coverage.schema.json",
        "crossframe.ultra.v82.semantic-coverage",
        "U09-U10-verdict/U11-semantic-coverage.json",
    ),
    ArtifactSpec(
        "U11-article-review.json",
        "U11",
        "ultra-article-review.schema.json",
        "crossframe.ultra.v82.article-review",
        "U09-U10-verdict/U11-article-review.json",
    ),
)
_SPEC_BY_RELATIVE_PATH = {spec.relative_path: spec for spec in _STATIC_ARTIFACT_SPECS}
_DYNAMIC_RECURSIVE_SPEC = ArtifactSpec(
    "U07-recursive-states/<node-id>.json",
    "U7",
    "ultra-recursive-state.schema.json",
    "crossframe.ultra.v82.recursive-state",
    "U06-U08-inference/U07-recursive-states/<node-id>.json",
)


@dataclass(frozen=True, slots=True)
class PreparedAuthoring:
    authoring_dir: Path
    relative_slots: tuple[str, ...]
    slot_paths: tuple[Path, ...]
    control_path: Path


def _canonical_utc(value: datetime) -> str:
    _require_utc(value, "generated_at")
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.astimezone(timezone.utc).isoformat(timespec=timespec).replace(
        "+00:00", "Z"
    )


def _validate_layout(layout: RunLayout) -> None:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    expected = {
        "root_staging_dir": layout.root / ".staging",
        "input_dir": layout.run_dir / "input",
        "authoring_dir": layout.run_dir / "work" / "authoring",
        "artifacts_dir": layout.run_dir / "artifacts",
        "delivery_dir": layout.run_dir / "delivery",
        "validation_dir": layout.run_dir / "validation",
        "validation_current_dir": layout.run_dir / "validation" / "current",
        "validation_attempts_dir": layout.run_dir / "validation" / "attempts",
        "recovery_dir": layout.run_dir / "recovery",
        "logs_dir": layout.run_dir / "logs",
    }
    assert_safe_descendant(layout.root, layout.run_dir)
    for field, expected_path in expected.items():
        actual = getattr(layout, field)
        if actual != expected_path:
            raise ValueError(f"layout field {field} is outside the fixed run layout")
        assert_safe_descendant(layout.root, actual)


def build_materialization_control(layout: RunLayout) -> dict[str, object]:
    _validate_layout(layout)
    return {
        "authoring_slots": list(AUTHORING_SLOT_RELATIVE_PATHS),
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
    }


def prepare_authoring(layout: RunLayout) -> PreparedAuthoring:
    _validate_layout(layout)
    layout.authoring_dir.mkdir(parents=True, exist_ok=True)
    (layout.authoring_dir / "U07-recursive-states").mkdir(parents=True, exist_ok=True)
    (layout.authoring_dir / "article" / "packets").mkdir(parents=True, exist_ok=True)
    control_path = layout.artifacts_dir / MATERIALIZATION_CONTROL_FILENAME
    assert_safe_descendant(layout.root, control_path)
    atomic_write_json(control_path, build_materialization_control(layout))
    return PreparedAuthoring(
        authoring_dir=layout.authoring_dir,
        relative_slots=AUTHORING_SLOT_RELATIVE_PATHS,
        slot_paths=tuple(layout.authoring_dir / slot for slot in AUTHORING_SLOT_RELATIVE_PATHS),
        control_path=control_path,
    )


def _relative_authoring_path(layout: RunLayout, path: Path) -> str:
    _validate_layout(layout)
    if not isinstance(path, Path):
        raise TypeError("authoring path must be a pathlib.Path")
    assert_safe_descendant(layout.root, path)
    try:
        relative = path.relative_to(layout.authoring_dir).as_posix()
    except ValueError as error:
        raise ValueError("model-authored path is outside work/authoring") from error
    return relative


def _spec_for_path(layout: RunLayout, path: Path) -> ArtifactSpec:
    relative = _relative_authoring_path(layout, path)
    static = _SPEC_BY_RELATIVE_PATH.get(relative)
    if static is not None:
        return static
    recursive_prefix = "U07-recursive-states/"
    if relative.startswith(recursive_prefix) and relative.endswith(".json"):
        node_id = Path(relative).stem
        if not node_id or node_id in {".", ".."} or Path(relative).parent.as_posix() != "U07-recursive-states":
            raise ValueError("recursive-state authoring path must contain one safe node id")
        return ArtifactSpec(
            relative,
            _DYNAMIC_RECURSIVE_SPEC.phase_id,
            _DYNAMIC_RECURSIVE_SPEC.schema_name,
            _DYNAMIC_RECURSIVE_SPEC.schema_id,
            f"U06-U08-inference/U07-recursive-states/{node_id}.json",
        )
    raise ValueError(f"path is not a model-owned JSON authoring slot: {relative}")


def discover_authoring_inputs(layout: RunLayout) -> tuple[Path, ...]:
    _validate_layout(layout)
    ordered: list[Path] = []
    for slot in AUTHORING_SLOT_RELATIVE_PATHS:
        if slot == "U07-recursive-states/<node-id>.json":
            state_dir = layout.authoring_dir / "U07-recursive-states"
            if state_dir.is_dir():
                ordered.extend(sorted(state_dir.glob("*.json"), key=lambda path: path.name))
            continue
        if slot == "article/packets/<packet-id>.md":
            packet_dir = layout.authoring_dir / "article" / "packets"
            if packet_dir.is_dir():
                ordered.extend(sorted(packet_dir.glob("*.md"), key=lambda path: path.name))
            continue
        candidate = layout.authoring_dir / slot
        if candidate.is_file():
            ordered.append(candidate)
    for path in ordered:
        assert_safe_descendant(layout.root, path)
    return tuple(ordered)


def seal_authoring_artifact(
    layout: RunLayout,
    path: Path,
    *,
    generated_at: datetime,
    authority_documents: Mapping[str, Mapping[str, object]] | None = None,
    authority_values: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    spec = _spec_for_path(layout, path)
    timestamp = _canonical_utc(generated_at)
    authored = load_json_object(path)
    sealed: dict[str, Any] = copy.deepcopy(dict(authored))
    if authority_documents is not None:
        aliases = {
            "evidence": "evidence",
            "evidence_ledger": "evidence",
            "world_volume": "world_volume",
            "transformation_ledger": "transformation_ledger",
            "concept_disposition": "concept_disposition",
            "claim_mechanism_graph": "claim_mechanism_graph",
            "recursive_lineage": "recursive_lineage",
            "order_evaluation": "order_evaluation",
            "red_team_report": "red_team_report",
            "verdict": "verdict",
            "action_ranking": "action_ranking",
            "forecast_ledger": "forecast_ledger",
            "output_plan": "output_plan",
            "semantic_coverage": "semantic_coverage",
            "coverage": "semantic_coverage",
            "article_review": "article_review",
        }
        for field in tuple(sealed):
            suffix = None
            if field.endswith("_artifact_sha256"):
                suffix = "_artifact_sha256"
            elif field.endswith("_content_sha256"):
                suffix = "_content_sha256"
            if suffix is None:
                continue
            authority_name = aliases.get(field[: -len(suffix)])
            document = (
                None
                if authority_name is None
                else authority_documents.get(authority_name)
            )
            if document is None:
                continue
            if suffix == "_artifact_sha256":
                sealed[field] = sha256_bytes(canonical_json_bytes(document))
            else:
                content_sha256 = document.get("content_sha256")
                if not isinstance(content_sha256, str):
                    raise ValueError(
                        f"authority document {authority_name} has no content_sha256"
                    )
                sealed[field] = content_sha256
    if authority_values is not None:
        for field, value in authority_values.items():
            if field in sealed:
                sealed[field] = copy.deepcopy(value)
    if "parent_run_id" in sealed:
        sealed["parent_run_id"] = layout.run_dir.name
    if spec.relative_path == "U10-output-plan.json":
        sealed["article_path"] = "work/authoring/article.partial.md"
        sealed["coverage_required"] = True
        sealed["official_filename_allowed"] = False
        required_artifacts = sealed.get("required_artifacts")
        replacements: dict[str, str] = {}
        if isinstance(required_artifacts, list):
            for record in required_artifacts:
                if not isinstance(record, dict):
                    continue
                relative = record.get("path")
                if not isinstance(relative, str):
                    continue
                relative_path = PurePosixPath(relative)
                if (
                    relative_path.is_absolute()
                    or "\\" in relative
                    or not relative_path.parts
                    or relative_path.parts[0] != "artifacts"
                    or ".." in relative_path.parts
                ):
                    raise ValueError(
                        "output-plan required artifacts must use fixed artifacts/ paths"
                    )
                authority_path = layout.run_dir.joinpath(*relative_path.parts)
                assert_safe_descendant(layout.root, authority_path)
                if authority_path != layout.artifacts_dir and layout.artifacts_dir not in authority_path.parents:
                    raise ValueError(
                        "output-plan required artifact is outside the artifacts namespace"
                    )
                if not authority_path.is_file():
                    raise ValueError(
                        f"output-plan required artifact is absent: {relative}"
                    )
                declared = record.get("sha256")
                actual = _sha256_file(authority_path)
                if isinstance(declared, str):
                    previous = replacements.setdefault(declared, actual)
                    if previous != actual:
                        raise ValueError(
                            "one declared output-plan hash resolves to multiple artifacts"
                        )
                record["sha256"] = actual
        for collection_name in ("sections", "appendices"):
            collection = sealed.get(collection_name)
            if not isinstance(collection, list):
                continue
            for entry in collection:
                if not isinstance(entry, dict):
                    continue
                dependencies = entry.get("dependency_hashes")
                if isinstance(dependencies, list):
                    entry["dependency_hashes"] = [
                        replacements.get(value, value) for value in dependencies
                    ]
        semantic_universe = sealed.get("semantic_universe")
        if isinstance(semantic_universe, list):
            for unit in semantic_universe:
                if not isinstance(unit, dict):
                    continue
                authority_hash = unit.get("authority_artifact_sha256")
                if isinstance(authority_hash, str):
                    unit["authority_artifact_sha256"] = replacements.get(
                        authority_hash, authority_hash
                    )
            sealed["semantic_universe_sha256"] = sha256_bytes(
                canonical_json_bytes(semantic_universe)
            )
    sealed.update(
        {
            "schema_id": spec.schema_id,
            "schema_version": 1,
            "run_id": layout.run_dir.name,
            "version_binding": current_version_binding(),
            "generated_at": timestamp,
            "content_sha256": "0" * 64,
            "phase_id": spec.phase_id,
        }
    )
    sealed["content_sha256"] = compute_artifact_content_sha256(sealed)
    try:
        validated = validate_phase_artifact(
            spec.schema_name,
            sealed,
            expected_schema_id=spec.schema_id,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_phase_id=spec.phase_id,
        )
    except Exception as error:
        raise ValueError(f"model-authored schema field validation failed: {error}") from error
    atomic_write_json(path, validated)
    return validated


def artifact_destination(layout: RunLayout, source_path: Path) -> Path:
    spec = _spec_for_path(layout, source_path)
    destination = layout.artifacts_dir / spec.artifact_relative_path
    assert_safe_descendant(layout.root, destination)
    return destination


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_materialized_phase(
    layout: RunLayout,
    phase_store: object,
    phase_id: str,
    artifact_paths: Sequence[Path],
    *,
    input_artifact_hashes: Sequence[str] | None = None,
) -> dict[str, object]:
    _validate_layout(layout)
    if phase_id not in PHASES[4:12]:
        raise ValueError("materialized phase must be one of U4 through U11")
    complete = getattr(phase_store, "complete", None)
    if not callable(complete):
        raise TypeError("phase_store must be the existing PhaseStore")
    paths = tuple(artifact_paths)
    if not paths:
        raise ValueError("a materialized phase requires at least one artifact")
    hashes: list[str] = []
    for path in paths:
        if not isinstance(path, Path) or not path.is_file():
            raise ValueError(f"materialized artifact is not a file: {path}")
        assert_safe_descendant(layout.root, path)
        hashes.append(_sha256_file(path))
    inputs = None if input_artifact_hashes is None else tuple(input_artifact_hashes)
    if inputs is not None and any(
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        for digest in inputs
    ):
        raise ValueError("input_artifact_hashes must contain lowercase SHA-256 values")
    result = complete(
        phase_id,
        artifact_hashes=tuple(hashes),
        input_artifact_hashes=inputs,
    )
    if not isinstance(result, Mapping):
        raise TypeError("PhaseStore.complete must return an event object")
    return dict(result)


def checkpoint_article_packets(
    layout: RunLayout,
    phase_store: object,
    packet_paths: Sequence[Path],
    *,
    now: datetime,
    create_checkpoint: Callable[..., object],
) -> tuple[object, ...]:
    _validate_layout(layout)
    _require_utc(now, "now")
    if not callable(create_checkpoint):
        raise TypeError("create_checkpoint must be callable")
    packets = tuple(sorted(packet_paths, key=lambda path: path.name))
    results: list[object] = []
    packet_dir = layout.authoring_dir / "article" / "packets"
    for ordinal, packet in enumerate(packets, start=1):
        if not isinstance(packet, Path) or not packet.is_file():
            raise ValueError(f"article packet is not a file: {packet}")
        assert_safe_descendant(layout.root, packet)
        if packet.parent != packet_dir or packet.suffix.casefold() != ".md":
            raise ValueError("article packet must occupy the fixed authoring packet directory")
        results.append(
            create_checkpoint(
                layout,
                phase_store,
                boundary_kind="article-packet",
                boundary_id=packet.stem,
                boundary_ordinal=ordinal,
                artifact_paths=(packet,),
                now=now,
            )
        )
    return tuple(results)


def complete_u12(
    layout: RunLayout,
    phase_store: object,
    *,
    manifest_path: Path,
    postcheck_report_path: Path,
    delivery_paths: Sequence[Path],
    postcheck_passed: bool,
) -> dict[str, object]:
    _validate_layout(layout)
    if postcheck_passed is not True:
        raise ValueError("U12 completion requires a passing post-publish validation")
    expected_manifest = layout.artifacts_dir / "ultra-artifact-manifest.json"
    if manifest_path != expected_manifest or not manifest_path.is_file():
        raise ValueError("U12 completion requires the fixed artifact manifest")
    expected_report = (
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    if postcheck_report_path != expected_report or not postcheck_report_path.is_file():
        raise ValueError("U12 completion requires the committed post-publish validator report")
    expected_delivery = (
        layout.delivery_dir / "CrossFrame-Ultra-完整文章.md",
        layout.delivery_dir / "完整推演档案.md",
        layout.delivery_dir / "工件索引.md",
    )
    supplied_delivery = tuple(delivery_paths)
    if supplied_delivery != expected_delivery or not all(path.is_file() for path in supplied_delivery):
        raise ValueError("U12 completion requires all three fixed delivery files")
    complete = getattr(phase_store, "complete", None)
    if not callable(complete):
        raise TypeError("phase_store must be the existing PhaseStore")
    hashes = tuple(
        _sha256_file(path)
        for path in (manifest_path, postcheck_report_path, *supplied_delivery)
    )
    result = complete("U12", artifact_hashes=hashes)
    if not isinstance(result, Mapping):
        raise TypeError("PhaseStore.complete must return an event object")
    return dict(result)


@dataclass(frozen=True, slots=True)
class MaterializedBundle:
    phase_events: tuple[dict[str, object], ...]
    documents: Mapping[str, Mapping[str, object]]
    artifact_paths: tuple[Path, ...]
    partial_article_path: Path
    dossier_path: Path
    artifact_index_bytes: bytes


def _full_artifact_sha256(document: Mapping[str, object]) -> str:
    return sha256_bytes(canonical_json_bytes(document))


def _authority_name(spec: ArtifactSpec) -> str:
    names = {
        "U02-retrieval-ledger.json": "retrieval_ledger",
        "U03-evidence-ledger.json": "evidence",
        "U04-world-volume.json": "world_volume",
        "U05-transformation-ledger.json": "transformation_ledger",
        "U05-concept-disposition.json": "concept_disposition",
        "U06-claim-mechanism-graph.json": "claim_mechanism_graph",
        "U07-recursive-lineage.json": "recursive_lineage",
        "U08-order-evaluation.json": "order_evaluation",
        "U08-red-team-report.json": "red_team_report",
        "U09-verdict.json": "verdict",
        "U09-action-ranking.json": "action_ranking",
        "U09-forecast-ledger.json": "forecast_ledger",
        "U10-framework-gap-ledger.json": "framework_gap_ledger",
        "U10-output-plan.json": "output_plan",
        "U11-semantic-coverage.json": "semantic_coverage",
        "U11-article-review.json": "article_review",
    }
    if spec.schema_id == _DYNAMIC_RECURSIVE_SPEC.schema_id:
        return "recursive_state"
    try:
        return names[spec.relative_path]
    except KeyError as error:
        raise ValueError(f"no authority name for {spec.relative_path}") from error


def _completed_phase_event(phase_store: object, phase_id: str) -> dict[str, object] | None:
    events_method = getattr(phase_store, "events", None)
    if not callable(events_method):
        return None
    matching = [
        dict(event)
        for event in events_method()
        if isinstance(event, Mapping)
        and event.get("phase_id") == phase_id
        and event.get("status") == "complete"
    ]
    if len(matching) > 1:
        raise ValueError(f"phase {phase_id} has multiple complete events")
    return None if not matching else matching[0]


def _event_sha256(event: Mapping[str, object]) -> str:
    value = event.get("event_sha256")
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("complete phase event has no event_sha256")
    return value


def _event_output_hashes(event: Mapping[str, object]) -> tuple[str, ...]:
    value = event.get("output_artifact_hashes", event.get("artifact_hashes"))
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and len(item) == 64 for item in value
    ):
        raise ValueError("complete phase event has no output artifact hashes")
    return tuple(value)


def _runtime_relation_refs(volume: Mapping[str, object]) -> dict[str, dict[str, object]]:
    memberships = volume.get("memberships")
    circle_relations = volume.get("circle_relations")
    if not isinstance(memberships, list) or not isinstance(circle_relations, list):
        raise ValueError("world volume relations must be arrays")
    typed = [*(('Rac', record) for record in memberships), *(('Rcc', record) for record in circle_relations)]
    refs: dict[str, dict[str, object]] = {}
    for ordinal, (relation_kind, record) in enumerate(typed, start=1):
        if not isinstance(record, Mapping):
            raise ValueError("world volume relation record must be an object")
        refs[f"RELATION-AUTHORITY-{ordinal:02d}"] = {
            "relation_kind": relation_kind,
            "record_sha256": sha256_bytes(canonical_json_bytes(record)),
            "record": copy.deepcopy(dict(record)),
        }
    return refs


def _knowledge_authorities(repo: Path) -> tuple[dict[str, str], str]:
    references = repo.resolve() / "skills" / "crossframe-ultra" / "references"
    paths = {
        "registry_sha256": references / "concept-registry" / "v8.2-concept-registry.json",
        "route_map_sha256": references / "v8.2-route-map.json",
        "contract_map_sha256": references / "concept-contracts" / "v8.2-contract-map.json",
    }
    values: dict[str, str] = {}
    for field, path in paths.items():
        if not path.is_file():
            raise ValueError(f"knowledge authority is absent: {path}")
        values[field] = sha256_bytes(path.read_bytes())
    source_manifest = references / "source-manifest.json"
    if not source_manifest.is_file():
        raise ValueError(f"source manifest authority is absent: {source_manifest}")
    return values, sha256_bytes(source_manifest.read_bytes())


def _load_and_validate_upstream(
    layout: RunLayout,
    phase_store: object,
    relative_path: str,
    spec: ArtifactSpec,
) -> dict[str, object]:
    source = layout.authoring_dir / relative_path
    if not source.is_file():
        destination = layout.artifacts_dir / spec.artifact_relative_path
        if destination.is_file():
            source = destination
        else:
            raise ValueError(f"required upstream authoring artifact is absent: {relative_path}")
    document = load_json_object(source)
    try:
        validated = validate_phase_artifact(
            spec.schema_name,
            document,
            expected_schema_id=spec.schema_id,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_phase_id=spec.phase_id,
        )
    except Exception as error:
        raise ValueError(f"upstream artifact {relative_path} is invalid: {error}") from error
    event = _completed_phase_event(phase_store, spec.phase_id)
    if event is not None and _full_artifact_sha256(validated) not in _event_output_hashes(event):
        raise ValueError(f"upstream artifact {relative_path} is outside its complete phase event")
    destination = layout.artifacts_dir / spec.artifact_relative_path
    if not destination.is_file():
        atomic_write_json(destination, validated)
    elif destination.read_bytes() != canonical_json_bytes(validated):
        raise ValueError(f"upstream artifact copy differs from authoring authority: {relative_path}")
    return validated


def _load_completed_documents(
    layout: RunLayout,
    event: Mapping[str, object],
    sources: Sequence[Path],
) -> tuple[list[dict[str, object]], list[Path]]:
    documents: list[dict[str, object]] = []
    destinations: list[Path] = []
    for source in sources:
        spec = _spec_for_path(layout, source)
        destination = artifact_destination(layout, source)
        if not destination.is_file():
            raise ValueError(f"completed phase artifact is absent: {destination}")
        document = load_json_object(destination)
        try:
            validated = validate_phase_artifact(
                spec.schema_name,
                document,
                expected_schema_id=spec.schema_id,
                expected_run_id=layout.run_dir.name,
                expected_version_binding=current_version_binding(),
                expected_phase_id=spec.phase_id,
            )
        except Exception as error:
            raise ValueError(f"completed phase artifact is invalid: {destination}: {error}") from error
        documents.append(validated)
        destinations.append(destination)
    actual_hashes = tuple(_sha256_file(path) for path in destinations)
    if sorted(actual_hashes) != sorted(_event_output_hashes(event)):
        raise ValueError("completed phase artifact hashes differ from the phase event")
    return documents, destinations


def _seal_json_phase(
    layout: RunLayout,
    phase_store: object,
    phase_id: str,
    sources: Sequence[Path],
    *,
    generated_at: datetime,
    authority_documents: dict[str, Mapping[str, object]],
    authority_values: Mapping[str, object] | None,
    input_artifact_hashes: Sequence[str],
    validate_documents: Callable[[Sequence[Mapping[str, object]]], None],
    create_checkpoint: Callable[..., object],
) -> tuple[dict[str, object], list[dict[str, object]], list[Path]]:
    completed = _completed_phase_event(phase_store, phase_id)
    if completed is not None:
        documents, destinations = _load_completed_documents(
            layout, completed, sources
        )
        validate_documents(documents)
        return completed, documents, destinations

    documents: list[dict[str, object]] = []
    destinations: list[Path] = []
    for source in sources:
        spec = _spec_for_path(layout, source)
        sealed = seal_authoring_artifact(
            layout,
            source,
            generated_at=generated_at,
            authority_documents=authority_documents,
            authority_values=authority_values,
        )
        destination = artifact_destination(layout, source)
        atomic_write_json(destination, sealed)
        documents.append(sealed)
        destinations.append(destination)
        name = _authority_name(spec)
        if name == "recursive_state" and isinstance(authority_values, dict):
            recursive_hashes = authority_values.get("recursive_state_artifact_hashes")
            if isinstance(recursive_hashes, list):
                recursive_hashes.append(_full_artifact_sha256(sealed))
        else:
            authority_documents[name] = sealed
    validate_documents(documents)
    event = record_materialized_phase(
        layout,
        phase_store,
        phase_id,
        destinations,
        input_artifact_hashes=input_artifact_hashes,
    )
    create_checkpoint(
        layout,
        phase_store,
        boundary_kind="phase",
        boundary_id=phase_id,
        boundary_ordinal=0,
        artifact_paths=tuple(destinations),
        now=generated_at,
    )
    return event, documents, destinations


def _phase_input_hashes(
    authority_documents: Mapping[str, Mapping[str, object]], *names: str
) -> tuple[str, ...]:
    values = []
    for name in names:
        try:
            document = authority_documents[name]
        except KeyError as error:
            raise ValueError(f"missing upstream authority document: {name}") from error
        values.append(_full_artifact_sha256(document))
    return tuple(values)


def _packet_mappings(
    output_plan: Mapping[str, object], packet_paths: Sequence[Path]
) -> tuple[dict[str, object], ...]:
    sections = output_plan.get("sections")
    appendices = output_plan.get("appendices")
    universe = output_plan.get("semantic_universe")
    if not isinstance(sections, list) or not isinstance(appendices, list):
        raise ValueError("output plan sections and appendices must be arrays")
    entries = sections + appendices
    packets = tuple(sorted(packet_paths, key=lambda path: path.name))
    if len(entries) != len(packets):
        raise ValueError("article packet count differs from the frozen output plan")
    source_refs_by_unit: dict[str, tuple[str, ...]] = {}
    if isinstance(universe, list):
        for item in universe:
            if not isinstance(item, Mapping):
                continue
            unit_id = item.get("unit_id")
            refs = item.get("source_refs")
            if isinstance(unit_id, str) and isinstance(refs, list) and all(
                isinstance(ref, str) for ref in refs
            ):
                source_refs_by_unit[unit_id] = tuple(refs)
    result = []
    for entry, packet_path in zip(entries, packets, strict=True):
        if not isinstance(entry, Mapping):
            raise ValueError("output plan entry must be an object")
        prose = packet_path.read_text("utf-8")
        semantic_ids = entry.get("semantic_unit_ids")
        if not isinstance(semantic_ids, list) or not all(
            isinstance(unit_id, str) for unit_id in semantic_ids
        ):
            raise ValueError("output plan semantic_unit_ids must be strings")
        source_refs = sorted(
            {
                source_ref
                for unit_id in semantic_ids
                for source_ref in source_refs_by_unit.get(unit_id, ())
            }
        )
        result.append(
            {
                "packet_id": packet_path.stem,
                "section_id": entry.get("section_id"),
                "ordinal": entry.get("ordinal"),
                "dependency_hashes": copy.deepcopy(entry.get("dependency_hashes")),
                "semantic_unit_ids": copy.deepcopy(semantic_ids),
                "source_refs": source_refs,
                "prose": prose,
                "prose_sha256": sha256_bytes(prose.encode("utf-8")),
            }
        )
    return tuple(result)


def _canonical_markdown(path: Path, label: str) -> bytes:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} must be UTF-8") from error
    if not text.strip() or "\x00" in text or text.startswith("\ufeff"):
        raise ValueError(f"{label} must be nonempty canonical text")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    value = normalized.encode("utf-8")
    if value != raw:
        atomic_write_bytes(path, value)
    return value


def build_artifact_index_bytes(
    layout: RunLayout,
    *,
    additional_paths: Sequence[Path] = (),
) -> bytes:
    _validate_layout(layout)
    paths = [
        path
        for path in layout.artifacts_dir.rglob("*")
        if path.is_file() and path.name != "ultra-artifact-manifest.json"
    ]
    paths.extend(additional_paths)
    unique = sorted(set(paths), key=lambda path: path.relative_to(layout.run_dir).as_posix())
    lines = [
        "# 工件索引",
        "",
        "| phase | artifact path | sha256 |",
        "|---|---|---|",
    ]
    for path in unique:
        assert_safe_descendant(layout.root, path)
        relative = path.relative_to(layout.run_dir).as_posix()
        phase = "runtime"
        if path.suffix.casefold() == ".json":
            try:
                phase_value = load_json_object(path).get("phase_id")
            except Exception:
                phase_value = None
            if isinstance(phase_value, str):
                phase = phase_value
        elif path.name == "article.partial.md" or path.name == "完整推演档案.md":
            phase = "U11"
        lines.append(f"| {phase} | {relative} | {_sha256_file(path)} |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def materialize_u4_u11(
    repo: Path,
    layout: RunLayout,
    phase_store: object,
    *,
    now: datetime,
    create_checkpoint: Callable[..., object],
) -> MaterializedBundle:
    _validate_layout(layout)
    _require_utc(now, "now")
    if not isinstance(repo, Path) or not repo.resolve().is_dir():
        raise ValueError("repo must be an existing Path")
    prepared = prepare_authoring(layout)
    documents: dict[str, Mapping[str, object]] = {}
    phase_events: list[dict[str, object]] = []
    artifact_paths: list[Path] = []

    evidence_spec = _SPEC_BY_RELATIVE_PATH["U03-evidence-ledger.json"]
    evidence = _load_and_validate_upstream(
        layout, phase_store, evidence_spec.relative_path, evidence_spec
    )
    documents["evidence"] = evidence

    from . import article, concept_closure, coverage, forecast, judgment, recursion, world_volume

    u4_source = prepared.authoring_dir / "U04-world-volume.json"

    def validate_u4(values: Sequence[Mapping[str, object]]) -> None:
        volume = values[0]
        relation_refs = _runtime_relation_refs(volume)
        world_volume.validate_world_volume(
            volume,
            evidence_ledger=evidence,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_evidence_artifact_sha256=_full_artifact_sha256(evidence),
            relation_refs=relation_refs,
            expected_relation_refs_sha256=sha256_bytes(canonical_json_bytes(relation_refs)),
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U4",
        (u4_source,),
        generated_at=now,
        authority_documents=documents,
        authority_values=None,
        input_artifact_hashes=_phase_input_hashes(documents, "evidence"),
        validate_documents=validate_u4,
        create_checkpoint=create_checkpoint,
    )
    documents["world_volume"] = values[0]
    phase_events.append(event)
    artifact_paths.extend(paths)

    knowledge_values, source_manifest_sha256 = _knowledge_authorities(repo)
    u5_sources = (
        prepared.authoring_dir / "U05-transformation-ledger.json",
        prepared.authoring_dir / "U05-concept-disposition.json",
    )

    def validate_u5(values: Sequence[Mapping[str, object]]) -> None:
        transformations, concepts = values
        concept_closure.validate_concept_closure(
            concepts,
            repo=repo,
            evidence_ledger=evidence,
            world_volume=documents["world_volume"],
            transformation_ledger=transformations,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_source_manifest_sha256=source_manifest_sha256,
            expected_evidence_artifact_sha256=_full_artifact_sha256(evidence),
            expected_world_volume_artifact_sha256=_full_artifact_sha256(documents["world_volume"]),
            expected_transformation_ledger_artifact_sha256=_full_artifact_sha256(transformations),
            expected_registry_sha256=knowledge_values["registry_sha256"],
            expected_route_map_sha256=knowledge_values["route_map_sha256"],
            expected_contract_map_sha256=knowledge_values["contract_map_sha256"],
            required_route_ids=concepts["required_route_ids"],
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U5",
        u5_sources,
        generated_at=now,
        authority_documents=documents,
        authority_values=knowledge_values,
        input_artifact_hashes=_phase_input_hashes(documents, "evidence", "world_volume"),
        validate_documents=validate_u5,
        create_checkpoint=create_checkpoint,
    )
    documents["transformation_ledger"], documents["concept_disposition"] = values
    phase_events.append(event)
    artifact_paths.extend(paths)

    u6_source = prepared.authoring_dir / "U06-claim-mechanism-graph.json"

    def validate_u6(values: Sequence[Mapping[str, object]]) -> None:
        judgment._validate_claim_mechanism_graph(
            values[0],
            evidence_ledger=evidence,
            world_volume=documents["world_volume"],
            transformation_ledger=documents["transformation_ledger"],
            concept_disposition=documents["concept_disposition"],
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_evidence_ledger_artifact_sha256=_full_artifact_sha256(evidence),
            expected_world_volume_artifact_sha256=_full_artifact_sha256(documents["world_volume"]),
            expected_transformation_ledger_artifact_sha256=_full_artifact_sha256(documents["transformation_ledger"]),
            expected_concept_disposition_artifact_sha256=_full_artifact_sha256(documents["concept_disposition"]),
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U6",
        (u6_source,),
        generated_at=now,
        authority_documents=documents,
        authority_values=None,
        input_artifact_hashes=_phase_input_hashes(
            documents,
            "evidence",
            "world_volume",
            "transformation_ledger",
            "concept_disposition",
        ),
        validate_documents=validate_u6,
        create_checkpoint=create_checkpoint,
    )
    documents["claim_mechanism_graph"] = values[0]
    phase_events.append(event)
    artifact_paths.extend(paths)

    state_sources = tuple(
        sorted(
            (prepared.authoring_dir / "U07-recursive-states").glob("*.json"),
            key=lambda path: str(load_json_object(path).get("node_id", path.name)),
        )
    )
    if not state_sources:
        raise ValueError("U7 requires at least one recursive state artifact")
    u7_sources = (*state_sources, prepared.authoring_dir / "U07-recursive-lineage.json")
    recursive_hashes: list[str] = []

    def validate_u7(values: Sequence[Mapping[str, object]]) -> None:
        state_values = list(values[:-1])
        lineage = values[-1]
        registry = {_full_artifact_sha256(state): state for state in state_values}
        for state in state_values:
            recursion._validate_recursive_state(
                state,
                parent_volume=documents["world_volume"],
                recursive_state_artifacts=registry,
                transformation_ledger=documents["transformation_ledger"],
                claim_mechanism_graph=documents["claim_mechanism_graph"],
                expected_run_id=layout.run_dir.name,
                expected_version_binding=current_version_binding(),
                expected_world_volume_artifact_sha256=_full_artifact_sha256(documents["world_volume"]),
                expected_transformation_ledger_artifact_sha256=_full_artifact_sha256(documents["transformation_ledger"]),
                expected_claim_mechanism_graph_artifact_sha256=_full_artifact_sha256(documents["claim_mechanism_graph"]),
            )
        recursion._validate_recursive_lineage_bundle(
            lineage,
            documents["world_volume"],
            recursive_state_artifacts=registry,
            transformation_ledger=documents["transformation_ledger"],
            claim_mechanism_graph=documents["claim_mechanism_graph"],
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_world_volume_artifact_sha256=_full_artifact_sha256(documents["world_volume"]),
            expected_transformation_ledger_artifact_sha256=_full_artifact_sha256(documents["transformation_ledger"]),
            expected_claim_mechanism_graph_artifact_sha256=_full_artifact_sha256(documents["claim_mechanism_graph"]),
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U7",
        u7_sources,
        generated_at=now,
        authority_documents=documents,
        authority_values={"recursive_state_artifact_hashes": recursive_hashes},
        input_artifact_hashes=_phase_input_hashes(
            documents,
            "world_volume",
            "transformation_ledger",
            "concept_disposition",
            "claim_mechanism_graph",
        ),
        validate_documents=validate_u7,
        create_checkpoint=create_checkpoint,
    )
    state_values = values[:-1]
    lineage = values[-1]
    documents["recursive_lineage"] = lineage
    phase_events.append(event)
    artifact_paths.extend(paths)

    u8_sources = (
        prepared.authoring_dir / "U08-order-evaluation.json",
        prepared.authoring_dir / "U08-red-team-report.json",
    )

    def validate_u8(values: Sequence[Mapping[str, object]]) -> None:
        order_evaluation, red_team = values
        registry = {_full_artifact_sha256(state): state for state in state_values}
        recursion._validate_order_evaluation(
            order_evaluation,
            claim_mechanism_graph=documents["claim_mechanism_graph"],
            recursive_lineage=lineage,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_claim_mechanism_graph_artifact_sha256=_full_artifact_sha256(documents["claim_mechanism_graph"]),
            expected_recursive_lineage_artifact_sha256=_full_artifact_sha256(lineage),
        )
        recursion._validate_red_team_report(
            red_team,
            claim_mechanism_graph=documents["claim_mechanism_graph"],
            recursive_lineage=lineage,
            order_evaluation=order_evaluation,
            recursive_state_artifacts=registry,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_claim_mechanism_graph_artifact_sha256=_full_artifact_sha256(documents["claim_mechanism_graph"]),
            expected_recursive_lineage_artifact_sha256=_full_artifact_sha256(lineage),
            expected_order_evaluation_artifact_sha256=_full_artifact_sha256(order_evaluation),
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U8",
        u8_sources,
        generated_at=now,
        authority_documents=documents,
        authority_values=None,
        input_artifact_hashes=_phase_input_hashes(
            documents, "claim_mechanism_graph", "recursive_lineage"
        ),
        validate_documents=validate_u8,
        create_checkpoint=create_checkpoint,
    )
    documents["order_evaluation"], documents["red_team_report"] = values
    phase_events.append(event)
    artifact_paths.extend(paths)

    u9_sources = (
        prepared.authoring_dir / "U09-verdict.json",
        prepared.authoring_dir / "U09-action-ranking.json",
        prepared.authoring_dir / "U09-forecast-ledger.json",
    )

    def validate_u9(values: Sequence[Mapping[str, object]]) -> None:
        verdict, action_ranking, forecast_ledger = values
        registry = {_full_artifact_sha256(state): state for state in state_values}
        judgment._validate_verdict_with_authority(
            verdict,
            evidence_ledger=evidence,
            recursive_lineage=lineage,
            claim_mechanism_graph=documents["claim_mechanism_graph"],
            order_evaluation=documents["order_evaluation"],
            red_team_report=documents["red_team_report"],
            recursive_state_artifacts=registry,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_evidence_ledger_artifact_sha256=_full_artifact_sha256(evidence),
            expected_claim_mechanism_graph_artifact_sha256=_full_artifact_sha256(documents["claim_mechanism_graph"]),
            expected_recursive_lineage_artifact_sha256=_full_artifact_sha256(lineage),
            expected_order_evaluation_artifact_sha256=_full_artifact_sha256(documents["order_evaluation"]),
            expected_red_team_report_artifact_sha256=_full_artifact_sha256(documents["red_team_report"]),
        )
        judgment._validate_action_ranking(
            action_ranking,
            verdict=verdict,
            evidence=evidence,
            lineage=lineage,
            expected_verdict_artifact_sha256=_full_artifact_sha256(verdict),
        )
        forecast._validate_forecast_ledger(
            forecast_ledger,
            verdict=verdict,
            evidence=evidence,
            lineage=lineage,
            expected_verdict_artifact_sha256=_full_artifact_sha256(verdict),
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U9",
        u9_sources,
        generated_at=now,
        authority_documents=documents,
        authority_values=None,
        input_artifact_hashes=_phase_input_hashes(
            documents,
            "evidence",
            "claim_mechanism_graph",
            "recursive_lineage",
            "order_evaluation",
            "red_team_report",
        ),
        validate_documents=validate_u9,
        create_checkpoint=create_checkpoint,
    )
    documents["verdict"], documents["action_ranking"], documents["forecast_ledger"] = values
    phase_events.append(event)
    artifact_paths.extend(paths)

    u10_sources = (
        prepared.authoring_dir / "U10-framework-gap-ledger.json",
        prepared.authoring_dir / "U10-output-plan.json",
    )
    u9_event_sha256 = _event_sha256(event)

    def validate_u10(values: Sequence[Mapping[str, object]]) -> None:
        gap, output_plan = values
        judgment._validate_framework_gap_isolation(
            gap,
            claim_mechanism_graph=documents["claim_mechanism_graph"],
            verdict=documents["verdict"],
            action_ranking=documents["action_ranking"],
        )
        article.validate_output_plan_artifact(
            output_plan,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_u9_parent_event_sha256=u9_event_sha256,
            expected_required_artifacts=output_plan["required_artifacts"],
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U10",
        u10_sources,
        generated_at=now,
        authority_documents=documents,
        authority_values={"u9_parent_event_sha256": u9_event_sha256},
        input_artifact_hashes=_phase_input_hashes(
            documents,
            "claim_mechanism_graph",
            "verdict",
            "action_ranking",
            "forecast_ledger",
        ),
        validate_documents=validate_u10,
        create_checkpoint=create_checkpoint,
    )
    documents["framework_gap_ledger"], documents["output_plan"] = values
    phase_events.append(event)
    artifact_paths.extend(paths)

    packet_paths = tuple(
        sorted(
            (prepared.authoring_dir / "article" / "packets").glob("*.md"),
            key=lambda path: path.name,
        )
    )
    checkpoint_article_packets(
        layout,
        phase_store,
        packet_paths,
        now=now,
        create_checkpoint=create_checkpoint,
    )
    packets = _packet_mappings(documents["output_plan"], packet_paths)
    partial_path = prepared.authoring_dir / PARTIAL_ARTICLE_RELATIVE_PATH
    assembled = article.assemble_article(documents["output_plan"], packets, partial_path)

    coverage_source = prepared.authoring_dir / "U11-semantic-coverage.json"
    coverage_document = seal_authoring_artifact(
        layout,
        coverage_source,
        generated_at=now,
        authority_documents=documents,
        authority_values={
            "article_sha256": assembled.article_sha256,
            "semantic_universe_sha256": documents["output_plan"]["semantic_universe_sha256"],
        },
    )
    coverage.validate_semantic_coverage(
        assembled.article_text,
        documents["output_plan"],
        documents["output_plan"]["semantic_universe"],
        coverage_document["mappings"],
    )
    coverage_destination = artifact_destination(layout, coverage_source)
    atomic_write_json(coverage_destination, coverage_document)
    documents["semantic_coverage"] = coverage_document

    review_source = prepared.authoring_dir / "U11-article-review.json"
    authored_review = seal_authoring_artifact(
        layout,
        review_source,
        generated_at=now,
        authority_documents=documents,
        authority_values={
            "article_sha256": assembled.article_sha256,
            "semantic_universe_sha256": documents["output_plan"]["semantic_universe_sha256"],
        },
    )
    built_review = coverage.build_article_review_artifact(
        assembled.article_text,
        documents["output_plan"],
        coverage_document,
        run_id=layout.run_dir.name,
        version_binding=current_version_binding(),
        generated_at=_canonical_utc(now),
        expected_output_plan_artifact_sha256=_full_artifact_sha256(documents["output_plan"]),
        expected_coverage_artifact_sha256=_full_artifact_sha256(coverage_document),
    )
    if authored_review != built_review:
        raise ValueError("model-authored article review differs from deterministic runtime review")
    review_destination = artifact_destination(layout, review_source)
    atomic_write_json(review_destination, built_review)
    documents["article_review"] = built_review

    dossier_path = prepared.authoring_dir / "完整推演档案.md"
    _canonical_markdown(dossier_path, "complete dossier")
    artifact_index_path = layout.artifacts_dir / "ultra-artifact-index.md"
    artifact_index_bytes = build_artifact_index_bytes(
        layout, additional_paths=(partial_path, dossier_path)
    )
    atomic_write_bytes(artifact_index_path, artifact_index_bytes)
    u11_paths = (
        coverage_destination,
        review_destination,
        partial_path,
        dossier_path,
        artifact_index_path,
    )
    u11_event = _completed_phase_event(phase_store, "U11")
    if u11_event is None:
        u11_event = record_materialized_phase(
            layout,
            phase_store,
            "U11",
            u11_paths,
            input_artifact_hashes=_phase_input_hashes(documents, "output_plan"),
        )
        create_checkpoint(
            layout,
            phase_store,
            boundary_kind="phase",
            boundary_id="U11",
            boundary_ordinal=0,
            artifact_paths=u11_paths,
            now=now,
        )
    elif sorted(_event_output_hashes(u11_event)) != sorted(
        _sha256_file(path) for path in u11_paths
    ):
        raise ValueError("completed U11 artifacts differ from the phase event")
    phase_events.append(u11_event)
    artifact_paths.extend(
        (coverage_destination, review_destination, artifact_index_path)
    )
    return MaterializedBundle(
        phase_events=tuple(phase_events),
        documents=copy.deepcopy(documents),
        artifact_paths=tuple(artifact_paths),
        partial_article_path=partial_path,
        dossier_path=dossier_path,
        artifact_index_bytes=artifact_index_bytes,
    )


@dataclass(frozen=True, slots=True)
class CompleteMaterializationResult:
    run_id: str
    status: str
    manifest_path: Path
    article_path: Path
    dossier_path: Path
    artifact_index_path: Path
    final_chat_path: Path
    postcheck_passed: bool


def _resume_phase_store(result: object) -> object:
    phase_store = getattr(result, "phase_store", None)
    if phase_store is None and isinstance(result, Mapping):
        phase_store = result.get("phase_store")
    if phase_store is None and callable(getattr(result, "complete", None)):
        phase_store = result
    if phase_store is None or not callable(getattr(phase_store, "complete", None)):
        raise RuntimeError("resume_run did not provide the existing PhaseStore")
    return phase_store


def _strictly_later(now: datetime, timestamp: str) -> datetime:
    _require_utc(now, "now")
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("status updated_at is not a canonical UTC timestamp")
    previous = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    return now if now > previous else previous + timedelta(microseconds=1)


def _validator_set_authority(*modules: object) -> str:
    for module in modules:
        for name in (
            "VALIDATOR_SET_SHA256",
            "validator_set_sha256",
            "compute_validator_set_sha256",
        ):
            value = getattr(module, name, None)
            if callable(value):
                value = value()
            if isinstance(value, str) and len(value) == 64 and all(
                character in "0123456789abcdef" for character in value
            ):
                return value
    raise RuntimeError("Task 12 does not expose its validator-set hash authority")


def materialize_complete_run(
    repo: Path,
    mode: RunMode,
    run_id: str,
    *,
    policy: RootPolicy,
    now: datetime,
    entropy: bytes,
    fresh_check: Callable[[str], bytes],
    commit_report: Callable[[str, bytes], object],
) -> CompleteMaterializationResult:
    """Materialize U4-U12 through Task 12's single PhaseStore and fixed APIs."""

    if not isinstance(repo, Path) or not repo.resolve().is_dir():
        raise ValueError("repo must be an existing Path")
    if not isinstance(mode, RunMode):
        raise TypeError("mode must be a RunMode")
    if not isinstance(policy, RootPolicy):
        raise TypeError("policy must be a RootPolicy")
    _require_utc(now, "now")
    if not isinstance(entropy, bytes):
        raise TypeError("entropy must be bytes")
    if not callable(fresh_check) or not callable(commit_report):
        raise TypeError("fresh_check and commit_report must be callable")
    layout = build_run_layout(mode, run_id, policy)

    try:
        recovery = __import__(
            "ultra_runtime.recovery", fromlist=["create_checkpoint"]
        )
        artifacts = __import__(
            "ultra_runtime.artifacts", fromlist=["build_artifact_manifest"]
        )
        validation = __import__(
            "ultra_runtime.validation", fromlist=["commit_validation_attempt"]
        )
    except ModuleNotFoundError as error:
        raise RuntimeError("Task 12 recovery/validation dependencies are not integrated") from error

    from .deliverables import (
        build_final_chat_projection,
        publish_delivery,
        recover_publish_transaction,
        write_final_chat_projection,
    )
    from .indexes import IndexStore
    from .locks import acquire_run_lease, release_run_lease
    from .status import RunStatusStore

    status_store = RunStatusStore(layout)
    lease = acquire_run_lease(layout, now, timedelta(minutes=30))
    attention_marked = False

    def mark_needs_attention(reason: str) -> object:
        nonlocal attention_marked
        current = status_store.read()
        if current.status == "needs_attention":
            attention_marked = True
            return current
        if current.status in {"complete", "failed", "cancelled"}:
            raise RuntimeError(
                f"cannot mark terminal run {current.status} as needs_attention"
            )
        changed = status_store.transition(
            current,
            "needs_attention",
            _strictly_later(now, current.updated_at),
            current_phase=current.current_phase,
            last_complete_phase=current.last_complete_phase,
            reason=reason,
            validation_passed=False,
        )
        attention_marked = True
        return changed

    try:
        current = status_store.read()
        if current.status != "running":
            if current.status not in {
                "created",
                "interrupted",
                "blocked",
                "needs_attention",
            }:
                raise RuntimeError(
                    f"run status {current.status!r} cannot materialize"
                )
            current = status_store.transition(
                current,
                "running",
                _strictly_later(now, current.updated_at),
                current_phase=current.current_phase,
                last_complete_phase=current.last_complete_phase,
                reason="materialization admitted",
                validation_passed=False,
            )

        recover_publish_transaction(
            layout, mark_needs_attention=mark_needs_attention
        )
        if attention_marked:
            raise RuntimeError(
                "an incomplete publication was rolled back; operator attention is required"
            )

        resumed = recovery.resume_run(layout, now=now)
        phase_store = _resume_phase_store(resumed)
        bundle = materialize_u4_u11(
            repo,
            layout,
            phase_store,
            now=now,
            create_checkpoint=recovery.create_checkpoint,
        )
        u11_event = bundle.phase_events[-1]
        if u11_event.get("phase_id") != "U11":
            raise RuntimeError("materialization did not end at a complete U11 event")

        validator_set_sha256 = _validator_set_authority(artifacts, validation)
        manifest_path = layout.artifacts_dir / "ultra-artifact-manifest.json"
        previous_manifest = (
            manifest_path.read_bytes() if manifest_path.is_file() else None
        )
        manifest = artifacts.build_artifact_manifest(
            layout,
            phase_chain_head_sha256=_event_sha256(u11_event),
            validator_set_sha256=validator_set_sha256,
            generated_at=now,
        )
        if not isinstance(manifest, Mapping):
            raise TypeError("build_artifact_manifest must return an object")
        if manifest_path.is_file() and manifest_path.read_bytes() != previous_manifest:
            if previous_manifest is None:
                manifest_path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(manifest_path, previous_manifest)
            raise RuntimeError(
                "build_artifact_manifest wrote before the publish journal boundary"
            )
        manifest_bytes = canonical_json_bytes(manifest)
        transaction_id = create_run_id(now, entropy)
        publication = publish_delivery(
            layout,
            transaction_id=transaction_id,
            article_bytes=bundle.partial_article_path.read_bytes(),
            dossier_bytes=bundle.dossier_path.read_bytes(),
            artifact_index_bytes=bundle.artifact_index_bytes,
            manifest_bytes=manifest_bytes,
            fresh_check=fresh_check,
            commit_report=commit_report,
            mark_needs_attention=mark_needs_attention,
        )
        current_report_path = (
            layout.validation_current_dir / "ultra-validator-report.json"
        )
        if not current_report_path.is_file():
            raise RuntimeError(
                "post-publish report was not committed by the lease-owning parent"
            )
        if current_report_path.read_bytes() != publication.postcheck_report_bytes:
            raise RuntimeError(
                "committed post-publish report differs from fresh checker stdout"
            )
        u12_event = complete_u12(
            layout,
            phase_store,
            manifest_path=publication.paths.manifest_path,
            postcheck_report_path=current_report_path,
            delivery_paths=(
                publication.paths.article_path,
                publication.paths.dossier_path,
                publication.paths.artifact_index_path,
            ),
            postcheck_passed=publication.postcheck_passed,
        )
        recovery.create_checkpoint(
            layout,
            phase_store,
            boundary_kind="phase",
            boundary_id="U12",
            boundary_ordinal=0,
            artifact_paths=(
                publication.paths.manifest_path,
                current_report_path,
                publication.paths.article_path,
                publication.paths.dossier_path,
                publication.paths.artifact_index_path,
            ),
            now=now,
        )
        if u12_event.get("phase_id") != "U12":
            raise RuntimeError("PhaseStore did not complete U12")

        current = status_store.read()
        complete_status = status_store.transition(
            current,
            "complete",
            _strictly_later(now, current.updated_at),
            current_phase="U12",
            last_complete_phase="U12",
            reason="post-publish validation passed",
            validation_passed=True,
        )
        verdict = bundle.documents.get("verdict")
        if not isinstance(verdict, Mapping):
            raise RuntimeError("complete materialization has no locked verdict")
        build_final_chat_projection(layout, verdict, complete_status)
        final_chat_path = write_final_chat_projection(
            layout, verdict, complete_status
        )
        IndexStore(layout.root).rebuild()
        return CompleteMaterializationResult(
            run_id=run_id,
            status="complete",
            manifest_path=publication.paths.manifest_path,
            article_path=publication.paths.article_path,
            dossier_path=publication.paths.dossier_path,
            artifact_index_path=publication.paths.artifact_index_path,
            final_chat_path=final_chat_path,
            postcheck_passed=True,
        )
    except BaseException as error:
        if not attention_marked:
            try:
                mark_needs_attention(f"materialization failed: {type(error).__name__}: {error}")
            except BaseException as status_error:
                add_note = getattr(error, "add_note", None)
                if callable(add_note):
                    add_note(
                        "failed to mark materialization needs_attention: "
                        f"{status_error}"
                    )
        raise
    finally:
        release_run_lease(layout, lease)


__all__ = (
    "AUTHORING_SLOT_RELATIVE_PATHS",
    "ArtifactSpec",
    "CompleteMaterializationResult",
    "MaterializedBundle",
    "PreparedAuthoring",
    "artifact_destination",
    "build_materialization_control",
    "checkpoint_article_packets",
    "complete_u12",
    "discover_authoring_inputs",
    "build_artifact_index_bytes",
    "materialize_complete_run",
    "materialize_u4_u11",
    "prepare_authoring",
    "record_materialized_phase",
    "seal_authoring_artifact",
)
