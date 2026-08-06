from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import MappingProxyType

from tests.pytest_import_guard import pytest
from tests.ultra_capability_support import (
    accept_pending_capability_result,
    capability_attestation_for_contract,
    default_capability_requirements,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_CLI = REPO_ROOT / "skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py"
ROOT_CLI = REPO_ROOT / "scripts/crossframe_ultra_runtime.py"
FORBIDDEN_CLI_OPTIONS = (
    "--run-dir",
    "--authoring-dir",
    "--output-root",
    "--destination",
    "--fallback",
)
EXPECTED_COMMANDS = (
    "start",
    "prepare",
    "checkpoint",
    "materialize",
    "validate",
    "repair-plan",
    "resume",
    "fork",
    "cancel",
    "rebuild-index",
)


def _load_cli():
    if not SKILL_CLI.is_file():
        pytest.skip(f"Task 13 CLI is not implemented: {SKILL_CLI}")
    spec = importlib.util.spec_from_file_location("task13_ultra_cli", SKILL_CLI)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _root_policy(tmp_path: Path):
    scripts_dir = REPO_ROOT / "skills/crossframe-ultra/scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from ultra_runtime.paths import RootPolicy

    return RootPolicy(tmp_path / "production", tmp_path / "test")


def _fresh_u1_authority_repo(tmp_path: Path) -> Path:
    from tests.test_ultra_source_read_coverage import _write_release_manifest

    authority_repo = tmp_path / "u1-authority-repo"
    skill_root = authority_repo / "skills/crossframe-ultra"
    skill_root.parent.mkdir(parents=True)
    shutil.copytree(REPO_ROOT / "skills/crossframe-ultra", skill_root)
    _write_release_manifest(
        authority_repo,
        skill_root / "references/release-manifest.json",
    )
    return authority_repo


def _host_result_completed_at(action) -> str:
    issued_at = datetime.fromisoformat(
        str(action.document["issued_at"]).replace("Z", "+00:00")
    )
    return (issued_at + timedelta(seconds=1)).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def _accept_closed_input_evidence_result(layout, action) -> None:
    from ultra_runtime import host_handshake, jsonio

    payload = action.document["payload"]
    assert isinstance(payload, dict)
    materials = payload["material_inventory"]
    assert isinstance(materials, list) and materials
    material = materials[0]
    assert isinstance(material, dict)
    relative_path = str(material["path"])
    material_bytes = (layout.input_dir / relative_path).read_bytes()
    statement = material_bytes.decode("utf-8")
    source_ref = "SEALED-MATERIAL-1"
    result = {
        "candidate_entries": [
            {
                "evidence_id": "EV-U3-SEALED-MATERIAL-1",
                "identity": "user-claim",
                "statement": statement,
                "source_refs": [source_ref],
                "observed_at": None,
                "confidence": "unknown",
                "event_date": None,
                "publication_date": None,
                "interest": "The user supplied this sealed material.",
                "upstream_lineage": [source_ref],
                "supported_claim": "The material records the user's supplied statement.",
                "cannot_prove": "The supplied statement does not independently prove truth.",
                "attribution": {
                    "origin_kind": "material",
                    "origin_ref": relative_path,
                    "content_sha256": hashlib.sha256(material_bytes).hexdigest(),
                    "span": [0, len(material_bytes)],
                    "proof_grade": "self-reported",
                },
            }
        ],
        "verified_subagent_candidates": [],
    }
    jsonio.atomic_write_json(action.result_path, result)
    completed_at = _host_result_completed_at(action)
    receipt = {
        "schema_id": "crossframe.ultra.v82.host-result-receipt",
        "schema_version": 1,
        "run_id": action.document["run_id"],
        "version_binding": copy.deepcopy(action.document["version_binding"]),
        "phase_id": "U3",
        "action_kind": "evidence-authoring",
        "parent_event_sha256": action.document["parent_event_sha256"],
        "request_sha256": action.document["request_sha256"],
        "action_sha256": action.action_sha256,
        "result_relative_path": action.document["result_relative_path"],
        "result_sha256": hashlib.sha256(action.result_path.read_bytes()).hexdigest(),
        "execution_id": "test-host-evidence-authoring",
        "completed_at": completed_at,
        "provider": {
            "provider_id": "test-host",
            "provider_kind": "runtime",
            "version": "1.0.0",
        },
        "tool": {
            "tool_id": "evidence-authoring",
            "provider_id": "test-host",
            "version": "1.0.0",
        },
        "execution_status": "complete",
        "attempts": [{"attempt": 1, "status": "success", "error": None}],
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        jsonio.canonical_json_bytes(receipt)
    ).hexdigest()
    host_handshake.accept_host_result(layout, action=action, receipt=receipt)


def _drive_cli_foundation_host_loop(
    cli,
    *,
    common: list[str],
    run_id: str,
    policy,
    layout,
    start_time: datetime,
) -> dict[str, object]:
    from ultra_runtime import host_handshake
    from tests.test_ultra_end_to_end_fixture import _accept_source_read_batch

    source_batch = 0
    for ordinal in range(1, 40):
        pending = host_handshake.load_pending_action(layout)
        if pending is not None:
            action_kind = pending.document["action_kind"]
            if action_kind == "capability-attestation":
                accept_pending_capability_result(
                    layout,
                    completed_at=_host_result_completed_at(pending),
                )
            elif action_kind == "source-read":
                source_batch += 1
                _accept_source_read_batch(
                    layout,
                    pending,
                    batch_ordinal=source_batch,
                )
            elif action_kind == "evidence-authoring":
                _accept_closed_input_evidence_result(layout, pending)
            else:
                pytest.fail(f"unexpected foundation host action: {action_kind}")

        stdout = StringIO()
        current_time = start_time + timedelta(seconds=ordinal * 2)
        assert cli.execute(
            ["materialize", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=stdout,
            stderr=StringIO(),
            root_policy=policy,
            now=lambda current_time=current_time: current_time,
            entropy=lambda: f"foundation-host-loop-{ordinal}".encode(),
        ) == 0
        response = json.loads(stdout.getvalue())
        if response["outcome"] == "awaiting-authoring":
            return response
        assert response["outcome"] == "awaiting-host-action", response
    pytest.fail("foundation host loop did not reach the U4 authoring wait")


def test_task13_cli_and_wrapper_exist_for_red_gate() -> None:
    assert SKILL_CLI.is_file(), SKILL_CLI
    assert ROOT_CLI.is_file(), ROOT_CLI


def test_parser_exposes_only_the_frozen_commands_and_options() -> None:
    cli = _load_cli()
    parser = cli.build_parser()
    help_text = parser.format_help()
    command_action = next(
        action for action in parser._actions if action.dest == "command"
    )

    assert tuple(command_action.choices) == EXPECTED_COMMANDS
    assert not any(option in help_text for option in FORBIDDEN_CLI_OPTIONS)

    expected_options = {
        "start": {
            "--repo",
            "--mode",
            "--request-file",
            "--request-stdin",
            "--material-file",
        },
        "prepare": {"--repo", "--mode", "--run-id"},
        "checkpoint": {"--repo", "--mode", "--run-id", "--phase"},
        "materialize": {"--repo", "--mode", "--run-id"},
        "validate": {"--repo", "--mode", "--run-id", "--json"},
        "repair-plan": {"--repo", "--mode", "--run-id"},
        "resume": {"--repo", "--mode", "--run-id"},
        "fork": {"--repo", "--mode", "--run-id", "--reason"},
        "cancel": {"--repo", "--mode", "--run-id"},
        "rebuild-index": {"--repo", "--mode"},
    }
    for name, subparser in command_action.choices.items():
        actual = {
            option
            for action in subparser._actions
            for option in action.option_strings
            if option != "--help"
        }
        assert actual == expected_options[name]
        assert not any(option in subparser.format_help() for option in FORBIDDEN_CLI_OPTIONS)


def test_parser_enforces_request_xor_modes_and_phase_domain() -> None:
    cli = _load_cli()
    parser = cli.build_parser()
    common = ["--repo", str(REPO_ROOT), "--mode", "test"]

    with pytest.raises(SystemExit):
        parser.parse_args(["start", *common])
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "start",
                *common,
                "--request-file",
                "request.txt",
                "--request-stdin",
            ]
        )
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["checkpoint", *common, "--run-id", "run", "--phase", "U12"]
        )
    parsed = parser.parse_args(
        ["checkpoint", *common, "--run-id", "run", "--phase", "U11"]
    )
    assert parsed.phase == "U11"


