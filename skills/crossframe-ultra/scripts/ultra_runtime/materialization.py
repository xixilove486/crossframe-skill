from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from typing import Any

from .constants import PHASES, current_version_binding
from .foundation import (
    FoundationInputError,
    load_input_inventory,
    load_request_profile,
)
from .host_handshake import HostActionSeal
from .jsonio import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
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
REQUEST_INTAKE_AUTHORITY_RELATIVE_PATH = Path(
    "recovery/request-intake-authority.json"
)
_REQUEST_INTAKE_AUTHORITY_FIELDS = frozenset(
    {
        "schema_id",
        "schema_version",
        "run_id",
        "version_binding",
        "generated_at",
        "request_sha256",
        "request_size",
        "content_sha256",
    }
)


class FoundationRecoveryError(RuntimeError):
    """A partial foundation cannot continue from its durable checkpoint."""


class _AuthoringWaitSignal(RuntimeError):
    def __init__(self, action: Mapping[str, object]) -> None:
        super().__init__("materialization is awaiting the next model-owned slot")
        self.action = copy.deepcopy(dict(action))


@dataclass(frozen=True, slots=True)
class MaterializationProgress:
    outcome: str
    run_id: str
    status: str
    current_phase: str
    last_complete_phase: str | None
    next_action: dict[str, object] | None
    final_chat: dict[str, object] | None


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

_OUTPUT_PLAN_UPSTREAM_SCHEMA_SEQUENCE = (
    "crossframe.ultra.v82.evidence-ledger",
    "crossframe.ultra.v82.world-volume",
    "crossframe.ultra.v82.transformation-ledger",
    "crossframe.ultra.v82.concept-disposition",
    "crossframe.ultra.v82.claim-mechanism-graph",
    "crossframe.ultra.v82.recursive-lineage",
    "crossframe.ultra.v82.order-evaluation",
    "crossframe.ultra.v82.red-team-report",
    "crossframe.ultra.v82.verdict",
    "crossframe.ultra.v82.action-ranking",
    "crossframe.ultra.v82.forecast-ledger",
)
_OUTPUT_PLAN_UPSTREAM_PHASE_BY_SCHEMA_ID = {
    "crossframe.ultra.v82.evidence-ledger": "U3",
    "crossframe.ultra.v82.world-volume": "U4",
    "crossframe.ultra.v82.transformation-ledger": "U5",
    "crossframe.ultra.v82.concept-disposition": "U5",
    "crossframe.ultra.v82.claim-mechanism-graph": "U6",
    "crossframe.ultra.v82.recursive-state": "U7",
    "crossframe.ultra.v82.recursive-lineage": "U7",
    "crossframe.ultra.v82.order-evaluation": "U8",
    "crossframe.ultra.v82.red-team-report": "U8",
    "crossframe.ultra.v82.verdict": "U9",
    "crossframe.ultra.v82.action-ranking": "U9",
    "crossframe.ultra.v82.forecast-ledger": "U9",
}
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
    control = build_materialization_control(layout)
    if control_path.exists():
        try:
            raw = control_path.read_bytes()
            existing = load_json_object_bytes(raw, source=str(control_path))
        except (OSError, TypeError, ValueError) as error:
            raise FoundationInputError("materialization control is unreadable") from error
        if raw != canonical_json_bytes(existing) or existing != control:
            raise FoundationInputError("materialization control authority differs")
    else:
        atomic_write_json(control_path, control)
    return PreparedAuthoring(
        authoring_dir=layout.authoring_dir,
        relative_slots=AUTHORING_SLOT_RELATIVE_PATHS,
        slot_paths=tuple(layout.authoring_dir / slot for slot in AUTHORING_SLOT_RELATIVE_PATHS),
        control_path=control_path,
    )


_AUTHORING_PHASE_GROUPS: dict[str, tuple[str, ...]] = {
    "U4": ("U04-world-volume.json",),
    "U5": ("U05-transformation-ledger.json", "U05-concept-disposition.json"),
    "U6": ("U06-claim-mechanism-graph.json",),
    "U7": ("U07-recursive-states/<node-id>.json", "U07-recursive-lineage.json"),
    "U8": ("U08-order-evaluation.json", "U08-red-team-report.json"),
    "U9": (
        "U09-verdict.json",
        "U09-action-ranking.json",
        "U09-forecast-ledger.json",
    ),
    "U10": ("U10-framework-gap-ledger.json", "U10-output-plan.json"),
    "U11": (
        "U11-semantic-coverage.json",
        "U11-article-review.json",
        "完整推演档案.md",
    ),
}


def _authoring_slot_paths(
    layout: RunLayout,
    relative_path: str,
) -> tuple[Path, ...]:
    if relative_path == "U07-recursive-states/<node-id>.json":
        return tuple(
            sorted(
                (layout.authoring_dir / "U07-recursive-states").glob("*.json"),
                key=lambda path: path.name,
            )
        )
    if relative_path == "article/packets/<packet-id>.md":
        return tuple(
            sorted(
                (layout.authoring_dir / "article/packets").glob("*.md"),
                key=lambda path: path.name,
            )
        )
    path = layout.authoring_dir / relative_path
    return (path,) if path.is_file() else ()


def _authoring_slot_exists(layout: RunLayout, relative_path: str) -> bool:
    return bool(_authoring_slot_paths(layout, relative_path))


def _validate_present_authoring_slots(
    layout: RunLayout,
    relative_paths: Sequence[str],
) -> None:
    for relative_path in relative_paths:
        for path in _authoring_slot_paths(layout, relative_path):
            try:
                if path.suffix.casefold() == ".json":
                    load_json_object(path)
                    continue
                raw = path.read_bytes()
                text = raw.decode("utf-8")
            except (OSError, TypeError, UnicodeDecodeError, ValueError) as error:
                raise ValueError(
                    f"model-authored slot is unreadable: {relative_path}"
                ) from error
            if not text.strip() or "\x00" in text or text.startswith("\ufeff"):
                raise ValueError(
                    f"model-authored slot is unreadable: {relative_path}"
                )


def next_authoring_action(
    layout: RunLayout,
    phase_store: object,
) -> dict[str, object] | None:
    """Return the unique next model-owned slot, or ``None`` when U4-U11 are ready."""

    _validate_layout(layout)
    current = getattr(phase_store, "current_phase", None)
    if not isinstance(current, str):
        return None
    try:
        phase_number = int(current[1:])
    except (ValueError, IndexError):
        return None
    next_phase = f"U{phase_number + 1}"
    group = _AUTHORING_PHASE_GROUPS.get(next_phase)
    if group is None:
        return None
    if next_phase == "U11":
        packet_slot = "article/packets/<packet-id>.md"
        _validate_present_authoring_slots(layout, (*group, packet_slot))
        if not _authoring_slot_exists(layout, packet_slot):
            return {
                "action_kind": "authoring",
                "owner": "model",
                "phase_id": "U11",
                "relative_path": packet_slot,
            }
    else:
        _validate_present_authoring_slots(layout, group)
    missing = tuple(path for path in group if not _authoring_slot_exists(layout, path))
    if not missing:
        return None
    action: dict[str, object] = {
        "action_kind": "authoring",
        "owner": "model",
        "phase_id": next_phase,
        "relative_path": missing[0],
    }
    if len(missing) > 1:
        action["relative_paths"] = list(missing)
    return action


