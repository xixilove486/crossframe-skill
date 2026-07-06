# CrossFrame Max Concept Registry

This registry is a locator and trigger index for `crossframe-max`.

It does not replace the full-source primary knowledge base. A registry hit only tells the runtime where to read next. Every concept definition, boundary, allowed use, forbidden use, and key claim must still be confirmed against `references/v6-full-source/` paragraph ids before final output.

## Runtime Rule

1. Start concept-registry lookup after `max-local-world-model` identifies structural variables.
2. Use this file to map visible words, semantic neighbors, and structural symptoms to source paragraph ranges.
3. Read the listed full-source paragraphs and nearby paragraphs before using the concept.
4. If a concept is not listed here, do full-source keyword and heading search, then record a registry gap in `max-concept-graph`.
5. Do not treat a registry row as a definition. The definition lives in full-source.

Minimum chain:

```text
local structural variable -> concept-registry lookup -> full-source paragraph read -> concept contract -> claim ledger
```

## Source Anchor Closure Rule

每个 `concept_id` 进入 `max-concept-hit-ledger.json` 时，`source_ranges_from_registry` 必须来自本 registry 的 primary source anchors。`source_ranges_read` 必须覆盖或至少交叉对应 source range，`source_paragraph_ids` 必须落在 `source_ranges_read` 内。否则进入 `concept_source_anchor_mismatch`，不得通过补写 final Markdown 修复。

## Lookup Outcomes

| outcome | meaning | required action |
| --- | --- | --- |
| direct hit | User wording or structural variable matches a registry concept. | Read listed paragraphs and nearby paragraphs. |
| neighbor hit | User wording is not the concept term, but the mechanism belongs to the concept neighborhood. | Read listed concept plus neighbor concepts. |
| conflict hit | Multiple concepts can explain the same signal. | Read all candidate concepts and downgrade until evidence separates them. |
| gap hit | The concept is absent from registry. | Search full-source, cite paragraph ids, and record the registry gap. |

## Core Concept Entries

