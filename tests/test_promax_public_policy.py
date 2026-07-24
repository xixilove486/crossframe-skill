from __future__ import annotations

import unittest

from scripts import check_crossframe_skill_integrity as integrity


VALID_POLICY = (
    "ProMax 是 v8-only 的 exact-name only 独立 skill："
    "仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、"
    "`$crossframe-promax` 或 `/crossframe-promax` 时读取 "
    "`skills/crossframe-promax/SKILL.md`。"
    "Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；"
    "suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。"
)


class ProMaxPublicPolicyTests(unittest.TestCase):
    def assert_rejected(self, text: str, expected: str) -> None:
        with self.assertRaisesRegex(SystemExit, expected):
            integrity.check_promax_policy_text(text, "adapter.md", "test")

    def test_complete_policy_passes(self) -> None:
        integrity.check_promax_policy_text(VALID_POLICY, "adapter.md", "test")

    def test_each_exact_trigger_name_is_required(self) -> None:
        for trigger in integrity.PROMAX_EXACT_TRIGGER_NAMES:
            with self.subTest(trigger=trigger):
                self.assert_rejected(
                    VALID_POLICY.replace(f"`{trigger}`", "`removed-trigger`"),
                    "exact trigger",
                )

    def test_fallback_permission_is_rejected(self) -> None:
        self.assert_rejected(
            VALID_POLICY.replace("不得降级回 Max", "允许降级回 Max"),
            "no fallback",
        )

    def test_contradictory_fallback_permission_is_rejected_even_with_no_fallback_marker(self) -> None:
        self.assert_rejected(
            VALID_POLICY + " 同时允许降级回 Max。",
            "contradictory fallback",
        )

    def test_a_fifth_code_literal_trigger_name_is_rejected(self) -> None:
        self.assert_rejected(
            VALID_POLICY + " 此外，`ProMax` 也会触发。",
            "unapproved trigger",
        )

    def test_generated_claude_mirror_is_not_a_canonical_link(self) -> None:
        self.assert_rejected(
            VALID_POLICY.replace(
                "`skills/crossframe-promax/SKILL.md`",
                "`.claude/skills/crossframe-promax/SKILL.md`",
            ),
            "canonical skill",
        )


if __name__ == "__main__":
    unittest.main()
