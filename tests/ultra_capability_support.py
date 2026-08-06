from __future__ import annotations

import copy
from collections.abc import Mapping
import hashlib
import json


def default_capability_requirements() -> dict[str, str]:
    return {
        "filesystem": "required",
        "docx_parser": "not-applicable",
        "network": "required",
        "retrieval": "required",
        "validators": "required",
        "subagents": "not-applicable",
        "model_context": "required",
    }


def default_measured_availability() -> dict[str, str]:
    return {
        "filesystem": "available",
        "docx_parser": "unavailable",
        "network": "available",
        "retrieval": "available",
        "validators": "available",
        "subagents": "unavailable",
        "model_context": "available",
    }


def capability_attestation_for_contract(
    *,
    run_id: str,
    version_binding: Mapping[str, object],
    contract: Mapping[str, object],
    generated_at: str,
    measured_availability: Mapping[str, str] | None = None,
):
    from ultra_runtime.foundation import validate_host_capability_attestation
    from ultra_runtime.schemas import compute_artifact_content_sha256

    document = {
        "schema_id": "crossframe.ultra.v82.host-capability-attestation",
        "schema_version": 1,
        "run_id": run_id,
        "version_binding": copy.deepcopy(dict(version_binding)),
        "generated_at": generated_at,
        "phase_id": "U0",
        "request_sha256": contract["request_sha256"],
        "action_sha256": "a" * 64,
        "receipt_sha256": "b" * 64,
        "analysis_kind": contract["analysis_kind"],
        "run_mode": contract["run_mode"],
        "requirements": copy.deepcopy(contract["capabilities"]),
        "measured_availability": copy.deepcopy(
            dict(measured_availability or default_measured_availability())
        ),
        "providers": [
            {
                "provider_id": "test-host",
                "provider_kind": "runtime",
                "version": "1.0.0",
            }
        ],
        "tools": [
            {
                "tool_id": "local-filesystem",
                "provider_id": "test-host",
                "version": "1.0.0",
            }
        ],
        "sensitivity": contract["sensitivity"],
        "retention": contract["retention"],
        "outbound_permission": contract["outbound_permission"],
        "evidence_cutoff": contract["evidence_cutoff"],
        "resource_limits": copy.deepcopy(contract["resource_limits"]),
        "measured_at": generated_at,
        "proof_grade": "host-measured",
        "content_sha256": "0" * 64,
    }
    document["content_sha256"] = compute_artifact_content_sha256(document)
    return validate_host_capability_attestation(document)


def accept_pending_capability_result(
    layout,
    *,
    completed_at: str,
    network: str = "unavailable",
):
    from ultra_runtime import host_handshake, jsonio

    action = host_handshake.load_pending_action(layout)
    if action is None:
        raise AssertionError("test run has no pending host capability action")
    result = {
        "measured_availability": {
            "filesystem": "available",
            "docx_parser": "unavailable",
            "network": network,
            "retrieval": network,
            "validators": "available",
            "subagents": "unavailable",
            "model_context": "available",
        },
        "providers": [
            {
                "provider_id": "test-host",
                "provider_kind": "runtime",
                "version": "1.0.0",
            }
        ],
        "tools": [
            {
                "tool_id": "local-filesystem",
                "provider_id": "test-host",
                "version": "1.0.0",
            }
        ],
        "measured_at": completed_at,
        "proof_grade": "host-measured",
    }
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": action.document["version_binding"],
        "phase_id": action.document["phase_id"],
        "action_kind": action.document["action_kind"],
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "provider": {
            "provider_id": "test-host",
            "provider_kind": "runtime",
            "version": "1.0.0",
        },
        "tool": {
            "tool_id": "local-filesystem",
            "provider_id": "test-host",
            "version": "1.0.0",
        },
        "execution_id": "test-host-capability",
        "execution_status": "complete",
        "attempts": [
            {"attempt": 1, "status": "success", "error": None},
        ],
        "completed_at": completed_at,
    }
    encoded = (
        json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    receipt["receipt_sha256"] = hashlib.sha256(encoded).hexdigest()
    return host_handshake.accept_host_result(
        layout,
        action=action,
        receipt=receipt,
    )
