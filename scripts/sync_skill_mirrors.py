from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


CROSSFRAME_SKILLS = [
    "crossframe",
    "crossframe-suite",
    "crossframe-essay",
    "crossframe-critical",
    "crossframe-review",
    "crossframe-dialogue",
    "crossframe-casebook",
    "crossframe-history",
    "crossframe-inquiry",
    "crossframe-max",
    "crossframe-promax",
    "crossframe-public",
    "crossframe-org",
    "crossframe-teach",
    "crossframe-debate",
    "crossframe-notebook",
]

IGNORED_DIRECTORY_NAMES = {"__pycache__", ".pytest_cache"}
IGNORED_FILE_NAMES = {".v8-full-source.lock"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.name not in IGNORED_FILE_NAMES
        and not any(part in IGNORED_DIRECTORY_NAMES for part in path.relative_to(root).parts)
    }


def same_tree(left: Path, right: Path) -> bool:
    return left.is_dir() and right.is_dir() and tree_hashes(left) == tree_hashes(right)


def sync_skill(src: Path, dst: Path, check_only: bool) -> None:
    require(src.is_dir(), f"missing source skill: {src}")
    if check_only:
        require(same_tree(src, dst), f"mirror drift: {dst}")
        return

    if dst.exists():
        require(dst.is_dir(), f"mirror destination is not a directory: {dst}")
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(*IGNORED_DIRECTORY_NAMES, *IGNORED_FILE_NAMES),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync CrossFrame skill mirrors from skills/crossframe*.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument(
        "--mirror",
        action="append",
        default=[],
        help="Mirror skill root. Defaults to .claude/skills when omitted.",
    )
    parser.add_argument("--check", action="store_true", help="Only check for mirror drift.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    source_root = repo / "skills"
    require(source_root.is_dir(), f"missing skills directory: {source_root}")
    mirrors = [Path(value).resolve() for value in (args.mirror or [repo / ".claude" / "skills"])]

    for mirror_root in mirrors:
        if not args.check:
            mirror_root.mkdir(parents=True, exist_ok=True)
        for skill in CROSSFRAME_SKILLS:
            sync_skill(source_root / skill, mirror_root / skill, args.check)
        print(f"ok: {'checked' if args.check else 'synced'} {mirror_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