@pytest.mark.parametrize("source_kind", ["file", "stdin"])
def test_start_copies_exact_request_bytes_and_never_projects_prompt_text(
    tmp_path: Path, source_kind: str
) -> None:
    cli = _load_cli()
    request_bytes = "只存入输入目录；绝不进入索引与路径。\x00\n".encode("utf-8")
    argv = ["start", "--repo", str(REPO_ROOT), "--mode", "test"]
    stdin = BytesIO(b"")
    if source_kind == "file":
        request_path = tmp_path / "request.bin"
        request_path.write_bytes(request_bytes)
        argv.extend(["--request-file", str(request_path)])
    else:
        argv.append("--request-stdin")
        stdin = BytesIO(request_bytes)
    stdout = StringIO()

    result = cli.execute(
        argv,
        stdin=stdin,
        stdout=stdout,
        stderr=StringIO(),
        root_policy=_root_policy(tmp_path),
        now=lambda: datetime(2026, 8, 2, 3, 4, 5, tzinfo=timezone.utc),
        entropy=lambda: b"task-13-start-fixture",
    )

    assert result == 0
    response = json.loads(stdout.getvalue())
    run_id = response["run_id"]
    assert run_id == "20260802T030405Z-" + __import__("hashlib").sha256(
        b"task-13-start-fixture"
    ).hexdigest()[:12]
    run_dir = (
        tmp_path
        / "test/runs/2026/08"
        / run_id
    )
    assert (run_dir / "input/request.bin").read_bytes() == request_bytes
    metadata = json.loads((run_dir / "input/request-metadata.json").read_text("utf-8"))
    assert metadata == {
        "request_sha256": __import__("hashlib").sha256(request_bytes).hexdigest(),
        "request_size": len(request_bytes),
    }
    intake = json.loads(
        (run_dir / "recovery/request-intake-authority.json").read_text("utf-8")
    )
    assert intake["schema_id"] == "crossframe.ultra.v82.request-intake-authority"
    assert intake["run_id"] == run_id
    assert intake["request_sha256"] == metadata["request_sha256"]
    assert intake["request_size"] == metadata["request_size"]
    assert intake["generated_at"] == "2026-08-02T03:04:05Z"
    from ultra_runtime.schemas import compute_artifact_content_sha256

    assert intake["content_sha256"] == compute_artifact_content_sha256(intake)
    prompt = request_bytes.decode("utf-8", errors="ignore").replace("\x00", "")
    for path in (tmp_path / "test").rglob("*"):
        assert prompt not in path.name
        if path.is_file() and path != run_dir / "input/request.bin":
            assert request_bytes not in path.read_bytes()


