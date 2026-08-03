from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path
import re
import shutil
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills/crossframe-ultra/scripts"
RUNTIME_DIR = SCRIPTS_DIR / "ultra_runtime"
TEMPLATE_DIR = REPO_ROOT / "skills/crossframe-ultra/templates"
RUN_ID = "20260802T000000Z-0123456789ab"

TEMPLATE_MARKERS = {
    "ultra-run-status-output.md": ("run_id", "phase", "validation", "continuation"),
    "ultra-world-volume-output.md": ("boundary", "node", "channel", "clock"),
    "ultra-transformation-ledger-output.md": ("rule", "effect", "provenance"),
    "ultra-concept-disposition-output.md": ("concept", "disposition", "justification"),
    "ultra-claim-mechanism-output.md": ("claim", "mechanism", "edge", "unknown"),
    "ultra-recursive-state-output.md": ("node", "parent", "state", "channel"),
    "ultra-recursive-lineage-output.md": ("lineage", "parent", "order-2", "order-3"),
    "ultra-order-evaluation-output.md": ("order-2", "reversal", "order-3", "lock-in"),
    "ultra-retrieval-output.md": ("query", "source", "result", "cutoff"),
    "ultra-red-team-output.md": ("rival", "counter", "residual", "confidence"),
    "ultra-verdict-output.md": ("fact", "prediction", "value", "responsibility", "authorization"),
    "ultra-action-ranking-output.md": ("action", "rank", "constraint", "indicator"),
    "ultra-forecast-output.md": ("forecast", "indicator", "window", "resolution"),
    "ultra-framework-gap-output.md": ("gap", "framework", "boundary", "disposition"),
    "ultra-dossier-output.md": ("推演", "证据", "机制", "撤回条件"),
    "ultra-artifact-index-output.md": ("artifact", "sha256", "phase", "path"),
    "ultra-validator-report-output.md": ("validator", "manifest", "passed", "error"),
    "ultra-repair-plan-output.md": ("attempt", "repair", "reset", "bounded"),
}

CLOSED_ORGANIZATION_CASE = {
    "case_id": "org-delay-multiparent",
    "material_closed": True,
    "parents": ["care-constraint", "incentive-system", "resource-allocation"],
    "channels": [
        {"channel_id": "formal-schedule", "clock": "weekly", "latency_days": 2},
        {"channel_id": "care-load", "clock": "event-driven", "latency_days": 11},
    ],
    "order_2": {
        "effect": "reversal",
        "condition": "formal escalation increases hidden care-load displacement",
    },
    "order_3": {
        "effect": "lock-in",
        "condition": "promotion metrics reward the escalation pattern",
    },
    "rival": {
        "explanation_id": "individual-execution-deficit",
        "confidence": "low",
    },
    "verdict_kinds": [
        "fact",
        "prediction",
        "value",
        "responsibility",
        "authorization",
    ],
}


def _module(name: str):
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module(f"ultra_runtime.{name}")


def _layout(paths, tmp_path: Path):
    policy = paths.RootPolicy(tmp_path / "production", tmp_path / "test")
    return paths.build_run_layout(paths.RunMode.TEST, RUN_ID, policy)


def _real_read_events(jsonio, run_id: str) -> bytes:
    source_path = (
        REPO_ROOT / "skills/crossframe-ultra/references/source-manifest.json"
    )
    source = json.loads(source_path.read_text("utf-8"))
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    binding = _module("constants").current_version_binding()
    rows: list[bytes] = []
    for unit in source["source_units"]:
        event: dict[str, object] = {
            "schema_id": "crossframe.ultra.v82.read-event",
            "schema_version": 1,
            "run_id": run_id,
            "version_binding": binding,
            "generated_at": "2026-08-02T00:00:00Z",
            "content_sha256": unit["sha256"],
            "phase_id": "U1",
            "source_unit_id": unit["unit_id"],
            "source_kind": unit["kind"],
            "source_ordinal": unit["ordinal"],
            "source_manifest_sha256": source_sha256,
            "promoted_semantic_snapshot_sha256": binding[
                "framework_semantic_sha256"
            ],
            "source_lock_sha256": "d" * 64,
            "parent_event_sha256": "e" * 64,
            "receipt_sha256": hashlib.sha256(
                f"{run_id}:{unit['unit_id']}:receipt".encode("utf-8")
            ).hexdigest(),
            "reader_mode": "full-source",
            "execution_identity": {
                "kind": "host-process",
                "process_id": 1,
                "executable": "python",
                "user": "fixture-user",
            },
            "read_at": "2026-08-02T00:00:00Z",
        }
        event["read_event_sha256"] = jsonio.sha256_bytes(
            jsonio.canonical_json_bytes(event)
        )
        rows.append(jsonio.canonical_json_bytes(event))
    return b"".join(rows)


class RecordingPhaseStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = [
            (phase, (phase.lower() * 32)[:64]) for phase in ("U0", "U1", "U2", "U3")
        ]

    def complete(self, phase_id: str, *, artifact_hashes, **kwargs):
        digests = tuple(artifact_hashes)
        assert digests and all(len(digest) == 64 for digest in digests)
        self.calls.append((phase_id, digests))
        return {
            "phase_id": phase_id,
            "event_sha256": (phase_id.lower() * 32)[:64],
            "artifact_hashes": list(digests),
        }


def test_all_eighteen_task13_templates_exist_and_freeze_semantic_fields() -> None:
    assert len(TEMPLATE_MARKERS) == 18
    for filename, markers in TEMPLATE_MARKERS.items():
        path = TEMPLATE_DIR / filename
        assert path.is_file(), path
        raw = path.read_bytes()
        assert raw.endswith(b"\n")
        assert b"\r\n" not in raw
        text = raw.decode("utf-8").casefold()
        assert text.startswith("# ")
        for marker in markers:
            assert marker.casefold() in text, f"{filename}: missing {marker}"


def test_closed_fixture_contract_has_the_required_structural_stressors() -> None:
    case = CLOSED_ORGANIZATION_CASE
    assert case["material_closed"] is True
    assert len(case["parents"]) >= 2
    assert len(case["channels"]) == 2
    assert len({channel["clock"] for channel in case["channels"]}) == 2
    assert case["order_2"]["effect"] == "reversal"
    assert case["order_3"]["effect"] == "lock-in"
    assert case["rival"]["confidence"] == "low"
    assert case["verdict_kinds"] == [
        "fact",
        "prediction",
        "value",
        "responsibility",
        "authorization",
    ]


