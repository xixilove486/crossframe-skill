from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit

from promax_runtime.claim_path import validate_claim_path_saturation
from promax_runtime.concept_closure import validate_concept_closure
from promax_runtime.deliverables import (
    validate_continuation_lineage,
    validate_final_chat,
    validate_output_bundle,
)
from promax_runtime.jsonio import canonical_json_bytes, load_json_bytes, sha256_json
from promax_runtime.pollution import validate_version_isolation
from promax_runtime.position import (
    selection_review_basis_sha256,
    validate_position_semantics,
    validate_recommendation_semantics,
)
from promax_runtime.repair import build_repair_plan, normalize_machine_failures
from promax_runtime.retrieval import validate_retrieval_saturation
from promax_runtime.safe_files import read_stable_regular_file
from promax_runtime.schemas import validate_instance
from promax_runtime.source_integrity import (
    V8_SOURCE_SNAPSHOT_SHA256,
    build_source_snapshot,
    validate_read_event_coverage,
)
from promax_runtime.state_machine import PHASES, RunBinding, validate_phase_history
from promax_runtime.validation import (
    MachineValidationError,
    build_machine_failure,
    build_validator_report,
    validate_validator_report_freshness,
)


CHECKER_VERSION = "crossframe-promax-artifact-checker/1"
REPORT_ARTIFACT = "promax-validator-report.json"
REPAIR_ARTIFACT = "promax-repair-plan.json"
FINAL_CHAT_ARTIFACT = "promax-final-chat.json"

# These maps are the sole workspace path vocabulary used by the checker.  The
# report is deliberately absent: output bytes may never be used as validation
# input in the same invocation.
JSON_ARTIFACTS = {
    "run_contract": "promax-run-contract.json",
    "source_snapshot": "promax-source-snapshot.json",
    "local_world_model": "promax-local-world-model.locked.json",
    "concept_disposition": "promax-concept-disposition-ledger.json",
    "claim_path_graph": "promax-claim-path-graph.json",
    "retrieval_ledger": "promax-retrieval-ledger.json",
    "red_team_report": "promax-red-team-report.json",
    "position": "promax-position.locked.json",
    "recommendation": "promax-recommendation.locked.json",
    "output_plan": "promax-output-plan.locked.json",
    "manifest": "promax-artifact-manifest.json",
    "continuation_ledger": "promax-continuation-ledger.json",
}
JSONL_ARTIFACTS = {
    "read_events": "promax-read-events.jsonl",
    "phase_events": "promax-phase-events.jsonl",
}
TEXT_ARTIFACTS = {
    "worldview_capsule": "promax-worldview-capsule.locked.md",
    "dossier": "promax-dossier.md",
    "concept_atlas": "promax-concept-atlas.md",
    "case_and_countercase": "promax-case-and-countercase.md",
    "essay": "promax-essay.md",
    "continuation_index": "promax-continuation-index.md",
}

_SCHEMAS = {
    "run_contract": "promax-run-contract.schema.json",
    "source_snapshot": "promax-source-snapshot.schema.json",
    "local_world_model": "promax-local-world-model.schema.json",
    "concept_disposition": "promax-concept-disposition.schema.json",
    "claim_path_graph": "promax-claim-path-graph.schema.json",
    "retrieval_ledger": "promax-retrieval-ledger.schema.json",
    "red_team_report": "promax-red-team-report.schema.json",
    "position": "promax-position.schema.json",
    "recommendation": "promax-recommendation.schema.json",
    "output_plan": "promax-output-plan.schema.json",
    "manifest": "promax-artifact-manifest.schema.json",
    "continuation_ledger": "promax-continuation-ledger.schema.json",
}

_PHASE_BY_KEY = {
    "run_contract": "P0",
    "source_snapshot": "P1",
    "read_events": "P2",
    "worldview_capsule": "P3",
    "local_world_model": "P3",
    "concept_disposition": "P4",
    "claim_path_graph": "P5",
    "retrieval_ledger": "P6",
    "red_team_report": "P7",
    "position": "P8",
    "recommendation": "P8",
    "output_plan": "P9",
    "dossier": "P10",
    "concept_atlas": "P10",
    "case_and_countercase": "P10",
    "essay": "P10",
    "continuation_ledger": "P10",
    "continuation_index": "P10",
    "manifest": "P10",
    "phase_events": "P0",
    "final_chat": "P11",
}

_CAPABILITY_GAP_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
_TEST_FIXTURE_RUN_ID_RE = re.compile(r"^promax-fixture(?:-|$)", re.IGNORECASE)
_MANIFEST_CURRENT_ARTIFACTS = {
    JSON_ARTIFACTS["source_snapshot"],
    JSONL_ARTIFACTS["read_events"],
    TEXT_ARTIFACTS["worldview_capsule"],
    JSON_ARTIFACTS["local_world_model"],
    JSON_ARTIFACTS["concept_disposition"],
    JSON_ARTIFACTS["claim_path_graph"],
    JSON_ARTIFACTS["retrieval_ledger"],
    JSON_ARTIFACTS["red_team_report"],
    JSON_ARTIFACTS["position"],
    JSON_ARTIFACTS["recommendation"],
    JSON_ARTIFACTS["output_plan"],
    TEXT_ARTIFACTS["dossier"],
    TEXT_ARTIFACTS["concept_atlas"],
    TEXT_ARTIFACTS["case_and_countercase"],
    TEXT_ARTIFACTS["essay"],
    TEXT_ARTIFACTS["continuation_index"],
}
_MANIFEST_FORBIDDEN_ARTIFACTS = {
    JSON_ARTIFACTS["run_contract"],
    JSON_ARTIFACTS["manifest"],
    JSON_ARTIFACTS["continuation_ledger"],
    JSONL_ARTIFACTS["phase_events"],
    REPORT_ARTIFACT,
    REPAIR_ARTIFACT,
    FINAL_CHAT_ARTIFACT,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def machine_failure(
    *,
    error_type: str,
    artifact: str,
    affected_phase: str,
    repair_action: str,
) -> dict[str, object]:
    """Create the one permitted public failure shape."""

    return build_machine_failure(
        error_type=error_type,
        artifact=artifact,
        affected_phase=affected_phase,
        repair_action=repair_action,
    )


def classify_outcome(
    mode: str,
    *,
    failures: Sequence[Mapping[str, object]],
    capability_gaps: Sequence[str],
) -> dict[str, str]:
    """Apply the strict complete/artifact-run downgrade boundary."""

    if failures:
        return {
            "overall_status": "fail",
            "completion_status": "promax-artifact-incomplete:validation-failed",
        }
    normalized_gaps = sorted({str(item).strip() for item in capability_gaps if str(item).strip()})
    if any(_CAPABILITY_GAP_RE.fullmatch(item) is None for item in normalized_gaps):
        raise ValueError("capability gap reasons must be stable lowercase identifiers")
    if normalized_gaps:
        if mode == "promax-artifact-run":
            return {
                "overall_status": "blocked",
                "completion_status": "promax-artifact-incomplete:" + "+".join(normalized_gaps),
            }
        return {
            "overall_status": "fail",
            "completion_status": "promax-artifact-incomplete:capability-gap",
        }
    return {"overall_status": "pass", "completion_status": mode}


def _trusted_root(path: Path | str, *, label: str) -> Path:
    try:
        root = Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(f"{label} does not resolve to an existing directory") from error
    if not root.is_dir():
        raise ValueError(f"{label} must be a directory: {root}")
    return root


def _load_jsonl_bytes(raw: bytes, *, source: str) -> list[dict[str, object]]:
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        raise ValueError(f"JSONL document must end with a newline: {source}")
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(raw[:-1].split(b"\n"), start=1):
        if not line.strip():
            raise ValueError(f"blank JSONL record at {source}:{line_number}")
        value = load_json_bytes(line, source=f"{source}:{line_number}")
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record must be an object at {source}:{line_number}")
        records.append(value)
    return records


def _read_fixed(
    workspace: Path,
    name: str,
    *,
    kind: str,
) -> tuple[object, Path]:
    if Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"checker artifact name is not fixed and local: {name!r}")
    path = workspace / name
    raw = read_stable_regular_file(path, within_root=workspace)
    if kind == "json":
        return load_json_bytes(raw, source=str(path)), path
    if kind == "jsonl":
        return _load_jsonl_bytes(raw, source=str(path)), path
    try:
        return raw.decode("utf-8", errors="strict"), path
    except UnicodeError as error:
        raise ValueError(f"artifact is not strict UTF-8 text: {name}") from error