| concept | aliases / structural symptoms | primary source anchors | must-read neighbors |
| --- | --- | --- | --- |
| 结构域 | 局部世界, 分析对象, 对象边界, 最小共同指向 | `03-world-layer.md` `P0901-P0906`, `P1447-P1450` | 边界与接口, 指向锚点, 条件势场 |
| 边界与接口 | 内外区分, 跨域互操作, 流动/隔离, 边界通道 | `03-world-layer.md` `P0907-P0908`; `02-boundary-layer.md` `P0195-P0896` | 结构域, 条件势场, 观测反身性 |
| 指向锚点 | 锚点, 子锚点, 共同方向, 意义牵引 | `03-world-layer.md` `P0909-P0910`, `P1039-P1097` | 生成节点, 递进模式, 反馈写回 |
| 生成节点 | 先行者, 启动者, 早期承接, 转译/让渡 | `03-world-layer.md` `P0911-P0912` | 行动承接层, 动力-承接链, 结构负荷 |
| 行动承接层 | 承接者, 主体层, 成本承担, 风险吸收 | `03-world-layer.md` `P0913-P0914`, `P1220-P1319` | 动力-承接链, 反馈写回, 主体位置矩阵 |
| 动力-承接链 | 推力链, 支撑通道, 资源/信任/责任传导 | `03-world-layer.md` `P0915-P0916`, `P1098-P1219` | 行动承接层, 结构负荷, 反馈写回 |
| 反馈写回 | 信息回流, 坏消息回流, 经验能否改变结构 | `03-world-layer.md` `P0917-P0918`, `P1461-P1463`, `P1496-P1497` | 证据追踪, 申诉入口, 修复 |
| 条件势场 | 外部条件, 压力分布, 势场系数, 多层条件场 | `03-world-layer.md` `P0919-P0920`, `P1180-P1219`, `P1464-P1466`; `04-state-layer.md` `P1708-P1718` | 边界与接口, 嵌套耦合, 局部实现, 负向势场螺旋 |
| 结构负荷 | 维护债, 熵增, 恢复余量下降, 虚稳态 | `03-world-layer.md` `P0921-P0922`, `P1320-P1416`, `P1471-P1472` | 状态坐标, 修复, 有序退场 |
| 演化相位 | 阶段, 生命周期, 状态坐标, 路径窗口 | `03-world-layer.md` `P0923-P0924`; `04-state-layer.md` `P1520-P1813` | 非线性路径库, 路径置信分层, 有序退场 |
| 时间不可逆 | 修复窗口, 不可复原, 路径依赖, 已发生伤害 | `03-world-layer.md` `P1467-P1470`; `04-state-layer.md` `P1520-P1813` | 演化相位, 有序退场, 不可穷尽声明 |
| 演化记忆 | 经验记忆, 制度资产/负债, 记忆保存, 继承经验 | `03-world-layer.md` `P1354-P1417`; `04-state-layer.md` `P1729-P1813` | 有序退场, 良性消亡, 开放性承担行动 |
| 状态坐标与生命周期 | 状态坐标, 生命周期, 阶段0-6, 时间窗口 | `04-state-layer.md` `P1520-P1813`; `06-tool-layer.md` `P1991-P2120` | 演化相位, 非线性路径库, 路径置信分层 |
| 路径置信分层 | 路径置信, 概率分层, 反事实边界, 多路径判断 | `04-state-layer.md` `P1604-P1654`; `06-tool-layer.md` `P1991-P2120` | 非线性路径库, 强判断八件套, 不可穷尽声明 |
| 开放性承担行动 | 爱的操作化边界, 真实成本, 非工具性, 生成事件 | `03-world-layer.md` `P0925-P0933`, `P1478-P1480`, `P1508-P1519`; `09-governance-layer.md` `P3168-P3178` | 超越性窗口, 边界保护, 不可穷尽声明 |
| 解释准入 | 能否解释, 解释对象, 材料边界, 适用范围 | `02-boundary-layer.md` `P0195-P0275`; `05-interface-layer.md` `P1814-P1846` | 工具准入, 来源-证据-判断-行动上限, 不可判断区 |
| 工具准入 | 能否使用诊断工具, 输出边界, 工具权限 | `02-boundary-layer.md` `P0276-P0355`; `06-tool-layer.md` `P1858-P1915` | 干涉授权, 过程性产物边界, 强判断八件套 |
| 干涉授权 | 能否介入, 修复授权, 处置授权, 行动上限 | `07-intervention-layer.md` `P2366-P2427`; `09-governance-layer.md` `P3103-P3115` | 工具准入, 责任链硬规则, 低权力主体保护 |
| 七闸 | 解释前置闸门, 判断闸门, 安全闸门 | `02-boundary-layer.md` `P0271-P0355`; `06-tool-layer.md` `P1858-P1915` | 解释准入, 强判断八件套, 命题验证表 |
| 五闸十三步 | 诊断流程, 分步核验, 程序化判断 | `06-tool-layer.md` `P1858-P1990` | 七闸, 命题验证表, 过程性产物边界 |
| 开放断言 | 不能终审但可开放陈述, 候选判断, 低强度表达 | `06-tool-layer.md` `P2243-P2270`; `07-intervention-layer.md` `P2271-P2365`; `09-governance-layer.md` `P3168-P3178` | 强判断八件套, 不可穷尽声明, 正当不透明 |
| 命题验证表 | claim 检查, source_anchor, 证据追踪, 判断降级 | `02-boundary-layer.md` `P0271-P0275`; `06-tool-layer.md` `P1991-P2120` | 强判断八件套, 来源-证据-判断-行动上限 |
| 强判断八件套 | 强判断, 公开判断, 行动建议, 程序正义 | `02-boundary-layer.md` `P0786-P0819`; `06-tool-layer.md` `P1991-P2120` | 命题验证表, 反向证据, 撤回条件 |
| 低条件试探行动 | 小步试探, 可逆行动, 低风险验证, 停止权 | `07-intervention-layer.md` `P2428-P2546`; `08-application-layer.md` `P2547-P2590` | 干涉授权, 低权力主体保护, T0-T4 恢复与再承接 |
| 权力封闭度 | 申诉受阻, 退出受阻, 证据通道封闭, 反馈失效 | `08-application-layer.md` `P2630-P2885`; `09-governance-layer.md` `P2886-P2950` | 低权力主体保护, 反模型殖民, 反馈写回 |
| 低权力主体保护 | 受害者, 沉默者, 无法申诉者, 退出者保护 | `02-boundary-layer.md` `P0786-P0819`; `09-governance-layer.md` `P3103-P3115` | 权力封闭度, 责任链硬规则, 主体位置矩阵 |
| 观测反身性 | 诊断改变对象, 发布改变行动链, 评分进入结构 | `03-world-layer.md` `P1473-P1477`; `05-interface-layer.md` `P1814-P1849`; `06-tool-layer.md` `P1850-P1857` | 过程性产物边界, 公开发布判断门禁 |
| 过程性产物边界 | AI 产物, 报告, 诊断书, 审计材料, 不是终审 | `09-governance-layer.md` `P3103-P3115`; `09-governance-layer.md` `P3264-P3265` | 人工智能诊断边界, 开放断言, 正当不透明 |
| 来源-证据-判断-行动上限 | source_anchor, 证据链, 判断档位, 行动边界 | `02-boundary-layer.md` `P0271-P0275`; `06-tool-layer.md` `P1991-P2120` | 命题验证表, 强判断八件套, claim ledger |
| 责任链硬规则 | 伤害事实, 补证义务, 边界保护, 不能被意义取消 | `07-intervention-layer.md` `P2366-P2427`; `09-governance-layer.md` `P3168-P3178` | 低权力主体保护, 开放性承担行动, 干涉授权 |
| T0-T4 恢复与再承接 | 恢复阶段, 信任载体, 再承接, 阶段边界 | `07-intervention-layer.md` `P2428-P2546`; `08-application-layer.md` `P2547-P2590`; `04-state-layer.md` `P1729-P1813` | 低条件试探行动, 有序退场, 结构负荷 |
| 不浪费爱原则 | 爱不变忍耐义务, 开放行动不债权化, 成本不浪费 | `03-world-layer.md` `P1508-P1519`; `07-intervention-layer.md` `P2428-P2546`; `08-application-layer.md` `P2547-P2590` | 开放性承担行动, 责任链硬规则, 有序退场 |
| 反模型殖民 | AI 判断扩张, 模型语言压过现实主体, 解释殖民 | `09-governance-layer.md` `P3103-P3115`; `09-governance-layer.md` `P3264-P3265` | 过程性产物边界, 正当不透明, 低权力主体保护 |
| 反领域殖民 | 一个领域话语吞并其他领域, 专业接口越权 | `02-boundary-layer.md` `P0195-P0275`; `09-governance-layer.md` `P2886-P2950` | 解释准入, 工具准入, 正当不透明 |
| 概念武器化 | 用概念压人, 用框架定罪, 用理论取消申诉 | `09-governance-layer.md` `P2886-P2950`; `09-governance-layer.md` `P3264-P3265` | 低权力主体保护, 过程性产物边界, 强判断八件套 |
| 正当不透明 | 不可完全解释, 隐私边界, 不透明保护, 非文本证据 | `09-governance-layer.md` `P3168-P3178`; `02-boundary-layer.md` `P0195-P0275` | 不可穷尽声明, 解释准入, 反模型殖民 |
| 不可穷尽声明 | 不可判断区, 解释边界, 未穷尽资料, 不终审 | `09-governance-layer.md` `P3168-P3178`; `02-boundary-layer.md` `P0195-P0275` | 正当不透明, 开放断言, 解释准入 |
| 非文本证据 | 行动痕迹, 沉默, 退出, 身体/时间成本, 非话语材料 | `05-interface-layer.md` `P1814-P1849`; `06-tool-layer.md` `P1850-P1857`; `02-boundary-layer.md` `P0271-P0275` | 来源-证据-判断-行动上限, 低权力主体保护 |
| 虚稳态 | 表面稳定, 高维护债, 失真反馈, 结构脆弱 | `03-world-layer.md` `P1320-P1416`; `04-state-layer.md` `P1604-P1654` | 结构负荷, 反馈写回, 非线性路径库 |
| 有序退场 | 保护性退出, 锚点移交, 资源释放, 演化记忆保存 | `04-state-layer.md` `P1729-P1813`; `07-intervention-layer.md` `P2428-P2546`; `08-application-layer.md` `P2547-P2590` | 良性消亡, 不浪费爱原则, T0-T4 恢复与再承接 |
| 良性消亡 | 完成使命后的消解, 不再占用资源, 记忆保留 | `04-state-layer.md` `P1729-P1813`; `09-governance-layer.md` `P3168-P3178` | 有序退场, 开放性承担行动, 不可穷尽声明 |

