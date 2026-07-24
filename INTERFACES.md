# 多接口适配说明

这个仓库的权威 skill 主体位于：

- `skills/crossframe/SKILL.md`
- `skills/crossframe-suite/SKILL.md`
- `skills/crossframe-essay/SKILL.md`
- `skills/crossframe-critical/SKILL.md`
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

`crossframe-suite` 负责复杂任务的连续调度；`crossframe` 负责结构诊断；`crossframe-essay` 负责把结构诊断转成中文批判性洞察文章；`crossframe-critical` 是只允许点名触发的结构批判长文 skill，不接入 suite 默认链路；`crossframe-max` 是只允许显式点名触发的最大化结构推演入口，把一件事当作局部世界展开世界观、运行规律、问题结构、处理路径和演化分支；`crossframe-promax` 是精确点名的 v8 独立 runtime；其它 `crossframe-*` 负责评审、答复、案例、历史研究、追问、公共议题、组织修复、教学、辩论和研究笔记。其他接口文件只是薄适配层，用来告诉不同 AI 工具如何读取与调用这些 skill。不要把完整协议复制成多份，以免内容漂移。

## 适配原则

- 中文为权威语义；`CrossFrame` 只是英文传播名与 skill id。
- 新增接口只负责入口、路由和最小约束。
- 整套 CrossFrame skill 只能显式触发；用户必须点名 `crossframe-suite`、`crossframe`、某个 `crossframe-*`，或使用 `$crossframe-*` / `/crossframe-*` 命令。
- 外部初始触发不能是被动的；普通分析、写作、评论、组织修复、读书或辩论任务不应自动召回 CrossFrame。
- 用户显式调用 `crossframe-suite` 后，多 skill 连续任务仍然先读取 `skills/crossframe-suite/SKILL.md`；suite 可以按 routing map 联合读取 sibling skill，但不替代专项 skill。
- `crossframe-suite` 是显式调用后的推荐总入口；只要从总入口进入，默认在必要专项 skill 后追加 `crossframe-essay -> crossframe-review`，输出档位为 `full-visible-v5-longform`。
- 完整链路完成后，下一轮实质输入默认进入 `crossframe-inquiry`；纯致谢、确认收到或结束语只轻量收束。
- `crossframe-critical` 不进入总入口调度。只有用户明确写 `$crossframe-critical`、`crossframe-critical` 或要求测试这个批判 skill 时才读取它。
- `crossframe-max` 不进入 suite 的 `2+1` 模式/角色选择器，也不走普通文章类型选择器。只有用户明确写 `$crossframe-max`、`/crossframe-max`、`crossframe-max` 或要求最大算力、全尺度穷尽推演、不设字数限制完整解释时才读取它。
- CrossFrame ProMax 是 v8-only 的 exact-name only 独立 skill：仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时读取 `skills/crossframe-promax/SKILL.md`。Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。
- 当前仓库包含 16 个 CrossFrame skill。
- 只有用户明确说“只要/不要文章/短答/表格/清单/纯诊断/仅行动方案”时，才关闭默认文章层。
- 若需要更新框架主体，优先更新 `skills/crossframe/`，再回填薄适配层。
- 若需要更新文章写作主体，优先更新 `skills/crossframe-essay/`，并确认它仍通过相对路径读取 `skills/crossframe/`。
- 若需要更新平行专项主体，优先更新对应 `skills/crossframe-*/`，并确认它仍通过相对路径读取 `skills/crossframe/`。
- 用户可见输出默认先给推理提纲，再说人话。
- 文章输出默认先给完整可见 `结构洞察底稿`，再给完整长文 `文章正文`；从 `crossframe-suite` 默认成文时默认启用现代编辑底色；需要深度时可按需加入概念上升和中西经典/理论参照。
- 直接引用必须可核验；不确定原句时只做意译、典故或思想映射。
- 现代编辑同志口吻是前台声口层，不改变结构判断；亲切不能和稀泥，严厉不能人格审判。
- 默认不展示内部 reasoning、工具调用参数、路径试错、错误栈或英文自我规划；需要审计时只展示台账摘要、风险点和必要下一步。
- 高风险概念必须按需读取 `skills/crossframe/references/concept-cards/`，不要只按字面理解。
- 防失真材料日常以 `skills/crossframe/references/runtime-read-policy.md`、`skills/crossframe/references/read-routing-map.md` 和 `skills/crossframe/references/continuity-closure-map.md` 为入口；需要展开审计或追踪原文结构时，再查看 `skills/crossframe/references/v5-term-fidelity.md`、`skills/crossframe/references/continuity-bundles.md`、`skills/crossframe/references/v5-source-spine.md`、`skills/crossframe/references/v5-section-digest-index.md`、`skills/crossframe/worksheets/concept-fidelity-check.md` 和 `skills/crossframe/worksheets/source-continuity-check.md`。
- 高责任、公共制度、亲密关系、长期演化、深度分析和文章输出场景，不能只读单张概念卡；必须检查对应 5.0 连续联读包。
- 深水区模块以命题验证、高反身性、亲密关系轻量入口、疗愈转移、公共制度专项、框架边界、生命周期、递进闭环、势场解离、治理连续性、超大规模压力测试、表达翻译和理论后台索引为入口。
- `skills/crossframe/references/v5-coverage-map.md` 用于维护时核对 v5.0 覆盖状态，不作为普通输出材料。

