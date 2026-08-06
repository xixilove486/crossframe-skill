from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import copy
from pathlib import Path
from pathlib import PurePosixPath
import re
from typing import Any

from .artifacts import (
    MANIFEST_FILENAME,
    PARTIAL_ARTICLE_PATH,
    READ_EVENTS_PATH,
    ArtifactManifestError,
    validation_manifest_path,
    validate_artifact_manifest,
)
from .constants import current_version_binding
from .jsonio import (
    atomic_write_bytes,
    canonical_json_bytes,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from .locks import (
    CancelledRunError,
    Lease,
    load_cancel_intent,
    require_run_lease_owner,
)
from .paths import (
    RunLayout,
    RunMode,
    assert_safe_descendant,
    build_run_layout,
    default_root_policy,
)
from .schemas import (
    compute_artifact_content_sha256,
    validate_phase_artifact,
)


_SCHEMAS_BY_ID = {
    "crossframe.ultra.v82.run-contract": "ultra-run-contract.schema.json",
    "crossframe.ultra.v82.host-capability-attestation": (
        "ultra-host-capability-attestation.schema.json"
    ),
    "crossframe.ultra.v82.retrieval-ledger": "ultra-retrieval-ledger.schema.json",
    "crossframe.ultra.v82.evidence-ledger": "ultra-evidence-ledger.schema.json",
    "crossframe.ultra.v82.world-volume": "ultra-world-volume.schema.json",
    "crossframe.ultra.v82.transformation-ledger": "ultra-transformation-ledger.schema.json",
    "crossframe.ultra.v82.concept-disposition": "ultra-concept-disposition.schema.json",
    "crossframe.ultra.v82.claim-mechanism-graph": "ultra-claim-mechanism-graph.schema.json",
    "crossframe.ultra.v82.recursive-state": "ultra-recursive-state.schema.json",
    "crossframe.ultra.v82.recursive-lineage": "ultra-recursive-lineage.schema.json",
    "crossframe.ultra.v82.order-evaluation": "ultra-order-evaluation.schema.json",
    "crossframe.ultra.v82.red-team-report": "ultra-red-team-report.schema.json",
    "crossframe.ultra.v82.verdict": "ultra-verdict.schema.json",
    "crossframe.ultra.v82.action-ranking": "ultra-action-ranking.schema.json",
    "crossframe.ultra.v82.forecast-ledger": "ultra-forecast-ledger.schema.json",
    "crossframe.ultra.v82.framework-gap-ledger": "ultra-framework-gap-ledger.schema.json",
    "crossframe.ultra.v82.output-plan": "ultra-output-plan.schema.json",
    "crossframe.ultra.v82.semantic-coverage": "ultra-semantic-coverage.schema.json",
    "crossframe.ultra.v82.article-review": "ultra-article-review.schema.json",
    "crossframe.ultra.v82.semantic-review": "ultra-semantic-review.schema.json",
}
_CHECK_ORDER = (
    "manifest-integrity",
    "artifact-integrity",
    "source-read-coverage",
    "semantic-tamper-resistance",
    "article-coverage",
    "publication-boundary",
    "privacy-logs",
)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"Authorization\s*:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:password|passwd|secret)\s*[=:]\s*\S+", re.IGNORECASE),
)
_U1_SOURCE_LOCK_PATH = "recovery/u1-authority/source-lock.json"
_U1_READ_PLAN_PATH = "recovery/u1-authority/read-plan.json"
_U1_SOURCE_COVERAGE_PATH = "recovery/u1-authority/source-coverage.json"
_RUN_CONTRACT_PATH = "artifacts/ultra-run-contract.json"
_HOST_CAPABILITY_ATTESTATION_PATH = (
    "artifacts/U00-U03-evidence/U00-host-capability-attestation.json"
)
_COMPLETE_THROUGH_U11 = tuple(f"U{number}" for number in range(12))
_COMPLETE_THROUGH_U12 = tuple(f"U{number}" for number in range(13))
_VALIDATION_LAYER_IDS = (
    "deterministic",
    "adversarial",
    "fresh-semantic",
)


class _AuthorityDAGError(ValueError):
    def __init__(self, message: str, *, phase_id: str | None = None) -> None:
        super().__init__(message)
        self.phase_id = phase_id


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _checked_repo(repo: Path) -> Path:
    if not isinstance(repo, Path):
        raise TypeError("repo must be a pathlib.Path")
    resolved = repo.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("repo must be an existing directory")
    required = resolved / "skills/crossframe-ultra/scripts/ultra_runtime/validation.py"
    if not required.is_file():
        raise ValueError("repo does not contain the CrossFrame Ultra validator")
    return resolved


def validator_set_sha256(repo: Path) -> str:
    root = _checked_repo(repo)
    runtime = root / "skills/crossframe-ultra/scripts/ultra_runtime"
    relative_files = [
        "skills/crossframe-ultra/references/compatibility-matrix.json",
        "skills/crossframe-ultra/references/source-manifest.json",
        "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py",
        "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_knowledge.py",
        "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py",
        "scripts/check_crossframe_ultra_artifacts.py",
    ]
    relative_files.extend(
        path.relative_to(root).as_posix()
        for path in sorted(runtime.glob("*.py"))
    )
    relative_files.extend(
        path.relative_to(root).as_posix()
        for path in sorted((root / "skills/crossframe-ultra/schemas").glob("*.json"))
    )
    hashes: dict[str, str] = {}
    for relative in relative_files:
        path = root / Path(relative)
        if not path.is_file():
            raise ValueError(f"validator-set authority is missing: {relative}")
        hashes[relative] = sha256_bytes(path.read_bytes())
    if runtime != Path(__file__).resolve().parent and root == _repo_root():
        raise ValueError("validator runtime path is not bound to the selected repository")
    return sha256_bytes(canonical_json_bytes(hashes))


def _issue(
    issues: dict[str, list[tuple[str, str]]],
    check_id: str,
    error_code: str,
    artifact: str,
) -> None:
    issues[check_id].append((error_code, artifact))


def _artifact_path(layout: RunLayout, relative: str) -> Path:
    candidate = layout.run_dir / Path(relative)
    assert_safe_descendant(layout.root, candidate)
    try:
        candidate.relative_to(layout.run_dir)
    except (ValueError, OSError) as error:
        raise ValueError(f"artifact path escapes its run: {relative}") from error
    return candidate


