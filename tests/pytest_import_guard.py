from __future__ import annotations

import unittest


try:
    import pytest
except ModuleNotFoundError as error:
    if error.name == "pytest":
        raise unittest.SkipTest("pytest is unavailable") from error
    raise
