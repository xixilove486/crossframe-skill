from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any

from check_crossframe_max_artifacts import check_crossframe_max_artifacts


VALIDATOR_NAME = "check_crossframe_max_artifacts"
DEFAULT_MAX_RETRY_COUNT = 2
HARD_MAX_RETRY_COUNT = 3

PHASE_DOWNSTREAM = {
    "run_contract": [
        "max-read-plan.json",
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-claim-board.json",
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
    ],
    "read_plan": [
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-board.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "source_snapshot": [
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-evidence-reasoning-audit.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "concept_hit": [
        "max-claim-ledger.json",
        "max-claim-board.json",
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "claim": [
        "max-evidence-reasoning-audit.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "audit": [
        "max-output-plan.locked.md",
        "max-dossier.md",
        "max-essay.md",
    ],
    "output_plan": [
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
    ],
    "final_markdown": [],
    "repository_maintenance": [],
}


@dataclass(frozen=True)
class ValidationError:
    error_id: str
    validator: str
    error_type: str
    severity: str
    artifact: str
    field: str | None
    message: str
    affected_phase: str
    repair_action: str
    downstream_reset: list[str]
    final_output_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_skill_root() -> Path:
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "scripts" and script_path.parent.parent.name == "crossframe-max":
        return script_path.parent.parent
    return script_path.parents[1] / "skills" / "crossframe-max"


def phase_for_artifact(artifact: str) -> str:
    if artifact == "max-run-contract.json":
        return "run_contract"
    if artifact == "max-read-plan.json":
        return "read_plan"
    if artifact == "max-source-snapshot.json":
        return "source_snapshot"
    if artifact in {"max-concept-hit-ledger.json"}:
        return "concept_hit"
    if artifact in {"max-claim-ledger.json", "max-claim-board.json"}:
        return "claim"
    if artifact in {"max-evidence-reasoning-audit.json", "max-audit-board.json"}:
        return "audit"
    if artifact == "max-output-plan.locked.md":
        return "output_plan"
    if artifact in {
        "max-artifact-manifest.md",
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
    }:
        return "final_markdown"
    return "final_markdown"


def extract_artifact(message: str) -> str:
    for token in [
        "max-read-plan.json",
        "max-concept-hit-ledger.json",
        "max-claim-ledger.json",
        "max-evidence-reasoning-audit.json",
        "max-run-contract.json",
        "max-source-snapshot.json",
        "max-worldview-capsule.locked.md",
        "max-local-world-model.locked.md",
        "max-claim-board.json",
        "max-audit-board.json",
        "max-output-plan.locked.md",
        "max-artifact-manifest.md",
        "max-dossier.md",
        "max-essay.md",
        "max-continuation-ledger.md",
        "max-continuation-index.md",
        "v6-route-map.yaml",
        "v6-contract-map.json",
        "concept-registry/index.md",
    ]:
        if token in message:
            return token
    if ": " in message:
        prefix = message.split(":", 1)[0]
        if prefix.endswith((".json", ".md", ".yaml")):
            return prefix
    return "workspace"


def classify_message(message: str) -> tuple[str, str, str, str | None]:
    lowered = message.lower()
    if "invalid json" in lowered:
        return "invalid_json", "create_missing_artifact", phase_for_artifact(extract_artifact(message)), None
    if message.startswith("missing file:") or message.startswith("missing structured ledger:") or "missing phase-lock artifact" in message or "missing route-ledger artifact" in message:
        return "missing_artifact", "create_missing_artifact", phase_for_artifact(extract_artifact(message)), None
    if "full-source" in message and ("not satisfied" in lowered or "partial" in lowered or "missing" in lowered):
        return "full_source_incomplete", "max_incomplete", "source_snapshot", None
    if "source_ranges_from_registry does not match" in message or "source_ranges_read does not overlap" in message:
        return "concept_source_anchor_mismatch", "regenerate_concept_hit_and_downstream", "concept_hit", "source_ranges_from_registry"
    if "source_paragraph_ids not covered" in message:
        return "source_paragraph_not_in_read_range", "regenerate_concept_hit_and_downstream", "concept_hit", "source_paragraph_ids"
    if "contract_id" in message or "v6-contract-map.json" in message:
        return "concept_contract_missing", "repository_maintenance_required", "repository_maintenance", "contract_id"
    if "not found in concept registry" in message:
        return "concept_registry_missing", "regenerate_concept_hit_and_downstream", "concept_hit", "concept_id"
    if "required_concepts missing from concept registry" in message or "missing route required concepts" in message:
        return "route_registry_closure_failed", "regenerate_concept_hit_and_downstream", "concept_hit", "route_required_concepts"
    if "route_key" in message or "route_map_version" in message or "missing route " in message or "forbidden output check" in message:
        return "route_plan_mismatch", "regenerate_output_plan_and_final_markdown", "read_plan", None
    if "concept_ids missing concept hits" in message:
        return "claim_missing_concept_hit", "regenerate_concept_hit_and_downstream", "concept_hit", "concept_ids"
    if "final claims missing audits" in message or "design decisions missing audits" in message:
        return "claim_missing_audit", "regenerate_audit_and_downstream", "audit", "claim_id"
    if "missing evidence_chain" in message or "evidence chain" in lowered:
        return "evidence_chain_missing", "regenerate_audit_and_downstream", "audit", "evidence_chain"
    if "missing counterevidence" in message or "counterevidence_status" in message:
        return "counterevidence_missing", "regenerate_audit_and_downstream", "audit", "counterevidence"
    if "external search" in lowered or "needs_external_search" in message:
        return "external_search_required", "needs_external_search", "audit", None
    if "longform-dominance gate failed" in message:
        return "essay_too_short", "regenerate_markdown_only", "final_markdown", None
    if "heading section too thin" in message:
        return "dossier_section_too_thin", "regenerate_markdown_only", "final_markdown", None
    if "repeated" in lowered or "marker stuffing" in lowered:
        return "repeated_filler", "regenerate_markdown_only", "final_markdown", None
    if "forbidden output appears" in message:
        return "forbidden_output_present", "regenerate_markdown_only", "final_markdown", None
    if "must reference a real claim_id or source_paragraph_id" in message:
        return "missing_claim_or_source_reference", "regenerate_markdown_only", "final_markdown", None
    return "unrepairable_repository_state", "max_incomplete", phase_for_artifact(extract_artifact(message)), None


def validation_error_from_message(index: int, message: str, validator: str = VALIDATOR_NAME) -> ValidationError:
    error_type, repair_action, affected_phase, field = classify_message(message)
    artifact = extract_artifact(message)
    if artifact == "workspace" and affected_phase != "repository_maintenance":
        artifact = PHASE_DOWNSTREAM.get(affected_phase, ["workspace"])[0] if PHASE_DOWNSTREAM.get(affected_phase) else "workspace"
    return ValidationError(
        error_id=f"max-{index:04d}",
        validator=validator,
        error_type=error_type,
        severity="error",
        artifact=artifact,
        field=field,
        message=message,
        affected_phase=affected_phase,
        repair_action=repair_action,
        downstream_reset=list(PHASE_DOWNSTREAM.get(affected_phase, [])),
        final_output_allowed=False,
    )


def coerce_validation_errors(raw_errors: list[Any]) -> list[ValidationError]:
    coerced: list[ValidationError] = []
    for index, error in enumerate(raw_errors, start=1):
        if isinstance(error, ValidationError):
            coerced.append(error)
            continue
        if all(hasattr(error, attr) for attr in ["error_type", "message", "repair_action"]):
            data = error.to_dict() if hasattr(error, "to_dict") else vars(error)
            coerced.append(ValidationError(**data))
            continue
        coerced.append(validation_error_from_message(index, str(error)))
    return coerced


def run_validators(workspace: Path, skill_root: Path | None = None) -> list[ValidationError]:
    skill_root = skill_root or default_skill_root()
    structured_func = getattr(sys.modules.get("check_crossframe_max_artifacts"), "check_crossframe_max_artifacts_structured", None)
    if structured_func is not None:
        return coerce_validation_errors(structured_func(workspace, skill_root))
    return coerce_validation_errors(check_crossframe_max_artifacts(workspace, skill_root))


def validator_report(workspace: Path, errors: list[ValidationError]) -> dict[str, Any]:
    return {
        "report_version": "v1",
        "workspace": str(workspace),
        "passed": not errors,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "validators": ["check_crossframe_max_artifacts", "check_crossframe_max_route_ledgers"],
        "errors": [error.to_dict() for error in errors],
    }


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def build_repair_plan(errors: list[ValidationError], workspace: Path, validation_attempt: int = 1) -> dict[str, Any]:
    if not errors:
        return {
            "repair_plan_version": "v1",
            "workspace": str(workspace),
            "validation_attempt": validation_attempt,
            "retry_count": validation_attempt - 1,
            "final_output_allowed": True,
            "max_retry_count": DEFAULT_MAX_RETRY_COUNT,
            "errors": [],
            "affected_phases": [],
            "must_regenerate": [],
            "must_not_patch_only": [],
            "repair_actions": [],
            "downgrade_required": [],
            "withdraw_required": [],
            "external_search_required": False,
            "repository_maintenance_required": False,
            "max_incomplete_if_unresolved": False,
        }

    affected_phases = ordered_unique([error.affected_phase for error in errors])
    must_regenerate = ordered_unique(
        [
            artifact
            for error in errors
            for artifact in ([error.artifact] + list(error.downstream_reset))
            if artifact != "workspace"
        ]
    )
    repair_actions = ordered_unique([error.repair_action for error in errors])
    evidence_insufficient = {"evidence_chain_missing", "counterevidence_missing", "external_search_required"}
    downgrade_required = [
        error.error_id
        for error in errors
        if error.error_type in evidence_insufficient or error.repair_action == "downgrade_claim"
    ]
    external_search_required = any(error.error_type == "external_search_required" for error in errors)
    repository_maintenance_required = any(
        error.error_type == "concept_contract_missing" or error.repair_action == "repository_maintenance_required"
        for error in errors
    )
    must_not_patch_only: list[str] = []
    if any(phase in {"concept_hit", "claim", "audit", "output_plan"} for phase in affected_phases):
        must_not_patch_only.append("max-essay.md")
    if any("max-dossier.md" in error.downstream_reset for error in errors):
        must_not_patch_only.append("max-dossier.md")
    if validation_attempt >= HARD_MAX_RETRY_COUNT:
        repair_actions = ordered_unique(repair_actions + ["max_incomplete"])

    return {
        "repair_plan_version": "v1",
        "workspace": str(workspace),
        "validation_attempt": validation_attempt,
        "retry_count": validation_attempt - 1,
        "final_output_allowed": False,
        "max_retry_count": DEFAULT_MAX_RETRY_COUNT,
        "errors": [error.to_dict() for error in errors],
        "affected_phases": affected_phases,
        "must_regenerate": must_regenerate,
        "must_not_patch_only": ordered_unique(must_not_patch_only),
        "repair_actions": repair_actions,
        "downgrade_required": downgrade_required,
        "withdraw_required": [],
        "external_search_required": external_search_required,
        "repository_maintenance_required": repository_maintenance_required,
        "max_incomplete_if_unresolved": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CrossFrame Max validator report and repair plan.")
    parser.add_argument("--workspace", default=".", help="Directory containing max artifacts.")
    parser.add_argument("--skill-root", default=None, help="Path to crossframe-max skill root.")
    parser.add_argument("--validation-attempt", type=int, default=1)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--write-repair-plan", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else default_skill_root()
    errors = run_validators(workspace, skill_root)
    report = validator_report(workspace, errors)
    plan = build_repair_plan(errors, workspace, args.validation_attempt)

    if args.write_report and not args.dry_run:
        (workspace / "max-validator-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if errors and args.write_repair_plan and not args.dry_run:
        (workspace / "max-repair-plan.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.dry_run:
        print(json.dumps({"validator_report": report, "repair_plan": plan}, ensure_ascii=False, indent=2))
    elif errors:
        print(f"repair plan required: {len(errors)} validator error(s)", file=sys.stderr)
    else:
        print("ok: crossframe max validator report passed; no repair plan required")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
