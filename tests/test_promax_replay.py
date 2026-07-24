from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime import build_capability_disclosure, initialize_run
from promax_runtime.artifacts import build_artifact_manifest, inventory_artifacts
from promax_runtime import validation


STAMP = "2026-07-23T00:00:00Z"
HASH_A = hashlib.sha256(b"phase-a").hexdigest()
HASH_B = hashlib.sha256(b"not-current").hexdigest()
MACHINE_FAILURE_FIELDS = {
    "error_type",
    "artifact",
    "affected_phase",
    "downstream_reset",
    "repair_action",
}
VALIDATOR_VERSIONS = {
    "schema": "1.0.0",
    "source-integrity": "1.0.0",
    "state-machine": "1.0.0",
}


def _artifact_ref(path: str, digest: str) -> dict[str, object]:
    return {
        "path": path,
        "sha256": digest,
        "media_type": "application/json",
    }


class ReplayFixture:
    def __init__(self, run_dir: Path) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            validator_ids=tuple(VALIDATOR_VERSIONS),
        )
        initialized = initialize_run(
            ROOT,
            "use crossframe-promax",
            mode="promax-complete",
            capabilities=capabilities,
            created_at=STAMP,
            run_id="promax-replay-test",
            recommendation_required=False,
        )
        self.contract = initialized["run_contract"]
        self.run_dir = run_dir
        self.known: dict[str, str] = {}
        self.role_records: list[dict[str, object]] = []
        output_phases = ("P4", "P6", "P7", "P8", "P10")
        metadata: dict[str, dict[str, object]] = {}

        for index, plan in enumerate(self.contract["role_plan"]):
            sequence = plan["sequence"]
            input_path = f"role-inputs/{sequence}.json"
            output_path = f"role-outputs/{sequence}.json"
            input_bytes = input_path.encode("utf-8")
            output_bytes = output_path.encode("utf-8")
            input_sha = hashlib.sha256(input_bytes).hexdigest()
            output_sha = hashlib.sha256(output_bytes).hexdigest()
            self.known[input_path] = input_sha
            self.known[output_path] = output_sha
            for path, body in ((input_path, input_bytes), (output_path, output_bytes)):
                target = run_dir / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            metadata[input_path] = {
                "generating_phase": "P0",
                "input_artifact_sha256s": [],
                "status": "current",
            }
            metadata[output_path] = {
                "generating_phase": output_phases[index],
                "input_artifact_sha256s": [input_sha],
                "status": "current",
            }
            self.role_records.append(
                {
                    **plan,
                    "input_artifacts": [_artifact_ref(input_path, input_sha)],
                    "observed_input_artifacts": [_artifact_ref(input_path, input_sha)],
                    "output_artifacts": [_artifact_ref(output_path, output_sha)],
                    "status": "completed",
                }
            )

        artifacts = inventory_artifacts(run_dir, metadata)
        self.manifest = build_artifact_manifest(
            self.contract,
            phase_chain_head_sha256=HASH_A,
            artifacts=artifacts,
            role_records=self.role_records,
            generated_at=STAMP,
        )
        checks = [
            {
                "validator_id": validator_id,
                "status": "pass",
                "checked_artifact_paths": sorted(self.known),
                "failure_codes": [],
            }
            for validator_id in VALIDATOR_VERSIONS
        ]
        self.report = validation.build_validator_report(
            self.contract,
            self.manifest,
            validator_versions=VALIDATOR_VERSIONS,
            checks=checks,
            validation_attempt=1,
            completion_status="promax-complete",
            validated_at=STAMP,
            run_dir=run_dir,
        )