def _active_phase_checkpoints(
    recovery: object,
    events: Sequence[Mapping[str, object]],
    checkpoints: Sequence[Mapping[str, object]],
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    selector = getattr(recovery, "_active_completed_events", None)
    if not callable(selector):
        raise _AuthorityDAGError("active recovery generation selector is unavailable")
    _, active_events = selector(events)
    selected: list[dict[str, object]] = []
    for event in active_events:
        event_sha256 = event.get("event_sha256")
        matches = [
            checkpoint
            for checkpoint in checkpoints
            if checkpoint.get("boundary_kind") == "phase"
            and checkpoint.get("phase_event_sha256") == event_sha256
        ]
        if len(matches) != 1:
            raise _AuthorityDAGError(
                "active phase event must bind exactly one checkpoint",
                phase_id=str(event.get("phase_id")),
            )
        selected.append(copy.deepcopy(dict(matches[0])))
    return (
        tuple(copy.deepcopy(dict(event)) for event in active_events),
        tuple(selected),
    )


def _load_verified_disk_authority(
    layout: RunLayout,
    manifest: Mapping[str, Any],
) -> dict[str, object]:
    from . import recovery

    try:
        recovery._validate_layout(layout)
        run_authority, compatibility = recovery._validate_authority(layout)
        if compatibility != "resume":
            raise ValueError("fresh validation requires exact current recovery authority")
        events = recovery._read_events(
            layout,
            run_authority,
            compatibility=compatibility,
        )
    except Exception as error:
        raise _AuthorityDAGError(f"recovery authority is invalid: {error}") from error

    events_by_hash = {str(event["event_sha256"]): event for event in events}
    checkpoints_dir = layout.recovery_dir / "checkpoints"
    try:
        candidates = sorted(checkpoints_dir.iterdir(), key=lambda path: path.name)
    except OSError as error:
        raise _AuthorityDAGError("checkpoint directory is unavailable") from error
    if not candidates:
        raise _AuthorityDAGError("checkpoint directory is empty")

    checkpoints: list[dict[str, object]] = []
    slots: set[tuple[int, str, str, int]] = set()
    for path in candidates:
        phase_id: str | None = None
        try:
            if not path.is_file() or re.fullmatch(r"[0-9a-f]{64}\.json", path.name) is None:
                raise ValueError("checkpoint directory contains a noncanonical entry")
            raw = path.read_bytes()
            checkpoint = load_json_object_bytes(raw, source=str(path))
            raw_phase = checkpoint.get("phase_id")
            phase_id = raw_phase if isinstance(raw_phase, str) else None
            if sha256_bytes(raw) != path.stem:
                raise ValueError("checkpoint filename hash differs from its bytes")
            if raw != canonical_json_bytes(checkpoint):
                raise ValueError("checkpoint bytes are not canonical JSON")
            validated = recovery._validate_checkpoint(
                layout,
                checkpoint,
                authority=run_authority,
                compatibility=compatibility,
                events_by_hash=events_by_hash,
            )
            slot = recovery._checkpoint_slot(validated)
            if slot in slots:
                raise ValueError("checkpoint logical slot is duplicated")
            slots.add(slot)
            checkpoints.append(validated)
        except Exception as error:
            raise _AuthorityDAGError(
                f"checkpoint authority is invalid: {error}",
                phase_id=phase_id,
            ) from error
    checkpoints.sort(key=recovery._checkpoint_sort_key)

    active_events, active_phase_checkpoints = _active_phase_checkpoints(
        recovery,
        events,
        checkpoints,
    )
    phase_ids = tuple(
        str(event["phase_id"])
        for event in active_events
    )
    if phase_ids not in {_COMPLETE_THROUGH_U11, _COMPLETE_THROUGH_U12}:
        raise _AuthorityDAGError("phase chain is not complete through U11")
    phase_checkpoints = list(active_phase_checkpoints)
    if tuple(str(checkpoint["phase_id"]) for checkpoint in phase_checkpoints) != phase_ids:
        raise _AuthorityDAGError("phase checkpoints do not exactly cover the event chain")

    refs_by_phase: dict[str, dict[str, str]] = {}
    for checkpoint in phase_checkpoints:
        phase_id = str(checkpoint["phase_id"])
        refs = checkpoint.get("artifact_hashes")
        if not isinstance(refs, list):
            raise _AuthorityDAGError(
                "phase checkpoint artifact refs are invalid",
                phase_id=phase_id,
            )
        refs_by_phase[phase_id] = {
            str(item["path"]): str(item["sha256"])
            for item in refs
            if isinstance(item, Mapping)
        }
        if len(refs_by_phase[phase_id]) != len(refs):
            raise _AuthorityDAGError(
                "phase checkpoint artifact refs are duplicated",
                phase_id=phase_id,
            )

    manifest_refs: dict[str, dict[str, str]] = {}
    for record in manifest["artifacts"]:
        phase_id = str(record["phase_id"])
        manifest_refs.setdefault(phase_id, {})[str(record["path"])] = str(
            record["sha256"]
        )
    u0_checkpoint_refs = refs_by_phase.get("U0", {})
    if set(u0_checkpoint_refs) != {_RUN_CONTRACT_PATH}:
        raise _AuthorityDAGError(
            "U0 checkpoint does not bind only the fixed run contract",
            phase_id="U0",
        )
    u0_manifest_refs = manifest_refs.get("U0", {})
    expected_u0_manifest_paths = {
        _RUN_CONTRACT_PATH,
        _HOST_CAPABILITY_ATTESTATION_PATH,
    }
    if set(u0_manifest_refs) != expected_u0_manifest_paths:
        raise _AuthorityDAGError(
            "U0 manifest does not contain the fixed authority files",
            phase_id="U0",
        )
    if (
        u0_checkpoint_refs[_RUN_CONTRACT_PATH]
        != u0_manifest_refs[_RUN_CONTRACT_PATH]
    ):
        raise _AuthorityDAGError(
            "U0 checkpoint run contract differs from the manifest",
            phase_id="U0",
        )
    try:
        run_contract = load_json_object(_artifact_path(layout, _RUN_CONTRACT_PATH))
    except Exception as error:
        raise _AuthorityDAGError(
            "U0 run contract is unavailable",
            phase_id="U0",
        ) from error
    if (
        run_contract.get("capability_attestation_sha256")
        != u0_manifest_refs[_HOST_CAPABILITY_ATTESTATION_PATH]
    ):
        raise _AuthorityDAGError(
            "U0 capability attestation differs from the run contract",
            phase_id="U0",
        )
    for phase_id in tuple(f"U{number}" for number in range(2, 12)):
        if refs_by_phase.get(phase_id) != manifest_refs.get(phase_id):
            raise _AuthorityDAGError(
                "phase checkpoint differs from the manifest artifact set",
                phase_id=phase_id,
            )
    expected_u1_paths = {
        _U1_SOURCE_LOCK_PATH,
        _U1_READ_PLAN_PATH,
        _U1_SOURCE_COVERAGE_PATH,
    }
    if set(refs_by_phase.get("U1", {})) != expected_u1_paths:
        raise _AuthorityDAGError(
            "U1 checkpoint does not bind the fixed source authority files",
            phase_id="U1",
        )
    if "U12" in refs_by_phase:
        expected_u12_paths = {
            "artifacts/ultra-artifact-manifest.json",
            "validation/current/ultra-validator-report.json",
            "delivery/CrossFrame-Ultra-完整文章.md",
            "delivery/完整推演档案.md",
            "delivery/工件索引.md",
        }
        if set(refs_by_phase["U12"]) != expected_u12_paths:
            raise _AuthorityDAGError(
                "U12 checkpoint does not bind the fixed completion files",
                phase_id="U12",
            )
    u11_event = next(
        event for event in active_events if event.get("phase_id") == "U11"
    )
    if manifest.get("phase_chain_head_sha256") != u11_event.get("event_sha256"):
        raise _AuthorityDAGError("manifest does not bind the verified U11 chain head")
    return {
        "run_authority": copy.deepcopy(run_authority),
        "events": tuple(copy.deepcopy(event) for event in active_events),
        "refs_by_phase": copy.deepcopy(refs_by_phase),
        "active_generation": int(u11_event.get("generation", 0)),
    }


def _load_structured_artifacts(
    layout: RunLayout,
    manifest: Mapping[str, Any],
    issues: dict[str, list[tuple[str, str]]],
) -> dict[str, list[dict[str, object]]]:
    loaded: dict[str, list[dict[str, object]]] = {}
    for record in manifest["artifacts"]:
        schema_id = str(record["schema_id"])
        if schema_id in {
            "crossframe.ultra.v82.read-event",
            "crossframe.ultra.v82.article-partial",
            "crossframe.ultra.v82.complete-dossier",
            "crossframe.ultra.v82.artifact-index",
        }:
            continue
        relative = str(record["path"])
        schema_name = _SCHEMAS_BY_ID.get(schema_id)
        if schema_name is None:
            _issue(
                issues,
                "artifact-integrity",
                "ULTRA-UNKNOWN-ARTIFACT",
                relative,
            )
            continue
        try:
            document = load_json_object(_artifact_path(layout, relative))
            validate_phase_artifact(
                schema_name,
                document,
                expected_schema_id=schema_id,
                expected_run_id=layout.run_dir.name,
                expected_version_binding=current_version_binding(),
                expected_phase_id=str(record["phase_id"]),
            )
        except Exception:
            if schema_id == "crossframe.ultra.v82.world-volume":
                code = "ULTRA-WORLD-FLATTENING"
                check = "semantic-tamper-resistance"
            elif schema_id == "crossframe.ultra.v82.recursive-state":
                code = "ULTRA-LINEAGE-LOSS"
                check = "semantic-tamper-resistance"
            elif schema_id == "crossframe.ultra.v82.claim-mechanism-graph":
                code = "ULTRA-EMPTY-RIVAL" if _has_empty_rival(document) else "ULTRA-ARTIFACT-SCHEMA"
                check = "semantic-tamper-resistance" if code == "ULTRA-EMPTY-RIVAL" else "artifact-integrity"
            else:
                code = "ULTRA-ARTIFACT-SCHEMA"
                check = "artifact-integrity"
            _issue(issues, check, code, relative)
            loaded.setdefault(schema_id, []).append(document)
            continue
        loaded.setdefault(schema_id, []).append(document)
    return loaded


def _has_empty_rival(graph: Mapping[str, Any]) -> bool:
    claims = {
        item.get("claim_id"): item
        for item in graph.get("claims", [])
        if isinstance(item, Mapping)
    }
    mechanisms = {
        item.get("mechanism_id"): item
        for item in graph.get("mechanisms", [])
        if isinstance(item, Mapping)
    }
    rivals = [
        item
        for item in graph.get("explanations", [])
        if isinstance(item, Mapping) and item.get("kind") == "strongest-rival"
    ]
    if len(rivals) != 1:
        return True
    rival = rivals[0]
    claim_ids = rival.get("claim_ids")
    mechanism_ids = rival.get("mechanism_ids")
    if not isinstance(claim_ids, list) or not claim_ids:
        return True
    if not isinstance(mechanism_ids, list) or not mechanism_ids:
        return True
    return any(
        not isinstance(claims.get(item, {}).get("statement"), str)
        or not claims[item]["statement"].strip()
        for item in claim_ids
    ) or any(
        not isinstance(mechanisms.get(item, {}).get("description"), str)
        or not mechanisms[item]["description"].strip()
        for item in mechanism_ids
    )


def _marker_stuffed(text: object) -> bool:
    if not isinstance(text, str):
        return False
    words = re.findall(r"[A-Za-z0-9_-]+", text.casefold())
    if len(words) < 64:
        return False
    counts = Counter(words)
    return max(counts.values()) / len(words) >= 0.5 or len(counts) / len(words) < 0.08


def _validate_claim_semantics(
    loaded: Mapping[str, list[dict[str, object]]],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    from . import judgment

    evidence_docs = loaded.get("crossframe.ultra.v82.evidence-ledger", [])
    graph_docs = loaded.get("crossframe.ultra.v82.claim-mechanism-graph", [])
    evidence_records: dict[str, Mapping[str, object]] = {}
    for evidence in evidence_docs:
        for item in evidence.get("entries", []):
            if isinstance(item, Mapping):
                evidence_id = item.get("evidence_id")
                if isinstance(evidence_id, str):
                    evidence_records[evidence_id] = item
    for graph in graph_docs:
        if _has_empty_rival(graph):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-EMPTY-RIVAL",
                "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
            )
        strings = [
            item.get(field)
            for collection, field in (("claims", "statement"), ("mechanisms", "description"))
            for item in graph.get(collection, [])
            if isinstance(item, Mapping)
        ]
        if any(_marker_stuffed(value) for value in strings):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-MARKER-STUFFING",
                "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
            )
        for claim in graph.get("claims", []):
            if not isinstance(claim, Mapping) or claim.get("identity") not in {
                "observed",
                "reported",
                "inferred-from-material",
            }:
                continue
            try:
                judgment.validate_support_edges(
                    claim=claim,
                    evidence_records=evidence_records,
                    factual=True,
                )
            except judgment.ClaimMechanismError as error:
                _issue(
                    issues,
                    "semantic-tamper-resistance",
                    "ULTRA-EVIDENCE-HOLLOW",
                    "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
                )
                if "simulated" in str(error):
                    _issue(
                        issues,
                        "semantic-tamper-resistance",
                        "ULTRA-SIMULATION-AS-FACT",
                        "artifacts/U06-U08-inference/ultra-claim-mechanism-graph.json",
                    )

    for verdict in loaded.get("crossframe.ultra.v82.verdict", []):
        for lock in verdict.get("five_verdicts", []):
            if not isinstance(lock, Mapping) or lock.get("kind") != "fact":
                continue
            try:
                judgment.validate_support_edges(
                    claim={
                        "statement": lock.get("proposition"),
                        "evidence_refs": lock.get("evidence_refs"),
                    },
                    evidence_records=evidence_records,
                    factual=True,
                )
            except judgment.ClaimMechanismError as error:
                _issue(
                    issues,
                    "semantic-tamper-resistance",
                    "ULTRA-EVIDENCE-HOLLOW",
                    "artifacts/U09-verdict-action/ultra-verdict.json",
                )
                if "simulated" in str(error):
                    _issue(
                        issues,
                        "semantic-tamper-resistance",
                        "ULTRA-SIMULATION-AS-FACT",
                        "artifacts/U09-verdict-action/ultra-verdict.json",
                    )


