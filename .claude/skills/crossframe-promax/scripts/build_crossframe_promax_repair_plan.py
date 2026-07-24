from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Sequence

from promax_runtime.jsonio import canonical_json_bytes, load_json
from promax_runtime.repair import build_repair_plan
from promax_runtime.validation import build_machine_failure


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _write_atomic(path: Path, value: object) -> None:
    target = Path(path)
    if not target.is_absolute():
        raise ValueError("atomic repair-plan output path must be absolute")
    if target.is_symlink():
        raise ValueError("repair-plan output must not be a symbolic link")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.stage-",
        dir=str(target.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _isolated_output_path(path: Path, audit_inputs: Sequence[Path]) -> Path:
    absolute = Path(os.path.abspath(path))
    target = absolute.parent.resolve(strict=False) / absolute.name
    if target.is_symlink():
        raise ValueError("repair-plan output must not be a symbolic link")
    input_paths = [Path(item).resolve(strict=True) for item in audit_inputs]
    target_spelling = os.path.normcase(str(target))
    for input_path in input_paths:
        if target_spelling == os.path.normcase(str(input_path)):
            raise ValueError("repair-plan output must not overwrite an audit input")
    if target.exists():
        if not target.is_file():
            raise ValueError("repair-plan output must be a regular file path")
        for input_path in input_paths:
            if os.path.samefile(target, input_path):
                raise ValueError(
                    "repair-plan output must not alias an audit input file"
                )
    return target


class _StructuredArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _StructuredArgumentParser(
        description="Build one local CrossFrame ProMax v8 repair plan"
    )
    parser.add_argument("--failed-report", type=Path, required=True)
    parser.add_argument("--failures", type=Path, required=True)
    parser.add_argument("--created-at")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        failed_report = load_json(args.failed_report)
        failures = load_json(args.failures)
        if not isinstance(failed_report, dict):
            raise ValueError("failed report input must be a JSON object")
        if not isinstance(failures, list):
            raise ValueError("failures input must be a JSON array")
        plan = build_repair_plan(
            failed_report,
            failures,
            created_at=args.created_at or _utc_now(),
        )
        output_path = None
        if args.output is not None:
            output_path = _isolated_output_path(
                args.output,
                (args.failed_report, args.failures),
            )
            _write_atomic(output_path, plan)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "repair_plan": plan,
                    "output_path": (
                        str(output_path) if output_path is not None else None
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (OSError, TypeError, ValueError) as error:
        failure = build_machine_failure(
            error_type="repair_plan_input_invalid",
            artifact="promax-repair-plan.json",
            affected_phase="P11",
            repair_action="correct_repair_plan_inputs",
        )
        print(
            json.dumps(
                {"status": "error", "error": failure},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
