from __future__ import annotations

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    child = (
        Path(__file__).resolve().parents[1]
        / "skills/crossframe-ultra/scripts/check_crossframe_ultra_artifacts.py"
    )
    sys.path.insert(0, str(child.parent))
    runpy.run_path(str(child), run_name="__main__")
