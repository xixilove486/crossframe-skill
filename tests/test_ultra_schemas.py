from __future__ import annotations

import copy
import importlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterator

from tests.pytest_import_guard import pytest
from jsonschema import Draft202012Validator, ValidationError
from referencing.exceptions import NoSuchResource


ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = ROOT / "skills/crossframe-ultra"
SCHEMA_ROOT = ULTRA_ROOT / "schemas"
RUNTIME_SCRIPTS = ULTRA_ROOT / "scripts"

FRAMEWORK_RAW_SHA256 = (
    "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20"
)
FRAMEWORK_SEMANTIC_SHA256 = (
    "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0"
)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
HASH_F = "f" * 64
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64
HASH_3 = "3" * 64
HASH_4 = "4" * 64
HASH_5 = "5" * 64
HASH_6 = "6" * 64
HASH_7 = "7" * 64
SOURCE_TREE_SHA256 = (
    "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187"
)
STAMP = "2026-08-02T08:00:00Z"
RUN_ID = "ultra-run-20260802-0001"

OUTPUT_PLAN_SECTION_TITLES = (
    "主判断、范围和置信度",
    "用户观点的最强重建",
    "事实、证据、来源关系和未知项",
    "立体多圈层联合状态",
    "机制、真实通道和跨圈层级联",
    "竞争解释与排序",
    "一阶、二阶、三阶推演",
    "每阶简单基线、增量和停止理由",
    "事实、预测、价值、责任、授权裁决",
    "行动、不行动、切换和反转条件",
)
OUTPUT_PLAN_APPENDIX_TITLES = (
    "圈层—角色—尺度映射",
    "分支、合并、剪枝、残差和停止点",
    "预测、时间窗、指标和解析条件",
    "概念、证据和来源锚点",
    "未知项与框架缺口候选",
)
BLIND_RECOVERY_FIELD_IDS = (
    "main_verdict",
    "confidence",
    "steelmanned_user_position",
    "decisive_evidence",
    "unknowns",
    "circle_relations",
    "mechanisms",
    "strongest_rival",
    "order_1",
    "order_2",
    "order_3",
    "five_verdicts",
    "action",
    "residuals",
    "reversal_conditions",
)
SEMANTIC_UNIT_KINDS = (
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
)
QUALITY_CHECK_IDS = (
    "reader-contract",
    "repeated-paragraph",
    "template-language",
    "jargon-before-explanation",
    "unresolved-pronoun",
    "unsupported-certainty",
    "truncation-promise",
    "machine-dump",
    "independent-article",
    "semantic-coverage",
    "blind-recovery",
)
SEMANTIC_REVIEW_DIMENSION_IDS = (
    "direct-answer",
    "evidence-boundary",
    "current-judgment",
    "mechanism-competition",
    "recursive-expansion",
    "residuals",
    "reversal-conditions",
    "action-comparison",
    "concept-fidelity",
)
RETRIEVAL_TRIGGER_KINDS = (
    "real-world",
    "time-sensitive",
    "legal",
    "medical",
    "financial",
    "political",
    "product",
    "policy",
    "institutional",
    "current-fact",
)
RETRIEVAL_BLOCK_CLASSES = (
    "network-unavailable",
    "outbound-denied",
    "retry-exhaustion",
    "rate-limit",
    "timeout",
    "resource-condition",
)
PROMOTED_RAC_FIELDS = (
    "actor_ref",
    "circle_ref",
    "membership_basis",
    "start_time",
    "end_time",
    "roles",
    "commitment_strength",
    "actual_participation",
    "exit_ability",
    "dispute_status",
    "evidence_status",
    "source_refs",
)
PROMOTED_RCC_FIELDS = (
    "source_circle_ref",
    "target_circle_ref",
    "direction",
    "relation_type",
    "shared_members_or_interfaces",
    "channel",
    "strength_or_scope",
    "time_window",
    "delay",
    "threshold",
    "evidence_refs",
    "counterexample_refs",
    "failure_conditions",
)
SCALE_AXIS_IDS = ("A", "X", "T", "O", "C", "R", "I", "N", "J")
AXIS_RELATIONS = ("equal", "expands", "contracts", "incomparable", "unknown")
AXIS_MISSING_STATUSES = (
    "unknown",
    "not_applicable",
    "not_observable",
    "withheld_for_protection",
)
COMPARISON_PAYLOAD_KINDS = (
    "mapping",
    "set",
    "interval",
    "graph",
    "authorization-difference",
    "deep-equality",
)
TRANSFORMATION_CLASSES = (
    "horizontal_or_incomparable",
    "mixed",
    "unresolved",
    "all_equal",
    "elevation",
    "reduction",
)
AXIS_DIFFERENCE_FIELDS = (
    "axis_id",
    "source_state",
    "target_state",
    "relation",
    "order_witness",
    "information_loss",
    "uncertainty",
)
ORDER_WITNESS_FIELDS = (
    "comparator_id",
    "comparator_version",
    "verifier_id",
    "evidence_refs",
    "comparison_payload",
    "comparator_result_ref",
    "verification_artifact_ref",
    "verification_hash",
    "validation_status",
)
COMPARISON_PAYLOAD_FIELDS = (
    "payload_kind",
    "payload_ref",
    "payload_sha256",
    "description",
)

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
    "ultra-evidence-lineage.schema.json",
    "ultra-forecast-ledger.schema.json",
    "ultra-forecast-resolution-event.schema.json",
    "ultra-framework-gap-ledger.schema.json",
    "ultra-host-action.schema.json",
    "ultra-host-capability-attestation.schema.json",
    "ultra-host-result-receipt.schema.json",
    "ultra-input-inventory.schema.json",
    "ultra-order-evaluation.schema.json",
    "ultra-output-plan.schema.json",
    "ultra-phase-event.schema.json",
    "ultra-read-event.schema.json",
    "ultra-read-plan.schema.json",
    "ultra-recovery-checkpoint.schema.json",
    "ultra-recursive-lineage.schema.json",
    "ultra-recursive-state.schema.json",
    "ultra-red-team-report.schema.json",
    "ultra-release-manifest.schema.json",
    "ultra-repair-plan.schema.json",
    "ultra-retrieval-ledger.schema.json",
    "ultra-route-map.schema.json",
    "ultra-run-contract.schema.json",
    "ultra-run-migration.schema.json",
    "ultra-run-status.schema.json",
    "ultra-semantic-coverage.schema.json",
    "ultra-semantic-review.schema.json",
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
        "ultra-host-action.schema.json",
        "ultra-host-result-receipt.schema.json",
        "ultra-read-plan.schema.json",
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
        "runtime_version": "1.1.0",
        "artifact_schema_version": 2,
        "compiler_version": "1.0.0",
        "validator_version": "1.1.0",
        "article_contract_version": "1.1.0",
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
        "variables": [
            {
                "name": name,
                "value": value,
                "unit": "category",
                "clock_id": "CLOCK-INTERACTION",
            }
        ],
    }


def scale_profile(*, organizational: str) -> dict[str, str]:
    return {
        "A": "local actor partition",
        "X": "local",
        "T": "interaction",
        "O": organizational,
        "C": "bounded channel",
        "R": "visible record",
        "I": "declared impact",
        "N": "local graph",
        "J": "delegated authority",
    }


def evidence_status(*, identity: str = "reported") -> dict[str, Any]:
    return {
        "status": "supported-hypothesis",
        "information_identity": identity,
        "source_lineage": ["SOURCE-1"],
        "visibility": "visible in the supplied record",
    }


def normalized_axis_state(
    suffix: str, *, normalized_state_sha256: str = HASH_A
) -> dict[str, Any]:
    return {
        "status": "recorded",
        "normalized_state_ref": f"AXIS-STATE-{suffix}",
        "normalized_state_sha256": normalized_state_sha256,
        "description": "The normalized axis state is frozen for comparison.",
    }


def missing_axis_state(status: str) -> dict[str, Any]:
    assert status in AXIS_MISSING_STATUSES
    return {
        "status": status,
        "normalized_state_ref": None,
        "normalized_state_sha256": None,
        "description": f"The axis state is explicitly {status}.",
    }


def comparison_payload(
    suffix: str,
    *,
    payload_kind: str | None,
    missing: bool = False,
) -> dict[str, Any]:
    return {
        "payload_kind": payload_kind,
        "payload_ref": None if missing else f"COMPARISON-PAYLOAD-{suffix}",
        "payload_sha256": None if missing else HASH_B,
        "description": (
            "The comparison payload is unavailable for the stated reason."
            if missing
            else "The frozen comparison payload is independently reviewable."
        ),
    }


def order_witness(suffix: str, relation: str) -> dict[str, Any]:
    assert relation in AXIS_RELATIONS
    missing = relation == "unknown"
    return {
        "comparator_id": (
            None
            if missing
            else (
                "builtin:deep-equality"
                if relation == "equal"
                else f"AXIS-COMPARATOR-{suffix}"
            )
        ),
        "comparator_version": None if missing else "1.0.0",
        "verifier_id": None if missing else f"AXIS-VERIFIER-{suffix}",
        "evidence_refs": [] if missing else ["EVIDENCE-1"],
        "comparison_payload": comparison_payload(
            suffix,
            payload_kind=(
                None
                if missing
                else "mapping" if relation != "equal" else "deep-equality"
            ),
            missing=missing,
        ),
        "comparator_result_ref": (
            None if missing else f"COMPARATOR-RESULT-{suffix}"
        ),
        "verification_artifact_ref": (
            None if missing else f"VERIFICATION-ARTIFACT-{suffix}"
        ),
        "verification_hash": None if missing else HASH_C,
        "validation_status": "missing" if missing else "valid",
    }


def axis_difference(suffix: str, axis_id: str, relation: str) -> dict[str, Any]:
    source_state = normalized_axis_state(f"{suffix}-{axis_id}-SOURCE")
    target_state = (
        copy.deepcopy(source_state)
        if relation == "equal"
        else normalized_axis_state(
            f"{suffix}-{axis_id}-TARGET", normalized_state_sha256=HASH_B
        )
    )
    return {
        "axis_id": axis_id,
        "source_state": source_state,
        "target_state": target_state,
        "relation": relation,
        "order_witness": order_witness(f"{suffix}-{axis_id}", relation),
        "information_loss": [],
        "uncertainty": [],
    }


def scale_relations_for_class(transformation_class: str) -> dict[str, str]:
    assert transformation_class in TRANSFORMATION_CLASSES
    relations = dict.fromkeys(SCALE_AXIS_IDS, "equal")
    if transformation_class == "horizontal_or_incomparable":
        relations.update(A="incomparable", X="unknown", T="expands", O="contracts")
    elif transformation_class == "mixed":
        relations.update(A="expands", X="contracts", T="unknown")
    elif transformation_class == "unresolved":
        relations.update(A="expands", X="unknown")
    elif transformation_class == "elevation":
        relations["A"] = "expands"
    elif transformation_class == "reduction":
        relations["A"] = "contracts"
    return relations


def transformation_record(
    suffix: str,
    kind: str,
    *,
    transformation_class: str = "all_equal",
) -> dict[str, Any]:
    if kind == "scale":
        input_type = output_type = "scale-state"
        input_axis = output_axis = None
        relations = scale_relations_for_class(transformation_class)
        axis_differences = [
            axis_difference(suffix, axis_id, relations[axis_id])
            for axis_id in SCALE_AXIS_IDS
        ]
        class_value: str | None = transformation_class
    elif kind == "circle-relation":
        input_type = output_type = "circle-relation"
        input_axis = output_axis = None
        axis_differences = []
        class_value = None
    else:
        input_type, output_type = "source-representation", "represented-state"
        input_axis = output_axis = None
        axis_differences = []
        class_value = None
    return {
        "transform_id": f"TRANSFORM-{suffix}",
        "kind": kind,
        "input_identity": {
            "identity_type": input_type,
            "location_ref": "POS-TEAM-MANAGER",
            "axis_id": input_axis,
            "value": f"input-{suffix}",
            "evidence_ids": ["EVIDENCE-1"],
        },
        "output_identity": {
            "identity_type": output_type,
            "location_ref": "CIRCLE-TEAM",
            "axis_id": output_axis,
            "value": f"output-{suffix}",
            "evidence_ids": ["EVIDENCE-1"],
        },
        "axis_differences": axis_differences,
        "transformation_class": class_value,
        "preserved": [],
        "changed": [],
        "folded": [],
        "omitted": [],
        "unknown": [],
        "task_relative_loss": [],
        "location_effects": [],
        "effective_variables": [],
        "closure_status": "bounded",
        "residuals": [],
        "return_conditions": [],
    }


