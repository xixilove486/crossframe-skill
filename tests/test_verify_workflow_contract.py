from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/verify.yml"
EXPECTED_JOBS = {
    "repository-integrity": "check_crossframe_skill_integrity.py --repo .",
    "max-contracts-and-artifacts": "unittest discover -s tests",
    "promax-contracts-and-artifacts": "check_crossframe_promax_v8_knowledge.py --repo .",
    "schemas-and-fixtures": "validate_crossframe_max_repair_fixtures.py",
    "mirrors-and-package": "sync_skill_mirrors.py --check",
}


def job_blocks(text: str) -> dict[str, str]:
    jobs_text = text.split("\njobs:\n", 1)[1]
    matches = list(re.finditer(r"(?m)^  ([a-z0-9-]+):\s*$", jobs_text))
    return {
        match.group(1): jobs_text[
            match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(jobs_text)
        ]
        for index, match in enumerate(matches)
    }


class VerifyWorkflowContractTests(unittest.TestCase):
    def test_workflow_has_five_independent_stable_jobs(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        blocks = job_blocks(text)
        for job_id, command in EXPECTED_JOBS.items():
            self.assertIn(job_id, blocks)
            block = blocks[job_id]
            self.assertIn(f"name: {job_id}", block)
            self.assertIn(command, block)
            self.assertNotRegex(block, r"(?m)^\s+needs:")

        promax = blocks["promax-contracts-and-artifacts"]
        for marker in (
            "check_crossframe_promax_v8_full_source.py --repo .",
            "check_crossframe_promax_v8_knowledge.py --repo .",
            "test_promax_repository_integration.py",
            "test_promax_materializer.py",
            "skills/crossframe-promax/schemas",
            "jsonschema",
        ):
            self.assertIn(marker, promax)

        package = blocks["mirrors-and-package"]
        for required_path in (
            ".claude/commands/crossframe-promax.md",
            ".claude/skills/crossframe-promax/SKILL.md",
            "skills/crossframe-promax/SKILL.md",
            "skills/crossframe-promax/references/v8-full-source/00-index.md",
            "skills/crossframe-promax/schemas/promax-run-contract.schema.json",
            "skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py",
            "skills/crossframe-promax/templates/promax-artifact-manifest-output.md",
        ):
            self.assertIn(required_path, package)


if __name__ == "__main__":
    unittest.main()
