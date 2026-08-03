from __future__ import annotations

import copy
from datetime import datetime, timezone
import importlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterator

import pytest
from jsonschema import Draft202012Validator, ValidationError
from referencing.exceptions import NoSuchResource


ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = ROOT / "skills/crossframe-ultra"
SCHEMA_ROOT = ULTRA_ROOT / "schemas"
RUNTIME_SCRIPTS = ULTRA_ROOT / "scripts"
RUNTIME_FIXTURE_ROOT = ROOT / "tests/fixtures/ultra-runtime"

FRAMEWORK_RAW_SHA256 = (
    "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
)
FRAMEWORK_SEMANTIC_SHA256 = (
    "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
SOURCE_TREE_SHA256 = (
    "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
)
STAMP = "2026-08-02T08:00:00Z"
RUN_ID = "ultra-run-20260802-0001"

EXPECTED_SCHEMA_NAMES = (
    "ultra-action-ranking.schema.json",
    "ultra-article-review.schema.json",
    "ultra-artifact-manifest.schema.json",
    "ultra-claim-mechanism-graph.schema.json",
    "ultra-common.schema.json",
    "ultra-compatibility-matrix.schema.json",
    "ultra-concept-disposition.schema.json",
    "ultra-concept-registry.schema.json",
    "ultra-contract-map.schema.json",
    "ultra-evidence-ledger.schema.json",
    "ultra-forecast-ledger.schema.json",
    "ultra-framework-gap-ledger.schema.json",
    "ultra-order-evaluation.schema.json",
    "ultra-output-plan.schema.json",
    "ultra-phase-event.schema.json",
    "ultra-read-event.schema.json",
    "ultra-recovery-checkpoint.schema.json",
    "ultra-recursive-lineage.schema.json",
    "ultra-red-team-report.schema.json",
    "ultra-release-manifest.schema.json",
    "ultra-repair-plan.schema.json",
    "ultra-retrieval-ledger.schema.json",
    "ultra-route-map.schema.json",
    "ultra-run-contract.schema.json",
    "ultra-run-status.schema.json",
    "ultra-semantic-coverage.schema.json",
    "ultra-source-lock.schema.json",
    "ultra-source-manifest.schema.json",
    "ultra-transformation-ledger.schema.json",
    "ultra-validator-report.schema.json",
    "ultra-verdict.schema.json",
    "ultra-world-volume.schema.json",
)

AUTHORITY_SCHEMAS = frozenset(
    {
        "ultra-concept-registry.schema.json",
        "ultra-contract-map.schema.json",
        "ultra-route-map.schema.json",
        "ultra-source-manifest.schema.json",
    }
)
ARTIFACT_SCHEMAS = tuple(
    name
    for name in EXPECTED_SCHEMA_NAMES
    if name != "ultra-common.schema.json" and name not in AUTHORITY_SCHEMAS
)
INSTANCE_SCHEMA_IDS = {
    name: "crossframe.ultra.v82."
    + name.removeprefix("ultra-").removesuffix(".schema.json")
    for name in ARTIFACT_SCHEMAS
}


def version_binding() -> dict[str, Any]:
    return {
        "framework_version": "8.2",
        "framework_revision": "v8.2-r1",
        "framework_raw_sha256": FRAMEWORK_RAW_SHA256,
        "framework_semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
        "runtime_version": "1.0.0",
        "artifact_schema_version": 1,
        "compiler_version": "1.0.0",
        "validator_version": "1.0.0",
        "article_contract_version": "1.0.0",
        "source_tree_sha256": SOURCE_TREE_SHA256,
    }


def artifact(
    schema_name: str,
    *,
    phase_id: str | None = None,
    content_sha256: str = HASH_A,
    **payload: Any,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_id": INSTANCE_SCHEMA_IDS[schema_name],
        "schema_version": 1,
        "run_id": RUN_ID,
        "version_binding": version_binding(),
        "generated_at": STAMP,
        "content_sha256": content_sha256,
    }
    if phase_id is not None:
        value["phase_id"] = phase_id
    value.update(payload)
    return value


def local_state(state_id: str, name: str, value: str) -> dict[str, Any]:
    return {
        "state_id": state_id,
        "variables": [{"name": name, "value": value, "unit": "category"}],
    }


def scale_profile(*, organizational: str) -> dict[str, str]:
    return {
        "spatial": "local",
        "temporal": "interaction",
        "organizational": organizational,
        "institutional": "informal",
        "material": "bounded",
        "informational": "partial",
        "relational": "direct",
        "power": "delegated",
        "risk": "reversible",
    }


def evidence_status(*, identity: str = "reported") -> dict[str, Any]:
    return {
        "status": "supported-hypothesis",
        "information_identity": identity,
        "source_lineage": ["SOURCE-1"],
        "visibility": "visible in the supplied record",
    }


def compatibility_matrix_instance() -> dict[str, Any]:
    current = version_binding()
    framework_from = {**current, "framework_revision": "v8.2-r0"}
    schema_from = {**current, "artifact_schema_version": 0}
    return artifact(
        "ultra-compatibility-matrix.schema.json",
        matrix_version=1,
        binding_fields=list(version_binding()),
        allowed_results=["resume", "read-only", "fork-required", "reject"],
        known_migrations={
            "framework_revisions": [
                {
                    "from_binding": framework_from,
                    "to_binding": current,
                    "result": "fork-required",
                }
            ],
            "artifact_schemas": [
                {
                    "from_binding": schema_from,
                    "to_binding": current,
                    "result": "fork-required",
                }
            ],
        },
        rules=[
            {
                "rule_id": "known-framework-migration",
                "priority": 10,
                "match_kind": "known-migration",
                "allowed_mismatch_fields": ["framework_revision"],
                "result": "fork-required",
            },
            {
                "rule_id": "known-schema-migration",
                "priority": 11,
                "match_kind": "known-migration",
                "allowed_mismatch_fields": ["artifact_schema_version"],
                "result": "fork-required",
            },
            {
                "rule_id": "readable-runtime",
                "priority": 20,
                "match_kind": "mismatch-subset",
                "allowed_mismatch_fields": [
                    "runtime_version",
                    "validator_version",
                ],
                "result": "read-only",
            },
            {
                "rule_id": "exact-binding",
                "priority": 30,
                "match_kind": "exact",
                "allowed_mismatch_fields": [],
                "result": "resume",
            },
            {
                "rule_id": "reject-unsupported",
                "priority": 100,
                "match_kind": "fallback",
                "allowed_mismatch_fields": [],
                "result": "reject",
            },
        ],
        source_revision_promotion={
            "same_semantic": {
                "action": "record-alternate-raw-package",
                "keep_revision": True,
                "build_beside_current": False,
                "requires_validation": False,
                "promote_stable_after_validation": False,
                "overwrite_existing_release": False,
            },
            "changed_semantic": {
                "action": "build-new-immutable-revision",
                "keep_revision": False,
                "build_beside_current": True,
                "requires_validation": True,
                "promote_stable_after_validation": True,
                "overwrite_existing_release": False,
            },
        },
    )


def minimal_instances() -> dict[str, dict[str, Any]]:
    fixtures: dict[str, dict[str, Any]] = {
        "ultra-release-manifest.schema.json": artifact(
            "ultra-release-manifest.schema.json",
            release_id="ultra-v8.2-r1",
            release_state="stable",
            stable_pointer="releases/stable.json",
            framework_source={
                "path": "sources/framework-v8.2.docx",
                "raw_sha256": FRAMEWORK_RAW_SHA256,
                "semantic_sha256": FRAMEWORK_SEMANTIC_SHA256,
                "alternate_raw_packages": [],
            },
            compiler={
                "normalization_algorithm": "ultra-semantic-normalization",
                "normalization_version": "1.0.0",
            },
            source_counts={
                "paragraphs": 1,
                "headings": 1,
                "tables": 0,
                "concepts": 1,
                "contracts": 1,
                "source_units": 1,
            },
            release_artifacts=[
                {
                    "path": "registry/concepts.json",
                    "sha256": HASH_B,
                    "media_type": "application/json",
                }
            ],
            built_at=STAMP,
            validated_at=STAMP,
        ),
        "ultra-compatibility-matrix.schema.json": compatibility_matrix_instance(),
        "ultra-run-contract.schema.json": artifact(
            "ultra-run-contract.schema.json",
            phase_id="U0",
            trigger="CrossFrame Ultra",
            request_sha256=HASH_B,
            run_mode="production",
            sensitivity="private",
            retention="retain",
            outbound_permission="denied",
            evidence_cutoff=STAMP,
            capabilities={
                "filesystem": "available",
                "docx_parser": "available",
                "network": "unavailable",
                "retrieval": "not-applicable",
                "validators": "available",
                "subagents": "unavailable",
                "model_context": "available",
            },
            resource_limits={
                "maximum_branches": 12,
                "maximum_retrieval_rounds_without_material_novelty": 2,
                "maximum_tool_retries": 3,
                "maximum_repair_attempts": 3,
            },
        ),
        "ultra-run-status.schema.json": artifact(
            "ultra-run-status.schema.json",
            phase_id="U0",
            status="running",
            previous_status="created",
            current_phase="U0",
            last_complete_phase=None,
            reason=None,
            tools_allowed=True,
            validation_passed=False,
            updated_at=STAMP,
        ),
        "ultra-phase-event.schema.json": artifact(
            "ultra-phase-event.schema.json",
            phase_id="U1",
            event_type="phase-completed",
            parent_event_sha256=HASH_A,
            input_artifact_hashes=[HASH_A],
            output_artifact_hashes=[HASH_B],
            source_sha256=HASH_C,
            evidence_cutoff=STAMP,
            run_contract_sha256=HASH_B,
            timestamp=STAMP,
            status="complete",
            failure_code=None,
            invalidated_phases=[],
            event_sha256=HASH_C,
        ),
        "ultra-source-lock.schema.json": artifact(
            "ultra-source-lock.schema.json",
            phase_id="U1",
            source_release_id="ultra-v8.2-r1",
            source_manifest_sha256=HASH_A,
            evidence_cutoff=STAMP,
            lock_status="locked",
            inputs=[
                {
                    "path": "input/request.md",
                    "sha256": HASH_B,
                    "media_type": "text/markdown",
                }
            ],
        ),
        "ultra-read-event.schema.json": artifact(
            "ultra-read-event.schema.json",
            phase_id="U1",
            source_unit_id="V82-P0001",
            source_kind="paragraph",
            source_ordinal=1,
            source_manifest_sha256=HASH_A,
            promoted_semantic_snapshot_sha256=HASH_B,
            reader_mode="full-source",
            execution_identity={
                "kind": "host-process",
                "process_id": 1234,
                "executable": "C:/Python/python.exe",
                "user": "fixture-user",
            },
            read_at=STAMP,
            read_event_sha256=HASH_C,
        ),
        "ultra-evidence-ledger.schema.json": artifact(
            "ultra-evidence-ledger.schema.json",
            phase_id="U3",
            evidence_cutoff=STAMP,
            entries=[
                {
                    "evidence_id": "EVIDENCE-1",
                    "identity": "observed",
                    "statement": "The supplied record contains one dated event.",
                    "source_refs": ["SOURCE-1"],
                    "observed_at": STAMP,
                    "confidence": "high",
                    "event_date": "2026-08-01",
                    "publication_date": "2026-08-01",
                    "interest": "No declared conflict in the supplied record.",
                    "upstream_lineage": ["UPSTREAM-1"],
                    "supported_claim": "The supplied record contains one dated event.",
                    "cannot_prove": "The record cannot prove the downstream response.",
                }
            ],
            unknowns=[
                {
                    "unknown_id": "UNKNOWN-1",
                    "location_ref": "POS-TEAM-MANAGER",
                    "description": "The downstream response is not observed.",
                    "resolution_condition": "Observe the next review cycle.",
                }
            ],
        ),
        "ultra-retrieval-ledger.schema.json": artifact(
            "ultra-retrieval-ledger.schema.json",
            phase_id="U2",
            network_available=False,
            outbound_authorized=False,
            entries=[
                {
                    "query_id": "QUERY-1",
                    "query_sha256": HASH_B,
                    "direction": "counterexample",
                    "result_summary": "Retrieval was not authorized.",
                    "source_refs": [],
                    "stop_reason": "outbound-not-authorized",
                }
            ],
            saturation={"rounds": 0, "stop_reason": "outbound-not-authorized"},
        ),
        "ultra-world-volume.schema.json": artifact(
            "ultra-world-volume.schema.json",
            phase_id="U4",
            volume_id="OMEGA-0",
            object_boundary={
                "object_ids": ["ACTOR-1", "CIRCLE-FAMILY", "CIRCLE-TEAM"],
                "boundary_rule": "Only represented actors and circles are in scope.",
            },
            actors=[
                {
                    "actor_id": "ACTOR-1",
                    "label": "Actor one",
                    "identity_criteria": "The same represented person in the frozen window.",
                    "M_state": local_state("M-ACTOR-1", "resources", "bounded"),
                    "Psi_state": local_state("PSI-ACTOR-1", "meaning", "engaged"),
                    "scale_profile": scale_profile(organizational="individual"),
                    "evidence_status": evidence_status(),
                }
            ],
            circles=[
                {
                    "circle_id": "CIRCLE-FAMILY",
                    "label": "Family",
                    "boundary_rule": "Household membership",
                    "membership_basis": "declared household role",
                    "identity_criteria": "The same household boundary and membership rule.",
                    "M_state": local_state("M-CIRCLE-FAMILY", "resources", "shared"),
                    "Psi_state": local_state("PSI-CIRCLE-FAMILY", "meaning", "familial"),
                    "scale_profile": scale_profile(organizational="household"),
                    "evidence_status": evidence_status(),
                },
                {
                    "circle_id": "CIRCLE-TEAM",
                    "label": "Team",
                    "boundary_rule": "Current project membership",
                    "membership_basis": "active work assignment",
                    "identity_criteria": "The same project boundary and active assignment rule.",
                    "M_state": local_state("M-CIRCLE-TEAM", "resources", "allocated"),
                    "Psi_state": local_state("PSI-CIRCLE-TEAM", "rule", "review"),
                    "scale_profile": scale_profile(organizational="team"),
                    "evidence_status": evidence_status(),
                },
            ],
            positions=[
                {
                    "position_id": "POS-TEAM-MANAGER",
                    "actor_id": "ACTOR-1",
                    "circle_id": "CIRCLE-TEAM",
                    "role_id": "ROLE-MANAGER",
                    "identity_criteria": "Actor one acting under the team mandate.",
                    "M_state": {
                        "state_id": "M-POS-1",
                        "variables": [
                            {"name": "budget", "value": 1, "unit": "share"}
                        ],
                    },
                    "Psi_state": {
                        "state_id": "PSI-POS-1",
                        "variables": [
                            {"name": "rule", "value": "review", "unit": "text"}
                        ],
                    },
                    "scale_profile": scale_profile(organizational="team"),
                    "evidence_status": evidence_status(identity="observed"),
                }
            ],
            memberships=[
                {
                    "membership_id": "MEMBERSHIP-1",
                    "actor_id": "ACTOR-1",
                    "circle_id": "CIRCLE-TEAM",
                    "role_id": "ROLE-MANAGER",
                    "basis": "active work assignment",
                    "role_conditions": "Decision authority is limited to the active project.",
                    "exit_conditions": "The actor may leave after handing off active work.",
                    "power_distribution": "DIST-POWER-1",
                }
            ],
            containment_relations=[
                {
                    "child_circle_id": "CIRCLE-TEAM",
                    "parent_circle_id": "CIRCLE-FAMILY",
                    "basis": "shared resource dependency",
                }
            ],
            circle_relations=[
                {
                    "relation_id": "REL-1",
                    "from_circle_id": "CIRCLE-FAMILY",
                    "to_circle_id": "CIRCLE-TEAM",
                    "relation_type": "resource-transfer",
                    "direction": "directed",
                }
            ],
            clocks=[
                {
                    "clock_id": "CLOCK-1",
                    "scope_id": "CIRCLE-TEAM",
                    "kind": "organizational",
                    "current_time": STAMP,
                    "horizon": "P90D",
                }
            ],
            channels=[
                {
                    "channel_id": "CHANNEL-1",
                    "from_position_id": "POS-TEAM-MANAGER",
                    "to_position_id": "POS-TEAM-MANAGER",
                    "channel_type": "decision",
                    "active": True,
                    "capacity": "one reviewed decision per cycle",
                    "delay": "one review cycle",
                    "threshold": "manager approval",
                    "constraint_distribution": "DIST-CONSTRAINT-1",
                    "access_distribution": "Only the represented manager position can transmit.",
                }
            ],
            events=[
                {
                    "event_id": "WORLD-EVENT-1",
                    "source_position_id": "POS-TEAM-MANAGER",
                    "target_position_ids": ["POS-TEAM-MANAGER"],
                    "channel_ids": ["CHANNEL-1"],
                }
            ],
            local_distributions=[
                {
                    "distribution_id": "DIST-POWER-1",
                    "kind": "power",
                    "location_ref": "MEMBERSHIP-1",
                    "description": "Decision power is local to the team membership.",
                },
                {
                    "distribution_id": "DIST-CONSTRAINT-1",
                    "kind": "constraint",
                    "location_ref": "CHANNEL-1",
                    "description": "Approval constrains the decision channel.",
                },
                {
                    "distribution_id": "DIST-EXIT-1",
                    "kind": "exit",
                    "location_ref": "MEMBERSHIP-1",
                    "description": "Exit requires a handoff at this membership.",
                },
                {
                    "distribution_id": "DIST-BURDEN-1",
                    "kind": "burden",
                    "location_ref": "M-POS-1",
                    "description": "Review effort is borne at the manager position.",
                },
                {
                    "distribution_id": "DIST-SPILLOVER-1",
                    "kind": "spillover",
                    "location_ref": "PSI-POS-1",
                    "description": "Review meaning can spill over into perceived legitimacy.",
                },
            ],
            unknowns=[
                {
                    "unknown_id": "UNKNOWN-1",
                    "location_ref": "POS-TEAM-MANAGER",
                    "description": "Response latency is unknown.",
                }
            ],
            residuals=[
                {
                    "residual_id": "RESIDUAL-1",
                    "location_ref": "CIRCLE-TEAM",
                    "description": "Unmodeled peer effect.",
                }
            ],
        ),
        "ultra-transformation-ledger.schema.json": artifact(
            "ultra-transformation-ledger.schema.json",
            phase_id="U5",
            source_volume_sha256=HASH_A,
            transformations=[
                {
                    "transform_id": "TRANSFORM-1",
                    "kind": "scale",
                    "input_identity": "POS-TEAM-MANAGER@interaction",
                    "output_identity": "POS-TEAM-MANAGER@organizational",
                    "preserved": ["actor identity"],
                    "changed": ["time horizon"],
                    "folded": [],
                    "omitted": [],
                    "unknown": ["long-term response"],
                    "task_relative_loss": [
                        {
                            "loss_id": "LOSS-1",
                            "description": "Interaction detail is aggregated.",
                            "location_ref": "POS-TEAM-MANAGER",
                        }
                    ],
                    "location_effects": [
                        {
                            "effect_id": "EFFECT-GAIN-1",
                            "location_ref": "POS-TEAM-MANAGER",
                            "effect_kind": "gain",
                            "description": "The organizational view exposes the decision mandate.",
                        },
                        {
                            "effect_id": "EFFECT-DAMAGE-1",
                            "location_ref": "POS-TEAM-MANAGER",
                            "effect_kind": "damage",
                            "description": "Interaction detail is obscured at the position.",
                        },
                        {
                            "effect_id": "EFFECT-EXIT-1",
                            "location_ref": "MEMBERSHIP-1",
                            "effect_kind": "exit-cost",
                            "description": "A handoff is required before exit.",
                        },
                        {
                            "effect_id": "EFFECT-SPILLOVER-1",
                            "location_ref": "CIRCLE-FAMILY",
                            "effect_kind": "spillover",
                            "description": "Organizational delay can consume shared time.",
                        },
                    ],
                    "effective_variables": ["budget", "rule"],
                    "closure_status": "bounded",
                    "residual_ids": ["RESIDUAL-1"],
                    "return_conditions": ["material residual changes verdict"],
                }
            ],
        ),
        "ultra-concept-disposition.schema.json": artifact(
            "ultra-concept-disposition.schema.json",
            phase_id="U5",
            registry_sha256=HASH_A,
            dispositions=[
                {
                    "concept_id": "V82-CONCEPT-CHANNEL",
                    "status": "applied",
                    "rationale": "A concrete decision channel reaches the position.",
                    "route_required": True,
                    "neighbor_concept_ids": [],
                    "semantic_unit_ids": ["UNIT-CHANNEL-1"],
                    "condition_branch": None,
                    "evidence_plan": None,
                }
            ],
            unvisited_concept_ids=[],
            closure_complete=True,
        ),
        "ultra-claim-mechanism-graph.schema.json": artifact(
            "ultra-claim-mechanism-graph.schema.json",
            phase_id="U6",
            central_claim_id="CLAIM-1",
            claims=[
                {
                    "claim_id": "CLAIM-1",
                    "statement": "The decision channel changes the local action set.",
                    "identity": "inferred-from-material",
                    "evidence_refs": ["EVIDENCE-1"],
                    "status": "active",
                }
            ],
            mechanisms=[
                {
                    "mechanism_id": "MECHANISM-1",
                    "description": "Delegated authority changes available actions.",
                    "input_refs": ["CLAIM-1"],
                    "output_refs": ["POS-TEAM-MANAGER"],
                    "channel_refs": ["CHANNEL-1"],
                    "evidence_refs": ["EVIDENCE-1"],
                }
            ],
            edges=[
                {
                    "from_id": "CLAIM-1",
                    "to_id": "MECHANISM-1",
                    "edge_type": "supported-by",
                }
            ],
            explanations=[
                {
                    "explanation_id": "EXPLANATION-MAIN",
                    "kind": "main",
                    "claim_ids": ["CLAIM-1"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "rank": 1,
                }
            ],
            insights=[
                {
                    "insight_id": "INSIGHT-1",
                    "effects": ["changes-intervention"],
                    "reason": "The channel identifies a reversible intervention point.",
                }
            ],
        ),
        "ultra-recursive-lineage.schema.json": artifact(
            "ultra-recursive-lineage.schema.json",
            phase_id="U7",
            parent_volume_sha256=HASH_A,
            nodes=[
                {
                    "node_id": "NODE-1",
                    "parent_node_ids": [],
                    "order": 1,
                    "state_sha256": HASH_B,
                    "inherited_unknown_ids": ["UNKNOWN-1"],
                    "inherited_loss_ids": ["LOSS-1"],
                    "inherited_residual_ids": ["RESIDUAL-1"],
                    "event_id": "WORLD-EVENT-1",
                    "mechanism_ids": ["MECHANISM-1"],
                    "state_diff_sha256": HASH_C,
                    "signal_refs": ["SIGNAL-1"],
                    "evidence_identity": "simulated-result",
                }
            ],
            branches=[
                {
                    "branch_id": "BRANCH-MAIN",
                    "kind": "main",
                    "node_ids": ["NODE-1"],
                    "status": "active",
                    "merge_parent_ids": [],
                    "prune_reason": None,
                    "retained_residual_ids": ["RESIDUAL-1"],
                }
            ],
            maximum_order=1,
        ),
        "ultra-order-evaluation.schema.json": artifact(
            "ultra-order-evaluation.schema.json",
            phase_id="U8",
            lineage_sha256=HASH_A,
            evaluations=[
                {
                    "order": 1,
                    "branch_kinds": [
                        "main",
                        "strongest-rival",
                        "mixture",
                        "residual",
                    ],
                    "baseline": {
                        "baseline_id": "BASELINE-1",
                        "description": "No state-changing channel.",
                    },
                    "explanation_gain": "Adds a reachable mechanism.",
                    "forecast_gain": "Adds a resolvable signal.",
                    "added_assumptions": ["Delegated authority remains active."],
                    "added_losses": ["LOSS-1"],
                    "local_predictability": "bounded",
                    "continue_recursive": False,
                    "stop_kind": "no-material-state-change",
                    "rationale": "The next order adds no material state change.",
                }
            ],
        ),
        "ultra-red-team-report.schema.json": artifact(
            "ultra-red-team-report.schema.json",
            phase_id="U8",
            target_graph_sha256=HASH_A,
            attacks=[
                {
                    "attack_id": "ATTACK-1",
                    "target_ref": "CLAIM-1",
                    "attack_kind": "strongest-counterexample",
                    "challenge": "The channel may be nominal rather than effective.",
                    "evidence_refs": ["EVIDENCE-1"],
                    "result": "revise",
                }
            ],
            sensitivity_checks=[
                {
                    "check_id": "SENSITIVITY-1",
                    "variable": "channel activity",
                    "variation": "inactive",
                    "outcome": "main explanation loses rank",
                }
            ],
            baseline_comparisons=[
                {"order": 1, "baseline_ref": "BASELINE-1", "winner": "lineage"}
            ],
            unresolved_attack_ids=[],
            overall_status="revised",
        ),
        "ultra-verdict.schema.json": artifact(
            "ultra-verdict.schema.json",
            phase_id="U9",
            decidability="decidable",
            main_verdict={
                "proposition": "The active channel currently best explains the action change.",
                "scope": "The represented team position and frozen time window.",
                "epistemic_identity": "inferred-from-material",
                "confidence": "low",
                "decisive_reason_ids": ["EVIDENCE-1", "MECHANISM-1"],
                "strongest_rival_id": "EXPLANATION-RIVAL",
                "rival_rejection_reasons": ["It does not explain the reachable channel."],
                "residual_ids": ["RESIDUAL-1"],
                "reversal_conditions": ["The channel is shown to be inactive."],
                "time_window": "P90D",
                "indicator_ids": ["INDICATOR-1"],
                "action_implication": "Use a reversible probe.",
                "distributions": [
                    {
                        "circle_id": "CIRCLE-TEAM",
                        "benefits": ["faster feedback"],
                        "harms": ["local coordination cost"],
                        "responsibility": ["team lead monitors"],
                        "spillovers": ["family time pressure"],
                    }
                ],
            },
            explanation_ranking=[
                {"explanation_id": "EXPLANATION-MAIN", "rank": 1},
                {"explanation_id": "EXPLANATION-RIVAL", "rank": 2},
                {"explanation_id": "EXPLANATION-MIXTURE", "rank": 3},
                {"explanation_id": "EXPLANATION-RESIDUAL", "rank": 4},
            ],
            five_verdicts=[
                {
                    "kind": kind,
                    "proposition": f"Bounded {kind} judgment.",
                    "basis_refs": ["EVIDENCE-1"],
                    "status": "locked",
                }
                for kind in (
                    "fact",
                    "prediction",
                    "value",
                    "responsibility",
                    "authorization",
                )
            ],
            assumptions=["The declared channel remains active."],
            decisive_unknown_ids=[],
        ),
        "ultra-action-ranking.schema.json": artifact(
            "ultra-action-ranking.schema.json",
            phase_id="U9",
            requested_choice=True,
            options=[
                {
                    "option_id": "OPTION-PROBE",
                    "kind": "probe",
                    "description": "Run a reversible probe.",
                    "authorized": True,
                    "benefits": ["new evidence"],
                    "harms": ["small coordination cost"],
                    "requirements": ["team consent"],
                    "rollback": "Stop after one review cycle.",
                },
                {
                    "option_id": "OPTION-NO-ACTION",
                    "kind": "no-action",
                    "description": "Take no action this cycle.",
                    "authorized": True,
                    "benefits": ["no immediate disruption"],
                    "harms": ["unknown remains unresolved"],
                    "requirements": [],
                    "rollback": "Not applicable.",
                },
            ],
            ranking=["OPTION-PROBE", "OPTION-NO-ACTION"],
            preferred_option_id="OPTION-PROBE",
            second_option_id="OPTION-NO-ACTION",
            switch_conditions=["Switch if authorization is withdrawn."],
            stop_conditions=["Stop if harm exceeds the bounded threshold."],
            no_action_consequences=["The decisive unknown remains."],
        ),
        "ultra-forecast-ledger.schema.json": artifact(
            "ultra-forecast-ledger.schema.json",
            phase_id="U9",
            forecasts=[
                {
                    "forecast_id": "FORECAST-1",
                    "direction": "increase",
                    "time_window": "P90D",
                    "indicator": "recorded feedback events",
                    "resolution_rule": "Resolve increase if count exceeds the frozen baseline.",
                    "evidence_cutoff": STAMP,
                    "branch_refs": ["BRANCH-MAIN"],
                    "node_refs": ["NODE-1"],
                    "status": "open",
                    "probability": None,
                    "reference_class": None,
                    "calibration_basis": None,
                    "probability_admissible": False,
                }
            ],
            resolutions=[],
        ),
        "ultra-framework-gap-ledger.schema.json": artifact(
            "ultra-framework-gap-ledger.schema.json",
            phase_id="U9",
            candidates=[
                {
                    "gap_id": "GAP-1",
                    "description": "The framework has no calibrated latency prior.",
                    "current_run_refs": ["UNKNOWN-1"],
                    "evidence_refs": ["EVIDENCE-1"],
                    "future_revision_proposal": "Add a latency calibration contract.",
                    "status": "candidate",
                }
            ],
            isolated_from_current_reasoning=True,
        ),
        "ultra-output-plan.schema.json": artifact(
            "ultra-output-plan.schema.json",
            phase_id="U10",
            article_path="delivery/CrossFrame-Ultra-完整文章.partial.md",
            sections=[
                {
                    "section_id": "SECTION-1",
                    "title": "主判断、范围与置信度",
                    "ordinal": 1,
                    "semantic_unit_ids": ["UNIT-VERDICT-1"],
                    "dependency_hashes": [HASH_A],
                }
            ],
            appendices=[
                {
                    "section_id": "APPENDIX-1",
                    "title": "未知项与框架缺口候选",
                    "ordinal": 11,
                    "semantic_unit_ids": ["UNIT-GAP-1"],
                    "dependency_hashes": [HASH_B],
                }
            ],
            required_artifacts=["ultra-verdict.json", "ultra-action-ranking.json"],
            coverage_required=True,
            official_filename_allowed=False,
        ),
        "ultra-semantic-coverage.schema.json": artifact(
            "ultra-semantic-coverage.schema.json",
            phase_id="U10",
            article_sha256=HASH_A,
            required_unit_kinds=[
                "claim",
                "evidence",
                "unknown",
                "circle-relation",
                "scale-transform",
                "translation-loss",
                "mechanism",
                "branch",
                "residual",
                "forecast",
                "verdict",
                "action",
                "reversal-condition",
            ],
            mappings=[
                {
                    "unit_id": "UNIT-VERDICT-1",
                    "unit_kind": "verdict",
                    "section_id": "SECTION-1",
                    "normalized_excerpt": "当前主判断是可逆探测优先。",
                    "source_refs": ["CLAIM-1", "EVIDENCE-1"],
                }
            ],
            missing_unit_ids=[],
            coverage_percent=100,
            coverage_complete=True,
        ),
        "ultra-article-review.schema.json": artifact(
            "ultra-article-review.schema.json",
            phase_id="U11",
            article_sha256=HASH_A,
            coverage_sha256=HASH_B,
            blind_reader_fields=[
                {
                    "field_id": "main_verdict",
                    "recovered": True,
                    "excerpt": "当前主判断是可逆探测优先。",
                }
            ],
            quality_checks=[
                {
                    "check_id": "no-external-dependency",
                    "status": "pass",
                    "evidence": "All decisive units occur in the article.",
                }
            ],
            external_dependencies=[],
            overall_status="pass",
            official_filename_allowed=False,
        ),
        "ultra-recovery-checkpoint.schema.json": artifact(
            "ultra-recovery-checkpoint.schema.json",
            phase_id="U7",
            phase_event_sha256=HASH_A,
            artifact_hashes=[
                {
                    "path": "artifacts/U06-U08-inference/lineage.json",
                    "sha256": HASH_B,
                    "media_type": "application/json",
                }
            ],
            evidence_cutoff=STAMP,
            completed_boundary=True,
            resumable=True,
        ),
        "ultra-artifact-manifest.schema.json": artifact(
            "ultra-artifact-manifest.schema.json",
            phase_id="U12",
            phase_chain_head_sha256=HASH_A,
            validator_set_sha256=HASH_B,
            artifacts=[
                {
                    "path": "artifacts/U09-U10-verdict/verdict.json",
                    "sha256": HASH_C,
                    "schema_id": "crossframe.ultra.v82.verdict",
                    "phase_id": "U9",
                    "media_type": "application/json",
                }
            ],
            delivery_artifacts=[
                {
                    "path": "delivery/CrossFrame-Ultra-完整文章.partial.md",
                    "sha256": HASH_A,
                    "media_type": "text/markdown",
                }
            ],
            official_delivery_published=False,
        ),
        "ultra-validator-report.schema.json": artifact(
            "ultra-validator-report.schema.json",
            phase_id="U12",
            attempt_id="VALIDATION-1",
            manifest_sha256=HASH_A,
            validator_set_sha256=HASH_B,
            checks=[
                {
                    "validator_id": "schema-closure",
                    "status": "pass",
                    "error_codes": [],
                    "artifact_refs": ["ultra-verdict.json"],
                }
            ],
            overall_status="pass",
            validated_at=STAMP,
            fresh_context=True,
        ),
        "ultra-repair-plan.schema.json": artifact(
            "ultra-repair-plan.schema.json",
            phase_id="U12",
            failed_report_sha256=HASH_A,
            attempt_number=1,
            failures=[
                {
                    "error_code": "ULTRA-COVERAGE-MISSING",
                    "artifact": "delivery/article.partial.md",
                    "affected_phase": "U10",
                    "downstream_reset": ["U10", "U11", "U12"],
                    "retryable": True,
                    "repair_action": "regenerate_missing_semantic_unit_packet",
                }
            ],
            reset_from_phase="U10",
            preserved_artifact_hashes=[HASH_B],
            repair_actions=["regenerate_missing_semantic_unit_packet"],
            manifest_regeneration_required=True,
            revalidation_required=True,
            status="planned",
        ),
    }
    assert set(fixtures) == set(ARTIFACT_SCHEMAS)
    return fixtures


PRIMARY_FIELD = {
    "ultra-release-manifest.schema.json": "release_id",
    "ultra-compatibility-matrix.schema.json": "rules",
    "ultra-run-contract.schema.json": "capabilities",
    "ultra-run-status.schema.json": "status",
    "ultra-phase-event.schema.json": "event_sha256",
    "ultra-source-lock.schema.json": "inputs",
    "ultra-read-event.schema.json": "read_event_sha256",
    "ultra-evidence-ledger.schema.json": "entries",
    "ultra-retrieval-ledger.schema.json": "entries",
    "ultra-world-volume.schema.json": "positions",
    "ultra-transformation-ledger.schema.json": "transformations",
    "ultra-concept-disposition.schema.json": "dispositions",
    "ultra-claim-mechanism-graph.schema.json": "mechanisms",
    "ultra-recursive-lineage.schema.json": "nodes",
    "ultra-order-evaluation.schema.json": "evaluations",
    "ultra-red-team-report.schema.json": "attacks",
    "ultra-verdict.schema.json": "main_verdict",
    "ultra-action-ranking.schema.json": "options",
    "ultra-forecast-ledger.schema.json": "forecasts",
    "ultra-framework-gap-ledger.schema.json": "candidates",
    "ultra-output-plan.schema.json": "sections",
    "ultra-semantic-coverage.schema.json": "mappings",
    "ultra-article-review.schema.json": "blind_reader_fields",
    "ultra-recovery-checkpoint.schema.json": "phase_event_sha256",
    "ultra-artifact-manifest.schema.json": "artifacts",
    "ultra-validator-report.schema.json": "checks",
    "ultra-repair-plan.schema.json": "failures",
}


def load_runtime():
    scripts = str(RUNTIME_SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module("ultra_runtime")


def walk_dict_paths(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    if isinstance(value, dict):
        yield path
        for key, child in value.items():
            yield from walk_dict_paths(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_dict_paths(child, path + (index,))


def dict_at(value: Any, path: tuple[Any, ...]) -> dict[str, Any]:
    current = value
    for part in path:
        current = current[part]
    assert isinstance(current, dict)
    return current


def test_every_ultra_schema_is_closed_and_valid() -> None:
    assert SCHEMA_ROOT.is_dir(), "Ultra schema directory is missing"
    paths = sorted(SCHEMA_ROOT.glob("*.schema.json"))
    assert tuple(path.name for path in paths) == EXPECTED_SCHEMA_NAMES
    for path in paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == f"https://crossframe.local/schemas/{path.name}"
        assert schema.get("additionalProperties") is False or schema.get(
            "unevaluatedProperties"
        ) is False


def test_common_schema_current_binding_matches_runtime_constants() -> None:
    runtime = load_runtime()
    constants = importlib.import_module("ultra_runtime.constants")
    common = runtime.load_schema("ultra-common.schema.json")
    properties = common["$defs"]["currentVersionBinding"]["allOf"][1][
        "properties"
    ]
    schema_binding = {field: definition["const"] for field, definition in properties.items()}
    assert schema_binding == constants.current_version_binding()


@pytest.mark.parametrize(
    ("fixture_name", "schema_name", "schema_id", "phase_id"),
    (
        (
            "evidence-ledger-valid.json",
            "ultra-evidence-ledger.schema.json",
            "crossframe.ultra.v82.evidence-ledger",
            "U3",
        ),
        (
            "world-volume-valid.json",
            "ultra-world-volume.schema.json",
            "crossframe.ultra.v82.world-volume",
            "U4",
        ),
        (
            "transformation-valid.json",
            "ultra-transformation-ledger.schema.json",
            "crossframe.ultra.v82.transformation-ledger",
            "U5",
        ),
    ),
)
def test_phase_fixture_envelope_and_content_hash_bind_external_authority(
    fixture_name: str,
    schema_name: str,
    schema_id: str,
    phase_id: str,
) -> None:
    schemas = importlib.import_module("ultra_runtime.schemas")
    artifact_value = json.loads(
        (RUNTIME_FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8")
    )

    validated = schemas.validate_phase_artifact(
        schema_name,
        artifact_value,
        expected_schema_id=schema_id,
        expected_run_id="ultra-task8-run",
        expected_version_binding=version_binding(),
        expected_phase_id=phase_id,
    )
    assert validated == artifact_value


def test_phase_artifact_rejects_payload_change_with_old_hash() -> None:
    schemas = importlib.import_module("ultra_runtime.schemas")
    artifact_value = json.loads(
        (RUNTIME_FIXTURE_ROOT / "evidence-ledger-valid.json").read_text(
            encoding="utf-8"
        )
    )
    artifact_value["entries"][0]["statement"] += " changed"

    with pytest.raises(schemas.UltraSchemaError, match="content_sha256"):
        schemas.validate_phase_artifact(
            "ultra-evidence-ledger.schema.json",
            artifact_value,
            expected_schema_id="crossframe.ultra.v82.evidence-ledger",
            expected_run_id="ultra-task8-run",
            expected_version_binding=version_binding(),
            expected_phase_id="U3",
        )


@pytest.mark.parametrize("mutation", ("run", "version", "phase", "authority"))
def test_self_rehashed_artifact_cannot_choose_its_expected_authority(
    mutation: str,
) -> None:
    import hashlib

    schemas = importlib.import_module("ultra_runtime.schemas")
    artifact_value = json.loads(
        (RUNTIME_FIXTURE_ROOT / "evidence-ledger-valid.json").read_text(
            encoding="utf-8"
        )
    )
    if mutation == "run":
        artifact_value["run_id"] = "attacker-selected-run"
    elif mutation == "version":
        artifact_value["version_binding"]["source_tree_sha256"] = "e" * 64
    elif mutation == "phase":
        artifact_value["phase_id"] = "U4"
    else:
        artifact_value["schema_id"] = "crossframe.ultra.v82.world-volume"
    payload = copy.deepcopy(artifact_value)
    payload.pop("content_sha256")
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    artifact_value["content_sha256"] = hashlib.sha256(
        (canonical + "\n").encode("utf-8")
    ).hexdigest()

    with pytest.raises((schemas.UltraSchemaError, ValidationError)):
        schemas.validate_phase_artifact(
            "ultra-evidence-ledger.schema.json",
            artifact_value,
            expected_schema_id="crossframe.ultra.v82.evidence-ledger",
            expected_run_id="ultra-task8-run",
            expected_version_binding=version_binding(),
            expected_phase_id="U3",
        )


def test_schema_ids_are_unique_and_isolated_from_max_and_promax() -> None:
    ultra_ids = []
    for path in SCHEMA_ROOT.glob("*.schema.json"):
        ultra_ids.append(json.loads(path.read_text(encoding="utf-8"))["$id"])
    assert len(ultra_ids) == len(set(ultra_ids))
    assert all("/ultra-" in schema_id for schema_id in ultra_ids)

    existing_ids = set()
    for runtime_name in ("crossframe-max", "crossframe-promax"):
        for path in (ROOT / "skills" / runtime_name / "schemas").glob("*.json"):
            document = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(document, dict) and isinstance(document.get("$id"), str):
                existing_ids.add(document["$id"])
    assert set(ultra_ids).isdisjoint(existing_ids)


def test_each_artifact_schema_has_a_real_minimal_valid_instance() -> None:
    runtime = load_runtime()
    fixtures = minimal_instances()
    assert set(fixtures) == set(ARTIFACT_SCHEMAS)
    assert len({fixture["schema_id"] for fixture in fixtures.values()}) == len(fixtures)
    for schema_name, fixture in fixtures.items():
        runtime.validate_instance(schema_name, fixture)


def test_every_artifact_requires_envelope_and_its_primary_payload() -> None:
    runtime = load_runtime()
    for schema_name, fixture in minimal_instances().items():
        for field in (
            "schema_id",
            "schema_version",
            "run_id",
            "version_binding",
            "generated_at",
            "content_sha256",
            PRIMARY_FIELD[schema_name],
        ):
            broken = copy.deepcopy(fixture)
            del broken[field]
            with pytest.raises(ValidationError):
                runtime.validate_instance(schema_name, broken)


def test_runtime_artifact_schemas_reject_unknown_fields() -> None:
    runtime = load_runtime()
    for schema_name, fixture in minimal_instances().items():
        broken = copy.deepcopy(fixture)
        broken["unexpected"] = True
        with pytest.raises(ValidationError):
            runtime.validate_instance(schema_name, broken)


def test_critical_nested_objects_reject_unknown_fields() -> None:
    runtime = load_runtime()
    for schema_name, fixture in minimal_instances().items():
        nested_paths = [path for path in walk_dict_paths(fixture) if path]
        assert nested_paths, schema_name
        for path in nested_paths:
            broken = copy.deepcopy(fixture)
            dict_at(broken, path)["unexpected"] = True
            with pytest.raises(ValidationError):
                runtime.validate_instance(schema_name, broken)


def test_bad_hash_version_phase_status_and_timestamp_are_rejected() -> None:
    runtime = load_runtime()
    valid = minimal_instances()["ultra-run-status.schema.json"]
    mutations = (
        (("content_sha256",), "A" * 64),
        (("version_binding", "framework_version"), "8.0"),
        (("version_binding", "framework_revision"), "v8.2-r2"),
        (("version_binding", "framework_raw_sha256"), HASH_A),
        (("version_binding", "framework_semantic_sha256"), HASH_B),
        (("version_binding", "runtime_version"), "1.0.1"),
        (("version_binding", "artifact_schema_version"), 2),
        (("phase_id",), "U13"),
        (("status",), "done"),
        (("generated_at",), "not-a-date"),
    )
    for path, value in mutations:
        broken = copy.deepcopy(valid)
        target: Any = broken
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-run-status.schema.json", broken)


def test_world_volume_and_forecast_nested_negative_cases() -> None:
    runtime = load_runtime()
    fixtures = minimal_instances()

    flat = copy.deepcopy(fixtures["ultra-world-volume.schema.json"])
    flat["global_M"] = {"budget": 1}
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", flat)

    missing_identity = copy.deepcopy(fixtures["ultra-world-volume.schema.json"])
    del missing_identity["positions"][0]["identity_criteria"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", missing_identity)

    missing_local_state = copy.deepcopy(fixtures["ultra-world-volume.schema.json"])
    del missing_local_state["actors"][0]["M_state"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", missing_local_state)

    overloaded_evidence_status = copy.deepcopy(
        fixtures["ultra-world-volume.schema.json"]
    )
    overloaded_evidence_status["actors"][0]["evidence_status"][
        "power_distribution"
    ] = "must remain local to Rac, Q, M or Psi"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-world-volume.schema.json", overloaded_evidence_status
        )

    net_effect_only = copy.deepcopy(
        fixtures["ultra-transformation-ledger.schema.json"]
    )
    del net_effect_only["transformations"][0]["location_effects"]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-transformation-ledger.schema.json", net_effect_only
        )

    uncalibrated = copy.deepcopy(fixtures["ultra-forecast-ledger.schema.json"])
    forecast = uncalibrated["forecasts"][0]
    forecast["probability"] = 0.73
    forecast["probability_admissible"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-forecast-ledger.schema.json", uncalibrated)


def test_task7_runtime_phase_and_read_events_conform_to_public_schemas() -> None:
    runtime = load_runtime()
    state_machine = importlib.import_module("ultra_runtime.state_machine")
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": HASH_A,
        "run_mode": "test",
        "sensitivity": "public",
        "retention": "retain",
        "outbound_permission": "denied",
        "evidence_cutoff": STAMP,
        "capabilities": {
            "filesystem": "available",
            "docx_parser": "available",
            "network": "unavailable",
            "retrieval": "not-applicable",
            "validators": "available",
            "subagents": "unavailable",
            "model_context": "available",
        },
        "resource_limits": {
            "maximum_branches": 8,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }
    store = state_machine.PhaseStore(
        run_id=RUN_ID,
        version_binding=version_binding(),
        source_sha256=HASH_B,
        input_artifact_hashes=(HASH_C,),
        evidence_cutoff=STAMP,
        now=datetime(2026, 8, 2, 8, tzinfo=timezone.utc),
        run_contract=contract,
    )
    phase_event = store.complete("U0", artifact_hashes=(HASH_A,))
    runtime.validate_instance("ultra-phase-event.schema.json", phase_event)

    source_manifest = source_integrity.load_source_manifest(
        ULTRA_ROOT / "references" / "source-manifest.json"
    )
    read_receipt = source_integrity.capture_committed_read_receipts(
        ROOT,
        manifest=source_manifest,
    )[0]
    read_event = source_integrity.make_read_event(
        run_id=RUN_ID,
        version_binding=version_binding(),
        source_unit=read_receipt.source_unit,
        promoted_semantic_snapshot_sha256=source_manifest.semantic_sha256,
        source_manifest_sha256=source_manifest.sha256,
        reader_mode="full-source",
        execution_identity=source_integrity.execution_identity(),
        read_at=STAMP,
        receipt=read_receipt,
    )
    runtime.validate_instance("ultra-read-event.schema.json", read_event)


def test_local_ref_registry_resolves_without_network() -> None:
    runtime = load_runtime()
    registry = runtime.build_schema_registry()
    for schema_name in EXPECTED_SCHEMA_NAMES:
        schema_id = f"https://crossframe.local/schemas/{schema_name}"
        assert registry.get(schema_id) is not None
    runtime.validate_instance(
        "ultra-run-status.schema.json",
        minimal_instances()["ultra-run-status.schema.json"],
    )


def test_public_schema_registries_are_concurrently_isolated() -> None:
    runtime = load_runtime()
    schema_id = (
        "https://crossframe.local/schemas/ultra-run-status.schema.json"
    )

    def build_registry(_: int):
        return runtime.build_schema_registry()

    with ThreadPoolExecutor(max_workers=8) as executor:
        registries = list(executor.map(build_registry, range(8)))

    documents = [registry.get(schema_id).contents for registry in registries]
    assert len({id(registry) for registry in registries}) == len(registries)
    assert len({id(document) for document in documents}) == len(documents)

    original = copy.deepcopy(documents[0])
    try:
        documents[0].clear()
        assert documents[1]["$id"] == schema_id
    finally:
        documents[0].update(original)


def test_public_registry_pollution_cannot_change_internal_validation() -> None:
    runtime = load_runtime()
    schema_name = "ultra-run-status.schema.json"
    schema_id = f"https://crossframe.local/schemas/{schema_name}"
    public_document = runtime.build_schema_registry().get(schema_id).contents
    original = copy.deepcopy(public_document)
    try:
        public_document.clear()
        with pytest.raises(ValidationError):
            runtime.validate_instance(schema_name, {})
    finally:
        public_document.update(original)


def test_schema_registry_rejects_unknown_uri_retrieval() -> None:
    runtime = load_runtime()
    registry = runtime.build_schema_registry()
    with pytest.raises(NoSuchResource):
        registry.get_or_retrieve(
            "https://crossframe.local/schemas/ultra-unknown.schema.json"
        )


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "safe\n../../../escape.json",
        "safe\tartifact.json",
        "artifact.json:stream",
        "artifact<draft>.json",
        'artifact"draft.json',
        "artifact|draft.json",
        "artifact?.json",
        "artifact*.json",
        "/absolute/artifact.json",
        "C:\\absolute\\artifact.json",
        "\\\\server\\share\\artifact.json",
        "\\\\?\\C:\\artifact.json",
        "dir//artifact.json",
        "dir\\\\artifact.json",
        "dir/./artifact.json",
        "dir\\..\\artifact.json",
        "dir./artifact.json",
        "dir/artifact.json ",
        "CON",
        "nul.json",
        "dir/COM1.log",
        "dir/lPt9",
    ),
)
def test_relative_paths_reject_control_platform_and_segment_escapes(
    unsafe_path: str,
) -> None:
    runtime = load_runtime()
    broken = copy.deepcopy(minimal_instances()["ultra-source-lock.schema.json"])
    broken["inputs"][0]["path"] = unsafe_path
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-source-lock.schema.json", broken)


@pytest.mark.parametrize(
    "safe_path",
    (
        "delivery/article.partial.md",
        "nested\\artifact.json",
        ".hidden/artifact.json",
        "foo..bar/artifact.json",
    ),
)
def test_relative_paths_accept_safe_portable_segments(safe_path: str) -> None:
    runtime = load_runtime()
    instance = copy.deepcopy(minimal_instances()["ultra-source-lock.schema.json"])
    instance["inputs"][0]["path"] = safe_path
    runtime.validate_instance("ultra-source-lock.schema.json", instance)


@pytest.mark.parametrize(
    "unsafe_name",
    (
        "../ultra-common.schema.json",
        "..\\ultra-common.schema.json",
        "schemas/ultra-common.schema.json",
        "E:\\ultra-common.schema.json",
        "ultra-common.schema.json/extra",
        "not-listed.schema.json",
        "",
    ),
)
def test_schema_loader_rejects_path_traversal_and_non_whitelisted_names(
    unsafe_name: str,
) -> None:
    runtime = load_runtime()
    with pytest.raises(runtime.UltraSchemaError):
        runtime.load_schema(unsafe_name)
