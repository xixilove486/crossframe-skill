from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _entry(module, evidence_id, identity, upstream="report-1"):
    return {
        "evidence_id": evidence_id,
        "identity": identity,
        "statement": f"statement-{evidence_id}",
        "source_refs": [upstream],
        "observed_at": "2026-08-01T00:00:00Z" if identity == "observed" else None,
        "confidence": "medium" if identity == "observed" else "unknown",
        "event_date": "2026-07-31",
        "publication_date": "2026-08-01",
        "interest": "none declared",
        "upstream_lineage": [upstream],
        "supported_claim": "claim-1",
        "cannot_prove": "does not prove universal validity",
    }


def test_identity_enum_and_ledger_freeze():
    import ultra_runtime.evidence as module

    assert set(module.EVIDENCE_IDENTITIES) == {
        "observed", "reported", "inferred", "competing", "user-claim",
        "model-candidate", "simulated", "unknown",
    }
    ledger = module.EvidenceLedger("run-evidence-01", "2026-08-02T00:00:00Z")
    ledger.append(_entry(module, "EV-1", "observed"))
    ledger.append(_entry(module, "EV-2", "reported"))
    frozen = ledger.freeze()
    assert frozen.frozen
    with pytest.raises(module.EvidenceFrozenError):
        ledger.append(_entry(module, "EV-LATE", "observed"))


def test_same_upstream_forms_one_independence_cluster_and_weak_identities_do_not_support_fact():
    import ultra_runtime.evidence as module

    entries = [
        _entry(module, "EV-OBS", "observed", "same-report"),
        _entry(module, "EV-REP", "reported", "same-report"),
        _entry(module, "EV-SIM", "simulated", "sim-report"),
        _entry(module, "EV-USER", "user-claim", "user"),
        _entry(module, "EV-UNK", "unknown", "unknown"),
    ]
    ledger = module.EvidenceLedger.from_entries("run-evidence-02", "2026-08-02T00:00:00Z", entries)
    clusters = ledger.independence_clusters()
    assert any({"EV-OBS", "EV-REP"} <= set(cluster) for cluster in clusters)
    assert ledger.independent_support_count("claim-1") == 1
    assert ledger.satisfies_factual_requirement("claim-1", require_observed=True)
    assert ledger.explicit_unknowns
    assert ledger.confidence_for("EV-USER") == "unknown"

    weak_only = module.EvidenceLedger.from_entries(
        "run-evidence-weak",
        "2026-08-02T00:00:00Z",
        [
            _entry(module, "EV-SIM-ONLY", "simulated", "sim"),
            _entry(module, "EV-USER-ONLY", "user-claim", "user"),
            _entry(module, "EV-MODEL-ONLY", "model-candidate", "model"),
            _entry(module, "EV-UNKNOWN-ONLY", "unknown", "unknown"),
        ],
    )
    assert not weak_only.satisfies_factual_requirement("claim-1")


@pytest.mark.parametrize("identity", ["simulated", "user-claim", "model-candidate", "unknown"])
def test_non_observed_identities_cannot_be_promoted_to_observed(identity):
    import ultra_runtime.evidence as module

    entry = _entry(module, "EV-X", identity)
    with pytest.raises(module.EvidenceValidationError):
        module.validate_evidence_entry(entry, factual_requirement=True)


@pytest.mark.parametrize(
    "field",
    [
        "event_date",
        "publication_date",
        "interest",
        "upstream_lineage",
        "supported_claim",
        "cannot_prove",
    ],
)
def test_every_evidence_source_requires_dates_interest_lineage_scope_and_limit(field):
    import ultra_runtime.evidence as module

    entry = _entry(module, "EV-MISSING", "reported")
    del entry[field]
    with pytest.raises(module.EvidenceValidationError):
        module.validate_evidence_entry(entry)


def test_evidence_after_cutoff_is_rejected_and_unknown_stays_explicit():
    import ultra_runtime.evidence as module

    late = _entry(module, "EV-LATE", "observed")
    late["event_date"] = "2026-08-03"
    with pytest.raises(module.EvidenceValidationError):
        module.EvidenceLedger.from_entries(
            "run-evidence-cutoff",
            "2026-08-02T00:00:00Z",
            [late],
        )

    unknown = _entry(module, "EV-UNKNOWN", "unknown", "unknown-source")
    ledger = module.EvidenceLedger.from_entries(
        "run-evidence-unknown",
        "2026-08-02T00:00:00Z",
        [unknown],
    )
    assert tuple(item["evidence_id"] for item in ledger.explicit_unknowns) == (
        "EV-UNKNOWN",
    )


def test_user_claim_cannot_raise_effective_confidence():
    import ultra_runtime.evidence as module

    user_claim = _entry(module, "EV-USER-HIGH", "user-claim", "user")
    user_claim["confidence"] = "high"
    ledger = module.EvidenceLedger.from_entries(
        "run-evidence-user",
        "2026-08-02T00:00:00Z",
        [user_claim],
    )
    assert ledger.confidence_for("EV-USER-HIGH") == "unknown"


def test_fork_creates_new_run_and_preserves_frozen_ledger():
    import ultra_runtime.evidence as module

    ledger = module.EvidenceLedger("run-evidence-03", "2026-08-02T00:00:00Z")
    ledger.append(_entry(module, "EV-1", "observed"))
    ledger.freeze()
    fork = ledger.fork("run-evidence-04", "2026-08-03T00:00:00Z")
    assert fork.run_id == "run-evidence-04"
    assert not fork.frozen
    assert fork.entries == ledger.entries


def test_fork_rejects_reusing_the_current_run_id():
    import ultra_runtime.evidence as module

    ledger = module.EvidenceLedger("run-evidence-same", "2026-08-02T00:00:00Z")
    with pytest.raises(module.EvidenceValidationError, match="new run_id"):
        ledger.fork("run-evidence-same", "2026-08-03T00:00:00Z")


def test_same_source_reference_cannot_be_split_by_self_declared_lineage():
    import ultra_runtime.evidence as module

    first = _entry(module, "EV-SAME-A", "reported", "declared-lineage-a")
    second = _entry(module, "EV-SAME-B", "reported", "declared-lineage-b")
    first["source_refs"] = ["shared-primary-report"]
    second["source_refs"] = ["shared-primary-report"]
    ledger = module.EvidenceLedger.from_entries(
        "run-evidence-shared-source",
        "2026-08-02T00:00:00Z",
        [first, second],
    )

    assert ledger.independent_support_count("claim-1") == 1
