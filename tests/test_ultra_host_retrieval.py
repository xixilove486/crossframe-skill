from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

from tests.pytest_import_guard import pytest
from tests import test_ultra_retrieval_privacy as privacy_support


ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-08-05T19:00:00Z"
NOW = datetime(2026, 8, 5, 19, 0, tzinfo=timezone.utc)
RETRIEVED_CONTENT = "The dated policy notice reports the current bounded rule."


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


@pytest.fixture(scope="module")
def sealed_u1_context(tmp_path_factory):
    """Build an isolated sealed-U1 test authority."""

    return privacy_support.retrieval_authority_context.__wrapped__(tmp_path_factory)


@pytest.fixture
def fresh_u1(sealed_u1_context):
    from ultra_runtime import foundation, jsonio

    layout = sealed_u1_context["run_layout"]
    shutil.rmtree(layout.recovery_dir, ignore_errors=True)
    shutil.rmtree(layout.input_dir, ignore_errors=True)
    request_bytes = (ROOT / "AGENTS.md").read_bytes()
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    jsonio.atomic_write_bytes(layout.input_dir / "AGENTS.md", request_bytes)
    jsonio.atomic_write_bytes(layout.input_dir / "request.bin", request_bytes)
    jsonio.atomic_write_json(
        layout.input_dir / "request-metadata.json",
        {"request_sha256": request_sha256, "request_size": len(request_bytes)},
    )
    foundation.seal_input_inventory(
        layout,
        request_sha256=request_sha256,
        material_files=(),
        now=NOW,
        request_bytes=request_bytes,
    )
    ledger_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    ledger_path.unlink(missing_ok=True)
    store = privacy_support._fresh_phase_store()
    value = SimpleNamespace(
        layout=layout,
        phase_store=store,
        repo=ROOT,
        now=NOW,
        later=NOW + timedelta(seconds=5),
        claim=(
            "Assess the current policy evidence for Alice Example at "
            "alice@example.com from /private/report.pdf"
        ),
    )
    yield value
    shutil.rmtree(layout.recovery_dir, ignore_errors=True)
    ledger_path.unlink(missing_ok=True)


def _accept_retrieval_result(
    fresh_u1,
    action,
    *,
    mutate_result=None,
    mutate_receipt=None,
    attempts=None,
):
    from ultra_runtime import host_handshake, jsonio

    query = action.document["payload"]["queries"][0]
    content = RETRIEVED_CONTENT
    result = {
        "schema_id": "crossframe.ultra.v82.host-retrieval-result",
        "schema_version": 1,
        "action_sha256": action.action_sha256,
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
        "execution_id": "host-retrieval-exec-1",
        "queries": [
            {
                "query_sha256": query["query_sha256"],
                "status": "complete",
            }
        ],
        "sources": [
            {
                "source_id": "SOURCE-PRIMARY-1",
                "query_sha256": query["query_sha256"],
                "url": "https://example.test/policy?lang=en&page=1",
                "content": content,
                "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "event_date": "2026-08-01",
                "publication_date": "2026-08-02",
                "interest": "Publisher states no relevant financial interest.",
                "upstream_lineage": ["PRIMARY-NOTICE-1"],
                "supported_claim": "The notice supports the bounded current-policy claim.",
                "cannot_prove": "It cannot prove universal policy effectiveness.",
            }
        ],
        "entries": [
            {
                "query_id": "QUERY-1",
                "query_sha256": query["query_sha256"],
                "direction": "support",
                "result_summary": "One primary notice was returned.",
                "source_refs": ["SOURCE-PRIMARY-1"],
                "stop_reason": "bounded-result-recorded",
            }
        ],
    }
    if mutate_result is not None:
        mutate_result(result)
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": copy.deepcopy(action.document["version_binding"]),
        "phase_id": action.document["phase_id"],
        "action_kind": action.document["action_kind"],
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": "host-retrieval-exec-1",
        "completed_at": "2026-08-05T19:00:02Z",
        "provider": copy.deepcopy(result["provider"]),
        "tool": copy.deepcopy(result["tool"]),
        "execution_status": "complete",
        "attempts": copy.deepcopy(
            attempts
            or [{"attempt": 1, "status": "success", "error": None}]
        ),
    }
    if mutate_receipt is not None:
        mutate_receipt(receipt)
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt)).hexdigest()
    return host_handshake.accept_host_result(
        fresh_u1.layout,
        action=action,
        receipt=receipt,
    )


