from __future__ import annotations

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

from promax_runtime import (
    ROLE_IDS,
    V8_SOURCE_SNAPSHOT_SHA256,
    build_capability_disclosure,
    build_role_plan,
    initialize_run,
)
from promax_runtime.artifacts import (
    build_artifact_manifest,
    inventory_artifacts,
    validate_role_records,
)
from promax_runtime.claim_path import validate_claim_path_graph
from promax_runtime.concept_closure import validate_concept_disposition
from promax_runtime.jsonio import sha256_json
from promax_runtime.position import validate_position_lock
from promax_runtime.repair import build_repair_plan
from promax_runtime.retrieval import validate_retrieval_ledger
from promax_runtime.source_integrity import build_source_snapshot, sha256_file
from promax_runtime import source_integrity
from promax_runtime.validation import (
    ReplayBindingError,
    build_validator_report,
    validate_validator_report_freshness,
    validator_set_sha256,
)
import crossframe_promax_runtime


STAMP = "2026-07-23T00:00:00Z"
RUN_ID = "promax-run-contract-test"
HASH_A = hashlib.sha256(b"artifact-a").hexdigest()
HASH_B = hashlib.sha256(b"artifact-b").hexdigest()


def artifact_ref(path: str, sha256: str) -> dict[str, object]:
    return {
        "path": path,
        "sha256": sha256,
        "media_type": "application/json",
    }


