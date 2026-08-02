from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
SOURCE_MANIFEST = ROOT / "skills/crossframe-ultra/references/source-manifest.json"
SOURCE_MANIFEST_SHA256 = "1c22cda241473ecb3654e37ee9890b975457bb098334ab5c0f85d2775abf6725"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _binding() -> dict[str, object]:
    return {
        "framework_version": "8.2",
        "framework_revision": "v8.2-r1",
        "framework_raw_sha256": "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20",
        "framework_semantic_sha256": "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0",
        "runtime_version": "1.0.0",
        "artifact_schema_version": 1,
        "compiler_version": "1.0.0",
        "validator_version": "1.0.0",
        "article_contract_version": "1.0.0",
        "source_tree_sha256": "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187",
    }


def _snapshot(module):
    return module.load_source_manifest(
        SOURCE_MANIFEST, expected_sha256=SOURCE_MANIFEST_SHA256
    )


def _events(module, snapshot):
    return module.capture_authority_read_diagnostic(
        ROOT,
        run_id="run-read-01",
        version_binding=_binding(),
        manifest=snapshot,
        reader_mode="full-source",
        read_at="2026-08-02T00:00:00Z",
    )


def _validate(module, batch, snapshot, **expectations):
    return module.audit_read_capture(
        batch,
        snapshot,
        promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
        expected_run_id=expectations.get("run_id", "run-read-01"),
        expected_version_binding=expectations.get("version_binding", _binding()),
        expected_parent_event_sha256=expectations.get("parent", "0" * 64),
    )


def test_unverified_mapping_manifest_has_no_runtime_bypass():
    import ultra_runtime.source_integrity as module

    with pytest.raises(module.SourceManifestError, match="sealed manifest"):
        module.build_read_plan(
            {"source_unit_count": 4753},
            promoted_semantic_snapshot_sha256="a" * 64,
        )


def test_authority_manifest_loader_rejects_a_different_expected_hash():
    import ultra_runtime.source_integrity as module

    with pytest.raises(module.SourceManifestError, match="authority binding"):
        module.load_source_manifest(SOURCE_MANIFEST, expected_sha256="f" * 64)


def test_captured_read_events_bind_the_real_host_execution_identity():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    receipt = module.capture_committed_read_receipts(ROOT, manifest=snapshot)[0]
    with pytest.raises(module.SourceCoverageError, match="current host"):
        module.make_read_event(
            run_id="run-fake-host",
            version_binding=_binding(),
            source_unit=receipt.source_unit,
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            source_manifest_sha256=snapshot.sha256,
            reader_mode="full-source",
            execution_identity={
                **module.execution_identity(),
                "process_id": 999999,
            },
            read_at="2026-08-02T00:00:00Z",
            receipt=receipt,
        )


def test_authority_snapshot_cannot_be_rebound_after_caller_mutates_a_copy():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    mutated_copy = snapshot.document
    mutated_copy["source_units"][0]["sha256"] = "0" * 64
    assert snapshot.document["source_units"][0]["sha256"] != "0" * 64
    with pytest.raises(module.SourceManifestError, match="snapshot.*issued|authority snapshot"):
        module.build_read_plan(
            object.__new__(module.SourceManifestSnapshot),
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
        )


def test_manifest_replacement_between_stat_and_open_is_rejected(tmp_path, monkeypatch):
    import ultra_runtime.source_integrity as module

    target = tmp_path / "source-manifest.json"
    target.write_bytes(SOURCE_MANIFEST.read_bytes())
    replacement = tmp_path / "replacement.json"
    replacement.write_text("{}", encoding="utf-8")
    original_open = Path.open
    replaced = False

    def replace_then_open(path, *args, **kwargs):
        nonlocal replaced
        if path == target and not replaced:
            replaced = True
            replacement.replace(target)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", replace_then_open)
    with pytest.raises(module.SourceManifestError, match="changed.*(?:read|replaced)|invalid source manifest"):
        module.load_source_manifest(target)


