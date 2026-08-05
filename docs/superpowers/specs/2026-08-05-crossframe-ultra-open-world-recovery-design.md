# CrossFrame Ultra 自然语言与开放证据运行时恢复设计

**状态：** 已批准设计

**日期：** 2026-08-05

**权威语义：** 中文

**目标实现：** `skills/crossframe-ultra/`

**理论权威：** 已晋升的《跨尺度多圈层结构推演框架 v8.2》语义快照

## 1. 决策

CrossFrame Ultra 恢复为可由普通 Agent 宿主执行的参考运行时：用户精确点名 Ultra 后，可以直接提交自然语言问题；宿主按 U0 权限和能力边界读取框架、调用检索工具或 subagent、提交绑定当前运行的结果凭据；runtime 验证并封存 U0–U3 后继续完整 U4–U12 推演。

运行时采用两个正式输入分支：

1. `open-world`：普通自然语言问题的默认 fresh 分支。现实、时效、法律、医疗、金融、政治、产品、政策、制度和当前事实问题默认需要外部检索。
2. `closed-input`：用户明确要求只依据完整给定材料时使用的特殊分支。给定材料构成完整证据宇宙，U2 才可标记 `not-applicable`。

`pure-logic` 保留为独立、严格证明的免检索资格，不从普通自然语言自动宽松推断。无法证明 `closed-input` 或 `pure-logic` 时，默认进入 `open-world`。

本次恢复选择持久化 host-runtime handshake，不采用进程内 callback 作为核心合同，也不允许宿主先检索再把结果伪装成 closed-input。

## 2. 目标与非目标

### 2.1 目标

- 精确点名 Ultra 后，普通自然语言问题可以启动 fresh run 并完成 U0–U12。
- 需要现实证据时，宿主能够真实调用联网检索并把结果绑定到 U2、U3。
- subagent 可以参与来源发现、反例搜索、来源谱系和校准，但不能代替最终裁决。
- 保留现有 request-intake、防篡改、固定根、版本绑定、阶段散列和失败关闭能力。
- 保持 v8.2 概念、合同、来源锚点和完整状态内核不漂移。
- 保持完整推演、明确判断、竞争解释、三阶展开、行动排序和完整文章的表达能力。
- 让预期中的宿主等待成为可恢复状态，而不是靠异常、删除 checkpoint 或手工清 lease 推进。
- 让 validator 同时检查结构完整性、证据身份、支持关系、运行历史和文章质量。

### 2.2 非目标

- 不修改、扩展或重新解释 v8.2 理论。
- 不把框架缺口候选晋升为当前运行的理论权威。
- 不把 Ultra 改成隐式触发；exact-name-only 只约束外部路由，不约束问题载荷必须是 JSON。
- 不在核心 runtime 内绑定某一家宿主的私有 SDK。
- 不声称普通宿主凭据具有不存在的密码学证明。没有提供者签名时，它是可追溯的宿主证明，不是不可伪造的第三方证明。
- 不修改或清理既有完成运行及其法证现场。

## 3. 不可变约束

1. v8.2-r1 的原始 DOCX 散列、规范化语义散列、完整源单元、概念注册表和合同语义保持不变。
2. 用户问题是请求和候选命题，不自动成为外部事实证据。
3. 模型候选、模拟参数、预测、反事实和观察事实保持身份隔离。
4. 现实事实缺少合格证据时降低判断资格或阻断对应事实裁决，不能用空引用绕过。
5. U3 后不得原地添加新证据；新证据只能派生新运行。
6. 只有当前 writer lease owner 可以修改权威状态、phase head、checkpoint 和正式工件。
7. cancel、repair 和 fork 必须留下 append-only 历史，不允许删除既有 phase event、checkpoint 或验证尝试来制造当前自洽。
8. Ultra 失败不得回退到 Max、ProMax、suite 或普通短答。
9. U12 通过前不得发布正式文章或成功含义。

## 4. 四方边界