def foundation_progress_projection(
    layout: RunLayout,
    progress: object,
) -> MaterializationProgress:
    """Project a foundation result into the stable public progress shape."""

    pending = getattr(progress, "pending_action", None)
    phase_store = getattr(progress, "phase_store", None)
    completed_phase = getattr(progress, "completed_phase", None)
    if pending is not None:
        action = copy.deepcopy(getattr(pending, "document", pending))
        phase_id = str(action.get("phase_id", completed_phase or "U0"))
        last = None if phase_store is None else getattr(phase_store, "current_phase", None)
        return MaterializationProgress(
            outcome="awaiting-host-action",
            run_id=layout.run_dir.name,
            status="running",
            current_phase=phase_id,
            last_complete_phase=last,
            next_action=action,
            final_chat=None,
        )
    if getattr(progress, "outcome", None) == "blocked":
        last = None if phase_store is None else getattr(phase_store, "current_phase", None)
        current = last or completed_phase or "U0"
        return MaterializationProgress(
            outcome="blocked",
            run_id=layout.run_dir.name,
            status="blocked",
            current_phase=str(current),
            last_complete_phase=last,
            next_action=None,
            final_chat=None,
        )
    if phase_store is None:
        raise FoundationRecoveryError("foundation progress has no PhaseStore")
    last = getattr(phase_store, "current_phase", None)
    action = next_authoring_action(layout, phase_store)
    if action is not None:
        return MaterializationProgress(
            outcome="awaiting-authoring",
            run_id=layout.run_dir.name,
            status="running",
            current_phase=str(action["phase_id"]),
            last_complete_phase=last,
            next_action=action,
            final_chat=None,
        )
    return MaterializationProgress(
        outcome="foundation-complete",
        run_id=layout.run_dir.name,
        status="running",
        current_phase=str(last),
        last_complete_phase=last,
        next_action=None,
        final_chat=None,
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
    recursive_state_replacements: dict[str, str] = {}
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
        supplied_replacements = authority_values.get(
            "recursive_state_hash_replacements"
        )
        if (
            spec.relative_path == "U07-recursive-lineage.json"
            and isinstance(supplied_replacements, Mapping)
        ):
            recursive_state_replacements = {
                str(prior): str(current)
                for prior, current in supplied_replacements.items()
            }
        for field, value in authority_values.items():
            if field in sealed:
                if (
                    spec.relative_path == "U07-recursive-lineage.json"
                    and field == "recursive_state_artifact_hashes"
                    and isinstance(sealed[field], list)
                    and isinstance(value, list)
                    and len(sealed[field]) == len(value)
                ):
                    if not recursive_state_replacements:
                        recursive_state_replacements = dict(
                            zip(sealed[field], value, strict=True)
                        )
                sealed[field] = copy.deepcopy(value)
    if recursive_state_replacements:
        nodes = sealed.get("nodes")
        if isinstance(nodes, list):
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                prior = node.get("recursive_state_artifact_sha256")
                if isinstance(prior, str) and prior in recursive_state_replacements:
                    node["recursive_state_artifact_sha256"] = (
                        recursive_state_replacements[prior]
                    )
    if "parent_run_id" in sealed:
        sealed["parent_run_id"] = layout.run_dir.name
    if spec.relative_path == "U10-output-plan.json":
        sealed["article_path"] = "work/authoring/article.partial.md"
        sealed["coverage_required"] = True
        sealed["official_filename_allowed"] = False
        expected_required_artifacts = (
            None
            if authority_values is None
            else authority_values.get("output_plan_required_artifacts")
        )
        if expected_required_artifacts is None:
            raise ValueError(
                "U10 sealing requires runtime-derived U3-U9 required_artifacts"
            )
        _rebind_output_plan_required_artifacts(
            sealed,
            expected_required_artifacts,
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
    if spec.relative_path == "U10-output-plan.json":
        from . import article

        expected_u9_parent = (
            None
            if authority_values is None
            else authority_values.get("u9_parent_event_sha256")
        )
        if not isinstance(expected_u9_parent, str):
            raise ValueError("U10 sealing requires the runtime-derived U9 parent event")
        validated = article.validate_output_plan_artifact(
            validated,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_u9_parent_event_sha256=expected_u9_parent,
            expected_required_artifacts=expected_required_artifacts,
        )
        authority_documents = (
            None
            if authority_values is None
            else authority_values.get("output_plan_authority_documents")
        )
        if authority_documents is not None:
            if not isinstance(authority_documents, Mapping):
                raise TypeError("output-plan authority documents must be a mapping")
            required_concept_semantic_unit_ids = authority_values.get(
                "required_concept_semantic_unit_ids"
            )
            if required_concept_semantic_unit_ids is None:
                raise ValueError(
                    "U10 sealing requires runtime-derived concept semantic units"
                )
            _validate_output_plan_semantic_authority(
                validated,
                authority_documents,
                required_concept_semantic_unit_ids=(
                    required_concept_semantic_unit_ids
                ),
            )
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
    partial_path = layout.authoring_dir / PARTIAL_ARTICLE_RELATIVE_PATH
    if not partial_path.is_file():
        raise ValueError("article packet checkpoints require the assembled partial article")
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
                artifact_paths=(partial_path, packet),
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


def _required_artifact_records(
    value: object,
    *,
    label: str,
) -> tuple[dict[str, str], ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be an array")
    records: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping) or set(raw) != {
            "path",
            "sha256",
            "media_type",
        }:
            raise ValueError(
                f"{label}[{index}] must contain only path, sha256, and media_type"
            )
        path = raw.get("path")
        digest = raw.get("sha256")
        media_type = raw.get("media_type")
        if not isinstance(path, str) or not path:
            raise ValueError(f"{label}[{index}] path must be nonempty")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(f"{label}[{index}] sha256 must be lowercase SHA-256")
        if media_type != "application/json":
            raise ValueError(f"{label}[{index}] must identify a JSON artifact")
        key = (path, digest, media_type)
        if key in seen:
            raise ValueError(f"{label} contains duplicate artifact records")
        seen.add(key)
        records.append(
            {"path": path, "sha256": digest, "media_type": media_type}
        )
    if not records:
        raise ValueError(f"{label} must not be empty")
    return tuple(records)


def _rebind_output_plan_required_artifacts(
    output_plan: dict[str, Any],
    expected_required_artifacts: object,
) -> None:
    declared = _required_artifact_records(
        output_plan.get("required_artifacts"),
        label="model-authored output-plan required_artifacts",
    )
    expected = _required_artifact_records(
        expected_required_artifacts,
        label="runtime-derived U3-U9 required_artifacts",
    )
    declared_identity = tuple(
        (record["path"], record["media_type"]) for record in declared
    )
    expected_identity = tuple(
        (record["path"], record["media_type"]) for record in expected
    )
    if declared_identity != expected_identity:
        raise ValueError(
            "output-plan paths do not match runtime-derived U3-U9 required_artifacts"
        )

    replacements: dict[str, str] = {}
    for authored, frozen in zip(declared, expected, strict=True):
        previous = replacements.setdefault(authored["sha256"], frozen["sha256"])
        if previous != frozen["sha256"]:
            raise ValueError(
                "one model-authored output-plan hash resolves to multiple upstream artifacts"
            )
    output_plan["required_artifacts"] = copy.deepcopy(list(expected))
    for collection_name in ("sections", "appendices"):
        collection = output_plan.get(collection_name)
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
    semantic_universe = output_plan.get("semantic_universe")
    if isinstance(semantic_universe, list):
        for unit in semantic_universe:
            if not isinstance(unit, dict):
                continue
            authority_hash = unit.get("authority_artifact_sha256")
            if isinstance(authority_hash, str):
                unit["authority_artifact_sha256"] = replacements.get(
                    authority_hash,
                    authority_hash,
                )
        output_plan["semantic_universe_sha256"] = sha256_bytes(
            canonical_json_bytes(semantic_universe)
        )


def _derive_output_plan_upstream_authority(
    layout: RunLayout,
    authorities: Sequence[tuple[Path, Mapping[str, object]]],
) -> tuple[tuple[dict[str, str], ...], dict[str, Mapping[str, object]]]:
    frozen = tuple(authorities)
    schema_ids = tuple(document.get("schema_id") for _, document in frozen)
    recursive_count = schema_ids.count("crossframe.ultra.v82.recursive-state")
    if recursive_count < 1:
        raise ValueError("runtime-derived U3-U9 authority requires recursive states")
    expected_schema_ids = (
        *_OUTPUT_PLAN_UPSTREAM_SCHEMA_SEQUENCE[:5],
        *("crossframe.ultra.v82.recursive-state",) * recursive_count,
        *_OUTPUT_PLAN_UPSTREAM_SCHEMA_SEQUENCE[5:],
    )
    if schema_ids != expected_schema_ids:
        raise ValueError(
            "validated U3-U9 documents do not match the frozen upstream artifact DAG"
        )

    records: list[dict[str, str]] = []
    documents_by_sha256: dict[str, Mapping[str, object]] = {}
    seen_paths: set[str] = set()
    for path, document in frozen:
        if not isinstance(path, Path) or not path.is_file():
            raise ValueError("runtime-derived U3-U9 authority path is not a file")
        if not isinstance(document, Mapping):
            raise TypeError("runtime-derived U3-U9 authority must be a document")
        assert_safe_descendant(layout.root, path)
        if layout.artifacts_dir not in path.parents:
            raise ValueError(
                "runtime-derived U3-U9 authority must occupy the artifacts namespace"
            )
        schema_id = document.get("schema_id")
        expected_phase = _OUTPUT_PLAN_UPSTREAM_PHASE_BY_SCHEMA_ID.get(schema_id)
        if expected_phase is None or document.get("phase_id") != expected_phase:
            raise ValueError(
                "runtime-derived U3-U9 authority has an invalid schema/phase identity"
            )
        canonical_bytes = canonical_json_bytes(document)
        if path.read_bytes() != canonical_bytes:
            raise ValueError(
                "runtime-derived U3-U9 authority differs from its validated document"
            )
        relative = path.relative_to(layout.run_dir).as_posix()
        digest = sha256_bytes(canonical_bytes)
        if relative in seen_paths or digest in documents_by_sha256:
            raise ValueError(
                "runtime-derived U3-U9 authority reuses an artifact path or hash"
            )
        seen_paths.add(relative)
        documents_by_sha256[digest] = copy.deepcopy(dict(document))
        records.append(
            {
                "path": relative,
                "sha256": digest,
                "media_type": "application/json",
            }
        )
    return tuple(records), documents_by_sha256


def _owner_id(record: Mapping[str, object], field: str, label: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} has no record owner ID")
    return value


def _record_mappings(value: object, label: str) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be an array of owned records")
    result: list[Mapping[str, object]] = []
    for index, record in enumerate(value):
        if not isinstance(record, Mapping):
            raise ValueError(f"{label}[{index}] must be an owned record")
        result.append(record)
    return tuple(result)


_OwnerPath = tuple[str | int, ...]


def _register_owner(
    owners: dict[str, _OwnerPath],
    locator: str,
    owner_path: _OwnerPath,
) -> None:
    previous = owners.get(locator)
    if previous is not None:
        raise ValueError(
            "upstream artifact has duplicate owner locator "
            f"{locator!r}: {previous!r} and {owner_path!r}"
        )
    owners[locator] = owner_path


def _register_record_owners(
    owners: dict[str, _OwnerPath],
    value: object,
    field: str,
    role_path: _OwnerPath,
) -> None:
    label = ".".join(str(part) for part in role_path)
    for index, record in enumerate(_record_mappings(value, label)):
        _register_owner(
            owners,
            _owner_id(record, field, f"{label}[{index}]"),
            (*role_path, index, field),
        )


def _artifact_authority_owner_map(
    document: Mapping[str, object],
) -> dict[str, _OwnerPath]:
    schema_id = document.get("schema_id")
    owners: dict[str, _OwnerPath] = {}
    if schema_id == "crossframe.ultra.v82.evidence-ledger":
        _register_record_owners(
            owners,
            document.get("entries"),
            "evidence_id",
            ("entries",),
        )
        _register_record_owners(
            owners,
            document.get("unknowns"),
            "unknown_id",
            ("unknowns",),
        )
    elif schema_id == "crossframe.ultra.v82.world-volume":
        _register_owner(
            owners,
            _owner_id(document, "volume_id", "world volume"),
            ("world-volume", "volume_id"),
        )
        for collection, field in (
            ("actors", "actor_id"),
            ("circles", "circle_id"),
            ("positions", "position_id"),
            ("clocks", "clock_id"),
            ("channels", "channel_id"),
            ("events", "event_id"),
            ("local_distributions", "distribution_id"),
            ("unknowns", "unknown_id"),
            ("residuals", "residual_id"),
        ):
            _register_record_owners(
                owners,
                document.get(collection),
                field,
                (collection,),
            )
        for collection in ("actors", "circles", "positions"):
            for index, record in enumerate(
                _record_mappings(document.get(collection), collection)
            ):
                for state_field in ("M_state", "Psi_state"):
                    state = record.get(state_field)
                    if not isinstance(state, Mapping):
                        raise ValueError(
                            f"{collection}[{index}].{state_field} must be an owned record"
                        )
                    _register_owner(
                        owners,
                        _owner_id(
                            state,
                            "state_id",
                            f"{collection}[{index}].{state_field}",
                        ),
                        (collection, index, state_field, "state_id"),
                    )
    elif schema_id == "crossframe.ultra.v82.transformation-ledger":
        transformations = _record_mappings(
            document.get("transformations"), "transformations"
        )
        for index, transformation in enumerate(transformations):
            label = f"transformations[{index}]"
            _register_owner(
                owners,
                _owner_id(transformation, "transform_id", label),
                ("transformations", index, "transform_id"),
            )
            for collection in ("preserved", "changed", "folded", "omitted", "unknown"):
                _register_record_owners(
                    owners,
                    transformation.get(collection),
                    "component_id",
                    ("transformations", index, collection),
                )
            _register_record_owners(
                owners,
                transformation.get("effective_variables"),
                "variable_ref",
                ("transformations", index, "effective_variables"),
            )
            for collection, field in (
                ("task_relative_loss", "loss_id"),
                ("location_effects", "effect_id"),
                ("return_conditions", "condition_id"),
            ):
                _register_record_owners(
                    owners,
                    transformation.get(collection),
                    field,
                    ("transformations", index, collection),
                )
    elif schema_id == "crossframe.ultra.v82.concept-disposition":
        dispositions = _record_mappings(document.get("dispositions"), "dispositions")
        for index, disposition in enumerate(dispositions):
            label = f"dispositions[{index}]"
            _register_owner(
                owners,
                _owner_id(disposition, "concept_id", label),
                ("dispositions", index, "concept_id"),
            )
            branch = disposition.get("condition_branch")
            if branch is not None:
                if not isinstance(branch, Mapping):
                    raise ValueError(f"{label}.condition_branch must be an owned record")
                _register_owner(
                    owners,
                    _owner_id(branch, "branch_id", f"{label}.condition_branch"),
                    ("dispositions", index, "condition_branch", "branch_id"),
                )
                plan = branch.get("evidence_plan")
                if not isinstance(plan, Mapping):
                    raise ValueError(
                        f"{label}.condition_branch.evidence_plan must be an owned record"
                    )
                _register_owner(
                    owners,
                    _owner_id(
                        plan,
                        "plan_id",
                        f"{label}.condition_branch.evidence_plan",
                    ),
                    (
                        "dispositions",
                        index,
                        "condition_branch",
                        "evidence_plan",
                        "plan_id",
                    ),
                )
        _register_record_owners(
            owners,
            document.get("semantic_obligations"),
            "obligation_id",
            ("semantic_obligations",),
        )
    elif schema_id == "crossframe.ultra.v82.claim-mechanism-graph":
        for collection, field in (
            ("claims", "claim_id"),
            ("mechanisms", "mechanism_id"),
            ("edges", "edge_id"),
            ("explanations", "explanation_id"),
            ("insights", "insight_id"),
        ):
            _register_record_owners(
                owners,
                document.get(collection),
                field,
                (collection,),
            )
    elif schema_id == "crossframe.ultra.v82.recursive-state":
        _register_owner(
            owners,
            _owner_id(document, "node_id", "recursive state"),
            ("recursive-state", "node_id"),
        )
        bounded_subgraph = document.get("bounded_subgraph")
        if bounded_subgraph is not None:
            if not isinstance(bounded_subgraph, Mapping):
                raise ValueError(
                    "recursive state bounded_subgraph must be an owned record"
                )
            _register_owner(
                owners,
                _owner_id(
                    bounded_subgraph,
                    "subgraph_id",
                    "recursive state bounded_subgraph",
                ),
                ("bounded_subgraph", "subgraph_id"),
            )
    elif schema_id == "crossframe.ultra.v82.recursive-lineage":
        _register_record_owners(
            owners,
            document.get("branches"),
            "branch_id",
            ("branches",),
        )
    elif schema_id == "crossframe.ultra.v82.order-evaluation":
        for index, evaluation in enumerate(
            _record_mappings(document.get("evaluations"), "evaluations")
        ):
            baseline = evaluation.get("baseline")
            if not isinstance(baseline, Mapping):
                raise ValueError(f"evaluations[{index}].baseline must be an owned record")
            _register_owner(
                owners,
                _owner_id(
                    baseline,
                    "baseline_id",
                    f"evaluations[{index}].baseline",
                ),
                ("evaluations", index, "baseline", "baseline_id"),
            )
    elif schema_id == "crossframe.ultra.v82.red-team-report":
        for collection, field in (
            ("attacks", "attack_id"),
            ("sensitivity_checks", "check_id"),
            ("unresolved_items", "unresolved_item_id"),
        ):
            _register_record_owners(
                owners,
                document.get(collection),
                field,
                (collection,),
            )
    elif schema_id == "crossframe.ultra.v82.verdict":
        _register_record_owners(
            owners,
            document.get("five_verdicts"),
            "verdict_id",
            ("five_verdicts",),
        )
    elif schema_id == "crossframe.ultra.v82.action-ranking":
        _register_record_owners(
            owners,
            document.get("options"),
            "option_id",
            ("options",),
        )
    elif schema_id == "crossframe.ultra.v82.forecast-ledger":
        _register_record_owners(
            owners,
            document.get("forecasts"),
            "forecast_id",
            ("forecasts",),
        )
    else:
        raise ValueError("upstream artifact has no approved record-owner locators")
    if not owners:
        raise ValueError("upstream artifact has no owned authority locators")
    return owners


def _concept_semantic_owner_locators(
    document: Mapping[str, object],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for index, obligation in enumerate(
        _record_mappings(document.get("semantic_obligations"), "semantic_obligations")
    ):
        semantic_unit_id = _owner_id(
            obligation,
            "semantic_unit_id",
            f"semantic_obligations[{index}] semantic unit",
        )
        obligation_id = _owner_id(
            obligation,
            "obligation_id",
            f"semantic_obligations[{index}]",
        )
        if semantic_unit_id in result:
            raise ValueError("concept disposition repeats a semantic unit ID")
        result[semantic_unit_id] = obligation_id
    return result


def _validate_output_plan_semantic_authority(
    output_plan: Mapping[str, object],
    authority_documents_by_sha256: Mapping[str, Mapping[str, object]],
    *,
    required_concept_semantic_unit_ids: Collection[str],
) -> None:
    required = _required_artifact_records(
        output_plan.get("required_artifacts"),
        label="sealed output-plan required_artifacts",
    )
    required_hashes = tuple(record["sha256"] for record in required)
    if set(required_hashes) != set(authority_documents_by_sha256):
        raise ValueError(
            "sealed output-plan authority differs from runtime-derived U3-U9 documents"
        )
    if isinstance(
        required_concept_semantic_unit_ids,
        (str, bytes, bytearray, Mapping),
    ) or not isinstance(required_concept_semantic_unit_ids, Collection):
        raise TypeError("required concept semantic units must be a collection")
    required_concept_ids = frozenset(required_concept_semantic_unit_ids)
    if not all(isinstance(unit_id, str) and unit_id for unit_id in required_concept_ids):
        raise ValueError("required concept semantic units must be identified")
    concept_authorities = [
        (digest, document)
        for digest, document in authority_documents_by_sha256.items()
        if document.get("schema_id") == "crossframe.ultra.v82.concept-disposition"
    ]
    if len(concept_authorities) != 1:
        raise ValueError("runtime authority must contain one concept disposition")
    concept_sha256, concept_document = concept_authorities[0]
    concept_owner_by_semantic_id = _concept_semantic_owner_locators(concept_document)
    if not required_concept_ids.issubset(concept_owner_by_semantic_id):
        raise ValueError(
            "required concept semantic units differ from the validated concept disposition"
        )
    unit_dependencies: dict[str, frozenset[str]] = {}
    for collection_name in ("sections", "appendices"):
        collection = output_plan.get(collection_name)
        if not isinstance(collection, list):
            raise ValueError(f"output-plan {collection_name} must be an array")
        for entry in collection:
            if not isinstance(entry, Mapping):
                raise ValueError("output-plan section must be an object")
            dependencies = entry.get("dependency_hashes")
            unit_ids = entry.get("semantic_unit_ids")
            if not isinstance(dependencies, list) or not isinstance(unit_ids, list):
                raise ValueError("output-plan section authority arrays are invalid")
            dependency_set = frozenset(dependencies)
            for unit_id in unit_ids:
                if isinstance(unit_id, str):
                    unit_dependencies[unit_id] = dependency_set

    semantic_universe = output_plan.get("semantic_universe")
    if not isinstance(semantic_universe, list):
        raise ValueError("output-plan semantic universe must be an array")
    unit_authority: dict[str, tuple[str, str]] = {}
    authorized_hashes: set[str] = set()
    for raw in semantic_universe:
        if not isinstance(raw, Mapping):
            raise ValueError("output-plan semantic unit must be an object")
        unit_id = raw.get("unit_id")
        authority_hash = raw.get("authority_artifact_sha256")
        locator = raw.get("authority_locator")
        if not isinstance(unit_id, str) or not isinstance(authority_hash, str):
            raise ValueError("output-plan semantic authority identity is invalid")
        document = authority_documents_by_sha256.get(authority_hash)
        if document is None:
            raise ValueError(
                f"semantic unit {unit_id} is outside runtime-derived U3-U9 authority"
            )
        if not isinstance(locator, str) or locator not in _artifact_authority_owner_map(
            document
        ):
            raise ValueError(
                f"semantic unit {unit_id} authority_locator is absent from its bound artifact"
            )
        if authority_hash not in unit_dependencies.get(unit_id, frozenset()):
            raise ValueError(
                f"semantic unit {unit_id} authority is absent from its section dependencies"
            )
        unit_authority[unit_id] = (authority_hash, locator)
        authorized_hashes.add(authority_hash)
    missing_artifact_paths = [
        record["path"]
        for record in required
        if record["sha256"] not in authorized_hashes
    ]
    if missing_artifact_paths:
        raise ValueError(
            "runtime-derived required artifacts without semantic-unit authority: "
            f"{missing_artifact_paths}"
        )
    missing_concept_ids = sorted(required_concept_ids - set(unit_authority))
    misbound_concept_ids = sorted(
        unit_id
        for unit_id in required_concept_ids.intersection(unit_authority)
        if unit_authority[unit_id]
        != (concept_sha256, concept_owner_by_semantic_id[unit_id])
    )
    if missing_concept_ids or misbound_concept_ids:
        raise ValueError(
            "output plan omits or misbinds required concept semantic units: "
            f"missing={missing_concept_ids}, misbound={misbound_concept_ids}"
        )


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
    events = getattr(phase_store, "events", None)
    if not isinstance(events, tuple):
        return None
    active: list[dict[str, object]] = []
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("phase event history contains a non-mapping")
        if event.get("status") == "complete":
            active.append(dict(event))
        elif event.get("status") == "invalidated":
            reset_from = event.get("reset_from_phase")
            if not isinstance(reset_from, str) or reset_from not in PHASES:
                raise ValueError("phase invalidation has no reset authority")
            active = active[: PHASES.index(reset_from)]
    matching = [event for event in active if event.get("phase_id") == phase_id]
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
    if relative_path in {
        "U01-read-events.jsonl",
        "U02-retrieval-ledger.json",
        "U03-evidence-ledger.json",
    } and source.exists():
        raise FoundationRecoveryError(
            f"runtime-owned foundation artifact was placed in model authoring: {relative_path}"
        )
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
        authored_artifact_sha256 = _full_artifact_sha256(load_json_object(source))
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
                sealed_sha256 = _full_artifact_sha256(sealed)
                recursive_hashes.append(sealed_sha256)
                replacements = authority_values.get(
                    "recursive_state_hash_replacements"
                )
                if isinstance(replacements, dict):
                    replacements[authored_artifact_sha256] = sealed_sha256
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
        if path.is_file()
        and path.name
        not in {"ultra-artifact-manifest.json", "ultra-artifact-index.md"}
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
) -> MaterializedBundle | HostActionSeal:
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
    evidence_path = artifact_destination(
        layout,
        prepared.authoring_dir / evidence_spec.relative_path,
    )
    upstream_authorities: list[tuple[Path, Mapping[str, object]]] = [
        (evidence_path, evidence)
    ]

    from . import (
        article,
        concept_closure,
        coverage,
        forecast,
        judgment,
        recursion,
        semantic_review,
        world_volume,
    )

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
    upstream_authorities.extend(zip(paths, values, strict=True))

    knowledge_values, source_manifest_sha256 = _knowledge_authorities(repo)
    u5_sources = (
        prepared.authoring_dir / "U05-transformation-ledger.json",
        prepared.authoring_dir / "U05-concept-disposition.json",
    )

    required_concept_semantic_unit_ids: frozenset[str] | None = None

    def validate_u5(values: Sequence[Mapping[str, object]]) -> None:
        nonlocal required_concept_semantic_unit_ids
        transformations, concepts = values
        required_concept_semantic_unit_ids = concept_closure.validate_concept_closure(
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
    if required_concept_semantic_unit_ids is None:
        raise RuntimeError("U5 validation did not return concept semantic units")
    documents["transformation_ledger"], documents["concept_disposition"] = values
    phase_events.append(event)
    artifact_paths.extend(paths)
    upstream_authorities.extend(zip(paths, values, strict=True))

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
    upstream_authorities.extend(zip(paths, values, strict=True))

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
        authority_values={
            "recursive_state_artifact_hashes": recursive_hashes,
            "recursive_state_hash_replacements": {},
        },
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
    upstream_authorities.extend(zip(paths, values, strict=True))

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
    upstream_authorities.extend(zip(paths, values, strict=True))

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
    upstream_authorities.extend(zip(paths, values, strict=True))

    required_artifacts, authority_documents_by_sha256 = (
        _derive_output_plan_upstream_authority(layout, upstream_authorities)
    )

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
            expected_required_artifacts=required_artifacts,
        )
        _validate_output_plan_semantic_authority(
            output_plan,
            authority_documents_by_sha256,
            required_concept_semantic_unit_ids=(
                required_concept_semantic_unit_ids
            ),
        )

    event, values, paths = _seal_json_phase(
        layout,
        phase_store,
        "U10",
        u10_sources,
        generated_at=now,
        authority_documents=documents,
        authority_values={
            "u9_parent_event_sha256": u9_event_sha256,
            "output_plan_required_artifacts": required_artifacts,
            "output_plan_authority_documents": authority_documents_by_sha256,
            "required_concept_semantic_unit_ids": (
                required_concept_semantic_unit_ids
            ),
        },
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
    packets = _packet_mappings(documents["output_plan"], packet_paths)
    partial_path = prepared.authoring_dir / PARTIAL_ARTICLE_RELATIVE_PATH
    assembled = article.assemble_article(documents["output_plan"], packets, partial_path)
    u11_event = _completed_phase_event(phase_store, "U11")
    active_generation = getattr(phase_store, "active_generation", 0)
    if type(active_generation) is not int or active_generation < 0:
        raise ValueError("U11 semantic review active generation is invalid")
    persisted_semantic_action = semantic_review.load_semantic_review_action(
        layout,
        active_generation,
    )
    u11_generated_at = now
    if u11_event is not None or persisted_semantic_action is not None:
        existing_coverage_path = artifact_destination(
            layout,
            prepared.authoring_dir / "U11-semantic-coverage.json",
        )
        existing_coverage = load_json_object(existing_coverage_path)
        if persisted_semantic_action is not None:
            payload = persisted_semantic_action.document.get("payload")
            if (
                not isinstance(payload, Mapping)
                or payload.get("coverage_artifact_sha256")
                != _sha256_file(existing_coverage_path)
            ):
                raise ValueError(
                    "persisted semantic review coverage authority differs"
                )
        existing_timestamp = existing_coverage.get("generated_at")
        if not isinstance(existing_timestamp, str) or not existing_timestamp.endswith("Z"):
            raise ValueError("completed U11 coverage has no canonical generated_at")
        u11_generated_at = datetime.fromisoformat(
            existing_timestamp[:-1] + "+00:00"
        )
    if u11_event is None and persisted_semantic_action is None:
        checkpoint_article_packets(
            layout,
            phase_store,
            packet_paths,
            now=now,
            create_checkpoint=create_checkpoint,
        )

    coverage_source = prepared.authoring_dir / "U11-semantic-coverage.json"
    coverage_document = seal_authoring_artifact(
        layout,
        coverage_source,
        generated_at=u11_generated_at,
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
        generated_at=u11_generated_at,
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
        generated_at=_canonical_utc(u11_generated_at),
        expected_output_plan_artifact_sha256=_full_artifact_sha256(documents["output_plan"]),
        expected_coverage_artifact_sha256=_full_artifact_sha256(coverage_document),
    )
    if built_review.get("overall_status") != "mechanical-complete":
        raise ValueError(
            "deterministic U11 article review must be mechanical-complete"
        )
    if authored_review != built_review:
        raise ValueError("model-authored article review differs from deterministic runtime review")
    review_destination = artifact_destination(layout, review_source)
    atomic_write_json(review_destination, built_review)
    documents["article_review"] = built_review

    intake_path = _request_intake_authority_path(layout)
    try:
        intake_raw = intake_path.read_bytes()
        intake = load_json_object_bytes(intake_raw, source=str(intake_path))
    except (OSError, TypeError, ValueError) as error:
        raise ValueError("semantic review requires request intake authority") from error
    request_sha256 = intake.get("request_sha256")
    run_contract = getattr(phase_store, "run_contract", None)
    if (
        intake_raw != canonical_json_bytes(intake)
        or set(intake) != _REQUEST_INTAKE_AUTHORITY_FIELDS
        or intake.get("schema_id")
        != "crossframe.ultra.v82.request-intake-authority"
        or intake.get("schema_version") != 1
        or intake.get("run_id") != layout.run_dir.name
        or intake.get("version_binding") != current_version_binding()
        or intake.get("content_sha256")
        != compute_artifact_content_sha256(intake)
        or not isinstance(request_sha256, str)
        or not isinstance(run_contract, Mapping)
        or run_contract.get("request_sha256") != request_sha256
    ):
        raise ValueError("semantic review request intake authority differs")
    required_concept_units = semantic_review.validate_required_concept_units(
        documents["concept_disposition"],
        required_concept_semantic_unit_ids,
    )
    u10_event = _completed_phase_event(phase_store, "U10")
    if u10_event is None:
        raise ValueError("semantic review requires the active U10 parent event")
    action = semantic_review.ensure_semantic_review_action(
        layout,
        request_sha256=request_sha256,
        request_intake_authority_sha256=sha256_bytes(intake_raw),
        u10_parent_event_sha256=_event_sha256(u10_event),
        active_generation=active_generation,
        article_sha256=assembled.article_sha256,
        output_plan_artifact_sha256=_full_artifact_sha256(
            documents["output_plan"]
        ),
        coverage_artifact_sha256=_full_artifact_sha256(coverage_document),
        article_review_artifact_sha256=_full_artifact_sha256(built_review),
        evidence_ledger_artifact_sha256=_full_artifact_sha256(
            documents["evidence"]
        ),
        concept_disposition_artifact_sha256=_full_artifact_sha256(
            documents["concept_disposition"]
        ),
        required_concept_semantic_unit_ids=required_concept_units,
        now=now,
    )
    accepted = semantic_review.load_accepted_semantic_review_result(
        layout,
        action,
    )
    if accepted is None:
        if u11_event is not None:
            raise ValueError(
                "completed U11 has no accepted semantic review receipt"
            )
        return action
    host_result = semantic_review.load_host_semantic_review_result(
        layout,
        action,
    )
    semantic_document = semantic_review.project_semantic_review_artifact(
        action=action,
        accepted_result=accepted,
        host_result=host_result,
        version_binding=current_version_binding(),
        generated_at=_canonical_utc(u11_generated_at),
        deterministic_status="pass",
        adversarial_status="pass",
    )
    if (
        semantic_document.get("overall_status") != "pass"
        or semantic_document.get("publication_allowed") is not True
    ):
        raise ValueError("fresh semantic review does not allow publication")
    semantic_destination = assert_safe_descendant(
        layout.root,
        layout.artifacts_dir
        / "U09-U10-verdict"
        / "U11-semantic-review.json",
    )
    if semantic_destination.exists():
        try:
            existing_raw = semantic_destination.read_bytes()
            existing_semantic = load_json_object_bytes(
                existing_raw,
                source=str(semantic_destination),
            )
        except (OSError, TypeError, ValueError) as error:
            raise ValueError("runtime semantic review artifact is unreadable") from error
        if (
            existing_raw != canonical_json_bytes(existing_semantic)
            or existing_semantic != semantic_document
        ):
            raise ValueError("runtime semantic review artifact authority differs")
    else:
        atomic_write_json(semantic_destination, semantic_document)
    documents["semantic_review"] = semantic_document

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
        semantic_destination,
        partial_path,
        dossier_path,
        artifact_index_path,
    )
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
        (
            coverage_destination,
            review_destination,
            semantic_destination,
            artifact_index_path,
        )
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
class CompleteMaterializationResult(MaterializationProgress):
    manifest_path: Path
    article_path: Path
    dossier_path: Path
    artifact_index_path: Path
    final_chat_path: Path
    postcheck_passed: bool


@dataclass(frozen=True, slots=True)
class RepairMaterializationResult:
    run_id: str
    status: str
    outcome: str
    repair_attempt_id: str
    reopened_phase: str
    active_generation: int
    next_action: Mapping[str, str]


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


def preflight_foundation_progress(
    layout: RunLayout,
    status_store: object,
    *,
    now: datetime,
    lease: object | None = None,
) -> object:
    """Validate immutable foundation state before any progress side effect."""

    _validate_layout(layout)
    _require_utc(now, "now")
    current = status_store.read()
    if current.status not in {"created", "running"}:
        raise FoundationInputError(
            f"foundation status boundary is {current.status!r}, not created or running"
        )
    _foundation_input_inventory(layout, status_record=current)
    checkpoints_dir = layout.recovery_dir / "checkpoints"
    checkpoints_exist = checkpoints_dir.is_dir() and any(
        path.is_file() for path in checkpoints_dir.glob("*.json")
    )
    if not checkpoints_exist and (
        current.current_phase != "U0" or current.last_complete_phase is not None
    ):
        raise FoundationInputError(
            "fresh foundation status boundary must be created or running/U0 "
            "with no completed phase"
        )
    if checkpoints_exist and current.current_phase != "U0":
        from . import recovery

        checkpoint = recovery.select_resume_checkpoint(layout)
        expected_phase = str(checkpoint["phase_id"])
        expected_last_complete = (
            "U10"
            if checkpoint.get("boundary_kind") == "article-packet"
            else expected_phase
        )
        current_phase_ahead = PHASES.index(current.current_phase) > PHASES.index(
            expected_phase
        )
        last_complete_ahead = (
            current.last_complete_phase is not None
            and PHASES.index(current.last_complete_phase)
            > PHASES.index(expected_last_complete)
        )
        if current_phase_ahead or last_complete_ahead:
            raise FoundationInputError(
                "run status boundary is ahead of the durable checkpoint"
            )
    if current.status == "created":
        current = status_store.transition(
            current,
            "running",
            now,
            current_phase=current.current_phase,
            last_complete_phase=current.last_complete_phase,
            reason="runtime progress admitted",
            validation_passed=False,
            lease=lease,
        )
    return current


def _request_intake_authority_path(layout: RunLayout) -> Path:
    path = layout.run_dir / REQUEST_INTAKE_AUTHORITY_RELATIVE_PATH
    assert_safe_descendant(layout.root, path)
    return path


def seal_request_intake_authority(
    layout: RunLayout,
    *,
    request_sha256: str,
    request_size: int,
    created_at: str,
) -> dict[str, object]:
    if (
        not isinstance(request_sha256, str)
        or len(request_sha256) != 64
        or any(character not in "0123456789abcdef" for character in request_sha256)
    ):
        raise ValueError("request intake SHA-256 is invalid")
    if not isinstance(request_size, int) or isinstance(request_size, bool) or request_size < 0:
        raise ValueError("request intake size is invalid")
    if not isinstance(created_at, str) or not created_at.endswith("Z"):
        raise ValueError("request intake time is not canonical UTC")
    authority: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.request-intake-authority",
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "version_binding": current_version_binding(),
        "generated_at": created_at,
        "request_sha256": request_sha256,
        "request_size": request_size,
        "content_sha256": "0" * 64,
    }
    authority["content_sha256"] = compute_artifact_content_sha256(authority)
    path = _request_intake_authority_path(layout)
    if path.exists():
        raise FileExistsError("request intake authority already exists")
    atomic_write_json(path, authority)
    return copy.deepcopy(authority)


def _validated_request_intake_authority(
    layout: RunLayout,
    *,
    status_record: object,
) -> dict[str, object]:
    path = _request_intake_authority_path(layout)
    try:
        raw = path.read_bytes()
        authority = load_json_object_bytes(raw, source=str(path))
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError(
            "request intake authority is absent or unreadable"
        ) from error
    if (
        raw != canonical_json_bytes(authority)
        or set(authority) != _REQUEST_INTAKE_AUTHORITY_FIELDS
        or authority.get("schema_id")
        != "crossframe.ultra.v82.request-intake-authority"
        or authority.get("schema_version") != 1
        or authority.get("run_id") != layout.run_dir.name
        or authority.get("version_binding") != current_version_binding()
        or authority.get("generated_at") != getattr(status_record, "created_at", None)
        or authority.get("content_sha256")
        != compute_artifact_content_sha256(authority)
    ):
        raise FoundationInputError("request intake authority is invalid")
    request_sha256 = authority.get("request_sha256")
    request_size = authority.get("request_size")
    if (
        not isinstance(request_sha256, str)
        or len(request_sha256) != 64
        or any(character not in "0123456789abcdef" for character in request_sha256)
        or not isinstance(request_size, int)
        or isinstance(request_size, bool)
        or request_size < 0
    ):
        raise FoundationInputError("request intake authority payload is invalid")
    return authority


def _foundation_input_inventory(
    layout: RunLayout,
    *,
    status_record: object,
) -> tuple[bytes, dict[str, object], tuple[dict[str, str], ...], str]:
    request_path = layout.input_dir / "request.bin"
    metadata_path = layout.input_dir / "request-metadata.json"
    try:
        for path in (request_path, metadata_path):
            assert_safe_descendant(layout.root, path)
            if not path.is_file():
                raise FoundationInputError(
                    f"fresh foundation input is absent: {path.name}"
                )
        request_bytes = request_path.read_bytes()
        request_sha256 = sha256_bytes(request_bytes)
        metadata_raw = metadata_path.read_bytes()
        metadata = load_json_object_bytes(metadata_raw, source=str(metadata_path))
    except FoundationInputError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise FoundationInputError(
            "fresh foundation request metadata is unreadable"
        ) from error
    if (
        set(metadata) != {"request_sha256", "request_size"}
        or metadata.get("request_sha256") != request_sha256
        or metadata.get("request_size") != len(request_bytes)
        or metadata_raw != canonical_json_bytes(metadata)
    ):
        raise FoundationInputError(
            "request metadata differs from the immutable request bytes"
        )
    intake = _validated_request_intake_authority(
        layout,
        status_record=status_record,
    )
    if (
        intake["request_sha256"] != request_sha256
        or intake["request_size"] != len(request_bytes)
    ):
        raise FoundationInputError(
            "request intake authority differs from the current input bytes"
        )
    load_input_inventory(layout)

    try:
        files = tuple(
            sorted(
                (path for path in layout.input_dir.rglob("*") if path.is_file()),
                key=lambda path: path.relative_to(layout.input_dir).as_posix(),
            )
        )
    except OSError as error:
        raise FoundationInputError(
            "fresh foundation input inventory is unreadable"
        ) from error
    inputs = tuple(
        {
            "path": path.relative_to(layout.input_dir).as_posix(),
            "sha256": _sha256_file(path),
            "media_type": (
                "application/json"
                if path.suffix.casefold() == ".json"
                else "text/markdown"
                if path.suffix.casefold() in {".md", ".markdown"}
                else "text/plain"
                if path.suffix.casefold() == ".txt"
                else "application/octet-stream"
            ),
        }
        for path in files
    )
    input_snapshot_sha256 = sha256_bytes(canonical_json_bytes(inputs))
    return request_bytes, metadata, inputs, input_snapshot_sha256


def _assert_no_uncheckpointed_foundation_residuals(
    layout: RunLayout,
    current_phase: str,
) -> None:
    phase_paths = {
        "U1": (
            layout.recovery_dir / "u1-authority/source-lock.json",
            layout.recovery_dir / "u1-authority/read-plan.json",
            layout.recovery_dir / "u1-authority/source-coverage.json",
            layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl",
        ),
        "U2": (
            layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json",
        ),
        "U3": (
            layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json",
        ),
    }
    start = PHASES.index(current_phase) + 1
    residuals = [
        path
        for phase_id in PHASES[start:4]
        for path in phase_paths[phase_id]
        if path.exists()
    ]
    residuals.extend(
        path
        for path in (
            layout.authoring_dir / "U01-read-events.jsonl",
            layout.authoring_dir / "U02-retrieval-ledger.json",
            layout.authoring_dir / "U03-evidence-ledger.json",
        )
        if path.exists()
    )
    if residuals:
        relative = sorted(
            path.relative_to(layout.run_dir).as_posix() for path in residuals
        )
        raise FoundationRecoveryError(
            "partial foundation contains uncheckpointed downstream state: "
            + ", ".join(relative)
        )


def _u1_coverage_artifact(
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    parent_event_sha256: str,
    source_lock_sha256: str,
    receipts: Sequence[object],
    events: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "artifact_type": "crossframe.ultra.v82.u1-source-coverage",
        "run_id": run_id,
        "version_binding": copy.deepcopy(dict(version_binding)),
        "parent_event_sha256": parent_event_sha256,
        "source_lock_sha256": source_lock_sha256,
        "receipt_sha256s": [
            str(getattr(receipt, "receipt_sha256")) for receipt in receipts
        ],
        "read_event_sha256s": [
            str(event["read_event_sha256"]) for event in events
        ],
    }


def _create_phase_checkpoint(
    recovery: object,
    layout: RunLayout,
    phase_store: object,
    phase_id: str,
    artifact_paths: Sequence[Path],
    *,
    now: datetime,
    lease: object,
) -> object:
    create_checkpoint = getattr(recovery, "create_checkpoint", None)
    if not callable(create_checkpoint):
        raise RuntimeError("recovery checkpoint producer is unavailable")
    return create_checkpoint(
        layout,
        phase_store,
        boundary_kind="phase",
        boundary_id=phase_id,
        boundary_ordinal=0,
        artifact_paths=tuple(artifact_paths),
        now=now,
        lease=lease,
    )


@dataclass(frozen=True, slots=True)
class _FoundationContext:
    analysis_kind: str
    claim: str
    material: str
    material_inventory: tuple[dict[str, str], ...]
    material_universe_sha256: str | None
    request_sha256: str
    evidence_cutoff: str
    inputs: tuple[dict[str, str], ...]
    input_snapshot_sha256: str
    binding: dict[str, object]
    timestamp: str
    manifest: object | None
    measurement: object | None


def _load_foundation_context(
    repo: Path,
    layout: RunLayout,
    mode: RunMode,
    *,
    now: datetime,
    status_record: object,
    require_u1_measurement: bool,
) -> _FoundationContext:
    from . import source_integrity

    _request_bytes, metadata, inputs, input_snapshot_sha256 = (
        _foundation_input_inventory(layout, status_record=status_record)
    )
    profile = load_request_profile(layout)
    material_texts: list[str] = []
    for item in profile.material_inventory:
        if item["media_type"] not in {"text/plain", "text/markdown"}:
            continue
        try:
            material_texts.append(
                (layout.input_dir / item["path"]).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError) as error:
            raise FoundationInputError(
                "text material inventory entry is unreadable"
            ) from error
    material = "\n\n".join(material_texts)
    evidence_cutoff = getattr(status_record, "created_at", None)
    if not isinstance(evidence_cutoff, str) or not evidence_cutoff:
        raise FoundationInputError(
            "run status does not expose the immutable creation time"
        )
    manifest = None
    measurement = None
    if require_u1_measurement:
        manifest = source_integrity.load_source_manifest(
            repo / "skills/crossframe-ultra/references/source-manifest.json"
        )
        measurement_arguments: dict[str, object] = {
            "manifest": manifest,
            "run_mode": mode.value,
        }
        if mode is RunMode.TEST:
            measurement_arguments["release_manifest_path"] = (
                repo / "skills/crossframe-ultra/references/release-manifest.json"
            )
        measurement = source_integrity.measure_u1_prerequisites(
            repo,
            **measurement_arguments,
        )
        if not measurement.ready:
            raise RuntimeError(
                "U1 prerequisites are not ready: "
                + ", ".join(measurement.missing)
            )
    return _FoundationContext(
        analysis_kind=profile.analysis_kind,
        claim=profile.claim,
        material=material,
        material_inventory=profile.material_inventory,
        material_universe_sha256=profile.material_universe_sha256,
        request_sha256=str(metadata["request_sha256"]),
        evidence_cutoff=evidence_cutoff,
        inputs=inputs,
        input_snapshot_sha256=input_snapshot_sha256,
        binding=current_version_binding(),
        timestamp=_canonical_utc(now),
        manifest=manifest,
        measurement=measurement,
    )


def _complete_foundation_u1(
    repo: Path,
    layout: RunLayout,
    phase_store: object,
    context: _FoundationContext,
    *,
    now: datetime,
    recovery: object,
    lease: object,
) -> None:
    from . import source_integrity

    manifest = context.manifest
    measurement = context.measurement
    if manifest is None or measurement is None:
        raise FoundationRecoveryError("U0 recovery lacks fresh U1 prerequisites")
    u0_event = phase_store.events[-1]
    if u0_event.get("phase_id") != "U0":
        raise FoundationRecoveryError("U1 continuation does not follow U0")
    u0_event_sha256 = _event_sha256(u0_event)
    source_lock = source_integrity.build_source_lock(
        run_id=phase_store.run_id,
        version_binding=context.binding,
        generated_at=context.timestamp,
        prerequisite_measurement=measurement,
        parent_event_sha256=u0_event_sha256,
        evidence_cutoff=context.evidence_cutoff,
        run_layout=layout,
        inputs=context.inputs,
    )
    source_lock_seal = source_integrity.validate_source_lock(
        source_lock,
        prerequisite_measurement=measurement,
        expected_run_id=phase_store.run_id,
        expected_version_binding=context.binding,
        expected_parent_event_sha256=u0_event_sha256,
        expected_evidence_cutoff=context.evidence_cutoff,
        expected_inputs=context.inputs,
        run_layout=layout,
    )
    read_plan = source_integrity.build_read_plan(
        manifest,
        promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
        source_manifest_sha256=manifest.sha256,
        source_lock_sha256=source_lock_seal.artifact_sha256,
        parent_event_sha256=u0_event_sha256,
    )
    read_session = source_integrity.open_source_read_session(
        repo,
        manifest=manifest,
        run_id=phase_store.run_id,
        version_binding=context.binding,
        source_lock_sha256=source_lock_seal.artifact_sha256,
        parent_event_sha256=u0_event_sha256,
        reader_mode="full-source",
        read_at=context.timestamp,
    )
    receipts = []
    for source_unit_id in read_plan["source_unit_ids"]:
        _record, receipt = source_integrity.capture_source_unit_read(
            read_session,
            str(source_unit_id),
        )
        receipts.append(receipt)
    read_events = tuple(
        source_integrity.make_read_event(
            run_id=phase_store.run_id,
            version_binding=context.binding,
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
            source_manifest_sha256=manifest.sha256,
            source_lock_sha256=source_lock_seal.artifact_sha256,
            parent_event_sha256=u0_event_sha256,
            receipt=receipt,
        )
        for receipt in receipts
    )
    read_audit = source_integrity.audit_read_capture(
        read_events,
        manifest,
        receipts=tuple(receipts),
        promoted_semantic_snapshot_sha256=manifest.semantic_sha256,
        expected_run_id=phase_store.run_id,
        expected_version_binding=context.binding,
        expected_source_lock_sha256=source_lock_seal.artifact_sha256,
        expected_parent_event_sha256=u0_event_sha256,
    )
    u1_authority = source_integrity.validate_u1_authority(
        source_lock_seal,
        read_audit,
    )
    source_lock_path = layout.recovery_dir / "u1-authority/source-lock.json"
    source_coverage_path = layout.recovery_dir / "u1-authority/source-coverage.json"
    read_events_path = (
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl"
    )
    atomic_write_json(source_lock_path, source_lock)
    source_coverage = _u1_coverage_artifact(
        run_id=phase_store.run_id,
        version_binding=context.binding,
        parent_event_sha256=u0_event_sha256,
        source_lock_sha256=source_lock_seal.artifact_sha256,
        receipts=tuple(receipts),
        events=read_events,
    )
    atomic_write_json(source_coverage_path, source_coverage)
    if _sha256_file(source_coverage_path) != read_audit.artifact_sha256:
        raise RuntimeError("persisted U1 source coverage differs from its authority")
    atomic_write_bytes(
        read_events_path,
        b"".join(canonical_json_bytes(event) for event in read_events),
    )
    phase_store.complete(
        "U1",
        artifact_hashes=(
            u1_authority.source_lock_artifact_sha256,
            u1_authority.read_coverage_artifact_sha256,
        ),
        u1_authority=u1_authority,
    )
    _create_phase_checkpoint(
        recovery,
        layout,
        phase_store,
        "U1",
        (source_lock_path, source_coverage_path),
        now=now,
        lease=lease,
    )


def _complete_foundation_u2(
    layout: RunLayout,
    phase_store: object,
    context: _FoundationContext,
    *,
    now: datetime,
    recovery: object,
    lease: object,
) -> None:
    from . import retrieval

    decision = retrieval.assess_retrieval_eligibility(
        context.claim,
        phase_store=phase_store,
        material_inventory=context.material_inventory,
        material_universe_sha256=context.material_universe_sha256,
    )
    retrieval_ledger = retrieval.build_retrieval_ledger(
        decision,
        generated_at=context.timestamp,
        phase_store=phase_store,
    )
    retrieval_seal = retrieval.validate_retrieval_ledger(
        retrieval_ledger,
        phase_store=phase_store,
        expected_run_id=phase_store.run_id,
        expected_version_binding=context.binding,
        expected_phase_id="U2",
        expected_u1_parent_event_sha256=_event_sha256(phase_store.events[-1]),
        expected_request_sha256=context.request_sha256,
        expected_decision_sha256=decision.decision_sha256,
        expected_authorization_sha256=None,
    )
    retrieval_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    atomic_write_json(retrieval_path, retrieval_ledger)
    phase_store.complete(
        "U2",
        artifact_hashes=(retrieval_seal.artifact_sha256,),
        retrieval_authority=retrieval_seal,
    )
    _create_phase_checkpoint(
        recovery,
        layout,
        phase_store,
        "U2",
        (retrieval_path,),
        now=now,
        lease=lease,
    )


def _complete_foundation_u3(
    layout: RunLayout,
    phase_store: object,
    context: _FoundationContext,
    *,
    now: datetime,
    recovery: object,
    lease: object,
) -> None:
    from . import evidence

    request_source_id = "REQUEST-" + context.request_sha256[:24].upper()
    phase_store.append_evidence(
        {
            "evidence_id": "EVIDENCE-" + context.request_sha256[:24].upper(),
            "identity": "user-claim",
            "statement": f"{context.claim}\n\n{context.material}",
            "source_refs": [request_source_id],
            "observed_at": None,
            "confidence": "unknown",
            "event_date": context.evidence_cutoff[:10],
            "publication_date": context.evidence_cutoff[:10],
            "interest": "The sealed request is user-supplied material.",
            "upstream_lineage": [request_source_id],
            "supported_claim": context.claim,
            "cannot_prove": (
                "The supplied claim and material do not independently prove a real-world fact."
            ),
        }
    )
    evidence_artifact = phase_store.evidence_artifact
    evidence_seal = evidence.validate_evidence_artifact(
        evidence_artifact,
        expected_run_id=phase_store.run_id,
        expected_version_binding=context.binding,
        expected_phase_id="U3",
        expected_evidence_cutoff=context.evidence_cutoff,
    )
    evidence_path = (
        layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
    )
    atomic_write_json(evidence_path, evidence_artifact)
    phase_store.complete(
        "U3",
        artifact_hashes=(evidence_seal.artifact_sha256,),
        evidence_authority=evidence_seal,
    )
    _create_phase_checkpoint(
        recovery,
        layout,
        phase_store,
        "U3",
        (evidence_path,),
        now=now,
        lease=lease,
    )


def _continue_foundation_u0_u3(
    repo: Path,
    layout: RunLayout,
    mode: RunMode,
    phase_store: object,
    context: _FoundationContext,
    *,
    now: datetime,
    recovery: object,
    lease: object,
) -> object:
    current_phase = getattr(phase_store, "current_phase", None)
    if current_phase not in {"U0", "U1", "U2"}:
        raise FoundationRecoveryError(
            "partial foundation checkpoint does not end at U0, U1, or U2"
        )
    run_contract = getattr(phase_store, "run_contract", None)
    if (
        getattr(phase_store, "run_id", None) != layout.run_dir.name
        or getattr(phase_store, "evidence_cutoff", None) != context.evidence_cutoff
        or not isinstance(run_contract, Mapping)
        or run_contract.get("request_sha256") != context.request_sha256
        or run_contract.get("run_mode") != mode.value
    ):
        raise FoundationRecoveryError(
            "partial foundation authority differs from the frozen request"
        )
    _assert_no_uncheckpointed_foundation_residuals(layout, current_phase)
    if current_phase == "U0":
        _complete_foundation_u1(
            repo,
            layout,
            phase_store,
            context,
            now=now,
            recovery=recovery,
            lease=lease,
        )
        current_phase = "U1"
    if current_phase == "U1":
        _assert_no_uncheckpointed_foundation_residuals(layout, current_phase)
        _complete_foundation_u2(
            layout,
            phase_store,
            context,
            now=now,
            recovery=recovery,
            lease=lease,
        )
        current_phase = "U2"
    if current_phase == "U2":
        _assert_no_uncheckpointed_foundation_residuals(layout, current_phase)
        _complete_foundation_u3(
            layout,
            phase_store,
            context,
            now=now,
            recovery=recovery,
            lease=lease,
        )
    return phase_store


def _establish_fresh_u0_u3(
    repo: Path,
    layout: RunLayout,
    mode: RunMode,
    *,
    now: datetime,
    recovery: object,
    status_record: object,
    lease: object,
) -> object:
    from .foundation import advance_u0

    if (
        getattr(status_record, "status", None) != "running"
        or getattr(status_record, "current_phase", None) != "U0"
        or getattr(status_record, "last_complete_phase", None) is not None
    ):
        raise FoundationInputError(
            "fresh foundation status boundary must be running/U0 with no completed phase"
        )
    progress = advance_u0(layout, repo=repo, now=now, lease=lease)
    if progress.outcome == "awaiting-host-action":
        raise FoundationRecoveryError(
            "fresh U0 is awaiting a capability-attestation host action"
        )
    phase_store = progress.phase_store
    if (
        progress.outcome != "advanced"
        or progress.completed_phase != "U0"
        or phase_store is None
    ):
        raise FoundationRecoveryError("fresh U0 did not produce a PhaseStore")
    context = _load_foundation_context(
        repo,
        layout,
        mode,
        now=now,
        status_record=status_record,
        require_u1_measurement=True,
    )
    manifest = context.manifest
    measurement = context.measurement
    if manifest is None or measurement is None:
        raise RuntimeError("fresh foundation U1 prerequisites are unavailable")
    return _continue_foundation_u0_u3(
        repo,
        layout,
        mode,
        phase_store,
        context,
        now=now,
        recovery=recovery,
        lease=lease,
    )


def _resume_or_establish_u0_u3(
    repo: Path,
    layout: RunLayout,
    mode: RunMode,
    *,
    now: datetime,
    recovery: object,
    status_record: object,
    lease: object,
) -> object:
    resume_run = getattr(recovery, "resume_run", None)
    error_type = getattr(recovery, "RecoveryStateError", None)
    if not callable(resume_run) or not isinstance(error_type, type):
        raise RuntimeError("recovery foundation APIs are unavailable")
    try:
        resumed = resume_run(
            layout,
            now=now,
            source_repository=repo.resolve(),
            lease=lease,
        )
    except error_type as error:
        if str(error) != "no completed resumable checkpoint is available":
            raise
        return _establish_fresh_u0_u3(
            repo,
            layout,
            mode,
            now=now,
            recovery=recovery,
            status_record=status_record,
            lease=lease,
        )
    phase_store = _resume_phase_store(resumed)
    current_phase = getattr(phase_store, "current_phase", None)
    if current_phase in {"U0", "U1", "U2"}:
        context = _load_foundation_context(
            repo,
            layout,
            mode,
            now=now,
            status_record=status_record,
            require_u1_measurement=current_phase == "U0",
        )
        return _continue_foundation_u0_u3(
            repo,
            layout,
            mode,
            phase_store,
            context,
            now=now,
            recovery=recovery,
            lease=lease,
        )
    if current_phase not in PHASES[3:]:
        raise FoundationRecoveryError("durable foundation phase is invalid")
    return phase_store


def _validator_set_authority(repo: Path, validation: object) -> str:
    authority = getattr(validation, "validator_set_sha256", None)
    if not callable(authority):
        raise RuntimeError("Task 12 does not expose its validator-set hash authority")
    value = authority(repo)
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise RuntimeError("Task 12 returned an invalid validator-set hash")
    return value


def _apply_pending_validation_repair(
    layout: RunLayout,
    *,
    now: datetime,
    lease: object,
) -> RepairMaterializationResult | None:
    _require_utc(now, "now")
    report_path = layout.validation_current_dir / "ultra-validator-report.json"
    if not report_path.is_file():
        return None
    report = load_json_object(report_path)
    if report.get("overall_status") != "fail":
        return None
    from . import repair

    attempt_id, attempt_number = repair.current_attempt_identity(layout, now=now)
    attempt_root = repair._repair_attempt_root(layout, attempt_id)
    application_path = attempt_root / "repair-application.json"
    if application_path.is_file():
        committed_plan = load_json_object(
            layout.validation_current_dir / "ultra-repair-plan.json"
        )
        repair.apply_repair_plan(
            layout,
            plan=committed_plan,
            now=now,
            lease=lease,
        )
        return None
    plan = repair.build_repair_plan(
        layout,
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        now=now,
        lease=lease,
    )
    committed = repair.commit_repair_plan(
        layout,
        attempt_id=attempt_id,
        plan=plan,
        lease=lease,
    )
    if committed.get("status") != "planned":
        return RepairMaterializationResult(
            run_id=layout.run_dir.name,
            status="needs_attention",
            outcome="repair-needs-attention",
            repair_attempt_id=attempt_id,
            reopened_phase=str(committed["reset_from_phase"]),
            active_generation=0,
            next_action={
                "phase_id": "U12",
                "relative_path": "operator-review",
            },
        )
    application = repair.apply_repair_plan(
        layout,
        plan=committed,
        now=now,
        lease=lease,
    )
    next_action = application.get("next_action")
    if not isinstance(next_action, Mapping) or any(
        not isinstance(next_action.get(field), str)
        for field in ("phase_id", "relative_path")
    ):
        raise RuntimeError("repair application next action is invalid")
    return RepairMaterializationResult(
        run_id=layout.run_dir.name,
        status="running",
        outcome="repair-applied",
        repair_attempt_id=attempt_id,
        reopened_phase=str(application["reopened_phase"]),
        active_generation=int(application["active_generation"]),
        next_action={
            "phase_id": str(next_action["phase_id"]),
            "relative_path": str(next_action["relative_path"]),
        },
    )


def _close_u12_transaction(
    layout: RunLayout,
    phase_store: object,
    publication: object,
    *,
    recovery: object,
    status_store: object,
    now: datetime,
    mark_needs_attention: Callable[[str], object],
    lease: object,
) -> tuple[dict[str, object], object, Path]:
    from .deliverables import (
        _mark_u12_durable,
        _roll_forward_u12_transaction,
        recover_publish_transaction,
    )

    paths = getattr(publication, "paths", None)
    if paths is None:
        raise TypeError("publication must expose its fixed publication paths")
    report_path = layout.validation_current_dir / "ultra-validator-report.json"
    durable = False
    try:
        event = complete_u12(
            layout,
            phase_store,
            manifest_path=paths.manifest_path,
            postcheck_report_path=report_path,
            delivery_paths=(
                paths.article_path,
                paths.dossier_path,
                paths.artifact_index_path,
            ),
            postcheck_passed=getattr(publication, "postcheck_passed", False),
        )
        checkpoint = recovery.create_checkpoint(
            layout,
            phase_store,
            boundary_kind="phase",
            boundary_id="U12",
            boundary_ordinal=0,
            artifact_paths=(
                paths.manifest_path,
                report_path,
                paths.article_path,
                paths.dossier_path,
                paths.artifact_index_path,
            ),
            now=now,
            lease=lease,
        )
        durable = True
        _mark_u12_durable(
            layout,
            paths,
            event=event,
            checkpoint=checkpoint,
        )

        journal = load_json_object(paths.journal_path)
        completed_journal = _roll_forward_u12_transaction(
            layout,
            paths,
            journal,
            lease=lease,
        )
        if completed_journal.get("state") != "complete":
            raise RuntimeError("U12 publish journal did not complete")
        reread_status = status_store.read()
        if (
            reread_status.status != "complete"
            or reread_status.current_phase != "U12"
            or reread_status.last_complete_phase != "U12"
            or reread_status.validation_passed is not True
            or reread_status.tools_allowed is not False
        ):
            raise RuntimeError("U12 terminal status authority is inconsistent")

        event_path = layout.recovery_dir / "phase-events.jsonl"
        try:
            raw_events = event_path.read_bytes()
        except OSError as error:
            raise RuntimeError("U12 phase event journal cannot be read") from error
        if not raw_events or not raw_events.endswith(b"\n"):
            raise RuntimeError("U12 phase event journal is incomplete")
        disk_events = []
        for ordinal, row in enumerate(raw_events.splitlines(keepends=True), start=1):
            parsed = load_json_object_bytes(
                row,
                source=f"{event_path}:{ordinal}",
            )
            if row != canonical_json_bytes(parsed):
                raise RuntimeError("U12 phase event journal is not canonical")
            disk_events.append(parsed)
        u12_events = [
            item
            for item in disk_events
            if item.get("phase_id") == "U12" and item.get("status") == "complete"
        ]

        checkpoints = recovery.load_checkpoints(layout)
        u12_checkpoints = [
            item
            for item in checkpoints
            if item.get("boundary_kind") == "phase"
            and item.get("phase_id") == "U12"
        ]
        ordered_paths = (
            paths.manifest_path,
            report_path,
            paths.article_path,
            paths.dossier_path,
            paths.artifact_index_path,
        )
        ordered_hashes = tuple(_sha256_file(path) for path in ordered_paths)
        expected_refs = tuple(
            (path.relative_to(layout.run_dir).as_posix(), digest)
            for path, digest in zip(ordered_paths, ordered_hashes)
        )
        raw_refs = checkpoint.get("artifact_hashes")
        observed_refs = (
            tuple(
                (str(item.get("path")), str(item.get("sha256")))
                for item in raw_refs
                if isinstance(item, Mapping)
            )
            if isinstance(raw_refs, list)
            else ()
        )
        if (
            u12_events != [event]
            or u12_checkpoints != [checkpoint]
            or tuple(event.get("output_artifact_hashes", ())) != ordered_hashes
            or observed_refs != expected_refs
            or checkpoint.get("phase_event_sha256") != event.get("event_sha256")
        ):
            raise RuntimeError(
                "U12 disk event and checkpoint do not bind the ordered completion files"
            )
        return event, reread_status, layout.run_dir / "final-chat.json"
    except BaseException as error:
        if durable:
            try:
                current = status_store.read()
                if current.status not in {"complete", "needs_attention"}:
                    mark_needs_attention(
                        "durable U12 transaction requires roll-forward: "
                        f"{type(error).__name__}: {error}"
                    )
            except BaseException as attention_error:
                add_note = getattr(error, "add_note", None)
                if callable(add_note):
                    add_note(
                        "failed to hold durable U12 as needs_attention: "
                        f"{attention_error}"
                    )
        else:
            try:
                recover_publish_transaction(
                    layout,
                    mark_needs_attention=mark_needs_attention,
                    lease=lease,
                )
            except BaseException as rollback_error:
                add_note = getattr(error, "add_note", None)
                if callable(add_note):
                    add_note(f"failed to roll back pre-U12 publication: {rollback_error}")
        raise


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
) -> CompleteMaterializationResult | MaterializationProgress | RepairMaterializationResult:
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
        publish_delivery,
        publication_paths,
        recover_publish_transaction,
    )
    from .locks import (
        CancelledRunError,
        LeaseNeedsAttentionError,
        acquire_run_lease,
        release_run_lease,
    )
    from .status import RunStatusStore

    status_store = RunStatusStore(layout)
    lease = None
    attention_marked = False
    phase_store_restored = False
    publication_journal_path = layout.recovery_dir / "publish-transaction.json"

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
            lease=lease,
        )
        attention_marked = True
        return changed

    def stop_if_cancel_requested() -> None:
        if lease is None:
            return
        converge = getattr(recovery, "converge_cancel_if_requested", None)
        if not callable(converge):
            raise RuntimeError("cancel convergence API is unavailable")
        if converge(layout, lease=lease, now=now) is not None:
            raise CancelledRunError(
                "cancel intent converged before materialization commit"
            )

    try:
        try:
            lease = acquire_run_lease(layout, now, timedelta(minutes=30))
        except LeaseNeedsAttentionError as error:
            input_drift_error = getattr(recovery, "_RecoveryInputDriftError", None)
            if (
                not isinstance(input_drift_error, type)
                or not isinstance(error.__cause__, input_drift_error)
                or not _request_intake_authority_path(layout).is_file()
            ):
                raise
            current = status_store.read()
            checkpoints_dir = layout.recovery_dir / "checkpoints"
            if not checkpoints_dir.is_dir() or not any(
                path.is_file() for path in checkpoints_dir.glob("*.json")
            ):
                raise
            _foundation_input_inventory(layout, status_record=current)
            raise
        stop_if_cancel_requested()
        current = status_store.read()
        repair_result = _apply_pending_validation_repair(
            layout,
            now=now,
            lease=lease,
        )
        if repair_result is not None:
            return repair_result
        current = status_store.read()
        checkpoints_dir = layout.recovery_dir / "checkpoints"
        if current.status != "complete":
            current = preflight_foundation_progress(
                layout,
                status_store,
                now=now,
                lease=lease,
            )
        elif checkpoints_dir.is_dir() and any(
            path.is_file() for path in checkpoints_dir.glob("*.json")
        ):
            _foundation_input_inventory(layout, status_record=current)
        if current.status == "complete":
            recovered_publication = recover_publish_transaction(
                layout,
                mark_needs_attention=mark_needs_attention,
                lease=lease,
            )
            if not isinstance(
                recovered_publication, Mapping
            ) or recovered_publication.get("state") != "complete":
                raise RuntimeError("terminal complete run has no complete publish journal")
            paths = publication_paths(
                layout,
                str(recovered_publication["transaction_id"]),
            )
            return CompleteMaterializationResult(
                outcome="complete",
                run_id=run_id,
                status="complete",
                current_phase="U12",
                last_complete_phase="U12",
                next_action=None,
                final_chat=(
                    load_json_object(layout.run_dir / "final-chat.json")
                    if (layout.run_dir / "final-chat.json").is_file()
                    else None
                ),
                manifest_path=paths.manifest_path,
                article_path=paths.article_path,
                dossier_path=paths.dossier_path,
                artifact_index_path=paths.artifact_index_path,
                final_chat_path=layout.run_dir / "final-chat.json",
                postcheck_passed=True,
            )

        from .foundation import advance_foundation

        foundation = advance_foundation(
            layout,
            repo=repo.resolve(),
            now=now,
            lease=lease,
        )
        projected = foundation_progress_projection(layout, foundation)
        if projected.outcome in {"awaiting-host-action", "awaiting-authoring", "blocked"}:
            return projected
        phase_store = getattr(foundation, "phase_store", None)
        if phase_store is None or getattr(phase_store, "current_phase", None) not in {
            "U3",
            "U4",
            "U5",
            "U6",
            "U7",
            "U8",
            "U9",
            "U10",
            "U11",
        }:
            raise FoundationRecoveryError("foundation coordinator did not seal U3")
        phase_store_restored = True
        current = status_store.read()
        _foundation_input_inventory(layout, status_record=current)
        prepare_authoring(layout)
        if current.status != "running":
            raise RuntimeError(
                f"resumed run status {current.status!r} cannot materialize"
            )

        def create_owned_checkpoint(*args: Any, **kwargs: Any) -> object:
            checkpoint = recovery.create_checkpoint(*args, **kwargs, lease=lease)
            if (
                kwargs.get("boundary_kind") == "phase"
                and kwargs.get("boundary_id") in PHASES[4:11]
            ):
                action = next_authoring_action(layout, phase_store)
                if action is not None:
                    raise _AuthoringWaitSignal(action)
            return checkpoint

        try:
            bundle = materialize_u4_u11(
                repo,
                layout,
                phase_store,
                now=now,
                create_checkpoint=create_owned_checkpoint,
            )
        except _AuthoringWaitSignal as wait:
            stop_if_cancel_requested()
            last_complete = getattr(phase_store, "current_phase", None)
            if not isinstance(last_complete, str):
                raise RuntimeError(
                    "authoring wait has no completed phase authority"
                ) from wait
            return MaterializationProgress(
                outcome="awaiting-authoring",
                run_id=run_id,
                status="running",
                current_phase=str(wait.action["phase_id"]),
                last_complete_phase=last_complete,
                next_action=copy.deepcopy(wait.action),
                final_chat=None,
            )
        if isinstance(bundle, HostActionSeal):
            stop_if_cancel_requested()
            if (
                bundle.document.get("action_kind") != "semantic-review"
                or bundle.document.get("phase_id") != "U11"
            ):
                raise RuntimeError(
                    "U11 materialization returned an unauthorized host action"
                )
            return MaterializationProgress(
                outcome="awaiting-host-action",
                run_id=run_id,
                status="running",
                current_phase="U11",
                last_complete_phase="U10",
                next_action=copy.deepcopy(bundle.document),
                final_chat=None,
            )
        u11_event = bundle.phase_events[-1]
        if u11_event.get("phase_id") != "U11":
            raise RuntimeError("materialization did not end at a complete U11 event")
        stop_if_cancel_requested()
        recover_publish_transaction(
            layout,
            mark_needs_attention=mark_needs_attention,
            lease=lease,
        )
        if attention_marked:
            raise RuntimeError(
                "an incomplete publication was rolled back; operator attention is required"
            )

        validator_set_sha256 = _validator_set_authority(repo, validation)
        manifest_path = layout.artifacts_dir / "ultra-artifact-manifest.json"
        previous_manifest = (
            manifest_path.read_bytes() if manifest_path.is_file() else None
        )
        article_bytes = bundle.partial_article_path.read_bytes()
        dossier_bytes = bundle.dossier_path.read_bytes()
        manifest = artifacts.build_candidate_artifact_manifest(
            layout,
            phase_chain_head_sha256=_event_sha256(u11_event),
            validator_set_sha256=validator_set_sha256,
            generated_at=now,
            delivery_payloads={
                "delivery/CrossFrame-Ultra-完整文章.md": article_bytes,
                "delivery/完整推演档案.md": dossier_bytes,
                "delivery/工件索引.md": bundle.artifact_index_bytes,
            },
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
            article_bytes=article_bytes,
            dossier_bytes=dossier_bytes,
            artifact_index_bytes=bundle.artifact_index_bytes,
            manifest_bytes=manifest_bytes,
            fresh_check=fresh_check,
            commit_report=commit_report,
            mark_needs_attention=mark_needs_attention,
            lease=lease,
        )
        stop_if_cancel_requested()
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
        u12_event, complete_status, final_chat_path = _close_u12_transaction(
            layout,
            phase_store,
            publication,
            recovery=recovery,
            status_store=status_store,
            now=now,
            mark_needs_attention=mark_needs_attention,
            lease=lease,
        )
        if u12_event.get("phase_id") != "U12":
            raise RuntimeError("PhaseStore did not complete U12")
        return CompleteMaterializationResult(
            outcome="complete",
            run_id=run_id,
            status="complete",
            current_phase="U12",
            last_complete_phase="U12",
            next_action=None,
            final_chat=(
                load_json_object(final_chat_path)
                if final_chat_path.is_file()
                else None
            ),
            manifest_path=publication.paths.manifest_path,
            article_path=publication.paths.article_path,
            dossier_path=publication.paths.dossier_path,
            artifact_index_path=publication.paths.artifact_index_path,
            final_chat_path=final_chat_path,
            postcheck_passed=True,
        )
    except BaseException as error:
        if isinstance(error, CancelledRunError) and lease is not None:
            try:
                converge = getattr(recovery, "converge_cancel_if_requested", None)
                if callable(converge):
                    converge(layout, lease=lease, now=now)
            except BaseException as cancellation_error:
                add_note = getattr(error, "add_note", None)
                if callable(add_note):
                    add_note(
                        "failed to converge durable cancellation: "
                        f"{cancellation_error}"
                    )
        elif isinstance(error, FoundationInputError):
            try:
                rejected = status_store.read()
                if rejected.status in {"created", "running", "interrupted"}:
                    status_store.transition(
                        rejected,
                        "blocked",
                        _strictly_later(now, rejected.updated_at),
                        current_phase=rejected.current_phase,
                        last_complete_phase=rejected.last_complete_phase,
                        reason=f"fresh foundation input rejected: {error}",
                        validation_passed=False,
                        lease=lease,
                    )
            except BaseException as status_error:
                add_note = getattr(error, "add_note", None)
                if callable(add_note):
                    add_note(
                        "failed to mark rejected foundation blocked: "
                        f"{status_error}"
                    )
        elif isinstance(error, FoundationRecoveryError) and not attention_marked:
            try:
                mark_needs_attention(
                    f"foundation recovery requires attention: {error}"
                )
            except BaseException as status_error:
                add_note = getattr(error, "add_note", None)
                if callable(add_note):
                    add_note(
                        "failed to mark foundation recovery needs_attention: "
                        f"{status_error}"
                    )
        if (
            phase_store_restored
            and publication_journal_path.is_file()
            and not attention_marked
        ):
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
        if lease is not None:
            release_run_lease(layout, lease)


__all__ = (
    "AUTHORING_SLOT_RELATIVE_PATHS",
    "ArtifactSpec",
    "CompleteMaterializationResult",
    "MaterializationProgress",
    "RepairMaterializationResult",
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
    "next_authoring_action",
    "preflight_foundation_progress",
    "prepare_authoring",
    "record_materialized_phase",
    "seal_request_intake_authority",
    "seal_authoring_artifact",
)