def test_real_world_claim_issues_redacted_retrieval_action(fresh_u1) -> None:
    from ultra_runtime import retrieval

    action = retrieval.issue_retrieval_action(
        fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        generated_at=STAMP,
    )

    assert action.document["action_kind"] == "retrieval"
    assert action.document["payload"]["decision"]["status"] == "required"
    action_text = _canonical(action.document).decode("utf-8")
    assert "alice@example.com" not in action_text
    assert "/private/report.pdf" not in action_text
    assert action.document["payload"]["queries"]


def test_foundation_u2_boundary_issues_the_pending_retrieval_action(fresh_u1) -> None:
    from ultra_runtime import foundation

    progress = foundation.advance_u2(
        fresh_u1.layout,
        phase_store=fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        now=fresh_u1.now,
    )

    assert progress.outcome == "awaiting-host-action"
    assert progress.phase_store is fresh_u1.phase_store
    assert progress.pending_action is not None
    assert progress.pending_action.document["action_kind"] == "retrieval"
    assert progress.completed_phase is None


def test_open_world_materials_do_not_turn_off_required_retrieval(fresh_u1) -> None:
    from ultra_runtime import foundation

    progress = foundation.advance_u2(
        fresh_u1.layout,
        phase_store=fresh_u1.phase_store,
        analysis_kind="open-world",
        claim=fresh_u1.claim,
        trigger_kinds=("real-world",),
        material_inventory=tuple(privacy_support._locked_inputs()),
        material_universe_sha256=privacy_support.INPUT_SNAPSHOT_SHA256,
        now=fresh_u1.now,
    )

    assert progress.outcome == "awaiting-host-action"
    assert progress.pending_action is not None
    assert progress.pending_action.document["payload"]["decision"]["status"] == "required"


def test_closed_input_material_authority_completes_u2_without_dispatch(
    sealed_u1_context,
) -> None:
    from ultra_runtime import foundation, recovery

    layout = sealed_u1_context["run_layout"]
    shutil.rmtree(layout.recovery_dir, ignore_errors=True)
    layout.input_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "AGENTS.md", layout.input_dir / "AGENTS.md")
    ledger_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    ledger_path.unlink(missing_ok=True)
    store = privacy_support._fresh_phase_store(analysis_kind="closed-input")

    progress = foundation.advance_u2(
        layout,
        phase_store=store,
        analysis_kind="closed-input",
        claim="Use only the supplied sealed material.",
        trigger_kinds=(),
        material_inventory=tuple(privacy_support._locked_inputs()),
        material_universe_sha256=privacy_support.INPUT_SNAPSHOT_SHA256,
        now=NOW,
    )

    assert progress.outcome == "advanced"
    assert progress.completed_phase == "U2"
    assert not (layout.recovery_dir / "pending-action.json").exists()
    ledger = json.loads(ledger_path.read_text("utf-8"))
    assert ledger["retrieval_status"] == "not-applicable"
    assert ledger["authorization_sha256"] is None
    assert any(
        item["phase_id"] == "U2" for item in recovery.load_checkpoints(layout)
    )


