# Claude Code 适配入口

@AGENTS.md

CrossFrame skills 在 Claude Code 中也是显式调用 only。不要因为普通分析、写作、评论、组织修复、读书、辩论或评审任务自动触发 `.claude/skills/crossframe*/SKILL.md`。只有用户明确点名 `crossframe-suite`、`crossframe`、某个 `crossframe-*`，或使用下面的 `/crossframe*` 命令时才进入 CrossFrame。用户显式调用 `/crossframe-suite` 后，suite 内部继续可以按 routing map 联合读取 sibling skills，这不算被动触发。

这个仓库提供 Claude Code 项目级 skill：

- `.claude/skills/crossframe/SKILL.md`
- `.claude/skills/crossframe-suite/SKILL.md`
- `.claude/skills/crossframe-essay/SKILL.md`
- `.claude/skills/crossframe-review/SKILL.md`
- `.claude/skills/crossframe-dialogue/SKILL.md`
- `.claude/skills/crossframe-casebook/SKILL.md`
- `.claude/skills/crossframe-history/SKILL.md`
- `.claude/skills/crossframe-inquiry/SKILL.md`
- `.claude/skills/crossframe-max/SKILL.md`
- `.claude/skills/crossframe-promax/SKILL.md`
- `.claude/skills/crossframe-public/SKILL.md`
- `.claude/skills/crossframe-org/SKILL.md`
- `.claude/skills/crossframe-teach/SKILL.md`
- `.claude/skills/crossframe-debate/SKILL.md`
- `.claude/skills/crossframe-notebook/SKILL.md`
- `.claude/commands/crossframe.md`
- `.claude/commands/crossframe-suite.md`
- `.claude/commands/crossframe-explain.md`
- `.claude/commands/crossframe-audit.md`
- `.claude/commands/crossframe-essay.md`
- `.claude/commands/crossframe-review.md`
- `.claude/commands/crossframe-dialogue.md`
- `.claude/commands/crossframe-casebook.md`
- `.claude/commands/crossframe-history.md`
- `.claude/commands/crossframe-inquiry.md`
- `.claude/commands/crossframe-max.md`
- `.claude/commands/crossframe-promax.md`
- `.claude/commands/crossframe-public.md`
- `.claude/commands/crossframe-org.md`
- `.claude/commands/crossframe-teach.md`
- `.claude/commands/crossframe-debate.md`
- `.claude/commands/crossframe-notebook.md`

在仓库根目录运行 `claude` 后，可以直接使用：

```text
/crossframe 帮我分析这个组织为什么复盘很多但没有真实修复
/crossframe-suite 写一篇公共评论文章，并安排诊断、查源、成文和评审顺序
/crossframe-explain 解释一下虚无主义
/crossframe-audit 检查这个高责任判断能不能公开
/crossframe-essay 写一篇“团队越复盘越失真”的批判性洞察文章
/crossframe-review 评审这段输出有没有真的推理
/crossframe-dialogue 像编辑回信一样回答这个读者问题
/crossframe-casebook 把这些复盘材料整理成案例库
/crossframe-history 分析唐中后期安史之乱、藩镇与两税法的史料边界和历史接口层
/crossframe-inquiry 基于刚才完成的分析，继续追问反证、补证和迁移条件
/crossframe-max 把这件事当作一个局部世界，做全尺度结构推演并写完整解释
/crossframe-promax 用 v8 框架穷尽分析这个判断，主动搜索反例并给出明确立场
/crossframe-public 分析这个平台申诉机制是否只是表面治理
/crossframe-org 给这个项目失败写组织修复备忘录
/crossframe-teach 用人话解释开放断言
/crossframe-debate 检验这个命题的正反结构和撤回条件
/crossframe-notebook 读这篇文章，写与 CrossFrame 的关联与不同
```

本文件保持轻量。若任务确实涉及 CrossFrame 使用、文档修订或适配层维护，再按需读取：

CrossFrame ProMax is a v8-only, exact-name only independent skill. Read `skills/crossframe-promax/SKILL.md` only when the user writes `crossframe-promax`, `CrossFrame ProMax`, `$crossframe-promax`, or `/crossframe-promax`. If both Max and ProMax are named, ProMax wins; generic maximality remains Max; suite never auto-upgrades; ProMax uses its own audit with no review chain and never falls back to Max.

