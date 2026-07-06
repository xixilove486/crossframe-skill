# CrossFrame Max v6 Core Concept Contracts

本文件是 `crossframe-max` 的 v6 核心概念契约层。它只规定运行时的概念准入、禁用、证据输入、降档、停止和撤回条件；它不替代 `references/v6-full-source/`。最终产物必须把中心判断回指到 `source_paragraph_ids`，并在 `max-claim-ledger.json`、`max-concept-hit-ledger.json` 与 `max-evidence-reasoning-audit.json` 中登记。

## Contract Format

- `allowed_when`：概念可以被启用的边界条件。
- `forbidden_when`：概念会扭曲 v6 语义的禁用条件。
- `required_inputs`：启用前必须读取、确认或登记的输入。
- `downgrade_if`：必须降档、拆分、暂停或转入候选的条件。
- `stop_if`：必须停止继续推出结论的停止条件。
- `withdraw_if`：已经形成的判断必须撤回的撤回条件。

通用硬规则：

- 没有 `source_paragraph_ids`，不得把概念写成最终依据。
- 没有非工具性证据、非占有性证据、真实成本与边界条件，不得把行动升格为开放性承担行动。
- 没有停止条件和撤回条件，不得形成强判断或行动建议。
- 概念契约只能约束判断强度，不能越过事实、伤害、责任链、低权力主体保护和材料边界。

## 结构域

- `allowed_when`：对象可以被界定为一个有边界、角色、资源、反馈、记忆、接口和承接关系的局部世界。
- `forbidden_when`：对象只是标签、情绪、人格归类、道德评价或单点事件，尚未建立结构变量。
- `required_inputs`：对象边界、尺度层级、行动主体、承接主体、资源/反馈/记忆通道、相关 `source_paragraph_ids`。
- `downgrade_if`：边界说不清、主体位置缺失、尺度被混写，或局部世界无法与材料对应。
- `stop_if`：继续解释会把未给材料的对象补成完整世界。
- `withdraw_if`：发现对象边界设错，或关键主体/尺度完全不在本轮材料中。

## 行动承接层

- `allowed_when`：可以说明谁在行动之后承担真实成本、风险、解释劳动、修复劳动、情绪压力、维护债或连续性压力。
- `forbidden_when`：把行动承接层当成“主角”“责任人”“受害者”或“谁比较重要”的同义词。
- `required_inputs`：成本链、权力位置、退出条件、承接者可见度、低权力主体保护、相关 `source_paragraph_ids`。
- `downgrade_if`：无法指出成本如何转移、由谁承接、是否写回结构。
- `stop_if`：材料只能证明有人行动，不能证明有人承接。
- `withdraw_if`：后续证据显示成本由另一个主体承担，或所谓承接只是叙事姿态。

## 动力—承接链

- `allowed_when`：可以描述动力、资源、信任、压力、责任或伤害如何启动、转译、传递、被接住或失效。
- `forbidden_when`：只讲动机故事、性格推断或情绪因果，没有通道、接收端和反馈回路。
- `required_inputs`：启动端、传递通道、接收端、失效点、回流路径、维护债、相关 `source_paragraph_ids`。
- `downgrade_if`：无法识别承接端，或链条只停留在“因为 A 所以 B”的直线叙述。
- `stop_if`：缺少中间通道，继续推理会把想象路径写成机制。
- `withdraw_if`：反向证据显示动力没有进入承接结构，或承接链被外部变量截断。

## 反馈写回

- `allowed_when`：反馈确实改变规则、资源、角色、边界、记忆、能力、接口或责任配置。
- `forbidden_when`：把表达、抱怨、道歉、复盘、会议、评分、安慰或情绪宣泄当成结构改变。
- `required_inputs`：反馈来源、接收接口、写回目标、改变证据、未写回证据、相关 `source_paragraph_ids`。
- `downgrade_if`：只能证明反馈被听见，不能证明反馈改变结构。
- `stop_if`：反馈没有进入任何可验证的规则、资源、角色或边界。
- `withdraw_if`：后续证据显示所谓写回只是表演性记录或延迟性安抚。

## 结构负荷

- `allowed_when`：可以识别维护债、隐藏成本、过载、熵增、恢复能力下降或虚稳态维持成本。
- `forbidden_when`：把一般压力、痛苦、复杂性、忙碌或冲突直接叫作结构负荷。
- `required_inputs`：负荷承接者、维护机制、资源消耗、时间累积、恢复窗口、相关 `source_paragraph_ids`。
- `downgrade_if`：无法说明哪个结构必须持续运转，或负荷如何积累。
- `stop_if`：材料只能证明主观疲惫，不能证明结构性维护成本。
- `withdraw_if`：证据显示负荷是短期扰动，未进入持续结构。

