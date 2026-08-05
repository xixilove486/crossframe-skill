---
name: crossframe-ultra
description: "Use only when the user explicitly invokes crossframe-ultra, CrossFrame Ultra, $crossframe-ultra, or /crossframe-ultra; reject generic maximum, full, or Ultra-analysis wording."
---

# CrossFrame Ultra Skill

把本 skill 作为《跨尺度多圈层结构推演框架 v8.2》已构建、已验证、已晋升快照的薄执行控制器。运行完整 U0–U12，保存可验证工件，形成当前最佳判断，并只在 U12 通过后发布一篇可独立阅读的中文文章。详细语义留在权威快照、注册表、合同、协议和 schema 中；不要在本入口复写理论正文。

## Activation contract

<!-- ULTRA-EXPLICIT-ONLY -->
只接受下列四种宿主已确认的显式形式：

<!-- ULTRA-ACCEPTED-FORMS-BEGIN -->
- `crossframe-ultra`
- `CrossFrame Ultra`
- `$crossframe-ultra`
- `/crossframe-ultra`
<!-- ULTRA-ACCEPTED-FORMS-END -->

以下表达都是拒绝触发的 near-miss；“领域通用”不等于允许隐式调用：

<!-- ULTRA-NEAR-MISSES-BEGIN -->
- `最大化`
- `最完整`
- `Ultra 分析`
- `maximum`
- `full`
<!-- ULTRA-NEAR-MISSES-END -->

<!-- ULTRA-NO-SUITE-UPGRADE -->
`crossframe-suite` 不得自动升级到 Ultra。<!-- ULTRA-NO-REVIEW-CHAIN --> Ultra 不串联 `crossframe-review`。<!-- ULTRA-NO-FALLBACK --> Ultra 失败、阻断或材料不足时不得回退到 Max 或 ProMax，也不得改成交谈短答。

<!-- ULTRA-MULTI-RUNTIME-CONFIRM -->
若用户明确要求比较 Ultra 与另一个 runtime，先分别独立运行 Ultra 和被比较 runtime，再比较各自结果；若同一请求同时明确点名多个 runtime 但未提出比较，暂停确认本次选择哪个 runtime。两种分支互斥；不要用优先级吞掉用户意图，也不要把并列点名擅自改写为比较。

宿主已经加载本 skill 时，不要再次要求用户重复名称；直接执行 U0，并记录显式路由证据。

## Authority and fixed roots

<!-- ULTRA-PROMOTED-V82-ONLY -->
唯一理论权威是 canonical tree 中已构建、已验证、已晋升的 v8.2-r1 语义快照、概念注册表、合同和路由。拒绝 v8.0、文件名推测的“最新版本”、外部摘要或运行时生成内容成为理论权威。

<!-- ULTRA-NO-THEORY-SELF-AMENDMENT -->
运行不得修改、增补或“优化” v8.2 定义。<!-- ULTRA-NO-HIDDEN-THEORY --> 不得把新增理论藏进写作偏好、内部规则或其它未晋升材料。发现框架缺口时只登记候选。

固定位置为：

- canonical source：`E:\世界模型\skill\crossframe-skill\skills\crossframe-ultra`
- Codex install：`C:\Users\cangm\.codex\skills\crossframe-ultra`
- Reasonix install：`C:\Users\cangm\.agents\skills\crossframe-ultra`
- Claude install：`C:\Users\cangm\.claude\skills\crossframe-ultra`
- production root：`E:\世界模型\output\crossframe-ultra`
- test root：`E:\世界模型\output\crossframe-ultra-tests`

固定根不可用、不可安全解析或不可写时失败关闭。生产与测试根不得互换，不得回退到当前目录、临时目录、源码目录或安装目录。

执行脚本与 `--repo` 必须来自同一棵已安装树：脚本位于 `<repo>\skills\crossframe-ultra\scripts\crossframe_ultra_runtime.py`，`--repo` 必须逐字传入对应的 `<repo>`。Codex 使用 `C:\Users\cangm\.codex`；Reasonix 使用 `C:\Users\cangm\.agents`；Claude 使用 `C:\Users\cangm\.claude`。禁止用一棵安装树的脚本搭配另一棵树或 canonical source 的 `--repo`。

