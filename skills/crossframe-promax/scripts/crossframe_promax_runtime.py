from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Sequence

from promax_runtime import (
    CANONICAL_VALIDATOR_IDS,
    build_capability_disclosure,
    initialize_run,
)
from promax_runtime.jsonio import canonical_json_bytes
from promax_runtime.materialization import materialize_run, prepare_run
from promax_runtime.source_integrity import build_source_snapshot
from promax_runtime.state_machine import (
    RunBinding,
    append_phase_event,
    seal_phase_event,
    validate_phase_history,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def _initialize_directory(
    run_dir: Path,
    initialized: dict[str, dict[str, object]],
) -> None:
    target = run_dir.resolve()
    if target.exists():
        raise ValueError(f"run directory already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent))
    )
    try:
        contract_path = stage / "promax-run-contract.json"
        _write_json(contract_path, initialized["run_contract"])
        contract = initialized["run_contract"]
        output_artifact_hashes = {
            "promax-run-contract.json": hashlib.sha256(
                contract_path.read_bytes()
            ).hexdigest()
        }
        source_snapshot = initialized.get("source_snapshot")
        if source_snapshot is not None:
            snapshot_path = stage / "promax-source-snapshot.json"
            _write_json(snapshot_path, source_snapshot)
            output_artifact_hashes["promax-source-snapshot.json"] = hashlib.sha256(
                snapshot_path.read_bytes()
            ).hexdigest()
        binding = RunBinding(
            run_id=contract["run_id"],
            run_nonce=contract["run_nonce"],
            request_sha256=contract["request_sha256"],
            source_snapshot_sha256=contract["source_snapshot_sha256"],
        )
        state = validate_phase_history([], expected_binding=binding)
        event = seal_phase_event(
            state,
            "P0",
            input_artifact_hashes={},
            output_artifact_hashes=output_artifact_hashes,
        )
        append_phase_event(
            stage / "promax-phase-events.jsonl",
            event,
            expected_head_sha256=None,
        )
        os.replace(stage, target)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CrossFrame ProMax v8 artifact runtime control plane"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser(
        "snapshot", help="print the canonical v8 source snapshot binding"
    )
    snapshot.add_argument("--repo", type=Path, default=Path.cwd())
    snapshot.add_argument("--verified-at", default=None)

    init = subparsers.add_parser(
        "init", help="initialize a new immutable P0 artifact run"
    )
    init.add_argument("--repo", type=Path, default=Path.cwd())
    init.add_argument("--run-dir", type=Path, required=True)
    init.add_argument("--request", required=True)
    init.add_argument(
        "--mode",
        default="promax-artifact-run",
        choices=(
            "promax-artifact-run",
            "promax-complete",
            "promax-design-review",
            "promax-blocked/progress",
        ),
    )
    init.add_argument("--run-id")
    init.add_argument("--created-at")
    init.add_argument("--subagents", action="store_true", default=False)
    init.add_argument("--no-subagents", action="store_false", dest="subagents")
    init.add_argument("--max-parallelism", type=int, default=4)
    init.add_argument("--network", action="store_true", default=False)
    init.add_argument(
        "--recommendation-required", action="store_true", default=False
    )
    init.add_argument("--blocker-category")
    init.add_argument("--blocker-detail")

    prepare = subparsers.add_parser(
        "prepare",
        help="seal deterministic P1 reads and create a 709-item authoring pack",
    )
    prepare.add_argument("--repo", type=Path, default=Path.cwd())
    prepare.add_argument("--run-dir", type=Path, required=True)
    prepare.add_argument("--authoring-dir", type=Path, required=True)
    prepare.add_argument("--read-at", default=None)

    materialize = subparsers.add_parser(
        "materialize",
        help="validate model semantics and publish the P2-P10 control plane",
    )
    materialize.add_argument("--repo", type=Path, default=Path.cwd())
    materialize.add_argument("--run-dir", type=Path, required=True)
    materialize.add_argument("--authoring-dir", type=Path, required=True)
    materialize.add_argument("--request", required=True)
    materialize.add_argument("--generated-at", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "snapshot":
        snapshot = build_source_snapshot(
            args.repo,
            verified_at=args.verified_at or _utc_now(),
        )
        print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "prepare":
        prepared = prepare_run(
            args.repo,
            run_dir=args.run_dir,
            authoring_dir=args.authoring_dir,
            read_at=args.read_at or _utc_now(),
        )
        print(json.dumps(prepared, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "materialize":
        materialized = materialize_run(
            args.repo,
            run_dir=args.run_dir,
            authoring_dir=args.authoring_dir,
            request_text=args.request,
            generated_at=args.generated_at or _utc_now(),
        )
        print(json.dumps(materialized, ensure_ascii=False, sort_keys=True))
        return 0 if materialized.get("published") is True else 1

    created_at = args.created_at or _utc_now()
    blocker = None
    if args.blocker_category is not None or args.blocker_detail is not None:
        if args.blocker_category is None or args.blocker_detail is None:
            raise ValueError("both blocker category and detail are required")
        blocker = {
            "category": args.blocker_category,
            "detail": args.blocker_detail,
        }
    capabilities = build_capability_disclosure(
        subagents_available=args.subagents,
        max_parallelism=args.max_parallelism if args.subagents else 0,
        network_available=args.network,
        live_retrieval=args.network,
        files_writable=(
            blocker is None or blocker.get("category") != "filesystem_unwritable"
        ),
        validator_ids=(
            ()
            if blocker is not None
            and blocker.get("category") == "required_tool_forbidden"
            else CANONICAL_VALIDATOR_IDS
        ),
        validators_available=(
            blocker is None or blocker.get("category") != "required_tool_forbidden"
        ),
        validators_executable=(
            blocker is None or blocker.get("category") != "required_tool_forbidden"
        ),
    )
    initialized = initialize_run(
        args.repo,
        args.request,
        mode=args.mode,
        capabilities=capabilities,
        created_at=created_at,
        run_id=args.run_id,
        blocker=blocker,
        recommendation_required=args.recommendation_required,
    )
    if blocker is not None and blocker.get("category") == "filesystem_unwritable":
        print(
            json.dumps(
                {
                    "status": "blocked/progress",
                    "phase": "P0-not-materialized",
                    "materialized": False,
                    "run_id": initialized["run_contract"]["run_id"],
                    "blocker": blocker,
                    "run_contract": initialized["run_contract"],
                    "source_snapshot": initialized.get("source_snapshot"),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    _initialize_directory(args.run_dir, initialized)
    blocked = args.mode == "promax-blocked/progress"
    print(
        json.dumps(
            {
                "status": "blocked/progress" if blocked else "initialized",
                "run_id": initialized["run_contract"]["run_id"],
                "run_dir": str(args.run_dir.resolve()),
                "phase": "P0",
                "materialized": True,
                "blocker": blocker if blocked else None,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