def _failure_for(
    key: str,
    *,
    error_type: str,
    repair_action: str,
) -> dict[str, object]:
    if key == "final_chat":
        artifact = FINAL_CHAT_ARTIFACT
    else:
        artifact = (
            JSON_ARTIFACTS.get(key)
            or JSONL_ARTIFACTS.get(key)
            or TEXT_ARTIFACTS.get(key)
        )
    if artifact is None:
        raise ValueError(f"unknown checker artifact key: {key}")
    return machine_failure(
        error_type=error_type,
        artifact=artifact,
        affected_phase=_PHASE_BY_KEY[key],
        repair_action=repair_action,
    )


def _append_failure(
    failures: list[dict[str, object]],
    diagnostics: list[str],
    *,
    key: str,
    error_type: str,
    repair_action: str,
    error: BaseException,
    preserve_machine_failure: bool = True,
) -> None:
    if preserve_machine_failure and isinstance(error, MachineValidationError):
        failure = error.failure
    else:
        failure = _failure_for(
            key,
            error_type=error_type,
            repair_action=repair_action,
        )
    fingerprint = tuple(
        str(failure[field]) for field in ("error_type", "artifact", "affected_phase")
    )
    if not any(
        tuple(str(existing[field]) for field in ("error_type", "artifact", "affected_phase"))
        == fingerprint
        for existing in failures
    ):
        failures.append(failure)
    diagnostics.append(f"{failure['error_type']}:{failure['artifact']}:{error}")


def _semantic_error_type(gate: str, error: BaseException) -> tuple[str, str]:
    """Map a domain validator's precise complaint to a stable repair code."""

    message = str(error).casefold()
    if gate == "retrieval":
        if "direction" in message or "lacks retrieval" in message:
            return "retrieval_direction_missing", "retrieval_ledger"
        if any(token in message for token in ("independent", "duplicate source", "duplicate url")):
            return "source_independence_invalid", "retrieval_ledger"
        return "retrieval_saturation_incomplete", "retrieval_ledger"
    if gate == "position":
        if any(token in message for token in ("authoriz", "授权")):
            return "authorization_ceiling_exceeded", "position"
        if any(token in message for token in ("stability", "drift", "evidence-bound")):
            return "stance_stability_failed", "position"
        return "position_stability_failed", "position"
    if gate == "recommendation":
        if any(
            token in message
            for token in (
                "cannot grant recommendation authorization",
                "cannot self-grant",
                "leaks real-world authorization",
                "不能授权",
                "已授权",
            )
        ):
            return "authorization_ceiling_exceeded", "recommendation"
        return "recommendation_option_set_incomplete", "recommendation"
    if gate == "output":
        if "continuation" in message and any(
            token in message for token in ("parent", "manifest", "sequence", "resume")
        ):
            return "continuation_parent_mismatch", "continuation_ledger"
        if any(
            token in message
            for token in (
                "unsupported type",
                "similar example",
                "failure example",
                "case heading",
                "case header",
                "typed example",
                "example type",
            )
        ):
            return "mechanism_example_coverage_invalid", "case_and_countercase"
        if any(
            token in message
            for token in (
                "does not explain",
                "omits the applied",
                "semantic",
                "definition",
                "misuse",
                "neighbor",
            )
        ):
            return "semantic_content_missing", "output_plan"
        if any(token in message for token in ("manifest", "stale artifact")):
            for key in ("dossier", "concept_atlas", "case_and_countercase", "essay"):
                if TEXT_ARTIFACTS[key].casefold() in message:
                    return "manifest_stale", key
            return "manifest_stale", "manifest"
        return "output_semantic_coverage_invalid", "output_plan"
    raise ValueError(f"unknown semantic gate: {gate}")


def _schema_error_type(key: str, error: BaseException) -> str:
    if key == "recommendation":
        return "recommendation_option_set_incomplete"
    if key == "retrieval_ledger" and "too short" in str(error).casefold():
        return "retrieval_direction_missing"
    return "schema_validation_failed"


