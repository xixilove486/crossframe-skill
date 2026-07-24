from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SCRIPTS = ROOT / "skills/crossframe-promax/scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS))

import check_crossframe_promax_artifacts as checker
import crossframe_promax_fixture_factory as fixture_factory
import crossframe_promax_runtime
from promax_runtime.artifacts import CANONICAL_VALIDATOR_IDS, validate_role_records
from promax_runtime.errors import PhaseCASMismatch, PhaseLockBusy
from promax_runtime.jsonio import (
    canonical_json_bytes,
    load_json,
    load_jsonl,
    sha256_json,
)
from promax_runtime.materialization import (
    CONCEPT_DECISIONS_ARTIFACT,
    MaterializationError,
    ROLE_ATTESTATIONS_ARTIFACT,
    _bind_stability_control_fields,
    _build_concept_ledger,
    _rationale_template_fingerprint,
    _role_records,
    materialize_run,
    prepare_run,
)
from promax_runtime.source_integrity import V8_SOURCE_SNAPSHOT_SHA256
from promax_runtime.state_machine import (
    RunBinding,
    append_phase_event,
    build_reset_event,
    validate_phase_history,
)


REQUEST = (
    "请使用 $crossframe-promax 分析 bounded transfer mechanism 的结构，"
    "并给出有反例、撤回条件和六方案比较的明确建议。"
)
STAMP = "2026-07-23T10:00:00Z"
READ_STAMP = "2026-07-23T10:01:00Z"
REGISTRY = load_json(
    ROOT
    / "skills/crossframe-promax/references/concept-registry/v8-concept-registry.json"
)
CONCEPT_BY_ID = {item["concept_id"]: item for item in REGISTRY["concepts"]}


def write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def init_run(
    run_dir: Path,
    *,
    run_id: str,
    subagents: bool = False,
    mode: str = "promax-complete",
    network: bool = True,
) -> None:
    args = [
        "init",
        "--repo",
        str(ROOT),
        "--run-dir",
        str(run_dir),
        "--request",
        REQUEST,
        "--mode",
        mode,
        "--run-id",
        run_id,
        "--created-at",
        STAMP,
        "--recommendation-required",
    ]
    if network:
        args.append("--network")
    if subagents:
        args.extend(["--subagents", "--max-parallelism", "5"])
    with redirect_stdout(io.StringIO()):
        status = crossframe_promax_runtime.main(args)
    if status != 0:
        raise AssertionError(f"init returned {status}")


def prepare_valid_run(
    base: Path,
    *,
    suffix: str,
    subagents: bool = False,
    mode: str = "promax-complete",
    network: bool = True,
) -> tuple[Path, Path]:
    run_dir = base / f"run-{suffix}"
    authoring_dir = base / f"authoring-{suffix}"
    init_run(
        run_dir,
        run_id=f"promax-production-{suffix}",
        subagents=subagents,
        mode=mode,
        network=network,
    )
    result = prepare_run(
        ROOT,
        run_dir=run_dir,
        authoring_dir=authoring_dir,
        read_at=READ_STAMP,
    )
    if result["status"] != "prepared":
        raise AssertionError(result)
    return run_dir, authoring_dir