| 角色 | 权限 | 禁止事项 |
| --- | --- | --- |
| 用户 | 提交问题、材料和明确许可 | 自填 capability、phase、hash、evidence identity 或 runtime authority |
| 宿主 Agent | 读取 runtime action，调用已授权工具，提交结果凭据，完成语义 authoring | 直接改 status、phase event、checkpoint、lease、manifest 或正式 delivery |
| Ultra runtime | 发行 action、验证凭据、构建控制工件、推进状态、恢复与发布 | 代替宿主宣称已读、伪造联网结果、把模型内容当外部事实 |
| fresh validator | 从磁盘重算结构、历史、证据和文章合同 | 参与正文生成、修报告、忽略失败项或用 marker 冒充语义支持 |

宿主适配器只负责把 Codex、Reasonix、Claude 等宿主的真实工具结果翻译为统一凭据。核心 runtime 只认识规范化 action、receipt 和 artifact，不猜测提供者 API。

## 5. 输入与运行画像

### 5.1 请求冻结

`start --request-stdin` 和 `start --request-file` 继续封存原始 request bytes、大小、SHA-256 和独立 request-intake authority。普通 UTF-8 自然语言是合法输入，不要求三字段 JSON。

精确激活形式与用户问题分开记录。激活形式证明路由，request bytes 证明实际问题；两者不能互相替代。

用户提供的附件或长材料复制到运行包固定的 `input/materials/`，由 runtime 生成不可变 input inventory。宿主不得通过任意输出目录参数引用材料。

### 5.2 分支判定

- 普通自然语言默认 `analysis_kind=open-world`。
- `closed-input` 需要用户明确的仅材料边界、至少一份非空材料、完整 input inventory 和 material-universe hash。
- `pure-logic` 需要独立 control-plane basis，且不得命中任何现实检索触发类型。
- 用户问题不能同时充当 `claim` 与虚构的完整 `material` 来取得 closed-input 资格。

分支判定进入 U0 run contract，并绑定 request、run、version 和 evidence cutoff。

## 6. 持久化 host-runtime handshake

每个宿主动作都遵循同一闭环：

`runtime 决策 → runtime 授权 → 固定 action → 宿主执行 → untrusted receipt → runtime 验证与接纳 → phase seal`

runtime 把当前唯一待办写入固定 `recovery/pending-action.json`，至少包含：

- action ID、kind 和 schema version；
- run、request、version、parent phase event 和 capability attestation 绑定；
- 已去敏的工具输入或 read plan；
- 允许的提供者类别、资源限制、截止时间和停止条件；
- 固定 result slot、action SHA-256 和重放保护字段。

宿主只向 action 指定的 result slot 写 canonical receipt。receipt 至少包含：

- action SHA-256；
- 宿主、provider、tool、execution ID 和执行时间；
- 实际执行状态、错误或取消结果；
- 查询、来源、内容摘要、有限摘录和结果内容散列；
- `cannot_prove`、来源利益和共同上游；
- receipt SHA-256。

runtime 将 receipt 视为不可信输入，重新验证字段闭合、父链、权限、路径、散列、URL、来源身份和资源边界。验收后写入 immutable admitted artifact；拒绝的 receipt 保留在尝试历史中，不推进 phase。

没有提供者签名时，manifest 必须把证明等级写为 `host-attested`；有可验证签名时才可写更高等级。文章和判断不能把证明等级偷换成事实置信度。

## 7. U0–U3 恢复合同

### 7.1 U0：宿主能力、隐私与许可

新增持久、散列绑定的 host capability attestation。它分开记录：

- `requirements`：本次运行需要的 filesystem、DOCX parser、network、retrieval、validators、subagents 和 model context；
- `measured_availability`：宿主当前真实可用状态；
- sensitivity、retention、outbound permission 及许可依据；
- provider/tool identity、测量时间和证明等级；
- resource limits 和 evidence cutoff；
- request、run、version 绑定。

runtime 依据 attestation 构建 U0 run contract；宿主不能直接提交完整 runtime-owned run contract。`required + unavailable` 在任何外发前进入 `blocked`。恢复时读取原 attestation 并重新验证，不从 run contract 反推 availability。

公开普通问题可使用 `outbound_permission=allowed`；包含内部、私人或受限材料时，只允许被 U0 明确批准的去敏查询。无法安全去敏或 permission=`denied` 时，必需检索失败关闭。

### 7.2 U1：真实读取计划与凭据

runtime 生成并持久化 canonical read plan，绑定全部 4,753 个已晋升源单元、内容散列、reader mode、request、U0 parent、input snapshot、source manifest 和 version。

