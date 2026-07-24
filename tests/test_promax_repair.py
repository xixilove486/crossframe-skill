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

from promax_runtime.repair import build_repair_plan
from promax_runtime.schemas import validate_instance
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256


STAMP = "2026-07-23T00:00:00Z"
HASH_A = hashlib.sha256(b"failed-report").hexdigest()
MACHINE_FAILURE_FIELDS = {
    "error_type",
    "artifact",
    "affected_phase",
    "downstream_reset",
    "repair_action",
}


def _failed_report() -> dict[str, object]:
    return {
        "run_id": "promax-repair-test",
        "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        "report_sha256": HASH_A,
    }


def _failure(
    *,
    error_type: str,
    artifact: str,
    affected_phase: str,
    downstream_reset: list[str],
) -> dict[str, object]:
    return {
        "error_type": error_type,
        "artifact": artifact,
        "affected_phase": affected_phase,
        "downstream_reset": downstream_reset,
        "repair_action": "rebuild_artifact_regenerate_manifest_and_revalidate",
    }


def _machine_failures() -> list[dict[str, object]]:
    return [
        _failure(
            error_type="position_lock_stale",
            artifact="promax-position.locked.json",
            affected_phase="P8",
            downstream_reset=["P8", "P9", "P10", "P11"],
        ),
        _failure(
            error_type="claim_path_incomplete",
            artifact="promax-claim-path-graph.json",
            affected_phase="P5",
            downstream_reset=["P5", "P6", "P7", "P8", "P9", "P10", "P11"],
        ),
    ]


