# Repair plan 生成合同

产物：`promax-repair-plan.json`
生成阶段：`P11` 验证失败之后
Schema：`promax-repair-plan.schema.json`
生成权：确定性 repair builder

禁止手写 reset 范围或直接改 validator report。把失败报告和检查器输出的机器 failures 交给：

```text
python skills/crossframe-promax/scripts/build_crossframe_promax_repair_plan.py --failed-report <失败报告> --failures <机器失败记录> --created-at <带时区时间> --output <repair plan 路径>
```

## 输入 failure 合同

每条 failure 必须且只能含：

- `error_type`：小写稳定标识；
- `artifact`：规范相对路径；
- `affected_phase`：`P0`–`P11`；
- `downstream_reset`：从 affected phase 起的精确后代序列；
- `repair_action`：可执行修复动作。

同一 `error_type`、artifact、phase 组合不得重复，大小写折叠后冲突的路径不得同时存在。

## 根字段

生成器写入：`schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`failed_report_sha256`、`failures`、`reset_from_phase`、`invalidated_phases`、`repair_actions`、`validation_state`、`manifest_regeneration_required`、`revalidation_required`、`revalidation_scope`、`created_at`。

- `schema_id` 固定为 `crossframe.promax.v8.repair-plan`，`schema_version=1`。
- `reset_from_phase` 是全部 failures 中最早的 affected phase。
- `invalidated_phases` 必须是该阶段及其全部后代，顺序与状态机一致。
- `validation_state` 固定为 `not_run`。
- `manifest_regeneration_required=true`、`revalidation_required=true`、`revalidation_scope=full-validator-set`。

## Repair action

每条 action 只含 `action_id`、`phase_id`、`description`、`expected_output_paths`。当前 builder 生成 `REPAIR-1`，从最早阶段局部重跑，重建受影响工件，重新生成 manifest，再执行完整冻结验证集。

执行 repair plan 时追加 reset event，不覆盖旧 phase events。修复源工件而非补关键词；修复后旧 manifest、continuation 绑定与 validator report 均不可复用。