## Required reads

依次读取并执行：

1. `protocols/ultra-source-authority-protocol.md`
2. `protocols/ultra-runtime-protocol.md`
3. `protocols/ultra-world-volume-protocol.md`
4. `protocols/ultra-recursive-inference-protocol.md`
5. `protocols/ultra-judgment-protocol.md`
6. `protocols/ultra-article-protocol.md`
7. `protocols/ultra-safety-recovery-protocol.md`
8. `protocols/ultra-validation-repair-protocol.md`
9. `references/runtime-routing-map.md`
10. `references/retrieval-policy.md`
11. `references/source-manifest.json`、`references/release-manifest.json` 与 `references/compatibility-matrix.json`
12. `references/v8.2-route-map.json`、完整 concept registry、contract map 与被路由的晋升源单元

索引只负责定位。逐项读取覆盖、来源散列、全注册表处置和 validator 才能证明闭合；不要用术语出现次数代替执行。

## Runtime command boundary

只通过 `<repo>\skills\crossframe-ultra\scripts\crossframe_ultra_runtime.py` 的固定接口调用 `start`、`prepare`、`checkpoint`、`materialize`、`validate`、`repair-plan`、`resume`、`fork`、`cancel`、`rebuild-index`，并让同一命令的 `--repo` 指向这个 `<repo>`。逐字使用 `references/runtime-routing-map.md` 中的签名。

fresh CLI 运行只接受宿主根据已确认用户材料构造的 canonical closed-input envelope：UTF-8、无 BOM、键排序、紧凑分隔符、末尾一个 LF，且字段只能是 `analysis_kind`、`claim`、`material`。固定形状为：

```json
{"analysis_kind":"closed-input","claim":"待判断的非空命题或问题","material":"本次运行的完整非空封闭材料"}
```

这里的 envelope 只是不可变输入，不是 authority。不得加入或自填 run ID、版本、散列、敏感级别、能力、读取凭据、检索结论、证据 ID、phase event 或 checkpoint。`start` 会独立封存 runtime-owned request intake authority；之后同时替换 request 与 metadata 仍会被拒绝。`start` 后调用 `prepare`；fresh `materialize` 由 runtime 自动建立并封存 U0–U3，再从 U4 继续。不要写 `U01-read-events.jsonl`、`U02-retrieval-ledger.json` 或 `U03-evidence-ledger.json` 来替代 runtime authority。

若进程在已完成的 U0、U1 或 U2 checkpoint 后中断，下一次 `materialize` 从该 checkpoint 继续，不能重建已封存阶段。若发现没有对应 checkpoint 的下游残留，进入 `needs_attention`，不得覆盖或冒充成功恢复。

选择这个 eligible closed-input 分支即选择冻结的 runtime-owned bootstrap profile：`sensitivity=private`、`retention=retain`、`outbound_permission=deidentified-only`；filesystem、validators、model context 为 `available`，DOCX parser、network、retrieval、subagents 为 `not-applicable`；资源上限沿用已晋升 U0 合同的 `64 / 2 / 3 / 3`。该 profile 不允许 caller 覆盖，也不授权任何外发或现实检索。

只有当用户已提供足够且封闭的材料时才能使用该 envelope。普通自由文本、缺少完整材料或需要现实检索的请求不得伪装为 `closed-input`；当前 runtime 会将该 fresh run 标记为 `blocked` 并失败关闭。此时直接报告边界，不要循环调用 `resume`、`checkpoint`、`materialize` 或搜索隐藏入口。

<!-- ULTRA-NO-ARBITRARY-PATH-FLAGS -->
禁止添加 `--run-dir`、`--authoring-dir`、`--output-root`、`--destination` 或 `--fallback`；也禁止创造任意输出格式、任意目录或跳阶段参数。模型只写 `prepare` 返回且当前分支明确为 model-owned 的 authoring slots；fresh foundation 中 U01–U03 必须不存在，模型 authoring 从 U04 开始。runtime 写身份、版本、散列、阶段、状态、索引、manifest 和正式 delivery。

