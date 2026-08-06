from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
RUN_ID = "run-evidence-01"
STAMP = "2026-08-02T00:00:00Z"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


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


def _hash_without(value: dict[str, object], *fields: str) -> str:
    payload = copy.deepcopy(value)
    for field in fields:
        payload.pop(field, None)
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _binding() -> dict[str, object]:
    return {
        "framework_version": "8.2",
        "framework_revision": "v8.2-r1",
        "framework_raw_sha256": "608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20",
        "framework_semantic_sha256": "4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0",
        "runtime_version": "1.1.0",
        "artifact_schema_version": 2,
        "compiler_version": "1.0.0",
        "validator_version": "1.1.0",
        "article_contract_version": "1.1.0",
        "source_tree_sha256": "9bb924e3d0249993b7de34d585ef805011106784fbbadd9ddbe43abc98a90187",
    }


def _entry(evidence_id: str, identity: str, upstream: str = "report-1"):
    statement = f"statement-{evidence_id}"
    if identity in {"observed", "reported"}:
        origin_kind = "source"
        origin_ref = upstream
        span = None
    elif identity == "user-claim":
        origin_kind = "request"
        origin_ref = "request.bin"
        span = [0, 1]
    else:
        origin_kind = "model"
        origin_ref = upstream
        span = None
    return {
        "evidence_id": evidence_id,
        "identity": identity,
        "statement": statement,
        "source_refs": [upstream],
        "observed_at": "2026-08-01T00:00:00Z" if identity == "observed" else None,
        "confidence": "medium" if identity in {"observed", "reported"} else "unknown",
        "event_date": "2026-07-31",
        "publication_date": "2026-08-01",
        "interest": "none declared",
        "upstream_lineage": [upstream],
        "supported_claim": "claim-1",
        "cannot_prove": "does not prove universal validity",
        "attribution": {
            "origin_kind": origin_kind,
            "origin_ref": origin_ref,
            "content_sha256": hashlib.sha256(statement.encode("utf-8")).hexdigest(),
            "span": span,
            "proof_grade": "fixture-bound",
        },
    }


def _unknown(unknown_id: str = "UNKNOWN-1") -> dict[str, str]:
    return {
        "unknown_id": unknown_id,
        "location_ref": "POS-1",
        "description": "The downstream response is not observed.",
        "resolution_condition": "Observe the next review cycle.",
    }


def _ledger(module, *, run_id: str = RUN_ID, cutoff: str = STAMP):
    ledger = module.EvidenceLedger(
        run_id,
        cutoff,
        version_binding=_binding(),
        generated_at=STAMP,
    )
    ledger.append(_entry("EV-OBS", "observed", "same-report"))
    ledger.append(_entry("EV-REP", "reported", "same-report"))
    ledger.append(_entry("EV-SIM", "simulated", "simulation"))
    ledger.append(_entry("EV-USER", "user-claim", "user"))
    ledger.append(_entry("EV-UNK", "unknown", "unknown-source"))
    ledger.append_unknown(_unknown())
    return ledger


def test_evidence_identity_lineage_and_factual_support_remain_separate():
    import ultra_runtime.evidence as module

    assert set(module.EVIDENCE_IDENTITIES) == {
        "observed",
        "reported",
        "inferred",
        "competing",
        "user-claim",
        "model-candidate",
        "simulated",
        "unknown",
    }
    ledger = _ledger(module)
    assert any(
        {"EV-OBS", "EV-REP"} <= set(cluster)
        for cluster in ledger.independence_clusters()
    )
    assert ledger.independent_support_count("claim-1") == 1
    assert ledger.satisfies_factual_requirement("claim-1", require_observed=True)
    assert ledger.confidence_for("EV-USER") == "unknown"
    assert tuple(item["evidence_id"] for item in ledger.explicit_unknowns) == (
        "EV-UNK",
    )


@pytest.mark.parametrize(
    "identity",
    ("simulated", "user-claim", "model-candidate", "unknown"),
)
def test_nonfactual_identities_cannot_satisfy_a_factual_requirement(identity):
    import ultra_runtime.evidence as module

    with pytest.raises(module.EvidenceValidationError):
        module.validate_evidence_entry(
            _entry("EV-WEAK", identity),
            factual_requirement=True,
        )


def test_evidence_after_the_frozen_cutoff_is_rejected():
    import ultra_runtime.evidence as module

    late = _entry("EV-LATE", "observed")
    late["event_date"] = "2026-08-03"
    ledger = module.EvidenceLedger(
        RUN_ID,
        STAMP,
        version_binding=_binding(),
        generated_at=STAMP,
    )
    with pytest.raises(module.EvidenceValidationError, match="cutoff"):
        ledger.append(late)