## 开放性承担行动

- `allowed_when`：行动承担了真实成本，同时保留对方自由、边界、拒绝权、退出权和未来可能性；行动不把成本转成债权。
- `forbidden_when`：用爱要求忍耐、取消责任、取消边界、道德化牺牲，或把控制、占有、补偿、角色依赖、道德表演写成爱。
- `required_inputs`：真实成本、非工具性证据、非占有性证据、自由保留、边界条件、低权力主体保护、停止条件、撤回条件、相关 `source_paragraph_ids`。
- `downgrade_if`：行动带有交换、控制、债权化、回报压力、身份绑定或顺从要求。
- `stop_if`：无法区分开放行动与创伤重复、拯救幻想、补偿冲动或权力策略。
- `withdraw_if`：发现行动主要服务于占有、控制、道德表演、债权化、角色依赖，或要求受伤害者继续承接。

## 解释准入

- `allowed_when`：材料边界、对象边界、证据状态、主体保护和输出风险允许进行结构解释。
- `forbidden_when`：用框架强行解释证据缺席、沉默主体、隐私材料、不可访问经验或需要保护的对象。
- `required_inputs`：材料来源、事实/解释区分、缺席主体、输出用途、风险边界、相关 `source_paragraph_ids`。
- `downgrade_if`：解释超过证据、遮蔽未知、消除不确定性，或把模型语言写成现实终审。
- `stop_if`：继续解释会伤害低权力主体、暴露隐私、制造强者背书或扩大反身性风险。
- `withdraw_if`：发现材料来源不可靠、关键证据相反，或解释对象不应被公开结构化。

## 工具准入

- `allowed_when`：诊断、评分、表格、审计、模板或输出工具有足够输入，且行动边界清楚。
- `forbidden_when`：工具被当作权威认证、处分授权、惩罚机制、人格判决或现实终审。
- `required_inputs`：工具用途、输入范围、输出上限、不能证明什么、受影响主体、回滚方式、相关 `source_paragraph_ids`。
- `downgrade_if`：工具不能说明自身盲区、误伤对象、使用边界和撤回条件。
- `stop_if`：工具输出会直接变成处置、定性、惩罚或公开标签。
- `withdraw_if`：发现工具输入不完整、尺度错配、误伤低权力主体，或被用于契约外用途。

## 强判断

- `allowed_when`：source_anchor、`source_paragraph_ids`、外部事实来源、反向证据状态、推理链、降档条件、撤回条件和行动上限同时存在。
- `forbidden_when`：从框架推演、语感、单一材料、词命中、风格印象或动机猜测直接形成强判断。
- `required_inputs`：claim_id、来源台账、概念命中台账、举证链、推理链、反向证据、校准回合、公开边界。
- `downgrade_if`：强判断八件套缺任一项，或反向证据尚未检查。
- `stop_if`：没有停止条件、撤回条件、行动上限或低权力主体保护。
- `withdraw_if`：关键反例成立、来源被推翻、主体位置错置，或行动上限被输出突破。

## 低条件试探行动

- `allowed_when`：下一步行动低风险、可逆、可观察、可停止、边界清楚，并保护低权力主体。
- `forbidden_when`：借“试探”施压、测试忠诚、绕过同意、制造债务、扩大暴露或把不确定判断转成行动命令。
- `required_inputs`：行动条件、范围、观察信号、停止条件、回滚方式、伤害上限、受影响主体、相关 `source_paragraph_ids`。
- `downgrade_if`：行动无法停止、无法回滚、无法观察，或失败会增加伤害。
- `stop_if`：行动会把候选判断变成现实压力。
- `withdraw_if`：对象拒绝、风险升高、观察信号反向，或行动开始服务于控制/证明而非保护。

## 观测反身性

- `allowed_when`：命名、诊断、评分、发布、检索、引用或干涉会改变对象行动链，需要把观察者纳入局部世界。
- `forbidden_when`：把分析输出当成无后果、无位置、不会改变对象的旁观描述。
- `required_inputs`：观察者位置、发布边界、受影响主体、策略性表演风险、二次伤害风险、相关 `source_paragraph_ids`。
- `downgrade_if`：输出路径、受众、使用场景或对象反应不可知。
- `stop_if`：继续公开会改变证据、扩大伤害、触发报复或制造错误安全感。
- `withdraw_if`：发现本次分析已经成为对象压力源，或被强势主体用于背书/处分。