def _validate_world_and_lineage(
    loaded: Mapping[str, list[dict[str, object]]],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    for volume in loaded.get("crossframe.ultra.v82.world-volume", []):
        required = ("actors", "circles", "positions", "memberships", "local_distributions")
        if any(not isinstance(volume.get(field), list) or not volume[field] for field in required):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-WORLD-FLATTENING",
                "artifacts/U04-U05-world-volume/ultra-world-volume.json",
            )
        if any(key.startswith("global_") for key in volume):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-WORLD-FLATTENING",
                "artifacts/U04-U05-world-volume/ultra-world-volume.json",
            )
    for state in loaded.get("crossframe.ultra.v82.recursive-state", []):
        inherited = (
            "inherited_fact_ids",
            "inherited_unknown_ids",
            "inherited_loss_ids",
            "inherited_residual_ids",
        )
        if any(not isinstance(state.get(field), list) or not state[field] for field in inherited):
            _issue(
                issues,
                "semantic-tamper-resistance",
                "ULTRA-LINEAGE-LOSS",
                "artifacts/U06-U08-inference",
            )


def _single_document(
    loaded: Mapping[str, list[dict[str, object]]],
    schema_id: str,
) -> dict[str, object]:
    documents = loaded.get(schema_id, [])
    if len(documents) != 1:
        raise ValueError(f"disk authority requires exactly one {schema_id} artifact")
    return documents[0]


