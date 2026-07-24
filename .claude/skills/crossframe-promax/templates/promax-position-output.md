# Position lock 生成合同

产物：`promax-position.locked.json`
生成阶段：`P8`
Schema：`promax-position.schema.json`

`schema_id` 固定为 `crossframe.promax.v8.position`，`schema_version=1`。根对象只包含 `schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`central_claim_id`、`relation_to_proposition`、`proposition_verdict`、`position`、`judgment_strength`、`primary_reasons`、`runner_up_explanation`、`strongest_counterevidence`、`why_not_adopted`、`withdrawal_conditions`、`action_ceiling`、`locked_at`。

## 锁定规则

- `central_claim_id` 必须与 claim graph 和 red-team report 完全一致。
- `relation_to_proposition` 只能是 `supports`、`rejects`、`mixed`、`indeterminate`；它是 ProMax 的成对比较控制字段，不冒充 v8 root-instance 状态。
- `proposition_verdict` 必须精确等于 `VERDICT[<relation_to_proposition>] <中心 claim statement>`，例如 `VERDICT[rejects] 所有此类组织一定会崩溃`。它是机器可比的权威裁决前缀，不得用同一 prose 标签容纳相反结论。
- `position` 是当前最佳、可撤回的明确判断，必须以完整 `proposition_verdict` 开头，再给出自然语言解释；正文不得反向改写该裁决。
- `judgment_strength` 只能是 `tentative`、`moderate`、`strong`、`indeterminate`，并与 red-team stability 的 after 状态相等。
- `primary_reasons` 至少一项，分别说明 v8 合同、证据、机制区分、路径信号与攻击承受力；不得只重复 position。
- `runner_up_explanation` 必须点名 claim graph 中一个非领先机制的精确 label，并解释它在何种条件下成为次优或反超；只有标签不合格。

## 最强反方绑定

1. 在 red-team attacks 中按 `position_impact` 找到最高影响攻击。
2. 把该攻击的 `strongest_counterposition` 纳入 `strongest_counterevidence`，保持语义与可追溯引用。
3. `why_not_adopted` 必须直接回应该反方的关键机制或证据，而不是泛称“证据不足”。
4. `withdrawal_conditions` 至少一条逐字绑定最强反方，并同时包含条件触发与撤回、调整或降级动作。
5. 若最强攻击为 `survived_with_revision`，其 `revision` 必须出现在 `primary_reasons` 或 `withdrawal_conditions`。

## 授权边界与时间

`action_ceiling` 必须明确“仅作分析”“不授权”或“需要另行授权”的边界，不能含自我授予现实行动权限的表达。预测强度、建议排序和用户要求都不能抬高授权上限。

`locked_at` 必须严格晚于 `red-team-report.completed_at`；red-team 不得早于 claim graph。写盘后执行 `validate_position_semantics()`，确认中心 claim、最强攻击、runner-up、稳定性状态和行动上限均闭合。