class ProMaxRepairPlanTests(unittest.TestCase):
    def _run_cli(
        self,
        report_path: Path,
        failures_path: Path,
        output_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        cli = ROOT / "scripts/build_crossframe_promax_repair_plan.py"
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(cli),
                "--failed-report",
                str(report_path),
                "--failures",
                str(failures_path),
                "--created-at",
                STAMP,
                "--output",
                str(output_path),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def _write_cli_inputs(self, directory: Path) -> tuple[Path, Path, bytes, bytes]:
        report_path = directory / "failed-report.json"
        failures_path = directory / "failures.json"
        report_bytes = json.dumps(_failed_report(), ensure_ascii=False).encode("utf-8")
        failures_bytes = json.dumps(
            _machine_failures(), ensure_ascii=False
        ).encode("utf-8")
        report_path.write_bytes(report_bytes)
        failures_path.write_bytes(failures_bytes)
        return report_path, failures_path, report_bytes, failures_bytes

    def _assert_alias_rejected(
        self,
        completed: subprocess.CompletedProcess[str],
        report_path: Path,
        failures_path: Path,
        report_bytes: bytes,
        failures_bytes: bytes,
    ) -> None:
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        status = json.loads(completed.stderr)
        self.assertEqual(status["status"], "error")
        self.assertEqual(set(status["error"]), MACHINE_FAILURE_FIELDS)
        self.assertEqual(report_path.read_bytes(), report_bytes)
        self.assertEqual(failures_path.read_bytes(), failures_bytes)

    def test_earliest_failure_only_sets_reset_boundary_and_forces_full_revalidation(self) -> None:
        try:
            plan = build_repair_plan(
                _failed_report(),
                _machine_failures(),
                created_at=STAMP,
            )
        except ValueError as error:
            self.fail(f"machine-readable failures must be accepted: {error}")

        validate_instance("promax-repair-plan.schema.json", plan)
        self.assertEqual(plan["reset_from_phase"], "P5")
        self.assertEqual(
            plan["invalidated_phases"],
            ["P5", "P6", "P7", "P8", "P9", "P10", "P11"],
        )
        self.assertEqual(plan["validation_state"], "not_run")
        self.assertIs(plan["manifest_regeneration_required"], True)
        self.assertIs(plan["revalidation_required"], True)
        self.assertEqual(plan["revalidation_scope"], "full-validator-set")
        self.assertEqual(plan["repair_actions"][0]["phase_id"], "P5")
        self.assertEqual(
            plan["repair_actions"][0]["expected_output_paths"],
            ["promax-claim-path-graph.json", "promax-position.locked.json"],
        )
        for failure in plan["failures"]:
            self.assertEqual(set(failure), MACHINE_FAILURE_FIELDS)

    def test_forged_downstream_reset_is_rejected(self) -> None:
        forged = _machine_failures()
        forged[1]["downstream_reset"] = ["P5", "P11"]
        with self.assertRaisesRegex(ValueError, "downstream_reset|downstream"):
            build_repair_plan(_failed_report(), forged, created_at=STAMP)

    def test_cli_rejects_canonical_output_aliases_of_both_audit_inputs(self) -> None:
        aliases = ("report", "failures", "normalized-report")
        for alias in aliases:
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as directory:
                temp = Path(directory)
                report, failures, report_bytes, failures_bytes = self._write_cli_inputs(
                    temp
                )
                if alias == "report":
                    output = report
                elif alias == "failures":
                    output = failures
                else:
                    (temp / "nested").mkdir()
                    output = temp / "nested" / ".." / report.name
                completed = self._run_cli(report, failures, output)
                self._assert_alias_rejected(
                    completed,
                    report,
                    failures,
                    report_bytes,
                    failures_bytes,
                )

    def test_cli_rejects_existing_hardlink_output_alias(self) -> None:
        for input_name in ("report", "failures"):
            with self.subTest(input=input_name), tempfile.TemporaryDirectory() as directory:
                temp = Path(directory)
                report, failures, report_bytes, failures_bytes = self._write_cli_inputs(
                    temp
                )
                output = temp / "hardlink-plan.json"
                linked_input = report if input_name == "report" else failures
                try:
                    os.link(linked_input, output)
                except OSError as error:
                    self.skipTest(f"hard links unavailable: {error}")
                completed = self._run_cli(report, failures, output)
                self._assert_alias_rejected(
                    completed,
                    report,
                    failures,
                    report_bytes,
                    failures_bytes,
                )

    def test_cli_rejects_existing_symlink_output_alias(self) -> None:
        for input_name in ("report", "failures"):
            with self.subTest(input=input_name), tempfile.TemporaryDirectory() as directory:
                temp = Path(directory)
                report, failures, report_bytes, failures_bytes = self._write_cli_inputs(
                    temp
                )
                output = temp / "symlink-plan.json"
                linked_input = report if input_name == "report" else failures
                try:
                    os.symlink(linked_input, output)
                except OSError as error:
                    self.skipTest(f"symbolic links unavailable: {error}")
                completed = self._run_cli(report, failures, output)
                self._assert_alias_rejected(
                    completed,
                    report,
                    failures,
                    report_bytes,
                    failures_bytes,
                )

    def test_root_cli_is_thin_structured_and_returns_nonzero_for_bad_input(self) -> None:
        cli = ROOT / "scripts/build_crossframe_promax_repair_plan.py"
        self.assertTrue(cli.is_file(), "root repair-plan CLI is missing")
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            report_path = temp / "failed-report.json"
            failures_path = temp / "failures.json"
            output_path = temp / "promax-repair-plan.json"
            report_path.write_text(
                json.dumps(_failed_report(), ensure_ascii=False),
                encoding="utf-8",
            )
            failures_path.write_text(
                json.dumps(_machine_failures(), ensure_ascii=False),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(cli),
                    "--failed-report",
                    str(report_path),
                    "--failures",
                    str(failures_path),
                    "--created-at",
                    STAMP,
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            status = json.loads(completed.stdout)
            self.assertEqual(status["status"], "ok")
            self.assertEqual(status["repair_plan"]["validation_state"], "not_run")
            persisted = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted, status["repair_plan"])

            failures_path.write_text("{}", encoding="utf-8")
            failed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(cli),
                    "--failed-report",
                    str(report_path),
                    "--failures",
                    str(failures_path),
                    "--created-at",
                    STAMP,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(failed.returncode, 0)
            failure_status = json.loads(failed.stderr)
            self.assertEqual(failure_status["status"], "error")
            self.assertEqual(set(failure_status["error"]), MACHINE_FAILURE_FIELDS)
            self.assertEqual(
                failure_status["error"]["error_type"],
                "repair_plan_input_invalid",
            )

            missing_args = subprocess.run(
                [sys.executable, "-B", str(cli)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(missing_args.returncode, 0)
            try:
                missing_status = json.loads(missing_args.stderr)
            except json.JSONDecodeError as error:
                self.fail(f"argument failure was not structured JSON: {error}")
            self.assertEqual(missing_status["status"], "error")
            self.assertEqual(set(missing_status["error"]), MACHINE_FAILURE_FIELDS)


if __name__ == "__main__":
    unittest.main()