- `README.md`
- `skills/crossframe-suite/SKILL.md`
- `skills/crossframe-suite/references/workflow-routing-map.md`
- `skills/crossframe/SKILL.md`
- `skills/crossframe-essay/SKILL.md`
- `skills/crossframe/references/read-routing-map.md`
- `skills/crossframe/references/runtime-read-policy.md`
- `skills/crossframe/references/continuity-closure-map.md`
- `skills/crossframe/references/continuity-bundles.md`
- `skills/crossframe/references/v5-source-spine.md`
- `skills/crossframe/references/v5-section-digest-index.md`
- `skills/crossframe/references/v5-term-fidelity.md`
- `skills/crossframe/references/theory-backend-index.md`
- `skills/crossframe/references/v5-coverage-map.md`
- `skills/crossframe/protocols/framework-boundary-protocol.md`
- `skills/crossframe/protocols/lifecycle-diagnosis-protocol.md`
- `skills/crossframe/protocols/progression-protocol.md`
- `skills/crossframe/protocols/field-dissociation-protocol.md`
- `skills/crossframe/protocols/governance-continuity-protocol.md`
- `skills/crossframe/protocols/large-scale-stress-test-protocol.md`
- `skills/crossframe/protocols/expression-translation-protocol.md`
- `skills/crossframe/protocols/diagnosis-protocol.md`
- `skills/crossframe/protocols/proposition-verification-protocol.md`
- `skills/crossframe/protocols/high-reflexivity-protocol.md`
- `skills/crossframe/protocols/intimate-relationship-protocol.md`
- `skills/crossframe/protocols/healing-transfer-protocol.md`
- `skills/crossframe/protocols/public-institution-protocol.md`
- `skills/crossframe/templates/reasoning-outline-output.md`
- `skills/crossframe/templates/user-facing-language.md`
- `skills/crossframe/references/concept-cards/README.md`
- `skills/crossframe-essay/protocols/essay-protocol.md`
- `skills/crossframe-essay/protocols/interactive-drafting-protocol.md`
- `skills/crossframe-essay/references/evidence-and-search-rules.md`
- `skills/crossframe-essay/references/critical-insight-principles.md`
- `skills/crossframe-essay/protocols/concept-elevation-protocol.md`
- `skills/crossframe-essay/references/reference-and-allusion-rules.md`
- `skills/crossframe-essay/references/concept-reference-map.md`
- `skills/crossframe-essay/protocols/editorial-comrade-voice-protocol.md`
- `skills/crossframe-essay/references/editorial-voice-principles.md`
- `skills/crossframe-essay/templates/insight-dossier-template.md`
- `skills/crossframe-essay/templates/essay-output-template.md`
- `skills/crossframe-review/SKILL.md`
- `skills/crossframe-dialogue/SKILL.md`
- `skills/crossframe-casebook/SKILL.md`
- `skills/crossframe-history/SKILL.md`
- `skills/crossframe-inquiry/SKILL.md`
- `skills/crossframe-max/SKILL.md`
- `skills/crossframe-promax/SKILL.md`
- `skills/crossframe-public/SKILL.md`
- `skills/crossframe-org/SKILL.md`
- `skills/crossframe-teach/SKILL.md`
- `skills/crossframe-debate/SKILL.md`
- `skills/crossframe-notebook/SKILL.md`

额外约束：

- 中文为权威语义。
- 默认先给推理提纲，再输出人话判断。
- 不要把术语堆砌当成结构分析。
- 不要把开放断言写成终局审判。
- 使用高风险概念前，先读对应概念卡，并用 `runtime-read-policy.md` 与 `continuity-closure-map.md` 避免概念压缩和联读遗漏。
- 高责任、公共制度、亲密关系、长期演化、深度分析和文章输出，优先读取 `runtime-read-policy.md`、`read-routing-map.md` 和 `continuity-closure-map.md`；需要展开审计时再查看连续联读包和源结构连续性工作表，避免只读单概念卡导致 5.0 失真。
- 强判断、高反身性、亲密关系、疗愈转移、公共制度、框架边界、生命周期、递进、势场解离、治理连续性、超大规模压力测试和长期演化问题，必须按 `read-routing-map.md` 进入对应深水区模块。
- 当用户要写文章、长文、评论、思想文章或批判性洞察文章时，使用 `crossframe-essay`：先形成完整可见 `结构洞察底稿`，再写完整长文 `文章正文`；需要深度时按需概念上升和引入中西经典/理论参照，但引用必须可核验并回到现实责任链。
- `crossframe-essay` 自动成文默认读取现代编辑口吻协议：问题型主题用答复体，公共评论、思想文章和概念文章用评论体；只有用户明确要求中性报告、备忘录、表格、清单、纯诊断或学术摘要时才关闭。不要口号化，不要把亲切写成和稀泥，也不要把严厉写成人格审判。
- 当用户要求评审、短答复、案例库、公共议题、组织修复、概念教学、命题辩论或研究笔记时，优先使用对应 `crossframe-*` 平行 skill；所有平行 skill 仍须读取 `skills/crossframe/SKILL.md` 与 `skills/crossframe/references/read-routing-map.md`。
- 当用户明确要求 `crossframe-max`、最大算力、全尺度穷尽推演、把一件事当作局部世界完整解释或不设字数限制时，读取 `skills/crossframe-max/SKILL.md`。这是独立模式，不走 `crossframe-suite` 的 `2+1` 模式/角色选择器，也不走普通文章类型选择器。
- 显式调用后优先考虑 `crossframe-suite` 作为总入口。当用户显式要求多个 CrossFrame skill 连续协作时，先用 `crossframe-suite` 决定顺序；suite 内部联合读取 sibling skills 不算被动触发。常见链路包括 `crossframe -> crossframe-public -> crossframe-essay -> crossframe-review`、`crossframe -> crossframe-org -> crossframe-essay -> crossframe-review`、`crossframe -> crossframe-history -> crossframe-essay -> crossframe-review`、`crossframe -> crossframe-notebook -> crossframe-essay -> crossframe-review`、`crossframe -> crossframe-review(lite) -> crossframe-inquiry`。不要一次读取全部 skill。
- 完整链路已经完成分析、成文和 review 后，下一轮实质输入默认进入 `crossframe-inquiry`；纯致谢、确认收到或结束语（如“谢谢”“好的”“明白了”“先这样”）只轻量收束，不自动展开追问。
- 当用户从 suite 总入口进入任何 CrossFrame 内容任务时，默认输出 `full-visible-v5-longform`：先完成必要专项 skill，再追加 `crossframe-essay -> crossframe-review`，包含完整可见底稿和完整长文正文。只有用户明确说“只要/不要文章/短答/表格/清单/纯诊断/仅行动方案”时，才关闭默认文章层。
- 默认不展示内部 reasoning、工具调用参数、路径试错、错误栈或英文自我规划；需要审计时只展示台账摘要、风险点和必要下一步。
