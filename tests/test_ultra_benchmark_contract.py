from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests" / "evals" / "ultra-vs-promax"
RUBRIC_PATH = EVAL_ROOT / "rubric.json"
SCENARIOS_PATH = EVAL_ROOT / "scenarios.json"
PAIRING_PATH = EVAL_ROOT / "pairing-manifest.json"
RESULTS_PATH = EVAL_ROOT / "results.json"
README_PATH = EVAL_ROOT / "README.md"
BUILDER_PATH = EVAL_ROOT / "build_results.py"

FROZEN_CLI = (
    "python -B tests/evals/ultra-vs-promax/build_results.py "
    "--repo-root . --eval-root tests/evals/ultra-vs-promax "
    "--output tests/evals/ultra-vs-promax/results.json"
)
PREPARE_CLI = (
    FROZEN_CLI
    + " --transition-to execution-ready"
    + " --promax-skill-tree-sha256 <64-lowercase-hex>"
    + " --ultra-skill-tree-sha256 <64-lowercase-hex>"
)
SEAL_CLI = FROZEN_CLI + " --transition-to ready-for-results-build"

EXPECTED_WEIGHTS = {
    "truth_evidence_unknowns": 20,
    "circle_scale_translation_closure": 15,
    "mechanism_causal_chain": 10,
    "three_order_recursion": 15,
    "judgment_rival_reversal": 15,
    "forecast_resolvability": 10,
    "completeness_readability_independence": 15,
}

EXPECTED_THRESHOLDS = {
    "minimum_ultra_case_wins": 18,
    "minimum_median_score_advantage": 10,
    "no_category_median_regression": True,
    "minimum_ultra_decisive_case_wins": 7,
    "maximum_ultra_simulation_as_fact_cases": 0,
    "maximum_ultra_severe_factual_error_cases": 0,
}