def test_foundation_u2_admits_the_accepted_result_and_completes_u2(fresh_u1) -> None:
    from ultra_runtime import foundation, recovery

    first = foundation.advance_u2(
        fresh_u1.layout,
        phase_store=fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        now=fresh_u1.now,
    )
    assert first.pending_action is not None
    _accept_retrieval_result(fresh_u1, first.pending_action)
    first.pending_action.result_path.write_bytes(_canonical({"reused": True}))

    progress = foundation.advance_u2(
        fresh_u1.layout,
        phase_store=fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        now=fresh_u1.later,
    )

    assert progress.outcome == "advanced"
    assert progress.completed_phase == "U2"
    assert progress.pending_action is None
    assert progress.phase_store.current_phase == "U2"
    ledger_path = (
        fresh_u1.layout.artifacts_dir
        / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    ledger = json.loads(ledger_path.read_text("utf-8"))
    assert ledger["retrieval_status"] == "required-complete"
    checkpoint = next(
        item
        for item in recovery.load_checkpoints(fresh_u1.layout)
        if item["phase_id"] == "U2"
    )
    assert [item["path"] for item in checkpoint["artifact_hashes"]] == [
        "artifacts/U00-U03-evidence/U02-retrieval-ledger.json"
    ]
    assert checkpoint["artifact_hashes"][0]["sha256"] == hashlib.sha256(
        ledger_path.read_bytes()
    ).hexdigest()


def _advance_fresh_u1_to_u2(fresh_u1):
    from ultra_runtime import foundation

    first = foundation.advance_u2(
        fresh_u1.layout,
        phase_store=fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        now=fresh_u1.now,
    )
    assert first.pending_action is not None
    _accept_retrieval_result(fresh_u1, first.pending_action)
    completed = foundation.advance_u2(
        fresh_u1.layout,
        phase_store=fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        now=fresh_u1.later,
    )
    assert completed.completed_phase == "U2"
    return completed.phase_store


def _rewrite_admitted_source_projection(fresh_u1, content: str) -> None:
    admitted_path = (
        fresh_u1.layout.recovery_dir
        / "u2-authority/admitted-host-result.json"
    )
    admitted = json.loads(admitted_path.read_text("utf-8"))
    external = admitted["sources"][0]["external_content"]
    external["content"] = content
    external["content_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    admitted["content_sha256"] = hashlib.sha256(
        _canonical(
            {
                key: value
                for key, value in admitted.items()
                if key != "content_sha256"
            }
        )
    ).hexdigest()
    admitted_path.write_bytes(_canonical(admitted))


def test_u3_rejects_rehashed_tampered_u2_source_projection(fresh_u1) -> None:
    from ultra_runtime import foundation

    phase_store = _advance_fresh_u1_to_u2(fresh_u1)
    _rewrite_admitted_source_projection(
        fresh_u1,
        "Forged source content that was never accepted by the host handshake.",
    )

    with pytest.raises(
        foundation.FoundationInputError,
        match="projection|accepted|authority",
    ):
        foundation._advance_u3(
            fresh_u1.layout,
            phase_store=phase_store,
            profile=foundation.RequestProfile(
                "open-world",
                fresh_u1.claim,
                (),
                None,
            ),
            now=fresh_u1.later + timedelta(seconds=1),
        )


def test_fresh_validation_rejects_rehashed_tampered_u2_source_projection(
    fresh_u1,
) -> None:
    from ultra_runtime import validation

    phase_store = _advance_fresh_u1_to_u2(fresh_u1)
    ledger_path = (
        fresh_u1.layout.artifacts_dir
        / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    _rewrite_admitted_source_projection(
        fresh_u1,
        "Forged source content that was never accepted by the host handshake.",
    )

    with pytest.raises(
        validation._AuthorityDAGError,
        match="projection|accepted|authority",
    ):
        validation._validate_u2_source_projection_authority(
            fresh_u1.layout,
            u2_refs={
                "artifacts/U00-U03-evidence/U02-retrieval-ledger.json": (
                    hashlib.sha256(ledger_path.read_bytes()).hexdigest()
                )
            },
            request_sha256=phase_store.run_contract["request_sha256"],
        )


def _accept_evidence_authoring_result(
    fresh_u1,
    action,
    *,
    mutate_result=None,
) -> None:
    from ultra_runtime import host_handshake, jsonio

    content_sha256 = hashlib.sha256(RETRIEVED_CONTENT.encode("utf-8")).hexdigest()
    result = {
        "candidate_entries": [
            {
                "evidence_id": "EV-U3-HOST-1",
                "identity": "reported",
                "statement": RETRIEVED_CONTENT,
                "source_refs": ["SOURCE-PRIMARY-1"],
                "observed_at": None,
                "confidence": "medium",
                "event_date": "2026-08-01",
                "publication_date": "2026-08-02",
                "interest": "Publisher states no relevant financial interest.",
                "upstream_lineage": ["PRIMARY-NOTICE-1"],
                "supported_claim": "The notice supports the bounded current-policy claim.",
                "cannot_prove": "It cannot prove universal policy effectiveness.",
                "attribution": {
                    "origin_kind": "source",
                    "origin_ref": "SOURCE-PRIMARY-1",
                    "content_sha256": content_sha256,
                    "span": None,
                    "proof_grade": "host-attested",
                },
            }
        ],
        "verified_subagent_candidates": [],
    }
    if mutate_result is not None:
        mutate_result(result)
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": copy.deepcopy(action.document["version_binding"]),
        "phase_id": "U3",
        "action_kind": "evidence-authoring",
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": "host-evidence-authoring-1",
        "completed_at": "2026-08-05T19:00:07Z",
        "provider": {
            "provider_id": "test-host",
            "provider_kind": "runtime",
            "version": "1.0.0",
        },
        "tool": {
            "tool_id": "evidence-authoring",
            "provider_id": "test-host",
            "version": "1.0.0",
        },
        "execution_status": "complete",
        "attempts": [{"attempt": 1, "status": "success", "error": None}],
    }
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt)).hexdigest()
    host_handshake.accept_host_result(
        fresh_u1.layout,
        action=action,
        receipt=receipt,
    )


