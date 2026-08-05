# CrossFrame Ultra v8.2 第五部分　跨尺度与跨圈层变换

Raw SHA256: `608a4e4099b18c96c18ed3c92a2ab5cdacbd737daca4214c77debdd795da3a20`
Semantic SHA256: `4b63a6455cf73c136ae18d124aeed4301267fd2da78cca79c74e2850fb2728b0`
Source role: `division`
Paragraph range: `V82-P0863`-`V82-P1082`
Paragraph count: `220`
Tables: `V82-T012, V82-T013, V82-T014, V82-T015, V82-T016`

## Source Paragraphs

<!-- source-paragraph:V82-P0863 style=PartTitle -->
第五部分　跨尺度与跨圈层变换

<!-- source-paragraph:V82-P0864 style=BodyCJK -->
本部分回答：对象、观察或行动从 SP0 变到 SP1 时，哪些内容得到扩展，哪些内容发生收缩，哪些位置不可比较，凭什么建立转换桥，以及什么信息会在转换中丢失。一般过程统称尺度变换；只有九轴积偏序严格成立时，才称尺度升格。

<!-- source-paragraph:V82-P0865 style=SecH2 -->
5.1　合同角色与无歧义引用

<!-- source-paragraph:V82-P0866 style=BodyCJK -->
九个尺度轴是 D 类定义，角色为 scale_axis_definition；九个转换算子是 O 类程序，角色为 scale_transformation_operator；U01—U11 是 D 类通用原语定义，角色为 universal_primitive_definition。定义和程序不冒充经验真值，具体跨层因果、对象转换或零结论必须链接预注册 root-instance。

<!-- source-paragraph:V82-P0867 style=BodyCJK -->
尺度实体一律使用限定 ID：scale_axis:A 至 scale_axis:J、scale_operator:M01 至 scale_operator:M09、universal_primitive:U01 至 universal_primitive:U11。因此，scale_axis:O 表示组织层级，claim_type=O 表示操作程序，二者不会混淆。依赖只分为 inferential_requires、protocol_requires、specializes 和 applies_to；协议使用 CAUSAL、EVIDENCE、ANALOGY、SOURCE 等正式 ID，不使用中文简称或裸轴名。

<!-- source-paragraph:V82-P0868 style=SecH2 -->
5.2　九轴状态与逐轴比较

<!-- source-paragraph:V82-P0869 style=BodyCJK -->
每个对象和变换绑定：

<!-- source-paragraph:V82-P0870 style=BodyCJK -->
SP=<A,X,T,O,C,R,I,N,J>

<!-- source-paragraph:V82-P0871 style=TableHead -->
轴

<!-- source-paragraph:V82-P0872 style=TableHead -->
状态字段核心

<!-- source-paragraph:V82-P0873 style=TableHead -->
expands 的计算见证

<!-- source-paragraph:V82-P0874 style=TableHead -->
不可替代边界

<!-- source-paragraph:V82-P0875 style=TableText -->
A 聚合层次

<!-- source-paragraph:V82-P0876 style=TableText -->
单位、成员集、分区、聚合规则、权重、排除项

<!-- source-paragraph:V82-P0877 style=TableText -->
目标总体覆盖源总体，目标分区是源分区的登记粗化

<!-- source-paragraph:V82-P0878 style=TableText -->
不得由 O、X、I 或 J 替代

<!-- source-paragraph:V82-P0879 style=TableText -->
X 空间范围

<!-- source-paragraph:V82-P0880 style=TableText -->
坐标系、空间集合、边界通道、外部连接

<!-- source-paragraph:V82-P0881 style=TableText -->
坐标对齐后源空间是真子集

<!-- source-paragraph:V82-P0882 style=TableText -->
不得由 A、O、I 或 J 替代

<!-- source-paragraph:V82-P0883 style=TableText -->
T 时间跨度

<!-- source-paragraph:V82-P0884 style=TableText -->
时间基准、窗口角色、起止点、时滞模型

<!-- source-paragraph:V82-P0885 style=TableText -->
同一基准与角色下目标区间真包含源区间

<!-- source-paragraph:V82-P0886 style=TableText -->
当前截面和长期路径不能互代

<!-- source-paragraph:V82-P0887 style=TableText -->
O 组织层级

<!-- source-paragraph:V82-P0888 style=TableText -->
组织图、版本、节点、包含边、接口、重叠

<!-- source-paragraph:V82-P0889 style=TableText -->
同版组织 DAG 中目标节点覆盖源节点祖先闭包

<!-- source-paragraph:V82-P0890 style=TableText -->
组织上位不等于 J 扩大

<!-- source-paragraph:V82-P0891 style=TableText -->
C 因果层次

<!-- source-paragraph:V82-P0892 style=TableText -->
因果模型、变量、边、干预语义、抽象映射

<!-- source-paragraph:V82-P0893 style=TableText -->
目标模型经语义保持映射覆盖源模型并增加可区分层面

<!-- source-paragraph:V82-P0894 style=TableText -->
层级标签、时序和相关不能代替因果桥

<!-- source-paragraph:V82-P0895 style=TableText -->
R 观察分辨率

<!-- source-paragraph:V82-P0896 style=TableText -->
测量协议、可区分类、参数、误差、保护性省略

<!-- source-paragraph:V82-P0897 style=TableText -->
目标协议保留源协议全部区分并至少细分一类

<!-- source-paragraph:V82-P0898 style=TableText -->
高分辨率不等于完整或有权行动

<!-- source-paragraph:V82-P0899 style=TableText -->
I 影响范围

<!-- source-paragraph:V82-P0900 style=TableText -->
结果、阈值、窗口、受影响位置、效应阶次

<!-- source-paragraph:V82-P0901 style=TableText -->
对齐后目标受影响位置集真包含源集合

<!-- source-paragraph:V82-P0902 style=TableText -->
影响和观察均不等于授权

<!-- source-paragraph:V82-P0903 style=TableText -->
N 网络拓扑范围

<!-- source-paragraph:V82-P0904 style=TableText -->
图与版本、节点、边、语义、采样边界

<!-- source-paragraph:V82-P0905 style=TableText -->
存在语义保持图嵌入且目标覆盖源图

<!-- source-paragraph:V82-P0906 style=TableText -->
网络中心不等于责任中心

<!-- source-paragraph:V82-P0907 style=TableText -->
J 管辖与授权范围

<!-- source-paragraph:V82-P0908 style=TableText -->
原子授权元组集合；每个元组固定来源、主体、单一对象、单一动作、地域、期限、撤回、有效性和证据

<!-- source-paragraph:V82-P0909 style=TableText -->
目标有效原子元组规范化集合真包含，且每个新增元组有独立有效性见证

<!-- source-paragraph:V82-P0910 style=TableText -->
任何其他轴均不能替代 J；禁止对象集与动作集做笛卡尔积

<!-- source-paragraph:V82-P0911 style=BodyCJK -->
每轴关系只有五种：equal、expands、contracts、incomparable、unknown。轴比较记录固定包含 axis_id、源/目标状态、关系、顺序见证、信息损失和不确定性。非未知关系的 order_witness 不是一句说明，而是闭合对象：comparator_id 与 comparator_version 必须对应该轴比较器，verifier_id 明确谁或什么执行验证，evidence_refs 非空，comparison_payload 给出实际映射、集合、区间、图或授权差异，verification_artifact_ref 与 verification_hash 指向可复核产物，validation_status 必须为 valid。unknown 使用带理由的缺失状态。完全相同的两状态可用内置深相等复算 equal；其他相等以及全部扩展、收缩和不可比关系，都必须从外部比较器结果注册表核对轴、版本、源/目标摘要、关系和哈希。相同状态申报扩展或收缩直接失败。没有可解析见证，只能记 unknown；contracts 是同轴 expands 的逆关系，不是凭语言印象标注。

<!-- source-paragraph:V82-P0912 style=BodyCJK -->
“九轴都要登记”不等于“九轴对一切对象都适用”。某轴整体确实不适用时，轴状态使用带理由的 not_applicable 对象，而不是删掉该轴。典型例子是没有行动主体和授权概念的自然过程：其 J 轴不适用，不等于“存在一个空授权集合”。源、目标两端经同一适用性判据均不适用时，该轴可在见证中记为 equal；仅一端不适用而另一端适用时，语义域已经改变，应记 incomparable；材料不足仍记 unknown。这样既保持九轴接口稳定，也不把人类制度语义强塞进广义世界。

<!-- source-paragraph:V82-P0913 style=BodyCJK -->
每个轴状态都须满足反身性、反对称性和传递性。为避免“差一点相等”破坏传递，轴状态先按 equality_rule 形成规范化等价类，偏序在这些等价类的商集上定义；容差只能通过预注册的共同规范化器或固定分箱把两端送入同一等价类，不能用任意两点之间“距离小于阈值”直接定义相等。反身性要求规范化状态与自身为 equal；反对称性要求双向不大于只能落入同一等价类；传递性只在中间状态、版本和见证可组合时成立，任何映射、坐标、图版本、变量或授权链断裂都会使关系回到 unknown。

<!-- source-paragraph:V82-P0914 style=BodyCJK -->
每轴的主比较量成立还不够。若该轴记录含边界通道、时滞模型、接口、误差模型、干预语义或保护性省略等辅助状态，expands 还要求这些字段存在可组合的语义保持映射；主范围扩大而辅助语义发生无映射冲突时，只能登记 incomparable 或 unknown。这使“范围更大”不会偷渡成“整个轴状态更高”。

<!-- source-paragraph:V82-P0915 style=SecH2 -->
5.3　积偏序与变换分类

<!-- source-paragraph:V82-P0916 style=BodyCJK -->
SP0≼SP1 当且仅当九轴全部为 equal 或 expands；严格关系 SP0≺SP1 还要求至少一轴 expands。机器分类按以下顺序执行：

<!-- source-paragraph:V82-P0917 style=ListPara -->
任一轴 incomparable：horizontal_or_incomparable；已知不可比不会被另一轴的未知覆盖；

<!-- source-paragraph:V82-P0918 style=ListPara -->
否则同时出现扩展和收缩：mixed；两种已知方向已经足以排除积偏序，即使还有轴未知；

<!-- source-paragraph:V82-P0919 style=ListPara -->
否则任一轴 unknown：unresolved；

<!-- source-paragraph:V82-P0920 style=ListPara -->
九轴全 equal：all_equal；

<!-- source-paragraph:V82-P0921 style=ListPara -->
仅含 equal/expands 且至少一轴扩展：elevation；

<!-- source-paragraph:V82-P0922 style=ListPara -->
仅含 equal/contracts 且至少一轴收缩：reduction。

<!-- source-paragraph:V82-P0923 style=BodyCJK -->
因此，宏观聚合同时压缩观察分辨率时通常是 mixed，不应笼统叫升格；领域类比常是 horizontal_or_incomparable；材料不足时是 unresolved。只有分类为 elevation 的实例才使用“尺度升格”。观察范围、空间范围、组织范围、影响范围或网络范围扩大，都不会改变 J；J 只能由新的有效授权元组见证扩展。

<!-- source-paragraph:V82-P0924 style=BodyCJK -->
J 状态不是“一个来源 + 一组主体 + 一组对象 + 一组动作”的独立字段拼盘，因为那会凭空生成未被授权的对象—动作组合。authorization_tuple_contract 要求每个原子元组只绑定一个来源、一个决策主体、一个对象和一个动作，同时保存地域、有效期、撤回条件、证据和独立复核；多对象或多动作必须拆成多个元组。只有状态为有效的规范化原子元组进入集合比较。J 轴扩展的见证要在 comparison_payload 中列出目标新增而源端没有的完整元组及其独立有效性证据，并与记录的 j_authorization 对齐。任意字符串、tuple ID、自称、实际控制、观察覆盖、影响扩大、上位组织位置或其他轴的扩展都不能使 J 变为 expands。

<!-- source-paragraph:V82-P0925 style=SecH2 -->
5.4　所有算子的三态与零结论门

<!-- source-paragraph:V82-P0926 style=BodyCJK -->
每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。

<!-- source-paragraph:V82-P0927 style=BodyCJK -->
算子程序统一使用四个结果状态：

<!-- source-paragraph:V82-P0928 style=ListPara -->
supported：本次选定分支的桥、决策规则和正向阈值已预注册且通过；只有 G、因果、对象/干预转换分支才强制 root-instance、预选子型和唯一成功判据，纯描述分支可把这些 G 专用字段记为 not_applicable；

<!-- source-paragraph:V82-P0929 style=ListPara -->
unsupported_or_undecided：桥接不足，或正向门未通过而零结论门也未通过；

<!-- source-paragraph:V82-P0930 style=ListPara -->
null_supported：只有预注册 null_decision_rule、等价性或充分性检验、功效或灵敏度及容差全部通过时，才支持限定零结论；

<!-- source-paragraph:V82-P0931 style=ListPara -->
not_evaluated：算子或相应分支尚未运行；已运行且描述桥成立的分支可以是 supported，不能因不需要 G-instance 而降为未评估。

<!-- source-paragraph:V82-P0932 style=BodyCJK -->
“未显著”“切断后看似不变”“效应消失”“简单模型表现相当”或“目标证据不足”都不能自动写成 null_supported。这条纪律适用于 M01—M09，而不只适用于跨层因果。

<!-- source-paragraph:V82-P0933 style=SecH2 -->
5.5　九种尺度变换算子

<!-- source-paragraph:V82-P0934 style=BodyCJK -->
每个算子都有独有 semantic_signature，不能复制 M01 的聚合语句冒充其他算子。

<!-- source-paragraph:V82-P0935 style=SecH3 -->
5.5.1　M01　聚合

