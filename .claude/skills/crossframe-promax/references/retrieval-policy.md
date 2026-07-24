# ProMax 外部检索政策

外部资料用于检验事实、机制、案例和反例，不是 v8 概念定义的来源。概念名、定义、前提、禁用替代、邻接关系和行动上限只从当前冻结的 v8 registry、contracts、routes 与全源锚点取得。

## 必须检索的情形

- 请求涉及现实机构、人物、政策、法律、平台规则、技术标准、历史事件或可能变化的当前事实。
- claim 需要真实案例、频率、时序、结果或失败条件才能升格。
- 用户要求最优选择，而方案排序依赖外部成本、风险、权限或可逆性。
- red-team 需要寻找反向证据、替代机制或低可见位置的受影响者材料。

若事实稳定性无法确认，按需要实时检索处理。引用必须直接支持相邻主张；优先原始、官方和研究来源，并分开记录事件日期与发布日期。

## 五向闭包

每个 required claim 都必须覆盖五个 `direction`，且 `claim_relation` 与方向相容：

| `direction` | 允许的 `claim_relation` | 检索目的 |
| --- | --- | --- |
| `support` | `supports`、`mixed`、`contextual` | 找到对当前机制最有力的支持及其边界 |
| `reverse` | `refutes`、`mixed`、`contextual` | 主动寻找相反结果、反向时序或未发生结果 |
| `failure` | `refutes`、`mixed`、`contextual` | 寻找机制失效、干预失败或外推失败 |
| `alternative_mechanism` | `alternative_mechanism` | 检索能解释同一现象的竞争机制 |
| `affected_or_low_power` | `affected_position` | 检索受影响、低权力或低可见位置的材料 |

不得只给中心 claim 做五向检索而遗漏其它 required claims。一次查询可以绑定多个 claim，但必须逐项保留 `claim_ids` 和实际关系。

## 每条查询必须保存

- `retrieval_id`、连续 `round`、`direction`、`claim_relation`。
- 实际 `query`、真实 `tool`、`retrieved_at`、目标 `claim_ids`。
- `finding`、明确的 `cannot_prove` 列表和本次 `stop_reason`。
- 每个来源的 HTTP(S) `url`、`title`、`publisher`、`published_at`、`event_date`、`source_type`、`interest_relevance`、`independence_group`、`duplicate_relation`、`duplicate_of_url`。

`cannot_prove` 必须写出来源无法证明的因果、普遍性、概率、授权或跨尺度外推，不得把免责声明写成空泛句。

## 来源独立性

1. 同一规范 URL 只能登记一次；忽略 URL fragment，并规范化 scheme、host 和默认端口。
2. `independent` 的 `duplicate_of_url` 必须为 `null`。
3. `same_origin`、`syndicated`、`derived`、`duplicate` 必须指向 ledger 内已经登记的真实 URL，并保持同一 `independence_group`。
4. 同一 host 与同一路径、查询的来源不能伪装成独立来源。
5. 聚合稿、转载稿和基于同一数据集的二次报道不能作为多份独立证据计数。

## 案例标型

- `real_case`：有可回查外部来源，且正文说明来源能证明与不能证明什么。
- `user_material`：只来自用户材料，不冒充外部事实。
- `conditional_scenario`：明确写出若何条件成立才成立。
- `structural_analogy`：只比较结构关系，不声称现实事实相同。

真实案例不足时，以后两类补充解释，但不能伪造现实案例。外部案例与 v8 定义冲突时，案例只能改变事实判断或适用条件，不能改写定义。

## 饱和与停止

`saturation_rounds` 从 1 连续编号；每一轮必须至少有一条同轮查询。最后连续两轮都必须满足 `substantive_novelty=false` 与 `changed_claim_ids=[]`。实质新增是足以改变 claim、概念处置、判断强度、路径排序、行动上限或引入阻断性反例的信息。

停止理由必须说明查询边界与无新增结果，不能只写“已经充分”。调用次数、篇幅或时间耗尽不等于饱和；容量不足时建立 continuation。

## 能力缺口

`network_available` 必须与 run contract 同值。网络可用时每条查询至少保留一个真实来源；网络不可用时仍执行结构分析和条件分支，来源数组可以为空，但真实案例依赖的 claim 必须降档，并且不能宣布 `promax-complete`。不得把模型记忆写成刚刚检索的来源。