def populate_authoring(
    run_dir: Path,
    authoring_dir: Path,
    *,
    network_available: bool = True,
) -> None:
    contract = load_json(run_dir / "promax-run-contract.json")
    run_id = str(contract["run_id"])
    decisions = load_json(authoring_dir / CONCEPT_DECISIONS_ARTIFACT)
    decisions["request_keywords"] = ["bounded transfer mechanism"]
    decisions["request_binding_statement"] = (
        "本轮逐项裁决均绑定 bounded transfer mechanism 的冻结对象边界。"
    )
    decisions["route_ids"] = ["V8-ROUTE-01-GUIDE"]
    decisions["completed_at"] = "2026-07-23T10:04:00Z"
    applied_rationale = ""
    for item in decisions["decisions"]:
        name = item["authoritative_name_zh"]
        canonical = CONCEPT_BY_ID[item["concept_id"]]
        definition = canonical["definition"]
        applied = item["concept_id"] == fixture_factory.FIXTURE_CONCEPT_ID
        item["status"] = "applied" if applied else "not_applicable"
        item["rationale"] = (
            f"{name}：针对 bounded transfer mechanism 的冻结对象逐项核对；"
            f"v8 定义依据为“{definition}”，责任层为 {canonical['responsibility_layer']}，"
            f"原文锚点为 {canonical['primary_source_anchor_id']}。"
            + (
                "该概念直接限定行动者状态的证据边界，故进入中心结构解释。"
                if applied
                else "该概念在当前对象、责任层或证据条件中不承担解释责任。"
            )
        )
        item["evidence_refs"] = ["EVIDENCE-USER-1"] if applied else []
        item["output_section_ids"] = ["SECTION-CONCEPTS"] if applied else []
        item["pending_evidence"] = []
        if applied:
            applied_rationale = item["rationale"]
    write_json(authoring_dir / CONCEPT_DECISIONS_ARTIFACT, decisions)

    local_world = fixture_factory.build_local_world_model(
        run_id=run_id,
        locked_at="2026-07-23T10:03:00Z",
    )
    local_world["object_boundary"]["object_id"] = "OBJ-TRANSFER-1"
    local_world["object_boundary"]["name"] = "bounded transfer mechanism 分析对象"
    local_world["object_boundary"]["in_scope"] = [
        "bounded transfer mechanism 的结构关系与竞争解释"
    ]

    claim_graph = fixture_factory.build_claim_path_graph(
        run_id=run_id,
        updated_at="2026-07-23T10:05:00Z",
    )
    retrieval = fixture_factory.build_retrieval_ledger(
        run_id=run_id,
        completed_at="2026-07-23T10:06:00Z",
        network_available=network_available,
    )
    evidence_basis_sha256 = sha256_json(
        {
            "request_sha256": contract["request_sha256"],
            "source_snapshot_sha256": contract["source_snapshot_sha256"],
            "local_world_model_sha256": sha256_json(local_world),
            "retrieval_ledger_sha256": sha256_json(retrieval),
        }
    )
    red_team = fixture_factory.build_red_team_report(
        run_id=run_id,
        completed_at="2026-07-23T10:07:00Z",
        evidence_basis_sha256=evidence_basis_sha256,
    )
    position = fixture_factory.build_position_lock(
        run_id=run_id,
        locked_at="2026-07-23T10:08:00Z",
    )
    recommendation = fixture_factory.build_recommendation_lock(
        position,
        run_id=run_id,
        locked_at="2026-07-23T10:09:00Z",
    )
    output_plan = fixture_factory.build_output_plan(
        run_id=run_id,
        locked_at="2026-07-23T10:10:00Z",
    )
    semantic_json = {
        "promax-local-world-model.locked.json": local_world,
        "promax-claim-path-graph.json": claim_graph,
        "promax-retrieval-ledger.json": retrieval,
        "promax-red-team-report.json": red_team,
        "promax-position.locked.json": position,
        "promax-recommendation.locked.json": recommendation,
        "promax-output-plan.locked.json": output_plan,
    }
    for name, value in semantic_json.items():
        write_json(authoring_dir / name, value)

    deliverables = fixture_factory.build_deliverables(
        ROOT,
        recommendation=recommendation,
    )
    deliverables["promax-concept-atlas.md"] = deliverables[
        "promax-concept-atlas.md"
    ].replace(
        "Applied to the fixture object using the exact registered definition.",
        applied_rationale,
    )
    deliverables["promax-essay.md"] = deliverables["promax-essay.md"].replace(
        "Applied to the fixture object using the exact registered definition.",
        applied_rationale,
    )
    texts = {
        "promax-worldview-capsule.locked.md": (
            "# CrossFrame ProMax v8 世界观胶囊\n\n"
            "本运行只用冻结 v8 源解释 bounded transfer mechanism；"
            "事实、结构推断和现实授权严格分离。\n"
        ),
        **deliverables,
        "promax-continuation-index.md": (
            "# CrossFrame ProMax v8 续写索引\n\n"
            "bounded transfer mechanism 本轮输出已闭合；无待续写分支。\n"
        ),
    }
    for name, value in texts.items():
        (authoring_dir / name).write_text(value, encoding="utf-8", newline="")
    attestation_path = authoring_dir / ROLE_ATTESTATIONS_ARTIFACT
    if attestation_path.exists():
        attestations = load_json(attestation_path)
        for record in attestations["roles"]:
            record["agent_id"] = f"isolated-agent-{record['sequence']}"
            record["status"] = "completed"
            if "observed_input_artifacts" in record:
                input_path = record["input_artifact_paths"][0]
                output_path = record["output_artifact_paths"][0]
                record["observed_input_artifacts"] = [
                    {
                        "path": input_path,
                        "sha256": hashlib.sha256(
                            (authoring_dir / input_path).read_bytes()
                        ).hexdigest(),
                    }
                ]
                record["produced_output_artifacts"] = [
                    {
                        "path": output_path,
                        "sha256": hashlib.sha256(
                            (authoring_dir / output_path).read_bytes()
                        ).hexdigest(),
                    }
                ]
                record["completed_at"] = "2026-07-23T10:10:30Z"
        write_json(attestation_path, attestations)


