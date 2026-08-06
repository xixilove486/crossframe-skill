from __future__ import annotations

import hashlib
from pathlib import Path
import sys

from tests.pytest_import_guard import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/crossframe-ultra/scripts"
RUN_ID = "run-u3-admission-01"
CUTOFF = "2026-08-05T18:00:00Z"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _entry(
    *,
    evidence_id: str,
    identity: str,
    statement: str,
    source_refs: list[str],
    attribution: dict[str, object],
    event_date: str | None = "2026-08-01",
    publication_date: str | None = "2026-08-02",
) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "identity": identity,
        "statement": statement,
        "source_refs": source_refs,
        "observed_at": None,
        "confidence": "medium" if identity in {"observed", "reported"} else "unknown",
        "event_date": event_date,
        "publication_date": publication_date,
        "interest": "none declared",
        "upstream_lineage": source_refs,
        "supported_claim": "AI adoption may displace some jobs.",
        "cannot_prove": "This entry cannot prove a universal employment outcome.",
        "attribution": attribution,
    }


def _authority(
    module,
    *,
    request_bytes: bytes = "用户说裁员将发生".encode("utf-8"),
    input_inventory: tuple[dict[str, object], ...] = (),
    admitted_sources: dict[str, dict[str, object]] | None = None,
):
    return module.EvidenceAdmissionAuthority(
        run_id=RUN_ID,
        request_bytes=request_bytes,
        input_inventory=input_inventory,
        admitted_sources=admitted_sources or {},
        evidence_cutoff=CUTOFF,
    )


def test_user_claim_requires_exact_request_byte_span() -> None:
    import ultra_runtime.evidence as module

    request_bytes = "用户说裁员将发生".encode("utf-8")
    entry = _entry(
        evidence_id="EV-USER-1",
        identity="user-claim",
        statement="模型新写出的政策判断",
        source_refs=["REQUEST-CLAIM"],
        attribution={
            "origin_kind": "request",
            "origin_ref": "request.bin",
            "content_sha256": _sha256(request_bytes),
            "span": [0, len(request_bytes)],
            "proof_grade": "self-reported",
        },
        event_date=None,
        publication_date=None,
    )

    with pytest.raises(
        module.EvidenceValidationError,
        match="user-claim.*request.*span",
    ):
        module.admit_evidence_candidate(
            entry,
            authority=_authority(module, request_bytes=request_bytes),
        )


def test_user_claim_with_exact_request_byte_span_is_admitted() -> None:
    import ultra_runtime.evidence as module

    prefix = "问题：".encode("utf-8")
    statement = "AI 会改变就业"
    statement_bytes = statement.encode("utf-8")
    request_bytes = prefix + statement_bytes
    entry = _entry(
        evidence_id="EV-USER-EXACT",
        identity="user-claim",
        statement=statement,
        source_refs=["REQUEST-CLAIM"],
        attribution={
            "origin_kind": "request",
            "origin_ref": "request.bin",
            "content_sha256": _sha256(request_bytes),
            "span": [len(prefix), len(request_bytes)],
            "proof_grade": "self-reported",
        },
        event_date=None,
        publication_date=None,
    )

    admitted = module.admit_evidence_candidate(
        entry,
        authority=_authority(module, request_bytes=request_bytes),
    )

    assert admitted["statement"] == statement
    assert admitted["attribution"]["span"] == [len(prefix), len(request_bytes)]


def test_user_claim_material_span_is_checked_against_inventory_bytes() -> None:
    import ultra_runtime.evidence as module

    material_prefix = "材料：".encode("utf-8")
    statement = "部分岗位已减少"
    material_bytes = material_prefix + statement.encode("utf-8")
    material_path = "materials/MAT-0001.txt"
    inventory = (
        {
            "path": material_path,
            "sha256": _sha256(material_bytes),
            "media_type": "text/plain",
            "content_bytes": material_bytes,
        },
    )
    entry = _entry(
        evidence_id="EV-MATERIAL-1",
        identity="user-claim",
        statement=statement,
        source_refs=["MATERIAL-1"],
        attribution={
            "origin_kind": "material",
            "origin_ref": material_path,
            "content_sha256": _sha256(material_bytes),
            "span": [len(material_prefix), len(material_bytes)],
            "proof_grade": "self-reported",
        },
        event_date=None,
        publication_date=None,
    )

    admitted = module.admit_evidence_candidate(
        entry,
        authority=_authority(module, input_inventory=inventory),
    )

    assert admitted["statement"] == statement