宿主或受控 subagent 实际读取 source unit 后返回 read receipt。runtime 可以生成 plan、校验 bytes 和聚合 coverage，但不得代替 reader 宣称已读。完整读取可分批并行，每个 receipt 都绑定真实 execution ID、时间和 source-unit hash。

`read-plan.json` 的散列进入 U1 outputs、checkpoint 和恢复验证。只有 plan 全覆盖、receipt 无重复且内容散列匹配时完成 U1。

### 7.3 U2：检索与 subagent 补证

沿用现有检索原语和资格集合，打通可持久恢复的宿主桥：

1. runtime 形成 `required` 或 `not-applicable` 决策；
2. 检查 network、ACL、outbound permission 和资源；
3. 发行去敏、幂等且绑定当前 U1 的 retrieval action；
4. 宿主调用真实 web/search/browser 工具；
5. runtime 验证结果 receipt、来源清单和共同上游；
6. 形成 `required-complete`、`required-blocked` 或 `not-applicable` ledger。

`not-applicable` 只允许 pure-logic 或真实 closed-input。必需检索的网络不可用、外发拒绝、ACL 未证实、重试耗尽、rate limit 或 timeout 不能改写成 N/A。

subagent 是可选的补证通道，只能承担来源发现、反例、受影响位置、来源谱系和校准任务。每次任务需要去敏 prompt、task/result receipt、模型或宿主身份、资源上限、结果 hash 和 `cannot_prove`。subagent 结果先进入 candidate 区，只有被来源验证和 U3 admission 接纳后才成为证据。subagent 不得写运行包控制字段或最终裁决。

### 7.4 U3：证据接纳与冻结

U3 从三类来源构建证据账本：

1. 用户请求与用户提供材料；
2. U2 admitted web sources；
3. 经来源验证的 subagent candidates。

每条证据必须保存信息身份、原始来源、来源谱系、共同上游、支持的具体命题、不能证明什么、可见性和 cutoff。未知 event/publication date 保持 `null/unknown`，不得为了通过 schema 伪造日期。

`user-claim` 必须能通过 request/material span 或内容 hash 精确归属于用户。模型生成的政策、数字、因果链或预测不得标成 user-claim。U3 完成后 ledger 不可变。

## 8. U4–U12 的证据与表达约束

### 8.1 允许大胆生成，但不允许身份偷换

Ultra 继续完整生成世界卷、竞争机制、三阶递归、五类裁决、行动排序和文章。生成力度不因证据治理而收缩。

- 模型提出的新机制标记为 `model-candidate`，可以参与比较，但不能伪装为已观察事实。
- 示例数字、情景参数和压力测试值标记为 `simulated`，说明用途、范围和反转条件。
- 预测进入 forecast ledger，不能回写成当前事实。
- 价值、责任和授权判断显式列出事实前提与规范前提。

### 8.2 支持关系

每个事实命题和事实裁决必须有非空 support edge。support edge 绑定 evidence ID、支持范围、不能证明项和独立性簇。

现实事实至少需要一条非 `user-claim`、非 `model-candidate`、非 `simulated` 的 admitted evidence。用户主张可以被钢人化和分析，但不能独立提高事实置信度。空 `evidence_refs`、只引用模型节点或把共同上游重复计数都不能通过。

validator 能证明声明的身份、引用、来源和结构支持是否闭合；它不能把结构闭合冒充终极事实。语义支持由独立 fresh review 检查，并明确其模型判断属性。

### 8.3 文章质量

最终文章继续要求：

- 直接回答用户中心问题；
- 给出当前最佳判断而非空泛中立；
- 展开至少两个竞争机制、主要残差和反转条件；
- 完成一至三阶结构推演；
- 比较行动、不行动、延迟、试探、退出或转移；
- 让普通读者不依赖内部工件也能完整阅读。

机械关键词命中不能替代语义覆盖。coverage 使用 concept/claim/section ID 和可追踪责任映射；fresh article review 检查是否真正回答问题、是否只是列名、是否重复 marker、是否把工件字段堆成正文。

Reasonix 已产生的运行作为法证样本保持只读：其答案展开力度用于正向质量基准，其错误输入身份、零外部检索、模拟事实化、手工删除 checkpoint/lease 和 validator 误放行用于负向回归。CI 不依赖该机器本地路径或修改其字节。