def test_invalid_evidence_authoring_result_is_rejected_before_pending_is_consumed(
    fresh_u1,
) -> None:
    from ultra_runtime import foundation, host_handshake

    phase_store = _advance_fresh_u1_to_u2(fresh_u1)
    profile = foundation.RequestProfile("open-world", fresh_u1.claim, (), None)
    progress = foundation._advance_u3(
        fresh_u1.layout,
        phase_store=phase_store,
        profile=profile,
        now=fresh_u1.later + timedelta(seconds=1),
    )
    action = progress.pending_action
    assert action is not None

    def invalidate(result):
        result["candidate_entries"][0]["evidence_id"] = ""

    with pytest.raises(host_handshake.HostHandshakeError):
        _accept_evidence_authoring_result(
            fresh_u1,
            action,
            mutate_result=invalidate,
        )
    assert host_handshake.load_pending_action(fresh_u1.layout) == action
    accepted = (
        fresh_u1.layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json"
    )
    assert not accepted.exists()
    assert len(tuple((accepted.parent / "attempts").glob("*-rejected.json"))) == 1


def test_u3_evidence_authoring_wait_is_u2_bound_and_idempotent(fresh_u1) -> None:
    from ultra_runtime import foundation

    phase_store = _advance_fresh_u1_to_u2(fresh_u1)
    profile = foundation.RequestProfile("open-world", fresh_u1.claim, (), None)
    first = foundation._advance_u3(
        fresh_u1.layout,
        phase_store=phase_store,
        profile=profile,
        now=fresh_u1.later + timedelta(seconds=1),
    )

    assert first.outcome == "awaiting-host-action"
    assert first.pending_action is not None
    assert first.pending_action.document["action_kind"] == "evidence-authoring"
    assert first.pending_action.document["payload"]["u2_event_sha256"] == (
        phase_store.events[-1]["event_sha256"]
    )
    pending_path = fresh_u1.layout.recovery_dir / "pending-action.json"
    pending_bytes = pending_path.read_bytes()
    repeated = foundation._advance_u3(
        fresh_u1.layout,
        phase_store=phase_store,
        profile=profile,
        now=fresh_u1.later + timedelta(seconds=2),
    )
    assert repeated.pending_action == first.pending_action
    assert pending_path.read_bytes() == pending_bytes


