# 适配说明

| 工具 | 入口 | 推荐用法 | 注意事项 |
| --- | --- | --- | --- |
| Codex | `skills/crossframe*/` | Windows 运行 `scripts/install-codex.ps1`，macOS / Linux 运行 `scripts/install-codex.sh`，安装后显式点名 `crossframe-suite` | 不被动触发 |
| Claude Code | `.claude/skills/crossframe*/` + `.claude/commands/crossframe*.md` + `CLAUDE.md` | 使用 `/crossframe-suite`、`/crossframe-max`、`/crossframe-promax`、`/crossframe-essay`、`/crossframe-history`、`/crossframe-inquiry` | 仓库命令和全局命令可同步 |
| Gemini CLI | `GEMINI.md` | 读取仓库级上下文后按 skill 路由 | 不要一次加载全部 skill |
| Cursor | `.cursor/rules/crossframe*.mdc` | ProMax 可由专用 `crossframe-promax.mdc` 精确点名进入，主体仍读 `skills/` | `alwaysApply: false` |
| GitHub Copilot | `.github/copilot-instructions.md` | 仓库内文档分析和维护时使用 | 不能替代完整 skill 文件 |
| Windsurf / Cascade | `.windsurf/skills/crossframe-promax/SKILL.md` + `.windsurf/rules/crossframe-promax.md` | 原生 skill 发现后仍只接受四种精确名称，主体回到 `skills/` | `model_decision`，不做自动常驻规则 |
| Cline | `.clinerules/crossframe.md` + `crossframe-promax.md` | 精确点名 ProMax 时使用专用薄入口 | 保持薄适配 |
| Roo Code | `.roo/skills/crossframe-promax/SKILL.md` + `.roo/rules/crossframe-promax.md` | 原生 skill 发现后仍只接受四种精确名称，主体回到 `skills/` | 保持 explicit-only |
| Continue | `.continue/rules/crossframe.md` + `crossframe-promax.md` | 精确点名 ProMax 时使用专用 Local rule | 只提示路由 |
| Aider | `CONVENTIONS.md` + `.aider.conf.yml` | 维护仓库时读取约定 | 不复制主体协议 |
| 通用 agent | `AGENTS.md` | 第一个入口文件 | 仍需回到 `skills/` |
| LLM 索引 | `llms.txt` | 机器可读入口 | 适合快速定位 |

如果工具不支持 skill 文件夹，也可以只读取 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md` 或 `llms.txt`。但薄入口只负责路由，效果不如完整保留 `skills/crossframe*`。

所有薄适配都必须保留三条新路由：历史材料、史料边界和长时段制度问题进入 `crossframe-history`；全尺度推演、最大化结构推演、把一件事当作局部世界完整解释时进入独立 `crossframe-max`，不走 suite 的 `2+1` 选择器；完整分析、成文和 review 已完成后，下一轮未明确换题或退出、且不是纯致谢/确认收到/结束语的实质用户输入默认进入 `crossframe-inquiry`，并可定向检索 1-3 个 sibling skill 的必要材料。

CrossFrame ProMax 是 v8-only 的 exact-name only 独立 skill：仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时读取 `skills/crossframe-promax/SKILL.md`。Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。适配层只保留这条路由并链接权威 skill，不复制 v8 知识或运行协议。

维护镜像时运行：

```powershell
python scripts\sync_skill_mirrors.py --check
python scripts\sync_skill_mirrors.py
```

默认会同步仓库内 `skills/crossframe*` 到 `.claude/skills`。

Codex 的两个安装脚本都会安装同一组 16 个 `crossframe-*` skills，并在覆盖已有目录前做临时备份；安装失败时回滚原目录。
