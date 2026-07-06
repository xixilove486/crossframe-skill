# Changelog

## Unreleased

### Added

- 新增 `crossframe-max` repair loop：validator 失败后生成 `max-validator-report.json` 与 `max-repair-plan.json`，按 affected phase 执行受控重建、降档、撤回或 incomplete。
- 新增 Max repair schemas、repair plan template、repair fixture validator 和 repair plan builder。
- 新增 v6 contract map，校验 route-required concepts、registry anchors 与 concept contracts 的闭环。

### Changed

- `check_crossframe_max_route_ledgers.py` 增加 concept source anchor closure、contract closure 和结构化 JSON 报告。
- `check_crossframe_max_artifacts.py` 增加结构化错误、真实 claim/source 回指检查和 repair action 映射。
- CI 增加 Max repair fixtures 与 repair schemas 校验。

## v5.1.7 - 2026-06-24

### Added

- 新增 claim ledger schema fixtures 与 `scripts/validate_claim_ledger_schema_fixtures.py`，用 `jsonschema` 校验好样例通过、坏样例失败。
- GitHub Actions verify workflow 新增 Bash/Python/PowerShell 脚本语法检查、schema fixture 校验和发布包烟测。

### Changed

- `crossframe-history` 与 `crossframe-inquiry` 触发语义统一为 `explicit-or-suite`：允许显式命令或 suite 路由，不允许普通任务隐式触发。
- README、Quickstart 与 WORKFLOWS 同步补齐本地验证命令、安全边界和输出体积预算。
- `scripts/install-codex.ps1` 增加 `py -3` / `python` fallback。
- 网站 Demo / Install tabs 增加方向键、Home、End 键盘切换支持，并为 no-JS 场景保留可读提示和默认安装命令。

### Verification

- 完整性校验新增 CI 覆盖、schema fixtures、explicit-or-suite 语义、安装脚本 fallback 和网站键盘 tab 检查。

## v5.1.6 - 2026-06-23

### Added

- 新增 GitHub Actions verify workflow，自动运行 skill integrity、source continuity、claim ledger schema、mirror sync 和 whitespace 检查。
- 新增 `scripts/install-codex.sh`，为 macOS / Linux 提供 Codex Bash 安装入口。

### Changed

- README 顶部版本徽章与首页 footer 对齐到 `v5.1.6`。
- 首页 Hero CTA 增加“查看文档”入口，指向仓库文档区。
- 首页增加 no-JS fallback，说明交互示例需要 JavaScript，并引导用户查看 README 和 docs。
- 首页 Install 区改为同时展示 Windows PowerShell 与 macOS / Linux Bash 安装方式。

## v5.1.5 - 2026-06-22

### Changed

- 首页 Demo Cards 全部改为虚构或匿名结构样例，避免把真实国家、平台、组织或宗教/哲学争议放在 landing page 第一层。
- Demo 区新增安全说明、匿名模拟标签和低敏 tab 命名：概念追问、历史接口、组织机制、公共证据、完成后追问。
- Hero 补充 10 秒微流程，并把 CTA 调整为“开始安装 / 查看模拟场景”。
- 新增“什么时候适合用 CrossFrame？”适合/不适合区块，降低新用户误解。
- 分享预览从 SVG 切换为 PNG，并补齐 Twitter card 元数据。
- Install、FAQ、Footer 和 `docs/EXAMPLES.md` 补齐非 Windows、虚构样例、高责任主题边界和版本状态说明。

### Verification

- 完整性校验新增安全模拟首页、PNG 分享图、FAQ、Use Boundary、v5.1.5 包版本和敏感 demo 退场检查。

## v5.1.4 - 2026-06-22

### Changed

- 首页补充“项目介绍页，不是在线运行器”的说明，降低首次访问误解。
- 移动端 hero 视觉区调整为 240px，改善结构图和台账卡片可读性。
- Demo 与 Install tabs 补齐 `tabpanel` / `aria-controls` 语义。
- Install 区补充 Windows PowerShell 与 macOS / Linux 手动复制说明。
- FAQ 增加“网页能否直接运行 CrossFrame”。
- Canonical、`og:url` 和 `og:image` 改为公开页面绝对地址。

