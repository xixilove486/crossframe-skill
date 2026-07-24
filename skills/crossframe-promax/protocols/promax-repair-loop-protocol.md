# ProMax 验证与局部修复协议

本协议规定 `artifact-validation` 失败后的确定性 `repair-loop`。validator 是完成状态的唯一裁决入口；不得通过改报告、补 marker、删工件或整轮自由重写绕过失败。

## 目录

1. [验证入口](#验证入口)
2. [状态与退出码](#状态与退出码)
3. [机器错误合同](#机器错误合同)
4. [生成 repair plan](#生成-repair-plan)
5. [确定最早重置点](#确定最早重置点)
6. [append-only reset](#append-only-reset)
7. [按阶段局部修复](#按阶段局部修复)
8. [manifest 与 continuation 重建](#manifest-与-continuation-重建)
9. [重新验证](#重新验证)
10. [能力缺口与 continuation](#能力缺口与-continuation)
11. [禁止绕过](#禁止绕过)
12. [修复完成清单](#修复完成清单)

## 验证入口

从仓库根目录运行 canonical checker：

```text
python skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py --workspace <工件目录> --repo <仓库根目录> --write-report --json
```

需要同时验证最终聊天投影时加入 `--final-chat`，并在工件目录提供固定名称 `promax-final-chat.json`。最终聊天验证不能替代完整输出验证。

验证前要求：

1. run directory 是现有普通目录，不是软链接目标。
2. 固定文件名与 schema 一致。
3. P0-P10 当前状态已写入 `promax-phase-events.jsonl`。
4. manifest 在所有分析工件之后生成。
5. continuation ledger 绑定当前 manifest。
6. validator report 不作为同次验证输入。

不要在运行 checker 的同时修改工件。验证过程中发生文件变化时，结果不可信，重新生成 manifest 后再运行。

## 状态与退出码

checker 返回机器 JSON，并使用：

- 退出码 `0`：`overall_status=pass`；
- 退出码 `1`：`overall_status=fail` 或调用无效；
- 退出码 `2`：`overall_status=blocked`，通常是 artifact run 的诚实能力缺口。

`completion_status` 只能由 checker 推导。常见状态：

- `promax-complete`
- `promax-artifact-run`
- `promax-design-review`
- `promax-artifact-incomplete:validation-failed`
- `promax-artifact-incomplete:<能力缺口集合>`

不要把 process exit code、模型自评或文件存在性单独当作完成证明。读取 JSON 中的 failures、capability gaps、anomalies、validator report 和 repair plan。

## 机器错误合同

每条 failure 必须恰好包含：

1. `error_type`
2. `artifact`
3. `affected_phase`
4. `downstream_reset`
5. `repair_action`

把它们视为不可随意改写的机器合同：

- `error_type` 指明失败类别；
- `artifact` 指明首个检测到问题的工件；
- `affected_phase` 指明最早语义责任阶段；
- `downstream_reset` 是必须失效的有序阶段集合；
- `repair_action` 规定局部修复责任。

同一根因可能造成多个下游错误。先处理最早 affected phase，不要逐条在下游补表面症状。保留完整 failure 集供重验审计。

validator report 必须绑定当前 run、request、snapshot、phase chain head、manifest、validator set、validation attempt 与当前工件 hashes。陈旧报告、另一个 run 的报告或重复 attempt 不能复用。

## 生成 repair plan

checker 在可构建时直接返回结构化 `repair_plan`。把该对象不加修改地持久化为 `promax-repair-plan.json`。

若需要从已有失败报告和独立 failures 数组重建，使用实际 CLI：

```text
python skills/crossframe-promax/scripts/build_crossframe_promax_repair_plan.py --failed-report <失败报告.json> --failures <失败数组.json> --output <工件目录绝对路径>/promax-repair-plan.json
```

输入报告与 failures 文件必须是不同的普通文件；输出必须是绝对路径，不能覆盖任何审计输入，也不能是符号链接。

repair plan 必须符合 `promax-repair-plan.schema.json`，并包含：

- run 与 source snapshot 绑定；
- failed report hash；
- 规范化 failures；
- `reset_from_phase`；
- invalidated phases；
- repair actions；
- `validation_state=not_run`；
- `manifest_regeneration_required=true`；
- `revalidation_required=true`；
- `revalidation_scope=full`。

不要手工把 `validation_state` 写为 passed。repair plan 只授权修复，不证明修复完成。

## 确定最早重置点

在全部 failures 中按 `P0` 到 `P11` 选择最早 `affected_phase`，设为 `reset_from_phase`。失效该阶段和所有下游活动阶段。

示例责任边界：

| 失败 | 最早责任阶段 |
| --- | --- |
| run binding、能力合同错误 | `P0` |
| source snapshot、read coverage、内容 hash 错误 | `P1` |
| worldview capsule 未绑定完整读取 | `P2` |
| 对象、事件、证据或授权边界错误 | `P3` |
| registry、route、neighbor 或误用闭包错误 | `P4` |
| claim cycle、机制、路径或写回错误 | `P5` |
| 五向检索、来源独立性或饱和错误 | `P6` |
| 反方攻击或立场诱导稳定性错误 | `P7` |
| position、recommendation 或授权泄漏 | `P8` |
| output plan 覆盖错误 | `P9` |
| 长文语义、typed example、manifest 或 continuation 错误 | `P10` |
| validator report 重放或最终聊天错误 | `P11` |

具体 failure 的 `affected_phase` 优先于本表。本表只帮助理解，不覆盖 checker 输出。

## append-only reset

不得删除或重写历史 phase events。执行：

1. 读取并验证当前 `promax-phase-events.jsonl`，构造 `PhaseState`。
2. 确认 `reset_from_phase` 是当前活动完成阶段。
3. 调用 `build_reset_event(state, reset_from_phase, reason=<机器错误摘要>)`。
4. 调用 `append_phase_event` 原子追加 reset event。
5. 再次调用 `validate_phase_history`，确认该阶段及全部下游失效，前序阶段仍活动。
6. 保留旧工件文件用于审计，但在新 inventory 中标为 invalidated 或 superseded；不要让它们继续成为 current 输入。

如果失败只影响 P11 外部报告而 P10 工件仍新鲜，不需要重置 P10。丢弃陈旧报告并重新运行 validator；仍须保持 validation state 为 not_run，直到新验证结束。

## 按阶段局部修复

从 reset point 读取仍活动的最近上游冻结工件，执行 repair actions：

### P0-P2

- P0：重新初始化新的 run；不可在原 run 内改变 request、nonce 或 snapshot 绑定。
- P1：重新验证 source 与 knowledge，重建缺失或错误的 read events，重新检查全部覆盖。
- P2：只从已验证 read coverage 重建 worldview capsule。

### P3-P5

- P3：修正对象、身份、尺度、时钟、事件、证据或授权边界。
- P4：重新遍历全部 registry，修复 route/neighbor closure、处置理由和误用排除。
- P5：重建受影响 claims、真正不同的机制、无环路径、信号、停止点与 writeback。

### P6-P8

- P6：补运行缺失的检索方向，修正 URL、来源类型、同源关系、cannot prove 和饱和轮。
- P7：重新执行具体 attack、最强反方与成对姿态稳定性检查；把新证据写回上游状态。
- P8：在更新后的 red-team 后重新锁定 position 与所需 recommendation，检查排序和授权上限。

### P9-P10

- P9：重新映射全部 applied concepts、claims、mechanisms、paths、examples、countercases、position 与 recommendation。
- P10：只重写受影响章节，但重新运行四份长文的整体语义检查；更新 typed examples、continuation index、manifest 与 continuation ledger。

每个重跑阶段通过 `seal_phase_event` 与 `append_phase_event` 生成新的活动 hash。不要把旧 event hash 复制到新事件。

## manifest 与 continuation 重建

任何 current 工件发生改变后：

1. 从真实文件字节重新运行 `inventory_artifacts`。
2. 只把当前分析工件放入 manifest；排除 run contract、phase events、manifest 自身、continuation ledger、validator report、repair plan 与 final-chat 投影。
3. 用当前活动 P10 chain head、role records 与新 inventory 调用 `build_artifact_manifest`。
4. 最后写 `promax-artifact-manifest.json`。
5. 重新生成 `promax-continuation-ledger.json`，绑定新的 `manifest_sha256`。
6. 若 continuation index 内容改变，它先进入 inventory，再生成 manifest；不能在 manifest 后修改。

旧 manifest 与 continuation 父状态不能沿用。仅更新时间戳而不更新内容 hash 也不能修复 stale manifest。

## 重新验证

局部修复后始终执行全量 revalidation：

```text
python skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py --workspace <工件目录> --repo <仓库根目录> --write-report --json
```

原因：局部修复只限制重建范围，不能缩小最终证明范围。全量 validator 要重新检查源覆盖、状态机、闭包、语义、manifest、continuation 和重放防护。

重新验证前确认：

- repair plan 仍绑定同一 run 和 snapshot；
- validation state 处于 not_run；
- manifest 已重新生成；
- validator report 输出路径安全；
- validation attempt 严格递增；
- checker 输入中没有上一次 report。

新报告失败时生成新的 repair plan，选择新 failure 集中的最早 affected phase。不要在同一 repair plan 上反复改写失败历史。

## 能力缺口与 continuation

`promax-artifact-run` 在真实能力缺口下可以返回 blocked/incomplete，并保留可用长文。执行：

1. 把缺口登记为稳定的 lowercase identifier。
2. 标出受影响 claim、检索方向、例子和完成 gate。
3. 降低依赖缺失能力的结论强度。
4. 保存已经完成的 dossier、atlas、case/countercase 和 essay。
5. 在 continuation ledger 中登记恢复所需能力、下一阶段或 section 与当前 manifest 父状态。
6. 能力恢复后先验证 parent manifest，再继续修复。

上下文、token、调用次数或时间不足不等于现实已穷尽。把剩余工作写入 continuation，不把未完成状态改成 complete。

## 禁止绕过

严禁：

- 只补测试 marker、概念 ID 或固定短语；
- 用字符数或 essay/dossier 比例代替语义覆盖；
- 编辑 validator report 的 status、hash 或 checks；
- 删除失败项后重新提交相同工件；
- 复用另一个 run、旧 manifest 或旧报告；
- 让 continuation 指向非当前 manifest；
- 直接覆盖上游 locked artifact 而不 reset；
- 整轮自由重抽以掩盖最早根因；
- 因 validator 失败而删除已有完整长文；
- 把能力缺口、材料不足或网络失败写成自行选择的轻量档。

异常字符串、空反例、伪 read ledger、重复来源、错误 phase transition、授权泄漏和 marker stuffing 都必须由对应阶段的实质修复解决。

## 修复完成清单

- [ ] canonical checker 已产生完整机器 failure 合同。
- [ ] repair plan 绑定当前 run、snapshot 与失败报告。
- [ ] reset point 是全部失败中最早 affected phase。
- [ ] reset event 已 append-only 写入且状态机验证通过。
- [ ] 只重建 reset point 及下游，没有改写仍有效上游。
- [ ] 每项 repair action 都有对应的语义或数据修复。
- [ ] current 工件重新散列，旧工件状态明确。
- [ ] manifest 在所有 current 分析工件之后重建。
- [ ] continuation ledger 绑定新 manifest。
- [ ] validation state 在重验前为 not_run。
- [ ] 全量 validator 已重新运行，attempt 递增且报告 fresh。
- [ ] final chat 只投影新报告允许的状态和工件入口。

只有清单全部满足且新 validator report 通过，repair-loop 才结束。
