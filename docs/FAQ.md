# FAQ

## 为什么必须 explicit-only？

CrossFrame 会改变 AI 的读取和判断方式。普通摘要、改写、事实查询或工具操作不应该自动进入结构诊断链路。只有用户明确点名 CrossFrame、`crossframe-suite`、某个 `crossframe-*` 或命令时才启动。

## 为什么这么复杂？

复杂问题最容易被 AI 压缩成顺口判断。Claim ledger、source ledger、concept contract 和 review 都是为了防止“看起来很像推理”的输出越过证据边界。

## 一定会写长文吗？

从 `crossframe-suite` 进入 CrossFrame 内容任务时，默认会追加 `crossframe-essay -> crossframe-review`。用户明确要求“只要短答 / 表格 / 清单 / 纯诊断 / 不要文章”时，关闭文章层。

## 完成后为什么还要 inquiry？

一轮诊断或文章完成后，很多真正有价值的问题才出现。`crossframe-inquiry` 会基于上一轮 claim ledger 和 review 结果继续追问、反证、补证、迁移和收束。

## crossframe-max 和 suite 有什么区别？

`crossframe-suite` 负责普通连续工作流调度；`crossframe-max` 是显式点名的独立模式。它把对象当作局部世界，展开世界观、运行规律、问题结构、处理路径和演化分支，不走 suite 的 `2+1` 选择器，也不设默认字数上限。

## crossframe-promax 会自动替代 Max 吗？

不会。CrossFrame ProMax 是 v8-only 的 exact-name only 独立 skill：仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时读取 `skills/crossframe-promax/SKILL.md`。Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。

## 是否需要原始 DOCX？

普通用户不需要。公开仓库已经包含生成后的 v5 连续性材料，日常运行：

```powershell
python scripts\check_source_continuity.py --materials-only --repo .
```

只有维护者要从原始 v5.0 DOCX 重新生成源结构材料时，才需要传 `--source-docx`。