## 权力封闭度

- `allowed_when`：结构限制申诉、退出、反证、纠错、低权力主体可见性、规则修订或责任追索。
- `forbidden_when`：把权力封闭度简化为个人强势、坏人、控制欲或单一机构标签。
- `required_inputs`：正式通道、非正式通道、申诉路径、退出路径、反证路径、回应义务、报复风险、相关 `source_paragraph_ids`。
- `downgrade_if`：没有检查正式/非正式通道，或只凭结果反推封闭。
- `stop_if`：材料不足以判断通道是否存在、是否可用、是否有报复成本。
- `withdraw_if`：发现有效申诉/退出/反证/纠错通道真实存在，并且低权力主体可安全使用。

## 时间不可逆

- `allowed_when`：判断依赖修复窗口、路径依赖、不可复原损失或已发生行动对后续结构的约束。
- `forbidden_when`：把不可逆写成宿命论、历史必然、放弃修复或追责取消。
- `required_inputs`：时间窗口、已发生行动、不可复原部分、可新建结构、相关 `source_paragraph_ids`。
- `downgrade_if`：只能说明时间经过，不能说明结构窗口或损失已经改变。
- `stop_if`：继续推理会把可修复对象写成不可挽回。
- `withdraw_if`：后续证据显示关键窗口仍存在，或所谓损失可以通过新结构承接。

## 演化记忆

- `allowed_when`：可以识别经验、失败教训、制度资产/负债、记忆载体或跨阶段继承机制。
- `forbidden_when`：把情绪记忆、怀旧叙事或宣传口号直接写成可继承结构资产。
- `required_inputs`：记忆内容、载体、继承路径、污染风险、清除/保存边界、相关 `source_paragraph_ids`。
- `downgrade_if`：无法说明记忆如何被记录、传递、再解释或进入下一轮行动。
- `stop_if`：材料只支持个人回忆，不支持结构性继承。
- `withdraw_if`：发现记忆被系统性篡改、清除、污染，或主要服务于创伤再生产。

## 有序退场

- `allowed_when`：结构修复不再安全或不再必要，需要保护主体、转移资源、保存记忆和外部承接。
- `forbidden_when`：把退场写成逃避责任、抛弃低权力主体、终止追责或浪漫化牺牲。
- `required_inputs`：退场触发条件、受影响主体、资源转移、记忆保存、留下者保护、相关 `source_paragraph_ids`。
- `downgrade_if`：退出路径、承接对象或保护条件不清楚。
- `stop_if`：退场建议会增加暴露、报复、资源剥夺或责任断裂。
- `withdraw_if`：出现可安全修复路径，或退场条件被证明尚未触发。

## 不可穷尽声明

- `allowed_when`：材料、视角、主体位置、外部事实或未来路径仍有不可消除缺口。
- `forbidden_when`：用不可穷尽掩盖证据不足、逃避判断、制造神秘化或免除撤回义务。
- `required_inputs`：已读边界、未读队列、不可判断区、撤回条件、下一步补证入口、相关 `source_paragraph_ids`。
- `downgrade_if`：不可穷尽声明没有指明具体缺口或补证路径。
- `stop_if`：继续输出会把未穷尽材料写成终审。
- `withdraw_if`：后续补证消除了相关缺口，或声明被用来阻止反证。

## 正当不透明

- `allowed_when`：隐私、沉默、非文本证据、低权力主体安全或位置遮蔽构成合理不可完全解释边界。
- `forbidden_when`：把不透明当作免证、拒绝复核、权力遮蔽或概念神秘化。
- `required_inputs`：不透明来源、保护对象、可说边界、不可说边界、替代证据、相关 `source_paragraph_ids`。
- `downgrade_if`：无法区分保护性不透明与证据缺席。
- `stop_if`：继续解释会暴露隐私、制造二次伤害或强迫主体自证。
- `withdraw_if`：发现不透明被强势主体用于逃避责任或压制申诉。

## 状态坐标与生命周期

- `allowed_when`：需要描述对象在特定层级、时间窗口和结构变量组合下的阶段位置。
- `forbidden_when`：把阶段当成线性命运、价值等级、全体对象必经路径或进步叙事。
- `required_inputs`：对象、层级、时间窗口、并行子系统、反向条件、暂停判断条件、相关 `source_paragraph_ids`。
- `downgrade_if`：状态判断缺少尺度、窗口或可撤回条件。
- `stop_if`：继续推理会从阶段标签直接推出命运。
- `withdraw_if`：后续证据显示对象处于并行状态、回退、休眠、分裂或外部接管。

