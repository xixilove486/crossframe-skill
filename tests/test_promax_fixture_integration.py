from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

import check_crossframe_promax_artifacts as checker


CATALOG_PATH = ROOT / "tests/fixtures/promax-runtime/scenarios.json"
FACTORY_CLI = ROOT / "scripts/crossframe_promax_fixture_factory.py"
ADVERSARIAL_SCENARIOS = (
    "marker-stuffing",
    "empty-strings",
    "forged-read-coverage",
    "equal-count-source-mutation",
    "unsupported-url",
    "duplicate-sources-independent",
    "missing-reverse",
    "no-action-omitted",
    "stance-flip",
    "authorization-leakage",
    "untyped-examples",
    "phase-replay",
    "stale-manifest",
    "wrong-continuation-parent",
)


def load_catalog() -> dict[str, object]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def parse_json_stdout(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    text = result.stdout.strip()
    if not text:
        raise AssertionError(
            f"command emitted no JSON stdout; stderr was:\n{result.stderr}"
        )
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        lines = [line for line in text.splitlines() if line.strip()]
        try:
            parsed = json.loads(lines[-1])
        except (IndexError, json.JSONDecodeError) as error:
            raise AssertionError(f"command stdout is not JSON:\n{text}") from error
    if not isinstance(parsed, dict):
        raise AssertionError("command JSON output must be an object")
    return parsed


def tree_snapshot(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


class ProMaxFixtureEndToEndTests(unittest.TestCase):
    _temp: tempfile.TemporaryDirectory[str]
    _first: Path
    _second: Path
    _materialize_status: dict[str, dict[str, object]] | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        root = Path(cls._temp.name)
        cls._first = root / "first"
        cls._second = root / "second"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()

    @classmethod
    def _command_environment(cls) -> dict[str, str]:
        environment = dict(os.environ)
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment

    @classmethod
    def _materialize_all_twice(cls) -> dict[str, dict[str, object]]:
        if cls._materialize_status is not None:
            return cls._materialize_status
        scenarios = load_catalog()["scenarios"]
        if not isinstance(scenarios, list):
            raise AssertionError("scenario catalog must contain an array")
        statuses: dict[str, dict[str, object]] = {}
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                raise AssertionError("scenario catalog item must be an object")
            scenario_id = str(scenario["scenario_id"])
            for parent in (cls._first, cls._second):
                workspace = parent / scenario_id
                result = subprocess.run(
                    [
                        sys.executable,
                        str(FACTORY_CLI),
                        "materialize",
                        "--repo",
                        str(ROOT),
                        "--scenario",
                        scenario_id,
                        "--output",
                        str(workspace),
                        "--json",
                    ],
                    cwd=ROOT,
                    env=cls._command_environment(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                if result.returncode != 0:
                    raise AssertionError(
                        f"factory failed for {scenario_id}:\n{result.stderr}"
                    )
                status = parse_json_stdout(result)
                if status.get("status") != "ok":
                    raise AssertionError(
                        f"factory did not report ok for {scenario_id}: {status}"
                    )
                if status.get("scenario_id") != scenario_id:
                    raise AssertionError("factory status changed the requested scenario_id")
                if status.get("mutation") != scenario.get("mutation"):
                    raise AssertionError(
                        f"factory did not report the catalog mutation for {scenario_id}"
                    )
                statuses[scenario_id] = status
        cls._materialize_status = statuses
        return statuses

    def test_01_catalog_has_sixteen_closed_single_mutation_scenarios(self) -> None:
        catalog = load_catalog()
        self.assertEqual(set(catalog), {"schema_version", "scenarios"})
        self.assertEqual(catalog["schema_version"], 1)
        scenarios = catalog["scenarios"]
        self.assertEqual(len(scenarios), 16)
        self.assertEqual(
            len({scenario["scenario_id"] for scenario in scenarios}),
            16,
        )
        mutations: list[str] = []
        for scenario in scenarios:
            fixture_class = scenario["fixture_class"]
            if fixture_class == "positive":
                self.assertIsNone(scenario["mutation"])
            else:
                self.assertIsInstance(scenario["mutation"], str)
                self.assertTrue(scenario["mutation"].strip())
                mutations.append(scenario["mutation"])
        self.assertEqual(len(mutations), 15)
        self.assertEqual(len(set(mutations)), 15)

    def test_02_every_scenario_materializes_deterministically_with_one_reported_mutation(self) -> None:
        statuses = self._materialize_all_twice()
        self.assertEqual(len(statuses), 16)
        for scenario_id in sorted(statuses):
            first = tree_snapshot(self._first / scenario_id)
            second = tree_snapshot(self._second / scenario_id)
            with self.subTest(scenario=scenario_id):
                self.assertTrue(first, "materialized fixture must contain artifacts")
                self.assertEqual(first, second)

    def test_03_checker_distinguishes_pass_incomplete_and_exact_adversarial_errors(self) -> None:
        self._materialize_all_twice()
        catalog = load_catalog()["scenarios"]
        records = {
            scenario["scenario_id"]: scenario
            for scenario in catalog
        }
        selected = (
            "valid-complete",
            "artifact-incomplete",
            *ADVERSARIAL_SCENARIOS,
        )
        for scenario_id in selected:
            report = checker.validate_workspace(
                self._first / scenario_id,
                repo=ROOT,
                final_chat=True,
                allow_test_fixture=True,
            )
            returncode = (
                0
                if report["overall_status"] == "pass"
                else 2
                if report["overall_status"] == "blocked"
                else 1
            )
            scenario = records[scenario_id]
            with self.subTest(scenario=scenario_id):
                if scenario_id == "valid-complete":
                    self.assertEqual(returncode, 0)
                    self.assertEqual(report.get("overall_status"), "pass")
                    self.assertEqual(report.get("completion_status"), "promax-complete")
                    self.assertEqual(report.get("failures"), [])
                    continue
                if scenario_id == "artifact-incomplete":
                    self.assertIn(returncode, {0, 2})
                    self.assertEqual(report.get("overall_status"), "blocked")
                    self.assertEqual(
                        report.get("completion_status"),
                        scenario["expected_outcome"],
                    )
                    self.assertEqual(report.get("failures"), [])
                    continue
                self.assertNotEqual(returncode, 0)
                self.assertEqual(report.get("overall_status"), "fail")
                failures = report.get("failures")
                self.assertIsInstance(failures, list)
                self.assertTrue(failures)
                self.assertEqual(
                    failures[0].get("error_type"),
                    scenario["expected_error_type"],
                )


if __name__ == "__main__":
    unittest.main()