## 当前支持的接口

| 接口 | 入口文件 | 说明 |
| --- | --- | --- |
| Codex | `skills/crossframe*/` | 可直接用 skill-installer 安装；安装后不被动触发，需用户显式点名；suite 显式启动后仍可联合调用 sibling skill |
| Claude Code | `.claude/skills/crossframe*/SKILL.md` + `.claude/commands/crossframe*.md` + `CLAUDE.md` | 禁止自动触发 skill；通过 `/crossframe`、`/crossframe-suite`、`/crossframe-max`、`/crossframe-promax`、`/crossframe-explain`、`/crossframe-audit`、`/crossframe-essay` 或明确点名启动 |
| Gemini CLI | `GEMINI.md` | 仓库级上下文入口 |
| Cursor | `.cursor/rules/crossframe-suite.mdc` + `.cursor/rules/crossframe.mdc` + `.cursor/rules/crossframe-essay.mdc` + `AGENTS.md` | 规则文件与通用入口 |
| GitHub Copilot | `.github/copilot-instructions.md` | 仓库级说明 |
| Windsurf / Cascade | `.windsurf/rules/crossframe.md` + `AGENTS.md` | Workspace rule，只支持手动 `@crossframe` 或明确点名，不使用自动规则场景 |
| Cline | `.clinerules/crossframe.md` | Project rule |
| Roo Code | `.roo/rules/crossframe.md` | Workspace-wide rule |
| Continue | `.continue/rules/crossframe.md` | Local rule |
| Aider | `CONVENTIONS.md` + `.aider.conf.yml` | 自动读取 conventions |
| LLM 索引 | `llms.txt` | 机器可读入口索引 |
| 通用 agent | `AGENTS.md` | 显式点名后的入口 |

## 迁移到别的项目

如果要把 CrossFrame 带到另一个项目：

- Codex：复制所有 `skills/crossframe*/` 到 `$HOME/.codex/skills/`
- Claude Code：复制 `.claude/skills/crossframe*/`、`.claude/commands/`、`CLAUDE.md`，并保留所有 `skills/crossframe*/`
- Gemini CLI：复制 `GEMINI.md`，并保留所有 `skills/crossframe*/`
- Cursor：复制 `.cursor/rules/crossframe*.mdc` 或 `AGENTS.md`，并保留所有 `skills/crossframe*/`
- GitHub Copilot：复制 `.github/copilot-instructions.md` 和 `AGENTS.md`，并保留所有 `skills/crossframe*/`
- Windsurf / Cascade：复制 `.windsurf/rules/crossframe.md`，并保留所有 `skills/crossframe*/`
- Cline：复制 `.clinerules/crossframe.md`，并保留所有 `skills/crossframe*/`
- Roo Code：复制 `.roo/rules/crossframe.md`，并保留所有 `skills/crossframe*/`
- Continue：复制 `.continue/rules/crossframe.md`，并保留所有 `skills/crossframe*/`
- Aider：复制 `CONVENTIONS.md` 和 `.aider.conf.yml`，并保留所有 `skills/crossframe*/`

## 维护顺序

1. `skills/crossframe-suite/SKILL.md` 与 `skills/crossframe-suite/references/workflow-routing-map.md`
2. `skills/crossframe/SKILL.md`
3. `skills/crossframe/references/runtime-read-policy.md`、`skills/crossframe/references/read-routing-map.md`、`skills/crossframe/references/continuity-closure-map.md`、`skills/crossframe/references/v5-term-fidelity.md`、`skills/crossframe/references/continuity-bundles.md`、`skills/crossframe/references/v5-source-spine.md`
4. `skills/crossframe-essay/SKILL.md`
5. 各 `skills/crossframe-*/SKILL.md`
6. 各 `skills/crossframe-*/protocols/` 与 `references/`
7. `skills/crossframe/references/theory-backend-index.md`
8. `skills/crossframe/references/v5-coverage-map.md`
9. `skills/crossframe/protocols/`
10. `skills/crossframe/worksheets/`
11. `skills/crossframe/templates/`
12. `skills/crossframe/references/concept-cards/`
13. `README.md`
14. `AGENTS.md`
15. `INTERFACES.md`
16. 其他接口入口文件