def _ordered_failures(
    failures: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if not failures:
        return []
    normalized = normalize_machine_failures(failures)
    priority = {
        "schema_validation_failed": 0,
        "source_snapshot_content_mismatch": 1,
        "source_read_coverage_invalid": 1,
        "source_independence_invalid": 1,
        "retrieval_direction_missing": 1,
        "recommendation_option_set_incomplete": 1,
        "stance_stability_failed": 1,
        "authorization_ceiling_exceeded": 1,
        "semantic_content_missing": 1,
        "mechanism_example_coverage_invalid": 1,
        "continuation_parent_mismatch": 1,
        "manifest_stale": 1,
    }
    return sorted(
        normalized,
        key=lambda failure: (
            PHASES.index(str(failure["affected_phase"])),
            priority.get(str(failure["error_type"]), 5),
            str(failure["artifact"]),
            str(failure["error_type"]),
        ),
    )


def _validate_source_independence(retrieval: Mapping[str, object]) -> None:
    """Reject same-origin evidence relabelled as independent by URL variation."""

    entries = retrieval.get("entries")
    if not isinstance(entries, list):
        raise ValueError("retrieval entries must be an array")
    origins: dict[tuple[str, str], str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("sources"), list):
            continue
        for source in entry["sources"]:
            if not isinstance(source, Mapping):
                continue
            url = source.get("url")
            publisher = source.get("publisher")
            if not isinstance(url, str) or not isinstance(publisher, str):
                continue
            host = (urlsplit(url).hostname or "").casefold()
            identity = (host, publisher.strip().casefold())
            if not host or not identity[1]:
                continue
            prior = origins.get(identity)
            if prior is not None and source.get("duplicate_relation") == "independent":
                raise ValueError(
                    f"same origin sources are falsely independent: {prior!r}, {url!r}"
                )
            origins[identity] = url


def _evidence_basis_sha256(
    run_contract: Mapping[str, object],
    local_world_model: Mapping[str, object],
    retrieval_ledger: Mapping[str, object],
) -> str:
    """Bind a stance probe to the evidence artifacts the checker actually read."""

    request_sha256 = run_contract.get("request_sha256")
    source_snapshot_sha256 = run_contract.get("source_snapshot_sha256")
    if not isinstance(request_sha256, str) or not isinstance(
        source_snapshot_sha256, str
    ):
        raise ValueError("stability evidence-basis lacks immutable run bindings")
    return sha256_json(
        {
            "request_sha256": request_sha256,
            "source_snapshot_sha256": source_snapshot_sha256,
            "local_world_model_sha256": sha256_json(local_world_model),
            "retrieval_ledger_sha256": sha256_json(retrieval_ledger),
        }
    )


def _validate_stability_evidence_binding(
    run_contract: Mapping[str, object],
    local_world_model: Mapping[str, object],
    retrieval_ledger: Mapping[str, object],
    red_team_report: Mapping[str, object],
) -> str:
    """Reject self-reported prompt or evidence hashes not tied to run artifacts."""

    expected_basis = _evidence_basis_sha256(
        run_contract,
        local_world_model,
        retrieval_ledger,
    )
    checks = red_team_report.get("stability_checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("stability evidence-basis has no closed probe records")
    for index, check in enumerate(checks):
        if not isinstance(check, Mapping):
            raise ValueError(f"stability check {index} is not structured")
        pro_prompt = check.get("pro_prompt")
        anti_prompt = check.get("anti_prompt")
        if (
            not isinstance(pro_prompt, str)
            or not pro_prompt.strip()
            or not isinstance(anti_prompt, str)
            or not anti_prompt.strip()
        ):
            raise ValueError(f"stability check {index} lacks actual prompt text")
        if pro_prompt == anti_prompt:
            raise ValueError(f"stability check {index} reuses one prompt on both sides")
        if check.get("pro_prompt_sha256") != sha256_json(pro_prompt):
            raise ValueError(f"stability check {index} pro prompt hash is not derived")
        if check.get("anti_prompt_sha256") != sha256_json(anti_prompt):
            raise ValueError(f"stability check {index} anti prompt hash is not derived")
        for side in ("before", "after"):
            if check.get(f"evidence_basis_sha256_{side}") != expected_basis:
                raise ValueError(
                    f"stability {side} evidence-basis is not bound to actual run artifacts"
                )
    return expected_basis


def _validate_stability_ranking_binding(
    run_contract: Mapping[str, object],
    red_team_report: Mapping[str, object],
    recommendation: Mapping[str, object],
    retrieval_ledger: Mapping[str, object] | None = None,
) -> None:
    required = run_contract.get("recommendation_required")
    checks = red_team_report.get("stability_checks")
    if type(required) is not bool or not isinstance(checks, list) or not checks:
        raise ValueError("stability ranking binding lacks a closed run/check contract")
    if required:
        normative_selection_basis_sha256 = selection_review_basis_sha256(
            recommendation
        )
        ranking = recommendation.get("ranking")
        option_kind_ranking = recommendation.get("option_kind_ranking")
        option_semantic_ranking = recommendation.get("option_semantic_ranking")
        if not isinstance(ranking, list) or not ranking:
            raise ValueError("required recommendation has no ranking to bind")
        options = recommendation.get("options")
        if not isinstance(options, list) or not options:
            raise ValueError("required recommendation has no concrete options to bind")
        options_by_id = {
            option.get("option_id"): option
            for option in options
            if isinstance(option, Mapping)
            and isinstance(option.get("option_id"), str)
        }
        if len(options_by_id) != len(options):
            raise ValueError("recommendation concrete option IDs are not closed")
        for check in checks:
            if not isinstance(check, Mapping):
                raise ValueError("stability ranking check is not structured")
            for side in ("before", "after"):
                ids = check.get(f"option_ranking_{side}")
                if (
                    not isinstance(ids, list)
                    or len(ids) != len(options_by_id)
                    or set(ids) != set(options_by_id)
                ):
                    raise ValueError(
                        f"stability {side} ranking is not a permutation of concrete options"
                    )
                expected_option_kinds = [
                    options_by_id[option_id].get("option_kind") for option_id in ids
                ]
                expected_semantics = [
                    sha256_json(
                        {
                            key: copy.deepcopy(value)
                            for key, value in options_by_id[option_id].items()
                            if key != "option_id"
                        }
                    )
                    for option_id in ids
                ]
                if (
                    check.get(f"option_kind_ranking_{side}")
                    != expected_option_kinds
                    or check.get(f"option_semantic_ranking_{side}")
                    != expected_semantics
                ):
                    raise ValueError(
                        f"stability {side} ranking projections are not derived from concrete options"
                    )
            if (
                check.get("option_ranking_after") != ranking
                or check.get("option_kind_ranking_after") != option_kind_ranking
                or check.get("option_semantic_ranking_after") != option_semantic_ranking
            ):
                raise ValueError(
                    "same-evidence stability ranking projections differ from the locked recommendation"
                )
            if any(
                check.get(
                    f"normative_selection_basis_sha256_{side}"
                )
                != normative_selection_basis_sha256
                for side in ("before", "after")
            ):
                raise ValueError(
                    "same-evidence normative selection basis differs from the locked recommendation"
                )
        if recommendation.get("ranking_policy") == "evidence_bound_case_comparison":
            entries = (
                retrieval_ledger.get("entries")
                if isinstance(retrieval_ledger, Mapping)
                else None
            )
            if not isinstance(entries, list):
                raise ValueError("evidence-bound ranking lacks a retrieval ledger")
            retrieval_ids = {
                entry.get("retrieval_id")
                for entry in entries
                if isinstance(entry, Mapping)
                and isinstance(entry.get("retrieval_id"), str)
            }
            evidence_refs = recommendation.get("ranking_evidence_refs")
            if (
                not isinstance(evidence_refs, list)
                or not evidence_refs
                or any(ref not in retrieval_ids for ref in evidence_refs)
            ):
                raise ValueError(
                    "evidence-bound ranking references do not resolve to retrieval entries"
                )
            wrapper = recommendation.get("selection_review_wrapper")
            supports = (
                wrapper.get("ranking_support")
                if isinstance(wrapper, Mapping)
                else None
            )
            if not isinstance(supports, list) or not supports:
                raise ValueError(
                    "evidence-bound ranking lacks a structured ranking-support matrix"
                )
            support_refs: set[str] = set()
            for support in supports:
                if not isinstance(support, Mapping):
                    raise ValueError(
                        "evidence-bound ranking-support matrix contains an unstructured cell"
                    )
                refs = support.get("evidence_refs")
                if (
                    not isinstance(refs, list)
                    or not refs
                    or any(ref not in retrieval_ids for ref in refs)
                ):
                    raise ValueError(
                        "evidence-bound ranking-support evidence does not resolve to retrieval entries"
                    )
                support_refs.update(
                    ref for ref in refs if isinstance(ref, str)
                )
            if support_refs != set(evidence_refs):
                raise ValueError(
                    "ranking evidence is not closed over the ranking-support matrix"
                )
    else:
        not_requested_basis_sha256 = sha256_json({"status": "not_requested"})
        for check in checks:
            if not isinstance(check, Mapping) or any(
                check.get(field) != []
                for field in (
                    "option_ranking_before",
                    "option_ranking_after",
                    "option_kind_ranking_before",
                    "option_kind_ranking_after",
                    "option_semantic_ranking_before",
                    "option_semantic_ranking_after",
                )
            ):
                raise ValueError(
                    "not-requested recommendation stability rankings must remain empty"
                )
            if any(
                check.get(
                    f"normative_selection_basis_sha256_{side}"
                )
                != not_requested_basis_sha256
                for side in ("before", "after")
            ):
                raise ValueError(
                    "not-requested recommendation stability selection basis is not closed"
                )


def _load_concept_registry(repo: Path) -> dict[str, object]:
    references = repo / "skills" / "crossframe-promax" / "references"
    path = references / "concept-registry" / "v8-concept-registry.json"
    raw = read_stable_regular_file(path, within_root=references)
    value = load_json_bytes(raw, source=str(path))
    if not isinstance(value, dict):
        raise ValueError("canonical v8 concept registry must be an object")
    validate_instance("v8-concept-registry.schema.json", value)
    return value


def _validate_manifest_inventory_policy(manifest: Mapping[str, object]) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("manifest artifacts must be an array")
    all_paths: list[str] = []
    current_paths: set[str] = set()
    for record in artifacts:
        if not isinstance(record, Mapping) or not isinstance(record.get("path"), str):
            raise ValueError("manifest artifact records must have fixed text paths")
        path = str(record["path"])
        all_paths.append(path)
        if record.get("status") == "current":
            current_paths.add(path)
    forbidden = sorted(set(all_paths) & _MANIFEST_FORBIDDEN_ARTIFACTS)
    if forbidden:
        raise ValueError(
            f"manifest creates a control-plane/output identity cycle: {forbidden!r}"
        )
    if current_paths != _MANIFEST_CURRENT_ARTIFACTS:
        missing = sorted(_MANIFEST_CURRENT_ARTIFACTS - current_paths)
        extra = sorted(current_paths - _MANIFEST_CURRENT_ARTIFACTS)
        raise ValueError(
            f"manifest current analysis inventory is not closed; missing={missing!r}, extra={extra!r}"
        )


def _next_validation_attempt(
    workspace: Path,
    run_contract: Mapping[str, object],
    manifest: Mapping[str, object],
    validator_versions: Mapping[str, str],
) -> int:
    report_path = workspace / REPORT_ARTIFACT
    if not report_path.exists() and not report_path.is_symlink():
        return 1
    value, _ = _read_fixed(workspace, REPORT_ARTIFACT, kind="json")
    if not isinstance(value, Mapping):
        raise ValueError("existing validator report must be a JSON object")
    attempt = value.get("validation_attempt")
    if type(attempt) is not int or attempt < 1:
        raise ValueError("existing validator report has no valid validation_attempt")
    validate_validator_report_freshness(
        value,
        run_contract,
        manifest,
        validator_versions=validator_versions,
        expected_validation_attempt=attempt,
        run_dir=workspace,
    )
    return attempt + 1


def _preflight_failure_anchor(
    run_contract: Mapping[str, object],
    failures: Sequence[Mapping[str, object]],
    *,
    validated_at: str,
) -> dict[str, object]:
    body: dict[str, object] = {
        "anchor_type": "crossframe.promax.v8.preflight-failure",
        "run_id": run_contract.get("run_id"),
        "source_snapshot_sha256": run_contract.get("source_snapshot_sha256"),
        "failures": [dict(item) for item in failures],
        "validated_at": validated_at,
    }
    return {**body, "report_sha256": sha256_json(body)}


def _validator_checks(
    run_contract: Mapping[str, object],
    failures: Sequence[Mapping[str, object]],
    capability_gaps: Sequence[str],
) -> tuple[dict[str, str], list[dict[str, object]]]:
    capabilities = run_contract.get("capabilities")
    validators = capabilities.get("validators") if isinstance(capabilities, Mapping) else None
    raw_ids = validators.get("validator_ids") if isinstance(validators, Mapping) else None
    if not isinstance(raw_ids, list) or not raw_ids or any(
        not isinstance(item, str) or not item for item in raw_ids
    ):
        raise ValueError("run contract has no executable frozen validator set")
    versions = {validator_id: CHECKER_VERSION for validator_id in raw_ids}
    codes: dict[str, list[str]] = {validator_id: [] for validator_id in raw_ids}

    checked_paths = {
        "schema": sorted(JSON_ARTIFACTS.values()),
        "source-integrity": [
            JSON_ARTIFACTS["source_snapshot"],
            JSONL_ARTIFACTS["read_events"],
        ],
        "version-isolation": ["skills/crossframe-promax/SKILL.md"],
        "concept-closure": [JSON_ARTIFACTS["concept_disposition"]],
        "claim-path": [JSON_ARTIFACTS["claim_path_graph"]],
        "retrieval": [JSON_ARTIFACTS["retrieval_ledger"]],
        "position": [
            JSON_ARTIFACTS["red_team_report"],
            JSON_ARTIFACTS["position"],
            JSON_ARTIFACTS["recommendation"],
        ],
        "output": [
            JSON_ARTIFACTS["output_plan"],
            TEXT_ARTIFACTS["dossier"],
            TEXT_ARTIFACTS["concept_atlas"],
            TEXT_ARTIFACTS["case_and_countercase"],
            TEXT_ARTIFACTS["essay"],
        ],
        "manifest": [JSON_ARTIFACTS["manifest"]],
        "state-machine": [JSONL_ARTIFACTS["phase_events"]],
        "continuation": [
            JSON_ARTIFACTS["continuation_ledger"],
            TEXT_ARTIFACTS["continuation_index"],
        ],
    }

    def choose(failure: Mapping[str, object]) -> str:
        error_type = str(failure.get("error_type", ""))
        artifact = str(failure.get("artifact", ""))
        if "schema" in error_type and "schema" in codes:
            return "schema"
        preferred = None
        if error_type == "version_pollution_detected":
            preferred = "version-isolation"
        elif artifact in {JSON_ARTIFACTS["source_snapshot"], JSONL_ARTIFACTS["read_events"]}:
            preferred = "source-integrity"
        elif artifact == JSON_ARTIFACTS["concept_disposition"]:
            preferred = "concept-closure"
        elif artifact == JSON_ARTIFACTS["claim_path_graph"]:
            preferred = "claim-path"
        elif artifact == JSON_ARTIFACTS["retrieval_ledger"]:
            preferred = "retrieval"
        elif artifact in {
            JSON_ARTIFACTS["red_team_report"],
            JSON_ARTIFACTS["position"],
            JSON_ARTIFACTS["recommendation"],
        }:
            preferred = "position"
        elif artifact == JSON_ARTIFACTS["manifest"]:
            preferred = "manifest"
        elif artifact == JSONL_ARTIFACTS["phase_events"]:
            preferred = "state-machine"
        elif artifact in {
            JSON_ARTIFACTS["continuation_ledger"],
            TEXT_ARTIFACTS["continuation_index"],
        }:
            preferred = "continuation"
        elif artifact in {
            JSON_ARTIFACTS["output_plan"],
            TEXT_ARTIFACTS["dossier"],
            TEXT_ARTIFACTS["concept_atlas"],
            TEXT_ARTIFACTS["case_and_countercase"],
            TEXT_ARTIFACTS["essay"],
        }:
            preferred = "output"
        if preferred in codes:
            return str(preferred)
        if "source-integrity" in codes and artifact in {
            JSON_ARTIFACTS["source_snapshot"],
            JSONL_ARTIFACTS["read_events"],
        }:
            return "source-integrity"
        if "state-machine" in codes:
            return "state-machine"
        return raw_ids[0]

    for failure in failures:
        target = choose(failure)
        code = str(failure["error_type"])
        if code not in codes[target]:
            codes[target].append(code)
    if capability_gaps and not failures:
        target = "retrieval" if "retrieval" in codes else raw_ids[0]
        codes[target].extend(
            code for code in sorted(set(capability_gaps)) if code not in codes[target]
        )

    checks: list[dict[str, object]] = []
    for validator_id in raw_ids:
        failure_codes = codes[validator_id]
        status = "fail" if failures and failure_codes else "blocked" if failure_codes else "pass"
        checks.append(
            {
                "validator_id": validator_id,
                "status": status,
                "checked_artifact_paths": checked_paths.get(validator_id, []),
                "failure_codes": failure_codes,
            }
        )
    if failures and not any(check["status"] == "fail" for check in checks):
        checks[0]["status"] = "fail"
        checks[0]["failure_codes"] = sorted(
            {str(item["error_type"]) for item in failures}
        )
    return versions, checks


def write_report_atomic(
    report_path: Path | str,
    report: Mapping[str, object],
    *,
    workspace: Path | str,
    input_paths: Iterable[Path | str],
) -> None:
    """Atomically publish a report whose inode is isolated from every input."""

    root = _trusted_root(workspace, label="workspace")
    target = Path(report_path)
    if not target.is_absolute():
        raise ValueError("validator report output path must be absolute")
    if target.parent.resolve(strict=True) != root or target.name != REPORT_ARTIFACT:
        raise ValueError("validator report must use the fixed workspace output path")

    input_identities: set[tuple[int, int]] = set()
    for raw_path in input_paths:
        path = Path(raw_path)
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        info = path.stat()
        if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"validator input identity is unsafe: {path}")
        input_identities.add((info.st_dev, info.st_ino))

    if target.exists() or target.is_symlink():
        info = target.lstat()
        if target.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("existing validator report output identity is unsafe")
        if (info.st_dev, info.st_ino) in input_identities:
            raise ValueError("validator report output aliases a validation input")

    payload = canonical_json_bytes(dict(report)) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".promax-validator-report.", suffix=".tmp", dir=root
    )
    temporary = Path(temporary_name)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) in input_identities:
            raise ValueError("temporary report output aliases a validation input")
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def validate_workspace(
    workspace: Path | str,
    *,
    repo: Path | str,
    final_chat: bool = False,
    write_report: bool = False,
    validated_at: str | None = None,
    allow_test_fixture: bool = False,
) -> dict[str, object]:
    """Run all independent ProMax hard gates and aggregate repairable failures."""

    root = _trusted_root(workspace, label="workspace")
    repo_root = _trusted_root(repo, label="repo")
    stamp = validated_at or _utc_now()
    documents: dict[str, object] = {}
    texts: dict[str, str] = {}
    input_paths: list[Path] = []
    failures: list[dict[str, object]] = []
    diagnostics: list[str] = []
    anomalies: list[str] = []
    capability_gaps: list[str] = []

    for key, name in JSON_ARTIFACTS.items():
        try:
            value, path = _read_fixed(root, name, kind="json")
            if not isinstance(value, dict):
                raise ValueError("top-level JSON value must be an object")
            documents[key] = value
            input_paths.append(path)
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key=key,
                error_type="artifact_missing_or_unreadable",
                repair_action="rebuild_artifact_as_safe_regular_file_and_revalidate",
                error=error,
            )

    manifest = documents.get("manifest")
    if isinstance(manifest, Mapping):
        try:
            _validate_manifest_inventory_policy(manifest)
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="manifest",
                error_type="manifest_stale",
                repair_action="regenerate_closed_analysis_manifest_and_revalidate",
                error=error,
            )
    for key, name in JSONL_ARTIFACTS.items():
        try:
            value, path = _read_fixed(root, name, kind="jsonl")
            documents[key] = value
            input_paths.append(path)
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key=key,
                error_type="artifact_missing_or_unreadable",
                repair_action="rebuild_append_only_event_log_and_revalidate",
                error=error,
            )
    for key, name in TEXT_ARTIFACTS.items():
        try:
            value, path = _read_fixed(root, name, kind="text")
            assert isinstance(value, str)
            texts[key] = value
            input_paths.append(path)
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key=key,
                error_type="artifact_missing_or_unreadable",
                repair_action="rebuild_artifact_as_strict_utf8_and_revalidate",
                error=error,
            )
    if final_chat:
        try:
            value, path = _read_fixed(root, FINAL_CHAT_ARTIFACT, kind="json")
            if not isinstance(value, dict):
                raise ValueError("final chat must be a JSON object")
            documents["final_chat"] = value
            input_paths.append(path)
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="final_chat",
                error_type="final_chat_invalid",
                repair_action="rebuild_final_chat_delivery_index_and_revalidate",
                error=error,
            )

    run_contract = documents.get("run_contract")
    mode = run_contract.get("mode") if isinstance(run_contract, Mapping) else None
    if not isinstance(mode, str):
        mode = "promax-artifact-run"
    run_id = run_contract.get("run_id") if isinstance(run_contract, Mapping) else None
    source_sha = (
        run_contract.get("source_snapshot_sha256")
        if isinstance(run_contract, Mapping)
        else None
    )
    if (
        not allow_test_fixture
        and isinstance(run_id, str)
        and _TEST_FIXTURE_RUN_ID_RE.match(run_id) is not None
    ):
        failures.append(
            machine_failure(
                error_type="test_fixture_provenance_forbidden",
                artifact=JSON_ARTIFACTS["run_contract"],
                affected_phase="P0",
                repair_action="restart_with_real_request_bound_artifacts",
            )
        )
        diagnostics.append(
            "test_fixture_provenance_forbidden:promax-run-contract.json:"
            "production validation rejects deterministic fixture run_id values"
        )

    # Schema checks are independent and therefore all run even when one fails.
    for key, schema_name in _SCHEMAS.items():
        document = documents.get(key)
        if document is None:
            continue
        try:
            validate_instance(schema_name, document)
        except Exception as error:
            error_type = _schema_error_type(key, error)
            _append_failure(
                failures,
                diagnostics,
                key=key,
                error_type=error_type,
                repair_action="rebuild_artifact_from_canonical_schema_and_revalidate",
                error=error,
            )

    validators_executable = False
    if isinstance(run_contract, Mapping):
        capabilities = run_contract.get("capabilities")
        validators = capabilities.get("validators") if isinstance(capabilities, Mapping) else None
        validator_ids = validators.get("validator_ids") if isinstance(validators, Mapping) else None
        validators_executable = bool(
            isinstance(validators, Mapping)
            and validators.get("available") is True
            and validators.get("executable") is True
            and isinstance(validator_ids, list)
            and validator_ids
        )
        if not validators_executable:
            if mode == "promax-artifact-run":
                capability_gaps.append("validators-unavailable")
            else:
                _append_failure(
                    failures,
                    diagnostics,
                    key="run_contract",
                    error_type="capability_gap_not_permitted",
                    repair_action="restore_executable_frozen_validator_set_and_restart_run",
                    error=ValueError("run contract has no executable frozen validator set"),
                )

    try:
        validate_version_isolation(repo_root / "skills" / "crossframe-promax")
    except Exception as error:
        failures.append(
            machine_failure(
                error_type="version_pollution_detected",
                artifact="skills/crossframe-promax/SKILL.md",
                affected_phase="P1",
                repair_action="remove_non_v8_or_sibling_knowledge_and_revalidate",
            )
        )
        diagnostics.append(f"version_pollution_detected:skills/crossframe-promax:{error}")

    bindings_valid = isinstance(run_id, str) and isinstance(source_sha, str)
    if bindings_valid:
        for key, document in documents.items():
            if key in {
                "run_contract",
                "source_snapshot",
                "manifest",
                "read_events",
                "phase_events",
                "final_chat",
            } or not isinstance(document, Mapping):
                continue
            if key == "recommendation" and document == {"status": "not_requested"}:
                continue
            try:
                if document.get("run_id") != run_id or document.get(
                    "source_snapshot_sha256"
                ) != source_sha:
                    raise ValueError("immutable run/source binding mismatch")
            except Exception as error:
                _append_failure(
                    failures,
                    diagnostics,
                    key=key,
                    error_type="run_binding_mismatch",
                    repair_action="rebuild_artifact_for_current_run_and_revalidate",
                    error=error,
                )

    source_snapshot = documents.get("source_snapshot")
    if isinstance(source_snapshot, Mapping):
        try:
            verified_at = source_snapshot.get("verified_at")
            canonical_snapshot = build_source_snapshot(
                repo_root,
                verified_at=verified_at if isinstance(verified_at, str) else stamp,
            )
            if dict(source_snapshot) != canonical_snapshot:
                raise ValueError("workspace source snapshot differs from canonical v8 bytes")
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="source_snapshot",
                error_type="source_snapshot_content_mismatch",
                repair_action="rebuild_source_snapshot_from_exact_v8_assets_and_revalidate",
                error=error,
            )

    if bindings_valid and isinstance(documents.get("read_events"), list):
        try:
            validate_read_event_coverage(
                documents["read_events"],
                repo=repo_root,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=source_sha,
            )
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="read_events",
                error_type="source_read_coverage_invalid",
                repair_action="reread_exact_v8_targets_and_rebuild_read_events",
                error=error,
            )

    phase_state = None
    if bindings_valid and isinstance(run_contract, Mapping) and isinstance(
        documents.get("phase_events"), list
    ):
        try:
            binding = RunBinding(
                run_id=run_id,
                run_nonce=run_contract["run_nonce"],
                request_sha256=run_contract["request_sha256"],
                source_snapshot_sha256=source_sha,
            )
            phase_state = validate_phase_history(
                documents["phase_events"], expected_binding=binding
            )
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="phase_events",
                error_type="phase_history_replay",
                repair_action="discard_replayed_history_and_resume_from_last_valid_phase",
                error=error,
            )

    concept_registry = None
    try:
        concept_registry = _load_concept_registry(repo_root)
    except Exception as error:
        _append_failure(
            failures,
            diagnostics,
            key="source_snapshot",
            error_type="source_snapshot_content_mismatch",
            repair_action="restore_canonical_v8_registry_and_revalidate",
            error=error,
        )

    concept_disposition = documents.get("concept_disposition")
    if bindings_valid and isinstance(concept_disposition, Mapping):
        try:
            route_ids = concept_disposition.get("route_ids")
            if not isinstance(route_ids, list):
                raise ValueError("concept route_ids must be an array")
            validate_concept_closure(
                concept_disposition,
                repo=repo_root,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=source_sha,
                required_route_ids=route_ids,
            )
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="concept_disposition",
                error_type="concept_closure_incomplete",
                repair_action="complete_registry_route_neighbor_disposition_and_revalidate",
                error=error,
            )

    claim_graph = documents.get("claim_path_graph")
    if bindings_valid and isinstance(claim_graph, Mapping):
        try:
            validate_claim_path_saturation(
                claim_graph,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=source_sha,
            )
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="claim_path_graph",
                error_type="claim_path_incomplete",
                repair_action="complete_claim_mechanism_branch_cycle_and_revalidate",
                error=error,
            )

    retrieval = documents.get("retrieval_ledger")
    if isinstance(retrieval, Mapping) and isinstance(run_contract, Mapping):
        capabilities = run_contract.get("capabilities")
        network = capabilities.get("network") if isinstance(capabilities, Mapping) else None
        disclosed_available = network.get("available") if isinstance(network, Mapping) else None
        disclosed_live = network.get("live_retrieval") if isinstance(network, Mapping) else None
        ledger_available = retrieval.get("network_available")
        if (
            type(disclosed_available) is bool
            and type(disclosed_live) is bool
            and type(ledger_available) is bool
        ):
            if ledger_available != disclosed_available or (
                ledger_available and not disclosed_live
            ):
                _append_failure(
                    failures,
                    diagnostics,
                    key="run_contract",
                    error_type="capability_disclosure_mismatch",
                    repair_action="restore_frozen_capability_binding_and_rerun_retrieval",
                    error=ValueError(
                        "retrieval network availability contradicts the frozen run contract"
                    ),
                )
            elif ledger_available is False:
                capability_gaps.append("network-unavailable")
    if bindings_valid and isinstance(retrieval, Mapping) and isinstance(claim_graph, Mapping):
        try:
            raw_claims = claim_graph.get("claims")
            if not isinstance(raw_claims, list):
                raise ValueError("claim graph claims must be an array")
            claim_ids = [
                str(item["claim_id"])
                for item in raw_claims
                if isinstance(item, Mapping)
                and isinstance(item.get("claim_id"), str)
            ]
            validate_retrieval_saturation(
                retrieval,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=source_sha,
                required_claim_ids=claim_ids,
                strict_completion=mode != "promax-artifact-run",
            )
            _validate_source_independence(retrieval)
        except Exception as error:
            error_type, artifact_key = _semantic_error_type("retrieval", error)
            _append_failure(
                failures,
                diagnostics,
                key=artifact_key,
                error_type=error_type,
                repair_action="complete_five_direction_retrieval_and_saturation_rounds",
                error=error,
            )

    position = documents.get("position")
    red_team = documents.get("red_team_report")
    local_world = documents.get("local_world_model")
    if all(
        isinstance(item, Mapping)
        for item in (position, red_team, claim_graph, local_world, retrieval)
    ) and bindings_valid:
        try:
            _validate_stability_evidence_binding(
                run_contract,
                local_world,
                retrieval,
                red_team,
            )
            validate_position_semantics(
                position,
                red_team_report=red_team,
                claim_path_graph=claim_graph,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=source_sha,
            )
        except Exception as error:
            error_type, artifact_key = _semantic_error_type("position", error)
            _append_failure(
                failures,
                diagnostics,
                key=artifact_key,
                error_type=error_type,
                repair_action="rerun_red_team_and_relock_evidence_bound_position",
                error=error,
            )

    recommendation = documents.get("recommendation")
    if bindings_valid and isinstance(run_contract, Mapping) and isinstance(
        recommendation, Mapping
    ) and isinstance(position, Mapping):
        try:
            validate_recommendation_semantics(
                run_contract,
                recommendation,
                position=position,
                expected_run_id=run_id,
                expected_source_snapshot_sha256=source_sha,
            )
            if not isinstance(red_team, Mapping):
                raise ValueError("recommendation stability binding requires red-team state")
            _validate_stability_ranking_binding(
                run_contract, red_team, recommendation, retrieval
            )
        except Exception as error:
            if "stability" in str(error).casefold():
                error_type, artifact_key = "stance_stability_failed", "red_team_report"
            else:
                error_type, artifact_key = _semantic_error_type("recommendation", error)
            _append_failure(
                failures,
                diagnostics,
                key=artifact_key,
                error_type=error_type,
                repair_action="rebuild_closed_six_option_recommendation_and_revalidate",
                error=error,
            )

    deliverables = {
        TEXT_ARTIFACTS[key]: texts[key]
        for key in ("dossier", "concept_atlas", "case_and_countercase", "essay")
        if key in texts
    }
    if (
        isinstance(documents.get("continuation_ledger"), Mapping)
        and isinstance(documents.get("manifest"), Mapping)
        and len(deliverables) == 4
    ):
        try:
            validate_continuation_lineage(
                documents["continuation_ledger"],
                manifest=documents["manifest"],
                deliverables=deliverables,
            )
        except Exception as error:
            error_type, artifact_key = _semantic_error_type("output", error)
            repair_action = (
                "rebuild_changed_artifact_regenerate_manifest_and_revalidate"
                if error_type == "manifest_stale"
                else "reattach_continuation_to_current_manifest_parent"
            )
            _append_failure(
                failures,
                diagnostics,
                key=artifact_key,
                error_type=error_type,
                repair_action=repair_action,
                error=error,
            )
    validated_output = None
    output_requirements = (
        isinstance(run_contract, Mapping),
        isinstance(position, Mapping),
        isinstance(recommendation, Mapping),
        isinstance(documents.get("output_plan"), Mapping),
        isinstance(concept_disposition, Mapping),
        isinstance(claim_graph, Mapping),
        isinstance(concept_registry, Mapping),
        isinstance(documents.get("manifest"), Mapping),
        isinstance(documents.get("continuation_ledger"), Mapping),
        len(deliverables) == 4,
    )
    if all(output_requirements):
        try:
            validated_output = validate_output_bundle(
                run_contract=run_contract,
                position=position,
                recommendation=recommendation,
                output_plan=documents["output_plan"],
                concept_disposition=concept_disposition,
                claim_path_graph=claim_graph,
                concept_registry=concept_registry,
                deliverables=deliverables,
                manifest=documents["manifest"],
                continuation_ledger=documents["continuation_ledger"],
            )
            raw_anomalies = validated_output.get("anomalies")
            if isinstance(raw_anomalies, list):
                anomalies.extend(
                    item for item in raw_anomalies if isinstance(item, str)
                )
        except Exception as error:
            error_type, artifact_key = _semantic_error_type("output", error)
            _append_failure(
                failures,
                diagnostics,
                key=artifact_key,
                error_type=error_type,
                repair_action="rebuild_plan_outputs_examples_and_lineage_then_revalidate",
                error=error,
            )

    final_chat_projection: dict[str, object] | None = None
    if (
        final_chat
        and isinstance(documents.get("final_chat"), Mapping)
        and validated_output is not None
        and isinstance(position, Mapping)
        and isinstance(documents.get("manifest"), Mapping)
        and isinstance(documents.get("continuation_ledger"), Mapping)
    ):
        try:
            final_chat_projection = validate_final_chat(
                documents["final_chat"],
                run_contract=run_contract,
                position=position,
                manifest=documents["manifest"],
                continuation_ledger=documents["continuation_ledger"],
                validated_output=validated_output,
            )
        except Exception as error:
            final_chat_projection = None
            _append_failure(
                failures,
                diagnostics,
                key="final_chat",
                error_type="final_chat_invalid",
                repair_action="rebuild_five_field_final_chat_delivery_index",
                error=error,
            )
    elif final_chat and isinstance(documents.get("final_chat"), Mapping):
        diagnostics.append("final_chat_not_checked:required_output_gate_did_not_pass")

    if phase_state is not None and isinstance(manifest, Mapping):
        try:
            if phase_state.chain_head_sha256 != manifest.get("phase_chain_head_sha256"):
                raise ValueError("manifest is not bound to the active phase-chain head")
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="manifest",
                error_type="manifest_stale",
                repair_action="regenerate_manifest_from_current_phase_chain_and_revalidate",
                error=error,
            )

    if mode != "promax-artifact-run" and capability_gaps:
        failures.append(
            _failure_for(
                "retrieval_ledger",
                error_type="capability_gap_not_permitted",
                repair_action="restore_required_capability_and_rerun_strict_validation",
            )
        )
    failures = _ordered_failures(failures)
    outcome = classify_outcome(
        mode, failures=failures, capability_gaps=capability_gaps
    )
    if (
        final_chat
        and isinstance(final_chat_projection, Mapping)
        and final_chat_projection.get("run_status") != outcome["completion_status"]
    ):
        _append_failure(
            failures,
            diagnostics,
            key="final_chat",
            error_type="final_chat_status_mismatch",
            repair_action="project_the_fresh_checker_completion_status_and_revalidate",
            error=ValueError(
                "final chat run status does not equal the fresh checker completion status"
            ),
        )
        failures = _ordered_failures(failures)
        outcome = classify_outcome(
            mode,
            failures=failures,
            capability_gaps=capability_gaps,
        )

    official_report = None
    repair_plan = None
    failure_anchor = None
    if (
        validators_executable
        and isinstance(run_contract, Mapping)
        and isinstance(manifest, Mapping)
    ):
        try:
            versions, checks = _validator_checks(
                run_contract, failures, capability_gaps
            )
            validation_attempt = 1
            if write_report:
                try:
                    validation_attempt = _next_validation_attempt(
                        root, run_contract, manifest, versions
                    )
                except Exception as error:
                    if isinstance(error, MachineValidationError):
                        _append_failure(
                            failures,
                            diagnostics,
                            key="manifest",
                            error_type="validator_report_replay",
                            repair_action="discard_stale_report_and_revalidate",
                            error=error,
                        )
                    else:
                        replay_failure = machine_failure(
                            error_type="validator_report_replay",
                            artifact=REPORT_ARTIFACT,
                            affected_phase="P11",
                            repair_action="discard_stale_report_and_revalidate",
                        )
                        if replay_failure not in failures:
                            failures.append(replay_failure)
                        diagnostics.append(
                            f"validator_report_replay:{REPORT_ARTIFACT}:{error}"
                        )
                    failures = _ordered_failures(failures)
                    outcome = classify_outcome(
                        mode, failures=failures, capability_gaps=capability_gaps
                    )
                    versions, checks = _validator_checks(
                        run_contract, failures, capability_gaps
                    )
            official_report = build_validator_report(
                run_contract,
                manifest,
                validator_versions=versions,
                checks=checks,
                validation_attempt=validation_attempt,
                completion_status=outcome["completion_status"],
                validated_at=stamp,
                run_dir=root,
            )
            if failures:
                repair_plan = build_repair_plan(
                    official_report, failures, created_at=stamp
                )
        except Exception as error:
            _append_failure(
                failures,
                diagnostics,
                key="manifest",
                error_type="manifest_stale",
                repair_action="regenerate_manifest_and_run_full_validation",
                error=error,
                preserve_machine_failure=False,
            )
            failures = _ordered_failures(failures)
            outcome = classify_outcome(
                mode, failures=failures, capability_gaps=capability_gaps
            )
            official_report = None
            repair_plan = None

    if repair_plan is None and failures and isinstance(run_contract, Mapping):
        try:
            failure_anchor = _preflight_failure_anchor(
                run_contract, failures, validated_at=stamp
            )
            repair_plan = build_repair_plan(
                failure_anchor, failures, created_at=stamp
            )
        except Exception as error:
            diagnostics.append(f"repair_plan_not_built:{error}")
            failure_anchor = None

    if write_report:
        if official_report is None:
            diagnostics.append(
                "validator_report_not_written:manifest_or_run_contract_failed_preflight"
            )
        else:
            try:
                write_report_atomic(
                    root / REPORT_ARTIFACT,
                    official_report,
                    workspace=root,
                    input_paths=input_paths,
                )
            except Exception as error:
                output_failure = machine_failure(
                    error_type="validator_report_output_unsafe",
                    artifact=REPORT_ARTIFACT,
                    affected_phase="P11",
                    repair_action="replace_unsafe_report_path_and_revalidate",
                )
                if output_failure not in failures:
                    failures.append(output_failure)
                diagnostics.append(
                    f"validator_report_output_unsafe:{REPORT_ARTIFACT}:{error}"
                )
                failures = _ordered_failures(failures)
                outcome = classify_outcome(
                    mode, failures=failures, capability_gaps=capability_gaps
                )
                official_report = None
                failure_anchor = _preflight_failure_anchor(
                    run_contract, failures, validated_at=stamp
                )
                repair_plan = build_repair_plan(
                    failure_anchor, failures, created_at=stamp
                )

    result: dict[str, object] = {
        "overall_status": outcome["overall_status"],
        "completion_status": outcome["completion_status"],
        "failures": copy.deepcopy(failures),
        "capability_gaps": sorted(set(capability_gaps)),
        "anomalies": sorted(set(anomalies)),
        "diagnostics": diagnostics,
        "validator_report": official_report,
        "repair_plan": repair_plan,
        "preflight_failure_anchor": failure_anchor,
        "final_chat_projection": final_chat_projection if not failures else None,
    }
    return result


