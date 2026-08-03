from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = ROOT / "tests" / "evals" / "ultra-vs-promax"
BUILDER_PATH = BENCHMARK_ROOT / "build_results.py"
FORWARD_ROOT = ROOT / "tests" / "evals" / "ultra-forward"
REGISTRY_PATH = FORWARD_ROOT / "forecast-registry.jsonl"
RESOLUTIONS_PATH = FORWARD_ROOT / "resolutions.jsonl"
README_PATH = FORWARD_ROOT / "README.md"

DOMAINS = ("public", "organization", "business-tech", "personal", "history")
HORIZONS = ("short", "medium", "long")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_builder():
    assert BUILDER_PATH.is_file(), "Task 16 results builder does not exist"
    spec = importlib.util.spec_from_file_location(
        "ultra_forward_build_results",
        BUILDER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
        newline="\n",
    )


def make_forward_records(
    count: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pairs: list[dict[str, object]] = []
    resolutions: list[dict[str, object]] = []
    for index in range(count):
        case_id = f"F{index + 1:03d}"
        indicator_id = f"indicator-{case_id.lower()}"
        products: dict[str, dict[str, object]] = {}
        for product in ("promax", "ultra"):
            ultra = product == "ultra"
            products[product] = {
                "runtime_name": f"crossframe-{product}",
                "forecast_artifact_sha256": sha256_text(
                    f"{case_id}|{product}|artifact"
                ),
                "forecast_record_sha256": sha256_text(
                    f"{case_id}|{product}|record"
                ),
                "forecast_id": f"{case_id.lower()}-{product}",
                "indicator_id": indicator_id,
                "window_start": "2026-01-02T00:00:00Z",
                "window_end": (
                    "2026-02-01T00:00:00Z"
                    if ultra
                    else "2026-01-10T00:00:00Z"
                ),
                "probability_admissible": True,
                "probability": 0.8,
            }
        pair: dict[str, object] = {
            "schema_id": "crossframe.ultra-forward.pair",
            "schema_version": 1,
            "case_id": case_id,
            "domain": DOMAINS[index % len(DOMAINS)],
            "time_horizon": HORIZONS[index % len(HORIZONS)],
            "independence_cluster_id": f"cluster-{index + 1:03d}",
            "model_id": "gpt-5.6-sol",
            "reasoning_effort": "max",
            "frozen_at": "2026-01-01T00:00:00Z",
            "evidence_cutoff": "2026-01-01T00:00:00Z",
            "request_sha256": sha256_text(f"{case_id}|request"),
            "evidence_bundle_sha256": sha256_text(f"{case_id}|evidence"),
            "tool_profile_sha256": sha256_text(f"{case_id}|tools"),
            "products": products,
        }
        resolution_products: dict[str, dict[str, object]] = {}
        for product in ("promax", "ultra"):
            ultra = product == "ultra"
            resolved = ultra or index % 2 == 1
            resolution_products[product] = {
                "forecast_artifact_sha256": products[product][
                    "forecast_artifact_sha256"
                ],
                "forecast_record_sha256": products[product][
                    "forecast_record_sha256"
                ],
                "resolution_event_sha256": sha256_text(
                    f"{case_id}|{product}|resolution"
                ),
                "indicator_id": indicator_id,
                "observed_at": (
                    "2026-01-15T00:00:00Z" if resolved else None
                ),
                "indicator_resolved": resolved,
                "direction_correct": ultra if resolved else None,
                "time_window_covered": ultra if resolved else False,
                "outcome": (
                    "correct"
                    if ultra
                    else "incorrect"
                    if resolved
                    else "indeterminate"
                ),
                "brier_score": (
                    0.04 if ultra else 0.64 if resolved else None
                ),
            }
        resolution: dict[str, object] = {
            "schema_id": "crossframe.ultra-forward.resolution",
            "schema_version": 1,
            "case_id": case_id,
            "original_pair_record_sha256": sha256_json(pair),
            "resolved_at": "2026-02-02T00:00:00Z",
            "products": resolution_products,
        }
        pairs.append(pair)
        resolutions.append(resolution)
    return pairs, resolutions


def test_committed_forward_registries_are_empty_and_not_evaluated() -> None:
    assert REGISTRY_PATH.is_file()
    assert RESOLUTIONS_PATH.is_file()
    assert REGISTRY_PATH.read_bytes() == b""
    assert RESOLUTIONS_PATH.read_bytes() == b""

    builder = load_builder()
    assert builder.evaluate_forward_validation(
        registry_path=REGISTRY_PATH,
        resolutions_path=RESOLUTIONS_PATH,
    ) == {
        "state": "not_evaluated",
        "resolved_independent_cases": 0,
        "domain_count": 0,
        "horizon_count": 0,
        "probability_pair_count": 0,
        "minimum_gate_passed": False,
        "stable_positive_advantage": False,
        "metrics": None,
    }


def test_forward_gate_requires_thirty_independent_cases_five_domains_and_three_horizons(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    pairs, resolutions = make_forward_records(29)
    registry = tmp_path / "forecast-registry.jsonl"
    resolution_path = tmp_path / "resolutions.jsonl"
    write_jsonl(registry, pairs)
    write_jsonl(resolution_path, resolutions)

    result = builder.evaluate_forward_validation(
        registry_path=registry,
        resolutions_path=resolution_path,
        bootstrap_samples=400,
    )
    assert result["resolved_independent_cases"] == 29
    assert result["domain_count"] == 5
    assert result["horizon_count"] == 3
    assert result["minimum_gate_passed"] is False
    assert result["stable_positive_advantage"] is False
    assert result["state"] == "not_evaluated"


def test_forward_validated_requires_stable_positive_paired_cluster_advantage(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    pairs, resolutions = make_forward_records(30)
    registry = tmp_path / "forecast-registry.jsonl"
    resolution_path = tmp_path / "resolutions.jsonl"
    write_jsonl(registry, pairs)
    write_jsonl(resolution_path, resolutions)

    result = builder.evaluate_forward_validation(
        registry_path=registry,
        resolutions_path=resolution_path,
        bootstrap_samples=400,
    )
    assert result["state"] == "forward-validated"
    assert result["resolved_independent_cases"] == 30
    assert result["domain_count"] == 5
    assert result["horizon_count"] == 3
    assert result["probability_pair_count"] == 15
    assert result["minimum_gate_passed"] is True
    assert result["stable_positive_advantage"] is True

    metrics = result["metrics"]
    for metric_name in ("direction", "time_window"):
        metric = metrics[metric_name]
        assert metric["promax"] == 0.0
        assert metric["ultra"] == 1.0
        assert metric["paired_advantage"] == 1.0
        assert metric["cluster_bootstrap_95ci"][0] > 0
    indicator = metrics["declared_indicator"]
    assert indicator["promax"] == 0.5
    assert indicator["ultra"] == 1.0
    assert indicator["paired_advantage"] == 0.5
    assert indicator["cluster_bootstrap_95ci"][0] > 0
    probability = metrics["admissible_probability"]
    assert probability["promax_mean_brier"] == pytest.approx(0.64)
    assert probability["ultra_mean_brier"] == pytest.approx(0.04)
    assert probability["paired_advantage"] == pytest.approx(0.6)
    assert probability["cluster_bootstrap_95ci"][0] > 0


def test_forward_evaluator_rejects_mutated_originals_duplicate_clusters_and_bad_scores(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    pairs, resolutions = make_forward_records(30)
    registry = tmp_path / "forecast-registry.jsonl"
    resolution_path = tmp_path / "resolutions.jsonl"
    write_jsonl(resolution_path, resolutions)

    pairs[0]["domain"] = "mutated-after-resolution"
    write_jsonl(registry, pairs)
    with pytest.raises(
        builder.ForwardValidationError,
        match="original_pair_record_sha256",
    ):
        builder.evaluate_forward_validation(registry, resolution_path)

    pairs, resolutions = make_forward_records(30)
    pairs[1]["independence_cluster_id"] = pairs[0]["independence_cluster_id"]
    resolutions[1]["original_pair_record_sha256"] = sha256_json(pairs[1])
    write_jsonl(registry, pairs)
    write_jsonl(resolution_path, resolutions)
    with pytest.raises(
        builder.ForwardValidationError,
        match="independence_cluster_id",
    ):
        builder.evaluate_forward_validation(registry, resolution_path)

    pairs, resolutions = make_forward_records(30)
    resolutions[0]["products"]["ultra"]["brier_score"] = 0.5
    write_jsonl(registry, pairs)
    write_jsonl(resolution_path, resolutions)
    with pytest.raises(builder.ForwardValidationError, match="Brier"):
        builder.evaluate_forward_validation(registry, resolution_path)


def test_forward_readme_freezes_append_only_no_claim_contract() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    for marker in (
        "append-only",
        "immutable original",
        "at least 30 independent resolved cases",
        "five domains",
        "three time horizons",
        "paired",
        "case-clustered",
        "does not claim forward-validated",
        "forecast-registry.jsonl",
        "resolutions.jsonl",
    ):
        assert marker in text