def actual_role_records(
    contract: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    records: list[dict[str, object]] = []
    known: dict[str, str] = {}
    for plan in contract["role_plan"]:
        sequence = plan["sequence"]
        input_path = f"role-inputs/{sequence}.json"
        output_path = f"role-outputs/{sequence}.json"
        input_sha = hashlib.sha256(input_path.encode("utf-8")).hexdigest()
        output_sha = hashlib.sha256(output_path.encode("utf-8")).hexdigest()
        known[input_path] = input_sha
        known[output_path] = output_sha
        input_ref = artifact_ref(input_path, input_sha)
        output_ref = artifact_ref(output_path, output_sha)
        record = {
            **plan,
            "input_artifacts": [input_ref],
            "observed_input_artifacts": [copy.deepcopy(input_ref)],
            "output_artifacts": [output_ref],
            "status": "completed",
        }
        if plan["execution_mode"] == "multi-agent-isolated":
            agent_id = f"runtime-agent-{sequence}"
            claim = {
                "run_id": contract["run_id"],
                "request_sha256": contract["request_sha256"],
                "source_snapshot_sha256": contract["source_snapshot_sha256"],
                "role_id": plan["role_id"],
                "sequence": sequence,
                "agent_id": agent_id,
                "completed_at": STAMP,
                "observed_input_artifacts": [copy.deepcopy(input_ref)],
                "produced_output_artifacts": [copy.deepcopy(output_ref)],
            }
            record["agent_id"] = agent_id
            record["execution_attestation"] = {
                "run_id": claim["run_id"],
                "request_sha256": claim["request_sha256"],
                "source_snapshot_sha256": claim["source_snapshot_sha256"],
                "completed_at": claim["completed_at"],
                "observed_input_artifacts": claim["observed_input_artifacts"],
                "produced_output_artifacts": claim["produced_output_artifacts"],
                "claim_sha256": sha256_json(claim),
            }
        records.append(record)
    return records, known


def initialized(
    *,
    request: str = "请明确调用 CrossFrame ProMax。",
    subagents: bool = True,
    mode: str = "promax-artifact-run",
) -> dict[str, dict[str, object]]:
    capabilities = build_capability_disclosure(
        subagents_available=subagents,
        max_parallelism=4 if subagents else 0,
        validator_ids=("schema", "source-integrity", "state-machine"),
    )
    return initialize_run(
        ROOT,
        request,
        mode=mode,
        capabilities=capabilities,
        created_at=STAMP,
        run_id=RUN_ID,
    )


class ProMaxRunInitializationTests(unittest.TestCase):
    def test_platform_selected_runtime_does_not_reparse_the_request_for_activation(
        self,
    ) -> None:
        for request in (
            "分析这个具体问题，直接进入完整推演。",
            "比较这个方案与 crossframe-max 的差异。",
        ):
            with self.subTest(request=request):
                contract = initialized(request=request)["run_contract"]
                self.assertEqual(
                    contract["requested_skill_names"], ["crossframe-promax"]
                )
                self.assertEqual(
                    contract["routing_conflict"],
                    {
                        "detected": False,
                        "conflicting_names": [],
                        "resolved_to": "crossframe-promax",
                        "priority_rule": (
                            "routing-priority-crossframe-promax-over-"
                            "crossframe-max-no-fallback"
                        ),
                        "fallback_allowed": False,
                    },
                )

    def test_initialization_freezes_the_recommendation_request_switch(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=True,
            max_parallelism=4,
            validator_ids=("schema",),
        )
        required = initialize_run(
            ROOT,
            "请用 CrossFrame ProMax。",
            mode="promax-artifact-run",
            capabilities=capabilities,
            created_at=STAMP,
            run_id=RUN_ID,
            recommendation_required=True,
        )
        self.assertIs(required["run_contract"]["recommendation_required"], True)

        defaulted = initialize_run(
            ROOT,
            "请用 CrossFrame ProMax。",
            mode="promax-artifact-run",
            capabilities=capabilities,
            created_at=STAMP,
            run_id=RUN_ID,
        )
        self.assertIs(defaulted["run_contract"]["recommendation_required"], False)

    def test_initialization_uses_token_hex_32_and_binds_the_exact_v8_snapshot(self) -> None:
        nonce = "ab" * 32
        capabilities = build_capability_disclosure(
            subagents_available=True,
            max_parallelism=4,
            validator_ids=("schema",),
        )
        with mock.patch("promax_runtime.artifacts.secrets.token_hex", return_value=nonce) as token_hex:
            result = initialize_run(
                ROOT,
                "请用 CrossFrame ProMax。",
                mode="promax-artifact-run",
                capabilities=capabilities,
                created_at=STAMP,
                run_id=RUN_ID,
            )
        token_hex.assert_called_once_with(32)

        contract = result["run_contract"]
        snapshot = result["source_snapshot"]
        self.assertEqual(contract["run_nonce"], nonce)
        self.assertEqual(len(contract["run_nonce"]), 64)
        self.assertEqual(
            contract["request_sha256"],
            hashlib.sha256("请用 CrossFrame ProMax。".encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            contract["source_snapshot_sha256"], V8_SOURCE_SNAPSHOT_SHA256
        )
        self.assertEqual(
            snapshot["source_snapshot_sha256"], V8_SOURCE_SNAPSHOT_SHA256
        )
        self.assertEqual(snapshot["paragraph_count"], 3863)
        self.assertEqual(snapshot["table_count"], 117)
        self.assertEqual(snapshot["section_count"], 16)

    def test_capabilities_select_five_ordered_real_or_sequential_role_plans(self) -> None:
        multi = build_capability_disclosure(
            subagents_available=True,
            max_parallelism=4,
            validator_ids=("schema", "source-integrity"),
        )
        single = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            validator_ids=("schema", "source-integrity"),
        )

        self.assertEqual(set(multi), {"files", "network", "subagents", "validators"})
        for capabilities, expected_mode in (
            (multi, "multi-agent-isolated"),
            (single, "single-agent-separated"),
        ):
            with self.subTest(mode=expected_mode):
                plan = build_role_plan(capabilities)
                self.assertEqual([item["role_id"] for item in plan], list(ROLE_IDS))
                self.assertEqual([item["sequence"] for item in plan], [1, 2, 3, 4, 5])
                self.assertEqual(
                    {item["execution_mode"] for item in plan}, {expected_mode}
                )
                self.assertEqual(
                    {item["exchange_protocol"] for item in plan},
                    {"structured-artifacts-only"},
                )
                for item in plan:
                    self.assertNotIn("status", item)
                    self.assertNotIn("output_artifacts", item)

        multi_contract = initialized(subagents=True)["run_contract"]
        single_contract = initialized(subagents=False)["run_contract"]
        self.assertEqual(multi_contract["orchestration_mode"], "multi-agent-isolated")
        self.assertEqual(
            single_contract["orchestration_mode"], "single-agent-separated"
        )

    def test_initialization_rejects_self_downgrade_modes(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            validator_ids=("schema",),
        )
        for request, mode in (
            ("do a deep analysis", "brief"),
            ("use crossframe-max", "promax-lite"),
        ):
            with self.subTest(request=request, mode=mode):
                with self.assertRaises(ValueError):
                    initialize_run(
                        ROOT,
                        request,
                        mode=mode,
                        capabilities=capabilities,
                        created_at=STAMP,
                        run_id=RUN_ID,
                    )

    def test_blocked_progress_requires_one_authorized_structured_blocker(self) -> None:
        capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            validator_ids=("schema",),
        )
        with self.assertRaises(ValueError):
            initialize_run(
                ROOT,
                "use crossframe-promax",
                mode="promax-blocked/progress",
                capabilities=capabilities,
                created_at=STAMP,
                run_id=RUN_ID,
            )
        with self.assertRaises(ValueError):
            initialize_run(
                ROOT,
                "use crossframe-promax",
                mode="promax-artifact-run",
                capabilities=capabilities,
                created_at=STAMP,
                run_id=RUN_ID,
                blocker={
                    "category": "source_unavailable",
                    "detail": "not allowed outside blocked mode",
                },
            )

        blocked_capabilities = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            validator_ids=(),
            validators_available=False,
            validators_executable=False,
        )
        result = initialize_run(
            ROOT,
            "use crossframe-promax",
            mode="promax-blocked/progress",
            capabilities=blocked_capabilities,
            created_at=STAMP,
            run_id=RUN_ID,
            blocker={
                "category": "required_tool_forbidden",
                "detail": "the required validator process cannot execute",
            },
        )
        self.assertEqual(
            result["run_contract"]["blocker"]["category"],
            "required_tool_forbidden",
        )

        with tempfile.TemporaryDirectory() as directory:
            source_blocked = initialize_run(
                Path(directory),
                "use crossframe-promax",
                mode="promax-blocked/progress",
                capabilities=capabilities,
                created_at=STAMP,
                run_id=RUN_ID,
                blocker={
                    "category": "source_unavailable",
                    "detail": "the canonical v8 assets cannot be read",
                },
            )
        self.assertEqual(set(source_blocked), {"run_contract"})
        with self.assertRaisesRegex(ValueError, "source_unavailable"):
            initialize_run(
                ROOT,
                "use crossframe-promax",
                mode="promax-blocked/progress",
                capabilities=capabilities,
                created_at=STAMP,
                run_id=RUN_ID,
                blocker={
                    "category": "source_unavailable",
                    "detail": "false blocker",
                },
            )

    def test_capability_disclosure_normalizes_validators_and_requires_honest_blocking(self) -> None:
        with self.assertRaisesRegex(ValueError, "iterable|text"):
            build_capability_disclosure(
                subagents_available=False,
                max_parallelism=0,
                validator_ids="schema",
            )
        with self.assertRaisesRegex(ValueError, "unique|normalization"):
            build_capability_disclosure(
                subagents_available=False,
                max_parallelism=0,
                validator_ids=("schema", " schema "),
            )
        unavailable = build_capability_disclosure(
            subagents_available=False,
            max_parallelism=0,
            files_writable=False,
        )
        self.assertIn("file writes unavailable", unavailable["files"]["limitations"])
        with self.assertRaisesRegex(ValueError, "blocked/progress"):
            initialize_run(
                ROOT,
                "use crossframe-promax",
                mode="promax-artifact-run",
                capabilities=unavailable,
                created_at=STAMP,
                run_id=RUN_ID,
            )