## Root Assumption Anchors

Use these anchors when a claim depends on hard worldview constraints.

| anchor | source range | lookup trigger |
| --- | --- | --- |
| A1 结构域识别 | `03-world-layer.md` around `P1447-P1450` | Object boundary, local world, whether an object can be treated as a structure domain. |
| A2 有限承载 | `03-world-layer.md` around `P1451-P1453` | Cost, resources, attention, recovery, responsibility, support channel. |
| A3 存护-消解双功能 | `03-world-layer.md` around `P1454-P1457` | Protection that also suppresses, order that also harms, structure that both preserves and dissolves. |
| A4 位置遮蔽与视角不完备 | `03-world-layer.md` around `P1458-P1460` | Insider view, outsider view, missing edge feedback, self-diagnosis. |
| A5 反馈写回 | `03-world-layer.md` around `P1461-P1463` | Bad news, appeal, revision, evidence, correction, review. |
| A6 跨尺度嵌套耦合 | `03-world-layer.md` around `P1464-P1466` | Scale movement, nested systems, adjacent domains, external forces. |
| A7 时间不可逆 | `03-world-layer.md` around `P1467-P1470` | Repair window, return fantasy, path dependence, irreversible harm. |
| A8 结构负荷、熵增与永续脆弱 | `03-world-layer.md` around `P1471-P1472` | Maintenance debt, structural load, decay, recovery capacity. |
| A9 观测参与与反身性 | `03-world-layer.md` around `P1473-P1477` | Public naming, rating, diagnosis, intervention changing the object. |
| A10 开放性承担 | `03-world-layer.md` around `P1478-P1480` | Love, open action, real cost, non-commanded responsibility. |

