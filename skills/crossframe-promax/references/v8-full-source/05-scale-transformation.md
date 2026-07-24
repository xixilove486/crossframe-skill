# 第五部分　跨尺度与跨圈层变换

Source SHA256: `3186805a3e46e1b16948a4e51d08e7693a8e0dd04aa6b4604e796266d649936c`
Source role: `05-scale-transformation`
Paragraph range: `V8-P0807`-`V8-P0995`
Paragraph count: `189`

## Source Paragraphs

<!-- source_paragraph:V8-P0807 style=1 -->
第五部分　跨尺度与跨圈层变换

<!-- source_paragraph:V8-P0808 style= -->
本部分回答：对象、观察或行动从 SP0 变到 SP1 时，哪些内容得到扩展，哪些内容发生收缩，哪些位置不可比较，凭什么建立转换桥，以及什么信息会在转换中丢失。一般过程统称尺度变换；只有九轴积偏序严格成立时，才称尺度升格。

<!-- source_paragraph:V8-P0809 style=21 -->
一、合同角色与无歧义引用

<!-- source_paragraph:V8-P0810 style= -->
九个尺度轴是 D 类定义，角色为 scale_axis_definition；九个转换算子是 O 类程序，角色为 scale_transformation_operator；U01—U11 是 D 类通用原语定义，角色为 universal_primitive_definition。定义和程序不冒充经验真值，具体跨层因果、对象转换或零结论必须链接预注册 root-instance。

<!-- source_paragraph:V8-P0811 style=af -->
尺度实体一律使用限定 ID：scale_axis:A 至 scale_axis:J、scale_operator:M01 至 scale_operator:M09、universal_primitive:U01 至 universal_primitive:U11。因此，scale_axis:O 表示组织层级，claim_type=O 表示操作程序，二者不会混淆。依赖只分为 inferential_requires、protocol_requires、specializes 和 applies_to；协议使用 CAUSAL、EVIDENCE、ANALOGY、SOURCE 等正式 ID，不使用中文简称或裸轴名。

<!-- source_paragraph:V8-P0812 style=21 -->
二、九轴状态与逐轴比较

<!-- source_paragraph:V8-P0813 style= -->
每个对象和变换绑定：

<!-- source_paragraph:V8-P0814 style=af -->
SP=<A,X,T,O,C,R,I,N,J>

<!-- source_paragraph:V8-P0815 style= -->
轴

<!-- source_paragraph:V8-P0816 style= -->
状态字段核心

<!-- source_paragraph:V8-P0817 style= -->
expands 的计算见证

<!-- source_paragraph:V8-P0818 style= -->
不可替代边界

<!-- source_paragraph:V8-P0819 style= -->
A 聚合层次

<!-- source_paragraph:V8-P0820 style= -->
单位、成员集、分区、聚合规则、权重、排除项

<!-- source_paragraph:V8-P0821 style= -->
目标总体覆盖源总体，目标分区是源分区的登记粗化

<!-- source_paragraph:V8-P0822 style= -->
不得由 O、X、I 或 J 替代

<!-- source_paragraph:V8-P0823 style= -->
X 空间范围

<!-- source_paragraph:V8-P0824 style= -->
坐标系、空间集合、边界通道、外部连接

<!-- source_paragraph:V8-P0825 style= -->
坐标对齐后源空间是真子集

<!-- source_paragraph:V8-P0826 style= -->
不得由 A、O、I 或 J 替代

<!-- source_paragraph:V8-P0827 style= -->
T 时间跨度

<!-- source_paragraph:V8-P0828 style= -->
时间基准、窗口角色、起止点、时滞模型

<!-- source_paragraph:V8-P0829 style= -->
同一基准与角色下目标区间真包含源区间

<!-- source_paragraph:V8-P0830 style= -->
当前截面和长期路径不能互代

<!-- source_paragraph:V8-P0831 style= -->
O 组织层级

<!-- source_paragraph:V8-P0832 style= -->
组织图、版本、节点、包含边、接口、重叠

<!-- source_paragraph:V8-P0833 style= -->
同版组织 DAG 中目标节点覆盖源节点祖先闭包

<!-- source_paragraph:V8-P0834 style= -->
组织上位不等于 J 扩大

<!-- source_paragraph:V8-P0835 style= -->
C 因果层次

<!-- source_paragraph:V8-P0836 style= -->
因果模型、变量、边、干预语义、抽象映射

<!-- source_paragraph:V8-P0837 style= -->
目标模型经语义保持映射覆盖源模型并增加可区分层面

<!-- source_paragraph:V8-P0838 style= -->
层级标签、时序和相关不能代替因果桥

<!-- source_paragraph:V8-P0839 style= -->
R 观察分辨率

<!-- source_paragraph:V8-P0840 style= -->
测量协议、可区分类、参数、误差、保护性省略

<!-- source_paragraph:V8-P0841 style= -->
目标协议保留源协议全部区分并至少细分一类

<!-- source_paragraph:V8-P0842 style= -->
高分辨率不等于完整或有权行动

<!-- source_paragraph:V8-P0843 style= -->
I 影响范围

<!-- source_paragraph:V8-P0844 style= -->
结果、阈值、窗口、受影响位置、效应阶次

<!-- source_paragraph:V8-P0845 style= -->
对齐后目标受影响位置集真包含源集合

<!-- source_paragraph:V8-P0846 style= -->
影响和观察均不等于授权

<!-- source_paragraph:V8-P0847 style= -->
N 网络拓扑范围

<!-- source_paragraph:V8-P0848 style= -->
图与版本、节点、边、语义、采样边界

<!-- source_paragraph:V8-P0849 style= -->
存在语义保持图嵌入且目标覆盖源图

<!-- source_paragraph:V8-P0850 style= -->
网络中心不等于责任中心

<!-- source_paragraph:V8-P0851 style= -->
J 管辖与授权范围

<!-- source_paragraph:V8-P0852 style= -->
原子授权元组集合；每个元组固定来源、主体、单一对象、单一动作、地域、期限、撤回、有效性和证据

<!-- source_paragraph:V8-P0853 style= -->
目标有效原子元组规范化集合真包含，且每个新增元组有独立有效性见证

<!-- source_paragraph:V8-P0854 style= -->
任何其他轴均不能替代 J；禁止对象集与动作集做笛卡尔积

<!-- source_paragraph:V8-P0855 style=af -->
每轴关系只有五种：equal、expands、contracts、incomparable、unknown。轴比较记录固定包含 axis_id、源/目标状态、关系、顺序见证、信息损失和不确定性。非未知关系的 order_witness 不是一句说明，而是闭合对象：comparator_id 与 comparator_version 必须对应该轴比较器，verifier_id 明确谁或什么执行验证，evidence_refs 非空，comparison_payload 给出实际映射、集合、区间、图或授权差异，verification_artifact_ref 与 verification_hash 指向可复核产物，validation_status 必须为 valid。unknown 使用带理由的缺失状态。完全相同的两状态可用内置深相等复算 equal；其他相等以及全部扩展、收缩和不可比关系，都必须从外部比较器结果注册表核对轴、版本、源/目标摘要、关系和哈希。相同状态申报扩展或收缩直接失败。没有可解析见证，只能记 unknown；contracts 是同轴 expands 的逆关系，不是凭语言印象标注。

<!-- source_paragraph:V8-P0856 style=af -->
“九轴都要登记”不等于“九轴对一切对象都适用”。某轴整体确实不适用时，轴状态使用带理由的 not_applicable 对象，而不是删掉该轴。典型例子是没有行动主体和授权概念的自然过程：其 J 轴不适用，不等于“存在一个空授权集合”。源、目标两端经同一适用性判据均不适用时，该轴可在见证中记为 equal；仅一端不适用而另一端适用时，语义域已经改变，应记 incomparable；材料不足仍记 unknown。这样既保持九轴接口稳定，也不把人类制度语义强塞进广义世界。

<!-- source_paragraph:V8-P0857 style=af -->
每个轴状态都须满足反身性、反对称性和传递性。为避免“差一点相等”破坏传递，轴状态先按 equality_rule 形成规范化等价类，偏序在这些等价类的商集上定义；容差只能通过预注册的共同规范化器或固定分箱把两端送入同一等价类，不能用任意两点之间“距离小于阈值”直接定义相等。反身性要求规范化状态与自身为 equal；反对称性要求双向不大于只能落入同一等价类；传递性只在中间状态、版本和见证可组合时成立，任何映射、坐标、图版本、变量或授权链断裂都会使关系回到 unknown。

<!-- source_paragraph:V8-P0858 style=af -->
每轴的主比较量成立还不够。若该轴记录含边界通道、时滞模型、接口、误差模型、干预语义或保护性省略等辅助状态，expands 还要求这些字段存在可组合的语义保持映射；主范围扩大而辅助语义发生无映射冲突时，只能登记 incomparable 或 unknown。这使“范围更大”不会偷渡成“整个轴状态更高”。

<!-- source_paragraph:V8-P0859 style=21 -->
三、积偏序与变换分类

<!-- source_paragraph:V8-P0860 style= -->
SP0≼SP1 当且仅当九轴全部为 equal 或 expands；严格关系 SP0≺SP1 还要求至少一轴 expands。机器分类按以下顺序执行：

<!-- source_paragraph:V8-P0861 style= -->
任一轴 incomparable：horizontal_or_incomparable；已知不可比不会被另一轴的未知覆盖；

<!-- source_paragraph:V8-P0862 style= -->
否则同时出现扩展和收缩：mixed；两种已知方向已经足以排除积偏序，即使还有轴未知；

