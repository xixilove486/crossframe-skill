from __future__ import annotations

# This Python wrapper is trustworthy only when isolation was established at
# interpreter startup.  A non-isolated process may already have executed
# PYTHONPATH sitecustomize code, so it must fail instead of attempting re-entry.
import sys as _bootstrap_sys


_ISOLATION_ERROR = (
    "trusted source validation requires direct Python startup flags -I -S -B"
)
if __name__ == "__main__" and not (
    _bootstrap_sys.flags.isolated
    and _bootstrap_sys.flags.no_site
    and _bootstrap_sys.flags.dont_write_bytecode
):
    if "--json" in _bootstrap_sys.argv[1:]:
        _bootstrap_sys.stdout.write(
            '{"errors":["trusted source validation requires direct Python '
            'startup flags -I -S -B"],"ok":false}\n'
        )
    else:
        _bootstrap_sys.stderr.write(f"error: {_ISOLATION_ERROR}\n")
    raise SystemExit(2)


import os
import subprocess


CANONICAL_SCRIPT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "skills",
        "crossframe-ultra",
        "scripts",
        "check_crossframe_ultra_v82_source.py",
    )
)


if __name__ == "__main__":
    command = [
        _bootstrap_sys.executable,
        "-I",
        "-S",
        "-B",
        CANONICAL_SCRIPT,
        *_bootstrap_sys.argv[1:],
    ]
    completed = subprocess.run(command, check=False)
    raise SystemExit(completed.returncode)
