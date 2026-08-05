from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
import importlib
from io import BytesIO
import json
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Any, BinaryIO, TextIO


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ultra_runtime.indexes import IndexStore
from ultra_runtime.jsonio import (
    atomic_write_bytes,
    atomic_write_json,
    load_json_object,
    load_json_object_bytes,
    sha256_bytes,
)
from ultra_runtime.locks import acquire_run_lease, release_run_lease
from ultra_runtime.materialization import prepare_authoring, seal_request_intake_authority
from ultra_runtime.paths import (
    RootPolicy,
    RunLayout,
    RunMode,
    build_run_layout,
    create_run_id,
    default_root_policy,
)
from ultra_runtime.status import RunStatusStore, _record_to_object


FORBIDDEN_CLI_OPTIONS = (
    "--run-dir",
    "--authoring-dir",
    "--output-root",
    "--destination",
    "--fallback",
)
COMMANDS = (
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


def _add_repo_mode(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True, metavar="PATH")
    parser.add_argument("--mode", required=True, choices=tuple(mode.value for mode in RunMode))


def _add_run(parser: argparse.ArgumentParser) -> None:
    _add_repo_mode(parser)
    parser.add_argument("--run-id", required=True, metavar="RUN_ID")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crossframe_ultra_runtime.py",
        description="Run the fixed-root CrossFrame Ultra runtime.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser(
        "start", help="create a fixed-root run", add_help=False
    )
    _add_repo_mode(start)
    request = start.add_mutually_exclusive_group(required=True)
    request.add_argument("--request-file", metavar="PATH")
    request.add_argument("--request-stdin", action="store_true")

    prepare = subparsers.add_parser(
        "prepare", help="prepare model-owned authoring slots", add_help=False
    )
    _add_run(prepare)

    checkpoint = subparsers.add_parser(
        "checkpoint", help="checkpoint one completed phase", add_help=False
    )
    _add_run(checkpoint)
    checkpoint.add_argument("--phase", required=True, choices=tuple(f"U{number}" for number in range(12)))

    materialize = subparsers.add_parser(
        "materialize",
        help="bootstrap eligible fresh U0-U3 or resume, then materialize and publish",
        add_help=False,
    )
    _add_run(materialize)

    validate = subparsers.add_parser(
        "validate", help="run the fresh read-only checker", add_help=False
    )
    _add_run(validate)
    validate.add_argument("--json", action="store_true", dest="json_output")

    repair = subparsers.add_parser(
        "repair-plan", help="build the bounded repair plan", add_help=False
    )
    _add_run(repair)

    resume = subparsers.add_parser(
        "resume", help="resume from the selected checkpoint", add_help=False
    )
    _add_run(resume)

    fork = subparsers.add_parser(
        "fork", help="fork only for a known version migration", add_help=False
    )
    _add_run(fork)
    fork.add_argument("--reason", required=True, metavar="TEXT")

    cancel = subparsers.add_parser("cancel", help="cancel a run", add_help=False)
    _add_run(cancel)

    rebuild = subparsers.add_parser(
        "rebuild-index", help="rebuild neutral fixed-root indexes", add_help=False
    )
    _add_repo_mode(rebuild)

    return parser


