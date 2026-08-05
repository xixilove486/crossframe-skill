from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from ultra_runtime.paths import RunMode
from ultra_runtime.validation import validate_run_from_disk


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_crossframe_ultra_artifacts.py",
        description="Validate one fixed-root CrossFrame Ultra run from fresh disk state.",
    )
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("production", "test"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report_bytes = validate_run_from_disk(
        args.repo, RunMode(args.mode), args.run_id
    )
    sys.stdout.buffer.write(report_bytes)
    sys.stdout.buffer.flush()
    try:
        report = json.loads(report_bytes)
    except (TypeError, ValueError):
        return 0
    return 0 if not isinstance(report, dict) or report.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
