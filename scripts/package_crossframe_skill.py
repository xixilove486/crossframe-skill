from __future__ import annotations

import argparse
import datetime as dt
import zipfile
from pathlib import Path


INCLUDE_ROOTS = [
    ".claude",
    ".clinerules",
    ".continue",
    ".cursor",
    ".github",
    ".roo",
    ".windsurf",
    "docs",
    "scripts",
    "site",
    "skills",
]

INCLUDE_FILES = [
    ".aider.conf.yml",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CONVENTIONS.md",
    "GEMINI.md",
    "INTERFACES.md",
    "LICENSE",
    "README.md",
    "llms.txt",
]

EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "artifacts",
    "build",
    "dist",
    "drafts",
    "node_modules",
    "outputs",
    "runs",
    "venv",
    "work",
}

EXCLUDED_NAMES = {
    ".env",
    ".env.local",
    ".v8-full-source.lock",
    ".DS_Store",
    "Thumbs.db",
}

EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def iter_package_files(repo: Path):
    for rel in INCLUDE_FILES:
        path = repo / rel
        if path.is_file():
            yield path
    for root_name in INCLUDE_ROOTS:
        root = repo / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.name not in EXCLUDED_NAMES
                and path.suffix.casefold() not in EXCLUDED_SUFFIXES
                and not any(part in EXCLUDED_PARTS for part in path.relative_to(repo).parts)
            ):
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the public CrossFrame skill suite.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--version", default="v5.1.7", help="Release version label.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for the zip artifact.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    output_dir = (repo / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_path = output_dir / f"crossframe-skill-suite-{args.version}-{stamp}.zip"

    files = sorted(set(iter_package_files(repo)))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(repo).as_posix())

    print(f"created: {zip_path}")
    print(f"files: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
