from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Sequence


CANONICAL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/crossframe-ultra/scripts/build_crossframe_ultra_release_manifest.py"
)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    completed = subprocess.run(
        [sys.executable, "-B", str(CANONICAL_SCRIPT), *arguments],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
