# ProMax 成文协议

本协议只约束 P9–P10 的读者投影与中文表达，不提供新的理论定义，也不改变 P8 已冻结的事实、命题、证据、判断、建议或授权。完整性由 dossier、atlas、case/countercase 与 essay 共同承担；任何单份正文都不需要复制整套审计字段。

## 固定边界

1. 只读取本 skill 自带的 `references/promax-house-voice.md`、`references/prose-routing-map.md` 与被 P9 选中的技法卡。
2. 表达资产不得成为知识来源。技法只能决定入口、递进、转折、比较、反驳、边界或结尾，不能新增事实、强机制、概念原义或现实授权。
3. P9 自动选择文章体裁，不展示选择器、不暂停等待用户确认。
4. 声口固定为 `crossframe-promax`。体裁改变组织方式，不改变判断偏好、证据责任和撤回义务。
5. 正文不设总字数上限。以 reader beats 和论证依赖闭合为停止条件；字符数、段长和章节数只作异常提示。

## P9：读者投影

P9 在原有 package coverage 之外冻结 `reader_projection`：

- `article_type`：九种体裁之一。
- `house_voice_id`：固定 `crossframe-promax`。
- `thesis_claim_id`：正文中心命题。
- `core_concept_ids`：真正改变中心判断、机制竞争、反方或建议的 applied concepts。
- `atlas_only_concept_ids`：其余 applied concepts。
- `selected_techniques`：恰三个核心技法，按需零至两个辅助技法；总数不得超过五个。
- `reader_beats`：按信息依赖登记入口、中心命题、机制、证据或案例、同维比较、最强反方、明确立场、撤回、行动边界和结尾。

`core_concept_ids` 与 `atlas_only_concept_ids` 必须互斥，并集必须等于全部 applied concepts。所有 applied concepts 的权威定义、邻接关系与误用边界仍由 atlas 精确闭合；正文只承担核心概念的读者转译。

## 自动体裁

根据请求对象、主要交付责任和读者需要自动选择：

- `reply`：回应具体困惑或“怎么看、怎么办”。
- `public-commentary`：公共制度、政策、平台与机构责任。
- `concept-explanation`：思想、理论与概念关系。
- `organization-review`：团队、项目、流程、授权与反馈修复。
- `case-analysis`：由案例承载多层机制与判断。
- `debate-refutation`：拆命题、保留最强反方并检验论据根基。
- `reading-synthesis`：互读书、论文、文章或理论材料。
- `trend-deduction`：条件分支、早期信号、反向信号与终点状态。
- `neutral-analysis`：不明显属于以上类型的混合长文。

体裁只决定 reader beats 和技法路由，不得改变 P8 position、judgment strength、recommendation ranking 或 action ceiling。

## 正文主序

正文默认按以下信息依赖推进；可以合并相邻动作，但不能颠倒论证所需前提：

1. 现实入口：一个可核验事实、具体矛盾、高成本信号或真实处境。
2. 中心命题：尽早说清真正要判断什么以及当前结论。
3. 机制递进：解释为何卡住、反复或产生当前结果，并区分至少两个竞争机制。
4. 同维正反比较：在同对象、同尺度、同窗口和同评价维度下比较路径与代价。
5. 最强反方：重建其最强论据、可成立条件和可观察预测，不攻击稻草人。
6. 明确立场：说明为何当前仍选择首位判断或方案，以及次选在什么条件下上升。
7. 撤回条件与行动边界：写明什么事实会降档、切换或停止，以及当前允许做到哪里。
8. 余味结尾：回到现实责任或尚未封死的问题，不用宏大口号代替判断。

## 概念进入正文

每个核心概念只能按以下顺序进入：

1. 先说现实关系；
2. 必要时命名权威中文术语；
3. 说明这个区分比日常说法多解释了什么；
4. 立即回到事实、机制、成本、反例或行动后果。

禁止“概念名—完整定义—在当前问题中的应用”的逐项目录式成文。删掉所有框架术语后，陌生读者仍应能复述中心判断、因果链、成本承担者、最强反方、撤回条件和下一步边界。

## 四份公开产物的责任

- `promax-dossier.md`：完整结构底稿、命题与证据、读者投影、体裁与技法落地审计。
- `promax-concept-atlas.md`：全部 applied concepts 的权威定义、当前作用、邻接关系、误用边界和源锚点。
- `promax-case-and-countercase.md`：每个主要机制的 typed similar cases 与 typed failure cases。
- `promax-essay.md`：没有机器字段和审计脚手架的连续读者正文。

四份产物必须语义一致，但禁止通过逐字复制机器字段制造一致性。

## P10：主笔与独立审校

`longform_writer` 依据 P9 的 reader projection 生成四份公开产物。随后 `prose_fidelity_auditor` 读取当前 essay、P8 锁与 P9 output plan，生成内部 `promax-prose-review.json`。

审校必须覆盖：

- 现实入口；
- 论证依赖；
- 核心概念保真；
- 证据绑定；
- 最强反方；
- 公平比较；
- 立场与建议一致性；
- 撤回与行动边界；
- 固定声口；
- 审计泄漏。

每个通过判断都要给出正文中的实际短摘。review 必须绑定当前 essay、position 与 output plan 的 SHA-256；陈旧散列、正文中不存在的短摘、漏掉 reader beat 或维度自相矛盾都视为失败。

## 表达闸

正文必须同时满足：

- 第一段不用框架 ID、概念墙或运行字段开场。
- 不出现 `V8-CANON-*`、`CLAIM-*`、`OPTION-*`、散列、key/value 台账或 validator marker。
- “在本题中”“本轮中”“本运行中”合计不得超过两次。
- 不以“问题复杂、各有道理、还需研究”代替当前判断。
- 不自动迎合用户，也不为显得独立而自动反对；只服从被冻结的证据与判断。
- 不使用“历史必然、文明升级、时代洪流”等无证据宏大叙事，不制造任意数字阈值或虚假精确。
- 批评行为、程序、责任链和代价转移，不做人格审判。

段落偏长、章节很多或正文很长只能触发审阅提示，不能单独判失败。真正的失败是读者无法沿信息依赖理解判断，或表达越过上游锁。

## 修复

- 纯正文表达、声口、重复、入口或技法落地失败：重置 P10。
- 体裁、reader beats、核心概念集合或技法映射错误：重置 P9。
- 立场、建议或撤回条件发生实质漂移：重置 P8。
- 事实或证据不足以支撑正文命题：按最早根因重置 P6 或更早阶段。
- 概念处置本身错误：重置 P4；只有正文转译错误时留在 P10。

每次失败都生成新的 repair plan、失效旧 review 与 manifest，并递增 validation attempt。不设固定重写次数；只有 fresh validator report 通过，或记录真实能力缺口并进入 continuation，才能结束。