def _validate_repo(value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("--repo must be a nonempty path")
    repo = Path(value).resolve()
    if not repo.is_dir():
        raise ValueError(f"--repo is not a directory: {repo}")
    if not (repo / "skills" / "crossframe-ultra").is_dir():
        raise ValueError(f"--repo does not contain skills/crossframe-ultra: {repo}")
    return repo


def _mode(value: str) -> RunMode:
    return RunMode(value)


def _layout(args: argparse.Namespace, policy: RootPolicy) -> RunLayout:
    return build_run_layout(_mode(args.mode), args.run_id, policy)


def _read_stdin_bytes(stdin: object) -> bytes:
    stream = getattr(stdin, "buffer", stdin)
    read = getattr(stream, "read", None)
    if not callable(read):
        raise TypeError("stdin must expose a binary read() method")
    value = read()
    if isinstance(value, str):
        return value.encode("utf-8")
    if not isinstance(value, bytes):
        raise TypeError("stdin read() must return bytes or text")
    return value


def _json_safe(value: object) -> object:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(child) for child in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    fields = getattr(value, "__dict__", None)
    if isinstance(fields, dict):
        return _json_safe(fields)
    return str(value)


def _emit_json(stdout: TextIO, value: object) -> None:
    stdout.write(
        json.dumps(
            _json_safe(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def _task12(module_name: str):
    try:
        return importlib.import_module(f"ultra_runtime.{module_name}")
    except ModuleNotFoundError as error:
        if error.name == f"ultra_runtime.{module_name}":
            raise RuntimeError(
                f"Task 12 dependency ultra_runtime.{module_name} is not integrated"
            ) from error
        raise


@contextmanager
def _run_lease(layout: RunLayout, now: datetime):
    lease = acquire_run_lease(layout, now, timedelta(minutes=15))
    try:
        yield lease
    finally:
        release_run_lease(layout, lease)


def _start(
    args: argparse.Namespace,
    *,
    stdin: object,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
    entropy: bytes,
) -> int:
    if args.request_stdin:
        request_bytes = _read_stdin_bytes(stdin)
    else:
        request_path = Path(args.request_file).resolve()
        if not request_path.is_file():
            raise ValueError(f"--request-file is not a file: {request_path}")
        request_bytes = request_path.read_bytes()
    run_id = create_run_id(now, entropy)
    layout = build_run_layout(_mode(args.mode), run_id, policy)
    if layout.run_dir.exists():
        raise FileExistsError(f"run already exists: {run_id}")
    layout.run_dir.mkdir(parents=True)
    atomic_write_bytes(layout.input_dir / "request.bin", request_bytes)
    request_sha256 = sha256_bytes(request_bytes)
    atomic_write_json(
        layout.input_dir / "request-metadata.json",
        {"request_sha256": request_sha256, "request_size": len(request_bytes)},
    )
    created = RunStatusStore(layout).create(now)
    seal_request_intake_authority(
        layout,
        request_sha256=request_sha256,
        request_size=len(request_bytes),
        created_at=created.created_at,
    )
    IndexStore(layout.root).rebuild()
    _emit_json(
        stdout,
        {
            "mode": args.mode,
            "request_sha256": request_sha256,
            "run_id": run_id,
            "status": "created",
        },
    )
    return 0


def _advance_to_running(layout: RunLayout, now: datetime) -> object:
    store = RunStatusStore(layout)
    current = store.read()
    if current.status == "running":
        return current
    if current.status not in {"created", "interrupted", "blocked", "needs_attention"}:
        raise RuntimeError(f"run status {current.status!r} cannot enter authoring")
    return store.transition(
        current,
        "running",
        now,
        current_phase=current.current_phase,
        last_complete_phase=current.last_complete_phase,
        reason="runtime command admitted",
        validation_passed=False,
    )


def _prepare(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
) -> int:
    layout = _layout(args, policy)
    with _run_lease(layout, now):
        _advance_to_running(layout, now)
        prepared = prepare_authoring(layout)
    IndexStore(layout.root).rebuild()
    _emit_json(
        stdout,
        {
            "authoring_dir": str(prepared.authoring_dir.resolve()),
            "control_path": str(prepared.control_path.resolve()),
            "run_id": args.run_id,
            "slots": list(prepared.relative_slots),
        },
    )
    return 0


def _phase_store_from_recovery(result: object) -> object:
    candidate = getattr(result, "phase_store", None)
    if candidate is None and isinstance(result, Mapping):
        candidate = result.get("phase_store")
    if candidate is None and callable(getattr(result, "complete", None)):
        candidate = result
    if candidate is None or not callable(getattr(candidate, "complete", None)):
        raise RuntimeError("resume_run did not return the existing PhaseStore")
    return candidate


def _matching_artifact_paths(
    layout: RunLayout, phase_store: object, phase_id: str
) -> tuple[Path, ...]:
    events = getattr(phase_store, "events", None)
    if not isinstance(events, tuple):
        raise RuntimeError("existing PhaseStore does not expose its events property")
    matching = [
        event
        for event in events
        if isinstance(event, Mapping)
        and event.get("phase_id") == phase_id
        and event.get("status") == "complete"
    ]
    if not matching:
        raise RuntimeError(f"phase {phase_id} has no complete phase event")
    hashes = matching[-1].get(
        "output_artifact_hashes", matching[-1].get("artifact_hashes")
    )
    if not isinstance(hashes, list) or not hashes:
        raise RuntimeError(f"phase {phase_id} has no artifact hashes")
    wanted = list(hashes)
    candidates: dict[str, list[Path]] = {digest: [] for digest in wanted if isinstance(digest, str)}
    excluded_parts = {"validation", "recovery", "logs", ".staging"}
    for path in layout.run_dir.rglob("*"):
        if not path.is_file() or excluded_parts.intersection(path.parts):
            continue
        digest = sha256_bytes(path.read_bytes())
        if digest in candidates:
            candidates[digest].append(path)
    resolved = []
    for digest in wanted:
        paths = candidates.get(digest, [])
        if not paths:
            raise RuntimeError(f"phase {phase_id} artifact hash is absent from disk: {digest}")
        paths.sort(key=lambda path: (layout.artifacts_dir not in path.parents, str(path)))
        resolved.append(paths[0])
    return tuple(resolved)


def _checkpoint(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
) -> int:
    layout = _layout(args, policy)
    recovery = _task12("recovery")
    with _run_lease(layout, now):
        resumed = recovery.resume_run(layout, now=now)
        phase_store = _phase_store_from_recovery(resumed)
        artifact_paths = _matching_artifact_paths(layout, phase_store, args.phase)
        checkpoint = recovery.create_checkpoint(
            layout,
            phase_store,
            boundary_kind="phase",
            boundary_id=args.phase,
            boundary_ordinal=0,
            artifact_paths=artifact_paths,
            now=now,
        )
    _emit_json(stdout, checkpoint)
    return 0


def _checker_command(repo: Path, mode: RunMode, run_id: str) -> list[str]:
    checker = repo / "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py"
    if not checker.is_file():
        raise RuntimeError(f"fresh checker is not installed: {checker}")
    return [
        sys.executable,
        "-B",
        str(checker),
        "--repo",
        str(repo),
        "--mode",
        mode.value,
        "--run-id",
        run_id,
        "--json",
    ]


def _fresh_checker(repo: Path, mode: RunMode, run_id: str) -> bytes:
    completed = subprocess.run(
        _checker_command(repo, mode, run_id),
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    if not completed.stdout:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"fresh checker produced no canonical stdout: {detail}")
    try:
        report = load_json_object_bytes(completed.stdout, source="fresh checker stdout")
    except Exception as error:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"fresh checker stdout is not canonical JSON: {detail}") from error
    if completed.returncode not in {0, 1}:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"fresh checker exited with {completed.returncode}: {detail}"
        )
    if report.get("overall_status") == "pass" and completed.returncode != 0:
        raise RuntimeError("fresh checker exit status disagrees with passing report")
    return completed.stdout


def _commit_report(layout: RunLayout, report_bytes: bytes) -> dict[str, object]:
    validation = _task12("validation")
    report = load_json_object_bytes(report_bytes, source="fresh checker stdout")
    return validation.commit_validation_attempt(
        layout,
        attempt_id=report["attempt_id"],
        report_bytes=report_bytes,
        expected_manifest_sha256=report["manifest_sha256"],
        expected_validator_set_sha256=report["validator_set_sha256"],
    )


def _validate(
    args: argparse.Namespace,
    *,
    repo: Path,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
) -> int:
    mode = _mode(args.mode)
    layout = _layout(args, policy)
    with _run_lease(layout, now):
        report_bytes = _fresh_checker(repo, mode, args.run_id)
        report = load_json_object_bytes(report_bytes, source="fresh checker stdout")
        _commit_report(layout, report_bytes)
    if args.json_output:
        stdout.write(report_bytes.decode("utf-8"))
    else:
        _emit_json(
            stdout,
            {
                "attempt_id": report["attempt_id"],
                "overall_status": report["overall_status"],
                "run_id": args.run_id,
            },
        )
    return 0 if report.get("overall_status") == "pass" else 1


def _repair_plan(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
) -> int:
    layout = _layout(args, policy)
    repair = _task12("repair")
    current_report = load_json_object(
        layout.validation_current_dir / "ultra-validator-report.json"
    )
    attempts = [path for path in layout.validation_attempts_dir.iterdir() if path.is_dir()]
    with _run_lease(layout, now):
        plan = repair.build_repair_plan(
            layout,
            attempt_id=current_report["attempt_id"],
            attempt_number=len(attempts),
            now=now,
        )
    _emit_json(stdout, plan)
    return 0


def _resume(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
) -> int:
    layout = _layout(args, policy)
    recovery = _task12("recovery")
    with _run_lease(layout, now):
        result = recovery.resume_run(layout, now=now)
    IndexStore(layout.root).rebuild()
    _emit_json(
        stdout,
        {
            "outcome": result.outcome,
            "compatibility_result": result.compatibility_result,
            "checkpoint": result.checkpoint,
            "status": (
                None if result.status is None else _record_to_object(result.status)
            ),
        },
    )
    return 0


def _fork(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
    entropy: bytes,
) -> int:
    layout = _layout(args, policy)
    recovery = _task12("recovery")
    with _run_lease(layout, now):
        result = recovery.fork_run(
            layout,
            mode=_mode(args.mode),
            policy=policy,
            reason=args.reason,
            now=now,
            entropy=entropy,
        )
    IndexStore(layout.root).rebuild()
    _emit_json(stdout, result)
    return 0


def _cancel(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
) -> int:
    layout = _layout(args, policy)
    recovery = _task12("recovery")
    with _run_lease(layout, now):
        status = recovery.cancel_run(
            layout,
            reason="operator requested cancellation",
            now=now,
        )
    IndexStore(layout.root).rebuild()
    _emit_json(stdout, status)
    return 0


def _materialize(
    args: argparse.Namespace,
    *,
    repo: Path,
    stdout: TextIO,
    policy: RootPolicy,
    now: datetime,
    entropy: bytes,
) -> int:
    materialization = importlib.import_module("ultra_runtime.materialization")
    runner = getattr(materialization, "materialize_complete_run", None)
    if not callable(runner):
        raise RuntimeError("Task 13 complete materialization orchestrator is unavailable")
    result = runner(
        repo,
        _mode(args.mode),
        args.run_id,
        policy=policy,
        now=now,
        entropy=entropy,
        fresh_check=lambda stage: _fresh_checker(repo, _mode(args.mode), args.run_id),
        commit_report=lambda stage, report_bytes: _commit_report(
            build_run_layout(_mode(args.mode), args.run_id, policy), report_bytes
        ),
    )
    _emit_json(stdout, result)
    return 0


def execute(
    argv: list[str] | tuple[str, ...],
    *,
    stdin: object,
    stdout: TextIO,
    stderr: TextIO,
    root_policy: RootPolicy | None = None,
    now: Callable[[], datetime] | None = None,
    entropy: Callable[[], bytes] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv))
    repo = _validate_repo(args.repo)
    policy = default_root_policy() if root_policy is None else root_policy
    if not isinstance(policy, RootPolicy):
        raise TypeError("root_policy must be a RootPolicy")
    now_value = (lambda: datetime.now(timezone.utc)) if now is None else now
    entropy_value = (lambda: secrets.token_bytes(32)) if entropy is None else entropy
    if not callable(now_value) or not callable(entropy_value):
        raise TypeError("now and entropy must be callables")
    current_time = now_value()

    if args.command == "start":
        return _start(
            args,
            stdin=stdin,
            stdout=stdout,
            policy=policy,
            now=current_time,
            entropy=entropy_value(),
        )
    if args.command == "rebuild-index":
        mode = _mode(args.mode)
        root = policy.production_root if mode is RunMode.PRODUCTION else policy.test_root
        IndexStore(root).rebuild()
        _emit_json(stdout, {"mode": mode.value, "rebuilt": True, "root": str(root.resolve())})
        return 0
    if args.command == "prepare":
        return _prepare(args, stdout=stdout, policy=policy, now=current_time)
    if args.command == "checkpoint":
        return _checkpoint(args, stdout=stdout, policy=policy, now=current_time)
    if args.command == "materialize":
        return _materialize(
            args,
            repo=repo,
            stdout=stdout,
            policy=policy,
            now=current_time,
            entropy=entropy_value(),
        )
    if args.command == "validate":
        return _validate(
            args,
            repo=repo,
            stdout=stdout,
            policy=policy,
            now=current_time,
        )
    if args.command == "repair-plan":
        return _repair_plan(args, stdout=stdout, policy=policy, now=current_time)
    if args.command == "resume":
        return _resume(args, stdout=stdout, policy=policy, now=current_time)
    if args.command == "fork":
        return _fork(
            args,
            stdout=stdout,
            policy=policy,
            now=current_time,
            entropy=entropy_value(),
        )
    if args.command == "cancel":
        return _cancel(args, stdout=stdout, policy=policy, now=current_time)
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    try:
        return execute(
            sys.argv[1:] if argv is None else argv,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ("COMMANDS", "FORBIDDEN_CLI_OPTIONS", "build_parser", "execute", "main")
