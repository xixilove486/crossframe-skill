# Gemini CLI 适配入口

@AGENTS.md

本文件是 Gemini CLI 的仓库级上下文入口。

CrossFrame skills 在 Gemini CLI 中也是显式调用 only。不要因为普通分析、写作、评论、组织修复、读书、辩论或评审任务自动触发 CrossFrame。只有用户明确点名 `crossframe-suite`、`crossframe`、某个 `crossframe-*`，或明确说“用 CrossFrame / 用跨尺度结构诊断框架”时才进入本文件下面的 CrossFrame 路由。

如果用户显式调用 `crossframe-suite`，并要求一个复杂任务需要多个 CrossFrame skill 连续协作，先读取：

1. `skills/crossframe-suite/SKILL.md`
2. `skills/crossframe-suite/references/workflow-routing-map.md`
3. `skills/crossframe-suite/protocols/suite-dispatch-protocol.md`

常见链路：普通文章 `crossframe -> crossframe-essay -> crossframe-review`；公共评论 `crossframe -> crossframe-public -> crossframe-essay -> crossframe-review`；组织复盘文章 `crossframe -> crossframe-org -> crossframe-essay -> crossframe-review`；历史研究 `crossframe -> crossframe-history -> crossframe-essay(full-visible-v5-longform) -> crossframe-review`；答读者问 `crossframe -> crossframe-dialogue -> crossframe-essay(full-visible-v5-longform) -> crossframe-review`；读书研究 `crossframe -> crossframe-notebook -> crossframe-essay(full-visible-v5-longform) -> crossframe-review`；完成后追问 `crossframe -> crossframe-review(lite) -> crossframe-inquiry`。不要一次读取全部 skill。

显式调用后优先考虑 `crossframe-suite`。suite 内部按 routing map 联合读取 sibling skills 不算被动触发。只要用户从 suite 总入口进入任何 CrossFrame 内容任务，默认先完成必要专项 skill，再追加 `crossframe-essay -> crossframe-review`，输出 `full-visible-v5-longform`，包含完整可见底稿和完整长文正文。只有用户明确说“只要/不要文章/短答/表格/清单/纯诊断/仅行动方案”时，才关闭默认文章层。

完整链路已经完成分析、成文和 review 后，下一轮实质输入默认进入 `crossframe-inquiry`；纯致谢、确认收到或结束语（如“谢谢”“好的”“明白了”“先这样”）只轻量收束，不自动展开追问。

如果用户显式调用 `crossframe-max`、`/crossframe-max`、`$crossframe-max`，或要求最大算力、全尺度穷尽推演、不设字数限制完整解释，请读取 `skills/crossframe-max/SKILL.md`。这是独立模式，不走 `crossframe-suite` 的 `2+1` 模式/角色选择器，也不走普通文章类型选择器；它把一件事当作局部世界来建模，展开世界观、运行规律、问题结构、处理路径和演化分支。

CrossFrame ProMax 是 v8-only 的 exact-name only 独立 skill：仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时读取 `skills/crossframe-promax/SKILL.md`。Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。

如果用户显式调用 `crossframe-essay` 或经 `crossframe-suite` 路由到写作，并要求写中文文章、长文、评论、思想文章、批判性洞察文章或结构洞察文章，请读取：

1. `skills/crossframe-essay/SKILL.md`
2. `skills/crossframe/SKILL.md`
3. `skills/crossframe/references/read-routing-map.md`
4. 对应 `skills/crossframe/protocols/` 文件
5. 高责任、公共制度、亲密关系、长期演化、深度分析和文章输出，优先读取 `skills/crossframe/references/runtime-read-policy.md` 与 `skills/crossframe/references/continuity-closure-map.md`；需要展开源结构时再按需读取 `skills/crossframe/references/continuity-bundles.md`、`skills/crossframe/references/v5-source-spine.md` 与 `skills/crossframe/references/v5-section-digest-index.md`
6. `skills/crossframe-essay/references/evidence-and-search-rules.md`
7. 若需要概念上升、引经据典、理论参照或文学互文，读取 `skills/crossframe-essay/protocols/concept-elevation-protocol.md`、`skills/crossframe-essay/references/reference-and-allusion-rules.md`、`skills/crossframe-essay/references/concept-reference-map.md`
8. 自动成文默认读取 `skills/crossframe-essay/protocols/editorial-comrade-voice-protocol.md` 与 `skills/crossframe-essay/references/editorial-voice-principles.md`；只有显式中性报告/备忘录/表格/纯诊断时关闭
9. `skills/crossframe-essay/protocols/essay-protocol.md` 或 `interactive-drafting-protocol.md`
10. `skills/crossframe-essay/templates/insight-dossier-template.md`
11. `skills/crossframe-essay/templates/essay-output-template.md` 或 `interactive-session-template.md`

