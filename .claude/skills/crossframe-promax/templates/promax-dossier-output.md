# Dossier 生成合同

产物：`promax-dossier.md`
生成阶段：`P10`
冻结输入：P0–P9 当前工件

Dossier 是本轮推演的可审计总档案，不是最终 essay 的摘要，也不是字段转储。使用完整中文说明每个结构选择如何由上游工件约束；所有 claim、证据、机制、路径、反方和判断都保留稳定 ID 与来源引用。

## 固定章节

1. `# ProMax v8 推演档案`
2. `## 运行与事实边界`：run 状态、对象边界、尺度、时间窗、evidence cutoff、能力缺口、已知/报告/推断/未知的分界。
3. `## Local world`：行动者、圈层候选、M/Ψ 双通道、时钟、事件、identity criteria、residuals、action/authorization limits。
4. `## 概念处置总览`：四类终态计数、required routes、neighbor closure、applied concepts 的章节去向；不能用计数代替 atlas。
5. `## Claims 与竞争机制`：逐条写出全部 claim ID 和完整 statement；说明中心 claim、默认三个竞争机制、区分条件及简单基线。
6. `## 路径与前瞻条件`：按 DAG 写触发、早期信号、反向信号、停止点、writeback、forecast conditions 和 choice boundary。
7. `## 检索前沿`：按每个 claim 汇总五个 direction、来源独立性、支持/反驳关系、不能证明什么及最后两轮饱和证据。
8. `## Red-team 与修订`：逐类说明攻击、最强反方、结果、实际修订和成对立场稳定性；不能只列 attack IDs。
9. `## 冻结立场`：完整携带 position、判断强度、主要理由、runner-up、最强反证、为何不采纳、撤回条件和 action ceiling。
10. `## 方案比较`：仅在 recommendation 被请求时，逐项比较六类方案、评价维度、排序、首选、次选、切换、不行动后果、授权、停止与回滚。
11. `## 未完成项与续跑`：列出 capability gaps、unknown_pending、unexpanded branches、待补真实事实和 continuation 入口；没有未完成项时说明验证所证明的闭包范围。

## 交叉绑定

- 全部 claim statements 必须至少出现在 dossier 或 essay；中心 claim 两者都应直接表达。
- Applied concepts 的精确定义与逐概念解释放在 atlas 和 essay，dossier 只汇总并链接 SECTION IDs。
- 机制案例的全文放在 case/countercase；dossier 说明案例为何能或不能区分机制。
- 建议未被请求时，dossier 不得生成方案 ID、首选或推荐语言。
- 能力不可用、来源不足或未完成分支必须写成结构化不完整，不能伪装成严格完成。

## 文字质量

每节至少回答“当前判断是什么、依据是什么、竞争解释是什么、什么会改变它”。使用连续论述连接字段，不用 marker、散列或术语数量冒充语义。不得披露私密推理过程、工具试错和自由聊天记忆。