def _validate_u4_u9_authorities(
    repo: Path,
    layout: RunLayout,
    loaded: Mapping[str, list[dict[str, object]]],
    authority: Mapping[str, object],
) -> frozenset[str]:
    from . import concept_closure
    from . import forecast
    from . import judgment
    from . import materialization
    from . import recursion
    from . import world_volume

    raw_refs = authority.get("refs_by_phase")
    if not isinstance(raw_refs, Mapping):
        raise ValueError("verified phase artifact refs are unavailable")

    def expected_hash(phase_id: str, relative: str) -> str:
        phase_refs = raw_refs.get(phase_id)
        if not isinstance(phase_refs, Mapping):
            raise ValueError(f"verified {phase_id} artifact refs are unavailable")
        digest = phase_refs.get(relative)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(f"verified artifact hash is unavailable: {relative}")
        return digest

    evidence = _single_document(
        loaded, "crossframe.ultra.v82.evidence-ledger"
    )
    world = _single_document(loaded, "crossframe.ultra.v82.world-volume")
    transformations = _single_document(
        loaded, "crossframe.ultra.v82.transformation-ledger"
    )
    concepts = _single_document(
        loaded, "crossframe.ultra.v82.concept-disposition"
    )
    graph = _single_document(
        loaded, "crossframe.ultra.v82.claim-mechanism-graph"
    )
    lineage = _single_document(
        loaded, "crossframe.ultra.v82.recursive-lineage"
    )
    order_evaluation = _single_document(
        loaded, "crossframe.ultra.v82.order-evaluation"
    )
    red_team = _single_document(
        loaded, "crossframe.ultra.v82.red-team-report"
    )
    verdict = _single_document(loaded, "crossframe.ultra.v82.verdict")
    action_ranking = _single_document(
        loaded, "crossframe.ultra.v82.action-ranking"
    )
    forecast_ledger = _single_document(
        loaded, "crossframe.ultra.v82.forecast-ledger"
    )

    evidence_hash = expected_hash(
        "U3", "artifacts/U00-U03-evidence/U03-evidence-ledger.json"
    )
    world_hash = expected_hash(
        "U4", "artifacts/U04-U05-world-volume/U04-world-volume.json"
    )
    transformation_hash = expected_hash(
        "U5",
        "artifacts/U04-U05-world-volume/U05-transformation-ledger.json",
    )
    concept_hash = expected_hash(
        "U5", "artifacts/U04-U05-world-volume/U05-concept-disposition.json"
    )
    graph_hash = expected_hash(
        "U6", "artifacts/U06-U08-inference/U06-claim-mechanism-graph.json"
    )
    lineage_hash = expected_hash(
        "U7", "artifacts/U06-U08-inference/U07-recursive-lineage.json"
    )
    order_hash = expected_hash(
        "U8", "artifacts/U06-U08-inference/U08-order-evaluation.json"
    )
    red_team_hash = expected_hash(
        "U8", "artifacts/U06-U08-inference/U08-red-team-report.json"
    )
    verdict_hash = expected_hash(
        "U9", "artifacts/U09-U10-verdict/U09-verdict.json"
    )

    relation_refs = materialization._runtime_relation_refs(world)
    relation_refs_sha256 = sha256_bytes(canonical_json_bytes(relation_refs))
    world_volume.validate_world_volume(
        world,
        evidence_ledger=evidence,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_evidence_artifact_sha256=evidence_hash,
        relation_refs=relation_refs,
        expected_relation_refs_sha256=relation_refs_sha256,
    )
    knowledge_values, source_manifest_sha256 = materialization._knowledge_authorities(
        repo
    )
    required_concept_semantic_unit_ids = concept_closure.validate_concept_closure(
        concepts,
        repo=repo,
        evidence_ledger=evidence,
        world_volume=world,
        transformation_ledger=transformations,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_source_manifest_sha256=source_manifest_sha256,
        expected_evidence_artifact_sha256=evidence_hash,
        expected_world_volume_artifact_sha256=world_hash,
        expected_transformation_ledger_artifact_sha256=transformation_hash,
        expected_registry_sha256=knowledge_values["registry_sha256"],
        expected_route_map_sha256=knowledge_values["route_map_sha256"],
        expected_contract_map_sha256=knowledge_values["contract_map_sha256"],
        required_route_ids=concepts["required_route_ids"],
    )
    judgment._validate_claim_mechanism_graph(
        graph,
        evidence_ledger=evidence,
        world_volume=world,
        transformation_ledger=transformations,
        concept_disposition=concepts,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_evidence_ledger_artifact_sha256=evidence_hash,
        expected_world_volume_artifact_sha256=world_hash,
        expected_transformation_ledger_artifact_sha256=transformation_hash,
        expected_concept_disposition_artifact_sha256=concept_hash,
    )

    states = loaded.get("crossframe.ultra.v82.recursive-state", [])
    if not states:
        raise ValueError("verified U7 authority has no recursive states")
    state_registry: dict[str, dict[str, object]] = {}
    for state in states:
        node_id = state.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("verified recursive state has no node_id")
        relative = f"artifacts/U06-U08-inference/U07-recursive-states/{node_id}.json"
        state_hash = expected_hash("U7", relative)
        if state_hash in state_registry:
            raise ValueError("verified recursive state hash is duplicated")
        state_registry[state_hash] = state
    for state in states:
        recursion._validate_recursive_state(
            state,
            parent_volume=world,
            recursive_state_artifacts=state_registry,
            transformation_ledger=transformations,
            claim_mechanism_graph=graph,
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_world_volume_artifact_sha256=world_hash,
            expected_transformation_ledger_artifact_sha256=transformation_hash,
            expected_claim_mechanism_graph_artifact_sha256=graph_hash,
        )
    recursion._validate_recursive_lineage_bundle(
        lineage,
        world,
        recursive_state_artifacts=state_registry,
        transformation_ledger=transformations,
        claim_mechanism_graph=graph,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_world_volume_artifact_sha256=world_hash,
        expected_transformation_ledger_artifact_sha256=transformation_hash,
        expected_claim_mechanism_graph_artifact_sha256=graph_hash,
    )
    recursion._validate_order_evaluation(
        order_evaluation,
        claim_mechanism_graph=graph,
        recursive_lineage=lineage,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_claim_mechanism_graph_artifact_sha256=graph_hash,
        expected_recursive_lineage_artifact_sha256=lineage_hash,
    )
    recursion._validate_red_team_report(
        red_team,
        claim_mechanism_graph=graph,
        recursive_lineage=lineage,
        order_evaluation=order_evaluation,
        recursive_state_artifacts=state_registry,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_claim_mechanism_graph_artifact_sha256=graph_hash,
        expected_recursive_lineage_artifact_sha256=lineage_hash,
        expected_order_evaluation_artifact_sha256=order_hash,
    )
    judgment._validate_verdict_with_authority(
        verdict,
        evidence_ledger=evidence,
        recursive_lineage=lineage,
        claim_mechanism_graph=graph,
        order_evaluation=order_evaluation,
        red_team_report=red_team,
        recursive_state_artifacts=state_registry,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_evidence_ledger_artifact_sha256=evidence_hash,
        expected_claim_mechanism_graph_artifact_sha256=graph_hash,
        expected_recursive_lineage_artifact_sha256=lineage_hash,
        expected_order_evaluation_artifact_sha256=order_hash,
        expected_red_team_report_artifact_sha256=red_team_hash,
    )
    judgment._validate_action_ranking(
        action_ranking,
        verdict=verdict,
        evidence=evidence,
        lineage=lineage,
        expected_verdict_artifact_sha256=verdict_hash,
    )
    forecast._validate_forecast_ledger(
        forecast_ledger,
        verdict=verdict,
        evidence=evidence,
        lineage=lineage,
        expected_verdict_artifact_sha256=verdict_hash,
    )
    return frozenset(required_concept_semantic_unit_ids)