def test_frozen_evidence_ledger_is_a_real_public_schema_artifact_with_two_hash_roles():
    import ultra_runtime.evidence as module
    from ultra_runtime.schemas import validate_instance

    ledger = _ledger(module)
    assert ledger.freeze() is ledger
    artifact = ledger.artifact
    validate_instance("ultra-evidence-ledger.schema.json", artifact)
    assert artifact["schema_id"] == "crossframe.ultra.v82.evidence-ledger"
    assert artifact["phase_id"] == "U3"
    assert artifact["content_sha256"] == _hash_without(artifact, "content_sha256")
    assert ledger.content_sha256 == artifact["content_sha256"]
    assert ledger.artifact_sha256 == hashlib.sha256(_canonical(artifact)).hexdigest()

    seal = module.validate_evidence_artifact(
        artifact,
        expected_run_id=RUN_ID,
        expected_version_binding=_binding(),
        expected_phase_id="U3",
        expected_evidence_cutoff=STAMP,
    )
    assert seal.content_sha256 == ledger.content_sha256
    assert seal.artifact_sha256 == ledger.artifact_sha256


@pytest.mark.parametrize("mutation", ("self-selected-run", "moved-cutoff"))
def test_resealed_evidence_artifact_cannot_select_its_own_external_authority(mutation):
    import ultra_runtime.evidence as module
    from ultra_runtime.schemas import validate_instance

    ledger = _ledger(module).freeze()
    changed = copy.deepcopy(ledger.artifact)
    if mutation == "self-selected-run":
        changed["run_id"] = "run-evidence-attacker"
    else:
        changed["evidence_cutoff"] = "2026-08-01T00:00:00Z"
    changed["content_sha256"] = _hash_without(changed, "content_sha256")
    validate_instance("ultra-evidence-ledger.schema.json", changed)
    with pytest.raises(module.EvidenceValidationError, match="authority|expected|cutoff|run"):
        module.validate_evidence_artifact(
            changed,
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_phase_id="U3",
            expected_evidence_cutoff=STAMP,
        )


def test_external_evidence_artifact_rejects_semantics_that_would_be_silently_normalized():
    import ultra_runtime.evidence as module
    from ultra_runtime.schemas import validate_instance

    changed = copy.deepcopy(_ledger(module).freeze().artifact)
    user_claim = next(
        entry for entry in changed["entries"] if entry["identity"] == "user-claim"
    )
    user_claim["confidence"] = "high"
    changed["content_sha256"] = _hash_without(changed, "content_sha256")
    validate_instance("ultra-evidence-ledger.schema.json", changed)
    with pytest.raises(module.EvidenceValidationError, match="canonical|normal|confidence"):
        module.validate_evidence_artifact(
            changed,
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_phase_id="U3",
            expected_evidence_cutoff=STAMP,
        )


@pytest.mark.parametrize("duplicate_kind", ("evidence", "unknown"))
def test_external_resealed_evidence_artifact_rejects_duplicate_identifiers(duplicate_kind):
    import ultra_runtime.evidence as module
    from ultra_runtime.schemas import validate_instance

    changed = copy.deepcopy(_ledger(module).freeze().artifact)
    if duplicate_kind == "evidence":
        duplicate = copy.deepcopy(changed["entries"][0])
        duplicate["statement"] = "A distinct statement with the same evidence ID."
        changed["entries"].append(duplicate)
    else:
        duplicate = copy.deepcopy(changed["unknowns"][0])
        duplicate["description"] = "A distinct unknown with the same unknown ID."
        changed["unknowns"].append(duplicate)
    changed["content_sha256"] = _hash_without(changed, "content_sha256")
    validate_instance("ultra-evidence-ledger.schema.json", changed)
    with pytest.raises(module.EvidenceValidationError, match="duplicate"):
        module.validate_evidence_artifact(
            changed,
            expected_run_id=RUN_ID,
            expected_version_binding=_binding(),
            expected_phase_id="U3",
            expected_evidence_cutoff=STAMP,
        )


def test_post_u3_mutation_is_forbidden_and_fork_requires_a_new_run_and_cutoff():
    import ultra_runtime.evidence as module

    ledger = _ledger(module).freeze()
    with pytest.raises(module.EvidenceFrozenError):
        ledger.append(_entry("EV-LATE", "observed"))
    with pytest.raises(module.EvidenceFrozenError):
        ledger.append_unknown(_unknown("UNKNOWN-LATE"))
    with pytest.raises(module.EvidenceValidationError, match="new run_id"):
        ledger.fork(RUN_ID, "2026-08-03T00:00:00Z")
    with pytest.raises(module.EvidenceValidationError, match="new evidence cutoff"):
        ledger.fork("run-evidence-fork", STAMP)

    fork = ledger.fork("run-evidence-fork", "2026-08-03T00:00:00Z")
    assert fork.run_id == "run-evidence-fork"
    assert fork.evidence_cutoff == "2026-08-03T00:00:00Z"
    assert not fork.frozen
    assert fork.entries == ledger.entries
    assert fork.unknowns == ledger.unknowns


def test_same_source_reference_cannot_be_split_by_self_declared_lineage():
    import ultra_runtime.evidence as module

    first = _entry("EV-SAME-A", "reported", "declared-lineage-a")
    second = _entry("EV-SAME-B", "reported", "declared-lineage-b")
    first["source_refs"] = ["shared-primary-report"]
    second["source_refs"] = ["shared-primary-report"]
    ledger = module.EvidenceLedger.from_entries(
        "run-evidence-shared-source",
        STAMP,
        [first, second],
        version_binding=_binding(),
        generated_at=STAMP,
    )
    assert ledger.independent_support_count("claim-1") == 1