def test_unknown_source_dates_remain_null() -> None:
    import ultra_runtime.evidence as module

    source_id = "SRC-U2-1"
    source_content = b"A host-retrieved source with no known publication date."
    source_sha256 = _sha256(source_content)
    admitted_u2_sources = {
        source_id: {
            "source_id": source_id,
            "content_sha256": source_sha256,
            "event_date": None,
            "publication_date": None,
        }
    }
    entry = _entry(
        evidence_id="EV-REPORTED-1",
        identity="reported",
        statement="The retrieved source reports possible job displacement.",
        source_refs=[source_id],
        attribution={
            "origin_kind": "source",
            "origin_ref": source_id,
            "content_sha256": source_sha256,
            "span": None,
            "proof_grade": "host-attested",
        },
        event_date=None,
        publication_date=None,
    )

    admitted = module.admit_evidence_candidate(
        entry,
        authority=_authority(module, admitted_sources=admitted_u2_sources),
    )

    assert admitted["event_date"] is None
    assert admitted["publication_date"] is None


def test_unknown_source_dates_cannot_be_fabricated_during_admission() -> None:
    import ultra_runtime.evidence as module

    source_id = "SRC-U2-UNKNOWN-DATE"
    source_sha256 = _sha256(b"source with unknown dates")
    authority = _authority(
        module,
        admitted_sources={
            source_id: {
                "source_id": source_id,
                "content_sha256": source_sha256,
                "event_date": None,
                "publication_date": None,
            }
        },
    )
    entry = _entry(
        evidence_id="EV-FABRICATED-DATE",
        identity="reported",
        statement="The candidate invents dates absent from the source.",
        source_refs=[source_id],
        attribution={
            "origin_kind": "source",
            "origin_ref": source_id,
            "content_sha256": source_sha256,
            "span": None,
            "proof_grade": "host-attested",
        },
        event_date="2026-08-01",
        publication_date="2026-08-02",
    )

    with pytest.raises(module.EvidenceValidationError, match="source date"):
        module.admit_evidence_candidate(entry, authority=authority)


def test_nullable_dates_and_attribution_freeze_as_a_public_u3_artifact() -> None:
    import ultra_runtime.evidence as module
    from ultra_runtime.schemas import validate_instance

    source_id = "SRC-U2-SCHEMA"
    source_sha256 = _sha256(b"schema source record")
    authority = _authority(
        module,
        admitted_sources={
            source_id: {
                "source_id": source_id,
                "content_sha256": source_sha256,
            }
        },
    )
    admitted = module.admit_evidence_candidate(
        _entry(
            evidence_id="EV-SCHEMA-1",
            identity="reported",
            statement="A source with unknown dates remains admissible.",
            source_refs=[source_id],
            attribution={
                "origin_kind": "source",
                "origin_ref": source_id,
                "content_sha256": source_sha256,
                "span": None,
                "proof_grade": "host-attested",
            },
            event_date=None,
            publication_date=None,
        ),
        authority=authority,
    )
    ledger = module.EvidenceLedger(RUN_ID, CUTOFF, generated_at=CUTOFF)
    ledger.append(admitted)

    artifact = ledger.freeze().artifact

    validate_instance("ultra-evidence-ledger.schema.json", artifact)
    assert artifact["entries"][0]["attribution"] == admitted["attribution"]
    assert artifact["entries"][0]["event_date"] is None
    assert artifact["entries"][0]["publication_date"] is None