### Verification

- 完整性校验新增本轮网页抛光项覆盖。

## v5.1.3 - 2026-06-22

### Added

- 新增 `site/` 纯静态中文介绍页，用独立 landing page 展示 CrossFrame 的用途、质量链、场景 demo、14 个 skill 地图和安装入口。
- 新增 GitHub Pages workflow，从 `site/` 直接部署项目网站。

### Changed

- README 顶部增加网页介绍和 Release 入口。
- 发布包脚本纳入 `site/`，公开 zip 会包含网站文件。

### Verification

- 完整性校验新增网站关键文案、交互脚本、视觉资产、Pages workflow 和发布包覆盖检查。

## v5.1.2 - 2026-06-22

### Changed

- README 顶部徽章更新为 `CrossFrame_v5.1`，工作流徽章更新为 `diagnosis -> writing -> review -> inquiry`。
- `docs/WHAT_IS_CROSSFRAME.md` 增加一分钟例子、“它不是什么”和最推荐用法，提升新用户入口说明。
- 完成态 `crossframe-inquiry` 接管排除纯致谢、确认收到、结束语或无内容回应，避免把“谢谢 / 好的 / 明白了 / 先这样”自动展开成追问。
- `docs/EXAMPLES.md` 增加 inquiry mini 输出示例。

### Verification

- 完整性校验新增 README badge、介绍页三块内容、完成态结束语例外和 inquiry 示例检查。

## v5.1.1 - 2026-06-22

### Changed

- Cursor、Continue、Cline、Roo、Windsurf、Copilot 和通用适配入口补齐 `crossframe-history` 与完成态 `crossframe-inquiry` 路由。
- 完整链路完成后，未明确换题或退出的下一轮用户输入默认进入 `crossframe-inquiry`；追问层可定向检索 1-3 个 sibling skill 的必要材料。
- 对外说明统一使用 `full-visible-v5-longform`，不再使用容易误判为旧版的混合长文叫法。

### Verification

- 完整性校验新增适配入口断裂检查、旧叫法禁用检查和 history/inquiry 覆盖检查。

## v5.1.0 - 2026-06-22

### Added

- 面向普通用户的 `docs/` 文档层：快速开始、概念说明、工作流、样例、适配、安全边界和 FAQ。
- `scripts/sync_skill_mirrors.py`：同步 `skills/crossframe*` 到 `.claude/skills` 等镜像。
- `scripts/package_crossframe_skill.py`：生成公开发布 zip。

### Changed

- README 改为面向大众的入口页，详细说明迁移到 `docs/`。
- 公开验证命令默认使用 `--materials-only`，不依赖维护者本机私有 DOCX 路径。
- Suite 与适配入口明确禁止向用户暴露内部 reasoning、工具调用参数、路径试错、错误栈或英文自我规划。

### Removed

- 旧 v2 连续性脚本不再作为公开维护入口。

## v5.0.2 - 2026-06-22

### Added

- `crossframe-history`：历史材料、史料边界、长时段制度问题和 archive/FOIA backlog 接口层。
- `crossframe-inquiry`：完成态后的结构追问层，支持反证、补证、迁移应用和行动边界确认。
- `claim ledger`、`concept contract`、`source_id -> claim_id` 回指和正文强于台账回扫。
- Claude、Cursor、Gemini、Copilot、Windsurf、Cline、Roo、Continue、Aider 和通用 agent 的 14-skill 薄适配。

### Changed

- Suite 默认链路加入 read-state capsule、source-anchor 检查、claim-ledger-check、review 和 completion inquiry 接管。
- 来源台账升级为十字段口径，要求稳定 `source_id` 和“支持的 `claim_id` / 命题”。
- `crossframe-review(lite)` 明确为 `crossframe-review` 的轻量用法，不再作为独立 skill 名称。
- 运行时不再使用旧 `integrity-check.md` 入口。
- 运行时不再使用 `five-gates-worksheet.md`。

## v5.0.1 - 2026-06-15

- 发布旧稳定版 CrossFrame Skill Suite。
- 包含 suite、core、essay、review、public、org、debate、critical、dialogue、casebook、notebook、teach 等早期 skill。
