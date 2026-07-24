# Retrieval ledger 生成合同

产物：`promax-retrieval-ledger.json`
生成阶段：`P6`
Schema：`promax-retrieval-ledger.schema.json`

`schema_id` 固定为 `crossframe.promax.v8.retrieval-ledger`，`schema_version=1`。根对象只包含 `schema_id`、`schema_version`、`run_id`、`source_snapshot_sha256`、`entries`、`saturation_rounds`、`network_available`、`completed_at`。

## 每个 required claim 的五向闭包

每个 claim graph 中的 claim ID 都必须分别覆盖：

- `support`，关系为 `supports`、`mixed` 或 `contextual`；
- `reverse`，关系为 `refutes`、`mixed` 或 `contextual`；
- `failure`，关系为 `refutes`、`mixed` 或 `contextual`；
- `alternative_mechanism`，关系必须为 `alternative_mechanism`；
- `affected_or_low_power`，关系必须为 `affected_position`。

不能用五条只绑定中心 claim 的记录冒充全 claim 覆盖。

## 每条 `entries[]`

闭合字段为 `retrieval_id`、`round`、`direction`、`claim_relation`、`query`、`tool`、`retrieved_at`、`sources`、`claim_ids`、`finding`、`cannot_prove`、`stop_reason`。

- `retrieval_id` 使用唯一 `RETRIEVAL-*`；`round` 从 1 开始并指向已登记饱和轮次。
- `query` 保存实际查询式，`tool` 保存实际工具，`retrieved_at` 使用带时区时间；不得把模型记忆登记为刚完成的检索。
- `claim_ids` 非空且只指向 graph 中已有 claims。
- `finding` 说明检索结果如何支持、反驳、限定或替代目标 claim。
- `cannot_prove` 非空，逐项写清不能由当前来源推出的因果、范围、概率、跨尺度结论或现实授权。
- `stop_reason` 只解释本条查询为何停止，不代替全局饱和证明。

## 每个来源

`sources[]` 的闭合字段为 `url`、`title`、`publisher`、`published_at`、`event_date`、`source_type`、`interest_relevance`、`independence_group`、`duplicate_relation`、`duplicate_of_url`。

- `url` 必须是可回查的绝对 HTTP(S) 地址；同一规范 URL 只能出现一次。
- `source_type` 只能是 `primary`、`official`、`research`、`journalistic`、`first_person`、`secondary`。
- `published_at` 与 `event_date` 分开填写，均为完整日期。
- `interest_relevance` 说明来源生产者、资助者、发布者或被影响位置与 claim 的利益关系。
- `duplicate_relation=independent` 时 `duplicate_of_url=null`；`same_origin`、`syndicated`、`derived`、`duplicate` 必须指向 ledger 内已有 URL，并使用同一 `independence_group`。

## 饱和轮次

每条 `saturation_rounds[]` 只含 `round`、`substantive_novelty`、`changed_claim_ids`、`stop_reason`。轮次必须从 1 连续编号且每轮实际有查询。最后连续两轮必须同时满足：

- `substantive_novelty=false`
- `changed_claim_ids=[]`
- `stop_reason` 说明对 claim、概念状态、判断强度、路径排序、行动上限和阻断性反例均无实质新增

## 能力与完成状态

`network_available` 必须与 run contract 完全一致。网络可用时每条 entry 至少一个真实来源；网络不可用时如实保留空来源和能力缺口，继续条件化分析，但依赖现实事实的 claims 降档，且不能通过严格完成门。

写盘前阅读 `references/retrieval-policy.md`，再过 schema、`validate_retrieval_saturation()` 与来源独立性检查。
