from __future__ import annotations

from pathlib import Path
import runpy


CANONICAL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/crossframe-promax/scripts/check_crossframe_promax_v8_full_source.py"
)


if __name__ == "__main__":
    runpy.run_path(str(CANONICAL_SCRIPT), run_name="__main__")