class ProMaxReplayTests(unittest.TestCase):
    def _machine_failure(self, error: BaseException) -> dict[str, object]:
        self.assertTrue(
            hasattr(error, "as_dict"),
            f"replay failure is not machine-readable: {error!r}",
        )
        failure = error.as_dict()
        self.assertEqual(set(failure), MACHINE_FAILURE_FIELDS)
        self.assertIn(failure["affected_phase"], tuple(f"P{i}" for i in range(12)))
        self.assertIsInstance(failure["downstream_reset"], list)
        self.assertTrue(failure["repair_action"])
        return failure

    def test_old_report_replay_bindings_emit_exact_machine_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ReplayFixture(Path(directory))
            mutations = {
                "run_nonce": "z" * 64,
                "request_sha256": HASH_B,
                "source_snapshot_sha256": HASH_B,
                "phase_chain_head_sha256": HASH_B,
                "manifest_sha256": HASH_B,
                "validator_set_sha256": HASH_B,
                "validation_attempt": 2,
            }
            for field, replacement in mutations.items():
                stale = copy.deepcopy(fixture.report)
                stale[field] = replacement
                with self.subTest(field=field):
                    with self.assertRaises(validation.ReplayBindingError) as caught:
                        validation.validate_validator_report_freshness(
                            stale,
                            fixture.contract,
                            fixture.manifest,
                            validator_versions=VALIDATOR_VERSIONS,
                            expected_validation_attempt=1,
                            run_dir=fixture.run_dir,
                        )
                    failure = self._machine_failure(caught.exception)
                    self.assertEqual(failure["artifact"], "promax-validator-report.json")
                    self.assertEqual(failure["affected_phase"], "P11")
                    self.assertEqual(failure["downstream_reset"], ["P11"])

    def test_changed_current_bytes_identify_the_generating_phase_for_local_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ReplayFixture(Path(directory))
            changed_path = "role-outputs/1.json"
            (fixture.run_dir / changed_path).write_bytes(b"changed after validation")

            with self.assertRaises(validation.ReplayBindingError) as caught:
                validation.validate_validator_report_freshness(
                    fixture.report,
                    fixture.contract,
                    fixture.manifest,
                    validator_versions=VALIDATOR_VERSIONS,
                    expected_validation_attempt=1,
                    run_dir=fixture.run_dir,
                )

            failure = self._machine_failure(caught.exception)
            self.assertEqual(failure["error_type"], "current_artifact_bytes_stale")
            self.assertEqual(failure["artifact"], changed_path)
            self.assertEqual(failure["affected_phase"], "P4")
            self.assertEqual(
                failure["downstream_reset"],
                ["P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11"],
            )

    def test_tampered_manifest_is_a_p10_machine_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ReplayFixture(Path(directory))
            tampered = copy.deepcopy(fixture.manifest)
            tampered["generated_at"] = "2026-07-23T00:00:01Z"

            with self.assertRaises(validation.ReplayBindingError) as caught:
                validation.validate_validator_report_freshness(
                    fixture.report,
                    fixture.contract,
                    tampered,
                    validator_versions=VALIDATOR_VERSIONS,
                    expected_validation_attempt=1,
                    run_dir=fixture.run_dir,
                )

            failure = self._machine_failure(caught.exception)
            self.assertEqual(failure["error_type"], "manifest_replay_or_tamper")
            self.assertEqual(failure["artifact"], "promax-artifact-manifest.json")
            self.assertEqual(failure["affected_phase"], "P10")
            self.assertEqual(failure["downstream_reset"], ["P10", "P11"])

    def test_continuation_must_bind_the_current_manifest_and_a_current_parent_artifact(self) -> None:
        self.assertTrue(
            hasattr(validation, "validate_continuation_parent"),
            "continuation parent validator is missing",
        )
        validate_parent = validation.validate_continuation_parent
        with tempfile.TemporaryDirectory() as directory:
            fixture = ReplayFixture(Path(directory))
            parent_sha = fixture.known["role-outputs/5.json"]
            ledger = {
                "schema_id": "crossframe.promax.v8.continuation-ledger",
                "schema_version": 1,
                "run_id": fixture.contract["run_id"],
                "source_snapshot_sha256": fixture.contract[
                    "source_snapshot_sha256"
                ],
                "parent_manifest_sha256": fixture.manifest["manifest_sha256"],
                "continuations": [
                    {
                        "continuation_id": "CONT-1",
                        "sequence": 1,
                        "parent_artifact_sha256": parent_sha,
                        "resume_from_phase": "P10",
                        "pending_artifact_paths": ["continuations/part-2.md"],
                        "reason": "delivery continues in the next artifact",
                        "status": "pending",
                    }
                ],
                "updated_at": STAMP,
            }
            self.assertEqual(
                validate_parent(ledger, fixture.manifest),
                ledger,
            )

            for field, replacement in (
                ("parent_manifest_sha256", HASH_B),
                ("parent_artifact_sha256", HASH_B),
            ):
                stale = copy.deepcopy(ledger)
                if field == "parent_artifact_sha256":
                    stale["continuations"][0][field] = replacement
                else:
                    stale[field] = replacement
                with self.subTest(field=field):
                    with self.assertRaises(validation.ReplayBindingError) as caught:
                        validate_parent(stale, fixture.manifest)
                    failure = self._machine_failure(caught.exception)
                    self.assertEqual(
                        failure["artifact"], "promax-continuation-ledger.json"
                    )
                    self.assertEqual(failure["affected_phase"], "P10")
                    self.assertEqual(failure["downstream_reset"], ["P10", "P11"])


if __name__ == "__main__":
    unittest.main()
