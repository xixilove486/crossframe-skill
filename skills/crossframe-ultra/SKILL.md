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

<!-- ULTRA-ACTIVATION-NOT-PAYLOAD -->
精确点名只限制 Ultra 的外部激活，不限制问题载荷。宿主确认激活并加载本 skill 后，用户可以直接提交普通自然语言问题；不要要求用户重复 Ultra 名称，也不要把问题强制改写成 JSON。

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

执行脚本与 `--repo` 必须来自同一棵已安装树：正式仓库相对路径为 `skills/crossframe-ultra/scripts/crossframe_ultra_runtime.py`，Windows 路径位于 `<repo>\skills\crossframe-ultra\scripts\crossframe_ultra_runtime.py`，`--repo` 必须逐字传入对应的 `<repo>`。Codex 使用 `C:\Users\cangm\.codex`；Reasonix 使用 `C:\Users\cangm\.agents`；Claude 使用 `C:\Users\cangm\.claude`。禁止用一棵安装树的脚本搭配另一棵树或 canonical source 的 `--repo`。

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
11. `references/host-adapter-contract.md`
12. `references/source-manifest.json`、`references/release-manifest.json` 与 `references/compatibility-matrix.json`
13. `references/v8.2-route-map.json`、完整 concept registry、contract map 与被路由的晋升源单元

索引只负责定位。逐项读取覆盖、来源散列、全注册表处置和 validator 才能证明闭合；不要用术语出现次数代替执行。

## Runtime command boundary

只通过 `<repo>\skills\crossframe-ultra\scripts\crossframe_ultra_runtime.py` 的固定接口调用 `start`、`prepare`、`checkpoint`、`materialize`、`validate`、`repair-plan`、`resume`、`fork`、`evidence-fork`、`cancel`、`rebuild-index`，并让同一命令的 `--repo` 指向这个 `<repo>`。逐字使用 `references/runtime-routing-map.md` 中的签名。

普通 UTF-8 自然语言 request bytes 是合法 fresh 输入，默认进入 `analysis_kind=open-world`。`closed-input` 是特殊分支：只有用户明确要求仅依据其提供的材料，且至少一份独立、非空材料已由 runtime inventory 和 material-universe hash 封存时，才使用 canonical envelope：

```json
{"analysis_kind":"closed-input","claim":"待判断的非空命题或问题","material":"本次运行的完整非空封闭材料"}
```

这里的 envelope 仍只是不可变输入，不是 authority。用户问题不能同时复制成 `claim` 与虚构的完整 `material` 来取得 closed-input 资格；不能独立证明 `closed-input` 或 `pure-logic` 时保持 open-world。不得加入或自填 run ID、版本、散列、敏感级别、能力、读取凭据、检索结论、证据 ID、phase event 或 checkpoint。

`start` 独立封存 request intake authority；`prepare` 幂等返回当前唯一 `recovery/pending-action.json`、固定 result slot 或 model-owned authoring slot。宿主按 action 执行 `capability-attestation`、`source-read`、`retrieval`、`subagent`、`evidence-authoring` 或 U11 的 `semantic-review`：必须调用真实宿主工具，把 receipt 或语义工件只写到指定 slot，再调用 `materialize` 让 runtime 验证、接纳、封存并发行下一步。具体翻译规则见 `references/host-adapter-contract.md`。

`semantic-review` 只提供 action-bound reviewer identity 与九维判断；runtime 负责正式工件 envelope 和 publication disposition，且该判断不能覆盖 deterministic 或 adversarial failure。

联网、读源和 subagent 只能在 pending action 与 U0 权限内真实执行。subagent 输出和其它模型生成内容先是 untrusted `candidate`，不是证据；只有来源验证并经 U3 admission 接纳后才能进入证据账本。不得把候选、模拟、预测或用户问题改标为已观察事实。

`outcome=awaiting-host-action` 与 `outcome=awaiting-authoring` 是 `status=running` 的正常进度：执行唯一 next action 后继续，不得把等待写成 validation failure、`needs_attention` 或异常。若进程在已完成 checkpoint 后中断，只通过 runtime 的 `resume` / `materialize` 恢复；新证据通过 `evidence-fork` 派生 child。不得手工编辑或删除 control、phase event、checkpoint、validation history 或 lease，也不得借手工清理推进运行。

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
