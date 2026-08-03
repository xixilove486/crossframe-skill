# Ultra 运行状态输出

本模板用于解释权威运行状态，不替代 runtime 写入的 run-status.json。run_id、状态迁移、revision、时间戳和验证结果必须来自已验证的运行布局与状态存储，模型不得自行改写。

## 运行标识与阶段

| 字段 | 当前值 | 说明 |
|---|---|---|
| run_id | 待 runtime 绑定 | 固定根内的中性运行标识 |
| status | 待 runtime 绑定 | created、running 或其它权威状态 |
| current phase | 待 runtime 绑定 | 当前 U0–U12 phase |
| last complete phase | 待 runtime 绑定 | 最近完成且散列闭合的阶段 |

## validation

记录 validation 是否通过、对应报告散列以及尚未通过的错误代码。只有 U12 新鲜检查通过后，状态才能进入 complete。

## continuation

continuation 只说明能否从最后一个已验证边界继续，以及 continuation entry 的绝对运行路径或空值。cancelled、failed 与 complete 状态不得暗示仍可继续写入。
