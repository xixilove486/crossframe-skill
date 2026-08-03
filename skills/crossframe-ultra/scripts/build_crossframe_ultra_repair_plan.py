from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Sequence

from ultra_runtime.jsonio import canonical_json_bytes
from ultra_runtime.paths import (
    RootPolicy,
    RunMode,
    build_run_layout,
    default_root_policy,
)
from ultra_runtime.repair import (
    build_repair_plan,
    commit_repair_plan,
    current_attempt_identity,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build one bounded CrossFrame Ultra repair plan"
    )
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--mode",
        required=True,
        choices=(RunMode.PRODUCTION.value, RunMode.TEST.value),
    )
    parser.add_argument("--run-id", required=True)
    return parser


def _validated_repo(path: Path) -> Path:
    repo = path.resolve(strict=True)
    if not repo.is_dir():
        raise ValueError("--repo must name a repository directory")
    required = (
        repo
        / "skills"
        / "crossframe-ultra"
        / "schemas"
        / "ultra-repair-plan.schema.json"
    )
    if not required.is_file():
        raise ValueError("--repo is not a CrossFrame Ultra repository")
    return repo


def main(
    argv: Sequence[str] | None = None,
    *,
    policy: RootPolicy | None = None,
    now: datetime | None = None,
) -> int:
    try:
        args = _parser().parse_args(argv)
        _validated_repo(args.repo)
        selected_policy = default_root_policy() if policy is None else policy
        selected_now = datetime.now(timezone.utc) if now is None else now
        layout = build_run_layout(
            RunMode(args.mode),
            args.run_id,
            selected_policy,
        )
        attempt_id, attempt_number = current_attempt_identity(
            layout,
            now=selected_now,
        )
        plan = build_repair_plan(
            layout,
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            now=selected_now,
        )
        committed = commit_repair_plan(
            layout,
            attempt_id=attempt_id,
            plan=plan,
        )
        sys.stdout.buffer.write(canonical_json_bytes(committed))
        return 0
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