AUTOMATIC_FAILURES = (
    "severe_factual_error",
    "simulation_as_fact",
    "unsupported_central_verdict",
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        assert not path.is_symlink()
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def load_json(path: Path) -> object:
    assert path.is_file(), f"missing deterministic Task 16 asset: {path.as_posix()}"
    return json.loads(path.read_text(encoding="utf-8"))


def load_builder(*, stub_skill_measurement: bool = True):
    assert BUILDER_PATH.is_file(), "Task 16 results builder does not exist"
    spec = importlib.util.spec_from_file_location(
        "ultra_vs_promax_build_results",
        BUILDER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if stub_skill_measurement:
        module._measure_execution_skill_tree_sha256 = lambda _repo: {
            "promax": "a" * 64,
            "ultra": "b" * 64,
        }
    return module


def canonical_promax_skill_tree_sha256(skill_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(skill_root.rglob("*")):
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


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )




def test_rubric_freezes_weights_blind_grading_and_release_thresholds() -> None:
    rubric = load_json(RUBRIC_PATH)
    assert isinstance(rubric, dict)
    assert rubric["schema_id"] == "crossframe.ultra-vs-promax.rubric"
    assert rubric["schema_version"] == 1
    assert rubric["dimension_weights"] == EXPECTED_WEIGHTS
    assert sum(rubric["dimension_weights"].values()) == 100
    assert rubric["grader_count"] == 3
    assert rubric["automatic_case_loss"] == list(AUTOMATIC_FAILURES)
    assert rubric["release_thresholds"] == EXPECTED_THRESHOLDS
    assert rubric["word_count_rewarded"] is False
    assert "repetition" in rubric["penalty_policy"]
    assert "unsupported detail" in rubric["penalty_policy"]
    assert rubric["score_derivation"] == (
        "build_results.py derives totals, votes, medians, winners, and thresholds "
        "from hash-bound raw grades"
    )


def test_pairing_manifest_is_execution_ready_hash_bound_balanced_and_blind() -> None:
    builder = load_builder(stub_skill_measurement=False)
    summary = builder.validate_contract(
        repo_root=ROOT,
        eval_root=EVAL_ROOT,
        expected_state="execution-ready",
    )
    assert summary == {
        "state": "execution-ready",
        "schema_version": 2,
        "case_count": 24,
        "pair_count": 24,
        "product_run_count": 0,
        "blind_grade_count": 0,
    }

    rubric = load_json(RUBRIC_PATH)
    manifest = load_json(PAIRING_PATH)
    scenarios = load_json(SCENARIOS_PATH)
    assert isinstance(rubric, dict)
    assert isinstance(manifest, dict)
    assert isinstance(scenarios, list)
    assert manifest["schema_id"] == (
        "crossframe.ultra-vs-promax.pairing-manifest"
    )
    assert manifest["schema_version"] == 2
    assert manifest["status"] == "execution-ready"
    assert manifest["rubric_sha256"] == sha256_json(rubric)
    assert manifest["product_model"] == {
        "model_id": "gpt-5.6-sol",
        "reasoning_effort": "max",
    }
    assert manifest["grader_contract"] == {
        "count": 3,
        "model_id": "gpt-5.6-sol",
        "reasoning_effort": "max",
        "fresh_context_required": True,
        "prior_grades_visible": False,
    }

    randomization = manifest["label_randomization"]
    assert randomization["algorithm"] == "sha256-sort-balanced-v1"
    assert randomization["seed_sha256"] == sha256_bytes(
        randomization["seed"].encode("utf-8")
    )
    ranked = sorted(
        (case["id"] for case in scenarios),
        key=lambda case_id: hashlib.sha256(
            f"{randomization['seed']}|{case_id}".encode("utf-8")
        ).hexdigest(),
    )
    ultra_as_a = set(ranked[:12])

    observed_ultra_a: set[str] = set()
    measured_skill_hashes = builder._measure_execution_skill_tree_sha256(ROOT)
    for case, pair in zip(scenarios, manifest["pairs"], strict=True):
        case_id = case["id"]
        assert "execution_readiness" not in case
        assert pair["case_id"] == case_id
        assert pair["tool_profile_id"] == "frozen-offline"
        assert pair["status"] == "execution-ready"
        assert pair["bindings"]["request_sha256"] == sha256_bytes(
            (ROOT / case["prompt_path"]).read_bytes()
        )
        assert pair["bindings"]["evidence_cutoff_sha256"] == sha256_bytes(
            (ROOT / case["evidence_cutoff_path"]).read_bytes()
        )
        assert pair["bindings"]["materials_tree_sha256"] == tree_sha256(
            ROOT / case["materials_dir"]
        )
        assert pair["bindings"]["privacy_policy_sha256"] == sha256_bytes(
            (ROOT / case["privacy_policy_path"]).read_bytes()
        )
        assert set(pair["blind_labels"].values()) == {"promax", "ultra"}
        if pair["blind_labels"]["A"] == "ultra":
            observed_ultra_a.add(case_id)
        assert len(pair["graders"]) == 3
        assert [grader["grader_id"] for grader in pair["graders"]] == [
            "grader-1",
            "grader-2",
            "grader-3",
        ]
        assert len({grader["grade_path"] for grader in pair["graders"]}) == 3
        for binding in ("product_packet_sha256", "grader_base_packet_sha256"):
            value = pair["bindings"][binding]
            assert len(value) == 64
            assert value == value.lower()
            int(value, 16)
        for product in ("promax", "ultra"):
            contract = pair["products"][product]
            assert contract["status"] == "execution-ready"
            assert contract["skill_tree_sha256"] == measured_skill_hashes[product]
            assert contract["fallback_allowed"] is False
            assert contract["article_path"] == (
                f"tests/evals/ultra-vs-promax/raw/{case_id}/{product}/article.md"
            )
            assert contract["metadata_path"] == (
                "tests/evals/ultra-vs-promax/raw/"
                f"{case_id}/{product}/run-metadata.json"
            )
        assert pair["audit_only"]["expected_pressure_path"] == case[
            "expected_pressure_path"
        ]
    assert observed_ultra_a == ultra_as_a
    assert len(observed_ultra_a) == 12
    assert sorted(
        path.relative_to(EVAL_ROOT / "raw").as_posix()
        for path in (EVAL_ROOT / "raw").rglob("*")
        if path.is_file()
    ) == [".gitkeep"]

    assert manifest["grader_visibility"] == {
        "visible": ["Article A", "Article B", "case prompt", "case materials", "rubric"],
        "hidden": [
            "product names",
            "pairing manifest",
            "runtime internals",
            "directory names",
            "prior grades",
            "expected pressure metadata",
        ],
    }


def test_committed_results_is_an_explicit_not_run_placeholder() -> None:
    results = load_json(RESULTS_PATH)
    assert results == {
        "schema_id": "crossframe.ultra-vs-promax.results",
        "schema_version": 1,
        "benchmark_id": "crossframe-ultra-vs-promax-24-v1",
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


def test_builder_refuses_missing_product_runs_without_rewriting_placeholder() -> None:
    builder = load_builder()
    before = RESULTS_PATH.read_bytes()
    with pytest.raises(
        builder.BenchmarkBuildError,
        match="pairing manifest state is 'execution-ready'.*ready-for-results-build",
    ):
        builder.build_results(repo_root=ROOT, eval_root=EVAL_ROOT)
    assert RESULTS_PATH.read_bytes() == before


def test_builder_derives_all_scores_winners_medians_and_thresholds_from_raw_grades(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path)

    results = builder.build_results(repo_root=repo, eval_root=evaluation)

    assert results["status"] == "complete"
    assert results["aggregate"]["ultra_case_wins"] == 24
    assert results["aggregate"]["promax_case_wins"] == 0
    assert results["aggregate"]["ties"] == 0
    assert results["aggregate"]["ultra_decisive_case_wins"] == 8
    assert results["aggregate"]["median_ultra_score"] == 100
    assert results["aggregate"]["median_ultra_score"] - results["aggregate"][
        "median_promax_score"
    ] >= 10
    assert results["release_status"] == "passed"
    assert len(results["cases"]) == 24
    for case in results["cases"]:
        assert case["winner"] == "ultra"
        assert len(case["raw_grade_refs"]) == 3
        assert set(case["product_scores"]) == {"promax", "ultra"}
    assert set(results["aggregate"]["dimension_medians"]) == {
        "promax",
        "ultra",
    }
    assert set(results["aggregate"]["category_medians"]) == {
        "promax",
        "ultra",
    }
    assert json.loads((evaluation / "results.json").read_text("utf-8")) == results


def test_builder_rejects_tampering_and_hand_authored_aggregate_fields(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path)
    article = evaluation / "raw" / "P01" / "ultra" / "article.md"
    article.write_text("tampered\n", encoding="utf-8")
    placeholder = (evaluation / "results.json").read_bytes()
    with pytest.raises(builder.BenchmarkBuildError, match="raw output SHA-256"):
        builder.build_results(repo_root=repo, eval_root=evaluation)
    assert (evaluation / "results.json").read_bytes() == placeholder

    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path / "second")
    grade_path = evaluation / "raw" / "P01" / "grades" / "grader-1.json"
    grade = json.loads(grade_path.read_text("utf-8"))
    grade["total"] = 100
    _write_json(grade_path, grade)
    placeholder = (evaluation / "results.json").read_bytes()
    with pytest.raises(builder.BenchmarkBuildError, match="unexpected fields"):
        builder.build_results(repo_root=repo, eval_root=evaluation)
    assert (evaluation / "results.json").read_bytes() == placeholder


def test_builder_refuses_missing_raw_hashes_and_blind_grades(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path / "hash")
    metadata_path = evaluation / "raw" / "P01" / "ultra" / "run-metadata.json"
    metadata = json.loads(metadata_path.read_text("utf-8"))
    del metadata["raw_output_sha256"]
    _write_json(metadata_path, metadata)
    placeholder = (evaluation / "results.json").read_bytes()
    with pytest.raises(builder.BenchmarkBuildError, match="raw_output_sha256"):
        builder.build_results(repo_root=repo, eval_root=evaluation)
    assert (evaluation / "results.json").read_bytes() == placeholder

    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path / "grade")
    missing_grade = (
        evaluation / "raw" / "P01" / "grades" / "grader-3.json"
    )
    missing_grade.unlink()
    placeholder = (evaluation / "results.json").read_bytes()
    with pytest.raises(builder.BenchmarkBuildError, match="blind grade|missing"):
        builder.build_results(repo_root=repo, eval_root=evaluation)
    assert (evaluation / "results.json").read_bytes() == placeholder


def test_builder_rejects_hand_authored_results_aggregate(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path)
    results_path = evaluation / "results.json"
    hand_authored = json.loads(results_path.read_text("utf-8"))
    hand_authored["aggregate"] = {"ultra_case_wins": 24}
    _write_json(results_path, hand_authored)
    before = results_path.read_bytes()
    with pytest.raises(builder.BenchmarkBuildError, match="hand-authored aggregate"):
        builder.build_results(repo_root=repo, eval_root=evaluation)
    assert results_path.read_bytes() == before


def test_frozen_cli_rebuilds_only_from_complete_hash_bound_raw_evidence(
    tmp_path: Path,
) -> None:
    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path)
    command = [
        sys.executable,
        "-B",
        "tests/evals/ultra-vs-promax/build_results.py",
        "--repo-root",
        ".",
        "--eval-root",
        "tests/evals/ultra-vs-promax",
        "--output",
        "tests/evals/ultra-vs-promax/results.json",
    ]
    completed = subprocess.run(
        command,
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    rebuilt = json.loads((evaluation / "results.json").read_text("utf-8"))
    assert rebuilt["status"] == "complete"
    assert rebuilt["product_runs"] == {"required": 48, "completed": 48}
    assert rebuilt["blind_grades"] == {"required": 72, "completed": 72}


def test_frozen_cli_fails_without_rewriting_the_unrun_placeholder() -> None:
    before = RESULTS_PATH.read_bytes()
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "tests/evals/ultra-vs-promax/build_results.py",
            "--repo-root",
            ".",
            "--eval-root",
            "tests/evals/ultra-vs-promax",
            "--output",
            "tests/evals/ultra-vs-promax/results.json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "pairing manifest state is 'execution-ready'" in completed.stderr
    assert "requires 'ready-for-results-build'" in completed.stderr
    assert RESULTS_PATH.read_bytes() == before


def test_state_machine_seals_inputs_then_completed_pairs_before_results(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_complete_synthetic_eval(
        tmp_path,
        complete_state=False,
    )
    results_before = (evaluation / "results.json").read_bytes()
    manifest_before = (evaluation / "pairing-manifest.json").read_bytes()

    with pytest.raises(builder.BenchmarkBuildError, match="illegal transition"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )
    assert (evaluation / "pairing-manifest.json").read_bytes() == manifest_before
    assert (evaluation / "results.json").read_bytes() == results_before

    execution_ready = builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    assert execution_ready == {
        "from": "scaffold",
        "to": "execution-ready",
        "pair_count": 24,
        "results_status": "not_run",
    }
    manifest = json.loads((evaluation / "pairing-manifest.json").read_text("utf-8"))
    assert manifest["status"] == "execution-ready"
    assert {pair["status"] for pair in manifest["pairs"]} == {"execution-ready"}
    assert {
        contract["status"]
        for pair in manifest["pairs"]
        for contract in pair["products"].values()
    } == {"execution-ready"}
    assert (evaluation / "results.json").read_bytes() == results_before

    assert builder.validate_contract(
        repo_root=repo,
        eval_root=evaluation,
        expected_state="execution-ready",
    ) == {
        "state": "execution-ready",
        "schema_version": 2,
        "case_count": 24,
        "pair_count": 24,
        "product_run_count": 0,
        "blind_grade_count": 0,
    }

    _write_v2_product_runs(builder, repo, evaluation)
    execution_manifest = (evaluation / "pairing-manifest.json").read_bytes()
    with pytest.raises(builder.BenchmarkBuildError, match="blind grade|missing"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )
    assert (evaluation / "pairing-manifest.json").read_bytes() == execution_manifest
    assert (evaluation / "results.json").read_bytes() == results_before
    _write_v2_blind_grades(builder, repo, evaluation)

    completed = builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="ready-for-results-build",
    )
    assert completed == {
        "from": "execution-ready",
        "to": "ready-for-results-build",
        "pair_count": 24,
        "results_status": "not_run",
    }
    manifest = json.loads((evaluation / "pairing-manifest.json").read_text("utf-8"))
    assert manifest["status"] == "ready-for-results-build"
    assert {pair["status"] for pair in manifest["pairs"]} == {"completed"}
    assert {
        contract["status"]
        for pair in manifest["pairs"]
        for contract in pair["products"].values()
    } == {"completed"}
    assert (evaluation / "results.json").read_bytes() == results_before
    assert builder.validate_contract(
        repo_root=repo,
        eval_root=evaluation,
        expected_state="ready-for-results-build",
    ) == {
        "state": "ready-for-results-build",
        "schema_version": 2,
        "case_count": 24,
        "pair_count": 24,
        "product_run_count": 48,
        "blind_grade_count": 72,
    }


def test_synthetic_v1_scaffold_cannot_be_prepared_before_evidence_is_frozen(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(
        tmp_path,
        pairing_schema_version=1,
    )
    materials_dir = evaluation / "cases" / "P01" / "materials"
    materials_path = materials_dir / "manifest.json"
    materials = json.loads(materials_path.read_text("utf-8"))
    materials["reviews"]["privacy"]["status"] = "pending"
    _write_json(materials_path, materials)
    pairing_path = evaluation / "pairing-manifest.json"
    pairing = json.loads(pairing_path.read_text("utf-8"))
    pairing["pairs"][0]["bindings"]["materials_tree_sha256"] = tree_sha256(
        materials_dir
    )
    _write_json(pairing_path, pairing)
    manifest_before = pairing_path.read_bytes()
    results_path = evaluation / "results.json"
    results_before = results_path.read_bytes()

    with pytest.raises(builder.BenchmarkBuildError, match="frozen|review|pending"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="execution-ready",
            promax_skill_tree_sha256="a" * 64,
            ultra_skill_tree_sha256="b" * 64,
        )
    assert pairing_path.read_bytes() == manifest_before
    assert results_path.read_bytes() == results_before


def test_execution_ready_rejects_asserted_skill_hash_mismatch_atomically(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    pairing_before = (evaluation / "pairing-manifest.json").read_bytes()
    results_before = (evaluation / "results.json").read_bytes()

    with pytest.raises(
        builder.BenchmarkBuildError,
        match="promax.*does not match.*measured",
    ):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="execution-ready",
            promax_skill_tree_sha256="c" * 64,
            ultra_skill_tree_sha256="b" * 64,
        )

    assert (evaluation / "pairing-manifest.json").read_bytes() == pairing_before
    assert (evaluation / "results.json").read_bytes() == results_before


def test_execution_ready_rejects_stale_skill_measurement_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    pairing_before = (evaluation / "pairing-manifest.json").read_bytes()
    results_before = (evaluation / "results.json").read_bytes()

    def reject_stale(_repo: Path) -> dict[str, str]:
        raise builder.BenchmarkBuildError(
            "Ultra skill-tree measurement is stale or not ready"
        )

    monkeypatch.setattr(
        builder,
        "_measure_execution_skill_tree_sha256",
        reject_stale,
    )
    with pytest.raises(builder.BenchmarkBuildError, match="stale|not ready"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="execution-ready",
            promax_skill_tree_sha256="a" * 64,
            ultra_skill_tree_sha256="b" * 64,
        )

    assert (evaluation / "pairing-manifest.json").read_bytes() == pairing_before
    assert (evaluation / "results.json").read_bytes() == results_before


def test_promax_skill_hash_matches_green_canonical_algorithm() -> None:
    builder = load_builder(stub_skill_measurement=False)
    expected = canonical_promax_skill_tree_sha256(
        ROOT / "skills" / "crossframe-promax"
    )

    assert builder._measure_promax_skill_tree_sha256(ROOT) == expected


def test_ultra_skill_hash_matches_fresh_release_artifact_authority() -> None:
    builder = load_builder(stub_skill_measurement=False)
    release_manifest = load_json(
        ROOT / "skills/crossframe-ultra/references/release-manifest.json"
    )
    assert isinstance(release_manifest, dict)
    release_artifacts = {
        artifact["path"]: artifact["sha256"]
        for artifact in release_manifest["release_artifacts"]
    }

    expected = sha256_bytes(canonical_json_bytes(release_artifacts) + b"\n")
    assert builder._measure_ultra_skill_tree_sha256(ROOT) == expected


def test_transition_cli_refuses_reentering_committed_execution_ready_state() -> None:
    manifest_before = PAIRING_PATH.read_bytes()
    results_before = RESULTS_PATH.read_bytes()
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "tests/evals/ultra-vs-promax/build_results.py",
            "--repo-root",
            ".",
            "--eval-root",
            "tests/evals/ultra-vs-promax",
            "--output",
            "tests/evals/ultra-vs-promax/results.json",
            "--transition-to",
            "execution-ready",
            "--promax-skill-tree-sha256",
            "a" * 64,
            "--ultra-skill-tree-sha256",
            "b" * 64,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "illegal transition 'execution-ready' -> 'execution-ready'" in completed.stderr
    assert PAIRING_PATH.read_bytes() == manifest_before
    assert RESULTS_PATH.read_bytes() == results_before


def test_readme_separates_execution_readiness_from_expensive_evidence() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    for marker in (
        "48 product runs",
        "three fresh blind graders",
        "72 raw grade files",
        "does not generate model output",
        "not_run",
        "fail closed",
        "no forward-validation claim",
        "build_results.py",
        FROZEN_CLI,
        PREPARE_CLI,
        SEAL_CLI,
        "scaffold -> execution-ready -> ready-for-results-build",
        "completed pairs",
        "checked-in `execution-ready`",
        "0 product runs and 0 blind grades",
        "Benchmark execution is deferred",
    ):
        assert marker in text


def _make_v2_synthetic_eval(
    tmp_path: Path,
    *,
    pairing_schema_version: int = 2,
) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    evaluation = repo / "tests" / "evals" / "ultra-vs-promax"
    shutil.copytree(EVAL_ROOT, evaluation)
    scenarios = json.loads((evaluation / "scenarios.json").read_text("utf-8"))
    pairing = json.loads((evaluation / "pairing-manifest.json").read_text("utf-8"))
    if pairing_schema_version not in {1, 2}:
        raise ValueError("synthetic pairing schema version must be 1 or 2")
    pairing["schema_version"] = pairing_schema_version
    pairing["status"] = "scaffold"

    for case, pair in zip(scenarios, pairing["pairs"], strict=True):
        pair["status"] = "pending"
        for product in pair["products"].values():
            product["status"] = "pending"
            product["skill_tree_sha256"] = None
        if pairing_schema_version == 2:
            case.pop("execution_readiness", None)
        else:
            case["execution_readiness"] = "awaiting-evidence-bundle"
        case_id = case["id"]
        case_dir = evaluation / "cases" / case_id
        materials_dir = case_dir / "materials"
        shutil.rmtree(materials_dir)
        materials_dir.mkdir()
        source_path = materials_dir / "synthetic-source.txt"
        source_path.write_text(
            f"Synthetic source for {case_id}; not benchmark evidence.\n",
            encoding="utf-8",
            newline="\n",
        )
        source_files = [
            {
                "path": "synthetic-source.txt",
                "sha256": sha256_bytes(source_path.read_bytes()),
                "media_type": "text/plain",
                "license": "CC0-1.0",
            }
        ]
        source_set_sha256 = sha256_json(source_files)

        cutoff_path = case_dir / "evidence-cutoff.json"
        cutoff = json.loads(cutoff_path.read_text("utf-8"))
        cutoff["evidence_state"] = "frozen"
        _write_json(cutoff_path, cutoff)

        allowed_paths = [
            case["prompt_path"],
            case["evidence_cutoff_path"],
            f"{case['materials_dir']}/synthetic-source.txt",
        ]
        privacy = {
            "schema_id": "crossframe.ultra.benchmark-privacy-policy",
            "schema_version": 2,
            "case_id": case_id,
            "default_deny": True,
            "product_packet_allowlist": allowed_paths,
            "grader_case_packet_allowlist": allowed_paths,
            "grader_injected_slots": ["rubric", "article-a", "article-b"],
            "audit_only_paths": [
                f"{case['materials_dir']}/manifest.json",
                case["privacy_policy_path"],
                case["expected_pressure_path"],
            ],
        }
        privacy_path = case_dir / "privacy-policy.json"
        _write_json(privacy_path, privacy)

        common_review = {
            "status": "passed",
            "reviewed_at": "2026-08-03T12:00:00Z",
            "subject_sha256": source_set_sha256,
            "evidence": ["Synthetic review evidence."],
        }
        materials = {
            "schema_id": "crossframe.ultra.benchmark-materials-manifest",
            "schema_version": 2,
            "case_id": case_id,
            "bundle_status": "frozen",
            "retrieval_mode": (
                "prohibited"
                if case["category"] == "closed-material"
                else "frozen-bundle-only"
            ),
            "source_files": source_files,
            "source_count": 1,
            "source_set_sha256": source_set_sha256,
            "reviews": {
                "license": {
                    **common_review,
                    "reviewer_id": f"license-reviewer-{case_id}",
                    "source_decisions": [
                        {
                            "path": "synthetic-source.txt",
                            "sha256": source_files[0]["sha256"],
                            "license": "CC0-1.0",
                            "redistribution_allowed": True,
                            "basis": "Project-authored synthetic fixture.",
                        }
                    ],
                },
                "privacy": {
                    **common_review,
                    "reviewer_id": f"privacy-reviewer-{case_id}",
                    "privacy_policy_sha256": sha256_bytes(
                        privacy_path.read_bytes()
                    ),
                    "sensitive_paths": [],
                    "outbound_safe": True,
                },
                "outcome_leakage": {
                    **common_review,
                    "reviewer_id": f"outcome-reviewer-{case_id}",
                    "evidence_cutoff_sha256": sha256_bytes(
                        cutoff_path.read_bytes()
                    ),
                    "expected_pressure_sha256": sha256_bytes(
                        (case_dir / "expected-pressure.json").read_bytes()
                    ),
                    "post_cutoff_paths": [],
                    "outcome_disclosure_paths": [],
                },
            },
        }
        _write_json(materials_dir / "manifest.json", materials)

        pair_bindings = {
            "request_sha256": sha256_bytes((case_dir / "prompt.md").read_bytes()),
            "evidence_cutoff_sha256": sha256_bytes(cutoff_path.read_bytes()),
            "materials_tree_sha256": tree_sha256(materials_dir),
            "privacy_policy_sha256": sha256_bytes(privacy_path.read_bytes()),
        }
        if pairing_schema_version == 2:
            pair_bindings.update(
                {
                    "product_packet_sha256": None,
                    "grader_base_packet_sha256": None,
                }
            )
        pair["bindings"] = pair_bindings

    _write_json(evaluation / "scenarios.json", scenarios)
    _write_json(evaluation / "pairing-manifest.json", pairing)
    return repo, evaluation


def _write_v2_product_runs(builder, repo: Path, evaluation: Path) -> None:
    pairing = json.loads((evaluation / "pairing-manifest.json").read_text("utf-8"))
    for pair in pairing["pairs"]:
        case_id = pair["case_id"]
        packet = builder.build_product_packet(
            repo_root=repo,
            eval_root=evaluation,
            case_id=case_id,
        )
        assert sha256_json(packet) == pair["bindings"]["product_packet_sha256"]
        for product in ("promax", "ultra"):
            tree_hash = "a" * 64 if product == "promax" else "b" * 64
            product_contract = pair["products"][product]
            raw_dir = evaluation / "raw" / case_id / product
            artifact_dir = raw_dir / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            article_path = raw_dir / "article.md"
            article_path.write_text(
                (
                    "# Blind benchmark article\n\n"
                    + (
                        "Evidence, mechanisms, judgment, and reversal conditions.\n"
                        if product == "ultra"
                        else "A shorter independent analysis.\n"
                    )
                ),
                encoding="utf-8",
                newline="\n",
            )
            metadata = {
                "schema_id": "crossframe.ultra-vs-promax.product-run",
                "schema_version": 2,
                "run_id": f"product-{case_id}-{product}",
                "case_id": case_id,
                "product": product,
                "runtime_name": product_contract["runtime_name"],
                "framework_version": product_contract["framework_version"],
                "model_id": pairing["product_model"]["model_id"],
                "reasoning_effort": pairing["product_model"]["reasoning_effort"],
                "fresh_context": True,
                "tool_profile_id": pair["tool_profile_id"],
                "request_sha256": pair["bindings"]["request_sha256"],
                "evidence_cutoff_sha256": pair["bindings"][
                    "evidence_cutoff_sha256"
                ],
                "materials_tree_sha256": pair["bindings"][
                    "materials_tree_sha256"
                ],
                "privacy_policy_sha256": pair["bindings"][
                    "privacy_policy_sha256"
                ],
                "packet_sha256": pair["bindings"]["product_packet_sha256"],
                "skill_tree_sha256": tree_hash,
                "raw_output_path": article_path.relative_to(repo).as_posix(),
                "raw_output_sha256": sha256_bytes(article_path.read_bytes()),
                "artifact_dir": artifact_dir.relative_to(repo).as_posix(),
                "artifact_tree_sha256": tree_sha256(artifact_dir),
            }
            metadata["receipt_sha256"] = _product_context_receipt_sha256(metadata)
            _write_json(raw_dir / "run-metadata.json", metadata)


def _write_v2_blind_grades(builder, repo: Path, evaluation: Path) -> None:
    pairing = json.loads((evaluation / "pairing-manifest.json").read_text("utf-8"))
    rubric = json.loads((evaluation / "rubric.json").read_text("utf-8"))
    weights = rubric["dimension_weights"]
    for pair in pairing["pairs"]:
        case_id = pair["case_id"]
        labels = pair["blind_labels"]
        article_hashes = {
            product: sha256_bytes(
                (evaluation / "raw" / case_id / product / "article.md").read_bytes()
            )
            for product in ("promax", "ultra")
        }
        for grader in pair["graders"]:
            packet = builder.build_grader_packet(
                repo_root=repo,
                eval_root=evaluation,
                case_id=case_id,
                grader_id=grader["grader_id"],
            )
            scores = {
                label: {
                    dimension: (
                        maximum
                        if labels[label] == "ultra"
                        else max(0, maximum - 3)
                    )
                    for dimension, maximum in weights.items()
                }
                for label in ("A", "B")
            }
            grade = {
                "schema_id": "crossframe.ultra-vs-promax.blind-grade",
                "schema_version": 2,
                "run_id": f"grade-{case_id}-{grader['grader_id']}",
                "case_id": case_id,
                "grader_id": grader["grader_id"],
                "model_id": pairing["grader_contract"]["model_id"],
                "reasoning_effort": pairing["grader_contract"]["reasoning_effort"],
                "fresh_context": True,
                "prior_grades_visible": False,
                "rubric_sha256": sha256_json(rubric),
                "request_sha256": pair["bindings"]["request_sha256"],
                "materials_tree_sha256": pair["bindings"][
                    "materials_tree_sha256"
                ],
                "article_a_sha256": article_hashes[labels["A"]],
                "article_b_sha256": article_hashes[labels["B"]],
                "packet_sha256": sha256_json(packet),
                "dimension_scores": scores,
                "dimension_findings": {
                    label: {
                        dimension: f"Synthetic {label} finding for {dimension}."
                        for dimension in weights
                    }
                    for label in ("A", "B")
                },
                "automatic_failures": {
                    label: {flag: False for flag in AUTOMATIC_FAILURES}
                    for label in ("A", "B")
                },
                "automatic_failure_findings": {
                    label: {flag: [] for flag in AUTOMATIC_FAILURES}
                    for label in ("A", "B")
                },
            }
            grade["receipt_sha256"] = _grade_context_receipt_sha256(grade)
            _write_json(repo / grader["grade_path"], grade)


def _product_context_receipt_sha256(metadata: dict[str, object]) -> str:
    return sha256_json(
        {
            field: metadata[field]
            for field in (
                "run_id",
                "case_id",
                "product",
                "runtime_name",
                "model_id",
                "reasoning_effort",
                "packet_sha256",
                "skill_tree_sha256",
            )
        }
    )


def _grade_context_receipt_sha256(grade: dict[str, object]) -> str:
    return sha256_json(
        {
            field: grade[field]
            for field in (
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
            )
        }
    )


def _make_v2_complete_synthetic_eval(
    tmp_path: Path,
    *,
    complete_state: bool = True,
) -> tuple[Path, Path]:
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    if complete_state:
        builder = load_builder()
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="execution-ready",
            promax_skill_tree_sha256="a" * 64,
            ultra_skill_tree_sha256="b" * 64,
        )
        _write_v2_product_runs(builder, repo, evaluation)
        _write_v2_blind_grades(builder, repo, evaluation)
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )
    return repo, evaluation