def test_reported_evidence_must_reference_an_admitted_source() -> None:
    import ultra_runtime.evidence as module

    statement = "An unadmitted report is presented as factual evidence."
    entry = _entry(
        evidence_id="EV-REPORTED-UNADMITTED",
        identity="reported",
        statement=statement,
        source_refs=["SRC-NOT-ADMITTED"],
        attribution={
            "origin_kind": "source",
            "origin_ref": "SRC-NOT-ADMITTED",
            "content_sha256": _sha256(statement.encode("utf-8")),
            "span": None,
            "proof_grade": "host-attested",
        },
    )

    with pytest.raises(module.EvidenceValidationError, match="admitted source"):
        module.admit_evidence_candidate(entry, authority=_authority(module))


def test_subagent_text_without_admitted_source_is_not_evidence() -> None:
    import ultra_runtime.evidence as module

    statement = "A subagent proposes a causal mechanism without a source."
    candidate = _entry(
        evidence_id="EV-SUBAGENT-1",
        identity="model-candidate",
        statement=statement,
        source_refs=["SRC-NOT-ADMITTED"],
        attribution={
            "origin_kind": "subagent",
            "origin_ref": "SUBAGENT-CANDIDATE-1",
            "content_sha256": _sha256(statement.encode("utf-8")),
            "span": None,
            "proof_grade": "host-attested",
        },
        event_date=None,
        publication_date=None,
    )

    with pytest.raises(module.EvidenceValidationError, match="admitted source"):
        module.admit_evidence_candidate(
            candidate,
            authority=_authority(module),
        )


def test_subagent_candidate_with_admitted_source_refs_is_admitted() -> None:
    import ultra_runtime.evidence as module

    source_id = "SRC-U2-SUBAGENT"
    source_sha256 = _sha256(b"admitted source record")
    statement = "A sourced subagent candidate remains a model candidate."
    candidate = _entry(
        evidence_id="EV-SUBAGENT-ADMITTED",
        identity="model-candidate",
        statement=statement,
        source_refs=[source_id],
        attribution={
            "origin_kind": "subagent",
            "origin_ref": "SUBAGENT-CANDIDATE-2",
            "content_sha256": _sha256(statement.encode("utf-8")),
            "span": None,
            "proof_grade": "host-attested",
        },
        event_date=None,
        publication_date=None,
    )

    admitted = module.admit_evidence_candidate(
        candidate,
        authority=_authority(
            module,
            admitted_sources={
                source_id: {
                    "source_id": source_id,
                    "content_sha256": source_sha256,
                }
            },
        ),
    )

    assert admitted["identity"] == "model-candidate"
    assert admitted["confidence"] == "unknown"


@pytest.mark.parametrize("identity", ("model-candidate", "simulated"))
def test_model_generated_evidence_requires_model_origin(identity: str) -> None:
    import ultra_runtime.evidence as module

    request_bytes = b"model-origin-confusion"
    entry = _entry(
        evidence_id=f"EV-{identity.upper()}",
        identity=identity,
        statement=request_bytes.decode("utf-8"),
        source_refs=["REQUEST-CLAIM"],
        attribution={
            "origin_kind": "request",
            "origin_ref": "request.bin",
            "content_sha256": _sha256(request_bytes),
            "span": [0, len(request_bytes)],
            "proof_grade": "self-reported",
        },
        event_date=None,
        publication_date=None,
    )

    with pytest.raises(module.EvidenceValidationError, match="model origin"):
        module.admit_evidence_candidate(
            entry,
            authority=_authority(module, request_bytes=request_bytes),
        )


def test_simulated_numbers_remain_nonfactual_model_evidence() -> None:
    import ultra_runtime.evidence as module

    statement = "Scenario parameter: displacement rises by 37 percent."
    entry = _entry(
        evidence_id="EV-SIMULATED-1",
        identity="simulated",
        statement=statement,
        source_refs=["MODEL-ULTRA"],
        attribution={
            "origin_kind": "model",
            "origin_ref": "MODEL-ULTRA",
            "content_sha256": _sha256(statement.encode("utf-8")),
            "span": None,
            "proof_grade": "model-generated",
        },
        event_date=None,
        publication_date=None,
    )

    admitted = module.admit_evidence_candidate(entry, authority=_authority(module))

    assert admitted["identity"] == "simulated"
    assert admitted["confidence"] == "unknown"
    with pytest.raises(module.EvidenceValidationError, match="factual"):
        module.validate_evidence_entry(admitted, factual_requirement=True)
