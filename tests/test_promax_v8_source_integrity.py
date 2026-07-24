from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "skills/crossframe-promax/scripts/check_crossframe_promax_v8_full_source.py"
)
CHECKER_LAUNCHER = ROOT / "scripts/check_crossframe_promax_v8_full_source.py"
GENERATOR_PATH = (
    ROOT
    / "skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py"
)
GITATTRIBUTES_PATH = ROOT / ".gitattributes"
REFERENCES = ROOT / "skills/crossframe-promax/references"
MANIFEST_PATH = REFERENCES / "source_manifest.json"
SOURCE_TREE = REFERENCES / "v8-full-source"
REAL_SOURCE = Path(r"E:\世界模型\跨尺度多圈层结构推演框架_v8.0.docx")
SNAPSHOT_SHA256 = "3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c"
TREE_MERKLE_ROOT = "9b804bd8d4de67b0e0cc0ce3fd106aafe5dd7a40e04a11023af627c9fab4ed6b"

EXPECTED_RANGES = [
    {
        "file": "00-source-envelope.md",
        "paragraph_start": "V8-P0001",
        "paragraph_end": "V8-P0333",
        "table_start": "V8-T001",
        "table_end": "V8-T001",
    },
    {
        "file": "01-guide.md",
        "paragraph_start": "V8-P0334",
        "paragraph_end": "V8-P0407",
        "table_start": "V8-T002",
        "table_end": "V8-T003",
    },
    {
        "file": "02-boundary-method.md",
        "paragraph_start": "V8-P0408",
        "paragraph_end": "V8-P0485",
        "table_start": "V8-T004",
        "table_end": "V8-T004",
    },
    {
        "file": "03-universal-grammar.md",
        "paragraph_start": "V8-P0486",
        "paragraph_end": "V8-P0543",
        "table_start": None,
        "table_end": None,
    },
    {
        "file": "04-root-assumptions.md",
        "paragraph_start": "V8-P0544",
        "paragraph_end": "V8-P0806",
        "table_start": "V8-T005",
        "table_end": "V8-T010",
    },
    {
        "file": "05-scale-transformation.md",
        "paragraph_start": "V8-P0807",
        "paragraph_end": "V8-P0995",
        "table_start": "V8-T011",
        "table_end": "V8-T014",
    },
    {
        "file": "06-operation-evolution.md",
        "paragraph_start": "V8-P0996",
        "paragraph_end": "V8-P1072",
        "table_start": "V8-T015",
        "table_end": "V8-T015",
    },
    {
        "file": "07-human-world.md",
        "paragraph_start": "V8-P1073",
        "paragraph_end": "V8-P2243",
        "table_start": "V8-T016",
        "table_end": "V8-T073",
    },
    {
        "file": "08-human-state-prototype.md",
        "paragraph_start": "V8-P2244",
        "paragraph_end": "V8-P2526",
        "table_start": "V8-T074",
        "table_end": "V8-T083",
    },
    {
        "file": "09-actor-state-personality.md",
        "paragraph_start": "V8-P2527",
        "paragraph_end": "V8-P2715",
        "table_start": "V8-T084",
        "table_end": "V8-T089",
    },
    {
        "file": "10-multicircle-joint-state.md",
        "paragraph_start": "V8-P2716",
        "paragraph_end": "V8-P2906",
        "table_start": "V8-T090",
        "table_end": "V8-T095",
    },
    {
        "file": "11-event-dynamic-deduction.md",
        "paragraph_start": "V8-P2907",
        "paragraph_end": "V8-P3095",
        "table_start": "V8-T096",
        "table_end": "V8-T101",
    },
    {
        "file": "12-conditional-forecast-choice.md",
        "paragraph_start": "V8-P3096",
        "paragraph_end": "V8-P3306",
        "table_start": "V8-T102",
        "table_end": "V8-T109",
    },
    {
        "file": "13-interface-tools.md",
        "paragraph_start": "V8-P3307",
        "paragraph_end": "V8-P3558",
        "table_start": "V8-T110",
        "table_end": "V8-T117",
    },
    {
        "file": "14-normative-selection.md",
        "paragraph_start": "V8-P3559",
        "paragraph_end": "V8-P3625",
        "table_start": None,
        "table_end": None,
    },
    {
        "file": "15-intervention-applications.md",
        "paragraph_start": "V8-P3626",
        "paragraph_end": "V8-P3734",
        "table_start": None,
        "table_end": None,
    },
    {
        "file": "16-governance.md",
        "paragraph_start": "V8-P3735",
        "paragraph_end": "V8-P3863",
        "table_start": None,
        "table_end": None,
    },
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_payload(path: Path):
    content = path.read_text(encoding="utf-8")
    marker = "## Canonical Structure\n\n```json\n"
    payload_text = content.split(marker, 1)[1].split("\n```", 1)[0]
    return json.loads(payload_text)


def replace_canonical_payload(path: Path, payload) -> None:
    content = path.read_text(encoding="utf-8")
    marker = "## Canonical Structure\n\n```json\n"
    before, old_payload = content.split(marker, 1)
    _old_json, after = old_payload.split("\n```", 1)
    replacement = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(
        before + marker + replacement + "\n```" + after,
        encoding="utf-8",
        newline="\n",
    )


def refresh_manifest_entry(repo: Path, relative_path: str) -> None:
    references = repo / "skills/crossframe-promax/references"
    manifest_path = references / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(
        item for item in manifest["files"] if item["path"] == relative_path
    )
    artifact = references / relative_path
    entry["sha256"] = sha256_file(artifact)
    entry["size"] = artifact.stat().st_size
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


@contextmanager
def copied_repository():
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory) / "repo"
        references = repo / "skills/crossframe-promax/references"
        references.mkdir(parents=True)
        shutil.copytree(SOURCE_TREE, references / "v8-full-source")
        if MANIFEST_PATH.is_file():
            shutil.copy2(MANIFEST_PATH, references / "source_manifest.json")
        scripts = repo / "skills/crossframe-promax/scripts"
        scripts.mkdir(parents=True)
        shutil.copy2(GENERATOR_PATH, scripts / GENERATOR_PATH.name)
        yield repo


