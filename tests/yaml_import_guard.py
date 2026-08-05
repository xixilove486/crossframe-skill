from __future__ import annotations

import unittest


try:
    import yaml
except ModuleNotFoundError as error:
    if error.name == "yaml":
        raise unittest.SkipTest("yaml is unavailable") from error
    raise
