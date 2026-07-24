from __future__ import annotations

from pathlib import Path
import runpy
import sys


target = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "crossframe-promax"
    / "scripts"
    / "build_crossframe_promax_repair_plan.py"
)
sys.path.insert(0, str(target.parent))
runpy.run_path(str(target), run_name="__main__")