@pytest.mark.parametrize("mutation", ("wrong_manifest", "wrong_snapshot", "wrong_run"))
def test_read_coverage_rejects_raw_rehashed_events_even_when_the_metadata_looks_valid(mutation):
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    raw_events = [dict(event) for event in _events(module, snapshot).events]
    if mutation == "wrong_manifest":
        raw_events[0]["source_manifest_sha256"] = "e" * 64
    elif mutation == "wrong_snapshot":
        raw_events[0]["promoted_semantic_snapshot_sha256"] = "e" * 64
    else:
        raw_events[0]["run_id"] = "different-run"
    event = {key: value for key, value in raw_events[0].items() if key != "read_event_sha256"}
    raw_events[0]["read_event_sha256"] = hashlib.sha256(
        json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    with pytest.raises(module.SourceCoverageError, match="trusted|captured|batch"):
        _validate(
            module,
            raw_events,
            snapshot,
        )


def test_exact_4753_unit_plan_is_hash_bound_and_never_claims_reads():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    plan = module.build_read_plan(
        snapshot, promoted_semantic_snapshot_sha256=snapshot.semantic_sha256
    )
    assert plan["source_unit_count"] == 4753
    assert plan["paragraph_count"] == 4631
    assert plan["table_count"] == 122
    assert "read_events" not in plan
    assert len(plan["source_unit_ids"]) == 4753
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA256


def test_anchored_reads_of_paragraph_and_table_bodies_cover_the_full_snapshot():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    events = _events(module, snapshot)
    coverage = _validate(module, events, snapshot)
    assert (coverage.total, coverage.paragraphs, coverage.tables, coverage.complete) == (
        4753,
        4631,
        122,
        True,
    )


def test_coverage_rejects_rehashed_manual_events_and_an_arbitrary_tree_hash():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    batch = _events(module, snapshot)
    manually_rehashed = [dict(event) for event in batch.events]
    manually_rehashed[0]["version_binding"]["source_tree_sha256"] = "e" * 64
    event = {
        key: value
        for key, value in manually_rehashed[0].items()
        if key != "read_event_sha256"
    }
    manually_rehashed[0]["read_event_sha256"] = hashlib.sha256(
        json.dumps(
            event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    with pytest.raises(module.SourceCoverageError, match="trusted|captured|batch"):
        _validate(module, manually_rehashed, snapshot)


@pytest.mark.parametrize("mutation", ("duplicate", "missing", "wrong_hash", "mixed_tree"))
def test_read_coverage_rejects_incomplete_or_cross_binding_batches(mutation):
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    batch = _events(module, snapshot)
    events = list(batch.events)
    if mutation == "duplicate":
        events[-1] = events[-2]
    elif mutation == "missing":
        events.pop()
    elif mutation == "wrong_hash":
        events[0]["content_sha256"] = "f" * 64
    else:
        events[0]["version_binding"]["source_tree_sha256"] = "e" * 64
        event = {key: value for key, value in events[0].items() if key != "read_event_sha256"}
        events[0]["read_event_sha256"] = hashlib.sha256(
            json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
    object.__setattr__(batch, "_events", tuple(events))
    with pytest.raises(module.SourceCoverageError):
        _validate(module, batch, snapshot)


def test_manifest_snapshot_is_factory_sealed_and_metadata_cannot_mint_a_read():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    forged_document = snapshot.document
    forged_document["source_units"][0]["sha256"] = "0" * 64
    with pytest.raises(TypeError):
        module.SourceManifestSnapshot(
            document=forged_document,
            sha256=snapshot.sha256,
            semantic_sha256=snapshot.semantic_sha256,
        )
    with pytest.raises(module.SourceCoverageError, match="receipt|source read"):
        module.make_read_event(
            run_id="run-read-forged",
            version_binding=_binding(),
            source_unit=snapshot.document["source_units"][0],
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            source_manifest_sha256=snapshot.sha256,
            reader_mode="full-source",
            execution_identity=module.execution_identity(),
            read_at="2026-08-02T00:00:00Z",
        )


def test_u1_requires_a_real_measurement_not_a_self_attested_dictionary():
    import ultra_runtime.source_integrity as module

    checks = {
        "source_manifest": "verified",
        "release_manifest": "verified",
        "compatibility_matrix": "verified",
        "knowledge_closure": "verified",
        "skill_tree_hash": "verified",
        "fixed_root": "verified",
        "free_space_reserve": "verified",
        "current_user_acl": "unknown",
    }
    with pytest.raises(module.SourceLockError, match="measurement|attestation"):
        module.verify_u1_prerequisites(checks)

    verification = module.measure_u1_prerequisites(ROOT, manifest=_snapshot(module))
    assert verification.ready
    assert "source_manifest" in verification.verified


def test_public_coverage_audit_rejects_a_run_a_batch_for_run_b_or_new_boundary():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    batch = _events(module, snapshot)
    with pytest.raises(module.SourceCoverageError, match="run|boundary"):
        module.audit_read_capture(
            batch,
            snapshot,
            promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
            expected_run_id="run-read-B",
            expected_version_binding=_binding(),
            expected_parent_event_sha256="a" * 64,
        )


def test_public_read_diagnostic_is_explicitly_non_authorizing():
    import ultra_runtime.source_integrity as module

    snapshot = _snapshot(module)
    diagnostic = module.capture_authority_read_diagnostic(
        ROOT,
        run_id="diagnostic-run",
        version_binding=_binding(),
        manifest=snapshot,
        reader_mode="full-source",
        read_at="2026-08-03T00:00:00Z",
        parent_event_sha256="a" * 64,
    )
    audit = module.audit_read_capture(
        diagnostic,
        snapshot,
        promoted_semantic_snapshot_sha256=snapshot.semantic_sha256,
        expected_run_id="diagnostic-run",
        expected_version_binding=_binding(),
        expected_parent_event_sha256="a" * 64,
    )
    assert audit.complete
    assert audit.authorizes_phase is False
