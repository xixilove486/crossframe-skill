from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]


BASE_COMMIT = "e2e0965"
PRESERVATION_PATH = ROOT / "tests/fixtures/promax-preservation.json"
SUITE_ROUTE_PATHS = (
    ROOT / "skills/crossframe-suite/SKILL.md",
    ROOT / "skills/crossframe-suite/protocols/suite-dispatch-protocol.md",
    ROOT / "skills/crossframe-suite/references/workflow-routing-map.md",
)
EXPECTED_CROSSFRAME_SKILLS = {
    "crossframe",
    "crossframe-casebook",
    "crossframe-critical",
    "crossframe-debate",
    "crossframe-dialogue",
    "crossframe-essay",
    "crossframe-history",
    "crossframe-inquiry",
    "crossframe-max",
    "crossframe-notebook",
    "crossframe-org",
    "crossframe-promax",
    "crossframe-public",
    "crossframe-review",
    "crossframe-suite",
    "crossframe-teach",
    "crossframe-ultra",
}
ROUTING_BEGIN = "<!-- PROMAX-ROUTING-BEGIN -->"
ROUTING_END = "<!-- PROMAX-ROUTING-END -->"
ROUTING_REQUIRED_MARKERS = (
    "PROMAX-NAMED-ONLY",
    "PROMAX-PRIORITY-OVER-MAX",
    "PROMAX-NO-FALLBACK-TO-MAX",
    "PROMAX-GENERIC-MAX-STAYS-MAX",
)
ROUTING_TARGET_MATRIX = {
    "exact-promax": "PROMAX-ROUTE-EXACT-PROMAX-TO-PROMAX",
    "both-names": "PROMAX-ROUTE-BOTH-NAMES-TO-PROMAX",
    "max-only": "PROMAX-ROUTE-MAX-ONLY-TO-MAX",
    "generic-max": "PROMAX-GENERIC-MAX-STAYS-MAX",
    "near-miss": "PROMAX-ROUTE-NEAR-MISS-NO-MATCH",
}
EXACT_PROMAX_FORMS = (
    "crossframe-promax",
    "CrossFrame ProMax",
    "$crossframe-promax",
    "/crossframe-promax",
)
PROMAX_NEAR_MISSES = (
    "ProMax",
    "crossframe pro max",
    "crossframe-promaxx",
    "crossframe-pro",
)
FORBIDDEN_FALLBACK_PATTERNS = (
    r"(?i)(?<!not )(?<!n't )\ballow(?:s|ed|ing)?\b.{0,40}\b(?:fallback|degrad(?:e|ation))\b",
    r"(?i)\b(?:fallback|degrad(?:e|ation))\b.{0,40}(?<!not )(?<!n't )\ballow(?:s|ed|ing)?\b",
    r"(?<!不)(?:允许|可以|可).{0,24}(?:自动)?.{0,8}(?:退回|回退|降级)",
)
FORBIDDEN_FALLBACK_MARKERS = (
    "PROMAX-FALLBACK-ALLOWED",
    "PROMAX-AUTOMATIC-FALLBACK-TO-MAX",
    "PROMAX-AUTO-DEGRADE-TO-MAX",
)


def run_git(*args: str, allowed_codes: tuple[int, ...] = (0,)) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise AssertionError(f"unable to execute git {' '.join(args)}: {error}") from error
    if result.returncode not in allowed_codes:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise AssertionError(
            f"git {' '.join(args)} failed with exit code {result.returncode}: "
            f"{stderr or '<no stderr>'}"
        )
    return result.stdout