<!-- source_paragraph:V8-P0863 style= -->
否则任一轴 unknown：unresolved；

<!-- source_paragraph:V8-P0864 style= -->
九轴全 equal：all_equal；

<!-- source_paragraph:V8-P0865 style= -->
仅含 equal/expands 且至少一轴扩展：elevation；

<!-- source_paragraph:V8-P0866 style= -->
仅含 equal/contracts 且至少一轴收缩：reduction。

<!-- source_paragraph:V8-P0867 style= -->
因此，宏观聚合同时压缩观察分辨率时通常是 mixed，不应笼统叫升格；领域类比常是 horizontal_or_incomparable；材料不足时是 unresolved。只有分类为 elevation 的实例才使用“尺度升格”。观察范围、空间范围、组织范围、影响范围或网络范围扩大，都不会改变 J；J 只能由新的有效授权元组见证扩展。

<!-- source_paragraph:V8-P0868 style=af -->
J 状态不是“一个来源 + 一组主体 + 一组对象 + 一组动作”的独立字段拼盘，因为那会凭空生成未被授权的对象—动作组合。authorization_tuple_contract 要求每个原子元组只绑定一个来源、一个决策主体、一个对象和一个动作，同时保存地域、有效期、撤回条件、证据和独立复核；多对象或多动作必须拆成多个元组。只有状态为有效的规范化原子元组进入集合比较。J 轴扩展的见证要在 comparison_payload 中列出目标新增而源端没有的完整元组及其独立有效性证据，并与记录的 j_authorization 对齐。任意字符串、tuple ID、自称、实际控制、观察覆盖、影响扩大、上位组织位置或其他轴的扩展都不能使 J 变为 expands。

<!-- source_paragraph:V8-P0869 style=21 -->
四、所有算子的三态与零结论门

<!-- source_paragraph:V8-P0870 style= -->
每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。

<!-- source_paragraph:V8-P0871 style=af -->
算子程序统一使用四个结果状态：

<!-- source_paragraph:V8-P0872 style= -->
supported：本次选定分支的桥、决策规则和正向阈值已预注册且通过；只有 G、因果、对象/干预转换分支才强制 root-instance、预选子型和唯一成功判据，纯描述分支可把这些 G 专用字段记为 not_applicable；

<!-- source_paragraph:V8-P0873 style= -->
unsupported_or_undecided：桥接不足，或正向门未通过而零结论门也未通过；

<!-- source_paragraph:V8-P0874 style= -->
null_supported：只有预注册 null_decision_rule、等价性或充分性检验、功效或灵敏度及容差全部通过时，才支持限定零结论；

<!-- source_paragraph:V8-P0875 style= -->
not_evaluated：算子或相应分支尚未运行；已运行且描述桥成立的分支可以是 supported，不能因不需要 G-instance 而降为未评估。

<!-- source_paragraph:V8-P0876 style= -->
“未显著”“切断后看似不变”“效应消失”“简单模型表现相当”或“目标证据不足”都不能自动写成 null_supported。这条纪律适用于 M01—M09，而不只适用于跨层因果。

<!-- source_paragraph:V8-P0877 style=21 -->
五、九种尺度变换算子

<!-- source_paragraph:V8-P0878 style= -->
每个算子都有独有 semantic_signature，不能复制 M01 的聚合语句冒充其他算子。

<!-- source_paragraph:V8-P0879 style=31 -->
M01　聚合

<!-- source_paragraph:V8-P0880 style= -->
签名是“单位—总体分区聚合”。最低桥包括逐单位映射、成员与排除、权重与缺失、替代聚合规则和异质性。信息损失包括尾部、次序、协方差、局部时序及少数位置可见度。总体不能按登记规则复现、合理替代规则造成方向反转，或总体关联被回填为个体属性时，程序失败。即使聚合获得支持，也不得据总体结果直接处置成员。

<!-- source_paragraph:V8-P0881 style=31 -->
M02　嵌套

<!-- source_paragraph:V8-P0882 style= -->
签名是“边界—成员嵌入”。它必须分成两条支路：

<!-- source_paragraph:V8-P0883 style= -->
描述性嵌套只检验边界、成员、重叠、退出和接口映射；它可以成立而没有任何跨层因果。

<!-- source_paragraph:V8-P0884 style= -->
跨层因果必须链接预注册 G4a 或 G4b root-instance，固定子型和唯一成功判据，并通过 CAUSAL 与三态/null 门。

<!-- source_paragraph:V8-P0885 style= -->
控制当前状态与共同环境后没有条件增量，并不自动证明“没有跨层作用”；只有等价/充分性、功效/灵敏度和容差门同时通过，才可登记限定零结论。描述性嵌套不生成上位优先、下位义务或 J 轴扩展。

<!-- source_paragraph:V8-P0886 style=af -->
记录时必须在 descriptive_nesting、cross_layer_causal、object_conversion、intervention_conversion 中选一支，并分别绑定描述、因果、对象转换或干预转换模式；不得用描述性嵌套的边界材料支持后面三支。

<!-- source_paragraph:V8-P0887 style=31 -->
M03　网络传播

<!-- source_paragraph:V8-P0888 style= -->
签名是“沿时间化路径传导”。必须登记节点、边、方向、权重、容量、采样边界、候选与替代路径、时延和损耗。连接或同步只生成候选；切断路径后结果不变而零结论门未通过时，仍是 unsupported_or_undecided。网络采样会遗漏弱边、离网位置和跨网桥，只保留终点影响也不能恢复传播次序。中心性不等于意图、责任或处置权限。

<!-- source_paragraph:V8-P0889 style=31 -->
M04　时间累积

<!-- source_paragraph:V8-P0890 style= -->
签名是“带窗口的纵向组合”。必须冻结时间基准、基线、窗口、时滞、持久阈值和累积/衰减/恢复规则，并比较共同趋势、季节、队列和替代窗口。效应在控制后消失或随窗口变化，只表示正向支持不足；没有通过零结论门，不能发布“无累积”。基础时间组合不预证 G3；只有历史项在控制当前状态后仍提供条件增量时，才链接 G3-instance。

<!-- source_paragraph:V8-P0891 style=31 -->
M05　制度化

<!-- source_paragraph:V8-P0892 style= -->
签名是“持久制度写回”。它把五个判断分开：制度事实上存在、法律有效、规范正当、保护是否成立、是否应继续。记录、角色、资源、决策规则或后续转移发生持久改变，可以支持制度化事实；授权无效、参与不足、保护机制失效、缺少申诉/反报复/回滚属于治理失败、规范争议和行动降级理由，不能据此抹掉制度已存在的事实。反过来，制度存在也不证明它合法、正当、具有充分保护或应继续。

<!-- source_paragraph:V8-P0893 style=af -->
selected_operator_branch 只允许 institutional_fact、institutional_causal_effect、institutional_object_conversion 或 institutional_intervention_conversion。法律有效性审查、治理质量、规范正当性、保护充分性和应否继续没有任何一项能伪装成 institutional_fact 的正向或零结论。

<!-- source_paragraph:V8-P0894 style=31 -->
M06　涌现

<!-- source_paragraph:V8-P0895 style= -->
签名是“互动生成目标尺度模式”。源单位、互动规则、目标对象和目标模式须与预登记简单加和模型在同一指标上比较。简单加和模型表现相当，只在充分性/等价、功效/灵敏度和容差门通过时支持“加和已足够”；否则保持未决。宏观模式不能反推唯一微观原因，也不能自动证明下行因果。下行约束须另链 G4/CAUSAL 实例。

<!-- source_paragraph:V8-P0896 style=31 -->
M07　委托/代表

<!-- source_paragraph:V8-P0897 style= -->
签名是“代表事实分类与可选授权转移”。必须分开记录：代表性主张、实际代行事实、争议或自任代表、有效委托、J 轴权限转移。无授权时仍可记录实际代行及其影响和责任，但不得登记 J 扩展；授权无效会触发停止或降级，却不能把已经发生的代行与后果删除。多数、可见性、影响力、自称或实际控制都不等于有效委托。

<!-- source_paragraph:V8-P0898 style=af -->
记录必须在 representation_claim、actual_acts、delegation_validity、J_transfer 中选一支。前三支即使获得支持也不能改变 J；只有 J_transfer 与结构化授权元组、独立有效性证据和 j_authorization 同时通过时，J 才可扩展。

<!-- source_paragraph:V8-P0899 style=31 -->
M08　压缩/抽象

<!-- source_paragraph:V8-P0900 style= -->
签名是“多对一表示压缩”。源材料、算法、阈值、版本、误差、不可恢复信息和任务所需不变量必须可追踪。unknown、not_applicable、not_observable、withheld_for_protection 必须保持区分，任何一种都不能压成“不存在”。高损失表示不得支持高影响行动。

<!-- source_paragraph:V8-P0901 style=31 -->
M09　横向迁移

<!-- source_paragraph:V8-P0902 style= -->
签名是“跨领域类比迁移”。必须登记映射、差异、断裂、禁止映射、目标责任链和 J 轴差异。源域材料只生成目标候选；supported 或 null_supported 都必须来自独立目标实例。目标证据不足是 not_evaluated 或 unsupported_or_undecided，不是目标机制不存在的证明。类比不生成目标领域行动授权。

<!-- source_paragraph:V8-P0903 style=21 -->
六、通用原语的尺度边界

<!-- source_paragraph:V8-P0904 style= -->
通用原语是 D 类接口，不再携带经验零模型或证伪模板。尤其需要锁住四项边界：