## 9. 正常宿主循环

核心 CLI 继续复用 `start`、`prepare`、`materialize`、`validate`、`repair-plan`、`resume`、`cancel` 和 `rebuild-index`。只有同版本新证据派生缺少现成接口，因此新增语义独立的 `evidence-fork`；它不复用版本迁移 `fork`：

1. `start` 接收原始自然语言并建立 immutable request intake；
2. `prepare` 幂等返回当前 pending action、result slot 和下一步说明；
3. 宿主执行 action 并写 receipt 或语义 authoring slot；
4. `materialize` 验证当前输入，尽可能推进，然后发布下一个 action；
5. 重复至 U12 complete。

缺少尚未到期的 host result 或下一阶段 authoring file 是正常等待：命令返回成功的机器可读结果 `outcome=awaiting-host-action` 或 `outcome=awaiting-authoring`，保留 `status=running`，释放 writer lease，并写明唯一 next action。它不是 validation failure、needs_attention 或异常。

receipt 无效、越权或与 parent 不符才返回拒绝；资源耗尽、不可恢复残留或历史损坏进入对应 attention/failure 状态。宿主不再通过捕获“缺少下一个文件”的异常猜流程。

## 10. 状态、取消、修复与 fork

### 10.1 writer ownership

- 只有成功取得当前 writer lease 的 caller 可以修改 status、phase head、checkpoint、artifact authority 和 publication transaction。
- 未取得 lease 的 caller 只能返回 conflict，不能把运行改成 blocked、failed 或 needs_attention。
- 所有异常状态转换都位于 lease-owner 边界内。

### 10.2 durable cancel

`cancel` 使用独立 cancel-intent lock 写入 immutable cancellation intent，不等待取得 writer lease。活跃 writer 在工具派发前后、phase commit 前和 heartbeat 时检查 intent，停止新动作并收敛为唯一 terminal cancelled event。

无活跃 writer 时，cancel command 在验证旧 lease 已失效后取得新的 writer lease，再完成权威状态收敛。cancelled phase authority 优先于陈旧 run-status；重复 cancel 不产生重复 terminal event。

### 10.3 bounded repair

`repair-plan` 继续生成不可变计划；`materialize` 在 U12 validation failure 后执行受控闭环：

1. 定位最早受影响 phase；
2. 追加 invalidation/supersession 事件；
3. 保留旧 checkpoint、artifact 和 validation attempt；
4. 只重新开放受影响 phase 及下游 authoring；
5. 返回唯一 next action；
6. 最多执行 U0 资源合同允许的修复次数。

修复不得删除或改写旧历史，不得只补 marker、改 validator report 或手工清 lease。

### 10.4 new-evidence fork

版本迁移 fork 与同版本新证据 fork 使用不同 schema 和命令语义。新增 evidence-fork 入口，至少绑定：

- parent run、parent U3 event 和 evidence hash；
- 继承的 immutable request/input refs；
- 新增 evidence candidate refs；
- 严格更晚的 cutoff；
- 新的 U0 capability/privacy attestation；
- 新 run ID 和 evidence-lineage artifact。

父运行保持只读。child 不继承 U4–U12 的推理、预测或裁决作为当前事实。

## 11. Validator 恢复

fresh validator 增加以下必须失败的检查：

- 普通现实问题被包装成 closed-input；
- 必须检索却得到 N/A 或零查询/零来源；
- host availability 只从 run contract 推断而没有 attestation；
- U1 缺 read plan 或 receipt 由 runtime 代替 reader 生成；
- user-claim 无 request/material 精确归属；
- model-candidate、simulated 或 forecast 被当成 observed/reported；
- 现实事实或事实裁决没有合格 support edge；
- 来源支持范围超过 `supported_claim` 或落入 `cannot_prove`；
- 共同上游被重复计数为独立证据；
- U3 后原地插入证据；
- phase event、checkpoint、lease 或 validation history 被删除/改写；
- non-owner 改写状态；
- 文章只满足 marker 而没有完成中心问题、竞争解释和反转条件。

验证分为三层：

1. deterministic：schema、hash、phase、identity、support graph、lineage、append-only history；
2. adversarial fixtures：错标身份、空心证据、共同上游、模拟事实化、篡改与取消竞态；
3. fresh semantic review：证据是否实质支持命题、文章是否完整回答问题、概念是否按 v8.2 使用。

