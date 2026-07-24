# Validator report 生成合同

产物：`promax-validator-report.json`
生成阶段：`P11`
Schema：`promax-validator-report.schema.json`
生成权：确定性检查器

禁止模型直接编写、复制或修补 report。使用：

```text
python skills/crossframe-promax/scripts/check_crossframe_promax_artifacts.py --workspace <工件目录> --repo <仓库根目录> --write-report --json
```

检查器从当前 run contract、phase chain、manifest、实际工件字节和冻结 validator set 构建报告；报告自身不作为同一次验证输入。重复 `--write-report` 时 `validation_attempt` 必须递增。

## 根字段

`schema_id`、`schema_version`、`run_id`、`run_nonce`、`request_sha256`、`source_snapshot_sha256`、`phase_chain_head_sha256`、`manifest_sha256`、`validator_set_sha256`、`validation_attempt`、`current_artifact_hashes`、`checks`、`overall_status`、`completion_status`、`validated_at`、`report_sha256` 全部由检查器生成。

`schema_id` 固定为 `crossframe.promax.v8.validator-report`，`schema_version=1`。`report_sha256` 是移除自身后完整 body 的规范 JSON 散列。

## Check 闭包

每条 check 只含 `validator_id`、`status`、`checked_artifact_paths`、`failure_codes`。冻结 validator set 中每个 ID 必须恰好出现一次：

- `status=pass` 时 `failure_codes=[]`。
- `status=fail` 或 `blocked` 时 `failure_codes` 非空。
- 任一 fail 使 `overall_status=fail`；无 fail 但有 blocked 时为 `blocked`；其余为 `pass`。

`current_artifact_hashes` 必须与 manifest 当前 inventory 完全相等。run nonce、request、snapshot、phase head、manifest 和 validator set 任一不一致都视为 replay 或 stale report。

## Completion status

`completion_status` 可以是 run mode，或 `promax-artifact-incomplete:<具体原因>`。只有全部严格门通过时才能为 `promax-complete`，且此时 `overall_status` 必须为 `pass`。能力缺口、网络不可用、未闭合分支或真实事实不足不能被报告文本覆盖。

报告失败后保留原报告，使用机器 failures 构建 repair plan；不得改 checks、散列或 overall status 来制造通过。