<!-- source_paragraph:V8-P0905 style= -->
U07 的基础反馈只要求返回通道和后续状态更新，不要求 G3；持久历史增量和学习才另检 G3。

<!-- source_paragraph:V8-P0906 style= -->
U09 的瞬时需求—容量缺口不要求 G3；累积损伤或迟恢复才另检历史条件增量。

<!-- source_paragraph:V8-P0907 style= -->
U10 只登记候选痕迹、载体和保留窗口，不预证路径依赖；G3 仍须证明历史项在控制当前状态后的条件增量。

<!-- source_paragraph:V8-P0908 style= -->
U11 的基础相位模式不要求 G3 或 G4；因果触发另检 G2，迟滞另检 G3，对象转换另检 G4。

<!-- source_paragraph:V8-P0909 style= -->
同理，U01 只登记候选对象而不预保证 G1；U05 的关系定义不证明因果；U06 的通道字段不证明通道效应。

<!-- source_paragraph:V8-P0910 style=21 -->
七、统一尺度变换记录

<!-- source_paragraph:V8-P0911 style= -->
每个实例都必须出现十四节和全部字段：

<!-- source_paragraph:V8-P0912 style= -->
节

<!-- source_paragraph:V8-P0913 style= -->
必填字段

<!-- source_paragraph:V8-P0914 style= -->
identity

<!-- source_paragraph:V8-P0915 style= -->
contract_id、concept_id、version、proposition_ids、purpose

<!-- source_paragraph:V8-P0916 style= -->
scale

<!-- source_paragraph:V8-P0917 style= -->
SP0、SP1、九条 axis_differences、unchanged_axes、transformation_class、j_authorization

<!-- source_paragraph:V8-P0918 style= -->
objects

<!-- source_paragraph:V8-P0919 style= -->
源/目标有效对象、source_K、target_K、identity_mapping、单位、总体、边界、成员、排除项

<!-- source_paragraph:V8-P0920 style= -->
semantics

<!-- source_paragraph:V8-P0921 style= -->
preserved_core、allowed_changes、lost_elements、prohibited_mappings

<!-- source_paragraph:V8-P0922 style= -->
transformation

<!-- source_paragraph:V8-P0923 style= -->
单一算子、selected_operator_branch、claim_mode、规则、因果桥、时滞、映射误差、有效期、root-instance、子型、成功判据、正向和零决策规则、正向阈值、等价/充分性检验、功效/灵敏度、容差、结果状态

<!-- source_paragraph:V8-P0924 style= -->
variables

<!-- source_paragraph:V8-P0925 style= -->
输入、状态、输出和跨变量依赖

<!-- source_paragraph:V8-P0926 style= -->
evidence

<!-- source_paragraph:V8-P0927 style= -->
源/目标证据、覆盖、异质性、反例、缺席信号、替代解释、残差检验、复制或外部验证

<!-- source_paragraph:V8-P0928 style= -->
loss

<!-- source_paragraph:V8-P0929 style= -->
压缩细节、不可恢复信息、低可见位置和局部排除区

<!-- source_paragraph:V8-P0930 style= -->
responsibility

<!-- source_paragraph:V8-P0931 style= -->
行动者、决策者、授权者、承接载体、责任主体、受益者和成本承担者

<!-- source_paragraph:V8-P0932 style= -->
normative

<!-- source_paragraph:V8-P0933 style= -->
价值前提、选择类型、规范选择记录、运行时 N 原则、授权来源、C12 门和 O1-O4 程序

<!-- source_paragraph:V8-P0934 style= -->
protection

<!-- source_paragraph:V8-P0935 style= -->
保护适用性、低权力位置、安全提交和反报复

<!-- source_paragraph:V8-P0936 style= -->
action

<!-- source_paragraph:V8-P0937 style= -->
判断上限、行动上限、禁止动作、停止条件、责任人和机器可指向的 selected_action

<!-- source_paragraph:V8-P0938 style= -->
correction

<!-- source_paragraph:V8-P0939 style= -->
申诉、复核、回滚、修复和写回

<!-- source_paragraph:V8-P0940 style= -->
lifecycle

<!-- source_paragraph:V8-P0941 style= -->
有效期、复审点、暂停和退场

<!-- source_paragraph:V8-P0942 style=af -->
source_K、target_K 和 identity_mapping 共同决定对象保持、转换或不可比；同名不是同一性证据。映射记录必须同时保存源、目标 K 的摘要，源对象与目标对象分别在两套 K 下的四项判据结果，正向与反向映射，保持和违反的判据，结果前冻结的预注册引用，以及可复核的验证制品与哈希。判据结果只允许 passed、failed 或 undetermined，不能用一个布尔值掩盖是哪一项没有通过。

<!-- source_paragraph:V8-P0943 style= -->
K 映射分类

<!-- source_paragraph:V8-P0944 style= -->
最低成立条件

<!-- source_paragraph:V8-P0945 style= -->
结果上限

<!-- source_paragraph:V8-P0946 style= -->
same_object

<!-- source_paragraph:V8-P0947 style= -->
双向映射均有效；源对象与目标对象在 source_K、target_K 下四项检查均通过；保持判据非空且违反判据为空

<!-- source_paragraph:V8-P0948 style= -->
可在当前合同内沿用对象身份，但不推出语义、因果或规范性质也保持

<!-- source_paragraph:V8-P0949 style= -->
converted_object

<!-- source_paragraph:V8-P0950 style= -->
source_under_source_K 与 target_under_target_K 通过，target_under_source_K 失败；违反项和结果前预注册引用具体；另有 object_conversion 模式及取得支持的 G4b 实例

<!-- source_paragraph:V8-P0951 style= -->
只登记预注册 K 下的对象转换，不得在结果后改写 K 制造转换

<!-- source_paragraph:V8-P0952 style= -->
incomparable

<!-- source_paragraph:V8-P0953 style= -->
两端各自在本方 K 下通过，至少一个交叉 K 检查失败；正反向映射保存完整尝试记录且至少一项验证为无效，并有可解析证据

<!-- source_paragraph:V8-P0954 style= -->
表示已知不可比，只能 unsupported_or_undecided；不是“尚未评估”

<!-- source_paragraph:V8-P0955 style= -->
undetermined

<!-- source_paragraph:V8-P0956 style= -->
检验尚未运行，或必要映射、判据未知或不可观察；四项结果均保持 undetermined

<!-- source_paragraph:V8-P0957 style= -->
只能 unsupported_or_undecided 或 not_evaluated；不构成不可比或对象转换

<!-- source_paragraph:V8-P0958 style=af -->
只有源/目标对象和两套 K 都可由验证器重算为深相等时，才允许 builtin:deep-identity。其他非平凡保持或对象转换必须把 mapping_id 交给独立 identity_mapping_results 注册表，逐项核对对象摘要、K 摘要、方向映射、四项判据结果、验证制品和哈希；记录内部自报 valid 或一个看似正确的 ID 前缀都不能充当证明。

<!-- source_paragraph:V8-P0959 style=af -->
对象转换模式与结果四态必须一致：supported 才对应 converted_object；null_supported 对应通过零结论三门的 same_object；unsupported_or_undecided 只允许保持、已知不可比或未决；not_evaluated 必须保持 undetermined。因此，未检验和检验失败都不能先把目标写成“已经转换”。其他 claim_mode 也不得在同一条原子记录里兼报 converted_object，对象转换必须拆成自己的原子检验。

<!-- source_paragraph:V8-P0960 style=af -->
claim_mode 为 root_hypothesis、causal、object_conversion 或 intervention_conversion 时必须填写 root_instance_ids，后三者还必须给出非空因果桥；只有 descriptive_mapping 可把 root-instance、子型和成功判据标为 not_applicable。非描述模式登记 supported 或 null_supported 时，还必须向验证器提交可解析的 root-instance 注册表，并核对实例 ID、根族、合同版本、预选子型、唯一成功判据与实例状态；一个看似正确的字符串前缀不能充当实例。描述桥正向门通过时可以记 supported，只有所选模式没有运行时才记 not_evaluated。

<!-- source_paragraph:V8-P0961 style=af -->
十四节是稳定接口，不是把人类治理语义投射给所有对象。protection.applicability 必须显式登记对象类型、下游用途、理由和证据引用，不能从 actors 等空列表反推。对象类型为 nonhuman，且用途只含 description_only 或有证据证明不影响人类/有感主体的 nonhuman_intervention_without_human_or_sentient_effect 时，safe_submission 与 anti_retaliation 可带理由记 not_applicable；但现实实验或工程干预仍有行动主体和对象，必须填写具体 J、行动责任人、停止、复核与回滚，只有纯描述用途才允许 J 不适用。自然系统中的能量、物质或计算资源本身不触发这套人类保护合同。对象为人类、有感非人、混合或未知，或用途涉及人的评价、其稀缺资源配置、权利、暴露风险或现实处置时，保护字段立即成为强制项，不得沿用先前的不适用状态。保护不适用绝不推出行动正当，规范选择仍另行判断。

