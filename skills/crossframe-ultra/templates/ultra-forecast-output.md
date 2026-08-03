# Ultra 预测台账输出

本模板用于 U9 冻结原始 forecast。原始台账在结果揭晓前不可变；后续结果只能追加为独立、已验证的 resolution event，不能重写初始判断。

| forecast | direction | indicator | window | branch / node | status |
|---|---|---|---|---|---|
| 待填 | 待填 | 待填 | 待填 | 待填 | frozen |

## 解析合同

每条预测记录 evidence cutoff、window start、window end、resolution rule 与可机械执行的 predicate。方向、baseline、target 和 tolerance 必须相容。

## resolution

初始 materialization 不创建 resolution。结果存在后，resolution 只记录观测值、来源、解析时间和 supported、refuted 或 unresolved 结论，并保持对原 forecast hash 的绑定。

概率只有在 reference class、calibration basis 与 probability admissible 合同全部满足时才可填写；否则保留方向性预测。
