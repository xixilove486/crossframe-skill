from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import importlib
from pathlib import Path
from types import SimpleNamespace
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "crossframe-ultra" / "scripts"
RUN_ID = "20260806T120000Z-101010101010"
NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
DIMENSIONS = (
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


def _module(name: str):
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    importlib.invalidate_caches()
    return importlib.import_module(f"ultra_runtime.{name}")


def _layout(tmp_path: Path, *, suffix: str = ""):
    paths = _module("paths")
    policy = paths.RootPolicy(
        tmp_path / f"production{suffix}",
        tmp_path / f"test{suffix}",
    )
    return paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy), policy


def _authority(**overrides: object) -> dict[str, object]:
    authority: dict[str, object] = {
        "request_sha256": "1" * 64,
        "request_intake_authority_sha256": "2" * 64,
        "u10_parent_event_sha256": "3" * 64,
        "active_generation": 4,
        "article_sha256": "5" * 64,
        "output_plan_artifact_sha256": "6" * 64,
        "coverage_artifact_sha256": "7" * 64,
        "article_review_artifact_sha256": "8" * 64,
        "evidence_ledger_artifact_sha256": "9" * 64,
        "concept_disposition_artifact_sha256": "a" * 64,
        "required_concept_semantic_unit_ids": (
            "SEMANTIC-UNIT-V82-M01",
            "SEMANTIC-UNIT-V82-M02",
        ),
    }
    authority.update(overrides)
    return authority


def _issue(semantic_review, layout, **overrides: object):
    return semantic_review.ensure_semantic_review_action(
        layout,
        **_authority(**overrides),
        now=NOW,
    )


def _dimension_reviews() -> list[dict[str, object]]:
    return [
        {
            "dimension_id": dimension,
            "status": "pass",
            "rationale": f"The article substantively satisfies {dimension}.",
            "article_spans": [f"SPAN-{ordinal:02d}"],
            "authority_refs": [f"AUTHORITY-{ordinal:02d}"],
        }
        for ordinal, dimension in enumerate(DIMENSIONS, start=1)
    ]


def _host_result(action) -> dict[str, object]:
    return {
        "schema_id": "crossframe.ultra.v82.host-semantic-review-result",
        "schema_version": 1,
        "action_sha256": action.action_sha256,
        "reviewed_at": "2026-08-06T12:00:01Z",
        "reviewer": {
            "reviewer_id": "reviewer-semantic-01",
            "host_id": "host-codex-01",
            "provider_id": "provider-openai-01",
            "model": "semantic-review-model",
            "execution_id": "execution-semantic-01",
            "proof_grade": "host-attested",
        },
        "dimension_reviews": _dimension_reviews(),
    }


def _receipt(action, result: dict[str, object]) -> dict[str, object]:
    jsonio = _module("jsonio")
    jsonio.atomic_write_json(action.result_path, result)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": action.document["version_binding"],
        "phase_id": "U11",
        "action_kind": "semantic-review",
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": "execution-semantic-01",
        "completed_at": "2026-08-06T12:00:02Z",
        "provider": {
            "provider_id": "provider-openai-01",
            "provider_kind": "service",
            "version": "2026-08-06",
        },
        "tool": {
            "tool_id": "semantic-reviewer-01",
            "provider_id": "provider-openai-01",
            "version": "1",
        },
        "execution_status": "complete",
        "attempts": [{"attempt": 1, "status": "success", "error": None}],
    }
    receipt["receipt_sha256"] = jsonio.sha256_bytes(
        jsonio.canonical_json_bytes(receipt)
    )
    return receipt


def test_semantic_action_is_persistent_restart_stable_and_stale_closed(
    tmp_path: Path,
) -> None:
    semantic_review = _module("semantic_review")
    layout, _ = _layout(tmp_path)

    action = _issue(semantic_review, layout)
    pending_path = layout.recovery_dir / "pending-action.json"
    authority_path = semantic_review.semantic_review_action_path(layout, 4)
    pending_bytes = pending_path.read_bytes()
    authority_bytes = authority_path.read_bytes()

    restarted = semantic_review.ensure_semantic_review_action(
        layout,
        **_authority(),
        now=NOW + timedelta(minutes=5),
    )

    assert restarted == action
    assert restarted.document["action_kind"] == "semantic-review"
    assert restarted.document["parent_event_sha256"] == "3" * 64
    assert restarted.document["payload"]["active_generation"] == 4
    assert pending_path.read_bytes() == pending_bytes
    assert authority_path.read_bytes() == authority_bytes
    stale_authorities = (
        {"article_sha256": "b" * 64},
        {"output_plan_artifact_sha256": "c" * 64},
        {"coverage_artifact_sha256": "d" * 64},
        {"u10_parent_event_sha256": "e" * 64},
        {"active_generation": 5},
    )
    for overrides in stale_authorities:
        with pytest.raises(
            semantic_review.SemanticReviewError,
            match="article|authority|generation|parent",
        ):
            semantic_review.ensure_semantic_review_action(
                layout,
                **_authority(**overrides),
                now=NOW + timedelta(minutes=6),
            )


