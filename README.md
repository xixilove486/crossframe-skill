<div align="center">

<p><strong>CROSSFRAME · V8 STRUCTURAL REASONING RUNTIME</strong></p>

# CrossFrame ProMax

### 可运行、可审计、可修复的重型 AI 结构推演系统

**它不是简单“让模型多想一会儿”的提示词，而是把 v8 全源知识、结构推演、真实检索、反方攻击、明确裁决、完整长文与机器验证锁进同一条独立 runtime。**

由 **CrossFrame 作者与 ChatGPT 5.6 Sol（Ultra）** 共同设计、实现、攻击与验证。

<p><sub>CrossFrame ProMax 属于更广泛的 CrossFrame Skill Suite 家族，同时是 v8-only、exact-name only 的独立 runtime；它不取代 Suite、Max 与其他专项 skills。</sub></p>

<br>

![ProMax](https://img.shields.io/badge/ProMax-1.0.0%20%7C%20v8.0-2f81f7?style=flat-square&labelColor=0d1117&color=2f81f7)
![Runtime](https://img.shields.io/badge/runtime-independent-58a6ff?style=flat-square&labelColor=0d1117&color=58a6ff)
![Python](https://img.shields.io/badge/Python-3.11-79c0ff?style=flat-square&labelColor=0d1117&color=79c0ff)
![Trigger](https://img.shields.io/badge/trigger-exact--name_only-d29922?style=flat-square&labelColor=0d1117&color=d29922)
![Validation](https://img.shields.io/badge/validation-artifact--first-2ea69b?style=flat-square&labelColor=0d1117&color=2ea69b)
![License](https://img.shields.io/badge/license-MIT-f8efcf?style=flat-square&labelColor=fffdf6&color=f8efcf)

<p align="center">
  <a href="skills/crossframe-promax/SKILL.md"><strong>CrossFrame ProMax skill</strong></a>
  ·
  <a href="https://xi-kari.github.io/crossframe-skill/"><strong>网页介绍</strong></a>
  ·
  <a href="https://github.com/xi-kari/crossframe-skill/releases"><strong>下载 Release</strong></a>
</p>

<p align="center">
  <a href="#promax-runtime"><strong>运行链</strong></a>
  ·
  <a href="#promax-capabilities"><strong>ProMax 能力</strong></a>
  ·
  <a href="#model-flavor"><strong>模型风味</strong></a>
  ·
  <a href="#promax-conditions"><strong>依赖与消耗</strong></a>
  ·
  <a href="#quickstart"><strong>快速开始</strong></a>
  ·
  <a href="#what"><strong>Skills 家族</strong></a>
  ·
  <a href="#use-cases"><strong>适用场景</strong></a>
  ·
  <a href="#workflow"><strong>工作流</strong></a>
  ·
  <a href="#max"><strong>Max 模式</strong></a>
  ·
  <a href="#promax"><strong>ProMax 模式</strong></a>
  ·
  <a href="#closure"><strong>质量闭环</strong></a>
  ·
  <a href="#skills"><strong>Skill 地图</strong></a>
  ·
  <a href="#docs"><strong>文档</strong></a>
</p>

</div>

<table>
<tr>
<td align="center"><strong>3,980</strong><br>全源读取事件<br><sub>3,863 个段落 + 117 张表</sub></td>
<td align="center"><strong>709 个概念</strong><br>逐项处置<br><sub>定义、邻接、误用边界</sub></td>
<td align="center"><strong>P0–P11</strong><br>阶段状态机<br><sub>冻结、验证、定向修复</sub></td>
<td align="center"><strong>五向真实检索</strong><br>案例校准<br><sub>支持、反例、边界条件</sub></td>
</tr>
</table>

> **共创边界：** ChatGPT 5.6 Sol（Ultra）参与了 ProMax skill 的架构设计、实现、攻击测试与验证；CrossFrame v8 的框架定义仍以作者提供的 v8 原始材料为权威。共创模型不是运行依赖，其他具备文件、Python 与可选网络能力的 Agent 型 AI 也可以调用。

---

<a id="promax-runtime"></a>
## 一条可验证的 ProMax 运行链

```text
request → v8 full-source → concept closure → local world model
        → claim-path → retrieval → red-team → position lock
        → dossier + essay → validator → phase-aware repair
```

ProMax 不是一次性 prompt。它是有状态、有工件、有验证闸的独立运行时：先冻结问题与 v8 源快照，再构造概念闭合、局部世界、命题路径和检索工件；初稿必须经过反方攻击与立场锁定，最终 dossier 与 essay 还要由 fresh validator 独立验收。若失败，系统依据 `affected_phase` 只重置受影响阶段及其下游产物，再进行定向修复，不靠补几个关键词伪装完成。

<a id="promax-capabilities"></a>
## ProMax 完整能力

| 能力 | 运行约束 | 可审计结果 |
| --- | --- | --- |
| **v8 全源加载** | 固定源快照；读取 **3,863 个段落、117 张表** | 每次读取形成 read event 与 hash，证明实际加载范围 |
| **概念闭合** | 对 **709 个概念**逐项登记定义、邻接概念、误用边界和与当前请求相关的理由 | 概念不能只被“提到”，必须说明如何进入或退出本次推演 |
| **局部世界建模** | 显式建模对象、行动者、圈层、尺度、双通道、时钟、事件、证据与未知项 | 分离已知、推断和待证部分，阻止把单一视角冒充全局 |
| **命题与路径** | 建立中心命题、竞争机制、路径 DAG、条件预测、切换条件与撤回条件 | 结论绑定可检验路径，不以修辞强度代替机制解释 |
| **真实检索** | 按五向检索搜寻案例、支持证据、反例和边界条件，并将支持与反例分开登记 | 有网络时外部校准；断网时诚实降档，不伪造来源或检索完成态 |
| **自我攻击** | 构造最强反方，检查概念误用、立场稳定性与证据截止 | 让反例真正有机会改写、降档或推翻初始判断 |
| **明确裁决** | 攻击后始终锁定立场；只有用户明确要求建议时，才比较六类行动并给出主方案、备选、停止条件与回滚路径 | 未要求建议时只完成明确判断，recommendation 闭合为 `{"status":"not_requested"}`，不自行制造方案 |
| **可验证交付** | 物化 dossier、concept atlas、cases、essay 与 manifest，再交给 fresh validator 和 phase repair | 最终文本不能自我认证；发布状态由独立校验报告决定 |

<a id="model-flavor"></a>
## 如何抑制模型自身风味

不同 AI 有不同的训练偏好：有的倾向顺从，有的先反驳，有的习惯列举却不裁决。ProMax 不假设能抹去这些差异，而是用五道结构约束限制它们对判断的支配：

1. **v8 定义优先。** 框架原文与概念契约覆盖模型预训练中碰巧同名的概念，禁止用熟悉词义替代 CrossFrame 的独特定义。
2. **冻结关键工件。** 请求、源快照、证据边界、命题和阶段产物被显式登记，防止推演中悄悄改题、换证据或移动判断标准。
3. **检索与 red-team 攻击草稿。** 真实案例检索和最强反方不是装饰性章节，而是可以迫使初稿改写、降档或撤回的独立步骤，不能只顺着用户说。
4. **position lock 强制裁决。** 模型必须在攻击后给出明确立场、比较备选，并登记撤回、停止与回滚条件；不能用“各有道理”逃避判断。
5. **fresh validator 与阶段修复。** 新鲜校验进程依据工件而非文风验收；失败后按阶段修复，防止流畅文字给自己盖章。

这些约束不会让不同模型的措辞、节奏和全部判断变得字面完全相同，但它要求每个模型都通过同一套结构契约与审计闸；差异必须暴露在证据、路径、反例和撤回条件中，而不能藏在模型习惯里。

<a id="promax-conditions"></a>
## 运行条件、消耗与触发边界

| 项目 | 要求 |
| --- | --- |
| Python | **Python 3.11**（仓库 CI 基准） |
| 生产依赖 | `jsonschema` |
| 仓库验证 | `pytest`、`PyYAML` |
| 宿主能力 | 读取 skill 文件、执行 Python、写入独立 artifact 目录 |
| 网络 | 外部真实案例检索的可选能力；无网络时必须显式降档 |
| v8 材料 | 全源快照随 skill 携带，运行时不依赖原始 Word 文件 |

ProMax 仅在用户明确使用以下四种名称之一时触发：`crossframe-promax`、`CrossFrame ProMax`、`$crossframe-promax`、`/crossframe-promax`。仅说“最大算力”“全尺度”或“穷尽推演”不构成 ProMax 点名，泛化最大化请求仍由 Max；suite 不得自动升级。若 Max 与 ProMax 同时出现，ProMax 优先；一旦进入 ProMax，也不得降级回 Max。

> **消耗警告：** 完整轮次会连续读取 v8 全源，逐项处置 709 个概念，并执行检索、反方攻击、建议比较、长文物化与验证修复，可能消耗数百万至数千万 token。用户提供的一次 DeepSeek V4 Pro 完整单轮观察约为 **17,000,000 token**；它不是通用 benchmark、平均值或固定成本。请只在确实需要时显式点名，并预先确认模型额度、上下文续跑能力和成本上限。

---

<a id="what"></a>
## 它是什么

**以下徽章描述 CrossFrame Skill Suite 主线，不代表上方 ProMax 的 v8 runtime 或独立审计链。**

![Suite Framework](https://img.shields.io/badge/framework-CrossFrame_v5.1.7-e4ddff?style=flat-square&labelColor=fffaff&color=e4ddff)
![Suite Workflow](https://img.shields.io/badge/workflow-diagnosis_%E2%86%92_writing_%E2%86%92_review_%E2%86%92_inquiry-d9f2df?style=flat-square&labelColor=fbfffb&color=d9f2df)

CrossFrame Skill Suite 是一组给 AI agent 使用的中文结构诊断与成文 skills。

它适合处理那些不能只靠“给建议”“写一段评论”“简单总结”解决的问题：关系、团队、组织、制度、公共争议、历史材料、命题辩论、读者来信、研究笔记，以及需要写成完整中文文章的复杂议题。

当前仓库包含 16 个 `crossframe-*` skills；它们都是 explicit-only，不会在普通任务中自动触发。推荐入口是 `crossframe-suite`；部分专项 skill 只应由 suite 或显式命令路由进入。`crossframe-max` 是独立的最大化推演入口，用来把对象当作局部世界展开世界观、运行规律、问题结构、处理路径和演化分支，不进入 suite 的 `2+1` 选择器。[`crossframe-promax`](skills/crossframe-promax/SKILL.md) 则是上文展示的 v8-only、exact-name only 独立旗舰 runtime，与 Max 的 v6 运行时相互隔离。完整分析、成文和 review 结束后，后续追问默认交给 `crossframe-inquiry`。

安全边界先行：

- CrossFrame 不替代法律、医疗、财务、心理危机处置、正式调查或机构审查。
- 高责任结论必须保留 `source_id`、`claim_id`、证据档位、撤回条件和行动上限。
- 不做人格审判、命运预言或无证据公共定性；证据不足时只能降档、补证或撤回。

它的核心目标不是堆术语，而是让 AI 在输出前先完成几件事：

- 分清事实、解释、证据和推断。
- 看清问题发生在哪个尺度：个人、关系、组织、制度、历史阶段或公共场域。
- 找到责任链、授权链、反馈链和机制候选。
- 判断哪些结论可以说，哪些只能保留为开放断言。
- 把结构判断翻译成普通人能读懂的中文表达。

---

<a id="quickstart"></a>
## 快速开始

Codex 安装：

Windows PowerShell：

```powershell
.\scripts\install-codex.ps1
```

macOS / Linux：

```bash
bash scripts/install-codex.sh
```

Claude Code 项目内常用命令：

```text
/crossframe-suite 分析这个团队为什么复盘很多但没有真实修复
/crossframe-max 把这件事当作一个局部世界，做全尺度结构推演并写完整解释
/crossframe-promax 用 v8 框架穷尽分析这个判断，主动搜索反例并给出明确立场
/crossframe-essay 写一篇关于平台治理的中文评论文章
/crossframe-inquiry 基于刚才的文章继续追问反证和迁移条件
```

公开仓库日常验证：

```bash
python scripts/check_crossframe_skill_integrity.py --repo .
python scripts/check_source_continuity.py --materials-only --repo .
python -m json.tool skills/crossframe/schemas/claim-ledger.schema.json
python -m pip install jsonschema
python scripts/validate_claim_ledger_schema_fixtures.py --repo .
python scripts/check_crossframe_max_v6_full_source.py --repo . --source-docx <path-to-v6-docx> --allow-source-path-mismatch
python scripts/check_crossframe_max_v6_registry_anchors.py --repo .
python scripts/validate_crossframe_max_route_ledger_fixtures.py
python scripts/validate_crossframe_max_repair_fixtures.py
python scripts/sync_skill_mirrors.py --check
bash -n scripts/install-codex.sh
python -m py_compile scripts/*.py
git diff --check
```

完整上手说明见 [docs/QUICKSTART.md](docs/QUICKSTART.md)。

---

<a id="use-cases"></a>
## 适用场景

CrossFrame 适合用于：

- **关系与责任链**：亲密关系、家庭、照护、解释劳动、退出困难、低权力主体保护。
- **团队与组织**：项目复盘、授权失衡、反馈写回、责任转移、组织修复备忘录。
- **公共议题**：平台治理、政策评论、机构责任、公共承诺、合规材料和申诉文本。
- **历史材料**：史料边界、断代尺度、制度连续性、archive / FOIA backlog。
- **全尺度推演**：把一件事当作局部世界，展开概念命中、运行规律、演化路径和处理问题方案。
- **命题辩论**：正反结构、隐藏前提、最强反方、证据要求和撤回条件。
- **读书与研究**：理论、文章、摘录和案例材料的互读笔记。
- **中文成文**：把结构诊断转成评论、思想文章、读者答复、案例、备忘录或长文。
- **输出审查**：检查 AI 回答有没有真正推理、是否越界、是否把材料写成了空话。
- **完成后追问**：在一轮分析、成文或质量闸完成后，继续追问、反证、补证和迁移应用。

不适合用于：

- 单纯事实查询。
- 纯工具执行等非结构诊断任务。
- 普通聊天、普通改写、普通摘要。
- 用户没有要求 CrossFrame 式结构分析的场景。

---

<a id="language"></a>
## 中文输出

CrossFrame 默认面向中文问题和中文读者。

使用时应保持：

- **主要输出使用中文**。
- 结构判断、文章正文、读者答复、案例和审查报告都应以中文完成。
- `crossframe-*` 这类英文只作为 skill id 或路由标签使用，不应替代中文解释。
- 术语尽量放在后台，前台先说人话。
- 需要引用外部材料时，引用和证据边界必须可核验。

---

<a id="workflow"></a>
## 工作流

多步骤任务推荐从总入口开始：

```text
crossframe-suite
```

它会先判断任务类型，再选择需要读取的专项 skill。常见链路如下：

```text
结构诊断      crossframe -> crossframe-review
中文长文      crossframe -> crossframe-essay -> crossframe-review
公共评论      crossframe -> crossframe-public -> crossframe-essay -> crossframe-review
组织复盘      crossframe -> crossframe-org -> crossframe-essay -> crossframe-review
历史研究      crossframe -> crossframe-history -> crossframe-essay -> crossframe-review
答读者问      crossframe -> crossframe-dialogue
读书研究      crossframe -> crossframe-notebook
超限推演      crossframe-max -> crossframe-review
v8 ProMax     crossframe-promax（独立审计，不串联 review）
完成后追问    crossframe -> crossframe-review(lite) -> crossframe-inquiry
```

CrossFrame 是 **explicit-only**：只有用户明确点名 CrossFrame、`crossframe-suite`、`crossframe`、某个 `crossframe-*`，或使用对应命令时才应启动。

`crossframe-suite` 默认是重型链路：未指定时使用 `full-visible-v5-longform`，会输出完整可见底稿、完整长文正文和 review。用户可以显式要求 `brief-visible` 或 `standard-visible` 来控制体积；体积降低不取消事实边界、`claim_id`、撤回条件和行动上限。

`crossframe-max` 不使用 suite 的 `2+1` 模式/角色选择器，也不使用普通文章类型选择器。它先形成世界观胶囊和局部世界模型，再展开 `max-path-tree`、`max-dossier` 和不设默认字数上限的 `max-essay`。

---

<a id="max"></a>
## Max 模式

`crossframe-max` 是独立的 v6 世界观前置 meta-runtime。它用于用户明确要求最大尺度、穷尽推演、完整解释、无限制长文、全尺度世界观解释，或要求审查 skill、prompt、agent、工具、模板、脚本和运行协议设计的任务。

Suite release version 是 v5.1.7；`crossframe-max` 使用的 source framework version 是 v6.0。

它的运行核心是先让 AI 加载 v6 判断框架，再把对象建模为局部世界。完整运行会读取 `references/v6-full-source/`、`references/v6-route-map.yaml`、`references/concept-registry/index.md`、`references/concept-contracts/v6-core-contracts.md` 和检索触发策略，随后生成阶段锁、读取台账、命题台账、概念命中台账、举证推理审计、结构底稿和完整长文。

`crossframe-max` 有四个运行档位：

- `max-artifact-run`：默认档位。先生成核心 artifact、长文和 continuation，再由 validator 如实登记未满足项。
- `max-complete`：完整 full-source exhaustive pass、阶段锁、artifact-first、template-fidelity、longform-dominance、route-ledger gate 和 validator 全部满足后，才可宣称完成。
- `max-design-review`：用于 skill、prompt、agent、工具、模板、脚本和运行时设计；必须使用 `skill_design` route，并登记 `design_decision_id`、`v6_rule_ids`、反向证据、撤回条件和行动上限。
- `max-blocked/progress`：只有真实的材料、权限、工具、安全边界或用户中止阻断时使用，并登记已完成读态与恢复入口。

`max-artifact-incomplete:<registered-reason>` 是派生交付标签，不是运行档位。run contract 从 `not_run` 开始，由 validator 在检查后写入 `passed` 或 `failed`；failed 必须先重置为 `not_run` 才能重验。校验前只能写 `pending-validator`，只有 fresh passed complete report 可以宣称 `max-complete`。失败标签统一为 `max-validation-failed:<profile>:<first-error-type>`。

Max 的完成条件不是“写得很长”，而是结构产物能通过校验：`max-read-ledger.json` 覆盖 v6 源段落，route 概念来自 registry，强判断有 source anchor、反证、降档和撤回条件，设计判断不越过行动上限。`max-essay` 是最终完整解释层，不能只是 `max-dossier` 摘要。

Max 的 validator 不是终点。校验失败时必须生成 `max-validator-report.json` 与 `max-repair-plan.json`，按 `affected_phase` 重置受影响阶段及其下游产物。能补生成的补生成，能重写的只重写对应 Markdown；strict-only 缺口使用 `mark_artifact_incomplete`，证据不足、source anchor 不成立或 concept contract 不存在时必须降档或撤回，不得通过补 marker 伪装完成。artifact-run 校验失败不会抹除已生成产物，但 report 必须投影为 failed 和非 complete 标签。分析 manifest 排除三个控制面 sidecar；report 分别绑定 run contract、manifest 和 inventoried artifact hashes。

Max 相关验证：

```bash
python scripts/validate_crossframe_max_route_ledger_fixtures.py
python scripts/validate_crossframe_max_repair_fixtures.py
python scripts/build_crossframe_max_repair_plan.py --workspace <artifact-dir> --write-report --write-repair-plan
```

---

<a id="promax"></a>
## ProMax 模式

`crossframe-promax` 直接搭载 v8.0，不混入 Max 的 v6 或其它框架版本。它以完整 v8 源快照、概念注册表、概念契约、路由图和可验证运行工件为依据，要求模型穷尽相关概念、给出明确判断、主动举出相似结构、检索可核验案例、攻击自己的结论并登记成立边界与撤回条件。

ProMax 的触发边界比 Max 更窄：它只接受上文列出的四种精确名称。仅说“最大算力”“全尺度”“穷尽推演”仍进入 Max；suite 也不能把普通 Max 或重型任务自动升级为 ProMax。若同一请求同时精确点名 Max 与 ProMax，必须选择 ProMax，且不得回退到 Max。

ProMax 自带生成—反证—校验—修复闭环，最终回答只在工件通过校验后发布。因此它不追加 `crossframe-review`，也不复用 Max 的 repair 或 audit 链。

---

<a id="closure"></a>
## 质量闭环

CrossFrame 的关键不是“多写几个步骤”，而是让 AI 对自己的判断交账：

```text
source_id -> claim_id -> concept contract -> source anchor -> review -> inquiry
```

- `source ledger` 使用十字段口径，必须说明每个 `source_id` 支持哪个 `claim_id`，以及不能证明什么。
- `claim ledger` 约束中心命题、机制句、行动建议、公共定性、文章转译和高风险概念判断。
- `concept contract` 防止责任链、开放断言、权力封闭、低条件行动等概念被当成口号或标签。
- `crossframe-review` 检查正文是否强于台账、生成层是否自我盖章、证据档位是否越界。
- `crossframe-inquiry` 在完整链路后复用上游台账和 review 结果，继续追问、反证、补证和迁移。

默认不展示内部 reasoning、工具调用参数、路径试错、错误栈或英文自我规划。用户可见输出只保留必要的推理提纲、证据边界、判断档位、结论和下一步。

---

<a id="skills"></a>
## Skill 地图

| Skill | 用途 |
| --- | --- |
| `crossframe-suite` | 总调度入口，决定连续工作流 |
| `crossframe` | 结构诊断核心层 |
| `crossframe-max` | v6 世界观前置 meta-runtime，把对象当作局部世界完成最大化推演、完整解释或设计审查 |
| `crossframe-promax` | v8-only、精确点名的独立推演 runtime，内置穷尽、反证、校验和修复闭环 |
| `crossframe-essay` | 把结构诊断转成完整中文文章 |
| `crossframe-review` | 审查推理、证据边界和输出质量 |
| `crossframe-dialogue` | 读者答复、编辑回信、咨询式短答 |
| `crossframe-casebook` | 把材料整理成可复用案例 |
| `crossframe-history` | 历史材料、史料边界、长时段制度问题 |
| `crossframe-public` | 公共议题、平台治理、政策和机构责任 |
| `crossframe-org` | 团队、项目和组织修复 |
| `crossframe-teach` | 概念讲解、误读纠偏和练习 |
| `crossframe-debate` | 命题辩论、正反结构和撤回条件 |
| `crossframe-notebook` | 读书、理论、文章和摘录研究笔记 |
| `crossframe-critical` | 点名调用的结构批判长文 |
| `crossframe-inquiry` | 完成态后的结构追问、反证、补证和迁移 |

---

<a id="docs"></a>
## 文档

| 文档 | 内容 |
| --- | --- |
| [WHAT_IS_CROSSFRAME.md](docs/WHAT_IS_CROSSFRAME.md) | 普通人版介绍 |
| [QUICKSTART.md](docs/QUICKSTART.md) | 5 分钟上手和验证命令 |
| [CONCEPTS.md](docs/CONCEPTS.md) | claim ledger、source ledger、concept contract、review、inquiry |
| [WORKFLOWS.md](docs/WORKFLOWS.md) | 常见任务链路 |
| [EXAMPLES.md](docs/EXAMPLES.md) | 精简输入、工作流和输出摘要 |
| [ADAPTERS.md](docs/ADAPTERS.md) | Codex、Claude、Cursor、Gemini、Copilot 等适配方式 |
| [SAFETY_AND_LIMITS.md](docs/SAFETY_AND_LIMITS.md) | 安全边界和公开发布限制 |
| [FAQ.md](docs/FAQ.md) | 常见问题 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更 |

---

<a id="principles"></a>
## 输出原则

CrossFrame 输出应当：

- 先给简短推理提纲，再给正式回答。
- 区分事实、解释、机制候选和判断档位。
- 不把结构诊断写成人格审判。
- 不把证据不足的判断写成已经闭合。
- 不把复杂问题压缩成口号、鸡汤或责任稀释。
- 面向普通中文读者，尽量少堆术语。
- 公共、机构、历史和现实事实相关内容必须保留证据边界。
- 文章输出要先有结构洞察，再进入正文。

---

## License

MIT License. See [LICENSE](LICENSE).
