from __future__ import annotations

import argparse
import base64
from collections import Counter
import copy
from datetime import datetime
import hashlib
import importlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import stat
import statistics
import sys
import tempfile
from typing import Mapping, Sequence


BENCHMARK_ID = "crossframe-ultra-vs-promax-24-v1"
PRODUCTS = ("promax", "ultra")
CATEGORIES = (
    "public",
    "organization",
    "business-tech",
    "personal",
    "history",
    "closed-material",
)
DIMENSION_WEIGHTS = {
    "truth_evidence_unknowns": 20,
    "circle_scale_translation_closure": 15,
    "mechanism_causal_chain": 10,
    "three_order_recursion": 15,
    "judgment_rival_reversal": 15,
    "forecast_resolvability": 10,
    "completeness_readability_independence": 15,
}
AUTOMATIC_FAILURES = (
    "severe_factual_error",
    "simulation_as_fact",
    "unsupported_central_verdict",
)
RELEASE_THRESHOLDS = {
    "minimum_ultra_case_wins": 18,
    "minimum_median_score_advantage": 10,
    "no_category_median_regression": True,
    "minimum_ultra_decisive_case_wins": 7,
    "maximum_ultra_simulation_as_fact_cases": 0,
    "maximum_ultra_severe_factual_error_cases": 0,
}
NOT_RUN_RESULTS = {
    "schema_id": "crossframe.ultra-vs-promax.results",
    "schema_version": 1,
    "benchmark_id": BENCHMARK_ID,
    "status": "not_run",
    "product_runs": {"required": 48, "completed": 0},
    "blind_grades": {"required": 72, "completed": 0},
    "benchmark_results": None,
    "release_status": "not_evaluated",
    "prediction_validation_state": "not_evaluated",
    "note": (
        "Deterministic contracts only; no product output, blind grade, score, "
        "winner, threshold result, or forward-validation claim exists yet."
    ),
}
SHA256_HEX = frozenset("0123456789abcdef")


class BenchmarkBuildError(ValueError):
    """Raised before results are changed when benchmark evidence is invalid."""


class ForwardValidationError(ValueError):
    """Raised when paired forward records violate the frozen contract."""