## 非线性路径库

- `allowed_when`：对象可能出现跳阶、回退、休眠、分裂、合并、外部接管、吞并或良性消亡。
- `forbidden_when`：把路径库当成任意想象、单一路径预言或反事实文学。
- `required_inputs`：当前坐标、候选路径、触发条件、反向条件、路径置信、相关 `source_paragraph_ids`。
- `downgrade_if`：路径缺少触发条件、证据锚点或置信分层。
- `stop_if`：材料不足以区分路径候选。
- `withdraw_if`：关键触发条件被证伪，或路径已被现实事件排除。

## 路径置信分层

- `allowed_when`：多个未来路径或历史解释路径并存，需要区分高/中/低置信和不可判断区。
- `forbidden_when`：把低置信路径写成结论，或用概率词包装无证据猜测。
- `required_inputs`：路径列表、支持证据、反向证据、触发条件、撤回条件、相关 `source_paragraph_ids`。
- `downgrade_if`：无法说明路径之间的证据差异。
- `stop_if`：路径分层会制造确定性幻觉或行动误导。
- `withdraw_if`：新证据改变路径排序，或某路径进入不可判断区。

## 虚稳态

- `allowed_when`：表面稳定依赖高维护债、反馈失真、低恢复余量或指标健康掩盖脆弱性。
- `forbidden_when`：把任何稳定、忙碌、压力或短期平静都叫作虚稳态。
- `required_inputs`：稳定表象、维护成本、反馈失真、恢复余量、破裂信号、相关 `source_paragraph_ids`。
- `downgrade_if`：只能证明系统稳定，不能证明稳定依赖隐藏成本。
- `stop_if`：缺少负荷承接者或反馈失真证据。
- `withdraw_if`：证据显示稳定来自真实恢复能力，而非维护债遮蔽。

## 干涉授权

- `allowed_when`：从解释进入行动、修复、保护、撤离、治理或资源配置建议前，需要确认授权和上限。
- `forbidden_when`：从诊断直接跳到处分、惩罚、公开标签、资源剥夺或现实处置。
- `required_inputs`：行动目的、授权来源、受影响主体、停止条件、回滚方式、行动上限、相关 `source_paragraph_ids`。
- `downgrade_if`：授权来源、风险边界或回滚机制不清楚。
- `stop_if`：行动会越过事实、法律、伦理、低权力主体保护或用户授权。
- `withdraw_if`：发现授权不存在、主体拒绝、风险升高或行动被误用。

## 低权力主体保护

- `allowed_when`：判断或行动可能影响受害者、沉默者、退出者、无法申诉者或低可见主体。
- `forbidden_when`：用保护名义代替主体意愿、制造公开暴露、要求继续承接或取消责任链。
- `required_inputs`：低权力主体位置、风险、退出权、申诉权、反报复保护、相关 `source_paragraph_ids`。
- `downgrade_if`：无法识别受影响主体或其安全条件。
- `stop_if`：输出会增加二次伤害、报复、曝光或证明负担。
- `withdraw_if`：主体位置判断错误，或保护建议被强势主体利用。

## 责任链硬规则

- `allowed_when`：需要防止意义、爱、复杂性、疗愈或组织利益取消伤害事实和补证义务。
- `forbidden_when`：把责任链简化为道德归罪、人格审判或单向惩罚。
- `required_inputs`：伤害事实、责任主体、补证义务、保护边界、不可取消条件、相关 `source_paragraph_ids`。
- `downgrade_if`：事实、责任、补证义务或主体边界缺任一项。
- `stop_if`：继续解释会替代正式调查或扩大无证据定责。
- `withdraw_if`：关键事实被推翻，或责任主体位置设错。

## T0-T4 恢复与再承接

- `allowed_when`：需要把修复、疗愈、保护、再承接、撤离或转移排列为可停止的操作阶段。
- `forbidden_when`：把 T0-T4 当成线性康复剧本、强迫和解路径或继续忍耐义务。
- `required_inputs`：安全条件、信任载体、修复接口、再承接条件、撤离触发、相关 `source_paragraph_ids`。
- `downgrade_if`：阶段条件、停止权或回滚路径不清楚。
- `stop_if`：修复建议会压低安全条件或要求低权力主体继续承接。
- `withdraw_if`：T0 安全条件失效，或 T4 触发条件成立。

## 过程性产物边界

