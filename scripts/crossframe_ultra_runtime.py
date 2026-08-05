from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_main():
    repo = Path(__file__).resolve().parents[1]
    target = repo / "skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py"
    scripts_dir = target.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(
        "crossframe_ultra_skill_runtime", target
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load CrossFrame Ultra runtime: {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


if __name__ == "__main__":
    raise SystemExit(_load_main()())
