from __future__ import annotations

import builtins
import importlib.util
from pathlib import Path
from types import ModuleType
import unittest
from unittest import mock


TESTS_ROOT = Path(__file__).resolve().parent
GUARD_CASES = (
    ("pytest", TESTS_ROOT / "pytest_import_guard.py"),
    ("yaml", TESTS_ROOT / "yaml_import_guard.py"),
)


class OptionalDependencyGuardTests(unittest.TestCase):
    def _load_guard(
        self,
        dependency: str,
        guard_path: Path,
        import_result: ModuleType | ModuleNotFoundError,
    ) -> ModuleType:
        self.assertTrue(guard_path.is_file(), f"missing dependency guard: {guard_path.name}")
        spec = importlib.util.spec_from_file_location(
            f"dependency_guard_test_{dependency}", guard_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        original_import = builtins.__import__

        def controlled_import(
            name: str,
            globals: dict[str, object] | None = None,
            locals: dict[str, object] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ):
            if level == 0 and name == dependency:
                if isinstance(import_result, ModuleNotFoundError):
                    raise import_result
                return import_result
            return original_import(name, globals, locals, fromlist, level)

        with mock.patch.object(builtins, "__import__", side_effect=controlled_import):
            spec.loader.exec_module(module)
        return module

    def test_exports_dependency_module_when_import_succeeds(self) -> None:
        for dependency, guard_path in GUARD_CASES:
            with self.subTest(dependency=dependency):
                dependency_module = ModuleType(dependency)
                guard = self._load_guard(dependency, guard_path, dependency_module)
                self.assertIs(getattr(guard, dependency), dependency_module)

    def test_skips_only_when_top_level_dependency_is_missing(self) -> None:
        for dependency, guard_path in GUARD_CASES:
            with self.subTest(dependency=dependency):
                missing = ModuleNotFoundError(
                    f"No module named '{dependency}'", name=dependency
                )
                with self.assertRaises(unittest.SkipTest) as raised:
                    self._load_guard(dependency, guard_path, missing)
                self.assertIs(raised.exception.__cause__, missing)

    def test_propagates_transitive_module_not_found_error_unchanged(self) -> None:
        for dependency, guard_path in GUARD_CASES:
            with self.subTest(dependency=dependency):
                missing = ModuleNotFoundError(
                    "No module named 'transitive_dependency'",
                    name="transitive_dependency",
                )
                with self.assertRaises(ModuleNotFoundError) as raised:
                    self._load_guard(dependency, guard_path, missing)
                self.assertIs(raised.exception, missing)


if __name__ == "__main__":
    unittest.main()
