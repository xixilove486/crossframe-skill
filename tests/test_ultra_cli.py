from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO, StringIO
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from tests.pytest_import_guard import pytest


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
        "start": {"--repo", "--mode", "--request-file", "--request-stdin"},
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
    prompt = request_bytes.decode("utf-8", errors="ignore").replace("\x00", "")
    for path in (tmp_path / "test").rglob("*"):
        assert prompt not in path.name
        if path.is_file() and path != run_dir / "input/request.bin":
            assert request_bytes not in path.read_bytes()


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