## U0–U12

严格按固定顺序推进，并保存每阶段的父散列、输入散列、来源散列、状态和下游影响：

<!-- ULTRA-PHASES-BEGIN -->
- `U0`阶段：确认显式触发，冻结问题合同、敏感级别、外发许可、能力和资源边界。
- `U1`阶段：锁定框架、runtime、schema、工具、输入、固定根和全源读取计划。
- `U2`阶段：判定检索资格并执行，或结构化记录 not-applicable。
- `U3`阶段：冻结证据、来源谱系和截止时间；新证据只能派生新运行。
- `U4`阶段：建立完整初始联合状态体 Ω0。
- `U5`阶段：审计尺度、圈层、转义、有效变量、闭合、损失和残差。
- `U6`阶段：建立命题、机制、竞争解释和合格洞察。
- `U7`阶段：生成一至三阶递归状态体和分支谱系。
- `U8`阶段：完成逐阶评价、简单基线、红队、敏感性和合法停止判断。
- `U9`阶段：冻结主判断、五类裁决、行动排序和预测原件。
- `U10`阶段：隔离框架缺口候选，冻结输出计划与语义覆盖责任。
- `U11`阶段：生成全部结构化工件、档案、文章包、partial article 和盲读审校。
- `U12`阶段：从磁盘做新鲜验证、有限局部修复、正式发布和 manifest 封存。
<!-- ULTRA-PHASES-END -->

运行状态只允许：

<!-- ULTRA-RUN-STATES-BEGIN -->
- `created`
- `running`
- `interrupted`
- `blocked`
- `needs_attention`
- `failed`
- `cancelled`
- `complete`
<!-- ULTRA-RUN-STATES-END -->

完整处置 concept registry 的每一项，状态只允许：

<!-- ULTRA-CONCEPT-DISPOSITIONS-BEGIN -->
- `applied`
- `tested-rejected`
- `not-applicable`
- `unknown-pending`
<!-- ULTRA-CONCEPT-DISPOSITIONS-END -->

每项处置必须有请求绑定的独立理由及 schema 所需证据、未知、变换、route、contract 和条件分支；不得批量填默认状态。

全部结构化 authoring slots、依赖顺序和 Task 11/Task 13 模板映射以 `references/runtime-routing-map.md` 为唯一执行地图。只交付一篇正式主文章：`delivery\CrossFrame-Ultra-完整文章.md`。

<!-- ULTRA-FRAMEWORK-GAP-NEXT-RUN-ONLY -->
U10 的 framework-gap candidates 与其派生内容不得影响当前运行的状态、排序、裁决、行动或文章；只有经框架构建—验证—晋升后，未来的新运行才能使用。

## Validation, repair, and final chat

<!-- ULTRA-FRESH-VALIDATION-REQUIRED -->
authoring 完成后，从磁盘启动不参与生成正文的新鲜 validator。失败只重置最早受影响阶段及下游，保留有效上游散列；最多执行协议允许的有限修复次数。不得改报告、补 marker、跳过失败项或整轮覆盖来伪装通过。

<!-- ULTRA-NO-EARLY-FINAL -->
U12 全部通过前，禁止输出最终回答、`complete`、正式文章文件名或任何成功含义；只报告权威运行状态与恢复入口。不得把未运行 validator 写成 validation failure。

最终聊天只逐值投影已验证的 `final-chat.json` 六个字段：

<!-- ULTRA-FINAL-CHAT-FIELDS-BEGIN -->
- `run_status`
- `center_judgment_summary`
- `key_reversal_conditions`
- `article_path`
- `run_path`
- `continuation_entry`
<!-- ULTRA-FINAL-CHAT-FIELDS-END -->

`article_path` 与 `run_path` 必须是由已验证固定布局推导的绝对路径；不要改写锁定判断，不要用聊天摘要替代完整文章或运行包。