文章输出默认先给完整可见 `结构洞察底稿`，再给完整长文 `文章正文`。公共议题、最新事实、真实组织/平台/人物/政策/公司相关内容必须查源；私人关系、哲学概念和泛论随笔默认不查源，除非用户要求。直接引用必须可核验；不确定原句时只做意译或思想映射；经典/理论参照必须回到现实机制与责任链。现代编辑底色是默认前台表达：亲切但不和稀泥，果敢但不人格审判。

如果用户显式调用 `crossframe` 或经 `crossframe-suite` 路由到结构诊断、推演、开放断言、高责任审查或低条件行动，请读取：

1. `skills/crossframe/SKILL.md`
2. `skills/crossframe/references/read-routing-map.md`
3. 对应 `skills/crossframe/protocols/` 文件
4. `skills/crossframe/templates/reasoning-outline-output.md`
5. `skills/crossframe/templates/user-facing-language.md`
6. 若使用高风险概念，读取 `skills/crossframe/references/concept-cards/README.md` 与对应概念卡
7. 高责任、公共制度、亲密关系、长期演化、深度分析和文章输出，优先读取 `skills/crossframe/references/runtime-read-policy.md` 与 `skills/crossframe/references/continuity-closure-map.md`；需要展开源结构时再按需读取 `skills/crossframe/references/continuity-bundles.md`、`skills/crossframe/references/v5-source-spine.md` 与 `skills/crossframe/references/v5-section-digest-index.md`
8. 输出前用 `skills/crossframe/references/runtime-read-policy.md`、`skills/crossframe/references/read-routing-map.md` 和 `skills/crossframe/references/continuity-closure-map.md` 做轻量闭包检查；需要审计时再展开 `skills/crossframe/worksheets/concept-fidelity-check.md` 和 `skills/crossframe/worksheets/source-continuity-check.md`

输出要求：

- 先给简短推理提纲。
- 先说人话，不堆术语。
- 明确区分事实、解释、机制候选和判断档位。
- 中文概念不强行英文化。
- 前台少术语，后台不能少读必要概念。
- 强判断、高反身性、亲密关系、疗愈转移、公共制度、框架边界、生命周期、递进、势场解离、治理连续性、超大规模压力测试和长期演化问题，按 `read-routing-map.md` 读取对应深水区模块。
- 需要连续保真的场景，必须检查 5.0 连续联读包，避免只读单概念卡导致失真。
- 默认不展示内部 reasoning、工具调用参数、路径试错、错误栈或英文自我规划；只展示必要的推理提纲、证据边界、判断档位、结论和下一步。

如果用户显式点名以下专项 skill，或经 `crossframe-suite` 路由到以下专项任务，优先读取对应平行 skill，再按该 skill 的说明读取 `skills/crossframe/SKILL.md` 与路由图：

- 评审、审查、打分、抓坏输出：`skills/crossframe-review/SKILL.md`
- 答读者问、编辑回信、咨询式短答复：`skills/crossframe-dialogue/SKILL.md`
- 案例库、材料沉淀、复盘转案例：`skills/crossframe-casebook/SKILL.md`
- 历史材料、历史事件、史料互读、长时段演化、archive/FOIA backlog：`skills/crossframe-history/SKILL.md`
- 完成态后继续追问、反证、补证、迁移应用或行动边界确认：`skills/crossframe-inquiry/SKILL.md`
- 最大化结构推演、局部世界建模、全尺度解释、演化路径穷尽：`skills/crossframe-max/SKILL.md`
- 精确点名的 v8 ProMax 穷尽推演、全概念命中、自反例攻击：`skills/crossframe-promax/SKILL.md`
- 公共议题、平台申诉、制度评论、合规材料：`skills/crossframe-public/SKILL.md`
- 组织修复、反馈写回、复盘改造、低风险试点：`skills/crossframe-org/SKILL.md`
- 概念教学、误读纠偏、练习题：`skills/crossframe-teach/SKILL.md`
- 命题辩论、正反结构、撤回条件：`skills/crossframe-debate/SKILL.md`
- 读书、理论、文章研究笔记，关联与不同：`skills/crossframe-notebook/SKILL.md`