<!-- source_paragraph:V8-P0962 style=af -->
action_owner 只说明谁负责执行或停止，不能反推 claim_mode=intervention_conversion，也不能证明行动有效或正当。任何外部行动必须链接 selection_record_id，公开 value_premises 与运行时 normative_principle_ids；N1 单独只能阻止越权，不能产生正向方案。选择记录中的 feasible_alternatives 不是名称列表，而是带稳定 option_id 的结构化方案；每项冻结 option_kind、动作类型、目标对象、地域、有效期、可逆性、预期影响和分配影响，并且恰有一项 option_kind=no_action，由 no_action_option_id 唯一指向。selected_action.selected_option_id 必须解析到一项 external_action，而且其动作、对象、地域和有效期与该方案逐项相等；选择不行动 ID、只对上自然语言标签，或同时改写动作与 J 而不改获准方案，都必须被拒绝。至少一条当前有效且独立复核的 J 原子授权元组还必须同时覆盖该主体、对象、动作、地域和期限，并与授权来源一致；一条无关但形式有效的授权不能为拟议行动背书。记录还必须有通过的十组件 c12_gate、O1-O4 procedure_ids、行动责任人、禁止动作、停止、保护、申诉、复核和回滚。缺任一项时，行动上限只能是不行动或继续审议；经验上的干预转换另由相应 root-instance 判断。

<!-- source_paragraph:V8-P0963 style=af -->
记录链只提供组合次序，不把前一步的支持自动传递给后一步。链校验必须保证每步 contract_id 唯一、每步只有一个算子、相邻对象引用及同一性判据兼容、前一 SP1 与后一 SP0 一致；任一步未决、失效或损失超限，都要在链级输出中保留，不能被最终一步的成功覆盖。

<!-- source_paragraph:V8-P0964 style=21 -->
八、机器校验与保护底板

<!-- source_paragraph:V8-P0965 style= -->
record_schema 要求十四节和各节字段集合精确一致，字段类型由 field_types_by_section 固定。九条轴比较记录不得缺轴或重复；每条非未知轴关系必须提交结构化且由对应比较器验证为有效的见证；transformation_class 必须与分类算法输出一致；算子 ID 必须使用限定形式，语义签名必须互异。这里的机器分类器只组合已经通过领域比较器的逐轴关系，不自行替代空间几何、组织图、因果抽象、网络嵌入、对象同一性或授权有效性判断；没有可解析的 comparator_results 与非平凡 identity_mapping_results 产物，就不允许把记录内自报关系升级为尺度升格。源对象与目标对象的经验材料必须引用可解析的独立记录，内部概念编号和框架说明不得充当证据。

<!-- source_paragraph:V8-P0966 style=af -->
四种缺失状态构成封闭词表：unknown 表示当前未知，not_applicable 表示按合同确实不适用，not_observable 表示当前通道和窗口不可观察，withheld_for_protection 表示为保护而不公开。四者都不是“不存在”，也不能删除字段代替状态。

<!-- source_paragraph:V8-P0967 style=af -->
carrying_vehicles 与 responsible_subjects 必须分栏；承接、可见、受影响或能力较强都不自动产生责任。凡对人类或有感主体的权利、稀缺资源配置、暴露风险或现实处置产生影响，保护底板必须识别低权力位置和局部排除区，提供安全提交、反报复、停止、申诉、复核和回滚，且不得记为不适用。保护不足时，判断上限与行动上限同时降低。纯描述记录的条件性不适用也不能被下游行动继承；用途改变时必须重开保护审查。

<!-- source_paragraph:V8-P0968 style=21 -->
九、证据边界与独立支持

<!-- source_paragraph:V8-P0969 style= -->
M01—M09 的名称、编号、语义签名和分类结果只规定变换应怎样描述与检验，不构成变换已经发生、映射有效或目标性质成立的经验支持。内部概念标签、示例、字段完整度和算法自报结果均不得进入 source_evidence 或 target_evidence 代替对象材料。

<!-- source_paragraph:V8-P0970 style=af -->
每个实际变换必须分别在源对象和目标对象上取得可解析的独立材料，明确映射、保持项、改变项、丢失项、误差与竞争解释，并接受同一结果状态、正向门和零结论门。源域材料只能生成目标候选；目标侧没有独立支持时，结论停在待检验映射或未知。

<!-- source_paragraph:V8-P0971 style=21 -->
十、跨圈层关系变换

<!-- source_paragraph:V8-P0972 style= -->
尺度变换与圈层关系变换必须分开。尺度变换回答同一问题在 SP0 与 SP1 之间哪些变量保持、改变或丢失；圈层关系变换回答两个或多个候选圈层在同一或不同尺度上如何并列、包含、重叠、桥接、竞争或临时形成。一个关系变化可能伴随尺度变化，但不能用其中一个词替代另一个合同。

<!-- source_paragraph:V8-P0973 style=af -->
跨圈层记录至少包含关系源、关系目标、静态关系类型、成员或接口基准、方向、通道、时延、阈值、时间窗、证据、反例和前后快照。transformed 只作为关系更新结果：原平行关系可能因桥接者出现而转为桥接，重叠关系可能因制度整合转为嵌套，临时圈层可能制度化或解体。每次转化都要检查 K 是否保持；K 失效时记录对象转换，不以改名延续旧对象。

<!-- source_paragraph:V8-P0974 style= -->
变换问题

<!-- source_paragraph:V8-P0975 style= -->
需要调用

<!-- source_paragraph:V8-P0976 style= -->
不得偷换

<!-- source_paragraph:V8-P0977 style= -->
个体状态能否代表团队

<!-- source_paragraph:V8-P0978 style= -->
聚合 M01、尺度合同与分布损失

<!-- source_paragraph:V8-P0979 style= -->
成员属于团队不等于代表团队

<!-- source_paragraph:V8-P0980 style= -->
团队是否被组织包含

<!-- source_paragraph:V8-P0981 style= -->
嵌套 M02 与具体包含基准

<!-- source_paragraph:V8-P0982 style= -->
共同上级不等于成员包含

<!-- source_paragraph:V8-P0983 style= -->
两圈层是否因共享成员相关

<!-- source_paragraph:V8-P0984 style= -->
重叠关系、成员映射与共同环境

<!-- source_paragraph:V8-P0985 style= -->
重叠不自动产生有效反馈

<!-- source_paragraph:V8-P0986 style= -->
桥接者是否改变另一圈层

<!-- source_paragraph:V8-P0987 style= -->
M03 传播、通道和反事实

<!-- source_paragraph:V8-P0988 style= -->
接触不等于传导，传导不等于代表

<!-- source_paragraph:V8-P0989 style= -->
临时群体是否形成持久对象

<!-- source_paragraph:V8-P0990 style= -->
G1、G3、M05 与 K

<!-- source_paragraph:V8-P0991 style= -->
留痕不等于制度化

<!-- source_paragraph:V8-P0992 style=af -->
多重成员关系要求同一行动者在多个圈层中保留不同角色、可见信息、责任、风险和退出能力。不得先把行动者聚合为单一状态，再把该状态复制到所有圈层。跨圈层推演应从局部状态出发，经已声明的成员或接口通道传播，并逐步登记聚合损失。

<!-- source_paragraph:V8-P0993 style=21 -->
十一、平行与嵌套的同时表示

<!-- source_paragraph:V8-P0994 style= -->
现实结构不是单棵层级树。局部包含关系可以与横向网络、成员重叠、竞争资源和平台桥接同时存在。表示层采用有向多重关系图：节点维持各自对象合同，边维持各自关系合同；“上层”只表示某项包含、管辖或聚合关系，不表示更真实、更正确或更有权。

<!-- source_paragraph:V8-P0995 style=af -->
当多个圈层共享环境却没有直接通道时，模型保留共同条件节点，不虚构圈层间直接边；当通道只在事件窗口内开放时，边具有起止时间；当不同关系方向相反时，分别建边。这样才能在事件发生后判断哪条关系真正改变，而不是把整个结构一次性重画成事后故事。

## Canonical Structure