def _sync_single_v2_bundle_bindings(evaluation: Path, case_id: str = "P01") -> None:
    pairing_path = evaluation / "pairing-manifest.json"
    pairing = json.loads(pairing_path.read_text("utf-8"))
    pair = next(item for item in pairing["pairs"] if item["case_id"] == case_id)
    case_dir = evaluation / "cases" / case_id
    pair["bindings"]["materials_tree_sha256"] = tree_sha256(
        case_dir / "materials"
    )
    pair["bindings"]["privacy_policy_sha256"] = sha256_bytes(
        (case_dir / "privacy-policy.json").read_bytes()
    )
    _write_json(pairing_path, pairing)


def test_v2_manifest_rejects_bare_passed_review(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    manifest_path = evaluation / "cases" / "P01" / "materials" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["reviews"]["license"] = "passed"
    _write_json(manifest_path, manifest)
    _sync_single_v2_bundle_bindings(evaluation)

    with pytest.raises(builder.BenchmarkBuildError, match="license review|object"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_v2_review_subject_must_match_source_set(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    manifest_path = evaluation / "cases" / "P01" / "materials" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["reviews"]["privacy"]["subject_sha256"] = "f" * 64
    _write_json(manifest_path, manifest)
    _sync_single_v2_bundle_bindings(evaluation)

    with pytest.raises(builder.BenchmarkBuildError, match="subject"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_v2_license_review_must_cover_every_source(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    manifest_path = evaluation / "cases" / "P01" / "materials" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["reviews"]["license"]["source_decisions"] = []
    _write_json(manifest_path, manifest)
    _sync_single_v2_bundle_bindings(evaluation)

    with pytest.raises(builder.BenchmarkBuildError, match="license.*cover|source decision"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_v2_default_deny_allowlist_rejects_audit_path(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    case_dir = evaluation / "cases" / "P01"
    privacy_path = case_dir / "privacy-policy.json"
    privacy = json.loads(privacy_path.read_text("utf-8"))
    privacy["product_packet_allowlist"].append(
        "tests/evals/ultra-vs-promax/cases/P01/expected-pressure.json"
    )
    _write_json(privacy_path, privacy)
    manifest_path = case_dir / "materials" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["reviews"]["privacy"]["privacy_policy_sha256"] = sha256_bytes(
        privacy_path.read_bytes()
    )
    _write_json(manifest_path, manifest)
    _sync_single_v2_bundle_bindings(evaluation)

    with pytest.raises(builder.BenchmarkBuildError, match="allowlist|audit-only"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_v2_bundle_rejects_noncanonical_case_paths(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    scenarios_path = evaluation / "scenarios.json"
    scenarios = json.loads(scenarios_path.read_text("utf-8"))
    scenarios[0]["prompt_path"] = scenarios[1]["prompt_path"]
    _write_json(scenarios_path, scenarios)

    with pytest.raises(builder.BenchmarkBuildError, match="canonical"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_v2_source_coverage_counts_nested_manifest_names(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    undeclared = (
        evaluation
        / "cases"
        / "P01"
        / "materials"
        / "nested"
        / "manifest.json"
    )
    _write_json(undeclared, {"undeclared": True})
    _sync_single_v2_bundle_bindings(evaluation)

    with pytest.raises(builder.BenchmarkBuildError, match="undeclared"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_v2_packets_never_expose_audit_only_or_product_identity(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    product_packet = builder.build_product_packet(
        repo_root=repo,
        eval_root=evaluation,
        case_id="P01",
    )
    product_text = json.dumps(product_packet, ensure_ascii=False).lower()
    for forbidden in ("expected-pressure", "privacy-policy", "manifest.json", "reviews"):
        assert forbidden not in product_text

    _write_v2_product_runs(builder, repo, evaluation)
    grader_packet = builder.build_grader_packet(
        repo_root=repo,
        eval_root=evaluation,
        case_id="P01",
        grader_id="grader-1",
    )
    assert set(grader_packet) == {
        "files",
        "rubric",
        "article-a",
        "article-b",
    }
    assert grader_packet["files"] == product_packet["files"]
    assert all(
        "/" not in str(item["logical_name"])
        and "\\" not in str(item["logical_name"])
        for item in grader_packet["files"]
    )
    grader_text = json.dumps(grader_packet, ensure_ascii=False).lower()
    for forbidden in (
        "expected-pressure",
        "privacy-policy",
        "manifest.json",
        "reviews",
        "promax",
        "ultra",
        "raw/",
        "case_id",
        "grader_id",
        "prior grades",
    ):
        assert forbidden not in grader_text
    assert grader_packet["article-a"]["logical_name"] == "Article A"
    assert grader_packet["article-b"]["logical_name"] == "Article B"


def test_v2_reviews_require_three_distinct_reviewer_ids(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    manifest_path = evaluation / "cases" / "P01" / "materials" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["reviews"]["privacy"]["reviewer_id"] = manifest["reviews"][
        "license"
    ]["reviewer_id"]
    _write_json(manifest_path, manifest)
    _sync_single_v2_bundle_bindings(evaluation)

    with pytest.raises(builder.BenchmarkBuildError, match="distinct reviewer"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_execution_ready_rejects_preexisting_raw_evidence_atomically(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    preexisting = evaluation / "raw" / "P01" / "promax" / "article.md"
    preexisting.parent.mkdir(parents=True, exist_ok=True)
    preexisting.write_text("preexisting output\n", encoding="utf-8", newline="\n")
    pairing_before = (evaluation / "pairing-manifest.json").read_bytes()
    results_before = (evaluation / "results.json").read_bytes()

    with pytest.raises(builder.BenchmarkBuildError, match="raw.*empty|preexisting"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="execution-ready",
            promax_skill_tree_sha256="a" * 64,
            ultra_skill_tree_sha256="b" * 64,
        )

    assert (evaluation / "pairing-manifest.json").read_bytes() == pairing_before
    assert (evaluation / "results.json").read_bytes() == results_before


@pytest.mark.parametrize(
    "relative",
    (
        "tests/evals/ultra-vs-promax/cases/P01",
        "tests/evals/ultra-vs-promax/cases/P01/materials",
        "tests/evals/ultra-vs-promax/cases/P01/materials/synthetic-source.txt",
    ),
)
def test_v2_paths_reject_windows_reparse_points_at_every_layer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    target = (repo / relative).absolute()
    real_lstat = os.lstat
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    class ReparseStat:
        def __init__(self, original: os.stat_result) -> None:
            self._original = original
            self.st_file_attributes = (
                getattr(original, "st_file_attributes", 0) | reparse_flag
            )

        def __getattr__(self, name: str) -> object:
            return getattr(self._original, name)

    def lstat_with_reparse(path: object, *args: object, **kwargs: object) -> object:
        original = real_lstat(path, *args, **kwargs)
        candidate = Path(os.fsdecode(path))
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if candidate.absolute() == target:
            return ReparseStat(original)
        return original

    monkeypatch.setattr(builder.os, "lstat", lstat_with_reparse)
    with pytest.raises(builder.BenchmarkBuildError, match="reparse|symlink"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
        )


def test_synthetic_v2_fixture_ignores_real_material_directory_contents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contaminated = tmp_path / "contaminated-eval"
    shutil.copytree(EVAL_ROOT, contaminated)
    audit_copy = contaminated / "cases" / "P01" / "materials" / "audit-copy.json"
    _write_json(audit_copy, {"audit_only": True})
    monkeypatch.setattr(sys.modules[__name__], "EVAL_ROOT", contaminated)

    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path / "isolated")
    summary = builder.validate_contract(
        repo_root=repo,
        eval_root=evaluation,
        expected_state="scaffold",
    )
    assert summary["case_count"] == 24
    assert sorted(
        path.relative_to(evaluation / "cases" / "P01" / "materials").as_posix()
        for path in (evaluation / "cases" / "P01" / "materials").rglob("*")
        if path.is_file()
    ) == ["manifest.json", "synthetic-source.txt"]


def test_v1_scaffold_migrates_atomically_to_v2_execution_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(
        tmp_path,
        pairing_schema_version=1,
    )
    manifest_path = evaluation / "pairing-manifest.json"
    results_path = evaluation / "results.json"
    results_before = results_path.read_bytes()
    replace_calls: list[tuple[Path, Path]] = []
    real_replace = builder.os.replace

    def counting_replace(source: object, destination: object) -> None:
        replace_calls.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(builder.os, "replace", counting_replace)
    summary = builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )

    migrated = json.loads(manifest_path.read_text("utf-8"))
    assert summary["from"] == "scaffold"
    assert summary["to"] == "execution-ready"
    assert migrated["schema_version"] == 2
    assert migrated["status"] == "execution-ready"
    assert len(replace_calls) == 1
    assert replace_calls[0][1] == manifest_path
    assert results_path.read_bytes() == results_before
    assert builder.validate_contract(
        repo_root=repo,
        eval_root=evaluation,
        expected_state="execution-ready",
    )["schema_version"] == 2


def test_single_v2_bundle_validates_beside_v1_scaffold(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(
        tmp_path,
        pairing_schema_version=1,
    )

    summary = builder.validate_case_bundle(
        repo_root=repo,
        eval_root=evaluation,
        case_id="P01",
        require_frozen=True,
    )

    assert summary["status"] == "bundle-ready"
    assert summary["case_id"] == "P01"
    assert summary["source_count"] == 1


def test_single_bundle_binds_canonical_scenario_question(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(
        tmp_path,
        pairing_schema_version=1,
    )
    scenarios_path = evaluation / "scenarios.json"
    scenarios = json.loads(scenarios_path.read_text("utf-8"))
    scenarios[0]["question"] = "Tampered scenario text"
    _write_json(scenarios_path, scenarios)

    with pytest.raises(builder.BenchmarkBuildError, match="question|prompt"):
        builder.validate_case_bundle(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
            require_frozen=True,
        )


def test_product_fresh_context_receipt_is_hash_bound(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    _write_v2_product_runs(builder, repo, evaluation)
    metadata_path = evaluation / "raw" / "P01" / "promax" / "run-metadata.json"
    metadata = json.loads(metadata_path.read_text("utf-8"))
    metadata["receipt_sha256"] = "f" * 64
    _write_json(metadata_path, metadata)

    with pytest.raises(
        builder.BenchmarkBuildError,
        match="fresh context receipt SHA-256 mismatch",
    ):
        builder.build_grader_packet(
            repo_root=repo,
            eval_root=evaluation,
            case_id="P01",
            grader_id="grader-1",
        )


def test_grade_fresh_context_receipt_is_hash_bound(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    _write_v2_product_runs(builder, repo, evaluation)
    _write_v2_blind_grades(builder, repo, evaluation)
    grade_path = evaluation / "raw" / "P01" / "grades" / "grader-1.json"
    grade = json.loads(grade_path.read_text("utf-8"))
    grade["receipt_sha256"] = "f" * 64
    _write_json(grade_path, grade)

    with pytest.raises(
        builder.BenchmarkBuildError,
        match="fresh context receipt SHA-256 mismatch",
    ):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )


def test_ready_for_results_requires_48_unique_product_context_ids(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    _write_v2_product_runs(builder, repo, evaluation)
    first_path = evaluation / "raw" / "P01" / "promax" / "run-metadata.json"
    duplicate_path = evaluation / "raw" / "P01" / "ultra" / "run-metadata.json"
    first = json.loads(first_path.read_text("utf-8"))
    duplicate = json.loads(duplicate_path.read_text("utf-8"))
    duplicate["run_id"] = first["run_id"]
    duplicate["receipt_sha256"] = _product_context_receipt_sha256(duplicate)
    _write_json(duplicate_path, duplicate)

    with pytest.raises(builder.BenchmarkBuildError, match="duplicate product.*run_id"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )


def test_ready_for_results_requires_72_unique_grade_context_ids(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    _write_v2_product_runs(builder, repo, evaluation)
    _write_v2_blind_grades(builder, repo, evaluation)
    first_path = evaluation / "raw" / "P01" / "grades" / "grader-1.json"
    duplicate_path = evaluation / "raw" / "P01" / "grades" / "grader-2.json"
    first = json.loads(first_path.read_text("utf-8"))
    duplicate = json.loads(duplicate_path.read_text("utf-8"))
    duplicate["run_id"] = first["run_id"]
    duplicate["receipt_sha256"] = _grade_context_receipt_sha256(duplicate)
    _write_json(duplicate_path, duplicate)

    with pytest.raises(builder.BenchmarkBuildError, match="duplicate grade.*run_id"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )


def test_results_rebuild_rechecks_unique_context_ids(tmp_path: Path) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_complete_synthetic_eval(tmp_path)
    first_path = evaluation / "raw" / "P01" / "promax" / "run-metadata.json"
    duplicate_path = evaluation / "raw" / "P01" / "ultra" / "run-metadata.json"
    first = json.loads(first_path.read_text("utf-8"))
    duplicate = json.loads(duplicate_path.read_text("utf-8"))
    duplicate["run_id"] = first["run_id"]
    duplicate["receipt_sha256"] = _product_context_receipt_sha256(duplicate)
    _write_json(duplicate_path, duplicate)
    results_before = (evaluation / "results.json").read_bytes()

    with pytest.raises(builder.BenchmarkBuildError, match="duplicate product.*run_id"):
        builder.build_results(repo_root=repo, eval_root=evaluation)

    assert (evaluation / "results.json").read_bytes() == results_before


def test_execution_ready_is_atomic_when_the_twenty_fourth_bundle_fails(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    case_id = "C04"
    manifest_path = evaluation / "cases" / case_id / "materials" / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["reviews"]["outcome_leakage"]["subject_sha256"] = "0" * 64
    _write_json(manifest_path, manifest)
    _sync_single_v2_bundle_bindings(evaluation, case_id)
    pairing_before = (evaluation / "pairing-manifest.json").read_bytes()
    results_before = (evaluation / "results.json").read_bytes()

    with pytest.raises(builder.BenchmarkBuildError, match="subject"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="execution-ready",
            promax_skill_tree_sha256="a" * 64,
            ultra_skill_tree_sha256="b" * 64,
        )

    assert (evaluation / "pairing-manifest.json").read_bytes() == pairing_before
    assert (evaluation / "results.json").read_bytes() == results_before


def test_seal_rejects_last_grade_packet_tampering_without_partial_migration(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    _write_v2_product_runs(builder, repo, evaluation)
    _write_v2_blind_grades(builder, repo, evaluation)
    grade_path = evaluation / "raw" / "C04" / "grades" / "grader-3.json"
    grade = json.loads(grade_path.read_text("utf-8"))
    grade["packet_sha256"] = "0" * 64
    _write_json(grade_path, grade)
    pairing_before = (evaluation / "pairing-manifest.json").read_bytes()
    results_before = (evaluation / "results.json").read_bytes()

    with pytest.raises(builder.BenchmarkBuildError, match="packet_sha256|packet"):
        builder.transition_state(
            repo_root=repo,
            eval_root=evaluation,
            target_state="ready-for-results-build",
        )

    assert (evaluation / "pairing-manifest.json").read_bytes() == pairing_before
    assert (evaluation / "results.json").read_bytes() == results_before


def test_validate_contract_accepts_committed_execution_ready_and_v1_never_executes(
    tmp_path: Path,
) -> None:
    builder = load_builder()
    assert builder.validate_contract(
        repo_root=ROOT,
        eval_root=EVAL_ROOT,
        expected_state="execution-ready",
    ) == {
        "state": "execution-ready",
        "schema_version": 2,
        "case_count": 24,
        "pair_count": 24,
        "product_run_count": 0,
        "blind_grade_count": 0,
    }

    repo, evaluation = _make_v2_synthetic_eval(
        tmp_path,
        pairing_schema_version=1,
    )
    assert builder.validate_scaffold(repo_root=repo, eval_root=evaluation)[
        "status"
    ] == "scaffold-valid"
    with pytest.raises(builder.BenchmarkBuildError, match="version 2|execution-ready"):
        builder.validate_contract(
            repo_root=repo,
            eval_root=evaluation,
            expected_state="execution-ready",
        )

    repo, evaluation = _make_v2_synthetic_eval(tmp_path / "v2")
    scaffold = builder.validate_contract(
        repo_root=repo,
        eval_root=evaluation,
        expected_state="scaffold",
    )
    assert scaffold["state"] == "scaffold"
    assert scaffold["schema_version"] == 2


def test_each_state_transition_uses_one_atomic_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = load_builder()
    repo, evaluation = _make_v2_synthetic_eval(tmp_path)
    real_replace = builder.os.replace
    replace_calls: list[tuple[object, object]] = []

    def recording_replace(source: object, destination: object) -> None:
        replace_calls.append((source, destination))
        real_replace(source, destination)

    monkeypatch.setattr(builder.os, "replace", recording_replace)
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="execution-ready",
        promax_skill_tree_sha256="a" * 64,
        ultra_skill_tree_sha256="b" * 64,
    )
    assert len(replace_calls) == 1

    _write_v2_product_runs(builder, repo, evaluation)
    _write_v2_blind_grades(builder, repo, evaluation)
    replace_calls.clear()
    builder.transition_state(
        repo_root=repo,
        eval_root=evaluation,
        target_state="ready-for-results-build",
    )
    assert len(replace_calls) == 1