def test_u3_persisted_action_without_pending_or_accepted_result_fails_closed(
    fresh_u1,
) -> None:
    from ultra_runtime import foundation

    phase_store = _advance_fresh_u1_to_u2(fresh_u1)
    profile = foundation.RequestProfile("open-world", fresh_u1.claim, (), None)
    waiting = foundation._advance_u3(
        fresh_u1.layout,
        phase_store=phase_store,
        profile=profile,
        now=fresh_u1.later + timedelta(seconds=1),
    )
    assert waiting.pending_action is not None
    (fresh_u1.layout.recovery_dir / "pending-action.json").unlink()

    with pytest.raises(
        foundation.FoundationInputError,
        match="pending|accepted|dispatch",
    ):
        foundation._advance_u3(
            fresh_u1.layout,
            phase_store=phase_store,
            profile=profile,
            now=fresh_u1.later + timedelta(seconds=2),
        )


def test_u3_accepted_evidence_result_completes_and_checkpoints(fresh_u1) -> None:
    from ultra_runtime import foundation, recovery

    phase_store = _advance_fresh_u1_to_u2(fresh_u1)
    profile = foundation.RequestProfile("open-world", fresh_u1.claim, (), None)
    waiting = foundation._advance_u3(
        fresh_u1.layout,
        phase_store=phase_store,
        profile=profile,
        now=fresh_u1.later + timedelta(seconds=1),
    )
    assert waiting.pending_action is not None
    _accept_evidence_authoring_result(fresh_u1, waiting.pending_action)
    waiting.pending_action.result_path.write_bytes(_canonical({"reused": True}))

    completed = foundation._advance_u3(
        fresh_u1.layout,
        phase_store=phase_store,
        profile=profile,
        now=fresh_u1.later + timedelta(seconds=3),
    )

    assert completed.outcome == "advanced"
    assert completed.completed_phase == "U3"
    assert phase_store.current_phase == "U3"
    assert not (fresh_u1.layout.recovery_dir / "pending-action.json").exists()
    evidence_path = (
        fresh_u1.layout.artifacts_dir
        / "U00-U03-evidence/U03-evidence-ledger.json"
    )
    artifact = json.loads(evidence_path.read_text("utf-8"))
    assert artifact["entries"][0]["identity"] == "reported"
    assert any(
        item["phase_id"] == "U3"
        for item in recovery.load_checkpoints(fresh_u1.layout)
    )


@pytest.mark.parametrize(
    ("network", "outbound_permission", "expected_block_class"),
    (
        ("unavailable", "deidentified-only", "network-unavailable"),
        ("available", "denied", "outbound-denied"),
    ),
)
def test_blocked_u2_persists_zero_dispatch_ledger(
    sealed_u1_context,
    network: str,
    outbound_permission: str,
    expected_block_class: str,
) -> None:
    from ultra_runtime import foundation

    layout = sealed_u1_context["run_layout"]
    shutil.rmtree(layout.recovery_dir, ignore_errors=True)
    ledger_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    ledger_path.unlink(missing_ok=True)
    store = privacy_support._fresh_phase_store(network, outbound_permission)

    progress = foundation.advance_u2(
        layout,
        phase_store=store,
        claim="A current real-world policy claim.",
        trigger_kinds=("real-world",),
        now=NOW,
    )

    assert progress.outcome == "blocked"
    assert not (layout.recovery_dir / "pending-action.json").exists()
    assert not (
        layout.recovery_dir / "u2-authority/retrieval-action.json"
    ).exists()
    ledger = json.loads(ledger_path.read_text("utf-8"))
    assert ledger["retrieval_status"] == "required-blocked"
    assert ledger["block_result"]["block_class"] == expected_block_class
    assert ledger["query_count"] == 0
    assert ledger["queries"] == []
    assert ledger["sources"] == []
    assert store.current_phase == "U1"