class ProMaxControlBindingTests(unittest.TestCase):
    def test_control_plane_derives_semantic_problem_prompt_and_evidence_hashes(self) -> None:
        contract = {
            "request_sha256": "a" * 64,
            "source_snapshot_sha256": "b" * 64,
        }
        documents = {
            "promax-claim-path-graph.json": {
                "stance_neutral_problem": {
                    "analysis_object": "对象",
                    "proposition_under_test": "对象一定会转型",
                    "time_window": "未来一年",
                    "evidence_cutoff": STAMP,
                }
            },
            "promax-local-world-model.locked.json": {"known": ["事实"]},
            "promax-retrieval-ledger.json": {"entries": []},
            "promax-red-team-report.json": {
                "stability_checks": [
                    {
                        "pro_prompt": "请赞成对象一定会转型",
                        "anti_prompt": "请反对对象一定会转型",
                    }
                ]
            },
            "promax-position.locked.json": {
                "relation_to_proposition": "mixed",
                "position": "占位",
            },
        }

        _bind_stability_control_fields(documents, contract)

        problem = documents["promax-claim-path-graph.json"][
            "stance_neutral_problem"
        ]
        expected_problem = sha256_json(
            {
                "analysis_object": "对象",
                "proposition_under_test": "对象一定会转型",
                "time_window": "未来一年",
            }
        )
        self.assertEqual(problem["semantic_key_sha256"], expected_problem)
        check = documents["promax-red-team-report.json"]["stability_checks"][0]
        self.assertEqual(
            check["pro_prompt_sha256"],
            sha256_json("请赞成对象一定会转型"),
        )
        self.assertEqual(
            check["semantic_problem_sha256_before"],
            expected_problem,
        )
        self.assertEqual(
            check["evidence_basis_sha256_before"],
            check["evidence_basis_sha256_after"],
        )
        self.assertEqual(
            documents["promax-position.locked.json"]["proposition_verdict"],
            "VERDICT[mixed] 对象一定会转型",
        )

        forged = copy.deepcopy(documents)
        forged["promax-red-team-report.json"]["stability_checks"][0][
            "evidence_basis_sha256_after"
        ] = "c" * 64
        with self.assertRaisesRegex(
            MaterializationError,
            "semantic_fixed_field_mismatch",
        ):
            _bind_stability_control_fields(forged, contract)

class ProMaxProductionMaterializerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls._temp.name)
        cls.run_dir, cls.authoring_dir = prepare_valid_run(
            cls.base,
            suffix="complete",
        )
        populate_authoring(cls.run_dir, cls.authoring_dir)
        cls.materialized = materialize_run(
            ROOT,
            run_dir=cls.run_dir,
            authoring_dir=cls.authoring_dir,
            request_text=REQUEST,
            generated_at="2026-07-23T10:11:00Z",
        )
        cls.checked = checker.validate_workspace(
            cls.run_dir,
            repo=ROOT,
            final_chat=True,
            write_report=False,
            validated_at="2026-07-23T10:12:00Z",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()

    def test_production_materialize_closes_real_run_and_passes_checker(self) -> None:
        self.assertIs(self.materialized["published"], True)
        self.assertEqual(self.checked["overall_status"], "pass")
        self.assertEqual(self.checked["completion_status"], "promax-complete")
        self.assertFalse(
            str(load_json(self.run_dir / "promax-run-contract.json")["run_id"])
            .casefold()
            .startswith("promax-fixture")
        )
        contract = load_json(self.run_dir / "promax-run-contract.json")
        self.assertEqual(
            contract["capabilities"]["validators"]["validator_ids"],
            list(CANONICAL_VALIDATOR_IDS),
        )

        read_events = load_jsonl(self.run_dir / "promax-read-events.jsonl")
        self.assertEqual(len(read_events), 3863 + 117)
        ledger = load_json(self.run_dir / "promax-concept-disposition-ledger.json")
        self.assertEqual(len(ledger["dispositions"]), 709)
        self.assertEqual(
            len({item["concept_id"] for item in ledger["dispositions"]}),
            709,
        )
        self.assertTrue(all(item["status"] for item in ledger["dispositions"]))

        events = load_jsonl(self.run_dir / "promax-phase-events.jsonl")
        self.assertEqual([item["phase_id"] for item in events], [f"P{i}" for i in range(11)])
        self.assertTrue(all(item["event_type"] == "phase_sealed" for item in events))
        for path in checker._MANIFEST_CURRENT_ARTIFACTS:
            self.assertTrue((self.run_dir / path).is_file(), path)

    def test_materialized_phase_hashes_and_manifest_match_current_bytes(self) -> None:
        contract = load_json(self.run_dir / "promax-run-contract.json")
        events = load_jsonl(self.run_dir / "promax-phase-events.jsonl")
        binding = RunBinding(
            run_id=contract["run_id"],
            run_nonce=contract["run_nonce"],
            request_sha256=contract["request_sha256"],
            source_snapshot_sha256=contract["source_snapshot_sha256"],
        )
        state = validate_phase_history(events, expected_binding=binding)
        self.assertEqual(state.next_phase_id, "P11")
        for event in events:
            for relative, expected in event["output_artifact_hashes"].items():
                actual = hashlib.sha256((self.run_dir / relative).read_bytes()).hexdigest()
                self.assertEqual(actual, expected, relative)

        manifest = load_json(self.run_dir / "promax-artifact-manifest.json")
        self.assertEqual(manifest["phase_chain_head_sha256"], events[-1]["event_sha256"])
        self.assertEqual(
            {item["path"] for item in manifest["artifacts"]},
            checker._MANIFEST_CURRENT_ARTIFACTS,
        )
        for item in manifest["artifacts"]:
            actual = hashlib.sha256((self.run_dir / item["path"]).read_bytes()).hexdigest()
            self.assertEqual(actual, item["sha256"], item["path"])
        validate_role_records(
            contract,
            manifest["role_records"],
            known_artifacts={
                item["path"]: item["sha256"] for item in manifest["artifacts"]
            },
            artifact_records=manifest["artifacts"],
        )

    def test_final_chat_is_canonical_exact_checker_projection(self) -> None:
        projection = self.checked["final_chat_projection"]
        self.assertIsInstance(projection, dict)
        self.assertEqual(
            (self.run_dir / "promax-final-chat.json").read_bytes(),
            canonical_json_bytes(projection) + b"\n",
        )
        contract = load_json(self.run_dir / "promax-run-contract.json")
        position = load_json(self.run_dir / "promax-position.locked.json")
        output_plan = load_json(self.run_dir / "promax-output-plan.locked.json")
        self.assertEqual(projection["run_status"], contract["mode"])
        self.assertEqual(projection["center_judgment_summary"], position["position"])
        self.assertEqual(
            projection["key_withdrawal_conditions"],
            position["withdrawal_conditions"],
        )
        self.assertEqual(projection["artifact_links"], output_plan["required_artifacts"])
        self.assertIsNone(projection["continuation_entry"])

    def test_artifact_run_final_projection_uses_checker_downgrade_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(
                base,
                suffix="artifact-gap",
                mode="promax-artifact-run",
                network=False,
            )
            populate_authoring(
                run_dir,
                authoring_dir,
                network_available=False,
            )
            result = materialize_run(
                ROOT,
                run_dir=run_dir,
                authoring_dir=authoring_dir,
                request_text=REQUEST,
                generated_at="2026-07-23T10:11:00Z",
            )
            self.assertIs(result["published"], True)
            expected_status = "promax-artifact-incomplete:network-unavailable"
            self.assertEqual(
                result["validator_result"]["completion_status"],
                expected_status,
            )
            self.assertEqual(
                result["final_chat_projection"]["run_status"],
                expected_status,
            )
            self.assertEqual(
                load_json(run_dir / "promax-final-chat.json"),
                result["final_chat_projection"],
            )

    def test_materialize_rejects_missing_model_semantics_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="missing-position")
            populate_authoring(run_dir, authoring_dir)
            (authoring_dir / "promax-position.locked.json").unlink()
            before = tree_snapshot(run_dir)
            with self.assertRaisesRegex(
                MaterializationError,
                "semantic_bundle_missing.*promax-position.locked.json",
            ):
                materialize_run(
                    ROOT,
                    run_dir=run_dir,
                    authoring_dir=authoring_dir,
                    request_text=REQUEST,
                    generated_at="2026-07-23T10:11:00Z",
                )
            self.assertEqual(tree_snapshot(run_dir), before)

    def test_concept_decisions_reject_name_substituted_bulk_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="bulk-template")
            contract = load_json(run_dir / "promax-run-contract.json")
            decisions = load_json(authoring_dir / CONCEPT_DECISIONS_ARTIFACT)
            decisions["request_keywords"] = ["bounded transfer mechanism"]
            decisions["request_binding_statement"] = (
                "本轮逐项裁决均绑定 bounded transfer mechanism 的冻结对象边界。"
            )
            decisions["route_ids"] = ["V8-ROUTE-01-GUIDE"]
            decisions["completed_at"] = "2026-07-23T10:04:00Z"
            for index, item in enumerate(decisions["decisions"]):
                item["status"] = "applied" if index == 0 else "not_applicable"
                item["rationale"] = (
                    f"{item['authoritative_name_zh']}：针对 bounded transfer mechanism "
                    "统一核对后，当前不承担中心结构解释责任。"
                )
                item["evidence_refs"] = ["EVIDENCE-USER-1"] if index == 0 else []
                item["output_section_ids"] = ["SECTION-CONCEPTS"] if index == 0 else []
                item["pending_evidence"] = []

            with self.assertRaisesRegex(
                MaterializationError,
                "bulk_rationale_template_detected",
            ):
                _build_concept_ledger(
                    ROOT,
                    contract,
                    decisions,
                    request_text=REQUEST,
                )

    def test_concept_decisions_reject_numeric_suffix_bulk_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(
                base,
                suffix="bulk-numeric-suffix",
            )
            contract = load_json(run_dir / "promax-run-contract.json")
            decisions = load_json(authoring_dir / CONCEPT_DECISIONS_ARTIFACT)
            decisions["request_keywords"] = ["bounded transfer mechanism"]
            decisions["request_binding_statement"] = (
                "本轮逐项裁决均绑定 bounded transfer mechanism 的冻结对象边界。"
            )
            decisions["route_ids"] = ["V8-ROUTE-01-GUIDE"]
            decisions["completed_at"] = "2026-07-23T10:04:00Z"
            ordinal_labels = ("序号", "编号", "条目", "item", "no.")
            for index, item in enumerate(decisions["decisions"]):
                item["status"] = "applied" if index == 0 else "not_applicable"
                item["rationale"] = (
                    f"{item['authoritative_name_zh']}：针对 bounded transfer mechanism "
                    "统一核对后，当前不承担中心结构解释责任；"
                    f"{ordinal_labels[index % len(ordinal_labels)]} {index}。"
                )
                item["evidence_refs"] = ["EVIDENCE-USER-1"] if index == 0 else []
                item["output_section_ids"] = ["SECTION-CONCEPTS"] if index == 0 else []
                item["pending_evidence"] = []

            with self.assertRaisesRegex(
                MaterializationError,
                "bulk_rationale_template_detected",
            ):
                _build_concept_ledger(
                    ROOT,
                    contract,
                    decisions,
                    request_text=REQUEST,
                )

    def test_rationale_fingerprint_preserves_substantive_numbers(self) -> None:
        shared = {
            "concept_id": "V8-CANON-TEST",
            "authoritative_name": "测试概念",
        }
        first = _rationale_template_fingerprint(
            "测试概念：阈值 12.5%，至少 3 层，日期 2026-07-23，版本 v8.0。",
            **shared,
        )
        second = _rationale_template_fingerprint(
            "测试概念：阈值 18.5%，至少 4 层，日期 2026-08-24，版本 v8.1。",
            **shared,
        )
        self.assertNotEqual(first, second)
        for token in ("12", "5", "3", "2026", "07", "23", "v8", "0"):
            self.assertIn(token, first)

    def test_concurrent_prepare_cannot_delete_the_committed_read_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir = base / "run-concurrent-prepare"
            init_run(run_dir, run_id="promax-production-concurrent-prepare")
            authoring_dirs = [base / "authoring-a", base / "authoring-b"]
            start = threading.Barrier(2)
            loaded = threading.Barrier(2)
            import promax_runtime.materialization as materialization_module

            real_load = materialization_module._load_run_state

            def synchronized_load(*args: object, **kwargs: object):
                value = real_load(*args, **kwargs)
                try:
                    loaded.wait(timeout=1.0)
                except threading.BrokenBarrierError:
                    pass
                return value

            def invoke(authoring_dir: Path) -> dict[str, object]:
                start.wait(timeout=5.0)
                return prepare_run(
                    ROOT,
                    run_dir=run_dir,
                    authoring_dir=authoring_dir,
                    read_at=READ_STAMP,
                )

            outcomes: list[object] = []
            with patch.object(
                materialization_module,
                "_load_run_state",
                side_effect=synchronized_load,
            ):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [pool.submit(invoke, path) for path in authoring_dirs]
                    for future in futures:
                        try:
                            outcomes.append(future.result(timeout=30.0))
                        except BaseException as error:
                            outcomes.append(error)

            successes = [item for item in outcomes if isinstance(item, dict)]
            failures = [item for item in outcomes if isinstance(item, BaseException)]
            self.assertEqual(len(successes), 1, outcomes)
            self.assertEqual(len(failures), 1, outcomes)
            self.assertTrue((run_dir / "promax-read-events.jsonl").is_file())
            events = load_jsonl(run_dir / "promax-phase-events.jsonl")
            self.assertEqual([item["phase_id"] for item in events], ["P0", "P1"])
            state = validate_phase_history(events)
            self.assertEqual(
                state.active_artifact_hashes["promax-read-events.jsonl"],
                hashlib.sha256(
                    (run_dir / "promax-read-events.jsonl").read_bytes()
                ).hexdigest(),
            )

    def test_failed_post_publish_check_restores_exact_p1_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="postcheck-rollback")
            populate_authoring(run_dir, authoring_dir)
            before = tree_snapshot(run_dir)
            real_validate = checker.validate_workspace
            calls = 0

            def fail_postcheck(*args: object, **kwargs: object) -> dict[str, object]:
                nonlocal calls
                calls += 1
                if calls <= 2:
                    return real_validate(*args, **kwargs)
                return {
                    "failures": [{"gate": "fault-injection"}],
                    "final_chat_projection": None,
                }

            with patch.object(checker, "validate_workspace", side_effect=fail_postcheck):
                with self.assertRaisesRegex(
                    MaterializationError,
                    "published_workspace_postcheck_failed",
                ):
                    materialize_run(
                        ROOT,
                        run_dir=run_dir,
                        authoring_dir=authoring_dir,
                        request_text=REQUEST,
                        generated_at="2026-07-23T10:11:00Z",
                    )
            self.assertEqual(tree_snapshot(run_dir), before)

    def test_mid_publish_write_failure_restores_exact_p1_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="write-rollback")
            populate_authoring(run_dir, authoring_dir)
            before = tree_snapshot(run_dir)
            import promax_runtime.materialization as materialization_module

            real_publish = materialization_module._atomic_publish_bytes
            live_writes = 0

            def fail_fourth_live_write(path: Path, raw: bytes) -> None:
                nonlocal live_writes
                if path.parent == run_dir and path.name != "promax-phase-events.jsonl":
                    live_writes += 1
                    if live_writes == 4:
                        raise OSError("injected publish failure")
                real_publish(path, raw)

            with patch.object(
                materialization_module,
                "_atomic_publish_bytes",
                side_effect=fail_fourth_live_write,
            ):
                with self.assertRaises(OSError):
                    materialize_run(
                        ROOT,
                        run_dir=run_dir,
                        authoring_dir=authoring_dir,
                        request_text=REQUEST,
                        generated_at="2026-07-23T10:11:00Z",
                    )
            self.assertEqual(tree_snapshot(run_dir), before)
            self.assertFalse(
                (run_dir.parent / f".{run_dir.name}.promax-publish-transaction").exists()
            )

    def test_next_public_call_recovers_an_interrupted_publish_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="crash-recovery")
            before = tree_snapshot(run_dir)
            import promax_runtime.materialization as materialization_module

            state = validate_phase_history(
                load_jsonl(run_dir / "promax-phase-events.jsonl")
            )
            transaction, journal = materialization_module._begin_publish_transaction(
                run_dir,
                expected_head_sha256=str(state.chain_head_sha256),
                target_head_sha256="f" * 64,
            )
            journal["status"] = "publishing"
            materialization_module._write_publish_journal(transaction, journal)
            (run_dir / "promax-essay.md").write_text(
                "partial publish that survived a hard stop",
                encoding="utf-8",
                newline="",
            )

            with self.assertRaisesRegex(
                MaterializationError,
                "semantic_bundle_missing",
            ):
                materialize_run(
                    ROOT,
                    run_dir=run_dir,
                    authoring_dir=authoring_dir,
                    request_text=REQUEST,
                    generated_at="2026-07-23T10:11:00Z",
                )
            self.assertEqual(tree_snapshot(run_dir), before)
            self.assertFalse(transaction.exists())

    def test_two_concurrent_materializers_have_exactly_one_winner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="concurrent-materialize")
            populate_authoring(run_dir, authoring_dir)
            start = threading.Barrier(2)

            def invoke() -> object:
                start.wait(timeout=5.0)
                try:
                    return materialize_run(
                        ROOT,
                        run_dir=run_dir,
                        authoring_dir=authoring_dir,
                        request_text=REQUEST,
                        generated_at="2026-07-23T10:11:00Z",
                    )
                except BaseException as error:
                    return error

            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = [future.result(timeout=90.0) for future in [
                    pool.submit(invoke),
                    pool.submit(invoke),
                ]]
            winners = [item for item in outcomes if isinstance(item, dict)]
            losers = [item for item in outcomes if isinstance(item, BaseException)]
            self.assertEqual(len(winners), 1, outcomes)
            self.assertIs(winners[0]["published"], True)
            self.assertEqual(len(losers), 1, outcomes)
            self.assertIsInstance(losers[0], PhaseLockBusy)
            checked = checker.validate_workspace(
                run_dir,
                repo=ROOT,
                final_chat=True,
                write_report=False,
                validated_at="2026-07-23T10:12:00Z",
            )
            self.assertEqual(checked["overall_status"], "pass")

    def test_formal_head_change_after_stage_validation_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(base, suffix="head-cas")
            populate_authoring(run_dir, authoring_dir)
            real_validate = checker.validate_workspace
            injected_snapshot: dict[str, str] | None = None

            def advance_formal_head(*args: object, **kwargs: object) -> dict[str, object]:
                nonlocal injected_snapshot
                result = real_validate(*args, **kwargs)
                workspace = Path(args[0]).resolve()
                if workspace != run_dir.resolve() and injected_snapshot is None:
                    events = load_jsonl(run_dir / "promax-phase-events.jsonl")
                    state = validate_phase_history(events)
                    reset = build_reset_event(
                        state,
                        "P1",
                        reason="concurrent authoritative reset",
                    )
                    append_phase_event(
                        run_dir / "promax-phase-events.jsonl",
                        reset,
                        expected_head_sha256=state.chain_head_sha256,
                    )
                    injected_snapshot = tree_snapshot(run_dir)
                return result

            with patch.object(checker, "validate_workspace", side_effect=advance_formal_head):
                with self.assertRaises(PhaseCASMismatch):
                    materialize_run(
                        ROOT,
                        run_dir=run_dir,
                        authoring_dir=authoring_dir,
                        request_text=REQUEST,
                        generated_at="2026-07-23T10:11:00Z",
                    )
            self.assertIsNotNone(injected_snapshot)
            self.assertEqual(tree_snapshot(run_dir), injected_snapshot)

    def test_production_materializer_rejects_fixture_provenance_without_bypass(self) -> None:
        source = (
            ROOT / "skills/crossframe-promax/scripts/promax_runtime/materialization.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("crossframe_promax_fixture_factory", source)
        self.assertNotIn("tests/fixtures/promax-runtime", source)
        self.assertNotIn("allow_test_fixture", source)
        help_text = crossframe_promax_runtime._parser().format_help()
        self.assertIn("prepare", help_text)
        self.assertIn("materialize", help_text)
        self.assertNotIn("--scenario", help_text)
        self.assertNotIn("--allow-test-fixture", help_text)

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir = base / "run"
            authoring_dir = base / "authoring"
            init_run(run_dir, run_id="promax-fixture-production")
            before = tree_snapshot(run_dir)
            with self.assertRaisesRegex(
                MaterializationError,
                "test_fixture_provenance_forbidden",
            ):
                prepare_run(
                    ROOT,
                    run_dir=run_dir,
                    authoring_dir=authoring_dir,
                    read_at=READ_STAMP,
                )
            self.assertEqual(tree_snapshot(run_dir), before)
            self.assertFalse(authoring_dir.exists())

    def test_multi_agent_run_requires_and_records_five_unique_attestations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(
                base,
                suffix="multi-agent",
                subagents=True,
            )
            attestation_path = authoring_dir / ROLE_ATTESTATIONS_ARTIFACT
            self.assertTrue(attestation_path.is_file())
            populate_authoring(run_dir, authoring_dir)
            attestations = load_json(attestation_path)
            self.assertEqual(len(attestations["roles"]), 5)
            self.assertEqual(
                len({item["agent_id"] for item in attestations["roles"]}),
                5,
            )
            result = materialize_run(
                ROOT,
                run_dir=run_dir,
                authoring_dir=authoring_dir,
                request_text=REQUEST,
                generated_at="2026-07-23T10:11:00Z",
            )
            self.assertIs(result["published"], True)
            manifest = load_json(run_dir / "promax-artifact-manifest.json")
            self.assertEqual(len(manifest["role_records"]), 5)
            self.assertTrue(
                all(
                    item["execution_mode"] == "multi-agent-isolated"
                    for item in manifest["role_records"]
                )
            )
            self.assertEqual(
                {item["agent_id"] for item in manifest["role_records"]},
                {f"isolated-agent-{index}" for index in range(1, 6)},
            )
            self.assertTrue(
                all(item["execution_attestation"] for item in manifest["role_records"])
            )
            published_hashes = {
                item["path"]: item["sha256"] for item in manifest["artifacts"]
            }
            for record in manifest["role_records"]:
                attestation = record["execution_attestation"]
                for field in (
                    "observed_input_artifacts",
                    "produced_output_artifacts",
                ):
                    for artifact in attestation[field]:
                        if artifact["path"] in published_hashes:
                            self.assertEqual(
                                artifact["sha256"],
                                published_hashes[artifact["path"]],
                            )

    def test_multi_agent_attestation_without_byte_hashes_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(
                base,
                suffix="multi-agent-unhashed",
                subagents=True,
            )
            populate_authoring(run_dir, authoring_dir)
            attestations = load_json(authoring_dir / ROLE_ATTESTATIONS_ARTIFACT)
            for record in attestations["roles"]:
                record.pop("observed_input_artifacts", None)
                record.pop("produced_output_artifacts", None)
                record.pop("completed_at", None)
            write_json(authoring_dir / ROLE_ATTESTATIONS_ARTIFACT, attestations)
            contract = load_json(run_dir / "promax-run-contract.json")
            digests = {
                "promax-local-world-model.locked.json": "1" * 64,
                "promax-concept-disposition-ledger.json": "2" * 64,
                "promax-claim-path-graph.json": "3" * 64,
                "promax-retrieval-ledger.json": "4" * 64,
                "promax-red-team-report.json": "5" * 64,
                "promax-position.locked.json": "6" * 64,
                "promax-output-plan.locked.json": "7" * 64,
                "promax-essay.md": "8" * 64,
            }
            with self.assertRaisesRegex(
                MaterializationError,
                "role attestation entry is open or incomplete",
            ):
                _role_records(
                    contract,
                    digests,
                    authoring=authoring_dir,
                )

    def test_multi_agent_attestation_must_bind_canonical_published_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            run_dir, authoring_dir = prepare_valid_run(
                base,
                suffix="multi-agent-canonical-bytes",
                subagents=True,
            )
            populate_authoring(run_dir, authoring_dir)
            target_name = "promax-retrieval-ledger.json"
            target_path = authoring_dir / target_name
            retrieval = load_json(target_path)
            retrieval.pop("source_snapshot_sha256")
            write_json(target_path, retrieval)
            raw_digest = hashlib.sha256(target_path.read_bytes()).hexdigest()
            attestations = load_json(authoring_dir / ROLE_ATTESTATIONS_ARTIFACT)
            for record in attestations["roles"]:
                for field in (
                    "observed_input_artifacts",
                    "produced_output_artifacts",
                ):
                    for artifact in record[field]:
                        if artifact["path"] == target_name:
                            artifact["sha256"] = raw_digest
            write_json(authoring_dir / ROLE_ATTESTATIONS_ARTIFACT, attestations)

            before = tree_snapshot(run_dir)
            with self.assertRaisesRegex(
                MaterializationError,
                "canonical staged bytes",
            ):
                materialize_run(
                    ROOT,
                    run_dir=run_dir,
                    authoring_dir=authoring_dir,
                    request_text=REQUEST,
                    generated_at="2026-07-23T10:11:00Z",
                )
            self.assertEqual(tree_snapshot(run_dir), before)


if __name__ == "__main__":
    unittest.main()
