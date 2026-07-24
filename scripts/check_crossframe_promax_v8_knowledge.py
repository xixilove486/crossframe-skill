from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_checker():
    path = (
        Path(__file__).resolve().parents[1]
        / "skills/crossframe-promax/scripts/check_crossframe_promax_v8_knowledge.py"
    )
    spec = importlib.util.spec_from_file_location("crossframe_promax_v8_knowledge_checker", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load checker: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(_load_checker().main())
