---
trigger: model_decision
description: Use CrossFrame for Chinese cross-scale structural diagnosis, inference, open assertions, anti-capture checks, strong judgment, low-condition actions, public institutions, history research, long-term evolution, and concept explanation.
---

# CrossFrame Rule

Use this rule when the user asks for CrossFrame、跨尺度结构诊断、结构诊断、推演、开放断言、反俘获审查、低条件试探行动、强判断、高反身性、亲密关系、疗愈转移、公共制度、长期演化、概念解释，或复杂关系/团队/组织/制度/公共争议分析。

For complex tasks that require multiple CrossFrame sibling skills in sequence, use `skills/crossframe-suite/SKILL.md` first and follow `skills/crossframe-suite/references/workflow-routing-map.md`. Do not trigger all sibling skills at once.

Use `crossframe-suite` as the default CrossFrame entry. For any CrossFrame content task through Suite, finish the needed sibling skills first, then append `crossframe-essay -> crossframe-review` and use `full-visible-v5-longform`: complete visible structural dossier plus complete long-form Chinese article. Only skip the article layer when the user explicitly says only/no article/short answer/table/checklist/pure diagnosis/action plan only.

For 中文文章、长文、评论、思想文章、批判性洞察文章 or structure-to-essay writing, use `skills/crossframe-essay/SKILL.md` first, then read `skills/crossframe/SKILL.md` and `skills/crossframe/references/read-routing-map.md`. Output `结构洞察底稿` before `文章正文`. If concept elevation, theory, classics, or allusion are needed, read `skills/crossframe-essay/protocols/concept-elevation-protocol.md` and keep references verifiable and tied back to reality. If the user asks for 亲切、编辑、同志口吻、报刊答复 or advice, read `skills/crossframe-essay/protocols/editorial-comrade-voice-protocol.md`; use a modern editor voice, not retro slogans or personality judgment.

For review, dialogue, casebook, history research, post-completion inquiry, public issue, organization repair, concept teaching, debate, or notebook tasks, use the matching `skills/crossframe-*/SKILL.md` sibling skill before falling back to the generic CrossFrame rule. Follow-up questions, counterexamples, missing evidence, transfer conditions, or action-boundary checks after a completed workflow should use `skills/crossframe-inquiry/SKILL.md`.

For `crossframe-max`, maximum CrossFrame mode, exhaustive structural projection, full-scale world-model interpretation, or no word-limit complete explanation, read `skills/crossframe-max/SKILL.md`. This is an independent named-only mode; do not route it through the suite `2+1` selector or ordinary article-type selector.

CrossFrame ProMax is a v8-only, exact-name only independent skill. Read `skills/crossframe-promax/SKILL.md` only for `crossframe-promax`, `CrossFrame ProMax`, `$crossframe-promax`, or `/crossframe-promax`. If both Max and ProMax are named, ProMax wins; generic maximality remains Max; suite never auto-upgrades; ProMax uses its own audit with no review chain and never falls back to Max.

After a completed suite workflow has produced diagnosis, article, and review, any substantive follow-up without an explicit new-task/exit or pure acknowledgment/thanks signal should use `skills/crossframe-inquiry/SKILL.md` by default. Pure acknowledgments or endings such as "谢谢", "好的", "明白了", or "先这样" should only close lightly. The inquiry layer may retrieve 1-3 relevant sibling skills for question design, counterexamples, transfer conditions, and risk boundaries, but it must not output formal sibling judgments.

Read order:

1. `skills/crossframe/SKILL.md`
2. `skills/crossframe/references/read-routing-map.md`
3. The routed protocol, worksheet, concept card, and template
4. `skills/crossframe/templates/reasoning-outline-output.md`
5. `skills/crossframe/templates/user-facing-language.md`

Output a short 推理提纲 first, then a readable Chinese answer. Do not use concept names as conclusions. If a high-risk concept carries the judgment, read the matching card under `skills/crossframe/references/concept-cards/` and use `skills/crossframe/references/runtime-read-policy.md` and `skills/crossframe/references/continuity-closure-map.md` as the concept fidelity and source-continuity check.

Never turn CrossFrame into personality judgment, fate prediction, responsibility dilution, professional replacement, or AI compliance theater.

For philosophical/meaning questions such as 第一因, 生命是什么, 虚无主义, or 存在意义, first use concept explanation, scale decomposition, and a structural open assertion. Fall back to framework boundary only when no structural question can be formed.