def test_semantic_receipt_projects_runtime_envelope_and_replay_fails_closed(
    tmp_path: Path,
) -> None:
    semantic_review = _module("semantic_review")
    host_handshake = _module("host_handshake")
    constants = _module("constants")
    layout, _ = _layout(tmp_path)
    action = _issue(semantic_review, layout)
    result = _host_result(action)
    receipt = _receipt(action, result)

    accepted = host_handshake.accept_host_result(
        layout,
        action=action,
        receipt=receipt,
    )
    artifact = semantic_review.project_semantic_review_artifact(
        action=action,
        accepted_result=accepted,
        host_result=result,
        version_binding=constants.current_version_binding(),
        generated_at="2026-08-06T12:00:03Z",
        deterministic_status="pass",
        adversarial_status="pass",
    )

    assert artifact["schema_id"] == "crossframe.ultra.v82.semantic-review"
    assert artifact["run_id"] == RUN_ID
    assert artifact["phase_id"] == "U11"
    assert artifact["active_generation"] == 4
    assert artifact["host_action_sha256"] == action.action_sha256
    assert artifact["host_receipt_sha256"] == accepted.receipt_sha256
    assert artifact["overall_status"] == "pass"
    assert artifact["publication_allowed"] is True
    with pytest.raises(host_handshake.HostHandshakeError, match="replay|completed"):
        host_handshake.accept_host_result(
            layout,
            action=action,
            receipt=receipt,
        )

    second_layout, _ = _layout(tmp_path, suffix="-forged")
    second = _issue(semantic_review, second_layout)
    forged = _host_result(second)
    forged["publication_allowed"] = True
    with pytest.raises(
        host_handshake.HostHandshakeError,
        match="runtime-owned|unknown|fields",
    ):
        host_handshake.accept_host_result(
            second_layout,
            action=second,
            receipt=_receipt(second, forged),
        )
    assert host_handshake.load_pending_action(second_layout) == second


def test_semantic_wait_keeps_running_releases_lease_and_skips_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semantic_review = _module("semantic_review")
    materialization = _module("materialization")
    foundation = _module("foundation")
    deliverables = _module("deliverables")
    paths = _module("paths")
    status = _module("status")
    layout, policy = _layout(tmp_path)
    created = status.RunStatusStore(layout).create(NOW)
    status.RunStatusStore(layout).transition(
        created,
        "running",
        NOW + timedelta(microseconds=1),
    )
    action = _issue(semantic_review, layout)
    phase_store = SimpleNamespace(current_phase="U10", active_generation=4)
    foundation_result = SimpleNamespace(phase_store=phase_store)
    forbidden_calls: list[str] = []

    def forbidden(label: str):
        def fail(*args, **kwargs):
            del args, kwargs
            forbidden_calls.append(label)
            pytest.fail(f"{label} ran during semantic host wait")

        return fail

    monkeypatch.setattr(materialization, "build_run_layout", lambda *args: layout)
    monkeypatch.setattr(
        materialization,
        "_apply_pending_validation_repair",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        materialization,
        "preflight_foundation_progress",
        lambda *args, **kwargs: status.RunStatusStore(layout).read(),
    )
    monkeypatch.setattr(
        materialization,
        "_foundation_input_inventory",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(foundation, "advance_foundation", lambda *args, **kwargs: foundation_result)
    monkeypatch.setattr(
        materialization,
        "foundation_progress_projection",
        lambda *args, **kwargs: materialization.MaterializationProgress(
            outcome="foundation-complete",
            run_id=RUN_ID,
            status="running",
            current_phase="U10",
            last_complete_phase="U10",
            next_action=None,
            final_chat=None,
        ),
    )
    monkeypatch.setattr(materialization, "prepare_authoring", lambda *args: None)
    monkeypatch.setattr(
        deliverables,
        "recover_publish_transaction",
        forbidden("publication-recovery"),
    )
    monkeypatch.setattr(
        materialization,
        "materialize_u4_u11",
        lambda *args, **kwargs: action,
    )
    monkeypatch.setattr(deliverables, "publish_delivery", forbidden("publication"))

    progress = materialization.materialize_complete_run(
        ROOT,
        paths.RunMode.TEST,
        RUN_ID,
        policy=policy,
        now=NOW + timedelta(seconds=1),
        entropy=b"semantic-wait-canary",
        fresh_check=forbidden("validation"),
        commit_report=forbidden("report-commit"),
    )

    assert progress.outcome == "awaiting-host-action"
    assert progress.status == "running"
    assert progress.current_phase == "U11"
    assert progress.last_complete_phase == "U10"
    assert progress.next_action == action.document
    assert status.RunStatusStore(layout).read().status == "running"
    assert forbidden_calls == []
    assert not (layout.run_dir / ".writer-lease.json").exists()
    assert not (layout.recovery_dir / "publish-transaction.json").exists()
    assert not (layout.artifacts_dir / "ultra-artifact-manifest.json").exists()
    assert not layout.validation_current_dir.exists()
    assert not (layout.recovery_dir / "repair-plan.json").exists()
