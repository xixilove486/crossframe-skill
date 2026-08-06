from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

from scripts.sync_skill_mirrors import CROSSFRAME_SKILLS


ROOT = Path(__file__).resolve().parents[1]
ULTRA = ROOT / "skills/crossframe-ultra"
CLAUDE_COMMAND = ROOT / ".claude/commands/crossframe-ultra.md"

FROZEN_BASE_COMMIT = "e1b422cddefc302255453d372954a1fddbe13669"
FROZEN_MANIFEST_CANONICAL_SHA256 = (
    "4ac83ab579e645d1a7ff82a1c8cf8b3507b6b00dec2dc3e4df8c4effe6295770"
)
APPROVED_GLOBAL_INVENTORY_TEST_PATH = (
    "tests/test_promax_repository_integration.py"
)
APPROVED_GLOBAL_INVENTORY_TEST_GIT_OBJECT_ID = (
    "50a10897a8eb3a829531d4983063598353ff2ef2"
)
APPROVED_GLOBAL_INVENTORY_TEST_BLOB_SHA256 = (
    "64092532aad969bc3dd4b43d17ab7181eab3b7843a3bd502a99362fb0f8a88bb"
)
TREE_HASH_ALGORITHM = (
    'digest.update(repo_path.encode("utf-8")); digest.update(b"\\0"); '
    'digest.update(git_mode.encode("ascii")); digest.update(b"\\0"); '
    'digest.update(git_blob); digest.update(b"\\0")'
)
SURFACE_MATCHERS: tuple[tuple[str, Callable[[str], bool]], ...] = (
    (
        "skills_crossframe_max",
        lambda path: path.startswith("skills/crossframe-max/"),
    ),
    (
        "skills_crossframe_promax",
        lambda path: path.startswith("skills/crossframe-promax/"),
    ),
    (
        "claude_skills_crossframe_max",
        lambda path: path.startswith(".claude/skills/crossframe-max/"),
    ),
    (
        "claude_skills_crossframe_promax",
        lambda path: path.startswith(".claude/skills/crossframe-promax/"),
    ),
    (
        "claude_command_crossframe_max",
        lambda path: path == ".claude/commands/crossframe-max.md",
    ),
    (
        "claude_command_crossframe_promax",
        lambda path: path == ".claude/commands/crossframe-promax.md",
    ),
    (
        "tests_max",
        lambda path: re.fullmatch(r"tests/test_max_[^/]*\.py", path) is not None,
    ),
    (
        "tests_promax",
        lambda path: re.fullmatch(r"tests/test_promax_[^/]*\.py", path) is not None,
    ),
)
PROTECTED_PATHSPECS = (
    "skills/crossframe-max",
    "skills/crossframe-promax",
    ".claude/skills/crossframe-max",
    ".claude/skills/crossframe-promax",
    ".claude/commands/crossframe-max.md",
    ".claude/commands/crossframe-promax.md",
    ":(glob)tests/test_max_*.py",
    ":(glob)tests/test_promax_*.py",
)
FROZEN_WORKFLOW_JOBS = frozenset(
    {"max-contracts-and-artifacts", "promax-contracts-and-artifacts"}
)
TASK12A_BASE_COMMIT = "7e5029a582ffa48ffef56739306e94a20e7e1bf5"
FROZEN_ULTRA_THEORY_PATHS = (
    "skills/crossframe-ultra/references/v8.2-full-source",
    "skills/crossframe-ultra/references/v8.2-route-map.json",
    "skills/crossframe-ultra/references/concept-registry",
    "skills/crossframe-ultra/references/concept-contracts",
    "skills/crossframe-ultra/references/source-manifest.json",
)


def run_git(*args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed with exit code {result.returncode}: "
        f"{result.stderr.decode('utf-8', errors='replace').strip() or '<no stderr>'}"
    )
    return result.stdout


def git_tree_entries(commit: str) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for record in run_git("ls-tree", "-r", "-z", commit).split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode_bytes, object_type, object_id_bytes = metadata.split(b" ", 2)
        if object_type != b"blob":
            continue
        repo_path = path_bytes.decode("utf-8")
        assert repo_path not in entries, f"duplicate Git tree path: {repo_path}"
        entries[repo_path] = (
            mode_bytes.decode("ascii"),
            object_id_bytes.decode("ascii"),
        )
    assert entries, f"Git tree is empty: {commit}"
    return entries