@pytest.fixture(scope="module")
def real_seam_result(
    tmp_path_factory,
) -> dict[str, object]:
    from tests import test_ultra_state_machine as state_fixtures

    evidence = _module("evidence")
    jsonio = _module("jsonio")
    materialization = _module("materialization")
    recovery = _module("recovery")
    state_machine = _module("state_machine")
    status = _module("status")
    context = state_fixtures.u1_prerequisite_context.__wrapped__(tmp_path_factory)
    u1_authority = state_fixtures.u1_authority.__wrapped__(context)
    layout = context["run_layout"]
    original_store = state_fixtures._store(state_machine)
    state_fixtures._complete_u0_u1(original_store, u1_authority)
    state_fixtures._complete_u2(original_store)
    evidence_fixture = json.loads(
        (
            REPO_ROOT / "tests/fixtures/ultra-runtime/evidence-ledger-valid.json"
        ).read_text("utf-8")
    )
    for entry in evidence_fixture["entries"]:
        original_store.append_evidence(entry)
    evidence_seal = evidence.validate_evidence_artifact(
        original_store.evidence_artifact,
        expected_run_id=original_store.run_id,
        expected_version_binding=_module("constants").current_version_binding(),
        expected_phase_id="U3",
        expected_evidence_cutoff=original_store.evidence_cutoff,
    )
    original_store.complete(
        "U3",
        artifact_hashes=(evidence_seal.artifact_sha256,),
        evidence_authority=evidence_seal,
    )
    run_contract_path = layout.artifacts_dir / "ultra-run-contract.json"
    evidence_path = (
        layout.artifacts_dir / "U00-U03-evidence/U03-evidence-ledger.json"
    )
    jsonio.atomic_write_json(run_contract_path, dict(original_store.run_contract))
    jsonio.atomic_write_json(evidence_path, original_store.evidence_artifact)
    read_events_path = (
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl"
    )
    jsonio.atomic_write_bytes(
        read_events_path,
        _real_read_events(jsonio, original_store.run_id),
    )
    now = datetime(2026, 8, 4, tzinfo=timezone.utc)
    checkpoint = recovery.create_checkpoint(
        layout,
        original_store,
        boundary_kind="phase",
        boundary_id="U3",
        boundary_ordinal=0,
        artifact_paths=(evidence_path,),
        now=now,
    )
    expected_events = original_store.events
    del original_store

    statuses = status.RunStatusStore(layout)
    created = statuses.create(now)
    running = statuses.transition(created, "running", now + timedelta(seconds=1))
    statuses.transition(running, "interrupted", now + timedelta(seconds=2))

    resumed = recovery.resume_run(layout, now=now + timedelta(seconds=3))

    assert resumed.checkpoint == checkpoint
    assert resumed.phase_store.events == expected_events
    assert resumed.phase_store.events[-1]["phase_id"] == "U3"
    assert resumed.phase_store.events[-1]["status"] == "complete"
    assert resumed.phase_store.evidence_frozen is True
    assert resumed.phase_store.evidence_sha256 == evidence_seal.artifact_sha256

    world_source = layout.authoring_dir / "U04-world-volume.json"
    jsonio.atomic_write_json(
        world_source,
        json.loads(
            (
                REPO_ROOT / "tests/fixtures/ultra-runtime/world-volume-valid.json"
            ).read_text("utf-8")
        ),
    )
    world = materialization.seal_authoring_artifact(
        layout,
        world_source,
        generated_at=now + timedelta(seconds=4),
        authority_documents={"evidence": jsonio.load_json_object(evidence_path)},
    )
    world_path = materialization.artifact_destination(layout, world_source)
    jsonio.atomic_write_json(world_path, world)
    u4_event = materialization.record_materialized_phase(
        layout,
        resumed.phase_store,
        "U4",
        (world_path,),
        input_artifact_hashes=(
            hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        ),
    )

    assert u4_event["phase_id"] == "U4"
    recovery.create_checkpoint(
        layout,
        resumed.phase_store,
        boundary_kind="phase",
        boundary_id="U4",
        boundary_ordinal=0,
        artifact_paths=(world_path,),
        now=now + timedelta(seconds=5),
    )
    restarted = recovery.resume_run(layout, now=now + timedelta(seconds=6))
    assert restarted.phase_store.evidence_frozen is True
    assert restarted.phase_store.evidence_sha256 == evidence_seal.artifact_sha256
    assert [
        event["phase_id"] for event in restarted.phase_store.events
    ].count("U4") == 1

    from tests.test_ultra_concept_closure import make_concept_document
    from tests.test_ultra_judgment import make_action_ranking, make_gap_ledger
    from tests.test_ultra_recursion import state_registry

    fixture_root = REPO_ROOT / "tests/fixtures/ultra-runtime"
    load_fixture = lambda name: json.loads((fixture_root / name).read_text("utf-8"))
    transformation = load_fixture("transformation-valid.json")
    verdict = load_fixture("verdict-valid.json")
    authored = {
        "U05-transformation-ledger.json": transformation,
        "U05-concept-disposition.json": make_concept_document(
            evidence_fixture,
            load_fixture("world-volume-valid.json"),
            transformation,
        ),
        "U06-claim-mechanism-graph.json": load_fixture(
            "claim-mechanism-graph-valid.json"
        ),
        "U07-recursive-lineage.json": load_fixture("recursive-lineage-valid.json"),
        "U08-order-evaluation.json": load_fixture("order-evaluation-valid.json"),
        "U08-red-team-report.json": load_fixture("red-team-report-valid.json"),
        "U09-verdict.json": verdict,
        "U09-action-ranking.json": make_action_ranking(verdict),
        "U09-forecast-ledger.json": load_fixture("forecast-valid.json"),
    }
    for recursive_state in state_registry().values():
        authored[
            f"U07-recursive-states/{recursive_state['node_id']}.json"
        ] = recursive_state
    authored["U10-framework-gap-ledger.json"] = make_gap_ledger(
        authored["U09-action-ranking.json"]
    )
    output_authority = json.loads(
        (
            fixture_root
            / "article-packets/frozen-upstream-authority.json"
        ).read_text("utf-8")
    )
    output_authority["required_artifacts"][0]["path"] = (
        "artifacts/U09-U10-verdict/U09-verdict.json"
    )
    output_authority["required_artifacts"][1]["path"] = (
        "artifacts/U09-U10-verdict/U09-action-ranking.json"
    )
    authored["U10-output-plan.json"] = _module("article").build_output_plan_artifact(
        run_id=output_authority["run_id"],
        version_binding=output_authority["version_binding"],
        generated_at=output_authority["generated_at"]["u10"],
        u9_parent_event_sha256=output_authority["u9_parent_event_sha256"],
        article_path=output_authority["article_path"],
        sections=output_authority["sections"],
        appendices=output_authority["appendices"],
        required_artifacts=output_authority["required_artifacts"],
        semantic_universe=output_authority["semantic_universe"],
        blind_recovery_expectations=output_authority[
            "blind_recovery_expectations"
        ],
    )
    for relative, document in authored.items():
        jsonio.atomic_write_json(layout.authoring_dir / relative, document)

    with pytest.raises(ValueError, match="packet count"):
        materialization.materialize_u4_u11(
            REPO_ROOT,
            layout,
            restarted.phase_store,
            now=now + timedelta(seconds=7),
            create_checkpoint=recovery.create_checkpoint,
        )

    sealed_plan = jsonio.load_json_object(
        layout.artifacts_dir / "U09-U10-verdict/U10-output-plan.json"
    )
    article_text = (
        fixture_root / "article-packets/blind-reader-article.md"
    ).read_text("utf-8").replace("\r\n", "\n")
    article_parts = tuple(
        match.group(0).strip() + "\n"
        for match in re.finditer(r"(?ms)^## .*?(?=^## |\Z)", article_text)
    )
    assert len(article_parts) == 15
    packet_dir = layout.authoring_dir / "article/packets"
    for ordinal, prose in enumerate(article_parts, start=1):
        packet_path = packet_dir / f"packet-{ordinal:02d}.md"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(prose, encoding="utf-8", newline="\n")
    packet_paths = tuple(sorted(packet_dir.glob("*.md"), key=lambda path: path.name))
    packet_documents = materialization._packet_mappings(sealed_plan, packet_paths)
    assembled = _module("article").assemble_article(
        sealed_plan,
        packet_documents,
        layout.authoring_dir / "article.partial.md",
    )
    coverage = _module("coverage")
    plan_sha256 = jsonio.sha256_bytes(jsonio.canonical_json_bytes(sealed_plan))
    coverage_document = coverage.build_semantic_coverage_artifact(
        assembled.article_text,
        sealed_plan,
        output_authority["mappings"],
        run_id=layout.run_dir.name,
        version_binding=_module("constants").current_version_binding(),
        generated_at="2026-08-04T00:00:08Z",
        expected_output_plan_artifact_sha256=plan_sha256,
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / "U11-semantic-coverage.json",
        coverage_document,
    )
    coverage_sha256 = jsonio.sha256_bytes(
        jsonio.canonical_json_bytes(coverage_document)
    )
    review_document = coverage.build_article_review_artifact(
        assembled.article_text,
        sealed_plan,
        coverage_document,
        run_id=layout.run_dir.name,
        version_binding=_module("constants").current_version_binding(),
        generated_at="2026-08-04T00:00:08Z",
        expected_output_plan_artifact_sha256=plan_sha256,
        expected_coverage_artifact_sha256=coverage_sha256,
    )
    jsonio.atomic_write_json(
        layout.authoring_dir / "U11-article-review.json",
        review_document,
    )
    (layout.authoring_dir / "完整推演档案.md").write_text(
        "# 完整推演档案\n\n真实磁盘 seam 验证档案。\n",
        encoding="utf-8",
        newline="\n",
    )
    bundle = materialization.materialize_u4_u11(
        REPO_ROOT,
        layout,
        restarted.phase_store,
        now=now + timedelta(seconds=8),
        create_checkpoint=recovery.create_checkpoint,
    )
    assert bundle.phase_events[-1]["phase_id"] == "U11"
    assert [
        event["phase_id"] for event in restarted.phase_store.events
    ] == [f"U{ordinal}" for ordinal in range(12)]
    snapshot_root = layout.root.parent / "u11-seam-snapshot"
    shutil.copytree(layout.root, snapshot_root)

    paths = _module("paths")
    validation = _module("validation")
    policy = paths.RootPolicy(
        layout.root.parent / "production-control",
        layout.root,
    )
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(validation, "default_root_policy", lambda: policy)

    def fresh_check(stage: str) -> bytes:
        assert stage in {"pre-publish", "post-publish"}
        official_article = (
            layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
        )
        if stage == "pre-publish":
            assert not official_article.exists()
        else:
            assert official_article.is_file()
        return validation.validate_run_from_disk(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
        )

    def commit_report(stage: str, report_bytes: bytes) -> object:
        assert stage in {"pre-publish", "post-publish"}
        report = json.loads(report_bytes.decode("utf-8"))
        return validation.commit_validation_attempt(
            layout,
            attempt_id=report["attempt_id"],
            report_bytes=report_bytes,
            expected_manifest_sha256=report["manifest_sha256"],
            expected_validator_set_sha256=report["validator_set_sha256"],
        )

    complete = materialization.materialize_complete_run(
        REPO_ROOT,
        paths.RunMode.TEST,
        layout.run_dir.name,
        policy=policy,
        now=now + timedelta(seconds=9),
        entropy=b"task12-task13-real-seam",
        fresh_check=fresh_check,
        commit_report=commit_report,
    )
    assert complete.status == "complete"
    final_status = status.RunStatusStore(layout).read()
    assert final_status.status == "complete"
    assert final_status.current_phase == "U12"
    assert final_status.last_complete_phase == "U12"
    assert final_status.validation_passed is True
    assert final_status.tools_allowed is False
    u12_checkpoint = recovery.select_resume_checkpoint(layout)
    assert u12_checkpoint["phase_id"] == "U12"
    manifest = jsonio.load_json_object(complete.manifest_path)
    journal = jsonio.load_json_object(
        layout.recovery_dir / "publish-transaction.json"
    )
    latest_complete = _module("indexes").IndexStore(layout.root).read_pointer(
        "latest-complete"
    )
    phase_events = tuple(
        json.loads(line)
        for line in (
            layout.recovery_dir / "phase-events.jsonl"
        ).read_text("utf-8").splitlines()
    )
    monkeypatch.undo()
    return {
        "layout": layout,
        "u11_snapshot_root": snapshot_root,
        "u3_evidence_frozen": resumed.phase_store.evidence_frozen,
        "u3_evidence_sha256": resumed.phase_store.evidence_sha256,
        "expected_evidence_sha256": evidence_seal.artifact_sha256,
        "u4_event_count": sum(
            event["phase_id"] == "U4" for event in phase_events
        ),
        "complete": complete,
        "final_status": final_status,
        "u12_checkpoint": u12_checkpoint,
        "manifest": manifest,
        "journal": journal,
        "latest_complete": latest_complete,
    }


