from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
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


def _run_contract() -> dict[str, object]:
    return {
        "trigger": "crossframe-ultra",
        "request_sha256": "0" * 64,
        "run_mode": "production",
        "sensitivity": "public",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-02T00:00:00Z",
        "capabilities": {
            "filesystem": "available",
            "docx_parser": "available",
            "network": "available",
            "retrieval": "required",
            "validators": "available",
            "subagents": "available",
            "model_context": "available",
        },
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }


def _store(module, *, run_contract=None, capability_availability=None):
    return module.PhaseStore(
        run_id="run-state-01",
        version_binding=_binding(),
        source_sha256="d" * 64,
        input_artifact_hashes=("e" * 64,),
        evidence_cutoff="2026-08-02T00:00:00Z",
        now=datetime(2026, 8, 2, tzinfo=timezone.utc),
        run_contract=run_contract or _run_contract(),
        capability_availability=capability_availability or {"retrieval": "available"},
    )


def _event_sha256(event: dict[str, object]) -> str:
    payload = {key: value for key, value in event.items() if key != "event_sha256"}
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _artifact_sha256(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _phase_artifacts(store, phase: str) -> tuple[str, ...]:
    return (
        (store.evidence_sha256,)
        if phase == "U3"
        else (_artifact_sha256(phase),)
    )


def _complete(store, phase: str):
    return store.complete(phase, artifact_hashes=_phase_artifacts(store, phase))


def test_runtime_module_and_contract_are_available():
    import ultra_runtime.state_machine as module

    assert module.PHASE_ORDER == ("U0", "U1", "U2", "U3")
    assert hasattr(module, "PhaseStore")
    assert hasattr(module, "EvidenceFrozenError")


def test_adjacent_u0_to_u3_chain_and_required_event_fields():
    import ultra_runtime.state_machine as module

    store = _store(module)
    for phase in module.PHASE_ORDER:
        event = _complete(store, phase)
        assert event["phase_id"] == phase
        assert event["parent_event_sha256"]
        assert event["event_sha256"]
        assert event["event_sha256"] == _event_sha256(event)
        assert event["timestamp"] == "2026-08-02T00:00:00Z"
        assert event["status"] == "complete"
        assert event["failure_code"] is None
        assert {
            "run_id",
            "phase_id",
            "event_type",
            "parent_event_sha256",
            "input_artifact_hashes",
            "output_artifact_hashes",
            "version_binding",
            "timestamp",
            "status",
            "failure_code",
            "invalidated_phases",
            "event_sha256",
        } <= set(event)
    assert store.current_phase == "U3"
    assert store.evidence_frozen


@pytest.mark.parametrize("phase", ["U1", "U2", "U3"])
def test_skipped_phase_is_rejected(phase):
    import ultra_runtime.state_machine as module

    store = _store(module)
    with pytest.raises(module.PhaseTransitionError):
        store.complete(phase, artifact_hashes=(_artifact_sha256(phase),))


def test_u0_contract_is_closed_frozen_and_bound_to_available_capabilities():
    import ultra_runtime.state_machine as module

    contract = _run_contract()
    store = _store(module, run_contract=contract)
    contract["sensitivity"] = "restricted"
    contract["capabilities"]["network"] = "unavailable"
    assert store.run_contract["sensitivity"] == "public"
    assert store.run_contract["capabilities"]["network"] == "available"

    invalid = _run_contract()
    invalid["capabilities"]["network"] = "sometimes"
    with pytest.raises(module.RunContractError):
        _store(module, run_contract=invalid)

    missing = _run_contract()
    del missing["outbound_permission"]
    with pytest.raises(module.RunContractError):
        _store(module, run_contract=missing)


def test_required_capability_reported_unavailable_blocks_u0():
    import ultra_runtime.state_machine as module

    with pytest.raises(module.RunBlockedError):
        _store(
            module,
            capability_availability={"retrieval": "unavailable"},
        )


def test_u1_does_not_accept_a_caller_attestation_or_batch_argument():
    import ultra_runtime.state_machine as module

    store = _store(module)
    store.complete("U0", artifact_hashes=(_artifact_sha256("U0"),))
    with pytest.raises(TypeError):
        store.complete(
            "U1",
            artifact_hashes=(_artifact_sha256("U1"),),
            u1_verification={"verified": "caller-supplied"},
        )


def test_parent_hash_input_and_binding_are_immutable():
    import ultra_runtime.state_machine as module

    store = _store(module)
    first = store.complete("U0", artifact_hashes=(_artifact_sha256("U0"),))
    with pytest.raises(module.PhaseIntegrityError):
        store.complete("U1", artifact_hashes=("g" * 64,), parent_event_sha256="0" * 64)
    with pytest.raises(module.PhaseIntegrityError):
        store.complete("U1", artifact_hashes=(_artifact_sha256("U1"),), input_artifact_hashes=("h" * 64,))
    with pytest.raises(module.PhaseIntegrityError):
        store.complete("U1", artifact_hashes=(_artifact_sha256("U1"),), version_binding={**_binding(), "runtime_version": "9.9.9"})
    with pytest.raises(module.PhaseIntegrityError):
        store.complete("U1", artifact_hashes=(_artifact_sha256("U1"),), source_sha256="9" * 64)
    with pytest.raises(module.PhaseIntegrityError):
        store.complete(
            "U1",
            artifact_hashes=(_artifact_sha256("U1"),),
            evidence_cutoff="2027-01-01T00:00:00Z",
        )
    assert store.events == (first,)


def test_event_hash_replay_and_tampering_are_rejected():
    import ultra_runtime.state_machine as module

    store = _store(module)
    event = store.complete("U0", artifact_hashes=(_artifact_sha256("U0"),))
    with pytest.raises(module.PhaseIntegrityError):
        store.replay_event(event)
    tampered = {**event, "status": "failed"}
    with pytest.raises(module.PhaseIntegrityError):
        _store(module).replay_event(tampered)


@pytest.mark.parametrize(
    "mutation",
    [
        "extra_field",
        "complete_with_invalidated_phase",
        "failed_with_output",
        "failed_with_invalidated_current_phase",
    ],
)
def test_replay_rejects_rehashed_events_with_incoherent_or_open_fields(mutation):
    import ultra_runtime.state_machine as module

    origin = _store(module)
    if mutation.startswith("failed"):
        event = origin.fail(
            "U0",
            failure_code="U0_BLOCKED",
            invalidated_phases=("U1",),
        )
    else:
        event = origin.complete("U0", artifact_hashes=(_artifact_sha256("U0"),))

    if mutation == "extra_field":
        event["attacker_controlled"] = True
    elif mutation == "complete_with_invalidated_phase":
        event["invalidated_phases"] = ["U1"]
    elif mutation == "failed_with_output":
        event["output_artifact_hashes"] = [_artifact_sha256("unexpected")]
    else:
        event["invalidated_phases"] = ["U0"]
    event["event_sha256"] = _event_sha256(event)

    with pytest.raises(module.PhaseIntegrityError):
        _store(module).replay_event(event)


def test_failed_event_records_code_and_invalidated_phases_without_advancing():
    import ultra_runtime.state_machine as module

    store = _store(module)
    store.complete("U0", artifact_hashes=(_artifact_sha256("U0"),))
    failed = store.fail(
        "U1",
        failure_code="SOURCE_LOCK_FAILED",
        invalidated_phases=("U2", "U3"),
    )
    assert failed["event_type"] == "phase-failed"
    assert failed["status"] == "failed"
    assert failed["failure_code"] == "SOURCE_LOCK_FAILED"
    assert failed["invalidated_phases"] == ["U2", "U3"]
    assert failed["event_sha256"] == _event_sha256(failed)
    assert store.current_phase == "U0"


def test_naive_event_clock_is_rejected():
    import ultra_runtime.state_machine as module

    with pytest.raises(module.PhaseIntegrityError):
        module.PhaseStore(
            run_id="run-naive-clock",
            version_binding=_binding(),
            source_sha256="d" * 64,
            input_artifact_hashes=("e" * 64,),
            evidence_cutoff="2026-08-02T00:00:00Z",
            now=datetime(2026, 8, 2),
            run_contract=_run_contract(),
            capability_availability={"retrieval": "available"},
        )


def test_replayed_event_and_late_evidence_require_fork():
    import ultra_runtime.state_machine as module

    store = _store(module)
    for phase in module.PHASE_ORDER:
        _complete(store, phase)
    with pytest.raises(module.EvidenceFrozenError):
        store.append_evidence({"evidence_id": "EV-LATE"})
    with pytest.raises(module.PhaseTransitionError):
        store.complete("U3", artifact_hashes=(_artifact_sha256("same"),))
    fork = store.fork_run("run-state-02")
    assert fork.run_id == "run-state-02"
    assert fork.run_id != store.run_id
    assert not fork.evidence_frozen


def test_evidence_cutoff_cannot_move_after_freeze():
    import ultra_runtime.state_machine as module

    store = _store(module)
    for phase in module.PHASE_ORDER:
        _complete(store, phase)
    with pytest.raises(module.EvidenceFrozenError):
        store.freeze_evidence_cutoff("2027-01-01T00:00:00Z")


def test_constructor_rejects_a_well_formed_but_non_authoritative_version_binding():
    import ultra_runtime.state_machine as module

    changed = {**_binding(), "runtime_version": "9.9.9"}
    with pytest.raises(module.PhaseIntegrityError, match="current|authority"):
        module.PhaseStore(
            run_id="run-wrong-authority",
            version_binding=changed,
            source_sha256="d" * 64,
            input_artifact_hashes=("e" * 64,),
            evidence_cutoff="2026-08-02T00:00:00Z",
            now=datetime(2026, 8, 2, tzinfo=timezone.utc),
            run_contract=_run_contract(),
            capability_availability={"retrieval": "available"},
        )


def test_phase_store_exposes_a_schema_valid_u0_run_contract_artifact():
    import ultra_runtime.state_machine as module
    from ultra_runtime.schemas import validate_instance

    store = _store(module)
    validate_instance("ultra-run-contract.schema.json", store.run_contract)


def test_fork_rejects_reusing_the_current_run_id():
    import ultra_runtime.state_machine as module

    store = _store(module)
    with pytest.raises(module.PhaseIntegrityError, match="new run_id"):
        store.fork_run(store.run_id, evidence_cutoff="2026-08-03T00:00:00Z")


def test_u3_binds_and_freezes_the_validated_evidence_ledger():
    import ultra_runtime.state_machine as module

    store = _store(module)
    with pytest.raises(ValueError):
        store.append_evidence({"evidence_id": "EV-INCOMPLETE"})

    for phase in ("U0", "U1", "U2"):
        _complete(store, phase)
    with pytest.raises(module.PhaseIntegrityError, match="evidence ledger"):
        store.complete("U3", artifact_hashes=(_artifact_sha256("unbound"),))

    event = store.complete("U3", artifact_hashes=(store.evidence_sha256,))
    assert store.evidence_frozen
    assert store.evidence_sha256 in event["output_artifact_hashes"]


def test_replayed_u3_boundary_freezes_the_same_evidence_ledger():
    import ultra_runtime.state_machine as module

    source = _store(module)
    for phase in module.PHASE_ORDER:
        _complete(source, phase)

    replayed = _store(module)
    for event in source.events:
        replayed.replay_event(event)

    assert replayed.current_phase == "U3"
    assert replayed.evidence_frozen


def test_replayed_u1_event_reexecutes_the_internal_source_coverage_gate():
    import ultra_runtime.state_machine as module

    source = _store(module)
    _complete(source, "U0")
    u1_event = _complete(source, "U1")
    replayed = _store(module)
    replayed.replay_event(source.events[0])
    replayed.replay_event(u1_event)
    assert replayed.has_valid_u1_source_coverage


def test_u1_internally_captures_full_source_coverage_and_binds_its_artifact():
    import ultra_runtime.state_machine as module

    store = _store(module)
    _complete(store, "U0")
    event = _complete(store, "U1")
    assert store.u1_coverage_sha256 in event["output_artifact_hashes"]
    assert store.has_valid_u1_source_coverage


def test_replayed_u1_reexecutes_the_authority_coverage_check(monkeypatch):
    import ultra_runtime.source_integrity as source_integrity
    import ultra_runtime.state_machine as module

    source = _store(module)
    _complete(source, "U0")
    u1_event = _complete(source, "U1")
    replayed = _store(module)
    replayed.replay_event(source.events[0])

    def fail_if_rechecked(*args, **kwargs):
        raise source_integrity.SourceCoverageError("no source units captured")

    monkeypatch.setattr(source_integrity, "_capture_validate_u1_authority", fail_if_rechecked)
    with pytest.raises(module.PhaseIntegrityError, match="coverage"):
        replayed.replay_event(u1_event)
