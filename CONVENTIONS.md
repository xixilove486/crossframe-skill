# CrossFrame Agent Conventions

This repository is a publishable AI skill repo. The canonical implementations live in `skills/crossframe-suite/`, `skills/crossframe/`, and `skills/crossframe-essay/`.

CrossFrame skills are explicit-only. Do not trigger this suite passively for ordinary analysis, writing, public commentary, organization repair, reading, debate, or review tasks. Enter CrossFrame only when the user explicitly names CrossFrame, `crossframe-suite`, `crossframe`, a specific `crossframe-*` skill, or a `$crossframe-*` / `/crossframe-*` command.

After explicit invocation, use `crossframe-suite` as the preferred CrossFrame entry for complex tasks that need multiple sibling skills in sequence. Read `skills/crossframe-suite/SKILL.md` first and follow `skills/crossframe-suite/references/workflow-routing-map.md`. Suite-directed sibling skill use after explicit invocation is allowed and is not passive triggering. The suite skill only routes; it must not replace the specialized skill bodies.

For any CrossFrame content task through Suite, finish the needed sibling skills first, then append `crossframe-essay -> crossframe-review` and use `full-visible-v5-longform`: complete visible structural dossier plus complete long-form Chinese article. Only skip the article layer when the user explicitly says only/no article/short answer/table/checklist/pure diagnosis/action plan only.

After a completed Suite workflow has produced diagnosis, article, and review, substantive follow-ups route to `crossframe-inquiry`; pure acknowledgments or endings such as "谢谢", "好的", "明白了", or "先这样" only close lightly and do not open inquiry.

`crossframe-max` is a named-only independent mode. Use it only when the user explicitly asks for `crossframe-max`, `/crossframe-max`, `$crossframe-max`, maximum CrossFrame mode, exhaustive structural projection, full-scale world-model interpretation, or no word-limit complete explanation. It does not use the suite `2+1` selector or ordinary article-type selector.

CrossFrame ProMax is a v8-only, exact-name only independent skill. Read `skills/crossframe-promax/SKILL.md` only when the user writes `crossframe-promax`, `CrossFrame ProMax`, `$crossframe-promax`, or `/crossframe-promax`. If both Max and ProMax are named, ProMax wins; generic maximality remains Max; suite never auto-upgrades; ProMax uses its own audit with no review chain and never falls back to Max.

After explicit CrossFrame invocation, when the user asks for CrossFrame、跨尺度结构诊断、结构诊断、推演、开放断言、反俘获审查、低条件试探行动、强判断、高反身性、亲密关系、疗愈转移、公共制度、长期演化或概念解释:

1. Read `skills/crossframe/SKILL.md`.
2. Read `skills/crossframe/references/read-routing-map.md`.
3. Load only the routed protocol, worksheet, concept card, and template.
4. Start the final answer with a short 推理提纲 unless the user explicitly asks for an ultra-short answer.
5. Speak plain Chinese first; use terms only as optional internal mapping.

Do not copy the full v5.0 text into adapters. Do not duplicate the full skill body across root instruction files. Keep adapters thin and point back to `skills/crossframe/` and `skills/crossframe-essay/`.

CrossFrame must not become personality judgment, fate prediction, professional advice replacement, responsibility dilution, or AI compliance theater.

Visible output must not expose internal reasoning, tool-call parameters, path trial-and-error, stack traces, or English self-planning. Show only the needed outline, evidence boundary, judgment grade, answer, review summary, and next step.

For v5 local fidelity, use `skills/crossframe/references/runtime-read-policy.md`, `skills/crossframe/references/read-routing-map.md`, and `skills/crossframe/references/continuity-closure-map.md` before final output when high-risk concepts, public/institutional responsibility, intimate relationships, long-term evolution, deep analysis, AI compliance, weak signals, or essay/article output are involved. Expand to `continuity-bundles.md`, `concept-fidelity-check.md`, and `source-continuity-check.md` only when an audit or source-structure trace needs details.

After explicit CrossFrame Essay or Suite invocation, when the user asks for 中文文章、长文、评论、思想文章、批判性洞察文章 or structure-to-essay writing:

1. Read `skills/crossframe-essay/SKILL.md`.
2. Read `skills/crossframe/SKILL.md` and `skills/crossframe/references/read-routing-map.md`.
3. Build a `结构洞察底稿` before writing the article body.
4. Use search only for public/current/real-world evidence boundaries and examples; do not let sources decide the thesis.
5. When depth, concept elevation, 引经据典, or theory references are needed, read `skills/crossframe-essay/protocols/concept-elevation-protocol.md` and `skills/crossframe-essay/references/reference-and-allusion-rules.md`.
6. When the user asks for 亲切、编辑、同志口吻、报刊答复、耐心解答, or advice, read `skills/crossframe-essay/protocols/editorial-comrade-voice-protocol.md` and `skills/crossframe-essay/references/editorial-voice-principles.md`.
7. Direct quotes must be verifiable; uncertain source text should be paraphrased or mapped as a thought tradition.
8. Write plain Chinese for ordinary readers and keep CrossFrame terms mostly in the backend. Modern editor-comrade voice should be patient, humble, serious, and decisive, not slogan-like or judgmental.

After explicit invocation of a CrossFrame-adjacent specialized workflow, use the matching sibling skill first: `crossframe-review`, `crossframe-dialogue`, `crossframe-casebook`, `crossframe-history`, `crossframe-max`, `crossframe-promax`, `crossframe-public`, `crossframe-org`, `crossframe-teach`, `crossframe-debate`, `crossframe-notebook`, or `crossframe-inquiry`. Except for the standalone v8-only ProMax runtime, each sibling skill remains a light wrapper around `skills/crossframe/` and must not duplicate the canonical framework text.

This repository adapts exactly 16 CrossFrame skills.