def check_workspace(
    workspace: Path | str,
    *,
    repo: Path | str,
    final_chat: bool = False,
    write_report: bool = False,
    validated_at: str | None = None,
    allow_test_fixture: bool = False,
) -> dict[str, object]:
    """Canonical alias; ``allow_test_fixture`` is reserved for repository tests."""

    return validate_workspace(
        workspace,
        repo=repo,
        final_chat=final_chat,
        write_report=write_report,
        validated_at=validated_at,
        allow_test_fixture=allow_test_fixture,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate one fixed CrossFrame ProMax v8 artifact workspace."
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--final-chat",
        action="store_true",
        required=True,
        help=f"also validate the fixed {FINAL_CHAT_ARTIFACT} delivery index",
    )
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = validate_workspace(
            args.workspace,
            repo=args.repo,
            final_chat=args.final_chat,
            write_report=args.write_report,
        )
    except Exception as error:
        failure = machine_failure(
            error_type="checker_invocation_invalid",
            artifact=JSON_ARTIFACTS["run_contract"],
            affected_phase="P0",
            repair_action="correct_checker_workspace_and_repo_then_revalidate",
        )
        failed = {
            "overall_status": "fail",
            "completion_status": "promax-artifact-incomplete:validation-failed",
            "failures": [failure],
            "capability_gaps": [],
            "anomalies": [],
            "diagnostics": [str(error)],
            "validator_report": None,
            "repair_plan": None,
            "final_chat_projection": None,
        }
        if args.json:
            print(json.dumps(failed, ensure_ascii=False, sort_keys=True))
        else:
            print(f"fail: {failed['completion_status']}")
            print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{result['overall_status']}: {result['completion_status']}")
        for failure in result["failures"]:
            print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
    return 0 if result["overall_status"] == "pass" else 2 if result["overall_status"] == "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