class ProMaxSourceSnapshotTests(unittest.TestCase):
    def test_snapshot_hashes_are_derived_from_the_canonical_v8_assets(self) -> None:
        snapshot = build_source_snapshot(ROOT, verified_at=STAMP)
        references = ROOT / "skills/crossframe-promax/references"
        self.assertEqual(
            snapshot["source_manifest_sha256"],
            sha256_file(references / "source_manifest.json"),
        )
        self.assertEqual(
            snapshot["concept_registry_sha256"],
            sha256_file(references / "concept-registry/v8-concept-registry.json"),
        )
        self.assertEqual(
            snapshot["contract_map_sha256"],
            sha256_file(references / "concept-contracts/v8-contract-map.json"),
        )
        self.assertEqual(
            snapshot["route_map_sha256"],
            sha256_file(references / "v8-route-map.json"),
        )
        self.assertEqual(snapshot["framework_version"], "v8.0")
        self.assertNotIn("lineage", snapshot)

    def test_snapshot_rejects_control_asset_swap_between_parse_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            target_references = repo / "skills/crossframe-promax/references"
            target_references.parent.mkdir(parents=True)
            shutil.copytree(
                ROOT / "skills/crossframe-promax/references",
                target_references,
            )
            concept_path = (
                target_references
                / "concept-registry"
                / "v8-concept-registry.json"
            )
            original_sha256_file = source_integrity.sha256_file
            swapped = False

            def swap_before_recheck(path: Path | str) -> str:
                nonlocal swapped
                if not swapped:
                    swapped = True
                    concept_path.write_text("{}\n", encoding="utf-8")
                return original_sha256_file(path)

            with mock.patch.object(
                source_integrity,
                "sha256_file",
                side_effect=swap_before_recheck,
            ):
                with self.assertRaisesRegex(ValueError, "changed"):
                    build_source_snapshot(repo, verified_at=STAMP)


class ProMaxStructuredRoleExchangeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = initialized()["run_contract"]
        self.records, self.known = actual_role_records(self.contract)

    def test_all_five_actual_role_records_are_structured_and_hash_bound(self) -> None:
        validated = validate_role_records(self.contract, self.records, self.known)
        self.assertEqual([item["role_id"] for item in validated], list(ROLE_IDS))

    def test_execution_attestation_cannot_claim_different_published_bytes(self) -> None:
        records = copy.deepcopy(self.records)
        record = records[1]
        attestation = record["execution_attestation"]
        attestation["produced_output_artifacts"][0]["sha256"] = HASH_A
        claim = {
            "run_id": self.contract["run_id"],
            "request_sha256": self.contract["request_sha256"],
            "source_snapshot_sha256": self.contract["source_snapshot_sha256"],
            "role_id": record["role_id"],
            "sequence": record["sequence"],
            "agent_id": record["agent_id"],
            "completed_at": attestation["completed_at"],
            "observed_input_artifacts": attestation["observed_input_artifacts"],
            "produced_output_artifacts": attestation["produced_output_artifacts"],
        }
        attestation["claim_sha256"] = sha256_json(claim)

        with self.assertRaisesRegex(ValueError, "published artifact bytes"):
            validate_role_records(self.contract, records, self.known)

    def test_undeclared_observation_wrong_output_or_free_memory_is_rejected(self) -> None:
        cases: list[list[dict[str, object]]] = []

        undeclared = copy.deepcopy(self.records)
        undeclared[0]["observed_input_artifacts"] = [
            artifact_ref("undeclared.json", HASH_A)
        ]
        cases.append(undeclared)

        wrong_output = copy.deepcopy(self.records)
        wrong_output[1]["output_artifacts"][0]["sha256"] = HASH_B
        cases.append(wrong_output)

        free_memory = copy.deepcopy(self.records)
        free_memory[2]["free_memory_summary"] = "trust me"
        cases.append(free_memory)

        wrong_media = copy.deepcopy(self.records)
        wrong_media[3]["output_artifacts"][0]["media_type"] = "text/plain"
        cases.append(wrong_media)

        duplicate_output = copy.deepcopy(self.records)
        duplicate_output[4]["output_artifacts"] = copy.deepcopy(
            duplicate_output[3]["output_artifacts"]
        )
        cases.append(duplicate_output)

        reads_own_output = copy.deepcopy(self.records)
        reads_own_output[1]["input_artifacts"] = copy.deepcopy(
            reads_own_output[1]["output_artifacts"]
        )
        reads_own_output[1]["observed_input_artifacts"] = copy.deepcopy(
            reads_own_output[1]["output_artifacts"]
        )
        cases.append(reads_own_output)

        reads_future_output = copy.deepcopy(self.records)
        reads_future_output[0]["input_artifacts"] = copy.deepcopy(
            reads_future_output[4]["output_artifacts"]
        )
        reads_future_output[0]["observed_input_artifacts"] = copy.deepcopy(
            reads_future_output[4]["output_artifacts"]
        )
        cases.append(reads_future_output)

        skipped = copy.deepcopy(self.records[:-1])
        cases.append(skipped)

        for records in cases:
            with self.subTest(records=len(records)):
                with self.assertRaises(ValueError):
                    validate_role_records(self.contract, records, self.known)


class ProMaxArtifactAndReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        initialized_run = initialized(mode="promax-complete")
        self.contract = initialized_run["run_contract"]
        self.records, self.known = actual_role_records(self.contract)

    def _manifest(self, root: Path) -> dict[str, object]:
        metadata: dict[str, dict[str, object]] = {}
        output_phases = ("P4", "P6", "P7", "P8", "P10")
        output_metadata: dict[str, tuple[str, list[str]]] = {}
        for index, record in enumerate(self.records):
            observed_hashes = [
                item["sha256"] for item in record["observed_input_artifacts"]
            ]
            for output in record["output_artifacts"]:
                output_metadata[output["path"]] = (
                    output_phases[index],
                    observed_hashes,
                )
        for path, expected_sha in self.known.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            data = path.encode("utf-8")
            target.write_bytes(data)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected_sha)
            output_phase, lineage = output_metadata.get(path, ("P0", []))
            metadata[path] = {
                "generating_phase": output_phase,
                "input_artifact_sha256s": lineage,
                "status": "current",
            }
        artifacts = inventory_artifacts(root, metadata)
        return build_artifact_manifest(
            self.contract,
            phase_chain_head_sha256=HASH_A,
            artifacts=artifacts,
            role_records=self.records,
            generated_at=STAMP,
        )

    def test_inventory_manifest_and_role_records_are_bound_to_current_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            self.assertEqual(manifest["mode"], "promax-complete")
            self.assertEqual(
                manifest["run_contract_sha256"],
                hashlib.sha256(
                    json.dumps(
                        self.contract,
                        ensure_ascii=False,
                        allow_nan=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest(),
            )
            body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
            expected_manifest_sha = hashlib.sha256(
                json.dumps(
                    body,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            self.assertEqual(manifest["manifest_sha256"], expected_manifest_sha)

    def test_inventory_rejects_traversal_missing_files_and_hidden_reasoning_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (
                "../escape.json",
                "missing.json",
                "a//b.json",
                "./a.json",
                "a/./b.json",
                "artifacts/chain-of-thought.md",
                "scratchpad/internal-monologue.txt",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        inventory_artifacts(
                            root,
                            {
                                path: {
                                    "generating_phase": "P0",
                                    "input_artifact_sha256s": [],
                                    "status": "current",
                                }
                            },
                        )

    def test_inventory_rejects_casefold_path_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Alias.json").write_text("{}", encoding="utf-8")
            metadata = {
                "Alias.json": {
                    "generating_phase": "P0",
                    "input_artifact_sha256s": [],
                    "status": "current",
                },
                "alias.json": {
                    "generating_phase": "P0",
                    "input_artifact_sha256s": [],
                    "status": "current",
                },
            }
            with self.assertRaisesRegex(ValueError, "alias|case|duplicate"):
                inventory_artifacts(root, metadata)

    def test_inventory_rejects_hardlinked_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            root.mkdir()
            outside = base / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            linked = root / "linked.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                self.skipTest(f"hard links unavailable on this host: {error}")
            with self.assertRaisesRegex(ValueError, "hard|link|regular"):
                inventory_artifacts(
                    root,
                    {
                        "linked.json": {
                            "generating_phase": "P0",
                            "input_artifact_sha256s": [],
                            "status": "current",
                        }
                    },
                )

    def test_inventory_rechecks_the_open_file_against_link_swap_races(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            root.mkdir()
            target = root / "artifact.json"
            target.write_text("original", encoding="utf-8")
            outside = base / "outside.json"
            outside.write_text("outside", encoding="utf-8")
            original_open = Path.open
            swapped = False

            def swap_before_open(path: Path, *args: object, **kwargs: object):
                nonlocal swapped
                if path == target and not swapped:
                    swapped = True
                    target.unlink()
                    os.link(outside, target)
                return original_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", autospec=True, side_effect=swap_before_open):
                with self.assertRaisesRegex(ValueError, "changed|hard|link|regular"):
                    inventory_artifacts(
                        root,
                        {
                            "artifact.json": {
                                "generating_phase": "P0",
                                "input_artifact_sha256s": [],
                                "status": "current",
                            }
                        },
                    )

    def test_role_records_cannot_bind_invalidated_or_superseded_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._manifest(Path(directory))
            artifacts = copy.deepcopy(manifest["artifacts"])
            referenced_path = self.records[0]["input_artifacts"][0]["path"]
            for artifact in artifacts:
                if artifact["path"] == referenced_path:
                    artifact["status"] = "invalidated"
                    break
            with self.assertRaisesRegex(ValueError, "current|artifact|role"):
                build_artifact_manifest(
                    self.contract,
                    phase_chain_head_sha256=HASH_A,
                    artifacts=artifacts,
                    role_records=self.records,
                    generated_at=STAMP,
                )

    def test_role_inputs_require_prior_producers_and_outputs_bind_observed_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            artifacts = copy.deepcopy(manifest["artifacts"])

            broken_lineage = copy.deepcopy(artifacts)
            first_output = self.records[0]["output_artifacts"][0]["path"]
            for artifact in broken_lineage:
                if artifact["path"] == first_output:
                    artifact["input_artifact_sha256s"] = []
                    break
            with self.assertRaisesRegex(ValueError, "lineage|observed"):
                build_artifact_manifest(
                    self.contract,
                    phase_chain_head_sha256=HASH_A,
                    artifacts=broken_lineage,
                    role_records=self.records,
                    generated_at=STAMP,
                )

            orphan_path = "orphan-future.json"
            orphan_bytes = orphan_path.encode("utf-8")
            (root / orphan_path).write_bytes(orphan_bytes)
            orphan_sha = hashlib.sha256(orphan_bytes).hexdigest()
            artifacts.append(
                {
                    "path": orphan_path,
                    "sha256": orphan_sha,
                    "media_type": "application/json",
                    "generating_phase": "P10",
                    "input_artifact_sha256s": [],
                    "status": "current",
                }
            )
            future_read = copy.deepcopy(self.records)
            future_ref = artifact_ref(orphan_path, orphan_sha)
            future_read[0]["input_artifacts"] = [future_ref]
            future_read[0]["observed_input_artifacts"] = [future_ref]
            for artifact in artifacts:
                if artifact["path"] == first_output:
                    artifact["input_artifact_sha256s"] = [orphan_sha]
                    break
            with self.assertRaisesRegex(ValueError, "prior producer|P3"):
                build_artifact_manifest(
                    self.contract,
                    phase_chain_head_sha256=HASH_A,
                    artifacts=artifacts,
                    role_records=future_read,
                    generated_at=STAMP,
                )

    def test_validator_report_replay_bindings_and_artifact_freshness_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._manifest(Path(directory))
            versions = {
                "schema": "1.0.0",
                "source-integrity": "1.0.0",
                "state-machine": "1.0.0",
            }
            checks = [
                {
                    "validator_id": validator_id,
                    "status": "pass",
                    "checked_artifact_paths": sorted(self.known),
                    "failure_codes": [],
                }
                for validator_id in versions
            ]
            with self.assertRaisesRegex(ValueError, "validator|check"):
                build_validator_report(
                    self.contract,
                    manifest,
                    validator_versions=versions,
                    checks=checks[:-1],
                    validation_attempt=1,
                    completion_status="promax-complete",
                    validated_at=STAMP,
                    run_dir=Path(directory),
                )
            report = build_validator_report(
                self.contract,
                manifest,
                validator_versions=versions,
                checks=checks,
                validation_attempt=1,
                completion_status="promax-complete",
                validated_at=STAMP,
                run_dir=Path(directory),
            )
            self.assertEqual(
                report["validator_set_sha256"], validator_set_sha256(versions)
            )
            validate_validator_report_freshness(
                report,
                self.contract,
                manifest,
                validator_versions=versions,
                expected_validation_attempt=1,
                run_dir=Path(directory),
            )

            mutations = {
                "nonce": ("run_nonce", "old-run-nonce"),
                "request": ("request_sha256", HASH_B),
                "snapshot": ("source_snapshot_sha256", HASH_B),
                "phase": ("phase_chain_head_sha256", HASH_B),
                "manifest": ("manifest_sha256", HASH_B),
                "validator-set": ("validator_set_sha256", HASH_B),
            }
            for name, (field, replacement) in mutations.items():
                stale = copy.deepcopy(report)
                stale[field] = replacement
                with self.subTest(name=name):
                    with self.assertRaises(ReplayBindingError):
                        validate_validator_report_freshness(
                            stale,
                            self.contract,
                            manifest,
                            validator_versions=versions,
                            expected_validation_attempt=1,
                            run_dir=Path(directory),
                        )

            stale_artifact = copy.deepcopy(report)
            stale_artifact["current_artifact_hashes"][0]["sha256"] = HASH_B
            with self.assertRaises(ReplayBindingError):
                validate_validator_report_freshness(
                    stale_artifact,
                    self.contract,
                    manifest,
                    validator_versions=versions,
                    expected_validation_attempt=1,
                    run_dir=Path(directory),
                )

    def test_rehashed_manifest_cannot_bypass_role_observation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._manifest(Path(directory))
            tampered = copy.deepcopy(manifest)
            tampered["role_records"][0]["observed_input_artifacts"] = copy.deepcopy(
                tampered["role_records"][1]["input_artifacts"]
            )
            unsigned = dict(tampered)
            unsigned.pop("manifest_sha256")
            tampered["manifest_sha256"] = sha256_json(unsigned)
            versions = {
                "schema": "1.0.0",
                "source-integrity": "1.0.0",
                "state-machine": "1.0.0",
            }
            checks = [
                {
                    "validator_id": validator_id,
                    "status": "pass",
                    "checked_artifact_paths": sorted(self.known),
                    "failure_codes": [],
                }
                for validator_id in versions
            ]

            with self.assertRaisesRegex(ValueError, "observed|declared|role"):
                build_validator_report(
                    self.contract,
                    tampered,
                    validator_versions=versions,
                    checks=checks,
                    validation_attempt=1,
                    completion_status="promax-complete",
                    validated_at=STAMP,
                    run_dir=Path(directory),
                )

    def test_rehashed_report_cannot_lie_about_check_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = self._manifest(Path(directory))
            versions = {
                "schema": "1.0.0",
                "source-integrity": "1.0.0",
                "state-machine": "1.0.0",
            }
            report = build_validator_report(
                self.contract,
                manifest,
                validator_versions=versions,
                checks=[
                    {
                        "validator_id": validator_id,
                        "status": "pass",
                        "checked_artifact_paths": sorted(self.known),
                        "failure_codes": [],
                    }
                    for validator_id in versions
                ],
                validation_attempt=1,
                completion_status="promax-complete",
                validated_at=STAMP,
                run_dir=Path(directory),
            )
            tampered = copy.deepcopy(report)
            tampered["checks"][0]["status"] = "fail"
            tampered["checks"][0]["failure_codes"] = ["FORGED_FAILURE"]
            unsigned = dict(tampered)
            unsigned.pop("report_sha256")
            tampered["report_sha256"] = sha256_json(unsigned)

            with self.assertRaisesRegex(ReplayBindingError, "status|check|complete"):
                validate_validator_report_freshness(
                    tampered,
                    self.contract,
                    manifest,
                    validator_versions=versions,
                    expected_validation_attempt=1,
                    run_dir=Path(directory),
                )

    def test_report_cannot_reduce_the_frozen_validator_set_or_change_run_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            one_check = [
                {
                    "validator_id": "schema",
                    "status": "pass",
                    "checked_artifact_paths": sorted(self.known),
                    "failure_codes": [],
                }
            ]
            with self.assertRaisesRegex(ReplayBindingError, "exact set|frozen"):
                build_validator_report(
                    self.contract,
                    manifest,
                    validator_versions={"schema": "1.0.0"},
                    checks=one_check,
                    validation_attempt=1,
                    completion_status="promax-complete",
                    validated_at=STAMP,
                    run_dir=root,
                )

            artifact_contract = initialized(mode="promax-artifact-run")["run_contract"]
            artifact_records, artifact_known = actual_role_records(artifact_contract)
            self.contract = artifact_contract
            self.records = artifact_records
            self.known = artifact_known
            artifact_manifest = self._manifest(root / "artifact-run")
            versions = {
                "schema": "1.0.0",
                "source-integrity": "1.0.0",
                "state-machine": "1.0.0",
            }
            checks = [
                {
                    "validator_id": validator_id,
                    "status": "pass",
                    "checked_artifact_paths": sorted(self.known),
                    "failure_codes": [],
                }
                for validator_id in versions
            ]
            with self.assertRaisesRegex(ValueError, "mode|completion"):
                build_validator_report(
                    artifact_contract,
                    artifact_manifest,
                    validator_versions=versions,
                    checks=checks,
                    validation_attempt=1,
                    completion_status="promax-complete",
                    validated_at=STAMP,
                    run_dir=root / "artifact-run",
                )

    def test_validator_freshness_rehashes_current_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self._manifest(root)
            versions = {
                "schema": "1.0.0",
                "source-integrity": "1.0.0",
                "state-machine": "1.0.0",
            }
            checks = [
                {
                    "validator_id": validator_id,
                    "status": "pass",
                    "checked_artifact_paths": sorted(self.known),
                    "failure_codes": [],
                }
                for validator_id in versions
            ]
            report = build_validator_report(
                self.contract,
                manifest,
                validator_versions=versions,
                checks=checks,
                validation_attempt=1,
                completion_status="promax-complete",
                validated_at=STAMP,
                run_dir=root,
            )
            changed_path = root / manifest["artifacts"][0]["path"]
            changed_path.write_bytes(b"changed after manifest")

            with self.assertRaisesRegex(ReplayBindingError, "bytes|stale|match"):
                validate_validator_report_freshness(
                    report,
                    self.contract,
                    manifest,
                    validator_versions=versions,
                    expected_validation_attempt=1,
                    run_dir=root,
                )

    def test_repair_plan_resets_only_the_earliest_failed_phase_and_descendants(self) -> None:
        report = {
            "report_sha256": HASH_A,
            "run_id": self.contract["run_id"],
            "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
        }
        failures = [
            {
                "failure_code": "STALE_POSITION",
                "affected_artifact_paths": ["promax-position.locked.json"],
                "affected_phase": "P8",
                "evidence": ["position hash is stale"],
            },
            {
                "failure_code": "CLAIM_PATH_GAP",
                "affected_artifact_paths": ["promax-claim-path-graph.json"],
                "affected_phase": "P5",
                "evidence": ["one path lacks a current parent"],
            },
        ]
        plan = build_repair_plan(report, failures, created_at=STAMP)
        self.assertEqual(plan["reset_from_phase"], "P5")
        self.assertEqual(
            plan["invalidated_phases"],
            ["P5", "P6", "P7", "P8", "P9", "P10", "P11"],
        )
        self.assertTrue(plan["revalidation_required"])
        self.assertEqual(plan["failed_report_sha256"], HASH_A)

        aliased = copy.deepcopy(failures)
        aliased[0]["affected_artifact_paths"] = ["Artifacts/A.json"]
        aliased[1]["affected_artifact_paths"] = ["artifacts/a.json"]
        with self.assertRaisesRegex(ValueError, "casefold|alias"):
            build_repair_plan(report, aliased, created_at=STAMP)


class ProMaxSchemaBoundHelperTests(unittest.TestCase):
    def test_domain_helpers_are_not_empty_stubs_and_reject_wrong_run_binding(self) -> None:
        validators = (
            (validate_concept_disposition, "promax-concept-disposition.schema.json"),
            (validate_claim_path_graph, "promax-claim-path-graph.schema.json"),
            (validate_retrieval_ledger, "promax-retrieval-ledger.schema.json"),
            (validate_position_lock, "promax-position.schema.json"),
        )
        for validator, schema_name in validators:
            with self.subTest(schema=schema_name):
                with self.assertRaises(ValueError):
                    validator(
                        {
                            "run_id": "wrong-run",
                            "source_snapshot_sha256": V8_SOURCE_SNAPSHOT_SHA256,
                        },
                        expected_run_id=RUN_ID,
                        expected_source_snapshot_sha256=V8_SOURCE_SNAPSHOT_SHA256,
                    )


class ProMaxRuntimeCLITests(unittest.TestCase):
    def test_cli_has_no_activation_subcommand_and_root_entrypoint_is_thin(self) -> None:
        with mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                crossframe_promax_runtime.main(
                    ["route", "--request", "use CrossFrame ProMax"]
                )
        self.assertEqual(raised.exception.code, 2)

        root_entry = ROOT / "scripts/crossframe_promax_runtime.py"
        self.assertTrue(root_entry.is_file())
        text = root_entry.read_text(encoding="utf-8")
        self.assertIn("runpy.run_path", text)
        self.assertNotIn("ArgumentParser", text)
        self.assertLess(len(text), 2000)

    def test_init_cli_writes_schema_bound_contract_and_snapshot_without_cot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            with mock.patch(
                "promax_runtime.artifacts.secrets.token_hex", return_value="cd" * 32
            ), mock.patch("sys.stdout", io.StringIO()):
                exit_code = crossframe_promax_runtime.main(
                    [
                        "init",
                        "--repo",
                        str(ROOT),
                        "--run-dir",
                        str(run_dir),
                        "--request",
                        "请用 CrossFrame ProMax。",
                        "--run-id",
                        RUN_ID,
                        "--created-at",
                        STAMP,
                        "--no-subagents",
                    ]
                )
            self.assertEqual(exit_code, 0)
            contract = json.loads(
                (run_dir / "promax-run-contract.json").read_text(encoding="utf-8")
            )
            snapshot = json.loads(
                (run_dir / "promax-source-snapshot.json").read_text(encoding="utf-8")
            )
            events = [
                json.loads(line)
                for line in (run_dir / "promax-phase-events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(contract["orchestration_mode"], "single-agent-separated")
            self.assertIs(contract["recommendation_required"], False)
            self.assertEqual(snapshot["source_snapshot_sha256"], V8_SOURCE_SNAPSHOT_SHA256)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["phase_id"], "P0")
            self.assertEqual(events[0]["run_nonce"], contract["run_nonce"])
            self.assertEqual(
                set(events[0]["output_artifact_hashes"]),
                {"promax-run-contract.json", "promax-source-snapshot.json"},
            )
            serialized = json.dumps(
                {"contract": contract, "snapshot": snapshot}, ensure_ascii=False
            ).lower()
            for forbidden in (
                "chain_of_thought",
                "hidden_reasoning",
                "internal_monologue",
                "scratchpad",
            ):
                self.assertNotIn(forbidden, serialized)

    def test_init_cli_can_freeze_a_requested_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            with mock.patch(
                "promax_runtime.artifacts.secrets.token_hex", return_value="ef" * 32
            ), mock.patch("sys.stdout", io.StringIO()):
                exit_code = crossframe_promax_runtime.main(
                    [
                        "init",
                        "--repo",
                        str(ROOT),
                        "--run-dir",
                        str(run_dir),
                        "--request",
                        "请用 CrossFrame ProMax 给出建议。",
                        "--run-id",
                        RUN_ID,
                        "--created-at",
                        STAMP,
                        "--recommendation-required",
                    ]
                )
            self.assertEqual(exit_code, 0)
            contract = json.loads(
                (run_dir / "promax-run-contract.json").read_text(encoding="utf-8")
            )
            self.assertIs(contract["recommendation_required"], True)

    def test_cli_materializes_source_blocker_and_streams_unwritable_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_repo = root / "missing-source"
            missing_repo.mkdir()
            source_run = root / "source-blocked-run"
            output = io.StringIO()
            with mock.patch("sys.stdout", output):
                exit_code = crossframe_promax_runtime.main(
                    [
                        "init",
                        "--repo",
                        str(missing_repo),
                        "--run-dir",
                        str(source_run),
                        "--request",
                        "use crossframe-promax",
                        "--mode",
                        "promax-blocked/progress",
                        "--blocker-category",
                        "source_unavailable",
                        "--blocker-detail",
                        "canonical v8 source is unreadable",
                        "--created-at",
                        STAMP,
                    ]
                )
            self.assertEqual(exit_code, 0)
            source_status = json.loads(output.getvalue())
            self.assertEqual(source_status["status"], "blocked/progress")
            self.assertTrue(source_status["materialized"])
            self.assertTrue((source_run / "promax-run-contract.json").is_file())
            self.assertFalse((source_run / "promax-source-snapshot.json").exists())
            self.assertTrue((source_run / "promax-phase-events.jsonl").is_file())

            unwritable_run = root / "unwritable-run"
            output = io.StringIO()
            with mock.patch("sys.stdout", output):
                exit_code = crossframe_promax_runtime.main(
                    [
                        "init",
                        "--repo",
                        str(ROOT),
                        "--run-dir",
                        str(unwritable_run),
                        "--request",
                        "use crossframe-promax",
                        "--mode",
                        "promax-blocked/progress",
                        "--blocker-category",
                        "filesystem_unwritable",
                        "--blocker-detail",
                        "artifact destination is read-only",
                        "--created-at",
                        STAMP,
                    ]
                )
            streamed = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(streamed["status"], "blocked/progress")
            self.assertFalse(streamed["materialized"])
            self.assertFalse(
                streamed["run_contract"]["capabilities"]["files"]["writable"]
            )
            self.assertFalse(unwritable_run.exists())


if __name__ == "__main__":
    unittest.main()
