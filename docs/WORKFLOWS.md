# 工作流

## 默认入口

复杂任务优先进入：

```text
crossframe-suite
```

Suite 只负责调度，不替代专项 skill。它会先输出调度提纲，再读取所需 sibling skills。

## 常见链路

| 任务 | 推荐链路 |
| --- | --- |
| 结构诊断 | `crossframe -> crossframe-review` |
| 中文长文 | `crossframe -> crossframe-essay -> crossframe-review` |
| 公共评论 | `crossframe -> crossframe-public -> crossframe-essay -> crossframe-review` |
| 组织复盘 | `crossframe -> crossframe-org -> crossframe-essay -> crossframe-review` |
| 历史研究 | `crossframe -> crossframe-history -> crossframe-essay -> crossframe-review` |
| 答读者问 | `crossframe -> crossframe-dialogue` |
| 读书研究 | `crossframe -> crossframe-notebook` |
| 命题辩论 | `crossframe -> crossframe-debate -> crossframe-review` |
| 最大化推演 | `crossframe-max -> crossframe-review` |
| v8 ProMax | `crossframe-promax`（独立审计，不串联 review） |
| 完成后追问 | `previous_context -> crossframe-inquiry` |

## 完整长文链路

未显式关闭文章层时，suite 默认形成：

```text
crossframe
-> source-continuity-check
-> v5-read-state-capsule
-> source-anchor-integrity-check
-> claim ledger / claim-ledger-check
-> needed sibling skills
-> crossframe-essay
-> crossframe-review
-> crossframe-inquiry armed
```

完整链路完成后，下一轮用户没有明确说“新任务 / 换主题 / 退出追问 / 不接着上文”，且不是“谢谢 / 好的 / 明白了 / 先这样”等纯致谢、确认收到或结束语时，默认进入 `crossframe-inquiry`。

`crossframe-max` 是独立模式，不走 `crossframe-suite` 的 `2+1` 模式/角色选择器，也不走普通文章类型选择器。它用于把一个对象当作局部世界，展开世界观、运行规律、问题结构、处理路径、演化分支、`max-dossier` 和 `max-essay`。

CrossFrame ProMax 是 v8-only 的 exact-name only 独立 skill：仅在用户精确点名 `crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax` 或 `/crossframe-promax` 时读取 `skills/crossframe-promax/SKILL.md`。Max 与 ProMax 同时出现时 ProMax 优先；泛化最大化请求仍由 Max；suite 不得自动升级；ProMax 使用独立审计，不串联 review，也不得降级回 Max。

## 输出体积

suite 支持三档可见体积：

| 档位 | 适合 |
| --- | --- |
| `brief-visible` | 只要方向、短答、三句话、下一步行动。 |
| `standard-visible` | 要可读输出，但不需要完整长文。 |
| `full-visible-v5-longform` | 默认档位；完整可见底稿、完整长文正文和 review。 |

体积只影响前台展开程度，不取消事实边界、`claim_id`、证据档位、撤回条件和行动上限。

## 纯追问例外

如果用户已经有上游分析、文章、底稿或 review，又要求“继续追问”“我不同意”“还有别的解释吗”“怎么迁移到我这里”，不要重新默认成文，直接进入 inquiry。缺少上游 `claim ledger` 时，先做轻量 review 或要求用户提供上游输出。