def _validate_u10_authority(
    layout: RunLayout,
    loaded: Mapping[str, list[dict[str, object]]],
    authority: Mapping[str, object],
    *,
    required_concept_semantic_unit_ids: frozenset[str],
) -> None:
    from . import article
    from . import materialization

    raw_refs = authority.get("refs_by_phase")
    raw_events = authority.get("events")
    if not isinstance(raw_refs, Mapping) or not isinstance(raw_events, tuple):
        raise ValueError("verified U10 disk authority is unavailable")
    u9_events = [
        event
        for event in raw_events
        if isinstance(event, Mapping)
        and event.get("phase_id") == "U9"
        and event.get("status") == "complete"
    ]
    if len(u9_events) != 1:
        raise ValueError("verified U9 parent event is unavailable")

    documents_by_sha256: dict[str, Mapping[str, object]] = {}
    for documents in loaded.values():
        for document in documents:
            digest = sha256_bytes(canonical_json_bytes(document))
            if digest in documents_by_sha256:
                raise ValueError("verified disk artifacts reuse a content hash")
            documents_by_sha256[digest] = document

    upstream_candidates: list[tuple[Path, Mapping[str, object]]] = []
    for ordinal in range(3, 10):
        phase_id = f"U{ordinal}"
        phase_refs = raw_refs.get(phase_id)
        if not isinstance(phase_refs, Mapping):
            raise ValueError(f"verified {phase_id} artifact refs are unavailable")
        for relative, digest in phase_refs.items():
            if not isinstance(relative, str) or not isinstance(digest, str):
                raise ValueError("verified upstream artifact ref is invalid")
            document = documents_by_sha256.get(digest)
            if document is None:
                raise ValueError("verified upstream artifact bytes are unavailable")
            upstream_candidates.append(
                (_artifact_path(layout, relative), document)
            )

    frozen_sequence = materialization._OUTPUT_PLAN_UPSTREAM_SCHEMA_SEQUENCE
    recursive_schema_id = "crossframe.ultra.v82.recursive-state"
    schema_rank = {
        schema_id: index
        for index, schema_id in enumerate(frozen_sequence[:5])
    }
    schema_rank[recursive_schema_id] = 5
    schema_rank.update(
        {
            schema_id: index + 6
            for index, schema_id in enumerate(frozen_sequence[5:])
        }
    )
    try:
        upstream_authorities = sorted(
            upstream_candidates,
            key=lambda item: (
                schema_rank[str(item[1]["schema_id"])],
                item[0].as_posix()
                if item[1].get("schema_id") == recursive_schema_id
                else "",
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("verified U3-U9 schema sequence is invalid") from error

    required_artifacts, authority_documents = (
        materialization._derive_output_plan_upstream_authority(
            layout,
            upstream_authorities,
        )
    )
    output_plan = _single_document(
        loaded, "crossframe.ultra.v82.output-plan"
    )
    article.validate_output_plan_artifact(
        output_plan,
        expected_run_id=layout.run_dir.name,
        expected_version_binding=current_version_binding(),
        expected_u9_parent_event_sha256=str(u9_events[0]["event_sha256"]),
        expected_required_artifacts=required_artifacts,
    )
    materialization._validate_output_plan_semantic_authority(
        output_plan,
        authority_documents,
        required_concept_semantic_unit_ids=required_concept_semantic_unit_ids,
    )


def _validate_read_events(
    repo: Path,
    layout: RunLayout,
    manifest: Mapping[str, Any],
    authority: Mapping[str, object],
    issues: dict[str, list[tuple[str, str]]],
) -> None:
    records = [
        item
        for item in manifest["artifacts"]
        if item["schema_id"] == "crossframe.ultra.v82.read-event"
    ]
    if len(records) != 1 or records[0]["path"] != READ_EVENTS_PATH:
        _issue(
            issues,
            "source-read-coverage",
            "ULTRA-READ-COVERAGE",
            READ_EVENTS_PATH,
        )
        return
    from . import source_integrity

    try:
        raw_run_authority = authority.get("run_authority")
        raw_events = authority.get("events")
        raw_refs = authority.get("refs_by_phase")
        if (
            not isinstance(raw_run_authority, Mapping)
            or not isinstance(raw_events, tuple)
            or not isinstance(raw_refs, Mapping)
        ):
            raise ValueError("verified disk authority is incomplete")
        u0_event = next(
            event
            for event in raw_events
            if isinstance(event, Mapping) and event.get("phase_id") == "U0"
        )
        u1_refs = raw_refs.get("U1")
        if not isinstance(u1_refs, Mapping):
            raise ValueError("verified U1 checkpoint refs are unavailable")
        source_path = repo / "skills/crossframe-ultra/references/source-manifest.json"
        source = source_integrity.load_source_manifest(
            source_path,
            expected_sha256=str(raw_run_authority["source_sha256"]),
        )
        input_refs = raw_run_authority.get("input_refs")
        if not isinstance(input_refs, list) or not input_refs:
            raise ValueError("verified input refs are unavailable")
        expected_inputs: list[dict[str, str]] = []
        for item in input_refs:
            if not isinstance(item, Mapping):
                raise ValueError("verified input ref is malformed")
            relative = str(item["path"])
            parsed = PurePosixPath(relative)
            if (
                parsed.is_absolute()
                or "\\" in relative
                or len(parsed.parts) < 2
                or parsed.parts[0] != "input"
                or ".." in parsed.parts
            ):
                raise ValueError("verified input ref is outside the input directory")
            expected_inputs.append(
                {
                    "path": PurePosixPath(*parsed.parts[1:]).as_posix(),
                    "sha256": str(item["sha256"]),
                    "media_type": str(item["media_type"]),
                }
            )
        source_lock_path = _artifact_path(layout, _U1_SOURCE_LOCK_PATH)
        read_plan_path = _artifact_path(layout, _U1_READ_PLAN_PATH)
        source_coverage_path = _artifact_path(layout, _U1_SOURCE_COVERAGE_PATH)
        run_contract_path = _artifact_path(layout, _RUN_CONTRACT_PATH)
        source_lock_raw = source_lock_path.read_bytes()
        read_plan_raw = read_plan_path.read_bytes()
        source_coverage_raw = source_coverage_path.read_bytes()
        run_contract_raw = run_contract_path.read_bytes()
        source_lock = load_json_object_bytes(
            source_lock_raw,
            source=_U1_SOURCE_LOCK_PATH,
        )
        read_plan = load_json_object_bytes(
            read_plan_raw,
            source=_U1_READ_PLAN_PATH,
        )
        source_coverage = load_json_object_bytes(
            source_coverage_raw,
            source=_U1_SOURCE_COVERAGE_PATH,
        )
        run_contract = load_json_object_bytes(
            run_contract_raw,
            source=_RUN_CONTRACT_PATH,
        )
        if (
            source_lock_raw != canonical_json_bytes(source_lock)
            or read_plan_raw != canonical_json_bytes(read_plan)
            or source_coverage_raw != canonical_json_bytes(source_coverage)
            or run_contract_raw != canonical_json_bytes(run_contract)
        ):
            raise ValueError("persisted U1 authority bytes are not canonical")
        if sha256_bytes(run_contract_raw) != raw_run_authority.get(
            "run_contract_sha256"
        ):
            raise ValueError("persisted run contract differs from run authority")
        expected_request_sha256 = run_contract.get("request_sha256")
        read_events_raw = _artifact_path(layout, READ_EVENTS_PATH).read_bytes()
        if not read_events_raw or not read_events_raw.endswith(b"\n"):
            raise source_integrity.SourceCoverageError(
                "read event journal is incomplete"
            )
        read_events: list[dict[str, object]] = []
        for ordinal, row in enumerate(read_events_raw.splitlines(keepends=True), start=1):
            event = load_json_object_bytes(
                row,
                source=f"{READ_EVENTS_PATH}:{ordinal}",
            )
            if row != canonical_json_bytes(event):
                raise source_integrity.SourceCoverageError(
                    "read event journal is not canonical JSONL"
                )
            read_events.append(event)
        expected_source_lock_sha256 = u1_refs.get(_U1_SOURCE_LOCK_PATH)
        expected_read_plan_sha256 = u1_refs.get(_U1_READ_PLAN_PATH)
        expected_read_coverage_sha256 = u1_refs.get(_U1_SOURCE_COVERAGE_PATH)
        if (
            not isinstance(expected_request_sha256, str)
            or not isinstance(expected_source_lock_sha256, str)
            or not isinstance(expected_read_plan_sha256, str)
            or not isinstance(expected_read_coverage_sha256, str)
        ):
            raise ValueError("verified U1 checkpoint hashes are unavailable")
        source_integrity._validate_persisted_u1_authority(
            repo=repo,
            run_layout=layout,
            manifest=source,
            source_lock=source_lock,
            read_plan=read_plan,
            coverage=source_coverage,
            read_events=read_events,
            expected_run_id=layout.run_dir.name,
            expected_run_mode=_mode_for_layout(layout).value,
            expected_version_binding=current_version_binding(),
            expected_parent_event_sha256=str(u0_event["event_sha256"]),
            expected_evidence_cutoff=str(raw_run_authority["evidence_cutoff"]),
            expected_inputs=expected_inputs,
            expected_request_sha256=expected_request_sha256,
            expected_source_lock_sha256=expected_source_lock_sha256,
            expected_read_plan_sha256=expected_read_plan_sha256,
            expected_read_coverage_sha256=expected_read_coverage_sha256,
        )
    except source_integrity.SourceCoverageError as error:
        message = str(error)
        code = (
            "ULTRA-SOURCE-MISMATCH"
            if "content hash differs" in message
            else "ULTRA-READ-COVERAGE"
            if "count" in message or "cover every" in message or "incomplete" in message
            else "ULTRA-READ-AUTHORITY"
        )
        _issue(
            issues,
            "source-read-coverage",
            code,
            READ_EVENTS_PATH,
        )
    except Exception:
        _issue(
            issues,
            "source-read-coverage",
            "ULTRA-READ-AUTHORITY",
            READ_EVENTS_PATH,
        )


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _validate_article_coverage(
    layout: RunLayout,
    loaded: Mapping[str, list[dict[str, object]]],
    issues: dict[str, list[tuple[str, str]]],
    *,
    required_concept_semantic_unit_ids: frozenset[str],
    disk_authority: Mapping[str, object] | None,
) -> str:
    coverage_docs = loaded.get("crossframe.ultra.v82.semantic-coverage", [])
    article_path = _artifact_path(layout, PARTIAL_ARTICLE_PATH)
    if len(coverage_docs) != 1 or not article_path.is_file():
        _issue(
            issues,
            "article-coverage",
            "ULTRA-COVERAGE-MISSING",
            PARTIAL_ARTICLE_PATH,
        )
        return "fail"
    coverage = coverage_docs[0]
    article_bytes = article_path.read_bytes()
    if coverage.get("article_sha256") != sha256_bytes(article_bytes):
        _issue(
            issues,
            "article-coverage",
            "ULTRA-ARTICLE-HASH",
            PARTIAL_ARTICLE_PATH,
        )
    try:
        from .coverage import normalize_excerpt

        article_text = article_bytes.decode("utf-8", errors="strict")
        article = normalize_excerpt(article_text)
    except UnicodeDecodeError:
        article_text = ""
        article = ""
    mappings = coverage.get("mappings", [])
    missing = [
        item
        for item in mappings
        if not isinstance(item, Mapping)
        or not isinstance(item.get("normalized_excerpt"), str)
        or normalize_excerpt(str(item["normalized_excerpt"])) not in article
    ]
    if (
        coverage.get("coverage_complete") is not True
        or coverage.get("coverage_percent") != 100
        or coverage.get("missing_unit_ids") != []
        or missing
    ):
        _issue(
            issues,
            "article-coverage",
            "ULTRA-COVERAGE-MISSING",
            "artifacts/U09-U10-verdict/U11-semantic-coverage.json",
        )
    try:
        from .coverage import build_article_review_artifact

        output_plan = _single_document(
            loaded, "crossframe.ultra.v82.output-plan"
        )
        article_review = _single_document(
            loaded, "crossframe.ultra.v82.article-review"
        )
        generated_at = article_review.get("generated_at")
        if not isinstance(generated_at, str):
            raise ValueError("article review generated_at is unavailable")
        rebuilt_review = build_article_review_artifact(
            article_text,
            output_plan,
            coverage,
            run_id=layout.run_dir.name,
            version_binding=current_version_binding(),
            generated_at=generated_at,
            expected_output_plan_artifact_sha256=sha256_bytes(
                canonical_json_bytes(output_plan)
            ),
            expected_coverage_artifact_sha256=sha256_bytes(
                canonical_json_bytes(coverage)
            ),
        )
        if (
            rebuilt_review != article_review
            or rebuilt_review.get("overall_status") != "mechanical-complete"
        ):
            raise ValueError("U11 article review is not mechanical-complete")
    except Exception:
        _issue(
            issues,
            "article-coverage",
            "ULTRA-ARTICLE-REVIEW-FAILED",
            "artifacts/U09-U10-verdict/U11-article-review.json",
        )

    semantic_status = "fail"
    try:
        from . import semantic_review

        semantic_document = _single_document(
            loaded, "crossframe.ultra.v82.semantic-review"
        )
        output_plan = _single_document(
            loaded, "crossframe.ultra.v82.output-plan"
        )
        evidence = _single_document(
            loaded, "crossframe.ultra.v82.evidence-ledger"
        )
        concept_disposition = _single_document(
            loaded, "crossframe.ultra.v82.concept-disposition"
        )
        intake_path = layout.recovery_dir / "request-intake-authority.json"
        intake_raw = intake_path.read_bytes()
        intake = load_json_object_bytes(intake_raw, source=str(intake_path))
        request_sha256 = intake.get("request_sha256")
        article_review = _single_document(
            loaded, "crossframe.ultra.v82.article-review"
        )
        if (
            disk_authority is None
            or intake_raw != canonical_json_bytes(intake)
            or not isinstance(request_sha256, str)
        ):
            raise ValueError("semantic review request or disk authority is absent")
        active_generation = disk_authority.get("active_generation")
        events = disk_authority.get("events")
        if type(active_generation) is not int or active_generation < 0 or not isinstance(
            events,
            tuple,
        ):
            raise ValueError("semantic review active generation is unavailable")
        u10_events = [
            event
            for event in events
            if isinstance(event, Mapping)
            and event.get("phase_id") == "U10"
            and event.get("status") == "complete"
        ]
        if len(u10_events) != 1:
            raise ValueError("semantic review U10 parent authority is unavailable")
        units = semantic_review.validate_required_concept_units(
            concept_disposition,
            required_concept_semantic_unit_ids,
        )
        action = semantic_review.load_semantic_review_action(
            layout,
            active_generation,
        )
        if action is None:
            raise ValueError("semantic review action authority is absent")
        semantic_review.validate_semantic_review_action(
            layout,
            action,
            request_sha256=request_sha256,
            request_intake_authority_sha256=sha256_bytes(intake_raw),
            u10_parent_event_sha256=str(u10_events[0]["event_sha256"]),
            active_generation=active_generation,
            article_sha256=sha256_bytes(article_bytes),
            output_plan_artifact_sha256=sha256_bytes(
                canonical_json_bytes(output_plan)
            ),
            coverage_artifact_sha256=sha256_bytes(
                canonical_json_bytes(coverage)
            ),
            article_review_artifact_sha256=sha256_bytes(
                canonical_json_bytes(article_review)
            ),
            evidence_ledger_artifact_sha256=sha256_bytes(
                canonical_json_bytes(evidence)
            ),
            concept_disposition_artifact_sha256=sha256_bytes(
                canonical_json_bytes(concept_disposition)
            ),
            required_concept_semantic_unit_ids=units,
        )
        accepted = semantic_review.load_accepted_semantic_review_result(
            layout,
            action,
        )
        if accepted is None:
            raise ValueError("semantic review accepted receipt is absent")
        host_result = semantic_review.load_host_semantic_review_result(
            layout,
            action,
        )
        deterministic_status = (
            "pass"
            if not any(
                records
                for check_id, records in issues.items()
                if check_id != "semantic-tamper-resistance"
            )
            else "fail"
        )
        adversarial_status = (
            "fail" if issues["semantic-tamper-resistance"] else "pass"
        )
        validated_semantic = semantic_review.validate_semantic_review(
            semantic_document,
            action=action,
            accepted_result=accepted,
            host_result=host_result,
            version_binding=current_version_binding(),
            expected_deterministic_status=deterministic_status,
            expected_adversarial_status=adversarial_status,
        )
        if (
            validated_semantic.get("overall_status") != "pass"
            or validated_semantic.get("publication_allowed") is not True
        ):
            raise ValueError("semantic review does not allow publication")
        semantic_status = "pass"
    except Exception:
        _issue(
            issues,
            "article-coverage",
            "ULTRA-SEMANTIC-REVIEW",
            "artifacts/U09-U10-verdict/U11-semantic-review.json",
        )
    return semantic_status


def _validate_logs(
    layout: RunLayout, issues: dict[str, list[tuple[str, str]]]
) -> None:
    if not layout.logs_dir.exists():
        return
    for path in sorted(layout.logs_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            assert_safe_descendant(layout.root, path)
            raw = path.read_bytes()
        except (OSError, TypeError, ValueError):
            _issue(issues, "privacy-logs", "ULTRA-SECRET-LOG", "logs")
            return
        if len(raw) > 4 * 1024 * 1024:
            _issue(issues, "privacy-logs", "ULTRA-SECRET-LOG", "logs")
            return
        text = raw.decode("utf-8", errors="replace")
        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            _issue(
                issues,
                "privacy-logs",
                "ULTRA-SECRET-LOG",
                path.relative_to(layout.run_dir).as_posix(),
            )
            return


def _report_checks(
    issues: Mapping[str, list[tuple[str, str]]]
) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    for check_id in _CHECK_ORDER:
        records = issues[check_id]
        checks.append(
            {
                "validator_id": check_id,
                "status": "fail" if records else "pass",
                "error_codes": sorted({code for code, _ in records}),
                "artifact_refs": sorted({artifact for _, artifact in records}),
            }
        )
    return checks


def _build_validation_layers(
    issues: Mapping[str, list[tuple[str, str]]],
    *,
    semantic_review_status: str,
) -> list[dict[str, object]]:
    if semantic_review_status not in {"pass", "fail"}:
        raise ValueError("semantic review status must be pass or fail")
    adversarial_records = issues["semantic-tamper-resistance"]
    deterministic_records = [
        record
        for check_id, records in issues.items()
        if check_id != "semantic-tamper-resistance"
        for record in records
        if record[0] != "ULTRA-SEMANTIC-REVIEW"
    ]
    records_by_layer = {
        "deterministic": deterministic_records,
        "adversarial": adversarial_records,
        "fresh-semantic": (
            []
            if semantic_review_status == "pass"
            else [
                (
                    "ULTRA-SEMANTIC-REVIEW",
                    "artifacts/U09-U10-verdict/U11-semantic-review.json",
                )
            ]
        ),
    }
    return [
        {
            "layer_id": layer_id,
            "status": "fail" if records_by_layer[layer_id] else "pass",
            "artifact_refs": sorted(
                {artifact for _, artifact in records_by_layer[layer_id]}
            ),
        }
        for layer_id in _VALIDATION_LAYER_IDS
    ]


def validate_run_from_disk(
    repo: Path,
    mode: RunMode,
    run_id: str,
) -> bytes:
    root = _checked_repo(repo)
    if not isinstance(mode, RunMode):
        raise TypeError("mode must be a RunMode")
    layout = build_run_layout(mode, run_id, default_root_policy())
    manifest_path = validation_manifest_path(layout)
    issues: dict[str, list[tuple[str, str]]] = {
        check_id: [] for check_id in _CHECK_ORDER
    }
    try:
        raw_manifest = manifest_path.read_bytes()
        manifest_document = load_json_object(manifest_path)
    except Exception:
        raw_manifest = b""
        manifest_document = {}
    manifest_sha = sha256_bytes(raw_manifest)
    manifest: dict[str, object] | None = None
    loaded: dict[str, list[dict[str, object]]] = {}
    required_concept_semantic_unit_ids = frozenset()
    semantic_review_status = "fail"
    active_generation = 0
    try:
        manifest = validate_artifact_manifest(layout, manifest_path)
    except ArtifactManifestError as error:
        target_check = (
            "publication-boundary"
            if error.error_code == "ULTRA-PREMATURE-PUBLISH"
            else "manifest-integrity"
        )
        _issue(issues, target_check, error.error_code, error.artifact)
    except Exception:
        _issue(
            issues,
            "manifest-integrity",
            "ULTRA-MANIFEST-INVALID",
            "artifacts/ultra-artifact-manifest.json",
        )

    validator_hash = validator_set_sha256(root)
    if manifest is not None:
        if manifest["validator_set_sha256"] != validator_hash:
            _issue(
                issues,
                "manifest-integrity",
                "ULTRA-VALIDATOR-SET-MISMATCH",
                "artifacts/ultra-artifact-manifest.json",
            )
        disk_authority: dict[str, object] | None = None
        try:
            disk_authority = _load_verified_disk_authority(layout, manifest)
            active_generation = int(disk_authority["active_generation"])
        except _AuthorityDAGError as error:
            _issue(
                issues,
                "artifact-integrity",
                "ULTRA-AUTHORITY-DAG",
                "recovery",
            )
            if error.phase_id == "U1":
                _issue(
                    issues,
                    "source-read-coverage",
                    "ULTRA-READ-AUTHORITY",
                    READ_EVENTS_PATH,
                )
        loaded = _load_structured_artifacts(layout, manifest, issues)
        if disk_authority is not None:
            _validate_read_events(root, layout, manifest, disk_authority, issues)
            try:
                required_concept_semantic_unit_ids = _validate_u4_u9_authorities(
                    root,
                    layout,
                    loaded,
                    disk_authority,
                )
                _validate_u10_authority(
                    layout,
                    loaded,
                    disk_authority,
                    required_concept_semantic_unit_ids=(
                        required_concept_semantic_unit_ids
                    ),
                )
            except Exception:
                _issue(
                    issues,
                    "artifact-integrity",
                    "ULTRA-AUTHORITY-DAG",
                    "artifacts/U04-U09",
                )
        _validate_claim_semantics(loaded, issues)
        _validate_world_and_lineage(loaded, issues)
        semantic_review_status = _validate_article_coverage(
            layout,
            loaded,
            issues,
            required_concept_semantic_unit_ids=(
                required_concept_semantic_unit_ids
            ),
            disk_authority=disk_authority,
        )
    _validate_logs(layout, issues)

    checks = _report_checks(issues)
    layers = _build_validation_layers(
        issues,
        semantic_review_status=semantic_review_status,
    )
    status = (
        "pass"
        if all(check["status"] == "pass" for check in checks)
        and all(layer["status"] == "pass" for layer in layers)
        else "fail"
    )
    article_path = _artifact_path(layout, PARTIAL_ARTICLE_PATH)
    article_sha256 = (
        sha256_bytes(article_path.read_bytes())
        if article_path.is_file()
        else "0" * 64
    )
    semantic_documents = loaded.get("crossframe.ultra.v82.semantic-review", [])
    semantic_review_artifact_sha256 = (
        sha256_bytes(canonical_json_bytes(semantic_documents[0]))
        if len(semantic_documents) == 1
        else "0" * 64
    )
    generated_at = manifest_document.get("generated_at")
    if not isinstance(generated_at, str):
        generated_at = "1970-01-01T00:00:00Z"
    report: dict[str, object] = {
        "schema_id": "crossframe.ultra.v82.validator-report",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": current_version_binding(),
        "generated_at": generated_at,
        "content_sha256": "0" * 64,
        "phase_id": "U12",
        "attempt_id": f"fresh-{manifest_sha[:16]}",
        "manifest_sha256": manifest_sha,
        "validator_set_sha256": validator_hash,
        "active_generation": active_generation,
        "article_sha256": article_sha256,
        "semantic_review_artifact_sha256": (
            semantic_review_artifact_sha256
        ),
        "checks": checks,
        "layers": layers,
        "overall_status": status,
        "publication_allowed": status == "pass",
        "validated_at": generated_at,
        "fresh_context": True,
    }
    report["content_sha256"] = compute_artifact_content_sha256(report)
    validate_phase_artifact(
        "ultra-validator-report.schema.json",
        report,
        expected_schema_id="crossframe.ultra.v82.validator-report",
        expected_run_id=run_id,
        expected_version_binding=current_version_binding(),
        expected_phase_id="U12",
    )
    return canonical_json_bytes(report)


def _mode_for_layout(layout: RunLayout) -> RunMode:
    policy = default_root_policy()
    if layout.root == policy.production_root:
        return RunMode.PRODUCTION
    if layout.root == policy.test_root:
        return RunMode.TEST
    raise ValueError("layout root is not one of the fixed root policy authorities")


def _validated_report_bytes(
    layout: RunLayout,
    report_bytes: bytes,
    *,
    attempt_id: str,
    manifest_sha256: str,
    validator_hash: str,
) -> dict[str, object]:
    if not isinstance(report_bytes, bytes):
        raise TypeError("report_bytes must be bytes")
    try:
        report = load_json_object_bytes(
            report_bytes, source="fresh child validator report"
        )
        validate_phase_artifact(
            "ultra-validator-report.schema.json",
            report,
            expected_schema_id="crossframe.ultra.v82.validator-report",
            expected_run_id=layout.run_dir.name,
            expected_version_binding=current_version_binding(),
            expected_phase_id="U12",
        )
    except Exception as error:
        raise ValueError(f"fresh validator report is invalid: {error}") from error
    if report_bytes != canonical_json_bytes(report):
        raise ValueError("fresh validator report bytes are not canonical")
    if report["attempt_id"] != attempt_id:
        raise ValueError("fresh validator report attempt_id differs from parent slot")
    if report["manifest_sha256"] != manifest_sha256:
        raise ValueError("fresh validator report is stale for the current manifest")
    if report["validator_set_sha256"] != validator_hash:
        raise ValueError("fresh validator report uses another validator generation")
    checks_status = (
        "pass"
        if all(check["status"] == "pass" for check in report["checks"])
        else "blocked"
        if any(check["status"] == "blocked" for check in report["checks"])
        else "fail"
    )
    layers = report.get("layers")
    if not isinstance(layers, list) or tuple(
        layer.get("layer_id") if isinstance(layer, Mapping) else None
        for layer in layers
    ) != _VALIDATION_LAYER_IDS:
        raise ValueError("fresh validator report layer contract is invalid")
    layers_pass = all(layer.get("status") == "pass" for layer in layers)
    expected_status = "pass" if checks_status == "pass" and layers_pass else checks_status
    if expected_status == "pass" and not layers_pass:
        expected_status = "fail"
    if report["overall_status"] != expected_status:
        raise ValueError("fresh validator report overall status contradicts its checks")
    if report.get("publication_allowed") is not (expected_status == "pass"):
        raise ValueError("fresh validator report publication contradicts its layers")
    article_path = _artifact_path(layout, PARTIAL_ARTICLE_PATH)
    expected_article_sha256 = (
        sha256_bytes(article_path.read_bytes())
        if article_path.is_file()
        else "0" * 64
    )
    if report.get("article_sha256") != expected_article_sha256:
        raise ValueError("fresh validator report is stale for the current article")
    semantic_path = _artifact_path(
        layout,
        "artifacts/U09-U10-verdict/U11-semantic-review.json",
    )
    expected_semantic_sha256 = (
        sha256_bytes(semantic_path.read_bytes())
        if semantic_path.is_file()
        else "0" * 64
    )
    if report.get("semantic_review_artifact_sha256") != expected_semantic_sha256:
        raise ValueError(
            "fresh validator report is stale for the semantic review artifact"
        )
    if semantic_path.is_file():
        semantic_document = load_json_object(semantic_path)
        if report.get("active_generation") != semantic_document.get(
            "active_generation"
        ):
            raise ValueError(
                "fresh validator report uses another active recovery generation"
            )
    return report


def _require_validation_commit_authority(
    layout: RunLayout,
    lease: Lease,
) -> None:
    if load_cancel_intent(layout) is not None:
        raise CancelledRunError("cancel intent blocks validation commit")
    require_run_lease_owner(layout, lease)


def commit_validation_attempt(
    layout: RunLayout,
    *,
    attempt_id: str,
    report_bytes: bytes,
    expected_manifest_sha256: str,
    expected_validator_set_sha256: str,
    lease: Lease,
) -> dict[str, object]:
    if not isinstance(layout, RunLayout):
        raise TypeError("layout must be a RunLayout")
    if not isinstance(attempt_id, str) or re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", attempt_id
    ) is None:
        raise ValueError("attempt_id is not a safe identifier")
    for value, name in (
        (expected_manifest_sha256, "expected_manifest_sha256"),
        (expected_validator_set_sha256, "expected_validator_set_sha256"),
    ):
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"{name} must be a SHA-256 digest")

    _require_validation_commit_authority(layout, lease)

    manifest_path = validation_manifest_path(layout)
    manifest = validate_artifact_manifest(layout, manifest_path)
    current_manifest_sha = sha256_bytes(manifest_path.read_bytes())
    if current_manifest_sha != expected_manifest_sha256:
        raise ValueError("stale validator report: manifest generation changed")
    current_validator_hash = validator_set_sha256(_repo_root())
    if (
        manifest["validator_set_sha256"] != expected_validator_set_sha256
        or current_validator_hash != expected_validator_set_sha256
    ):
        raise ValueError("validator-set generation changed before report commit")
    report = _validated_report_bytes(
        layout,
        report_bytes,
        attempt_id=attempt_id,
        manifest_sha256=current_manifest_sha,
        validator_hash=current_validator_hash,
    )
    fresh_bytes = validate_run_from_disk(
        _repo_root(), _mode_for_layout(layout), layout.run_dir.name
    )
    if fresh_bytes != report_bytes:
        raise ValueError("parent report bytes differ from fresh disk validation")
    _require_validation_commit_authority(layout, lease)

    attempt_path = (
        layout.validation_attempts_dir
        / attempt_id
        / "ultra-validator-report.json"
    )
    current_path = layout.validation_current_dir / "ultra-validator-report.json"
    for path in (attempt_path, current_path):
        assert_safe_descendant(layout.root, path)
    if attempt_path.exists() and attempt_path.read_bytes() != report_bytes:
        raise ValueError("validation attempt slot already contains different bytes")
    _require_validation_commit_authority(layout, lease)
    atomic_write_bytes(attempt_path, report_bytes)
    if attempt_path.read_bytes() != report_bytes:
        raise ValueError("validation attempt changed during durable write")
    _validated_report_bytes(
        layout,
        attempt_path.read_bytes(),
        attempt_id=attempt_id,
        manifest_sha256=current_manifest_sha,
        validator_hash=current_validator_hash,
    )
    _require_validation_commit_authority(layout, lease)
    atomic_write_bytes(current_path, report_bytes)
    if current_path.read_bytes() != report_bytes:
        raise ValueError("validation/current changed during atomic replacement")
    return copy.deepcopy(report)
