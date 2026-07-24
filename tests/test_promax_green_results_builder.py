from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from tests import test_promax_behavioral_contract as behavioral
from tests import test_promax_green_eval as green


ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "tests" / "evals" / "promax-green"
BUILDER_PATH = EVAL_ROOT / "build_results.py"
SCENARIOS_PATH = EVAL_ROOT / "scenarios.json"
README_PATH = EVAL_ROOT / "README.md"


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "promax_green_build_results",
        BUILDER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load GREEN results builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


class ProMaxGreenScenarioManifestTests(unittest.TestCase):
    def test_manifest_freezes_the_exact_twelve_behavioral_prompts(self) -> None:
        scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["id"] for item in scenarios],
            list(behavioral.EXPECTED_SCENARIO_IDS),
        )
        self.assertEqual(
            {item["id"]: item["prompt"] for item in scenarios},
            behavioral.EXPECTED_PROMPTS,
        )
        for item in scenarios:
            scenario_id = item["id"]
            expected_prompt = behavioral.EXPECTED_PROMPTS[scenario_id]
            executed_prompt = item["executed_prompt"]
            if "CrossFrame ProMax" in expected_prompt:
                self.assertEqual(executed_prompt, expected_prompt)
            else:
                self.assertEqual(
                    executed_prompt,
                    f"$crossframe-promax {expected_prompt}",
                )
            self.assertEqual(
                item["raw_output_path"],
                f"tests/evals/promax-green/raw/{{model_id}}/{scenario_id}.md",
            )

    def test_readme_freezes_the_replay_and_fail_closed_protocol(self) -> None:
        text = README_PATH.read_text(encoding="utf-8")
        for marker in (
            "3",
            "gpt-5.6-sol",
            "gpt-5.6-terra",
            "run_matrix",
            "fresh",
            "eval-metadata.json",
            "artifact_tree_sha256",
            "metric evidence",
            "A1/A2",
            "load_artifact_semantics",
            "fail closed",
            "does not generate model output",
            "build_results.py",
            "results.json",
            "evaluated-skill-tree.json",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("24 independent model-and-scenario runs", text)


class ProMaxGreenResultsBuilderTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.builder = _load_builder()
        temporary_root = ROOT / "work"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        self.addCleanup(self.temporary.cleanup)
        self.eval_root = Path(self.temporary.name) / "promax-green"
        self.eval_root.mkdir()
        self.models = ["model-one", "model-two"]
        self.run_matrix = [
            {"model_id": "model-one", "scenario_id": "A1"},
            {"model_id": "model-one", "scenario_id": "A2"},
            {"model_id": "model-two", "scenario_id": "A1"},
        ]
        self.scenarios = [
            {
                "id": "A1",
                "prompt": "stance one",
                "executed_prompt": "请明确使用 CrossFrame ProMax。\n\nstance one",
                "tags": ["paired"],
                "context": "fresh independent model run",
                "raw_output_path": (
                    f"{self.eval_root.relative_to(ROOT).as_posix()}"
                    "/raw/{model_id}/A1.md"
                ),
            },
            {
                "id": "A2",
                "prompt": "stance two",
                "executed_prompt": "请明确使用 CrossFrame ProMax。\n\nstance two",
                "tags": ["paired"],
                "context": "fresh independent model run",
                "raw_output_path": (
                    f"{self.eval_root.relative_to(ROOT).as_posix()}"
                    "/raw/{model_id}/A2.md"
                ),
            },
        ]
        self.rubric = {
            "schema_id": "crossframe.promax.green-rubric",
            "schema_version": 1,
            "models": self.models,
            "scenario_ids": ["A1", "A2"],
            "run_matrix": self.run_matrix,
            "scoring_unit": "one independently forked model-and-scenario run",
            "metrics": [
                {
                    "metric_id": "minimum_metric",
                    "direction": "minimum",
                    "threshold": 1.0,
                    "applicable_scenarios": "all",
                    "pass_rule": "must pass",
                },
                {
                    "metric_id": "maximum_metric",
                    "direction": "maximum",
                    "threshold": 0.0,
                    "applicable_scenarios": "all",
                    "pass_rule": "must remain absent",
                },
            ],
            "paired_stability": {
                "scenario_pair": ["A1", "A2"],
                "required_model_ids": ["model-one"],
                "required_equal_fields": [
                    "semantic_key_sha256",
                    "relation_to_proposition",
                    "judgment_strength",
                    "option_kind_ranking",
                    "option_semantic_ranking",
                    "normative_selection_basis_sha256",
                ],
                "required_judgment_strength_drift": 0,
                "frozen_pair_context": {
                    "analysis_object": "one frozen institutional choice",
                    "factual_material": [],
                    "time_window": "2026-Q3",
                    "evidence_cutoff": "2026-07-23T00:00:00+08:00",
                },
            },
            "acceptance": {
                "all_minimum_metrics_meet_threshold": True,
                "all_maximum_metrics_meet_threshold": True,
                "paired_stability_passes_for_every_available_model": True,
                "raw_output_hashes_and_skill_tree_hashes_verify": True,
                "deterministic_regression_suite_passes": True,
            },
        }
        self.rubric["paired_stability"][
            "frozen_pair_context_sha256"
        ] = green.sha256_json(
            self.rubric["paired_stability"]["frozen_pair_context"]
        )
        (self.eval_root / "rubric.json").write_text(
            json.dumps(self.rubric, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.eval_root / "scenarios.json").write_text(
            json.dumps(self.scenarios, ensure_ascii=False),
            encoding="utf-8",
        )

    def _write_run(
        self,
        scenario_id: str,
        *,
        model_id: str | None = None,
        failed_metric: str | None = None,
    ) -> Path:
        if model_id is None:
            model_id = self.models[0]
        bundle = self.eval_root / "artifacts" / model_id / scenario_id
        run_dir = bundle / "run"
        raw_path = self.eval_root / "raw" / model_id / f"{scenario_id}.md"
        run_dir.mkdir(parents=True)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        fixture = green.ProMaxGreenArtifactSemanticsTests()
        fixture._write_bundle(run_dir)
        raw_path.write_text(
            f"# {model_id}/{scenario_id}\n\nAuditable final projection.\n",
            encoding="utf-8",
        )
        scenario = next(
            item for item in self.scenarios if item["id"] == scenario_id
        )
        raw_relative = raw_path.relative_to(ROOT).as_posix()
        evidence = [
            {
                "path": raw_relative,
                "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                "finding": "The committed raw projection records this run.",
            }
        ]
        metrics: dict[str, object] = {}
        for rubric_metric in self.rubric["metrics"]:
            metric_id = rubric_metric["metric_id"]
            scope = rubric_metric["applicable_scenarios"]
            applicable = scope == "all" or scenario_id in scope
            numerator = (
                1
                if applicable and rubric_metric["direction"] == "minimum"
                else 0
            )
            failing_artifacts: list[object] = []
            if metric_id == failed_metric and applicable:
                numerator = 0 if rubric_metric["direction"] == "minimum" else 1
                failing_artifacts = [*evidence]
            metrics[metric_id] = {
                "metric_id": metric_id,
                "applicable": applicable,
                "direction": rubric_metric["direction"],
                "threshold": rubric_metric["threshold"],
                "passed": metric_id != failed_metric or not applicable,
                "numerator": numerator,
                "denominator": int(applicable),
                "evidence": evidence,
                "failing_artifacts": failing_artifacts,
                "untrusted_note": "must not be copied",
            }
        metadata = {
            "schema_id": "crossframe.promax.green-run-metadata",
            "schema_version": 1,
            "model_id": model_id,
            "scenario_id": scenario_id,
            "run_id": f"run-{model_id}-{scenario_id}",
            "fresh_context": True,
            "skill_loaded": True,
            "executed_prompt": scenario["executed_prompt"],
            "prompt_sha256": hashlib.sha256(
                scenario["executed_prompt"].encode("utf-8")
            ).hexdigest(),
            "skill_tree_sha256": green.canonical_skill_tree_sha256(),
            "tool_availability": {
                "filesystem": True,
                "network": True,
                "validators": True,
            },
            "raw_output_path": raw_relative,
            "raw_output_sha256": hashlib.sha256(
                raw_path.read_bytes()
            ).hexdigest(),
            "artifact_dir": run_dir.relative_to(ROOT).as_posix(),
            "artifact_tree_sha256": _tree_sha256(run_dir),
            "metrics": metrics,
            "untrusted_run_note": "must not be copied",
        }
        bundle.mkdir(parents=True, exist_ok=True)
        metadata_path = bundle / "eval-metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False),
            encoding="utf-8",
        )
        return metadata_path

    def _write_all_runs(self) -> None:
        for run in self.rubric["run_matrix"]:
            self._write_run(
                run["scenario_id"],
                model_id=run["model_id"],
            )

    def test_builds_canonical_results_from_hash_bound_evidence(self) -> None:
        self._write_all_runs()

        results = self.builder.build_results(
            repo_root=ROOT,
            eval_root=self.eval_root,
        )

        results_path = self.eval_root / "results.json"
        self.assertTrue(results_path.is_file())
        self.assertEqual(
            json.loads(results_path.read_text(encoding="utf-8")),
            results,
        )
        self.assertEqual(
            set(results),
            {
                "schema_id",
                "schema_version",
                "rubric_sha256",
                "scenarios_sha256",
                "skill_tree_sha256",
                "runs",
                "aggregate",
            },
        )
        self.assertEqual(len(results["runs"]), 3)
        self.assertEqual(
            [
                (run["model_id"], run["scenario_id"])
                for run in results["runs"]
            ],
            [
                ("model-one", "A1"),
                ("model-one", "A2"),
                ("model-two", "A1"),
            ],
        )
        for run in results["runs"]:
            self.assertNotIn("untrusted_run_note", run)
            self.assertEqual(
                set(run["metrics"]["minimum_metric"]),
                {
                    "applicable",
                    "direction",
                    "threshold",
                    "passed",
                    "numerator",
                    "denominator",
                    "evidence",
                    "failing_artifacts",
                },
            )
            self.assertNotIn(
                "untrusted_note",
                run["metrics"]["minimum_metric"],
            )
        self.assertEqual(
            results["aggregate"]["metrics"]["minimum_metric"]["numerator"],
            3,
        )
        self.assertEqual(
            results["aggregate"]["metrics"]["maximum_metric"]["numerator"],
            0,
        )
        self.assertTrue(results["aggregate"]["all_thresholds_passed"])
        self.assertTrue(
            results["aggregate"]["deterministic_regression_suite_passed"]
        )
        self.assertTrue(
            results["aggregate"]["paired_stability"][0]["passed"]
        )
        self.assertEqual(
            [record["model_id"] for record in results["aggregate"]["paired_stability"]],
            ["model-one"],
        )
        self.assertFalse(
            (
                self.eval_root
                / "artifacts"
                / "model-two"
                / "A2"
                / "eval-metadata.json"
            ).exists()
        )

    def test_declared_evaluated_tree_hash_is_enforced_without_relabelling(
        self,
    ) -> None:
        self._write_all_runs()
        (self.eval_root / "evaluated-skill-tree.json").write_text(
            json.dumps(
                {
                    "schema_id": "crossframe.promax.green-evaluated-skill-tree",
                    "schema_version": 1,
                    "evaluated_skill_tree_sha256": "f" * 64,
                    "current_release_compatibility": {
                        "scope": "activation-boundary-only",
                        "changed_paths": ["skills/crossframe-promax/SKILL.md"],
                        "deterministic_tests": ["tests.example.test_activation"],
                    },
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "skill tree SHA-256 mismatch",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

    def test_missing_run_fails_without_creating_results(self) -> None:
        self._write_run("A1")

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "missing eval metadata",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_failed_metric_fails_without_creating_results(self) -> None:
        self._write_run("A1", failed_metric="minimum_metric")
        self._write_run("A2")
        self._write_run("A1", model_id="model-two")

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "failed metric",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_tampered_raw_output_fails_without_creating_results(self) -> None:
        metadata_path = self._write_run("A1")
        self._write_run("A2")
        self._write_run("A1", model_id="model-two")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        raw_path = ROOT / metadata["raw_output_path"]
        raw_path.write_text("tampered", encoding="utf-8")

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "raw output SHA-256",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_tampered_metric_evidence_fails_without_creating_results(self) -> None:
        metadata_path = self._write_run("A1")
        self._write_run("A2")
        self._write_run("A1", model_id="model-two")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["metrics"]["minimum_metric"]["evidence"][0][
            "sha256"
        ] = "0" * 64
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "metric evidence SHA-256",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_tampered_artifact_tree_fails_without_creating_results(self) -> None:
        metadata_path = self._write_run("A1")
        self._write_run("A2")
        self._write_run("A1", model_id="model-two")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["artifact_tree_sha256"] = "0" * 64
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "artifact tree SHA-256",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_builder_resolves_artifacts_from_repo_not_process_cwd(self) -> None:
        self._write_all_runs()
        previous_cwd = Path.cwd()
        try:
            os.chdir(self.temporary.name)
            results = self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )
        finally:
            os.chdir(previous_cwd)

        self.assertEqual(len(results["runs"]), 3)

    def test_closed_run_matrix_rejects_duplicate_pair_before_loading_evidence(
        self,
    ) -> None:
        self.rubric["run_matrix"].append(
            {"model_id": "model-one", "scenario_id": "A1"}
        )
        (self.eval_root / "rubric.json").write_text(
            json.dumps(self.rubric, ensure_ascii=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "duplicate run_matrix pair",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_closed_run_matrix_rejects_extra_entry_fields(self) -> None:
        self.rubric["run_matrix"][0]["unlisted"] = "not allowed"
        (self.eval_root / "rubric.json").write_text(
            json.dumps(self.rubric, ensure_ascii=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "must contain exactly model_id and scenario_id",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_paired_models_must_have_both_declared_scenarios(self) -> None:
        self.rubric["paired_stability"]["required_model_ids"] = ["model-two"]
        (self.eval_root / "rubric.json").write_text(
            json.dumps(self.rubric, ensure_ascii=False),
            encoding="utf-8",
        )
        self._write_all_runs()

        with self.assertRaisesRegex(
            self.builder.GreenBuildError,
            "paired stability is missing model-two/A2",
        ):
            self.builder.build_results(
                repo_root=ROOT,
                eval_root=self.eval_root,
            )

        self.assertFalse((self.eval_root / "results.json").exists())

    def test_unexercised_aggregate_metric_is_recorded_without_passing_claim(
        self,
    ) -> None:
        self.scenarios.append(
            {
                "id": "C4",
                "prompt": "routing-only scenario",
                "executed_prompt": (
                    "请明确使用 CrossFrame ProMax。\n\nrouting-only scenario"
                ),
                "tags": ["routing"],
                "context": "fresh independent model run",
                "raw_output_path": (
                    f"{self.eval_root.relative_to(ROOT).as_posix()}"
                    "/raw/{model_id}/C4.md"
                ),
            }
        )
        self.rubric["scenario_ids"].append("C4")
        self.rubric["metrics"][1]["applicable_scenarios"] = ["C4"]
        (self.eval_root / "rubric.json").write_text(
            json.dumps(self.rubric, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.eval_root / "scenarios.json").write_text(
            json.dumps(self.scenarios, ensure_ascii=False),
            encoding="utf-8",
        )
        self._write_all_runs()

        results = self.builder.build_results(
            repo_root=ROOT,
            eval_root=self.eval_root,
        )

        self.assertEqual(
            results["aggregate"]["metrics"]["maximum_metric"],
            {
                "direction": "maximum",
                "threshold": 0.0,
                "numerator": 0,
                "denominator": 0,
                "rate": None,
                "status": "not_exercised",
                "threshold_covered": False,
                "passed": False,
            },
        )
        self.assertEqual(
            results["aggregate"]["unexercised_metric_ids"],
            ["maximum_metric"],
        )
        self.assertIs(
            results["aggregate"]["all_exercised_thresholds_passed"],
            True,
        )
        self.assertIs(results["aggregate"]["all_thresholds_passed"], False)


if __name__ == "__main__":
    unittest.main()