- `allowed_when`：输出是 AI 报告、审查、诊断、台账、模板、评分或其他过程性材料。
- `forbidden_when`：过程性产物被写成事实证明、现实终审、处分授权或机构结论。
- `required_inputs`：产物用途、输入边界、不能证明什么、复核入口、撤回条件、相关 `source_paragraph_ids`。
- `downgrade_if`：产物缺少边界、复核或撤回机制。
- `stop_if`：产物会直接进入现实处置、公开定性或资源分配。
- `withdraw_if`：发现产物被用于契约外用途或越过行动上限。

## 来源-证据-判断-行动上限

- `allowed_when`：任何 claim 需要从来源进入证据链、判断档位和行动边界。
- `forbidden_when`：只给来源编号、不说明证据能证明什么、不能证明什么和行动上限。
- `required_inputs`：source_anchor、source_paragraph_ids、claim_id、证据档位、反向证据、行动上限。
- `downgrade_if`：来源、证据、判断或行动上限任一环缺失。
- `stop_if`：没有反证入口或撤回条件。
- `withdraw_if`：来源失效、证据不支持 claim，或行动上限被输出突破。

## 开放断言

- `allowed_when`：证据不足以终审，但足以形成低强度、可追问、可撤回的候选陈述。
- `forbidden_when`：把开放断言包装成确定结论、公共定性或行动命令。
- `required_inputs`：claim_id、证据边界、反证入口、降档条件、撤回条件、相关 `source_paragraph_ids`。
- `downgrade_if`：开放断言缺少可检验条件或撤回路径。
- `stop_if`：表达会被读成强判断或现实授权。
- `withdraw_if`：反证成立，或材料边界不足以保留候选判断。

## 命题验证表

- `allowed_when`：需要逐条检查 claim 的来源、证据、概念、推理、反证、降档和撤回条件。
- `forbidden_when`：把表格填写当成证明，或用格式完整替代证据有效。
- `required_inputs`：claim、source_anchor、concept_ids、evidence_status、counterevidence、downgrade_condition、withdrawal_condition。
- `downgrade_if`：任一验证项为空、泛化或无法回指材料。
- `stop_if`：命题验证表不能区分事实、推断和行动建议。
- `withdraw_if`：表格回指失效、claim 被拆分，或反向证据改变判断。

## 强判断八件套

- `allowed_when`：强判断必须同时具备来源、证据、推理、概念契约、反证、校准、撤回和行动上限。
- `forbidden_when`：从词命中、概念密度、语感、单一材料或框架推演直接形成强判断。
- `required_inputs`：source_anchor、source_paragraph_ids、claim_id、concept_ids、counterevidence、calibration_rounds、withdrawal_condition、action_limit。
- `downgrade_if`：八件套任一项缺失、空泛或不能回指材料。
- `stop_if`：强判断会替代调查、法律程序、医疗心理判断或机构审查。
- `withdraw_if`：关键来源失效、反例成立、主体位置错置或行动上限被突破。

## 反模型殖民

- `allowed_when`：AI、模型语言、评分、诊断或模板可能压过现实主体、材料边界或专业程序。
- `forbidden_when`：把反模型殖民当成拒绝工具、拒绝证据或拒绝自动化的口号。
- `required_inputs`：模型位置、受影响主体、输出路径、现实后果、复核入口、相关 `source_paragraph_ids`。
- `downgrade_if`：无法说明模型语言如何进入现实结构。
- `stop_if`：输出会成为强势主体背书、处分依据或事实替代。
- `withdraw_if`：确认输出只在低风险内部草稿中使用且有明确复核边界。

## 反领域殖民

- `allowed_when`：一个领域的话语、指标、专业接口或制度逻辑正在吞并其他领域判断边界。
- `forbidden_when`：把跨领域引用、专业协作或必要翻译都视为殖民。
- `required_inputs`：领域边界、接口关系、被吞并对象、替代证据、复核机制、相关 `source_paragraph_ids`。
- `downgrade_if`：只能证明领域差异，不能证明越权吞并。
- `stop_if`：继续输出会取消必要专业接口或制造反专业姿态。
- `withdraw_if`：证据显示领域接口有授权、复核和边界保护。

## 概念武器化

- `allowed_when`：概念、框架、理论或诊断语言被用于压制申诉、定罪、羞辱、消除复杂性或越权处置。
- `forbidden_when`：把严肃批评、边界提醒或证据要求都说成概念武器化。
- `required_inputs`：使用者位置、被影响主体、概念用途、现实后果、反证与撤回条件、相关 `source_paragraph_ids`。
- `downgrade_if`：无法说明概念如何造成现实压制或行动越界。
- `stop_if`：判断本身会变成新的概念武器。
- `withdraw_if`：后续证据显示概念只是内部分析工具，未进入压制或处置链。
