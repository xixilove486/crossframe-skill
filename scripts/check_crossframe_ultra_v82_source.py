from __future__ import annotations

# Do not import pathlib/runpy while the repository's script directory is on
# sys.path.  Re-enter with all isolation flags first; this also gives direct
# wrapper invocations the same shadow-module protection as the canonical CLI.
import sys as _bootstrap_sys

if __name__ == "__main__" and not (
    _bootstrap_sys.flags.isolated
    and _bootstrap_sys.flags.no_site
    and _bootstrap_sys.flags.dont_write_bytecode
):
    _bootstrap_os = _bootstrap_sys.modules.get("os")
    if _bootstrap_os is None:
        raise RuntimeError("cannot enter isolated wrapper mode: os is unavailable")
    _bootstrap_os.execv(
        _bootstrap_sys.executable,
        [
            _bootstrap_sys.executable,
            "-I",
            "-S",
            "-B",
            _bootstrap_os.path.abspath(__file__),
            *_bootstrap_sys.argv[1:],
        ],
    )

from pathlib import Path
import runpy


CANONICAL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/crossframe-ultra/scripts/check_crossframe_ultra_v82_source.py"
)


if __name__ == "__main__":
    runpy.run_path(str(CANONICAL_SCRIPT), run_name="__main__")