def _reject_link_or_reparse(
    path: Path,
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> os.stat_result | None:
    try:
        result = os.lstat(path)
    except FileNotFoundError:
        return None
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if stat.S_ISLNK(result.st_mode) or (
        getattr(result, "st_file_attributes", 0) & reparse_flag
    ):
        raise error_type(f"{context} must not be a symlink or reparse point: {path}")
    return result


def _reject_path_layers(
    path: Path,
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> None:
    absolute = path.absolute()
    for layer in reversed((absolute, *absolute.parents)):
        _reject_link_or_reparse(
            layer,
            context=context,
            error_type=error_type,
        )


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BenchmarkBuildError(f"value is not canonical JSON: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r} is prohibited")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, context: str, error_type: type[ValueError]) -> object:
    try:
        text = data.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise error_type(f"invalid JSON in {context}: {exc}") from exc


def _load_json(
    path: Path,
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> object:
    _reject_link_or_reparse(path, context=context, error_type=error_type)
    if not path.is_file():
        raise error_type(f"missing {context}: {path}")
    return _decode_json(path.read_bytes(), context, error_type)


def _require_object(
    value: object,
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise error_type(f"{context} must be a JSON object")
    return value


def _require_list(
    value: object,
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> list[object]:
    if not isinstance(value, list):
        raise error_type(f"{context} must be a JSON array")
    return value


def _require_fields(
    value: Mapping[str, object],
    expected: set[str],
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        pieces: list[str] = []
        if missing:
            pieces.append("missing fields: " + ", ".join(missing))
        if unexpected:
            pieces.append("unexpected fields: " + ", ".join(unexpected))
        raise error_type(f"{context} has " + "; ".join(pieces))


def _require_sha256(
    value: object,
    *,
    context: str,
    nullable: bool = False,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> str | None:
    if value is None and nullable:
        return None
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in SHA256_HEX for character in value)
    ):
        raise error_type(f"{context} must be a lowercase SHA-256 hex digest")
    return value


def _require_bool(
    value: object,
    *,
    context: str,
    error_type: type[ValueError] = BenchmarkBuildError,
) -> bool:
    if type(value) is not bool:
        raise error_type(f"{context} must be a boolean")
    return value


def _parse_time(
    value: object,
    *,
    context: str,
    nullable: bool = False,
    error_type: type[ValueError] = ForwardValidationError,
) -> datetime | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise error_type(f"{context} must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise error_type(f"{context} is not an ISO-8601 timestamp") from exc
    return parsed


def _resolve_roots(
    repo_root: Path | str,
    eval_root: Path | str,
) -> tuple[Path, Path]:
    supplied_repo = Path(repo_root).absolute()
    _reject_path_layers(supplied_repo, context="repo root")
    repo = supplied_repo.resolve(strict=True)
    if not repo.is_dir():
        raise BenchmarkBuildError(f"repo root is not a directory: {repo}")
    supplied_eval = Path(eval_root)
    unresolved_evaluation = (
        supplied_eval if supplied_eval.is_absolute() else repo / supplied_eval
    ).absolute()
    _reject_path_layers(unresolved_evaluation, context="evaluation root")
    evaluation = unresolved_evaluation.resolve(strict=True)
    try:
        evaluation.relative_to(repo)
    except ValueError as exc:
        raise BenchmarkBuildError("evaluation root must stay inside repo root") from exc
    if not evaluation.is_dir():
        raise BenchmarkBuildError(
            f"evaluation root must be a real directory: {evaluation}"
        )
    return repo, evaluation


def _repo_path(repo: Path, relative: object, *, context: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise BenchmarkBuildError(f"{context} must be a repo-relative path")
    if "\\" in relative:
        raise BenchmarkBuildError(f"{context} must use forward slashes")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise BenchmarkBuildError(f"{context} is not a canonical repo-relative path")
    candidate = repo.joinpath(*pure.parts)
    current = repo
    _reject_link_or_reparse(current, context=context)
    for part in pure.parts:
        current = current / part
        _reject_link_or_reparse(current, context=context)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(repo)
    except ValueError as exc:
        raise BenchmarkBuildError(f"{context} escapes the repo root") from exc
    return candidate


def tree_sha256(root: Path) -> str:
    _reject_link_or_reparse(root, context="artifact tree")
    if not root.is_dir():
        raise BenchmarkBuildError(f"artifact tree must be a real directory: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        _reject_link_or_reparse(path, context="artifact tree entry")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _expected_bindings(repo: Path, case: Mapping[str, object]) -> dict[str, str]:
    case_id = str(case["id"])
    return {
        "request_sha256": sha256_bytes(
            _repo_path(
                repo,
                case["prompt_path"],
                context=f"pair {case_id} prompt",
            ).read_bytes()
        ),
        "evidence_cutoff_sha256": sha256_bytes(
            _repo_path(
                repo,
                case["evidence_cutoff_path"],
                context=f"pair {case_id} cutoff",
            ).read_bytes()
        ),
        "materials_tree_sha256": tree_sha256(
            _repo_path(
                repo,
                case["materials_dir"],
                context=f"pair {case_id} materials",
            )
        ),
        "privacy_policy_sha256": sha256_bytes(
            _repo_path(
                repo,
                case["privacy_policy_path"],
                context=f"pair {case_id} privacy",
            ).read_bytes()
        ),
    }


def _case_by_id(evaluation: Path, case_id: str) -> dict[str, object]:
    if not isinstance(case_id, str) or not case_id:
        raise BenchmarkBuildError("case_id must be a non-empty string")
    scenarios = _require_list(
        _load_json(evaluation / "scenarios.json", context="scenarios.json"),
        context="scenarios.json",
    )
    matches = [
        _require_object(item, context="scenario")
        for item in scenarios
        if isinstance(item, dict) and item.get("id") == case_id
    ]
    if len(matches) != 1:
        raise BenchmarkBuildError(f"case {case_id} must appear exactly once")
    return matches[0]


def _pair_by_case_id(
    evaluation: Path,
    case_id: str,
) -> tuple[dict[str, object], dict[str, object]]:
    manifest = _require_object(
        _load_json(
            evaluation / "pairing-manifest.json",
            context="pairing-manifest.json",
        ),
        context="pairing-manifest.json",
    )
    pairs = _require_list(manifest.get("pairs"), context="manifest pairs")
    matches = [
        _require_object(item, context=f"pair {case_id}")
        for item in pairs
        if isinstance(item, dict) and item.get("case_id") == case_id
    ]
    if len(matches) != 1:
        raise BenchmarkBuildError(f"pair {case_id} must appear exactly once")
    return manifest, matches[0]


def _validate_source_files(
    *,
    repo: Path,
    case: Mapping[str, object],
    materials: Mapping[str, object],
) -> tuple[Path, list[dict[str, object]]]:
    case_id = str(case["id"])
    materials_dir = _repo_path(
        repo,
        case["materials_dir"],
        context=f"case {case_id} materials directory",
    )
    _reject_link_or_reparse(
        materials_dir,
        context=f"case {case_id} materials directory",
    )
    if not materials_dir.is_dir():
        raise BenchmarkBuildError(
            f"case {case_id} materials directory must be a real directory"
        )
    raw_sources = _require_list(
        materials["source_files"],
        context=f"case {case_id} source files",
    )
    sources: list[dict[str, object]] = []
    declared_paths: set[str] = set()
    for index, raw_source in enumerate(raw_sources):
        source = _require_object(
            raw_source,
            context=f"case {case_id} source {index + 1}",
        )
        _require_fields(
            source,
            {"path", "sha256", "media_type", "license"},
            context=f"case {case_id} source {index + 1}",
        )
        relative = source["path"]
        if not isinstance(relative, str) or not relative or "\\" in relative:
            raise BenchmarkBuildError(
                f"case {case_id} source path must be repo-portable"
            )
        pure = PurePosixPath(relative)
        if (
            pure.is_absolute()
            or any(part in {"", ".", ".."} for part in pure.parts)
            or relative in declared_paths
        ):
            raise BenchmarkBuildError(
                f"case {case_id} source path is unsafe or duplicated"
            )
        declared_paths.add(relative)
        source_path = materials_dir.joinpath(*pure.parts)
        current = materials_dir
        for part in pure.parts:
            current = current / part
            _reject_link_or_reparse(
                current,
                context=f"case {case_id} source path",
            )
        if not source_path.is_file():
            raise BenchmarkBuildError(f"case {case_id} source file is missing")
        _require_sha256(
            source["sha256"],
            context=f"case {case_id} source SHA-256",
        )
        if sha256_bytes(source_path.read_bytes()) != source["sha256"]:
            raise BenchmarkBuildError(
                f"case {case_id} frozen source SHA-256 mismatch"
            )
        if (
            not isinstance(source["media_type"], str)
            or not source["media_type"].strip()
            or not isinstance(source["license"], str)
            or not source["license"].strip()
            or source["license"].strip().lower() in {"unknown", "unreviewed"}
        ):
            raise BenchmarkBuildError(
                f"case {case_id} source license/media review is incomplete"
            )
        sources.append(source)
    source_paths = [str(source["path"]) for source in sources]
    if source_paths != sorted(source_paths):
        raise BenchmarkBuildError(f"case {case_id} source files must be path-sorted")
    if (
        materials["source_count"] != len(sources)
        or type(materials["source_count"]) is not int
    ):
        raise BenchmarkBuildError(f"case {case_id} source_count is invalid")
    if not sources:
        raise BenchmarkBuildError(f"case {case_id} frozen bundle has no sources")
    expected_source_set = sha256_json(sources)
    _require_sha256(
        materials["source_set_sha256"],
        context=f"case {case_id} source set SHA-256",
    )
    if materials["source_set_sha256"] != expected_source_set:
        raise BenchmarkBuildError(f"case {case_id} source set SHA-256 mismatch")
    observed_paths: set[str] = set()
    for path in materials_dir.rglob("*"):
        _reject_link_or_reparse(
            path,
            context=f"case {case_id} materials entry",
        )
        if path.is_file() and path != materials_dir / "manifest.json":
            observed_paths.add(path.relative_to(materials_dir).as_posix())
    if observed_paths != declared_paths:
        raise BenchmarkBuildError(
            f"case {case_id} materials contain undeclared or missing files"
        )
    return materials_dir, sources


def _validate_review_evidence(
    review: Mapping[str, object],
    *,
    case_id: str,
    review_name: str,
    source_set_sha256: str,
    require_passed: bool,
) -> bool:
    status = review.get("status")
    if status not in {"pending", "passed"}:
        raise BenchmarkBuildError(
            f"case {case_id} {review_name} review status is invalid"
        )
    if require_passed and status != "passed":
        raise BenchmarkBuildError(
            f"case {case_id} {review_name} review has not passed"
        )
    _require_sha256(
        review.get("subject_sha256"),
        context=f"case {case_id} {review_name} review subject",
    )
    if review["subject_sha256"] != source_set_sha256:
        raise BenchmarkBuildError(
            f"case {case_id} {review_name} review subject does not match source set"
        )
    passed = status == "passed"
    reviewer_id = review.get("reviewer_id")
    if passed and (not isinstance(reviewer_id, str) or not reviewer_id.strip()):
        raise BenchmarkBuildError(
            f"case {case_id} {review_name} review has no reviewer"
        )
    reviewed_at = review.get("reviewed_at")
    if passed:
        _parse_time(
            reviewed_at,
            context=f"case {case_id} {review_name} reviewed_at",
            error_type=BenchmarkBuildError,
        )
    elif reviewed_at is not None:
        _parse_time(
            reviewed_at,
            context=f"case {case_id} {review_name} reviewed_at",
            error_type=BenchmarkBuildError,
        )
    evidence = _require_list(
        review.get("evidence"),
        context=f"case {case_id} {review_name} review evidence",
    )
    if any(not isinstance(item, str) or not item.strip() for item in evidence):
        raise BenchmarkBuildError(
            f"case {case_id} {review_name} review evidence is invalid"
        )
    if passed and not evidence:
        raise BenchmarkBuildError(
            f"case {case_id} {review_name} review has no evidence"
        )
    return passed


def _validate_reviews(
    *,
    repo: Path,
    case: Mapping[str, object],
    materials: Mapping[str, object],
    sources: Sequence[Mapping[str, object]],
    require_passed: bool,
) -> dict[str, object]:
    case_id = str(case["id"])
    reviews = _require_object(
        materials["reviews"],
        context=f"case {case_id} reviews",
    )
    _require_fields(
        reviews,
        {"license", "privacy", "outcome_leakage"},
        context=f"case {case_id} reviews",
    )
    source_set_sha256 = str(materials["source_set_sha256"])

    license_review = _require_object(
        reviews["license"],
        context=f"case {case_id} license review",
    )
    _require_fields(
        license_review,
        {
            "status",
            "reviewer_id",
            "reviewed_at",
            "subject_sha256",
            "evidence",
            "source_decisions",
        },
        context=f"case {case_id} license review",
    )
    license_passed = _validate_review_evidence(
        license_review,
        case_id=case_id,
        review_name="license",
        source_set_sha256=source_set_sha256,
        require_passed=require_passed,
    )
    decisions = _require_list(
        license_review["source_decisions"],
        context=f"case {case_id} license source decisions",
    )
    decisions_by_path: dict[str, dict[str, object]] = {}
    for index, raw_decision in enumerate(decisions):
        decision = _require_object(
            raw_decision,
            context=f"case {case_id} license source decision {index + 1}",
        )
        _require_fields(
            decision,
            {
                "path",
                "sha256",
                "license",
                "redistribution_allowed",
                "basis",
            },
            context=f"case {case_id} license source decision {index + 1}",
        )
        path = decision["path"]
        if not isinstance(path, str) or path in decisions_by_path:
            raise BenchmarkBuildError(
                f"case {case_id} license source decision is duplicated"
            )
        decisions_by_path[path] = decision
    sources_by_path = {str(source["path"]): source for source in sources}
    if set(decisions_by_path) != set(sources_by_path):
        raise BenchmarkBuildError(
            f"case {case_id} license review must cover every source exactly once"
        )
    for path, source in sources_by_path.items():
        decision = decisions_by_path[path]
        if (
            decision["sha256"] != source["sha256"]
            or decision["license"] != source["license"]
            or type(decision["redistribution_allowed"]) is not bool
            or not isinstance(decision["basis"], str)
            or not decision["basis"].strip()
        ):
            raise BenchmarkBuildError(
                f"case {case_id} license source decision is not bound"
            )
        if license_passed and decision["redistribution_allowed"] is not True:
            raise BenchmarkBuildError(
                f"case {case_id} license review prohibits redistribution"
            )

    privacy_review = _require_object(
        reviews["privacy"],
        context=f"case {case_id} privacy review",
    )
    _require_fields(
        privacy_review,
        {
            "status",
            "reviewer_id",
            "reviewed_at",
            "subject_sha256",
            "evidence",
            "privacy_policy_sha256",
            "sensitive_paths",
            "outbound_safe",
        },
        context=f"case {case_id} privacy review",
    )
    privacy_passed = _validate_review_evidence(
        privacy_review,
        case_id=case_id,
        review_name="privacy",
        source_set_sha256=source_set_sha256,
        require_passed=require_passed,
    )
    privacy_path = _repo_path(
        repo,
        case["privacy_policy_path"],
        context=f"case {case_id} privacy policy",
    )
    _require_sha256(
        privacy_review["privacy_policy_sha256"],
        context=f"case {case_id} reviewed privacy policy",
    )
    sensitive_paths = _require_list(
        privacy_review["sensitive_paths"],
        context=f"case {case_id} sensitive paths",
    )
    if privacy_review["privacy_policy_sha256"] != sha256_bytes(
        privacy_path.read_bytes()
    ):
        raise BenchmarkBuildError(
            f"case {case_id} privacy review policy hash mismatch"
        )
    if type(privacy_review["outbound_safe"]) is not bool:
        raise BenchmarkBuildError(f"case {case_id} privacy outbound_safe is invalid")
    if privacy_passed and (
        sensitive_paths or privacy_review["outbound_safe"] is not True
    ):
        raise BenchmarkBuildError(f"case {case_id} privacy review is not outbound safe")

    leakage_review = _require_object(
        reviews["outcome_leakage"],
        context=f"case {case_id} outcome leakage review",
    )
    _require_fields(
        leakage_review,
        {
            "status",
            "reviewer_id",
            "reviewed_at",
            "subject_sha256",
            "evidence",
            "evidence_cutoff_sha256",
            "expected_pressure_sha256",
            "post_cutoff_paths",
            "outcome_disclosure_paths",
        },
        context=f"case {case_id} outcome leakage review",
    )
    leakage_passed = _validate_review_evidence(
        leakage_review,
        case_id=case_id,
        review_name="outcome leakage",
        source_set_sha256=source_set_sha256,
        require_passed=require_passed,
    )
    cutoff_path = _repo_path(
        repo,
        case["evidence_cutoff_path"],
        context=f"case {case_id} evidence cutoff",
    )
    pressure_path = _repo_path(
        repo,
        case["expected_pressure_path"],
        context=f"case {case_id} expected pressure",
    )
    if (
        leakage_review["evidence_cutoff_sha256"]
        != sha256_bytes(cutoff_path.read_bytes())
        or leakage_review["expected_pressure_sha256"]
        != sha256_bytes(pressure_path.read_bytes())
    ):
        raise BenchmarkBuildError(
            f"case {case_id} outcome leakage review hash mismatch"
        )
    post_cutoff = _require_list(
        leakage_review["post_cutoff_paths"],
        context=f"case {case_id} post-cutoff paths",
    )
    disclosures = _require_list(
        leakage_review["outcome_disclosure_paths"],
        context=f"case {case_id} outcome disclosure paths",
    )
    if leakage_passed and (post_cutoff or disclosures):
        raise BenchmarkBuildError(
            f"case {case_id} outcome leakage review found prohibited paths"
        )
    reviewer_ids = [
        license_review.get("reviewer_id"),
        privacy_review.get("reviewer_id"),
        leakage_review.get("reviewer_id"),
    ]
    if require_passed and len(set(reviewer_ids)) != 3:
        raise BenchmarkBuildError(
            f"case {case_id} reviews require three distinct reviewer IDs"
        )
    return reviews


def _validate_packet_policy(
    *,
    repo: Path,
    case: Mapping[str, object],
    sources: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    case_id = str(case["id"])
    policy_path = _repo_path(
        repo,
        case["privacy_policy_path"],
        context=f"case {case_id} privacy policy",
    )
    policy = _require_object(
        _load_json(policy_path, context=f"case {case_id} privacy policy"),
        context=f"case {case_id} privacy policy",
    )
    _require_fields(
        policy,
        {
            "schema_id",
            "schema_version",
            "case_id",
            "default_deny",
            "product_packet_allowlist",
            "grader_case_packet_allowlist",
            "grader_injected_slots",
            "audit_only_paths",
        },
        context=f"case {case_id} privacy policy",
    )
    if (
        policy["schema_id"] != "crossframe.ultra.benchmark-privacy-policy"
        or policy["schema_version"] != 2
        or policy["case_id"] != case_id
        or policy["default_deny"] is not True
    ):
        raise BenchmarkBuildError(f"case {case_id} default-deny policy is invalid")
    expected_allowlist = [
        case["prompt_path"],
        case["evidence_cutoff_path"],
        *[
            f"{case['materials_dir']}/{source['path']}"
            for source in sources
        ],
    ]
    product_allowlist = _require_list(
        policy["product_packet_allowlist"],
        context=f"case {case_id} product packet allowlist",
    )
    grader_allowlist = _require_list(
        policy["grader_case_packet_allowlist"],
        context=f"case {case_id} grader case packet allowlist",
    )
    audit_only = _require_list(
        policy["audit_only_paths"],
        context=f"case {case_id} audit-only paths",
    )
    expected_audit_only = [
        f"{case['materials_dir']}/manifest.json",
        case["privacy_policy_path"],
        case["expected_pressure_path"],
    ]
    if (
        product_allowlist != expected_allowlist
        or grader_allowlist != expected_allowlist
    ):
        raise BenchmarkBuildError(
            f"case {case_id} default-deny allowlist is not an exact source closure"
        )
    if audit_only != expected_audit_only:
        raise BenchmarkBuildError(f"case {case_id} audit-only path set is invalid")
    if set(product_allowlist) & set(audit_only) or set(grader_allowlist) & set(
        audit_only
    ):
        raise BenchmarkBuildError(
            f"case {case_id} audit-only path leaked into packet allowlist"
        )
    slots = _require_list(
        policy["grader_injected_slots"],
        context=f"case {case_id} grader injected slots",
    )
    if slots != ["rubric", "article-a", "article-b"]:
        raise BenchmarkBuildError(f"case {case_id} grader injected slots are invalid")
    for index, relative in enumerate([*expected_allowlist, *expected_audit_only]):
        path = _repo_path(
            repo,
            relative,
            context=f"case {case_id} packet policy path {index + 1}",
        )
        _reject_link_or_reparse(
            path,
            context=f"case {case_id} packet policy path {index + 1}",
        )
        if not path.is_file():
            raise BenchmarkBuildError(
                f"case {case_id} packet policy path must be a real file"
            )
    return policy


def _validate_case_bundle(
    *,
    repo: Path,
    evaluation: Path,
    case: Mapping[str, object],
    require_frozen: bool,
    manifest_override: Mapping[str, object] | None = None,
    pair_override: Mapping[str, object] | None = None,
    validate_pairing: bool = True,
) -> dict[str, object]:
    raw_case_id = case.get("id")
    if not isinstance(raw_case_id, str) or not raw_case_id:
        raise BenchmarkBuildError("case identity must be a non-empty string")
    case_id = raw_case_id
    required_case_fields = {
        "id",
        "category",
        "question",
        "decisive_pressure",
        "v82_decisive",
        "adversarial_targets",
        "case_dir",
        "prompt_path",
        "evidence_cutoff_path",
        "materials_dir",
        "expected_pressure_path",
        "privacy_policy_path",
    }
    case_fields = set(case)
    if case_fields not in {
        frozenset(required_case_fields),
        frozenset({*required_case_fields, "execution_readiness"}),
    }:
        raise BenchmarkBuildError(f"case {case_id} path contract is incomplete")
    if case["category"] not in CATEGORIES:
        raise BenchmarkBuildError(f"case {case_id} category is invalid")
    targets = _require_list(
        case["adversarial_targets"],
        context=f"case {case_id} adversarial targets",
    )
    if (
        not isinstance(case["question"], str)
        or not case["question"].strip()
        or not isinstance(case["decisive_pressure"], str)
        or not case["decisive_pressure"].strip()
        or type(case["v82_decisive"]) is not bool
        or not targets
        or any(not isinstance(target, str) or not target.strip() for target in targets)
        or len(targets) != len(set(targets))
        or (
            "execution_readiness" in case
            and case["execution_readiness"] != "awaiting-evidence-bundle"
        )
    ):
        raise BenchmarkBuildError(f"case {case_id} scenario metadata is invalid")
    expected_dir = f"tests/evals/ultra-vs-promax/cases/{case_id}"
    expected_paths = {
        "case_dir": expected_dir,
        "prompt_path": f"{expected_dir}/prompt.md",
        "evidence_cutoff_path": f"{expected_dir}/evidence-cutoff.json",
        "materials_dir": f"{expected_dir}/materials",
        "expected_pressure_path": f"{expected_dir}/expected-pressure.json",
        "privacy_policy_path": f"{expected_dir}/privacy-policy.json",
    }
    if any(
        case[field] != expected for field, expected in expected_paths.items()
    ):
        raise BenchmarkBuildError(f"case {case_id} paths are not canonical")
    prompt_path = _repo_path(
        repo,
        case["prompt_path"],
        context=f"case {case_id} prompt",
    )
    if prompt_path.read_bytes() != (str(case["question"]) + "\n").encode("utf-8"):
        raise BenchmarkBuildError(
            f"case {case_id} question does not match the canonical prompt"
        )
    cutoff_path = _repo_path(
        repo,
        case["evidence_cutoff_path"],
        context=f"case {case_id} evidence cutoff",
    )
    cutoff = _require_object(
        _load_json(cutoff_path, context=f"case {case_id} evidence cutoff"),
        context=f"case {case_id} evidence cutoff",
    )
    _require_fields(
        cutoff,
        {
            "schema_id",
            "schema_version",
            "case_id",
            "benchmark_cutoff",
            "temporal_rule",
            "evidence_state",
        },
        context=f"case {case_id} evidence cutoff",
    )
    expected_temporal_rule = (
        "strictly-before-target-event"
        if case["category"] == "history"
        else "not-after-benchmark-cutoff"
    )
    if (
        cutoff["schema_id"] != "crossframe.ultra.benchmark-evidence-cutoff"
        or cutoff["schema_version"] != 1
        or cutoff["case_id"] != case_id
        or cutoff["benchmark_cutoff"] != "2026-08-02T00:00:00Z"
        or cutoff["temporal_rule"] != expected_temporal_rule
        or (require_frozen and cutoff["evidence_state"] != "frozen")
    ):
        raise BenchmarkBuildError(f"case {case_id} evidence cutoff is not frozen")
    materials_dir = _repo_path(
        repo,
        case["materials_dir"],
        context=f"case {case_id} materials directory",
    )
    materials = _require_object(
        _load_json(
            materials_dir / "manifest.json",
            context=f"case {case_id} materials manifest",
        ),
        context=f"case {case_id} materials manifest",
    )
    _require_fields(
        materials,
        {
            "schema_id",
            "schema_version",
            "case_id",
            "bundle_status",
            "retrieval_mode",
            "source_files",
            "source_count",
            "source_set_sha256",
            "reviews",
        },
        context=f"case {case_id} materials manifest",
    )
    expected_retrieval = (
        "prohibited"
        if case["category"] == "closed-material"
        else "frozen-bundle-only"
    )
    if (
        materials["schema_id"]
        != "crossframe.ultra.benchmark-materials-manifest"
        or materials["schema_version"] != 2
        or materials["case_id"] != case_id
        or materials["retrieval_mode"] != expected_retrieval
        or (require_frozen and materials["bundle_status"] != "frozen")
    ):
        raise BenchmarkBuildError(f"case {case_id} materials v2 contract is invalid")
    materials_dir, sources = _validate_source_files(
        repo=repo,
        case=case,
        materials=materials,
    )
    reviews = _validate_reviews(
        repo=repo,
        case=case,
        materials=materials,
        sources=sources,
        require_passed=require_frozen,
    )
    policy = _validate_packet_policy(repo=repo, case=case, sources=sources)
    bundle = {
        "case": case,
        "cutoff": cutoff,
        "materials": materials,
        "materials_dir": materials_dir,
        "sources": sources,
        "reviews": reviews,
        "policy": policy,
    }
    if not validate_pairing:
        return bundle
    if (manifest_override is None) != (pair_override is None):
        raise BenchmarkBuildError("pairing overrides must be supplied together")
    if manifest_override is None:
        manifest, pair = _pair_by_case_id(evaluation, case_id)
    else:
        manifest = _require_object(manifest_override, context="manifest override")
        pair = _require_object(pair_override, context=f"pair {case_id} override")
    if manifest.get("schema_version") != 2:
        raise BenchmarkBuildError(f"case {case_id} requires pairing manifest version 2")
    if pair.get("case_id") != case_id:
        raise BenchmarkBuildError(f"pair {case_id} identity is invalid")
    bindings = _require_object(
        pair.get("bindings"),
        context=f"pair {case_id} bindings",
    )
    _require_fields(
        bindings,
        {
            "request_sha256",
            "evidence_cutoff_sha256",
            "materials_tree_sha256",
            "privacy_policy_sha256",
            "product_packet_sha256",
            "grader_base_packet_sha256",
        },
        context=f"pair {case_id} bindings",
    )
    expected_evidence = _expected_bindings(repo, case)
    observed_evidence = {key: bindings[key] for key in expected_evidence}
    if observed_evidence != expected_evidence:
        raise BenchmarkBuildError(f"pair {case_id} evidence bindings changed")
    for field in ("product_packet_sha256", "grader_base_packet_sha256"):
        value = bindings[field]
        if value is not None:
            _require_sha256(value, context=f"pair {case_id} {field}")
    return {
        **bundle,
        "pair": pair,
        "manifest": manifest,
        "bindings": bindings,
    }


def validate_case_bundle(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
    case_id: str,
    require_frozen: bool = True,
) -> dict[str, object]:
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    bundle = _validate_case_bundle(
        repo=repo,
        evaluation=evaluation,
        case=_case_by_id(evaluation, case_id),
        require_frozen=require_frozen,
        validate_pairing=False,
    )
    materials = _require_object(bundle["materials"], context="materials")
    return {
        "status": "bundle-ready" if require_frozen else "bundle-valid",
        "case_id": case_id,
        "source_count": materials["source_count"],
        "source_set_sha256": materials["source_set_sha256"],
    }


def _packet_file(
    *,
    logical_name: str,
    path: Path,
    media_type: str,
) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "logical_name": logical_name,
        "media_type": media_type,
        "sha256": sha256_bytes(payload),
        "content_base64": base64.b64encode(payload).decode("ascii"),
    }


def _build_product_packet_from_bundle(
    *,
    repo: Path,
    bundle: Mapping[str, object],
) -> dict[str, object]:
    case = _require_object(bundle["case"], context="case")
    case_id = str(case["id"])
    materials_dir = Path(bundle["materials_dir"])
    sources = _require_list(bundle["sources"], context=f"case {case_id} sources")
    files = [
        _packet_file(
            logical_name="prompt",
            path=_repo_path(
                repo,
                case["prompt_path"],
                context=f"case {case_id} product packet prompt",
            ),
            media_type="text/markdown",
        ),
        _packet_file(
            logical_name="evidence-cutoff",
            path=_repo_path(
                repo,
                case["evidence_cutoff_path"],
                context=f"case {case_id} product packet cutoff",
            ),
            media_type="application/json",
        ),
    ]
    for index, raw_source in enumerate(sources, start=1):
        source = _require_object(raw_source, context=f"case {case_id} source")
        files.append(
            _packet_file(
                logical_name=f"material-{index:03d}",
                path=materials_dir.joinpath(*PurePosixPath(str(source["path"])).parts),
                media_type=str(source["media_type"]),
            )
        )
    return {
        "schema_id": "crossframe.benchmark.case-packet",
        "schema_version": 2,
        "case_id": case_id,
        "files": files,
    }


def _grader_rubric_view(rubric: Mapping[str, object]) -> dict[str, object]:
    return {
        "dimension_weights": rubric["dimension_weights"],
        "automatic_case_loss": rubric["automatic_case_loss"],
        "word_count_rewarded": rubric["word_count_rewarded"],
        "penalty_policy": rubric["penalty_policy"],
    }


def _build_grader_base_packet(
    *,
    product_packet: Mapping[str, object],
    rubric: Mapping[str, object],
) -> dict[str, object]:
    return {
        "files": product_packet["files"],
        "rubric": _grader_rubric_view(rubric),
    }


def build_product_packet(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
    case_id: str,
) -> dict[str, object]:
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    bundle = _validate_case_bundle(
        repo=repo,
        evaluation=evaluation,
        case=_case_by_id(evaluation, case_id),
        require_frozen=True,
    )
    packet = _build_product_packet_from_bundle(repo=repo, bundle=bundle)
    bindings = _require_object(bundle["bindings"], context=f"pair {case_id} bindings")
    bound_hash = bindings["product_packet_sha256"]
    if bound_hash is not None and bound_hash != sha256_json(packet):
        raise BenchmarkBuildError(f"case {case_id} product packet hash mismatch")
    return packet


def _build_grader_packet_from_runs(
    *,
    repo: Path,
    pair: Mapping[str, object],
    grader_id: str,
    base_packet: Mapping[str, object],
    product_runs: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    case_id = str(pair["case_id"])
    labels = _require_object(
        pair["blind_labels"],
        context=f"pair {case_id} blind labels",
    )
    articles: dict[str, object] = {}
    for label in ("A", "B"):
        product = str(labels[label])
        run = product_runs[product]
        article_path = _repo_path(
            repo,
            run["article_path"],
            context=f"case {case_id} Article {label}",
        )
        article_bytes = article_path.read_bytes()
        articles[f"article-{label.lower()}"] = {
            "logical_name": f"Article {label}",
            "sha256": sha256_bytes(article_bytes),
            "content_base64": base64.b64encode(article_bytes).decode("ascii"),
        }
    return {
        "files": base_packet["files"],
        "rubric": base_packet["rubric"],
        **articles,
    }


def build_grader_packet(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
    case_id: str,
    grader_id: str,
) -> dict[str, object]:
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    bundle = _validate_case_bundle(
        repo=repo,
        evaluation=evaluation,
        case=_case_by_id(evaluation, case_id),
        require_frozen=True,
    )
    pair = _require_object(bundle["pair"], context=f"pair {case_id}")
    manifest = _require_object(bundle["manifest"], context="manifest")
    if manifest.get("status") not in {"execution-ready", "ready-for-results-build"}:
        raise BenchmarkBuildError(
            f"case {case_id} grader packet requires execution-ready state"
        )
    graders = _require_list(pair["graders"], context=f"pair {case_id} graders")
    if not any(
        isinstance(item, dict) and item.get("grader_id") == grader_id
        for item in graders
    ):
        raise BenchmarkBuildError(f"case {case_id} has no grader {grader_id}")
    product_packet = _build_product_packet_from_bundle(repo=repo, bundle=bundle)
    rubric = _require_object(
        _load_json(evaluation / "rubric.json", context="rubric.json"),
        context="rubric.json",
    )
    base_packet = _build_grader_base_packet(
        product_packet=product_packet,
        rubric=rubric,
    )
    bindings = _require_object(bundle["bindings"], context=f"pair {case_id} bindings")
    if bindings["grader_base_packet_sha256"] != sha256_json(base_packet):
        raise BenchmarkBuildError(f"case {case_id} grader base packet hash mismatch")
    product_runs = {
        product: _validate_product_run(
            repo=repo,
            manifest=manifest,
            pair=pair,
            product=product,
            allowed_pair_statuses={"execution-ready", "completed"},
        )
        for product in PRODUCTS
    }
    return _build_grader_packet_from_runs(
        repo=repo,
        pair=pair,
        grader_id=grader_id,
        base_packet=base_packet,
        product_runs=product_runs,
    )


def _contract(
    repo: Path,
    evaluation: Path,
) -> dict[str, object]:
    scenarios = _require_list(
        _load_json(evaluation / "scenarios.json", context="scenarios.json"),
        context="scenarios.json",
    )
    rubric = _require_object(
        _load_json(evaluation / "rubric.json", context="rubric.json"),
        context="rubric.json",
    )
    manifest = _require_object(
        _load_json(
            evaluation / "pairing-manifest.json",
            context="pairing-manifest.json",
        ),
        context="pairing-manifest.json",
    )
    manifest_version = manifest.get("schema_version")
    if type(manifest_version) is not int or manifest_version not in {1, 2}:
        raise BenchmarkBuildError("pairing-manifest.json schema version is invalid")

    if len(scenarios) != 24:
        raise BenchmarkBuildError("scenarios.json must contain exactly 24 cases")
    case_ids: list[str] = []
    category_counts: Counter[str] = Counter()
    decisive_count = 0
    for index, raw_case in enumerate(scenarios):
        case = _require_object(raw_case, context=f"scenario[{index}]")
        scenario_fields = {
            "id",
            "category",
            "question",
            "decisive_pressure",
            "v82_decisive",
            "adversarial_targets",
            "case_dir",
            "prompt_path",
            "evidence_cutoff_path",
            "materials_dir",
            "expected_pressure_path",
            "privacy_policy_path",
        }
        if manifest_version == 1 or "execution_readiness" in case:
            scenario_fields.add("execution_readiness")
        _require_fields(
            case,
            scenario_fields,
            context=f"scenario[{index}]",
        )
        case_id = case["id"]
        category = case["category"]
        if not isinstance(case_id, str) or not isinstance(category, str):
            raise BenchmarkBuildError(f"scenario[{index}] identity is invalid")
        if (
            "execution_readiness" in case
            and case["execution_readiness"] != "awaiting-evidence-bundle"
        ):
            raise BenchmarkBuildError(
                f"scenario {case_id} legacy execution readiness is invalid"
            )
        case_ids.append(case_id)
        category_counts[category] += 1
        decisive_count += int(
            _require_bool(
                case["v82_decisive"], context=f"scenario {case_id} decisive flag"
            )
        )
        expected_dir = f"tests/evals/ultra-vs-promax/cases/{case_id}"
        expected_paths = {
            "case_dir": expected_dir,
            "prompt_path": f"{expected_dir}/prompt.md",
            "evidence_cutoff_path": f"{expected_dir}/evidence-cutoff.json",
            "materials_dir": f"{expected_dir}/materials",
            "expected_pressure_path": f"{expected_dir}/expected-pressure.json",
            "privacy_policy_path": f"{expected_dir}/privacy-policy.json",
        }
        for field, expected in expected_paths.items():
            if case[field] != expected:
                raise BenchmarkBuildError(
                    f"scenario {case_id} has non-canonical {field}"
                )
        for field in (
            "prompt_path",
            "evidence_cutoff_path",
            "materials_dir",
            "expected_pressure_path",
            "privacy_policy_path",
        ):
            path = _repo_path(repo, case[field], context=f"scenario {case_id} {field}")
            if field == "materials_dir":
                if not path.is_dir():
                    raise BenchmarkBuildError(f"missing materials directory: {path}")
            elif not path.is_file():
                raise BenchmarkBuildError(f"missing case asset: {path}")
    if len(set(case_ids)) != 24:
        raise BenchmarkBuildError("scenario case IDs must be unique")
    if category_counts != Counter({category: 4 for category in CATEGORIES}):
        raise BenchmarkBuildError("benchmark must contain four cases per category")
    if decisive_count != 8:
        raise BenchmarkBuildError("benchmark must contain exactly eight decisive cases")

    _require_fields(
        rubric,
        {
            "schema_id",
            "schema_version",
            "benchmark_id",
            "dimension_weights",
            "grader_count",
            "automatic_case_loss",
            "word_count_rewarded",
            "penalty_policy",
            "score_derivation",
            "release_thresholds",
        },
        context="rubric.json",
    )
    if (
        rubric["schema_id"] != "crossframe.ultra-vs-promax.rubric"
        or rubric["schema_version"] != 1
        or rubric["benchmark_id"] != BENCHMARK_ID
        or rubric["dimension_weights"] != DIMENSION_WEIGHTS
        or rubric["grader_count"] != 3
        or rubric["automatic_case_loss"] != list(AUTOMATIC_FAILURES)
        or rubric["word_count_rewarded"] is not False
        or rubric["release_thresholds"] != RELEASE_THRESHOLDS
    ):
        raise BenchmarkBuildError("rubric.json differs from the frozen rubric")

    _require_fields(
        manifest,
        {
            "schema_id",
            "schema_version",
            "benchmark_id",
            "status",
            "rubric_path",
            "rubric_sha256",
            "product_model",
            "grader_contract",
            "label_randomization",
            "tool_profiles",
            "fallback_allowed",
            "grader_visibility",
            "pairs",
        },
        context="pairing-manifest.json",
    )
    if (
        manifest["schema_id"]
        != "crossframe.ultra-vs-promax.pairing-manifest"
        or manifest["schema_version"] != manifest_version
        or manifest["benchmark_id"] != BENCHMARK_ID
        or manifest["status"]
        not in {"scaffold", "execution-ready", "ready-for-results-build"}
        or manifest["rubric_path"]
        != "tests/evals/ultra-vs-promax/rubric.json"
        or manifest["rubric_sha256"] != sha256_json(rubric)
        or manifest["product_model"]
        != {"model_id": "gpt-5.6-sol", "reasoning_effort": "max"}
        or manifest["grader_contract"]
        != {
            "count": 3,
            "model_id": "gpt-5.6-sol",
            "reasoning_effort": "max",
            "fresh_context_required": True,
            "prior_grades_visible": False,
        }
        or manifest["tool_profiles"]
        != {"frozen-offline": {"network": False, "retrieval": False}}
        or manifest["fallback_allowed"] is not False
    ):
        raise BenchmarkBuildError("pairing-manifest.json header is invalid")
    if manifest_version == 1 and manifest["status"] != "scaffold":
        raise BenchmarkBuildError(
            "pairing manifest version 1 is scaffold-only and cannot execute"
        )
    expected_visibility = {
        "visible": [
            "Article A",
            "Article B",
            "case prompt",
            "case materials",
            "rubric",
        ],
        "hidden": [
            "product names",
            "pairing manifest",
            "runtime internals",
            "directory names",
            "prior grades",
            "expected pressure metadata",
        ],
    }
    if manifest["grader_visibility"] != expected_visibility:
        raise BenchmarkBuildError("grader visibility contract is invalid")

    randomization = _require_object(
        manifest["label_randomization"], context="label randomization"
    )
    _require_fields(
        randomization,
        {"algorithm", "seed", "seed_sha256"},
        context="label randomization",
    )
    seed = randomization["seed"]
    if (
        randomization["algorithm"] != "sha256-sort-balanced-v1"
        or not isinstance(seed, str)
        or not seed
        or randomization["seed_sha256"] != sha256_bytes(seed.encode("utf-8"))
    ):
        raise BenchmarkBuildError("label randomization contract is invalid")
    ranked = sorted(
        case_ids,
        key=lambda case_id: hashlib.sha256(
            f"{seed}|{case_id}".encode("utf-8")
        ).hexdigest(),
    )
    ultra_as_a = set(ranked[:12])

    pairs = _require_list(manifest["pairs"], context="manifest pairs")
    if len(pairs) != 24:
        raise BenchmarkBuildError("pairing manifest must contain 24 pairs")
    normalized_pairs: list[dict[str, object]] = []
    manifest_status = str(manifest["status"])
    expected_pair_status = {
        "scaffold": "pending",
        "execution-ready": "execution-ready",
        "ready-for-results-build": "completed",
    }[manifest_status]
    for index, (raw_case, raw_pair) in enumerate(zip(scenarios, pairs, strict=True)):
        case = _require_object(raw_case, context=f"scenario[{index}]")
        pair = _require_object(raw_pair, context=f"pair[{index}]")
        case_id = str(case["id"])
        _require_fields(
            pair,
            {
                "case_id",
                "category",
                "v82_decisive",
                "status",
                "tool_profile_id",
                "bindings",
                "blind_labels",
                "products",
                "graders",
                "audit_only",
            },
            context=f"pair {case_id}",
        )
        if (
            pair["case_id"] != case_id
            or pair["category"] != case["category"]
            or pair["v82_decisive"] is not case["v82_decisive"]
            or pair["status"] != expected_pair_status
            or pair["tool_profile_id"] != "frozen-offline"
        ):
            raise BenchmarkBuildError(f"pair {case_id} identity is invalid")
        bindings = _require_object(
            pair["bindings"], context=f"pair {case_id} bindings"
        )
        binding_fields = {
            "request_sha256",
            "evidence_cutoff_sha256",
            "materials_tree_sha256",
            "privacy_policy_sha256",
        }
        if manifest_version == 2:
            binding_fields.update(
                {"product_packet_sha256", "grader_base_packet_sha256"}
            )
        _require_fields(
            bindings,
            binding_fields,
            context=f"pair {case_id} bindings",
        )
        expected_bindings = _expected_bindings(repo, case)
        for field, value in expected_bindings.items():
            _require_sha256(bindings[field], context=f"pair {case_id} {field}")
        if {field: bindings[field] for field in expected_bindings} != expected_bindings:
            raise BenchmarkBuildError(f"pair {case_id} evidence bindings changed")
        if manifest_version == 2:
            for field in ("product_packet_sha256", "grader_base_packet_sha256"):
                packet_hash = bindings[field]
                if manifest_status == "scaffold":
                    if packet_hash is not None:
                        raise BenchmarkBuildError(
                            f"scaffold pair {case_id} must not claim {field}"
                        )
                else:
                    _require_sha256(packet_hash, context=f"pair {case_id} {field}")

        expected_labels = (
            {"A": "ultra", "B": "promax"}
            if case_id in ultra_as_a
            else {"A": "promax", "B": "ultra"}
        )
        if pair["blind_labels"] != expected_labels:
            raise BenchmarkBuildError(f"pair {case_id} blind labels are invalid")

        products = _require_object(
            pair["products"], context=f"pair {case_id} products"
        )
        if set(products) != set(PRODUCTS):
            raise BenchmarkBuildError(f"pair {case_id} must bind both products")
        for product in PRODUCTS:
            contract = _require_object(
                products[product], context=f"pair {case_id} {product} contract"
            )
            _require_fields(
                contract,
                {
                    "runtime_name",
                    "framework_version",
                    "status",
                    "fallback_allowed",
                    "skill_tree_sha256",
                    "article_path",
                    "metadata_path",
                },
                context=f"pair {case_id} {product} contract",
            )
            expected_framework = "v8.0" if product == "promax" else "v8.2"
            if (
                contract["runtime_name"] != f"crossframe-{product}"
                or contract["framework_version"] != expected_framework
                or contract["status"] != expected_pair_status
                or contract["fallback_allowed"] is not False
                or contract["article_path"]
                != f"tests/evals/ultra-vs-promax/raw/{case_id}/{product}/article.md"
                or contract["metadata_path"]
                != (
                    "tests/evals/ultra-vs-promax/raw/"
                    f"{case_id}/{product}/run-metadata.json"
                )
            ):
                raise BenchmarkBuildError(
                    f"pair {case_id} {product} runtime contract is invalid"
                )
            skill_hash = contract["skill_tree_sha256"]
            if contract["status"] == "pending" and skill_hash is not None:
                raise BenchmarkBuildError(
                    f"pending pair {case_id} {product} must not claim a skill hash"
                )
            if contract["status"] in {"execution-ready", "completed"}:
                _require_sha256(
                    skill_hash,
                    context=f"pair {case_id} {product} skill_tree_sha256",
                )

        graders = _require_list(
            pair["graders"], context=f"pair {case_id} graders"
        )
        if len(graders) != 3:
            raise BenchmarkBuildError(f"pair {case_id} requires three graders")
        expected_grader_ids = ["grader-1", "grader-2", "grader-3"]
        for grader_index, raw_grader in enumerate(graders):
            grader = _require_object(
                raw_grader,
                context=f"pair {case_id} grader {grader_index + 1}",
            )
            _require_fields(
                grader,
                {"grader_id", "grade_path"},
                context=f"pair {case_id} grader {grader_index + 1}",
            )
            expected_id = expected_grader_ids[grader_index]
            if grader["grader_id"] != expected_id or grader["grade_path"] != (
                f"tests/evals/ultra-vs-promax/raw/{case_id}/grades/"
                f"{expected_id}.json"
            ):
                raise BenchmarkBuildError(
                    f"pair {case_id} grader path contract is invalid"
                )
        if pair["audit_only"] != {
            "expected_pressure_path": case["expected_pressure_path"]
        }:
            raise BenchmarkBuildError(f"pair {case_id} audit-only path is invalid")
        normalized_pairs.append(pair)

    return {
        "scenarios": scenarios,
        "rubric": rubric,
        "manifest": manifest,
        "pairs": normalized_pairs,
        "decisive_count": decisive_count,
        "schema_version": manifest_version,
    }


def validate_scaffold(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
) -> dict[str, object]:
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    contract = _contract(repo, evaluation)
    manifest = _require_object(contract["manifest"], context="manifest")
    if manifest["status"] != "scaffold":
        raise BenchmarkBuildError("validate_scaffold requires scaffold state")
    return {
        "status": "scaffold-valid",
        "case_count": len(contract["scenarios"]),
        "pair_count": len(contract["pairs"]),
        "required_product_runs": 48,
        "required_blind_grades": 72,
        "decisive_case_count": contract["decisive_count"],
    }


def _validated_v2_bundles(
    *,
    repo: Path,
    evaluation: Path,
    contract: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if contract["schema_version"] != 2:
        raise BenchmarkBuildError(
            "execution-ready requires pairing manifest version 2"
        )
    manifest = _require_object(contract["manifest"], context="manifest")
    pairs = _require_list(contract["pairs"], context="pairs")
    pairs_by_case = {
        str(_require_object(item, context="manifest pair")["case_id"]):
        _require_object(item, context="manifest pair")
        for item in pairs
    }
    bundles: dict[str, dict[str, object]] = {}
    for raw_case in _require_list(contract["scenarios"], context="scenarios"):
        case = _require_object(raw_case, context="scenario")
        case_id = str(case["id"])
        bundle = _validate_case_bundle(
            repo=repo,
            evaluation=evaluation,
            case=case,
            require_frozen=True,
            manifest_override=manifest,
            pair_override=pairs_by_case.get(case_id),
        )
        product_packet = _build_product_packet_from_bundle(repo=repo, bundle=bundle)
        rubric = _require_object(contract["rubric"], context="rubric")
        grader_base_packet = _build_grader_base_packet(
            product_packet=product_packet,
            rubric=rubric,
        )
        bindings = _require_object(
            bundle["bindings"],
            context=f"pair {case_id} bindings",
        )
        if manifest["status"] != "scaffold":
            if bindings["product_packet_sha256"] != sha256_json(product_packet):
                raise BenchmarkBuildError(
                    f"case {case_id} product packet hash mismatch"
                )
            if bindings["grader_base_packet_sha256"] != sha256_json(
                grader_base_packet
            ):
                raise BenchmarkBuildError(
                    f"case {case_id} grader base packet hash mismatch"
                )
        bundles[case_id] = {
            **bundle,
            "product_packet": product_packet,
            "grader_base_packet": grader_base_packet,
        }
    return bundles


def _validate_all_product_runs(
    *,
    repo: Path,
    manifest: Mapping[str, object],
    pairs: Sequence[object],
    allowed_pair_statuses: set[str] | frozenset[str],
) -> dict[str, dict[str, dict[str, object]]]:
    runs: dict[str, dict[str, dict[str, object]]] = {}
    seen_run_ids: set[str] = set()
    for raw_pair in pairs:
        pair = _require_object(raw_pair, context="manifest pair")
        case_id = str(pair["case_id"])
        case_runs: dict[str, dict[str, object]] = {}
        for product in PRODUCTS:
            run = _validate_product_run(
                repo=repo,
                manifest=manifest,
                pair=pair,
                product=product,
                allowed_pair_statuses=allowed_pair_statuses,
            )
            _require_unique_context_id(
                seen_run_ids,
                run,
                kind="product",
            )
            case_runs[product] = run
        runs[case_id] = case_runs
    return runs


def _validate_all_grades(
    *,
    repo: Path,
    rubric: Mapping[str, object],
    manifest: Mapping[str, object],
    pairs: Sequence[object],
    bundles: Mapping[str, Mapping[str, object]],
    product_runs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> int:
    grade_count = 0
    seen_run_ids: set[str] = set()
    for raw_pair in pairs:
        pair = _require_object(raw_pair, context="manifest pair")
        case_id = str(pair["case_id"])
        bundle = bundles[case_id]
        base_packet = _require_object(
            bundle["grader_base_packet"],
            context=f"case {case_id} grader base packet",
        )
        graders = _require_list(pair["graders"], context=f"pair {case_id} graders")
        for raw_grader in graders:
            grader = _require_object(
                raw_grader,
                context=f"pair {case_id} grader",
            )
            grader_id = str(grader["grader_id"])
            packet = _build_grader_packet_from_runs(
                repo=repo,
                pair=pair,
                grader_id=grader_id,
                base_packet=base_packet,
                product_runs=product_runs[case_id],
            )
            grade = _validate_grade(
                repo=repo,
                rubric=rubric,
                manifest=manifest,
                pair=pair,
                grader_contract=grader,
                product_runs=product_runs[case_id],
                expected_packet_sha256=sha256_json(packet),
            )
            _require_unique_context_id(
                seen_run_ids,
                grade,
                kind="grade",
            )
            grade_count += 1
    return grade_count


def validate_contract(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
    expected_state: str,
) -> dict[str, object]:
    if expected_state not in {
        "scaffold",
        "execution-ready",
        "ready-for-results-build",
    }:
        raise BenchmarkBuildError(f"unknown expected state {expected_state!r}")
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    contract = _contract(repo, evaluation)
    manifest = _require_object(contract["manifest"], context="manifest")
    if manifest["status"] != expected_state:
        raise BenchmarkBuildError(
            f"contract state {manifest['status']!r} does not match expected "
            f"{expected_state!r}"
        )
    product_run_count = 0
    blind_grade_count = 0
    if contract["schema_version"] == 2:
        bundles = _validated_v2_bundles(
            repo=repo,
            evaluation=evaluation,
            contract=contract,
        )
        if expected_state == "ready-for-results-build":
            pairs = _require_list(contract["pairs"], context="pairs")
            product_runs = _validate_all_product_runs(
                repo=repo,
                manifest=manifest,
                pairs=pairs,
                allowed_pair_statuses=frozenset({"completed"}),
            )
            product_run_count = sum(len(value) for value in product_runs.values())
            blind_grade_count = _validate_all_grades(
                repo=repo,
                rubric=_require_object(contract["rubric"], context="rubric"),
                manifest=manifest,
                pairs=pairs,
                bundles=bundles,
                product_runs=product_runs,
            )
    elif expected_state != "scaffold":
        raise BenchmarkBuildError(
            "execution-ready requires pairing manifest version 2"
        )
    return {
        "state": expected_state,
        "schema_version": contract["schema_version"],
        "case_count": len(_require_list(contract["scenarios"], context="scenarios")),
        "pair_count": len(_require_list(contract["pairs"], context="pairs")),
        "product_run_count": product_run_count,
        "blind_grade_count": blind_grade_count,
    }


def _context_receipt_sha256(
    record: Mapping[str, object],
    fields: Sequence[str],
) -> str:
    return sha256_json({field: record[field] for field in fields})


def _validate_context_identity(
    record: Mapping[str, object],
    *,
    fields: Sequence[str],
    context: str,
) -> str:
    run_id = record["run_id"]
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or run_id != run_id.strip()
    ):
        raise BenchmarkBuildError(f"{context} fresh context run_id is invalid")
    _require_sha256(
        record["receipt_sha256"],
        context=f"{context} fresh context receipt",
    )
    if record["receipt_sha256"] != _context_receipt_sha256(record, fields):
        raise BenchmarkBuildError(
            f"{context} fresh context receipt SHA-256 mismatch"
        )
    return run_id


def _require_unique_context_id(
    seen: set[str],
    run: Mapping[str, object],
    *,
    kind: str,
) -> None:
    run_id = str(run["run_id"])
    if run_id in seen:
        raise BenchmarkBuildError(
            f"duplicate {kind} fresh context run_id: {run_id}"
        )
    seen.add(run_id)


def _validate_product_run(
    *,
    repo: Path,
    manifest: Mapping[str, object],
    pair: Mapping[str, object],
    product: str,
    allowed_pair_statuses: set[str] | frozenset[str] = frozenset({"completed"}),
) -> dict[str, object]:
    case_id = str(pair["case_id"])
    products = _require_object(pair["products"], context=f"pair {case_id} products")
    product_contract = _require_object(
        products[product], context=f"pair {case_id} {product} contract"
    )
    if (
        pair["status"] not in allowed_pair_statuses
        or product_contract["status"] != pair["status"]
    ):
        raise BenchmarkBuildError(
            f"benchmark not ready: missing {product} product run for {case_id}"
        )
    metadata_path = _repo_path(
        repo,
        product_contract["metadata_path"],
        context=f"pair {case_id} {product} metadata path",
    )
    metadata = _require_object(
        _load_json(
            metadata_path,
            context=f"{case_id} {product} run metadata",
        ),
        context=f"{case_id} {product} run metadata",
    )
    _require_fields(
        metadata,
        {
            "schema_id",
            "schema_version",
            "run_id",
            "receipt_sha256",
            "case_id",
            "product",
            "runtime_name",
            "framework_version",
            "model_id",
            "reasoning_effort",
            "fresh_context",
            "tool_profile_id",
            "request_sha256",
            "evidence_cutoff_sha256",
            "materials_tree_sha256",
            "privacy_policy_sha256",
            "packet_sha256",
            "skill_tree_sha256",
            "raw_output_path",
            "raw_output_sha256",
            "artifact_dir",
            "artifact_tree_sha256",
        },
        context=f"{case_id} {product} run metadata",
    )
    model = _require_object(manifest["product_model"], context="product model")
    bindings = _require_object(pair["bindings"], context=f"pair {case_id} bindings")
    expected_values = {
        "schema_id": "crossframe.ultra-vs-promax.product-run",
        "schema_version": 2,
        "case_id": case_id,
        "product": product,
        "runtime_name": product_contract["runtime_name"],
        "framework_version": product_contract["framework_version"],
        "model_id": model["model_id"],
        "reasoning_effort": model["reasoning_effort"],
        "fresh_context": True,
        "tool_profile_id": pair["tool_profile_id"],
        "request_sha256": bindings["request_sha256"],
        "evidence_cutoff_sha256": bindings["evidence_cutoff_sha256"],
        "materials_tree_sha256": bindings["materials_tree_sha256"],
        "privacy_policy_sha256": bindings["privacy_policy_sha256"],
        "packet_sha256": bindings["product_packet_sha256"],
        "skill_tree_sha256": product_contract["skill_tree_sha256"],
        "raw_output_path": product_contract["article_path"],
    }
    for field, expected in expected_values.items():
        if metadata[field] != expected:
            raise BenchmarkBuildError(
                f"{case_id} {product} metadata field {field} is not bound"
            )
    run_id = _validate_context_identity(
        metadata,
        fields=(
            "run_id",
            "case_id",
            "product",
            "runtime_name",
            "model_id",
            "reasoning_effort",
            "packet_sha256",
            "skill_tree_sha256",
        ),
        context=f"{case_id} {product}",
    )
    _require_sha256(
        metadata["raw_output_sha256"],
        context=f"{case_id} {product} raw_output_sha256",
    )
    _require_sha256(
        metadata["artifact_tree_sha256"],
        context=f"{case_id} {product} artifact_tree_sha256",
    )
    article_path = _repo_path(
        repo,
        metadata["raw_output_path"],
        context=f"{case_id} {product} raw output path",
    )
    if not article_path.is_file() or article_path.is_symlink():
        raise BenchmarkBuildError(
            f"missing raw product output for {case_id} {product}: {article_path}"
        )
    actual_raw_hash = sha256_bytes(article_path.read_bytes())
    if actual_raw_hash != metadata["raw_output_sha256"]:
        raise BenchmarkBuildError(
            f"raw output SHA-256 mismatch for {case_id} {product}"
        )
    artifact_dir = _repo_path(
        repo,
        metadata["artifact_dir"],
        context=f"{case_id} {product} artifact directory",
    )
    if tree_sha256(artifact_dir) != metadata["artifact_tree_sha256"]:
        raise BenchmarkBuildError(
            f"artifact tree SHA-256 mismatch for {case_id} {product}"
        )
    return {
        "run_id": run_id,
        "metadata_path": product_contract["metadata_path"],
        "metadata_sha256": sha256_bytes(metadata_path.read_bytes()),
        "article_path": product_contract["article_path"],
        "article_sha256": actual_raw_hash,
        "metadata": metadata,
    }


def _validate_grade(
    *,
    repo: Path,
    rubric: Mapping[str, object],
    manifest: Mapping[str, object],
    pair: Mapping[str, object],
    grader_contract: Mapping[str, object],
    product_runs: Mapping[str, Mapping[str, object]],
    expected_packet_sha256: str,
) -> dict[str, object]:
    case_id = str(pair["case_id"])
    grade_path = _repo_path(
        repo,
        grader_contract["grade_path"],
        context=f"{case_id} {grader_contract['grader_id']} grade path",
    )
    grade = _require_object(
        _load_json(
            grade_path,
            context=f"{case_id} {grader_contract['grader_id']} blind grade",
        ),
        context=f"{case_id} {grader_contract['grader_id']} blind grade",
    )
    _require_fields(
        grade,
        {
            "schema_id",
            "schema_version",
            "run_id",
            "receipt_sha256",
            "case_id",
            "grader_id",
            "model_id",
            "reasoning_effort",
            "fresh_context",
            "prior_grades_visible",
            "rubric_sha256",
            "request_sha256",
            "materials_tree_sha256",
            "article_a_sha256",
            "article_b_sha256",
            "packet_sha256",
            "dimension_scores",
            "dimension_findings",
            "automatic_failures",
            "automatic_failure_findings",
        },
        context=f"{case_id} {grader_contract['grader_id']} blind grade",
    )
    grader_settings = _require_object(
        manifest["grader_contract"], context="grader contract"
    )
    bindings = _require_object(pair["bindings"], context=f"pair {case_id} bindings")
    blind_labels = _require_object(
        pair["blind_labels"], context=f"pair {case_id} blind labels"
    )
    expected_scalars = {
        "schema_id": "crossframe.ultra-vs-promax.blind-grade",
        "schema_version": 2,
        "case_id": case_id,
        "grader_id": grader_contract["grader_id"],
        "model_id": grader_settings["model_id"],
        "reasoning_effort": grader_settings["reasoning_effort"],
        "fresh_context": True,
        "prior_grades_visible": False,
        "rubric_sha256": sha256_json(rubric),
        "request_sha256": bindings["request_sha256"],
        "materials_tree_sha256": bindings["materials_tree_sha256"],
        "article_a_sha256": product_runs[str(blind_labels["A"])]["article_sha256"],
        "article_b_sha256": product_runs[str(blind_labels["B"])]["article_sha256"],
        "packet_sha256": expected_packet_sha256,
    }
    for field, expected in expected_scalars.items():
        if grade[field] != expected:
            raise BenchmarkBuildError(
                f"{case_id} {grader_contract['grader_id']} field {field} is not bound"
            )
    run_id = _validate_context_identity(
        grade,
        fields=(
            "run_id",
            "case_id",
            "grader_id",
            "model_id",
            "reasoning_effort",
            "prior_grades_visible",
            "rubric_sha256",
            "article_a_sha256",
            "article_b_sha256",
            "packet_sha256",
        ),
        context=f"{case_id} {grader_contract['grader_id']}",
    )

    scores = _require_object(
        grade["dimension_scores"], context=f"{case_id} dimension scores"
    )
    findings = _require_object(
        grade["dimension_findings"], context=f"{case_id} dimension findings"
    )
    failures = _require_object(
        grade["automatic_failures"], context=f"{case_id} automatic failures"
    )
    failure_findings = _require_object(
        grade["automatic_failure_findings"],
        context=f"{case_id} automatic failure findings",
    )
    if set(scores) != {"A", "B"} or set(findings) != {"A", "B"}:
        raise BenchmarkBuildError(f"{case_id} grade must score only A and B")
    if set(failures) != {"A", "B"} or set(failure_findings) != {"A", "B"}:
        raise BenchmarkBuildError(f"{case_id} grade failure maps must use A and B")

    label_totals: dict[str, int] = {}
    label_failures: dict[str, dict[str, bool]] = {}
    label_dimension_scores: dict[str, dict[str, int]] = {}
    for label in ("A", "B"):
        label_scores = _require_object(
            scores[label], context=f"{case_id} Article {label} scores"
        )
        label_findings = _require_object(
            findings[label], context=f"{case_id} Article {label} findings"
        )
        label_failure_map = _require_object(
            failures[label], context=f"{case_id} Article {label} failures"
        )
        label_failure_findings = _require_object(
            failure_findings[label],
            context=f"{case_id} Article {label} failure findings",
        )
        if set(label_scores) != set(DIMENSION_WEIGHTS):
            raise BenchmarkBuildError(
                f"{case_id} Article {label} score dimensions are incomplete"
            )
        if set(label_findings) != set(DIMENSION_WEIGHTS):
            raise BenchmarkBuildError(
                f"{case_id} Article {label} finding dimensions are incomplete"
            )
        normalized_scores: dict[str, int] = {}
        for dimension, maximum in DIMENSION_WEIGHTS.items():
            score = label_scores[dimension]
            if type(score) is not int or not 0 <= score <= maximum:
                raise BenchmarkBuildError(
                    f"{case_id} Article {label} score {dimension} is out of range"
                )
            finding = label_findings[dimension]
            if not isinstance(finding, str) or not finding.strip():
                raise BenchmarkBuildError(
                    f"{case_id} Article {label} finding {dimension} is empty"
                )
            normalized_scores[dimension] = score
        if set(label_failure_map) != set(AUTOMATIC_FAILURES):
            raise BenchmarkBuildError(
                f"{case_id} Article {label} automatic failures are incomplete"
            )
        if set(label_failure_findings) != set(AUTOMATIC_FAILURES):
            raise BenchmarkBuildError(
                f"{case_id} Article {label} automatic findings are incomplete"
            )
        normalized_failures: dict[str, bool] = {}
        for flag in AUTOMATIC_FAILURES:
            triggered = _require_bool(
                label_failure_map[flag],
                context=f"{case_id} Article {label} {flag}",
            )
            raw_findings = _require_list(
                label_failure_findings[flag],
                context=f"{case_id} Article {label} {flag} findings",
            )
            if any(not isinstance(item, str) or not item.strip() for item in raw_findings):
                raise BenchmarkBuildError(
                    f"{case_id} Article {label} {flag} findings are invalid"
                )
            if triggered != bool(raw_findings):
                raise BenchmarkBuildError(
                    f"{case_id} Article {label} {flag} finding/flag mismatch"
                )
            normalized_failures[flag] = triggered
        label_totals[label] = sum(normalized_scores.values())
        label_failures[label] = normalized_failures
        label_dimension_scores[label] = normalized_scores

    a_lost = any(label_failures["A"].values())
    b_lost = any(label_failures["B"].values())
    if a_lost != b_lost:
        winning_label = "B" if a_lost else "A"
    elif label_totals["A"] > label_totals["B"]:
        winning_label = "A"
    elif label_totals["B"] > label_totals["A"]:
        winning_label = "B"
    else:
        winning_label = "tie"

    return {
        "run_id": run_id,
        "grader_id": grader_contract["grader_id"],
        "grade_path": grader_contract["grade_path"],
        "grade_sha256": sha256_bytes(grade_path.read_bytes()),
        "label_totals": label_totals,
        "label_dimension_scores": label_dimension_scores,
        "label_failures": label_failures,
        "winning_label": winning_label,
    }


def _median(values: Sequence[int | float]) -> int | float:
    if not values:
        raise BenchmarkBuildError("cannot derive a median from no raw values")
    return statistics.median(values)


def _derive_results(
    *,
    repo: Path,
    evaluation: Path,
    contract: Mapping[str, object],
) -> dict[str, object]:
    manifest = _require_object(contract["manifest"], context="manifest")
    rubric = _require_object(contract["rubric"], context="rubric")
    scenarios = _require_list(contract["scenarios"], context="scenarios")
    pairs = _require_list(contract["pairs"], context="pairs")
    if manifest["status"] != "ready-for-results-build":
        raise BenchmarkBuildError(
            "benchmark not ready: pairing manifest is still a scaffold"
        )
    bundles = _validated_v2_bundles(
        repo=repo,
        evaluation=evaluation,
        contract=contract,
    )

    case_results: list[dict[str, object]] = []
    all_totals: dict[str, list[int | float]] = {product: [] for product in PRODUCTS}
    all_dimensions: dict[str, dict[str, list[int | float]]] = {
        product: {dimension: [] for dimension in DIMENSION_WEIGHTS}
        for product in PRODUCTS
    }
    category_totals: dict[str, dict[str, list[int | float]]] = {
        product: {category: [] for category in CATEGORIES} for product in PRODUCTS
    }
    automatic_case_counts: dict[str, Counter[str]] = {
        product: Counter() for product in PRODUCTS
    }
    seen_product_run_ids: set[str] = set()
    seen_grade_run_ids: set[str] = set()
    for raw_case, raw_pair in zip(scenarios, pairs, strict=True):
        case = _require_object(raw_case, context="scenario")
        pair = _require_object(raw_pair, context=f"pair {case['id']}")
        case_id = str(case["id"])
        product_runs = {
            product: _validate_product_run(
                repo=repo,
                manifest=manifest,
                pair=pair,
                product=product,
            )
            for product in PRODUCTS
        }
        for run in product_runs.values():
            _require_unique_context_id(
                seen_product_run_ids,
                run,
                kind="product",
            )
        graders = _require_list(pair["graders"], context=f"pair {case_id} graders")
        base_packet = _require_object(
            bundles[case_id]["grader_base_packet"],
            context=f"case {case_id} grader base packet",
        )
        grade_results: list[dict[str, object]] = []
        for raw_grader in graders:
            grader = _require_object(
                raw_grader,
                context=f"pair {case_id} grader",
            )
            packet = _build_grader_packet_from_runs(
                repo=repo,
                pair=pair,
                grader_id=str(grader["grader_id"]),
                base_packet=base_packet,
                product_runs=product_runs,
            )
            grade = _validate_grade(
                repo=repo,
                rubric=rubric,
                manifest=manifest,
                pair=pair,
                grader_contract=grader,
                product_runs=product_runs,
                expected_packet_sha256=sha256_json(packet),
            )
            _require_unique_context_id(
                seen_grade_run_ids,
                grade,
                kind="grade",
            )
            grade_results.append(grade)
        blind_labels = _require_object(
            pair["blind_labels"], context=f"pair {case_id} blind labels"
        )
        label_for_product = {
            str(product): str(label) for label, product in blind_labels.items()
        }
        product_totals: dict[str, int | float] = {}
        product_dimensions: dict[str, dict[str, int | float]] = {}
        product_failures: dict[str, dict[str, bool]] = {}
        for product in PRODUCTS:
            label = label_for_product[product]
            totals = [
                int(_require_object(result["label_totals"], context="totals")[label])
                for result in grade_results
            ]
            dimensions = {
                dimension: _median(
                    [
                        int(
                            _require_object(
                                _require_object(
                                    result["label_dimension_scores"],
                                    context="dimension scores",
                                )[label],
                                context=f"Article {label} dimension scores",
                            )[dimension]
                        )
                        for result in grade_results
                    ]
                )
                for dimension in DIMENSION_WEIGHTS
            }
            flags = {
                flag: any(
                    bool(
                        _require_object(
                            _require_object(
                                result["label_failures"], context="failure maps"
                            )[label],
                            context=f"Article {label} failures",
                        )[flag]
                    )
                    for result in grade_results
                )
                for flag in AUTOMATIC_FAILURES
            }
            for flag, triggered in flags.items():
                if triggered:
                    automatic_case_counts[product][flag] += 1
            product_totals[product] = _median(totals)
            product_dimensions[product] = dimensions
            product_failures[product] = flags
            all_totals[product].append(product_totals[product])
            category_totals[product][str(case["category"])].append(
                product_totals[product]
            )
            for dimension, score in dimensions.items():
                all_dimensions[product][dimension].append(score)

        vote_counts: Counter[str] = Counter()
        for result in grade_results:
            winning_label = str(result["winning_label"])
            if winning_label == "tie":
                vote_counts["tie"] += 1
            else:
                vote_counts[str(blind_labels[winning_label])] += 1
        if vote_counts["ultra"] >= 2:
            winner = "ultra"
        elif vote_counts["promax"] >= 2:
            winner = "promax"
        else:
            winner = "tie"

        case_results.append(
            {
                "case_id": case_id,
                "category": case["category"],
                "v82_decisive": case["v82_decisive"],
                "winner": winner,
                "grader_votes": {
                    "promax": vote_counts["promax"],
                    "ultra": vote_counts["ultra"],
                    "tie": vote_counts["tie"],
                },
                "product_scores": product_totals,
                "dimension_scores": product_dimensions,
                "automatic_failures": product_failures,
                "raw_product_refs": {
                    product: {
                        "metadata_path": product_runs[product]["metadata_path"],
                        "metadata_sha256": product_runs[product]["metadata_sha256"],
                        "article_path": product_runs[product]["article_path"],
                        "article_sha256": product_runs[product]["article_sha256"],
                    }
                    for product in PRODUCTS
                },
                "raw_grade_refs": [
                    {
                        "grader_id": result["grader_id"],
                        "path": result["grade_path"],
                        "sha256": result["grade_sha256"],
                    }
                    for result in grade_results
                ],
            }
        )

    ultra_case_wins = sum(case["winner"] == "ultra" for case in case_results)
    promax_case_wins = sum(case["winner"] == "promax" for case in case_results)
    ties = len(case_results) - ultra_case_wins - promax_case_wins
    ultra_decisive_wins = sum(
        case["winner"] == "ultra" and case["v82_decisive"]
        for case in case_results
    )
    median_scores = {product: _median(all_totals[product]) for product in PRODUCTS}
    dimension_medians = {
        product: {
            dimension: _median(all_dimensions[product][dimension])
            for dimension in DIMENSION_WEIGHTS
        }
        for product in PRODUCTS
    }
    category_medians = {
        product: {
            category: _median(category_totals[product][category])
            for category in CATEGORIES
        }
        for product in PRODUCTS
    }
    threshold_results = {
        "minimum_ultra_case_wins": ultra_case_wins
        >= RELEASE_THRESHOLDS["minimum_ultra_case_wins"],
        "minimum_median_score_advantage": (
            median_scores["ultra"] - median_scores["promax"]
            >= RELEASE_THRESHOLDS["minimum_median_score_advantage"]
        ),
        "no_category_median_regression": all(
            category_medians["ultra"][category]
            >= category_medians["promax"][category]
            for category in CATEGORIES
        ),
        "minimum_ultra_decisive_case_wins": ultra_decisive_wins
        >= RELEASE_THRESHOLDS["minimum_ultra_decisive_case_wins"],
        "maximum_ultra_simulation_as_fact_cases": (
            automatic_case_counts["ultra"]["simulation_as_fact"]
            <= RELEASE_THRESHOLDS["maximum_ultra_simulation_as_fact_cases"]
        ),
        "maximum_ultra_severe_factual_error_cases": (
            automatic_case_counts["ultra"]["severe_factual_error"]
            <= RELEASE_THRESHOLDS[
                "maximum_ultra_severe_factual_error_cases"
            ]
        ),
    }
    aggregate = {
        "ultra_case_wins": ultra_case_wins,
        "promax_case_wins": promax_case_wins,
        "ties": ties,
        "ultra_decisive_case_wins": ultra_decisive_wins,
        "median_promax_score": median_scores["promax"],
        "median_ultra_score": median_scores["ultra"],
        "dimension_medians": dimension_medians,
        "category_medians": category_medians,
        "automatic_failure_case_counts": {
            product: {
                flag: automatic_case_counts[product][flag]
                for flag in AUTOMATIC_FAILURES
            }
            for product in PRODUCTS
        },
    }
    return {
        "schema_id": "crossframe.ultra-vs-promax.results",
        "schema_version": 1,
        "benchmark_id": BENCHMARK_ID,
        "status": "complete",
        "product_runs": {"required": 48, "completed": 48},
        "blind_grades": {"required": 72, "completed": 72},
        "benchmark_results": {
            "derivation": "hash-bound-raw-evidence",
            "case_count": 24,
        },
        "cases": case_results,
        "aggregate": aggregate,
        "release_thresholds": RELEASE_THRESHOLDS,
        "threshold_results": threshold_results,
        "release_status": "passed" if all(threshold_results.values()) else "needs_attention",
        "prediction_validation_state": "not_evaluated",
        "build_bindings": {
            "rubric_sha256": sha256_json(rubric),
            "pairing_manifest_sha256": sha256_json(manifest),
        },
    }


def _atomic_write_json(path: Path, value: object) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
    ).encode("utf-8") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise


def _require_not_run_results(evaluation: Path) -> None:
    results = _require_object(
        _load_json(evaluation / "results.json", context="results.json"),
        context="results.json",
    )
    if results != NOT_RUN_RESULTS:
        raise BenchmarkBuildError(
            "state transition requires the exact not_run results placeholder; "
            "hand-authored aggregate data is prohibited"
        )


def _require_pristine_raw_root(evaluation: Path) -> None:
    raw_root = evaluation / "raw"
    _reject_link_or_reparse(raw_root, context="raw evidence root")
    if not raw_root.is_dir():
        raise BenchmarkBuildError("raw evidence root must be a real directory")
    entries = list(raw_root.iterdir())
    for entry in entries:
        _reject_link_or_reparse(entry, context="raw evidence placeholder")
    if (
        len(entries) != 1
        or entries[0].name != ".gitkeep"
        or not entries[0].is_file()
    ):
        raise BenchmarkBuildError(
            "raw evidence root must be empty except for raw/.gitkeep; "
            "preexisting product or grade evidence is prohibited"
        )


def _measure_promax_skill_tree_sha256(repo: Path) -> str:
    skill_root = _repo_path(
        repo,
        "skills/crossframe-promax",
        context="ProMax skill root",
    )
    if not skill_root.is_dir():
        raise BenchmarkBuildError("ProMax skill root is missing")
    digest = hashlib.sha256()
    for path in sorted(skill_root.rglob("*")):
        _reject_link_or_reparse(path, context="ProMax skill tree entry")
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(skill_root).as_posix()
        if relative == "references/.v8-full-source.lock":
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _measure_ultra_skill_tree_sha256(repo: Path) -> str:
    scripts_root = _repo_path(
        repo,
        "skills/crossframe-ultra/scripts",
        context="Ultra runtime scripts root",
    )
    manifest_path = _repo_path(
        repo,
        "skills/crossframe-ultra/references/source-manifest.json",
        context="Ultra source manifest",
    )
    if not scripts_root.is_dir() or not manifest_path.is_file():
        raise BenchmarkBuildError("Ultra measurement authority is missing")
    scripts_text = str(scripts_root)
    inserted = scripts_text not in sys.path
    if inserted:
        sys.path.insert(0, scripts_text)
    try:
        source_integrity = importlib.import_module(
            "ultra_runtime.source_integrity"
        )
    except Exception as exc:
        raise BenchmarkBuildError(
            "Ultra source-integrity runtime could not be loaded"
        ) from exc
    finally:
        if inserted:
            sys.path.remove(scripts_text)
    module_path = Path(str(source_integrity.__file__)).resolve()
    try:
        module_path.relative_to(scripts_root.resolve())
    except ValueError as exc:
        raise BenchmarkBuildError(
            "Ultra source-integrity runtime is not from the fixed skill root"
        ) from exc
    try:
        manifest = source_integrity.load_source_manifest(manifest_path)
        measurement = source_integrity.measure_u1_prerequisites(
            repo,
            manifest=manifest,
        )
    except Exception as exc:
        raise BenchmarkBuildError(
            "Ultra skill-tree measurement failed closed"
        ) from exc
    skill_tree_sha256 = getattr(measurement, "skill_tree_sha256", None)
    if getattr(measurement, "ready", False) is not True or not skill_tree_sha256:
        raise BenchmarkBuildError(
            "Ultra skill-tree measurement is not fresh and ready; "
            "the release manifest may be stale"
        )
    return _require_sha256(
        skill_tree_sha256,
        context="measured Ultra skill tree SHA-256",
    )


def _measure_execution_skill_tree_sha256(repo: Path) -> dict[str, str]:
    return {
        "promax": _measure_promax_skill_tree_sha256(repo),
        "ultra": _measure_ultra_skill_tree_sha256(repo),
    }


def _contract_with_manifest(
    contract: Mapping[str, object],
    manifest: dict[str, object],
) -> dict[str, object]:
    return {
        **contract,
        "schema_version": 2,
        "manifest": manifest,
        "pairs": _require_list(manifest["pairs"], context="manifest pairs"),
    }




def transition_state(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
    target_state: str,
    promax_skill_tree_sha256: str | None = None,
    ultra_skill_tree_sha256: str | None = None,
) -> dict[str, object]:
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    _require_not_run_results(evaluation)
    manifest_path = evaluation / "pairing-manifest.json"
    manifest_before = manifest_path.read_bytes()
    current_manifest = _require_object(
        _load_json(
            manifest_path,
            context="pairing-manifest.json",
        ),
        context="pairing-manifest.json",
    )
    current_state = current_manifest.get("status")
    legal_predecessor = {
        "execution-ready": "scaffold",
        "ready-for-results-build": "execution-ready",
    }
    if target_state not in legal_predecessor:
        raise BenchmarkBuildError(f"unknown target state {target_state!r}")
    if current_state != legal_predecessor[target_state]:
        raise BenchmarkBuildError(
            f"illegal transition {current_state!r} -> {target_state!r}"
        )

    contract = _contract(repo, evaluation)
    candidate = copy.deepcopy(
        _require_object(contract["manifest"], context="manifest")
    )
    scenarios = _require_list(contract["scenarios"], context="scenarios")
    candidate_pairs = _require_list(candidate["pairs"], context="manifest pairs")

    if target_state == "execution-ready":
        candidate["schema_version"] = 2
        for raw_pair in candidate_pairs:
            pair = _require_object(raw_pair, context="manifest pair")
            bindings = _require_object(
                pair["bindings"],
                context=f"pair {pair['case_id']} bindings",
            )
            bindings["product_packet_sha256"] = None
            bindings["grader_base_packet_sha256"] = None
        candidate_contract = _contract_with_manifest(contract, candidate)
        bundles = _validated_v2_bundles(
            repo=repo,
            evaluation=evaluation,
            contract=candidate_contract,
        )
        _require_pristine_raw_root(evaluation)
        asserted_hashes = {
            "promax": _require_sha256(
                promax_skill_tree_sha256,
                context="promax skill tree SHA-256",
            ),
            "ultra": _require_sha256(
                ultra_skill_tree_sha256,
                context="ultra skill tree SHA-256",
            ),
        }
        measured_hashes = _measure_execution_skill_tree_sha256(repo)
        for product in PRODUCTS:
            measured = _require_sha256(
                measured_hashes.get(product),
                context=f"measured {product} skill tree SHA-256",
            )
            if asserted_hashes[product] != measured:
                raise BenchmarkBuildError(
                    f"{product} skill tree SHA-256 assertion does not match "
                    "the measured fixed skill root"
                )
        product_hashes = measured_hashes
        candidate["status"] = "execution-ready"
        for raw_case, raw_pair in zip(scenarios, candidate_pairs, strict=True):
            case = _require_object(raw_case, context="scenario")
            pair = _require_object(raw_pair, context=f"pair {case['id']}")
            case_id = str(case["id"])
            bundle = bundles[case_id]
            pair["status"] = "execution-ready"
            bindings = _require_object(
                pair["bindings"],
                context=f"pair {case_id} bindings",
            )
            bindings.update(_expected_bindings(repo, case))
            bindings["product_packet_sha256"] = sha256_json(
                bundle["product_packet"]
            )
            bindings["grader_base_packet_sha256"] = sha256_json(
                bundle["grader_base_packet"]
            )
            products = _require_object(
                pair["products"], context=f"pair {case_id} products"
            )
            for product in PRODUCTS:
                product_contract = _require_object(
                    products[product],
                    context=f"pair {case_id} {product} contract",
                )
                product_contract["status"] = "execution-ready"
                product_contract["skill_tree_sha256"] = product_hashes[product]
        _validated_v2_bundles(
            repo=repo,
            evaluation=evaluation,
            contract=_contract_with_manifest(contract, candidate),
        )
    else:
        if contract["schema_version"] != 2:
            raise BenchmarkBuildError(
                "ready-for-results-build requires pairing manifest version 2"
            )
        if (
            promax_skill_tree_sha256 is not None
            or ultra_skill_tree_sha256 is not None
        ):
            raise BenchmarkBuildError(
                "skill tree hashes are accepted only for execution-ready"
            )
        bundles = _validated_v2_bundles(
            repo=repo,
            evaluation=evaluation,
            contract=contract,
        )
        current_pairs = _require_list(contract["pairs"], context="pairs")
        manifest = _require_object(contract["manifest"], context="manifest")
        product_runs = _validate_all_product_runs(
            repo=repo,
            manifest=manifest,
            pairs=current_pairs,
            allowed_pair_statuses=frozenset({"execution-ready"}),
        )
        grade_count = _validate_all_grades(
            repo=repo,
            rubric=_require_object(contract["rubric"], context="rubric"),
            manifest=manifest,
            pairs=current_pairs,
            bundles=bundles,
            product_runs=product_runs,
        )
        if sum(len(value) for value in product_runs.values()) != 48:
            raise BenchmarkBuildError("ready-for-results-build requires 48 outputs")
        if grade_count != 72:
            raise BenchmarkBuildError(
                "ready-for-results-build requires 72 fresh blind grades"
            )
        candidate["status"] = "ready-for-results-build"
        for raw_pair in candidate_pairs:
            pair = _require_object(raw_pair, context="manifest pair")
            pair["status"] = "completed"
            products = _require_object(
                pair["products"], context=f"pair {pair['case_id']} products"
            )
            for product in PRODUCTS:
                product_contract = _require_object(
                    products[product],
                    context=f"pair {pair['case_id']} {product} contract",
                )
                product_contract["status"] = "completed"

    if manifest_path.read_bytes() != manifest_before:
        raise BenchmarkBuildError("pairing manifest changed during state validation")
    _atomic_write_json(manifest_path, candidate)

    return {
        "from": current_state,
        "to": target_state,
        "pair_count": 24,
        "results_status": "not_run",
    }


def _resolve_output_path(
    *,
    repo: Path,
    evaluation: Path,
    output_path: Path | str | None,
) -> Path:
    if output_path is None:
        output = evaluation / "results.json"
    else:
        supplied = Path(output_path)
        output = supplied if supplied.is_absolute() else repo / supplied
        output = output.resolve(strict=False)
    canonical_output = (evaluation / "results.json").resolve(strict=False)
    if output != canonical_output:
        raise BenchmarkBuildError(
            "output must be the canonical evaluation results.json path"
        )
    return output


def build_results(
    *,
    repo_root: Path | str,
    eval_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, object]:
    repo, evaluation = _resolve_roots(repo_root, eval_root)
    output = _resolve_output_path(
        repo=repo,
        evaluation=evaluation,
        output_path=output_path,
    )
    existing_results = _require_object(
        _load_json(output, context="results.json"),
        context="results.json",
    )
    contract = _contract(repo, evaluation)
    results = _derive_results(
        repo=repo,
        evaluation=evaluation,
        contract=contract,
    )
    if existing_results != NOT_RUN_RESULTS and existing_results != results:
        raise BenchmarkBuildError(
            "results.json contains hand-authored aggregate data or stale derived data"
        )
    _atomic_write_json(output, results)
    return results


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if path.is_symlink():
        raise ForwardValidationError(f"JSONL registry must not be a symlink: {path}")
    if not path.is_file():
        raise ForwardValidationError(f"missing JSONL registry: {path}")
    records: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(path.read_bytes().splitlines(), start=1):
        if not raw_line.strip():
            raise ForwardValidationError(
                f"blank JSONL record at {path}:{line_number}"
            )
        value = _decode_json(
            raw_line,
            f"{path}:{line_number}",
            ForwardValidationError,
        )
        records.append(
            _require_object(
                value,
                context=f"{path}:{line_number}",
                error_type=ForwardValidationError,
            )
        )
    return records


def _validate_forward_pair(record: Mapping[str, object]) -> dict[str, object]:
    case_id = record.get("case_id")
    context = f"forward pair {case_id}"
    _require_fields(
        record,
        {
            "schema_id",
            "schema_version",
            "case_id",
            "domain",
            "time_horizon",
            "independence_cluster_id",
            "model_id",
            "reasoning_effort",
            "frozen_at",
            "evidence_cutoff",
            "request_sha256",
            "evidence_bundle_sha256",
            "tool_profile_sha256",
            "products",
        },
        context=context,
        error_type=ForwardValidationError,
    )
    if (
        record["schema_id"] != "crossframe.ultra-forward.pair"
        or record["schema_version"] != 1
        or not isinstance(case_id, str)
        or not case_id
        or not isinstance(record["domain"], str)
        or not record["domain"]
        or record["time_horizon"] not in {"short", "medium", "long"}
        or not isinstance(record["independence_cluster_id"], str)
        or not record["independence_cluster_id"]
        or record["model_id"] != "gpt-5.6-sol"
        or record["reasoning_effort"] != "max"
    ):
        raise ForwardValidationError(f"{context} identity is invalid")
    frozen_at = _parse_time(record["frozen_at"], context=f"{context} frozen_at")
    cutoff = _parse_time(
        record["evidence_cutoff"], context=f"{context} evidence_cutoff"
    )
    assert frozen_at is not None and cutoff is not None
    if cutoff > frozen_at:
        raise ForwardValidationError(f"{context} freezes before its evidence cutoff")
    for field in (
        "request_sha256",
        "evidence_bundle_sha256",
        "tool_profile_sha256",
    ):
        _require_sha256(
            record[field],
            context=f"{context} {field}",
            error_type=ForwardValidationError,
        )
    products = _require_object(
        record["products"], context=f"{context} products", error_type=ForwardValidationError
    )
    if set(products) != set(PRODUCTS):
        raise ForwardValidationError(f"{context} must contain both products")
    normalized_products: dict[str, dict[str, object]] = {}
    for product in PRODUCTS:
        raw_product = _require_object(
            products[product],
            context=f"{context} {product}",
            error_type=ForwardValidationError,
        )
        _require_fields(
            raw_product,
            {
                "runtime_name",
                "forecast_artifact_sha256",
                "forecast_record_sha256",
                "forecast_id",
                "indicator_id",
                "window_start",
                "window_end",
                "probability_admissible",
                "probability",
            },
            context=f"{context} {product}",
            error_type=ForwardValidationError,
        )
        if (
            raw_product["runtime_name"] != f"crossframe-{product}"
            or not isinstance(raw_product["forecast_id"], str)
            or not raw_product["forecast_id"]
            or not isinstance(raw_product["indicator_id"], str)
            or not raw_product["indicator_id"]
        ):
            raise ForwardValidationError(f"{context} {product} identity is invalid")
        for field in ("forecast_artifact_sha256", "forecast_record_sha256"):
            _require_sha256(
                raw_product[field],
                context=f"{context} {product} {field}",
                error_type=ForwardValidationError,
            )
        window_start = _parse_time(
            raw_product["window_start"],
            context=f"{context} {product} window_start",
        )
        window_end = _parse_time(
            raw_product["window_end"],
            context=f"{context} {product} window_end",
        )
        assert window_start is not None and window_end is not None
        if not cutoff <= window_start <= window_end:
            raise ForwardValidationError(f"{context} {product} window is invalid")
        admissible = _require_bool(
            raw_product["probability_admissible"],
            context=f"{context} {product} probability_admissible",
            error_type=ForwardValidationError,
        )
        probability = raw_product["probability"]
        if admissible:
            if (
                type(probability) not in {int, float}
                or not math.isfinite(float(probability))
                or not 0 <= float(probability) <= 1
            ):
                raise ForwardValidationError(
                    f"{context} {product} admissible probability is invalid"
                )
        elif probability is not None:
            raise ForwardValidationError(
                f"{context} {product} inadmissible probability must be null"
            )
        normalized_products[product] = raw_product
    return {"record": record, "products": normalized_products}


def _validate_forward_resolution(
    record: Mapping[str, object],
    pair: Mapping[str, object],
) -> dict[str, object]:
    case_id = pair["case_id"]
    context = f"forward resolution {case_id}"
    _require_fields(
        record,
        {
            "schema_id",
            "schema_version",
            "case_id",
            "original_pair_record_sha256",
            "resolved_at",
            "products",
        },
        context=context,
        error_type=ForwardValidationError,
    )
    if (
        record["schema_id"] != "crossframe.ultra-forward.resolution"
        or record["schema_version"] != 1
        or record["case_id"] != case_id
        or record["original_pair_record_sha256"] != sha256_json(pair)
    ):
        raise ForwardValidationError(
            f"{context} original_pair_record_sha256 or identity mismatch"
        )
    _parse_time(record["resolved_at"], context=f"{context} resolved_at")
    resolution_products = _require_object(
        record["products"],
        context=f"{context} products",
        error_type=ForwardValidationError,
    )
    pair_products = _require_object(
        pair["products"],
        context=f"forward pair {case_id} products",
        error_type=ForwardValidationError,
    )
    if set(resolution_products) != set(PRODUCTS):
        raise ForwardValidationError(f"{context} must contain both products")
    normalized: dict[str, dict[str, object]] = {}
    for product in PRODUCTS:
        original = _require_object(
            pair_products[product],
            context=f"forward pair {case_id} {product}",
            error_type=ForwardValidationError,
        )
        resolution = _require_object(
            resolution_products[product],
            context=f"{context} {product}",
            error_type=ForwardValidationError,
        )
        _require_fields(
            resolution,
            {
                "forecast_artifact_sha256",
                "forecast_record_sha256",
                "resolution_event_sha256",
                "indicator_id",
                "observed_at",
                "indicator_resolved",
                "direction_correct",
                "time_window_covered",
                "outcome",
                "brier_score",
            },
            context=f"{context} {product}",
            error_type=ForwardValidationError,
        )
        for field in ("forecast_artifact_sha256", "forecast_record_sha256"):
            if resolution[field] != original[field]:
                raise ForwardValidationError(
                    f"{context} {product} {field} binding mismatch"
                )
        _require_sha256(
            resolution["resolution_event_sha256"],
            context=f"{context} {product} resolution_event_sha256",
            error_type=ForwardValidationError,
        )
        if resolution["indicator_id"] != original["indicator_id"]:
            raise ForwardValidationError(
                f"{context} {product} indicator_id binding mismatch"
            )
        indicator_resolved = _require_bool(
            resolution["indicator_resolved"],
            context=f"{context} {product} indicator_resolved",
            error_type=ForwardValidationError,
        )
        time_covered = _require_bool(
            resolution["time_window_covered"],
            context=f"{context} {product} time_window_covered",
            error_type=ForwardValidationError,
        )
        direction = resolution["direction_correct"]
        observed_at = _parse_time(
            resolution["observed_at"],
            context=f"{context} {product} observed_at",
            nullable=True,
        )
        if not indicator_resolved:
            if (
                observed_at is not None
                or direction is not None
                or time_covered
                or resolution["outcome"] != "indeterminate"
                or resolution["brier_score"] is not None
            ):
                raise ForwardValidationError(
                    f"{context} {product} unresolved outcome mapping is invalid"
                )
        else:
            if type(direction) is not bool or observed_at is None:
                raise ForwardValidationError(
                    f"{context} {product} resolved direction is invalid"
                )
            window_start = _parse_time(
                original["window_start"],
                context=f"forward pair {case_id} {product} window_start",
            )
            window_end = _parse_time(
                original["window_end"],
                context=f"forward pair {case_id} {product} window_end",
            )
            assert window_start is not None and window_end is not None
            expected_time_covered = window_start <= observed_at <= window_end
            if time_covered is not expected_time_covered:
                raise ForwardValidationError(
                    f"{context} {product} time-window coverage mismatch"
                )
            expected_outcome = (
                "incorrect"
                if direction is False
                else "correct"
                if time_covered
                else "partial"
            )
            if resolution["outcome"] != expected_outcome:
                raise ForwardValidationError(
                    f"{context} {product} outcome mapping mismatch"
                )
            if original["probability_admissible"]:
                probability = float(original["probability"])
                binary_outcome = 1.0 if expected_outcome == "correct" else 0.0
                expected_brier = (probability - binary_outcome) ** 2
                actual_brier = resolution["brier_score"]
                if (
                    type(actual_brier) not in {int, float}
                    or not math.isclose(
                        float(actual_brier),
                        expected_brier,
                        rel_tol=0.0,
                        abs_tol=1e-12,
                    )
                ):
                    raise ForwardValidationError(
                        f"{context} {product} Brier score mismatch"
                    )
            elif resolution["brier_score"] is not None:
                raise ForwardValidationError(
                    f"{context} {product} inadmissible probability has a Brier score"
                )
        normalized[product] = resolution
    return normalized


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ForwardValidationError("cannot derive forward metric from no values")
    return sum(values) / len(values)


def _cluster_bootstrap_ci(
    values: Sequence[float],
    *,
    samples: int,
    seed_material: bytes,
) -> list[float]:
    if not values:
        raise ForwardValidationError("cannot bootstrap an empty paired metric")
    seed = int(hashlib.sha256(seed_material).hexdigest()[:16], 16)
    generator = random.Random(seed)
    draws = sorted(
        _mean([values[generator.randrange(len(values))] for _ in values])
        for _ in range(samples)
    )
    lower = draws[math.floor(0.025 * (samples - 1))]
    upper = draws[math.ceil(0.975 * (samples - 1))]
    return [lower, upper]


def evaluate_forward_validation(
    registry_path: Path | str,
    resolutions_path: Path | str,
    *,
    bootstrap_samples: int = 2000,
) -> dict[str, object]:
    if type(bootstrap_samples) is not int or bootstrap_samples < 100:
        raise ForwardValidationError("bootstrap_samples must be an integer >= 100")
    registry = _load_jsonl(Path(registry_path))
    resolutions = _load_jsonl(Path(resolutions_path))
    if not registry and not resolutions:
        return {
            "state": "not_evaluated",
            "resolved_independent_cases": 0,
            "domain_count": 0,
            "horizon_count": 0,
            "probability_pair_count": 0,
            "minimum_gate_passed": False,
            "stable_positive_advantage": False,
            "metrics": None,
        }
    if len(registry) != len(resolutions):
        raise ForwardValidationError(
            "forward registry and resolutions must contain the same case count"
        )

    pairs_by_case: dict[str, dict[str, object]] = {}
    clusters: set[str] = set()
    for raw_pair in registry:
        validated = _validate_forward_pair(raw_pair)
        case_id = str(raw_pair["case_id"])
        if case_id in pairs_by_case:
            raise ForwardValidationError(f"duplicate forward case_id {case_id}")
        cluster = str(raw_pair["independence_cluster_id"])
        if cluster in clusters:
            raise ForwardValidationError(
                f"duplicate independence_cluster_id {cluster}"
            )
        clusters.add(cluster)
        pairs_by_case[case_id] = validated

    resolutions_by_case: dict[str, dict[str, object]] = {}
    for raw_resolution in resolutions:
        case_id = raw_resolution.get("case_id")
        if not isinstance(case_id, str) or case_id not in pairs_by_case:
            raise ForwardValidationError(
                f"resolution refers to unknown forward case {case_id}"
            )
        if case_id in resolutions_by_case:
            raise ForwardValidationError(f"duplicate resolution case_id {case_id}")
        pair = _require_object(
            pairs_by_case[case_id]["record"],
            context=f"forward pair {case_id}",
            error_type=ForwardValidationError,
        )
        resolutions_by_case[case_id] = _validate_forward_resolution(
            raw_resolution, pair
        )
    if set(resolutions_by_case) != set(pairs_by_case):
        raise ForwardValidationError("missing one or more forward resolutions")

    raw_scores: dict[str, dict[str, list[float]]] = {
        metric: {product: [] for product in PRODUCTS}
        for metric in ("direction", "time_window", "declared_indicator")
    }
    advantages: dict[str, list[float]] = {
        metric: []
        for metric in ("direction", "time_window", "declared_indicator")
    }
    probability_scores: dict[str, list[float]] = {
        product: [] for product in PRODUCTS
    }
    probability_advantages: list[float] = []
    ordered_cases = sorted(pairs_by_case)
    for case_id in ordered_cases:
        product_resolutions = resolutions_by_case[case_id]
        case_scores: dict[str, dict[str, float]] = {}
        for product in PRODUCTS:
            resolution = _require_object(
                product_resolutions[product],
                context=f"forward resolution {case_id} {product}",
                error_type=ForwardValidationError,
            )
            scores = {
                "direction": 1.0 if resolution["direction_correct"] is True else 0.0,
                "time_window": 1.0 if resolution["time_window_covered"] is True else 0.0,
                "declared_indicator": 1.0
                if resolution["indicator_resolved"] is True
                else 0.0,
            }
            case_scores[product] = scores
            for metric, score in scores.items():
                raw_scores[metric][product].append(score)
        for metric in advantages:
            advantages[metric].append(
                case_scores["ultra"][metric] - case_scores["promax"][metric]
            )
        promax_brier = product_resolutions["promax"]["brier_score"]
        ultra_brier = product_resolutions["ultra"]["brier_score"]
        if promax_brier is not None and ultra_brier is not None:
            promax_score = float(promax_brier)
            ultra_score = float(ultra_brier)
            probability_scores["promax"].append(promax_score)
            probability_scores["ultra"].append(ultra_score)
            probability_advantages.append(promax_score - ultra_score)

    seed_material = canonical_json_bytes(
        {"registry": registry, "resolutions": resolutions}
    )
    metrics: dict[str, object] = {}
    lower_bounds: list[float] = []
    for metric in ("direction", "time_window", "declared_indicator"):
        ci = _cluster_bootstrap_ci(
            advantages[metric],
            samples=bootstrap_samples,
            seed_material=seed_material + metric.encode("utf-8"),
        )
        lower_bounds.append(ci[0])
        metrics[metric] = {
            "promax": _mean(raw_scores[metric]["promax"]),
            "ultra": _mean(raw_scores[metric]["ultra"]),
            "paired_advantage": _mean(advantages[metric]),
            "cluster_bootstrap_95ci": ci,
        }
    if probability_advantages:
        probability_ci = _cluster_bootstrap_ci(
            probability_advantages,
            samples=bootstrap_samples,
            seed_material=seed_material + b"admissible_probability",
        )
        lower_bounds.append(probability_ci[0])
        metrics["admissible_probability"] = {
            "promax_mean_brier": _mean(probability_scores["promax"]),
            "ultra_mean_brier": _mean(probability_scores["ultra"]),
            "paired_advantage": _mean(probability_advantages),
            "cluster_bootstrap_95ci": probability_ci,
        }
    else:
        metrics["admissible_probability"] = None

    domains = {str(pair["record"]["domain"]) for pair in pairs_by_case.values()}
    horizons = {
        str(pair["record"]["time_horizon"]) for pair in pairs_by_case.values()
    }
    minimum_gate_passed = (
        len(pairs_by_case) >= 30 and len(domains) >= 5 and len(horizons) >= 3
    )
    stable_positive = (
        minimum_gate_passed
        and bool(probability_advantages)
        and len(lower_bounds) == 4
        and all(lower > 0 for lower in lower_bounds)
    )
    return {
        "state": "forward-validated" if stable_positive else "not_evaluated",
        "resolved_independent_cases": len(pairs_by_case),
        "domain_count": len(domains),
        "horizon_count": len(horizons),
        "probability_pair_count": len(probability_advantages),
        "minimum_gate_passed": minimum_gate_passed,
        "stable_positive_advantage": stable_positive,
        "metrics": metrics,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Derive Ultra-versus-ProMax results from hash-bound raw evidence."
    )
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--eval-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--transition-to",
        choices=("execution-ready", "ready-for-results-build"),
    )
    parser.add_argument("--promax-skill-tree-sha256")
    parser.add_argument("--ultra-skill-tree-sha256")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        repo_root = Path(arguments.repo_root)
        eval_root = Path(arguments.eval_root)
        output = Path(arguments.output)
        if arguments.transition_to is not None:
            repo, evaluation = _resolve_roots(repo_root, eval_root)
            _resolve_output_path(
                repo=repo,
                evaluation=evaluation,
                output_path=output,
            )
            transition = transition_state(
                repo_root=repo,
                eval_root=evaluation,
                target_state=arguments.transition_to,
                promax_skill_tree_sha256=arguments.promax_skill_tree_sha256,
                ultra_skill_tree_sha256=arguments.ultra_skill_tree_sha256,
            )
            print(json.dumps(transition, ensure_ascii=False, sort_keys=True))
            return 0
        if (
            arguments.promax_skill_tree_sha256 is not None
            or arguments.ultra_skill_tree_sha256 is not None
        ):
            raise BenchmarkBuildError(
                "skill tree hashes are accepted only for the execution-ready transition"
            )
        results = build_results(
            repo_root=repo_root,
            eval_root=eval_root,
            output_path=output,
        )
    except BenchmarkBuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": results["status"],
                "product_runs": results["product_runs"],
                "blind_grades": results["blind_grades"],
                "release_status": results["release_status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