def commit_tree_entries(commit: str) -> dict[str, tuple[str, str]]:
    raw = run_git("ls-tree", "-r", "-z", commit)
    entries: dict[str, tuple[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, path_bytes = record.split(b"\t", 1)
            mode_bytes, object_type, object_id = metadata.split(b" ", 2)
            path = path_bytes.decode("utf-8")
            mode = mode_bytes.decode("ascii")
            blob_id = object_id.decode("ascii")
        except (UnicodeDecodeError, ValueError) as error:
            raise AssertionError(
                f"could not parse git ls-tree record for {commit}: {record!r}"
            ) from error
        if object_type != b"blob":
            raise AssertionError(
                f"protected base tree entry is not a blob: {path} ({object_type!r})"
            )
        if path in entries:
            raise AssertionError(f"duplicate path in git ls-tree output: {path}")
        entries[path] = (mode, blob_id)
    if not entries:
        raise AssertionError(f"git ls-tree returned no blobs for commit {commit}")
    return entries


def protected_surface_name(repo_path: str) -> str | None:
    lower = repo_path.lower()
    if "promax" in lower:
        return None
    if repo_path.startswith("skills/crossframe-max/"):
        return "skills_crossframe_max"
    if repo_path.startswith(".claude/skills/crossframe-max/"):
        return "claude_skills_crossframe_max"
    if repo_path == ".claude/commands/crossframe-max.md":
        return "claude_command_crossframe_max"
    pure_path = PurePosixPath(repo_path)
    if pure_path.parent == PurePosixPath("scripts") and "max" in pure_path.name.lower():
        return "root_max_scripts_excluding_promax"
    if re.fullmatch(r"tests/test_max_[^/]*\.py", repo_path):
        return "max_contract_tests"
    return None


def protected_commit_surfaces(
    entries: dict[str, tuple[str, str]],
) -> dict[str, list[str]]:
    surfaces = {
        "skills_crossframe_max": [],
        "claude_skills_crossframe_max": [],
        "claude_command_crossframe_max": [],
        "root_max_scripts_excluding_promax": [],
        "max_contract_tests": [],
    }
    for repo_path in entries:
        name = protected_surface_name(repo_path)
        if name is not None:
            surfaces[name].append(repo_path)
    for paths in surfaces.values():
        paths.sort()
    return surfaces


def current_protected_surfaces() -> dict[str, set[str]]:
    surfaces = {
        "skills_crossframe_max": set(),
        "claude_skills_crossframe_max": set(),
        "claude_command_crossframe_max": set(),
        "root_max_scripts_excluding_promax": set(),
        "max_contract_tests": set(),
    }
    raw = run_git("ls-files", "-z")
    for path_bytes in raw.split(b"\0"):
        if not path_bytes:
            continue
        try:
            repo_path = path_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise AssertionError(f"could not decode tracked Git path: {path_bytes!r}") from error
        name = protected_surface_name(repo_path)
        if name is not None:
            surfaces[name].add(repo_path)
    return surfaces


def commit_surface_hash(
    commit: str,
    entries: dict[str, tuple[str, str]],
    paths: list[str],
) -> str:
    digest = hashlib.sha256()
    for repo_path in paths:
        mode, _blob_id = entries[repo_path]
        blob = run_git("show", f"{commit}:{repo_path}")
        digest.update(repo_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(mode.encode("ascii"))
        digest.update(b"\0")
        digest.update(blob)
        digest.update(b"\0")
    return digest.hexdigest()


def assert_tracked_surface_clean(test: unittest.TestCase, paths: list[str]) -> None:
    if not paths:
        raise AssertionError("protected Git surface unexpectedly has no base paths")
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", *paths],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise AssertionError(f"unable to execute git diff --quiet: {error}") from error
    if result.returncode == 0:
        return
    if result.returncode > 1:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise AssertionError(
            f"git diff --quiet failed with exit code {result.returncode}: "
            f"{stderr or '<no stderr>'}"
        )
    changed = run_git("diff", "--name-status", "HEAD", "--", *paths).decode(
        "utf-8", errors="replace"
    )
    test.fail(f"protected tracked paths differ from HEAD:\n{changed.strip()}")


def untracked_protected_paths() -> dict[str, set[str]]:
    surfaces: dict[str, set[str]] = {}
    raw = run_git("ls-files", "--others", "--exclude-standard", "-z")
    for path_bytes in raw.split(b"\0"):
        if not path_bytes:
            continue
        try:
            repo_path = path_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise AssertionError(f"could not decode untracked Git path: {path_bytes!r}") from error
        name = protected_surface_name(repo_path)
        if name is not None:
            surfaces.setdefault(name, set()).add(repo_path)
    return surfaces


def workflow_job_blocks(text: str) -> dict[str, str]:
    jobs_markers = list(re.finditer(r"(?m)^jobs:[ \t]*\r?$", text))
    if len(jobs_markers) != 1:
        raise AssertionError(
            f"workflow must contain exactly one unindented jobs mapping; found {len(jobs_markers)}"
        )
    payload_start = jobs_markers[0].end()
    if text[payload_start : payload_start + 2] == "\r\n":
        payload_start += 2
    elif text[payload_start : payload_start + 1] == "\n":
        payload_start += 1
    else:
        raise AssertionError("workflow jobs mapping is not followed by a line ending")
    jobs_text = text[payload_start:]
    matches = list(re.finditer(r"(?m)^  ([a-z0-9][a-z0-9-]*):[ \t]*(?:\r?\n|$)", jobs_text))
    if not matches:
        raise AssertionError("workflow jobs mapping contains no sliceable two-space job headers")
    job_ids = [match.group(1) for match in matches]
    duplicates = sorted({job_id for job_id in job_ids if job_ids.count(job_id) > 1})
    if duplicates:
        raise AssertionError(f"workflow contains duplicate job headers: {', '.join(duplicates)}")
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(jobs_text)
        if end <= match.start():
            raise AssertionError(f"workflow job cannot be sliced: {match.group(1)}")
        block = jobs_text[match.start() : end]
        if not block.startswith(f"  {match.group(1)}:"):
            raise AssertionError(f"workflow job slice has the wrong header: {match.group(1)}")
        blocks[match.group(1)] = block
    return blocks


def assert_frozen_workflow_job(
    test: unittest.TestCase,
    text: str,
    job: dict[str, object],
    source: str,
) -> str:
    blocks = workflow_job_blocks(text)
    job_id = str(job["job_id"])
    test.assertIn(job_id, blocks, f"{source} workflow job is missing: {job_id}")
    actual = blocks[job_id]
    test.assertEqual(actual, job["raw_text"], f"{source} Max workflow job text changed")
    test.assertEqual(
        hashlib.sha256(actual.encode("utf-8")).hexdigest(),
        job["sha256"],
        f"{source} Max workflow job hash changed",
    )
    return actual


def routing_block(test: unittest.TestCase, text: str, path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    test.assertEqual(
        text.count(ROUTING_BEGIN),
        1,
        f"{relative} must contain exactly one {ROUTING_BEGIN} marker",
    )
    test.assertEqual(
        text.count(ROUTING_END),
        1,
        f"{relative} must contain exactly one {ROUTING_END} marker",
    )
    start = text.find(ROUTING_BEGIN) + len(ROUTING_BEGIN)
    end = text.find(ROUTING_END)
    test.assertLess(start, end, f"{relative} has reversed ProMax routing markers")
    block = text[start:end]
    test.assertTrue(block.strip(), f"{relative} has an empty ProMax routing block")
    return block


class ProMaxPreservationTests(unittest.TestCase):
    def test_all_max_surfaces_match_frozen_git_trees(self) -> None:
        manifest = json.loads(PRESERVATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["base_commit"], BASE_COMMIT)
        self.assertEqual(
            manifest["tree_hash_algorithm"],
            "SHA-256 over each base-commit blob in repository-relative POSIX path order: "
            "path_utf8 + NUL + git_mode_ascii + NUL + git_show_blob_bytes + NUL",
        )
        entries = commit_tree_entries("HEAD")
        committed_surfaces = protected_commit_surfaces(entries)
        current_surfaces = current_protected_surfaces()
        self.assertEqual(set(committed_surfaces), set(manifest["surfaces"]))
        self.assertEqual(set(current_surfaces), set(manifest["surfaces"]))

        untracked = untracked_protected_paths()
        self.assertEqual(untracked, {}, f"untracked files added to protected Max surfaces: {untracked}")
        for name, committed_paths in committed_surfaces.items():
            expected = manifest["surfaces"][name]
            with self.subTest(surface=name):
                self.assertEqual(set(committed_paths), current_surfaces[name])
                self.assertEqual(len(committed_paths), expected["file_count"])
                self.assertEqual(
                    commit_surface_hash("HEAD", entries, committed_paths),
                    expected["tree_sha256"],
                )
                assert_tracked_surface_clean(self, committed_paths)

    def test_max_workflow_job_matches_frozen_raw_text_and_hash(self) -> None:
        with self.assertRaisesRegex(AssertionError, "exactly one unindented jobs mapping"):
            workflow_job_blocks("name: no-jobs\n")
        with self.assertRaisesRegex(AssertionError, "no sliceable two-space job headers"):
            workflow_job_blocks("jobs:\n  # no job headers\n")
        with self.assertRaisesRegex(AssertionError, "duplicate job headers: build"):
            workflow_job_blocks("jobs:\n  build:\n  build:\n")

        manifest = json.loads(PRESERVATION_PATH.read_text(encoding="utf-8"))
        job = manifest["workflow_job"]
        workflow_path = ROOT / job["workflow_path"]
        self.assertTrue(workflow_path.is_file(), workflow_path.as_posix())
        try:
            current_text = workflow_path.read_text(encoding="utf-8")
        except OSError as error:
            raise AssertionError(
                f"could not read current workflow: {workflow_path.as_posix()}: {error}"
            ) from error
        except UnicodeDecodeError as error:
            raise AssertionError(
                f"workflow is not valid UTF-8: {workflow_path.as_posix()}"
            ) from error
        current_job = assert_frozen_workflow_job(
            self,
            current_text,
            job,
            "current worktree",
        )
        self.assertEqual(current_job, job["raw_text"])


class ProMaxRepositoryTargetTests(unittest.TestCase):
    def test_crossframe_skill_inventory_matches_frozen_seventeen_entries(self) -> None:
        skills = {
            path.name
            for path in (ROOT / "skills").iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(skills, EXPECTED_CROSSFRAME_SKILLS)

    def test_promax_canonical_skill_exists(self) -> None:
        path = ROOT / "skills/crossframe-promax/SKILL.md"
        self.assertTrue(path.is_file(), path.as_posix())

    def test_promax_claude_command_exists(self) -> None:
        path = ROOT / ".claude/commands/crossframe-promax.md"
        self.assertTrue(path.is_file(), path.as_posix())

    def test_promax_claude_command_is_a_thin_no_fallback_entry(self) -> None:
        path = ROOT / ".claude/commands/crossframe-promax.md"
        text = path.read_text(encoding="utf-8")
        self.assertLess(len(text), 2400)
        self.assertIn("skills/crossframe-promax/SKILL.md", text)
        self.assertIn("$ARGUMENTS", text)
        for marker in ROUTING_REQUIRED_MARKERS[:3]:
            self.assertIn(marker, text)
        self.assertNotIn("skills/crossframe-max/", text)
        self.assertNotIn("crossframe-review", text)
        for marker in FORBIDDEN_FALLBACK_MARKERS:
            self.assertNotIn(marker, text)
        for pattern in FORBIDDEN_FALLBACK_PATTERNS:
            self.assertNotRegex(text, pattern)

    def test_suite_has_one_complete_promax_routing_contract_per_file(self) -> None:
        for path in SUITE_ROUTE_PATHS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                block = routing_block(self, text, path)
                for marker in ROUTING_REQUIRED_MARKERS:
                    self.assertIn(marker, block, f"missing {marker}")
                for case, marker in ROUTING_TARGET_MATRIX.items():
                    self.assertIn(marker, block, f"routing matrix case {case} is missing")
                for marker in FORBIDDEN_FALLBACK_MARKERS:
                    self.assertNotIn(marker, block)
                for pattern in FORBIDDEN_FALLBACK_PATTERNS:
                    self.assertNotRegex(block, pattern)
                for exact_form in EXACT_PROMAX_FORMS:
                    self.assertIn(f"`{exact_form}`", block)
                for near_miss in PROMAX_NEAR_MISSES:
                    self.assertIn(f"`{near_miss}`", block)

    def test_promax_runtime_does_not_reimplement_suite_activation(self) -> None:
        runtime_cli = (
            ROOT / "skills/crossframe-promax/scripts/crossframe_promax_runtime.py"
        ).read_text(encoding="utf-8")
        pollution = (
            ROOT / "skills/crossframe-promax/scripts/promax_runtime/pollution.py"
        ).read_text(encoding="utf-8")
        artifacts = (
            ROOT / "skills/crossframe-promax/scripts/promax_runtime/artifacts.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn('add_parser("route"', runtime_cli)
        self.assertNotIn("resolve_explicit_route", runtime_cli)
        self.assertNotIn("resolve_explicit_route", pollution)
        self.assertNotIn("ExplicitRouteError", pollution)
        self.assertIn("platform_selected_promax_route()", artifacts)

    def test_suite_smoke_and_openai_adapter_cover_promax_priority(self) -> None:
        for relative in (
            "skills/crossframe-suite/evals/crossframe-suite-smoke-tests.md",
            "skills/crossframe-suite/agents/openai.yaml",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                for marker in ROUTING_REQUIRED_MARKERS:
                    self.assertIn(marker, text)
                self.assertIn("skills/crossframe-promax/SKILL.md", text)
                for marker in FORBIDDEN_FALLBACK_MARKERS:
                    self.assertNotIn(marker, text)
                for pattern in FORBIDDEN_FALLBACK_PATTERNS:
                    self.assertNotRegex(text, pattern)

    def test_generic_maximum_requests_still_route_to_max(self) -> None:
        text = (ROOT / "skills/crossframe-suite/SKILL.md").read_text(encoding="utf-8")
        matching_lines = [line for line in text.splitlines() if "最大算力" in line]
        self.assertTrue(matching_lines)
        self.assertTrue(
            any("crossframe-max" in line and "crossframe-promax" not in line for line in matching_lines)
        )

    def test_named_max_still_identifies_the_existing_max_skill(self) -> None:
        text = (ROOT / "skills/crossframe-max/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: crossframe-max", text)
        for form in ("crossframe-max", "$crossframe-max", "/crossframe-max"):
            self.assertIn(form, text)


if __name__ == "__main__":
    unittest.main()