def test_seam_recovery_restores_frozen_u3_evidence_with_same_sha(
    real_seam_result,
) -> None:
    assert real_seam_result["u3_evidence_frozen"] is True
    assert real_seam_result["u3_evidence_sha256"] == real_seam_result[
        "expected_evidence_sha256"
    ]


def test_seam_restart_reuses_u4_without_duplicate_phase_event(
    real_seam_result,
) -> None:
    assert real_seam_result["u4_event_count"] == 1


def test_task12_task13_real_disk_seam_commits_atomic_complete_run(
    real_seam_result,
) -> None:
    complete = real_seam_result["complete"]
    status_record = real_seam_result["final_status"]
    assert complete.status == "complete"
    assert status_record.status == "complete"
    assert status_record.current_phase == "U12"
    assert status_record.last_complete_phase == "U12"
    assert status_record.validation_passed is True
    assert status_record.tools_allowed is False
    assert real_seam_result["u12_checkpoint"]["phase_id"] == "U12"
    assert real_seam_result["manifest"]["official_delivery_published"] is True
    assert real_seam_result["journal"]["state"] == "complete"
    assert real_seam_result["latest_complete"]["run_id"] == status_record.run_id


def _snapshot_materialization_runtime(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    paths = _module("paths")
    validation = _module("validation")
    test_root = tmp_path / "test-control"
    shutil.copytree(real_seam_result["u11_snapshot_root"], test_root)
    policy = paths.RootPolicy(tmp_path / "production-control", test_root)
    layout = paths.build_run_layout(
        paths.RunMode.TEST,
        real_seam_result["final_status"].run_id,
        policy,
    )
    monkeypatch.setattr(validation, "default_root_policy", lambda: policy)

    def fresh_check(stage: str) -> bytes:
        official_article = (
            layout.delivery_dir / "CrossFrame-Ultra-完整文章.md"
        )
        if stage == "pre-publish":
            assert not official_article.exists()
        else:
            assert official_article.is_file()
        return validation.validate_run_from_disk(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
        )

    def commit_report(stage: str, report_bytes: bytes) -> object:
        report = json.loads(report_bytes.decode("utf-8"))
        return validation.commit_validation_attempt(
            layout,
            attempt_id=report["attempt_id"],
            report_bytes=report_bytes,
            expected_manifest_sha256=report["manifest_sha256"],
            expected_validator_set_sha256=report["validator_set_sha256"],
        )

    return paths, layout, policy, fresh_check, commit_report


def test_seam_pre_u12_checkpoint_failure_rolls_back_official_names(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy, fresh_check, commit_report = (
        _snapshot_materialization_runtime(real_seam_result, tmp_path, monkeypatch)
    )
    materialization = _module("materialization")
    recovery = _module("recovery")
    status = _module("status")
    original_checkpoint = recovery.create_checkpoint

    def fail_u12_checkpoint(*args, **kwargs):
        if kwargs.get("boundary_id") == "U12":
            raise recovery.RecoveryStateError("injected U12 checkpoint failure")
        return original_checkpoint(*args, **kwargs)

    monkeypatch.setattr(recovery, "create_checkpoint", fail_u12_checkpoint)
    with pytest.raises(recovery.RecoveryStateError, match="injected U12"):
        materialization.materialize_complete_run(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
            policy=policy,
            now=datetime(2026, 8, 4, 0, 1, tzinfo=timezone.utc),
            entropy=b"pre-u12-rollback",
            fresh_check=fresh_check,
            commit_report=commit_report,
        )

    publication = _module("deliverables").publication_paths(
        layout,
        "20260804T000100Z-" + hashlib.sha256(b"pre-u12-rollback").hexdigest()[:12],
    )
    assert not any(path.exists() for path in publication.official_paths)
    assert status.RunStatusStore(layout).read().status == "needs_attention"
    assert _module("jsonio").load_json_object(publication.journal_path)[
        "state"
    ] == "rolled-back"
    assert recovery.select_resume_checkpoint(layout)["phase_id"] == "U11"


def test_seam_durable_u12_status_cas_failure_is_retained_then_rolled_forward(
    real_seam_result,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths, layout, policy, fresh_check, commit_report = (
        _snapshot_materialization_runtime(real_seam_result, tmp_path, monkeypatch)
    )
    deliverables = _module("deliverables")
    materialization = _module("materialization")
    status = _module("status")
    original_transition = status.RunStatusStore.transition
    failed = False

    def fail_first_complete(self, expected, next_status, now, **kwargs):
        nonlocal failed
        if next_status == "complete" and not failed:
            failed = True
            raise status.RunStatusConflictError("injected complete CAS failure")
        return original_transition(self, expected, next_status, now, **kwargs)

    monkeypatch.setattr(status.RunStatusStore, "transition", fail_first_complete)
    with pytest.raises(status.RunStatusConflictError, match="injected complete CAS"):
        materialization.materialize_complete_run(
            REPO_ROOT,
            paths.RunMode.TEST,
            layout.run_dir.name,
            policy=policy,
            now=datetime(2026, 8, 4, 0, 2, tzinfo=timezone.utc),
            entropy=b"u12-roll-forward",
            fresh_check=fresh_check,
            commit_report=commit_report,
        )

    retained = status.RunStatusStore(layout).read()
    assert retained.status == "needs_attention"
    assert retained.tools_allowed is False
    assert (layout.delivery_dir / "CrossFrame-Ultra-完整文章.md").is_file()
    assert _module("recovery").select_resume_checkpoint(layout)["phase_id"] == "U12"
    journal_path = layout.recovery_dir / "publish-transaction.json"
    assert _module("jsonio").load_json_object(journal_path)["state"] == "u12-durable"

    recovered = deliverables.recover_publish_transaction(
        layout,
        mark_needs_attention=lambda reason: pytest.fail(reason),
    )
    assert recovered["state"] == "complete"
    completed = status.RunStatusStore(layout).read()
    assert completed.status == "complete"
    assert completed.tools_allowed is False
    assert _module("jsonio").load_json_object(journal_path)["state"] == "complete"
    assert _module("indexes").IndexStore(layout.root).read_pointer(
        "latest-complete"
    )["run_id"] == layout.run_dir.name


def _u0_recovery_case(tmp_path: Path):
    from tests.test_ultra_recovery import _fixture_run

    recovery = _module("recovery")
    jsonio = _module("jsonio")
    status = _module("status")
    _, layout, store, artifact_path = _fixture_run(tmp_path)
    now = datetime(2026, 8, 4, tzinfo=timezone.utc)
    checkpoint = recovery.create_checkpoint(
        layout,
        store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(artifact_path,),
        now=now,
    )
    statuses = status.RunStatusStore(layout)
    created = statuses.create(now)
    running = statuses.transition(created, "running", now + timedelta(seconds=1))
    statuses.transition(running, "interrupted", now + timedelta(seconds=2))
    return recovery, jsonio, statuses, layout, artifact_path, checkpoint, now


@pytest.mark.parametrize(
    "corruption",
    ("checkpoint", "artifact"),
    ids=("corrupt-checkpoint", "corrupt-artifact"),
)
def test_seam_corrupt_checkpoint_or_artifact_fails_closed(
    tmp_path: Path,
    corruption: str,
) -> None:
    recovery, jsonio, statuses, layout, artifact_path, checkpoint, now = (
        _u0_recovery_case(tmp_path)
    )
    if corruption == "checkpoint":
        checkpoint_path = (
            layout.recovery_dir
            / "checkpoints"
            / f"{jsonio.sha256_bytes(jsonio.canonical_json_bytes(checkpoint))}.json"
        )
        changed = dict(checkpoint)
        changed["generated_at"] = "2026-08-04T00:00:01Z"
        jsonio.atomic_write_json(checkpoint_path, changed)
    else:
        artifact_path.write_bytes(b"tampered artifact\n")

    with pytest.raises(recovery.RecoveryError, match="checkpoint|artifact|hash"):
        recovery.resume_run(layout, now=now + timedelta(seconds=3))
    assert statuses.read().status == "interrupted"
    assert not (layout.delivery_dir / "CrossFrame-Ultra-完整文章.md").exists()


def test_seam_changed_frozen_input_fails_closed(tmp_path: Path) -> None:
    recovery, jsonio, statuses, layout, _, _, now = _u0_recovery_case(tmp_path)
    authority = jsonio.load_json_object(layout.recovery_dir / "run-authority.json")
    input_path = layout.run_dir / authority["input_refs"][0]["path"]
    input_path.write_bytes(input_path.read_bytes() + b"input drift\n")

    with pytest.raises(recovery.RecoveryIntegrityError, match="input|hash"):
        recovery.resume_run(layout, now=now + timedelta(seconds=3))
    assert statuses.read().status == "interrupted"
    assert not (layout.delivery_dir / "CrossFrame-Ultra-完整文章.md").exists()


@pytest.mark.parametrize("mutation", ("pruned", "mixed"))
def test_seam_mixed_or_pruned_lineage_fails_closed(mutation: str) -> None:
    from tests import test_ultra_recursion as recursion_fixtures

    lineage = recursion_fixtures.load_fixture("recursive-lineage-valid.json")
    registry = recursion_fixtures.state_registry()
    declared = lineage["nodes"][2]["recursive_state_artifact_sha256"]
    if mutation == "pruned":
        registry.pop(declared)
    else:
        replacement = next(
            value for key, value in registry.items() if key != declared
        )
        registry[declared] = copy.deepcopy(replacement)

    with pytest.raises(ValueError, match="recursive-state|registry|sealed|hash"):
        recursion_fixtures.validate_lineage(lineage, registry=registry)


def test_full_fixture_records_u0_u12_once_and_packet_checkpoints_are_not_phase_events(
    tmp_path: Path
) -> None:
    materialization_path = RUNTIME_DIR / "materialization.py"
    delivery_path = RUNTIME_DIR / "deliverables.py"
    if not materialization_path.is_file() or not delivery_path.is_file():
        pytest.skip("Task 13 materialization boundary is not implemented")
    materialization = _module("materialization")
    deliverables = _module("deliverables")
    paths = _module("paths")
    layout = _layout(paths, tmp_path)
    prepared = materialization.prepare_authoring(layout)
    store = RecordingPhaseStore()
    base_time = datetime(2026, 8, 2, tzinfo=timezone.utc)

    phase_files = {
        "U4": ["U04-world-volume.json"],
        "U5": ["U05-transformation-ledger.json", "U05-concept-disposition.json"],
        "U6": ["U06-claim-mechanism-graph.json"],
        "U7": ["U07-recursive-states/node-a.json", "U07-recursive-lineage.json"],
        "U8": ["U08-order-evaluation.json", "U08-red-team-report.json"],
        "U9": ["U09-verdict.json", "U09-action-ranking.json", "U09-forecast-ledger.json"],
        "U10": ["U10-framework-gap-ledger.json", "U10-output-plan.json"],
    }
    for phase, relatives in phase_files.items():
        artifact_paths: list[Path] = []
        for ordinal, relative in enumerate(relatives, start=1):
            target = prepared.authoring_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(
                    {
                        "case": CLOSED_ORGANIZATION_CASE,
                        "phase": phase,
                        "ordinal": ordinal,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            artifact_paths.append(target)
        materialization.record_materialized_phase(
            layout,
            store,
            phase,
            artifact_paths,
        )

    packet_paths = []
    for ordinal in range(1, 4):
        packet = layout.authoring_dir / "article/packets" / f"packet-{ordinal:02d}.md"
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(f"## packet {ordinal}\n\ncase material\n", encoding="utf-8")
        packet_paths.append(packet)
    partial_for_checkpoints = layout.authoring_dir / "article.partial.md"
    partial_for_checkpoints.write_text(
        "# partial article\n\npacket checkpoint authority\n",
        encoding="utf-8",
    )
    checkpoints: list[tuple[str, int, tuple[Path, ...]]] = []
    before_packet_events = tuple(store.calls)
    materialization.checkpoint_article_packets(
        layout,
        store,
        packet_paths,
        now=base_time,
        create_checkpoint=lambda layout, phase_store, **kwargs: checkpoints.append(
            (
                kwargs["boundary_id"],
                kwargs["boundary_ordinal"],
                tuple(kwargs["artifact_paths"]),
            )
        ),
    )
    assert store.calls == list(before_packet_events)
    assert [ordinal for _, ordinal, _ in checkpoints] == [1, 2, 3]

    u11_paths = (
        layout.authoring_dir / "U11-semantic-coverage.json",
        layout.authoring_dir / "U11-article-review.json",
        layout.authoring_dir / "article.partial.md",
        layout.authoring_dir / "完整推演档案.md",
        layout.artifacts_dir / "ultra-artifact-index.md",
    )
    for ordinal, target in enumerate(u11_paths, start=1):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"U11 fixture artifact {ordinal}\n", encoding="utf-8")
    materialization.record_materialized_phase(
        layout,
        store,
        "U11",
        u11_paths,
    )

    article = "# 完整文章\n\n组织激励与照护约束共同导致延期。\n".encode("utf-8")
    dossier = (layout.authoring_dir / "完整推演档案.md").read_bytes()
    index = "# 工件索引\n\nU0-U12\n".encode("utf-8")
    manifest = b'{"fixture":"manifest"}\n'
    publication = deliverables.publish_delivery(
        layout,
        transaction_id="20260802T000100Z-bbbbbbbbbbbb",
        article_bytes=article,
        dossier_bytes=dossier,
        artifact_index_bytes=index,
        manifest_bytes=manifest,
        fresh_check=lambda stage: (
            f'{{"overall_status":"pass","stage":"{stage}"}}\n'.encode("utf-8")
        ),
        commit_report=lambda stage, report: None,
        mark_needs_attention=lambda reason: pytest.fail(reason),
    )
    postcheck_report_path = (
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    postcheck_report_path.parent.mkdir(parents=True, exist_ok=True)
    postcheck_report_path.write_bytes(publication.postcheck_report_bytes)
    materialization.complete_u12(
        layout,
        store,
        manifest_path=publication.paths.manifest_path,
        postcheck_report_path=postcheck_report_path,
        delivery_paths=(
            publication.paths.article_path,
            publication.paths.dossier_path,
            publication.paths.artifact_index_path,
        ),
        postcheck_passed=publication.postcheck_passed,
    )

    assert [phase for phase, _ in store.calls] == [f"U{number}" for number in range(13)]
    assert store.calls[-1][1] == tuple(
        __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        for path in (
            publication.paths.manifest_path,
            postcheck_report_path,
            publication.paths.article_path,
            publication.paths.dossier_path,
            publication.paths.artifact_index_path,
        )
    )
    assert not (layout.authoring_dir / "U09-forecast-resolution.json").exists()
    assert publication.paths.article_path.is_file()
    assert publication.paths.dossier_path.is_file()
    assert publication.paths.artifact_index_path.is_file()