def tree_fingerprint(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class ProMaxV8SourcePresenceTests(unittest.TestCase):
    def test_checker_launchers_and_committed_source_tree_exist(self) -> None:
        self.assertTrue(CHECKER_PATH.is_file(), f"missing checker: {CHECKER_PATH}")
        self.assertTrue(
            CHECKER_LAUNCHER.is_file(), f"missing checker launcher: {CHECKER_LAUNCHER}"
        )
        self.assertTrue(SOURCE_TREE.is_dir(), f"missing source tree: {SOURCE_TREE}")
        self.assertTrue(MANIFEST_PATH.is_file(), f"missing manifest: {MANIFEST_PATH}")

    def test_committed_tree_passes_checker_api_and_cli(self) -> None:
        checker = load_module("promax_v8_source_checker", CHECKER_PATH)
        self.assertEqual(checker.check_repository(ROOT), [])
        completed = subprocess.run(
            [sys.executable, str(CHECKER_LAUNCHER), "--repo", str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


class ProMaxV8ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_is_a_closed_release_contract(self) -> None:
        self.assertEqual(
            set(self.manifest),
            {
                "schema_id",
                "schema_version",
                "framework_version",
                "snapshot_sha256",
                "paragraph_count",
                "non_whitespace_chars",
                "table_count",
                "section_count",
                "generator",
                "source_ranges",
                "files",
            },
        )
        self.assertEqual(
            {
                key: self.manifest[key]
                for key in (
                    "schema_id",
                    "schema_version",
                    "framework_version",
                    "snapshot_sha256",
                    "paragraph_count",
                    "non_whitespace_chars",
                    "table_count",
                    "section_count",
                )
            },
            {
                "schema_id": "crossframe.promax.v8.source-manifest",
                "schema_version": 1,
                "framework_version": "v8.0",
                "snapshot_sha256": SNAPSHOT_SHA256,
                "paragraph_count": 3863,
                "non_whitespace_chars": 155721,
                "table_count": 117,
                "section_count": 16,
            },
        )
        self.assertEqual(set(self.manifest["generator"]), {"version", "sha256"})
        self.assertEqual(self.manifest["generator"]["version"], "1.0.0")
        self.assertEqual(
            self.manifest["generator"]["sha256"], sha256_file(GENERATOR_PATH)
        )

    def test_frozen_tree_merkle_root_is_independent_of_the_manifest(self) -> None:
        checker = load_module("promax_v8_source_checker_merkle", CHECKER_PATH)
        generator = load_module("promax_v8_generator_merkle", GENERATOR_PATH)
        self.assertEqual(len(checker._expected_tree_files()), 138)
        self.assertEqual(len(generator._expected_tree_files()), 138)
        self.assertEqual(checker.EXPECTED_TREE_MERKLE_ROOT, TREE_MERKLE_ROOT)
        self.assertEqual(generator.EXPECTED_TREE_MERKLE_ROOT, TREE_MERKLE_ROOT)
        self.assertEqual(checker.compute_tree_merkle_root(SOURCE_TREE), TREE_MERKLE_ROOT)
        self.assertEqual(generator.compute_tree_merkle_root(SOURCE_TREE), TREE_MERKLE_ROOT)

    def test_manifest_declares_exact_source_and_table_ranges(self) -> None:
        self.assertEqual(self.manifest["source_ranges"], EXPECTED_RANGES)
        for source_range in self.manifest["source_ranges"]:
            self.assertEqual(
                set(source_range),
                {
                    "file",
                    "paragraph_start",
                    "paragraph_end",
                    "table_start",
                    "table_end",
                },
            )

    def test_manifest_file_inventory_matches_committed_tree(self) -> None:
        entries = self.manifest["files"]
        self.assertEqual([entry["path"] for entry in entries], sorted(entry["path"] for entry in entries))
        self.assertEqual(len(entries), 138)
        self.assertTrue(all(set(entry) == {"path", "sha256", "size"} for entry in entries))
        actual_paths = sorted(
            f"v8-full-source/{path.relative_to(SOURCE_TREE).as_posix()}"
            for path in SOURCE_TREE.rglob("*")
            if path.is_file()
        )
        self.assertEqual([entry["path"] for entry in entries], actual_paths)
        for entry in entries:
            path = REFERENCES / entry["path"]
            self.assertEqual(entry["sha256"], sha256_file(path), entry["path"])
            self.assertEqual(entry["size"], path.stat().st_size, entry["path"])

    def test_indexes_have_source_sha_and_real_backlinks(self) -> None:
        index = (SOURCE_TREE / "00-index.md").read_text(encoding="utf-8")
        heading_index = (SOURCE_TREE / "00-heading-index.md").read_text(encoding="utf-8")
        term_index = (SOURCE_TREE / "00-term-index.md").read_text(encoding="utf-8")
        table_index = (SOURCE_TREE / "00-table-index.md").read_text(encoding="utf-8")
        sha_line = f"Source SHA256: `{SNAPSHOT_SHA256}`"
        for content in (index, heading_index, term_index, table_index):
            self.assertEqual(content.count(sha_line), 1)
        for source_range in EXPECTED_RANGES:
            self.assertIn(f"]({source_range['file']})", index)
        self.assertIn("## Exact Source Form Locator", term_index)
        self.assertGreater(term_index.count("]("), 16)
        self.assertGreater(heading_index.count("]("), 16)
        for table_number in range(1, 118):
            path = f"tables/V8-T{table_number:03d}.md"
            self.assertIn(f"]({path})", table_index)
        envelope_line = next(
            line
            for line in index.splitlines()
            if "](00-source-envelope.md)" in line
        )
        self.assertIn("V8-T001", envelope_line)


class ProMaxV8CheckerTamperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_module("promax_v8_source_checker_tamper", CHECKER_PATH)

    def assert_has_error(self, errors: list[str], fragment: str) -> None:
        self.assertTrue(
            any(fragment.lower() in error.lower() for error in errors),
            errors,
        )

    def test_missing_and_unexpected_files_are_rejected(self) -> None:
        for label, mutate, fragment in (
            (
                "missing",
                lambda tree: (tree / "16-governance.md").unlink(),
                "missing file",
            ),
            (
                "extra",
                lambda tree: (tree / "unexpected.md").write_text("extra", encoding="utf-8"),
                "unexpected file",
            ),
        ):
            with self.subTest(label=label), copied_repository() as repo:
                mutate(repo / "skills/crossframe-promax/references/v8-full-source")
                errors = self.checker.check_repository(repo)
                self.assert_has_error(errors, fragment)

    def test_deleted_duplicate_and_reordered_anchors_are_rejected(self) -> None:
        cases = (
            (
                "deleted",
                lambda text: text.replace(
                    "<!-- source_paragraph:V8-P0335", "<!-- removed_paragraph:V8-P0335", 1
                ),
            ),
            (
                "duplicate",
                lambda text: text.replace(
                    "<!-- source_paragraph:V8-P0335",
                    "<!-- source_paragraph:V8-P0334",
                    1,
                ),
            ),
            (
                "reordered",
                lambda text: text.replace("V8-P0334", "V8-PXXXX", 1)
                .replace("V8-P0335", "V8-P0334", 1)
                .replace("V8-PXXXX", "V8-P0335", 1),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label), copied_repository() as repo:
                source_file = (
                    repo
                    / "skills/crossframe-promax/references/v8-full-source/01-guide.md"
                )
                content = source_file.read_text(encoding="utf-8")
                source_file.write_text(mutate(content), encoding="utf-8", newline="\n")
                errors = self.checker.check_repository(repo)
                self.assert_has_error(errors, "anchor")

    def test_same_count_character_change_is_rejected(self) -> None:
        with copied_repository() as repo:
            source_file = (
                repo
                / "skills/crossframe-promax/references/v8-full-source/01-guide.md"
            )
            content = source_file.read_text(encoding="utf-8")
            changed = content.replace("第一部分", "第壹部分", 1)
            self.assertEqual(len(changed), len(content))
            source_file.write_text(changed, encoding="utf-8", newline="\n")
            errors = self.checker.check_repository(repo)
        self.assert_has_error(errors, "hash mismatch")

    def test_table_cell_character_change_is_rejected(self) -> None:
        with copied_repository() as repo:
            table_file = (
                repo
                / "skills/crossframe-promax/references/v8-full-source/tables/V8-T001.md"
            )
            content = table_file.read_text(encoding="utf-8")
            changed = content.replace("阅读区段", "阅览区段", 1)
            self.assertEqual(len(changed), len(content))
            table_file.write_text(changed, encoding="utf-8", newline="\n")
            errors = self.checker.check_repository(repo)
        self.assert_has_error(errors, "table prose/JSON")

    def test_table_row_exchange_is_rejected(self) -> None:
        with copied_repository() as repo:
            table_file = (
                repo
                / "skills/crossframe-promax/references/v8-full-source/tables/V8-T001.md"
            )
            payload = canonical_payload(table_file)
            payload["rows"][0], payload["rows"][1] = (
                payload["rows"][1],
                payload["rows"][0],
            )
            replace_canonical_payload(table_file, payload)
            errors = self.checker.check_repository(repo)
        self.assert_has_error(errors, "cell text")

    def test_table_cell_anchor_misalignment_is_rejected(self) -> None:
        with copied_repository() as repo:
            table_file = (
                repo
                / "skills/crossframe-promax/references/v8-full-source/tables/V8-T001.md"
            )
            payload = canonical_payload(table_file)
            payload["cell_paragraph_ids"][0][0][0] = "V8-P0013"
            replace_canonical_payload(table_file, payload)
            errors = self.checker.check_repository(repo)
        self.assert_has_error(errors, "cell anchor")

    def test_section_heading_rename_and_order_exchange_are_rejected(self) -> None:
        for label, mutate in (
            (
                "rename",
                lambda tree: (tree / "01-guide.md").write_text(
                    (tree / "01-guide.md")
                    .read_text(encoding="utf-8")
                    .replace("第一部分　导读", "第一部分　误名"),
                    encoding="utf-8",
                    newline="\n",
                ),
            ),
            (
                "order",
                lambda tree: self._exchange_files(
                    tree / "01-guide.md", tree / "02-boundary-method.md"
                ),
            ),
        ):
            with self.subTest(label=label), copied_repository() as repo:
                tree = repo / "skills/crossframe-promax/references/v8-full-source"
                mutate(tree)
                errors = self.checker.check_repository(repo)
                self.assert_has_error(errors, "section")

    @staticmethod
    def _exchange_files(first: Path, second: Path) -> None:
        first_bytes = first.read_bytes()
        second_bytes = second.read_bytes()
        first.write_bytes(second_bytes)
        second.write_bytes(first_bytes)

    def test_stale_manifest_hash_and_size_are_rejected(self) -> None:
        for field, value, fragment in (
            ("sha256", "0" * 64, "manifest hash mismatch"),
            ("size", -1, "manifest size mismatch"),
        ):
            with self.subTest(field=field), copied_repository() as repo:
                manifest_path = (
                    repo / "skills/crossframe-promax/references/source_manifest.json"
                )
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["files"][0][field] = value
                manifest_path.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                errors = self.checker.check_repository(repo)
                self.assert_has_error(errors, fragment)

    def test_coordinated_tree_and_manifest_tamper_hits_frozen_merkle_root(self) -> None:
        with copied_repository() as repo:
            source_file = (
                repo
                / "skills/crossframe-promax/references/v8-full-source/01-guide.md"
            )
            content = source_file.read_text(encoding="utf-8")
            original = "统一入口"
            replacement = "统壹入口"
            self.assertEqual(content.count(original), 2)
            source_file.write_text(
                content.replace(original, replacement),
                encoding="utf-8",
                newline="\n",
            )
            refresh_manifest_entry(repo, "v8-full-source/01-guide.md")
            errors = self.checker.check_repository(repo)
        self.assert_has_error(errors, "frozen tree Merkle root")

    def test_bom_and_bare_cr_are_rejected_by_the_frozen_tree_root(self) -> None:
        for label, mutate in (
            ("bom", lambda raw: b"\xef\xbb\xbf" + raw),
            ("bare-cr", lambda raw: raw.replace(b"\n", b"\r", 1)),
            ("invalid-utf8", lambda raw: raw + b"\xff"),
        ):
            with self.subTest(label=label), copied_repository() as repo:
                source_file = (
                    repo
                    / "skills/crossframe-promax/references/v8-full-source/"
                    "01-guide.md"
                )
                source_file.write_bytes(mutate(source_file.read_bytes()))
                refresh_manifest_entry(repo, "v8-full-source/01-guide.md")
                errors = self.checker.check_repository(repo)
            self.assert_has_error(errors, "frozen tree Merkle root")

    def test_broken_index_backlink_is_rejected(self) -> None:
        with copied_repository() as repo:
            index = repo / "skills/crossframe-promax/references/v8-full-source/00-index.md"
            content = index.read_text(encoding="utf-8")
            self.assertIn("](01-guide.md)", content)
            index.write_text(
                content.replace("](01-guide.md)", "](missing-guide.md)", 1),
                encoding="utf-8",
                newline="\n",
            )
            errors = self.checker.check_repository(repo)
        self.assert_has_error(errors, "index backlink")


class ProMaxV8CheckoutAndCoordinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_module("promax_v8_source_checker_coordination", CHECKER_PATH)

    def test_protected_release_files_are_forced_to_lf_by_git_attributes(self) -> None:
        content = GITATTRIBUTES_PATH.read_text(encoding="utf-8")
        for rule in (
            "/skills/crossframe-promax/references/v8-full-source/** text eol=lf",
            "/skills/crossframe-promax/references/source_manifest.json text eol=lf",
            "/skills/crossframe-promax/scripts/generate_crossframe_promax_v8_full_source.py text eol=lf",
            "/skills/crossframe-promax/scripts/check_crossframe_promax_v8_full_source.py text eol=lf",
        ):
            self.assertIn(rule, content)
        completed = subprocess.run(
            [
                "git",
                "check-attr",
                "eol",
                "--",
                "skills/crossframe-promax/references/v8-full-source/01-guide.md",
                "skills/crossframe-promax/references/source_manifest.json",
                "skills/crossframe-promax/scripts/"
                "generate_crossframe_promax_v8_full_source.py",
                "skills/crossframe-promax/scripts/"
                "check_crossframe_promax_v8_full_source.py",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        attributes = [line.rsplit(": ", 1)[-1] for line in completed.stdout.splitlines()]
        self.assertEqual(attributes, ["lf"] * 4)

    def test_checker_accepts_crlf_checkout_via_lf_normalized_release_hashes(self) -> None:
        with copied_repository() as repo:
            references = repo / "skills/crossframe-promax/references"
            protected_files = list((references / "v8-full-source").rglob("*.md"))
            protected_files.extend(
                (
                    references / "source_manifest.json",
                    repo
                    / "skills/crossframe-promax/scripts/"
                    "generate_crossframe_promax_v8_full_source.py",
                )
            )
            for path in protected_files:
                lf_bytes = path.read_bytes().replace(b"\r\n", b"\n")
                path.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))
            errors = self.checker.check_repository(repo)
        self.assertEqual(errors, [])

    def test_checker_reports_busy_without_reading_a_mixed_release(self) -> None:
        with copied_repository() as repo:
            references = repo / "skills/crossframe-promax/references"
            live = references / "v8-full-source"
            lock = references / ".v8-full-source.lock"
            script = r'''
import importlib.util
from pathlib import Path
import sys

module_path, lock_path = sys.argv[1:]
spec = importlib.util.spec_from_file_location("promax_lock_holder", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
generation_lock = module._acquire_generation_lock(Path(lock_path))
print("locked", flush=True)
sys.stdin.readline()
module._release_generation_lock(generation_lock)
'''
            process = subprocess.Popen(
                [sys.executable, "-c", script, str(GENERATOR_PATH), str(lock)],
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertIsNotNone(process.stdout)
                self.assertEqual(process.stdout.readline().strip(), "locked")
                os.replace(live, references / ".v8-full-source.backup-active")
                errors = self.checker.check_repository(repo)
            finally:
                if process.poll() is None:
                    if process.stdin is not None:
                        process.stdin.write("release\n")
                        process.stdin.flush()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("generation busy", errors[0].lower())

    def test_checker_uses_an_unlocked_persistent_coordination_file(self) -> None:
        with copied_repository() as repo:
            references = repo / "skills/crossframe-promax/references"
            lock = references / ".v8-full-source.lock"
            lock.write_bytes(b"\x00")
            errors = self.checker.check_repository(repo)
            self.assertEqual(errors, [])
            self.assertTrue(lock.is_file())

    def test_checker_recovers_a_stale_precommit_journal_before_validation(self) -> None:
        with copied_repository() as repo:
            references = repo / "skills/crossframe-promax/references"
            transaction_id = "3" * 32
            live = references / "v8-full-source"
            stage = references / f".v8-full-source.stage-{transaction_id}"
            manifest = references / "source_manifest.json"
            manifest_stage = references / (
                f".source_manifest.json.stage-{transaction_id}"
            )
            shutil.copytree(live, stage)
            shutil.copy2(manifest, manifest_stage)
            returncode = ProMaxV8GenerationSafetyTests.crash_release_after_rename(
                references,
                3,
            )
            self.assertEqual(returncode, 93)

            errors = self.checker.check_repository(repo)
            self.assertEqual(errors, [])
            self.assertFalse(
                (references / ".v8-full-source.transaction.json").exists()
            )


class ProMaxV8SourceComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = load_module("promax_v8_source_checker_source", CHECKER_PATH)

    def test_wrong_source_sha_is_rejected_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "wrong.docx"
            source.write_bytes(b"not the v8 source")
            errors = self.checker.check_repository(ROOT, source)
        self.assertTrue(any("source SHA256 mismatch" in error for error in errors), errors)

    def test_real_source_is_read_once_and_matches_committed_canonical_json(self) -> None:
        if not REAL_SOURCE.is_file():
            self.skipTest(f"real v8 source is unavailable: {REAL_SOURCE}")
        real_read_bytes = Path.read_bytes
        source_reads = 0

        def counted_read_bytes(path):
            nonlocal source_reads
            if Path(path) == REAL_SOURCE:
                source_reads += 1
            return real_read_bytes(path)

        with mock.patch.object(
            Path,
            "read_bytes",
            autospec=True,
            side_effect=counted_read_bytes,
        ):
            errors = self.checker.check_repository(ROOT, REAL_SOURCE)
        self.assertEqual(errors, [])
        self.assertEqual(source_reads, 1)


class ProMaxV8GenerationSafetyTests(unittest.TestCase):
    @staticmethod
    def assert_no_transaction_residue(references: Path) -> None:
        prefixes = (
            ".v8-full-source.stage-",
            ".v8-full-source.backup-",
            ".source_manifest.json.stage-",
            ".source_manifest.json.backup-",
            ".source_manifest.json.tmp-",
            "..v8-full-source.transaction.json.tmp-",
        )
        residue = sorted(
            path.name
            for path in references.iterdir()
            if path.name == ".v8-full-source.transaction.json"
            or path.name.startswith(prefixes)
        )
        if residue:
            raise AssertionError(f"transaction residue remains: {residue}")

    @staticmethod
    def crash_release_after_rename(references: Path, rename_number: int) -> int:
        transaction_id = str(rename_number) * 32
        stage_tree = references / f".v8-full-source.stage-{transaction_id}"
        live_tree = references / "v8-full-source"
        stage_manifest = references / f".source_manifest.json.stage-{transaction_id}"
        live_manifest = references / "source_manifest.json"
        script = r'''
import importlib.util
import os
from pathlib import Path
import sys

module_path, stage_tree, live_tree, stage_manifest, live_manifest, transaction_id, stop = sys.argv[1:]
spec = importlib.util.spec_from_file_location("promax_crash_generator", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
stage_tree = Path(stage_tree)
live_tree = Path(live_tree)
stage_manifest = Path(stage_manifest)
live_manifest = Path(live_manifest)
tree_backup = live_tree.parent / f".{live_tree.name}.backup-{transaction_id}"
manifest_backup = live_manifest.parent / f".{live_manifest.name}.backup-{transaction_id}"
release_targets = {
    tree_backup.resolve(),
    manifest_backup.resolve(),
    live_tree.resolve(),
    live_manifest.resolve(),
}
real_replace = module.os.replace
renames = 0
def crash_after_selected_replace(source, target):
    global renames
    real_replace(source, target)
    if Path(target).resolve() in release_targets:
        renames += 1
        if renames == int(stop):
            os._exit(90 + renames)
module.os.replace = crash_after_selected_replace
module.atomic_replace_release(
    stage_tree,
    live_tree,
    stage_manifest,
    live_manifest,
    transaction_id,
)
'''
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(GENERATOR_PATH),
                str(stage_tree),
                str(live_tree),
                str(stage_manifest),
                str(live_manifest),
                transaction_id,
                str(rename_number),
            ],
            cwd=ROOT,
            check=False,
        )
        return completed.returncode

    def assert_manifest_install_failure_restores_release(
        self,
        old_manifest: bytes | None,
        *,
        old_tree: bool = True,
    ) -> None:
        if not REAL_SOURCE.is_file():
            self.skipTest(f"source DOCX unavailable: {REAL_SOURCE}")

        generator = load_module(
            "promax_v8_generator_transaction_"
            f"{old_tree}_{old_manifest is not None}",
            GENERATOR_PATH,
        )
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            references = repo / "skills/crossframe-promax/references"
            live = references / "v8-full-source"
            manifest_path = references / "source_manifest.json"
            references.mkdir(parents=True)
            sentinel = live / "sentinel.bin"
            sentinel_bytes = b"old live tree\x00\xff"
            before = None
            if old_tree:
                live.mkdir()
                sentinel.write_bytes(sentinel_bytes)
                before = tree_fingerprint(live)
            if old_manifest is not None:
                manifest_path.write_bytes(old_manifest)

            real_replace = os.replace

            def fail_manifest_install(source, target):
                source_name = Path(source).name
                if Path(target) == manifest_path and (
                    source_name.startswith(".source_manifest.json.stage-")
                    or source_name.startswith(".source_manifest.json.tmp-")
                ):
                    raise OSError("injected manifest install failure")
                return real_replace(source, target)

            with mock.patch.object(
                generator.os,
                "replace",
                side_effect=fail_manifest_install,
            ):
                with self.assertRaisesRegex(
                    OSError, "injected manifest install failure"
                ):
                    generator.generate(repo, REAL_SOURCE)

            if old_tree:
                self.assertEqual(tree_fingerprint(live), before)
                self.assertEqual(sentinel.read_bytes(), sentinel_bytes)
            else:
                self.assertFalse(live.exists())
            if old_manifest is None:
                self.assertFalse(manifest_path.exists())
            else:
                self.assertEqual(manifest_path.read_bytes(), old_manifest)
            self.assert_no_transaction_residue(references)

    def test_generation_failure_preserves_the_committed_live_tree(self) -> None:
        generator = load_module("promax_v8_generator_integrity", GENERATOR_PATH)
        with copied_repository() as repo, tempfile.TemporaryDirectory() as directory:
            live = repo / "skills/crossframe-promax/references/v8-full-source"
            before = tree_fingerprint(live)
            wrong_source = Path(directory) / "wrong.docx"
            wrong_source.write_bytes(b"wrong source")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                generator.generate(repo, wrong_source)
            self.assertEqual(tree_fingerprint(live), before)

    def test_manifest_install_failure_restores_old_tree_and_manifest(self) -> None:
        self.assert_manifest_install_failure_restores_release(
            b'{"release":"old"}\r\n'
        )

    def test_manifest_install_failure_without_old_manifest_restores_old_tree(self) -> None:
        self.assert_manifest_install_failure_restores_release(None)

    def test_first_generation_manifest_install_failure_leaves_no_release(self) -> None:
        self.assert_manifest_install_failure_restores_release(
            None,
            old_tree=False,
        )

    def test_manifest_staging_write_failure_preserves_old_release(self) -> None:
        if not REAL_SOURCE.is_file():
            self.skipTest(f"source DOCX unavailable: {REAL_SOURCE}")
        generator = load_module(
            "promax_v8_generator_manifest_staging_failure",
            GENERATOR_PATH,
        )
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            references = repo / "skills/crossframe-promax/references"
            live = references / "v8-full-source"
            manifest_path = references / "source_manifest.json"
            live.mkdir(parents=True)
            sentinel = live / "sentinel.bin"
            sentinel.write_bytes(b"old live tree")
            old_tree = tree_fingerprint(live)
            old_manifest = b'{"release":"old"}\r\n'
            manifest_path.write_bytes(old_manifest)

            def fail_after_partial_stage(stage_path, _manifest):
                Path(stage_path).write_bytes(b'{"partial":')
                raise OSError("injected manifest staging failure")

            with mock.patch.object(
                generator,
                "write_source_manifest_stage",
                side_effect=fail_after_partial_stage,
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "injected manifest staging failure",
                ):
                    generator.generate(repo, REAL_SOURCE)

            self.assertEqual(tree_fingerprint(live), old_tree)
            self.assertEqual(manifest_path.read_bytes(), old_manifest)
            self.assert_no_transaction_residue(references)

    def test_stage_merkle_mismatch_never_installs_the_generated_release(self) -> None:
        if not REAL_SOURCE.is_file():
            self.skipTest(f"source DOCX unavailable: {REAL_SOURCE}")
        generator = load_module(
            "promax_v8_generator_stage_merkle_mismatch",
            GENERATOR_PATH,
        )
        with copied_repository() as repo:
            live = repo / "skills/crossframe-promax/references/v8-full-source"
            before_tree = tree_fingerprint(live)
            manifest_path = live.parent / "source_manifest.json"
            before_manifest = manifest_path.read_bytes()
            real_render = generator.render_v8_source_tree

            def render_then_tamper(snapshot, output_dir):
                real_render(snapshot, output_dir)
                source_file = Path(output_dir) / "01-guide.md"
                content = source_file.read_text(encoding="utf-8")
                source_file.write_text(
                    content.replace("统一入口", "统壹入口"),
                    encoding="utf-8",
                    newline="\n",
                )

            with mock.patch.object(
                generator,
                "render_v8_source_tree",
                side_effect=render_then_tamper,
            ), mock.patch.object(
                generator,
                "validate_generated_v8_tree",
                return_value=[],
            ):
                with self.assertRaisesRegex(ValueError, "frozen tree Merkle root"):
                    generator.generate(repo, REAL_SOURCE)

            self.assertEqual(tree_fingerprint(live), before_tree)
            self.assertEqual(manifest_path.read_bytes(), before_manifest)

    def test_durable_journal_recovers_every_process_crash_boundary(self) -> None:
        generator = load_module(
            "promax_v8_generator_crash_recovery",
            GENERATOR_PATH,
        )
        for rename_number in range(1, 5):
            with self.subTest(rename_number=rename_number), tempfile.TemporaryDirectory() as directory:
                references = Path(directory) / "references"
                transaction_id = str(rename_number) * 32
                stage_tree = references / f".v8-full-source.stage-{transaction_id}"
                live_tree = references / "v8-full-source"
                stage_manifest = references / f".source_manifest.json.stage-{transaction_id}"
                live_manifest = references / "source_manifest.json"
                stage_tree.mkdir(parents=True)
                live_tree.mkdir()
                (stage_tree / "release.txt").write_bytes(b"new tree")
                (live_tree / "release.txt").write_bytes(b"old tree")
                stage_manifest.write_bytes(b'{"release":"new"}\n')
                live_manifest.write_bytes(b'{"release":"old"}\n')

                returncode = self.crash_release_after_rename(
                    references,
                    rename_number,
                )
                self.assertEqual(returncode, 90 + rename_number)
                self.assertTrue(
                    (references / ".v8-full-source.transaction.json").is_file()
                )

                outcome = generator.recover_release_transaction(references)
                expected_release = b"new tree" if rename_number == 4 else b"old tree"
                expected_manifest = (
                    b'{"release":"new"}\n'
                    if rename_number == 4
                    else b'{"release":"old"}\n'
                )
                self.assertIn(outcome, {"committed", "rolled-back"})
                self.assertEqual(
                    (live_tree / "release.txt").read_bytes(),
                    expected_release,
                )
                self.assertEqual(live_manifest.read_bytes(), expected_manifest)
                self.assert_no_transaction_residue(references)

    def test_first_generation_crash_is_either_absent_or_fully_committed(self) -> None:
        generator = load_module(
            "promax_v8_generator_first_release_crash",
            GENERATOR_PATH,
        )
        for rename_number in (1, 2):
            with self.subTest(rename_number=rename_number), tempfile.TemporaryDirectory() as directory:
                references = Path(directory) / "references"
                transaction_id = str(rename_number) * 32
                stage_tree = references / f".v8-full-source.stage-{transaction_id}"
                stage_manifest = references / (
                    f".source_manifest.json.stage-{transaction_id}"
                )
                live_tree = references / "v8-full-source"
                live_manifest = references / "source_manifest.json"
                stage_tree.mkdir(parents=True)
                (stage_tree / "release.txt").write_bytes(b"first tree")
                stage_manifest.write_bytes(b'{"release":"first"}\n')

                returncode = self.crash_release_after_rename(
                    references,
                    rename_number,
                )
                self.assertEqual(returncode, 90 + rename_number)
                outcome = generator.recover_release_transaction(references)
                if rename_number == 1:
                    self.assertEqual(outcome, "rolled-back")
                    self.assertFalse(live_tree.exists())
                    self.assertFalse(live_manifest.exists())
                else:
                    self.assertEqual(outcome, "committed")
                    self.assertEqual(
                        (live_tree / "release.txt").read_bytes(),
                        b"first tree",
                    )
                    self.assertEqual(
                        live_manifest.read_bytes(),
                        b'{"release":"first"}\n',
                    )
                self.assert_no_transaction_residue(references)

    def test_exception_after_manifest_commit_does_not_report_false_failure(self) -> None:
        generator = load_module(
            "promax_v8_generator_post_commit_exception",
            GENERATOR_PATH,
        )
        with tempfile.TemporaryDirectory() as directory:
            references = Path(directory) / "references"
            stage_tree = references / ".v8-full-source.stage-test"
            live_tree = references / "v8-full-source"
            stage_manifest = references / ".source_manifest.json.stage-test"
            live_manifest = references / "source_manifest.json"
            stage_tree.mkdir(parents=True)
            live_tree.mkdir()
            (stage_tree / "release.txt").write_bytes(b"new tree")
            (live_tree / "release.txt").write_bytes(b"old tree")
            stage_manifest.write_bytes(b'{"release":"new"}\n')
            live_manifest.write_bytes(b'{"release":"old"}\n')
            real_replace = os.replace

            def raise_after_commit(source, target):
                real_replace(source, target)
                if Path(source) == stage_manifest and Path(target) == live_manifest:
                    raise OSError("injected exception after manifest commit")

            with mock.patch.object(
                generator.os,
                "replace",
                side_effect=raise_after_commit,
            ):
                generator.atomic_replace_release(
                    stage_tree,
                    live_tree,
                    stage_manifest,
                    live_manifest,
                    "c" * 32,
                )

            self.assertEqual(
                (live_tree / "release.txt").read_bytes(),
                b"new tree",
            )
            self.assertEqual(
                live_manifest.read_bytes(),
                b'{"release":"new"}\n',
            )
            self.assert_no_transaction_residue(references)

    def test_failed_explicit_unlock_is_nonfatal_and_close_releases_lock(self) -> None:
        generator = load_module(
            "promax_v8_generator_lock_release",
            GENERATOR_PATH,
        )
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / ".v8-full-source.lock"
            generation_lock = generator._acquire_generation_lock(lock)
            with mock.patch.object(
                generator,
                "_unlock_generation_lock_file",
                side_effect=OSError("injected explicit unlock failure"),
            ):
                with self.assertWarnsRegex(RuntimeWarning, "unlock failed"):
                    generator._release_generation_lock(generation_lock)

            replacement_lock = generator._acquire_generation_lock(lock)
            generator._release_generation_lock(replacement_lock)
            self.assertTrue(lock.is_file())

    def test_process_exit_automatically_releases_generation_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / ".v8-full-source.lock"
            script = r'''
import importlib.util
import os
from pathlib import Path
import sys

module_path, lock_path = sys.argv[1:]
spec = importlib.util.spec_from_file_location("promax_lock_crash", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module._acquire_generation_lock(Path(lock_path))
os._exit(0)
'''
            completed = subprocess.run(
                [sys.executable, "-c", script, str(GENERATOR_PATH), str(lock)],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)
            generator = load_module(
                "promax_v8_generator_after_lock_crash",
                GENERATOR_PATH,
            )
            generation_lock = generator._acquire_generation_lock(lock)
            generator._release_generation_lock(generation_lock)

    def test_committed_release_survives_backup_cleanup_failure(self) -> None:
        generator = load_module(
            "promax_v8_generator_backup_cleanup",
            GENERATOR_PATH,
        )
        transaction_id = "a" * 32
        for failed_backup_name in (
            f".v8-full-source.backup-{transaction_id}",
            f".source_manifest.json.backup-{transaction_id}",
        ):
            with self.subTest(failed_backup=failed_backup_name):
                with tempfile.TemporaryDirectory() as directory:
                    references = Path(directory) / "references"
                    stage_tree = references / ".v8-full-source.stage-test"
                    live_tree = references / "v8-full-source"
                    stage_manifest = references / ".source_manifest.json.stage-test"
                    live_manifest = references / "source_manifest.json"
                    stage_tree.mkdir(parents=True)
                    live_tree.mkdir()
                    (stage_tree / "new.txt").write_bytes(b"new tree")
                    (live_tree / "old.txt").write_bytes(b"old tree")
                    stage_manifest.write_bytes(b'{"release":"new"}\n')
                    live_manifest.write_bytes(b'{"release":"old"}\n')

                    real_remove_tree = generator._remove_tree

                    def fail_selected_backup(path):
                        if Path(path).name == failed_backup_name:
                            raise OSError("injected backup cleanup failure")
                        return real_remove_tree(path)

                    with mock.patch.object(
                        generator,
                        "_remove_tree",
                        side_effect=fail_selected_backup,
                    ):
                        with self.assertWarnsRegex(
                            RuntimeWarning,
                            "backup cleanup failed",
                        ):
                            generator.atomic_replace_release(
                                stage_tree,
                                live_tree,
                                stage_manifest,
                                live_manifest,
                                transaction_id,
                            )

                    self.assertEqual(
                        (live_tree / "new.txt").read_bytes(),
                        b"new tree",
                    )
                    self.assertFalse((live_tree / "old.txt").exists())
                    self.assertEqual(
                        live_manifest.read_bytes(),
                        b'{"release":"new"}\n',
                    )
                    failed_backup = references / failed_backup_name
                    self.assertTrue(failed_backup.exists())
                    remaining_backups = sorted(
                        path.name
                        for path in references.iterdir()
                        if ".backup-" in path.name
                    )
                    self.assertEqual(remaining_backups, [failed_backup_name])
                    self.assertTrue(
                        (references / ".v8-full-source.transaction.json").is_file()
                    )
                    self.assertFalse(stage_tree.exists())
                    self.assertFalse(stage_manifest.exists())

                    self.assertEqual(
                        generator.recover_release_transaction(references),
                        "committed",
                    )
                    self.assertFalse(failed_backup.exists())
                    self.assert_no_transaction_residue(references)

    def test_warning_as_error_cannot_break_committed_release_cleanup(self) -> None:
        generator = load_module(
            "promax_v8_generator_warning_as_error",
            GENERATOR_PATH,
        )
        transaction_id = "b" * 32
        with tempfile.TemporaryDirectory() as directory:
            references = Path(directory) / "references"
            stage_tree = references / ".v8-full-source.stage-test"
            live_tree = references / "v8-full-source"
            stage_manifest = references / ".source_manifest.json.stage-test"
            live_manifest = references / "source_manifest.json"
            stage_tree.mkdir(parents=True)
            live_tree.mkdir()
            (stage_tree / "new.txt").write_bytes(b"new tree")
            (live_tree / "old.txt").write_bytes(b"old tree")
            stage_manifest.write_bytes(b'{"release":"new"}\n')
            live_manifest.write_bytes(b'{"release":"old"}\n')
            failed_backup = references / (
                f".v8-full-source.backup-{transaction_id}"
            )
            manifest_backup = references / (
                f".source_manifest.json.backup-{transaction_id}"
            )
            real_remove_tree = generator._remove_tree

            def fail_tree_backup(path):
                if Path(path) == failed_backup:
                    raise OSError("injected tree backup cleanup failure")
                return real_remove_tree(path)

            with mock.patch.object(
                generator,
                "_remove_tree",
                side_effect=fail_tree_backup,
            ):
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    generator.atomic_replace_release(
                        stage_tree,
                        live_tree,
                        stage_manifest,
                        live_manifest,
                        transaction_id,
                    )

            self.assertEqual((live_tree / "new.txt").read_bytes(), b"new tree")
            self.assertEqual(
                live_manifest.read_bytes(),
                b'{"release":"new"}\n',
            )
            self.assertTrue(failed_backup.exists())
            self.assertFalse(manifest_backup.exists())


if __name__ == "__main__":
    unittest.main()