```json
[
  {
    "pid": "V8-P0807",
    "style": "1",
    "text": "第五部分　跨尺度与跨圈层变换"
  },
  {
    "pid": "V8-P0808",
    "style": "",
    "text": "本部分回答：对象、观察或行动从 SP0 变到 SP1 时，哪些内容得到扩展，哪些内容发生收缩，哪些位置不可比较，凭什么建立转换桥，以及什么信息会在转换中丢失。一般过程统称尺度变换；只有九轴积偏序严格成立时，才称尺度升格。"
  },
  {
    "pid": "V8-P0809",
    "style": "21",
    "text": "一、合同角色与无歧义引用"
  },
  {
    "pid": "V8-P0810",
    "style": "",
    "text": "九个尺度轴是 D 类定义，角色为 scale_axis_definition；九个转换算子是 O 类程序，角色为 scale_transformation_operator；U01—U11 是 D 类通用原语定义，角色为 universal_primitive_definition。定义和程序不冒充经验真值，具体跨层因果、对象转换或零结论必须链接预注册 root-instance。"
  },
  {
    "pid": "V8-P0811",
    "style": "af",
    "text": "尺度实体一律使用限定 ID：scale_axis:A 至 scale_axis:J、scale_operator:M01 至 scale_operator:M09、universal_primitive:U01 至 universal_primitive:U11。因此，scale_axis:O 表示组织层级，claim_type=O 表示操作程序，二者不会混淆。依赖只分为 inferential_requires、protocol_requires、specializes 和 applies_to；协议使用 CAUSAL、EVIDENCE、ANALOGY、SOURCE 等正式 ID，不使用中文简称或裸轴名。"
  },
  {
    "pid": "V8-P0812",
    "style": "21",
    "text": "二、九轴状态与逐轴比较"
  },
  {
    "pid": "V8-P0813",
    "style": "",
    "text": "每个对象和变换绑定："
  },
  {
    "pid": "V8-P0814",
    "style": "af",
    "text": "SP=<A,X,T,O,C,R,I,N,J>"
  },
  {
    "pid": "V8-P0815",
    "style": "",
    "text": "轴"
  },
  {
    "pid": "V8-P0816",
    "style": "",
    "text": "状态字段核心"
  },
  {
    "pid": "V8-P0817",
    "style": "",
    "text": "expands 的计算见证"
  },
  {
    "pid": "V8-P0818",
    "style": "",
    "text": "不可替代边界"
  },
  {
    "pid": "V8-P0819",
    "style": "",
    "text": "A 聚合层次"
  },
  {
    "pid": "V8-P0820",
    "style": "",
    "text": "单位、成员集、分区、聚合规则、权重、排除项"
  },
  {
    "pid": "V8-P0821",
    "style": "",
    "text": "目标总体覆盖源总体，目标分区是源分区的登记粗化"
  },
  {
    "pid": "V8-P0822",
    "style": "",
    "text": "不得由 O、X、I 或 J 替代"
  },
  {
    "pid": "V8-P0823",
    "style": "",
    "text": "X 空间范围"
  },
  {
    "pid": "V8-P0824",
    "style": "",
    "text": "坐标系、空间集合、边界通道、外部连接"
  },
  {
    "pid": "V8-P0825",
    "style": "",
    "text": "坐标对齐后源空间是真子集"
  },
  {
    "pid": "V8-P0826",
    "style": "",
    "text": "不得由 A、O、I 或 J 替代"
  },
  {
    "pid": "V8-P0827",
    "style": "",
    "text": "T 时间跨度"
  },
  {
    "pid": "V8-P0828",
    "style": "",
    "text": "时间基准、窗口角色、起止点、时滞模型"
  },
  {
    "pid": "V8-P0829",
    "style": "",
    "text": "同一基准与角色下目标区间真包含源区间"
  },
  {
    "pid": "V8-P0830",
    "style": "",
    "text": "当前截面和长期路径不能互代"
  },
  {
    "pid": "V8-P0831",
    "style": "",
    "text": "O 组织层级"
  },
  {
    "pid": "V8-P0832",
    "style": "",
    "text": "组织图、版本、节点、包含边、接口、重叠"
  },
  {
    "pid": "V8-P0833",
    "style": "",
    "text": "同版组织 DAG 中目标节点覆盖源节点祖先闭包"
  },
  {
    "pid": "V8-P0834",
    "style": "",
    "text": "组织上位不等于 J 扩大"
  },
  {
    "pid": "V8-P0835",
    "style": "",
    "text": "C 因果层次"
  },
  {
    "pid": "V8-P0836",
    "style": "",
    "text": "因果模型、变量、边、干预语义、抽象映射"
  },
  {
    "pid": "V8-P0837",
    "style": "",
    "text": "目标模型经语义保持映射覆盖源模型并增加可区分层面"
  },
  {
    "pid": "V8-P0838",
    "style": "",
    "text": "层级标签、时序和相关不能代替因果桥"
  },
  {
    "pid": "V8-P0839",
    "style": "",
    "text": "R 观察分辨率"
  },
  {
    "pid": "V8-P0840",
    "style": "",
    "text": "测量协议、可区分类、参数、误差、保护性省略"
  },
  {
    "pid": "V8-P0841",
    "style": "",
    "text": "目标协议保留源协议全部区分并至少细分一类"
  },
  {
    "pid": "V8-P0842",
    "style": "",
    "text": "高分辨率不等于完整或有权行动"
  },
  {
    "pid": "V8-P0843",
    "style": "",
    "text": "I 影响范围"
  },
  {
    "pid": "V8-P0844",
    "style": "",
    "text": "结果、阈值、窗口、受影响位置、效应阶次"
  },
  {
    "pid": "V8-P0845",
    "style": "",
    "text": "对齐后目标受影响位置集真包含源集合"
  },
  {
    "pid": "V8-P0846",
    "style": "",
    "text": "影响和观察均不等于授权"
  },
  {
    "pid": "V8-P0847",
    "style": "",
    "text": "N 网络拓扑范围"
  },
  {
    "pid": "V8-P0848",
    "style": "",
    "text": "图与版本、节点、边、语义、采样边界"
  },
  {
    "pid": "V8-P0849",
    "style": "",
    "text": "存在语义保持图嵌入且目标覆盖源图"
  },
  {
    "pid": "V8-P0850",
    "style": "",
    "text": "网络中心不等于责任中心"
  },
  {
    "pid": "V8-P0851",
    "style": "",
    "text": "J 管辖与授权范围"
  },
  {
    "pid": "V8-P0852",
    "style": "",
    "text": "原子授权元组集合；每个元组固定来源、主体、单一对象、单一动作、地域、期限、撤回、有效性和证据"
  },
  {
    "pid": "V8-P0853",
    "style": "",
    "text": "目标有效原子元组规范化集合真包含，且每个新增元组有独立有效性见证"
  },
  {
    "pid": "V8-P0854",
    "style": "",
    "text": "任何其他轴均不能替代 J；禁止对象集与动作集做笛卡尔积"
  },
  {
    "pid": "V8-P0855",
    "style": "af",
    "text": "每轴关系只有五种：equal、expands、contracts、incomparable、unknown。轴比较记录固定包含 axis_id、源/目标状态、关系、顺序见证、信息损失和不确定性。非未知关系的 order_witness 不是一句说明，而是闭合对象：comparator_id 与 comparator_version 必须对应该轴比较器，verifier_id 明确谁或什么执行验证，evidence_refs 非空，comparison_payload 给出实际映射、集合、区间、图或授权差异，verification_artifact_ref 与 verification_hash 指向可复核产物，validation_status 必须为 valid。unknown 使用带理由的缺失状态。完全相同的两状态可用内置深相等复算 equal；其他相等以及全部扩展、收缩和不可比关系，都必须从外部比较器结果注册表核对轴、版本、源/目标摘要、关系和哈希。相同状态申报扩展或收缩直接失败。没有可解析见证，只能记 unknown；contracts 是同轴 expands 的逆关系，不是凭语言印象标注。"
  },
  {
    "pid": "V8-P0856",
    "style": "af",
    "text": "“九轴都要登记”不等于“九轴对一切对象都适用”。某轴整体确实不适用时，轴状态使用带理由的 not_applicable 对象，而不是删掉该轴。典型例子是没有行动主体和授权概念的自然过程：其 J 轴不适用，不等于“存在一个空授权集合”。源、目标两端经同一适用性判据均不适用时，该轴可在见证中记为 equal；仅一端不适用而另一端适用时，语义域已经改变，应记 incomparable；材料不足仍记 unknown。这样既保持九轴接口稳定，也不把人类制度语义强塞进广义世界。"
  },
  {
    "pid": "V8-P0857",
    "style": "af",
    "text": "每个轴状态都须满足反身性、反对称性和传递性。为避免“差一点相等”破坏传递，轴状态先按 equality_rule 形成规范化等价类，偏序在这些等价类的商集上定义；容差只能通过预注册的共同规范化器或固定分箱把两端送入同一等价类，不能用任意两点之间“距离小于阈值”直接定义相等。反身性要求规范化状态与自身为 equal；反对称性要求双向不大于只能落入同一等价类；传递性只在中间状态、版本和见证可组合时成立，任何映射、坐标、图版本、变量或授权链断裂都会使关系回到 unknown。"
  },
  {
    "pid": "V8-P0858",
    "style": "af",
    "text": "每轴的主比较量成立还不够。若该轴记录含边界通道、时滞模型、接口、误差模型、干预语义或保护性省略等辅助状态，expands 还要求这些字段存在可组合的语义保持映射；主范围扩大而辅助语义发生无映射冲突时，只能登记 incomparable 或 unknown。这使“范围更大”不会偷渡成“整个轴状态更高”。"
  },
  {
    "pid": "V8-P0859",
    "style": "21",
    "text": "三、积偏序与变换分类"
  },
  {
    "pid": "V8-P0860",
    "style": "",
    "text": "SP0≼SP1 当且仅当九轴全部为 equal 或 expands；严格关系 SP0≺SP1 还要求至少一轴 expands。机器分类按以下顺序执行："
  },
  {
    "pid": "V8-P0861",
    "style": "",
    "text": "任一轴 incomparable：horizontal_or_incomparable；已知不可比不会被另一轴的未知覆盖；"
  },
  {
    "pid": "V8-P0862",
    "style": "",
    "text": "否则同时出现扩展和收缩：mixed；两种已知方向已经足以排除积偏序，即使还有轴未知；"
  },
  {
    "pid": "V8-P0863",
    "style": "",
    "text": "否则任一轴 unknown：unresolved；"
  },
  {
    "pid": "V8-P0864",
    "style": "",
    "text": "九轴全 equal：all_equal；"
  },
  {
    "pid": "V8-P0865",
    "style": "",
    "text": "仅含 equal/expands 且至少一轴扩展：elevation；"
  },
  {
    "pid": "V8-P0866",
    "style": "",
    "text": "仅含 equal/contracts 且至少一轴收缩：reduction。"
  },
  {
    "pid": "V8-P0867",
    "style": "",
    "text": "因此，宏观聚合同时压缩观察分辨率时通常是 mixed，不应笼统叫升格；领域类比常是 horizontal_or_incomparable；材料不足时是 unresolved。只有分类为 elevation 的实例才使用“尺度升格”。观察范围、空间范围、组织范围、影响范围或网络范围扩大，都不会改变 J；J 只能由新的有效授权元组见证扩展。"
  },
  {
    "pid": "V8-P0868",
    "style": "af",
    "text": "J 状态不是“一个来源 + 一组主体 + 一组对象 + 一组动作”的独立字段拼盘，因为那会凭空生成未被授权的对象—动作组合。authorization_tuple_contract 要求每个原子元组只绑定一个来源、一个决策主体、一个对象和一个动作，同时保存地域、有效期、撤回条件、证据和独立复核；多对象或多动作必须拆成多个元组。只有状态为有效的规范化原子元组进入集合比较。J 轴扩展的见证要在 comparison_payload 中列出目标新增而源端没有的完整元组及其独立有效性证据，并与记录的 j_authorization 对齐。任意字符串、tuple ID、自称、实际控制、观察覆盖、影响扩大、上位组织位置或其他轴的扩展都不能使 J 变为 expands。"
  },
  {
    "pid": "V8-P0869",
    "style": "21",
    "text": "四、所有算子的三态与零结论门"
  },
  {
    "pid": "V8-P0870",
    "style": "",
    "text": "每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。"
  },
  {
    "pid": "V8-P0871",
    "style": "af",
    "text": "算子程序统一使用四个结果状态："
  },
  {
    "pid": "V8-P0872",
    "style": "",
    "text": "supported：本次选定分支的桥、决策规则和正向阈值已预注册且通过；只有 G、因果、对象/干预转换分支才强制 root-instance、预选子型和唯一成功判据，纯描述分支可把这些 G 专用字段记为 not_applicable；"
  },
  {
    "pid": "V8-P0873",
    "style": "",
    "text": "unsupported_or_undecided：桥接不足，或正向门未通过而零结论门也未通过；"
  },
  {
    "pid": "V8-P0874",
    "style": "",
    "text": "null_supported：只有预注册 null_decision_rule、等价性或充分性检验、功效或灵敏度及容差全部通过时，才支持限定零结论；"
  },
  {
    "pid": "V8-P0875",
    "style": "",
    "text": "not_evaluated：算子或相应分支尚未运行；已运行且描述桥成立的分支可以是 supported，不能因不需要 G-instance 而降为未评估。"
  },
  {
    "pid": "V8-P0876",
    "style": "",
    "text": "“未显著”“切断后看似不变”“效应消失”“简单模型表现相当”或“目标证据不足”都不能自动写成 null_supported。这条纪律适用于 M01—M09，而不只适用于跨层因果。"
  },
  {
    "pid": "V8-P0877",
    "style": "21",
    "text": "五、九种尺度变换算子"
  },
  {
    "pid": "V8-P0878",
    "style": "",
    "text": "每个算子都有独有 semantic_signature，不能复制 M01 的聚合语句冒充其他算子。"
  },
  {
    "pid": "V8-P0879",
    "style": "31",
    "text": "M01　聚合"
  },
  {
    "pid": "V8-P0880",
    "style": "",
    "text": "签名是“单位—总体分区聚合”。最低桥包括逐单位映射、成员与排除、权重与缺失、替代聚合规则和异质性。信息损失包括尾部、次序、协方差、局部时序及少数位置可见度。总体不能按登记规则复现、合理替代规则造成方向反转，或总体关联被回填为个体属性时，程序失败。即使聚合获得支持，也不得据总体结果直接处置成员。"
  },
  {
    "pid": "V8-P0881",
    "style": "31",
    "text": "M02　嵌套"
  },
  {
    "pid": "V8-P0882",
    "style": "",
    "text": "签名是“边界—成员嵌入”。它必须分成两条支路："
  },
  {
    "pid": "V8-P0883",
    "style": "",
    "text": "描述性嵌套只检验边界、成员、重叠、退出和接口映射；它可以成立而没有任何跨层因果。"
  },
  {
    "pid": "V8-P0884",
    "style": "",
    "text": "跨层因果必须链接预注册 G4a 或 G4b root-instance，固定子型和唯一成功判据，并通过 CAUSAL 与三态/null 门。"
  },
  {
    "pid": "V8-P0885",
    "style": "",
    "text": "控制当前状态与共同环境后没有条件增量，并不自动证明“没有跨层作用”；只有等价/充分性、功效/灵敏度和容差门同时通过，才可登记限定零结论。描述性嵌套不生成上位优先、下位义务或 J 轴扩展。"
  },
  {
    "pid": "V8-P0886",
    "style": "af",
    "text": "记录时必须在 descriptive_nesting、cross_layer_causal、object_conversion、intervention_conversion 中选一支，并分别绑定描述、因果、对象转换或干预转换模式；不得用描述性嵌套的边界材料支持后面三支。"
  },
  {
    "pid": "V8-P0887",
    "style": "31",
    "text": "M03　网络传播"
  },
  {
    "pid": "V8-P0888",
    "style": "",
    "text": "签名是“沿时间化路径传导”。必须登记节点、边、方向、权重、容量、采样边界、候选与替代路径、时延和损耗。连接或同步只生成候选；切断路径后结果不变而零结论门未通过时，仍是 unsupported_or_undecided。网络采样会遗漏弱边、离网位置和跨网桥，只保留终点影响也不能恢复传播次序。中心性不等于意图、责任或处置权限。"
  },
  {
    "pid": "V8-P0889",
    "style": "31",
    "text": "M04　时间累积"
  },
  {
    "pid": "V8-P0890",
    "style": "",
    "text": "签名是“带窗口的纵向组合”。必须冻结时间基准、基线、窗口、时滞、持久阈值和累积/衰减/恢复规则，并比较共同趋势、季节、队列和替代窗口。效应在控制后消失或随窗口变化，只表示正向支持不足；没有通过零结论门，不能发布“无累积”。基础时间组合不预证 G3；只有历史项在控制当前状态后仍提供条件增量时，才链接 G3-instance。"
  },
  {
    "pid": "V8-P0891",
    "style": "31",
    "text": "M05　制度化"
  },
  {
    "pid": "V8-P0892",
    "style": "",
    "text": "签名是“持久制度写回”。它把五个判断分开：制度事实上存在、法律有效、规范正当、保护是否成立、是否应继续。记录、角色、资源、决策规则或后续转移发生持久改变，可以支持制度化事实；授权无效、参与不足、保护机制失效、缺少申诉/反报复/回滚属于治理失败、规范争议和行动降级理由，不能据此抹掉制度已存在的事实。反过来，制度存在也不证明它合法、正当、具有充分保护或应继续。"
  },
  {
    "pid": "V8-P0893",
    "style": "af",
    "text": "selected_operator_branch 只允许 institutional_fact、institutional_causal_effect、institutional_object_conversion 或 institutional_intervention_conversion。法律有效性审查、治理质量、规范正当性、保护充分性和应否继续没有任何一项能伪装成 institutional_fact 的正向或零结论。"
  },
  {
    "pid": "V8-P0894",
    "style": "31",
    "text": "M06　涌现"
  },
  {
    "pid": "V8-P0895",
    "style": "",
    "text": "签名是“互动生成目标尺度模式”。源单位、互动规则、目标对象和目标模式须与预登记简单加和模型在同一指标上比较。简单加和模型表现相当，只在充分性/等价、功效/灵敏度和容差门通过时支持“加和已足够”；否则保持未决。宏观模式不能反推唯一微观原因，也不能自动证明下行因果。下行约束须另链 G4/CAUSAL 实例。"
  },
  {
    "pid": "V8-P0896",
    "style": "31",
    "text": "M07　委托/代表"
  },
  {
    "pid": "V8-P0897",
    "style": "",
    "text": "签名是“代表事实分类与可选授权转移”。必须分开记录：代表性主张、实际代行事实、争议或自任代表、有效委托、J 轴权限转移。无授权时仍可记录实际代行及其影响和责任，但不得登记 J 扩展；授权无效会触发停止或降级，却不能把已经发生的代行与后果删除。多数、可见性、影响力、自称或实际控制都不等于有效委托。"
  },
  {
    "pid": "V8-P0898",
    "style": "af",
    "text": "记录必须在 representation_claim、actual_acts、delegation_validity、J_transfer 中选一支。前三支即使获得支持也不能改变 J；只有 J_transfer 与结构化授权元组、独立有效性证据和 j_authorization 同时通过时，J 才可扩展。"
  },
  {
    "pid": "V8-P0899",
    "style": "31",
    "text": "M08　压缩/抽象"
  },
  {
    "pid": "V8-P0900",
    "style": "",
    "text": "签名是“多对一表示压缩”。源材料、算法、阈值、版本、误差、不可恢复信息和任务所需不变量必须可追踪。unknown、not_applicable、not_observable、withheld_for_protection 必须保持区分，任何一种都不能压成“不存在”。高损失表示不得支持高影响行动。"
  },
  {
    "pid": "V8-P0901",
    "style": "31",
    "text": "M09　横向迁移"
  },
  {
    "pid": "V8-P0902",
    "style": "",
    "text": "签名是“跨领域类比迁移”。必须登记映射、差异、断裂、禁止映射、目标责任链和 J 轴差异。源域材料只生成目标候选；supported 或 null_supported 都必须来自独立目标实例。目标证据不足是 not_evaluated 或 unsupported_or_undecided，不是目标机制不存在的证明。类比不生成目标领域行动授权。"
  },
  {
    "pid": "V8-P0903",
    "style": "21",
    "text": "六、通用原语的尺度边界"
  },
  {
    "pid": "V8-P0904",
    "style": "",
    "text": "通用原语是 D 类接口，不再携带经验零模型或证伪模板。尤其需要锁住四项边界："
  },
  {
    "pid": "V8-P0905",
    "style": "",
    "text": "U07 的基础反馈只要求返回通道和后续状态更新，不要求 G3；持久历史增量和学习才另检 G3。"
  },
  {
    "pid": "V8-P0906",
    "style": "",
    "text": "U09 的瞬时需求—容量缺口不要求 G3；累积损伤或迟恢复才另检历史条件增量。"
  },
  {
    "pid": "V8-P0907",
    "style": "",
    "text": "U10 只登记候选痕迹、载体和保留窗口，不预证路径依赖；G3 仍须证明历史项在控制当前状态后的条件增量。"
  },
  {
    "pid": "V8-P0908",
    "style": "",
    "text": "U11 的基础相位模式不要求 G3 或 G4；因果触发另检 G2，迟滞另检 G3，对象转换另检 G4。"
  },
  {
    "pid": "V8-P0909",
    "style": "",
    "text": "同理，U01 只登记候选对象而不预保证 G1；U05 的关系定义不证明因果；U06 的通道字段不证明通道效应。"
  },
  {
    "pid": "V8-P0910",
    "style": "21",
    "text": "七、统一尺度变换记录"
  },
  {
    "pid": "V8-P0911",
    "style": "",
    "text": "每个实例都必须出现十四节和全部字段："
  },
  {
    "pid": "V8-P0912",
    "style": "",
    "text": "节"
  },
  {
    "pid": "V8-P0913",
    "style": "",
    "text": "必填字段"
  },
  {
    "pid": "V8-P0914",
    "style": "",
    "text": "identity"
  },
  {
    "pid": "V8-P0915",
    "style": "",
    "text": "contract_id、concept_id、version、proposition_ids、purpose"
  },
  {
    "pid": "V8-P0916",
    "style": "",
    "text": "scale"
  },
  {
    "pid": "V8-P0917",
    "style": "",
    "text": "SP0、SP1、九条 axis_differences、unchanged_axes、transformation_class、j_authorization"
  },
  {
    "pid": "V8-P0918",
    "style": "",
    "text": "objects"
  },
  {
    "pid": "V8-P0919",
    "style": "",
    "text": "源/目标有效对象、source_K、target_K、identity_mapping、单位、总体、边界、成员、排除项"
  },
  {
    "pid": "V8-P0920",
    "style": "",
    "text": "semantics"
  },
  {
    "pid": "V8-P0921",
    "style": "",
    "text": "preserved_core、allowed_changes、lost_elements、prohibited_mappings"
  },
  {
    "pid": "V8-P0922",
    "style": "",
    "text": "transformation"
  },
  {
    "pid": "V8-P0923",
    "style": "",
    "text": "单一算子、selected_operator_branch、claim_mode、规则、因果桥、时滞、映射误差、有效期、root-instance、子型、成功判据、正向和零决策规则、正向阈值、等价/充分性检验、功效/灵敏度、容差、结果状态"
  },
  {
    "pid": "V8-P0924",
    "style": "",
    "text": "variables"
  },
  {
    "pid": "V8-P0925",
    "style": "",
    "text": "输入、状态、输出和跨变量依赖"
  },
  {
    "pid": "V8-P0926",
    "style": "",
    "text": "evidence"
  },
  {
    "pid": "V8-P0927",
    "style": "",
    "text": "源/目标证据、覆盖、异质性、反例、缺席信号、替代解释、残差检验、复制或外部验证"
  },
  {
    "pid": "V8-P0928",
    "style": "",
    "text": "loss"
  },
  {
    "pid": "V8-P0929",
    "style": "",
    "text": "压缩细节、不可恢复信息、低可见位置和局部排除区"
  },
  {
    "pid": "V8-P0930",
    "style": "",
    "text": "responsibility"
  },
  {
    "pid": "V8-P0931",
    "style": "",
    "text": "行动者、决策者、授权者、承接载体、责任主体、受益者和成本承担者"
  },
  {
    "pid": "V8-P0932",
    "style": "",
    "text": "normative"
  },
  {
    "pid": "V8-P0933",
    "style": "",
    "text": "价值前提、选择类型、规范选择记录、运行时 N 原则、授权来源、C12 门和 O1-O4 程序"
  },
  {
    "pid": "V8-P0934",
    "style": "",
    "text": "protection"
  },
  {
    "pid": "V8-P0935",
    "style": "",
    "text": "保护适用性、低权力位置、安全提交和反报复"
  },
  {
    "pid": "V8-P0936",
    "style": "",
    "text": "action"
  },
  {
    "pid": "V8-P0937",
    "style": "",
    "text": "判断上限、行动上限、禁止动作、停止条件、责任人和机器可指向的 selected_action"
  },
  {
    "pid": "V8-P0938",
    "style": "",
    "text": "correction"
  },
  {
    "pid": "V8-P0939",
    "style": "",
    "text": "申诉、复核、回滚、修复和写回"
  },
  {
    "pid": "V8-P0940",
    "style": "",
    "text": "lifecycle"
  },
  {
    "pid": "V8-P0941",
    "style": "",
    "text": "有效期、复审点、暂停和退场"
  },
  {
    "pid": "V8-P0942",
    "style": "af",
    "text": "source_K、target_K 和 identity_mapping 共同决定对象保持、转换或不可比；同名不是同一性证据。映射记录必须同时保存源、目标 K 的摘要，源对象与目标对象分别在两套 K 下的四项判据结果，正向与反向映射，保持和违反的判据，结果前冻结的预注册引用，以及可复核的验证制品与哈希。判据结果只允许 passed、failed 或 undetermined，不能用一个布尔值掩盖是哪一项没有通过。"
  },
  {
    "pid": "V8-P0943",
    "style": "",
    "text": "K 映射分类"
  },
  {
    "pid": "V8-P0944",
    "style": "",
    "text": "最低成立条件"
  },
  {
    "pid": "V8-P0945",
    "style": "",
    "text": "结果上限"
  },
  {
    "pid": "V8-P0946",
    "style": "",
    "text": "same_object"
  },
  {
    "pid": "V8-P0947",
    "style": "",
    "text": "双向映射均有效；源对象与目标对象在 source_K、target_K 下四项检查均通过；保持判据非空且违反判据为空"
  },
  {
    "pid": "V8-P0948",
    "style": "",
    "text": "可在当前合同内沿用对象身份，但不推出语义、因果或规范性质也保持"
  },
  {
    "pid": "V8-P0949",
    "style": "",
    "text": "converted_object"
  },
  {
    "pid": "V8-P0950",
    "style": "",
    "text": "source_under_source_K 与 target_under_target_K 通过，target_under_source_K 失败；违反项和结果前预注册引用具体；另有 object_conversion 模式及取得支持的 G4b 实例"
  },
  {
    "pid": "V8-P0951",
    "style": "",
    "text": "只登记预注册 K 下的对象转换，不得在结果后改写 K 制造转换"
  },
  {
    "pid": "V8-P0952",
    "style": "",
    "text": "incomparable"
  },
  {
    "pid": "V8-P0953",
    "style": "",
    "text": "两端各自在本方 K 下通过，至少一个交叉 K 检查失败；正反向映射保存完整尝试记录且至少一项验证为无效，并有可解析证据"
  },
  {
    "pid": "V8-P0954",
    "style": "",
    "text": "表示已知不可比，只能 unsupported_or_undecided；不是“尚未评估”"
  },
  {
    "pid": "V8-P0955",
    "style": "",
    "text": "undetermined"
  },
  {
    "pid": "V8-P0956",
    "style": "",
    "text": "检验尚未运行，或必要映射、判据未知或不可观察；四项结果均保持 undetermined"
  },
  {
    "pid": "V8-P0957",
    "style": "",
    "text": "只能 unsupported_or_undecided 或 not_evaluated；不构成不可比或对象转换"
  },
  {
    "pid": "V8-P0958",
    "style": "af",
    "text": "只有源/目标对象和两套 K 都可由验证器重算为深相等时，才允许 builtin:deep-identity。其他非平凡保持或对象转换必须把 mapping_id 交给独立 identity_mapping_results 注册表，逐项核对对象摘要、K 摘要、方向映射、四项判据结果、验证制品和哈希；记录内部自报 valid 或一个看似正确的 ID 前缀都不能充当证明。"
  },
  {
    "pid": "V8-P0959",
    "style": "af",
    "text": "对象转换模式与结果四态必须一致：supported 才对应 converted_object；null_supported 对应通过零结论三门的 same_object；unsupported_or_undecided 只允许保持、已知不可比或未决；not_evaluated 必须保持 undetermined。因此，未检验和检验失败都不能先把目标写成“已经转换”。其他 claim_mode 也不得在同一条原子记录里兼报 converted_object，对象转换必须拆成自己的原子检验。"
  },
  {
    "pid": "V8-P0960",
    "style": "af",
    "text": "claim_mode 为 root_hypothesis、causal、object_conversion 或 intervention_conversion 时必须填写 root_instance_ids，后三者还必须给出非空因果桥；只有 descriptive_mapping 可把 root-instance、子型和成功判据标为 not_applicable。非描述模式登记 supported 或 null_supported 时，还必须向验证器提交可解析的 root-instance 注册表，并核对实例 ID、根族、合同版本、预选子型、唯一成功判据与实例状态；一个看似正确的字符串前缀不能充当实例。描述桥正向门通过时可以记 supported，只有所选模式没有运行时才记 not_evaluated。"
  },
  {
    "pid": "V8-P0961",
    "style": "af",
    "text": "十四节是稳定接口，不是把人类治理语义投射给所有对象。protection.applicability 必须显式登记对象类型、下游用途、理由和证据引用，不能从 actors 等空列表反推。对象类型为 nonhuman，且用途只含 description_only 或有证据证明不影响人类/有感主体的 nonhuman_intervention_without_human_or_sentient_effect 时，safe_submission 与 anti_retaliation 可带理由记 not_applicable；但现实实验或工程干预仍有行动主体和对象，必须填写具体 J、行动责任人、停止、复核与回滚，只有纯描述用途才允许 J 不适用。自然系统中的能量、物质或计算资源本身不触发这套人类保护合同。对象为人类、有感非人、混合或未知，或用途涉及人的评价、其稀缺资源配置、权利、暴露风险或现实处置时，保护字段立即成为强制项，不得沿用先前的不适用状态。保护不适用绝不推出行动正当，规范选择仍另行判断。"
  },
  {
    "pid": "V8-P0962",
    "style": "af",
    "text": "action_owner 只说明谁负责执行或停止，不能反推 claim_mode=intervention_conversion，也不能证明行动有效或正当。任何外部行动必须链接 selection_record_id，公开 value_premises 与运行时 normative_principle_ids；N1 单独只能阻止越权，不能产生正向方案。选择记录中的 feasible_alternatives 不是名称列表，而是带稳定 option_id 的结构化方案；每项冻结 option_kind、动作类型、目标对象、地域、有效期、可逆性、预期影响和分配影响，并且恰有一项 option_kind=no_action，由 no_action_option_id 唯一指向。selected_action.selected_option_id 必须解析到一项 external_action，而且其动作、对象、地域和有效期与该方案逐项相等；选择不行动 ID、只对上自然语言标签，或同时改写动作与 J 而不改获准方案，都必须被拒绝。至少一条当前有效且独立复核的 J 原子授权元组还必须同时覆盖该主体、对象、动作、地域和期限，并与授权来源一致；一条无关但形式有效的授权不能为拟议行动背书。记录还必须有通过的十组件 c12_gate、O1-O4 procedure_ids、行动责任人、禁止动作、停止、保护、申诉、复核和回滚。缺任一项时，行动上限只能是不行动或继续审议；经验上的干预转换另由相应 root-instance 判断。"
  },
  {
    "pid": "V8-P0963",
    "style": "af",
    "text": "记录链只提供组合次序，不把前一步的支持自动传递给后一步。链校验必须保证每步 contract_id 唯一、每步只有一个算子、相邻对象引用及同一性判据兼容、前一 SP1 与后一 SP0 一致；任一步未决、失效或损失超限，都要在链级输出中保留，不能被最终一步的成功覆盖。"
  },
  {
    "pid": "V8-P0964",
    "style": "21",
    "text": "八、机器校验与保护底板"
  },
  {
    "pid": "V8-P0965",
    "style": "",
    "text": "record_schema 要求十四节和各节字段集合精确一致，字段类型由 field_types_by_section 固定。九条轴比较记录不得缺轴或重复；每条非未知轴关系必须提交结构化且由对应比较器验证为有效的见证；transformation_class 必须与分类算法输出一致；算子 ID 必须使用限定形式，语义签名必须互异。这里的机器分类器只组合已经通过领域比较器的逐轴关系，不自行替代空间几何、组织图、因果抽象、网络嵌入、对象同一性或授权有效性判断；没有可解析的 comparator_results 与非平凡 identity_mapping_results 产物，就不允许把记录内自报关系升级为尺度升格。源对象与目标对象的经验材料必须引用可解析的独立记录，内部概念编号和框架说明不得充当证据。"
  },
  {
    "pid": "V8-P0966",
    "style": "af",
    "text": "四种缺失状态构成封闭词表：unknown 表示当前未知，not_applicable 表示按合同确实不适用，not_observable 表示当前通道和窗口不可观察，withheld_for_protection 表示为保护而不公开。四者都不是“不存在”，也不能删除字段代替状态。"
  },
  {
    "pid": "V8-P0967",
    "style": "af",
    "text": "carrying_vehicles 与 responsible_subjects 必须分栏；承接、可见、受影响或能力较强都不自动产生责任。凡对人类或有感主体的权利、稀缺资源配置、暴露风险或现实处置产生影响，保护底板必须识别低权力位置和局部排除区，提供安全提交、反报复、停止、申诉、复核和回滚，且不得记为不适用。保护不足时，判断上限与行动上限同时降低。纯描述记录的条件性不适用也不能被下游行动继承；用途改变时必须重开保护审查。"
  },
  {
    "pid": "V8-P0968",
    "style": "21",
    "text": "九、证据边界与独立支持"
  },
  {
    "pid": "V8-P0969",
    "style": "",
    "text": "M01—M09 的名称、编号、语义签名和分类结果只规定变换应怎样描述与检验，不构成变换已经发生、映射有效或目标性质成立的经验支持。内部概念标签、示例、字段完整度和算法自报结果均不得进入 source_evidence 或 target_evidence 代替对象材料。"
  },
  {
    "pid": "V8-P0970",
    "style": "af",
    "text": "每个实际变换必须分别在源对象和目标对象上取得可解析的独立材料，明确映射、保持项、改变项、丢失项、误差与竞争解释，并接受同一结果状态、正向门和零结论门。源域材料只能生成目标候选；目标侧没有独立支持时，结论停在待检验映射或未知。"
  },
  {
    "pid": "V8-P0971",
    "style": "21",
    "text": "十、跨圈层关系变换"
  },
  {
    "pid": "V8-P0972",
    "style": "",
    "text": "尺度变换与圈层关系变换必须分开。尺度变换回答同一问题在 SP0 与 SP1 之间哪些变量保持、改变或丢失；圈层关系变换回答两个或多个候选圈层在同一或不同尺度上如何并列、包含、重叠、桥接、竞争或临时形成。一个关系变化可能伴随尺度变化，但不能用其中一个词替代另一个合同。"
  },
  {
    "pid": "V8-P0973",
    "style": "af",
    "text": "跨圈层记录至少包含关系源、关系目标、静态关系类型、成员或接口基准、方向、通道、时延、阈值、时间窗、证据、反例和前后快照。transformed 只作为关系更新结果：原平行关系可能因桥接者出现而转为桥接，重叠关系可能因制度整合转为嵌套，临时圈层可能制度化或解体。每次转化都要检查 K 是否保持；K 失效时记录对象转换，不以改名延续旧对象。"
  },
  {
    "pid": "V8-P0974",
    "style": "",
    "text": "变换问题"
  },
  {
    "pid": "V8-P0975",
    "style": "",
    "text": "需要调用"
  },
  {
    "pid": "V8-P0976",
    "style": "",
    "text": "不得偷换"
  },
  {
    "pid": "V8-P0977",
    "style": "",
    "text": "个体状态能否代表团队"
  },
  {
    "pid": "V8-P0978",
    "style": "",
    "text": "聚合 M01、尺度合同与分布损失"
  },
  {
    "pid": "V8-P0979",
    "style": "",
    "text": "成员属于团队不等于代表团队"
  },
  {
    "pid": "V8-P0980",
    "style": "",
    "text": "团队是否被组织包含"
  },
  {
    "pid": "V8-P0981",
    "style": "",
    "text": "嵌套 M02 与具体包含基准"
  },
  {
    "pid": "V8-P0982",
    "style": "",
    "text": "共同上级不等于成员包含"
  },
  {
    "pid": "V8-P0983",
    "style": "",
    "text": "两圈层是否因共享成员相关"
  },
  {
    "pid": "V8-P0984",
    "style": "",
    "text": "重叠关系、成员映射与共同环境"
  },
  {
    "pid": "V8-P0985",
    "style": "",
    "text": "重叠不自动产生有效反馈"
  },
  {
    "pid": "V8-P0986",
    "style": "",
    "text": "桥接者是否改变另一圈层"
  },
  {
    "pid": "V8-P0987",
    "style": "",
    "text": "M03 传播、通道和反事实"
  },
  {
    "pid": "V8-P0988",
    "style": "",
    "text": "接触不等于传导，传导不等于代表"
  },
  {
    "pid": "V8-P0989",
    "style": "",
    "text": "临时群体是否形成持久对象"
  },
  {
    "pid": "V8-P0990",
    "style": "",
    "text": "G1、G3、M05 与 K"
  },
  {
    "pid": "V8-P0991",
    "style": "",
    "text": "留痕不等于制度化"
  },
  {
    "pid": "V8-P0992",
    "style": "af",
    "text": "多重成员关系要求同一行动者在多个圈层中保留不同角色、可见信息、责任、风险和退出能力。不得先把行动者聚合为单一状态，再把该状态复制到所有圈层。跨圈层推演应从局部状态出发，经已声明的成员或接口通道传播，并逐步登记聚合损失。"
  },
  {
    "pid": "V8-P0993",
    "style": "21",
    "text": "十一、平行与嵌套的同时表示"
  },
  {
    "pid": "V8-P0994",
    "style": "",
    "text": "现实结构不是单棵层级树。局部包含关系可以与横向网络、成员重叠、竞争资源和平台桥接同时存在。表示层采用有向多重关系图：节点维持各自对象合同，边维持各自关系合同；“上层”只表示某项包含、管辖或聚合关系，不表示更真实、更正确或更有权。"
  },
  {
    "pid": "V8-P0995",
    "style": "af",
    "text": "当多个圈层共享环境却没有直接通道时，模型保留共同条件节点，不虚构圈层间直接边；当通道只在事件窗口内开放时，边具有起止时间；当不同关系方向相反时，分别建边。这样才能在事件发生后判断哪条关系真正改变，而不是把整个结构一次性重画成事后故事。"
  }
]
```
