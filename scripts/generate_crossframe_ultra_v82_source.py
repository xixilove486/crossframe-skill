from __future__ import annotations

from pathlib import Path
import runpy


CANONICAL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/crossframe-ultra/scripts/generate_crossframe_ultra_v82_source.py"
)


if __name__ == "__main__":
    runpy.run_path(str(CANONICAL_SCRIPT), run_name="__main__")