## Operational Concept Anchors

| concept / gate | source anchors | trigger |
| --- | --- | --- |
| 证据追踪与判断降级 | `02-boundary-layer.md` around `P0271-P0275` | Any strong claim or contested claim. |
| 强判断程序正义 | `02-boundary-layer.md` around `P0786-P0819` | Strong judgment, public judgment, action recommendation. |
| 状态坐标 | `04-state-layer.md` `P1520-P1813` | Evolution, lifecycle, stagnation, regression, phase, future path. |
| 非线性路径库 | `04-state-layer.md` around `P1604-P1654` | Jump, split, merge, external takeover, paradigm replacement. |
| 有序退场 | `04-state-layer.md` around `P1729-P1813` | Mission completion, transfer, exit, memory preservation. |
| 人工智能诊断边界 | `09-governance-layer.md` around `P3103-P3115` | AI-generated judgment, report, evaluation, process artifact. |
| 反例写回 | `09-governance-layer.md` around `P2886-P2950`, `P3258-P3265` | Counterexample, downgrade, pause, withdrawal, publication gate. |
| 公开发布判断门禁 | `09-governance-layer.md` around `P3264-P3265` | Public article, report, post, appeal, governance output. |

## Registry Log Required In Artifacts

`max-concept-graph` must record:

- concept-registry lookup status
- direct hits
- neighbor hits
- conflict hits
- gap hits
- full-source paragraph ids read after each hit
- concepts downgraded after source read
- concepts rejected after source read