def surface_for_path(repo_path: str) -> str | None:
    matches = [name for name, predicate in SURFACE_MATCHERS if predicate(repo_path)]
    assert len(matches) <= 1, f"protected path matched multiple surfaces: {repo_path}"
    return matches[0] if matches else None


def protected_tree_entries(
    entries: dict[str, tuple[str, str]],
) -> dict[str, tuple[str, str, str]]:
    protected: dict[str, tuple[str, str, str]] = {}
    for repo_path, (git_mode, object_id) in entries.items():
        surface = surface_for_path(repo_path)
        if surface is not None:
            protected[repo_path] = (surface, git_mode, object_id)
    return protected


def read_git_blobs(object_ids: set[str]) -> dict[str, bytes]:
    ordered_ids = sorted(object_ids)
    raw = run_git(
        "cat-file",
        "--batch",
        input_bytes="".join(f"{object_id}\n" for object_id in ordered_ids).encode(
            "ascii"
        ),
    )
    blobs: dict[str, bytes] = {}
    position = 0
    for expected_object_id in ordered_ids:
        header_end = raw.find(b"\n", position)
        assert header_end >= 0, f"missing cat-file header: {expected_object_id}"
        header = raw[position:header_end].split(b" ")
        assert len(header) == 3, f"malformed cat-file header: {raw[position:header_end]!r}"
        object_id_bytes, object_type, size_bytes = header
        object_id = object_id_bytes.decode("ascii")
        assert object_id == expected_object_id
        assert object_type == b"blob", f"protected object is not a blob: {object_id}"
        size = int(size_bytes)
        content_start = header_end + 1
        content_end = content_start + size
        assert raw[content_end : content_end + 1] == b"\n"
        blobs[object_id] = raw[content_start:content_end]
        position = content_end + 1
    assert position == len(raw), "unexpected trailing bytes from git cat-file --batch"
    return blobs


def workflow_job_blocks(workflow: bytes) -> dict[str, bytes]:
    jobs_markers = list(re.finditer(br"(?m)^jobs:[ \t]*(?:\r?\n)", workflow))
    assert len(jobs_markers) == 1, (
        "workflow must contain exactly one unindented jobs mapping; "
        f"found {len(jobs_markers)}"
    )
    payload = workflow[jobs_markers[0].end() :]
    headers = list(
        re.finditer(
            br"(?m)^  ([a-z0-9][a-z0-9-]*):[ \t]*(?:\r?\n|$)", payload
        )
    )
    assert headers, "workflow jobs mapping has no two-space job headers"
    blocks: dict[str, bytes] = {}
    for index, match in enumerate(headers):
        job_id = match.group(1).decode("ascii")
        assert job_id not in blocks, f"duplicate workflow job: {job_id}"
        end = headers[index + 1].start() if index + 1 < len(headers) else len(payload)
        blocks[job_id] = payload[match.start() : end]
    return blocks


def assert_workflow_jobs_match_manifest(manifest: dict[str, object]) -> None:
    jobs = manifest["workflow_jobs"]
    assert isinstance(jobs, dict)
    assert set(jobs) == FROZEN_WORKFLOW_JOBS
    workflow_path = ".github/workflows/verify.yml"
    sources = {
        "FROZEN_BASE_COMMIT": run_git(
            "show", f"{FROZEN_BASE_COMMIT}:{workflow_path}"
        ),
        "HEAD": run_git("show", f"HEAD:{workflow_path}"),
        "worktree": (ROOT / workflow_path).read_bytes().replace(b"\r\n", b"\n"),
    }
    for source_name, workflow in sources.items():
        blocks = workflow_job_blocks(workflow)
        for job_id in sorted(FROZEN_WORKFLOW_JOBS):
            job = jobs[job_id]
            assert isinstance(job, dict)
            assert job["workflow_path"] == workflow_path
            assert job["job_id"] == job_id
            raw_text = job["raw_text"]
            assert isinstance(raw_text, str)
            expected = raw_text.encode("utf-8")
            actual = blocks.get(job_id)
            assert actual is not None, f"{source_name} workflow job is missing: {job_id}"
            assert actual == expected, f"{source_name} workflow job changed: {job_id}"
            assert hashlib.sha256(actual).hexdigest() == job["sha256"]