def test_resume_emits_json_projection_without_live_phase_store(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    run_id = "20260805T010203Z-0123456789ab"
    started_at = datetime(2026, 8, 5, 1, 2, 3, tzinfo=timezone.utc)
    resumed_at = started_at + timedelta(seconds=3)

    from ultra_runtime import recovery, state_machine, status
    from ultra_runtime.constants import current_version_binding
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    status_store = status.RunStatusStore(layout)
    created = status_store.create(started_at)
    running = status_store.transition(
        created,
        "running",
        started_at + timedelta(seconds=1),
    )
    interrupted = status_store.transition(
        running,
        "interrupted",
        started_at + timedelta(seconds=2),
        reason="test interruption",
    )
    status_record = status_store.transition(
        interrupted,
        "running",
        resumed_at,
        current_phase="U1",
        last_complete_phase="U1",
        reason="resumed from immutable checkpoint",
    )
    request_sha256 = hashlib.sha256(b"resume-cli-request").hexdigest()
    binding = current_version_binding()
    run_contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": request_sha256,
        "analysis_kind": "open-world",
        "run_mode": "test",
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-05T01:02:03Z",
        "capabilities": default_capability_requirements(),
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }
    attestation = capability_attestation_for_contract(
        run_id=run_id,
        version_binding=binding,
        contract=run_contract,
        generated_at="2026-08-05T01:02:03Z",
    )
    run_contract["capability_attestation_sha256"] = attestation.artifact_sha256
    phase_store = state_machine.PhaseStore(
        run_id=run_id,
        version_binding=binding,
        source_sha256=hashlib.sha256(b"resume-cli-source").hexdigest(),
        input_artifact_hashes=(request_sha256,),
        input_snapshot_sha256=request_sha256,
        evidence_cutoff="2026-08-05T01:02:03Z",
        now=started_at,
        run_contract=run_contract,
        capability_attestation=attestation,
        source_repository=REPO_ROOT,
        run_layout=layout,
    )
    checkpoint = {
        "boundary_kind": "phase",
        "boundary_ordinal": 0,
        "phase_id": "U1",
    }
    recovery_result = recovery.RecoveryResult(
        outcome="resume",
        compatibility_result="resume",
        checkpoint=checkpoint,
        status=status_record,
        phase_store=phase_store,
    )

    def resume_run(selected_layout, *, now):
        assert selected_layout == layout
        assert now == resumed_at + timedelta(seconds=1)
        return recovery_result

    monkeypatch.setattr(recovery, "resume_run", resume_run)
    stdout = StringIO()
    stderr = StringIO()

    return_code = cli.execute(
        [
            "resume",
            "--repo",
            str(REPO_ROOT),
            "--mode",
            "test",
            "--run-id",
            run_id,
        ],
        stdin=BytesIO(),
        stdout=stdout,
        stderr=stderr,
        root_policy=policy,
        now=lambda: resumed_at + timedelta(seconds=1),
        entropy=lambda: b"unused",
    )
    expected = {
        "outcome": "resume",
        "compatibility_result": "resume",
        "checkpoint": checkpoint,
        "status": status._record_to_object(status_record),
    }

    assert return_code == 0
    assert stderr.getvalue() == ""
    assert stdout.getvalue() == (
        json.dumps(
            expected,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    projected = json.loads(stdout.getvalue())
    assert set(projected) == {
        "outcome",
        "compatibility_result",
        "checkpoint",
        "status",
    }
    assert "phase_store" not in projected


def test_cancel_emits_persisted_canonical_status_from_real_mappingproxy_record(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    run_id = "20260805T010203Z-caace0123456"
    started_at = datetime(2026, 8, 5, 1, 2, 3, tzinfo=timezone.utc)

    from ultra_runtime import recovery, state_machine, status
    from ultra_runtime.constants import current_version_binding
    from ultra_runtime.jsonio import canonical_json_bytes
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    layout.input_dir.mkdir(parents=True)
    request_bytes = b"cancel-cli-request\n"
    request_path = layout.input_dir / "request.bin"
    request_path.write_bytes(request_bytes)
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    source_sha256 = hashlib.sha256(
        (REPO_ROOT / "skills/crossframe-ultra/references/source-manifest.json").read_bytes()
    ).hexdigest()
    binding = current_version_binding()
    run_contract = {
        "trigger": "crossframe-ultra",
        "request_sha256": request_sha256,
        "analysis_kind": "open-world",
        "run_mode": "test",
        "sensitivity": "private",
        "retention": "retain",
        "outbound_permission": "deidentified-only",
        "evidence_cutoff": "2026-08-05T01:02:03Z",
        "capabilities": default_capability_requirements(),
        "resource_limits": {
            "maximum_branches": 64,
            "maximum_retrieval_rounds_without_material_novelty": 2,
            "maximum_tool_retries": 3,
            "maximum_repair_attempts": 3,
        },
    }
    attestation = capability_attestation_for_contract(
        run_id=run_id,
        version_binding=binding,
        contract=run_contract,
        generated_at="2026-08-05T01:02:03Z",
    )
    run_contract["capability_attestation_sha256"] = attestation.artifact_sha256
    phase_store = state_machine.PhaseStore(
        run_id=run_id,
        version_binding=binding,
        source_sha256=source_sha256,
        input_artifact_hashes=(request_sha256,),
        input_snapshot_sha256=request_sha256,
        evidence_cutoff="2026-08-05T01:02:03Z",
        now=started_at,
        run_contract=run_contract,
        capability_attestation=attestation,
        source_repository=REPO_ROOT,
        run_layout=layout,
    )
    phase_store.complete(
        "U0",
        artifact_hashes=(phase_store.run_contract_artifact_sha256,),
    )
    contract_path = layout.artifacts_dir / "ultra-run-contract.json"
    contract_path.parent.mkdir(parents=True)
    attestation_path = (
        layout.artifacts_dir
        / "U00-U03-evidence/U00-host-capability-attestation.json"
    )
    attestation_path.parent.mkdir(parents=True, exist_ok=True)
    attestation_path.write_bytes(attestation.artifact_bytes)
    contract_path.write_bytes(canonical_json_bytes(dict(phase_store.run_contract)))
    recovery.create_checkpoint(
        layout,
        phase_store,
        boundary_kind="phase",
        boundary_id="U0",
        boundary_ordinal=0,
        artifact_paths=(contract_path,),
        now=started_at + timedelta(seconds=1),
    )
    status_store = status.RunStatusStore(layout)
    created = status_store.create(started_at)
    running = status_store.transition(
        created,
        "running",
        started_at + timedelta(seconds=2),
    )
    assert isinstance(running, status.RunStatusRecord)
    assert isinstance(running.version_binding, MappingProxyType)
    stdout = StringIO()
    stderr = StringIO()

    return_code = cli.execute(
        [
            "cancel",
            "--repo",
            str(REPO_ROOT),
            "--mode",
            "test",
            "--run-id",
            run_id,
        ],
        stdin=BytesIO(),
        stdout=stdout,
        stderr=stderr,
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=3),
        entropy=lambda: b"unused",
    )
    persisted_bytes = (layout.run_dir / "run-status.json").read_bytes()
    persisted_record = status_store.read()

    assert return_code == 0
    assert stderr.getvalue() == ""
    assert isinstance(persisted_record.version_binding, MappingProxyType)
    assert persisted_record.status == "cancelled"
    assert persisted_record.tools_allowed is False
    assert stdout.getvalue().encode("utf-8") == persisted_bytes
    assert persisted_bytes == canonical_json_bytes(status._record_to_object(persisted_record))
    assert persisted_bytes.endswith(b"\n")
    assert not persisted_bytes.endswith(b"\n\n")


def test_materialize_plain_request_emits_pending_capability_attestation(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    common = ["--repo", str(REPO_ROOT), "--mode", "test"]
    start_stdout = StringIO()
    started_at = datetime(2026, 8, 5, 1, 3, 30, tzinfo=timezone.utc)
    cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO("AI 会怎样改变就业？\n".encode("utf-8")),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at,
        entropy=lambda: b"task-2-cli-natural-language",
    )
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    stdout = StringIO()

    result = cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=1),
        entropy=lambda: b"unused-before-host-result",
    )

    response = json.loads(stdout.getvalue())
    assert result == 0
    assert response["status"] == "running"
    assert response["outcome"] == "awaiting-host-action"
    assert response["next_action"]["action_kind"] == "capability-attestation"
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    assert (layout.recovery_dir / "pending-action.json").is_file()
    assert not (layout.artifacts_dir / "ultra-run-contract.json").exists()
    assert json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))[
        "status"
    ] == "running"
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_plain_text_fresh_run_returns_u0_next_action(
    tmp_path: Path,
) -> None:
    """A normal natural-language run is a typed progress result, not a stop error."""
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    common = ["--repo", str(REPO_ROOT), "--mode", "test"]
    started_at = datetime(2026, 8, 5, 1, 3, 35, tzinfo=timezone.utc)
    start_stdout = StringIO()
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO("请分析当前 AI 就业问题。\n".encode("utf-8")),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at,
        entropy=lambda: b"task-6-plain-text-progress",
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]

    stdout = StringIO()
    assert cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=1),
        entropy=lambda: b"unused-task-6-progress",
    ) == 0

    response = json.loads(stdout.getvalue())
    assert response["outcome"] == "awaiting-host-action"
    assert response["status"] == "running"
    assert response["current_phase"] == "U0"
    assert response["next_action"]["action_kind"] == "capability-attestation"

    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    pending_path = layout.recovery_dir / "pending-action.json"
    pending_bytes = pending_path.read_bytes()
    repeated_stdout = StringIO()
    assert cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=repeated_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=2),
        entropy=lambda: b"unused-task-6-progress-repeat",
    ) == 0
    assert json.loads(repeated_stdout.getvalue()) == response
    assert pending_path.read_bytes() == pending_bytes
    assert not (layout.run_dir / ".writer-lease.json").exists()