<!-- source-paragraph:V82-P0936 style=BodyCJK -->
签名是“单位—总体分区聚合”。最低桥包括逐单位映射、成员与排除、权重与缺失、替代聚合规则和异质性。信息损失包括尾部、次序、协方差、局部时序及少数位置可见度。总体不能按登记规则复现、合理替代规则造成方向反转，或总体关联被回填为个体属性时，程序失败。即使聚合获得支持，也不得据总体结果直接处置成员。

<!-- source-paragraph:V82-P0937 style=SecH3 -->
5.5.2　M02　嵌套

<!-- source-paragraph:V82-P0938 style=BodyCJK -->
签名是“边界—成员嵌入”。它必须分成两条支路：

<!-- source-paragraph:V82-P0939 style=ListPara -->
描述性嵌套只检验边界、成员、重叠、退出和接口映射；它可以成立而没有任何跨层因果。

<!-- source-paragraph:V82-P0940 style=ListPara -->
跨层因果必须链接预注册 G4a 或 G4b root-instance，固定子型和唯一成功判据，并通过 CAUSAL 与三态/null 门。

<!-- source-paragraph:V82-P0941 style=BodyCJK -->
控制当前状态与共同环境后没有条件增量，并不自动证明“没有跨层作用”；只有等价/充分性、功效/灵敏度和容差门同时通过，才可登记限定零结论。描述性嵌套不生成上位优先、下位义务或 J 轴扩展。

<!-- source-paragraph:V82-P0942 style=BodyCJK -->
记录时必须在 descriptive_nesting、cross_layer_causal、object_conversion、intervention_conversion 中选一支，并分别绑定描述、因果、对象转换或干预转换模式；不得用描述性嵌套的边界材料支持后面三支。

<!-- source-paragraph:V82-P0943 style=SecH3 -->
5.5.3　M03　网络传播

<!-- source-paragraph:V82-P0944 style=BodyCJK -->
签名是“沿时间化路径传导”。必须登记节点、边、方向、权重、容量、采样边界、候选与替代路径、时延和损耗。连接或同步只生成候选；切断路径后结果不变而零结论门未通过时，仍是 unsupported_or_undecided。网络采样会遗漏弱边、离网位置和跨网桥，只保留终点影响也不能恢复传播次序。中心性不等于意图、责任或处置权限。

<!-- source-paragraph:V82-P0945 style=SecH3 -->
5.5.4　M04　时间累积

<!-- source-paragraph:V82-P0946 style=BodyCJK -->
签名是“带窗口的纵向组合”。必须冻结时间基准、基线、窗口、时滞、持久阈值和累积/衰减/恢复规则，并比较共同趋势、季节、队列和替代窗口。效应在控制后消失或随窗口变化，只表示正向支持不足；没有通过零结论门，不能发布“无累积”。基础时间组合不预证 G3；只有历史项在控制当前状态后仍提供条件增量时，才链接 G3-instance。

<!-- source-paragraph:V82-P0947 style=SecH3 -->
5.5.5　M05　制度化

<!-- source-paragraph:V82-P0948 style=BodyCJK -->
签名是“持久制度写回”。它把五个判断分开：制度事实上存在、法律有效、规范正当、保护是否成立、是否应继续。记录、角色、资源、决策规则或后续转移发生持久改变，可以支持制度化事实；授权无效、参与不足、保护机制失效、缺少申诉/反报复/回滚属于治理失败、规范争议和行动降级理由，不能据此抹掉制度已存在的事实。反过来，制度存在也不证明它合法、正当、具有充分保护或应继续。

<!-- source-paragraph:V82-P0949 style=BodyCJK -->
selected_operator_branch 只允许 institutional_fact、institutional_causal_effect、institutional_object_conversion 或 institutional_intervention_conversion。法律有效性审查、治理质量、规范正当性、保护充分性和应否继续没有任何一项能伪装成 institutional_fact 的正向或零结论。

<!-- source-paragraph:V82-P0950 style=SecH3 -->
5.5.6　M06　涌现

<!-- source-paragraph:V82-P0951 style=BodyCJK -->
签名是“互动生成目标尺度模式”。源单位、互动规则、目标对象和目标模式须与预登记简单加和模型在同一指标上比较。简单加和模型表现相当，只在充分性/等价、功效/灵敏度和容差门通过时支持“加和已足够”；否则保持未决。宏观模式不能反推唯一微观原因，也不能自动证明下行因果。下行约束须另链 G4/CAUSAL 实例。

<!-- source-paragraph:V82-P0952 style=SecH3 -->
5.5.7　M07　委托/代表

<!-- source-paragraph:V82-P0953 style=BodyCJK -->
签名是“代表事实分类与可选授权转移”。必须分开记录：代表性主张、实际代行事实、争议或自任代表、有效委托、J 轴权限转移。无授权时仍可记录实际代行及其影响和责任，但不得登记 J 扩展；授权无效会触发停止或降级，却不能把已经发生的代行与后果删除。多数、可见性、影响力、自称或实际控制都不等于有效委托。

<!-- source-paragraph:V82-P0954 style=BodyCJK -->
记录必须在 representation_claim、actual_acts、delegation_validity、J_transfer 中选一支。前三支即使获得支持也不能改变 J；只有 J_transfer 与结构化授权元组、独立有效性证据和 j_authorization 同时通过时，J 才可扩展。

<!-- source-paragraph:V82-P0955 style=SecH3 -->
5.5.8　M08　压缩/抽象

<!-- source-paragraph:V82-P0956 style=BodyCJK -->
签名是“多对一表示压缩”。源材料、算法、阈值、版本、误差、不可恢复信息和任务所需不变量必须可追踪。unknown、not_applicable、not_observable、withheld_for_protection 必须保持区分，任何一种都不能压成“不存在”。高损失表示不得支持高影响行动。

<!-- source-paragraph:V82-P0957 style=SecH3 -->
5.5.9　M09　横向迁移

<!-- source-paragraph:V82-P0958 style=BodyCJK -->
签名是“跨领域类比迁移”。必须登记映射、差异、断裂、禁止映射、目标责任链和 J 轴差异。源域材料只生成目标候选；supported 或 null_supported 都必须来自独立目标实例。目标证据不足是 not_evaluated 或 unsupported_or_undecided，不是目标机制不存在的证明。类比不生成目标领域行动授权。

<!-- source-paragraph:V82-P0959 style=SecH2 -->
5.6　通用原语的尺度边界

<!-- source-paragraph:V82-P0960 style=BodyCJK -->
通用原语是 D 类接口，不再携带经验零模型或证伪模板。尤其需要锁住四项边界：

<!-- source-paragraph:V82-P0961 style=ListPara -->
U07 的基础反馈只要求返回通道和后续状态更新，不要求 G3；持久历史增量和学习才另检 G3。

<!-- source-paragraph:V82-P0962 style=ListPara -->
U09 的瞬时需求—容量缺口不要求 G3；累积损伤或迟恢复才另检历史条件增量。

<!-- source-paragraph:V82-P0963 style=ListPara -->
U10 只登记候选痕迹、载体和保留窗口，不预证路径依赖；G3 仍须证明历史项在控制当前状态后的条件增量。

<!-- source-paragraph:V82-P0964 style=ListPara -->
U11 的基础相位模式不要求 G3 或 G4；因果触发另检 G2，迟滞另检 G3，对象转换另检 G4。

<!-- source-paragraph:V82-P0965 style=BodyCJK -->
同理，U01 只登记候选对象而不预保证 G1；U05 的关系定义不证明因果；U06 的通道字段不证明通道效应。

<!-- source-paragraph:V82-P0966 style=SecH2 -->
5.7　统一尺度变换记录

<!-- source-paragraph:V82-P0967 style=BodyCJK -->
每个实例都必须出现十四节和全部字段：

<!-- source-paragraph:V82-P0968 style=TableHead -->
节

<!-- source-paragraph:V82-P0969 style=TableHead -->
必填字段

<!-- source-paragraph:V82-P0970 style=TableText -->
identity

<!-- source-paragraph:V82-P0971 style=TableText -->
contract_id、concept_id、version、proposition_ids、purpose

<!-- source-paragraph:V82-P0972 style=TableText -->
scale

<!-- source-paragraph:V82-P0973 style=TableText -->
SP0、SP1、九条 axis_differences、unchanged_axes、transformation_class、j_authorization

<!-- source-paragraph:V82-P0974 style=TableText -->
objects

<!-- source-paragraph:V82-P0975 style=TableText -->
源/目标有效对象、source_K、target_K、identity_mapping、单位、总体、边界、成员、排除项

<!-- source-paragraph:V82-P0976 style=TableText -->
semantics

<!-- source-paragraph:V82-P0977 style=TableText -->
preserved_core、allowed_changes、lost_elements、prohibited_mappings

<!-- source-paragraph:V82-P0978 style=TableText -->
transformation

<!-- source-paragraph:V82-P0979 style=TableText -->
单一算子、selected_operator_branch、claim_mode、规则、因果桥、时滞、映射误差、有效期、root-instance、子型、成功判据、正向和零决策规则、正向阈值、等价/充分性检验、功效/灵敏度、容差、结果状态

<!-- source-paragraph:V82-P0980 style=TableText -->
variables

<!-- source-paragraph:V82-P0981 style=TableText -->
输入、状态、输出和跨变量依赖

<!-- source-paragraph:V82-P0982 style=TableText -->
evidence

<!-- source-paragraph:V82-P0983 style=TableText -->
源/目标证据、覆盖、异质性、反例、缺席信号、替代解释、残差检验、复制或外部验证

<!-- source-paragraph:V82-P0984 style=TableText -->
loss

<!-- source-paragraph:V82-P0985 style=TableText -->
压缩细节、不可恢复信息、低可见位置和局部排除区

<!-- source-paragraph:V82-P0986 style=TableText -->
responsibility

<!-- source-paragraph:V82-P0987 style=TableText -->
行动者、决策者、授权者、承接载体、责任主体、受益者和成本承担者

<!-- source-paragraph:V82-P0988 style=TableText -->
normative

<!-- source-paragraph:V82-P0989 style=TableText -->
价值前提、选择类型、规范选择记录、运行时 N 原则、授权来源、C12 门和 O1-O4 程序

<!-- source-paragraph:V82-P0990 style=TableText -->
protection

<!-- source-paragraph:V82-P0991 style=TableText -->
保护适用性、低权力位置、安全提交和反报复

<!-- source-paragraph:V82-P0992 style=TableText -->
action

<!-- source-paragraph:V82-P0993 style=TableText -->
判断上限、行动上限、禁止动作、停止条件、责任人和机器可指向的 selected_action

<!-- source-paragraph:V82-P0994 style=TableText -->
correction

<!-- source-paragraph:V82-P0995 style=TableText -->
申诉、复核、回滚、修复和写回

<!-- source-paragraph:V82-P0996 style=TableText -->
lifecycle

<!-- source-paragraph:V82-P0997 style=TableText -->
有效期、复审点、暂停和退场

<!-- source-paragraph:V82-P0998 style=BodyCJK -->
source_K、target_K 和 identity_mapping 共同决定对象保持、转换或不可比；同名不是同一性证据。映射记录必须同时保存源、目标 K 的摘要，源对象与目标对象分别在两套 K 下的四项判据结果，正向与反向映射，保持和违反的判据，结果前冻结的预注册引用，以及可复核的验证制品与哈希。判据结果只允许 passed、failed 或 undetermined，不能用一个布尔值掩盖是哪一项没有通过。

<!-- source-paragraph:V82-P0999 style=TableHead -->
K 映射分类

<!-- source-paragraph:V82-P1000 style=TableHead -->
最低成立条件

<!-- source-paragraph:V82-P1001 style=TableHead -->
结果上限

<!-- source-paragraph:V82-P1002 style=TableText -->
same_object

<!-- source-paragraph:V82-P1003 style=TableText -->
双向映射均有效；源对象与目标对象在 source_K、target_K 下四项检查均通过；保持判据非空且违反判据为空

<!-- source-paragraph:V82-P1004 style=TableText -->
可在当前合同内沿用对象身份，但不推出语义、因果或规范性质也保持

<!-- source-paragraph:V82-P1005 style=TableText -->
converted_object

<!-- source-paragraph:V82-P1006 style=TableText -->
source_under_source_K 与 target_under_target_K 通过，target_under_source_K 失败；违反项和结果前预注册引用具体；另有 object_conversion 模式及取得支持的 G4b 实例

<!-- source-paragraph:V82-P1007 style=TableText -->
只登记预注册 K 下的对象转换，不得在结果后改写 K 制造转换

<!-- source-paragraph:V82-P1008 style=TableText -->
incomparable

<!-- source-paragraph:V82-P1009 style=TableText -->
两端各自在本方 K 下通过，至少一个交叉 K 检查失败；正反向映射保存完整尝试记录且至少一项验证为无效，并有可解析证据

<!-- source-paragraph:V82-P1010 style=TableText -->
表示已知不可比，只能 unsupported_or_undecided；不是“尚未评估”

<!-- source-paragraph:V82-P1011 style=TableText -->
undetermined

<!-- source-paragraph:V82-P1012 style=TableText -->
检验尚未运行，或必要映射、判据未知或不可观察；四项结果均保持 undetermined

<!-- source-paragraph:V82-P1013 style=TableText -->
只能 unsupported_or_undecided 或 not_evaluated；不构成不可比或对象转换

<!-- source-paragraph:V82-P1014 style=BodyCJK -->
只有源/目标对象和两套 K 都可由验证器重算为深相等时，才允许 builtin:deep-identity。其他非平凡保持或对象转换必须把 mapping_id 交给独立 identity_mapping_results 注册表，逐项核对对象摘要、K 摘要、方向映射、四项判据结果、验证制品和哈希；记录内部自报 valid 或一个看似正确的 ID 前缀都不能充当证明。

