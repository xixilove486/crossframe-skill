from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil


def contained(root: Path, candidate: Path, *, label: str) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise SystemExit(f"unsafe {label}: {resolved}") from error
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--path", nargs="+", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--name")
    parser.add_argument("--ref")
    parser.add_argument("--method")
    args = parser.parse_args()

    repo = Path(args.repo).resolve(strict=True)
    destination = Path(args.dest).resolve(strict=False)
    destination.mkdir(parents=True, exist_ok=True)
    if args.name and len(args.path) != 1:
        raise SystemExit("--name requires exactly one --path")

    fail_skill = os.environ.get("FAKE_SKILL_INSTALLER_FAIL_SKILL")
    for raw_path in args.path:
        source = contained(repo, repo / raw_path, label="source")
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise SystemExit(f"invalid skill source: {source}")
        skill_name = args.name or source.name
        if fail_skill == skill_name:
            raise SystemExit(f"injected installer failure: {skill_name}")
        target = contained(destination, destination / skill_name, label="destination")
        if target.exists():
            raise SystemExit(f"destination already exists: {target}")
        shutil.copytree(source, target)
        print(f"installed {skill_name} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