def assert_protected_tree_hashes_match_manifest(
    protected: dict[str, tuple[str, str, str]],
    blobs: dict[str, bytes],
    manifest: dict[str, object],
    context: str,
    *,
    blob_overrides: dict[str, bytes] | None = None,
) -> None:
    overrides = blob_overrides or {}
    paths_by_surface: dict[str, list[str]] = {
        name: [] for name, _predicate in SURFACE_MATCHERS
    }
    for repo_path in sorted(protected):
        surface, _git_mode, _object_id = protected[repo_path]
        paths_by_surface[surface].append(repo_path)

    expected_surfaces = manifest["surfaces"]
    assert isinstance(expected_surfaces, dict)
    assert set(expected_surfaces) == set(paths_by_surface)
    for surface, paths in paths_by_surface.items():
        digest = hashlib.sha256()
        for repo_path in paths:
            _surface, git_mode, object_id = protected[repo_path]
            blob = overrides.get(repo_path, blobs[object_id])
            digest.update(repo_path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(git_mode.encode("ascii"))
            digest.update(b"\0")
            digest.update(blob)
            digest.update(b"\0")
        assert expected_surfaces[surface] == {
            "file_count": len(paths),
            "tree_sha256": digest.hexdigest(),
        }, f"protected surface changed at {context}: {surface}"

    aggregate = hashlib.sha256()
    for repo_path in sorted(protected):
        _surface, git_mode, object_id = protected[repo_path]
        blob = overrides.get(repo_path, blobs[object_id])
        aggregate.update(repo_path.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(git_mode.encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(blob)
        aggregate.update(b"\0")
    assert manifest["aggregate"] == {
        "file_count": len(protected),
        "tree_sha256": aggregate.hexdigest(),
    }, f"protected aggregate changed at {context}"


def assert_commit_protected_files_match_manifest(
    commit: str,
    manifest: dict[str, object],
) -> None:
    entries = git_tree_entries(commit)
    protected = protected_tree_entries(entries)
    expected_files = manifest["protected_files"]
    assert isinstance(expected_files, dict)
    assert set(protected) == set(expected_files), (
        f"protected path inventory changed at {commit}: "
        f"added={sorted(set(protected) - set(expected_files))}, "
        f"removed={sorted(set(expected_files) - set(protected))}"
    )
    blobs = read_git_blobs({object_id for _surface, _mode, object_id in protected.values()})
    for repo_path in sorted(protected):
        surface, git_mode, object_id = protected[repo_path]
        blob = blobs[object_id]
        assert expected_files[repo_path] == {
            "surface": surface,
            "git_mode": git_mode,
            "blob_sha256": hashlib.sha256(blob).hexdigest(),
        }, f"protected blob changed at {commit}: {repo_path}"
    assert_protected_tree_hashes_match_manifest(
        protected,
        blobs,
        manifest,
        commit,
    )


def assert_head_matches_approved_global_inventory_test_migration(
    manifest: dict[str, object],
) -> None:
    protected = protected_tree_entries(git_tree_entries("HEAD"))
    expected_files = manifest["protected_files"]
    assert isinstance(expected_files, dict)
    assert set(protected) == set(expected_files), (
        "protected path inventory changed at HEAD: "
        f"added={sorted(set(protected) - set(expected_files))}, "
        f"removed={sorted(set(expected_files) - set(protected))}"
    )

    blobs = read_git_blobs({object_id for _surface, _mode, object_id in protected.values()})
    approved_path = APPROVED_GLOBAL_INVENTORY_TEST_PATH
    expected_approved = expected_files[approved_path]
    assert isinstance(expected_approved, dict)
    baseline_protected = protected_tree_entries(
        git_tree_entries(FROZEN_BASE_COMMIT)
    )
    baseline_surface, baseline_mode, baseline_object_id = baseline_protected[
        approved_path
    ]
    baseline_blob = read_git_blobs({baseline_object_id})[baseline_object_id]

    for repo_path in sorted(protected):
        surface, git_mode, object_id = protected[repo_path]
        blob_sha256 = hashlib.sha256(blobs[object_id]).hexdigest()
        if repo_path == approved_path:
            assert surface == expected_approved["surface"]
            assert git_mode == expected_approved["git_mode"]
            assert blob_sha256 in {
                expected_approved["blob_sha256"],
                APPROVED_GLOBAL_INVENTORY_TEST_BLOB_SHA256,
            }, f"unapproved protected blob changed at HEAD: {repo_path}"
            if blob_sha256 == APPROVED_GLOBAL_INVENTORY_TEST_BLOB_SHA256:
                assert object_id == APPROVED_GLOBAL_INVENTORY_TEST_GIT_OBJECT_ID
            else:
                assert (surface, git_mode, object_id) == (
                    baseline_surface,
                    baseline_mode,
                    baseline_object_id,
                )
            continue
        assert expected_files[repo_path] == {
            "surface": surface,
            "git_mode": git_mode,
            "blob_sha256": blob_sha256,
        }, f"protected blob changed at HEAD: {repo_path}"

    dirty = run_git(
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        *PROTECTED_PATHSPECS,
    )
    approved_dirty = f" M {approved_path}\0".encode("utf-8")
    assert dirty in {b"", approved_dirty}, (
        f"unapproved protected worktree change: {dirty!r}"
    )
    if dirty:
        assert run_git("diff", "--summary", "--", approved_path) == b""
        current_blob = (ROOT / approved_path).read_bytes().replace(b"\r\n", b"\n")
        current_object_id = run_git(
            "hash-object",
            f"--path={approved_path}",
            approved_path,
        ).decode("ascii").strip()
    else:
        _surface, _mode, current_object_id = protected[approved_path]
        current_blob = blobs[current_object_id]
    assert current_object_id == APPROVED_GLOBAL_INVENTORY_TEST_GIT_OBJECT_ID
    assert (
        hashlib.sha256(current_blob).hexdigest()
        == APPROVED_GLOBAL_INVENTORY_TEST_BLOB_SHA256
    )

    assert_protected_tree_hashes_match_manifest(
        protected,
        blobs,
        manifest,
        "HEAD normalized for approved global inventory test migration",
        blob_overrides={approved_path: baseline_blob},
    )


def assert_protected_manifest_matches_head(manifest_path: Path) -> None:
    assert manifest_path.is_file(), manifest_path.as_posix()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == FROZEN_MANIFEST_CANONICAL_SHA256
    assert manifest["schema_version"] == 1
    assert manifest["base_commit"] == FROZEN_BASE_COMMIT
    assert manifest["tree_hash_algorithm"] == TREE_HASH_ALGORITHM
    run_git("cat-file", "-e", f"{FROZEN_BASE_COMMIT}^{{commit}}")

    assert_commit_protected_files_match_manifest(FROZEN_BASE_COMMIT, manifest)
    assert_head_matches_approved_global_inventory_test_migration(manifest)
    assert_workflow_jobs_match_manifest(manifest)


def test_preservation_manifest_matches_head_before_ultra_exists():
    assert_protected_manifest_matches_head(
        ROOT / "tests/fixtures/ultra-preservation.json"
    )


def test_ultra_is_separate_and_existing_runtimes_are_unchanged():
    assert (ULTRA / "SKILL.md").is_file()
    assert_protected_manifest_matches_head(ROOT / "tests/fixtures/ultra-preservation.json")


def test_ultra_has_an_explicit_generated_surface():
    assert "crossframe-ultra" in CROSSFRAME_SKILLS
    assert (ROOT / ".claude/commands/crossframe-ultra.md").is_file()


def test_claude_command_is_a_thin_open_world_host_adapter():
    text = CLAUDE_COMMAND.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) < 4_000
    assert "skills/crossframe-ultra/SKILL.md" in text
    assert "$ARGUMENTS" in text
    assert "精确点名" in text
    assert "普通自然语言" in text
    assert "open-world" in text
    assert "pending-action" in text
    assert "真实宿主工具" in text
    assert "不得回退" in text


def test_task12a_does_not_change_framework_source_registry_or_contracts():
    run_git(
        "diff",
        "--exit-code",
        TASK12A_BASE_COMMIT,
        "--",
        *FROZEN_ULTRA_THEORY_PATHS,
    )