def test_unknown_acl_blocks_u2_before_any_host_dispatch(
    sealed_u1_context,
    monkeypatch,
) -> None:
    from ultra_runtime import foundation, source_integrity

    layout = sealed_u1_context["run_layout"]
    shutil.rmtree(layout.recovery_dir, ignore_errors=True)
    ledger_path = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    ledger_path.unlink(missing_ok=True)
    monkeypatch.delattr(source_integrity.os, "getuid", raising=False)
    monkeypatch.setattr(
        source_integrity,
        "_windows_current_user_owns",
        lambda _path: None,
    )
    monkeypatch.setattr(source_integrity.os, "access", lambda _path, _mode: True)
    store = privacy_support._phase_store(
        authority_variant="host-retrieval-unknown-acl"
    )
    assert store.u1_acl_status == "unknown"

    progress = foundation.advance_u2(
        layout,
        phase_store=store,
        claim="A current real-world policy claim.",
        trigger_kinds=("real-world",),
        now=NOW,
    )

    assert progress.outcome == "blocked"
    assert not (layout.recovery_dir / "pending-action.json").exists()
    assert not (
        layout.recovery_dir / "u2-authority/retrieval-action.json"
    ).exists()
    ledger = json.loads(ledger_path.read_text("utf-8"))
    assert ledger["retrieval_status"] == "required-blocked"
    assert ledger["block_result"]["block_class"] == "outbound-denied"
    assert ledger["query_count"] == 0
    assert ledger["sources"] == []


def test_host_result_becomes_required_complete_ledger(fresh_u1) -> None:
    from ultra_runtime import retrieval

    action = retrieval.issue_retrieval_action(
        fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        generated_at=STAMP,
    )
    receipt = _accept_retrieval_result(fresh_u1, action)
    decision = retrieval.assess_retrieval_eligibility(
        fresh_u1.claim,
        phase_store=fresh_u1.phase_store,
        trigger_kinds=("real-world", "current-fact"),
    )
    authorization = retrieval.gate_retrieval(
        decision,
        phase_store=fresh_u1.phase_store,
    )

    ledger = retrieval.admit_host_retrieval_result(
        receipt,
        phase_store=fresh_u1.phase_store,
        decision=decision,
        authorization=authorization,
    )

    assert ledger["retrieval_status"] == "required-complete"
    assert ledger["query_count"] >= 1
    assert ledger["sources"][0]["record"]["url"].startswith("https://")
    assert ledger["sources"][0]["record"]["publication_date"] == "2026-08-02"
    admitted_path = (
        fresh_u1.layout.recovery_dir
        / "u2-authority/admitted-host-result.json"
    )
    admitted = json.loads(admitted_path.read_text("utf-8"))
    external = admitted["sources"][0]["external_content"]
    assert external["trust"] == "untrusted"
    assert external["content_sha256"] == hashlib.sha256(
        external["content"].encode("utf-8")
    ).hexdigest()


def _retrieval_authority(
    fresh_u1,
    *,
    trigger_kinds=("real-world", "current-fact"),
):
    from ultra_runtime import retrieval

    decision = retrieval.assess_retrieval_eligibility(
        fresh_u1.claim,
        phase_store=fresh_u1.phase_store,
        trigger_kinds=trigger_kinds,
    )
    authorization = retrieval.gate_retrieval(
        decision,
        phase_store=fresh_u1.phase_store,
    )
    return decision, authorization