只有三层均通过才允许 U12 发布。

## 12. 版本与兼容

这是 runtime 和 artifact contract 升级，不是理论版本升级：

- framework version/revision：保持 `8.2 / v8.2-r1`；
- framework raw/semantic SHA-256：保持不变；
- runtime version：升级为 `1.1.0`；
- artifact schema version：升级为 `2`；
- validator version：升级为 `1.1.0`；
- article contract version：升级为 `1.1.0`；
- compiler version：保持不变。

已完成的 v1 run 永久只读，runtime 只提供兼容读取和验证，不再创建新的 v1 run。进行中的 v1 run 不原地跨版本续跑；根据情况创建版本迁移 child 或新的 evidence child。新的 v2 closed-input run 仍执行 v2 U0、U1 和 U3 合同，只在 U2 具备严格 `not-applicable` 资格。

所有 canonical/mirror/release manifest、compatibility matrix 和适配器必须使用同一版本绑定与 skill tree hash。

## 13. 测试设计

### 13.1 TDD 顺序

每项修复先写能够复现当前失败的 RED 测试，再实现最小 GREEN，最后做局部重构。不得先改生产代码再补测试。

### 13.2 必须覆盖

- exact Ultra trigger + 普通中文自然语言 fresh run；
- open-world 默认路由与真实 required-retrieval handshake；
- closed-input 只在完整材料和明确边界下 N/A；
- pure-logic 独立资格；
- 动态 U0 capability/privacy attestation 与恢复；
- U1 read plan 持久化、分批 receipt、4,753 单元闭合；
- 去敏 retrieval action、host result ingest、来源 admission；
- network/outbound/ACL 阻断时零未授权工具调用；
- optional/required subagent 分支和隐私边界；
- U3 用户、web、subagent 证据聚合与共同上游去重；
- unknown date 不伪造；
- user-claim 精确归属、模拟值身份、事实 support edge；
- 正常 awaiting-host/authoring 不产生 Error block；
- cancel 抢占、陈旧 status、重复收敛和停止新工具；
- non-owner status mutation 被拒绝；
- repair append-only invalidation 与有限重试；
- late-evidence child fork；
- U12 文章质量、语义支持与完整发布；
- 固定 v8.2 源、registry、contract ID 和语义散列不变；
- Codex、Reasonix、Claude 薄适配器合同一致。

CI 使用确定性的 fake host/provider 和冻结来源包验证完整 handshake，不依赖实时网络。发布前另做一次显式授权的 live smoke，证明宿主真实工具路径可达；live smoke 结果与 CI 结果分开记录。

### 13.3 质量场景

使用“AI 就业危机、制度分支与多理论资源”作为端到端质量场景，验收结构而不锁死具体文字：

- 真实检索并区分当前事实、历史参照和理论资源；
- 不只列出 UBI 或 AI 公有化，能比较多个政策组合及其条件；
- 对更平等秩序与更坏野蛮状态给出条件分支，不写成宿命；
- 对马克思主义及其它思想资源做实质比较，不只列名；
- 保留明确判断、竞争机制、三阶展开、残差、反转条件和行动路径；
- 不把模型自设数字写成现实观测。

## 14. 完成标准

只有同时满足以下条件，恢复才算完成：

1. 普通自然语言测试问题可从 fresh start 运行至 U12 complete。
2. 需要检索的问题产生真实、绑定、可恢复的 U2 host-tool receipts 和 U3 admitted evidence。
3. closed-input 不能被问题自我复制或材料伪装取得。
4. 证据身份、support graph、共同上游、模拟和预测边界通过 adversarial tests。
5. Reasonix 类强展开效果保留，文章不退化为证据复述或空泛保守回答。
6. 全部 v8.2 理论源、概念 registry、contract map 和 semantic hash 保持不变。
7. cancel、lease、repair、evidence fork 和 append-only history 通过竞态与篡改测试。
8. Windows 完整 Ultra 测试得到最终 pytest summary；Linux 快速门与 manifest/mirror/integrity checks 通过。
9. canonical 仓库、GitHub 合并提交、Codex、Reasonix、Claude 安装树逐文件一致。
10. 已有法证运行和用户测试目录未被修改。
