from __future__ import annotations

import copy
from pathlib import Path

from tests.pytest_import_guard import pytest
from tests.test_ultra_semantic_handshake import (
    DIMENSIONS,
    _host_result,
    _issue,
    _layout,
    _module,
    _receipt,
)


def _build_review(tmp_path: Path, *, deterministic_status: str = "pass"):
    semantic_review = _module("semantic_review")
    host_handshake = _module("host_handshake")
    constants = _module("constants")
    layout, _ = _layout(tmp_path)
    action = _issue(semantic_review, layout)
    result = _host_result(action)
    accepted = host_handshake.accept_host_result(
        layout,
        action=action,
        receipt=_receipt(action, result),
    )
    review = semantic_review.project_semantic_review_artifact(
        action=action,
        accepted_result=accepted,
        host_result=result,
        version_binding=constants.current_version_binding(),
        generated_at="2026-08-06T12:00:03Z",
        deterministic_status=deterministic_status,
        adversarial_status="pass",
    )
    return semantic_review, action, accepted, result, review


def test_semantic_review_cannot_be_replayed_for_another_article(
    tmp_path: Path,
) -> None:
    runtime, action, accepted, result, review = _build_review(tmp_path)
    changed = copy.deepcopy(review)
    changed["article_sha256"] = "f" * 64
    changed["content_sha256"] = _module(
        "schemas"
    ).compute_artifact_content_sha256(changed)

    with pytest.raises(runtime.SemanticReviewError, match="receipt|authority"):
        runtime.validate_semantic_review(
            changed,
            action=action,
            accepted_result=accepted,
            host_result=result,
            version_binding=action.document["version_binding"],
            expected_deterministic_status="pass",
            expected_adversarial_status="pass",
        )


def test_semantic_review_cannot_override_a_deterministic_failure(
    tmp_path: Path,
) -> None:
    runtime, action, accepted, result, review = _build_review(
        tmp_path,
        deterministic_status="fail",
    )

    assert review["overall_status"] == "fail"
    assert review["publication_allowed"] is False
    forged = copy.deepcopy(review)
    forged["overall_status"] = "pass"
    forged["publication_allowed"] = True
    forged["content_sha256"] = _module(
        "schemas"
    ).compute_artifact_content_sha256(forged)
    with pytest.raises(runtime.SemanticReviewError, match="receipt|authority"):
        runtime.validate_semantic_review(
            forged,
            action=action,
            accepted_result=accepted,
            host_result=result,
            version_binding=action.document["version_binding"],
            expected_deterministic_status="fail",
            expected_adversarial_status="pass",
        )


def test_semantic_review_binds_exact_concept_units_and_execution_identity(
    tmp_path: Path,
) -> None:
    runtime, action, accepted, result, review = _build_review(tmp_path)

    validated = runtime.validate_semantic_review(
        review,
        action=action,
        accepted_result=accepted,
        host_result=result,
        version_binding=action.document["version_binding"],
        expected_deterministic_status="pass",
        expected_adversarial_status="pass",
    )

    assert runtime.SEMANTIC_REVIEW_DIMENSIONS == DIMENSIONS
    assert validated["reviewer"] == result["reviewer"]
    assert validated["required_concept_semantic_unit_ids"] == [
        "SEMANTIC-UNIT-V82-M01",
        "SEMANTIC-UNIT-V82-M02",
    ]
    assert validated["host_receipt_sha256"] == accepted.receipt_sha256
    assert validated["overall_status"] == "pass"
    assert validated["publication_allowed"] is True