def _mutate_host_result(result: dict[str, object], mutation: str) -> None:
    source = result["sources"][0]
    if mutation == "provider":
        result["provider"]["provider_id"] = "unmeasured-provider"
        result["tool"]["provider_id"] = "unmeasured-provider"
    elif mutation == "tool":
        result["tool"]["tool_id"] = "unmeasured-tool"
    elif mutation == "content-hash":
        source["content_sha256"] = "f" * 64
    elif mutation == "url":
        source["url"] = "file:///private/source"
    elif mutation == "date":
        source["publication_date"] = "2026-08-05T19:00:00Z"
    elif mutation == "interest":
        source["interest"] = ""
    elif mutation == "upstream":
        source["upstream_lineage"] = ["UPSTREAM-1", "UPSTREAM-1"]
    elif mutation == "supported-claim":
        source["supported_claim"] = ""
    elif mutation == "cannot-prove":
        source["cannot_prove"] = ""
    elif mutation == "zero-query":
        result["queries"] = []
    elif mutation == "zero-source":
        result["sources"] = []
        result["entries"] = []
    elif mutation == "not-applicable":
        result["retrieval_status"] = "not-applicable"
    elif mutation == "completed-before-issued":
        pass
    else:  # pragma: no cover - test table is closed below
        raise AssertionError(f"unknown mutation: {mutation}")


@pytest.mark.parametrize(
    "mutation",
    (
        "provider",
        "tool",
        "content-hash",
        "url",
        "date",
        "interest",
        "upstream",
        "supported-claim",
        "cannot-prove",
        "zero-query",
        "zero-source",
        "not-applicable",
        "completed-before-issued",
    ),
)
def test_host_result_requires_real_closed_retrieval_evidence(
    fresh_u1,
    mutation: str,
) -> None:
    from ultra_runtime import host_handshake, retrieval

    action = retrieval.issue_retrieval_action(
        fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world", "current-fact"),
        generated_at=STAMP,
    )

    def mutate(result):
        _mutate_host_result(result, mutation)

    def align_receipt(receipt):
        if mutation == "provider":
            receipt["provider"]["provider_id"] = "unmeasured-provider"
            receipt["tool"]["provider_id"] = "unmeasured-provider"
        elif mutation == "tool":
            receipt["tool"]["tool_id"] = "unmeasured-tool"
        elif mutation == "completed-before-issued":
            receipt["completed_at"] = "2026-08-05T18:59:59Z"

    with pytest.raises(host_handshake.HostHandshakeError):
        _accept_retrieval_result(
            fresh_u1,
            action,
            mutate_result=mutate,
            mutate_receipt=align_receipt,
        )
    assert host_handshake.load_pending_action(fresh_u1.layout) == action
    accepted = (
        fresh_u1.layout.recovery_dir
        / "host-results"
        / action.action_sha256
        / "accepted.json"
    )
    assert not accepted.exists()
    assert len(tuple((accepted.parent / "attempts").glob("*-rejected.json"))) == 1


def test_host_retrieval_receipt_replay_is_rejected(fresh_u1) -> None:
    from ultra_runtime import host_handshake, retrieval

    action = retrieval.issue_retrieval_action(
        fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world",),
        generated_at=STAMP,
    )
    receipt = _accept_retrieval_result(fresh_u1, action)

    with pytest.raises(host_handshake.HostHandshakeError, match="replay|completed"):
        host_handshake.accept_host_result(
            fresh_u1.layout,
            action=action,
            receipt=receipt.document,
        )


def test_host_retrieval_accepts_bounded_retry_then_success(fresh_u1) -> None:
    from ultra_runtime import retrieval

    action = retrieval.issue_retrieval_action(
        fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world",),
        generated_at=STAMP,
    )
    receipt = _accept_retrieval_result(
        fresh_u1,
        action,
        attempts=[
            {"attempt": 1, "status": "timeout", "error": "provider timeout"},
            {"attempt": 2, "status": "success", "error": None},
        ],
    )
    decision, authorization = _retrieval_authority(
        fresh_u1,
        trigger_kinds=("real-world",),
    )

    ledger = retrieval.admit_host_retrieval_result(
        receipt,
        phase_store=fresh_u1.phase_store,
        decision=decision,
        authorization=authorization,
    )

    assert ledger["retrieval_status"] == "required-complete"