<!-- source-paragraph:V82-P1015 style=BodyCJK -->
对象转换模式与结果四态必须一致：supported 才对应 converted_object；null_supported 对应通过零结论三门的 same_object；unsupported_or_undecided 只允许保持、已知不可比或未决；not_evaluated 必须保持 undetermined。因此，未检验和检验失败都不能先把目标写成“已经转换”。其他 claim_mode 也不得在同一条原子记录里兼报 converted_object，对象转换必须拆成自己的原子检验。

<!-- source-paragraph:V82-P1016 style=BodyCJK -->
claim_mode 为 root_hypothesis、causal、object_conversion 或 intervention_conversion 时必须填写 root_instance_ids，后三者还必须给出非空因果桥；只有 descriptive_mapping 可把 root-instance、子型和成功判据标为 not_applicable。非描述模式登记 supported 或 null_supported 时，还必须向验证器提交可解析的 root-instance 注册表，并核对实例 ID、根族、合同版本、预选子型、唯一成功判据与实例状态；一个看似正确的字符串前缀不能充当实例。描述桥正向门通过时可以记 supported，只有所选模式没有运行时才记 not_evaluated。

<!-- source-paragraph:V82-P1017 style=BodyCJK -->
十四节是稳定接口，不是把人类治理语义投射给所有对象。protection.applicability 必须显式登记对象类型、下游用途、理由和证据引用，不能从 actors 等空列表反推。对象类型为 nonhuman，且用途只含 description_only 或有证据证明不影响人类/有感主体的 nonhuman_intervention_without_human_or_sentient_effect 时，safe_submission 与 anti_retaliation 可带理由记 not_applicable；但现实实验或工程干预仍有行动主体和对象，必须填写具体 J、行动责任人、停止、复核与回滚，只有纯描述用途才允许 J 不适用。自然系统中的能量、物质或计算资源本身不触发这套人类保护合同。对象为人类、有感非人、混合或未知，或用途涉及人的评价、其稀缺资源配置、权利、暴露风险或现实处置时，保护字段立即成为强制项，不得沿用先前的不适用状态。保护不适用绝不推出行动正当，规范选择仍另行判断。

<!-- source-paragraph:V82-P1018 style=BodyCJK -->
action_owner 只说明谁负责执行或停止，不能反推 claim_mode=intervention_conversion，也不能证明行动有效或正当。任何外部行动必须链接 selection_record_id，公开 value_premises 与运行时 normative_principle_ids；N1 单独只能阻止越权，不能产生正向方案。选择记录中的 feasible_alternatives 不是名称列表，而是带稳定 option_id 的结构化方案；每项冻结 option_kind、动作类型、目标对象、地域、有效期、可逆性、预期影响和分配影响，并且恰有一项 option_kind=no_action，由 no_action_option_id 唯一指向。selected_action.selected_option_id 必须解析到一项 external_action，而且其动作、对象、地域和有效期与该方案逐项相等；选择不行动 ID、只对上自然语言标签，或同时改写动作与 J 而不改获准方案，都必须被拒绝。至少一条当前有效且独立复核的 J 原子授权元组还必须同时覆盖该主体、对象、动作、地域和期限，并与授权来源一致；一条无关但形式有效的授权不能为拟议行动背书。记录还必须有通过的十组件 c12_gate、O1-O4 procedure_ids、行动责任人、禁止动作、停止、保护、申诉、复核和回滚。缺任一项时，行动上限只能是不行动或继续审议；经验上的干预转换另由相应 root-instance 判断。

<!-- source-paragraph:V82-P1019 style=BodyCJK -->
记录链只提供组合次序，不把前一步的支持自动传递给后一步。链校验必须保证每步 contract_id 唯一、每步只有一个算子、相邻对象引用及同一性判据兼容、前一 SP1 与后一 SP0 一致；任一步未决、失效或损失超限，都要在链级输出中保留，不能被最终一步的成功覆盖。

<!-- source-paragraph:V82-P1020 style=SecH2 -->
5.8　机器校验与保护底板

<!-- source-paragraph:V82-P1021 style=BodyCJK -->
record_schema 要求十四节和各节字段集合精确一致，字段类型由 field_types_by_section 固定。九条轴比较记录不得缺轴或重复；每条非未知轴关系必须提交结构化且由对应比较器验证为有效的见证；transformation_class 必须与分类算法输出一致；算子 ID 必须使用限定形式，语义签名必须互异。这里的机器分类器只组合已经通过领域比较器的逐轴关系，不自行替代空间几何、组织图、因果抽象、网络嵌入、对象同一性或授权有效性判断；没有可解析的 comparator_results 与非平凡 identity_mapping_results 产物，就不允许把记录内自报关系升级为尺度升格。源对象与目标对象的经验材料必须引用可解析的独立记录，内部概念编号和框架说明不得充当证据。

<!-- source-paragraph:V82-P1022 style=BodyCJK -->
四种缺失状态构成封闭词表：unknown 表示当前未知，not_applicable 表示按合同确实不适用，not_observable 表示当前通道和窗口不可观察，withheld_for_protection 表示为保护而不公开。四者都不是“不存在”，也不能删除字段代替状态。

<!-- source-paragraph:V82-P1023 style=BodyCJK -->
carrying_vehicles 与 responsible_subjects 必须分栏；承接、可见、受影响或能力较强都不自动产生责任。凡对人类或有感主体的权利、稀缺资源配置、暴露风险或现实处置产生影响，保护底板必须识别低权力位置和局部排除区，提供安全提交、反报复、停止、申诉、复核和回滚，且不得记为不适用。保护不足时，判断上限与行动上限同时降低。纯描述记录的条件性不适用也不能被下游行动继承；用途改变时必须重开保护审查。

<!-- source-paragraph:V82-P1024 style=SecH2 -->
5.9　证据边界与独立支持

<!-- source-paragraph:V82-P1025 style=BodyCJK -->
M01—M09 的名称、编号、语义签名和分类结果只规定变换应怎样描述与检验，不构成变换已经发生、映射有效或目标性质成立的经验支持。内部概念标签、示例、字段完整度和算法自报结果均不得进入 source_evidence 或 target_evidence 代替对象材料。

<!-- source-paragraph:V82-P1026 style=BodyCJK -->
每个实际变换必须分别在源对象和目标对象上取得可解析的独立材料，明确映射、保持项、改变项、丢失项、误差与竞争解释，并接受同一结果状态、正向门和零结论门。源域材料只能生成目标候选；目标侧没有独立支持时，结论停在待检验映射或未知。

<!-- source-paragraph:V82-P1027 style=SecH2 -->
5.10　跨圈层关系变换

<!-- source-paragraph:V82-P1028 style=BodyCJK -->
尺度变换与圈层关系变换必须分开。尺度变换回答同一问题在 SP0 与 SP1 之间哪些变量保持、改变或丢失；圈层关系变换回答两个或多个候选圈层在同一或不同尺度上如何并列、包含、重叠、桥接、竞争或临时形成。一个关系变化可能伴随尺度变化，但不能用其中一个词替代另一个合同。

<!-- source-paragraph:V82-P1029 style=BodyCJK -->
跨圈层记录至少包含关系源、关系目标、静态关系类型、成员或接口基准、方向、通道、时延、阈值、时间窗、证据、反例和前后快照。transformed 只作为关系更新结果：原平行关系可能因桥接者出现而转为桥接，重叠关系可能因制度整合转为嵌套，临时圈层可能制度化或解体。每次转化都要检查 K 是否保持；K 失效时记录对象转换，不以改名延续旧对象。

<!-- source-paragraph:V82-P1030 style=TableHead -->
变换问题

<!-- source-paragraph:V82-P1031 style=TableHead -->
需要调用

<!-- source-paragraph:V82-P1032 style=TableHead -->
不得偷换

<!-- source-paragraph:V82-P1033 style=TableText -->
个体状态能否代表团队

<!-- source-paragraph:V82-P1034 style=TableText -->
聚合 M01、尺度合同与分布损失

<!-- source-paragraph:V82-P1035 style=TableText -->
成员属于团队不等于代表团队

<!-- source-paragraph:V82-P1036 style=TableText -->
团队是否被组织包含

<!-- source-paragraph:V82-P1037 style=TableText -->
嵌套 M02 与具体包含基准

<!-- source-paragraph:V82-P1038 style=TableText -->
共同上级不等于成员包含

<!-- source-paragraph:V82-P1039 style=TableText -->
两圈层是否因共享成员相关

<!-- source-paragraph:V82-P1040 style=TableText -->
重叠关系、成员映射与共同环境

<!-- source-paragraph:V82-P1041 style=TableText -->
重叠不自动产生有效反馈

<!-- source-paragraph:V82-P1042 style=TableText -->
桥接者是否改变另一圈层

<!-- source-paragraph:V82-P1043 style=TableText -->
M03 传播、通道和反事实

<!-- source-paragraph:V82-P1044 style=TableText -->
接触不等于传导，传导不等于代表

<!-- source-paragraph:V82-P1045 style=TableText -->
临时群体是否形成持久对象

<!-- source-paragraph:V82-P1046 style=TableText -->
G1、G3、M05 与 K

<!-- source-paragraph:V82-P1047 style=TableText -->
留痕不等于制度化

<!-- source-paragraph:V82-P1048 style=BodyCJK -->
多重成员关系要求同一行动者在多个圈层中保留不同角色、可见信息、责任、风险和退出能力。不得先把行动者聚合为单一状态，再把该状态复制到所有圈层。跨圈层推演应从局部状态出发，经已声明的成员或接口通道传播，并逐步登记聚合损失。

<!-- source-paragraph:V82-P1049 style=SecH3 -->
5.10.1　三类变换必须分开

<!-- source-paragraph:V82-P1050 style=BodyCJK -->
尺度变换回答同一问题在两个尺度剖面之间哪些变量保持、改变或丢失；圈层关系变换回答候选圈层之间的并列、包含、重叠、桥接、竞争或临时关系如何更新；表示或表述转义回答一个有来源的载荷怎样进入目标任务的词汇、变量或表达。三者可以同时发生，但必须拆成有序记录。

<!-- source-paragraph:V82-P1051 style=BodyCJK -->
本版把转义作为一等运行合同，但不新增第十尺度算子。一次转义可以调用传播、压缩、横向迁移或其他既有算子；只有未来证明它具有不可约化的独立输入输出、状态机、失败码和验证过程，才考虑提升为独立算子。

<!-- source-paragraph:V82-P1052 style=SecH3 -->
5.10.2　转义损失审计

<!-- source-paragraph:V82-P1053 style=BodyCJK -->
若两个在源任务中可区分的源状态，在目标表示中无法区分，则针对该项区别登记任务相关损失。恒等映射、可逆编码或对目标任务充分的映射可能没有检测到相关损失，因此规则是“不得预设无损”，而不是“必然有损”。

<!-- source-paragraph:V82-P1054 style=BodyCJK -->
审计项

<!-- source-paragraph:V82-P1055 style=BodyCJK -->
最低问题

<!-- source-paragraph:V82-P1056 style=BodyCJK -->
不得偷换

<!-- source-paragraph:V82-P1057 style=BodyCJK -->
保持

<!-- source-paragraph:V82-P1058 style=BodyCJK -->
哪些事实、关系、模态、权利或不确定性必须不变

<!-- source-paragraph:V82-P1059 style=BodyCJK -->
保持标题不等于保持语义

<!-- source-paragraph:V82-P1060 style=BodyCJK -->
改变

<!-- source-paragraph:V82-P1061 style=BodyCJK -->
哪些格式、单位、粒度或表达允许变化

<!-- source-paragraph:V82-P1062 style=BodyCJK -->
允许改变不等于任意改义

<!-- source-paragraph:V82-P1063 style=BodyCJK -->
折叠

<!-- source-paragraph:V82-P1064 style=BodyCJK -->
哪些源差异在目标端合并

<!-- source-paragraph:V82-P1065 style=BodyCJK -->
折叠不等于源差异不存在

<!-- source-paragraph:V82-P1066 style=BodyCJK -->
遗漏

<!-- source-paragraph:V82-P1067 style=BodyCJK -->
哪些内容未进入目标表示及原因

<!-- source-paragraph:V82-P1068 style=BodyCJK -->
保护性不公开不等于不存在

<!-- source-paragraph:V82-P1069 style=BodyCJK -->
新增

<!-- source-paragraph:V82-P1070 style=BodyCJK -->
哪些解释、推断或目标变量由转换产生

<!-- source-paragraph:V82-P1071 style=BodyCJK -->
新增变量不等于发现现实实体

<!-- source-paragraph:V82-P1072 style=BodyCJK -->
回返

<!-- source-paragraph:V82-P1073 style=BodyCJK -->
异常出现时回到哪个父记录或合同

<!-- source-paragraph:V82-P1074 style=BodyCJK -->
回返只重开审查，不修补旧运行

<!-- source-paragraph:V82-P1075 style=BodyCJK -->
往返重构可以作为检验，但不是充分条件。一个转换可能借助隐藏源记录实现表面往返，却没有保持目标任务语义；另一个单向摘要可能对指定任务充分。复核必须回到预先声明的保持项、损失容限和目标侧结果。

<!-- source-paragraph:V82-P1076 style=SecH3 -->
5.10.3　有效变量、闭合与残差回返

<!-- source-paragraph:V82-P1077 style=BodyCJK -->
有效变量是目标尺度或目标任务中，为压缩状态并改善预定解释、前瞻或方案比较而提出的变量候选。它必须绑定对象、尺度、时间窗、任务、测量、简单基线、误差、失效与退役；有效不等于真实实体、根因、普遍变量或授权依据。

<!-- source-paragraph:V82-P1078 style=BodyCJK -->
目标表示不默认动力闭合。被排除变量是否仍带来预定条件信息、预测或干预增量，继续走 G4 的正向门与零结论门。未达到显著增量不能自动证明闭合；出现增量时，把相应影响登记为记忆、噪声、迟滞、未解析项或残差候选，不能按形状直接命名新实体。