def compatibility_matrix_instance() -> dict[str, Any]:
    current = version_binding()
    legacy_v1 = {
        **current,
        "runtime_version": "1.0.0",
        "artifact_schema_version": 1,
        "validator_version": "1.0.0",
        "article_contract_version": "1.0.0",
    }
    return artifact(
        "ultra-compatibility-matrix.schema.json",
        matrix_version=1,
        binding_fields=list(version_binding()),
        allowed_results=["resume", "read-only", "fork-required", "reject"],
        known_migrations={
            "framework_revisions": [],
            "artifact_schemas": [
                {
                    "from_binding": legacy_v1,
                    "to_binding": current,
                    "result": "fork-required",
                }
            ],
        },
        rules=[
            {
                "rule_id": "v1-to-v2-migration",
                "priority": 10,
                "match_kind": "known-migration",
                "allowed_mismatch_fields": [
                    "runtime_version",
                    "artifact_schema_version",
                    "validator_version",
                    "article_contract_version",
                ],
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
            release_id="ultra-v8.2-r1-runtime-1.1.0",
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
        "ultra-host-capability-attestation.schema.json": artifact(
            "ultra-host-capability-attestation.schema.json",
            phase_id="U0",
            request_sha256=HASH_B,
            action_sha256=HASH_A,
            receipt_sha256=HASH_C,
            analysis_kind="open-world",
            run_mode="production",
            requirements={
                "filesystem": "required",
                "docx_parser": "not-applicable",
                "network": "required",
                "retrieval": "required",
                "validators": "required",
                "subagents": "not-applicable",
                "model_context": "required",
            },
            measured_availability={
                "filesystem": "available",
                "docx_parser": "unavailable",
                "network": "unavailable",
                "retrieval": "unavailable",
                "validators": "available",
                "subagents": "unavailable",
                "model_context": "available",
            },
            providers=[
                {
                    "provider_id": "schema-host",
                    "provider_kind": "runtime",
                    "version": "1.0.0",
                }
            ],
            tools=[
                {
                    "tool_id": "local-filesystem",
                    "provider_id": "schema-host",
                    "version": "1.0.0",
                }
            ],
            sensitivity="private",
            retention="retain",
            outbound_permission="denied",
            evidence_cutoff=STAMP,
            resource_limits={
                "maximum_branches": 12,
                "maximum_retrieval_rounds_without_material_novelty": 2,
                "maximum_tool_retries": 3,
                "maximum_repair_attempts": 3,
            },
            measured_at=STAMP,
            proof_grade="host-measured",
        ),
        "ultra-input-inventory.schema.json": artifact(
            "ultra-input-inventory.schema.json",
            request_sha256=HASH_B,
            materials=[
                {
                    "path": "materials/MAT-0001.md",
                    "sha256": HASH_C,
                    "media_type": "text/markdown",
                }
            ],
            material_universe_sha256=HASH_A,
        ),
        "ultra-run-contract.schema.json": artifact(
            "ultra-run-contract.schema.json",
            phase_id="U0",
            trigger="CrossFrame Ultra",
            request_sha256=HASH_B,
            analysis_kind="open-world",
            capability_attestation_sha256=HASH_C,
            run_mode="production",
            sensitivity="private",
            retention="retain",
            outbound_permission="denied",
            evidence_cutoff=STAMP,
            capabilities={
                "filesystem": "required",
                "docx_parser": "not-applicable",
                "network": "required",
                "retrieval": "not-applicable",
                "validators": "required",
                "subagents": "not-applicable",
                "model_context": "required",
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
            created_at=STAMP,
            revision=1,
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
            release_manifest_sha256=HASH_B,
            compatibility_matrix_sha256=HASH_C,
            knowledge_report_sha256=HASH_A,
            skill_tree_sha256=HASH_B,
            input_snapshot_sha256=HASH_C,
            parent_event_sha256=HASH_A,
            evidence_cutoff=STAMP,
            acl_status="verified-current-user",
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
            source_lock_sha256=HASH_C,
            parent_event_sha256=HASH_A,
            receipt_sha256=HASH_B,
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
                    "attribution": {
                        "origin_kind": "source",
                        "origin_ref": "SOURCE-1",
                        "content_sha256": "1" * 64,
                        "span": None,
                        "proof_grade": "fixture-bound",
                    },
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
        "ultra-evidence-lineage.schema.json": artifact(
            "ultra-evidence-lineage.schema.json",
            phase_id="U0",
            parent_run_id="ultra-run-20260801-parent",
            parent_u3_event_sha256=HASH_A,
            parent_evidence_sha256=HASH_B,
            parent_evidence_cutoff="2026-08-01T08:00:00Z",
            evidence_cutoff=STAMP,
            inherited_input_refs=[
                {
                    "path": "input/request.bin",
                    "sha256": HASH_C,
                    "media_type": "application/octet-stream",
                }
            ],
            new_evidence_ref={
                "path": "input/new-evidence.bin",
                "sha256": HASH_A,
                "media_type": "application/octet-stream",
            },
            status="pending-u0-attestation",
        ),
        "ultra-retrieval-ledger.schema.json": artifact(
            "ultra-retrieval-ledger.schema.json",
            phase_id="U2",
            decision_sha256=HASH_A,
            u1_parent_event_sha256=HASH_B,
            request_sha256=HASH_C,
            decision={
                "status": "not-applicable",
                "reason": "pure-logic",
                "run_id": RUN_ID,
                "u1_parent_event_sha256": HASH_B,
                "request_sha256": HASH_C,
                "version_binding": version_binding(),
                "claim_sha256": HASH_A,
                "basis_sha256": HASH_C,
                "eligibility_basis": {
                    "analysis_kind": "pure-logic",
                    "claim": "If A then B.",
                    "claim_sha256": HASH_A,
                    "run_id": RUN_ID,
                    "u1_parent_event_sha256": HASH_B,
                    "request_sha256": HASH_C,
                    "version_binding": version_binding(),
                    "material_inventory": [],
                    "material_universe_sha256": None,
                    "basis_sha256": HASH_C,
                },
                "decision_sha256": HASH_A,
            },
            retrieval_status="not-applicable",
            block_result=None,
            authorization_sha256=None,
            query_count=0,
            queries=[],
            sources=[],
            network_available=True,
            outbound_authorized=False,
            entries=[],
            saturation={"rounds": 0, "stop_reason": "not-applicable"},
        ),
        "ultra-world-volume.schema.json": artifact(
            "ultra-world-volume.schema.json",
            phase_id="U4",
            evidence_artifact_sha256=HASH_A,
            evidence_content_sha256=HASH_B,
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
                    "reification_risks": [
                        "Naming the family circle does not establish a separate entity."
                    ],
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
                    "reification_risks": [
                        "Naming the team circle does not establish a separate entity."
                    ],
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
                            {
                                "name": "budget",
                                "value": 1,
                                "unit": "share",
                                "clock_id": "CLOCK-INTERACTION",
                            }
                        ],
                    },
                    "Psi_state": {
                        "state_id": "PSI-POS-1",
                        "variables": [
                            {
                                "name": "rule",
                                "value": "review",
                                "unit": "text",
                                "clock_id": "CLOCK-INTERACTION",
                            }
                        ],
                    },
                    "scale_profile": scale_profile(organizational="team"),
                    "evidence_status": evidence_status(identity="observed"),
                }
            ],
            memberships=[
                {
                    "actor_ref": "ACTOR-1",
                    "circle_ref": "CIRCLE-TEAM",
                    "membership_basis": "active work assignment",
                    "start_time": STAMP,
                    "end_time": None,
                    "roles": ["ROLE-MANAGER"],
                    "commitment_strength": "active",
                    "actual_participation": "current",
                    "exit_ability": "handoff",
                    "dispute_status": "none",
                    "evidence_status": evidence_status(identity="observed"),
                    "source_refs": ["SOURCE-1"],
                }
            ],
            containment_relations=[
                {
                    "child_circle_id": "CIRCLE-TEAM",
                    "parent_circle_id": "CIRCLE-FAMILY",
                    "basis": "资源会计",
                }
            ],
            containment_closure=[
                {"circle_id": "CIRCLE-FAMILY", "ancestor_circle_ids": []},
                {
                    "circle_id": "CIRCLE-TEAM",
                    "ancestor_circle_ids": ["CIRCLE-FAMILY"],
                },
            ],
            circle_relations=[
                {
                    "source_circle_ref": "CIRCLE-FAMILY",
                    "target_circle_ref": "CIRCLE-TEAM",
                    "direction": "directed",
                    "relation_type": "嵌套",
                    "shared_members_or_interfaces": ["ACTOR-1"],
                    "channel": "CHANNEL-1",
                    "strength_or_scope": "shared resource dependency",
                    "time_window": "current",
                    "delay": "one review cycle",
                    "threshold": "manager approval",
                    "evidence_refs": ["EVIDENCE-1"],
                    "counterexample_refs": [],
                    "failure_conditions": [],
                }
            ],
            clocks=[
                {
                    "clock_id": "CLOCK-IMMEDIATE",
                    "scope_id": "CIRCLE-TEAM",
                    "kind": "immediate",
                    "current_time": STAMP,
                    "horizon": "PT1H",
                },
                {
                    "clock_id": "CLOCK-INTERACTION",
                    "scope_id": "CIRCLE-TEAM",
                    "kind": "interaction",
                    "current_time": STAMP,
                    "horizon": "P1D",
                },
                {
                    "clock_id": "CLOCK-ORGANIZATIONAL",
                    "scope_id": "CIRCLE-TEAM",
                    "kind": "organizational",
                    "current_time": STAMP,
                    "horizon": "P90D",
                },
                {
                    "clock_id": "CLOCK-INSTITUTIONAL",
                    "scope_id": "CIRCLE-TEAM",
                    "kind": "institutional",
                    "current_time": STAMP,
                    "horizon": "P1Y",
                },
                {
                    "clock_id": "CLOCK-LONG-TERM",
                    "scope_id": "CIRCLE-TEAM",
                    "kind": "long-term",
                    "current_time": STAMP,
                    "horizon": "P5Y",
                },
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
                    "identity_mapping": {
                        "source_k_ref": "POS-TEAM-MANAGER",
                        "target_k_ref": "POS-TEAM-MANAGER",
                        "mapping_rule": "Preserve the declared position identity.",
                        "preserves_identity": True,
                    },
                    "acl": {
                        "authorized_position_ids": ["POS-TEAM-MANAGER"],
                        "authorization_evidence_ids": ["EVIDENCE-1"],
                    },
                    "evidence_ids": ["EVIDENCE-1"],
                }
            ],
            events=[
                {
                    "event_id": "WORLD-EVENT-1",
                    "target_volume_id": "OMEGA-0",
                    "origin_kind": "endogenous",
                    "source_position_id": "POS-TEAM-MANAGER",
                    "target_position_ids": ["POS-TEAM-MANAGER"],
                    "channel_ids": ["CHANNEL-1"],
                    "channel_conditions": [
                        {
                            "channel_id": "CHANNEL-1",
                            "threshold_met": True,
                            "identity_preserved": True,
                            "acl_authorized": True,
                            "evidence_ids": ["EVIDENCE-1"],
                        }
                    ],
                    "M_updates": [
                        {
                            "position_id": "POS-TEAM-MANAGER",
                            "state_id": "M-POS-1",
                            "variable_changes": [
                                {
                                    "name": "budget",
                                    "source_value": 1,
                                    "target_value": 2,
                                    "unit": "share",
                                    "clock_id": "CLOCK-INTERACTION",
                                }
                            ],
                            "via_channel_id": "CHANNEL-1",
                        }
                    ],
                    "Psi_updates": [],
                    "relation_updates": [],
                    "clock_deltas": [],
                }
            ],
            local_distributions=[
                {
                    "distribution_id": "DIST-POWER-1",
                    "kind": "power",
                    "location_ref": "RAC-ACTOR-1-CIRCLE-TEAM",
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
                    "location_ref": "RAC-ACTOR-1-CIRCLE-TEAM",
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
            evidence_artifact_sha256=HASH_A,
            evidence_content_sha256=HASH_B,
            world_volume_artifact_sha256=HASH_C,
            world_volume_content_sha256=HASH_A,
            transformations=[
                transformation_record("SCALE-1", "scale"),
                transformation_record("CIRCLE-1", "circle-relation"),
                transformation_record("REP-1", "representation-translation"),
            ],
        ),
        "ultra-concept-disposition.schema.json": artifact(
            "ultra-concept-disposition.schema.json",
            phase_id="U5",
            evidence_artifact_sha256=HASH_A,
            evidence_content_sha256=HASH_B,
            world_volume_artifact_sha256=HASH_C,
            world_volume_content_sha256=HASH_A,
            transformation_ledger_artifact_sha256=HASH_B,
            transformation_ledger_content_sha256=HASH_C,
            registry_sha256=HASH_A,
            route_map_sha256=HASH_B,
            contract_map_sha256=HASH_C,
            required_route_ids=["ROUTE-1"],
            required_contract_ids=["CONTRACT-1"],
            required_requirement_ids=["REQ-1"],
            dispositions=[
                {
                    "concept_id": "V82-CONCEPT-CHANNEL",
                    "status": "applied",
                    "rationale": "A concrete decision channel reaches the position.",
                    "route_required": True,
                    "neighbor_concept_ids": [],
                    "route_ids": ["ROUTE-1"],
                    "contract_ids": ["CONTRACT-1"],
                    "requirement_ids": ["REQ-1"],
                    "obligation_ids": ["OBLIGATION-1"],
                    "evidence_ids": ["EVIDENCE-1"],
                    "unknown_ids": [],
                    "transformation_ids": ["TRANSFORM-SCALE-1"],
                    "condition_branch": None,
                }
            ],
            semantic_obligations=[
                {
                    "obligation_id": "OBLIGATION-1",
                    "concept_id": "V82-CONCEPT-CHANNEL",
                    "status": "applied",
                    "semantic_unit_id": "UNIT-CHANNEL-1",
                    "evidence_ids": ["EVIDENCE-1"],
                    "unknown_ids": [],
                    "transformation_ids": ["TRANSFORM-SCALE-1"],
                    "route_ids": ["ROUTE-1"],
                    "contract_ids": ["CONTRACT-1"],
                    "requirement_ids": ["REQ-1"],
                    "condition_branch_id": None,
                }
            ],
            unvisited_concept_ids=[],
            closure_complete=True,
        ),
        "ultra-claim-mechanism-graph.schema.json": artifact(
            "ultra-claim-mechanism-graph.schema.json",
            phase_id="U6",
            evidence_ledger_artifact_sha256=HASH_A,
            world_volume_artifact_sha256=HASH_B,
            transformation_ledger_artifact_sha256=HASH_C,
            concept_disposition_artifact_sha256=HASH_D,
            central_claim_id="CLAIM-1",
            partial_ranking_justification=None,
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
                    "edge_id": "EDGE-1",
                    "source": {"claim_id": "CLAIM-1"},
                    "target": {"mechanism_id": "MECHANISM-1"},
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
                },
                {
                    "explanation_id": "EXPLANATION-RIVAL",
                    "kind": "strongest-rival",
                    "claim_ids": ["CLAIM-1"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "rank": 2,
                },
                {
                    "explanation_id": "EXPLANATION-MIXTURE",
                    "kind": "mixture",
                    "claim_ids": ["CLAIM-1"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "rank": 3,
                },
                {
                    "explanation_id": "EXPLANATION-RESIDUAL",
                    "kind": "residual",
                    "claim_ids": ["CLAIM-1"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "rank": 4,
                },
            ],
            insights=[
                {
                    "insight_id": "INSIGHT-1",
                    "effects": ["changes-intervention"],
                    "reason": "The channel identifies a reversible intervention point.",
                }
            ],
        ),
        "ultra-recursive-state.schema.json": artifact(
            "ultra-recursive-state.schema.json",
            phase_id="U7",
            path_id="PATH-MAIN",
            node_id="NODE-1",
            parent_run_id=RUN_ID,
            parent_path_id="PATH-ROOT",
            parent_node_id="NODE-U4-ROOT",
            order=1,
            world_volume_artifact_sha256=HASH_B,
            transformation_ledger_artifact_sha256=HASH_C,
            concept_disposition_artifact_sha256=HASH_D,
            claim_mechanism_graph_artifact_sha256=HASH_E,
            full_state_sha256=HASH_F,
            inherited_fact_ids=["FACT-1"],
            inherited_evidence_ids=["EVIDENCE-1"],
            inherited_unknown_ids=["UNKNOWN-1"],
            inherited_loss_ids=["LOSS-1"],
            inherited_residual_ids=["RESIDUAL-1"],
            event_id="WORLD-EVENT-1",
            mechanism_ids=["MECHANISM-1"],
            state_diff_sha256=HASH_0,
            signal_ids=["SIGNAL-1"],
            evidence_identity="simulated-result",
            declared_evidence_grade="low",
        ),
        "ultra-recursive-lineage.schema.json": artifact(
            "ultra-recursive-lineage.schema.json",
            phase_id="U7",
            world_volume_artifact_sha256=HASH_B,
            transformation_ledger_artifact_sha256=HASH_C,
            concept_disposition_artifact_sha256=HASH_D,
            claim_mechanism_graph_artifact_sha256=HASH_E,
            recursive_state_artifact_hashes=[HASH_F],
            nodes=[
                {
                    "node_id": "NODE-1",
                    "path_id": "PATH-MAIN",
                    "parent_node_ids": [],
                    "order": 1,
                    "recursive_state_artifact_sha256": HASH_F,
                }
            ],
            branches=[
                {
                    "branch_id": "BRANCH-MAIN",
                    "kind": "main",
                    "node_ids": ["NODE-1"],
                    "status": "active",
                    "merge_parent_branch_ids": [],
                    "prune_reason": None,
                    "retained_residual_ids": ["RESIDUAL-1"],
                }
            ],
            maximum_order=1,
        ),
        "ultra-order-evaluation.schema.json": artifact(
            "ultra-order-evaluation.schema.json",
            phase_id="U8",
            claim_mechanism_graph_artifact_sha256=HASH_E,
            recursive_lineage_artifact_sha256=HASH_0,
            evaluations=[
                {
                    "order": 1,
                    "branch_coverage": [
                        {
                            "branch_kind": kind,
                            "applicability": "applicable",
                            "branch_ids": [f"BRANCH-{kind.upper()}"],
                            "not_applicable": None,
                        }
                        for kind in (
                            "main",
                            "strongest-rival",
                            "mixture",
                            "residual",
                        )
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
                    "continuation_value": "none",
                    "continue_recursive": False,
                    "stop_kind": "no-material-state-change",
                    "rationale": "The next order adds no material state change.",
                }
            ],
        ),
        "ultra-red-team-report.schema.json": artifact(
            "ultra-red-team-report.schema.json",
            phase_id="U8",
            claim_mechanism_graph_artifact_sha256=HASH_E,
            recursive_lineage_artifact_sha256=HASH_0,
            order_evaluation_artifact_sha256=HASH_1,
            attacks=[
                {
                    "attack_id": "ATTACK-1",
                    "target": {"claim_id": "CLAIM-1"},
                    "attack_kind": "strongest-counterexample",
                    "challenge": "The channel may be nominal rather than effective.",
                    "evidence_refs": ["EVIDENCE-1"],
                    "evidence_identity": "reported",
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
            unresolved_items=[],
            overall_status="revised",
        ),
        "ultra-verdict.schema.json": artifact(
            "ultra-verdict.schema.json",
            phase_id="U9",
            evidence_ledger_artifact_sha256=HASH_A,
            claim_mechanism_graph_artifact_sha256=HASH_E,
            recursive_lineage_artifact_sha256=HASH_0,
            order_evaluation_artifact_sha256=HASH_1,
            red_team_report_artifact_sha256=HASH_2,
            judgment_kind="best-current",
            main_verdict={
                "proposition": "The active channel currently best explains the action change.",
                "scope": "The represented team position and frozen time window.",
                "epistemic_identity": "inferred-from-material",
                "confidence": "low",
                "decisive_evidence_refs": ["EVIDENCE-1"],
                "decisive_claim_ids": ["CLAIM-1"],
                "decisive_mechanism_ids": ["MECHANISM-1"],
                "decisive_node_ids": ["NODE-1"],
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
            non_decidability=None,
            partial_ranking_justification=None,
            explanation_ranking=[
                {"explanation_id": "EXPLANATION-MAIN", "rank": 1},
                {"explanation_id": "EXPLANATION-RIVAL", "rank": 2},
                {"explanation_id": "EXPLANATION-MIXTURE", "rank": 3},
                {"explanation_id": "EXPLANATION-RESIDUAL", "rank": 4},
            ],
            five_verdicts=[
                {
                    "verdict_id": f"VERDICT-{kind.upper()}",
                    "kind": kind,
                    "proposition": f"Bounded {kind} judgment.",
                    "evidence_refs": ["EVIDENCE-1"],
                    "claim_ids": ["CLAIM-1"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "recursive_node_ids": ["NODE-1"],
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
            verdict_artifact_sha256=HASH_3,
            considered_verdict_ids=[
                "VERDICT-FACT",
                "VERDICT-PREDICTION",
                "VERDICT-VALUE",
                "VERDICT-RESPONSIBILITY",
                "VERDICT-AUTHORIZATION",
            ],
            requested_choice=True,
            options=[
                {
                    "option_id": f"OPTION-{kind.upper()}",
                    "kind": kind,
                    "description": f"Compare the {kind} option independently.",
                    "authorized": True,
                    "authorization_verdict_id": "VERDICT-AUTHORIZATION",
                    "benefits": ["new evidence"],
                    "harms": ["small coordination cost"],
                    "requirements": ["team consent"],
                    "rollback": "Stop after one review cycle.",
                }
                for kind in (
                    "active",
                    "delay",
                    "probe",
                    "exit-or-transfer",
                    "maintain-status-quo",
                    "no-action",
                )
            ],
            ranking=[
                "OPTION-PROBE",
                "OPTION-DELAY",
                "OPTION-ACTIVE",
                "OPTION-MAINTAIN-STATUS-QUO",
                "OPTION-EXIT-OR-TRANSFER",
                "OPTION-NO-ACTION",
            ],
            preferred_option_id="OPTION-PROBE",
            second_option_id="OPTION-DELAY",
            switch_conditions=["Switch if authorization is withdrawn."],
            stop_conditions=["Stop if harm exceeds the bounded threshold."],
            no_action_consequences=["The decisive unknown remains."],
        ),
        "ultra-forecast-ledger.schema.json": artifact(
            "ultra-forecast-ledger.schema.json",
            phase_id="U9",
            evidence_ledger_artifact_sha256=HASH_A,
            recursive_lineage_artifact_sha256=HASH_0,
            verdict_artifact_sha256=HASH_3,
            forecasts=[
                {
                    "forecast_id": "FORECAST-1",
                    "prediction_verdict_id": "VERDICT-PREDICTION",
                    "direction": "increase",
                    "time_window": "P90D",
                    "indicator": "recorded feedback events",
                    "indicator_id": "INDICATOR-1",
                    "window_start": STAMP,
                    "window_end": "2026-11-02T08:00:00Z",
                    "resolution_rule": "Resolve increase if count exceeds the frozen baseline.",
                    "resolution_predicate": {
                        "operator": "gt",
                        "baseline_value": 8,
                        "target_value": 10,
                        "tolerance": 0,
                    },
                    "evidence_cutoff": STAMP,
                    "branch_refs": ["BRANCH-MAIN"],
                    "node_refs": ["NODE-1"],
                    "status": "open",
                }
            ],
        ),
        "ultra-forecast-resolution-event.schema.json": artifact(
            "ultra-forecast-resolution-event.schema.json",
            phase_id="U9",
            resolution_event_id="RESOLUTION-1",
            forecast_ledger_artifact_sha256=HASH_4,
            forecast_id="FORECAST-1",
            indicator_id="INDICATOR-1",
            original_forecast_record_sha256=HASH_5,
            resolution_time="2026-11-02T08:00:00Z",
            observation_time="2026-11-02T08:00:00Z",
            indicator_resolved=True,
            direction_correct=True,
            time_window_covered=True,
            outcome="correct",
            observed_value=12,
            original_probability_admissible=False,
            brier_inputs=None,
            brier_score=None,
        ),
        "ultra-framework-gap-ledger.schema.json": artifact(
            "ultra-framework-gap-ledger.schema.json",
            phase_id="U10",
            evidence_ledger_artifact_sha256=HASH_A,
            claim_mechanism_graph_artifact_sha256=HASH_E,
            recursive_lineage_artifact_sha256=HASH_0,
            order_evaluation_artifact_sha256=HASH_1,
            red_team_report_artifact_sha256=HASH_2,
            verdict_artifact_sha256=HASH_3,
            action_ranking_artifact_sha256=HASH_4,
            forecast_ledger_artifact_sha256=HASH_5,
            candidates=[
                {
                    "gap_id": "GAP-1",
                    "description": "The framework has no calibrated latency prior.",
                    "evidence_refs": ["EVIDENCE-1"],
                    "claim_ids": ["CLAIM-1"],
                    "mechanism_ids": ["MECHANISM-1"],
                    "recursive_node_ids": ["NODE-1"],
                    "route_ids": ["ROUTE-1"],
                    "concept_ids": ["V82-CONCEPT-CHANNEL"],
                    "future_revision_proposal": "Add a latency calibration contract.",
                    "status": "candidate",
                }
            ],
            isolated_from_current_reasoning=True,
        ),
        "ultra-output-plan.schema.json": artifact(
            "ultra-output-plan.schema.json",
            phase_id="U10",
            u9_parent_event_sha256=HASH_C,
            article_path="delivery/CrossFrame-Ultra-完整文章.partial.md",
            sections=[
                {
                    "section_id": f"SECTION-{ordinal:02d}",
                    "title": title,
                    "ordinal": ordinal,
                    "semantic_unit_ids": [
                        f"UNIT-{((ordinal - 1) % len(SEMANTIC_UNIT_KINDS)) + 1:02d}"
                    ],
                    "dependency_hashes": [HASH_A],
                }
                for ordinal, title in enumerate(OUTPUT_PLAN_SECTION_TITLES, start=1)
            ],
            appendices=[
                {
                    "section_id": f"APPENDIX-{ordinal:02d}",
                    "title": title,
                    "ordinal": ordinal,
                    "semantic_unit_ids": [
                        f"UNIT-{((ordinal - 1) % len(SEMANTIC_UNIT_KINDS)) + 1:02d}"
                    ],
                    "dependency_hashes": [HASH_B],
                }
                for ordinal, title in enumerate(OUTPUT_PLAN_APPENDIX_TITLES, start=11)
            ],
            required_artifacts=[
                {
                    "path": "artifacts/U09-U10-output/ultra-verdict.json",
                    "sha256": HASH_A,
                    "media_type": "application/json",
                }
            ],
            semantic_universe=[
                {
                    "unit_id": f"UNIT-{ordinal:02d}",
                    "unit_kind": unit_kind,
                    "status": "applied",
                    "affects_ranking": True,
                    "used_in_reasoning": True,
                    "promised_to_reader": True,
                    "source_refs": ["EVIDENCE-1"],
                    "authority_artifact_sha256": HASH_A,
                    "authority_locator": f"unit:{ordinal:02d}",
                    "normalized_semantic_text_sha256": HASH_B,
                }
                for ordinal, unit_kind in enumerate(SEMANTIC_UNIT_KINDS, start=1)
            ],
            semantic_universe_sha256=HASH_C,
            blind_recovery_expectations=[
                {
                    "field_id": field_id,
                    "section_id": (
                        f"SECTION-{ordinal:02d}"
                        if ordinal <= 10
                        else f"APPENDIX-{ordinal:02d}"
                    ),
                    "semantic_unit_ids": [
                        f"UNIT-{((ordinal - 1) % len(SEMANTIC_UNIT_KINDS)) + 1:02d}"
                    ],
                    "normalized_value_sha256": HASH_A,
                }
                for ordinal, field_id in enumerate(BLIND_RECOVERY_FIELD_IDS, start=1)
            ],
            coverage_required=True,
            official_filename_allowed=False,
        ),
        "ultra-semantic-coverage.schema.json": artifact(
            "ultra-semantic-coverage.schema.json",
            phase_id="U11",
            output_plan_artifact_sha256=HASH_B,
            semantic_universe_sha256=HASH_C,
            article_sha256=HASH_A,
            required_unit_kinds=list(SEMANTIC_UNIT_KINDS),
            mappings=[
                {
                    "unit_id": f"UNIT-{ordinal:02d}",
                    "unit_kind": unit_kind,
                    "section_id": f"SECTION-{min(ordinal, 10):02d}",
                    "normalized_excerpt": f"Semantic unit {ordinal} is present.",
                    "source_refs": ["EVIDENCE-1"],
                }
                for ordinal, unit_kind in enumerate(SEMANTIC_UNIT_KINDS, start=1)
            ],
            missing_unit_ids=[],
            coverage_percent=100,
            coverage_complete=True,
        ),
        "ultra-article-review.schema.json": artifact(
            "ultra-article-review.schema.json",
            phase_id="U11",
            output_plan_artifact_sha256=HASH_C,
            semantic_universe_sha256=HASH_A,
            article_sha256=HASH_A,
            coverage_artifact_sha256=HASH_B,
            blind_recovery_contract_sha256=HASH_C,
            blind_reader_fields=[
                {
                    "field_id": field_id,
                    "recovered": True,
                    "excerpt": f"Recovered field {field_id}.",
                }
                for field_id in BLIND_RECOVERY_FIELD_IDS
            ],
            quality_checks=[
                {
                    "check_id": check_id,
                    "status": "pass",
                    "evidence": f"Mechanical check {check_id} passed.",
                }
                for check_id in QUALITY_CHECK_IDS
            ],
            external_dependencies=[],
            overall_status="mechanical-complete",
            official_filename_allowed=False,
            review_stage="mechanical-precheck",
            semantic_review_required=True,
            needs_u12_validation=True,
            u12_validator_artifact_required=True,
        ),
        "ultra-semantic-review.schema.json": artifact(
            "ultra-semantic-review.schema.json",
            phase_id="U11",
            request_sha256=HASH_1,
            request_intake_authority_sha256=HASH_2,
            u10_parent_event_sha256=HASH_3,
            active_generation=2,
            article_sha256=HASH_A,
            output_plan_artifact_sha256=HASH_B,
            coverage_artifact_sha256=HASH_C,
            article_review_artifact_sha256=HASH_D,
            evidence_ledger_artifact_sha256=HASH_D,
            concept_disposition_artifact_sha256=HASH_E,
            required_concept_semantic_unit_ids=["CONCEPT-UNIT-1"],
            required_concept_semantic_units_sha256=HASH_F,
            host_action_sha256=HASH_A,
            host_receipt_sha256=HASH_B,
            host_result_sha256=HASH_C,
            host_execution={
                "provider": {
                    "provider_id": "PROVIDER-1",
                    "provider_kind": "service",
                    "version": "1",
                },
                "tool": {
                    "tool_id": "SEMANTIC-REVIEWER-1",
                    "provider_id": "PROVIDER-1",
                    "version": "1",
                },
                "execution_id": "EXECUTION-1",
                "completed_at": STAMP,
            },
            reviewer={
                "reviewer_id": "REVIEWER-1",
                "host_id": "host-1",
                "provider_id": "PROVIDER-1",
                "model": "model-1",
                "execution_id": "EXECUTION-1",
                "proof_grade": "host-attested",
            },
            dimension_reviews=[
                {
                    "dimension_id": dimension_id,
                    "status": "pass",
                    "rationale": f"Fresh review passed {dimension_id}.",
                    "article_spans": [f"SPAN-{ordinal:02d}"],
                    "authority_refs": [f"AUTHORITY-{ordinal:02d}"],
                }
                for ordinal, dimension_id in enumerate(
                    SEMANTIC_REVIEW_DIMENSION_IDS, start=1
                )
            ],
            deterministic_status="pass",
            adversarial_status="pass",
            overall_status="pass",
            publication_allowed=True,
            reviewed_at=STAMP,
        ),
        "ultra-recovery-checkpoint.schema.json": artifact(
            "ultra-recovery-checkpoint.schema.json",
            phase_id="U7",
            boundary_kind="phase",
            boundary_id="U7",
            boundary_ordinal=0,
            generation=0,
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
        "ultra-run-migration.schema.json": artifact(
            "ultra-run-migration.schema.json",
            parent_run_id="ultra-run-20260801-parent",
            parent_checkpoint_sha256=HASH_A,
            parent_version_binding=version_binding(),
            compatibility_result="fork-required",
            fork_reason="Known framework migration requires an immutable child run.",
            frozen_input_refs=[
                {
                    "path": "input/request.md",
                    "sha256": HASH_B,
                    "media_type": "text/markdown",
                }
            ],
            inherited_artifact_hashes=[
                {
                    "path": "artifacts/U00-U03-evidence/evidence-ledger.json",
                    "sha256": HASH_C,
                    "media_type": "application/json",
                }
            ],
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
            active_generation=2,
            article_sha256=HASH_C,
            semantic_review_artifact_sha256=HASH_D,
            checks=[
                {
                    "validator_id": "schema-closure",
                    "status": "pass",
                    "error_codes": [],
                    "artifact_refs": ["ultra-verdict.json"],
                }
            ],
            layers=[
                {
                    "layer_id": layer_id,
                    "status": "pass",
                    "artifact_refs": ["artifacts/U11-article-validation/review.json"],
                }
                for layer_id in ("deterministic", "adversarial", "fresh-semantic")
            ],
            overall_status="pass",
            publication_allowed=True,
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
    load_runtime()
    schemas = importlib.import_module("ultra_runtime.schemas")
    for schema_name, fixture in fixtures.items():
        if schema_name not in {
            "ultra-phase-event.schema.json",
            "ultra-read-event.schema.json",
        }:
            fixture["content_sha256"] = schemas.compute_artifact_content_sha256(
                fixture
            )
    assert set(fixtures) == set(ARTIFACT_SCHEMAS)
    return fixtures


def required_retrieval_instance() -> dict[str, Any]:
    value = copy.deepcopy(minimal_instances()["ultra-retrieval-ledger.schema.json"])
    value["decision"] = {
        "status": "required",
        "reason": "A current factual claim needs external evidence.",
        "run_id": RUN_ID,
        "u1_parent_event_sha256": HASH_B,
        "request_sha256": HASH_C,
        "version_binding": version_binding(),
        "claim_sha256": HASH_A,
        "basis_sha256": HASH_C,
        "eligibility_basis": {
            "trigger_kinds": ["current-fact", "time-sensitive"],
            "claim": "A current factual claim needs external evidence.",
            "claim_sha256": HASH_A,
            "run_id": RUN_ID,
            "u1_parent_event_sha256": HASH_B,
            "request_sha256": HASH_C,
            "version_binding": version_binding(),
            "basis_sha256": HASH_C,
        },
        "decision_sha256": HASH_A,
    }
    value["retrieval_status"] = "required-complete"
    value["block_result"] = None
    value["authorization_sha256"] = HASH_B
    value["query_count"] = 1
    value["queries"] = [
        {
            "eligibility_status": "required",
            "redacted_query": "current factual claim counterexample",
            "query_sha256": HASH_C,
            "eligibility_decision_sha256": HASH_A,
            "authorization_sha256": HASH_B,
            "u1_parent_event_sha256": HASH_B,
            "request_sha256": HASH_C,
            "run_id": RUN_ID,
            "version_binding": version_binding(),
        }
    ]
    value["sources"] = [
        {
            "record": {
                "source_id": "SOURCE-RETRIEVED-1",
                "url": "https://example.test/source",
                "event_date": None,
                "publication_date": None,
                "interest": "No declared interest is available.",
                "upstream_lineage": [],
                "supported_claim": "The source supports a bounded claim.",
                "cannot_prove": "The source cannot prove the universal claim.",
            },
            "source_record_sha256": HASH_A,
            "query_sha256": HASH_C,
            "authorization_sha256": HASH_B,
            "decision_sha256": HASH_A,
            "run_id": RUN_ID,
            "u1_parent_event_sha256": HASH_B,
            "request_sha256": HASH_C,
            "version_binding": version_binding(),
            "inventory_item_sha256": HASH_C,
        }
    ]
    value["network_available"] = True
    value["outbound_authorized"] = True
    value["entries"] = [
        {
            "query_id": "QUERY-1",
            "query_sha256": HASH_C,
            "direction": "counterexample",
            "result_summary": "One bounded source was recorded.",
            "source_refs": ["SOURCE-RETRIEVED-1"],
            "stop_reason": "bounded-result-recorded",
        }
    ]
    value["saturation"] = {"rounds": 1, "stop_reason": "bounded-result-recorded"}
    return value


def blocked_retrieval_instance(
    block_class: str = "network-unavailable",
) -> dict[str, Any]:
    value = required_retrieval_instance()
    value["retrieval_status"] = "required-blocked"
    value["block_result"] = {
        "block_class": block_class,
        "detail": "Required retrieval could not complete within the frozen boundary.",
    }
    value["query_count"] = 0
    value["queries"] = []
    value["sources"] = []
    value["network_available"] = False
    value["outbound_authorized"] = True
    value["entries"] = []
    value["saturation"] = {"rounds": 0, "stop_reason": block_class}
    return value


PRIMARY_FIELD = {
    "ultra-release-manifest.schema.json": "release_id",
    "ultra-compatibility-matrix.schema.json": "rules",
    "ultra-host-capability-attestation.schema.json": "measured_availability",
    "ultra-input-inventory.schema.json": "materials",
    "ultra-run-contract.schema.json": "capabilities",
    "ultra-run-migration.schema.json": "parent_checkpoint_sha256",
    "ultra-run-status.schema.json": "status",
    "ultra-phase-event.schema.json": "event_sha256",
    "ultra-source-lock.schema.json": "inputs",
    "ultra-read-event.schema.json": "read_event_sha256",
    "ultra-evidence-ledger.schema.json": "entries",
    "ultra-evidence-lineage.schema.json": "parent_evidence_sha256",
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
    "ultra-forecast-resolution-event.schema.json": "resolution_event_id",
    "ultra-framework-gap-ledger.schema.json": "candidates",
    "ultra-recursive-state.schema.json": "node_id",
    "ultra-output-plan.schema.json": "sections",
    "ultra-semantic-coverage.schema.json": "mappings",
    "ultra-semantic-review.schema.json": "dimension_reviews",
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


def test_evidence_lineage_schema_has_disjoint_pending_and_finalized_branches() -> None:
    runtime = load_runtime()
    pending = minimal_instances()["ultra-evidence-lineage.schema.json"]
    runtime.validate_instance("ultra-evidence-lineage.schema.json", pending)

    finalized = copy.deepcopy(pending)
    finalized.update(
        {
            "status": "finalized-u0-admission",
            "lineage_request_sha256": HASH_D,
            "request_sha256": HASH_E,
            "capability_attestation_sha256": HASH_F,
            "run_contract_sha256": HASH_1,
            "u0_phase_event_sha256": HASH_2,
        }
    )
    runtime.validate_instance("ultra-evidence-lineage.schema.json", finalized)

    smuggled = copy.deepcopy(pending)
    smuggled["run_contract_sha256"] = HASH_1
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-evidence-lineage.schema.json", smuggled)

    incomplete = copy.deepcopy(finalized)
    incomplete.pop("u0_phase_event_sha256")
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-evidence-lineage.schema.json", incomplete)


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
    ("schema_name", "document"),
    (
        (
            "ultra-host-action.schema.json",
            {
                "schema_id": "crossframe.ultra.v82.host-action",
                "schema_version": 1,
                "run_id": RUN_ID,
                "version_binding": version_binding(),
                "phase_id": "U0",
                "action_kind": "capability-attestation",
                "parent_event_sha256": None,
                "request_sha256": HASH_1,
                "result_relative_path": "work/host/U00-capability-result.json",
                "payload": {"required_capabilities": ["filesystem", "validators"]},
                "issued_at": STAMP,
                "action_sha256": HASH_2,
            },
        ),
        (
            "ultra-host-result-receipt.schema.json",
            {
                "schema_id": "crossframe.ultra.v82.host-result-receipt",
                "schema_version": 1,
                "run_id": RUN_ID,
                "version_binding": version_binding(),
                "phase_id": "U0",
                "action_kind": "capability-attestation",
                "parent_event_sha256": None,
                "request_sha256": HASH_1,
                "action_sha256": HASH_2,
                "result_relative_path": "work/host/U00-capability-result.json",
                "result_sha256": HASH_3,
                "execution_id": "host-exec-1",
                "completed_at": STAMP,
                "receipt_sha256": HASH_4,
            },
        ),
    ),
)
def test_host_action_and_host_result_schemas_are_closed(
    schema_name: str, document: dict[str, Any]
) -> None:
    runtime = load_runtime()
    runtime.validate_instance(schema_name, document)
    document["host_selected_authority"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance(schema_name, document)


@pytest.mark.parametrize(
    ("schema_name", "schema_id", "phase_id"),
    (
        (
            "ultra-source-lock.schema.json",
            "crossframe.ultra.v82.source-lock",
            "U1",
        ),
        (
            "ultra-retrieval-ledger.schema.json",
            "crossframe.ultra.v82.retrieval-ledger",
            "U2",
        ),
        (
            "ultra-evidence-ledger.schema.json",
            "crossframe.ultra.v82.evidence-ledger",
            "U3",
        ),
        (
            "ultra-evidence-lineage.schema.json",
            "crossframe.ultra.v82.evidence-lineage",
            "U0",
        ),
        (
            "ultra-world-volume.schema.json",
            "crossframe.ultra.v82.world-volume",
            "U4",
        ),
        (
            "ultra-transformation-ledger.schema.json",
            "crossframe.ultra.v82.transformation-ledger",
            "U5",
        ),
        (
            "ultra-concept-disposition.schema.json",
            "crossframe.ultra.v82.concept-disposition",
            "U5",
        ),
        (
            "ultra-claim-mechanism-graph.schema.json",
            "crossframe.ultra.v82.claim-mechanism-graph",
            "U6",
        ),
        (
            "ultra-recursive-state.schema.json",
            "crossframe.ultra.v82.recursive-state",
            "U7",
        ),
        (
            "ultra-recursive-lineage.schema.json",
            "crossframe.ultra.v82.recursive-lineage",
            "U7",
        ),
        (
            "ultra-order-evaluation.schema.json",
            "crossframe.ultra.v82.order-evaluation",
            "U8",
        ),
        (
            "ultra-red-team-report.schema.json",
            "crossframe.ultra.v82.red-team-report",
            "U8",
        ),
        (
            "ultra-verdict.schema.json",
            "crossframe.ultra.v82.verdict",
            "U9",
        ),
        (
            "ultra-action-ranking.schema.json",
            "crossframe.ultra.v82.action-ranking",
            "U9",
        ),
        (
            "ultra-forecast-ledger.schema.json",
            "crossframe.ultra.v82.forecast-ledger",
            "U9",
        ),
        (
            "ultra-forecast-resolution-event.schema.json",
            "crossframe.ultra.v82.forecast-resolution-event",
            "U9",
        ),
        (
            "ultra-framework-gap-ledger.schema.json",
            "crossframe.ultra.v82.framework-gap-ledger",
            "U10",
        ),
        (
            "ultra-output-plan.schema.json",
            "crossframe.ultra.v82.output-plan",
            "U10",
        ),
        (
            "ultra-semantic-coverage.schema.json",
            "crossframe.ultra.v82.semantic-coverage",
            "U11",
        ),
        (
            "ultra-article-review.schema.json",
            "crossframe.ultra.v82.article-review",
            "U11",
        ),
    ),
)
def test_self_contained_generic_artifacts_bind_external_authority(
    schema_name: str,
    schema_id: str,
    phase_id: str,
) -> None:
    load_runtime()
    schemas = importlib.import_module("ultra_runtime.schemas")
    artifact_value = copy.deepcopy(minimal_instances()[schema_name])

    validated = schemas.validate_phase_artifact(
        schema_name,
        artifact_value,
        expected_schema_id=schema_id,
        expected_run_id=RUN_ID,
        expected_version_binding=version_binding(),
        expected_phase_id=phase_id,
    )
    assert validated == artifact_value


def test_phase_artifact_rejects_payload_change_with_old_hash() -> None:
    load_runtime()
    schemas = importlib.import_module("ultra_runtime.schemas")
    artifact_value = copy.deepcopy(
        minimal_instances()["ultra-evidence-ledger.schema.json"]
    )
    artifact_value["entries"][0]["statement"] += " changed"

    with pytest.raises(schemas.UltraSchemaError, match="content_sha256"):
        schemas.validate_phase_artifact(
            "ultra-evidence-ledger.schema.json",
            artifact_value,
            expected_schema_id="crossframe.ultra.v82.evidence-ledger",
            expected_run_id=RUN_ID,
            expected_version_binding=version_binding(),
            expected_phase_id="U3",
        )


@pytest.mark.parametrize("mutation", ("run", "version", "phase", "authority"))
def test_self_rehashed_artifact_cannot_choose_its_expected_authority(
    mutation: str,
) -> None:
    load_runtime()
    schemas = importlib.import_module("ultra_runtime.schemas")
    artifact_value = copy.deepcopy(
        minimal_instances()["ultra-evidence-ledger.schema.json"]
    )
    if mutation == "run":
        artifact_value["run_id"] = "attacker-selected-run"
    elif mutation == "version":
        artifact_value["version_binding"]["source_tree_sha256"] = "e" * 64
    elif mutation == "phase":
        artifact_value["phase_id"] = "U4"
    else:
        artifact_value["schema_id"] = "crossframe.ultra.v82.world-volume"
    artifact_value["content_sha256"] = schemas.compute_artifact_content_sha256(
        artifact_value
    )

    with pytest.raises((schemas.UltraSchemaError, ValidationError)):
        schemas.validate_phase_artifact(
            "ultra-evidence-ledger.schema.json",
            artifact_value,
            expected_schema_id="crossframe.ultra.v82.evidence-ledger",
            expected_run_id=RUN_ID,
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


@pytest.mark.parametrize(
    "required_field",
    (
        "status",
        "previous_status",
        "current_phase",
        "last_complete_phase",
        "reason",
        "tools_allowed",
        "validation_passed",
        "updated_at",
        "created_at",
        "revision",
    ),
)
def test_run_status_schema_requires_complete_lifecycle_authority(
    required_field: str,
) -> None:
    runtime = load_runtime()
    status = copy.deepcopy(minimal_instances()["ultra-run-status.schema.json"])
    del status[required_field]

    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-run-status.schema.json", status)


def test_run_status_schema_closes_created_complete_and_cancelled_invariants() -> None:
    runtime = load_runtime()
    running = minimal_instances()["ultra-run-status.schema.json"]

    created = copy.deepcopy(running)
    created.update(
        status="created",
        previous_status=None,
        phase_id="U0",
        current_phase="U0",
        last_complete_phase=None,
        tools_allowed=False,
        validation_passed=False,
        revision=0,
    )
    runtime.validate_instance("ultra-run-status.schema.json", created)

    complete = copy.deepcopy(running)
    complete.update(
        status="complete",
        previous_status="running",
        phase_id="U12",
        current_phase="U12",
        last_complete_phase="U12",
        tools_allowed=False,
        validation_passed=True,
        revision=2,
    )
    runtime.validate_instance("ultra-run-status.schema.json", complete)
    for field, invalid in (
        ("phase_id", "U11"),
        ("current_phase", "U11"),
        ("last_complete_phase", "U11"),
        ("tools_allowed", True),
        ("validation_passed", False),
    ):
        broken = copy.deepcopy(complete)
        broken[field] = invalid
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-run-status.schema.json", broken)

    cancelled = copy.deepcopy(running)
    cancelled.update(status="cancelled", tools_allowed=False)
    runtime.validate_instance("ultra-run-status.schema.json", cancelled)
    cancelled["tools_allowed"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-run-status.schema.json", cancelled)


def test_run_status_schema_accepts_only_canonical_fork_authority_hash() -> None:
    runtime = load_runtime()
    anchored = copy.deepcopy(minimal_instances()["ultra-run-status.schema.json"])
    anchored["fork_authority_sha256"] = HASH_A

    runtime.validate_instance("ultra-run-status.schema.json", anchored)

    anchored["fork_authority_sha256"] = "A" * 64
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-run-status.schema.json", anchored)


def test_recovery_checkpoint_schema_distinguishes_phase_and_packet_boundaries() -> None:
    runtime = load_runtime()
    phase = copy.deepcopy(
        minimal_instances()["ultra-recovery-checkpoint.schema.json"]
    )
    runtime.validate_instance("ultra-recovery-checkpoint.schema.json", phase)

    for field, invalid in (
        ("boundary_id", "U8"),
        ("boundary_ordinal", 1),
    ):
        broken = copy.deepcopy(phase)
        broken[field] = invalid
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-recovery-checkpoint.schema.json", broken)

    packet = copy.deepcopy(phase)
    packet.update(
        phase_id="U11",
        boundary_kind="article-packet",
        boundary_id="PACKET-001",
        boundary_ordinal=1,
    )
    runtime.validate_instance("ultra-recovery-checkpoint.schema.json", packet)
    for field, invalid in (
        ("phase_id", "U10"),
        ("boundary_ordinal", 0),
        ("boundary_id", "packet with spaces"),
    ):
        broken = copy.deepcopy(packet)
        broken[field] = invalid
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-recovery-checkpoint.schema.json", broken)


@pytest.mark.parametrize(
    "required_field",
    (
        "parent_run_id",
        "parent_checkpoint_sha256",
        "parent_version_binding",
        "compatibility_result",
        "fork_reason",
        "frozen_input_refs",
        "inherited_artifact_hashes",
    ),
)
def test_run_migration_schema_requires_closed_parent_and_inheritance_authority(
    required_field: str,
) -> None:
    runtime = load_runtime()
    migration = copy.deepcopy(
        minimal_instances()["ultra-run-migration.schema.json"]
    )
    del migration[required_field]

    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-run-migration.schema.json", migration)


@pytest.mark.parametrize(
    ("path", "invalid"),
    (
        (("compatibility_result",), "resume"),
        (("parent_checkpoint_sha256",), "not-a-hash"),
        (("parent_version_binding", "runtime_version"), "not-semver"),
        (("frozen_input_refs",), []),
        (("inherited_artifact_hashes",), []),
    ),
)
def test_run_migration_schema_rejects_unfrozen_or_nonfork_payloads(
    path: tuple[str, ...], invalid: Any
) -> None:
    runtime = load_runtime()
    migration = copy.deepcopy(
        minimal_instances()["ultra-run-migration.schema.json"]
    )
    target: Any = migration
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = invalid

    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-run-migration.schema.json", migration)


def test_run_migration_keeps_parent_binding_general_and_child_binding_current() -> None:
    runtime = load_runtime()
    migration = copy.deepcopy(
        minimal_instances()["ultra-run-migration.schema.json"]
    )
    migration["parent_version_binding"].update(
        framework_version="8.1",
        framework_revision="v8.1-r9",
        runtime_version="0.9.0",
        artifact_schema_version=0,
    )

    runtime.validate_instance("ultra-run-migration.schema.json", migration)
    assert migration["version_binding"] == version_binding()
    assert migration["parent_version_binding"] != migration["version_binding"]


@pytest.mark.parametrize(
    ("status", "event_type", "failure_code", "output_hashes"),
    (
        ("complete", "phase-completed", None, [HASH_B]),
        ("failed", "phase-failed", "ULTRA-FAILED", []),
        ("blocked", "phase-blocked", "ULTRA-BLOCKED", []),
        ("cancelled", "phase-cancelled", "ULTRA-CANCELLED", []),
    ),
)
def test_phase_event_pairs_all_four_states_and_failure_outputs(
    status: str,
    event_type: str,
    failure_code: str | None,
    output_hashes: list[str],
) -> None:
    runtime = load_runtime()
    event = copy.deepcopy(minimal_instances()["ultra-phase-event.schema.json"])
    event.update(
        status=status,
        event_type=event_type,
        failure_code=failure_code,
        output_artifact_hashes=output_hashes,
    )
    runtime.validate_instance("ultra-phase-event.schema.json", event)

    wrong_pair = copy.deepcopy(event)
    wrong_pair["event_type"] = (
        "phase-failed" if event_type != "phase-failed" else "phase-completed"
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-phase-event.schema.json", wrong_pair)

    if status == "complete":
        with_code = copy.deepcopy(event)
        with_code["failure_code"] = "ULTRA-UNEXPECTED"
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-phase-event.schema.json", with_code)
    else:
        with_output = copy.deepcopy(event)
        with_output["output_artifact_hashes"] = [HASH_A]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-phase-event.schema.json", with_output)

        without_code = copy.deepcopy(event)
        without_code["failure_code"] = ""
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-phase-event.schema.json", without_code)


def test_phase_event_artifact_hash_arrays_remain_bare_sha256_strings() -> None:
    runtime = load_runtime()
    event = copy.deepcopy(minimal_instances()["ultra-phase-event.schema.json"])
    event["input_artifact_hashes"] = [{"sha256": HASH_A}]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-phase-event.schema.json", event)


@pytest.mark.parametrize(
    "authority_field",
    (
        "source_manifest_sha256",
        "release_manifest_sha256",
        "compatibility_matrix_sha256",
        "knowledge_report_sha256",
        "skill_tree_sha256",
        "input_snapshot_sha256",
        "parent_event_sha256",
        "evidence_cutoff",
        "acl_status",
        "inputs",
    ),
)
def test_source_lock_requires_complete_u1_authority(authority_field: str) -> None:
    runtime = load_runtime()
    source_lock = copy.deepcopy(minimal_instances()["ultra-source-lock.schema.json"])
    del source_lock[authority_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-source-lock.schema.json", source_lock)


def test_source_lock_records_unknown_acl_without_claiming_verification() -> None:
    runtime = load_runtime()
    source_lock = copy.deepcopy(minimal_instances()["ultra-source-lock.schema.json"])
    source_lock["acl_status"] = "unknown"
    runtime.validate_instance("ultra-source-lock.schema.json", source_lock)

    source_lock["acl_status"] = "verified"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-source-lock.schema.json", source_lock)


@pytest.mark.parametrize(
    "authority_field",
    (
        "source_manifest_sha256",
        "promoted_semantic_snapshot_sha256",
        "source_lock_sha256",
        "parent_event_sha256",
        "receipt_sha256",
        "execution_identity",
        "read_event_sha256",
    ),
)
def test_read_event_requires_manifest_owned_authority(authority_field: str) -> None:
    runtime = load_runtime()
    read_event = copy.deepcopy(minimal_instances()["ultra-read-event.schema.json"])
    del read_event[authority_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-read-event.schema.json", read_event)


def test_read_event_keeps_one_source_content_hash_and_real_host_identity() -> None:
    runtime = load_runtime()
    read_event = copy.deepcopy(minimal_instances()["ultra-read-event.schema.json"])
    read_event["source_unit_content_sha256"] = HASH_A
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-read-event.schema.json", read_event)

    read_event = copy.deepcopy(minimal_instances()["ultra-read-event.schema.json"])
    read_event["execution_identity"]["process_id"] = 0
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-read-event.schema.json", read_event)


def test_retrieval_not_applicable_is_structured_without_magic_authority() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(minimal_instances()["ultra-retrieval-ledger.schema.json"])
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", ledger)

    magic_authority = copy.deepcopy(ledger)
    magic_authority["authorization_sha256"] = "0" * 64
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", magic_authority)

    fabricated_universe = copy.deepcopy(ledger)
    fabricated_universe["decision"]["eligibility_basis"][
        "material_universe_sha256"
    ] = HASH_A
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-retrieval-ledger.schema.json", fabricated_universe
        )


@pytest.mark.parametrize(
    ("network_available", "outbound_authorized"),
    ((False, False), (False, True), (True, False), (True, True)),
)
def test_retrieval_not_applicable_records_actual_capability_flags(
    network_available: bool, outbound_authorized: bool
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(minimal_instances()["ultra-retrieval-ledger.schema.json"])
    ledger["network_available"] = network_available
    ledger["outbound_authorized"] = outbound_authorized
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    "executed_field",
    ("authorization", "query-count", "queries", "sources", "entries", "rounds"),
)
def test_retrieval_not_applicable_forbids_execution_artifacts(
    executed_field: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(minimal_instances()["ultra-retrieval-ledger.schema.json"])
    executed = required_retrieval_instance()
    if executed_field == "authorization":
        ledger["authorization_sha256"] = HASH_B
    elif executed_field == "query-count":
        ledger["query_count"] = 1
    elif executed_field == "queries":
        ledger["queries"] = executed["queries"]
    elif executed_field == "sources":
        ledger["sources"] = executed["sources"]
    elif executed_field == "entries":
        ledger["entries"] = executed["entries"]
    else:
        ledger["saturation"]["rounds"] = 1
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", ledger)


def test_retrieval_closed_input_na_binds_material_inventory() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(minimal_instances()["ultra-retrieval-ledger.schema.json"])
    basis = ledger["decision"]["eligibility_basis"]
    basis["analysis_kind"] = "closed-input"
    basis["material_inventory"] = [
        {
            "path": "input/closed-material.md",
            "sha256": HASH_A,
            "media_type": "text/markdown",
        }
    ]
    basis["material_universe_sha256"] = HASH_B
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", ledger)

    basis["material_inventory"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", ledger)


def test_required_retrieval_uses_closed_multi_trigger_eligibility_basis() -> None:
    runtime = load_runtime()
    required = required_retrieval_instance()
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", required)

    unknown_trigger = copy.deepcopy(required)
    unknown_trigger["decision"]["eligibility_basis"]["trigger_kinds"] = [
        "editorial-preference"
    ]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-retrieval-ledger.schema.json", unknown_trigger
        )

    open_basis = copy.deepcopy(required)
    open_basis["decision"]["eligibility_basis"]["business_policy"] = "invented"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", open_basis)

    missing_basis = copy.deepcopy(required)
    missing_basis["decision"]["eligibility_basis"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", missing_basis)


def test_retrieval_eligibility_status_never_encodes_execution_blocking() -> None:
    runtime = load_runtime()
    blocked_decision = blocked_retrieval_instance()
    blocked_decision["decision"]["status"] = "blocked"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-retrieval-ledger.schema.json", blocked_decision
        )


def test_required_complete_retrieval_binds_authority_and_allows_no_sources() -> None:
    runtime = load_runtime()
    required = required_retrieval_instance()

    missing_authority = copy.deepcopy(required)
    missing_authority["authorization_sha256"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-retrieval-ledger.schema.json", missing_authority
        )

    no_sources = copy.deepcopy(required)
    no_sources["sources"] = []
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", no_sources)


@pytest.mark.parametrize("block_class", RETRIEVAL_BLOCK_CLASSES)
def test_required_blocked_retrieval_preserves_basis_and_closed_block_result(
    block_class: str,
) -> None:
    runtime = load_runtime()
    blocked = blocked_retrieval_instance(block_class)
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", blocked)

    missing_result = copy.deepcopy(blocked)
    missing_result["block_result"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", missing_result)


def test_required_blocked_retrieval_allows_honest_partial_progress() -> None:
    runtime = load_runtime()
    blocked = blocked_retrieval_instance("timeout")
    partial = required_retrieval_instance()
    blocked["query_count"] = partial["query_count"]
    blocked["queries"] = partial["queries"]
    blocked["entries"] = partial["entries"]
    blocked["saturation"] = {"rounds": 1, "stop_reason": "timeout"}
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", blocked)


def test_retrieval_status_and_block_result_cannot_confuse_execution_states() -> None:
    runtime = load_runtime()

    complete_with_block = required_retrieval_instance()
    complete_with_block["block_result"] = {
        "block_class": "timeout",
        "detail": "A timeout was observed.",
    }
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-retrieval-ledger.schema.json", complete_with_block
        )

    na_as_complete = copy.deepcopy(
        minimal_instances()["ultra-retrieval-ledger.schema.json"]
    )
    na_as_complete["retrieval_status"] = "required-complete"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-retrieval-ledger.schema.json", na_as_complete)

    unknown_block_class = blocked_retrieval_instance()
    unknown_block_class["block_result"]["block_class"] = "business-policy"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-retrieval-ledger.schema.json", unknown_block_class
        )


def test_retrieval_source_inventory_allows_honest_unknown_dates() -> None:
    runtime = load_runtime()
    required = required_retrieval_instance()
    record = required["sources"][0]["record"]
    assert record["event_date"] is None
    assert record["publication_date"] is None
    runtime.validate_instance("ultra-retrieval-ledger.schema.json", required)


@pytest.mark.parametrize(
    "authority_field", ("evidence_artifact_sha256", "evidence_content_sha256")
)
def test_world_volume_requires_named_u3_hash_roles(authority_field: str) -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    del volume[authority_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


@pytest.mark.parametrize("required_field", PROMOTED_RAC_FIELDS)
def test_world_volume_uses_exact_promoted_rac_fields(required_field: str) -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    del volume["memberships"][0][required_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)

    legacy = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    legacy["memberships"][0]["membership_id"] = "MEMBERSHIP-1"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", legacy)


@pytest.mark.parametrize("required_field", PROMOTED_RCC_FIELDS)
def test_world_volume_uses_exact_promoted_rcc_fields(required_field: str) -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    del volume["circle_relations"][0][required_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)

    legacy = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    legacy["circle_relations"][0]["relation_id"] = "REL-1"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", legacy)


def test_world_volume_requires_exact_axes_and_all_five_clock_kinds() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["actors"][0]["scale_profile"]["spatial"] = volume["actors"][0][
        "scale_profile"
    ].pop("A")
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)

    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["clocks"] = [
        clock for clock in volume["clocks"] if clock["kind"] != "institutional"
    ]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_required_arrays_may_be_honestly_empty() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["memberships"][0]["roles"] = []
    volume["memberships"][0]["source_refs"] = []
    volume["circle_relations"][0]["shared_members_or_interfaces"] = []
    volume["circle_relations"][0]["evidence_refs"] = []
    runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_circle_requires_nonempty_reification_risks() -> None:
    runtime = load_runtime()
    missing = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    del missing["circles"][0]["reification_risks"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", missing)

    empty = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    empty["circles"][0]["reification_risks"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", empty)


def test_world_volume_event_requires_closed_origin_kind() -> None:
    runtime = load_runtime()
    missing = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    del missing["events"][0]["origin_kind"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", missing)

    unknown = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    unknown["events"][0]["origin_kind"] = "unknown"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", unknown)


def test_world_volume_exogenous_event_accepts_null_or_boundary_source() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    event = volume["events"][0]
    event["origin_kind"] = "exogenous"
    event["source_position_id"] = None
    runtime.validate_instance("ultra-world-volume.schema.json", volume)

    event["source_position_id"] = "POS-TEAM-MANAGER"
    runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_endogenous_event_rejects_null_source() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["events"][0]["source_position_id"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_containment_basis_is_closed_to_design_six() -> None:
    runtime = load_runtime()
    for basis in ("成员", "角色", "合同", "资源会计", "制度管辖", "空间"):
        volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
        volume["containment_relations"][0]["basis"] = basis
        runtime.validate_instance("ultra-world-volume.schema.json", volume)

    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["containment_relations"][0]["basis"] = "shared resource dependency"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_local_distributions_allow_honest_empty_or_partial() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    power_distribution = copy.deepcopy(volume["local_distributions"][0])
    volume["local_distributions"] = []
    runtime.validate_instance("ultra-world-volume.schema.json", volume)

    volume["local_distributions"] = [power_distribution]
    runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_represents_missing_channel_authority_as_noop_shape() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    channel = volume["channels"][0]
    channel["threshold"] = None
    channel["identity_mapping"] = None
    channel["acl"] = None
    channel["evidence_ids"] = []
    event = volume["events"][0]
    event["target_position_ids"] = []
    event["channel_conditions"] = [
        {
            "channel_id": "CHANNEL-1",
            "threshold_met": False,
            "identity_preserved": False,
            "acl_authorized": False,
            "evidence_ids": [],
        }
    ]
    event["M_updates"] = []
    event["Psi_updates"] = []
    event["relation_updates"] = []
    event["clock_deltas"] = []
    runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_event_with_no_channel_rejects_updates() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["events"][0]["channel_ids"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


@pytest.mark.parametrize(
    ("condition_field", "invalid_value"),
    (
        ("threshold_met", False),
        ("identity_preserved", False),
        ("acl_authorized", False),
        ("evidence_ids", []),
    ),
)
def test_world_volume_event_without_any_fully_valid_condition_rejects_updates(
    condition_field: str, invalid_value: object
) -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    volume["events"][0]["channel_conditions"][0][condition_field] = invalid_value
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_event_allows_mixed_valid_and_invalid_conditions() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    invalid_condition = copy.deepcopy(volume["events"][0]["channel_conditions"][0])
    invalid_condition["threshold_met"] = False
    volume["events"][0]["channel_conditions"].append(invalid_condition)
    runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_no_channel_noop_allows_only_empty_updates() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    event = volume["events"][0]
    event["channel_ids"] = []
    event["channel_conditions"] = []
    event["M_updates"] = []
    event["Psi_updates"] = []
    event["relation_updates"] = []
    event["clock_deltas"] = []
    runtime.validate_instance("ultra-world-volume.schema.json", volume)


def test_world_volume_events_use_target_volume_and_value_level_updates() -> None:
    runtime = load_runtime()
    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    del volume["events"][0]["target_volume_id"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)

    volume = copy.deepcopy(minimal_instances()["ultra-world-volume.schema.json"])
    update = volume["events"][0]["M_updates"][0]
    update["changed_variable_names"] = ["budget"]
    del update["variable_changes"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-world-volume.schema.json", volume)


@pytest.mark.parametrize(
    "authority_field",
    (
        "evidence_artifact_sha256",
        "evidence_content_sha256",
        "world_volume_artifact_sha256",
        "world_volume_content_sha256",
    ),
)
def test_transformation_ledger_requires_two_named_upstream_pairs(
    authority_field: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    del ledger[authority_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    "missing_kind", ("scale", "circle-relation", "representation-translation")
)
def test_transformation_ledger_requires_each_transform_class(
    missing_kind: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"] = [
        item for item in ledger["transformations"] if item["kind"] != missing_kind
    ]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_transformation_ledger_allows_multiple_records_and_empty_audit_arrays() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"].append(transformation_record("SCALE-2", "scale"))
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_transformation_kind_label_cannot_be_swapped_over_identity_shape() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"].append(transformation_record("SCALE-KEEP", "scale"))
    ledger["transformations"][0]["kind"] = "circle-relation"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("transform_index", "identity_side", "wrong_identity_type"),
    (
        (0, "input_identity", "circle-relation"),
        (0, "output_identity", "represented-state"),
        (1, "input_identity", "scale-state"),
        (1, "output_identity", "source-representation"),
        (2, "input_identity", "scale-state"),
        (2, "output_identity", "circle-relation"),
    ),
)
def test_transformation_kind_rejects_swapped_identity_type(
    transform_index: int, identity_side: str, wrong_identity_type: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"][transform_index][identity_side][
        "identity_type"
    ] = wrong_identity_type
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("transform_index", "identity_side", "wrong_axis"),
    (
        (0, "input_identity", "T"),
        (0, "output_identity", "O"),
        (1, "input_identity", "A"),
        (1, "output_identity", "J"),
        (2, "input_identity", "T"),
        (2, "output_identity", "O"),
    ),
)
def test_transformation_kind_binds_identity_axis_shape(
    transform_index: int, identity_side: str, wrong_axis: str | None
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"][transform_index][identity_side]["axis_id"] = (
        wrong_axis
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_rejects_legacy_single_axis_t_to_o_shape() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    scale["input_identity"]["axis_id"] = "T"
    scale["output_identity"]["axis_id"] = "O"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_accepts_exact_nine_axis_profile() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    axis_ids = [
        item["axis_id"] for item in ledger["transformations"][0]["axis_differences"]
    ]
    assert tuple(axis_ids) == SCALE_AXIS_IDS
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "unknown"))
def test_scale_transformation_rejects_nonexact_axis_set(mutation: str) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    differences = ledger["transformations"][0]["axis_differences"]
    if mutation == "missing":
        differences.pop()
    elif mutation == "duplicate":
        differences[-1]["axis_id"] = "A"
        assert differences[0] != differences[-1]
    else:
        differences[-1]["axis_id"] = "Z"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("container", "extra_field"),
    (("witness", "explanation"), ("payload", "raw_text")),
)
def test_scale_transformation_rejects_open_witness_objects(
    container: str, extra_field: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    witness = ledger["transformations"][0]["axis_differences"][0]["order_witness"]
    target = witness if container == "witness" else witness["comparison_payload"]
    target[extra_field] = "free text"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("required_field", AXIS_DIFFERENCE_FIELDS)
def test_scale_axis_difference_requires_every_promoted_field(
    required_field: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    difference = ledger["transformations"][0]["axis_differences"][0]
    del difference[required_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("required_field", ORDER_WITNESS_FIELDS)
def test_scale_transformation_witness_requires_every_promoted_field(
    required_field: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    witness = ledger["transformations"][0]["axis_differences"][0]["order_witness"]
    del witness[required_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_nonunknown_relation_rejects_missing_witness() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    difference = ledger["transformations"][0]["axis_differences"][0]
    difference["order_witness"] = order_witness("MISSING-A", "unknown")
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_unknown_relation_rejects_valid_witness() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["relation"] = "unknown"
    scale["transformation_class"] = "unresolved"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("authority_path", "bad_value"),
    (
        (("comparator_id",), None),
        (("comparator_version",), None),
        (("verifier_id",), None),
        (("evidence_refs",), []),
        (("comparison_payload", "payload_kind"), None),
        (("comparison_payload", "payload_ref"), None),
        (("comparison_payload", "payload_sha256"), None),
        (("comparator_result_ref",), None),
        (("verification_artifact_ref",), None),
        (("verification_hash",), None),
        (("validation_status",), "invalid"),
    ),
)
def test_nonunknown_axis_relation_rejects_null_or_nonvalid_authority(
    authority_path: tuple[str, ...], bad_value: object
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    target: dict[str, Any] = ledger["transformations"][0]["axis_differences"][0][
        "order_witness"
    ]
    for part in authority_path[:-1]:
        target = target[part]
    target[authority_path[-1]] = bad_value
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("authority_path", "stolen_value"),
    (
        (("comparator_id",), "AXIS-COMPARATOR-STOLEN"),
        (("comparator_version",), "1.0.0"),
        (("verifier_id",), "AXIS-VERIFIER-STOLEN"),
        (("evidence_refs",), ["EVIDENCE-1"]),
        (("comparison_payload", "payload_kind"), "mapping"),
        (("comparison_payload", "payload_ref"), "COMPARISON-PAYLOAD-STOLEN"),
        (("comparison_payload", "payload_sha256"), HASH_B),
        (("comparator_result_ref",), "COMPARATOR-RESULT-STOLEN"),
        (("verification_artifact_ref",), "VERIFICATION-ARTIFACT-STOLEN"),
        (("verification_hash",), HASH_C),
        (("validation_status",), "valid"),
    ),
)
def test_unknown_axis_relation_rejects_stolen_authority(
    authority_path: tuple[str, ...], stolen_value: object
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("UNKNOWN-A", "unknown")
    scale["transformation_class"] = "unresolved"
    target: dict[str, Any] = difference["order_witness"]
    for part in authority_path[:-1]:
        target = target[part]
    target[authority_path[-1]] = stolen_value
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("payload_kind", "axis_id", "relation"),
    (
        ("mapping", "C", "expands"),
        ("set", "A", "expands"),
        ("interval", "T", "expands"),
        ("graph", "N", "expands"),
        ("authorization-difference", "J", "expands"),
        ("deep-equality", "A", "equal"),
    ),
)
def test_scale_transformation_accepts_representative_comparison_payload_kinds(
    payload_kind: str, axis_id: str, relation: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    axis_index = SCALE_AXIS_IDS.index(axis_id)
    scale["axis_differences"][axis_index] = axis_difference(
        "PAYLOAD-KIND", axis_id, relation
    )
    scale["transformation_class"] = "all_equal" if relation == "equal" else "elevation"
    payload = scale["axis_differences"][axis_index]["order_witness"][
        "comparison_payload"
    ]
    payload["payload_kind"] = payload_kind
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_rejects_deep_equality_for_expansion() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = axis_difference("DEEP-EXPANDS", "A", "expands")
    difference["order_witness"]["comparison_payload"][
        "payload_kind"
    ] = "deep-equality"
    scale["axis_differences"][0] = difference
    scale["transformation_class"] = "elevation"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_j_expansion_requires_authorization_difference() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    j_index = SCALE_AXIS_IDS.index("J")
    difference = axis_difference("J-EXPANDS", "J", "expands")
    assert difference["order_witness"]["comparison_payload"]["payload_kind"] == (
        "mapping"
    )
    scale["axis_differences"][j_index] = difference
    scale["transformation_class"] = "elevation"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_rejects_unknown_comparison_payload_kind() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"][0]["axis_differences"][0]["order_witness"][
        "comparison_payload"
    ]["payload_kind"] = "free-text"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("required_field", COMPARISON_PAYLOAD_FIELDS)
def test_scale_comparison_payload_requires_every_envelope_field(
    required_field: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    payload = ledger["transformations"][0]["axis_differences"][0][
        "order_witness"
    ]["comparison_payload"]
    del payload[required_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("missing_status", "missing_side"),
    tuple(
        (status, side)
        for status in ("unknown", "not_observable", "withheld_for_protection")
        for side in ("source", "target")
    ),
)
def test_scale_transformation_accepts_materially_missing_axis_as_unknown(
    missing_status: str, missing_side: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference[f"{missing_side}_state"] = missing_axis_state(missing_status)
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("UNKNOWN-A", "unknown")
    scale["transformation_class"] = "unresolved"
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("missing_side", ("source", "target"))
def test_scale_one_sided_not_applicable_axis_is_incomparable(
    missing_side: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference[f"{missing_side}_state"] = missing_axis_state("not_applicable")
    difference["relation"] = "incomparable"
    difference["order_witness"] = order_witness("NA-INCOMPARABLE-A", "incomparable")
    scale["transformation_class"] = "horizontal_or_incomparable"
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("missing_side", ("source", "target"))
def test_scale_one_sided_not_applicable_axis_cannot_be_unknown(
    missing_side: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference[f"{missing_side}_state"] = missing_axis_state("not_applicable")
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("NA-UNKNOWN-A", "unknown")
    scale["transformation_class"] = "unresolved"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("missing_status", "missing_side", "wrong_relation"),
    tuple(
        (status, side, relation)
        for status in ("unknown", "not_observable", "withheld_for_protection")
        for side in ("source", "target")
        for relation in ("equal", "expands")
    ),
)
def test_materially_missing_axis_rejects_nonunknown_relation(
    missing_status: str, missing_side: str, wrong_relation: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference[f"{missing_side}_state"] = missing_axis_state(missing_status)
    difference["relation"] = wrong_relation
    difference["order_witness"] = order_witness(
        "MISSING-NONUNKNOWN-A", wrong_relation
    )
    scale["transformation_class"] = (
        "all_equal" if wrong_relation == "equal" else "elevation"
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_bilateral_not_applicable_axis_is_equal_with_valid_witness() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    difference = ledger["transformations"][0]["axis_differences"][0]
    difference["source_state"] = missing_axis_state("not_applicable")
    difference["target_state"] = copy.deepcopy(difference["source_state"])
    difference["relation"] = "equal"
    difference["order_witness"] = order_witness("NA-EQUAL-A", "equal")
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_bilateral_not_applicable_axis_allows_unresolved_unknown() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["source_state"] = missing_axis_state("not_applicable")
    difference["target_state"] = copy.deepcopy(difference["source_state"])
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("NA-UNKNOWN-A", "unknown")
    scale["transformation_class"] = "unresolved"
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("relation", "transformation_class"),
    (
        ("expands", "elevation"),
        ("contracts", "reduction"),
        ("incomparable", "horizontal_or_incomparable"),
    ),
)
def test_scale_bilateral_not_applicable_axis_rejects_directional_relations(
    relation: str, transformation_class: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["source_state"] = missing_axis_state("not_applicable")
    difference["target_state"] = copy.deepcopy(difference["source_state"])
    difference["relation"] = relation
    difference["order_witness"] = order_witness(f"NA-{relation}-A", relation)
    scale["transformation_class"] = transformation_class
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_missing_axis_state_requires_a_nonempty_reason() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["target_state"] = missing_axis_state("unknown")
    difference["target_state"]["description"] = ""
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("UNKNOWN-A", "unknown")
    scale["transformation_class"] = "unresolved"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_missing_order_witness_requires_a_nonempty_reason() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("UNKNOWN-A", "unknown")
    difference["order_witness"]["comparison_payload"]["description"] = ""
    scale["transformation_class"] = "unresolved"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("mutation", ("unknown-status", "open", "null"))
def test_scale_axis_state_rejects_unknown_open_or_null_shape(mutation: str) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    difference = ledger["transformations"][0]["axis_differences"][0]
    if mutation == "unknown-status":
        difference["target_state"]["status"] = "absent"
    elif mutation == "open":
        difference["target_state"]["raw_state"] = "free text"
    else:
        difference["target_state"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("status", "authority_field"),
    (("recorded", "normalized_state_ref"), ("recorded", "normalized_state_sha256")),
)
def test_recorded_axis_state_rejects_null_authority(
    status: str, authority_field: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    state = ledger["transformations"][0]["axis_differences"][0]["target_state"]
    assert state["status"] == status
    state[authority_field] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("authority_field", "stolen_value"),
    (("normalized_state_ref", "AXIS-STATE-STOLEN"), ("normalized_state_sha256", HASH_B)),
)
def test_missing_axis_state_rejects_normalized_authority(
    authority_field: str, stolen_value: object
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = ledger["transformations"][0]
    difference = scale["axis_differences"][0]
    difference["target_state"] = missing_axis_state("unknown")
    difference["target_state"][authority_field] = stolen_value
    difference["relation"] = "unknown"
    difference["order_witness"] = order_witness("UNKNOWN-A", "unknown")
    scale["transformation_class"] = "unresolved"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize("transformation_class", TRANSFORMATION_CLASSES)
def test_scale_transformation_accepts_authority_classification_precedence(
    transformation_class: str,
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"][0] = transformation_record(
        "SCALE-CLASS",
        "scale",
        transformation_class=transformation_class,
    )
    for difference in ledger["transformations"][0]["axis_differences"]:
        if difference["relation"] in {"expands", "contracts"}:
            assert difference["source_state"]["normalized_state_sha256"] != (
                difference["target_state"]["normalized_state_sha256"]
            )
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("transformation_class", "masked_relations"),
    (
        ("horizontal_or_incomparable", {"incomparable", "unknown"}),
        ("mixed", {"expands", "contracts", "unknown"}),
    ),
)
def test_scale_classification_precedence_masks_lower_priority_relations(
    transformation_class: str, masked_relations: set[str]
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = transformation_record(
        "SCALE-PRECEDENCE",
        "scale",
        transformation_class=transformation_class,
    )
    assert masked_relations.issubset(
        {item["relation"] for item in scale["axis_differences"]}
    )
    ledger["transformations"][0] = scale
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("authority_class", "wrong_class"),
    (
        ("horizontal_or_incomparable", "mixed"),
        ("horizontal_or_incomparable", "unresolved"),
        ("mixed", "unresolved"),
        ("unresolved", "elevation"),
    ),
)
def test_scale_classification_rejects_precedence_bypass(
    authority_class: str, wrong_class: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    scale = transformation_record(
        "SCALE-PRECEDENCE-BYPASS",
        "scale",
        transformation_class=authority_class,
    )
    scale["transformation_class"] = wrong_class
    ledger["transformations"][0] = scale
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_all_equal_accepts_builtin_deep_equality_witness() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    difference = ledger["transformations"][0]["axis_differences"][0]
    assert difference["source_state"] == difference["target_state"]
    assert difference["order_witness"]["comparator_id"] == "builtin:deep-equality"
    runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    ("transform_index", "overflow_kind"),
    ((1, "axis-difference"), (1, "classification"), (2, "axis-difference"), (2, "classification")),
)
def test_non_scale_transformations_reject_scale_profile_fields(
    transform_index: int, overflow_kind: str
) -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    transform = ledger["transformations"][transform_index]
    if overflow_kind == "axis-difference":
        transform["axis_differences"] = [
            axis_difference("NON-SCALE", "A", "equal")
        ]
    else:
        transform["transformation_class"] = "all_equal"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_scale_transformation_rejects_wrong_classification() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"][0]["transformation_class"] = "elevation"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


def test_u5_transform_identity_cannot_jump_to_article_semantic_unit() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(
        minimal_instances()["ultra-transformation-ledger.schema.json"]
    )
    ledger["transformations"][0]["output_identity"][
        "identity_type"
    ] = "article-semantic-unit"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-transformation-ledger.schema.json", ledger)


@pytest.mark.parametrize(
    "authority_field",
    (
        "evidence_artifact_sha256",
        "evidence_content_sha256",
        "world_volume_artifact_sha256",
        "world_volume_content_sha256",
        "transformation_ledger_artifact_sha256",
        "transformation_ledger_content_sha256",
        "registry_sha256",
        "route_map_sha256",
        "contract_map_sha256",
    ),
)
def test_concept_disposition_requires_u5_upstreams_and_knowledge_authority(
    authority_field: str,
) -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    del closure[authority_field]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


def test_concept_disposition_is_u5_and_has_no_article_section_assignment() -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    closure["phase_id"] = "U6"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


def test_concept_disposition_allows_empty_authoritative_required_id_sets() -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    closure["required_route_ids"] = []
    closure["required_contract_ids"] = []
    closure["required_requirement_ids"] = []
    runtime.validate_instance("ultra-concept-disposition.schema.json", closure)

    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    closure["semantic_obligations"][0]["section_id"] = "SECTION-01"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


def test_unknown_pending_requires_structured_condition_and_evidence_plan() -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    disposition = closure["dispositions"][0]
    obligation = closure["semantic_obligations"][0]
    disposition["status"] = "unknown-pending"
    disposition["condition_branch"] = None
    obligation["status"] = "unknown-pending"
    obligation["condition_branch_id"] = "CONDITION-1"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)

    disposition["condition_branch"] = {
        "branch_id": "CONDITION-1",
        "condition": "A named evidence gap is resolved.",
        "evidence_plan": {
            "plan_id": "EVIDENCE-PLAN-1",
            "required_evidence": ["Observe the named source condition."],
        },
    }
    runtime.validate_instance("ultra-concept-disposition.schema.json", closure)

    disposition["condition_branch"]["evidence_plan"][
        "target_section_id"
    ] = "SECTION-01"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


@pytest.mark.parametrize("status", ("applied", "unknown-pending"))
def test_applied_and_unknown_pending_dispositions_require_an_obligation(
    status: str,
) -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    disposition = closure["dispositions"][0]
    disposition["status"] = status
    if status == "unknown-pending":
        disposition["condition_branch"] = {
            "branch_id": "CONDITION-1",
            "condition": "A named evidence gap is resolved.",
            "evidence_plan": {
                "plan_id": "EVIDENCE-PLAN-1",
                "required_evidence": ["Observe the named source condition."],
            },
        }
        obligation = closure["semantic_obligations"][0]
        obligation["status"] = "unknown-pending"
        obligation["condition_branch_id"] = "CONDITION-1"
    disposition["obligation_ids"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


@pytest.mark.parametrize("status", ("not-applicable", "tested-rejected"))
def test_nonsemantic_dispositions_allow_empty_obligation_sets(status: str) -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    disposition = closure["dispositions"][0]
    disposition["status"] = status
    disposition["obligation_ids"] = []
    disposition["condition_branch"] = None
    closure["semantic_obligations"] = []
    runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


@pytest.mark.parametrize("status", ("applied", "unknown-pending"))
def test_semantic_dispositions_require_top_level_obligation_records(
    status: str,
) -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    disposition = closure["dispositions"][0]
    disposition["status"] = status
    if status == "unknown-pending":
        disposition["condition_branch"] = {
            "branch_id": "CONDITION-1",
            "condition": "A named evidence gap is resolved.",
            "evidence_plan": {
                "plan_id": "EVIDENCE-PLAN-1",
                "required_evidence": ["Observe the named source condition."],
            },
        }
    assert disposition["obligation_ids"]
    closure["semantic_obligations"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


@pytest.mark.parametrize(
    ("disposition_status", "obligation_status"),
    (
        ("unknown-pending", "applied"),
        ("applied", "tested-rejected"),
    ),
)
def test_semantic_obligation_status_category_covers_disposition_status(
    disposition_status: str, obligation_status: str
) -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    disposition = closure["dispositions"][0]
    disposition["status"] = disposition_status
    if disposition_status == "unknown-pending":
        disposition["condition_branch"] = {
            "branch_id": "CONDITION-1",
            "condition": "A named evidence gap is resolved.",
            "evidence_plan": {
                "plan_id": "EVIDENCE-PLAN-1",
                "required_evidence": ["Observe the named source condition."],
            },
        }
    closure["semantic_obligations"][0]["status"] = obligation_status
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


def test_complete_concept_closure_rejects_unvisited_concepts() -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    closure["unvisited_concept_ids"] = ["V82-CONCEPT-UNVISITED"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


def test_incomplete_concept_closure_preserves_unvisited_concepts() -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    closure["closure_complete"] = False
    closure["unvisited_concept_ids"] = ["V82-CONCEPT-UNVISITED"]
    runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


def test_unknown_pending_semantic_obligation_requires_condition_branch_id() -> None:
    runtime = load_runtime()
    closure = copy.deepcopy(
        minimal_instances()["ultra-concept-disposition.schema.json"]
    )
    disposition = closure["dispositions"][0]
    disposition["status"] = "unknown-pending"
    disposition["condition_branch"] = {
        "branch_id": "CONDITION-1",
        "condition": "A named evidence gap is resolved.",
        "evidence_plan": {
            "plan_id": "EVIDENCE-PLAN-1",
            "required_evidence": ["Observe the named source condition."],
        },
    }
    obligation = closure["semantic_obligations"][0]
    obligation["status"] = "unknown-pending"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-concept-disposition.schema.json", closure)

    obligation["condition_branch_id"] = "CONDITION-1"
    runtime.validate_instance("ultra-concept-disposition.schema.json", closure)


W5_SCHEMA_PHASES = {
    "ultra-claim-mechanism-graph.schema.json": "U6",
    "ultra-recursive-state.schema.json": "U7",
    "ultra-recursive-lineage.schema.json": "U7",
    "ultra-order-evaluation.schema.json": "U8",
    "ultra-red-team-report.schema.json": "U8",
    "ultra-verdict.schema.json": "U9",
    "ultra-action-ranking.schema.json": "U9",
    "ultra-forecast-ledger.schema.json": "U9",
    "ultra-forecast-resolution-event.schema.json": "U9",
    "ultra-framework-gap-ledger.schema.json": "U10",
}


def test_w5_artifacts_keep_document_schema_v1_and_exact_phase_ownership() -> None:
    runtime = load_runtime()
    constants = importlib.import_module("ultra_runtime.constants")
    fixtures = minimal_instances()
    assert constants.ARTIFACT_SCHEMA_VERSION == 2
    for schema_name, phase_id in W5_SCHEMA_PHASES.items():
        fixture = fixtures[schema_name]
        assert fixture["schema_version"] == 1
        assert fixture["version_binding"]["artifact_schema_version"] == 2
        runtime.validate_instance(schema_name, fixture)

        wrong_phase = copy.deepcopy(fixture)
        wrong_phase["phase_id"] = "U12"
        with pytest.raises(ValidationError):
            runtime.validate_instance(schema_name, wrong_phase)


def test_u6_graph_requires_named_u3_u4_u5_authorities_and_four_explanations() -> None:
    runtime = load_runtime()
    graph = copy.deepcopy(
        minimal_instances()["ultra-claim-mechanism-graph.schema.json"]
    )
    runtime.validate_instance("ultra-claim-mechanism-graph.schema.json", graph)

    authority_fields = (
        "evidence_ledger_artifact_sha256",
        "world_volume_artifact_sha256",
        "transformation_ledger_artifact_sha256",
        "concept_disposition_artifact_sha256",
    )
    assert len({graph[field] for field in authority_fields}) == len(authority_fields)
    for field in authority_fields:
        broken = copy.deepcopy(graph)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-claim-mechanism-graph.schema.json", broken)

    missing_kind = copy.deepcopy(graph)
    missing_kind["explanations"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", missing_kind
        )

    duplicate_kind = copy.deepcopy(graph)
    duplicate_kind["explanations"][-1]["kind"] = "main"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", duplicate_kind
        )

    invented_effect = copy.deepcopy(graph)
    invented_effect["insights"][0]["effects"] = ["creates-framework-authority"]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", invented_effect
        )


def test_u6_graph_distinguishes_total_from_justified_partial_ranking() -> None:
    runtime = load_runtime()
    total = copy.deepcopy(
        minimal_instances()["ultra-claim-mechanism-graph.schema.json"]
    )
    runtime.validate_instance("ultra-claim-mechanism-graph.schema.json", total)

    missing_justification_role = copy.deepcopy(total)
    del missing_justification_role["partial_ranking_justification"]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", missing_justification_role
        )

    unjustified_partial = copy.deepcopy(total)
    unjustified_partial["explanations"][-1]["rank"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", unjustified_partial
        )

    justified_partial = copy.deepcopy(unjustified_partial)
    justified_partial["partial_ranking_justification"] = (
        "The residual explanation remains incomparable on frozen evidence."
    )
    runtime.validate_instance(
        "ultra-claim-mechanism-graph.schema.json", justified_partial
    )

    empty_justification = copy.deepcopy(justified_partial)
    empty_justification["partial_ranking_justification"] = ""
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", empty_justification
        )

    reason_without_partial_ranking = copy.deepcopy(total)
    reason_without_partial_ranking["partial_ranking_justification"] = (
        "A partial ranking was not actually recorded."
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-claim-mechanism-graph.schema.json", reason_without_partial_ranking
        )


def test_recursive_state_seals_parent_identity_state_boundary_and_inheritance() -> None:
    runtime = load_runtime()
    state = copy.deepcopy(minimal_instances()["ultra-recursive-state.schema.json"])
    runtime.validate_instance("ultra-recursive-state.schema.json", state)

    required_roles = (
        "path_id",
        "node_id",
        "parent_run_id",
        "parent_path_id",
        "parent_node_id",
        "world_volume_artifact_sha256",
        "transformation_ledger_artifact_sha256",
        "concept_disposition_artifact_sha256",
        "claim_mechanism_graph_artifact_sha256",
        "inherited_fact_ids",
        "inherited_evidence_ids",
        "inherited_unknown_ids",
        "inherited_loss_ids",
        "inherited_residual_ids",
        "event_id",
        "mechanism_ids",
        "state_diff_sha256",
        "signal_ids",
        "evidence_identity",
        "declared_evidence_grade",
    )
    for field in required_roles:
        broken = copy.deepcopy(state)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-recursive-state.schema.json", broken)

    bounded = copy.deepcopy(state)
    del bounded["full_state_sha256"]
    bounded["bounded_subgraph"] = {
        "subgraph_id": "SUBGRAPH-1",
        "root_state_ids": ["STATE-ROOT-1"],
        "included_state_ids": ["STATE-ROOT-1", "STATE-LOCAL-1"],
        "excluded_state_ids": ["STATE-OUTSIDE-1"],
        "boundary_rule": "Only positions reachable through CHANNEL-1 are included.",
        "subgraph_sha256": HASH_6,
    }
    runtime.validate_instance("ultra-recursive-state.schema.json", bounded)

    ambiguous = copy.deepcopy(bounded)
    ambiguous["full_state_sha256"] = HASH_7
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-recursive-state.schema.json", ambiguous)

    upgraded_by_depth = copy.deepcopy(state)
    upgraded_by_depth["declared_evidence_grade"] = "high-by-depth"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-recursive-state.schema.json", upgraded_by_depth
        )


def test_recursive_lineage_binds_sealed_state_artifacts_and_typed_branches() -> None:
    runtime = load_runtime()
    lineage = copy.deepcopy(
        minimal_instances()["ultra-recursive-lineage.schema.json"]
    )
    runtime.validate_instance("ultra-recursive-lineage.schema.json", lineage)

    for field in (
        "world_volume_artifact_sha256",
        "transformation_ledger_artifact_sha256",
        "concept_disposition_artifact_sha256",
        "claim_mechanism_graph_artifact_sha256",
        "recursive_state_artifact_hashes",
    ):
        broken = copy.deepcopy(lineage)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-recursive-lineage.schema.json", broken)

    caller_state = copy.deepcopy(lineage)
    caller_state["nodes"][0]["state_sha256"] = HASH_7
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-recursive-lineage.schema.json", caller_state)

    unsealed_node = copy.deepcopy(lineage)
    del unsealed_node["nodes"][0]["recursive_state_artifact_sha256"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-recursive-lineage.schema.json", unsealed_node)

    invented_branch = copy.deepcopy(lineage)
    invented_branch["branches"][0]["kind"] = "optimistic"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-recursive-lineage.schema.json", invented_branch)


def test_order_evaluation_binds_u6_u7_and_requires_four_branch_classes() -> None:
    runtime = load_runtime()
    evaluation = copy.deepcopy(
        minimal_instances()["ultra-order-evaluation.schema.json"]
    )
    runtime.validate_instance("ultra-order-evaluation.schema.json", evaluation)

    for field in (
        "claim_mechanism_graph_artifact_sha256",
        "recursive_lineage_artifact_sha256",
    ):
        broken = copy.deepcopy(evaluation)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-order-evaluation.schema.json", broken)

    missing_branch_class = copy.deepcopy(evaluation)
    missing_branch_class["evaluations"][0]["branch_coverage"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-order-evaluation.schema.json", missing_branch_class
        )

    structured_na = copy.deepcopy(evaluation)
    rival = structured_na["evaluations"][0]["branch_coverage"][1]
    rival["applicability"] = "not-applicable"
    rival["branch_ids"] = []
    rival["not_applicable"] = {
        "reason": "No independent rival branch survives the frozen evidence boundary.",
        "evidence_refs": ["EVIDENCE-1"],
        "residual_ids": ["RESIDUAL-RIVAL-1"],
    }
    runtime.validate_instance("ultra-order-evaluation.schema.json", structured_na)

    unstructured_na = copy.deepcopy(structured_na)
    unstructured_na["evaluations"][0]["branch_coverage"][1][
        "not_applicable"
    ] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-order-evaluation.schema.json", unstructured_na
        )


def test_order_evaluations_are_sequential_and_use_only_frozen_stop_kinds() -> None:
    runtime = load_runtime()
    evaluation = copy.deepcopy(
        minimal_instances()["ultra-order-evaluation.schema.json"]
    )
    second = copy.deepcopy(evaluation["evaluations"][0])
    second["order"] = 2
    evaluation["evaluations"].append(second)
    runtime.validate_instance("ultra-order-evaluation.schema.json", evaluation)

    reversed_orders = copy.deepcopy(evaluation)
    reversed_orders["evaluations"].reverse()
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-order-evaluation.schema.json", reversed_orders
        )

    continuing = copy.deepcopy(evaluation)
    continuing["evaluations"][0]["continue_recursive"] = True
    continuing["evaluations"][0]["continuation_value"] = "bounded"
    continuing["evaluations"][0]["stop_kind"] = None
    runtime.validate_instance("ultra-order-evaluation.schema.json", continuing)

    resource_stop = copy.deepcopy(evaluation)
    resource_stop["evaluations"][0]["stop_kind"] = "resource-exhaustion"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-order-evaluation.schema.json", resource_stop)


def test_red_team_report_binds_u6_u7_u8_and_preserves_evidence_identity() -> None:
    runtime = load_runtime()
    report = copy.deepcopy(minimal_instances()["ultra-red-team-report.schema.json"])
    runtime.validate_instance("ultra-red-team-report.schema.json", report)

    for field in (
        "claim_mechanism_graph_artifact_sha256",
        "recursive_lineage_artifact_sha256",
        "order_evaluation_artifact_sha256",
    ):
        broken = copy.deepcopy(report)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-red-team-report.schema.json", broken)

    unresolved = copy.deepcopy(report)
    unresolved["unresolved_items"] = [
        {
            "unresolved_item_id": "UNRESOLVED-1",
            "challenge_id": "ATTACK-1",
            "description": "The effective channel remains only reported.",
            "evidence_refs": ["EVIDENCE-1"],
        }
    ]
    runtime.validate_instance("ultra-red-team-report.schema.json", unresolved)

    collapsed_identity = copy.deepcopy(report)
    collapsed_identity["attacks"][0]["evidence_identity"] = "evidence"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-red-team-report.schema.json", collapsed_identity
        )


def test_verdict_binds_all_authorities_and_keeps_five_verdicts_independent() -> None:
    runtime = load_runtime()
    verdict = copy.deepcopy(minimal_instances()["ultra-verdict.schema.json"])
    runtime.validate_instance("ultra-verdict.schema.json", verdict)

    for field in (
        "evidence_ledger_artifact_sha256",
        "claim_mechanism_graph_artifact_sha256",
        "recursive_lineage_artifact_sha256",
        "order_evaluation_artifact_sha256",
        "red_team_report_artifact_sha256",
    ):
        broken = copy.deepcopy(verdict)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-verdict.schema.json", broken)

    duplicate_kind = copy.deepcopy(verdict)
    duplicate_kind["five_verdicts"][-1]["kind"] = "fact"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", duplicate_kind)

    without_ranking_justification_role = copy.deepcopy(verdict)
    del without_ranking_justification_role["partial_ranking_justification"]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-verdict.schema.json", without_ranking_justification_role
        )

    lock_ids = [lock["verdict_id"] for lock in verdict["five_verdicts"]]
    assert len(lock_ids) == len(set(lock_ids)) == 5
    without_lock_id = copy.deepcopy(verdict)
    del without_lock_id["five_verdicts"][0]["verdict_id"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", without_lock_id)

    malformed_lock_id = copy.deepcopy(verdict)
    malformed_lock_id["five_verdicts"][0]["verdict_id"] = "not an identifier"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", malformed_lock_id)

    partial_best_current = copy.deepcopy(verdict)
    partial_best_current["explanation_ranking"][-1]["rank"] = None
    partial_best_current["partial_ranking_justification"] = (
        "A best-current judgment cannot leave the ranking partial."
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", partial_best_current)

    duplicate_total_rank = copy.deepcopy(verdict)
    duplicate_total_rank["explanation_ranking"][-1]["rank"] = 1
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", duplicate_total_rank)

    coupled_basis = copy.deepcopy(verdict)
    coupled_basis["five_verdicts"][0]["basis_refs"] = ["MIXED-ROLE-1"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", coupled_basis)


def test_verdict_accepts_exact_non_decidability_instead_of_evasive_judgment() -> None:
    runtime = load_runtime()
    verdict = copy.deepcopy(minimal_instances()["ultra-verdict.schema.json"])
    verdict["judgment_kind"] = "non-decidability"
    verdict["main_verdict"] = None
    verdict["non_decidability"] = {
        "missing_proposition": "Whether CHANNEL-1 is effective rather than nominal.",
        "missing_comparison_rule": None,
    }
    verdict["partial_ranking_justification"] = (
        "The frozen material ranks the first two explanations only."
    )
    verdict["explanation_ranking"][2]["rank"] = None
    verdict["explanation_ranking"][3]["rank"] = None
    runtime.validate_instance("ultra-verdict.schema.json", verdict)

    pseudo_total = copy.deepcopy(verdict)
    pseudo_total["explanation_ranking"][2]["rank"] = 3
    pseudo_total["explanation_ranking"][3]["rank"] = 4
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", pseudo_total)

    unjustified_partial = copy.deepcopy(verdict)
    unjustified_partial["partial_ranking_justification"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", unjustified_partial)

    empty_partial_justification = copy.deepcopy(verdict)
    empty_partial_justification["partial_ranking_justification"] = ""
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-verdict.schema.json", empty_partial_justification
        )

    gapped_partial = copy.deepcopy(verdict)
    gapped_partial["explanation_ranking"][1]["rank"] = 3
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", gapped_partial)

    evasive = copy.deepcopy(verdict)
    evasive["non_decidability"]["missing_proposition"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", evasive)

    ambiguous = copy.deepcopy(verdict)
    ambiguous["non_decidability"]["missing_comparison_rule"] = (
        "No frozen rule compares the two remaining propositions."
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", ambiguous)


def test_action_ranking_binds_verdict_and_compares_all_six_action_kinds() -> None:
    runtime = load_runtime()
    ranking = copy.deepcopy(minimal_instances()["ultra-action-ranking.schema.json"])
    runtime.validate_instance("ultra-action-ranking.schema.json", ranking)

    no_verdict = copy.deepcopy(ranking)
    del no_verdict["verdict_artifact_sha256"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-action-ranking.schema.json", no_verdict)

    no_considered_locks = copy.deepcopy(ranking)
    del no_considered_locks["considered_verdict_ids"]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", no_considered_locks
        )

    duplicate_considered_lock = copy.deepcopy(ranking)
    duplicate_considered_lock["considered_verdict_ids"][-1] = (
        duplicate_considered_lock["considered_verdict_ids"][0]
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", duplicate_considered_lock
        )

    too_few_considered_locks = copy.deepcopy(ranking)
    too_few_considered_locks["considered_verdict_ids"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", too_few_considered_locks
        )

    missing_option_kind = copy.deepcopy(ranking)
    missing_option_kind["options"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", missing_option_kind
        )

    coupled_to_verdict_kind = copy.deepcopy(ranking)
    coupled_to_verdict_kind["options"][0]["verdict_kind"] = "authorization"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", coupled_to_verdict_kind
        )

    missing_authorization_lock = copy.deepcopy(ranking)
    del missing_authorization_lock["options"][0]["authorization_verdict_id"]
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", missing_authorization_lock
        )

    authorized_without_lock = copy.deepcopy(ranking)
    authorized_without_lock["options"][0]["authorization_verdict_id"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", authorized_without_lock
        )

    unauthorized = copy.deepcopy(ranking)
    unauthorized["options"][0]["authorized"] = False
    unauthorized["options"][0]["authorization_verdict_id"] = None
    runtime.validate_instance("ultra-action-ranking.schema.json", unauthorized)

    unauthorized_with_lock = copy.deepcopy(unauthorized)
    unauthorized_with_lock["options"][0]["authorization_verdict_id"] = (
        "VERDICT-AUTHORIZATION"
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-action-ranking.schema.json", unauthorized_with_lock
        )


def test_forecast_artifact_is_frozen_and_contains_no_resolution_records() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(minimal_instances()["ultra-forecast-ledger.schema.json"])
    runtime.validate_instance("ultra-forecast-ledger.schema.json", ledger)

    for field in (
        "evidence_ledger_artifact_sha256",
        "recursive_lineage_artifact_sha256",
        "verdict_artifact_sha256",
    ):
        broken = copy.deepcopy(ledger)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-forecast-ledger.schema.json", broken)

    mutable = copy.deepcopy(ledger)
    mutable["resolutions"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-forecast-ledger.schema.json", mutable)

    rewritten_status = copy.deepcopy(ledger)
    rewritten_status["forecasts"][0]["status"] = "resolved"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-ledger.schema.json", rewritten_status
        )


def test_forecast_requires_executable_lock_indicator_window_and_predicate() -> None:
    runtime = load_runtime()
    ledger = copy.deepcopy(minimal_instances()["ultra-forecast-ledger.schema.json"])
    runtime.validate_instance("ultra-forecast-ledger.schema.json", ledger)

    for field in (
        "prediction_verdict_id",
        "indicator_id",
        "window_start",
        "window_end",
        "resolution_predicate",
    ):
        broken = copy.deepcopy(ledger)
        del broken["forecasts"][0][field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-forecast-ledger.schema.json", broken)

    for field in (
        "operator",
        "baseline_value",
        "target_value",
        "tolerance",
    ):
        broken = copy.deepcopy(ledger)
        del broken["forecasts"][0]["resolution_predicate"][field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-forecast-ledger.schema.json", broken)

    open_predicate = copy.deepcopy(ledger)
    open_predicate["forecasts"][0]["resolution_predicate"]["caller_note"] = (
        "This must not become executable authority."
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-forecast-ledger.schema.json", open_predicate)

    branch_dependent = copy.deepcopy(ledger)
    branch_dependent["forecasts"][0]["direction"] = "branch-dependent"
    branch_dependent["forecasts"][0]["resolution_predicate"] = {
        "operator": "branch-equals",
        "baseline_value": None,
        "target_value": "BRANCH-MAIN",
        "tolerance": None,
    }
    runtime.validate_instance("ultra-forecast-ledger.schema.json", branch_dependent)

    branch_with_numeric_target = copy.deepcopy(branch_dependent)
    branch_with_numeric_target["forecasts"][0]["resolution_predicate"][
        "target_value"
    ] = 1
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-ledger.schema.json", branch_with_numeric_target
        )

    numeric_with_branch_operator = copy.deepcopy(ledger)
    numeric_with_branch_operator["forecasts"][0]["resolution_predicate"][
        "operator"
    ] = "branch-equals"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-ledger.schema.json", numeric_with_branch_operator
        )

    numeric_with_null_tolerance = copy.deepcopy(ledger)
    numeric_with_null_tolerance["forecasts"][0]["resolution_predicate"][
        "tolerance"
    ] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-ledger.schema.json", numeric_with_null_tolerance
        )


def test_forecast_probability_requires_complete_admissible_calibration() -> None:
    runtime = load_runtime()
    calibrated = copy.deepcopy(
        minimal_instances()["ultra-forecast-ledger.schema.json"]
    )
    forecast = calibrated["forecasts"][0]
    forecast.update(
        probability=0.73,
        reference_class="Comparable reversible team probes",
        calibration_basis="Frozen historical calibration set CALIBRATION-1",
        probability_admissible=True,
    )
    runtime.validate_instance("ultra-forecast-ledger.schema.json", calibrated)

    for field in (
        "reference_class",
        "calibration_basis",
        "probability_admissible",
    ):
        incomplete = copy.deepcopy(calibrated)
        del incomplete["forecasts"][0][field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-forecast-ledger.schema.json", incomplete)

    inadmissible = copy.deepcopy(calibrated)
    inadmissible["forecasts"][0]["probability_admissible"] = False
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-forecast-ledger.schema.json", inadmissible)


def test_forecast_resolution_is_a_separate_later_u9_event_with_bounded_brier() -> None:
    runtime = load_runtime()
    resolution = copy.deepcopy(
        minimal_instances()["ultra-forecast-resolution-event.schema.json"]
    )
    runtime.validate_instance("ultra-forecast-resolution-event.schema.json", resolution)

    for field in (
        "forecast_ledger_artifact_sha256",
        "forecast_id",
        "indicator_id",
        "original_forecast_record_sha256",
        "resolution_time",
        "observation_time",
        "indicator_resolved",
        "direction_correct",
        "time_window_covered",
        "outcome",
        "observed_value",
    ):
        broken = copy.deepcopy(resolution)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance(
                "ultra-forecast-resolution-event.schema.json", broken
            )

    scored = copy.deepcopy(resolution)
    scored["original_probability_admissible"] = True
    scored["brier_inputs"] = {"probability": 0.73, "binary_outcome": 1}
    scored["brier_score"] = 0.0729
    runtime.validate_instance("ultra-forecast-resolution-event.schema.json", scored)

    wrong_binary_outcome = copy.deepcopy(scored)
    wrong_binary_outcome["brier_inputs"]["binary_outcome"] = 0
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json", wrong_binary_outcome
        )

    forbidden_score = copy.deepcopy(scored)
    forbidden_score["original_probability_admissible"] = False
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json", forbidden_score
        )

    partial_score = copy.deepcopy(scored)
    partial_score["brier_score"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json", partial_score
        )

    partial = copy.deepcopy(scored)
    partial["outcome"] = "partial"
    partial["time_window_covered"] = False
    partial["brier_inputs"]["binary_outcome"] = 0
    partial["brier_score"] = 0.5329
    runtime.validate_instance("ultra-forecast-resolution-event.schema.json", partial)

    partial_inside_window = copy.deepcopy(partial)
    partial_inside_window["time_window_covered"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json", partial_inside_window
        )

    incorrect = copy.deepcopy(partial)
    incorrect["outcome"] = "incorrect"
    incorrect["direction_correct"] = False
    runtime.validate_instance("ultra-forecast-resolution-event.schema.json", incorrect)

    incorrect_with_correct_direction = copy.deepcopy(incorrect)
    incorrect_with_correct_direction["direction_correct"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json",
            incorrect_with_correct_direction,
        )

    unresolved = copy.deepcopy(resolution)
    unresolved["indicator_resolved"] = False
    unresolved["direction_correct"] = None
    unresolved["observed_value"] = None
    unresolved["outcome"] = "indeterminate"
    runtime.validate_instance("ultra-forecast-resolution-event.schema.json", unresolved)

    unresolved_with_observation = copy.deepcopy(unresolved)
    unresolved_with_observation["observed_value"] = 12
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json", unresolved_with_observation
        )

    resolved_without_observation = copy.deepcopy(resolution)
    resolved_without_observation["observed_value"] = None
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-forecast-resolution-event.schema.json", resolved_without_observation
        )

    indeterminate_admissible_original = copy.deepcopy(unresolved)
    indeterminate_admissible_original["original_probability_admissible"] = True
    runtime.validate_instance(
        "ultra-forecast-resolution-event.schema.json",
        indeterminate_admissible_original,
    )


def test_framework_gap_is_u10_only_true_isolated_and_bound_to_current_run() -> None:
    runtime = load_runtime()
    gap = copy.deepcopy(minimal_instances()["ultra-framework-gap-ledger.schema.json"])
    runtime.validate_instance("ultra-framework-gap-ledger.schema.json", gap)

    authority_fields = (
        "evidence_ledger_artifact_sha256",
        "claim_mechanism_graph_artifact_sha256",
        "recursive_lineage_artifact_sha256",
        "order_evaluation_artifact_sha256",
        "red_team_report_artifact_sha256",
        "verdict_artifact_sha256",
        "action_ranking_artifact_sha256",
        "forecast_ledger_artifact_sha256",
    )
    assert len({gap[field] for field in authority_fields}) == len(authority_fields)
    for field in authority_fields:
        broken = copy.deepcopy(gap)
        del broken[field]
        with pytest.raises(ValidationError):
            runtime.validate_instance("ultra-framework-gap-ledger.schema.json", broken)

    wrong_phase = copy.deepcopy(gap)
    wrong_phase["phase_id"] = "U9"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-framework-gap-ledger.schema.json", wrong_phase)

    captured = copy.deepcopy(gap)
    captured["isolated_from_current_reasoning"] = False
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-framework-gap-ledger.schema.json", captured)


def test_framework_gap_ids_have_no_u6_or_u9_reasoning_slots() -> None:
    runtime = load_runtime()
    fixtures = minimal_instances()

    graph = copy.deepcopy(fixtures["ultra-claim-mechanism-graph.schema.json"])
    graph["mechanisms"][0]["framework_gap_candidate_ids"] = ["GAP-1"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-claim-mechanism-graph.schema.json", graph)

    verdict = copy.deepcopy(fixtures["ultra-verdict.schema.json"])
    verdict["main_verdict"]["framework_gap_reason_ids"] = ["GAP-1"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-verdict.schema.json", verdict)

    ranking = copy.deepcopy(fixtures["ultra-action-ranking.schema.json"])
    ranking["options"][0]["framework_gap_authorization_ids"] = ["GAP-1"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-action-ranking.schema.json", ranking)


def test_w5_legacy_generic_reference_fields_are_rejected() -> None:
    runtime = load_runtime()
    fixtures = minimal_instances()
    mutations = (
        ("ultra-claim-mechanism-graph.schema.json", ("edges", 0), "from_id"),
        ("ultra-recursive-lineage.schema.json", ("nodes", 0), "state_sha256"),
        ("ultra-red-team-report.schema.json", ("attacks", 0), "target_ref"),
        ("ultra-verdict.schema.json", ("main_verdict",), "decisive_reason_ids"),
        ("ultra-framework-gap-ledger.schema.json", ("candidates", 0), "current_run_refs"),
    )
    for schema_name, path, field in mutations:
        broken = copy.deepcopy(fixtures[schema_name])
        target: Any = broken
        for part in path:
            target = target[part]
        target[field] = ["MIXED-ROLE-1"] if field.endswith("s") else "MIXED-ROLE-1"
        with pytest.raises(ValidationError):
            runtime.validate_instance(schema_name, broken)


def test_output_plan_freezes_design_titles_partial_path_and_u9_parent() -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    assert tuple(item["title"] for item in plan["sections"]) == OUTPUT_PLAN_SECTION_TITLES
    assert tuple(item["title"] for item in plan["appendices"]) == (
        OUTPUT_PLAN_APPENDIX_TITLES
    )
    runtime.validate_instance("ultra-output-plan.schema.json", plan)

    wrong_title = copy.deepcopy(plan)
    wrong_title["sections"][0]["title"] = "主判断、范围与置信度"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", wrong_title)

    wrong_path = copy.deepcopy(plan)
    wrong_path["article_path"] = "delivery/CrossFrame-Ultra-完整文章.md"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", wrong_path)

    official = copy.deepcopy(plan)
    official["official_filename_allowed"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", official)


def test_output_plan_requires_10_plus_5_and_structured_artifact_dependencies() -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan["sections"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)

    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan["appendices"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)

    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan["required_artifacts"] = ["ultra-verdict.json"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)

    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan["sections"][0]["dependency_hashes"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)


@pytest.mark.parametrize("collection", ("sections", "appendices"))
def test_output_plan_rejects_extra_reader_contract_entry(collection: str) -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan[collection].append(copy.deepcopy(plan[collection][-1]))
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)


@pytest.mark.parametrize("collection", ("sections", "appendices"))
def test_output_plan_rejects_swapped_reader_contract_entries(collection: str) -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan[collection][0], plan[collection][1] = (
        plan[collection][1],
        plan[collection][0],
    )
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)


@pytest.mark.parametrize("collection", ("sections", "appendices"))
def test_output_plan_rejects_wrong_reader_contract_ordinal(collection: str) -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan[collection][0]["ordinal"] += 1
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)


def test_output_plan_freezes_complete_semantic_universe_and_blind_contract() -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan["semantic_universe"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)

    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    plan["blind_recovery_expectations"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)


def test_output_plan_rejects_same_length_duplicate_or_unknown_unit_kind() -> None:
    runtime = load_runtime()
    duplicate_kind = copy.deepcopy(
        minimal_instances()["ultra-output-plan.schema.json"]
    )
    duplicate_kind["semantic_universe"][-1]["unit_kind"] = "claim"
    with pytest.raises(ValidationError):
        runtime.validate_instance(
            "ultra-output-plan.schema.json", duplicate_kind
        )

    unknown_kind = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    unknown_kind["semantic_universe"][0]["unit_kind"] = "unknown-kind"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", unknown_kind)


def test_output_plan_allows_extra_semantic_unit_of_existing_kind() -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    extra = copy.deepcopy(plan["semantic_universe"][0])
    extra["unit_id"] = "UNIT-CLAIM-EXTRA"
    extra["authority_locator"] = "unit:claim-extra"
    plan["semantic_universe"].append(extra)
    runtime.validate_instance("ultra-output-plan.schema.json", plan)


@pytest.mark.parametrize("mutation", ("duplicate", "unknown", "extra"))
def test_output_plan_blind_contract_rejects_set_mutations(mutation: str) -> None:
    runtime = load_runtime()
    plan = copy.deepcopy(minimal_instances()["ultra-output-plan.schema.json"])
    fields = plan["blind_recovery_expectations"]
    if mutation == "duplicate":
        fields[1]["field_id"] = fields[0]["field_id"]
    elif mutation == "unknown":
        fields[0]["field_id"] = "unknown-field"
    else:
        fields.append(copy.deepcopy(fields[-1]))
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-output-plan.schema.json", plan)


def test_semantic_coverage_is_u11_and_allows_honest_incomplete_state() -> None:
    runtime = load_runtime()
    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["phase_id"] = "U10"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)

    incomplete = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    missing = incomplete["mappings"].pop()["unit_id"]
    incomplete["missing_unit_ids"] = [missing]
    incomplete["coverage_percent"] = 92
    incomplete["coverage_complete"] = False
    runtime.validate_instance("ultra-semantic-coverage.schema.json", incomplete)


def test_semantic_coverage_allows_controlled_zero_percent_incomplete_state() -> None:
    runtime = load_runtime()
    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["mappings"] = []
    coverage["missing_unit_ids"] = [
        f"UNIT-{ordinal:02d}"
        for ordinal in range(1, len(SEMANTIC_UNIT_KINDS) + 1)
    ]
    coverage["coverage_percent"] = 0
    coverage["coverage_complete"] = False
    runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)


def test_incomplete_coverage_may_record_mapping_without_source_location() -> None:
    runtime = load_runtime()
    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["mappings"][0]["source_refs"] = []
    coverage["missing_unit_ids"] = ["UNIT-SOURCE-LOCATION-PENDING"]
    coverage["coverage_percent"] = 92
    coverage["coverage_complete"] = False
    runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)


def test_complete_semantic_coverage_requires_all_kinds_100_and_no_missing() -> None:
    runtime = load_runtime()
    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["missing_unit_ids"] = ["UNIT-MISSING"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)

    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["coverage_percent"] = 99
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)

    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["mappings"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)

    coverage = copy.deepcopy(
        minimal_instances()["ultra-semantic-coverage.schema.json"]
    )
    coverage["mappings"][0]["source_refs"] = []
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-semantic-coverage.schema.json", coverage)


def test_article_review_is_u11_mechanical_only_with_exact_contracts() -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    runtime.validate_instance("ultra-article-review.schema.json", review)

    wrong_phase = copy.deepcopy(review)
    wrong_phase["phase_id"] = "U12"
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", wrong_phase)

    missing_field = copy.deepcopy(review)
    missing_field["blind_reader_fields"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", missing_field)

    missing_check = copy.deepcopy(review)
    missing_check["quality_checks"].pop()
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", missing_check)


@pytest.mark.parametrize(
    ("collection", "id_field"),
    (("blind_reader_fields", "field_id"), ("quality_checks", "check_id")),
)
@pytest.mark.parametrize("mutation", ("duplicate", "unknown", "extra"))
def test_article_review_exact_sets_reject_duplicate_unknown_and_extra(
    collection: str, id_field: str, mutation: str
) -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    records = review[collection]
    if mutation == "duplicate":
        records[1][id_field] = records[0][id_field]
    elif mutation == "unknown":
        records[0][id_field] = "unknown-contract-id"
    else:
        records.append(copy.deepcopy(records[-1]))
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", review)


def test_article_review_records_mechanical_failure_without_fabricated_excerpt() -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    review["blind_reader_fields"][0]["recovered"] = False
    review["blind_reader_fields"][0]["excerpt"] = None
    review["quality_checks"][0]["status"] = "fail"
    review["external_dependencies"] = ["outside-report.json"]
    review["overall_status"] = "mechanical-fail"
    runtime.validate_instance("ultra-article-review.schema.json", review)

    fabricated = copy.deepcopy(review)
    fabricated["blind_reader_fields"][0]["excerpt"] = "Invented recovery prose."
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", fabricated)


@pytest.mark.parametrize(
    "failed_condition", ("blind-recovery", "quality-check", "dependency")
)
def test_article_review_complete_rejects_each_single_failed_condition(
    failed_condition: str,
) -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    if failed_condition == "blind-recovery":
        review["blind_reader_fields"][0]["recovered"] = False
        review["blind_reader_fields"][0]["excerpt"] = None
    elif failed_condition == "quality-check":
        review["quality_checks"][0]["status"] = "fail"
    else:
        review["external_dependencies"] = ["outside-report.json"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", review)


@pytest.mark.parametrize(
    "failed_condition", ("blind-recovery", "quality-check", "dependency")
)
def test_article_review_fail_accepts_each_single_failed_condition(
    failed_condition: str,
) -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    if failed_condition == "blind-recovery":
        review["blind_reader_fields"][0]["recovered"] = False
        review["blind_reader_fields"][0]["excerpt"] = None
    elif failed_condition == "quality-check":
        review["quality_checks"][0]["status"] = "fail"
    else:
        review["external_dependencies"] = ["outside-report.json"]
    review["overall_status"] = "mechanical-fail"
    runtime.validate_instance("ultra-article-review.schema.json", review)


def test_article_review_completion_requires_no_dependencies_and_later_u12() -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    review["external_dependencies"] = ["outside-report.json"]
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", review)

    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    review["official_filename_allowed"] = True
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", review)

    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    review["needs_u12_validation"] = False
    with pytest.raises(ValidationError):
        runtime.validate_instance("ultra-article-review.schema.json", review)


def test_article_review_has_no_prose_length_cap() -> None:
    runtime = load_runtime()
    review = copy.deepcopy(minimal_instances()["ultra-article-review.schema.json"])
    review["blind_reader_fields"][0]["excerpt"] = "evidence " * 5000
    runtime.validate_instance("ultra-article-review.schema.json", review)


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
        (("version_binding", "artifact_schema_version"), 1),
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