def test_host_retrieval_rejects_attempts_beyond_u0_limit(fresh_u1) -> None:
    from ultra_runtime import host_handshake, retrieval

    action = retrieval.issue_retrieval_action(
        fresh_u1.phase_store,
        claim=fresh_u1.claim,
        trigger_kinds=("real-world",),
        generated_at=STAMP,
    )

    with pytest.raises(host_handshake.HostHandshakeError, match="host result|invalid"):
        _accept_retrieval_result(
            fresh_u1,
            action,
            attempts=[
                {"attempt": 1, "status": "timeout", "error": "timeout"},
                {"attempt": 2, "status": "rate-limit", "error": "limited"},
                {"attempt": 3, "status": "timeout", "error": "timeout"},
                {"attempt": 4, "status": "success", "error": None},
            ],
        )


def test_subagent_candidate_without_admitted_source_cannot_enter_u3() -> None:
    from ultra_runtime import host_handshake, retrieval
    from ultra_runtime.schemas import validate_instance

    result = {
        "task_id": "SUBAGENT-TASK-1",
        "redacted_prompt_sha256": "a" * 64,
        "resource_limits": {
            "maximum_candidates": 4,
            "maximum_source_refs_per_candidate": 4,
        },
        "cannot_prove": "Candidates cannot prove the final U3 judgment.",
        "candidates": [
            {
                "candidate_id": "CANDIDATE-ADMITTED",
                "role": "source-discovery",
                "claim": "A source-linked discovery candidate.",
                "source_refs": ["SOURCE-PRIMARY-1"],
                "cannot_prove": "It cannot prove the general claim.",
            },
            {
                "candidate_id": "CANDIDATE-1",
                "role": "counterexample",
                "claim": "A counterexample candidate.",
                "source_refs": ["SOURCE-NOT-ADMITTED"],
                "cannot_prove": "It cannot prove the general claim.",
            },
        ],
    }
    result["content_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    document = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": privacy_support.RUN_ID,
        "version_binding": privacy_support._binding(),
        "phase_id": "U2",
        "action_kind": "subagent",
        "parent_event_sha256": privacy_support.U1_PARENT,
        "request_sha256": privacy_support.REQUEST_SHA256,
        "action_sha256": "d" * 64,
        "result_relative_path": "work/host/U02-subagent-result.json",
        "result_sha256": "e" * 64,
        "execution_id": "subagent-exec-1",
        "completed_at": "2026-08-05T19:00:02Z",
        "provider": {
            "provider_id": "test-host",
            "provider_kind": "model",
            "version": "1.0.0",
        },
        "tool": {
            "tool_id": "test-subagent",
            "provider_id": "test-host",
            "version": "1.0.0",
        },
        "execution_status": "complete",
        "attempts": [
            {"attempt": 1, "status": "success", "error": None},
        ],
        "result": result,
    }
    document["receipt_sha256"] = hashlib.sha256(_canonical(document)).hexdigest()
    validate_instance("ultra-host-result-receipt.schema.json", document)
    receipt = host_handshake.HostResultSeal(
        document,
        document["receipt_sha256"],
        document["action_sha256"],
    )

    assert retrieval.admit_subagent_candidates(
        receipt,
        admitted_source_ids={"SOURCE-PRIMARY-1"},
    ) == (
        {
            "candidate_id": "CANDIDATE-ADMITTED",
            "role": "source-discovery",
            "claim": "A source-linked discovery candidate.",
            "source_refs": ["SOURCE-PRIMARY-1"],
            "cannot_prove": "It cannot prove the general claim.",
        },
    )