<!-- source-paragraph:V82-P1079 style=BodyCJK -->
统一尺度变换记录的下一版本应在既有十四节内增加任务、转义父记录、折叠差异、回返地址、重构检验和目标有效变量候选。旧记录结构继续可读，新字段缺失时明确标为旧版本，不做静默补写。

<!-- source-paragraph:V82-P1080 style=SecH2 -->
5.11　平行与嵌套的同时表示

<!-- source-paragraph:V82-P1081 style=BodyCJK -->
现实结构不是单棵层级树。局部包含关系可以与横向网络、成员重叠、竞争资源和平台桥接同时存在。表示层采用有向多重关系图：节点维持各自对象合同，边维持各自关系合同；“上层”只表示某项包含、管辖或聚合关系，不表示更真实、更正确或更有权。

<!-- source-paragraph:V82-P1082 style=BodyCJK -->
当多个圈层共享环境却没有直接通道时，模型保留共同条件节点，不虚构圈层间直接边；当通道只在事件窗口内开放时，边具有起止时间；当不同关系方向相反时，分别建边。这样才能在事件发生后判断哪条关系真正改变，而不是把整个结构一次性重画成事后故事。

## Canonical Records

<!-- canonical-records:start -->
```json
{
  "paragraphs": [
    {
      "anchor": "V82-P0863",
      "ordinal": 863,
      "style": "PartTitle",
      "text": "第五部分　跨尺度与跨圈层变换"
    },
    {
      "anchor": "V82-P0864",
      "ordinal": 864,
      "style": "BodyCJK",
      "text": "本部分回答：对象、观察或行动从 SP0 变到 SP1 时，哪些内容得到扩展，哪些内容发生收缩，哪些位置不可比较，凭什么建立转换桥，以及什么信息会在转换中丢失。一般过程统称尺度变换；只有九轴积偏序严格成立时，才称尺度升格。"
    },
    {
      "anchor": "V82-P0865",
      "ordinal": 865,
      "style": "SecH2",
      "text": "5.1　合同角色与无歧义引用"
    },
    {
      "anchor": "V82-P0866",
      "ordinal": 866,
      "style": "BodyCJK",
      "text": "九个尺度轴是 D 类定义，角色为 scale_axis_definition；九个转换算子是 O 类程序，角色为 scale_transformation_operator；U01—U11 是 D 类通用原语定义，角色为 universal_primitive_definition。定义和程序不冒充经验真值，具体跨层因果、对象转换或零结论必须链接预注册 root-instance。"
    },
    {
      "anchor": "V82-P0867",
      "ordinal": 867,
      "style": "BodyCJK",
      "text": "尺度实体一律使用限定 ID：scale_axis:A 至 scale_axis:J、scale_operator:M01 至 scale_operator:M09、universal_primitive:U01 至 universal_primitive:U11。因此，scale_axis:O 表示组织层级，claim_type=O 表示操作程序，二者不会混淆。依赖只分为 inferential_requires、protocol_requires、specializes 和 applies_to；协议使用 CAUSAL、EVIDENCE、ANALOGY、SOURCE 等正式 ID，不使用中文简称或裸轴名。"
    },
    {
      "anchor": "V82-P0868",
      "ordinal": 868,
      "style": "SecH2",
      "text": "5.2　九轴状态与逐轴比较"
    },
    {
      "anchor": "V82-P0869",
      "ordinal": 869,
      "style": "BodyCJK",
      "text": "每个对象和变换绑定："
    },
    {
      "anchor": "V82-P0870",
      "ordinal": 870,
      "style": "BodyCJK",
      "text": "SP=<A,X,T,O,C,R,I,N,J>"
    },
    {
      "anchor": "V82-P0871",
      "ordinal": 871,
      "style": "TableHead",
      "text": "轴"
    },
    {
      "anchor": "V82-P0872",
      "ordinal": 872,
      "style": "TableHead",
      "text": "状态字段核心"
    },
    {
      "anchor": "V82-P0873",
      "ordinal": 873,
      "style": "TableHead",
      "text": "expands 的计算见证"
    },
    {
      "anchor": "V82-P0874",
      "ordinal": 874,
      "style": "TableHead",
      "text": "不可替代边界"
    },
    {
      "anchor": "V82-P0875",
      "ordinal": 875,
      "style": "TableText",
      "text": "A 聚合层次"
    },
    {
      "anchor": "V82-P0876",
      "ordinal": 876,
      "style": "TableText",
      "text": "单位、成员集、分区、聚合规则、权重、排除项"
    },
    {
      "anchor": "V82-P0877",
      "ordinal": 877,
      "style": "TableText",
      "text": "目标总体覆盖源总体，目标分区是源分区的登记粗化"
    },
    {
      "anchor": "V82-P0878",
      "ordinal": 878,
      "style": "TableText",
      "text": "不得由 O、X、I 或 J 替代"
    },
    {
      "anchor": "V82-P0879",
      "ordinal": 879,
      "style": "TableText",
      "text": "X 空间范围"
    },
    {
      "anchor": "V82-P0880",
      "ordinal": 880,
      "style": "TableText",
      "text": "坐标系、空间集合、边界通道、外部连接"
    },
    {
      "anchor": "V82-P0881",
      "ordinal": 881,
      "style": "TableText",
      "text": "坐标对齐后源空间是真子集"
    },
    {
      "anchor": "V82-P0882",
      "ordinal": 882,
      "style": "TableText",
      "text": "不得由 A、O、I 或 J 替代"
    },
    {
      "anchor": "V82-P0883",
      "ordinal": 883,
      "style": "TableText",
      "text": "T 时间跨度"
    },
    {
      "anchor": "V82-P0884",
      "ordinal": 884,
      "style": "TableText",
      "text": "时间基准、窗口角色、起止点、时滞模型"
    },
    {
      "anchor": "V82-P0885",
      "ordinal": 885,
      "style": "TableText",
      "text": "同一基准与角色下目标区间真包含源区间"
    },
    {
      "anchor": "V82-P0886",
      "ordinal": 886,
      "style": "TableText",
      "text": "当前截面和长期路径不能互代"
    },
    {
      "anchor": "V82-P0887",
      "ordinal": 887,
      "style": "TableText",
      "text": "O 组织层级"
    },
    {
      "anchor": "V82-P0888",
      "ordinal": 888,
      "style": "TableText",
      "text": "组织图、版本、节点、包含边、接口、重叠"
    },
    {
      "anchor": "V82-P0889",
      "ordinal": 889,
      "style": "TableText",
      "text": "同版组织 DAG 中目标节点覆盖源节点祖先闭包"
    },
    {
      "anchor": "V82-P0890",
      "ordinal": 890,
      "style": "TableText",
      "text": "组织上位不等于 J 扩大"
    },
    {
      "anchor": "V82-P0891",
      "ordinal": 891,
      "style": "TableText",
      "text": "C 因果层次"
    },
    {
      "anchor": "V82-P0892",
      "ordinal": 892,
      "style": "TableText",
      "text": "因果模型、变量、边、干预语义、抽象映射"
    },
    {
      "anchor": "V82-P0893",
      "ordinal": 893,
      "style": "TableText",
      "text": "目标模型经语义保持映射覆盖源模型并增加可区分层面"
    },
    {
      "anchor": "V82-P0894",
      "ordinal": 894,
      "style": "TableText",
      "text": "层级标签、时序和相关不能代替因果桥"
    },
    {
      "anchor": "V82-P0895",
      "ordinal": 895,
      "style": "TableText",
      "text": "R 观察分辨率"
    },
    {
      "anchor": "V82-P0896",
      "ordinal": 896,
      "style": "TableText",
      "text": "测量协议、可区分类、参数、误差、保护性省略"
    },
    {
      "anchor": "V82-P0897",
      "ordinal": 897,
      "style": "TableText",
      "text": "目标协议保留源协议全部区分并至少细分一类"
    },
    {
      "anchor": "V82-P0898",
      "ordinal": 898,
      "style": "TableText",
      "text": "高分辨率不等于完整或有权行动"
    },
    {
      "anchor": "V82-P0899",
      "ordinal": 899,
      "style": "TableText",
      "text": "I 影响范围"
    },
    {
      "anchor": "V82-P0900",
      "ordinal": 900,
      "style": "TableText",
      "text": "结果、阈值、窗口、受影响位置、效应阶次"
    },
    {
      "anchor": "V82-P0901",
      "ordinal": 901,
      "style": "TableText",
      "text": "对齐后目标受影响位置集真包含源集合"
    },
    {
      "anchor": "V82-P0902",
      "ordinal": 902,
      "style": "TableText",
      "text": "影响和观察均不等于授权"
    },
    {
      "anchor": "V82-P0903",
      "ordinal": 903,
      "style": "TableText",
      "text": "N 网络拓扑范围"
    },
    {
      "anchor": "V82-P0904",
      "ordinal": 904,
      "style": "TableText",
      "text": "图与版本、节点、边、语义、采样边界"
    },
    {
      "anchor": "V82-P0905",
      "ordinal": 905,
      "style": "TableText",
      "text": "存在语义保持图嵌入且目标覆盖源图"
    },
    {
      "anchor": "V82-P0906",
      "ordinal": 906,
      "style": "TableText",
      "text": "网络中心不等于责任中心"
    },
    {
      "anchor": "V82-P0907",
      "ordinal": 907,
      "style": "TableText",
      "text": "J 管辖与授权范围"
    },
    {
      "anchor": "V82-P0908",
      "ordinal": 908,
      "style": "TableText",
      "text": "原子授权元组集合；每个元组固定来源、主体、单一对象、单一动作、地域、期限、撤回、有效性和证据"
    },
    {
      "anchor": "V82-P0909",
      "ordinal": 909,
      "style": "TableText",
      "text": "目标有效原子元组规范化集合真包含，且每个新增元组有独立有效性见证"
    },
    {
      "anchor": "V82-P0910",
      "ordinal": 910,
      "style": "TableText",
      "text": "任何其他轴均不能替代 J；禁止对象集与动作集做笛卡尔积"
    },
    {
      "anchor": "V82-P0911",
      "ordinal": 911,
      "style": "BodyCJK",
      "text": "每轴关系只有五种：equal、expands、contracts、incomparable、unknown。轴比较记录固定包含 axis_id、源/目标状态、关系、顺序见证、信息损失和不确定性。非未知关系的 order_witness 不是一句说明，而是闭合对象：comparator_id 与 comparator_version 必须对应该轴比较器，verifier_id 明确谁或什么执行验证，evidence_refs 非空，comparison_payload 给出实际映射、集合、区间、图或授权差异，verification_artifact_ref 与 verification_hash 指向可复核产物，validation_status 必须为 valid。unknown 使用带理由的缺失状态。完全相同的两状态可用内置深相等复算 equal；其他相等以及全部扩展、收缩和不可比关系，都必须从外部比较器结果注册表核对轴、版本、源/目标摘要、关系和哈希。相同状态申报扩展或收缩直接失败。没有可解析见证，只能记 unknown；contracts 是同轴 expands 的逆关系，不是凭语言印象标注。"
    },
    {
      "anchor": "V82-P0912",
      "ordinal": 912,
      "style": "BodyCJK",
      "text": "“九轴都要登记”不等于“九轴对一切对象都适用”。某轴整体确实不适用时，轴状态使用带理由的 not_applicable 对象，而不是删掉该轴。典型例子是没有行动主体和授权概念的自然过程：其 J 轴不适用，不等于“存在一个空授权集合”。源、目标两端经同一适用性判据均不适用时，该轴可在见证中记为 equal；仅一端不适用而另一端适用时，语义域已经改变，应记 incomparable；材料不足仍记 unknown。这样既保持九轴接口稳定，也不把人类制度语义强塞进广义世界。"
    },
    {
      "anchor": "V82-P0913",
      "ordinal": 913,
      "style": "BodyCJK",
      "text": "每个轴状态都须满足反身性、反对称性和传递性。为避免“差一点相等”破坏传递，轴状态先按 equality_rule 形成规范化等价类，偏序在这些等价类的商集上定义；容差只能通过预注册的共同规范化器或固定分箱把两端送入同一等价类，不能用任意两点之间“距离小于阈值”直接定义相等。反身性要求规范化状态与自身为 equal；反对称性要求双向不大于只能落入同一等价类；传递性只在中间状态、版本和见证可组合时成立，任何映射、坐标、图版本、变量或授权链断裂都会使关系回到 unknown。"
    },
    {
      "anchor": "V82-P0914",
      "ordinal": 914,
      "style": "BodyCJK",
      "text": "每轴的主比较量成立还不够。若该轴记录含边界通道、时滞模型、接口、误差模型、干预语义或保护性省略等辅助状态，expands 还要求这些字段存在可组合的语义保持映射；主范围扩大而辅助语义发生无映射冲突时，只能登记 incomparable 或 unknown。这使“范围更大”不会偷渡成“整个轴状态更高”。"
    },
    {
      "anchor": "V82-P0915",
      "ordinal": 915,
      "style": "SecH2",
      "text": "5.3　积偏序与变换分类"
    },
    {
      "anchor": "V82-P0916",
      "ordinal": 916,
      "style": "BodyCJK",
      "text": "SP0≼SP1 当且仅当九轴全部为 equal 或 expands；严格关系 SP0≺SP1 还要求至少一轴 expands。机器分类按以下顺序执行："
    },
    {
      "anchor": "V82-P0917",
      "ordinal": 917,
      "style": "ListPara",
      "text": "任一轴 incomparable：horizontal_or_incomparable；已知不可比不会被另一轴的未知覆盖；"
    },
    {
      "anchor": "V82-P0918",
      "ordinal": 918,
      "style": "ListPara",
      "text": "否则同时出现扩展和收缩：mixed；两种已知方向已经足以排除积偏序，即使还有轴未知；"
    },
    {
      "anchor": "V82-P0919",
      "ordinal": 919,
      "style": "ListPara",
      "text": "否则任一轴 unknown：unresolved；"
    },
    {
      "anchor": "V82-P0920",
      "ordinal": 920,
      "style": "ListPara",
      "text": "九轴全 equal：all_equal；"
    },
    {
      "anchor": "V82-P0921",
      "ordinal": 921,
      "style": "ListPara",
      "text": "仅含 equal/expands 且至少一轴扩展：elevation；"
    },
    {
      "anchor": "V82-P0922",
      "ordinal": 922,
      "style": "ListPara",
      "text": "仅含 equal/contracts 且至少一轴收缩：reduction。"
    },
    {
      "anchor": "V82-P0923",
      "ordinal": 923,
      "style": "BodyCJK",
      "text": "因此，宏观聚合同时压缩观察分辨率时通常是 mixed，不应笼统叫升格；领域类比常是 horizontal_or_incomparable；材料不足时是 unresolved。只有分类为 elevation 的实例才使用“尺度升格”。观察范围、空间范围、组织范围、影响范围或网络范围扩大，都不会改变 J；J 只能由新的有效授权元组见证扩展。"
    },
    {
      "anchor": "V82-P0924",
      "ordinal": 924,
      "style": "BodyCJK",
      "text": "J 状态不是“一个来源 + 一组主体 + 一组对象 + 一组动作”的独立字段拼盘，因为那会凭空生成未被授权的对象—动作组合。authorization_tuple_contract 要求每个原子元组只绑定一个来源、一个决策主体、一个对象和一个动作，同时保存地域、有效期、撤回条件、证据和独立复核；多对象或多动作必须拆成多个元组。只有状态为有效的规范化原子元组进入集合比较。J 轴扩展的见证要在 comparison_payload 中列出目标新增而源端没有的完整元组及其独立有效性证据，并与记录的 j_authorization 对齐。任意字符串、tuple ID、自称、实际控制、观察覆盖、影响扩大、上位组织位置或其他轴的扩展都不能使 J 变为 expands。"
    },
    {
      "anchor": "V82-P0925",
      "ordinal": 925,
      "style": "SecH2",
      "text": "5.4　所有算子的三态与零结论门"
    },
    {
      "anchor": "V82-P0926",
      "ordinal": 926,
      "style": "BodyCJK",
      "text": "每条原子记录的 operator_ids 必须且只能包含一个算子，selected_operator_branch 再从该算子的分支注册表中唯一选择内部支路，最后用 claim_mode 声明本次评价的模式：descriptive_mapping（描述映射）、root_hypothesis（根假设实例）、causal（因果桥）、object_conversion（对象转换）或 intervention_conversion（干预转换）。分支注册表明确每个支路允许哪些模式；三者必须相容并在看结果前冻结，不能因正向门失败切换支路或退回较宽松的描述模式，也不能把一个模式的材料用于救援另一个模式。若一个实际过程包含多个算子，须拆成有序原子记录链：前一步的目标对象与 SP1 对齐后一步的源对象与 SP0，每一步各自登记结果状态、证据、损失和误差。一个总结果不能替多步分别结案。"
    },
    {
      "anchor": "V82-P0927",
      "ordinal": 927,
      "style": "BodyCJK",
      "text": "算子程序统一使用四个结果状态："
    },
    {
      "anchor": "V82-P0928",
      "ordinal": 928,
      "style": "ListPara",
      "text": "supported：本次选定分支的桥、决策规则和正向阈值已预注册且通过；只有 G、因果、对象/干预转换分支才强制 root-instance、预选子型和唯一成功判据，纯描述分支可把这些 G 专用字段记为 not_applicable；"
    },
    {
      "anchor": "V82-P0929",
      "ordinal": 929,
      "style": "ListPara",
      "text": "unsupported_or_undecided：桥接不足，或正向门未通过而零结论门也未通过；"
    },
    {
      "anchor": "V82-P0930",
      "ordinal": 930,
      "style": "ListPara",
      "text": "null_supported：只有预注册 null_decision_rule、等价性或充分性检验、功效或灵敏度及容差全部通过时，才支持限定零结论；"
    },
    {
      "anchor": "V82-P0931",
      "ordinal": 931,
      "style": "ListPara",
      "text": "not_evaluated：算子或相应分支尚未运行；已运行且描述桥成立的分支可以是 supported，不能因不需要 G-instance 而降为未评估。"
    },
    {
      "anchor": "V82-P0932",
      "ordinal": 932,
      "style": "BodyCJK",
      "text": "“未显著”“切断后看似不变”“效应消失”“简单模型表现相当”或“目标证据不足”都不能自动写成 null_supported。这条纪律适用于 M01—M09，而不只适用于跨层因果。"
    },
    {
      "anchor": "V82-P0933",
      "ordinal": 933,
      "style": "SecH2",
      "text": "5.5　九种尺度变换算子"
    },
    {
      "anchor": "V82-P0934",
      "ordinal": 934,
      "style": "BodyCJK",
      "text": "每个算子都有独有 semantic_signature，不能复制 M01 的聚合语句冒充其他算子。"
    },
    {
      "anchor": "V82-P0935",
      "ordinal": 935,
      "style": "SecH3",
      "text": "5.5.1　M01　聚合"
    },
    {
      "anchor": "V82-P0936",
      "ordinal": 936,
      "style": "BodyCJK",
      "text": "签名是“单位—总体分区聚合”。最低桥包括逐单位映射、成员与排除、权重与缺失、替代聚合规则和异质性。信息损失包括尾部、次序、协方差、局部时序及少数位置可见度。总体不能按登记规则复现、合理替代规则造成方向反转，或总体关联被回填为个体属性时，程序失败。即使聚合获得支持，也不得据总体结果直接处置成员。"
    },
    {
      "anchor": "V82-P0937",
      "ordinal": 937,
      "style": "SecH3",
      "text": "5.5.2　M02　嵌套"
    },
    {
      "anchor": "V82-P0938",
      "ordinal": 938,
      "style": "BodyCJK",
      "text": "签名是“边界—成员嵌入”。它必须分成两条支路："
    },
    {
      "anchor": "V82-P0939",
      "ordinal": 939,
      "style": "ListPara",
      "text": "描述性嵌套只检验边界、成员、重叠、退出和接口映射；它可以成立而没有任何跨层因果。"
    },
    {
      "anchor": "V82-P0940",
      "ordinal": 940,
      "style": "ListPara",
      "text": "跨层因果必须链接预注册 G4a 或 G4b root-instance，固定子型和唯一成功判据，并通过 CAUSAL 与三态/null 门。"
    },
    {
      "anchor": "V82-P0941",
      "ordinal": 941,
      "style": "BodyCJK",
      "text": "控制当前状态与共同环境后没有条件增量，并不自动证明“没有跨层作用”；只有等价/充分性、功效/灵敏度和容差门同时通过，才可登记限定零结论。描述性嵌套不生成上位优先、下位义务或 J 轴扩展。"
    },
    {
      "anchor": "V82-P0942",
      "ordinal": 942,
      "style": "BodyCJK",
      "text": "记录时必须在 descriptive_nesting、cross_layer_causal、object_conversion、intervention_conversion 中选一支，并分别绑定描述、因果、对象转换或干预转换模式；不得用描述性嵌套的边界材料支持后面三支。"
    },
    {
      "anchor": "V82-P0943",
      "ordinal": 943,
      "style": "SecH3",
      "text": "5.5.3　M03　网络传播"
    },
    {
      "anchor": "V82-P0944",
      "ordinal": 944,
      "style": "BodyCJK",
      "text": "签名是“沿时间化路径传导”。必须登记节点、边、方向、权重、容量、采样边界、候选与替代路径、时延和损耗。连接或同步只生成候选；切断路径后结果不变而零结论门未通过时，仍是 unsupported_or_undecided。网络采样会遗漏弱边、离网位置和跨网桥，只保留终点影响也不能恢复传播次序。中心性不等于意图、责任或处置权限。"
    },
    {
      "anchor": "V82-P0945",
      "ordinal": 945,
      "style": "SecH3",
      "text": "5.5.4　M04　时间累积"
    },
    {
      "anchor": "V82-P0946",
      "ordinal": 946,
      "style": "BodyCJK",
      "text": "签名是“带窗口的纵向组合”。必须冻结时间基准、基线、窗口、时滞、持久阈值和累积/衰减/恢复规则，并比较共同趋势、季节、队列和替代窗口。效应在控制后消失或随窗口变化，只表示正向支持不足；没有通过零结论门，不能发布“无累积”。基础时间组合不预证 G3；只有历史项在控制当前状态后仍提供条件增量时，才链接 G3-instance。"
    },
    {
      "anchor": "V82-P0947",
      "ordinal": 947,
      "style": "SecH3",
      "text": "5.5.5　M05　制度化"
    },
    {
      "anchor": "V82-P0948",
      "ordinal": 948,
      "style": "BodyCJK",
      "text": "签名是“持久制度写回”。它把五个判断分开：制度事实上存在、法律有效、规范正当、保护是否成立、是否应继续。记录、角色、资源、决策规则或后续转移发生持久改变，可以支持制度化事实；授权无效、参与不足、保护机制失效、缺少申诉/反报复/回滚属于治理失败、规范争议和行动降级理由，不能据此抹掉制度已存在的事实。反过来，制度存在也不证明它合法、正当、具有充分保护或应继续。"
    },
    {
      "anchor": "V82-P0949",
      "ordinal": 949,
      "style": "BodyCJK",
      "text": "selected_operator_branch 只允许 institutional_fact、institutional_causal_effect、institutional_object_conversion 或 institutional_intervention_conversion。法律有效性审查、治理质量、规范正当性、保护充分性和应否继续没有任何一项能伪装成 institutional_fact 的正向或零结论。"
    },
    {
      "anchor": "V82-P0950",
      "ordinal": 950,
      "style": "SecH3",
      "text": "5.5.6　M06　涌现"
    },
    {
      "anchor": "V82-P0951",
      "ordinal": 951,
      "style": "BodyCJK",
      "text": "签名是“互动生成目标尺度模式”。源单位、互动规则、目标对象和目标模式须与预登记简单加和模型在同一指标上比较。简单加和模型表现相当，只在充分性/等价、功效/灵敏度和容差门通过时支持“加和已足够”；否则保持未决。宏观模式不能反推唯一微观原因，也不能自动证明下行因果。下行约束须另链 G4/CAUSAL 实例。"
    },
    {
      "anchor": "V82-P0952",
      "ordinal": 952,
      "style": "SecH3",
      "text": "5.5.7　M07　委托/代表"
    },
    {
      "anchor": "V82-P0953",
      "ordinal": 953,
      "style": "BodyCJK",
      "text": "签名是“代表事实分类与可选授权转移”。必须分开记录：代表性主张、实际代行事实、争议或自任代表、有效委托、J 轴权限转移。无授权时仍可记录实际代行及其影响和责任，但不得登记 J 扩展；授权无效会触发停止或降级，却不能把已经发生的代行与后果删除。多数、可见性、影响力、自称或实际控制都不等于有效委托。"
    },
    {
      "anchor": "V82-P0954",
      "ordinal": 954,
      "style": "BodyCJK",
      "text": "记录必须在 representation_claim、actual_acts、delegation_validity、J_transfer 中选一支。前三支即使获得支持也不能改变 J；只有 J_transfer 与结构化授权元组、独立有效性证据和 j_authorization 同时通过时，J 才可扩展。"
    },
    {
      "anchor": "V82-P0955",
      "ordinal": 955,
      "style": "SecH3",
      "text": "5.5.8　M08　压缩/抽象"
    },
    {
      "anchor": "V82-P0956",
      "ordinal": 956,
      "style": "BodyCJK",
      "text": "签名是“多对一表示压缩”。源材料、算法、阈值、版本、误差、不可恢复信息和任务所需不变量必须可追踪。unknown、not_applicable、not_observable、withheld_for_protection 必须保持区分，任何一种都不能压成“不存在”。高损失表示不得支持高影响行动。"
    },
    {
      "anchor": "V82-P0957",
      "ordinal": 957,
      "style": "SecH3",
      "text": "5.5.9　M09　横向迁移"
    },
    {
      "anchor": "V82-P0958",
      "ordinal": 958,
      "style": "BodyCJK",
      "text": "签名是“跨领域类比迁移”。必须登记映射、差异、断裂、禁止映射、目标责任链和 J 轴差异。源域材料只生成目标候选；supported 或 null_supported 都必须来自独立目标实例。目标证据不足是 not_evaluated 或 unsupported_or_undecided，不是目标机制不存在的证明。类比不生成目标领域行动授权。"
    },
    {
      "anchor": "V82-P0959",
      "ordinal": 959,
      "style": "SecH2",
      "text": "5.6　通用原语的尺度边界"
    },
    {
      "anchor": "V82-P0960",
      "ordinal": 960,
      "style": "BodyCJK",
      "text": "通用原语是 D 类接口，不再携带经验零模型或证伪模板。尤其需要锁住四项边界："
    },
    {
      "anchor": "V82-P0961",
      "ordinal": 961,
      "style": "ListPara",
      "text": "U07 的基础反馈只要求返回通道和后续状态更新，不要求 G3；持久历史增量和学习才另检 G3。"
    },
    {
      "anchor": "V82-P0962",
      "ordinal": 962,
      "style": "ListPara",
      "text": "U09 的瞬时需求—容量缺口不要求 G3；累积损伤或迟恢复才另检历史条件增量。"
    },
    {
      "anchor": "V82-P0963",
      "ordinal": 963,
      "style": "ListPara",
      "text": "U10 只登记候选痕迹、载体和保留窗口，不预证路径依赖；G3 仍须证明历史项在控制当前状态后的条件增量。"
    },
    {
      "anchor": "V82-P0964",
      "ordinal": 964,
      "style": "ListPara",
      "text": "U11 的基础相位模式不要求 G3 或 G4；因果触发另检 G2，迟滞另检 G3，对象转换另检 G4。"
    },
    {
      "anchor": "V82-P0965",
      "ordinal": 965,
      "style": "BodyCJK",
      "text": "同理，U01 只登记候选对象而不预保证 G1；U05 的关系定义不证明因果；U06 的通道字段不证明通道效应。"
    },
    {
      "anchor": "V82-P0966",
      "ordinal": 966,
      "style": "SecH2",
      "text": "5.7　统一尺度变换记录"
    },
    {
      "anchor": "V82-P0967",
      "ordinal": 967,
      "style": "BodyCJK",
      "text": "每个实例都必须出现十四节和全部字段："
    },
    {
      "anchor": "V82-P0968",
      "ordinal": 968,
      "style": "TableHead",
      "text": "节"
    },
    {
      "anchor": "V82-P0969",
      "ordinal": 969,
      "style": "TableHead",
      "text": "必填字段"
    },
    {
      "anchor": "V82-P0970",
      "ordinal": 970,
      "style": "TableText",
      "text": "identity"
    },
    {
      "anchor": "V82-P0971",
      "ordinal": 971,
      "style": "TableText",
      "text": "contract_id、concept_id、version、proposition_ids、purpose"
    },
    {
      "anchor": "V82-P0972",
      "ordinal": 972,
      "style": "TableText",
      "text": "scale"
    },
    {
      "anchor": "V82-P0973",
      "ordinal": 973,
      "style": "TableText",
      "text": "SP0、SP1、九条 axis_differences、unchanged_axes、transformation_class、j_authorization"
    },
    {
      "anchor": "V82-P0974",
      "ordinal": 974,
      "style": "TableText",
      "text": "objects"
    },
    {
      "anchor": "V82-P0975",
      "ordinal": 975,
      "style": "TableText",
      "text": "源/目标有效对象、source_K、target_K、identity_mapping、单位、总体、边界、成员、排除项"
    },
    {
      "anchor": "V82-P0976",
      "ordinal": 976,
      "style": "TableText",
      "text": "semantics"
    },
    {
      "anchor": "V82-P0977",
      "ordinal": 977,
      "style": "TableText",
      "text": "preserved_core、allowed_changes、lost_elements、prohibited_mappings"
    },
    {
      "anchor": "V82-P0978",
      "ordinal": 978,
      "style": "TableText",
      "text": "transformation"
    },
    {
      "anchor": "V82-P0979",
      "ordinal": 979,
      "style": "TableText",
      "text": "单一算子、selected_operator_branch、claim_mode、规则、因果桥、时滞、映射误差、有效期、root-instance、子型、成功判据、正向和零决策规则、正向阈值、等价/充分性检验、功效/灵敏度、容差、结果状态"
    },
    {
      "anchor": "V82-P0980",
      "ordinal": 980,
      "style": "TableText",
      "text": "variables"
    },
    {
      "anchor": "V82-P0981",
      "ordinal": 981,
      "style": "TableText",
      "text": "输入、状态、输出和跨变量依赖"
    },
    {
      "anchor": "V82-P0982",
      "ordinal": 982,
      "style": "TableText",
      "text": "evidence"
    },
    {
      "anchor": "V82-P0983",
      "ordinal": 983,
      "style": "TableText",
      "text": "源/目标证据、覆盖、异质性、反例、缺席信号、替代解释、残差检验、复制或外部验证"
    },
    {
      "anchor": "V82-P0984",
      "ordinal": 984,
      "style": "TableText",
      "text": "loss"
    },
    {
      "anchor": "V82-P0985",
      "ordinal": 985,
      "style": "TableText",
      "text": "压缩细节、不可恢复信息、低可见位置和局部排除区"
    },
    {
      "anchor": "V82-P0986",
      "ordinal": 986,
      "style": "TableText",
      "text": "responsibility"
    },
    {
      "anchor": "V82-P0987",
      "ordinal": 987,
      "style": "TableText",
      "text": "行动者、决策者、授权者、承接载体、责任主体、受益者和成本承担者"
    },
    {
      "anchor": "V82-P0988",
      "ordinal": 988,
      "style": "TableText",
      "text": "normative"
    },
    {
      "anchor": "V82-P0989",
      "ordinal": 989,
      "style": "TableText",
      "text": "价值前提、选择类型、规范选择记录、运行时 N 原则、授权来源、C12 门和 O1-O4 程序"
    },
    {
      "anchor": "V82-P0990",
      "ordinal": 990,
      "style": "TableText",
      "text": "protection"
    },
    {
      "anchor": "V82-P0991",
      "ordinal": 991,
      "style": "TableText",
      "text": "保护适用性、低权力位置、安全提交和反报复"
    },
    {
      "anchor": "V82-P0992",
      "ordinal": 992,
      "style": "TableText",
      "text": "action"
    },
    {
      "anchor": "V82-P0993",
      "ordinal": 993,
      "style": "TableText",
      "text": "判断上限、行动上限、禁止动作、停止条件、责任人和机器可指向的 selected_action"
    },
    {
      "anchor": "V82-P0994",
      "ordinal": 994,
      "style": "TableText",
      "text": "correction"
    },
    {
      "anchor": "V82-P0995",
      "ordinal": 995,
      "style": "TableText",
      "text": "申诉、复核、回滚、修复和写回"
    },
    {
      "anchor": "V82-P0996",
      "ordinal": 996,
      "style": "TableText",
      "text": "lifecycle"
    },
    {
      "anchor": "V82-P0997",
      "ordinal": 997,
      "style": "TableText",
      "text": "有效期、复审点、暂停和退场"
    },
    {
      "anchor": "V82-P0998",
      "ordinal": 998,
      "style": "BodyCJK",
      "text": "source_K、target_K 和 identity_mapping 共同决定对象保持、转换或不可比；同名不是同一性证据。映射记录必须同时保存源、目标 K 的摘要，源对象与目标对象分别在两套 K 下的四项判据结果，正向与反向映射，保持和违反的判据，结果前冻结的预注册引用，以及可复核的验证制品与哈希。判据结果只允许 passed、failed 或 undetermined，不能用一个布尔值掩盖是哪一项没有通过。"
    },
    {
      "anchor": "V82-P0999",
      "ordinal": 999,
      "style": "TableHead",
      "text": "K 映射分类"
    },
    {
      "anchor": "V82-P1000",
      "ordinal": 1000,
      "style": "TableHead",
      "text": "最低成立条件"
    },
    {
      "anchor": "V82-P1001",
      "ordinal": 1001,
      "style": "TableHead",
      "text": "结果上限"
    },
    {
      "anchor": "V82-P1002",
      "ordinal": 1002,
      "style": "TableText",
      "text": "same_object"
    },
    {
      "anchor": "V82-P1003",
      "ordinal": 1003,
      "style": "TableText",
      "text": "双向映射均有效；源对象与目标对象在 source_K、target_K 下四项检查均通过；保持判据非空且违反判据为空"
    },
    {
      "anchor": "V82-P1004",
      "ordinal": 1004,
      "style": "TableText",
      "text": "可在当前合同内沿用对象身份，但不推出语义、因果或规范性质也保持"
    },
    {
      "anchor": "V82-P1005",
      "ordinal": 1005,
      "style": "TableText",
      "text": "converted_object"
    },
    {
      "anchor": "V82-P1006",
      "ordinal": 1006,
      "style": "TableText",
      "text": "source_under_source_K 与 target_under_target_K 通过，target_under_source_K 失败；违反项和结果前预注册引用具体；另有 object_conversion 模式及取得支持的 G4b 实例"
    },
    {
      "anchor": "V82-P1007",
      "ordinal": 1007,
      "style": "TableText",
      "text": "只登记预注册 K 下的对象转换，不得在结果后改写 K 制造转换"
    },
    {
      "anchor": "V82-P1008",
      "ordinal": 1008,
      "style": "TableText",
      "text": "incomparable"
    },
    {
      "anchor": "V82-P1009",
      "ordinal": 1009,
      "style": "TableText",
      "text": "两端各自在本方 K 下通过，至少一个交叉 K 检查失败；正反向映射保存完整尝试记录且至少一项验证为无效，并有可解析证据"
    },
    {
      "anchor": "V82-P1010",
      "ordinal": 1010,
      "style": "TableText",
      "text": "表示已知不可比，只能 unsupported_or_undecided；不是“尚未评估”"
    },
    {
      "anchor": "V82-P1011",
      "ordinal": 1011,
      "style": "TableText",
      "text": "undetermined"
    },
    {
      "anchor": "V82-P1012",
      "ordinal": 1012,
      "style": "TableText",
      "text": "检验尚未运行，或必要映射、判据未知或不可观察；四项结果均保持 undetermined"
    },
    {
      "anchor": "V82-P1013",
      "ordinal": 1013,
      "style": "TableText",
      "text": "只能 unsupported_or_undecided 或 not_evaluated；不构成不可比或对象转换"
    },
    {
      "anchor": "V82-P1014",
      "ordinal": 1014,
      "style": "BodyCJK",
      "text": "只有源/目标对象和两套 K 都可由验证器重算为深相等时，才允许 builtin:deep-identity。其他非平凡保持或对象转换必须把 mapping_id 交给独立 identity_mapping_results 注册表，逐项核对对象摘要、K 摘要、方向映射、四项判据结果、验证制品和哈希；记录内部自报 valid 或一个看似正确的 ID 前缀都不能充当证明。"
    },
    {
      "anchor": "V82-P1015",
      "ordinal": 1015,
      "style": "BodyCJK",
      "text": "对象转换模式与结果四态必须一致：supported 才对应 converted_object；null_supported 对应通过零结论三门的 same_object；unsupported_or_undecided 只允许保持、已知不可比或未决；not_evaluated 必须保持 undetermined。因此，未检验和检验失败都不能先把目标写成“已经转换”。其他 claim_mode 也不得在同一条原子记录里兼报 converted_object，对象转换必须拆成自己的原子检验。"
    },
    {
      "anchor": "V82-P1016",
      "ordinal": 1016,
      "style": "BodyCJK",
      "text": "claim_mode 为 root_hypothesis、causal、object_conversion 或 intervention_conversion 时必须填写 root_instance_ids，后三者还必须给出非空因果桥；只有 descriptive_mapping 可把 root-instance、子型和成功判据标为 not_applicable。非描述模式登记 supported 或 null_supported 时，还必须向验证器提交可解析的 root-instance 注册表，并核对实例 ID、根族、合同版本、预选子型、唯一成功判据与实例状态；一个看似正确的字符串前缀不能充当实例。描述桥正向门通过时可以记 supported，只有所选模式没有运行时才记 not_evaluated。"
    },
    {
      "anchor": "V82-P1017",
      "ordinal": 1017,
      "style": "BodyCJK",
      "text": "十四节是稳定接口，不是把人类治理语义投射给所有对象。protection.applicability 必须显式登记对象类型、下游用途、理由和证据引用，不能从 actors 等空列表反推。对象类型为 nonhuman，且用途只含 description_only 或有证据证明不影响人类/有感主体的 nonhuman_intervention_without_human_or_sentient_effect 时，safe_submission 与 anti_retaliation 可带理由记 not_applicable；但现实实验或工程干预仍有行动主体和对象，必须填写具体 J、行动责任人、停止、复核与回滚，只有纯描述用途才允许 J 不适用。自然系统中的能量、物质或计算资源本身不触发这套人类保护合同。对象为人类、有感非人、混合或未知，或用途涉及人的评价、其稀缺资源配置、权利、暴露风险或现实处置时，保护字段立即成为强制项，不得沿用先前的不适用状态。保护不适用绝不推出行动正当，规范选择仍另行判断。"
    },
    {
      "anchor": "V82-P1018",
      "ordinal": 1018,
      "style": "BodyCJK",
      "text": "action_owner 只说明谁负责执行或停止，不能反推 claim_mode=intervention_conversion，也不能证明行动有效或正当。任何外部行动必须链接 selection_record_id，公开 value_premises 与运行时 normative_principle_ids；N1 单独只能阻止越权，不能产生正向方案。选择记录中的 feasible_alternatives 不是名称列表，而是带稳定 option_id 的结构化方案；每项冻结 option_kind、动作类型、目标对象、地域、有效期、可逆性、预期影响和分配影响，并且恰有一项 option_kind=no_action，由 no_action_option_id 唯一指向。selected_action.selected_option_id 必须解析到一项 external_action，而且其动作、对象、地域和有效期与该方案逐项相等；选择不行动 ID、只对上自然语言标签，或同时改写动作与 J 而不改获准方案，都必须被拒绝。至少一条当前有效且独立复核的 J 原子授权元组还必须同时覆盖该主体、对象、动作、地域和期限，并与授权来源一致；一条无关但形式有效的授权不能为拟议行动背书。记录还必须有通过的十组件 c12_gate、O1-O4 procedure_ids、行动责任人、禁止动作、停止、保护、申诉、复核和回滚。缺任一项时，行动上限只能是不行动或继续审议；经验上的干预转换另由相应 root-instance 判断。"
    },
    {
      "anchor": "V82-P1019",
      "ordinal": 1019,
      "style": "BodyCJK",
      "text": "记录链只提供组合次序，不把前一步的支持自动传递给后一步。链校验必须保证每步 contract_id 唯一、每步只有一个算子、相邻对象引用及同一性判据兼容、前一 SP1 与后一 SP0 一致；任一步未决、失效或损失超限，都要在链级输出中保留，不能被最终一步的成功覆盖。"
    },
    {
      "anchor": "V82-P1020",
      "ordinal": 1020,
      "style": "SecH2",
      "text": "5.8　机器校验与保护底板"
    },
    {
      "anchor": "V82-P1021",
      "ordinal": 1021,
      "style": "BodyCJK",
      "text": "record_schema 要求十四节和各节字段集合精确一致，字段类型由 field_types_by_section 固定。九条轴比较记录不得缺轴或重复；每条非未知轴关系必须提交结构化且由对应比较器验证为有效的见证；transformation_class 必须与分类算法输出一致；算子 ID 必须使用限定形式，语义签名必须互异。这里的机器分类器只组合已经通过领域比较器的逐轴关系，不自行替代空间几何、组织图、因果抽象、网络嵌入、对象同一性或授权有效性判断；没有可解析的 comparator_results 与非平凡 identity_mapping_results 产物，就不允许把记录内自报关系升级为尺度升格。源对象与目标对象的经验材料必须引用可解析的独立记录，内部概念编号和框架说明不得充当证据。"
    },
    {
      "anchor": "V82-P1022",
      "ordinal": 1022,
      "style": "BodyCJK",
      "text": "四种缺失状态构成封闭词表：unknown 表示当前未知，not_applicable 表示按合同确实不适用，not_observable 表示当前通道和窗口不可观察，withheld_for_protection 表示为保护而不公开。四者都不是“不存在”，也不能删除字段代替状态。"
    },
    {
      "anchor": "V82-P1023",
      "ordinal": 1023,
      "style": "BodyCJK",
      "text": "carrying_vehicles 与 responsible_subjects 必须分栏；承接、可见、受影响或能力较强都不自动产生责任。凡对人类或有感主体的权利、稀缺资源配置、暴露风险或现实处置产生影响，保护底板必须识别低权力位置和局部排除区，提供安全提交、反报复、停止、申诉、复核和回滚，且不得记为不适用。保护不足时，判断上限与行动上限同时降低。纯描述记录的条件性不适用也不能被下游行动继承；用途改变时必须重开保护审查。"
    },
    {
      "anchor": "V82-P1024",
      "ordinal": 1024,
      "style": "SecH2",
      "text": "5.9　证据边界与独立支持"
    },
    {
      "anchor": "V82-P1025",
      "ordinal": 1025,
      "style": "BodyCJK",
      "text": "M01—M09 的名称、编号、语义签名和分类结果只规定变换应怎样描述与检验，不构成变换已经发生、映射有效或目标性质成立的经验支持。内部概念标签、示例、字段完整度和算法自报结果均不得进入 source_evidence 或 target_evidence 代替对象材料。"
    },
    {
      "anchor": "V82-P1026",
      "ordinal": 1026,
      "style": "BodyCJK",
      "text": "每个实际变换必须分别在源对象和目标对象上取得可解析的独立材料，明确映射、保持项、改变项、丢失项、误差与竞争解释，并接受同一结果状态、正向门和零结论门。源域材料只能生成目标候选；目标侧没有独立支持时，结论停在待检验映射或未知。"
    },
    {
      "anchor": "V82-P1027",
      "ordinal": 1027,
      "style": "SecH2",
      "text": "5.10　跨圈层关系变换"
    },
    {
      "anchor": "V82-P1028",
      "ordinal": 1028,
      "style": "BodyCJK",
      "text": "尺度变换与圈层关系变换必须分开。尺度变换回答同一问题在 SP0 与 SP1 之间哪些变量保持、改变或丢失；圈层关系变换回答两个或多个候选圈层在同一或不同尺度上如何并列、包含、重叠、桥接、竞争或临时形成。一个关系变化可能伴随尺度变化，但不能用其中一个词替代另一个合同。"
    },
    {
      "anchor": "V82-P1029",
      "ordinal": 1029,
      "style": "BodyCJK",
      "text": "跨圈层记录至少包含关系源、关系目标、静态关系类型、成员或接口基准、方向、通道、时延、阈值、时间窗、证据、反例和前后快照。transformed 只作为关系更新结果：原平行关系可能因桥接者出现而转为桥接，重叠关系可能因制度整合转为嵌套，临时圈层可能制度化或解体。每次转化都要检查 K 是否保持；K 失效时记录对象转换，不以改名延续旧对象。"
    },
    {
      "anchor": "V82-P1030",
      "ordinal": 1030,
      "style": "TableHead",
      "text": "变换问题"
    },
    {
      "anchor": "V82-P1031",
      "ordinal": 1031,
      "style": "TableHead",
      "text": "需要调用"
    },
    {
      "anchor": "V82-P1032",
      "ordinal": 1032,
      "style": "TableHead",
      "text": "不得偷换"
    },
    {
      "anchor": "V82-P1033",
      "ordinal": 1033,
      "style": "TableText",
      "text": "个体状态能否代表团队"
    },
    {
      "anchor": "V82-P1034",
      "ordinal": 1034,
      "style": "TableText",
      "text": "聚合 M01、尺度合同与分布损失"
    },
    {
      "anchor": "V82-P1035",
      "ordinal": 1035,
      "style": "TableText",
      "text": "成员属于团队不等于代表团队"
    },
    {
      "anchor": "V82-P1036",
      "ordinal": 1036,
      "style": "TableText",
      "text": "团队是否被组织包含"
    },
    {
      "anchor": "V82-P1037",
      "ordinal": 1037,
      "style": "TableText",
      "text": "嵌套 M02 与具体包含基准"
    },
    {
      "anchor": "V82-P1038",
      "ordinal": 1038,
      "style": "TableText",
      "text": "共同上级不等于成员包含"
    },
    {
      "anchor": "V82-P1039",
      "ordinal": 1039,
      "style": "TableText",
      "text": "两圈层是否因共享成员相关"
    },
    {
      "anchor": "V82-P1040",
      "ordinal": 1040,
      "style": "TableText",
      "text": "重叠关系、成员映射与共同环境"
    },
    {
      "anchor": "V82-P1041",
      "ordinal": 1041,
      "style": "TableText",
      "text": "重叠不自动产生有效反馈"
    },
    {
      "anchor": "V82-P1042",
      "ordinal": 1042,
      "style": "TableText",
      "text": "桥接者是否改变另一圈层"
    },
    {
      "anchor": "V82-P1043",
      "ordinal": 1043,
      "style": "TableText",
      "text": "M03 传播、通道和反事实"
    },
    {
      "anchor": "V82-P1044",
      "ordinal": 1044,
      "style": "TableText",
      "text": "接触不等于传导，传导不等于代表"
    },
    {
      "anchor": "V82-P1045",
      "ordinal": 1045,
      "style": "TableText",
      "text": "临时群体是否形成持久对象"
    },
    {
      "anchor": "V82-P1046",
      "ordinal": 1046,
      "style": "TableText",
      "text": "G1、G3、M05 与 K"
    },
    {
      "anchor": "V82-P1047",
      "ordinal": 1047,
      "style": "TableText",
      "text": "留痕不等于制度化"
    },
    {
      "anchor": "V82-P1048",
      "ordinal": 1048,
      "style": "BodyCJK",
      "text": "多重成员关系要求同一行动者在多个圈层中保留不同角色、可见信息、责任、风险和退出能力。不得先把行动者聚合为单一状态，再把该状态复制到所有圈层。跨圈层推演应从局部状态出发，经已声明的成员或接口通道传播，并逐步登记聚合损失。"
    },
    {
      "anchor": "V82-P1049",
      "ordinal": 1049,
      "style": "SecH3",
      "text": "5.10.1　三类变换必须分开"
    },
    {
      "anchor": "V82-P1050",
      "ordinal": 1050,
      "style": "BodyCJK",
      "text": "尺度变换回答同一问题在两个尺度剖面之间哪些变量保持、改变或丢失；圈层关系变换回答候选圈层之间的并列、包含、重叠、桥接、竞争或临时关系如何更新；表示或表述转义回答一个有来源的载荷怎样进入目标任务的词汇、变量或表达。三者可以同时发生，但必须拆成有序记录。"
    },
    {
      "anchor": "V82-P1051",
      "ordinal": 1051,
      "style": "BodyCJK",
      "text": "本版把转义作为一等运行合同，但不新增第十尺度算子。一次转义可以调用传播、压缩、横向迁移或其他既有算子；只有未来证明它具有不可约化的独立输入输出、状态机、失败码和验证过程，才考虑提升为独立算子。"
    },
    {
      "anchor": "V82-P1052",
      "ordinal": 1052,
      "style": "SecH3",
      "text": "5.10.2　转义损失审计"
    },
    {
      "anchor": "V82-P1053",
      "ordinal": 1053,
      "style": "BodyCJK",
      "text": "若两个在源任务中可区分的源状态，在目标表示中无法区分，则针对该项区别登记任务相关损失。恒等映射、可逆编码或对目标任务充分的映射可能没有检测到相关损失，因此规则是“不得预设无损”，而不是“必然有损”。"
    },
    {
      "anchor": "V82-P1054",
      "ordinal": 1054,
      "style": "BodyCJK",
      "text": "审计项"
    },
    {
      "anchor": "V82-P1055",
      "ordinal": 1055,
      "style": "BodyCJK",
      "text": "最低问题"
    },
    {
      "anchor": "V82-P1056",
      "ordinal": 1056,
      "style": "BodyCJK",
      "text": "不得偷换"
    },
    {
      "anchor": "V82-P1057",
      "ordinal": 1057,
      "style": "BodyCJK",
      "text": "保持"
    },
    {
      "anchor": "V82-P1058",
      "ordinal": 1058,
      "style": "BodyCJK",
      "text": "哪些事实、关系、模态、权利或不确定性必须不变"
    },
    {
      "anchor": "V82-P1059",
      "ordinal": 1059,
      "style": "BodyCJK",
      "text": "保持标题不等于保持语义"
    },
    {
      "anchor": "V82-P1060",
      "ordinal": 1060,
      "style": "BodyCJK",
      "text": "改变"
    },
    {
      "anchor": "V82-P1061",
      "ordinal": 1061,
      "style": "BodyCJK",
      "text": "哪些格式、单位、粒度或表达允许变化"
    },
    {
      "anchor": "V82-P1062",
      "ordinal": 1062,
      "style": "BodyCJK",
      "text": "允许改变不等于任意改义"
    },
    {
      "anchor": "V82-P1063",
      "ordinal": 1063,
      "style": "BodyCJK",
      "text": "折叠"
    },
    {
      "anchor": "V82-P1064",
      "ordinal": 1064,
      "style": "BodyCJK",
      "text": "哪些源差异在目标端合并"
    },
    {
      "anchor": "V82-P1065",
      "ordinal": 1065,
      "style": "BodyCJK",
      "text": "折叠不等于源差异不存在"
    },
    {
      "anchor": "V82-P1066",
      "ordinal": 1066,
      "style": "BodyCJK",
      "text": "遗漏"
    },
    {
      "anchor": "V82-P1067",
      "ordinal": 1067,
      "style": "BodyCJK",
      "text": "哪些内容未进入目标表示及原因"
    },
    {
      "anchor": "V82-P1068",
      "ordinal": 1068,
      "style": "BodyCJK",
      "text": "保护性不公开不等于不存在"
    },
    {
      "anchor": "V82-P1069",
      "ordinal": 1069,
      "style": "BodyCJK",
      "text": "新增"
    },
    {
      "anchor": "V82-P1070",
      "ordinal": 1070,
      "style": "BodyCJK",
      "text": "哪些解释、推断或目标变量由转换产生"
    },
    {
      "anchor": "V82-P1071",
      "ordinal": 1071,
      "style": "BodyCJK",
      "text": "新增变量不等于发现现实实体"
    },
    {
      "anchor": "V82-P1072",
      "ordinal": 1072,
      "style": "BodyCJK",
      "text": "回返"
    },
    {
      "anchor": "V82-P1073",
      "ordinal": 1073,
      "style": "BodyCJK",
      "text": "异常出现时回到哪个父记录或合同"
    },
    {
      "anchor": "V82-P1074",
      "ordinal": 1074,
      "style": "BodyCJK",
      "text": "回返只重开审查，不修补旧运行"
    },
    {
      "anchor": "V82-P1075",
      "ordinal": 1075,
      "style": "BodyCJK",
      "text": "往返重构可以作为检验，但不是充分条件。一个转换可能借助隐藏源记录实现表面往返，却没有保持目标任务语义；另一个单向摘要可能对指定任务充分。复核必须回到预先声明的保持项、损失容限和目标侧结果。"
    },
    {
      "anchor": "V82-P1076",
      "ordinal": 1076,
      "style": "SecH3",
      "text": "5.10.3　有效变量、闭合与残差回返"
    },
    {
      "anchor": "V82-P1077",
      "ordinal": 1077,
      "style": "BodyCJK",
      "text": "有效变量是目标尺度或目标任务中，为压缩状态并改善预定解释、前瞻或方案比较而提出的变量候选。它必须绑定对象、尺度、时间窗、任务、测量、简单基线、误差、失效与退役；有效不等于真实实体、根因、普遍变量或授权依据。"
    },
    {
      "anchor": "V82-P1078",
      "ordinal": 1078,
      "style": "BodyCJK",
      "text": "目标表示不默认动力闭合。被排除变量是否仍带来预定条件信息、预测或干预增量，继续走 G4 的正向门与零结论门。未达到显著增量不能自动证明闭合；出现增量时，把相应影响登记为记忆、噪声、迟滞、未解析项或残差候选，不能按形状直接命名新实体。"
    },
    {
      "anchor": "V82-P1079",
      "ordinal": 1079,
      "style": "BodyCJK",
      "text": "统一尺度变换记录的下一版本应在既有十四节内增加任务、转义父记录、折叠差异、回返地址、重构检验和目标有效变量候选。旧记录结构继续可读，新字段缺失时明确标为旧版本，不做静默补写。"
    },
    {
      "anchor": "V82-P1080",
      "ordinal": 1080,
      "style": "SecH2",
      "text": "5.11　平行与嵌套的同时表示"
    },
    {
      "anchor": "V82-P1081",
      "ordinal": 1081,
      "style": "BodyCJK",
      "text": "现实结构不是单棵层级树。局部包含关系可以与横向网络、成员重叠、竞争资源和平台桥接同时存在。表示层采用有向多重关系图：节点维持各自对象合同，边维持各自关系合同；“上层”只表示某项包含、管辖或聚合关系，不表示更真实、更正确或更有权。"
    },
    {
      "anchor": "V82-P1082",
      "ordinal": 1082,
      "style": "BodyCJK",
      "text": "当多个圈层共享环境却没有直接通道时，模型保留共同条件节点，不虚构圈层间直接边；当通道只在事件窗口内开放时，边具有起止时间；当不同关系方向相反时，分别建边。这样才能在事件发生后判断哪条关系真正改变，而不是把整个结构一次性重画成事后故事。"
    }
  ],
  "tables": [
    {
      "anchor": "V82-T012",
      "cell_paragraph_ordinals": [
        [
          [
            871
          ],
          [
            872
          ],
          [
            873
          ],
          [
            874
          ]
        ],
        [
          [
            875
          ],
          [
            876
          ],
          [
            877
          ],
          [
            878
          ]
        ],
        [
          [
            879
          ],
          [
            880
          ],
          [
            881
          ],
          [
            882
          ]
        ],
        [
          [
            883
          ],
          [
            884
          ],
          [
            885
          ],
          [
            886
          ]
        ],
        [
          [
            887
          ],
          [
            888
          ],
          [
            889
          ],
          [
            890
          ]
        ],
        [
          [
            891
          ],
          [
            892
          ],
          [
            893
          ],
          [
            894
          ]
        ],
        [
          [
            895
          ],
          [
            896
          ],
          [
            897
          ],
          [
            898
          ]
        ],
        [
          [
            899
          ],
          [
            900
          ],
          [
            901
          ],
          [
            902
          ]
        ],
        [
          [
            903
          ],
          [
            904
          ],
          [
            905
          ],
          [
            906
          ]
        ],
        [
          [
            907
          ],
          [
            908
          ],
          [
            909
          ],
          [
            910
          ]
        ]
      ],
      "ordinal": 12,
      "paragraph_ordinals": [
        871,
        872,
        873,
        874,
        875,
        876,
        877,
        878,
        879,
        880,
        881,
        882,
        883,
        884,
        885,
        886,
        887,
        888,
        889,
        890,
        891,
        892,
        893,
        894,
        895,
        896,
        897,
        898,
        899,
        900,
        901,
        902,
        903,
        904,
        905,
        906,
        907,
        908,
        909,
        910
      ],
      "rows": [
        [
          "轴",
          "状态字段核心",
          "expands 的计算见证",
          "不可替代边界"
        ],
        [
          "A 聚合层次",
          "单位、成员集、分区、聚合规则、权重、排除项",
          "目标总体覆盖源总体，目标分区是源分区的登记粗化",
          "不得由 O、X、I 或 J 替代"
        ],
        [
          "X 空间范围",
          "坐标系、空间集合、边界通道、外部连接",
          "坐标对齐后源空间是真子集",
          "不得由 A、O、I 或 J 替代"
        ],
        [
          "T 时间跨度",
          "时间基准、窗口角色、起止点、时滞模型",
          "同一基准与角色下目标区间真包含源区间",
          "当前截面和长期路径不能互代"
        ],
        [
          "O 组织层级",
          "组织图、版本、节点、包含边、接口、重叠",
          "同版组织 DAG 中目标节点覆盖源节点祖先闭包",
          "组织上位不等于 J 扩大"
        ],
        [
          "C 因果层次",
          "因果模型、变量、边、干预语义、抽象映射",
          "目标模型经语义保持映射覆盖源模型并增加可区分层面",
          "层级标签、时序和相关不能代替因果桥"
        ],
        [
          "R 观察分辨率",
          "测量协议、可区分类、参数、误差、保护性省略",
          "目标协议保留源协议全部区分并至少细分一类",
          "高分辨率不等于完整或有权行动"
        ],
        [
          "I 影响范围",
          "结果、阈值、窗口、受影响位置、效应阶次",
          "对齐后目标受影响位置集真包含源集合",
          "影响和观察均不等于授权"
        ],
        [
          "N 网络拓扑范围",
          "图与版本、节点、边、语义、采样边界",
          "存在语义保持图嵌入且目标覆盖源图",
          "网络中心不等于责任中心"
        ],
        [
          "J 管辖与授权范围",
          "原子授权元组集合；每个元组固定来源、主体、单一对象、单一动作、地域、期限、撤回、有效性和证据",
          "目标有效原子元组规范化集合真包含，且每个新增元组有独立有效性见证",
          "任何其他轴均不能替代 J；禁止对象集与动作集做笛卡尔积"
        ]
      ]
    },
    {
      "anchor": "V82-T013",
      "cell_paragraph_ordinals": [
        [
          [
            968
          ],
          [
            969
          ]
        ],
        [
          [
            970
          ],
          [
            971
          ]
        ],
        [
          [
            972
          ],
          [
            973
          ]
        ],
        [
          [
            974
          ],
          [
            975
          ]
        ],
        [
          [
            976
          ],
          [
            977
          ]
        ],
        [
          [
            978
          ],
          [
            979
          ]
        ],
        [
          [
            980
          ],
          [
            981
          ]
        ],
        [
          [
            982
          ],
          [
            983
          ]
        ],
        [
          [
            984
          ],
          [
            985
          ]
        ],
        [
          [
            986
          ],
          [
            987
          ]
        ],
        [
          [
            988
          ],
          [
            989
          ]
        ],
        [
          [
            990
          ],
          [
            991
          ]
        ],
        [
          [
            992
          ],
          [
            993
          ]
        ],
        [
          [
            994
          ],
          [
            995
          ]
        ],
        [
          [
            996
          ],
          [
            997
          ]
        ]
      ],
      "ordinal": 13,
      "paragraph_ordinals": [
        968,
        969,
        970,
        971,
        972,
        973,
        974,
        975,
        976,
        977,
        978,
        979,
        980,
        981,
        982,
        983,
        984,
        985,
        986,
        987,
        988,
        989,
        990,
        991,
        992,
        993,
        994,
        995,
        996,
        997
      ],
      "rows": [
        [
          "节",
          "必填字段"
        ],
        [
          "identity",
          "contract_id、concept_id、version、proposition_ids、purpose"
        ],
        [
          "scale",
          "SP0、SP1、九条 axis_differences、unchanged_axes、transformation_class、j_authorization"
        ],
        [
          "objects",
          "源/目标有效对象、source_K、target_K、identity_mapping、单位、总体、边界、成员、排除项"
        ],
        [
          "semantics",
          "preserved_core、allowed_changes、lost_elements、prohibited_mappings"
        ],
        [
          "transformation",
          "单一算子、selected_operator_branch、claim_mode、规则、因果桥、时滞、映射误差、有效期、root-instance、子型、成功判据、正向和零决策规则、正向阈值、等价/充分性检验、功效/灵敏度、容差、结果状态"
        ],
        [
          "variables",
          "输入、状态、输出和跨变量依赖"
        ],
        [
          "evidence",
          "源/目标证据、覆盖、异质性、反例、缺席信号、替代解释、残差检验、复制或外部验证"
        ],
        [
          "loss",
          "压缩细节、不可恢复信息、低可见位置和局部排除区"
        ],
        [
          "responsibility",
          "行动者、决策者、授权者、承接载体、责任主体、受益者和成本承担者"
        ],
        [
          "normative",
          "价值前提、选择类型、规范选择记录、运行时 N 原则、授权来源、C12 门和 O1-O4 程序"
        ],
        [
          "protection",
          "保护适用性、低权力位置、安全提交和反报复"
        ],
        [
          "action",
          "判断上限、行动上限、禁止动作、停止条件、责任人和机器可指向的 selected_action"
        ],
        [
          "correction",
          "申诉、复核、回滚、修复和写回"
        ],
        [
          "lifecycle",
          "有效期、复审点、暂停和退场"
        ]
      ]
    },
    {
      "anchor": "V82-T014",
      "cell_paragraph_ordinals": [
        [
          [
            999
          ],
          [
            1000
          ],
          [
            1001
          ]
        ],
        [
          [
            1002
          ],
          [
            1003
          ],
          [
            1004
          ]
        ],
        [
          [
            1005
          ],
          [
            1006
          ],
          [
            1007
          ]
        ],
        [
          [
            1008
          ],
          [
            1009
          ],
          [
            1010
          ]
        ],
        [
          [
            1011
          ],
          [
            1012
          ],
          [
            1013
          ]
        ]
      ],
      "ordinal": 14,
      "paragraph_ordinals": [
        999,
        1000,
        1001,
        1002,
        1003,
        1004,
        1005,
        1006,
        1007,
        1008,
        1009,
        1010,
        1011,
        1012,
        1013
      ],
      "rows": [
        [
          "K 映射分类",
          "最低成立条件",
          "结果上限"
        ],
        [
          "same_object",
          "双向映射均有效；源对象与目标对象在 source_K、target_K 下四项检查均通过；保持判据非空且违反判据为空",
          "可在当前合同内沿用对象身份，但不推出语义、因果或规范性质也保持"
        ],
        [
          "converted_object",
          "source_under_source_K 与 target_under_target_K 通过，target_under_source_K 失败；违反项和结果前预注册引用具体；另有 object_conversion 模式及取得支持的 G4b 实例",
          "只登记预注册 K 下的对象转换，不得在结果后改写 K 制造转换"
        ],
        [
          "incomparable",
          "两端各自在本方 K 下通过，至少一个交叉 K 检查失败；正反向映射保存完整尝试记录且至少一项验证为无效，并有可解析证据",
          "表示已知不可比，只能 unsupported_or_undecided；不是“尚未评估”"
        ],
        [
          "undetermined",
          "检验尚未运行，或必要映射、判据未知或不可观察；四项结果均保持 undetermined",
          "只能 unsupported_or_undecided 或 not_evaluated；不构成不可比或对象转换"
        ]
      ]
    },
    {
      "anchor": "V82-T015",
      "cell_paragraph_ordinals": [
        [
          [
            1030
          ],
          [
            1031
          ],
          [
            1032
          ]
        ],
        [
          [
            1033
          ],
          [
            1034
          ],
          [
            1035
          ]
        ],
        [
          [
            1036
          ],
          [
            1037
          ],
          [
            1038
          ]
        ],
        [
          [
            1039
          ],
          [
            1040
          ],
          [
            1041
          ]
        ],
        [
          [
            1042
          ],
          [
            1043
          ],
          [
            1044
          ]
        ],
        [
          [
            1045
          ],
          [
            1046
          ],
          [
            1047
          ]
        ]
      ],
      "ordinal": 15,
      "paragraph_ordinals": [
        1030,
        1031,
        1032,
        1033,
        1034,
        1035,
        1036,
        1037,
        1038,
        1039,
        1040,
        1041,
        1042,
        1043,
        1044,
        1045,
        1046,
        1047
      ],
      "rows": [
        [
          "变换问题",
          "需要调用",
          "不得偷换"
        ],
        [
          "个体状态能否代表团队",
          "聚合 M01、尺度合同与分布损失",
          "成员属于团队不等于代表团队"
        ],
        [
          "团队是否被组织包含",
          "嵌套 M02 与具体包含基准",
          "共同上级不等于成员包含"
        ],
        [
          "两圈层是否因共享成员相关",
          "重叠关系、成员映射与共同环境",
          "重叠不自动产生有效反馈"
        ],
        [
          "桥接者是否改变另一圈层",
          "M03 传播、通道和反事实",
          "接触不等于传导，传导不等于代表"
        ],
        [
          "临时群体是否形成持久对象",
          "G1、G3、M05 与 K",
          "留痕不等于制度化"
        ]
      ]
    },
    {
      "anchor": "V82-T016",
      "cell_paragraph_ordinals": [
        [
          [
            1054
          ],
          [
            1055
          ],
          [
            1056
          ]
        ],
        [
          [
            1057
          ],
          [
            1058
          ],
          [
            1059
          ]
        ],
        [
          [
            1060
          ],
          [
            1061
          ],
          [
            1062
          ]
        ],
        [
          [
            1063
          ],
          [
            1064
          ],
          [
            1065
          ]
        ],
        [
          [
            1066
          ],
          [
            1067
          ],
          [
            1068
          ]
        ],
        [
          [
            1069
          ],
          [
            1070
          ],
          [
            1071
          ]
        ],
        [
          [
            1072
          ],
          [
            1073
          ],
          [
            1074
          ]
        ]
      ],
      "ordinal": 16,
      "paragraph_ordinals": [
        1054,
        1055,
        1056,
        1057,
        1058,
        1059,
        1060,
        1061,
        1062,
        1063,
        1064,
        1065,
        1066,
        1067,
        1068,
        1069,
        1070,
        1071,
        1072,
        1073,
        1074
      ],
      "rows": [
        [
          "审计项",
          "最低问题",
          "不得偷换"
        ],
        [
          "保持",
          "哪些事实、关系、模态、权利或不确定性必须不变",
          "保持标题不等于保持语义"
        ],
        [
          "改变",
          "哪些格式、单位、粒度或表达允许变化",
          "允许改变不等于任意改义"
        ],
        [
          "折叠",
          "哪些源差异在目标端合并",
          "折叠不等于源差异不存在"
        ],
        [
          "遗漏",
          "哪些内容未进入目标表示及原因",
          "保护性不公开不等于不存在"
        ],
        [
          "新增",
          "哪些解释、推断或目标变量由转换产生",
          "新增变量不等于发现现实实体"
        ],
        [
          "回返",
          "异常出现时回到哪个父记录或合同",
          "回返只重开审查，不修补旧运行"
        ]
      ]
    }
  ]
}
```
<!-- canonical-records:end -->