@pytest.mark.parametrize("mutation", ("paired-input", "interrupted"))
def test_prepare_rejects_invalid_preflight_before_control_or_host_dispatch(
    tmp_path: Path,
    mutation: str,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    common = ["--repo", str(REPO_ROOT), "--mode", "test"]
    started_at = datetime(2026, 8, 5, 1, 3, 37, tzinfo=timezone.utc)
    start_stdout = StringIO()
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO("原始请求。\n".encode("utf-8")),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at,
        entropy=lambda: f"task-6-prepare-{mutation}".encode(),
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]

    from ultra_runtime.paths import RunMode, build_run_layout
    from ultra_runtime.status import RunStatusStore

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    expected_status = "created"
    if mutation == "paired-input":
        replacement = "替换请求。\n".encode("utf-8")
        (layout.input_dir / "request.bin").write_bytes(replacement)
        (layout.input_dir / "request-metadata.json").write_bytes(
            (
                json.dumps(
                    {
                        "request_sha256": hashlib.sha256(replacement).hexdigest(),
                        "request_size": len(replacement),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
        )
        expected_error = "intake"
    else:
        store = RunStatusStore(layout)
        created = store.read()
        running = store.transition(
            created,
            "running",
            started_at + timedelta(seconds=1),
            reason="test running boundary",
        )
        store.transition(
            running,
            "interrupted",
            started_at + timedelta(seconds=2),
            reason="test interrupted boundary",
        )
        expected_status = "interrupted"
        expected_error = "status boundary"

    with pytest.raises(ValueError, match=expected_error):
        cli.execute(
            ["prepare", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: started_at + timedelta(seconds=3),
            entropy=lambda: b"unused-task-6-prepare-preflight",
        )

    status = json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))
    assert status["status"] == expected_status
    assert not (layout.artifacts_dir / "ultra-materialization-control.json").exists()
    assert not (layout.recovery_dir / "pending-action.json").exists()
    assert not (layout.run_dir / ".writer-lease.json").exists()



def test_materialize_accepts_host_attestation_and_advances_to_u1_wait(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    monkeypatch.setattr(source_integrity, "PRODUCTION_ROOT", policy.production_root)
    authority_repo = _fresh_u1_authority_repo(tmp_path)
    common = ["--repo", str(authority_repo), "--mode", "test"]
    start_stdout = StringIO()
    started_at = datetime(2026, 8, 5, 1, 3, 40, tzinfo=timezone.utc)
    cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO("AI 会怎样改变就业？\n".encode("utf-8")),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at,
        entropy=lambda: b"task-2-cli-u0-complete",
    )
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    first_stdout = StringIO()
    cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=first_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=1),
        entropy=lambda: b"unused-before-u0",
    )
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    accept_pending_capability_result(
        layout,
        completed_at="2026-08-05T01:03:42Z",
    )
    stdout = StringIO()

    result = cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=3),
        entropy=lambda: b"unused-after-u0",
    )

    response = json.loads(stdout.getvalue())
    assert result == 0
    assert response["status"] == "running"
    assert response["outcome"] == "awaiting-host-action"
    assert response["current_phase"] == "U1"
    assert response["last_complete_phase"] == "U0"
    assert response["next_action"]["action_kind"] == "source-read"
    assert (layout.artifacts_dir / "ultra-run-contract.json").is_file()
    assert (layout.recovery_dir / "u1-authority/source-lock.json").is_file()
    assert (layout.recovery_dir / "u1-authority/read-plan.json").is_file()
    assert not (
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl"
    ).exists()
    repeated_stdout = StringIO()
    assert cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=repeated_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: started_at + timedelta(seconds=4),
        entropy=lambda: b"unused-repeat-u0",
    ) == 0
    assert json.loads(repeated_stdout.getvalue()) == response
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_materialize_bootstraps_real_u0_u3_chain_for_fresh_prepared_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    monkeypatch.setattr(source_integrity, "PRODUCTION_ROOT", policy.production_root)
    authority_repo = _fresh_u1_authority_repo(tmp_path)
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"若 A 则 B。",'
        '"material":"本请求是完整且封闭的材料全集。"}\n'
    ).encode("utf-8")
    common = ["--repo", str(authority_repo), "--mode", "test"]
    start_time = datetime(2026, 8, 5, 1, 2, 3, tzinfo=timezone.utc)
    start_stdout = StringIO()

    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time,
        entropy=lambda: b"fresh-u0-u3-cli-start",
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]

    prepare_stdout = StringIO()
    assert cli.execute(
        ["prepare", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=prepare_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(seconds=1),
        entropy=lambda: b"unused",
    ) == 0
    prepared = json.loads(prepare_stdout.getvalue())
    assert prepared["outcome"] == "awaiting-host-action"
    assert prepared["current_phase"] == "U0"
    assert prepared["next_action"]["action_kind"] == "capability-attestation"

    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    response = _drive_cli_foundation_host_loop(
        cli,
        common=common,
        run_id=run_id,
        policy=policy,
        layout=layout,
        start_time=start_time + timedelta(seconds=2),
    )
    assert response["status"] == "running"
    assert response["outcome"] == "awaiting-authoring"
    assert response["current_phase"] == "U4"
    assert response["last_complete_phase"] == "U3"
    assert response["next_action"]["relative_path"] == "U04-world-volume.json"

    contract = json.loads(
        (layout.artifacts_dir / "ultra-run-contract.json").read_text("utf-8")
    )
    assert contract["request_sha256"] == hashlib.sha256(request_bytes).hexdigest()
    assert contract["sensitivity"] == "private"
    assert contract["retention"] == "retain"
    assert contract["outbound_permission"] == "deidentified-only"
    assert contract["capabilities"] == {
        "filesystem": "required",
        "docx_parser": "not-applicable",
        "network": "not-applicable",
        "retrieval": "not-applicable",
        "validators": "required",
        "subagents": "not-applicable",
        "model_context": "required",
    }
    assert contract["resource_limits"] == {
        "maximum_branches": 64,
        "maximum_retrieval_rounds_without_material_novelty": 2,
        "maximum_tool_retries": 3,
        "maximum_repair_attempts": 3,
    }

    phase_events = [
        json.loads(line)
        for line in (layout.recovery_dir / "phase-events.jsonl")
        .read_text("utf-8")
        .splitlines()
    ]
    assert [event["phase_id"] for event in phase_events] == ["U0", "U1", "U2", "U3"]
    assert all(event["status"] == "complete" for event in phase_events)

    checkpoints = [
        json.loads(path.read_text("utf-8"))
        for path in (layout.recovery_dir / "checkpoints").glob("*.json")
    ]
    assert sorted(
        (checkpoint["boundary_id"], checkpoint["boundary_ordinal"])
        for checkpoint in checkpoints
        if checkpoint["boundary_kind"] == "phase"
    ) == [("U0", 0), ("U1", 0), ("U2", 0), ("U3", 0)]
    events_by_phase = {event["phase_id"]: event for event in phase_events}
    for checkpoint in checkpoints:
        if checkpoint["boundary_kind"] == "phase":
            assert checkpoint["phase_event_sha256"] == events_by_phase[
                checkpoint["boundary_id"]
            ]["event_sha256"]

    read_events = (
        layout.artifacts_dir / "U00-U03-evidence/ultra-read-events.jsonl"
    ).read_text("utf-8").splitlines()
    assert len(read_events) == 4753
    retrieval_ledger = json.loads(
        (
            layout.artifacts_dir
            / "U00-U03-evidence/U02-retrieval-ledger.json"
        ).read_text("utf-8")
    )
    assert retrieval_ledger["retrieval_status"] == "not-applicable"
    assert retrieval_ledger["decision"]["reason"] == "closed-input"

    def foundation_snapshot() -> dict[str, str]:
        candidates = {
            layout.run_dir / "run-status.json",
            layout.artifacts_dir / "ultra-run-contract.json",
            *(path for path in layout.recovery_dir.rglob("*") if path.is_file()),
            *(
                path
                for path in (
                    layout.artifacts_dir / "U00-U03-evidence"
                ).rglob("*")
                if path.is_file()
            ),
        }
        return {
            path.relative_to(layout.run_dir).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(candidates)
        }

    before_retry = foundation_snapshot()

    retry_stdout = StringIO()
    assert cli.execute(
        ["materialize", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=retry_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(minutes=1),
        entropy=lambda: b"fresh-u0-u3-cli-retry",
    ) == 0
    assert json.loads(retry_stdout.getvalue()) == response
    assert foundation_snapshot() == before_retry
    assert not (layout.run_dir / ".writer-lease.json").exists()


@pytest.mark.parametrize("failure_phase", ["U0", "U1", "U2"])
def test_materialize_resumes_each_durable_partial_foundation_checkpoint(
    tmp_path: Path,
    monkeypatch,
    failure_phase: str,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    monkeypatch.setattr(source_integrity, "PRODUCTION_ROOT", policy.production_root)
    authority_repo = _fresh_u1_authority_repo(tmp_path)
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"若 A 则 B。",'
        '"material":"完整封闭材料。"}\n'
    ).encode("utf-8")
    common = ["--repo", str(authority_repo), "--mode", "test"]
    start_time = datetime(2026, 8, 5, 1, 4, 3, tzinfo=timezone.utc)
    start_stdout = StringIO()
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time,
        entropy=lambda: f"partial-{failure_phase}-start".encode(),
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    assert cli.execute(
        ["prepare", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=StringIO(),
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(seconds=1),
        entropy=lambda: b"unused",
    ) == 0

    from ultra_runtime import recovery
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    original_checkpoint = recovery.create_checkpoint
    injected = False

    def inject_after_checkpoint(
        layout,
        phase_store,
        *,
        boundary_kind,
        boundary_id,
        boundary_ordinal,
        artifact_paths,
        now,
    ):
        nonlocal injected
        checkpoint = original_checkpoint(
            layout,
            phase_store,
            boundary_kind=boundary_kind,
            boundary_id=boundary_id,
            boundary_ordinal=boundary_ordinal,
            artifact_paths=artifact_paths,
            now=now,
        )
        if (
            boundary_kind == "phase"
            and boundary_id == failure_phase
            and not injected
        ):
            injected = True
            raise RuntimeError(f"injected after {boundary_id} checkpoint")
        return checkpoint

    monkeypatch.setattr(recovery, "create_checkpoint", inject_after_checkpoint)
    with pytest.raises(RuntimeError, match=f"after {failure_phase} checkpoint"):
        _drive_cli_foundation_host_loop(
            cli,
            common=common,
            run_id=run_id,
            policy=policy,
            layout=layout,
            start_time=start_time + timedelta(seconds=2),
        )
    monkeypatch.setattr(recovery, "create_checkpoint", original_checkpoint)

    response = _drive_cli_foundation_host_loop(
        cli,
        common=common,
        run_id=run_id,
        policy=policy,
        layout=layout,
        start_time=start_time + timedelta(minutes=1),
    )
    assert response["outcome"] == "awaiting-authoring"
    assert response["current_phase"] == "U4"
    assert response["next_action"]["relative_path"] == "U04-world-volume.json"
    phase_events = [
        json.loads(line)
        for line in (layout.recovery_dir / "phase-events.jsonl")
        .read_text("utf-8")
        .splitlines()
    ]
    assert [event["phase_id"] for event in phase_events] == ["U0", "U1", "U2", "U3"]
    assert [
        checkpoint["phase_id"] for checkpoint in recovery.load_checkpoints(layout)
    ] == ["U0", "U1", "U2", "U3"]
    assert not (layout.run_dir / ".writer-lease.json").exists()


def test_event_written_without_foundation_checkpoint_resumes_last_durable_boundary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    monkeypatch.setattr(source_integrity, "PRODUCTION_ROOT", policy.production_root)
    authority_repo = _fresh_u1_authority_repo(tmp_path)
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"若 A 则 B。",'
        '"material":"完整封闭材料。"}\n'
    ).encode("utf-8")
    common = ["--repo", str(authority_repo), "--mode", "test"]
    start_stdout = StringIO()
    start_time = datetime(2026, 8, 5, 1, 4, 15, tzinfo=timezone.utc)
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time,
        entropy=lambda: b"event-without-checkpoint-start",
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    assert cli.execute(
        ["prepare", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=StringIO(),
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(seconds=1),
        entropy=lambda: b"unused",
    ) == 0

    from ultra_runtime import recovery
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    original_write_immutable = recovery._write_immutable

    def fail_before_u1_checkpoint(path: Path, value: object) -> bytes:
        if (
            path.parent == layout.recovery_dir / "checkpoints"
            and isinstance(value, dict)
            and value.get("boundary_kind") == "phase"
            and value.get("phase_id") == "U1"
        ):
            raise RuntimeError("injected before U1 checkpoint write")
        return original_write_immutable(path, value)

    monkeypatch.setattr(recovery, "_write_immutable", fail_before_u1_checkpoint)
    with pytest.raises(RuntimeError, match="before U1 checkpoint write"):
        _drive_cli_foundation_host_loop(
            cli,
            common=common,
            run_id=run_id,
            policy=policy,
            layout=layout,
            start_time=start_time + timedelta(seconds=2),
        )
    monkeypatch.setattr(recovery, "_write_immutable", original_write_immutable)

    phase_events = [
        json.loads(line)
        for line in (layout.recovery_dir / "phase-events.jsonl")
        .read_text("utf-8")
        .splitlines()
    ]
    assert [event["phase_id"] for event in phase_events] == ["U0", "U1"]
    assert [
        checkpoint["phase_id"] for checkpoint in recovery.load_checkpoints(layout)
    ] == ["U0"]

    with pytest.raises(RuntimeError, match="uncheckpointed downstream state"):
        cli.execute(
            ["materialize", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: start_time + timedelta(minutes=1),
            entropy=lambda: b"event-without-checkpoint-retry",
        )
    status = json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))
    assert status["status"] == "needs_attention"
    assert status["last_complete_phase"] is None
    assert status["reason"].startswith("foundation recovery requires attention:")


def test_partial_foundation_with_uncheckpointed_downstream_state_needs_attention(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    monkeypatch.setattr(source_integrity, "PRODUCTION_ROOT", policy.production_root)
    authority_repo = _fresh_u1_authority_repo(tmp_path)
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"若 A 则 B。",'
        '"material":"完整封闭材料。"}\n'
    ).encode("utf-8")
    common = ["--repo", str(authority_repo), "--mode", "test"]
    start_stdout = StringIO()
    start_time = datetime(2026, 8, 5, 1, 4, 30, tzinfo=timezone.utc)
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time,
        entropy=lambda: b"partial-residual-start",
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    assert cli.execute(
        ["prepare", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=StringIO(),
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(seconds=1),
        entropy=lambda: b"unused",
    ) == 0

    from ultra_runtime import recovery
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    original_checkpoint = recovery.create_checkpoint

    def stop_after_u0(
        layout,
        phase_store,
        *,
        boundary_kind,
        boundary_id,
        boundary_ordinal,
        artifact_paths,
        now,
    ):
        checkpoint = original_checkpoint(
            layout,
            phase_store,
            boundary_kind=boundary_kind,
            boundary_id=boundary_id,
            boundary_ordinal=boundary_ordinal,
            artifact_paths=artifact_paths,
            now=now,
        )
        if boundary_kind == "phase" and boundary_id == "U0":
            raise RuntimeError("injected after U0 checkpoint")
        return checkpoint

    monkeypatch.setattr(recovery, "create_checkpoint", stop_after_u0)
    with pytest.raises(RuntimeError, match="after U0 checkpoint"):
        _drive_cli_foundation_host_loop(
            cli,
            common=common,
            run_id=run_id,
            policy=policy,
            layout=layout,
            start_time=start_time + timedelta(seconds=2),
        )
    monkeypatch.setattr(recovery, "create_checkpoint", original_checkpoint)
    residual = (
        layout.artifacts_dir / "U00-U03-evidence/U02-retrieval-ledger.json"
    )
    residual.parent.mkdir(parents=True, exist_ok=True)
    residual.write_bytes(b"uncheckpointed\n")

    with pytest.raises(
        RuntimeError,
        match="uncheckpointed downstream state",
    ):
        cli.execute(
            ["materialize", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: start_time + timedelta(minutes=1),
            entropy=lambda: b"partial-residual-retry",
        )
    status = json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))
    assert status["status"] == "needs_attention"
    assert status["last_complete_phase"] is None
    assert status["reason"].startswith("foundation recovery requires attention:")


def test_checkpointed_foundation_intake_mismatch_does_not_mask_authority_corruption(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    source_integrity = importlib.import_module("ultra_runtime.source_integrity")
    monkeypatch.setattr(source_integrity, "PRODUCTION_ROOT", policy.production_root)
    authority_repo = _fresh_u1_authority_repo(tmp_path)
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"原命题",'
        '"material":"原封闭材料"}\n'
    ).encode("utf-8")
    common = ["--repo", str(authority_repo), "--mode", "test"]
    start_stdout = StringIO()
    start_time = datetime(2026, 8, 5, 1, 4, 45, tzinfo=timezone.utc)
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time,
        entropy=lambda: b"checkpointed-intake-start",
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    assert cli.execute(
        ["prepare", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=StringIO(),
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(seconds=1),
        entropy=lambda: b"unused",
    ) == 0

    from ultra_runtime import recovery
    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    original_checkpoint = recovery.create_checkpoint

    def stop_after_u0(
        layout,
        phase_store,
        *,
        boundary_kind,
        boundary_id,
        boundary_ordinal,
        artifact_paths,
        now,
    ):
        checkpoint = original_checkpoint(
            layout,
            phase_store,
            boundary_kind=boundary_kind,
            boundary_id=boundary_id,
            boundary_ordinal=boundary_ordinal,
            artifact_paths=artifact_paths,
            now=now,
        )
        if boundary_kind == "phase" and boundary_id == "U0":
            raise RuntimeError("injected after U0 checkpoint")
        return checkpoint

    monkeypatch.setattr(recovery, "create_checkpoint", stop_after_u0)
    with pytest.raises(RuntimeError, match="after U0 checkpoint"):
        _drive_cli_foundation_host_loop(
            cli,
            common=common,
            run_id=run_id,
            policy=policy,
            layout=layout,
            start_time=start_time + timedelta(seconds=2),
        )
    monkeypatch.setattr(recovery, "create_checkpoint", original_checkpoint)

    intake = json.loads(
        (layout.recovery_dir / "request-intake-authority.json").read_text("utf-8")
    )
    assert intake["request_sha256"] == hashlib.sha256(request_bytes).hexdigest()

    replacement = (
        '{"analysis_kind":"closed-input","claim":"替换命题",'
        '"material":"替换封闭材料"}\n'
    ).encode("utf-8")
    (layout.input_dir / "request.bin").write_bytes(replacement)
    replacement_metadata = {
        "request_sha256": hashlib.sha256(replacement).hexdigest(),
        "request_size": len(replacement),
    }
    (layout.input_dir / "request-metadata.json").write_bytes(
        (
            json.dumps(
                replacement_metadata,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )

    from ultra_runtime import jsonio, locks
    from ultra_runtime.schemas import compute_artifact_content_sha256

    authority_path = layout.recovery_dir / "run-authority.json"
    authority_bytes = authority_path.read_bytes()
    authority = jsonio.load_json_object(authority_path)
    malformed_ref = dict(authority["input_refs"][0])
    malformed_ref.pop("media_type")
    authority["input_refs"][0] = malformed_ref
    authority["content_sha256"] = compute_artifact_content_sha256(authority)
    jsonio.atomic_write_json(authority_path, authority)

    with pytest.raises(locks.LeaseNeedsAttentionError) as caught:
        cli.execute(
            ["materialize", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: start_time + timedelta(minutes=1),
            entropy=lambda: b"checkpointed-authority-corruption",
        )
    assert isinstance(caught.value.__cause__, recovery.RecoveryIntegrityError)
    status = json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))
    assert status["status"] == "running"
    jsonio.atomic_write_bytes(authority_path, authority_bytes)

    with pytest.raises(ValueError, match="request intake authority differs"):
        cli.execute(
            ["materialize", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: start_time + timedelta(minutes=1),
            entropy=lambda: b"checkpointed-intake-retry",
        )
    status = json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))
    assert status["status"] == "blocked"
    assert status["current_phase"] == "U0"
    assert status["last_complete_phase"] is None
    assert status["reason"].startswith("fresh foundation input rejected:")


@pytest.mark.parametrize("mutation", ["paired-input", "metadata", "status"])
def test_materialize_rejects_intake_tamper_and_nonfresh_status(
    tmp_path: Path,
    mutation: str,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"原命题",'
        '"material":"原封闭材料"}\n'
    ).encode("utf-8")
    common = ["--repo", str(REPO_ROOT), "--mode", "test"]
    start_stdout = StringIO()
    start_time = datetime(2026, 8, 5, 1, 5, 3, tzinfo=timezone.utc)
    assert cli.execute(
        ["start", *common, "--request-stdin"],
        stdin=BytesIO(request_bytes),
        stdout=start_stdout,
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time,
        entropy=lambda: f"intake-{mutation}-start".encode(),
    ) == 0
    run_id = json.loads(start_stdout.getvalue())["run_id"]
    assert cli.execute(
        ["prepare", *common, "--run-id", run_id],
        stdin=BytesIO(),
        stdout=StringIO(),
        stderr=StringIO(),
        root_policy=policy,
        now=lambda: start_time + timedelta(seconds=1),
        entropy=lambda: b"unused",
    ) == 0

    from ultra_runtime.paths import RunMode, build_run_layout

    layout = build_run_layout(RunMode.TEST, run_id, policy)
    if mutation == "paired-input":
        replacement = (
            '{"analysis_kind":"closed-input","claim":"替换命题",'
            '"material":"替换封闭材料"}\n'
        ).encode("utf-8")
        (layout.input_dir / "request.bin").write_bytes(replacement)
        replacement_metadata = {
            "request_sha256": hashlib.sha256(replacement).hexdigest(),
            "request_size": len(replacement),
        }
        (layout.input_dir / "request-metadata.json").write_bytes(
            (
                json.dumps(
                    replacement_metadata,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
        )
    elif mutation == "metadata":
        metadata_path = layout.input_dir / "request-metadata.json"
        metadata = json.loads(metadata_path.read_text("utf-8"))
        metadata["request_size"] += 1
        metadata_path.write_bytes(
            (
                json.dumps(
                    metadata,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
        )
    else:
        from ultra_runtime.status import RunStatusStore

        store = RunStatusStore(layout)
        running = store.read()
        interrupted = store.transition(
            running,
            "interrupted",
            start_time + timedelta(seconds=2),
            reason="test status boundary",
        )
        store.transition(
            interrupted,
            "running",
            start_time + timedelta(seconds=3),
            current_phase="U1",
            last_complete_phase=None,
            reason="test nonfresh status boundary",
        )

    with pytest.raises(ValueError, match="intake|metadata|status boundary"):
        cli.execute(
            ["materialize", *common, "--run-id", run_id],
            stdin=BytesIO(),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: start_time + timedelta(seconds=4),
            entropy=lambda: b"intake-rejected-materialize",
        )

    status = json.loads((layout.run_dir / "run-status.json").read_text("utf-8"))
    assert status["status"] == "blocked"
    assert not (layout.artifacts_dir / "ultra-run-contract.json").exists()
    assert not (layout.recovery_dir / "phase-events.jsonl").exists()


def test_start_rejects_malformed_explicit_closed_input_without_creating_run(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    policy = _root_policy(tmp_path)
    common = ["--repo", str(REPO_ROOT), "--mode", "test"]
    request_bytes = (
        '{"analysis_kind":"closed-input","claim":"若 A 则 B。",'
        '"material":"封闭材料。","sensitivity":"private"}\n'
    ).encode("utf-8")

    with pytest.raises(ValueError, match="exactly analysis_kind, claim, and material"):
        cli.execute(
            ["start", *common, "--request-stdin"],
            stdin=BytesIO(request_bytes),
            stdout=StringIO(),
            stderr=StringIO(),
            root_policy=policy,
            now=lambda: datetime(2026, 8, 5, 1, 3, 3, tzinfo=timezone.utc),
            entropy=lambda: b"malformed-closed-input-start",
        )

    assert not (policy.test_root / "runs").exists()
    assert not tuple(tmp_path.rglob("run-authority.json"))
    assert not tuple(tmp_path.rglob("request-intake-authority.json"))


def test_root_wrapper_is_a_thin_forwarder_and_help_has_no_escape_hatches() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(ROOT_CLI), "--help"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert all(command in completed.stdout for command in EXPECTED_COMMANDS)
    assert not any(option in completed.stdout for option in FORBIDDEN_CLI_OPTIONS)
    assert (
        "bootstrap eligible fresh U0-U3 or resume, then materialize and publish"
        in " ".join(completed.stdout.split())
    )
