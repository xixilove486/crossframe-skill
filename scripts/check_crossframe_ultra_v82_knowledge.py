"""Isolated entry point for the CrossFrame Ultra v8.2 knowledge checker."""

import os
import sys


def _canonical_script() -> str:
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            "skills",
            "crossframe-ultra",
            "scripts",
            "check_crossframe_ultra_v82_knowledge.py",
        )
    )


if __name__ == "__main__":
    # The wrapper itself imports only frozen/built-in modules, then replaces
    # this process with an isolated, no-bytecode interpreter.  This removes
    # the wrapper/script directory and repository root from import search so a
    # repository-local ``json.py``/``ctypes.py`` cannot shadow the stdlib.
    argv = [sys.executable, "-I", "-B", _canonical_script(), *sys.argv[1:]]
    raise SystemExit(os.spawnv(os.P_WAIT, sys.executable, argv))
